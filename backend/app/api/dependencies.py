"""
FastAPI dependency functions.

Usage:
    from app.api.dependencies import get_current_user, require_admin

    @router.get("/protected")
    async def protected(current_user = Depends(get_current_user)):
        ...
"""
import logging
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.security import decode_access_token
from app.models.user import UserRole
from app.schemas.auth import UserResponse
from app.services import auth_service

logger = logging.getLogger(__name__)

bearer_scheme = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
) -> UserResponse:
    """
    Decode the Bearer JWT, load the user from MongoDB, and return a
    safe UserResponse.  Raises 401 on any auth failure.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired authentication token.",
        headers={"WWW-Authenticate": "Bearer"},
    )

    user_id = decode_access_token(credentials.credentials)
    if user_id is None:
        raise credentials_exception

    doc = await auth_service.get_user_by_id(user_id)
    if doc is None:
        raise credentials_exception

    if not doc.get("is_active", True):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Account is disabled.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return UserResponse(
        id=str(doc["_id"]),
        name=doc["name"],
        email=doc["email"],
        role=doc.get("role", UserRole.user),
        is_active=doc.get("is_active", True),
    )


async def require_admin(
    current_user: UserResponse = Depends(get_current_user),
) -> UserResponse:
    """
    Extends get_current_user: additionally requires the user to have the
    'admin' role.  Raises 403 otherwise.
    """
    if current_user.role != UserRole.admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to perform this action.",
        )
    return current_user
