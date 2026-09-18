"""
Background Reliability & Idempotency Test Suite.

Verifies material processing retry limits with db mock.
"""
import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from bson import ObjectId
from app.models.material import MaterialStatus


@pytest.mark.asyncio
async def test_material_retry_limits():
    mat_oid = ObjectId()
    mat_id = str(mat_oid)
    user_id = "test_retry_user_id"

    db_mock = MagicMock()
    db_mock["materials"].find_one = AsyncMock(return_value={
        "_id": mat_oid,
        "user_id": user_id,
        "project_id": "proj_123",
        "status": MaterialStatus.FAILED.value,
        "processing_attempts": 3
    })

    from app.services import material_service
    from fastapi import BackgroundTasks

    bg_tasks = BackgroundTasks()

    with patch("app.services.material_service.get_database", return_value=db_mock):
        with pytest.raises(ValueError) as exc:
            await material_service.retry_material(mat_id, user_id, bg_tasks)

        assert "Maximum processing retries reached" in str(exc.value)
