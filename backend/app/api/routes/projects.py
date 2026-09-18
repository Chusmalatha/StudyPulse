"""
Standalone Project routes (not nested under a Space).
Used for: GET/PATCH/DELETE /projects/{project_id}

For project creation and listing, use the nested routes under /spaces/{space_id}/projects.
"""
from fastapi import APIRouter, Depends, HTTPException, status

from app.api.dependencies import get_current_user
from app.schemas.auth import UserResponse
from app.schemas.projects import ProjectUpdate, ProjectResponse
from app.services import project_service

router = APIRouter(prefix="/projects", tags=["projects"])


def _not_found() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Project not found.",
    )


@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(
    project_id: str,
    current_user: UserResponse = Depends(get_current_user),
):
    """Get a single Project (ownership validated via JWT)."""
    try:
        return await project_service.get_project(project_id, current_user.id)
    except ValueError:
        raise _not_found()


@router.put("/{project_id}", response_model=ProjectResponse)
@router.patch("/{project_id}", response_model=ProjectResponse)
async def update_project(
    project_id: str,
    data: ProjectUpdate,
    current_user: UserResponse = Depends(get_current_user),
):
    """Update a Project (ownership validated)."""
    try:
        return await project_service.update_project(project_id, current_user.id, data)
    except ValueError:
        raise _not_found()


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_project(
    project_id: str,
    current_user: UserResponse = Depends(get_current_user),
):
    """Delete a Project (ownership validated)."""
    try:
        await project_service.delete_project(project_id, current_user.id)
    except ValueError:
        raise _not_found()
