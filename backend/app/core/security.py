"""
Security utilities: password hashing and JWT creation/validation.
"""
from datetime import datetime, timedelta, timezone
from typing import Optional

import bcrypt

from jose import JWTError, jwt

from app.core.config import settings

# ── Password hashing ──────────────────────────────────────────────────────────
def hash_password(plain_password: str) -> str:
    """Return a bcrypt hash of *plain_password*."""
    pwd_bytes = plain_password.encode('utf-8')
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(pwd_bytes, salt).decode('utf-8')


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Return True if *plain_password* matches *hashed_password*."""
    try:
        return bcrypt.checkpw(
            plain_password.encode('utf-8'),
            hashed_password.encode('utf-8')
        )
    except Exception:
        return False



# ── JWT ───────────────────────────────────────────────────────────────────────
def create_access_token(subject: str, expires_delta: Optional[timedelta] = None) -> str:
    """
    Create a signed JWT containing *subject* (typically the user-id string).
    """
    expire = datetime.now(timezone.utc) + (
        expires_delta
        if expires_delta is not None
        else timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    payload = {"sub": subject, "exp": expire}
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)


def decode_access_token(token: str) -> Optional[str]:
    """
    Decode *token* and return the *sub* claim (user-id string).
    Returns None if the token is invalid or expired.
    """
    try:
        payload = jwt.decode(
            token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM]
        )
        return payload.get("sub")
    except JWTError:
        return None
