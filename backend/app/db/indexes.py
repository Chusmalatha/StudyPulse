"""
Database index setup — call once at application startup.
"""
import logging
from app.db.database import get_database

logger = logging.getLogger(__name__)


async def create_indexes():
    """Ensure required database indexes exist."""
    db = get_database()
    if db is None:
        logger.warning("Database not connected — skipping index creation.")
        return

    try:
        # Unique index on users.email
        await db["users"].create_index("email", unique=True)
        
        # Indexes on spaces collection
        await db["spaces"].create_index([("user_id", 1)])

        # Indexes on projects collection
        await db["projects"].create_index([("user_id", 1)])
        await db["projects"].create_index([("space_id", 1)])
        await db["projects"].create_index([("space_id", 1), ("user_id", 1)])

        # Indexes on materials collection
        await db["materials"].create_index([("project_id", 1)])
        await db["materials"].create_index([("user_id", 1)])
        await db["materials"].create_index([("status", 1)])
        await db["materials"].create_index([("project_id", 1), ("user_id", 1)])

        # Indexes on chunks collection
        await db["chunks"].create_index([("project_id", 1)])
        await db["chunks"].create_index([("material_id", 1)])
        await db["chunks"].create_index([("material_id", 1), ("chunk_index", 1)])

        # Indexes on background_jobs collection
        await db["background_jobs"].create_index([("material_id", 1)])
        await db["background_jobs"].create_index([("project_id", 1)])
        await db["background_jobs"].create_index([("status", 1)])

        # Indexes on concepts, topics, sections collections
        await db["concepts"].create_index([("project_id", 1)])
        await db["concepts"].create_index([("project_id", 1), ("name", 1)])

        await db["topics"].create_index([("project_id", 1)])
        await db["topics"].create_index([("project_id", 1), ("name", 1)])

        await db["sections"].create_index([("project_id", 1)])
        await db["sections"].create_index([("project_id", 1), ("material_id", 1)])

        # Indexes on conversations & messages collections
        await db["conversations"].create_index([("project_id", 1)])
        await db["conversations"].create_index([("project_id", 1), ("user_id", 1)])
        await db["conversations"].create_index([("project_id", 1), ("updated_at", -1)])

        await db["messages"].create_index([("conversation_id", 1)])
        await db["messages"].create_index([("conversation_id", 1), ("created_at", 1)])
        await db["messages"].create_index([("project_id", 1)])

        # Indexes on assessment collections
        await db["assessments"].create_index([("project_id", 1)])
        await db["assessments"].create_index([("project_id", 1), ("user_id", 1)])
        await db["assessments"].create_index([("project_id", 1), ("created_at", -1)])

        await db["quiz_questions"].create_index([("assessment_id", 1)])
        await db["quiz_questions"].create_index([("project_id", 1)])
        await db["quiz_questions"].create_index([("assessment_id", 1), ("order_index", 1)])

        await db["question_attempts"].create_index([("assessment_id", 1)])
        await db["question_attempts"].create_index([("question_id", 1)])
        await db["question_attempts"].create_index([("project_id", 1), ("user_id", 1)])

        # Indexes on mastery & context collections (Phase 7)
        await db["mastery_events"].create_index([("concept_id", 1)])
        await db["mastery_events"].create_index([("project_id", 1)])
        await db["mastery_events"].create_index([("evidence_id", 1)])

        await db["repeated_mistakes"].create_index([("concept_id", 1)])
        await db["repeated_mistakes"].create_index([("project_id", 1), ("user_id", 1)])
        await db["repeated_mistakes"].create_index([("project_id", 1), ("concept_id", 1)])

        await db["learning_contexts"].create_index([("user_id", 1)])
        await db["learning_contexts"].create_index([("user_id", 1), ("project_id", 1)])
        await db["learning_contexts"].create_index([("user_id", 1), ("context_type", 1)])

        # Indexes on growth & recommendations collections (Phase 8)
        await db["growth_snapshots"].create_index([("project_id", 1), ("user_id", 1)])
        await db["growth_snapshots"].create_index([("concept_id", 1)])

        await db["recommendations"].create_index([("project_id", 1), ("user_id", 1)])
        await db["recommendations"].create_index([("project_id", 1), ("status", 1)])
        await db["recommendations"].create_index([("concept_id", 1)])

        # Indexes on events collection (Phase 9)
        await db["events"].create_index([("project_id", 1), ("user_id", 1)])
        await db["events"].create_index([("project_id", 1), ("created_at", -1)])
        await db["events"].create_index([("correlation_id", 1)])
        await db["events"].create_index([("event_type", 1)])

        logger.info("Database indexes verified.")
    except Exception as exc:
        logger.error(f"Failed to create indexes: {exc}")


