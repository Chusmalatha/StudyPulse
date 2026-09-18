"""
Project DB model definition.
"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class ProjectModel(BaseModel):
    """Internal representation of a Project document in MongoDB."""
    id: Optional[str] = None
    space_id: str
    user_id: str
    name: str
    description: str = ""
    learning_goal: str = ""
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
