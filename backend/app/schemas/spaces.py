"""
Pydantic schemas for Space API request/response payloads.
"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, field_validator


# ── Requests ──────────────────────────────────────────────────────────────────

class SpaceCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: str = Field("", max_length=500)

    @field_validator("name")
    @classmethod
    def name_not_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Space name cannot be blank.")
        return v.strip()

    @field_validator("description")
    @classmethod
    def strip_description(cls, v: str) -> str:
        return v.strip()


class SpaceUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)

    @field_validator("name")
    @classmethod
    def name_not_blank(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and not v.strip():
            raise ValueError("Space name cannot be blank.")
        return v.strip() if v else v

    @field_validator("description")
    @classmethod
    def strip_description(cls, v: Optional[str]) -> Optional[str]:
        return v.strip() if v else v


# ── Responses ─────────────────────────────────────────────────────────────────

class SpaceResponse(BaseModel):
    id: str
    user_id: str
    name: str
    description: str
    project_count: int = 0
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
