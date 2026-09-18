"""
Service for managing persistent student learning context items.
"""
import logging
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
from app.db.database import get_database
from app.models.mastery import LearningContextModel
from app.schemas.mastery import LearningContextResponse

logger = logging.getLogger(__name__)


class LearningContextService:
    """Manages creation, deduplication, and relevance retrieval of student learning context."""

    def __init__(self, db=None):
        self.db = db if db is not None else get_database()

    async def store_or_update_context(
        self,
        user_id: str,
        context_type: str,
        key: str,
        value: str,
        project_id: Optional[str] = None,
        importance: float = 1.0,
        source: str = "SYSTEM",
        confidence: float = 1.0,
        metadata: Optional[Dict[str, Any]] = None
    ) -> LearningContextModel:
        """Stores or updates a persistent learning context item."""
        if self.db is None:
            raise RuntimeError("Database not initialized")

        query = {"user_id": user_id, "key": key, "context_type": context_type}
        if project_id is not None:
            query["project_id"] = project_id
        else:
            query["project_id"] = None

        existing = await self.db["learning_contexts"].find_one(query)
        now = datetime.now(timezone.utc)

        if existing:
            update_data = {
                "value": value,
                "importance": max(existing.get("importance", 1.0), importance),
                "confidence": confidence,
                "last_updated": now,
                "metadata": metadata or existing.get("metadata", {})
            }
            await self.db["learning_contexts"].update_one(
                {"_id": existing["_id"]},
                {"$set": update_data}
            )
            existing.update(update_data)
            existing["id"] = str(existing["_id"])
            return LearningContextModel(**existing)

        new_doc = LearningContextModel(
            user_id=user_id,
            project_id=project_id,
            context_type=context_type,
            key=key,
            value=value,
            importance=importance,
            source=source,
            confidence=confidence,
            first_seen=now,
            last_updated=now,
            metadata=metadata or {}
        )
        doc_dict = new_doc.model_dump(by_alias=True, exclude={"id"})
        res = await self.db["learning_contexts"].insert_one(doc_dict)
        new_doc.id = str(res.inserted_id)
        return new_doc

    async def retrieve_relevant_context(
        self,
        user_id: str,
        project_id: str,
        query: Optional[str] = None,
        limit: int = 5
    ) -> List[LearningContextModel]:
        """
        Retrieves relevant persistent learning context for a user and project.
        Filters project-scoped or global context.
        Matches keywords in query if query is provided.
        """
        if self.db is None:
            return []

        # Find items for this user matching current project OR global
        filter_query = {
            "user_id": user_id,
            "$or": [
                {"project_id": project_id},
                {"project_id": None}
            ]
        }

        cursor = self.db["learning_contexts"].find(filter_query).sort("importance", -1)
        if hasattr(cursor, "to_list"):
            raw_items = await cursor.to_list(length=50)
        else:
            raw_items = [doc async for doc in cursor]


        results = []
        query_words = set(query.lower().split()) if query else set()

        for item in raw_items:
            item_copy = dict(item)
            if "_id" in item_copy:
                item_copy["_id"] = str(item_copy["_id"])
            model = LearningContextModel(**item_copy)

            
            # Simple keyword relevance scoring if query is provided
            if query_words:
                text_content = f"{model.key} {model.value}".lower()
                matching = any(word in text_content for word in query_words if len(word) > 2)
                # Always include severe weaknesses or direct query matches
                if matching or model.context_type in ["WEAKNESS", "REPEATED_MISTAKE"]:
                    results.append(model)
            else:
                results.append(model)

            if len(results) >= limit:
                break

        return results
