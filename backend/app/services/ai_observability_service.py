"""
AI Observability Service.

Logs latency, model usage, tokens, estimated cost, and correlation IDs into MongoDB.
"""
import time
import logging
import uuid
from datetime import datetime, timezone
from typing import Optional, Dict, Any

from app.db.database import get_database
from app.models.ai_usage import AIUsageModel, AIFeature

logger = logging.getLogger(__name__)


async def record_ai_usage(
    user_id: str,
    feature: AIFeature,
    model: str,
    provider: str,
    started_at: datetime,
    completed_at: datetime,
    latency_ms: float,
    project_id: Optional[str] = None,
    input_tokens: Optional[int] = None,
    output_tokens: Optional[int] = None,
    total_tokens: Optional[int] = None,
    estimated_cost: Optional[float] = None,
    success: bool = True,
    error_type: Optional[str] = None,
    error_message: Optional[str] = None,
    request_id: Optional[str] = None,
    correlation_id: Optional[str] = None,
) -> str:
    """Log an AI operation into the ai_usage collection."""
    db = get_database()
    if db is None:
        logger.warning("Database not available for recording AI usage.")
        return ""

    if not request_id:
        request_id = f"req_{uuid.uuid4().hex[:12]}"

    usage_model = AIUsageModel(
        user_id=user_id,
        project_id=project_id,
        feature=feature,
        model=model,
        provider=provider,
        started_at=started_at,
        completed_at=completed_at,
        latency_ms=round(latency_ms, 2),
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        total_tokens=total_tokens,
        estimated_cost=estimated_cost,
        success=success,
        error_type=error_type,
        error_message=error_message,
        request_id=request_id,
        correlation_id=correlation_id,
        created_at=datetime.now(timezone.utc),
    )

    doc = usage_model.model_dump(by_alias=True, exclude=["id"])
    try:
        res = await db["ai_usage"].insert_one(doc)
        logger.info(f"AI Usage recorded: {feature.value} ({model}) - {latency_ms:.1f}ms - Success: {success}")
        return str(res.inserted_id)
    except Exception as exc:
        logger.error(f"Failed to record AI usage: {exc}")
        return ""
