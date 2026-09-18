"""
Project business-logic service.
All Project database operations live here; routes stay thin.

Authorization strategy:
  Every query includes user_id (and space_id where relevant).
  MongoDB query itself enforces ownership — no separate permission check needed.
  Both "not found" and "unauthorized" return 404 to avoid data leakage.
"""
import logging
from datetime import datetime, timezone
from typing import List

from bson import ObjectId
from bson.errors import InvalidId

from app.db.database import get_database
from app.schemas.projects import ProjectCreate, ProjectUpdate, ProjectResponse

logger = logging.getLogger(__name__)


def _oid(value: str) -> ObjectId:
    try:
        return ObjectId(value)
    except (InvalidId, Exception):
        raise ValueError(f"Invalid ID: '{value}'")


def _doc_to_project_response(doc: dict) -> ProjectResponse:
    return ProjectResponse(
        id=str(doc["_id"]),
        space_id=str(doc["space_id"]),
        user_id=str(doc["user_id"]),
        name=doc["name"],
        description=doc.get("description", ""),
        learning_goal=doc.get("learning_goal", ""),
        created_at=doc.get("created_at"),
        updated_at=doc.get("updated_at"),
    )


async def _assert_space_owned(db, space_id: str, user_id: str) -> None:
    """Raise ValueError('not_found') if the space doesn't exist or isn't owned by user."""
    space = await db["spaces"].find_one({"_id": _oid(space_id), "user_id": user_id})
    if not space:
        raise ValueError("not_found")


async def create_project(space_id: str, user_id: str, data: ProjectCreate) -> ProjectResponse:
    """
    Create a Project inside a Space.
    Validates space ownership before creating.
    """
    db = get_database()
    await _assert_space_owned(db, space_id, user_id)

    now = datetime.now(timezone.utc)
    doc = {
        "space_id": space_id,
        "user_id": user_id,
        "name": data.name,
        "description": data.description,
        "learning_goal": data.learning_goal,
        "created_at": now,
        "updated_at": now,
    }
    result = await db["projects"].insert_one(doc)
    doc["_id"] = result.inserted_id
    logger.info(f"Project created: '{data.name}' in space {space_id} by user {user_id}")
    return _doc_to_project_response(doc)


async def get_projects(space_id: str, user_id: str) -> List[ProjectResponse]:
    """
    Return all Projects in a Space owned by user_id.
    Validates space ownership first.
    """
    db = get_database()
    await _assert_space_owned(db, space_id, user_id)
    cursor = db["projects"].find({"space_id": space_id, "user_id": user_id}).sort("created_at", -1)
    return [_doc_to_project_response(doc) async for doc in cursor]


async def get_project(project_id: str, user_id: str) -> ProjectResponse:
    """
    Return a Project by ID after ownership validation.
    Does NOT require space_id — for standalone project access.
    """
    db = get_database()
    doc = await db["projects"].find_one({"_id": _oid(project_id), "user_id": user_id})
    if not doc:
        raise ValueError("not_found")
    return _doc_to_project_response(doc)


async def get_project_in_space(project_id: str, space_id: str, user_id: str) -> ProjectResponse:
    """
    Return a Project validating BOTH ownership AND space membership.
    Use this for nested routes: /spaces/{space_id}/projects/{project_id}
    """
    db = get_database()
    await _assert_space_owned(db, space_id, user_id)
    doc = await db["projects"].find_one({
        "_id": _oid(project_id),
        "space_id": space_id,
        "user_id": user_id,
    })
    if not doc:
        raise ValueError("not_found")
    return _doc_to_project_response(doc)


async def update_project(project_id: str, user_id: str, data: ProjectUpdate) -> ProjectResponse:
    """Update a Project. Only non-None fields are changed."""
    db = get_database()
    updates = {k: v for k, v in data.model_dump(exclude_none=True).items()}
    if not updates:
        return await get_project(project_id, user_id)

    updates["updated_at"] = datetime.now(timezone.utc)
    result = await db["projects"].find_one_and_update(
        {"_id": _oid(project_id), "user_id": user_id},
        {"$set": updates},
        return_document=True,
    )
    if not result:
        raise ValueError("not_found")
    return _doc_to_project_response(result)


async def delete_project(project_id: str, user_id: str) -> None:
    """Delete a Project owned by user_id and cascade delete materials, files, chunks, and background jobs."""
    db = get_database()
    project = await db["projects"].find_one({"_id": _oid(project_id), "user_id": user_id})
    if not project:
        raise ValueError("not_found")

    # 1. Cascade delete associated materials and their physical files
    import os
    cursor = db["materials"].find({"project_id": project_id, "user_id": user_id})
    async for mat in cursor:
        file_path = mat.get("file_path")
        if file_path and os.path.exists(file_path):
            try:
                os.remove(file_path)
            except Exception as exc:
                logger.warning(f"Failed to remove material file '{file_path}': {exc}")

    await db["materials"].delete_many({"project_id": project_id, "user_id": user_id})
    await db["chunks"].delete_many({"project_id": project_id})
    await db["background_jobs"].delete_many({"project_id": project_id, "user_id": user_id})
    await db["concepts"].delete_many({"project_id": project_id})
    await db["topics"].delete_many({"project_id": project_id})
    await db["sections"].delete_many({"project_id": project_id})
    await db["conversations"].delete_many({"project_id": project_id, "user_id": user_id})
    await db["messages"].delete_many({"project_id": project_id})
    await db["assessments"].delete_many({"project_id": project_id, "user_id": user_id})
    await db["quiz_questions"].delete_many({"project_id": project_id})
    await db["question_attempts"].delete_many({"project_id": project_id})
    await db["mastery_events"].delete_many({"project_id": project_id, "user_id": user_id})
    await db["repeated_mistakes"].delete_many({"project_id": project_id, "user_id": user_id})
    await db["learning_contexts"].delete_many({"project_id": project_id, "user_id": user_id})
    await db["growth_snapshots"].delete_many({"project_id": project_id, "user_id": user_id})
    await db["recommendations"].delete_many({"project_id": project_id, "user_id": user_id})
    await db["events"].delete_many({"project_id": project_id, "user_id": user_id})

    # 2. Delete project document
    await db["projects"].delete_one({"_id": _oid(project_id), "user_id": user_id})
    logger.info(f"Project deleted: {project_id} by user {user_id}")



