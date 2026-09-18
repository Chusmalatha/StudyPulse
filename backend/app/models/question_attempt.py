"""
QuestionAttempt DB model definition.
"""
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

from app.models.quiz_question import QuestionType, QuestionDifficulty


class QuestionAttemptModel(BaseModel):
    """Internal representation of a Question Attempt document in MongoDB."""
    id: Optional[str] = Field(default=None, alias="_id")
    assessment_id: str
    question_id: str
    project_id: str
    user_id: str
    concept_ids: List[str] = Field(default_factory=list)
    question_type: QuestionType
    difficulty: QuestionDifficulty = QuestionDifficulty.MEDIUM
    student_answer: str
    is_correct: Optional[bool] = None
    evaluation: Optional[Dict[str, Any]] = None
    attempted_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    model_config = {"populate_by_name": True}
