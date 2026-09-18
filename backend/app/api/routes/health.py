from fastapi import APIRouter, Depends
from app.db.database import get_database

router = APIRouter()

@router.get("/health")
async def health_check():
    """
    Check application health status.
    """
    return {"status": "healthy"}
