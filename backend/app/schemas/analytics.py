"""
Pydantic API schemas for Analytics and Admin Dashboard.
"""
from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


# --- Project Analytics Schemas ---

class DailyActivityPoint(BaseModel):
    date: str  # YYYY-MM-DD
    count: int


class LearningActivitySummary(BaseModel):
    total_events: int
    activity_today: int
    activity_this_week: int
    activity_this_month: int
    tutor_interactions: int
    assessments_completed: int
    recommendations_completed: int
    time_series: List[DailyActivityPoint]


class QuizPerformanceTrendPoint(BaseModel):
    assessment_id: str
    title: str
    completed_at: datetime
    score_mcq: Optional[float] = None
    question_count: int


class QuizPerformanceMetrics(BaseModel):
    assessments_completed: int
    questions_attempted: int
    correct_attempts: int
    incorrect_attempts: int
    accuracy_percentage: float
    trend: List[QuizPerformanceTrendPoint]


class ConceptTrendItem(BaseModel):
    concept_id: str
    concept_name: str
    current_mastery: float
    status_label: str  # IMPROVING, STABLE, REQUIRING_ATTENTION, INSUFFICIENT_EVIDENCE
    evidence_count: int


class MasteryAnalyticsSummary(BaseModel):
    average_mastery: float
    strong_concepts_count: int
    requiring_attention_count: int
    total_concepts_tracked: int
    concept_trends: List[ConceptTrendItem]


class ProjectAIActivitySummary(BaseModel):
    tutor_requests: int
    quiz_generations: int
    open_ended_evaluations: int
    knowledge_extractions: int
    embeddings_generated: int
    total_ai_operations: int


class ProjectAnalyticsResponse(BaseModel):
    project_id: str
    learning_activity: LearningActivitySummary
    quiz_performance: QuizPerformanceMetrics
    mastery: MasteryAnalyticsSummary
    ai_activity: ProjectAIActivitySummary


# --- Global Analytics Schemas ---

class ActiveProjectSummary(BaseModel):
    project_id: str
    project_name: str
    space_name: str
    total_events: int
    last_active_at: Optional[datetime] = None


class GlobalAnalyticsResponse(BaseModel):
    total_spaces: int
    total_projects: int
    active_projects_count: int
    total_learning_events: int
    tutor_interactions: int
    assessments_completed: int
    questions_attempted: int
    overall_accuracy_percentage: float
    overall_average_mastery: float
    concepts_requiring_attention_count: int
    recommendations_completed_count: int
    active_projects: List[ActiveProjectSummary]


# --- Admin Dashboard Schemas ---

class AdminOverviewResponse(BaseModel):
    total_users: int
    active_projects_count: int
    total_tutor_requests: int
    total_quiz_attempts: int
    failed_jobs_count: int
    system_status: str  # HEALTHY, WARNING, CRITICAL


class AdminUserItem(BaseModel):
    id: str
    name: str
    email: str
    role: str
    created_at: Optional[datetime] = None
    spaces_count: int
    projects_count: int
    total_events_count: int
    last_active_at: Optional[datetime] = None


class AdminUserListResponse(BaseModel):
    users: List[AdminUserItem]
    total_count: int
    limit: int
    skip: int


class AdminUserJourneyResponse(BaseModel):
    user: AdminUserItem
    spaces_summary: List[Dict[str, Any]]
    projects_summary: List[Dict[str, Any]]
    materials_summary: Dict[str, Any]
    assessments_summary: Dict[str, Any]
    tutor_summary: Dict[str, Any]
    mastery_summary: Dict[str, Any]
    growth_snapshot: Optional[Dict[str, Any]] = None
    recommendations_summary: Dict[str, Any]
    timeline_events: List[Dict[str, Any]]


class AdminActivityItem(BaseModel):
    id: str
    event_type: str
    user_id: str
    user_name: Optional[str] = None
    project_id: Optional[str] = None
    project_name: Optional[str] = None
    payload: Dict[str, Any]
    correlation_id: str
    created_at: datetime


class AdminActivityListResponse(BaseModel):
    events: List[AdminActivityItem]
    total_count: int
    limit: int
    skip: int


class AdminEngagementResponse(BaseModel):
    daily_active_learners: int
    weekly_active_learners: int
    monthly_active_learners: int
    active_projects_count: int
    total_tutor_interactions: int
    total_assessments_completed: int
    total_recommendations_completed: int


class AIOperationDetail(BaseModel):
    operation_type: str
    request_count: int
    success_count: int
    failure_count: int
    avg_latency_ms: Optional[float] = None
    total_tokens: Optional[int] = None
    estimated_cost_usd: Optional[float] = None


class AdminAIUsageResponse(BaseModel):
    total_requests: int
    total_successes: int
    total_failures: int
    operations: List[AIOperationDetail]


class AdminAIEvaluationResponse(BaseModel):
    open_ended_evaluations_count: int
    good_evaluations_count: int
    needs_improvement_count: int
    tutor_grounded_responses_count: int
    tutor_ungrounded_responses_count: int
    grounding_rate_percentage: float


class AdminJobItem(BaseModel):
    id: str
    job_type: str
    status: str
    project_id: Optional[str] = None
    user_id: Optional[str] = None
    material_id: Optional[str] = None
    event_id: Optional[str] = None
    attempts: int
    max_attempts: int
    last_error: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class AdminJobsResponse(BaseModel):
    total_jobs: int
    queued: int
    processing: int
    completed: int
    failed: int
    jobs: List[AdminJobItem]


class HealthCheckItem(BaseModel):
    component: str
    status: str  # Healthy, Warning, Unavailable
    details: str


class AdminSystemHealthResponse(BaseModel):
    overall_status: str  # HEALTHY, WARNING, UNAVAILABLE
    checks: List[HealthCheckItem]
    checked_at: datetime
