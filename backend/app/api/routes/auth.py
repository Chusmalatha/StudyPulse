"""
Auth routes: register, login, me.
"""
from fastapi import APIRouter, Depends, HTTPException, status

from app.api.dependencies import get_current_user
from app.schemas.auth import (
    LoginRequest,
    RegisterRequest,
    TokenResponse,
    UserResponse,
)
from app.services import auth_service

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(data: RegisterRequest):
    """
    Create a new user account.
    - Email must be unique.
    - Password minimum 8 characters.
    - Role is always set to 'user' by the backend.
    """
    try:
        return await auth_service.register_user(data)
    except ValueError as exc:
        status_code = (
            status.HTTP_409_CONFLICT
            if "already registered" in str(exc)
            else status.HTTP_400_BAD_REQUEST
        )
        raise HTTPException(status_code=status_code, detail=str(exc))
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Service temporarily unavailable. Please try again in a moment.",
        )


@router.post("/login", response_model=TokenResponse)
async def login(data: LoginRequest):
    """
    Authenticate with email + password and receive a JWT access token.
    """
    try:
        return await auth_service.login_user(data)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(exc),
            headers={"WWW-Authenticate": "Bearer"},
        )
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Service temporarily unavailable. Please try again in a moment.",
        )



@router.get("/me", response_model=UserResponse)
async def me(current_user: UserResponse = Depends(get_current_user)):
    """
    Return the currently authenticated user's profile.
    Requires a valid Bearer token.
    """
    return current_user
