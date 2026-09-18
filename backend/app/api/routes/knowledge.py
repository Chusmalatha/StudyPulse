"""
Knowledge Extraction & RAG Retrieval API routes.

All routes require authentication via Depends(get_current_user).
Ownership and project data isolation are strictly enforced.
"""
from fastapi import APIRouter, Depends, HTTPException, status

from app.api.dependencies import get_current_user
from app.schemas.auth import UserResponse
from app.schemas.knowledge import (
    SearchQueryRequest,
    SearchResponse,
    ProjectKnowledgeResponse,
)
from app.services import knowledge_extraction_service, retrieval_service

router = APIRouter(tags=["knowledge"])


def _handle_error(exc: ValueError) -> HTTPException:
    msg = str(exc)
    if msg == "not_found" or "not found" in msg.lower():
        return HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found or access denied.",
        )
    return HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail=msg,
    )


@router.post("/projects/{project_id}/search", response_model=SearchResponse)
async def search_project_knowledge(
    project_id: str,
    payload: SearchQueryRequest,
    current_user: UserResponse = Depends(get_current_user),
):
    """
    Perform semantic vector RAG search inside a project's knowledge base.
    Restricted strictly to project_id owned by current authenticated user.
    """
    try:
        return await retrieval_service.search_project_knowledge(
            project_id=project_id,
            user_id=current_user.id,
            query=payload.query,
            top_k=payload.top_k,
        )
    except ValueError as exc:
        raise _handle_error(exc)


@router.get("/projects/{project_id}/knowledge", response_model=ProjectKnowledgeResponse)
async def get_project_knowledge(
    project_id: str,
    current_user: UserResponse = Depends(get_current_user),
):
    """
    Retrieve extracted concepts, topics, and sections for a project.
    """
    try:
        return await knowledge_extraction_service.get_project_knowledge(
            project_id=project_id,
            user_id=current_user.id,
        )
    except ValueError as exc:
        raise _handle_error(exc)


@router.post("/projects/{project_id}/knowledge/extract", response_model=ProjectKnowledgeResponse)
async def trigger_knowledge_extraction(
    project_id: str,
    current_user: UserResponse = Depends(get_current_user),
):
    """
    Manually trigger or re-run knowledge extraction over project's ready materials.
    """
    try:
        return await knowledge_extraction_service.extract_project_knowledge(
            project_id=project_id,
            user_id=current_user.id,
        )
    except ValueError as exc:
        raise _handle_error(exc)
