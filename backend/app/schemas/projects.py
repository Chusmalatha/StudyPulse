"""
Pydantic schemas for Project API request/response payloads.
"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, field_validator


# ── Requests ──────────────────────────────────────────────────────────────────

class ProjectCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: str = Field("", max_length=1000)
    learning_goal: str = Field("", max_length=1000)

    @field_validator("name")
    @classmethod
    def name_not_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Project name cannot be blank.")
        return v.strip()

    @field_validator("description", "learning_goal")
    @classmethod
    def strip_fields(cls, v: str) -> str:
        return v.strip()


class ProjectUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=1000)
    learning_goal: Optional[str] = Field(None, max_length=1000)

    @field_validator("name")
    @classmethod
    def name_not_blank(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and not v.strip():
            raise ValueError("Project name cannot be blank.")
        return v.strip() if v else v

    @field_validator("description", "learning_goal")
    @classmethod
    def strip_fields(cls, v: Optional[str]) -> Optional[str]:
        return v.strip() if v else v


# ── Responses ─────────────────────────────────────────────────────────────────

class ProjectResponse(BaseModel):
    id: str
    space_id: str
    user_id: str
    name: str
    description: str
    learning_goal: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
