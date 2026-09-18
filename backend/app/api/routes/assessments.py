"""
Assessment API Routes.

Endpoints:
- POST /api/v1/projects/{project_id}/assessments
- GET /api/v1/projects/{project_id}/assessments
- GET /api/v1/projects/{project_id}/assessments/{assessment_id}
- POST /api/v1/projects/{project_id}/assessments/{assessment_id}/questions/{question_id}/answer
- POST /api/v1/projects/{project_id}/assessments/{assessment_id}/complete
"""
from typing import List
from fastapi import APIRouter, Depends, status, HTTPException, BackgroundTasks

from app.api.dependencies import get_current_user
from app.schemas.auth import UserResponse
from app.schemas.assessment import (
    AssessmentCreateSchema,
    AssessmentResponseSchema,
    AnswerSubmitSchema,
    QuestionResultResponseSchema,
)
from app.services import assessment_service

router = APIRouter(prefix="/projects/{project_id}/assessments", tags=["Assessments"])


@router.post(
    "",
    response_model=AssessmentResponseSchema,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new adaptive assessment",
)
async def create_assessment(
    project_id: str,
    payload: AssessmentCreateSchema = None,
    current_user: UserResponse = Depends(get_current_user),
):
    q_count = payload.question_count if payload else 5
    target_cid = payload.target_concept_id if payload else None
    try:
        return await assessment_service.create_assessment(
            project_id=project_id,
            user_id=current_user.id,
            question_count=q_count,
            target_concept_id=target_cid,
        )
    except ValueError as exc:
        if str(exc) == "not_found":
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
        raise


@router.get(
    "",
    response_model=List[AssessmentResponseSchema],
    summary="List past assessments for a project",
)
async def list_assessments(
    project_id: str,
    current_user: UserResponse = Depends(get_current_user),
):
    try:
        return await assessment_service.list_assessments(project_id, current_user.id)
    except ValueError as exc:
        if str(exc) == "not_found":
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
        raise


@router.get(
    "/{assessment_id}",
    response_model=AssessmentResponseSchema,
    summary="Get assessment details and question list",
)
async def get_assessment(
    project_id: str,
    assessment_id: str,
    current_user: UserResponse = Depends(get_current_user),
):
    try:
        return await assessment_service.get_assessment(project_id, assessment_id, current_user.id)
    except ValueError as exc:
        if str(exc) == "not_found":
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Assessment not found")
        raise


@router.post(
    "/{assessment_id}/questions/{question_id}/answer",
    response_model=QuestionResultResponseSchema,
    summary="Submit answer for MCQ or Open-Ended question",
)
async def submit_question_answer(
    project_id: str,
    assessment_id: str,
    question_id: str,
    payload: AnswerSubmitSchema,
    current_user: UserResponse = Depends(get_current_user),
):
    try:
        return await assessment_service.answer_question(
            project_id=project_id,
            assessment_id=assessment_id,
            question_id=question_id,
            user_id=current_user.id,
            student_answer=payload.answer,
        )
    except ValueError as exc:
        if str(exc) == "not_found":
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Question or assessment not found")
        raise


@router.post(
    "/{assessment_id}/complete",
    response_model=AssessmentResponseSchema,
    summary="Complete an assessment and calculate score",
)
async def complete_assessment(
    project_id: str,
    assessment_id: str,
    background_tasks: BackgroundTasks,
    current_user: UserResponse = Depends(get_current_user),
):
    try:
        return await assessment_service.complete_assessment(
            project_id=project_id,
            assessment_id=assessment_id,
            user_id=current_user.id,
            background_tasks=background_tasks,
        )
    except ValueError as exc:
        if str(exc) == "not_found":
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Assessment not found")
        raise
