"""
Space routes + nested Project routes.

All routes require authentication (get_current_user dependency).
Authorization is enforced inside the service layer via user_id queries.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from typing import List

from app.api.dependencies import get_current_user
from app.schemas.auth import UserResponse
from app.schemas.spaces import SpaceCreate, SpaceUpdate, SpaceResponse
from app.schemas.projects import ProjectCreate, ProjectResponse
from app.services import space_service, project_service

router = APIRouter(prefix="/spaces", tags=["spaces"])

# ── helper ─────────────────────────────────────────────────────────────────────

def _not_found_or_forbidden(exc: ValueError) -> HTTPException:
    """
    Convert service ValueError to HTTP 404.
    We intentionally do NOT distinguish between 'not found' and 'unauthorized'
    to avoid leaking the existence of other users' resources.
    """
    return HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Space not found.",
    )


def _project_not_found() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Project not found.",
    )


def _validation_error(exc: ValueError) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        detail=str(exc),
    )


# ── Space CRUD ──────────────────────────────────────────────────────────────────

@router.post("", response_model=SpaceResponse, status_code=status.HTTP_201_CREATED)
async def create_space(
    data: SpaceCreate,
    current_user: UserResponse = Depends(get_current_user),
):
    """Create a new Space for the authenticated user."""
    return await space_service.create_space(current_user.id, data)


@router.get("", response_model=List[SpaceResponse])
async def list_spaces(
    current_user: UserResponse = Depends(get_current_user),
):
    """List all Spaces belonging to the authenticated user."""
    return await space_service.get_spaces(current_user.id)


@router.get("/{space_id}", response_model=SpaceResponse)
async def get_space(
    space_id: str,
    current_user: UserResponse = Depends(get_current_user),
):
    """Get a single Space (ownership validated)."""
    try:
        return await space_service.get_space(space_id, current_user.id)
    except ValueError:
        raise _not_found_or_forbidden(ValueError())


@router.put("/{space_id}", response_model=SpaceResponse)
@router.patch("/{space_id}", response_model=SpaceResponse)
async def update_space(
    space_id: str,
    data: SpaceUpdate,
    current_user: UserResponse = Depends(get_current_user),
):
    """Update a Space (ownership validated)."""
    try:
        return await space_service.update_space(space_id, current_user.id, data)
    except ValueError as exc:
        if "not_found" in str(exc):
            raise _not_found_or_forbidden(exc)
        raise _validation_error(exc)


@router.delete("/{space_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_space(
    space_id: str,
    current_user: UserResponse = Depends(get_current_user),
):
    """Delete a Space and ALL its Projects (cascade). Ownership validated."""
    try:
        await space_service.delete_space(space_id, current_user.id)
    except ValueError:
        raise _not_found_or_forbidden(ValueError())


# ── Nested Project routes ───────────────────────────────────────────────────────

@router.post("/{space_id}/projects", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
async def create_project(
    space_id: str,
    data: ProjectCreate,
    current_user: UserResponse = Depends(get_current_user),
):
    """
    Create a Project inside a Space.
    Validates that the Space belongs to the authenticated user first.
    """
    try:
        return await project_service.create_project(space_id, current_user.id, data)
    except ValueError:
        raise _project_not_found()


@router.get("/{space_id}/projects", response_model=List[ProjectResponse])
async def list_projects(
    space_id: str,
    current_user: UserResponse = Depends(get_current_user),
):
    """List Projects in a Space (space ownership validated)."""
    try:
        return await project_service.get_projects(space_id, current_user.id)
    except ValueError:
        raise _not_found_or_forbidden(ValueError())


@router.get("/{space_id}/projects/{project_id}", response_model=ProjectResponse)
async def get_project_in_space(
    space_id: str,
    project_id: str,
    current_user: UserResponse = Depends(get_current_user),
):
    """
    Get a single Project verifying BOTH Space ownership and Project membership.
    """
    try:
        return await project_service.get_project_in_space(project_id, space_id, current_user.id)
    except ValueError:
        raise _project_not_found()

