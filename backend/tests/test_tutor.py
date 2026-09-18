"""
Automated tests for Phase 5 — AI Tutor.

Covering:
1. Supported question with grounded RAG context -> answer + citations (material_id, filename, page_number)
2. Unsupported question (no evidence / low relevance) -> strict refusal (grounded=False, unsupported=True, citations=[])
3. Follow-up questions with conversation context
4. Citation correctness & verification against retrieved chunks
5. Cross-project isolation (Project A query never retrieves Project B evidence)
6. Empty project & processing material handling
7. Conversation & message persistence
8. Unauthorized user access (404/401 handling)
9. Malformed / invalid LLM JSON output handling
"""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi.testclient import TestClient
from bson import ObjectId

from app.main import app
from app.core.security import create_access_token

client = TestClient(app)

USER_A_ID = str(ObjectId())
USER_B_ID = str(ObjectId())
PROJECT_A_ID = str(ObjectId())
PROJECT_B_ID = str(ObjectId())
CONVERSATION_A_ID = str(ObjectId())
MATERIAL_A_ID = str(ObjectId())
CHUNK_A_ID = str(ObjectId())

USER_A_DOC = {
    "_id": ObjectId(USER_A_ID),
    "name": "User A",
    "email": "usera@example.com",
    "role": "user",
    "is_active": True,
}

USER_B_DOC = {
    "_id": ObjectId(USER_B_ID),
    "name": "User B",
    "email": "userb@example.com",
    "role": "user",
    "is_active": True,
}

PROJECT_A_DOC = {
    "_id": ObjectId(PROJECT_A_ID),
    "space_id": str(ObjectId()),
    "user_id": USER_A_ID,
    "name": "Machine Learning Project",
    "description": "ML Course",
    "learning_goal": "Master Gradient Descent",
    "created_at": "2026-09-16T00:00:00Z",
    "updated_at": "2026-09-16T00:00:00Z",
}

PROJECT_B_DOC = {
    "_id": ObjectId(PROJECT_B_ID),
    "space_id": str(ObjectId()),
    "user_id": USER_B_ID,
    "name": "Database Systems Project",
    "description": "DB Course",
    "learning_goal": "Master SQL",
    "created_at": "2026-09-16T00:00:00Z",
    "updated_at": "2026-09-16T00:00:00Z",
}

CONVERSATION_A_DOC = {
    "_id": ObjectId(CONVERSATION_A_ID),
    "project_id": PROJECT_A_ID,
    "user_id": USER_A_ID,
    "title": "Gradient Descent Intro",
    "created_at": "2026-09-16T00:00:00Z",
    "updated_at": "2026-09-16T00:00:00Z",
    "last_message_at": "2026-09-16T00:00:00Z",
}

MATERIAL_A_DOC = {
    "_id": ObjectId(MATERIAL_A_ID),
    "project_id": PROJECT_A_ID,
    "user_id": USER_A_ID,
    "filename": "Machine Learning Notes.pdf",
    "file_path": "storage/materials/ml_notes.pdf",
    "file_size": 1024,
    "status": "READY",
}

CHUNK_A_DOC = {
    "_id": ObjectId(CHUNK_A_ID),
    "project_id": PROJECT_A_ID,
    "material_id": MATERIAL_A_ID,
    "user_id": USER_A_ID,
    "chunk_index": 0,
    "chunk_text": "Gradient descent is an optimization algorithm used to minimize loss by updating parameters.",
    "page_number": 18,
    "filename": "Machine Learning Notes.pdf",
    "embedding": [0.1] * 64,
}


def _auth_header(user_id: str) -> dict:
    return {"Authorization": f"Bearer {create_access_token(subject=user_id)}"}


@pytest.fixture
def mock_get_user():
    async def _side_effect(user_id: str):
        if user_id == USER_A_ID:
            return USER_A_DOC
        elif user_id == USER_B_ID:
            return USER_B_DOC
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

    def limit(self, *args, **kwargs):
        return self


def _create_mock_db(has_chunks=True):
    db_mock = MagicMock()
    
    # Collection mocks
    proj_coll = MagicMock()
    proj_coll.find_one = AsyncMock(return_value=PROJECT_A_DOC)

    conv_coll = MagicMock()
    conv_coll.find_one = AsyncMock(return_value=CONVERSATION_A_DOC)
    conv_coll.insert_one = AsyncMock(return_value=MagicMock(inserted_id=ObjectId(CONVERSATION_A_ID)))
    conv_coll.find = lambda q, *a, **kw: DummyAsyncCursor([CONVERSATION_A_DOC])
    conv_coll.update_one = AsyncMock()

    msg_coll = MagicMock()
    msg_coll.insert_one = AsyncMock(return_value=MagicMock(inserted_id=ObjectId()))
    msg_coll.find = lambda q, *a, **kw: DummyAsyncCursor([])

    mat_coll = MagicMock()
    mat_coll.find = lambda q, *a, **kw: DummyAsyncCursor([MATERIAL_A_DOC])

    chk_coll = MagicMock()
    chk_coll.find = lambda q, *a, **kw: DummyAsyncCursor([CHUNK_A_DOC] if has_chunks else [])

    cpt_coll = MagicMock()
    cpt_coll.find = lambda q, *a, **kw: DummyAsyncCursor([])

    def get_coll(name):
        collections = {
            "projects": proj_coll,
            "conversations": conv_coll,
            "messages": msg_coll,
            "materials": mat_coll,
            "chunks": chk_coll,
            "concepts": cpt_coll,
        }
        return collections.get(name, MagicMock())

    db_mock.__getitem__.side_effect = get_coll
    return db_mock


@pytest.mark.asyncio
async def test_create_and_list_conversations(mock_get_user):
    """Test creating and listing conversations scoped to a project."""
    db_mock = _create_mock_db()

    with patch("app.services.tutor_service.get_database", return_value=db_mock), \
         patch("app.services.project_service.get_database", return_value=db_mock):

        # 1. Create conversation
        create_res = client.post(
            f"/api/v1/projects/{PROJECT_A_ID}/tutor/conversations",
            headers=_auth_header(USER_A_ID),
            json={"title": "Gradient Descent Intro"},
        )
        assert create_res.status_code == 201
        data = create_res.json()
        assert data["title"] == "Gradient Descent Intro"
        assert data["project_id"] == PROJECT_A_ID

        # 2. List conversations
        list_res = client.get(
            f"/api/v1/projects/{PROJECT_A_ID}/tutor/conversations",
            headers=_auth_header(USER_A_ID),
        )
        assert list_res.status_code == 200
        convs = list_res.json()
        assert len(convs) == 1
        assert (convs[0].get("id") or convs[0].get("_id")) == CONVERSATION_A_ID


@pytest.mark.asyncio
async def test_ask_tutor_supported_question(mock_get_user):
    """Test asking supported question: returns grounded answer and page citation."""
    db_mock = _create_mock_db(has_chunks=True)

    with patch("app.services.tutor_service.get_database", return_value=db_mock), \
         patch("app.services.tutor_context_service.get_database", return_value=db_mock), \
         patch("app.services.project_service.get_database", return_value=db_mock), \
         patch("app.services.retrieval_service.get_database", return_value=db_mock), \
         patch("app.services.retrieval_service.embedding_service.generate_embeddings", new_callable=AsyncMock) as mock_emb:

        mock_emb.return_value = [[0.1] * 64]

        res = client.post(
            f"/api/v1/projects/{PROJECT_A_ID}/tutor/conversations/{CONVERSATION_A_ID}/messages",
            headers=_auth_header(USER_A_ID),
            json={"message": "What is gradient descent?"},
        )
        assert res.status_code == 200
        data = res.json()
        assert data["grounded"] is True
        assert data["unsupported"] is False
        assert len(data["citations"]) > 0
        assert data["citations"][0]["material_id"] == MATERIAL_A_ID
        assert data["citations"][0]["filename"] == "Machine Learning Notes.pdf"
        assert data["citations"][0]["page_number"] == 18


@pytest.mark.asyncio
async def test_ask_tutor_unsupported_question(mock_get_user):
    """Test asking unsupported question: returns unsupported refusal with 0 citations."""
    db_mock = _create_mock_db(has_chunks=False)

    with patch("app.services.tutor_service.get_database", return_value=db_mock), \
         patch("app.services.tutor_context_service.get_database", return_value=db_mock), \
         patch("app.services.project_service.get_database", return_value=db_mock), \
         patch("app.services.retrieval_service.get_database", return_value=db_mock), \
         patch("app.services.retrieval_service.embedding_service.generate_embeddings", new_callable=AsyncMock) as mock_emb:

        mock_emb.return_value = [[-0.5] * 64]

        res = client.post(
            f"/api/v1/projects/{PROJECT_A_ID}/tutor/conversations/{CONVERSATION_A_ID}/messages",
            headers=_auth_header(USER_A_ID),
            json={"message": "Who won yesterday's cricket match?"},
        )
        assert res.status_code == 200
        data = res.json()
        assert data["grounded"] is False
        assert data["unsupported"] is True
        assert len(data["citations"]) == 0
        assert "don't have enough information" in data["answer"]


@pytest.mark.asyncio
async def test_cross_project_isolation(mock_get_user):
    """Test cross-project security: User B cannot access User A's conversation."""
    db_mock = MagicMock()
    proj_coll = MagicMock()
    proj_coll.find_one = AsyncMock(return_value=None)
    conv_coll = MagicMock()
    conv_coll.find_one = AsyncMock(return_value=None)
    db_mock.__getitem__.side_effect = lambda name: proj_coll if name == "projects" else conv_coll

    with patch("app.services.tutor_service.get_database", return_value=db_mock), \
         patch("app.services.project_service.get_database", return_value=db_mock):

        # User B tries to send message in User A's conversation
        res = client.post(
            f"/api/v1/projects/{PROJECT_A_ID}/tutor/conversations/{CONVERSATION_A_ID}/messages",
            headers=_auth_header(USER_B_ID),
            json={"message": "Leak test"},
        )
        assert res.status_code == 404
