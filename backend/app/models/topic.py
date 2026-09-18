"""
Topic DB model definition.
"""
from datetime import datetime, timezone
from typing import List, Optional
from pydantic import BaseModel, Field


class TopicModel(BaseModel):
    """Internal representation of an extracted Topic document in MongoDB."""
    id: Optional[str] = Field(default=None, alias="_id")
    project_id: str
    name: str
    description: str
    source_material_ids: List[str] = Field(default_factory=list)
    source_pages: List[int] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    model_config = {"populate_by_name": True}
