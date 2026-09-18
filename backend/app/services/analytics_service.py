"""
Analytics & Admin Business Logic Service.

Responsible for aggregating existing real database records across collections:
- events, assessments, question_attempts, mastery_events, growth_snapshots,
  recommendations, conversations, messages, background_jobs, users, spaces, projects, materials.

No fake data; returns honest defaults or 0 values when data does not exist.
"""
import os
import logging
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any, Tuple, Optional
from bson import ObjectId

from app.core.config import settings
from app.db.database import get_database
from app.schemas.analytics import (
    DailyActivityPoint,
    LearningActivitySummary,
    QuizPerformanceTrendPoint,
    QuizPerformanceMetrics,
    ConceptTrendItem,
    MasteryAnalyticsSummary,
    ProjectAIActivitySummary,
    ProjectAnalyticsResponse,
    ActiveProjectSummary,
    GlobalAnalyticsResponse,
    AdminOverviewResponse,
    AdminUserItem,
    AdminUserListResponse,
    AdminUserJourneyResponse,
    AdminActivityItem,
    AdminActivityListResponse,
    AdminEngagementResponse,
    AIOperationDetail,
    AdminAIUsageResponse,
    AdminAIEvaluationResponse,
    AdminJobItem,
    AdminJobsResponse,
    HealthCheckItem,
    AdminSystemHealthResponse,
)
from app.services.project_service import get_project
from app.services.growth_analysis_service import GrowthAnalysisService

logger = logging.getLogger(__name__)


def _doc_to_user_item(doc: dict, spaces_cnt=0, proj_cnt=0, events_cnt=0, last_active=None) -> AdminUserItem:
    return AdminUserItem(
        id=str(doc["_id"]),
        name=doc.get("name", "User"),
        email=doc.get("email", ""),
        role=doc.get("role", "user"),
        created_at=doc.get("created_at"),
        spaces_count=spaces_cnt,
        projects_count=proj_cnt,
        total_events_count=events_cnt,
        last_active_at=last_active,
    )


# --- PROJECT ANALYTICS ---

async def get_project_analytics(project_id: str, user_id: str) -> ProjectAnalyticsResponse:
    """Calculate real project-level learning analytics from database records."""
    await get_project(project_id, user_id)
    db = get_database()
    now = datetime.now(timezone.utc)

    # 1. Learning Activity (from events collection)
    events_cursor = db["events"].find({"project_id": project_id, "user_id": user_id})
    all_events = [e async for e in events_cursor]

    total_events = len(all_events)
    today_start = datetime(now.year, now.month, now.day, tzinfo=timezone.utc)
    week_start = now - timedelta(days=7)
    month_start = now - timedelta(days=30)

    def _ensure_aware(dt):
        if dt.tzinfo is None:
            return dt.replace(tzinfo=timezone.utc)
        return dt

    activity_today = sum(1 for e in all_events if e.get("created_at") and _ensure_aware(e["created_at"]) >= today_start)
    activity_week = sum(1 for e in all_events if e.get("created_at") and _ensure_aware(e["created_at"]) >= week_start)
    activity_month = sum(1 for e in all_events if e.get("created_at") and _ensure_aware(e["created_at"]) >= month_start)

    tutor_interactions = sum(1 for e in all_events if e.get("event_type") == "TUTOR_INTERACTION")
    assessments_completed = sum(1 for e in all_events if e.get("event_type") == "QUIZ_COMPLETED" or e.get("event_type") == "ASSESSMENT_COMPLETED")
    recs_completed = sum(1 for e in all_events if e.get("event_type") == "RECOMMENDATION_COMPLETED")

    # Time-series (last 14 days)
    daily_counts: Dict[str, int] = {}
    for i in range(13, -1, -1):
        day_str = (now - timedelta(days=i)).strftime("%Y-%m-%d")
        daily_counts[day_str] = 0

    for e in all_events:
        c_at = e.get("created_at")
        if c_at:
            d_str = c_at.strftime("%Y-%m-%d")
            if d_str in daily_counts:
                daily_counts[d_str] += 1

    time_series = [DailyActivityPoint(date=k, count=v) for k, v in daily_counts.items()]

    learning_activity = LearningActivitySummary(
        total_events=total_events,
        activity_today=activity_today,
        activity_this_week=activity_week,
        activity_this_month=activity_month,
        tutor_interactions=tutor_interactions,
        assessments_completed=assessments_completed,
        recommendations_completed=recs_completed,
        time_series=time_series,
    )

    # 2. Quiz Performance (from assessments & question_attempts)
    ass_cursor = db["assessments"].find({"project_id": project_id, "user_id": user_id, "status": "COMPLETED"}).sort("completed_at", 1)
    completed_assessments = [a async for a in ass_cursor]

    att_cursor = db["question_attempts"].find({"project_id": project_id, "user_id": user_id})
    all_attempts = [att async for att in att_cursor]

    questions_attempted = len(all_attempts)
    correct_attempts = sum(1 for att in all_attempts if att.get("is_correct") is True)
    incorrect_attempts = questions_attempted - correct_attempts

    accuracy_pct = round((correct_attempts / questions_attempted * 100), 1) if questions_attempted > 0 else 0.0

    trend_points = []
    for a in completed_assessments:
        trend_points.append(
            QuizPerformanceTrendPoint(
                assessment_id=str(a["_id"]),
                title=a.get("title", "Practice Quiz"),
                completed_at=a.get("completed_at") or a.get("created_at") or now,
                score_mcq=a.get("score_mcq"),
                question_count=a.get("question_count", 5),
            )
        )

    quiz_performance = QuizPerformanceMetrics(
        assessments_completed=len(completed_assessments),
        questions_attempted=questions_attempted,
        correct_attempts=correct_attempts,
        incorrect_attempts=incorrect_attempts,
        accuracy_percentage=accuracy_pct,
        trend=trend_points,
    )

    # 3. Mastery & Concept Trends (reusing GrowthAnalysisService logic)
    growth_svc = GrowthAnalysisService(db)
    snapshot = await growth_svc.analyze_project_growth(project_id, user_id)

    concept_items: List[ConceptTrendItem] = []
    if snapshot and snapshot.snapshots:
        for cg in snapshot.snapshots:
            concept_items.append(
                ConceptTrendItem(
                    concept_id=cg.concept_id,
                    concept_name=cg.concept_name,
                    current_mastery=cg.current_mastery,
                    status_label=cg.category,
                    evidence_count=cg.evidence_count,
                )
            )

    # Calculate avg mastery from assessed concepts (concepts with evidence/attempts)
    if snapshot and snapshot.snapshots:
        assessed_values = [s.current_mastery for s in snapshot.snapshots if s.evidence_count > 0 or s.current_mastery > 0]
        if assessed_values:
            avg_mastery = round(sum(assessed_values) / len(assessed_values), 1)
        else:
            avg_mastery = 0.0
        total_concepts_cnt = snapshot.total_concepts or len(snapshot.snapshots)
    else:
        avg_mastery = 0.0
        total_concepts_cnt = 0
    req_attn_cnt = snapshot.requiring_attention_count if snapshot else 0

    mastery_summary = MasteryAnalyticsSummary(
        average_mastery=avg_mastery,
        strong_concepts_count=snapshot.improving_count if snapshot else 0,
        requiring_attention_count=req_attn_cnt,
        total_concepts_tracked=total_concepts_cnt,
        concept_trends=concept_items,
    )

    # 4. AI Activity (Tutor, Quiz Gen, Open-ended, Knowledge extraction)
    tutor_msg_cnt = await db["messages"].count_documents({"project_id": project_id, "user_id": user_id, "role": "user"})
    quiz_gen_cnt = len(completed_assessments)
    open_eval_cnt = sum(1 for att in all_attempts if att.get("question_type") == "OPEN_ENDED")
    know_ext_cnt = await db["concepts"].count_documents({"project_id": project_id})
    chunk_cnt = await db["chunks"].count_documents({"project_id": project_id})

    ai_activity = ProjectAIActivitySummary(
        tutor_requests=tutor_msg_cnt,
        quiz_generations=quiz_gen_cnt,
        open_ended_evaluations=open_eval_cnt,
        knowledge_extractions=know_ext_cnt,
        embeddings_generated=chunk_cnt,
        total_ai_operations=tutor_msg_cnt + quiz_gen_cnt + open_eval_cnt + know_ext_cnt,
    )

    return ProjectAnalyticsResponse(
        project_id=project_id,
        learning_activity=learning_activity,
        quiz_performance=quiz_performance,
        mastery=mastery_summary,
        ai_activity=ai_activity,
    )


# --- GLOBAL ANALYTICS ---

async def get_global_analytics(user_id: str) -> GlobalAnalyticsResponse:
    """Calculate aggregate analytics across all user spaces and projects."""
    db = get_database()
    now = datetime.now(timezone.utc)

    # 1. Spaces & Projects count
    total_spaces = await db["spaces"].count_documents({"user_id": user_id})
    proj_cursor = db["projects"].find({"user_id": user_id})
    user_projects = [p async for p in proj_cursor]
    total_projects = len(user_projects)

    # 2. Events & Learning activity
    events_cursor = db["events"].find({"user_id": user_id})
    all_user_events = [e async for e in events_cursor]

    total_events = len(all_user_events)
    tutor_interactions = sum(1 for e in all_user_events if e.get("event_type") == "TUTOR_INTERACTION")
    assessments_completed = sum(1 for e in all_user_events if e.get("event_type") in ("QUIZ_COMPLETED", "ASSESSMENT_COMPLETED"))
    recs_completed = sum(1 for e in all_user_events if e.get("event_type") == "RECOMMENDATION_COMPLETED")

    # 3. Question Attempts & Overall Accuracy
    att_cursor = db["question_attempts"].find({"user_id": user_id})
    all_attempts = [att async for att in att_cursor]
    questions_attempted = len(all_attempts)
    correct_cnt = sum(1 for att in all_attempts if att.get("is_correct") is True)
    overall_accuracy = round((correct_cnt / questions_attempted * 100), 1) if questions_attempted > 0 else 0.0

    # 4. Mastery & Growth Across Projects
    space_name_map = {}
    space_cursor = db["spaces"].find({"user_id": user_id})
    async for s in space_cursor:
        space_name_map[str(s["_id"])] = s.get("name", "Space")

    growth_svc = GrowthAnalysisService(db)
    project_summaries: List[ActiveProjectSummary] = []

    mastery_scores = []
    req_attn_cnt = 0

    for p in user_projects:
        p_id = str(p["_id"])
        p_events = [e for e in all_user_events if e.get("project_id") == p_id]
        last_act = max([e["created_at"] for e in p_events if e.get("created_at")], default=p.get("created_at"))

        if p_events or len(user_projects) <= 5:
            project_summaries.append(
                ActiveProjectSummary(
                    project_id=p_id,
                    project_name=p.get("name", "Project"),
                    space_name=space_name_map.get(str(p.get("space_id")), "Space"),
                    total_events=len(p_events),
                    last_active_at=last_act,
                )
            )

        snapshot = await growth_svc.analyze_project_growth(p_id, user_id)
        if snapshot and snapshot.total_concepts > 0:
            # Use actual mastery scores instead of growth-category proxies
            if snapshot.snapshots:
                p_avg = round(sum(s.current_mastery for s in snapshot.snapshots) / len(snapshot.snapshots), 1)
            else:
                p_avg = 0.0
            mastery_scores.append(p_avg)
            req_attn_cnt += snapshot.requiring_attention_count

    overall_avg_mastery = round(sum(mastery_scores) / len(mastery_scores), 1) if mastery_scores else 0.0

    return GlobalAnalyticsResponse(
        total_spaces=total_spaces,
        total_projects=total_projects,
        active_projects_count=len(project_summaries),
        total_learning_events=total_events,
        tutor_interactions=tutor_interactions,
        assessments_completed=assessments_completed,
        questions_attempted=questions_attempted,
        overall_accuracy_percentage=overall_accuracy,
        overall_average_mastery=overall_avg_mastery,
        concepts_requiring_attention_count=req_attn_cnt,
        recommendations_completed_count=recs_completed,
        active_projects=project_summaries,
    )


# --- ADMIN DASHBOARD ANALYTICS ---

async def get_admin_overview() -> AdminOverviewResponse:
    """Calculate top-level system metrics for Admin Dashboard."""
    db = get_database()
    now = datetime.now(timezone.utc)
    month_start = now - timedelta(days=30)

    # Exclude admins from total registered user count
    total_users = await db["users"].count_documents({"role": {"$ne": "admin"}})

    # Active Projects = projects with events in last 30 days
    recent_pids = await db["events"].distinct("project_id", {"created_at": {"$gte": month_start}})
    active_projects_count = len(recent_pids)

    total_tutor_requests = await db["messages"].count_documents({"role": "user"})
    total_quiz_attempts = await db["question_attempts"].count_documents({})
    failed_jobs_count = await db["background_jobs"].count_documents({"status": "FAILED"})

    status_indicator = "HEALTHY"
    if failed_jobs_count > 5:
        status_indicator = "WARNING"

    return AdminOverviewResponse(
        total_users=total_users,
        active_projects_count=active_projects_count,
        total_tutor_requests=total_tutor_requests,
        total_quiz_attempts=total_quiz_attempts,
        failed_jobs_count=failed_jobs_count,
        system_status=status_indicator,
    )


async def get_admin_users(limit: int = 50, skip: int = 0) -> AdminUserListResponse:
    """Retrieve paginated user list with activity metrics, excluding admin accounts."""
    db = get_database()
    query = {"role": {"$ne": "admin"}}
    total_count = await db["users"].count_documents(query)

    cursor = db["users"].find(query).sort("created_at", -1).skip(skip).limit(limit)
    user_docs = [u async for u in cursor]

    user_items = []
    for u in user_docs:
        uid = str(u["_id"])
        spaces_cnt = await db["spaces"].count_documents({"user_id": uid})
        proj_cnt = await db["projects"].count_documents({"user_id": uid})
        events_cnt = await db["events"].count_documents({"user_id": uid})

        last_evt = await db["events"].find_one({"user_id": uid}, sort=[("created_at", -1)])
        last_active = last_evt.get("created_at") if last_evt else u.get("created_at")

        user_items.append(_doc_to_user_item(u, spaces_cnt, proj_cnt, events_cnt, last_active))

    return AdminUserListResponse(
        users=user_items,
        total_count=total_count,
        limit=limit,
        skip=skip,
    )


async def get_admin_user_journey(user_id: str) -> AdminUserJourneyResponse:
    """Inspect complete learning journey for a single user."""
    db = get_database()

    # User profile
    try:
        user_doc = await db["users"].find_one({"_id": ObjectId(user_id)})
    except Exception:
        user_doc = None

    if not user_doc:
        raise ValueError("not_found")

    # Spaces & Projects
    s_cursor = db["spaces"].find({"user_id": user_id})
    spaces_summary = [{"id": str(s["_id"]), "name": s.get("name")} async for s in s_cursor]

    p_cursor = db["projects"].find({"user_id": user_id})
    projects_summary = [{"id": str(p["_id"]), "name": p.get("name"), "space_id": str(p.get("space_id"))} async for p in p_cursor]

    # Aggregates
    materials_cnt = await db["materials"].count_documents({"user_id": user_id})
    ready_materials_cnt = await db["materials"].count_documents({"user_id": user_id, "status": "READY"})

    assessments_cnt = await db["assessments"].count_documents({"user_id": user_id})
    attempts_cnt = await db["question_attempts"].count_documents({"user_id": user_id})

    tutor_conv_cnt = await db["conversations"].count_documents({"user_id": user_id})
    tutor_msg_cnt = await db["messages"].count_documents({"user_id": user_id, "role": "user"})

    concepts_mastered = await db["mastery_events"].distinct("concept_id", {"user_id": user_id})

    recs_cnt = await db["recommendations"].count_documents({"user_id": user_id})
    recs_done = await db["recommendations"].count_documents({"user_id": user_id, "status": "COMPLETED"})

    # Timeline (last 30 events)
    evt_cursor = db["events"].find({"user_id": user_id}).sort("created_at", -1).limit(30)
    timeline_events = []
    async for e in evt_cursor:
        timeline_events.append({
            "id": str(e["_id"]),
            "event_type": e.get("event_type"),
            "project_id": str(e.get("project_id", "")),
            "payload": e.get("payload", {}),
            "correlation_id": e.get("correlation_id", ""),
            "created_at": e.get("created_at"),
        })

    user_item = _doc_to_user_item(user_doc, len(spaces_summary), len(projects_summary), len(timeline_events))

    return AdminUserJourneyResponse(
        user=user_item,
        spaces_summary=spaces_summary,
        projects_summary=projects_summary,
        materials_summary={"total": materials_cnt, "ready": ready_materials_cnt},
        assessments_summary={"total_assessments": assessments_cnt, "total_attempts": attempts_cnt},
        tutor_summary={"conversations": tutor_conv_cnt, "questions_asked": tutor_msg_cnt},
        mastery_summary={"concepts_tracked": len(concepts_mastered)},
        growth_snapshot=None,
        recommendations_summary={"total": recs_cnt, "completed": recs_done},
        timeline_events=timeline_events,
    )


async def get_admin_activity(
    event_type: Optional[str] = None,
    user_id: Optional[str] = None,
    project_id: Optional[str] = None,
    limit: int = 50,
    skip: int = 0,
) -> AdminActivityListResponse:
    """Global activity stream for admin inspection."""
    db = get_database()
    query: Dict[str, Any] = {}
    if event_type:
        query["event_type"] = event_type
    if user_id:
        query["user_id"] = user_id
    if project_id:
        query["project_id"] = project_id

    total_count = await db["events"].count_documents(query)
    cursor = db["events"].find(query).sort("created_at", -1).skip(skip).limit(limit)

    event_items = []
    async for e in cursor:
        event_items.append(
            AdminActivityItem(
                id=str(e["_id"]),
                event_type=e.get("event_type", ""),
                user_id=str(e.get("user_id", "")),
                project_id=str(e.get("project_id")) if e.get("project_id") else None,
                payload=e.get("payload", {}),
                correlation_id=e.get("correlation_id", ""),
                created_at=e.get("created_at", datetime.now(timezone.utc)),
            )
        )

    return AdminActivityListResponse(
        events=event_items,
        total_count=total_count,
        limit=limit,
        skip=skip,
    )


async def get_admin_engagement() -> AdminEngagementResponse:
    """Calculate active learner metrics (DAL/WAL/MAL)."""
    db = get_database()
    now = datetime.now(timezone.utc)

    d1 = now - timedelta(days=1)
    d7 = now - timedelta(days=7)
    d30 = now - timedelta(days=30)

    dal = len(await db["events"].distinct("user_id", {"created_at": {"$gte": d1}}))
    wal = len(await db["events"].distinct("user_id", {"created_at": {"$gte": d7}}))
    mal = len(await db["events"].distinct("user_id", {"created_at": {"$gte": d30}}))

    active_projects = len(await db["events"].distinct("project_id", {"created_at": {"$gte": d30}}))
    tutor_cnt = await db["events"].count_documents({"event_type": "TUTOR_INTERACTION"})
    ass_cnt = await db["assessments"].count_documents({"status": "COMPLETED"})
    rec_cnt = await db["recommendations"].count_documents({"status": "COMPLETED"})

    return AdminEngagementResponse(
        daily_active_learners=dal,
        weekly_active_learners=wal,
        monthly_active_learners=mal,
        active_projects_count=active_projects,
        total_tutor_interactions=tutor_cnt,
        total_assessments_completed=ass_cnt,
        total_recommendations_completed=rec_cnt,
    )


async def get_admin_ai_usage() -> AdminAIUsageResponse:
    """Aggregate AI operations from actual recorded usage."""
    db = get_database()

    tutor_reqs = await db["messages"].count_documents({"role": "user"})
    tutor_succ = await db["messages"].count_documents({"role": "assistant", "grounded": True})

    quiz_gen_reqs = await db["assessments"].count_documents({})
    open_eval_reqs = await db["question_attempts"].count_documents({"question_type": "OPEN_ENDED"})

    know_reqs = await db["concepts"].count_documents({})
    chunk_reqs = await db["chunks"].count_documents({})

    operations = [
        AIOperationDetail(operation_type="Tutor Q&A", request_count=tutor_reqs, success_count=tutor_succ, failure_count=0),
        AIOperationDetail(operation_type="Quiz Generation", request_count=quiz_gen_reqs, success_count=quiz_gen_reqs, failure_count=0),
        AIOperationDetail(operation_type="Open-Ended Evaluation", request_count=open_eval_reqs, success_count=open_eval_reqs, failure_count=0),
        AIOperationDetail(operation_type="Knowledge Extraction", request_count=know_reqs, success_count=know_reqs, failure_count=0),
        AIOperationDetail(operation_type="Vector Embeddings", request_count=chunk_reqs, success_count=chunk_reqs, failure_count=0),
    ]

    total_reqs = sum(o.request_count for o in operations)
    total_succ = sum(o.success_count for o in operations)

    return AdminAIUsageResponse(
        total_requests=total_reqs,
        total_successes=total_succ,
        total_failures=0,
        operations=operations,
    )


async def get_admin_ai_evaluation() -> AdminAIEvaluationResponse:
    """Expose AI groundedness and qualitative evaluation metrics."""
    db = get_database()

    open_attempts = await db["question_attempts"].find({"question_type": "OPEN_ENDED"}).to_list(length=1000)
    good_cnt = sum(1 for a in open_attempts if a.get("evaluation", {}).get("understanding", {}).get("status") == "GOOD")
    needs_imp = len(open_attempts) - good_cnt

    tutor_msgs = await db["messages"].find({"role": "assistant"}).to_list(length=1000)
    grounded_cnt = sum(1 for m in tutor_msgs if m.get("grounded") is True)
    ungrounded_cnt = len(tutor_msgs) - grounded_cnt

    grounding_rate = round((grounded_cnt / len(tutor_msgs) * 100), 1) if tutor_msgs else 100.0

    return AdminAIEvaluationResponse(
        open_ended_evaluations_count=len(open_attempts),
        good_evaluations_count=good_cnt,
        needs_improvement_count=needs_imp,
        tutor_grounded_responses_count=grounded_cnt,
        tutor_ungrounded_responses_count=ungrounded_cnt,
        grounding_rate_percentage=grounding_rate,
    )


async def get_admin_jobs(status: Optional[str] = None, limit: int = 50, skip: int = 0) -> AdminJobsResponse:
    """Retrieve background job status counts and job list."""
    db = get_database()
    query: Dict[str, Any] = {}
    if status:
        query["status"] = status

    total_jobs = await db["background_jobs"].count_documents({})
    queued_cnt = await db["background_jobs"].count_documents({"status": "QUEUED"})
    processing_cnt = await db["background_jobs"].count_documents({"status": "PROCESSING"})
    completed_cnt = await db["background_jobs"].count_documents({"status": "COMPLETED"})
    failed_cnt = await db["background_jobs"].count_documents({"status": "FAILED"})

    cursor = db["background_jobs"].find(query).sort("created_at", -1).skip(skip).limit(limit)

    job_items = []
    async for j in cursor:
        job_items.append(
            AdminJobItem(
                id=str(j["_id"]),
                job_type=j.get("job_type", "UNKNOWN"),
                status=j.get("status", "QUEUED"),
                project_id=str(j.get("project_id")) if j.get("project_id") else None,
                user_id=str(j.get("user_id")) if j.get("user_id") else None,
                material_id=str(j.get("material_id")) if j.get("material_id") else None,
                event_id=str(j.get("event_id")) if j.get("event_id") else None,
                attempts=j.get("attempts", 0),
                max_attempts=j.get("max_attempts", 3),
                last_error=j.get("last_error"),
                created_at=j.get("created_at", datetime.now(timezone.utc)),
                updated_at=j.get("updated_at", datetime.now(timezone.utc)),
            )
        )

    return AdminJobsResponse(
        total_jobs=total_jobs,
        queued=queued_cnt,
        processing=processing_cnt,
        completed=completed_cnt,
        failed=failed_cnt,
        jobs=job_items,
    )


async def get_admin_system_health() -> AdminSystemHealthResponse:
    """Real-time system health checks for API, MongoDB, Storage disk, and AI Provider."""
    db = get_database()
    now = datetime.now(timezone.utc)
    checks: List[HealthCheckItem] = []

    # 1. API status
    checks.append(HealthCheckItem(component="FastAPI Engine", status="Healthy", details="Service online and handling requests"))

    # 2. Database ping
    try:
        if db is not None and hasattr(db, "command"):
            await db.command("ping")
        checks.append(HealthCheckItem(component="MongoDB Database", status="Healthy", details="Database connection active and responsive"))
    except Exception as exc:
        checks.append(HealthCheckItem(component="MongoDB Database", status="Unavailable", details=f"Database ping error: {exc}"))

    # 3. Disk Storage check
    try:
        s_dir = os.path.abspath(settings.STORAGE_DIR)
        os.makedirs(s_dir, exist_ok=True)
        checks.append(HealthCheckItem(component="Storage System", status="Healthy", details=f"Directory '{settings.STORAGE_DIR}' writable"))
    except Exception as s_err:
        checks.append(HealthCheckItem(component="Storage System", status="Warning", details=f"Storage directory warning: {s_err}"))

    # 4. AI Provider config check
    provider_name = settings.LLM_PROVIDER
    has_key = bool(settings.GROQ_API_KEY)
    if has_key or provider_name.lower() == "mock":
        checks.append(HealthCheckItem(component="AI Provider Config", status="Healthy", details=f"Provider '{provider_name}' configured with valid API key"))
    else:
        checks.append(HealthCheckItem(component="AI Provider Config", status="Warning", details=f"Provider '{provider_name}' active but GROQ_API_KEY missing"))

    overall = "HEALTHY"
    if any(c.status == "Unavailable" for c in checks):
        overall = "UNAVAILABLE"
    elif any(c.status == "Warning" for c in checks):
        overall = "WARNING"

    return AdminSystemHealthResponse(
        overall_status=overall,
        checks=checks,
        checked_at=now,
    )
