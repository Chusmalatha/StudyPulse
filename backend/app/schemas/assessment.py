"""
Pydantic schemas for Assessment API endpoints and Open-Ended Evaluation.
"""
from datetime import datetime
from typing import List, Dict, Optional, Any
from pydantic import BaseModel, Field

from app.schemas.tutor import CitationSchema


class AssessmentCreateSchema(BaseModel):
    question_count: Optional[int] = Field(default=5, ge=1, le=20)
    target_concept_id: Optional[str] = None


class QuizQuestionPublicSchema(BaseModel):
    id: str
    assessment_id: str
    project_id: str
    concept_names: List[str] = Field(default_factory=list)
    question_type: str
    question_text: str
    options: Optional[Dict[str, str]] = None
    difficulty: str
    order_index: int
    source_references: List[CitationSchema] = Field(default_factory=list)

    model_config = {"populate_by_name": True, "from_attributes": True}


class QuizQuestionDetailSchema(QuizQuestionPublicSchema):
    correct_answer: Optional[str] = None
    explanation: Optional[str] = None


class AssessmentResponseSchema(BaseModel):
    id: str
    project_id: str
    user_id: str
    title: str
    status: str
    question_count: int
    current_question_index: int
    score_mcq: Optional[float] = None
    started_at: datetime
    completed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    questions: List[QuizQuestionPublicSchema] = Field(default_factory=list)

    model_config = {"populate_by_name": True, "from_attributes": True}


class AnswerSubmitSchema(BaseModel):
    answer: str = Field(..., min_length=1, max_length=5000)


class UnderstandingComponentSchema(BaseModel):
    status: str
    feedback: str


class OpenEndedEvaluationSchema(BaseModel):
    understanding: UnderstandingComponentSchema
    accuracy: UnderstandingComponentSchema
    relevance: UnderstandingComponentSchema
    key_concepts_present: List[str] = Field(default_factory=list)
    missing_concepts: List[str] = Field(default_factory=list)
    reasoning_feedback: str
    strengths: List[str] = Field(default_factory=list)
    areas_to_improve: List[str] = Field(default_factory=list)
    suggestion: str


class QuestionResultResponseSchema(BaseModel):
    attempt_id: str
    question_id: str
    question_type: str
    is_correct: Optional[bool] = None
    correct_answer: Optional[str] = None
    explanation: Optional[str] = None
    evaluation: Optional[OpenEndedEvaluationSchema] = None
    attempted_at: datetime
