"""
Message and Citation DB model definitions.
"""
from datetime import datetime, timezone
from enum import Enum
from typing import List, Optional, Any, Dict
from pydantic import BaseModel, Field


class MessageRole(str, Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class CitationModel(BaseModel):
    """Structured citation metadata pointing to an ingested knowledge chunk."""
    material_id: str
    filename: str
    page_number: int
    chunk_id: str
    relevance_score: float = 0.0


class MessageModel(BaseModel):
    """Internal representation of a Tutor Message document in MongoDB."""
    id: Optional[str] = Field(default=None, alias="_id")
    conversation_id: str
    project_id: str
    user_id: str
    role: MessageRole
    content: str
    citations: List[CitationModel] = Field(default_factory=list)
    grounded: bool = True
    retrieval_metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    model_config = {"populate_by_name": True}
