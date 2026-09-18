"""
Automated unit and integration test suite for Phase 8 — Growth Analysis + Recommendations.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from bson import ObjectId
from datetime import datetime, timezone

from app.models.growth_recommendation import GrowthSnapshotModel, RecommendationModel
from app.services.growth_analysis_service import GrowthAnalysisService
from app.services.recommendation_service import RecommendationService


class DummyAsyncCursor:
    def __init__(self, items):
        self.items = items

    def __aiter__(self):
        return self._gen()

    async def _gen(self):
        for item in self.items:
            yield item

    def sort(self, *args, **kwargs):
        return self

    def limit(self, *args, **kwargs):
        return self


class MockDB:
    def __init__(self):
        self.collections = {}

    def __getitem__(self, name):
        if name not in self.collections:
            self.collections[name] = MockCollection()
        return self.collections[name]


class MockCollection:
    def __init__(self):
        self.docs = []

    async def insert_one(self, doc):
        if "_id" not in doc:
            doc["_id"] = ObjectId()
        self.docs.append(doc)
        res = MagicMock()
        res.inserted_id = doc["_id"]
        return res

    async def find_one(self, query):
        for doc in self.docs:
            match = True
            for k, v in query.items():
                if k == "_id" and isinstance(v, ObjectId):
                    if doc.get("_id") != v:
                        match = False
                        break
                elif doc.get(k) != v:
                    match = False
                    break
            if match:
                return doc
        return None

    async def update_one(self, filter_q, update_q, upsert=False):
        doc = await self.find_one(filter_q)
        if doc and "$set" in update_q:
            doc.update(update_q["$set"])
        elif not doc and upsert:
            new_doc = dict(filter_q)
            if "$set" in update_q:
                new_doc.update(update_q["$set"])
            if "_id" not in new_doc:
                new_doc["_id"] = ObjectId()
            self.docs.append(new_doc)
        return MagicMock(modified_count=1)

    async def find_one_and_update(self, filter_q, update_q, return_document=True):
        doc = await self.find_one(filter_q)
        if doc and "$set" in update_q:
            doc.update(update_q["$set"])
            return doc
        return None

    def find(self, query=None):
        if not query:
            return DummyAsyncCursor(self.docs)
        matching = []
        for doc in self.docs:
            if "$in" in str(query):
                # Handle status in query
                status_filter = query.get("status")
                if isinstance(status_filter, dict) and "$in" in status_filter:
                    if doc.get("status") not in status_filter["$in"]:
                        continue
            match = True
            for k, v in query.items():
                if k == "status" and isinstance(v, dict):
                    continue
                if doc.get(k) != v:
                    match = False
                    break
            if match:
                matching.append(doc)
        return DummyAsyncCursor(matching)


@pytest.mark.asyncio
async def test_growth_categorization_and_deltas():
    """Test GrowthAnalysisService correctly categorizes concepts into IMPROVING, STABLE, REQUIRING_ATTENTION, and INSUFFICIENT_EVIDENCE."""
    db = MockDB()
    pid = str(ObjectId())
    uid = "user_growth_101"

    # Seed Project
    await db["projects"].insert_one({
        "_id": ObjectId(pid),
        "user_id": uid,
        "name": "ML Course"
    })

    # Concept 1: Brand new concept (no attempts) -> INSUFFICIENT_EVIDENCE
    c1_id = str(ObjectId())
    await db["concepts"].insert_one({
        "_id": ObjectId(c1_id),
        "project_id": pid,
        "name": "Neural Nets",
        "mastery_score": 0.0,
        "attempts": 0
    })

    # Concept 2: Improving concept (+15% delta) -> IMPROVING
    c2_id = str(ObjectId())
    await db["concepts"].insert_one({
        "_id": ObjectId(c2_id),
        "project_id": pid,
        "name": "Gradient Descent",
        "mastery_score": 75.0,
        "attempts": 4
    })
    await db["mastery_events"].insert_one({
        "concept_id": c2_id,
        "project_id": pid,
        "user_id": uid,
        "previous_score": 60.0,
        "new_score": 75.0,
        "created_at": datetime.now(timezone.utc)
    })

    # Concept 3: Declining concept (-10% delta) -> REQUIRING_ATTENTION
    c3_id = str(ObjectId())
    await db["concepts"].insert_one({
        "_id": ObjectId(c3_id),
        "project_id": pid,
        "name": "Regularization",
        "mastery_score": 40.0,
        "attempts": 3
    })
    await db["mastery_events"].insert_one({
        "concept_id": c3_id,
        "project_id": pid,
        "user_id": uid,
        "previous_score": 55.0,
        "new_score": 40.0,
        "created_at": datetime.now(timezone.utc)
    })

    growth_svc = GrowthAnalysisService(db)
    with patch("app.services.growth_analysis_service.get_project", new=AsyncMock()):
        response = await growth_svc.analyze_project_growth(pid, uid)

    assert response.total_concepts == 3
    assert response.improving_count == 1
    assert response.requiring_attention_count == 1
    assert response.insufficient_evidence_count == 1

    snapshots_by_id = {s.concept_id: s for s in response.snapshots}
    assert snapshots_by_id[c1_id].category == "INSUFFICIENT_EVIDENCE"
    assert snapshots_by_id[c2_id].category == "IMPROVING"
    assert snapshots_by_id[c2_id].change_percentage == 15.0
    assert snapshots_by_id[c3_id].category == "REQUIRING_ATTENTION"
    assert snapshots_by_id[c3_id].change_percentage == -15.0


@pytest.mark.asyncio
async def test_recommendation_generation_and_grounding():
    """Test RecommendationService generates material-grounded page references and avoids duplicates."""
    db = MockDB()
    pid = str(ObjectId())
    uid = "user_rec_202"

    await db["projects"].insert_one({
        "_id": ObjectId(pid),
        "user_id": uid,
        "name": "ML Course"
    })

    # Seed material and chunk with page 24 reference
    mat_id = str(ObjectId())
    await db["materials"].insert_one({
        "_id": ObjectId(mat_id),
        "project_id": pid,
        "user_id": uid,
        "filename": "ML_Textbook.pdf",
        "status": "READY"
    })

    c_id = str(ObjectId())
    await db["concepts"].insert_one({
        "_id": ObjectId(c_id),
        "project_id": pid,
        "name": "Overfitting",
        "mastery_score": 35.0,
        "attempts": 2
    })

    await db["mastery_events"].insert_one({
        "concept_id": c_id,
        "project_id": pid,
        "user_id": uid,
        "previous_score": 50.0,
        "new_score": 35.0,
        "created_at": datetime.now(timezone.utc)
    })

    await db["chunks"].insert_one({
        "project_id": pid,
        "concept_ids": c_id,
        "material_id": mat_id,
        "filename": "ML_Textbook.pdf",
        "page_number": 24,
        "chunk_text": "Overfitting occurs when model memorizes training noise."
    })

    rec_svc = RecommendationService(db)
    with patch("app.services.recommendation_service.get_project", new=AsyncMock()), \
         patch("app.services.growth_analysis_service.get_project", new=AsyncMock()):
        recs = await rec_svc.generate_recommendations(pid, uid)

    assert len(recs) >= 1
    # Check grounded material reference
    material_rec = next((r for r in recs if r.type == "REVIEW_MATERIAL"), None)
    assert material_rec is not None
    assert len(material_rec.material_references) == 1
    assert material_rec.material_references[0].filename == "ML_Textbook.pdf"
    assert material_rec.material_references[0].page_number == 24
    assert material_rec.priority == "HIGH"

    # Test Deduplication: Re-running generate_recommendations does NOT create duplicate active recommendations
    with patch("app.services.recommendation_service.get_project", new=AsyncMock()), \
         patch("app.services.growth_analysis_service.get_project", new=AsyncMock()):
        recs_dup = await rec_svc.generate_recommendations(pid, uid)
    material_recs_count = sum(1 for r in recs_dup if r.type == "REVIEW_MATERIAL" and r.concept_id == c_id)
    assert material_recs_count == 1


@pytest.mark.asyncio
async def test_recommendation_completion_lifecycle():
    """Test updating recommendation lifecycle from PENDING to COMPLETED and DISMISSED."""
    db = MockDB()
    pid = str(ObjectId())
    uid = "user_life_303"

    await db["projects"].insert_one({
        "_id": ObjectId(pid),
        "user_id": uid,
        "name": "ML Course"
    })

    rec_id = str(ObjectId())
    await db["recommendations"].insert_one({
        "_id": ObjectId(rec_id),
        "project_id": pid,
        "user_id": uid,
        "type": "PRACTICE_QUIZ",
        "title": "Practice Overfitting Quiz",
        "description": "Improve score",
        "reason": "Low mastery",
        "action": "Take quiz",
        "material_references": [],
        "priority": "HIGH",
        "status": "PENDING",
        "created_at": datetime.now(timezone.utc)
    })

    rec_svc = RecommendationService(db)

    # 1. Complete recommendation
    with patch("app.services.recommendation_service.get_project", new=AsyncMock()):
        completed = await rec_svc.complete_recommendation(rec_id, pid, uid)
    assert completed.status == "COMPLETED"
    assert completed.completed_at is not None

    # 2. Dismiss recommendation
    rec2_id = str(ObjectId())
    await db["recommendations"].insert_one({
        "_id": ObjectId(rec2_id),
        "project_id": pid,
        "user_id": uid,
        "type": "REVIEW_CONCEPT",
        "title": "Review Definitions",
        "status": "PENDING",
        "created_at": datetime.now(timezone.utc)
    })

    with patch("app.services.recommendation_service.get_project", new=AsyncMock()):
        dismiss_ok = await rec_svc.dismiss_recommendation(rec2_id, pid, uid)
    assert dismiss_ok is True
    rec2_doc = await db["recommendations"].find_one({"_id": ObjectId(rec2_id)})
    assert rec2_doc["status"] == "DISMISSED"


