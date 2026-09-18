"""
AI Tutor API Routes.

Endpoints:
- POST /api/v1/projects/{project_id}/tutor/conversations
- GET /api/v1/projects/{project_id}/tutor/conversations
- GET /api/v1/projects/{project_id}/tutor/conversations/{conversation_id}
- GET /api/v1/projects/{project_id}/tutor/conversations/{conversation_id}/messages
- POST /api/v1/projects/{project_id}/tutor/conversations/{conversation_id}/messages
"""
from typing import List
from fastapi import APIRouter, Depends, status, HTTPException

from app.api.dependencies import get_current_user
from app.schemas.auth import UserResponse
from app.schemas.tutor import (
    ConversationCreateSchema,
    ConversationResponseSchema,
    MessageCreateSchema,
    MessageResponseSchema,
    TutorAskResponseSchema,
)
from app.services import tutor_service

router = APIRouter(prefix="/projects/{project_id}/tutor", tags=["AI Tutor"])


@router.post(
    "/conversations",
    response_model=ConversationResponseSchema,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new AI Tutor conversation",
)
async def create_tutor_conversation(
    project_id: str,
    payload: ConversationCreateSchema = None,
    current_user: UserResponse = Depends(get_current_user),
):
    title = payload.title if payload else None
    try:
        return await tutor_service.create_conversation(project_id, current_user.id, title)
    except ValueError as exc:
        if str(exc) == "not_found":
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
        raise


@router.get(
    "/conversations",
    response_model=List[ConversationResponseSchema],
    summary="List all AI Tutor conversations for a project",
)
async def list_tutor_conversations(
    project_id: str,
    current_user: UserResponse = Depends(get_current_user),
):
    try:
        return await tutor_service.list_conversations(project_id, current_user.id)
    except ValueError as exc:
        if str(exc) == "not_found":
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
        raise


@router.get(
    "/conversations/{conversation_id}",
    response_model=ConversationResponseSchema,
    summary="Get conversation details by ID",
)
async def get_tutor_conversation(
    project_id: str,
    conversation_id: str,
    current_user: UserResponse = Depends(get_current_user),
):
    try:
        return await tutor_service.get_conversation(project_id, conversation_id, current_user.id)
    except ValueError as exc:
        if str(exc) == "not_found":
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project or conversation not found")
        raise


@router.get(
    "/conversations/{conversation_id}/messages",
    response_model=List[MessageResponseSchema],
    summary="List messages in a conversation",
)
async def list_tutor_messages(
    project_id: str,
    conversation_id: str,
    current_user: UserResponse = Depends(get_current_user),
):
    try:
        return await tutor_service.get_conversation_messages(project_id, conversation_id, current_user.id)
    except ValueError as exc:
        if str(exc) == "not_found":
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found")
        raise


@router.post(
    "/conversations/{conversation_id}/messages",
    response_model=TutorAskResponseSchema,
    summary="Send a question to the AI Tutor and receive a grounded answer with citations",
)
async def send_tutor_message(
    project_id: str,
    conversation_id: str,
    payload: MessageCreateSchema,
    current_user: UserResponse = Depends(get_current_user),
):
    try:
        return await tutor_service.ask_tutor(project_id, conversation_id, current_user.id, payload.message)
    except ValueError as exc:
        if str(exc) == "not_found":
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project or conversation not found")
        raise
