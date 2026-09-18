"""
Centralized Event Publisher & Reader Service.

Provides:
- publish_event (creates and stores ActivityEventModel with correlation_id assignment)
- get_events_by_project (retrieves chronological events for a project with security & pagination)
- get_event_by_id (retrieves single event by ID with security checks)
"""
import uuid
import logging
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List, Tuple

from bson import ObjectId
from app.db.database import get_database
from app.models.event import ActivityEventModel
from app.schemas.events import ActivityEventResponse
from app.services.project_service import get_project

logger = logging.getLogger(__name__)


def _doc_to_event_response(doc: dict) -> ActivityEventResponse:
    return ActivityEventResponse(
        id=str(doc["_id"]),
        event_type=doc["event_type"],
        user_id=str(doc["user_id"]),
        project_id=str(doc["project_id"]),
        space_id=str(doc["space_id"]) if doc.get("space_id") else None,
        entity_type=doc.get("entity_type", "project"),
        entity_id=str(doc.get("entity_id", "")),
        payload=doc.get("payload", {}),
        correlation_id=doc.get("correlation_id", ""),
        status=doc.get("status", "PROCESSED"),
        attempts=doc.get("attempts", 1),
        created_at=doc.get("created_at"),
        processed_at=doc.get("processed_at"),
        timestamp=doc.get("timestamp") or doc.get("created_at"),
    )


async def publish_event(
    event_type: str,
    user_id: str,
    project_id: str,
    entity_id: Optional[str] = None,
    entity_type: str = "project",
    space_id: Optional[str] = None,
    payload: Optional[Dict[str, Any]] = None,
    correlation_id: Optional[str] = None,
    source_component: str = "system",
    db=None,
) -> dict:
    """
    Centralized function to validate, store, and publish application activity events.
    Assigns or preserves correlation_id for end-to-end learning workflow tracing.
    Returns plain dict representation with 'id' and 'correlation_id'.
    """
    db_conn = db if db is not None else get_database()
    if db_conn is None:
        logger.error("Database connection missing when publishing event")
        raise RuntimeError("Database connection not available")

    corr_id = correlation_id or f"corr_{uuid.uuid4().hex}"
    now = datetime.now(timezone.utc)
    actual_entity_id = entity_id or project_id

    event_model = ActivityEventModel(
        event_type=event_type,
        user_id=user_id,
        project_id=project_id,
        space_id=space_id,
        entity_type=entity_type,
        entity_id=actual_entity_id,
        payload=payload or {},
        correlation_id=corr_id,
        status="PROCESSED",
        attempts=1,
        created_at=now,
        processed_at=now,
    )

    doc_dict = event_model.model_dump(by_alias=True, exclude=["id"])
    doc_dict["source_component"] = source_component
    res = await db_conn["events"].insert_one(doc_dict)
    event_id_str = str(res.inserted_id)

    logger.info(
        f"[EVENT_PUBLISHED] event_type={event_type} user_id={user_id} "
        f"project_id={project_id} event_id={event_id_str} correlation_id={corr_id}"
    )

    doc_dict["id"] = event_id_str
    doc_dict["_id"] = event_id_str
    return doc_dict


async def get_events_by_project(
    project_id: str,
    user_id: str,
    event_type: Optional[str] = None,
    correlation_id: Optional[str] = None,
    limit: int = 50,
    skip: int = 0,
) -> Tuple[List[ActivityEventResponse], int]:
    """Retrieve chronological event stream for a project with optional filters and security check."""
    await get_project(project_id, user_id)
    db = get_database()

    query = {"project_id": project_id, "user_id": user_id}
    if event_type:
        query["event_type"] = event_type
    if correlation_id:
        query["correlation_id"] = correlation_id

    total = await db["events"].count_documents(query)
    cursor = (
        db["events"]
        .find(query)
        .sort("created_at", -1)
        .skip(skip)
        .limit(limit)
    )

    events = [_doc_to_event_response(doc) async for doc in cursor]
    return events, total


async def get_event_by_id(
    project_id: str,
    event_id: str,
    user_id: str,
) -> ActivityEventResponse:
    """Retrieve a single event by ID with ownership verification."""
    await get_project(project_id, user_id)
    db = get_database()

    if not ObjectId.is_valid(event_id):
        raise ValueError("not_found")

    doc = await db["events"].find_one({
        "_id": ObjectId(event_id),
        "project_id": project_id,
        "user_id": user_id,
    })

    if not doc:
        raise ValueError("not_found")

    return _doc_to_event_response(doc)
