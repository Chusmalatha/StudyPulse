"""
Pydantic schemas for auth API request/response payloads.
These are distinct from the DB models in app/models/.
"""
from pydantic import BaseModel, EmailStr, Field, field_validator


# ── Requests ──────────────────────────────────────────────────────────────────
class RegisterRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    email: EmailStr
    password: str = Field(..., min_length=8)

    @field_validator("name")
    @classmethod
    def name_not_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Name cannot be blank")
        return v.strip()


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


# ── Responses ─────────────────────────────────────────────────────────────────
class UserResponse(BaseModel):
    """Safe user representation — never includes password_hash."""
    id: str
    name: str
    email: str
    role: str
    is_active: bool


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse
