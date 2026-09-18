"""
ActivityEvent DB model definition.
"""
from datetime import datetime, timezone
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field


class ActivityEventModel(BaseModel):
    """Internal representation of an Activity Event document in MongoDB."""
    id: Optional[str] = Field(default=None, alias="_id")
    event_type: str
    user_id: str
    project_id: Optional[str] = None
    space_id: Optional[str] = None
    entity_type: str = "project"  # e.g., material, assessment, question, concept, recommendation, conversation
    entity_id: str
    payload: Dict[str, Any] = Field(default_factory=dict)
    correlation_id: str
    status: str = "PROCESSED"  # PROCESSED, PENDING, FAILED, RETRY
    attempts: int = 0
    error: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    processed_at: Optional[datetime] = None

    model_config = {"populate_by_name": True}
