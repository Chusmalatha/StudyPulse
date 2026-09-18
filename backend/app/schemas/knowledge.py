"""
Pydantic schemas for Knowledge Extraction and RAG Retrieval API payloads.
"""
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field


class ConceptResponse(BaseModel):
    id: str
    project_id: str
    name: str
    description: str
    source_material_ids: List[str] = Field(default_factory=list)
    source_pages: List[int] = Field(default_factory=list)
    created_at: Optional[datetime] = None


class TopicResponse(BaseModel):
    id: str
    project_id: str
    name: str
    description: str
    source_material_ids: List[str] = Field(default_factory=list)
    source_pages: List[int] = Field(default_factory=list)
    created_at: Optional[datetime] = None


class SectionResponse(BaseModel):
    id: str
    project_id: str
    material_id: str
    title: str
    page_start: int
    page_end: int
    section_order: int
    created_at: Optional[datetime] = None


class ProjectKnowledgeResponse(BaseModel):
    project_id: str
    concepts: List[ConceptResponse] = Field(default_factory=list)
    topics: List[TopicResponse] = Field(default_factory=list)
    sections: List[SectionResponse] = Field(default_factory=list)


class SearchQueryRequest(BaseModel):
    query: str = Field(..., min_length=1, description="Semantic search query text")
    top_k: int = Field(default=5, ge=1, le=50, description="Maximum number of relevant chunks to return")


class SearchResultItem(BaseModel):
    chunk_id: str
    material_id: str
    filename: str
    page_number: int
    chunk_text: str
    score: float


class SearchResponse(BaseModel):
    query: str
    project_id: str
    results: List[SearchResultItem] = Field(default_factory=list)
    total_results: int
