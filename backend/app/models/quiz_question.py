"""
QuizQuestion DB model definition.
"""
from datetime import datetime, timezone
from enum import Enum
from typing import List, Dict, Optional, Any
from pydantic import BaseModel, Field

from app.models.message import CitationModel


class QuestionType(str, Enum):
    MCQ = "MCQ"
    OPEN_ENDED = "OPEN_ENDED"


class QuestionDifficulty(str, Enum):
    EASY = "EASY"
    MEDIUM = "MEDIUM"
    HARD = "HARD"


class QuizQuestionModel(BaseModel):
    """Internal representation of a Quiz Question document in MongoDB."""
    id: Optional[str] = Field(default=None, alias="_id")
    assessment_id: str
    project_id: str
    concept_ids: List[str] = Field(default_factory=list)
    concept_names: List[str] = Field(default_factory=list)
    question_type: QuestionType
    question_text: str
    options: Optional[Dict[str, str]] = None  # E.g. {"A": "...", "B": "...", "C": "...", "D": "..."}
    correct_answer: Optional[str] = None      # E.g. "B"
    difficulty: QuestionDifficulty = QuestionDifficulty.MEDIUM
    explanation: str = ""
    source_references: List[CitationModel] = Field(default_factory=list)
    order_index: int = 0
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    model_config = {"populate_by_name": True}
