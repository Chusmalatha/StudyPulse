"""
Pydantic schemas for Tutor API endpoints.
"""
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field


class CitationSchema(BaseModel):
    material_id: str
    filename: str
    page_number: int
    chunk_id: str
    relevance_score: float = 0.0


class ConversationCreateSchema(BaseModel):
    title: Optional[str] = None


class ConversationResponseSchema(BaseModel):
    id: str
    project_id: str
    user_id: str
    title: str
    created_at: datetime
    updated_at: datetime
    last_message_at: datetime

    model_config = {"populate_by_name": True, "from_attributes": True}


class MessageCreateSchema(BaseModel):
    message: str = Field(..., min_length=1, max_length=4000)


class MessageResponseSchema(BaseModel):
    id: str
    conversation_id: str
    project_id: str
    user_id: str
    role: str
    content: str
    citations: List[CitationSchema] = Field(default_factory=list)
    grounded: bool = True
    created_at: datetime

    model_config = {"populate_by_name": True, "from_attributes": True}


class TutorAskResponseSchema(BaseModel):
    answer: str
    citations: List[CitationSchema] = Field(default_factory=list)
    conversation_id: str
    message_id: str
    user_message_id: str
    grounded: bool = True
    unsupported: bool = False
