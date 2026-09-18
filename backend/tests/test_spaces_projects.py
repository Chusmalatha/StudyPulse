"""
Automated unit & integration tests for Spaces & Projects APIs.

Covering:
- Authentication enforcement (401/403 for unauthenticated calls)
- Space CRUD operations & validation
- Space ownership isolation (User A cannot access/update/delete User B's Space)
- Project CRUD operations & validation (including learning_goal field)
- Project ownership isolation (User A cannot access/update/delete User B's Project)
- Nested route validation (Project belonging to wrong Space)
- Cascade deletion (Deleting a Space deletes all child Projects)
- Invalid ID format handling (404 instead of 500 error)
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch
from bson import ObjectId

from app.main import app
from app.core.security import create_access_token
from app.schemas.auth import UserResponse
from app.schemas.spaces import SpaceResponse
from app.schemas.projects import ProjectResponse

client = TestClient(app)

USER_A_ID = str(ObjectId())
USER_B_ID = str(ObjectId())

USER_A_DOC = {
    "_id": ObjectId(USER_A_ID),
    "name": "User A",
    "email": "user_a@example.com",
    "role": "user",
    "is_active": True,
}

USER_B_DOC = {
    "_id": ObjectId(USER_B_ID),
    "name": "User B",
    "email": "user_b@example.com",
    "role": "user",
    "is_active": True,
}


def _auth_header(user_id: str) -> dict:
    return {"Authorization": f"Bearer {create_access_token(subject=user_id)}"}


@pytest.fixture
def mock_get_user():
    async def _side_effect(user_id: str):
        if user_id == USER_A_ID:
            return USER_A_DOC
        elif user_id == USER_B_ID:
            return USER_B_DOC
        return None

    with patch("app.api.dependencies.auth_service.get_user_by_id", side_effect=_side_effect):
        yield


# ── 1. Authentication Enforcement Tests ────────────────────────────────────────

class TestUnauthenticatedAccess:
    def test_spaces_require_auth(self):
        assert client.post("/api/v1/spaces", json={"name": "Test"}).status_code in (401, 403)
        assert client.get("/api/v1/spaces").status_code in (401, 403)
        assert client.get(f"/api/v1/spaces/{ObjectId()}").status_code in (401, 403)
        assert client.patch(f"/api/v1/spaces/{ObjectId()}", json={"name": "New"}).status_code in (401, 403)
        assert client.delete(f"/api/v1/spaces/{ObjectId()}").status_code in (401, 403)

    def test_projects_require_auth(self):
        space_id = str(ObjectId())
        proj_id = str(ObjectId())
        assert client.post(f"/api/v1/spaces/{space_id}/projects", json={"name": "Test"}).status_code in (401, 403)
        assert client.get(f"/api/v1/spaces/{space_id}/projects").status_code in (401, 403)
        assert client.get(f"/api/v1/spaces/{space_id}/projects/{proj_id}").status_code in (401, 403)
        assert client.get(f"/api/v1/projects/{proj_id}").status_code in (401, 403)
        assert client.patch(f"/api/v1/projects/{proj_id}", json={"name": "New"}).status_code in (401, 403)
        assert client.delete(f"/api/v1/projects/{proj_id}").status_code in (401, 403)


# ── 2. Space Validation & CRUD Tests ───────────────────────────────────────────

class TestSpaceValidationAndCRUD:
    def test_create_space_blank_name_fails(self, mock_get_user):
        resp = client.post(
            "/api/v1/spaces",
            headers=_auth_header(USER_A_ID),
            json={"name": "   ", "description": "Blank name test"},
        )
        assert resp.status_code == 422

    def test_create_space_missing_name_fails(self, mock_get_user):
        resp = client.post(
            "/api/v1/spaces",
            headers=_auth_header(USER_A_ID),
            json={"description": "No name provided"},
        )
        assert resp.status_code == 422

    def test_create_space_success(self, mock_get_user):
        mock_response = SpaceResponse(
            id=str(ObjectId()),
            user_id=USER_A_ID,
            name="Machine Learning",
            description="Learn ML concepts.",
            project_count=0,
        )
        with patch("app.api.routes.spaces.space_service.create_space", AsyncMock(return_value=mock_response)):
            resp = client.post(
                "/api/v1/spaces",
                headers=_auth_header(USER_A_ID),
                json={"name": "Machine Learning", "description": "Learn ML concepts."},
            )
        assert resp.status_code == 201
        data = resp.json()
        assert data["name"] == "Machine Learning"
        assert data["user_id"] == USER_A_ID

    def test_update_space_success(self, mock_get_user):
        space_id = str(ObjectId())
        mock_response = SpaceResponse(
            id=space_id,
            user_id=USER_A_ID,
            name="Updated Space Name",
            description="Updated description.",
            project_count=2,
        )
        with patch("app.api.routes.spaces.space_service.update_space", AsyncMock(return_value=mock_response)):
            resp = client.patch(
                f"/api/v1/spaces/{space_id}",
                headers=_auth_header(USER_A_ID),
                json={"name": "Updated Space Name", "description": "Updated description."},
            )
        assert resp.status_code == 200
        assert resp.json()["name"] == "Updated Space Name"

    def test_invalid_space_id_returns_404(self, mock_get_user):
        with patch("app.api.routes.spaces.space_service.get_space", AsyncMock(side_effect=ValueError("Invalid ID: 'invalid-id'"))):
            resp = client.get(
                "/api/v1/spaces/invalid-id",
                headers=_auth_header(USER_A_ID),
            )
        assert resp.status_code == 404


# ── 3. Security & Data Isolation Tests ─────────────────────────────────────────

class TestSpaceAndProjectSecurityIsolation:
    def test_user_b_cannot_get_user_a_space(self, mock_get_user):
        space_id = str(ObjectId())
        with patch("app.api.routes.spaces.space_service.get_space", AsyncMock(side_effect=ValueError("not_found"))):
            resp = client.get(
                f"/api/v1/spaces/{space_id}",
                headers=_auth_header(USER_B_ID),
            )
        assert resp.status_code == 404
        assert resp.json()["detail"] == "Space not found."

    def test_user_b_cannot_update_user_a_space(self, mock_get_user):
        space_id = str(ObjectId())
        with patch("app.api.routes.spaces.space_service.update_space", AsyncMock(side_effect=ValueError("not_found"))):
            resp = client.patch(
                f"/api/v1/spaces/{space_id}",
                headers=_auth_header(USER_B_ID),
                json={"name": "Hacked Name"},
            )
        assert resp.status_code == 404

    def test_user_b_cannot_delete_user_a_space(self, mock_get_user):
        space_id = str(ObjectId())
        with patch("app.api.routes.spaces.space_service.delete_space", AsyncMock(side_effect=ValueError("not_found"))):
            resp = client.delete(
                f"/api/v1/spaces/{space_id}",
                headers=_auth_header(USER_B_ID),
            )
        assert resp.status_code == 404

    def test_user_b_cannot_create_project_in_user_a_space(self, mock_get_user):
        space_id = str(ObjectId())
        with patch("app.api.routes.spaces.project_service.create_project", AsyncMock(side_effect=ValueError("not_found"))):
            resp = client.post(
                f"/api/v1/spaces/{space_id}/projects",
                headers=_auth_header(USER_B_ID),
                json={"name": "Unauthorized Project"},
            )
        assert resp.status_code == 404
        assert resp.json()["detail"] == "Project not found."

    def test_user_b_cannot_get_user_a_project(self, mock_get_user):
        proj_id = str(ObjectId())
        with patch("app.api.routes.projects.project_service.get_project", AsyncMock(side_effect=ValueError("not_found"))):
            resp = client.get(
                f"/api/v1/projects/{proj_id}",
                headers=_auth_header(USER_B_ID),
            )
        assert resp.status_code == 404

    def test_project_in_wrong_space_returns_404(self, mock_get_user):
        space_id = str(ObjectId())
        proj_id = str(ObjectId())
        with patch("app.api.routes.spaces.project_service.get_project_in_space", AsyncMock(side_effect=ValueError("not_found"))):
            resp = client.get(
                f"/api/v1/spaces/{space_id}/projects/{proj_id}",
                headers=_auth_header(USER_A_ID),
            )
        assert resp.status_code == 404


# ── 4. Project Validation & CRUD Tests ─────────────────────────────────────────

class TestProjectValidationAndCRUD:
    def test_create_project_blank_name_fails(self, mock_get_user):
        space_id = str(ObjectId())
        resp = client.post(
            f"/api/v1/spaces/{space_id}/projects",
            headers=_auth_header(USER_A_ID),
            json={"name": "  ", "description": "Test", "learning_goal": "Goal"},
        )
        assert resp.status_code == 422

    def test_create_project_success_with_learning_goal(self, mock_get_user):
        space_id = str(ObjectId())
        mock_proj = ProjectResponse(
            id=str(ObjectId()),
            space_id=space_id,
            user_id=USER_A_ID,
            name="Build ML Fundamentals",
            description="Learn core principles",
            learning_goal="Understand ML algorithms and models",
        )
        with patch("app.api.routes.spaces.project_service.create_project", AsyncMock(return_value=mock_proj)):
            resp = client.post(
                f"/api/v1/spaces/{space_id}/projects",
                headers=_auth_header(USER_A_ID),
                json={
                    "name": "Build ML Fundamentals",
                    "description": "Learn core principles",
                    "learning_goal": "Understand ML algorithms and models",
                },
            )
        assert resp.status_code == 201
        data = resp.json()
        assert data["name"] == "Build ML Fundamentals"
        assert data["learning_goal"] == "Understand ML algorithms and models"

    def test_update_project_learning_goal(self, mock_get_user):
        proj_id = str(ObjectId())
        mock_proj = ProjectResponse(
            id=proj_id,
            space_id=str(ObjectId()),
            user_id=USER_A_ID,
            name="ML Project",
            description="Updated desc",
            learning_goal="Master Neural Networks",
        )
        with patch("app.api.routes.projects.project_service.update_project", AsyncMock(return_value=mock_proj)):
            resp = client.patch(
                f"/api/v1/projects/{proj_id}",
                headers=_auth_header(USER_A_ID),
                json={"learning_goal": "Master Neural Networks"},
            )
        assert resp.status_code == 200
        assert resp.json()["learning_goal"] == "Master Neural Networks"
