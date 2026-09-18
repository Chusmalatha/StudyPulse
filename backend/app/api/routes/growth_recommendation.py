"""
API Router for Growth Analysis and Study Recommendations.
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from bson import ObjectId

from app.models.user import UserModel
from app.schemas.growth_recommendation import (
    ProjectGrowthResponse,
    RecommendationResponse,
    RecommendationCompleteRequest,
)
from app.api.dependencies import get_current_user
from app.services.growth_analysis_service import GrowthAnalysisService
from app.services.recommendation_service import RecommendationService

router = APIRouter(prefix="/projects", tags=["growth_recommendations"])


@router.get("/{project_id}/growth", response_model=ProjectGrowthResponse)
async def get_project_growth_analysis(
    project_id: str,
    current_user: UserModel = Depends(get_current_user),
):
    """
    Get growth analysis summary and concept trajectories for a project.
    Strictly isolated to user & project.
    """
    service = GrowthAnalysisService()
    try:
        return await service.analyze_project_growth(project_id, current_user.id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")


@router.get("/{project_id}/recommendations", response_model=List[RecommendationResponse])
async def get_project_recommendations(
    project_id: str,
    current_user: UserModel = Depends(get_current_user),
):
    """
    Get active study recommendations for a project.
    """
    service = RecommendationService()
    try:
        return await service.get_project_recommendations(project_id, current_user.id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")


@router.post("/{project_id}/recommendations/generate", response_model=List[RecommendationResponse])
async def generate_project_recommendations(
    project_id: str,
    current_user: UserModel = Depends(get_current_user),
):
    """
    Manually trigger/refresh recommendation generation for a project.
    """
    service = RecommendationService()
    try:
        return await service.generate_recommendations(project_id, current_user.id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")


@router.post("/{project_id}/recommendations/{recommendation_id}/complete", response_model=RecommendationResponse)
async def complete_recommendation(
    project_id: str,
    recommendation_id: str,
    current_user: UserModel = Depends(get_current_user),
):
    """
    Mark a study recommendation as COMPLETED.
    """
    if not ObjectId.is_valid(recommendation_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Recommendation not found")

    service = RecommendationService()
    try:
        return await service.complete_recommendation(recommendation_id, project_id, current_user.id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))


@router.post("/{project_id}/recommendations/{recommendation_id}/dismiss")
async def dismiss_recommendation(
    project_id: str,
    recommendation_id: str,
    current_user: UserModel = Depends(get_current_user),
):
    """
    Dismiss a recommendation.
    """
    if not ObjectId.is_valid(recommendation_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Recommendation not found")

    service = RecommendationService()
    try:
        success = await service.dismiss_recommendation(recommendation_id, project_id, current_user.id)
        if not success:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Recommendation not found")
        return {"status": "success", "message": "Recommendation dismissed"}
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
