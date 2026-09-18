"""
Pydantic schemas for Activity Events API.
"""
from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class ActivityEventResponse(BaseModel):
    """Public schema for an activity event."""
    id: str
    event_type: str
    user_id: str
    project_id: Optional[str] = None
    entity_type: str
    entity_id: str
    payload: Dict[str, Any] = Field(default_factory=dict)
    correlation_id: str
    status: str
    attempts: int
    error: Optional[str] = None
    created_at: datetime
    processed_at: Optional[datetime] = None


class EventListResponse(BaseModel):
    """API response schema for event list queries."""
    project_id: str
    total_count: int
    events: List[ActivityEventResponse]


class WorkflowStatusResponse(BaseModel):
    """API response schema for background workflow execution status."""
    correlation_id: str
    project_id: str
    status: str  # COMPLETED, PROCESSING, FAILED, RETRY
    completed_steps: List[str]
    pending_steps: List[str]
    last_error: Optional[str] = None
    updated_at: datetime
