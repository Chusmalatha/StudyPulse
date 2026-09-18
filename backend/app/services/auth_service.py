"""
Authentication business-logic service.
All database operations for auth go here; routes stay thin.
"""
import logging
from datetime import timezone, datetime
from typing import Optional

from bson import ObjectId
from pymongo.errors import DuplicateKeyError

from app.core.security import hash_password, verify_password, create_access_token
from app.db.database import get_database
from app.models.user import UserModel, UserRole
from app.schemas.auth import RegisterRequest, LoginRequest, UserResponse, TokenResponse

logger = logging.getLogger(__name__)


def _doc_to_user_response(doc: dict) -> UserResponse:
    """Convert a raw MongoDB document to a safe UserResponse."""
    return UserResponse(
        id=str(doc["_id"]),
        name=doc["name"],
        email=doc["email"],
        role=doc.get("role", UserRole.user),
        is_active=doc.get("is_active", True),
    )


async def register_user(data: RegisterRequest) -> UserResponse:
    """
    Create a new user.
    Raises ValueError on duplicate email or other validation failures.
    """
    db = get_database()
    now = datetime.now(timezone.utc)
    doc = {
        "name": data.name,
        "email": data.email.lower(),
        "password_hash": hash_password(data.password),
        "role": UserRole.user,
        "is_active": True,
        "created_at": now,
        "updated_at": now,
    }

    try:
        result = await db["users"].insert_one(doc)
    except DuplicateKeyError:
        raise ValueError("Email already registered.")

    doc["_id"] = result.inserted_id
    logger.info(f"New user registered: {data.email}")
    return _doc_to_user_response(doc)


async def login_user(data: LoginRequest) -> TokenResponse:
    """
    Validate credentials and return a JWT token response.
    Raises ValueError for invalid credentials.
    """
    db = get_database()
    doc = await db["users"].find_one({"email": data.email.lower()})

    if not doc or not verify_password(data.password, doc["password_hash"]):
        raise ValueError("Invalid email or password.")

    if not doc.get("is_active", True):
        raise ValueError("Account is disabled. Please contact support.")

    user = _doc_to_user_response(doc)
    token = create_access_token(subject=user.id)

    logger.info(f"User logged in: {data.email}")
    return TokenResponse(access_token=token, token_type="bearer", user=user)


async def get_user_by_id(user_id: str) -> Optional[dict]:
    """Return a raw MongoDB user document by id, or None."""
    db = get_database()
    try:
        return await db["users"].find_one({"_id": ObjectId(user_id)})
    except Exception:
        return None


async def ensure_seed_admin_user():
    """
    Ensure system admin account exists with:
    Email: alalachusmalatha@gmail.com
    Password: bujji4477
    Name: Chusmalatha
    Role: admin
    """
    try:
        db = get_database()
        if db is None:
            logger.warning("Database not connected yet; skipping seed admin creation.")
            return

        admin_email = "alalachusmalatha@gmail.com"
        existing = await db["users"].find_one({"email": admin_email})
        now = datetime.now(timezone.utc)
        hashed_pwd = hash_password("bujji4477")

        if existing:
            await db["users"].update_one(
                {"_id": existing["_id"]},
                {
                    "$set": {
                        "name": "Chusmalatha",
                        "role": UserRole.admin,
                        "password_hash": hashed_pwd,
                        "is_active": True,
                        "updated_at": now,
                    }
                },
            )
            logger.info(f"Seed admin user updated successfully: {admin_email}")
        else:
            doc = {
                "name": "Chusmalatha",
                "email": admin_email,
                "password_hash": hashed_pwd,
                "role": UserRole.admin,
                "is_active": True,
                "created_at": now,
                "updated_at": now,
            }
            await db["users"].insert_one(doc)
            logger.info(f"Seed admin user created successfully: {admin_email}")
    except Exception as exc:
        logger.error(f"Failed to ensure seed admin user: {exc}")

