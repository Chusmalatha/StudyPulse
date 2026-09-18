"""
Assessment Business Logic Service.

Handles:
- Assessment creation, state management, progress persistence
- Question answering (MCQ deterministic checking vs Open-Ended qualitative evaluation)
- Results aggregation and completion
"""
import logging
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any

from fastapi import HTTPException, status, BackgroundTasks
from bson import ObjectId

from app.db.database import get_database
from app.models.assessment import AssessmentModel, AssessmentStatus
from app.models.quiz_question import QuizQuestionModel, QuestionType, QuestionDifficulty
from app.models.question_attempt import QuestionAttemptModel
from app.schemas.assessment import (
    AssessmentResponseSchema,
    QuizQuestionPublicSchema,
    QuizQuestionDetailSchema,
    QuestionResultResponseSchema,
    OpenEndedEvaluationSchema,
)
from app.services.project_service import get_project
from app.services.adaptive_assessment_service import (
    select_adaptive_target_concepts,
    generate_grounded_question,
    evaluate_open_ended_answer,
)

logger = logging.getLogger(__name__)


def _doc_to_public_question(doc: dict) -> QuizQuestionPublicSchema:
    raw_refs = doc.get("source_references", [])
    refs = [
        {
            "material_id": r.get("material_id", ""),
            "filename": r.get("filename", ""),
            "page_number": r.get("page_number", 1),
            "chunk_id": r.get("chunk_id", ""),
            "relevance_score": r.get("relevance_score", 0.0),
        }
        for r in raw_refs
    ]
    return QuizQuestionPublicSchema(
        id=str(doc["_id"]),
        assessment_id=str(doc["assessment_id"]),
        project_id=str(doc["project_id"]),
        concept_names=doc.get("concept_names", []),
        question_type=doc.get("question_type", "MCQ"),
        question_text=doc.get("question_text", ""),
        options=doc.get("options"),
        difficulty=doc.get("difficulty", "MEDIUM"),
        order_index=doc.get("order_index", 0),
        source_references=refs,
    )


def _doc_to_assessment_response(doc: dict, questions: List[dict] = None) -> AssessmentResponseSchema:
    pub_questions = [_doc_to_public_question(q) for q in (questions or [])]
    return AssessmentResponseSchema(
        id=str(doc["_id"]),
        project_id=str(doc["project_id"]),
        user_id=str(doc["user_id"]),
        title=doc.get("title", "Adaptive Practice Quiz"),
        status=doc.get("status", "IN_PROGRESS"),
        question_count=doc.get("question_count", 5),
        current_question_index=doc.get("current_question_index", 0),
        score_mcq=doc.get("score_mcq"),
        started_at=doc.get("started_at"),
        completed_at=doc.get("completed_at"),
        created_at=doc.get("created_at"),
        updated_at=doc.get("updated_at"),
        questions=pub_questions,
    )


async def create_assessment(
    project_id: str,
    user_id: str,
    question_count: int = 5,
    target_concept_id: Optional[str] = None,
    background_tasks: Optional[BackgroundTasks] = None,
) -> AssessmentResponseSchema:
    """
    Create a new Adaptive Assessment for a project.
    Validates material readiness, selects adaptive target concepts (or target concept), generates questions,
    and returns initial assessment object.
    """
    await get_project(project_id, user_id)
    db = get_database()

    # Verify READY materials exist
    ready_mat = await db["materials"].find_one({"project_id": project_id, "status": "READY"})
    if not ready_mat:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Project has no processed learning materials yet. Upload and process a PDF material first.",
        )

    # Resolve target concept if target_concept_id is provided
    target_concept_doc = None
    quiz_title = "Adaptive Practice Quiz"
    if target_concept_id:
        import re as _re
        c_doc = None
        if ObjectId.is_valid(target_concept_id):
            c_doc = await db["concepts"].find_one({"_id": ObjectId(target_concept_id), "project_id": project_id})
        if not c_doc:
            escaped_name = _re.escape(target_concept_id.strip())
            c_doc = await db["concepts"].find_one({
                "project_id": project_id,
                "name": {"$regex": f"^{escaped_name}$", "$options": "i"}
            })
        if c_doc:
            target_concept_doc = c_doc
            quiz_title = f"Practice Quiz: {c_doc.get('name', 'Concept')}"

    now = datetime.now(timezone.utc)
    ass_model = AssessmentModel(
        project_id=project_id,
        user_id=user_id,
        title=quiz_title,
        status=AssessmentStatus.IN_PROGRESS,
        question_count=question_count,
        current_question_index=0,
        started_at=now,
        created_at=now,
        updated_at=now,
    )
    doc = ass_model.model_dump(by_alias=True, exclude=["id"])
    result = await db["assessments"].insert_one(doc)
    assessment_id = str(result.inserted_id)

    # 2. Select Adaptive Target Concepts
    if target_concept_doc:
        difficulties = [QuestionDifficulty.EASY, QuestionDifficulty.MEDIUM, QuestionDifficulty.MEDIUM, QuestionDifficulty.HARD, QuestionDifficulty.HARD]
        targets = [(target_concept_doc, difficulties[i % len(difficulties)]) for i in range(question_count)]
    else:
        targets = await select_adaptive_target_concepts(project_id, user_id, requested_count=question_count)

    generated_question_docs: List[dict] = []
    
    # Alternate MCQ and OPEN_ENDED types for balanced assessment
    for idx, (concept_dict, difficulty) in enumerate(targets):
        q_type = QuestionType.MCQ if idx % 2 == 0 else QuestionType.OPEN_ENDED
        q_model = await generate_grounded_question(
            project_id=project_id,
            user_id=user_id,
            assessment_id=assessment_id,
            target_concept=concept_dict,
            difficulty=difficulty,
            question_type=q_type,
            order_index=idx,
        )
        if q_model:
            q_dict = q_model.model_dump(by_alias=True, exclude=["id"])
            res_q = await db["quiz_questions"].insert_one(q_dict)
            q_dict["_id"] = res_q.inserted_id
            generated_question_docs.append(q_dict)

    if not generated_question_docs:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate assessment questions from project material.",
        )

    doc["_id"] = result.inserted_id

    # Event publishing: QUIZ_STARTED
    try:
        from app.services.event_publisher import publish_event
        await publish_event(
            project_id=project_id,
            user_id=user_id,
            event_type="QUIZ_STARTED",
            payload={
                "assessment_id": assessment_id,
                "question_count": len(generated_question_docs),
                "title": doc.get("title"),
            },
            source_component="assessment_service",
        )
    except Exception as ev_err:
        logger.warning(f"Failed to publish QUIZ_STARTED event: {ev_err}")

    return _doc_to_assessment_response(doc, generated_question_docs)


async def list_assessments(
    project_id: str,
    user_id: str,
) -> List[AssessmentResponseSchema]:
    """List all assessments for a project owned by user."""
    await get_project(project_id, user_id)
    db = get_database()

    cursor = db["assessments"].find(
        {"project_id": project_id, "user_id": user_id}
    ).sort("created_at", -1)

    assessments = []
    async for a_doc in cursor:
        ass_id = str(a_doc["_id"])
        q_cursor = db["quiz_questions"].find({"assessment_id": ass_id}).sort("order_index", 1)
        q_docs = [q async for q in q_cursor]
        if q_docs:
            assessments.append(_doc_to_assessment_response(a_doc, q_docs))

    return assessments


async def get_assessment(
    project_id: str,
    assessment_id: str,
    user_id: str,
) -> AssessmentResponseSchema:
    """Get single assessment details."""
    await get_project(project_id, user_id)
    db = get_database()

    if not ObjectId.is_valid(assessment_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Assessment not found")

    a_doc = await db["assessments"].find_one({
        "_id": ObjectId(assessment_id),
        "project_id": project_id,
        "user_id": user_id,
    })
    if not a_doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Assessment not found")

    q_cursor = db["quiz_questions"].find({"assessment_id": assessment_id}).sort("order_index", 1)
    q_docs = [q async for q in q_cursor]

    return _doc_to_assessment_response(a_doc, q_docs)


async def answer_question(
    project_id: str,
    assessment_id: str,
    question_id: str,
    user_id: str,
    student_answer: str,
) -> QuestionResultResponseSchema:
    """
    Process answer submission for an MCQ or Open-Ended question.
    - MCQ: Compares against stored correct_answer deterministically.
    - Open-Ended: Calls LLM qualitative evaluator.
    - Persists QuestionAttemptModel and updates assessment progress.
    """
    await get_project(project_id, user_id)
    db = get_database()

    # Validate assessment & question ownership
    if not ObjectId.is_valid(assessment_id) or not ObjectId.is_valid(question_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Question or assessment not found")

    ass_doc = await db["assessments"].find_one({
        "_id": ObjectId(assessment_id),
        "project_id": project_id,
        "user_id": user_id,
    })
    if not ass_doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Assessment not found")

    q_doc = await db["quiz_questions"].find_one({
        "_id": ObjectId(question_id),
        "project_id": project_id,
    })
    if not q_doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Question not found")

    q_doc_copy = dict(q_doc)
    q_doc_copy["_id"] = str(q_doc_copy["_id"])
    q_model = QuizQuestionModel(**q_doc_copy)
    clean_ans = student_answer.strip()
    now = datetime.now(timezone.utc)

    if q_model.question_type == QuestionType.MCQ:
        # Deterministic MCQ checking
        user_choice = clean_ans.upper()
        is_correct = (user_choice == (q_model.correct_answer or "").upper())

        att_model = QuestionAttemptModel(
            assessment_id=assessment_id,
            question_id=question_id,
            project_id=project_id,
            user_id=user_id,
            concept_ids=q_model.concept_ids,
            question_type=QuestionType.MCQ,
            difficulty=q_model.difficulty,
            student_answer=user_choice,
            is_correct=is_correct,
            evaluation=None,
            attempted_at=now,
        )
        att_dict = att_model.model_dump(by_alias=True, exclude=["id"])
        res_att = await db["question_attempts"].insert_one(att_dict)
        attempt_id_str = str(res_att.inserted_id)

        # Increment assessment question index
        await db["assessments"].update_one(
            {"_id": ObjectId(assessment_id)},
            {"$inc": {"current_question_index": 1}, "$set": {"updated_at": now}}
        )

        # Trigger Mastery Update for linked concepts (Phase 7)
        try:
            from app.services.mastery_service import MasteryService
            mastery_svc = MasteryService(db)
            diff_num = 1.0
            if q_model.difficulty == QuestionDifficulty.EASY:
                diff_num = 0.7
            elif q_model.difficulty == QuestionDifficulty.HARD:
                diff_num = 1.4

            for idx, c_id in enumerate(q_model.concept_ids):
                # Pass concept_name for fallback resolution when concept IDs are orphaned
                c_name = q_model.concept_names[idx] if idx < len(q_model.concept_names) else None
                mistake_desc = None if is_correct else f"Incorrect answer option '{user_choice}' selected on question: {q_model.question_text[:60]}..."
                await mastery_svc.update_mastery(
                    user_id=user_id,
                    project_id=project_id,
                    concept_id=c_id,
                    evidence_type="MCQ",
                    evidence_id=attempt_id_str,
                    is_correct=is_correct,
                    difficulty=diff_num,
                    mistake_description=mistake_desc,
                    concept_name=c_name
                )
        except Exception as exc:
            logger.error(f"Failed to update mastery on MCQ submission: {exc}")

        # Event publishing: QUESTION_ANSWERED
        try:
            from app.services.event_publisher import publish_event
            await publish_event(
                project_id=project_id,
                user_id=user_id,
                event_type="QUESTION_ANSWERED",
                payload={
                    "assessment_id": assessment_id,
                    "question_id": question_id,
                    "question_type": "MCQ",
                    "is_correct": is_correct,
                },
                source_component="assessment_service",
            )
        except Exception as ev_err:
            logger.warning(f"Failed to publish QUESTION_ANSWERED event: {ev_err}")

        return QuestionResultResponseSchema(
            attempt_id=attempt_id_str,
            question_id=question_id,
            question_type="MCQ",
            is_correct=is_correct,
            correct_answer=q_model.correct_answer,
            explanation=q_model.explanation,
            evaluation=None,
            attempted_at=now,
        )
    else:
        # Qualitative Open-Ended LLM evaluation
        eval_result = await evaluate_open_ended_answer(q_model, clean_ans, user_id=user_id)
        eval_dict = eval_result.model_dump()
        is_good = (eval_result.understanding.status == "GOOD")

        att_model = QuestionAttemptModel(
            assessment_id=assessment_id,
            question_id=question_id,
            project_id=project_id,
            user_id=user_id,
            concept_ids=q_model.concept_ids,
            question_type=QuestionType.OPEN_ENDED,
            difficulty=q_model.difficulty,
            student_answer=clean_ans,
            is_correct=is_good,
            evaluation=eval_dict,
            attempted_at=now,
        )
        att_dict = att_model.model_dump(by_alias=True, exclude=["id"])
        res_att = await db["question_attempts"].insert_one(att_dict)
        attempt_id_str = str(res_att.inserted_id)

        # Increment assessment question index
        await db["assessments"].update_one(
            {"_id": ObjectId(assessment_id)},
            {"$inc": {"current_question_index": 1}, "$set": {"updated_at": now}}
        )

        # Trigger Mastery Update for linked concepts (Phase 7)
        try:
            from app.services.mastery_service import MasteryService
            mastery_svc = MasteryService(db)
            diff_num = 1.0
            if q_model.difficulty == QuestionDifficulty.EASY:
                diff_num = 0.7
            elif q_model.difficulty == QuestionDifficulty.HARD:
                diff_num = 1.4

            qual_status = eval_result.understanding.status
            mistake_desc = None
            if not is_good and eval_result.areas_to_improve:
                mistake_desc = eval_result.areas_to_improve[0]

            for idx, c_id in enumerate(q_model.concept_ids):
                # Pass concept_name for fallback resolution when concept IDs are orphaned
                c_name = q_model.concept_names[idx] if idx < len(q_model.concept_names) else None
                await mastery_svc.update_mastery(
                    user_id=user_id,
                    project_id=project_id,
                    concept_id=c_id,
                    evidence_type="OPEN_ENDED",
                    evidence_id=attempt_id_str,
                    is_correct=is_good,
                    difficulty=diff_num,
                    qualitative_status=qual_status,
                    mistake_description=mistake_desc,
                    reason=f"Open-ended evaluation status: {qual_status}",
                    concept_name=c_name
                )
        except Exception as exc:
            logger.error(f"Failed to update mastery on Open-Ended submission: {exc}")

        # Event publishing: QUESTION_ANSWERED
        try:
            from app.services.event_publisher import publish_event
            await publish_event(
                project_id=project_id,
                user_id=user_id,
                event_type="QUESTION_ANSWERED",
                payload={
                    "assessment_id": assessment_id,
                    "question_id": question_id,
                    "question_type": "OPEN_ENDED",
                    "is_correct": is_good,
                },
                source_component="assessment_service",
            )
        except Exception as ev_err:
            logger.warning(f"Failed to publish QUESTION_ANSWERED event: {ev_err}")

        return QuestionResultResponseSchema(
            attempt_id=attempt_id_str,
            question_id=question_id,
            question_type="OPEN_ENDED",
            is_correct=is_good,
            correct_answer=None,
            explanation=q_model.explanation,
            evaluation=eval_result,
            attempted_at=now,
        )


async def complete_assessment(
    project_id: str,
    assessment_id: str,
    user_id: str,
    background_tasks: Optional[BackgroundTasks] = None,
) -> AssessmentResponseSchema:
    """Mark an assessment as COMPLETED and compute overall MCQ score."""
    await get_project(project_id, user_id)
    db = get_database()

    now = datetime.now(timezone.utc)
    attempts_cursor = db["question_attempts"].find({"assessment_id": assessment_id, "project_id": project_id})
    attempts = [a async for a in attempts_cursor]

    mcq_attempts = [a for a in attempts if a.get("question_type") == "MCQ"]
    score_mcq = None
    if mcq_attempts:
        correct_count = sum(1 for a in mcq_attempts if a.get("is_correct") is True)
        score_mcq = round((correct_count / len(mcq_attempts)) * 100, 1)

    await db["assessments"].update_one(
        {"_id": ObjectId(assessment_id), "project_id": project_id, "user_id": user_id},
        {"$set": {"status": AssessmentStatus.COMPLETED.value, "score_mcq": score_mcq, "completed_at": now, "updated_at": now}}
    )

    # Event publishing & Event-Driven Background Workflow Triggering (Phase 9)
    try:
        from app.services.event_publisher import publish_event
        from app.services.workflow_service import QuizCompletedWorkflow

        event_doc = await publish_event(
            project_id=project_id,
            user_id=user_id,
            event_type="QUIZ_COMPLETED",
            payload={
                "assessment_id": assessment_id,
                "score_mcq": score_mcq,
                "total_attempts": len(attempts),
            },
            source_component="assessment_service",
        )

        event_id = event_doc["id"]
        correlation_id = event_doc["correlation_id"]

        if background_tasks:
            background_tasks.add_task(
                QuizCompletedWorkflow.run_workflow,
                project_id=project_id,
                user_id=user_id,
                assessment_id=assessment_id,
                event_id=event_id,
                correlation_id=correlation_id,
            )
        else:
            # Inline fallback if BackgroundTasks context unavailable
            import asyncio
            asyncio.create_task(
                QuizCompletedWorkflow.run_workflow(
                    project_id=project_id,
                    user_id=user_id,
                    assessment_id=assessment_id,
                    event_id=event_id,
                    correlation_id=correlation_id,
                )
            )
    except Exception as ev_err:
        logger.warning(f"Failed to publish QUIZ_COMPLETED event or trigger workflow: {ev_err}")

    return await get_assessment(project_id, assessment_id, user_id)
