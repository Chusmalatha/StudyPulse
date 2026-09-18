"""
Background Learning Workflows and Event Handlers.
"""
import logging
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
from bson import ObjectId

from app.db.database import get_database
from app.models.job import JobStatus
from app.services.event_publisher import publish_event
from app.services.mastery_service import MasteryService
from app.services.learning_context_service import LearningContextService
from app.services.growth_analysis_service import GrowthAnalysisService
from app.services.recommendation_service import RecommendationService

logger = logging.getLogger(__name__)

MAX_WORKFLOW_RETRIES = 3


class QuizCompletedWorkflow:
    @staticmethod
    async def run_workflow(
        project_id: str,
        user_id: str,
        assessment_id: str,
        event_id: str,
        correlation_id: Optional[str] = None,
        db=None,
    ) -> Dict[str, Any]:
        """
        Background learning workflow triggered upon quiz completion.
        Orchestrates:
        1. Finalize Assessment
        2. Update Mastery
        3. Detect Mistakes
        4. Update Context
        5. Analyze Growth
        6. Generate Recommendations
        Enforces idempotency, safe retries, and failure isolation.
        """
        db_conn = db if db is not None else get_database()
        if db_conn is None:
            logger.warning("Database not connected for background workflow.")
            return {"status": JobStatus.FAILED.value, "reason": "No DB connection"}

        corr_id = correlation_id or f"corr_{event_id}"
        now = datetime.now(timezone.utc)

        # 1. Idempotency Check: check if already fully executed for this event_id
        existing_job = await db_conn["background_jobs"].find_one({
            "event_id": event_id,
            "job_type": "QUIZ_COMPLETED_WORKFLOW",
            "status": JobStatus.COMPLETED.value,
        })
        if existing_job:
            logger.info(f"[WORKFLOW_SKIP] Quiz completion workflow for event_id={event_id} already executed.")
            return {
                "status": JobStatus.COMPLETED.value,
                "event_id": event_id,
                "correlation_id": corr_id,
                "skipped": True,
                "completed_steps": existing_job.get("completed_steps", []),
            }

        # Create or update BackgroundJob tracking doc
        job_doc = {
            "job_type": "QUIZ_COMPLETED_WORKFLOW",
            "event_id": event_id,
            "correlation_id": corr_id,
            "project_id": project_id,
            "user_id": user_id,
            "status": JobStatus.PROCESSING.value,
            "attempts": 1,
            "max_attempts": MAX_WORKFLOW_RETRIES,
            "started_at": now,
            "created_at": now,
            "updated_at": now,
        }
        await db_conn["background_jobs"].update_one(
            {"event_id": event_id, "job_type": "QUIZ_COMPLETED_WORKFLOW"},
            {"$set": job_doc},
            upsert=True,
        )

        completed_steps = []

        try:
            # Step 1: Finalize Assessment
            completed_steps.append("FINALIZE_ASSESSMENT")

            # Step 2: Fetch attempts & Update Mastery
            attempts_cursor = db_conn["question_attempts"].find({
                "assessment_id": assessment_id,
                "project_id": project_id,
            })
            attempts = [a async for a in attempts_cursor]

            mastery_svc = MasteryService(db_conn)
            has_mistakes = False

            for att in attempts:
                att_id_str = str(att["_id"])
                is_corr = att.get("is_correct", False)
                q_type = att.get("question_type", "MCQ")
                if not is_corr:
                    has_mistakes = True

                for c_id in att.get("concept_ids", []):
                    await mastery_svc.update_mastery(
                        user_id=user_id,
                        project_id=project_id,
                        concept_id=c_id,
                        evidence_type=q_type,
                        evidence_id=att_id_str,
                        is_correct=is_corr,
                        difficulty=1.0,
                        reason=f"Workflow processing attempt {att_id_str}",
                    )

            await publish_event(
                event_type="MASTERY_UPDATED",
                user_id=user_id,
                project_id=project_id,
                entity_type="assessment",
                entity_id=assessment_id,
                payload={"concepts_updated_count": len(attempts)},
                correlation_id=corr_id,
                source_component="quiz_completed_workflow",
                db=db_conn,
            )
            completed_steps.append("UPDATE_MASTERY")

            # Step 3: Emit mistake detection
            if has_mistakes:
                await publish_event(
                    event_type="REPEATED_MISTAKE_DETECTED",
                    user_id=user_id,
                    project_id=project_id,
                    entity_type="assessment",
                    entity_id=assessment_id,
                    payload={"assessment_id": assessment_id},
                    correlation_id=corr_id,
                    source_component="quiz_completed_workflow",
                    db=db_conn,
                )
            completed_steps.append("DETECT_MISTAKES")

            # Step 4: Update Learning Context
            ctx_svc = LearningContextService(db_conn)
            await ctx_svc.store_or_update_context(
                user_id=user_id,
                project_id=project_id,
                context_type="ASSESSMENT_PATTERN",
                key=f"assessment_{assessment_id}",
                value=f"Completed practice assessment with {len(attempts)} questions.",
                importance=1.2,
                source="ASSESSMENT_WORKFLOW",
            )
            await publish_event(
                event_type="LEARNING_CONTEXT_UPDATED",
                user_id=user_id,
                project_id=project_id,
                entity_type="assessment",
                entity_id=assessment_id,
                payload={"assessment_id": assessment_id},
                correlation_id=corr_id,
                source_component="quiz_completed_workflow",
                db=db_conn,
            )
            completed_steps.append("UPDATE_CONTEXT")

            # Step 5: Failure-Isolated Growth Analysis
            growth_overall = 0.0
            try:
                growth_svc = GrowthAnalysisService(db_conn)
                snapshot = await growth_svc.analyze_project_growth(project_id, user_id)
                growth_overall = snapshot.overall_mastery if snapshot else 0.0
                await publish_event(
                    event_type="GROWTH_ANALYZED",
                    user_id=user_id,
                    project_id=project_id,
                    entity_type="project",
                    entity_id=project_id,
                    payload={"assessment_id": assessment_id, "overall_mastery": growth_overall},
                    correlation_id=corr_id,
                    source_component="quiz_completed_workflow",
                    db=db_conn,
                )
                completed_steps.append("ANALYZE_GROWTH")
            except Exception as g_exc:
                logger.error(f"[WORKFLOW_ISOLATED_ERROR] Growth analysis failed: {g_exc}")

            # Step 6: Failure-Isolated Recommendation Generation
            try:
                rec_svc = RecommendationService(db_conn)
                recs = await rec_svc.generate_recommendations(project_id, user_id)
                rec_title = recs[0].title if recs else "Study Next"
                await publish_event(
                    event_type="RECOMMENDATION_CREATED",
                    user_id=user_id,
                    project_id=project_id,
                    entity_type="project",
                    entity_id=project_id,
                    payload={"assessment_id": assessment_id, "recommendation_title": rec_title},
                    correlation_id=corr_id,
                    source_component="quiz_completed_workflow",
                    db=db_conn,
                )
                completed_steps.append("GENERATE_RECOMMENDATIONS")
            except Exception as r_exc:
                logger.error(f"[WORKFLOW_ISOLATED_ERROR] Recommendation generation failed: {r_exc}")

            # Mark BackgroundJob COMPLETED
            completed_at = datetime.now(timezone.utc)
            await db_conn["background_jobs"].update_one(
                {"event_id": event_id, "job_type": "QUIZ_COMPLETED_WORKFLOW"},
                {
                    "$set": {
                        "status": JobStatus.COMPLETED.value,
                        "completed_at": completed_at,
                        "updated_at": completed_at,
                        "completed_steps": completed_steps,
                    }
                },
            )

            logger.info(f"[WORKFLOW_COMPLETE] event_id={event_id} corr_id={corr_id} steps={completed_steps}")
            return {
                "status": JobStatus.COMPLETED.value,
                "event_id": event_id,
                "correlation_id": corr_id,
                "completed_steps": completed_steps,
            }

        except Exception as exc:
            logger.error(f"[WORKFLOW_FAILED] event_id={event_id} error={exc}")
            failed_at = datetime.now(timezone.utc)
            await db_conn["background_jobs"].update_one(
                {"event_id": event_id, "job_type": "QUIZ_COMPLETED_WORKFLOW"},
                {
                    "$set": {
                        "status": JobStatus.FAILED.value,
                        "last_error": str(exc),
                        "updated_at": failed_at,
                        "completed_steps": completed_steps,
                    }
                },
            )
            return {
                "status": JobStatus.FAILED.value,
                "event_id": event_id,
                "correlation_id": corr_id,
                "error": str(exc),
                "completed_steps": completed_steps,
            }


async def execute_quiz_completion_workflow(
    assessment_id: str,
    project_id: str,
    user_id: str,
    correlation_id: str,
    db=None,
) -> Dict[str, Any]:
    return await QuizCompletedWorkflow.run_workflow(
        project_id=project_id,
        user_id=user_id,
        assessment_id=assessment_id,
        event_id=f"event_{assessment_id}",
        correlation_id=correlation_id,
        db=db,
    )
