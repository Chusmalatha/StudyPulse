"""
BackgroundJob DB model definition.
"""
from datetime import datetime, timezone
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field


class JobStatus(str, Enum):
    QUEUED = "QUEUED"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class BackgroundJobModel(BaseModel):
    """Internal representation of a Background Job document in MongoDB."""
    id: Optional[str] = Field(default=None, alias="_id")
    job_type: str = "PROCESS_PDF"
    material_id: str
    project_id: str
    user_id: str
    event_id: Optional[str] = None
    correlation_id: Optional[str] = None
    status: JobStatus = JobStatus.QUEUED
    attempts: int = 0
    max_attempts: int = 3
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    last_error: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    model_config = {"populate_by_name": True}
