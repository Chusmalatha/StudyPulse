"""
User & Project Analytics API Routes.

Endpoints:
- GET /api/v1/projects/{project_id}/analytics
- GET /api/v1/analytics/overview
"""
from fastapi import APIRouter, Depends, status, HTTPException

from app.api.dependencies import get_current_user
from app.schemas.auth import UserResponse
from app.schemas.analytics import ProjectAnalyticsResponse, GlobalAnalyticsResponse
from app.services import analytics_service

router = APIRouter(prefix="", tags=["Analytics"])


@router.get(
    "/projects/{project_id}/analytics",
    response_model=ProjectAnalyticsResponse,
    summary="Get project-level learning analytics, quiz performance, concept trends, and AI activity",
)
async def get_project_analytics(
    project_id: str,
    current_user: UserResponse = Depends(get_current_user),
):
    try:
        return await analytics_service.get_project_analytics(project_id, current_user.id)
    except ValueError as exc:
        if str(exc) == "not_found":
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
        raise


@router.get(
    "/analytics/overview",
    response_model=GlobalAnalyticsResponse,
    summary="Get global learning analytics summary across all user spaces and projects",
)
async def get_global_analytics(
    current_user: UserResponse = Depends(get_current_user),
):
    return await analytics_service.get_global_analytics(current_user.id)
