"""
Space DB model definition.
"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class SpaceModel(BaseModel):
    """Internal representation of a Space document in MongoDB."""
    id: Optional[str] = None
    user_id: str
    name: str
    description: str = ""
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
