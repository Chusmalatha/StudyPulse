"""
Mastery & Learning Context API Router.
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from bson import ObjectId

from app.db.database import get_database
from app.models.user import UserModel
from app.models.concept import ConceptModel
from app.schemas.mastery import (
    ConceptMasteryResponse,
    ProjectMasterySummaryResponse,
    ConceptDetailMasteryResponse,
    MasteryEventResponse,
    RepeatedMistakeResponse,
)
from app.api.dependencies import get_current_user
from app.services.project_service import get_project

router = APIRouter(prefix="/projects", tags=["mastery"])


@router.get("/{project_id}/mastery", response_model=ProjectMasterySummaryResponse)
async def get_project_mastery_summary(
    project_id: str,
    current_user: UserModel = Depends(get_current_user),
):
    """
    Get project-wide mastery summary for all extracted concepts.
    Strictly isolated to user & project.
    """
    try:
        await get_project(project_id, current_user.id)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")

    db = get_database()

    cursor = db["concepts"].find({"project_id": project_id})
    raw_concepts = [c async for c in cursor]

    concept_responses: List[ConceptMasteryResponse] = []
    total_score = 0.0
    practiced_count = 0

    for c in raw_concepts:
        attempts = c.get("attempts", 0)
        score = float(c.get("mastery_score", 0.0))
        conf = float(c.get("confidence", 0.0))
        if attempts > 0:
            practiced_count += 1
            total_score += score

        concept_responses.append(
            ConceptMasteryResponse(
                concept_id=str(c["_id"]),
                name=c.get("name", "Unnamed Concept"),
                description=c.get("description", ""),
                mastery_score=score,
                confidence=conf,
                attempts=attempts,
                correct=c.get("correct", 0),
                mistakes=c.get("mistakes", 0),
                last_updated=c.get("last_updated"),
            )
        )

    # Sort: practiced concepts first (descending mastery score), then unpracticed
    concept_responses.sort(key=lambda x: (-(x.attempts > 0), -x.mastery_score))

    # Overall mastery = average of ONLY the practiced concepts (not all concepts)
    # This gives a fair reflection of actual performance, not diluted by untested concepts
    overall_mastery = round(total_score / practiced_count, 1) if practiced_count > 0 else 0.0

    return ProjectMasterySummaryResponse(
        project_id=project_id,
        overall_mastery=overall_mastery,
        total_concepts=len(concept_responses),
        practiced_concepts=practiced_count,
        concepts=concept_responses,
    )


@router.get("/{project_id}/mastery/{concept_id}", response_model=ConceptDetailMasteryResponse)
async def get_concept_mastery_detail(
    project_id: str,
    concept_id: str,
    current_user: UserModel = Depends(get_current_user),
):
    """
    Get detailed breakdown of a single concept's mastery, audit events, and repeated mistakes.
    """
    await get_project(project_id, current_user.id)
    db = get_database()

    if not ObjectId.is_valid(concept_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Concept not found")

    c_doc = await db["concepts"].find_one({"_id": ObjectId(concept_id), "project_id": project_id})
    if not c_doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Concept not found")

    # Fetch audit events
    evt_cursor = db["mastery_events"].find({"concept_id": concept_id, "project_id": project_id}).sort("created_at", -1).limit(10)
    raw_evts = [e async for e in evt_cursor]
    events = [
        MasteryEventResponse(
            id=str(e["_id"]),
            concept_id=str(e["concept_id"]),
            previous_score=float(e.get("previous_score", 0.0)),
            new_score=float(e.get("new_score", 0.0)),
            previous_confidence=float(e.get("previous_confidence", 0.0)),
            new_confidence=float(e.get("new_confidence", 0.0)),
            evidence_type=e.get("evidence_type", "MCQ"),
            evidence_id=str(e.get("evidence_id", "")),
            reason=e.get("reason", ""),
            created_at=e["created_at"]
        )
        for e in raw_evts
    ]

    # Fetch repeated mistakes
    m_cursor = db["repeated_mistakes"].find({"concept_id": concept_id, "project_id": project_id, "user_id": current_user.id}).sort("last_seen", -1)
    raw_mistakes = [m async for m in m_cursor]
    mistakes = [
        RepeatedMistakeResponse(
            id=str(m["_id"]),
            concept_id=str(m["concept_id"]),
            mistake_description=m.get("mistake_description", ""),
            occurrence_count=int(m.get("occurrence_count", 1)),
            first_seen=m["first_seen"],
            last_seen=m["last_seen"]
        )
        for m in raw_mistakes
    ]

    return ConceptDetailMasteryResponse(
        concept_id=str(c_doc["_id"]),
        name=c_doc.get("name", "Unnamed Concept"),
        description=c_doc.get("description", ""),
        mastery_score=float(c_doc.get("mastery_score", 0.0)),
        confidence=float(c_doc.get("confidence", 0.0)),
        attempts=int(c_doc.get("attempts", 0)),
        correct=int(c_doc.get("correct", 0)),
        mistakes=int(c_doc.get("mistakes", 0)),
        last_updated=c_doc.get("last_updated"),
        recent_events=events,
        repeated_mistakes=mistakes,
    )
