"""
Growth Snapshot and Recommendation DB models.
"""
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class MaterialReferenceModel(BaseModel):
    """Reference to a specific page or section in an uploaded PDF material."""
    material_id: str
    filename: str
    page_number: int


class GrowthSnapshotModel(BaseModel):
    """Snapshot of a concept's growth trajectory over time."""
    id: Optional[str] = Field(default=None, alias="_id")
    user_id: str
    project_id: str
    concept_id: str
    concept_name: str
    current_mastery: float
    previous_mastery: float
    change_percentage: float
    category: str  # "IMPROVING", "STABLE", "REQUIRING_ATTENTION", "INSUFFICIENT_EVIDENCE"
    evidence_count: int
    explanation: str
    last_evaluated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    model_config = {"populate_by_name": True}


class RecommendationModel(BaseModel):
    """Actionable study recommendation item generated for a learner."""
    id: Optional[str] = Field(default=None, alias="_id")
    user_id: str
    project_id: str
    concept_id: Optional[str] = None
    type: str  # "REVIEW_MATERIAL", "PRACTICE_QUIZ", "PRACTICE_OPEN_ENDED", "REVIEW_CONCEPT", "REVISIT_TUTOR"
    title: str
    description: str
    reason: str
    action: str
    material_references: List[MaterialReferenceModel] = Field(default_factory=list)
    priority: str = "MEDIUM"  # "HIGH", "MEDIUM", "LOW"
    status: str = "PENDING"  # "PENDING", "IN_PROGRESS", "COMPLETED", "DISMISSED"
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    completed_at: Optional[datetime] = None
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    model_config = {"populate_by_name": True}
