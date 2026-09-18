"""
Pydantic models that represent documents stored in MongoDB.
These are NOT the API schemas (see app/schemas/); they map 1-to-1 with DB docs.
"""
from datetime import datetime, timezone
from enum import Enum
from typing import Optional

from pydantic import BaseModel, EmailStr, Field
from bson import ObjectId


class UserRole(str, Enum):
    user = "user"
    admin = "admin"


class UserModel(BaseModel):
    """
    Represents a user document as stored in MongoDB.
    The `id` field maps to MongoDB's `_id` (stored/returned as a string).
    """
    id: Optional[str] = Field(default=None, alias="_id")
    name: str
    email: EmailStr
    password_hash: str
    role: UserRole = UserRole.user
    is_active: bool = True
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    model_config = {"populate_by_name": True}
