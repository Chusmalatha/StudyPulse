"""
Tests for Phase 9 — Events & Background Learning Workflows.
"""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi.testclient import TestClient
from bson import ObjectId

from app.main import app
from app.core.security import create_access_token
from app.models.job import JobStatus
from app.services import event_publisher
from app.services.workflow_service import QuizCompletedWorkflow

client = TestClient(app)

USER_ID = str(ObjectId())
PROJECT_ID = str(ObjectId())
EVENT_ID = str(ObjectId())
ASSESSMENT_ID = str(ObjectId())

USER_DOC = {
    "_id": ObjectId(USER_ID),
    "name": "Test User",
    "email": "test@example.com",
    "role": "user",
    "is_active": True,
}

PROJECT_DOC = {
    "_id": ObjectId(PROJECT_ID),
    "space_id": str(ObjectId()),
    "user_id": USER_ID,
    "name": "Workflow Test Project",
}

EVENT_DOC = {
    "_id": ObjectId(EVENT_ID),
    "event_type": "QUIZ_COMPLETED",
    "user_id": USER_ID,
    "project_id": PROJECT_ID,
    "entity_type": "assessment",
    "entity_id": ASSESSMENT_ID,
    "payload": {"score_mcq": 100.0},
    "correlation_id": f"corr_{EVENT_ID}",
    "status": "PROCESSED",
    "attempts": 1,
    "created_at": "2026-09-16T00:00:00Z",
    "processed_at": "2026-09-16T00:00:00Z",
}


def _auth_header(user_id: str) -> dict:
    return {"Authorization": f"Bearer {create_access_token(subject=user_id)}"}


class DummyAsyncCursor:
    def __init__(self, items):
        self.items = items

    def __aiter__(self):
        return self._gen()

    async def _gen(self):
        for item in self.items:
            yield item

    def sort(self, *args, **kwargs):
        return self

    def skip(self, *args, **kwargs):
        return self

    def limit(self, *args, **kwargs):
        return self


def _create_mock_db():
    db_mock = MagicMock()

    evt_coll = MagicMock()
    evt_coll.insert_one = AsyncMock(return_value=MagicMock(inserted_id=ObjectId(EVENT_ID)))
    evt_coll.find_one = AsyncMock(return_value=EVENT_DOC)
    evt_coll.count_documents = AsyncMock(return_value=1)
    evt_coll.find = lambda q, *a, **kw: DummyAsyncCursor([EVENT_DOC])

    proj_coll = MagicMock()
    proj_coll.find_one = AsyncMock(return_value=PROJECT_DOC)

    job_coll = MagicMock()
    job_coll.find_one = AsyncMock(return_value=None)
    job_coll.update_one = AsyncMock()

    att_coll = MagicMock()
    att_coll.find = lambda q, *a, **kw: DummyAsyncCursor([])

    def get_coll(name):
        collections = {
            "events": evt_coll,
            "projects": proj_coll,
            "background_jobs": job_coll,
            "question_attempts": att_coll,
        }
        return collections.get(name, MagicMock())

    db_mock.__getitem__.side_effect = get_coll
    return db_mock


@pytest.fixture
def mock_get_user():
    with patch("app.api.dependencies.auth_service.get_user_by_id", AsyncMock(return_value=USER_DOC)):
        yield


@pytest.mark.asyncio
async def test_publish_event_centralized():
    db_mock = _create_mock_db()
    res = await event_publisher.publish_event(
        event_type="MATERIAL_UPLOADED",
        user_id=USER_ID,
        project_id=PROJECT_ID,
        payload={"filename": "notes.pdf"},
        db=db_mock,
    )
    assert res["id"] == EVENT_ID
    assert res["event_type"] == "MATERIAL_UPLOADED"
    assert res["correlation_id"] is not None


@pytest.mark.asyncio
async def test_event_correlation_chain():
    db_mock = _create_mock_db()
    shared_corr = "corr_shared_123"

    ev1 = await event_publisher.publish_event(
        event_type="QUIZ_COMPLETED",
        user_id=USER_ID,
        project_id=PROJECT_ID,
        correlation_id=shared_corr,
        db=db_mock,
    )
    assert ev1["correlation_id"] == shared_corr


@pytest.mark.asyncio
async def test_quiz_completed_workflow_execution():
    db_mock = _create_mock_db()

    mock_mastery_svc = MagicMock()
    mock_mastery_svc.update_mastery = AsyncMock()

    mock_ctx_svc = MagicMock()
    mock_ctx_svc.store_or_update_context = AsyncMock()

    mock_growth_svc = MagicMock()
    mock_growth_svc.analyze_project_growth = AsyncMock(return_value=None)

    mock_rec_svc = MagicMock()
    mock_rec_svc.generate_recommendations = AsyncMock(return_value=[])

    with patch("app.services.workflow_service.MasteryService", return_value=mock_mastery_svc), \
         patch("app.services.workflow_service.LearningContextService", return_value=mock_ctx_svc), \
         patch("app.services.workflow_service.GrowthAnalysisService", return_value=mock_growth_svc), \
         patch("app.services.workflow_service.RecommendationService", return_value=mock_rec_svc), \
         patch("app.services.workflow_service.publish_event", AsyncMock()):

        result = await QuizCompletedWorkflow.run_workflow(
            project_id=PROJECT_ID,
            user_id=USER_ID,
            assessment_id=ASSESSMENT_ID,
            event_id=EVENT_ID,
            db=db_mock,
        )

        assert result["status"] == JobStatus.COMPLETED.value
        assert "FINALIZE_ASSESSMENT" in result["completed_steps"]
        assert "UPDATE_MASTERY" in result["completed_steps"]


@pytest.mark.asyncio
async def test_workflow_idempotency_duplicate_protection():
    db_mock = _create_mock_db()
    # Mock existing completed job
    db_mock["background_jobs"].find_one = AsyncMock(return_value={
        "status": JobStatus.COMPLETED.value,
        "completed_steps": ["FINALIZE_ASSESSMENT", "UPDATE_MASTERY"],
    })

    result = await QuizCompletedWorkflow.run_workflow(
        project_id=PROJECT_ID,
        user_id=USER_ID,
        assessment_id=ASSESSMENT_ID,
        event_id=EVENT_ID,
        db=db_mock,
    )

    assert result["status"] == JobStatus.COMPLETED.value
    assert result.get("skipped") is True


@pytest.mark.asyncio
async def test_events_api_endpoints(mock_get_user):
    db_mock = _create_mock_db()

    with patch("app.services.event_publisher.get_database", return_value=db_mock), \
         patch("app.services.project_service.get_database", return_value=db_mock):

        res = client.get(f"/api/v1/projects/{PROJECT_ID}/events", headers=_auth_header(USER_ID))
        assert res.status_code == 200
        body = res.json()
        assert "events" in body
        assert body["total_count"] == 1

        res_single = client.get(f"/api/v1/projects/{PROJECT_ID}/events/{EVENT_ID}", headers=_auth_header(USER_ID))
        assert res_single.status_code == 200
        assert res_single.json()["id"] == EVENT_ID
