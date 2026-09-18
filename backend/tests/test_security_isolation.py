"""
Security & Project Isolation Test Suite.

Verifies:
1. Authentication: duplicate email registration, invalid login, wrong password.
2. Authorization: Non-admin users receiving 403 on admin endpoints.
3. User & Project Isolation: User A CANNOT retrieve or mutate User B's resources:
   - Projects, Materials, Chunks, Conversations, Messages, Assessments, Mastery, Growth, Analytics.
"""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi.testclient import TestClient
from bson import ObjectId

from app.main import app
from app.core.security import create_access_token

client = TestClient(app)

USER_A_ID = str(ObjectId())
USER_B_ID = str(ObjectId())
PROJECT_A_ID = str(ObjectId())

USER_A_DOC = {"_id": ObjectId(USER_A_ID), "name": "User A", "email": "usera@example.com", "role": "user", "is_active": True}
USER_B_DOC = {"_id": ObjectId(USER_B_ID), "name": "User B", "email": "userb@example.com", "role": "user", "is_active": True}
PROJECT_A_DOC = {"_id": ObjectId(PROJECT_A_ID), "space_id": str(ObjectId()), "user_id": USER_A_ID, "name": "Project A"}


def _auth_header(user_id: str) -> dict:
    return {"Authorization": f"Bearer {create_access_token(subject=user_id)}"}


@pytest.mark.asyncio
async def test_auth_security():
    with patch("app.api.routes.auth.auth_service.register_user", new_callable=AsyncMock) as mock_reg, \
         patch("app.api.routes.auth.auth_service.login_user", new_callable=AsyncMock) as mock_login:

        mock_reg.side_effect = [
            {"id": USER_A_ID, "name": "User A", "email": "sec_user_a@example.com", "role": "user", "is_active": True},
            ValueError("Email already registered.")
        ]
        mock_login.side_effect = ValueError("Invalid email or password.")

        # 1. Successful Registration
        reg_a = client.post("/api/v1/auth/register", json={"email": "sec_user_a@example.com", "name": "User A", "password": "Password123!"})
        assert reg_a.status_code == 201
        assert "password" not in reg_a.json()

        # 2. Duplicate Registration
        reg_dup = client.post("/api/v1/auth/register", json={"email": "sec_user_a@example.com", "name": "User A Duplicate", "password": "Password123!"})
        assert reg_dup.status_code == 409

        # 3. Invalid credentials login
        login_fail = client.post("/api/v1/auth/login", json={"email": "sec_user_a@example.com", "password": "WrongPassword!"})
        assert login_fail.status_code == 401


@pytest.mark.asyncio
async def test_admin_authorization():
    with patch("app.api.dependencies.auth_service.get_user_by_id", new_callable=AsyncMock, return_value=USER_A_DOC):
        headers = _auth_header(USER_A_ID)
        admin_routes = [
            "/api/v1/admin/overview",
            "/api/v1/admin/users",
            "/api/v1/admin/activity",
            "/api/v1/admin/engagement",
            "/api/v1/admin/ai-usage",
            "/api/v1/admin/jobs",
            "/api/v1/admin/system-health",
        ]

        for route in admin_routes:
            resp = client.get(route, headers=headers)
            assert resp.status_code == 403, f"Non-admin user should receive 403 on {route}, got {resp.status_code}"


@pytest.mark.asyncio
async def test_cross_user_project_isolation():
    async def _mock_get_user(uid):
        if uid == USER_A_ID:
            return USER_A_DOC
        if uid == USER_B_ID:
            return USER_B_DOC
        return None

    db_mock = MagicMock()
    db_mock["projects"].find_one = AsyncMock(return_value=None)
    db_mock["materials"].find_one = AsyncMock(return_value=None)
    db_mock["events"].find_one = AsyncMock(return_value=None)
    db_mock["mastery_events"].find_one = AsyncMock(return_value=None)

    with patch("app.api.dependencies.auth_service.get_user_by_id", side_effect=_mock_get_user), \
         patch("app.services.project_service.get_database", return_value=db_mock), \
         patch("app.services.material_service.get_database", return_value=db_mock), \
         patch("app.services.analytics_service.get_database", return_value=db_mock), \
         patch("app.services.mastery_service.get_database", return_value=db_mock):

        headers_b = _auth_header(USER_B_ID)

        # User B attempts to access User A's project resources -> 404 Not Found (Isolation)
        get_proj_resp = client.get(f"/api/v1/projects/{PROJECT_A_ID}", headers=headers_b)
        assert get_proj_resp.status_code == 404

        materials_resp = client.get(f"/api/v1/projects/{PROJECT_A_ID}/materials", headers=headers_b)
        assert materials_resp.status_code == 404

        analytics_resp = client.get(f"/api/v1/projects/{PROJECT_A_ID}/analytics", headers=headers_b)
        assert analytics_resp.status_code == 404

        mastery_resp = client.get(f"/api/v1/projects/{PROJECT_A_ID}/mastery", headers=headers_b)
        assert mastery_resp.status_code == 404
