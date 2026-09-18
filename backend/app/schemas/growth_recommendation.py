"""
Pydantic schemas for Growth Analysis and Recommendations APIs.
"""
from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class MaterialReferenceSchema(BaseModel):
    """Public schema for a grounded material page reference."""
    material_id: str
    filename: str
    page_number: int


class GrowthSnapshotResponse(BaseModel):
    """API response schema for concept growth evaluation."""
    id: Optional[str] = None
    concept_id: str
    concept_name: str
    current_mastery: float
    previous_mastery: float
    change_percentage: float
    category: str  # "IMPROVING", "STABLE", "REQUIRING_ATTENTION", "INSUFFICIENT_EVIDENCE"
    evidence_count: int
    explanation: str
    last_evaluated_at: datetime


class ProjectGrowthResponse(BaseModel):
    """API response schema for overall project growth summary."""
    project_id: str
    improving_count: int
    stable_count: int
    requiring_attention_count: int
    insufficient_evidence_count: int
    total_concepts: int
    ai_narrative: Optional[str] = None  # AI-generated learning status summary
    snapshots: List[GrowthSnapshotResponse]


class RecommendationResponse(BaseModel):
    """API response schema for an actionable recommendation."""
    id: str
    project_id: str
    concept_id: Optional[str] = None
    type: str
    title: str
    description: str
    reason: str
    action: str
    material_references: List[MaterialReferenceSchema] = Field(default_factory=list)
    priority: str
    status: str
    created_at: datetime
    completed_at: Optional[datetime] = None


class RecommendationCompleteRequest(BaseModel):
    """Optional request payload when completing a recommendation."""
    notes: Optional[str] = None
