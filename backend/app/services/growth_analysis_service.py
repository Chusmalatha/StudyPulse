"""
Service for calculating and tracking learner concept growth trajectories.
"""
import logging
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from bson import ObjectId

from app.db.database import get_database
from app.models.growth_recommendation import GrowthSnapshotModel
from app.schemas.growth_recommendation import GrowthSnapshotResponse, ProjectGrowthResponse
from app.services.project_service import get_project

logger = logging.getLogger(__name__)


class GrowthAnalysisService:
    """Evaluates concept mastery history, categorizing progress into IMPROVING, STABLE, or REQUIRING_ATTENTION."""

    def __init__(self, db=None):
        self.db = db if db is not None else get_database()

    async def analyze_project_growth(
        self,
        project_id: str,
        user_id: str
    ) -> ProjectGrowthResponse:
        """
        Computes growth analysis for all concepts in a project.
        Evaluates mastery history, score deltas, and mistake patterns.
        Enforces zero fake data baselines for unpracticed concepts.
        """
        if self.db is None:
            raise RuntimeError("Database not initialized")

        await get_project(project_id, user_id)

        # 1. Fetch concepts for this project
        cursor = self.db["concepts"].find({"project_id": project_id})
        if hasattr(cursor, "to_list"):
            raw_concepts = await cursor.to_list(length=200)
        else:
            raw_concepts = [c async for c in cursor]

        snapshots: List[GrowthSnapshotResponse] = []
        improving_count = 0
        stable_count = 0
        req_attention_count = 0
        insufficient_count = 0
        now = datetime.now(timezone.utc)

        for c_doc in raw_concepts:
            cid = str(c_doc["_id"])
            concept_name = c_doc.get("name", "Unnamed Concept")
            current_mastery = float(c_doc.get("mastery_score", 0.0))
            attempts = int(c_doc.get("attempts", 0))

            # Fetch mastery audit history for this concept
            evt_cursor = self.db["mastery_events"].find({
                "concept_id": cid,
                "project_id": project_id,
                "user_id": user_id
            }).sort("created_at", 1)

            if hasattr(evt_cursor, "to_list"):
                events = await evt_cursor.to_list(length=100)
            else:
                events = [e async for e in evt_cursor]

            # Fetch active repeated mistakes
            mistake_cursor = self.db["repeated_mistakes"].find({
                "concept_id": cid,
                "project_id": project_id,
                "user_id": user_id
            })
            if hasattr(mistake_cursor, "to_list"):
                mistakes = await mistake_cursor.to_list(length=50)
            else:
                mistakes = [m async for m in mistake_cursor]

            # Determine Growth Category & Delta
            if attempts == 0 or len(events) == 0:
                category = "INSUFFICIENT_EVIDENCE"
                previous_mastery = 0.0
                change_pct = 0.0
                explanation = "Not enough practice evidence yet to determine growth trend. Take practice quizzes to build evidence."
                insufficient_count += 1
            else:
                # Baseline is the previous_score of the earliest event or the initial score
                previous_mastery = float(events[0].get("previous_score", 0.0))
                if len(events) > 1:
                    # Look at score change across recent events
                    change_pct = round(current_mastery - previous_mastery, 1)
                else:
                    change_pct = round(current_mastery - events[0].get("previous_score", 0.0), 1)

                recent_mistakes_count = sum(m.get("occurrence_count", 1) for m in mistakes)

                if change_pct >= 5.0 and recent_mistakes_count == 0:
                    category = "IMPROVING"
                    explanation = f"Mastery increased by +{change_pct}% over recent attempts with strong performance."
                    improving_count += 1
                elif change_pct <= -5.0 or recent_mistakes_count >= 2 or (current_mastery < 50.0 and attempts >= 2):
                    category = "REQUIRING_ATTENTION"
                    if change_pct < 0:
                        explanation = f"Mastery dropped by {change_pct}% across recent assessment attempts."
                    else:
                        explanation = f"Mastery is below threshold ({round(current_mastery, 1)}%) with {recent_mistakes_count} tracked repeated mistakes."
                    req_attention_count += 1
                else:
                    category = "STABLE"
                    explanation = f"Mastery has remained stable around {round(current_mastery, 1)}% over {attempts} attempts."
                    stable_count += 1

            # Persist / Update Growth Snapshot in DB
            snapshot_data = {
                "user_id": user_id,
                "project_id": project_id,
                "concept_id": cid,
                "concept_name": concept_name,
                "current_mastery": current_mastery,
                "previous_mastery": previous_mastery,
                "change_percentage": change_pct,
                "category": category,
                "evidence_count": len(events),
                "explanation": explanation,
                "last_evaluated_at": now
            }

            await self.db["growth_snapshots"].update_one(
                {"user_id": user_id, "project_id": project_id, "concept_id": cid},
                {"$set": snapshot_data},
                upsert=True
            )

            snapshots.append(
                GrowthSnapshotResponse(
                    concept_id=cid,
                    concept_name=concept_name,
                    current_mastery=current_mastery,
                    previous_mastery=previous_mastery,
                    change_percentage=change_pct,
                    category=category,
                    evidence_count=len(events),
                    explanation=explanation,
                    last_evaluated_at=now
                )
            )

        # Sort snapshots: requiring attention first, then improving, then stable, then insufficient
        category_order = {
            "REQUIRING_ATTENTION": 0,
            "IMPROVING": 1,
            "STABLE": 2,
            "INSUFFICIENT_EVIDENCE": 3,
        }
        snapshots.sort(key=lambda s: category_order.get(s.category, 4))

        # Generate AI narrative summary of the learner's growth
        ai_narrative = None
        try:
            from app.ai.llm import LLMProvider
            provider = LLMProvider()

            concept_summary_lines = []
            for s in snapshots:
                if s.category == "INSUFFICIENT_EVIDENCE":
                    concept_summary_lines.append(f"- {s.concept_name}: NOT YET TESTED (0 attempts)")
                else:
                    trend = f"+{s.change_percentage}%" if s.change_percentage >= 0 else f"{s.change_percentage}%"
                    concept_summary_lines.append(
                        f"- {s.concept_name}: {s.current_mastery}% mastery, {s.category}, trend {trend}, {s.evidence_count} quiz events"
                    )

            concept_summary = "\n".join(concept_summary_lines[:15])  # cap for token budget

            sys_prompt = (
                "You are an intelligent learning companion analyzing a student's concept mastery data.\n"
                "Write a concise, encouraging, and actionable 2-3 sentence narrative summary of the student's learning progress.\n"
                "Mention: which concepts need attention, which are untested, and what the student should do next.\n"
                "Be specific about concept names. Do NOT use bullet points — write flowing prose."
            )
            user_prompt = (
                f"CONCEPT MASTERY SUMMARY:\n{concept_summary}\n\n"
                "Write the 2-3 sentence learning narrative now."
            )
            narrative_json = provider.generate_json_completion(
                sys_prompt,
                user_prompt
            )
            # LLM may return {"narrative": "..."} or {"text": "..."}  or just a string in any key
            if isinstance(narrative_json, dict):
                ai_narrative = (
                    narrative_json.get("narrative")
                    or narrative_json.get("text")
                    or narrative_json.get("summary")
                    or next(iter(narrative_json.values()), None)
                )
            if ai_narrative:
                ai_narrative = str(ai_narrative).strip()
        except Exception as narr_err:
            logger.warning(f"AI narrative generation failed: {narr_err}")
            # Build a plain-text fallback narrative
            untested_names = [s.concept_name for s in snapshots if s.category == "INSUFFICIENT_EVIDENCE"]
            attn_names = [s.concept_name for s in snapshots if s.category == "REQUIRING_ATTENTION"]
            improving_names = [s.concept_name for s in snapshots if s.category == "IMPROVING"]
            parts = []
            if improving_names:
                parts.append(f"{', '.join(improving_names[:2])} {'is' if len(improving_names)==1 else 'are'} showing improvement.")
            if attn_names:
                parts.append(f"{', '.join(attn_names[:2])} {'needs' if len(attn_names)==1 else 'need'} attention — review the material and practice more.")
            if untested_names:
                parts.append(f"{', '.join(untested_names[:3])} {'has' if len(untested_names)==1 else 'have'} not been tested yet — take a quiz to start tracking.")
            ai_narrative = " ".join(parts) if parts else "Take a quiz to start building your mastery evidence."

        return ProjectGrowthResponse(
            project_id=project_id,
            improving_count=improving_count,
            stable_count=stable_count,
            requiring_attention_count=req_attention_count,
            insufficient_evidence_count=insufficient_count,
            total_concepts=len(snapshots),
            ai_narrative=ai_narrative,
            snapshots=snapshots,
        )
