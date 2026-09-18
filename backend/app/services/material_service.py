"""
Material business-logic service.

Handles:
- Upload validation (PDF only, non-empty, file size limits)
- Background processing pipeline (QUEUED -> PROCESSING -> READY/FAILED)
- Page-aware extraction, chunking, and embedding creation
- Duplicate job protection (atomic status checks)
- Idempotent retries (cleanup of old chunks before chunk insertion)
- BackgroundJob document tracking
- Project & Material ownership enforcement (404 for unauthorized access)
- Material deletion (file + DB doc + chunks + job tracking cleanup)
"""
import os
import uuid
import logging
from datetime import datetime, timezone
from typing import List, Optional

from bson import ObjectId
from bson.errors import InvalidId
from fastapi import UploadFile, BackgroundTasks

from app.core.config import settings
from app.db.database import get_database
from app.models.material import MaterialStatus
from app.models.job import JobStatus
from app.schemas.materials import MaterialResponse, ChunkResponse, MaterialRetryResponse
from app.services import pdf_service, embedding_service
from app.services.project_service import get_project

logger = logging.getLogger(__name__)

MAX_RETRY_ATTEMPTS = 3


def _oid(value: str) -> ObjectId:
    try:
        return ObjectId(value)
    except (InvalidId, Exception):
        raise ValueError("not_found")


def _doc_to_material_response(doc: dict) -> MaterialResponse:
    return MaterialResponse(
        id=str(doc["_id"]),
        project_id=str(doc["project_id"]),
        user_id=str(doc["user_id"]),
        filename=doc["filename"],
        original_filename=doc.get("original_filename", doc["filename"]),
        file_type=doc.get("file_type", "application/pdf"),
        file_size=doc.get("file_size", 0),
        status=doc.get("status", MaterialStatus.QUEUED),
        processing_attempts=doc.get("processing_attempts", 0),
        error_message=doc.get("error_message"),
        created_at=doc.get("created_at"),
        updated_at=doc.get("updated_at"),
        processed_at=doc.get("processed_at"),
    )


def _doc_to_chunk_response(doc: dict) -> ChunkResponse:
    return ChunkResponse(
        id=str(doc["_id"]),
        project_id=str(doc["project_id"]),
        material_id=str(doc["material_id"]),
        filename=doc["filename"],
        page_number=doc["page_number"],
        chunk_index=doc["chunk_index"],
        chunk_text=doc["chunk_text"],
        created_at=doc.get("created_at"),
    )


async def create_material(
    project_id: str,
    user_id: str,
    file: UploadFile,
    background_tasks: BackgroundTasks,
) -> MaterialResponse:
    """
    Validate upload, store PDF securely, create Material doc & BackgroundJob doc, and queue background task.
    """
    # 1. Validate project ownership
    await get_project(project_id, user_id)

    # 2. Validate file extension and MIME type
    original_filename = file.filename or "uploaded.pdf"
    if not original_filename.lower().endswith(".pdf"):
        raise ValueError("Only PDF files are supported.")

    content_type = file.content_type or ""
    if content_type and "pdf" not in content_type.lower() and content_type != "application/octet-stream":
        raise ValueError("Invalid file format. Please upload a valid PDF document.")

    # 3. Read file content and check configurable size limit
    content = await file.read()
    file_size = len(content)

    if file_size == 0:
        raise ValueError("Uploaded file is empty.")

    max_bytes = settings.MAX_PDF_SIZE_MB * 1024 * 1024
    if file_size > max_bytes:
        raise ValueError(f"File size exceeds maximum allowed limit of {settings.MAX_PDF_SIZE_MB}MB (file size: {file_size / (1024*1024):.1f}MB).")

    # 4. Generate safe storage path
    storage_dir = os.path.abspath(settings.STORAGE_DIR)
    os.makedirs(storage_dir, exist_ok=True)
    unique_filename = f"{uuid.uuid4().hex}.pdf"
    file_path = os.path.join(storage_dir, unique_filename)

    with open(file_path, "wb") as f:
        f.write(content)

    # 5. Insert Material record with status = QUEUED
    db = get_database()
    now = datetime.now(timezone.utc)
    doc = {
        "project_id": project_id,
        "user_id": user_id,
        "filename": original_filename,
        "original_filename": original_filename,
        "file_path": file_path,
        "file_type": "application/pdf",
        "file_size": file_size,
        "status": MaterialStatus.QUEUED.value,
        "processing_attempts": 0,
        "error_message": None,
        "created_at": now,
        "updated_at": now,
        "processed_at": None,
    }

    result = await db["materials"].insert_one(doc)
    doc["_id"] = result.inserted_id
    material_id = str(result.inserted_id)

    # 6. Create BackgroundJob record
    job_doc = {
        "job_type": "PROCESS_PDF",
        "material_id": material_id,
        "project_id": project_id,
        "user_id": user_id,
        "status": JobStatus.QUEUED.value,
        "attempts": 0,
        "max_attempts": MAX_RETRY_ATTEMPTS,
        "started_at": None,
        "completed_at": None,
        "last_error": None,
        "created_at": now,
        "updated_at": now,
    }
    await db["background_jobs"].insert_one(job_doc)

    logger.info(f"Material queued: '{original_filename}' ({material_id}) for project {project_id}")

    # Event publishing: MATERIAL_UPLOADED
    from app.services.event_publisher import publish_event
    await publish_event(
        project_id=project_id,
        user_id=user_id,
        event_type="MATERIAL_UPLOADED",
        payload={
            "material_id": material_id,
            "filename": original_filename,
            "file_size": file_size,
        },
        source_component="material_service",
    )

    # 7. Trigger background processing task
    background_tasks.add_task(process_material_task, material_id, project_id, user_id)

    return _doc_to_material_response(doc)


async def process_material_task(material_id: str, project_id: str, user_id: str) -> None:
    """
    Background worker processing pipeline:
      QUEUED -> PROCESSING -> Extract PDF Pages -> Chunk -> Embed -> Store Chunks -> READY (or FAILED)
    """
    db = get_database()
    if db is None:
        logger.error("Database not connected during background processing task.")
        return

    # Duplicate job protection: Atomically acquire processing lock
    material = await db["materials"].find_one({
        "_id": _oid(material_id),
        "project_id": project_id,
        "user_id": user_id,
    })

    if not material:
        logger.error(f"Background task aborted: Material {material_id} not found.")
        return

    current_status = material.get("status")
    if current_status == MaterialStatus.PROCESSING.value:
        logger.warning(f"Material {material_id} is already being processed — skipping duplicate execution.")
        return

    # Update material and job status to PROCESSING
    now = datetime.now(timezone.utc)
    attempts = material.get("processing_attempts", 0) + 1

    await db["materials"].update_one(
        {"_id": _oid(material_id)},
        {
            "$set": {
                "status": MaterialStatus.PROCESSING.value,
                "processing_attempts": attempts,
                "updated_at": now,
                "error_message": None,
            }
        },
    )

    await db["background_jobs"].update_one(
        {"material_id": material_id, "project_id": project_id},
        {
            "$set": {
                "status": JobStatus.PROCESSING.value,
                "attempts": attempts,
                "started_at": now,
                "updated_at": now,
                "last_error": None,
            }
        },
    )

    logger.info(f"Processing started for material {material_id} (Attempt {attempts}/{MAX_RETRY_ATTEMPTS})")

    # Event publishing: MATERIAL_PROCESSING_STARTED
    try:
        from app.services.event_publisher import publish_event
        await publish_event(
            project_id=project_id,
            user_id=user_id,
            event_type="MATERIAL_PROCESSING_STARTED",
            payload={
                "material_id": material_id,
                "attempt": attempts,
                "max_attempts": MAX_RETRY_ATTEMPTS,
            },
            source_component="material_service",
        )
    except Exception as ev_err:
        logger.warning(f"Failed to publish MATERIAL_PROCESSING_STARTED event: {ev_err}")

    try:
        file_path = material["file_path"]
        filename = material["filename"]

        # 1. Page-by-page text extraction
        pages = pdf_service.extract_pdf_pages(file_path)
        logger.info(f"PDF extraction complete for {material_id}: {len(pages)} pages extracted.")

        # 2. Page-aware text chunking
        chunks = pdf_service.chunk_pages(pages, chunk_size=500, overlap=50)
        logger.info(f"Chunking complete for {material_id}: {len(chunks)} chunks created.")

        # 3. Embedding generation
        chunk_texts = [c["chunk_text"] for c in chunks]
        embeddings = await embedding_service.generate_embeddings(chunk_texts)

        # 4. Idempotency: Clean up any existing chunks for this material before re-inserting
        del_res = await db["chunks"].delete_many({"material_id": material_id})
        if del_res.deleted_count > 0:
            logger.info(f"Cleared {del_res.deleted_count} previous chunks for material {material_id}")

        # 5. Insert chunks into database
        chunk_docs = []
        chunk_now = datetime.now(timezone.utc)
        for i, c in enumerate(chunks):
            chunk_docs.append({
                "project_id": project_id,
                "material_id": material_id,
                "filename": filename,
                "page_number": c["page_number"],
                "chunk_index": c["chunk_index"],
                "chunk_text": c["chunk_text"],
                "embedding": embeddings[i] if i < len(embeddings) else [],
                "created_at": chunk_now,
            })

        if chunk_docs:
            await db["chunks"].insert_many(chunk_docs)

        # 6. Mark status as READY and job as COMPLETED
        processed_at = datetime.now(timezone.utc)
        await db["materials"].update_one(
            {"_id": _oid(material_id)},
            {
                "$set": {
                    "status": MaterialStatus.READY.value,
                    "updated_at": processed_at,
                    "processed_at": processed_at,
                    "error_message": None,
                }
            },
        )

        await db["background_jobs"].update_one(
            {"material_id": material_id, "project_id": project_id},
            {
                "$set": {
                    "status": JobStatus.COMPLETED.value,
                    "completed_at": processed_at,
                    "updated_at": processed_at,
                }
            },
        )

        logger.info(f"Material processing successfully completed for {material_id} ({len(chunk_docs)} chunks stored).")

        # Event publishing: MATERIAL_PROCESSED
        from app.services.event_publisher import publish_event
        await publish_event(
            project_id=project_id,
            user_id=user_id,
            event_type="MATERIAL_PROCESSED",
            payload={
                "material_id": material_id,
                "filename": filename,
                "chunks_count": len(chunk_docs),
                "status": "READY",
            },
            source_component="material_service",
        )

        # 7. Trigger Phase 4 Knowledge Extraction for Project Knowledge Base
        try:
            from app.services import knowledge_extraction_service
            await knowledge_extraction_service.extract_project_knowledge(project_id, user_id)
            logger.info(f"Triggered knowledge extraction for project {project_id} after material {material_id} ready.")
        except Exception as k_exc:
            logger.warning(f"Knowledge extraction warning for project {project_id}: {k_exc}")


    except Exception as exc:
        logger.error(f"Material processing failed for {material_id}: {exc}", exc_info=True)
        err_msg = str(exc)
        failed_at = datetime.now(timezone.utc)

        await db["materials"].update_one(
            {"_id": _oid(material_id)},
            {
                "$set": {
                    "status": MaterialStatus.FAILED.value,
                    "updated_at": failed_at,
                    "error_message": err_msg,
                }
            },
        )

        await db["background_jobs"].update_one(
            {"material_id": material_id, "project_id": project_id},
            {
                "$set": {
                    "status": JobStatus.FAILED.value,
                    "updated_at": failed_at,
                    "last_error": err_msg,
                }
            },
        )

        # Event publishing: MATERIAL_PROCESSING_FAILED
        try:
            from app.services.event_publisher import publish_event
            await publish_event(
                project_id=project_id,
                user_id=user_id,
                event_type="MATERIAL_PROCESSING_FAILED",
                payload={
                    "material_id": material_id,
                    "error": err_msg,
                    "attempts": attempts,
                },
                source_component="material_service",
            )
        except Exception as ev_err:
            logger.warning(f"Failed to publish MATERIAL_PROCESSING_FAILED event: {ev_err}")


async def get_materials_by_project(project_id: str, user_id: str) -> List[MaterialResponse]:
    """Return all materials belonging to project_id owned by user_id."""
    await get_project(project_id, user_id)
    db = get_database()
    cursor = db["materials"].find({"project_id": project_id, "user_id": user_id}).sort("created_at", -1)
    return [_doc_to_material_response(doc) async for doc in cursor]


async def get_material(material_id: str, user_id: str) -> MaterialResponse:
    """Return a single material by ID after ownership validation."""
    db = get_database()
    doc = await db["materials"].find_one({"_id": _oid(material_id), "user_id": user_id})
    if not doc:
        raise ValueError("not_found")
    return _doc_to_material_response(doc)


async def retry_material(
    material_id: str,
    user_id: str,
    background_tasks: BackgroundTasks,
) -> MaterialRetryResponse:
    """
    Retry a failed material.
    Verifies ownership, status == FAILED, max retry limits, and queues background processing task.
    """
    db = get_database()
    material = await db["materials"].find_one({"_id": _oid(material_id), "user_id": user_id})
    if not material:
        raise ValueError("not_found")

    if material.get("status") not in (MaterialStatus.FAILED.value, MaterialStatus.QUEUED.value):
        raise ValueError("Only failed or queued materials can be retried.")

    attempts = material.get("processing_attempts", 0)
    if attempts >= MAX_RETRY_ATTEMPTS:
        raise ValueError(f"Maximum processing retries reached ({attempts}/{MAX_RETRY_ATTEMPTS}).")

    now = datetime.now(timezone.utc)
    await db["materials"].update_one(
        {"_id": _oid(material_id)},
        {
            "$set": {
                "status": MaterialStatus.QUEUED.value,
                "error_message": None,
                "updated_at": now,
            }
        },
    )

    project_id = str(material["project_id"])
    await db["background_jobs"].update_one(
        {"material_id": material_id, "project_id": project_id},
        {
            "$set": {
                "status": JobStatus.QUEUED.value,
                "last_error": None,
                "updated_at": now,
            }
        },
    )

    background_tasks.add_task(process_material_task, material_id, project_id, user_id)
    logger.info(f"Retry requested for material {material_id} by user {user_id}")

    return MaterialRetryResponse(
        material_id=material_id,
        status=MaterialStatus.QUEUED.value,
        processing_attempts=attempts,
        message="Material queued for retry processing.",
    )


async def get_material_chunks(material_id: str, user_id: str) -> List[ChunkResponse]:
    """Return all processed chunks for a material after ownership validation."""
    await get_material(material_id, user_id)
    db = get_database()
    cursor = db["chunks"].find({"material_id": material_id}).sort("chunk_index", 1)
    return [_doc_to_chunk_response(doc) async for doc in cursor]


async def delete_material(material_id: str, user_id: str) -> None:
    """
    Delete a Material, its physical file on disk, all associated Chunks, and BackgroundJob tracking records.
    """
    db = get_database()
    material = await db["materials"].find_one({"_id": _oid(material_id), "user_id": user_id})
    if not material:
        raise ValueError("not_found")

    # 1. Delete associated chunks from DB
    del_chunks = await db["chunks"].delete_many({"material_id": material_id})
    logger.info(f"Deleted {del_chunks.deleted_count} chunks for material {material_id}")

    # 2. Delete background jobs tracking records
    del_jobs = await db["background_jobs"].delete_many({"material_id": material_id})
    logger.info(f"Deleted {del_jobs.deleted_count} background_job records for material {material_id}")

    # 3. Delete sections associated with this material
    del_sections = await db["sections"].delete_many({"material_id": material_id})
    logger.info(f"Deleted {del_sections.deleted_count} section records for material {material_id}")

    # 4. Remove file from storage disk
    file_path = material.get("file_path")
    if file_path and os.path.exists(file_path):
        try:
            os.remove(file_path)
            logger.info(f"Deleted file '{file_path}' from disk")
        except Exception as exc:
            logger.warning(f"Failed to remove file '{file_path}': {exc}")

    # 5. Delete Material document
    await db["materials"].delete_one({"_id": _oid(material_id), "user_id": user_id})
    logger.info(f"Material {material_id} deleted by user {user_id}")


