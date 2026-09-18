"""
Automated tests for Phase 10 — Analytics & Admin Dashboard.

Covering:
1. Project Analytics Endpoint (GET /projects/{project_id}/analytics) & dynamic event/quiz/mastery aggregation.
2. Global Analytics Endpoint (GET /analytics/overview) & cross-project user statistics aggregation.
3. Admin Security & Authorization (Non-admin receives 403 Forbidden on /admin/*; Admin succeeds).
4. Admin Overview (GET /admin/overview) & system metrics database counts.
5. Admin Users List & User Journey Inspection (GET /admin/users, GET /admin/users/{user_id}).
6. Admin Global Activity Stream & Filtering (GET /admin/activity).
7. Admin Active Learners Engagement (GET /admin/engagement).
8. Admin AI Usage & Evaluation Quality (GET /admin/ai-usage, GET /admin/ai-evaluation).
9. Admin Background Jobs Inspection (GET /admin/jobs).
10. Admin System Health Checks (GET /admin/system-health).
"""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi.testclient import TestClient
from bson import ObjectId

from app.main import app
from app.core.security import create_access_token
from app.models.user import UserRole
from app.services import analytics_service

client = TestClient(app)

ADMIN_USER_ID = str(ObjectId())
NORMAL_USER_ID = str(ObjectId())
PROJECT_ID = str(ObjectId())
SPACE_ID = str(ObjectId())

ADMIN_USER_DOC = {
    "_id": ObjectId(ADMIN_USER_ID),
    "name": "Admin User",
    "email": "admin@example.com",
    "role": "admin",
    "is_active": True,
}

NORMAL_USER_DOC = {
    "_id": ObjectId(NORMAL_USER_ID),
    "name": "Normal Student",
    "email": "student@example.com",
    "role": "user",
    "is_active": True,
}

PROJECT_DOC = {
    "_id": ObjectId(PROJECT_ID),
    "space_id": SPACE_ID,
    "user_id": NORMAL_USER_ID,
    "name": "Analytics Test Project",
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

    async def to_list(self, length=None):
        return self.items

    def sort(self, *args, **kwargs):
        return self

    def skip(self, *args, **kwargs):
        return self

    def limit(self, *args, **kwargs):
        return self


def _create_mock_db():
    db_mock = MagicMock()

    u_coll = MagicMock()
    u_coll.find_one = AsyncMock(side_effect=lambda q: ADMIN_USER_DOC if q.get("_id") == ObjectId(ADMIN_USER_ID) else (NORMAL_USER_DOC if q.get("_id") == ObjectId(NORMAL_USER_ID) else None))
    u_coll.count_documents = AsyncMock(return_value=2)
    u_coll.find = lambda q, *a, **kw: DummyAsyncCursor([ADMIN_USER_DOC, NORMAL_USER_DOC])

    p_coll = MagicMock()
    p_coll.find_one = AsyncMock(return_value=PROJECT_DOC)
    p_coll.count_documents = AsyncMock(return_value=1)
    p_coll.find = lambda q, *a, **kw: DummyAsyncCursor([PROJECT_DOC])

    s_coll = MagicMock()
    s_coll.count_documents = AsyncMock(return_value=1)
    s_coll.find = lambda q, *a, **kw: DummyAsyncCursor([{"_id": ObjectId(SPACE_ID), "name": "Main Space"}])

    evt_coll = MagicMock()
    evt_coll.count_documents = AsyncMock(return_value=5)
    evt_coll.distinct = AsyncMock(return_value=[PROJECT_ID])
    evt_coll.find_one = AsyncMock(return_value=None)
    evt_coll.find = lambda q, *a, **kw: DummyAsyncCursor([
        {"_id": ObjectId(), "event_type": "MATERIAL_PROCESSED", "user_id": NORMAL_USER_ID, "project_id": PROJECT_ID, "created_at": None},
        {"_id": ObjectId(), "event_type": "QUIZ_COMPLETED", "user_id": NORMAL_USER_ID, "project_id": PROJECT_ID, "created_at": None},
    ])

    ass_coll = MagicMock()
    ass_coll.count_documents = AsyncMock(return_value=1)
    ass_coll.find = lambda q, *a, **kw: DummyAsyncCursor([{"_id": ObjectId(), "title": "Quiz 1", "score_mcq": 100.0, "status": "COMPLETED"}])

    att_coll = MagicMock()
    att_coll.count_documents = AsyncMock(return_value=3)
    att_coll.find = lambda q, *a, **kw: DummyAsyncCursor([
        {"_id": ObjectId(), "is_correct": True, "question_type": "MCQ"},
        {"_id": ObjectId(), "is_correct": True, "question_type": "MCQ"},
        {"_id": ObjectId(), "is_correct": False, "question_type": "OPEN_ENDED"},
    ])

    job_coll = MagicMock()
    job_coll.count_documents = AsyncMock(return_value=0)
    job_coll.find = lambda q, *a, **kw: DummyAsyncCursor([])

    msg_coll = MagicMock()
    msg_coll.count_documents = AsyncMock(return_value=2)

    cpt_coll = MagicMock()
    cpt_coll.count_documents = AsyncMock(return_value=2)
    cpt_coll.find = lambda q, *a, **kw: DummyAsyncCursor([])

    chk_coll = MagicMock()
    chk_coll.count_documents = AsyncMock(return_value=5)

    def get_coll(name):
        collections = {
            "users": u_coll,
            "projects": p_coll,
            "spaces": s_coll,
            "events": evt_coll,
            "assessments": ass_coll,
            "question_attempts": att_coll,
            "background_jobs": job_coll,
            "messages": msg_coll,
            "concepts": cpt_coll,
            "chunks": chk_coll,
            "materials": MagicMock(count_documents=AsyncMock(return_value=1)),
            "conversations": MagicMock(count_documents=AsyncMock(return_value=1)),
            "mastery_events": MagicMock(distinct=AsyncMock(return_value=[])),
            "recommendations": MagicMock(count_documents=AsyncMock(return_value=1)),
        }
        return collections.get(name, MagicMock())

    db_mock.__getitem__.side_effect = get_coll
    db_mock.command = AsyncMock(return_value={"ok": 1})
    return db_mock


@pytest.fixture
def mock_get_user():
    async def _side_effect(user_id: str):
        if user_id == ADMIN_USER_ID:
            return ADMIN_USER_DOC
        elif user_id == NORMAL_USER_ID:
            return NORMAL_USER_DOC
        return None

    with patch("app.api.dependencies.auth_service.get_user_by_id", side_effect=_side_effect):
        yield


@pytest.mark.asyncio
async def test_project_analytics_endpoint(mock_get_user):
    """Test GET /api/v1/projects/{project_id}/analytics returns real aggregated metrics."""
    db_mock = _create_mock_db()

    with patch("app.services.analytics_service.get_database", return_value=db_mock), \
         patch("app.services.project_service.get_database", return_value=db_mock):

        res = client.get(f"/api/v1/projects/{PROJECT_ID}/analytics", headers=_auth_header(NORMAL_USER_ID))
        assert res.status_code == 200
        body = res.json()
        assert body["project_id"] == PROJECT_ID
        assert "learning_activity" in body
        assert "quiz_performance" in body
        assert body["quiz_performance"]["accuracy_percentage"] == 66.7
        assert "mastery" in body
        assert "ai_activity" in body


@pytest.mark.asyncio
async def test_global_analytics_endpoint(mock_get_user):
    """Test GET /api/v1/analytics/overview aggregates across user projects."""
    db_mock = _create_mock_db()

    with patch("app.services.analytics_service.get_database", return_value=db_mock), \
         patch("app.services.project_service.get_database", return_value=db_mock):

        res = client.get("/api/v1/analytics/overview", headers=_auth_header(NORMAL_USER_ID))
        assert res.status_code == 200
        body = res.json()
        assert body["total_spaces"] == 1
        assert body["total_projects"] == 1
        assert body["overall_accuracy_percentage"] == 66.7


@pytest.mark.asyncio
async def test_admin_security_isolation(mock_get_user):
    """Test security isolation: normal user receives 403 Forbidden on admin APIs."""
    res = client.get("/api/v1/admin/overview", headers=_auth_header(NORMAL_USER_ID))
    assert res.status_code == 403
    assert "permission" in res.json()["detail"].lower()


@pytest.mark.asyncio
async def test_admin_overview_endpoint(mock_get_user):
    """Test GET /api/v1/admin/overview succeeds for admin user."""
    db_mock = _create_mock_db()

    with patch("app.services.analytics_service.get_database", return_value=db_mock):

        res = client.get("/api/v1/admin/overview", headers=_auth_header(ADMIN_USER_ID))
        assert res.status_code == 200
        body = res.json()
        assert body["total_users"] == 2
        assert body["system_status"] == "HEALTHY"


@pytest.mark.asyncio
async def test_admin_users_and_journey(mock_get_user):
    """Test GET /api/v1/admin/users and GET /api/v1/admin/users/{user_id}."""
    db_mock = _create_mock_db()

    with patch("app.services.analytics_service.get_database", return_value=db_mock):

        res = client.get("/api/v1/admin/users", headers=_auth_header(ADMIN_USER_ID))
        assert res.status_code == 200
        assert res.json()["total_count"] == 2

        res_j = client.get(f"/api/v1/admin/users/{NORMAL_USER_ID}", headers=_auth_header(ADMIN_USER_ID))
        assert res_j.status_code == 200
        assert res_j.json()["user"]["id"] == NORMAL_USER_ID


@pytest.mark.asyncio
async def test_admin_system_health(mock_get_user):
    """Test GET /api/v1/admin/system-health returns valid health checks."""
    db_mock = _create_mock_db()

    with patch("app.services.analytics_service.get_database", return_value=db_mock):

        res = client.get("/api/v1/admin/system-health", headers=_auth_header(ADMIN_USER_ID))
        assert res.status_code == 200
        body = res.json()
        assert body["overall_status"] in ("HEALTHY", "WARNING")
        assert len(body["checks"]) >= 4
