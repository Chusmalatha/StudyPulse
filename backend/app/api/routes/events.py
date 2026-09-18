"""
Events API Routes.

Endpoints:
- GET /api/v1/projects/{project_id}/events
- GET /api/v1/projects/{project_id}/events/{event_id}
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, status, HTTPException, Query

from app.api.dependencies import get_current_user
from app.schemas.auth import UserResponse
from app.schemas.events import EventListResponse, ActivityEventResponse
from app.services import event_publisher

router = APIRouter(prefix="/projects/{project_id}/events", tags=["Events"])


@router.get(
    "",
    response_model=EventListResponse,
    summary="Get chronological activity events stream for a project",
)
async def get_project_events(
    project_id: str,
    event_type: Optional[str] = Query(None, description="Filter by event type"),
    correlation_id: Optional[str] = Query(None, description="Filter by correlation ID"),
    limit: int = Query(50, ge=1, le=200, description="Max events to return"),
    skip: int = Query(0, ge=0, description="Number of events to skip"),
    current_user: UserResponse = Depends(get_current_user),
):
    try:
        events, total = await event_publisher.get_events_by_project(
            project_id=project_id,
            user_id=current_user.id,
            event_type=event_type,
            correlation_id=correlation_id,
            limit=limit,
            skip=skip,
        )
        return EventListResponse(
            project_id=project_id,
            total_count=total,
            events=events,
        )
    except ValueError as exc:
        if str(exc) == "not_found":
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
        raise


@router.get(
    "/{event_id}",
    response_model=ActivityEventResponse,
    summary="Get single activity event details",
)
async def get_event_detail(
    project_id: str,
    event_id: str,
    current_user: UserResponse = Depends(get_current_user),
):
    try:
        return await event_publisher.get_event_by_id(
            project_id=project_id,
            event_id=event_id,
            user_id=current_user.id,
        )
    except ValueError as exc:
        if str(exc) == "not_found":
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Event not found")
        raise
