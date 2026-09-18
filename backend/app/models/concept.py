"""
Concept DB model definition.
"""
from datetime import datetime, timezone
from typing import List, Optional
from pydantic import BaseModel, Field


class ConceptModel(BaseModel):
    """Internal representation of an extracted Concept document in MongoDB."""
    id: Optional[str] = Field(default=None, alias="_id")
    project_id: str
    name: str
    description: str
    source_material_ids: List[str] = Field(default_factory=list)
    source_pages: List[int] = Field(default_factory=list)
    
    # Mastery fields (Phase 7)
    mastery_score: float = 0.0
    confidence: float = 0.0
    attempts: int = 0
    correct: int = 0
    mistakes: int = 0
    last_updated: Optional[datetime] = None
    
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    model_config = {"populate_by_name": True}

