"""
AI Observability & Evaluation Test Suite.

Verifies AIUsage recording and AIEvaluation assertions with db mock.
"""
import pytest
from datetime import datetime, timezone
from unittest.mock import patch, MagicMock, AsyncMock

from app.models.ai_usage import AIFeature
from app.services.ai_observability_service import record_ai_usage
from app.services.ai_evaluation_service import evaluate_tutor_response, evaluate_quiz_structure


@pytest.mark.asyncio
async def test_ai_observability_logging():
    db_mock = MagicMock()
    db_mock["ai_usage"].insert_one = AsyncMock(return_value=MagicMock(inserted_id="doc_123"))

    user_id = "obs_user_123"
    project_id = "obs_proj_123"

    now = datetime.now(timezone.utc)
    with patch("app.services.ai_observability_service.get_database", return_value=db_mock):
        usage_id = await record_ai_usage(
            user_id=user_id,
            project_id=project_id,
            feature=AIFeature.TUTOR,
            model="llama3-70b-8192",
            provider="groq",
            started_at=now,
            completed_at=now,
            latency_ms=142.5,
            success=True
        )

        assert usage_id == "doc_123"
        db_mock["ai_usage"].insert_one.assert_called_once()


@pytest.mark.asyncio
async def test_ai_evaluation_scoring():
    db_mock = MagicMock()
    db_mock["ai_evaluations"].insert_one = AsyncMock(return_value=MagicMock(inserted_id="eval_123"))

    user_id = "eval_user_123"
    project_id = "eval_proj_123"

    with patch("app.services.ai_evaluation_service.get_database", return_value=db_mock):
        # Test Grounded Tutor Evaluation
        tutor_passed = await evaluate_tutor_response(
            user_id=user_id,
            project_id=project_id,
            message_id="msg_123",
            answer="Grounded answer text",
            is_grounded=True,
            is_unsupported=False,
            citations_count=1,
            retrieved_chunk_ids=["chk_1"],
            cited_chunk_ids=["chk_1"]
        )
        assert tutor_passed is True

        # Test Quiz Structure Evaluation
        valid_quiz_passed = await evaluate_quiz_structure(
            user_id=user_id,
            project_id=project_id,
            assessment_id="ass_123",
            questions=[{
                "question_type": "MCQ",
                "options": {"A": "1", "B": "2", "C": "3", "D": "4"},
                "correct_answer": "A"
            }]
        )
        assert valid_quiz_passed is True
