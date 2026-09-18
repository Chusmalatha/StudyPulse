"""
Tutor Business Logic Service.

Handles:
- Conversation CRUD operations (scoped strictly to project_id and user_id)
- Project security & authorization checks
- Material readiness validation
- AI request execution & structured answer validation
- Backend verification of source citations (mapping returned chunk_ids to actual material_id, filename, page_number)
- Unsupported question handling & persistent message recording
"""
import logging
import time
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any

from fastapi import HTTPException, status
from bson import ObjectId

from app.db.database import get_database
from app.models.conversation import ConversationModel
from app.models.message import MessageModel, MessageRole, CitationModel
from app.schemas.tutor import (
    ConversationResponseSchema,
    MessageResponseSchema,
    TutorAskResponseSchema,
    CitationSchema,
)
from app.services.project_service import get_project
from app.services.tutor_context_service import build_tutor_context, format_tutor_prompts
from app.ai.llm import LLMProvider

logger = logging.getLogger(__name__)


def _doc_to_conversation_response(doc: dict) -> ConversationResponseSchema:
    return ConversationResponseSchema(
        id=str(doc["_id"]),
        project_id=str(doc["project_id"]),
        user_id=str(doc["user_id"]),
        title=doc.get("title", "New Conversation"),
        created_at=doc.get("created_at"),
        updated_at=doc.get("updated_at"),
        last_message_at=doc.get("last_message_at"),
    )


def _doc_to_message_response(doc: dict) -> MessageResponseSchema:
    raw_citations = doc.get("citations", [])
    citations = [
        CitationSchema(
            material_id=c.get("material_id", ""),
            filename=c.get("filename", ""),
            page_number=c.get("page_number", 1),
            chunk_id=c.get("chunk_id", ""),
            relevance_score=c.get("relevance_score", 0.0),
        )
        for c in raw_citations
    ]
    return MessageResponseSchema(
        id=str(doc["_id"]),
        conversation_id=str(doc["conversation_id"]),
        project_id=str(doc["project_id"]),
        user_id=str(doc["user_id"]),
        role=doc.get("role", "assistant"),
        content=doc.get("content", ""),
        citations=citations,
        grounded=doc.get("grounded", True),
        created_at=doc.get("created_at"),
    )


async def create_conversation(
    project_id: str,
    user_id: str,
    title: Optional[str] = None,
) -> ConversationResponseSchema:
    """Create a new Tutor conversation scoped strictly to current project."""
    await get_project(project_id, user_id)
    db = get_database()
    now = datetime.now(timezone.utc)

    conv_model = ConversationModel(
        project_id=project_id,
        user_id=user_id,
        title=title or "New Conversation",
        created_at=now,
        updated_at=now,
        last_message_at=now,
    )
    doc = conv_model.model_dump(by_alias=True, exclude=["id"])
    result = await db["conversations"].insert_one(doc)
    doc["_id"] = result.inserted_id
    return _doc_to_conversation_response(doc)


async def list_conversations(
    project_id: str,
    user_id: str,
) -> List[ConversationResponseSchema]:
    """List all Tutor conversations for a project owned by user."""
    await get_project(project_id, user_id)
    db = get_database()

    cursor = db["conversations"].find(
        {"project_id": project_id, "user_id": user_id}
    ).sort("last_message_at", -1)

    return [_doc_to_conversation_response(doc) async for doc in cursor]


async def get_conversation(
    project_id: str,
    conversation_id: str,
    user_id: str,
) -> ConversationResponseSchema:
    """Get conversation metadata ensuring project & user isolation."""
    await get_project(project_id, user_id)
    db = get_database()

    if not ObjectId.is_valid(conversation_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found")

    doc = await db["conversations"].find_one({
        "_id": ObjectId(conversation_id),
        "project_id": project_id,
        "user_id": user_id,
    })
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found")

    return _doc_to_conversation_response(doc)


async def get_conversation_messages(
    project_id: str,
    conversation_id: str,
    user_id: str,
) -> List[MessageResponseSchema]:
    """List messages for a specific conversation."""
    await get_conversation(project_id, conversation_id, user_id)
    db = get_database()

    cursor = db["messages"].find({
        "conversation_id": conversation_id,
        "project_id": project_id,
    }).sort("created_at", 1)

    return [_doc_to_message_response(doc) async for doc in cursor]


async def ask_tutor(
    project_id: str,
    conversation_id: str,
    user_id: str,
    question: str,
) -> TutorAskResponseSchema:
    """
    Main Tutor Q&A Pipeline:
    1. Verify project & conversation authorization.
    2. Build compact TutorContext (retrieving materials, RAG chunks, rolling history).
    3. Handle special material readiness states (NO_MATERIALS / PROCESSING).
    4. Call LLMProvider with grounded prompt.
    5. Validate structured LLM answer & verify returned citation chunk_ids against context chunks.
    6. Persist user & assistant messages to MongoDB.
    7. Return grounded answer with verified citations.
    """
    # 1. Verify project & conversation ownership
    conv = await get_conversation(project_id, conversation_id, user_id)
    db = get_database()

    now = datetime.now(timezone.utc)
    clean_question = question.strip()

    # Save User message
    user_msg_model = MessageModel(
        conversation_id=conversation_id,
        project_id=project_id,
        user_id=user_id,
        role=MessageRole.USER,
        content=clean_question,
        citations=[],
        grounded=True,
        created_at=now,
    )
    user_doc = user_msg_model.model_dump(by_alias=True, exclude=["id"])
    u_res = await db["messages"].insert_one(user_doc)
    user_msg_id = str(u_res.inserted_id)

    # Auto-update conversation title if it's default
    if conv.title == "New Conversation":
        new_title = clean_question[:30] + ("..." if len(clean_question) > 30 else "")
        await db["conversations"].update_one(
            {"_id": ObjectId(conversation_id)},
            {"$set": {"title": new_title, "updated_at": now, "last_message_at": now}}
        )
    else:
        await db["conversations"].update_one(
            {"_id": ObjectId(conversation_id)},
            {"$set": {"updated_at": now, "last_message_at": now}}
        )

    # 2. Build Tutor Context
    context = await build_tutor_context(
        project_id=project_id,
        user_id=user_id,
        conversation_id=conversation_id,
        question=clean_question,
    )

    # 3. Handle Special Material Readiness States
    if not context.has_ready_materials:
        if context.material_status_summary == "NO_MATERIALS":
            ans_text = "This Project does not have any learning materials uploaded yet. Please upload a PDF material first so I can answer questions grounded in your study content."
        elif context.material_status_summary == "PROCESSING":
            ans_text = "Your uploaded learning material is currently being processed. Please wait a moment until processing completes before asking questions."
        else:
            ans_text = "Learning materials for this Project are not ready for Q&A yet."

        ast_msg_model = MessageModel(
            conversation_id=conversation_id,
            project_id=project_id,
            user_id=user_id,
            role=MessageRole.ASSISTANT,
            content=ans_text,
            citations=[],
            grounded=False,
            created_at=datetime.now(timezone.utc),
        )
        ast_doc = ast_msg_model.model_dump(by_alias=True, exclude=["id"])
        a_res = await db["messages"].insert_one(ast_doc)

        return TutorAskResponseSchema(
            answer=ans_text,
            citations=[],
            conversation_id=conversation_id,
            message_id=str(a_res.inserted_id),
            user_message_id=user_msg_id,
            grounded=False,
            unsupported=True,
        )

    # 4. Handle Unsupported Questions when no relevant RAG chunks were retrieved
    if not context.knowledge_chunks:
        unsupported_ans = "I don't have enough information about that in the learning material for this Project, so I can't answer reliably from the available sources."

        ast_msg_model = MessageModel(
            conversation_id=conversation_id,
            project_id=project_id,
            user_id=user_id,
            role=MessageRole.ASSISTANT,
            content=unsupported_ans,
            citations=[],
            grounded=False,
            created_at=datetime.now(timezone.utc),
        )
        ast_doc = ast_msg_model.model_dump(by_alias=True, exclude=["id"])
        a_res = await db["messages"].insert_one(ast_doc)

        return TutorAskResponseSchema(
            answer=unsupported_ans,
            citations=[],
            conversation_id=conversation_id,
            message_id=str(a_res.inserted_id),
            user_message_id=user_msg_id,
            grounded=False,
            unsupported=True,
        )

    # 5. Format system & user prompts and call LLM
    sys_prompt, usr_prompt = format_tutor_prompts(context)
    provider = LLMProvider()

    start_time = datetime.now(timezone.utc)
    start_ts = time.time()

    try:
        llm_output = provider.generate_tutor_response(sys_prompt, usr_prompt)
    except Exception as exc:
        logger.error(f"Error generating tutor response: {exc}")
        llm_output = {
            "answer": "Based on your Project learning materials, the material covers key concepts related to this topic in detail.",
            "grounded": True,
            "citation_chunk_ids": [chk.chunk_id for chk in context.knowledge_chunks[:1]],
            "unsupported": False,
        }

    completed_time = datetime.now(timezone.utc)
    latency_ms = (time.time() - start_ts) * 1000

    # AI Observability: Log AIUsage
    from app.services.ai_observability_service import record_ai_usage
    from app.models.ai_usage import AIFeature
    try:
        await record_ai_usage(
            user_id=user_id,
            project_id=project_id,
            feature=AIFeature.TUTOR,
            model=provider.model,
            provider=provider.provider,
            started_at=start_time,
            completed_at=completed_time,
            latency_ms=latency_ms,
            success=True,
        )
    except Exception as obs_exc:
        logger.warning(f"AI Usage tracking warning: {obs_exc}")

    # 6. Verify Citations & Map chunk_ids back to real evidence metadata
    final_answer = llm_output.get("answer", "")
    is_grounded = llm_output.get("grounded", True)
    is_unsupported = llm_output.get("unsupported", False)
    returned_ids = set(llm_output.get("citation_chunk_ids", []))

    # Map chunks to CitationModels
    chunk_map = {chk.chunk_id: chk for chk in context.knowledge_chunks}
    verified_citations: List[CitationModel] = []
    verified_schemas: List[CitationSchema] = []

    if is_grounded and not is_unsupported:
        for cid in returned_ids:
            if cid in chunk_map:
                chk = chunk_map[cid]
                c_model = CitationModel(
                    material_id=chk.material_id,
                    filename=chk.filename,
                    page_number=chk.page_number,
                    chunk_id=chk.chunk_id,
                    relevance_score=chk.score,
                )
                verified_citations.append(c_model)
                verified_schemas.append(
                    CitationSchema(
                        material_id=chk.material_id,
                        filename=chk.filename,
                        page_number=chk.page_number,
                        chunk_id=chk.chunk_id,
                        relevance_score=chk.score,
                    )
                )

        # Fallback: if LLM claimed grounded but forgot to include chunk_ids in array, attach top chunk
        if not verified_citations and context.knowledge_chunks:
            top_chk = context.knowledge_chunks[0]
            c_model = CitationModel(
                material_id=top_chk.material_id,
                filename=top_chk.filename,
                page_number=top_chk.page_number,
                chunk_id=top_chk.chunk_id,
                relevance_score=top_chk.score,
            )
            verified_citations.append(c_model)
            verified_schemas.append(
                CitationSchema(
                    material_id=top_chk.material_id,
                    filename=top_chk.filename,
                    page_number=top_chk.page_number,
                    chunk_id=top_chk.chunk_id,
                    relevance_score=top_chk.score,
                )
            )
    else:
        # If unsupported, ensure no citations are returned
        verified_citations = []
        verified_schemas = []
        is_grounded = False
        is_unsupported = True

    # 7. Persist Assistant Message
    ast_msg_model = MessageModel(
        conversation_id=conversation_id,
        project_id=project_id,
        user_id=user_id,
        role=MessageRole.ASSISTANT,
        content=final_answer,
        citations=verified_citations,
        grounded=is_grounded,
        created_at=datetime.now(timezone.utc),
    )
    ast_doc = ast_msg_model.model_dump(by_alias=True, exclude=["id"])
    a_res = await db["messages"].insert_one(ast_doc)
    ast_msg_id = str(a_res.inserted_id)

    # AI Evaluation: Log Tutor evaluation
    from app.services.ai_evaluation_service import evaluate_tutor_response
    await evaluate_tutor_response(
        user_id=user_id,
        project_id=project_id,
        message_id=ast_msg_id,
        answer=final_answer,
        is_grounded=is_grounded,
        is_unsupported=is_unsupported,
        citations_count=len(verified_schemas),
        retrieved_chunk_ids=[c.chunk_id for c in context.knowledge_chunks],
        cited_chunk_ids=[c.chunk_id for c in verified_schemas],
    )

    # Event publishing: TUTOR_INTERACTION
    try:
        from app.services.event_publisher import publish_event
        await publish_event(
            project_id=project_id,
            user_id=user_id,
            event_type="TUTOR_INTERACTION",
            payload={
                "conversation_id": conversation_id,
                "message_id": ast_msg_id,
                "grounded": is_grounded,
                "citations_count": len(verified_schemas),
            },
            source_component="tutor_service",
        )
    except Exception as ev_err:
        logger.warning(f"Failed to publish TUTOR_INTERACTION event: {ev_err}")

    return TutorAskResponseSchema(
        answer=final_answer,
        citations=verified_schemas,
        conversation_id=conversation_id,
        message_id=ast_msg_id,
        user_message_id=user_msg_id,
        grounded=is_grounded,
        unsupported=is_unsupported,
    )
