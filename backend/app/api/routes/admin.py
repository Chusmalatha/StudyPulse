"""
Admin Dashboard API Routes.

Protected strictly with require_admin dependency. Returns 403 Forbidden for non-admin users.

Endpoints:
- GET /api/v1/admin/overview
- GET /api/v1/admin/users
- GET /api/v1/admin/users/{user_id}
- GET /api/v1/admin/activity
- GET /api/v1/admin/engagement
- GET /api/v1/admin/ai-usage
- GET /api/v1/admin/ai-evaluation
- GET /api/v1/admin/jobs
- GET /api/v1/admin/jobs/{job_id}
- GET /api/v1/admin/system-health
"""
from typing import Optional
from fastapi import APIRouter, Depends, status, HTTPException, Query

from app.api.dependencies import require_admin
from app.schemas.auth import UserResponse
from app.schemas.analytics import (
    AdminOverviewResponse,
    AdminUserListResponse,
    AdminUserJourneyResponse,
    AdminActivityListResponse,
    AdminEngagementResponse,
    AdminAIUsageResponse,
    AdminAIEvaluationResponse,
    AdminJobsResponse,
    AdminJobItem,
    AdminSystemHealthResponse,
)
from app.services import analytics_service

router = APIRouter(prefix="/admin", tags=["Admin"])


@router.get(
    "/overview",
    response_model=AdminOverviewResponse,
    summary="Get top-level system metrics for Admin Dashboard",
)
async def get_admin_overview(
    admin: UserResponse = Depends(require_admin),
):
    return await analytics_service.get_admin_overview()


@router.get(
    "/users",
    response_model=AdminUserListResponse,
    summary="Get paginated list of registered users with activity stats",
)
async def get_admin_users(
    limit: int = Query(50, ge=1, le=200),
    skip: int = Query(0, ge=0),
    admin: UserResponse = Depends(require_admin),
):
    return await analytics_service.get_admin_users(limit=limit, skip=skip)


@router.get(
    "/users/{user_id}",
    response_model=AdminUserJourneyResponse,
    summary="Inspect an individual user's complete learning journey",
)
async def get_admin_user_journey(
    user_id: str,
    admin: UserResponse = Depends(require_admin),
):
    try:
        return await analytics_service.get_admin_user_journey(user_id)
    except ValueError as exc:
        if str(exc) == "not_found":
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
        raise


@router.get(
    "/activity",
    response_model=AdminActivityListResponse,
    summary="Get global activity event stream with optional filters",
)
async def get_admin_activity(
    event_type: Optional[str] = Query(None),
    user_id: Optional[str] = Query(None),
    project_id: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=200),
    skip: int = Query(0, ge=0),
    admin: UserResponse = Depends(require_admin),
):
    return await analytics_service.get_admin_activity(
        event_type=event_type,
        user_id=user_id,
        project_id=project_id,
        limit=limit,
        skip=skip,
    )


@router.get(
    "/engagement",
    response_model=AdminEngagementResponse,
    summary="Get active learner engagement metrics (DAL/WAL/MAL)",
)
async def get_admin_engagement(
    admin: UserResponse = Depends(require_admin),
):
    return await analytics_service.get_admin_engagement()


@router.get(
    "/ai-usage",
    response_model=AdminAIUsageResponse,
    summary="Get AI usage breakdown across operations",
)
async def get_admin_ai_usage(
    admin: UserResponse = Depends(require_admin),
):
    return await analytics_service.get_admin_ai_usage()


@router.get(
    "/ai-evaluation",
    response_model=AdminAIEvaluationResponse,
    summary="Get AI quality evaluation and tutor grounding metrics",
)
async def get_admin_ai_evaluation(
    admin: UserResponse = Depends(require_admin),
):
    return await analytics_service.get_admin_ai_evaluation()


@router.get(
    "/jobs",
    response_model=AdminJobsResponse,
    summary="Get background worker jobs status distribution and job list",
)
async def get_admin_jobs(
    status: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=200),
    skip: int = Query(0, ge=0),
    admin: UserResponse = Depends(require_admin),
):
    return await analytics_service.get_admin_jobs(status=status, limit=limit, skip=skip)


@router.get(
    "/system-health",
    response_model=AdminSystemHealthResponse,
    summary="Get real-time application system health checks",
)
async def get_admin_system_health(
    admin: UserResponse = Depends(require_admin),
):
    return await analytics_service.get_admin_system_health()
