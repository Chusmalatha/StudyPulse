"""
Pydantic schemas for Material API request/response payloads.
"""
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel


class MaterialResponse(BaseModel):
    id: str
    project_id: str
    user_id: str
    filename: str
    original_filename: Optional[str] = None
    file_type: str
    file_size: int
    status: str
    processing_attempts: int
    error_message: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    processed_at: Optional[datetime] = None


class ChunkResponse(BaseModel):
    id: str
    project_id: str
    material_id: str
    filename: str
    page_number: int
    chunk_index: int
    chunk_text: str
    created_at: Optional[datetime] = None


class MaterialRetryResponse(BaseModel):
    material_id: str
    status: str
    processing_attempts: int
    message: str
