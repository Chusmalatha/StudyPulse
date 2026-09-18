"""
RAG Isolation Test Suite.

Verifies project-isolated vector knowledge search with mock MongoDB cursor.
"""
import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from bson import ObjectId
from app.schemas.knowledge import SearchResponse, SearchResultItem


class DummyAsyncCursor:
    def __init__(self, items):
        self.items = items
    def __aiter__(self):
        return self._gen()
    async def _gen(self):
        for item in self.items:
            yield item


@pytest.mark.asyncio
async def test_rag_project_isolation():
    proj_a = str(ObjectId())
    proj_b = str(ObjectId())
    user_id = str(ObjectId())

    chunk_a = {
        "_id": "chk_a",
        "project_id": proj_a,
        "material_id": "mat_a",
        "filename": "quantum.pdf",
        "page_number": 1,
        "chunk_index": 0,
        "chunk_text": "Quantum superposition allows qubits to exist in multiple states simultaneously.",
        "embedding": [0.1] * 384,
    }

    proj_doc = {"_id": ObjectId(proj_a), "space_id": str(ObjectId()), "user_id": user_id, "name": "Quantum Physics"}
    db_mock = MagicMock()
    db_mock["projects"].find_one = AsyncMock(return_value=proj_doc)
    db_mock["chunks"].find = lambda q, *a, **kw: DummyAsyncCursor([chunk_a] if q.get("project_id") == proj_a else [])

    with patch("app.services.retrieval_service.get_database", return_value=db_mock), \
         patch("app.services.project_service.get_database", return_value=db_mock), \
         patch("app.services.embedding_service.generate_embeddings", new_callable=AsyncMock, return_value=[[0.1] * 384]):

        from app.services.retrieval_service import search_project_knowledge

        # Search Project A
        res_a = await search_project_knowledge(proj_a, user_id, "quantum superposition")
        assert len(res_a.results) > 0
        assert res_a.results[0].filename == "quantum.pdf"

        # Search Project B -> 0 results from Project A
        res_b = await search_project_knowledge(proj_b, user_id, "quantum superposition")
        assert len(res_b.results) == 0
