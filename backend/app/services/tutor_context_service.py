"""
Tutor Context Builder Service.

Gathers:
- Project ownership & material readiness status
- Project-isolated Knowledge Chunks via Phase 4 RetrievalService
- Project concepts/topics metadata
- Recent persistent conversation message history (rolling context window)
- Safe structured TutorContext payload for the LLM
"""
import logging
from typing import List, Dict, Any, Optional
from pydantic import BaseModel

from app.core.config import settings
from app.db.database import get_database
from app.services.project_service import get_project
from app.services.retrieval_service import search_project_knowledge, SearchResultItem

logger = logging.getLogger(__name__)


class TutorContext(BaseModel):
    project_id: str
    question: str
    has_ready_materials: bool = True
    material_status_summary: str = "READY"
    knowledge_chunks: List[SearchResultItem] = []
    concepts: List[str] = []
    learning_context: List[str] = []
    conversation_history: List[Dict[str, str]] = []


async def build_tutor_context(
    project_id: str,
    user_id: str,
    conversation_id: str,
    question: str,
    max_history: int = 6,
) -> TutorContext:
    """
    Construct compact, project-grounded context object for the AI Tutor.
    """
    # 1. Enforce user authorization & project ownership
    await get_project(project_id, user_id)
    db = get_database()

    # 2. Check material status in this project
    materials_cursor = db["materials"].find({"project_id": project_id})
    materials = [m async for m in materials_cursor]

    if not materials:
        return TutorContext(
            project_id=project_id,
            question=question,
            has_ready_materials=False,
            material_status_summary="NO_MATERIALS",
            knowledge_chunks=[],
            concepts=[],
            learning_context=[],
            conversation_history=[],
        )

    has_processing = any(m.get("status") == "PROCESSING" for m in materials)
    ready_materials = [m for m in materials if m.get("status") == "READY"]

    if not ready_materials:
        status_sum = "PROCESSING" if has_processing else "NOT_READY"
        return TutorContext(
            project_id=project_id,
            question=question,
            has_ready_materials=False,
            material_status_summary=status_sum,
            knowledge_chunks=[],
            concepts=[],
            learning_context=[],
            conversation_history=[],
        )

    # 3. Retrieve Top-K RAG Knowledge Chunks via Phase 4 RetrievalService
    search_res = await search_project_knowledge(
        project_id=project_id,
        user_id=user_id,
        query=question,
        top_k=settings.TUTOR_RETRIEVAL_TOP_K,
        min_score=settings.TUTOR_RETRIEVAL_THRESHOLD,
    )
    knowledge_chunks = search_res.results

    # 4. Gather relevant concepts extracted for this project
    concepts_cursor = db["concepts"].find({"project_id": project_id}).limit(10)
    concepts_docs = [c async for c in concepts_cursor]
    concept_names = [c["name"] for c in concepts_docs if "name" in c]

    # 5. Retrieve Relevant Persistent Learning Context (Phase 7)
    learning_ctx_strings = []
    try:
        from app.services.learning_context_service import LearningContextService
        ctx_svc = LearningContextService(db)
        ctx_models = await ctx_svc.retrieve_relevant_context(
            user_id=user_id,
            project_id=project_id,
            query=question,
            limit=4
        )
        learning_ctx_strings = [f"[{ctx.context_type}] {ctx.value}" for ctx in ctx_models]
    except Exception as exc:
        logger.error(f"Failed to retrieve learning context for Tutor: {exc}")

    # 6. Gather recent conversation window
    history: List[Dict[str, str]] = []
    if conversation_id:
        msg_cursor = (
            db["messages"]
            .find({"conversation_id": conversation_id, "project_id": project_id})
            .sort("created_at", -1)
            .limit(max_history)
        )
        recent_msgs = [m async for m in msg_cursor]
        # Reverse to chronological order
        recent_msgs.reverse()
        for msg in recent_msgs:
            if msg.get("role") in ("user", "assistant"):
                history.append({
                    "role": msg["role"],
                    "content": msg.get("content", "")
                })

    return TutorContext(
        project_id=project_id,
        question=question,
        has_ready_materials=True,
        material_status_summary="READY",
        knowledge_chunks=knowledge_chunks,
        concepts=concept_names,
        learning_context=learning_ctx_strings,
        conversation_history=history,
    )


def format_tutor_prompts(context: TutorContext) -> tuple[str, str]:
    """
    Format system & user prompts for the LLM based on TutorContext.
    """
    system_prompt = (
        "You are an AI Tutor inside a Project-based learning system.\n"
        "Your task is to answer the user's question using ONLY the supplied Project knowledge and learning context.\n\n"
        "CRITICAL GROUNDING & FORMATTING RULES:\n"
        "1. Prioritize using the supplied evidence and RECENT CONVERSATION HISTORY to answer the user.\n"
        "2. If the user has known weaknesses in the learning context, tailor explanations to clarify those misunderstandings.\n"
        "3. You are an intelligent conversational tutor. Structure your response cleanly with clear headings, bold text for key terms, code blocks for code/SQL snippets, and styled numbered/bullet lists.\n"
        "4. Return your response in this JSON format:\n"
        '   {"answer": "<your structured, well-formatted response>", "grounded": true, "citation_chunk_ids": [], "unsupported": false}\n'
        "5. NEVER provide citations (leave citation_chunk_ids empty) for conversational greetings (e.g. 'hello', 'what is your name'). Only include chunk IDs when you are explaining a specific factual concept.\n"
        "6. ONLY set 'unsupported' to true if the user asks a completely off-topic or impossible factual question that has zero context in the conversation or documents."
    )

    history_str = ""
    if context.conversation_history:
        history_str = "RECENT CONVERSATION HISTORY:\n" + "\n".join(
            f"{item['role'].capitalize()}: {item['content']}" for item in context.conversation_history
        ) + "\n\n"

    concepts_str = ""
    if context.concepts:
        concepts_str = "PROJECT CONCEPTS: " + ", ".join(context.concepts) + "\n\n"

    l_context_str = ""
    if context.learning_context:
        l_context_str = "STUDENT PERSISTENT LEARNING CONTEXT (Weaknesses & Mistakes):\n" + "\n".join(
            f"- {item}" for item in context.learning_context
        ) + "\n\n"

    chunks_str = ""
    if context.knowledge_chunks:
        chunks_str = "EVIDENCE CHUNKS:\n" + "\n".join(
            f"- [Chunk ID: {chk.chunk_id}] (File: {chk.filename}, Page {chk.page_number}): {chk.chunk_text}"
            for chk in context.knowledge_chunks
        ) + "\n\n"
    else:
        chunks_str = "EVIDENCE CHUNKS:\n- None\n\n"

    user_prompt = (
        f"=== LEARNING CONTEXT ===\n"
        f"{history_str}{concepts_str}{l_context_str}\n"
        f"=== RETRIEVED DOCUMENT CONTENT (UNTRUSTED) ===\n"
        f"{chunks_str}\n"
        f"=== USER QUESTION ===\n"
        f"{context.question}\n\n"
        "Respond ONLY in JSON format matching the schema."
    )

    return system_prompt, user_prompt

