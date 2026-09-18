"""
AIUsage DB Model definition for tracking AI operations, latency, tokens, costs, and correlation IDs.
"""
from datetime import datetime, timezone
from enum import Enum
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field


class AIFeature(str, Enum):
    TUTOR = "TUTOR"
    KNOWLEDGE_EXTRACTION = "KNOWLEDGE_EXTRACTION"
    EMBEDDING = "EMBEDDING"
    QUIZ_GENERATION = "QUIZ_GENERATION"
    OPEN_ENDED_EVALUATION = "OPEN_ENDED_EVALUATION"
    RECOMMENDATION = "RECOMMENDATION"
    OTHER = "OTHER"


class AIUsageModel(BaseModel):
    """Internal MongoDB representation of an AI operation log."""
    id: Optional[str] = Field(default=None, alias="_id")
    user_id: str
    project_id: Optional[str] = None
    feature: AIFeature
    model: str
    provider: str
    started_at: datetime
    completed_at: datetime
    latency_ms: float
    input_tokens: Optional[int] = None
    output_tokens: Optional[int] = None
    total_tokens: Optional[int] = None
    estimated_cost: Optional[float] = None
    success: bool = True
    error_type: Optional[str] = None
    error_message: Optional[str] = None
    request_id: Optional[str] = None
    correlation_id: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    model_config = {"populate_by_name": True}
