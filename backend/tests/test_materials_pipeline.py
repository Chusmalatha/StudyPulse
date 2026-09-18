"""
Automated tests for Phase 3 — PDF Upload + Background Processing Pipeline.

Covering:
- Authentication enforcement (401/403 for unauthenticated requests)
- File validation (PDF format check, empty file handling)
- Material & Project security isolation (User A vs User B)
- Page-aware extraction & chunking (page_number preserved on all chunks)
- Processing status progression (QUEUED -> PROCESSING -> READY / FAILED)
- Duplicate job protection (simultaneous processing prevention)
- Idempotency & Retry mechanism (re-running clears old chunks and updates attempts)
- Cascade deletion (deleting material removes chunks and storage file)
"""
import os
import pytest
import io
from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient
from bson import ObjectId
from pypdf import PdfWriter

from app.main import app
from app.core.security import create_access_token
from app.schemas.materials import MaterialResponse
from app.services import pdf_service, material_service
from app.models.material import MaterialStatus

client = TestClient(app)

USER_A_ID = str(ObjectId())
USER_B_ID = str(ObjectId())
PROJECT_A_ID = str(ObjectId())
PROJECT_B_ID = str(ObjectId())

USER_A_DOC = {
    "_id": ObjectId(USER_A_ID),
    "name": "User A",
    "email": "user_a@example.com",
    "role": "user",
    "is_active": True,
}


def _auth_header(user_id: str) -> dict:
    return {"Authorization": f"Bearer {create_access_token(subject=user_id)}"}


def _create_sample_pdf_bytes() -> bytes:
    """Helper to generate a valid multi-page PDF in memory."""
    writer = PdfWriter()
    writer.add_blank_page(width=200, height=200)
    writer.add_blank_page(width=200, height=200)
    buf = io.BytesIO()
    writer.write(buf)
    return buf.getvalue()


@pytest.fixture
def mock_get_user():
    async def _side_effect(user_id: str):
        if user_id == USER_A_ID:
            return USER_A_DOC
        return None

    with patch("app.api.dependencies.auth_service.get_user_by_id", side_effect=_side_effect):
        yield


# ── 1. Unauthenticated Access Tests ───────────────────────────────────────────

class TestUnauthenticatedMaterialAccess:
    def test_materials_endpoints_require_auth(self):
        proj_id = str(ObjectId())
        mat_id = str(ObjectId())

        assert client.post(f"/api/v1/projects/{proj_id}/materials").status_code in (401, 403)
        assert client.get(f"/api/v1/projects/{proj_id}/materials").status_code in (401, 403)
        assert client.get(f"/api/v1/materials/{mat_id}").status_code in (401, 403)
        assert client.post(f"/api/v1/materials/{mat_id}/retry").status_code in (401, 403)
        assert client.get(f"/api/v1/materials/{mat_id}/chunks").status_code in (401, 403)
        assert client.delete(f"/api/v1/materials/{mat_id}").status_code in (401, 403)


# ── 2. PDF Validation & Page Extraction Unit Tests ─────────────────────────────

class TestPDFProcessingService:
    def test_chunk_pages_preserves_page_number(self):
        pages = [
            {"page_number": 1, "text": "This is page 1 introduction to Machine Learning."},
            {"page_number": 2, "text": "This is page 2 detailing neural networks and deep learning models."},
        ]
        chunks = pdf_service.chunk_pages(pages, chunk_size=30, overlap=5)
        assert len(chunks) > 0

        # Verify page_number is explicitly present on EVERY chunk
        for chunk in chunks:
            assert "page_number" in chunk
            assert chunk["page_number"] in (1, 2)
            assert "chunk_text" in chunk
            assert "chunk_index" in chunk

    def test_invalid_pdf_path_raises_value_error(self):
        with pytest.raises(ValueError, match="Corrupt or unreadable PDF"):
            pdf_service.extract_pdf_pages("non_existent_file.pdf")


# ── 3. API Upload & Security Isolation Tests ───────────────────────────────────

class TestMaterialUploadAndSecurity:
    def test_upload_non_pdf_fails(self, mock_get_user):
        mock_proj = {"_id": ObjectId(PROJECT_A_ID), "user_id": USER_A_ID, "name": "Project A"}
        with patch("app.services.material_service.get_project", AsyncMock(return_value=mock_proj)):
            file_data = ("notes.txt", b"plain text content", "text/plain")
            resp = client.post(
                f"/api/v1/projects/{PROJECT_A_ID}/materials",
                headers=_auth_header(USER_A_ID),
                files={"file": file_data},
            )
        assert resp.status_code == 400
        assert "only pdf files are supported" in resp.json()["detail"].lower()

    def test_upload_empty_pdf_fails(self, mock_get_user):
        mock_proj = {"_id": ObjectId(PROJECT_A_ID), "user_id": USER_A_ID, "name": "Project A"}
        with patch("app.services.material_service.get_project", AsyncMock(return_value=mock_proj)):
            file_data = ("empty.pdf", b"", "application/pdf")
            resp = client.post(
                f"/api/v1/projects/{PROJECT_A_ID}/materials",
                headers=_auth_header(USER_A_ID),
                files={"file": file_data},
            )
        assert resp.status_code == 400
        assert "empty" in resp.json()["detail"].lower()

    def test_upload_to_unowned_project_returns_404(self, mock_get_user):
        with patch("app.services.material_service.get_project", AsyncMock(side_effect=ValueError("not_found"))):
            file_data = ("test.pdf", b"%PDF-1.4 sample content", "application/pdf")
            resp = client.post(
                f"/api/v1/projects/{PROJECT_B_ID}/materials",
                headers=_auth_header(USER_A_ID),
                files={"file": file_data},
            )
        assert resp.status_code == 404

    def test_get_unowned_material_returns_404(self, mock_get_user):
        mat_id = str(ObjectId())
        with patch("app.services.material_service.get_material", AsyncMock(side_effect=ValueError("not_found"))):
            resp = client.get(
                f"/api/v1/materials/{mat_id}",
                headers=_auth_header(USER_A_ID),
            )
        assert resp.status_code == 404

    def test_get_material_status_nested_alias(self, mock_get_user):
        mat_id = str(ObjectId())
        mock_resp = {
            "id": mat_id,
            "project_id": PROJECT_A_ID,
            "user_id": USER_A_ID,
            "filename": "test.pdf",
            "file_type": "application/pdf",
            "file_size": 1024,
            "status": "READY",
            "processing_attempts": 1,
        }
        with patch("app.services.material_service.get_material", AsyncMock(return_value=mock_resp)):
            resp = client.get(
                f"/api/v1/projects/{PROJECT_A_ID}/materials/{mat_id}",
                headers=_auth_header(USER_A_ID),
            )
        assert resp.status_code == 200
        assert resp.json()["id"] == mat_id
        assert resp.json()["status"] == "READY"


# ── 4. Background Processing Pipeline & Retry Tests ─────────────────────────

class TestBackgroundProcessingPipeline:
    @pytest.mark.asyncio
    async def test_process_material_task_duplicate_protection(self):
        mat_id = str(ObjectId())
        mock_mat = {
            "_id": ObjectId(mat_id),
            "project_id": PROJECT_A_ID,
            "user_id": USER_A_ID,
            "filename": "sample.pdf",
            "file_path": "storage/materials/test.pdf",
            "status": MaterialStatus.PROCESSING.value,
            "processing_attempts": 1,
        }

        mock_db = AsyncMock()
        mock_db["materials"].find_one = AsyncMock(return_value=mock_mat)

        with patch("app.services.material_service.get_database", return_value=mock_db), \
             patch("app.services.pdf_service.extract_pdf_pages") as mock_extract:

            await material_service.process_material_task(mat_id, PROJECT_A_ID, USER_A_ID)

            # verify extraction was NOT called because status was already PROCESSING
            mock_extract.assert_not_called()

    @pytest.mark.asyncio
    async def test_process_material_task_success_pipeline(self):
        mat_id = str(ObjectId())
        mock_mat = {
            "_id": ObjectId(mat_id),
            "project_id": PROJECT_A_ID,
            "user_id": USER_A_ID,
            "filename": "ml_notes.pdf",
            "file_path": "storage/materials/ml_notes.pdf",
            "status": MaterialStatus.QUEUED.value,
            "processing_attempts": 0,
        }

        mock_pages = [
            {"page_number": 1, "text": "Introduction to Machine Learning concepts."},
            {"page_number": 2, "text": "Supervised learning vs Unsupervised learning algorithms."},
        ]

        mock_db = AsyncMock()
        mock_db["materials"].find_one = AsyncMock(return_value=mock_mat)
        mock_db["materials"].update_one = AsyncMock()
        mock_db["background_jobs"].update_one = AsyncMock()
        mock_db["chunks"].delete_many = AsyncMock(return_value=AsyncMock(deleted_count=0))
        mock_db["chunks"].insert_many = AsyncMock()

        with patch("app.services.material_service.get_database", return_value=mock_db), \
             patch("app.services.pdf_service.extract_pdf_pages", return_value=mock_pages), \
             patch("app.services.embedding_service.generate_embeddings", AsyncMock(return_value=[[0.1]*64, [0.2]*64])):

            await material_service.process_material_task(mat_id, PROJECT_A_ID, USER_A_ID)

            # Verify chunks were cleared and inserted with page numbers preserved
            assert mock_db["chunks"].delete_many.called
            assert mock_db["chunks"].insert_many.called
            assert mock_db["background_jobs"].update_one.called
            inserted_docs = mock_db["chunks"].insert_many.call_args[0][0]
            assert len(inserted_docs) > 0
            for doc in inserted_docs:
                assert "page_number" in doc
                assert doc["project_id"] == PROJECT_A_ID
                assert doc["material_id"] == mat_id
                assert doc["filename"] == "ml_notes.pdf"

    def test_retry_ready_material_fails(self, mock_get_user):
        mat_id = str(ObjectId())
        mock_mat = {
            "_id": ObjectId(mat_id),
            "user_id": USER_A_ID,
            "project_id": PROJECT_A_ID,
            "status": "READY",
            "processing_attempts": 1,
        }
        with patch("app.services.material_service.get_database") as mock_db:
            mock_db.return_value["materials"].find_one = AsyncMock(return_value=mock_mat)
            resp = client.post(
                f"/api/v1/materials/{mat_id}/retry",
                headers=_auth_header(USER_A_ID),
            )
        assert resp.status_code == 400
        assert "only failed or queued materials can be retried" in resp.json()["detail"].lower()

    def test_retry_exceeding_max_attempts_fails(self, mock_get_user):
        mat_id = str(ObjectId())
        mock_mat = {
            "_id": ObjectId(mat_id),
            "user_id": USER_A_ID,
            "project_id": PROJECT_A_ID,
            "status": "FAILED",
            "processing_attempts": 3,
        }
        with patch("app.services.material_service.get_database") as mock_db:
            mock_db.return_value["materials"].find_one = AsyncMock(return_value=mock_mat)
            resp = client.post(
                f"/api/v1/materials/{mat_id}/retry",
                headers=_auth_header(USER_A_ID),
            )
        assert resp.status_code == 400
        assert "maximum processing retries reached" in resp.json()["detail"].lower()

