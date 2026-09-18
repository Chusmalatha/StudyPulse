"""
AIEvaluation DB Model definition for capturing deterministic evaluation metrics of AI outputs.
"""
from datetime import datetime, timezone
from enum import Enum
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field


class AIEvaluationType(str, Enum):
    TUTOR_GROUNDING = "TUTOR_GROUNDING"
    RETRIEVAL_ACCURACY = "RETRIEVAL_ACCURACY"
    QUIZ_STRUCTURE = "QUIZ_STRUCTURE"
    OPEN_ENDED_ACCURACY = "OPEN_ENDED_ACCURACY"
    RECOMMENDATION_RELEVANCE = "RECOMMENDATION_RELEVANCE"


class AIEvaluationModel(BaseModel):
    """Internal MongoDB representation of an AI Evaluation result."""
    id: Optional[str] = Field(default=None, alias="_id")
    user_id: str
    project_id: str
    feature: str
    evaluation_type: AIEvaluationType
    input_reference: Optional[str] = None  # e.g., message_id, assessment_id, recommendation_id
    criteria: Dict[str, Any] = Field(default_factory=dict)
    result: Dict[str, Any] = Field(default_factory=dict)
    passed: bool = True
    score: float = 1.0  # 0.0 to 1.0
    details: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    model_config = {"populate_by_name": True}
