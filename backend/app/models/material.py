"""
Material DB model definition.
"""
from datetime import datetime, timezone
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field


class MaterialStatus(str, Enum):
    QUEUED = "QUEUED"
    PROCESSING = "PROCESSING"
    READY = "READY"
    FAILED = "FAILED"


class MaterialModel(BaseModel):
    """Internal representation of a Material document in MongoDB."""
    id: Optional[str] = Field(default=None, alias="_id")
    project_id: str
    user_id: str
    filename: str
    original_filename: Optional[str] = None
    file_path: str
    file_type: str = "application/pdf"
    file_size: int
    status: MaterialStatus = MaterialStatus.QUEUED
    processing_attempts: int = 0
    error_message: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    processed_at: Optional[datetime] = None

    model_config = {"populate_by_name": True}
