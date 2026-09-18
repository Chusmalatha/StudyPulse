"""
Pydantic schemas for Mastery and Learning Context APIs.
"""
from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class ConceptMasteryResponse(BaseModel):
    """API schema for concept mastery details."""
    concept_id: str
    name: str
    description: str
    mastery_score: float
    confidence: float
    attempts: int
    correct: int
    mistakes: int
    last_updated: Optional[datetime] = None


class ProjectMasterySummaryResponse(BaseModel):
    """API schema for project-wide mastery summary."""
    project_id: str
    overall_mastery: float
    total_concepts: int
    practiced_concepts: int
    concepts: List[ConceptMasteryResponse]


class MasteryEventResponse(BaseModel):
    """API schema for mastery history log entry."""
    id: str
    concept_id: str
    previous_score: float
    new_score: float
    previous_confidence: float
    new_confidence: float
    evidence_type: str
    evidence_id: str
    reason: str
    created_at: datetime


class RepeatedMistakeResponse(BaseModel):
    """API schema for repeated mistake entry."""
    id: str
    concept_id: str
    mistake_description: str
    occurrence_count: int
    first_seen: datetime
    last_seen: datetime


class ConceptDetailMasteryResponse(ConceptMasteryResponse):
    """Detailed concept mastery including recent audit events and repeated mistakes."""
    recent_events: List[MasteryEventResponse] = Field(default_factory=list)
    repeated_mistakes: List[RepeatedMistakeResponse] = Field(default_factory=list)


class LearningContextResponse(BaseModel):
    """API schema for persistent learning context."""
    id: str
    project_id: Optional[str] = None
    context_type: str
    key: str
    value: str
    importance: float
    source: str
    confidence: float
    last_updated: datetime
    metadata: Dict[str, Any] = Field(default_factory=dict)
