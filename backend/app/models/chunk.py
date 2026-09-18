"""
Chunk DB model definition.
"""
from datetime import datetime, timezone
from typing import List, Optional
from pydantic import BaseModel, Field


class ChunkModel(BaseModel):
    """Internal representation of a processed text Chunk document in MongoDB."""
    id: Optional[str] = Field(default=None, alias="_id")
    project_id: str
    material_id: str
    filename: str
    page_number: int
    chunk_index: int
    chunk_text: str
    embedding: List[float] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    model_config = {"populate_by_name": True}
