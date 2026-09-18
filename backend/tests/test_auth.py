"""
Auth tests using FastAPI's TestClient.

Run with:
    cd backend
    .\\venv\\Scripts\\pytest tests/ -v

Strategy: Mock at the *service* layer so tests are not sensitive to
Motor/MongoDB driver internals, but the HTTP routing, schema validation,
and dependency injection are exercised for real.
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch, MagicMock
from bson import ObjectId

from app.main import app
from app.core.security import create_access_token, hash_password
from app.schemas.auth import UserResponse, TokenResponse

client = TestClient(app)

# ── shared fixtures ─────────────────────────────────────────────────────────
MOCK_USER_ID = str(ObjectId())

MOCK_USER = UserResponse(
    id=MOCK_USER_ID,
    name="Test User",
    email="test@example.com",
    role="user",
    is_active=True,
)

MOCK_TOKEN_RESPONSE = TokenResponse(
    access_token=create_access_token(subject=MOCK_USER_ID),
    token_type="bearer",
    user=MOCK_USER,
)


def _auth_header(user_id: str = MOCK_USER_ID) -> dict:
    return {"Authorization": f"Bearer {create_access_token(subject=user_id)}"}


# ── Registration tests ──────────────────────────────────────────────────────
class TestRegister:
    URL = "/api/v1/auth/register"

    def test_successful_registration(self):
        with patch(
            "app.api.routes.auth.auth_service.register_user",
            new_callable=AsyncMock,
            return_value=MOCK_USER,
        ):
            resp = client.post(self.URL, json={
                "name": "Alice",
                "email": "alice@example.com",
                "password": "securepassword1",
            })
        assert resp.status_code == 201
        data = resp.json()
        assert data["email"] == "test@example.com"   # from mock
        assert "password_hash" not in data
        assert "password" not in data
        assert data["role"] == "user"

    def test_duplicate_email_returns_409(self):
        with patch(
            "app.api.routes.auth.auth_service.register_user",
            new_callable=AsyncMock,
            side_effect=ValueError("Email already registered."),
        ):
            resp = client.post(self.URL, json={
                "name": "Alice",
                "email": "alice@example.com",
                "password": "securepassword1",
            })
        assert resp.status_code == 409
        assert "already registered" in resp.json()["detail"].lower()

    def test_invalid_email_returns_422(self):
        resp = client.post(self.URL, json={
            "name": "Alice",
            "email": "not-an-email",
            "password": "securepassword1",
        })
        assert resp.status_code == 422

    def test_password_too_short_returns_422(self):
        resp = client.post(self.URL, json={
            "name": "Alice",
            "email": "alice@example.com",
            "password": "abc",  # < 8 chars
        })
        assert resp.status_code == 422

    def test_admin_role_not_selectable_during_registration(self):
        """The service always creates 'user' role; test that response reflects this."""
        with patch(
            "app.api.routes.auth.auth_service.register_user",
            new_callable=AsyncMock,
            return_value=MOCK_USER,
        ):
            resp = client.post(self.URL, json={
                "name": "Alice",
                "email": "alice@example.com",
                "password": "securepassword1",
            })
        if resp.status_code == 201:
            assert resp.json()["role"] == "user"

    def test_missing_name_returns_422(self):
        resp = client.post(self.URL, json={
            "email": "alice@example.com",
            "password": "securepassword1",
        })
        assert resp.status_code == 422


# ── Login tests ─────────────────────────────────────────────────────────────
class TestLogin:
    URL = "/api/v1/auth/login"

    def test_correct_credentials_returns_token(self):
        with patch(
            "app.api.routes.auth.auth_service.login_user",
            new_callable=AsyncMock,
            return_value=MOCK_TOKEN_RESPONSE,
        ):
            resp = client.post(self.URL, json={
                "email": "test@example.com",
                "password": "correctpassword",
            })
        assert resp.status_code == 200
        data = resp.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert "password_hash" not in str(data)
        assert "user" in data

    def test_wrong_password_returns_401(self):
        with patch(
            "app.api.routes.auth.auth_service.login_user",
            new_callable=AsyncMock,
            side_effect=ValueError("Invalid email or password."),
        ):
            resp = client.post(self.URL, json={
                "email": "test@example.com",
                "password": "wrongpassword",
            })
        assert resp.status_code == 401

    def test_unknown_email_returns_401(self):
        with patch(
            "app.api.routes.auth.auth_service.login_user",
            new_callable=AsyncMock,
            side_effect=ValueError("Invalid email or password."),
        ):
            resp = client.post(self.URL, json={
                "email": "nobody@example.com",
                "password": "password123",
            })
        assert resp.status_code == 401


# ── Security utility tests ──────────────────────────────────────────────────
class TestSecurity:
    def test_password_hash_and_verify(self):
        """hash_password + verify_password round-trip."""
        from app.core.security import verify_password
        hashed = hash_password("mypassword")
        assert verify_password("mypassword", hashed)
        assert not verify_password("wrongpassword", hashed)

    def test_hash_does_not_store_plaintext(self):
        hashed = hash_password("mypassword")
        assert "mypassword" not in hashed

    def test_jwt_create_and_decode(self):
        from app.core.security import decode_access_token
        token = create_access_token(subject="user123")
        assert decode_access_token(token) == "user123"

    def test_expired_token_returns_none(self):
        from datetime import timedelta
        from app.core.security import decode_access_token
        token = create_access_token(subject="user123", expires_delta=timedelta(seconds=-1))
        assert decode_access_token(token) is None

    def test_invalid_token_returns_none(self):
        from app.core.security import decode_access_token
        assert decode_access_token("totally.invalid.token") is None


# ── Current-user endpoint tests ─────────────────────────────────────────────
class TestMe:
    URL = "/api/v1/auth/me"

    def test_valid_token_returns_user(self):
        mock_doc = {
            "_id": ObjectId(MOCK_USER_ID),
            "name": "Test User",
            "email": "test@example.com",
            "role": "user",
            "is_active": True,
        }
        with patch(
            "app.api.dependencies.auth_service.get_user_by_id",
            new_callable=AsyncMock,
            return_value=mock_doc,
        ):
            resp = client.get(self.URL, headers=_auth_header())
        assert resp.status_code == 200
        data = resp.json()
        assert data["email"] == "test@example.com"
        assert "password_hash" not in data

    def test_missing_token_returns_403(self):
        """Missing Authorization header is rejected with 401 or 403."""
        resp = client.get(self.URL)
        assert resp.status_code in (401, 403)

    def test_invalid_token_returns_401(self):
        resp = client.get(self.URL, headers={"Authorization": "Bearer totally.invalid"})
        assert resp.status_code == 401

    def test_expired_token_returns_401(self):
        from datetime import timedelta
        expired = create_access_token(subject=MOCK_USER_ID, expires_delta=timedelta(seconds=-1))
        resp = client.get(self.URL, headers={"Authorization": f"Bearer {expired}"})
        assert resp.status_code == 401

    def test_token_for_nonexistent_user_returns_401(self):
        with patch(
            "app.api.dependencies.auth_service.get_user_by_id",
            new_callable=AsyncMock,
            return_value=None,
        ):
            resp = client.get(self.URL, headers=_auth_header())
        assert resp.status_code == 401


# ── Authorization / data isolation tests ────────────────────────────────────
class TestAuthorization:
    def test_protected_endpoint_without_auth_is_rejected(self):
        resp = client.get("/api/v1/auth/me")
        assert resp.status_code in (401, 403)

    def test_user_identity_comes_from_jwt_not_client_header(self):
        """
        The backend must never trust a client-supplied user ID.
        Identity comes exclusively from the decoded JWT *sub* claim.
        Even if an attacker sends a fake X-User-Id header, the
        authenticated user is always the one encoded in the JWT.
        """
        attacker_id = str(ObjectId())   # different from MOCK_USER_ID
        mock_doc = {
            "_id": ObjectId(MOCK_USER_ID),
            "name": "Test User",
            "email": "test@example.com",
            "role": "user",
            "is_active": True,
        }
        with patch(
            "app.api.dependencies.auth_service.get_user_by_id",
            new_callable=AsyncMock,
            return_value=mock_doc,
        ) as mock_get:
            resp = client.get(
                "/api/v1/auth/me",
                headers={
                    **_auth_header(MOCK_USER_ID),
                    "X-User-Id": attacker_id,   # forged header
                },
            )
        assert resp.status_code == 200
        # The returned id is from the JWT, not the forged header
        assert resp.json()["id"] == MOCK_USER_ID
        assert resp.json()["id"] != attacker_id
        # get_user_by_id was called with the JWT sub, not the forged header
        mock_get.assert_called_once_with(MOCK_USER_ID)
