"""
Assessment DB model definition.
"""
from datetime import datetime, timezone
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field


class AssessmentStatus(str, Enum):
    DRAFT = "DRAFT"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"


class AssessmentModel(BaseModel):
    """Internal representation of an Assessment document in MongoDB."""
    id: Optional[str] = Field(default=None, alias="_id")
    project_id: str
    user_id: str
    title: str = "Adaptive Practice Quiz"
    status: AssessmentStatus = AssessmentStatus.IN_PROGRESS
    question_count: int = 5
    current_question_index: int = 0
    score_mcq: Optional[float] = None
    started_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    completed_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    model_config = {"populate_by_name": True}
