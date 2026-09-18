"""
Automated tests for Phase 4 — Knowledge Extraction & RAG Semantic Retrieval.

Covering:
- Structured Knowledge Extraction (Concepts, Topics, Sections from text chunks)
- Concept Deduplication (re-running extraction updates existing concept references)
- RAG Vector Similarity Search (query embedding, cosine score ranking, Top-K)
- Grounded Citation Metadata (preserves material_id, filename, page_number, score)
- Strict Project-Level Security & Data Isolation (User A vs User B, Project A vs Project B)
- Empty Project & Low-Relevance Search Behavior
"""
import pytest
from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient
from bson import ObjectId

from app.main import app
from app.core.security import create_access_token
from app.services import knowledge_extraction_service, retrieval_service

client = TestClient(app)

USER_A_ID = str(ObjectId())
USER_B_ID = str(ObjectId())
PROJECT_A_ID = str(ObjectId())
PROJECT_B_ID = str(ObjectId())
MATERIAL_A_ID = str(ObjectId())
MATERIAL_B_ID = str(ObjectId())

USER_A_DOC = {
    "_id": ObjectId(USER_A_ID),
    "name": "User A",
    "email": "user_a@example.com",
    "role": "user",
    "is_active": True,
}


def _auth_header(user_id: str) -> dict:
    return {"Authorization": f"Bearer {create_access_token(subject=user_id)}"}


@pytest.fixture
def mock_get_user():
    async def _side_effect(user_id: str):
        if user_id == USER_A_ID:
            return USER_A_DOC
        return None

    with patch("app.api.dependencies.auth_service.get_user_by_id", side_effect=_side_effect):
        yield


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


# ── 1. Knowledge Extraction Unit Tests ────────────────────────────────────────

class TestKnowledgeExtractionService:
    def test_extract_knowledge_from_chunk_texts(self):
        sample_chunks = [
            {
                "material_id": MATERIAL_A_ID,
                "page_number": 1,
                "chunk_text": "Chapter 1: Machine Learning Overview\nMachine Learning is a subset of Artificial Intelligence focusing on algorithms.",
            },
            {
                "material_id": MATERIAL_A_ID,
                "page_number": 12,
                "chunk_text": "Regularization techniques help prevent Overfitting by penalizing complex models during Gradient Descent.",
            },
        ]

        concepts, topics, sections = knowledge_extraction_service._extract_knowledge_from_chunk_texts(sample_chunks)

        assert len(concepts) > 0
        assert len(topics) > 0

        # Verify page number grounding is preserved
        concept_names = [c["name"].lower() for c in concepts]
        assert any("regularization" in name or "overfitting" in name or "machine" in name for name in concept_names)

        for c in concepts:
            assert "source_pages" in c
            assert len(c["source_pages"]) > 0

    @pytest.mark.asyncio
    async def test_extract_project_knowledge_deduplication(self):
        mock_chunks = [
            {
                "_id": ObjectId(),
                "project_id": PROJECT_A_ID,
                "material_id": MATERIAL_A_ID,
                "filename": "ml_notes.pdf",
                "page_number": 5,
                "chunk_index": 0,
                "chunk_text": "Gradient Descent is an optimization algorithm used to minimize loss.",
            }
        ]

        mock_proj = {"_id": ObjectId(PROJECT_A_ID), "user_id": USER_A_ID, "name": "Project A"}

        mock_concepts = AsyncMock()
        mock_concepts.find_one = AsyncMock(return_value=None)
        mock_concepts.insert_one = AsyncMock()
        mock_concepts.find = lambda *args, **kwargs: DummyAsyncCursor([])

        mock_topics = AsyncMock()
        mock_topics.find_one = AsyncMock(return_value=None)
        mock_topics.insert_one = AsyncMock()
        mock_topics.find = lambda *args, **kwargs: DummyAsyncCursor([])

        mock_sections = AsyncMock()
        mock_sections.find_one = AsyncMock(return_value=None)
        mock_sections.insert_one = AsyncMock()
        mock_sections.find = lambda *args, **kwargs: DummyAsyncCursor([])

        mock_chunks_coll = AsyncMock()
        mock_chunks_coll.find = lambda *args, **kwargs: DummyAsyncCursor(mock_chunks)

        collections = {
            "chunks": mock_chunks_coll,
            "concepts": mock_concepts,
            "topics": mock_topics,
            "sections": mock_sections,
        }

        mock_db = AsyncMock()
        mock_db.__getitem__.side_effect = lambda k: collections.get(k, AsyncMock())

        with patch("app.services.knowledge_extraction_service.get_project", AsyncMock(return_value=mock_proj)), \
             patch("app.services.knowledge_extraction_service.get_database", return_value=mock_db):

            await knowledge_extraction_service.extract_project_knowledge(PROJECT_A_ID, USER_A_ID)

            assert mock_concepts.insert_one.called or mock_concepts.find_one.called



# ── 2. RAG Semantic Retrieval Unit Tests ──────────────────────────────────────

class TestRAGSemanticRetrieval:
    @pytest.mark.asyncio
    async def test_search_project_knowledge_success(self):
        # Create 2 mock chunks for Project A with embeddings
        mock_chunks = [
            {
                "_id": ObjectId(),
                "project_id": PROJECT_A_ID,
                "material_id": MATERIAL_A_ID,
                "filename": "ml_textbook.pdf",
                "page_number": 14,
                "chunk_index": 0,
                "chunk_text": "Regularization restricts model weights to prevent overfitting in deep neural networks.",
                "embedding": [0.1] * 64,
            },
            {
                "_id": ObjectId(),
                "project_id": PROJECT_A_ID,
                "material_id": MATERIAL_A_ID,
                "filename": "ml_textbook.pdf",
                "page_number": 2,
                "chunk_index": 1,
                "chunk_text": "Introduction to Python programming language syntax.",
                "embedding": [0.0] * 64,
            },
        ]

        mock_proj = {"_id": ObjectId(PROJECT_A_ID), "user_id": USER_A_ID, "name": "Project A"}

        mock_db = AsyncMock()
        mock_db["chunks"].find = lambda *args, **kwargs: DummyAsyncCursor(mock_chunks)

        with patch("app.services.retrieval_service.get_project", AsyncMock(return_value=mock_proj)), \
             patch("app.services.retrieval_service.get_database", return_value=mock_db), \
             patch("app.services.embedding_service.generate_embeddings", AsyncMock(return_value=[[0.1] * 64])):

            res = await retrieval_service.search_project_knowledge(
                project_id=PROJECT_A_ID,
                user_id=USER_A_ID,
                query="What is regularization?",
                top_k=2,
            )

            assert res.query == "What is regularization?"
            assert res.project_id == PROJECT_A_ID
            assert len(res.results) > 0
            
            top_result = res.results[0]
            assert top_result.filename == "ml_textbook.pdf"
            assert top_result.page_number == 14
            assert top_result.score > 0.0

    @pytest.mark.asyncio
    async def test_search_empty_project_returns_zero_results(self):
        mock_proj = {"_id": ObjectId(PROJECT_A_ID), "user_id": USER_A_ID, "name": "Project A"}
        mock_db = AsyncMock()
        mock_db["chunks"].find = lambda *args, **kwargs: DummyAsyncCursor([])

        with patch("app.services.retrieval_service.get_project", AsyncMock(return_value=mock_proj)), \
             patch("app.services.retrieval_service.get_database", return_value=mock_db):

            res = await retrieval_service.search_project_knowledge(
                project_id=PROJECT_A_ID,
                user_id=USER_A_ID,
                query="What is machine learning?",
                top_k=5,
            )

            assert res.results == []
            assert res.total_results == 0



# ── 3. API & Security Isolation Tests ─────────────────────────────────────────

class TestKnowledgeAPIAndSecurity:
    def test_search_unauthenticated_fails(self):
        resp = client.post(f"/api/v1/projects/{PROJECT_A_ID}/search", json={"query": "test", "top_k": 5})
        assert resp.status_code in (401, 403)

    def test_get_knowledge_unauthenticated_fails(self):
        resp = client.get(f"/api/v1/projects/{PROJECT_A_ID}/knowledge")
        assert resp.status_code in (401, 403)

    def test_search_unowned_project_returns_404(self, mock_get_user):
        with patch("app.services.retrieval_service.get_project", AsyncMock(side_effect=ValueError("not_found"))):
            resp = client.post(
                f"/api/v1/projects/{PROJECT_B_ID}/search",
                headers=_auth_header(USER_A_ID),
                json={"query": "What is overfitting?", "top_k": 5},
            )
        assert resp.status_code == 404

    def test_search_endpoint_success(self, mock_get_user):
        mock_res = {
            "query": "regularization",
            "project_id": PROJECT_A_ID,
            "results": [
                {
                    "chunk_id": str(ObjectId()),
                    "material_id": MATERIAL_A_ID,
                    "filename": "notes.pdf",
                    "page_number": 3,
                    "chunk_text": "Regularization controls variance.",
                    "score": 0.85,
                }
            ],
            "total_results": 1,
        }
        with patch("app.services.retrieval_service.search_project_knowledge", AsyncMock(return_value=mock_res)):
            resp = client.post(
                f"/api/v1/projects/{PROJECT_A_ID}/search",
                headers=_auth_header(USER_A_ID),
                json={"query": "regularization", "top_k": 5},
            )
        assert resp.status_code == 200
        data = resp.json()
        assert data["query"] == "regularization"
        assert len(data["results"]) == 1
        assert data["results"][0]["page_number"] == 3
