"""
AI Evaluation Service.

Provides deterministic evaluation of Tutor responses, RAG retrieval accuracy, Quiz questions, and Recommendations.
"""
import logging
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional

from app.db.database import get_database
from app.models.ai_evaluation import AIEvaluationModel, AIEvaluationType

logger = logging.getLogger(__name__)


async def evaluate_tutor_response(
    user_id: str,
    project_id: str,
    message_id: str,
    answer: str,
    is_grounded: bool,
    is_unsupported: bool,
    citations_count: int,
    retrieved_chunk_ids: List[str],
    cited_chunk_ids: List[str],
) -> bool:
    """
    Evaluate Tutor Response:
    - Groundedness check: citations belong to retrieved chunks.
    - Unsupported handling check: if ungrounded, answer explicitly notes lack of material evidence.
    """
    db = get_database()
    passed = True
    score = 1.0
    details = "Tutor answer is grounded and cited correctly."

    if is_unsupported:
        if "don't have enough information" in answer.lower() or "can't answer reliably" in answer.lower() or not is_grounded:
            passed = True
            score = 1.0
            details = "Safely handled unsupported question without fabrication."
        else:
            passed = False
            score = 0.0
            details = "Claimed unsupported but gave a confident fabricated answer."
    else:
        # Grounded answer checks
        invalid_citations = [cid for cid in cited_chunk_ids if cid not in retrieved_chunk_ids]
        if invalid_citations:
            passed = False
            score = 0.5
            details = f"Citations included chunk_ids not in retrieved set: {invalid_citations}"
        elif citations_count == 0 and retrieved_chunk_ids:
            passed = False
            score = 0.7
            details = "Grounded answer omitted required citation attribution."

    eval_doc = AIEvaluationModel(
        user_id=user_id,
        project_id=project_id,
        feature="TUTOR",
        evaluation_type=AIEvaluationType.TUTOR_GROUNDING,
        input_reference=message_id,
        criteria={
            "is_grounded": is_grounded,
            "is_unsupported": is_unsupported,
            "citations_count": citations_count,
            "retrieved_count": len(retrieved_chunk_ids),
        },
        result={"passed": passed, "score": score},
        passed=passed,
        score=score,
        details=details,
        created_at=datetime.now(timezone.utc),
    )

    if db is not None:
        try:
            await db["ai_evaluations"].insert_one(eval_doc.model_dump(by_alias=True, exclude=["id"]))
        except Exception as exc:
            logger.error(f"Failed to insert AIEvaluation record: {exc}")

    return passed


async def evaluate_retrieval_isolation(
    user_id: str,
    project_id: str,
    query: str,
    retrieved_chunks: List[Dict[str, Any]],
) -> bool:
    """Verify 100% of retrieved chunks belong to project_id."""
    db = get_database()
    invalid_chunks = [c for c in retrieved_chunks if str(c.get("project_id")) != project_id]
    passed = len(invalid_chunks) == 0
    score = 1.0 if passed else 0.0

    eval_doc = AIEvaluationModel(
        user_id=user_id,
        project_id=project_id,
        feature="RETRIEVAL",
        evaluation_type=AIEvaluationType.RETRIEVAL_ACCURACY,
        input_reference=f"query:{query[:30]}",
        criteria={"expected_project_id": project_id, "retrieved_count": len(retrieved_chunks)},
        result={"invalid_chunks_count": len(invalid_chunks)},
        passed=passed,
        score=score,
        details="100% project isolation verified." if passed else f"Cross-project chunk leakage: {len(invalid_chunks)} items.",
        created_at=datetime.now(timezone.utc),
    )

    if db is not None:
        try:
            await db["ai_evaluations"].insert_one(eval_doc.model_dump(by_alias=True, exclude=["id"]))
        except Exception as exc:
            logger.error(f"Failed to insert AIEvaluation record: {exc}")

    return passed


async def evaluate_quiz_structure(
    user_id: str,
    project_id: str,
    assessment_id: str,
    questions: List[Dict[str, Any]],
) -> bool:
    """Verify MCQ questions have exactly 4 options and 1 correct answer."""
    db = get_database()
    passed = True
    issues = []

    for idx, q in enumerate(questions):
        if q.get("question_type") == "MCQ":
            options = q.get("options", {})
            if len(options) != 4:
                passed = False
                issues.append(f"Q{idx+1} does not have 4 options.")
            correct = q.get("correct_answer")
            if not correct or correct not in options:
                passed = False
                issues.append(f"Q{idx+1} correct answer '{correct}' is invalid.")

    score = 1.0 if passed else 0.0
    eval_doc = AIEvaluationModel(
        user_id=user_id,
        project_id=project_id,
        feature="QUIZ_GENERATION",
        evaluation_type=AIEvaluationType.QUIZ_STRUCTURE,
        input_reference=assessment_id,
        criteria={"total_questions": len(questions)},
        result={"issues": issues},
        passed=passed,
        score=score,
        details="Quiz structure fully valid." if passed else f"Structural issues: {'; '.join(issues)}",
        created_at=datetime.now(timezone.utc),
    )

    if db is not None:
        try:
            await db["ai_evaluations"].insert_one(eval_doc.model_dump(by_alias=True, exclude=["id"]))
        except Exception as exc:
            logger.error(f"Failed to insert AIEvaluation record: {exc}")

    return passed
