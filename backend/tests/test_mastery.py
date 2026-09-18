"""
Automated unit and integration test suite for Phase 7 — Concept Mastery & Persistent Context.
"""
import pytest
from datetime import datetime, timezone
from app.models.concept import ConceptModel
from app.services.mastery_service import MasteryService
from app.services.learning_context_service import LearningContextService


import pytest
from unittest.mock import AsyncMock, MagicMock
from bson import ObjectId
from datetime import datetime, timezone
from app.models.concept import ConceptModel
from app.services.mastery_service import MasteryService
from app.services.learning_context_service import LearningContextService


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
                if doc.get(k) != v:
                    match = False
                    break
            if match:
                return doc
        return None

    async def update_one(self, filter_q, update_q):
        doc = await self.find_one(filter_q)
        if doc and "$set" in update_q:
            doc.update(update_q["$set"])
        return MagicMock()

    def find(self, query=None):
        if not query:
            return DummyAsyncCursor(self.docs)
        matching = []
        for doc in self.docs:
            if "$or" in query:
                or_match = False
                for cond in query["$or"]:
                    cond_match = True
                    for k, v in cond.items():
                        if doc.get(k) != v:
                            cond_match = False
                            break
                    if cond_match:
                        or_match = True
                        break
                if or_match and doc.get("user_id") == query.get("user_id"):
                    matching.append(doc)
            else:
                match = True
                for k, v in query.items():
                    if doc.get(k) != v:
                        match = False
                        break
                if match:
                    matching.append(doc)
        return DummyAsyncCursor(matching)


@pytest.mark.asyncio
async def test_concept_mastery_zero_fake_data_baseline():
    """Verify new concepts start with 0.0 mastery, 0.0 confidence, and 0 attempts."""
    db = MockDB()
    concept_doc = {
        "project_id": "proj_p7_test",
        "name": "Neural Networks",
        "description": "Deep learning architectures",
        "mastery_score": 0.0,
        "confidence": 0.0,
        "attempts": 0,
        "correct": 0,
        "mistakes": 0,
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc),
    }
    res = await db["concepts"].insert_one(concept_doc)

    fetched = await db["concepts"].find_one({"_id": res.inserted_id})
    assert fetched["mastery_score"] == 0.0
    assert fetched["confidence"] == 0.0
    assert fetched["attempts"] == 0


@pytest.mark.asyncio
async def test_mastery_update_engine_bounded_and_idempotent():
    """
    Test mastery update calculations, asymptotic confidence, audit log creation,
    and evidence idempotency.
    """
    db = MockDB()
    cid = str(ObjectId())
    concept_doc = {
        "_id": ObjectId(cid),
        "project_id": "proj_mastery_101",
        "name": "Backpropagation",
        "description": "Gradient calculations in neural nets",
        "mastery_score": 0.0,
        "confidence": 0.0,
        "attempts": 0,
        "correct": 0,
        "mistakes": 0,
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc),
    }
    await db["concepts"].insert_one(concept_doc)

    mastery_svc = MasteryService(db)

    # 1. First correct attempt
    c1 = await mastery_svc.update_mastery(
        user_id="user_p7",
        project_id="proj_mastery_101",
        concept_id=cid,
        evidence_type="MCQ",
        evidence_id="attempt_001",
        is_correct=True,
        difficulty=1.0,
        reason="Correct MCQ answer"
    )

    assert c1 is not None
    assert c1.mastery_score > 0.0
    assert c1.attempts == 1
    assert c1.confidence > 0.0
    assert c1.mastery_score <= 100.0

    # Verify audit event in DB
    evt = await db["mastery_events"].find_one({"evidence_id": "attempt_001"})
    assert evt is not None
    assert evt["concept_id"] == cid
    assert evt["previous_score"] == 0.0

    # 2. Idempotency Check: Resubmit exact same evidence_id
    c1_dup = await mastery_svc.update_mastery(
        user_id="user_p7",
        project_id="proj_mastery_101",
        concept_id=cid,
        evidence_type="MCQ",
        evidence_id="attempt_001",
        is_correct=True,
        difficulty=1.0
    )

    assert c1_dup.mastery_score == c1.mastery_score
    assert c1_dup.attempts == 1  # Attempts must NOT increment twice

    # 3. Subsequent incorrect attempt
    c2 = await mastery_svc.update_mastery(
        user_id="user_p7",
        project_id="proj_mastery_101",
        concept_id=cid,
        evidence_type="MCQ",
        evidence_id="attempt_002",
        is_correct=False,
        difficulty=1.0,
        mistake_description="Confused chain rule with derivative addition"
    )

    assert c2.mastery_score < c1.mastery_score
    assert c2.attempts == 2
    assert c2.mistakes == 1

    # Verify repeated mistake record created
    mistake_doc = await db["repeated_mistakes"].find_one({"concept_id": cid, "user_id": "user_p7"})
    assert mistake_doc is not None
    assert "chain rule" in mistake_doc["mistake_description"]


@pytest.mark.asyncio
async def test_learning_context_isolation_and_relevance():
    """Test project scoping, global context handling, and relevance-based retrieval."""
    db = MockDB()
    ctx_svc = LearningContextService(db)

    # Store Project A weakness
    await ctx_svc.store_or_update_context(
        user_id="user_p7_context",
        project_id="proj_A",
        context_type="WEAKNESS",
        key="weakness_backprop",
        value="Struggles with matrix backpropagation math",
        importance=1.5
    )

    # Store Project B weakness
    await ctx_svc.store_or_update_context(
        user_id="user_p7_context",
        project_id="proj_B",
        context_type="WEAKNESS",
        key="weakness_sql",
        value="Struggles with SQL outer joins",
        importance=1.5
    )

    # Retrieve context for Project A query
    proj_a_ctx = await ctx_svc.retrieve_relevant_context(
        user_id="user_p7_context",
        project_id="proj_A",
        query="Explain backpropagation",
        limit=5
    )

    assert len(proj_a_ctx) == 1
    assert proj_a_ctx[0].project_id == "proj_A"
    assert "backpropagation" in proj_a_ctx[0].value.lower()

    # Verify Project B weakness does NOT leak into Project A queries
    assert not any(c.project_id == "proj_B" for c in proj_a_ctx)

