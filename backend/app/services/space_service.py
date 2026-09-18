"""
Space business-logic service.
All Space database operations live here; routes stay thin.

Authorization strategy:
  Every query includes `user_id` so MongoDB itself enforces ownership.
  A 404 is returned for both "not found" and "not owned" cases to avoid
  leaking the existence of other users' resources.
"""
import logging
from datetime import datetime, timezone
from typing import List

from bson import ObjectId
from bson.errors import InvalidId

from app.db.database import get_database
from app.schemas.spaces import SpaceCreate, SpaceUpdate, SpaceResponse

logger = logging.getLogger(__name__)


def _oid(value: str) -> ObjectId:
    """Convert a string to ObjectId, raising ValueError on invalid input."""
    try:
        return ObjectId(value)
    except (InvalidId, Exception):
        raise ValueError(f"Invalid ID: '{value}'")


def _doc_to_space_response(doc: dict, project_count: int = 0) -> SpaceResponse:
    """Convert a raw MongoDB document to a SpaceResponse."""
    return SpaceResponse(
        id=str(doc["_id"]),
        user_id=str(doc["user_id"]),
        name=doc["name"],
        description=doc.get("description", ""),
        project_count=project_count,
        created_at=doc.get("created_at"),
        updated_at=doc.get("updated_at"),
    )


async def create_space(user_id: str, data: SpaceCreate) -> SpaceResponse:
    """Create a new Space owned by user_id."""
    db = get_database()
    now = datetime.now(timezone.utc)
    doc = {
        "user_id": user_id,
        "name": data.name,
        "description": data.description,
        "created_at": now,
        "updated_at": now,
    }
    result = await db["spaces"].insert_one(doc)
    doc["_id"] = result.inserted_id
    logger.info(f"Space created: '{data.name}' by user {user_id}")
    return _doc_to_space_response(doc)


async def get_spaces(user_id: str) -> List[SpaceResponse]:
    """Return all Spaces belonging to user_id, with project counts."""
    db = get_database()
    cursor = db["spaces"].find({"user_id": user_id}).sort("created_at", -1)
    spaces = []
    async for doc in cursor:
        space_id_str = str(doc["_id"])
        count = await db["projects"].count_documents({"space_id": space_id_str, "user_id": user_id})
        spaces.append(_doc_to_space_response(doc, project_count=count))
    return spaces


async def get_space(space_id: str, user_id: str) -> SpaceResponse:
    """
    Return a single Space after ownership validation.
    Raises ValueError('not_found') if the space doesn't exist or isn't owned by user.
    """
    db = get_database()
    doc = await db["spaces"].find_one({"_id": _oid(space_id), "user_id": user_id})
    if not doc:
        raise ValueError("not_found")
    count = await db["projects"].count_documents({"space_id": space_id, "user_id": user_id})
    return _doc_to_space_response(doc, project_count=count)


async def update_space(space_id: str, user_id: str, data: SpaceUpdate) -> SpaceResponse:
    """Update a Space. Only fields explicitly provided are changed."""
    db = get_database()
    updates = {k: v for k, v in data.model_dump(exclude_none=True).items()}
    if not updates:
        # Nothing to update — just return the current space
        return await get_space(space_id, user_id)

    updates["updated_at"] = datetime.now(timezone.utc)
    result = await db["spaces"].find_one_and_update(
        {"_id": _oid(space_id), "user_id": user_id},
        {"$set": updates},
        return_document=True,
    )
    if not result:
        raise ValueError("not_found")
    count = await db["projects"].count_documents({"space_id": space_id, "user_id": user_id})
    return _doc_to_space_response(result, project_count=count)


async def delete_space(space_id: str, user_id: str) -> None:
    """
    Delete a Space and ALL its Projects (cascade).
    Raises ValueError('not_found') if not owned by user.
    """
    db = get_database()
    space = await db["spaces"].find_one({"_id": _oid(space_id), "user_id": user_id})
    if not space:
        raise ValueError("not_found")

    # Cascade: delete all projects in this space first
    del_result = await db["projects"].delete_many({"space_id": space_id, "user_id": user_id})
    logger.info(f"Deleted {del_result.deleted_count} projects from space {space_id}")

    await db["spaces"].delete_one({"_id": _oid(space_id), "user_id": user_id})
    logger.info(f"Space deleted: {space_id} by user {user_id}")
