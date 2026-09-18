"""
Section DB model definition.
"""
from datetime import datetime, timezone
from typing import Optional
from pydantic import BaseModel, Field


class SectionModel(BaseModel):
    """Internal representation of an extracted document Section in MongoDB."""
    id: Optional[str] = Field(default=None, alias="_id")
    project_id: str
    material_id: str
    title: str
    page_start: int
    page_end: int
    section_order: int = 0
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    model_config = {"populate_by_name": True}
