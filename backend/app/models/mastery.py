"""
Mastery, Repeated Mistakes, and Learning Context DB models.
"""
from datetime import datetime, timezone
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field


class MasteryEventModel(BaseModel):
    """Audit record for a concept mastery update."""
    id: Optional[str] = Field(default=None, alias="_id")
    concept_id: str
    project_id: str
    user_id: str
    previous_score: float
    new_score: float
    previous_confidence: float
    new_confidence: float
    evidence_type: str  # "MCQ", "OPEN_ENDED", "TUTOR_EVALUATION"
    evidence_id: str    # attempt_id or evidence tracking ID
    reason: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    model_config = {"populate_by_name": True}


class RepeatedMistakeModel(BaseModel):
    """Record of specific conceptual mistakes observed during assessments."""
    id: Optional[str] = Field(default=None, alias="_id")
    user_id: str
    project_id: str
    concept_id: str
    mistake_description: str
    occurrence_count: int = 1
    first_seen: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    last_seen: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    model_config = {"populate_by_name": True}


class LearningContextModel(BaseModel):
    """Structured memory item representing student context for RAG and Tutor."""
    id: Optional[str] = Field(default=None, alias="_id")
    user_id: str
    project_id: Optional[str] = None  # None if global preference
    context_type: str  # GOAL, STRENGTH, WEAKNESS, TUTOR_CONTEXT, ASSESSMENT_PATTERN, REPEATED_MISTAKE, PREFERENCE
    key: str
    value: str
    importance: float = 1.0
    source: str = "SYSTEM"  # SYSTEM, ASSESSMENT, TUTOR, MANUAL
    confidence: float = 1.0
    first_seen: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    last_updated: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: Dict[str, Any] = Field(default_factory=dict)

    model_config = {"populate_by_name": True}
