"""
Retrieval Service (RAG Semantic Search).

Performs project-scoped vector similarity search over KnowledgeChunks stored in MongoDB.

Key Features:
- User authorization & project ownership enforcement
- Vector embedding generation using the matching Phase 3 embedding provider
- Strict project data isolation (queries ONLY return chunks matching project_id)
- Top-K similarity search with configurable score thresholding
- Full citation metadata preservation (material_id, filename, page_number, score)
- Clean zero-results handling for unindexed or empty projects
"""
import time
import math
import logging
from typing import List, Dict, Any, Optional

from app.db.database import get_database
from app.schemas.knowledge import SearchResponse, SearchResultItem
from app.services import embedding_service
from app.services.project_service import get_project

logger = logging.getLogger(__name__)

DEFAULT_MIN_RELEVANCE_SCORE = 0.05


def _cosine_similarity(vec_a: List[float], vec_b: List[float]) -> float:
    """Calculate cosine similarity between two float vectors."""
    if not vec_a or not vec_b or len(vec_a) != len(vec_b):
        return 0.0

    dot_product = sum(a * b for a, b in zip(vec_a, vec_b))
    norm_a = math.sqrt(sum(a * a for a in vec_a))
    norm_b = math.sqrt(sum(b * b for b in vec_b))

    if norm_a == 0.0 or norm_b == 0.0:
        return 0.0

    return round(dot_product / (norm_a * norm_b), 4)


def _text_keyword_overlap_score(query: str, chunk_text: str) -> float:
    """Calculate keyword overlap bonus between query and chunk text."""
    query_terms = set(re_term for re_term in query.lower().split() if len(re_term) > 2)
    if not query_terms:
        return 0.0

    chunk_lower = chunk_text.lower()
    matches = sum(1 for term in query_terms if term in chunk_lower)
    return round(matches / len(query_terms) * 0.2, 4)


async def search_project_knowledge(
    project_id: str,
    user_id: Optional[str] = None,
    query: str = "",
    top_k: int = 5,
    min_score: float = DEFAULT_MIN_RELEVANCE_SCORE,
) -> SearchResponse:
    """
    Perform semantic RAG search inside a project's knowledge base.

    Args:
        project_id: Target project ID
        user_id: Authenticated user ID (derived from JWT, optional for internal queries)
        query: User search query string
        top_k: Maximum number of relevant chunks to return (default 5)
        min_score: Minimum similarity score threshold

    Returns:
        SearchResponse containing ranked top-K chunk results with page & filename citations.
    """
    start_time = time.time()

    # 1. Enforce user authorization and project ownership if user_id is provided
    if user_id:
        await get_project(project_id, user_id)

    query = query.strip()
    if not query:
        return SearchResponse(query="", project_id=project_id, results=[], total_results=0)

    db = get_database()

    # 2. Strict Project Isolation: Retrieve chunks ONLY for project_id
    cursor = db["chunks"].find({"project_id": project_id})
    chunks = [doc async for doc in cursor]

    if not chunks:
        logger.info(f"RAG search on empty project {project_id} (0 chunks stored).")
        return SearchResponse(query=query, project_id=project_id, results=[], total_results=0)

    # 3. Generate query vector embedding using identical provider
    query_embeddings = await embedding_service.generate_embeddings([query])
    query_vector = query_embeddings[0] if query_embeddings else []

    # 4. Compute vector similarity + hybrid keyword relevance for each chunk
    scored_items: List[SearchResultItem] = []

    for chunk in chunks:
        chunk_vector = chunk.get("embedding", [])
        vec_sim = _cosine_similarity(query_vector, chunk_vector)
        kw_bonus = _text_keyword_overlap_score(query, chunk.get("chunk_text", ""))

        # Combine vector similarity and keyword overlap score
        final_score = round(min(1.0, vec_sim + kw_bonus), 4)

        if final_score >= min_score:
            scored_items.append(
                SearchResultItem(
                    chunk_id=str(chunk["_id"]),
                    material_id=str(chunk["material_id"]),
                    filename=chunk.get("filename", "document.pdf"),
                    page_number=chunk.get("page_number", 1),
                    chunk_text=chunk.get("chunk_text", ""),
                    score=final_score,
                )
            )

    # 5. Sort descending by relevance score
    scored_items.sort(key=lambda item: item.score, reverse=True)

    # 6. Take top-K results
    top_results = scored_items[:top_k]
    latency_ms = round((time.time() - start_time) * 1000, 2)

    logger.info(
        f"RAG Search completed for project {project_id}: "
        f"query='{query[:30]}...', top_k={top_k}, returned={len(top_results)}/{len(scored_items)} "
        f"results in {latency_ms}ms"
    )

    return SearchResponse(
        query=query,
        project_id=project_id,
        results=top_results,
        total_results=len(scored_items),
    )
