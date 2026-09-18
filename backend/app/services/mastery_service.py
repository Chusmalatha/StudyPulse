"""
Service for updating concept mastery score, confidence, mastery history, and repeated mistakes.
"""
import math
import logging
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List, Tuple
from bson import ObjectId
from app.db.database import get_database
from app.models.concept import ConceptModel
from app.models.mastery import MasteryEventModel, RepeatedMistakeModel
from app.services.learning_context_service import LearningContextService

logger = logging.getLogger(__name__)


class MasteryService:
    """Core update engine for Concept Mastery & Learning Context."""

    def __init__(self, db=None, context_service: Optional[LearningContextService] = None):
        self.db = db if db is not None else get_database()
        self.context_service = context_service if context_service is not None else LearningContextService(self.db)

    async def _resolve_concept(
        self,
        concept_id: str,
        project_id: str,
        concept_name: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Resolve a concept document by ID, falling back to name-based lookup
        when the ID is orphaned (e.g. after concept re-extraction).
        Returns the raw concept document or None.
        """
        import re as _re
        c_doc = None
        try:
            if ObjectId.is_valid(concept_id):
                c_doc = await self.db["concepts"].find_one({"_id": ObjectId(concept_id), "project_id": project_id})
        except Exception:
            pass

        if not c_doc and concept_name:
            # Fallback: find concept by name (case-insensitive) in the same project
            escaped_name = _re.escape(concept_name.strip())
            c_doc = await self.db["concepts"].find_one({
                "project_id": project_id,
                "name": {"$regex": f"^{escaped_name}$", "$options": "i"}
            })
            if c_doc:
                logger.info(f"Resolved orphaned concept_id {concept_id} to '{concept_name}' (ID: {c_doc['_id']}) via name fallback.")

        return c_doc

    async def update_mastery(
        self,
        user_id: str,
        project_id: str,
        concept_id: str,
        evidence_type: str,     # "MCQ", "OPEN_ENDED"
        evidence_id: str,       # question_attempt_id (Idempotency key)
        is_correct: bool,
        difficulty: float = 1.0,
        qualitative_status: Optional[str] = None, # "GOOD", "NEEDS_IMPROVEMENT"
        mistake_description: Optional[str] = None,
        reason: Optional[str] = None,
        concept_name: Optional[str] = None  # Fallback name for resolving orphaned concept_ids
    ) -> Optional[ConceptModel]:
        """
        Updates concept mastery score & confidence based on new assessment evidence.
        Enforces idempotency using evidence_id.
        Falls back to concept_name lookup when concept_id is orphaned.
        """
        if self.db is None:
            raise RuntimeError("Database not initialized")

        # 1. Idempotency Check: verify evidence_id has not been processed
        existing_event = await self.db["mastery_events"].find_one({"evidence_id": evidence_id, "concept_id": concept_id})
        if existing_event:
            logger.info(f"Evidence {evidence_id} already processed for concept {concept_id}. Skipping.")
            c_doc = await self._resolve_concept(concept_id, project_id, concept_name)
            if c_doc:
                c_doc_copy = dict(c_doc)
                if "_id" in c_doc_copy:
                    c_doc_copy["_id"] = str(c_doc_copy["_id"])
                return ConceptModel(**c_doc_copy)
            return None


        # 2. Fetch target Concept (with name-based fallback for orphaned IDs)
        c_doc = await self._resolve_concept(concept_id, project_id, concept_name)
        if not c_doc:
            logger.warning(f"Concept {concept_id} (name='{concept_name}') not found in project {project_id}. Mastery update skipped.")
            return None

        # Update concept_id to the resolved ID (may differ from input if name-resolved)
        concept_id = str(c_doc["_id"])

        c_doc_copy = dict(c_doc)
        if "_id" in c_doc_copy:
            c_doc_copy["_id"] = str(c_doc_copy["_id"])
        concept = ConceptModel(**c_doc_copy)


        prev_score = concept.mastery_score
        prev_confidence = concept.confidence
        attempts = concept.attempts + 1

        # 3. Calculate Base Delta
        # Max single-attempt delta = 15.0
        max_delta = 15.0
        diff_factor = max(0.5, min(2.0, difficulty))

        if evidence_type == "MCQ":
            if is_correct:
                delta = max_delta * (0.6 + 0.4 * (diff_factor / 2.0))
            else:
                delta = -max_delta * 0.8
        elif evidence_type == "OPEN_ENDED":
            if qualitative_status == "GOOD" or is_correct:
                delta = max_delta * (0.8 + 0.2 * (diff_factor / 2.0))
            else:
                delta = -max_delta * 1.0
        else:
            delta = max_delta * 0.5 if is_correct else -max_delta * 0.5

        # Asymptotically bound score between 0.0 and 100.0
        new_score = prev_score + delta
        new_score = max(0.0, min(100.0, round(new_score, 2)))

        # Confidence formula: asymptotic approach to 1.0 (1.0 - e^(-0.25 * attempts))
        new_confidence = round(1.0 - math.exp(-0.25 * attempts), 2)

        correct_count = concept.correct + (1 if is_correct else 0)
        mistake_count = concept.mistakes + (0 if is_correct else 1)
        now = datetime.now(timezone.utc)

        # 4. Update Concept Document
        update_fields = {
            "mastery_score": new_score,
            "confidence": new_confidence,
            "attempts": attempts,
            "correct": correct_count,
            "mistakes": mistake_count,
            "last_updated": now,
            "updated_at": now
        }

        await self.db["concepts"].update_one(
            {"_id": ObjectId(concept_id)},
            {"$set": update_fields}
        )

        # 5. Record Audit Event
        evt_reason = reason or f"{evidence_type} {'correct' if is_correct else 'incorrect'} attempt (difficulty {difficulty})"
        audit_event = MasteryEventModel(
            concept_id=concept_id,
            project_id=project_id,
            user_id=user_id,
            previous_score=prev_score,
            new_score=new_score,
            previous_confidence=prev_confidence,
            new_confidence=new_confidence,
            evidence_type=evidence_type,
            evidence_id=evidence_id,
            reason=evt_reason
        )
        evt_dict = audit_event.model_dump(by_alias=True, exclude={"id"})
        await self.db["mastery_events"].insert_one(evt_dict)

        # 6. Handle Repeated Mistakes & Persistent Context if attempt was incorrect
        if not is_correct and mistake_description:
            await self._record_repeated_mistake(
                user_id=user_id,
                project_id=project_id,
                concept_id=concept_id,
                concept_name=concept.name,
                mistake_description=mistake_description
            )

        # 7. Update Persistent Context for Low Mastery / Weakness
        if new_score < 50.0 and attempts >= 2:
            await self.context_service.store_or_update_context(
                user_id=user_id,
                project_id=project_id,
                context_type="WEAKNESS",
                key=f"weakness_{concept_id}",
                value=f"Struggling with concept '{concept.name}' (Mastery: {new_score}%)",
                importance=1.5,
                source="MASTERY_SERVICE"
            )

        concept.mastery_score = new_score
        concept.confidence = new_confidence
        concept.attempts = attempts
        concept.correct = correct_count
        concept.mistakes = mistake_count
        concept.last_updated = now

        return concept

    async def _record_repeated_mistake(
        self,
        user_id: str,
        project_id: str,
        concept_id: str,
        concept_name: str,
        mistake_description: str
    ):
        """Records or updates a repeated mistake entry and adds to persistent context."""
        query = {
            "user_id": user_id,
            "project_id": project_id,
            "concept_id": concept_id,
            "mistake_description": mistake_description
        }
        now = datetime.now(timezone.utc)
        existing = await self.db["repeated_mistakes"].find_one(query)

        if existing:
            new_count = existing.get("occurrence_count", 1) + 1
            await self.db["repeated_mistakes"].update_one(
                {"_id": existing["_id"]},
                {"$set": {"occurrence_count": new_count, "last_seen": now}}
            )
        else:
            new_mistake = RepeatedMistakeModel(
                user_id=user_id,
                project_id=project_id,
                concept_id=concept_id,
                mistake_description=mistake_description,
                occurrence_count=1,
                first_seen=now,
                last_seen=now
            )
            m_dict = new_mistake.model_dump(by_alias=True, exclude={"id"})
            await self.db["repeated_mistakes"].insert_one(m_dict)

        # Sync repeated mistake to Persistent Learning Context
        await self.context_service.store_or_update_context(
            user_id=user_id,
            project_id=project_id,
            context_type="REPEATED_MISTAKE",
            key=f"repeated_mistake_{concept_id}",
            value=f"Repeated mistake in {concept_name}: {mistake_description}",
            importance=2.0,
            source="ASSESSMENT"
        )
