"""
Material API routes.

All routes require authentication via Depends(get_current_user).
Ownership and isolation are strictly enforced inside the material_service layer.
"""
from typing import List
from fastapi import APIRouter, Depends, File, UploadFile, BackgroundTasks, HTTPException, status

from app.api.dependencies import get_current_user
from app.schemas.auth import UserResponse
from app.schemas.materials import MaterialResponse, ChunkResponse, MaterialRetryResponse
from app.services import material_service

router = APIRouter(tags=["materials"])


def _handle_error(exc: ValueError) -> HTTPException:
    msg = str(exc)
    if msg == "not_found" or "not found" in msg.lower():
        return HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Material or Project not found.",
        )
    return HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail=msg,
    )


@router.post("/projects/{project_id}/materials", response_model=MaterialResponse, status_code=status.HTTP_201_CREATED)
async def upload_material(
    project_id: str,
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    current_user: UserResponse = Depends(get_current_user),
):
    """
    Upload a PDF material file for a Project.
    Validates project ownership, file type, and file size.
    Immediately queues background text extraction & chunking task.
    """
    try:
        return await material_service.create_material(project_id, current_user.id, file, background_tasks)
    except ValueError as exc:
        raise _handle_error(exc)


@router.get("/projects/{project_id}/materials", response_model=List[MaterialResponse])
async def list_project_materials(
    project_id: str,
    current_user: UserResponse = Depends(get_current_user),
):
    """
    List all materials uploaded to a Project (project ownership validated).
    """
    try:
        return await material_service.get_materials_by_project(project_id, current_user.id)
    except ValueError as exc:
        raise _handle_error(exc)


@router.get("/materials/{material_id}", response_model=MaterialResponse)
@router.get("/projects/{project_id}/materials/{material_id}", response_model=MaterialResponse)
async def get_material_status(
    material_id: str,
    project_id: str = None,
    current_user: UserResponse = Depends(get_current_user),
):
    """
    Get single material details & processing status (QUEUED, PROCESSING, READY, FAILED).
    """
    try:
        return await material_service.get_material(material_id, current_user.id)
    except ValueError as exc:
        raise _handle_error(exc)



@router.post("/materials/{material_id}/retry", response_model=MaterialRetryResponse)
async def retry_failed_material(
    material_id: str,
    background_tasks: BackgroundTasks,
    current_user: UserResponse = Depends(get_current_user),
):
    """
    Retry background processing for a failed material.
    Resets status to QUEUED and queues processing task.
    """
    try:
        return await material_service.retry_material(material_id, current_user.id, background_tasks)
    except ValueError as exc:
        raise _handle_error(exc)


@router.get("/materials/{material_id}/chunks", response_model=List[ChunkResponse])
async def get_material_chunks(
    material_id: str,
    current_user: UserResponse = Depends(get_current_user),
):
    """
    Get processed chunks for a material (includes page_number for citation verification).
    """
    try:
        return await material_service.get_material_chunks(material_id, current_user.id)
    except ValueError as exc:
        raise _handle_error(exc)


@router.delete("/materials/{material_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_material(
    material_id: str,
    current_user: UserResponse = Depends(get_current_user),
):
    """
    Delete a Material, its physical file from disk, and all associated chunks.
    """
    try:
        await material_service.delete_material(material_id, current_user.id)
    except ValueError as exc:
        raise _handle_error(exc)
