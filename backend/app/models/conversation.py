"""
Conversation DB model definition.
"""
from datetime import datetime, timezone
from typing import Optional
from pydantic import BaseModel, Field


class ConversationModel(BaseModel):
    """Internal representation of a Tutor Conversation document in MongoDB."""
    id: Optional[str] = Field(default=None, alias="_id")
    project_id: str
    user_id: str
    title: str = "New Conversation"
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    last_message_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    model_config = {"populate_by_name": True}
