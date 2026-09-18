"""
Knowledge Extraction Service.

Parses processed document chunks from READY materials into structured Project Knowledge:
- Concepts (key learning concepts with grounded source pages and materials)
- Topics (broader subject themes with source pages)
- Sections (document section boundaries and page ranges)

Enforces:
- Structured Pydantic output validation before database persistence
- Project-level data isolation
- Deduplication across multiple extraction runs (updating existing concept source references instead of duplicating)
- Preserving existing chunks & materials if extraction encounters errors
"""
import re
import logging
from datetime import datetime, timezone
from typing import List, Dict, Any, Tuple

from app.db.database import get_database
from app.models.concept import ConceptModel
from app.models.topic import TopicModel
from app.models.section import SectionModel
from app.schemas.knowledge import (
    ConceptResponse,
    TopicResponse,
    SectionResponse,
    ProjectKnowledgeResponse,
)
from app.services.project_service import get_project

logger = logging.getLogger(__name__)


def _doc_to_concept_response(doc: dict) -> ConceptResponse:
    return ConceptResponse(
        id=str(doc["_id"]),
        project_id=str(doc["project_id"]),
        name=doc["name"],
        description=doc.get("description", ""),
        source_material_ids=doc.get("source_material_ids", []),
        source_pages=sorted(list(set(doc.get("source_pages", [])))),
        created_at=doc.get("created_at"),
    )


def _doc_to_topic_response(doc: dict) -> TopicResponse:
    return TopicResponse(
        id=str(doc["_id"]),
        project_id=str(doc["project_id"]),
        name=doc["name"],
        description=doc.get("description", ""),
        source_material_ids=doc.get("source_material_ids", []),
        source_pages=sorted(list(set(doc.get("source_pages", [])))),
        created_at=doc.get("created_at"),
    )


def _doc_to_section_response(doc: dict) -> SectionResponse:
    return SectionResponse(
        id=str(doc["_id"]),
        project_id=str(doc["project_id"]),
        material_id=str(doc["material_id"]),
        title=doc["title"],
        page_start=doc["page_start"],
        page_end=doc["page_end"],
        section_order=doc.get("section_order", 0),
        created_at=doc.get("created_at"),
    )


def _extract_knowledge_from_chunk_texts(
    chunks: List[dict]
) -> Tuple[List[dict], List[dict], List[dict]]:
    """
    Extract structured concepts, topics, and sections from text chunks.
    Preserves exact material_id and page_number metadata.
    Returns: (raw_concepts, raw_topics, raw_sections)
    """
    concepts_map: Dict[str, dict] = {}
    topics_map: Dict[str, dict] = {}
    sections_list: List[dict] = []

    # Common technical concept patterns & headings
    header_regex = re.compile(r'^(?:chapter|section|\d+\.|\b)(?:\s*)([A-Z][A-Za-z0-9\s\-\:\,]{3,60})', re.IGNORECASE)

    for chunk in chunks:
        mat_id = chunk["material_id"]
        page_num = chunk.get("page_number", 1)
        text = chunk.get("chunk_text", "").strip()
        if not text:
            continue

        # 1. Section detection from chunk beginnings
        lines = text.split("\n")
        first_line = lines[0].strip()
        if len(first_line) > 3 and len(first_line) < 80:
            if first_line.isupper() or any(kw in first_line.lower() for kw in ["introduction", "overview", "methods", "results", "discussion", "conclusion", "chapter", "section"]):
                clean_title = re.sub(r'^[0-9\.\s\#\-]+', '', first_line).strip()
                if clean_title:
                    sections_list.append({
                        "material_id": mat_id,
                        "title": clean_title,
                        "page_start": page_num,
                        "page_end": page_num,
                    })

        # 2. Extract technical terms / concepts from text
        # Skipped here, will be handled after the chunks loop using LLM or Regex.

        # 3. Categorize into broad topics
        lower_text = text.lower()
        topic_keywords = {
            "Machine Learning & AI": ["machine learning", "neural network", "deep learning", "artificial intelligence", "model", "training"],
            "Data & Mathematics": ["dataset", "algorithm", "statistics", "matrix", "vector", "probability", "equation"],
            "Optimization & Evaluation": ["gradient", "loss", "accuracy", "optimization", "regularization", "overfitting", "validation"],
            "Software & Architecture": ["system", "architecture", "code", "implementation", "pipeline", "execution", "database"],
        }

        for topic_name, kws in topic_keywords.items():
            if any(kw in lower_text for kw in kws):
                t_key = topic_name.lower()
                if t_key not in topics_map:
                    topics_map[t_key] = {
                        "name": topic_name,
                        "description": f"Broad learning domain covering keywords extracted from page {page_num}.",
                        "source_material_ids": [mat_id],
                        "source_pages": [page_num],
                    }
                else:
                    if mat_id not in topics_map[t_key]["source_material_ids"]:
                        topics_map[t_key]["source_material_ids"].append(mat_id)
                    if page_num not in topics_map[t_key]["source_pages"]:
                        topics_map[t_key]["source_pages"].append(page_num)

    # Perform concept AND topic extraction using LLM on FULL PDF content
    extracted_concepts = []
    llm_topics: List[dict] = []
    try:
        from app.ai.llm import LLMProvider
        provider = LLMProvider()

        # Use as much PDF content as possible (up to 12,000 chars) for accurate extraction
        full_text = "\n".join([c.get("chunk_text", "") for c in chunks])[:12000]

        sys_prompt = (
            "You are an expert educator analyzing an uploaded PDF document.\n"
            "Your task:\n"
            "1. Extract 8 to 12 CORE LEARNING CONCEPTS explicitly discussed in this document.\n"
            "   - Concepts MUST appear directly in the text — do NOT invent general knowledge.\n"
            "   - Concept names should be short technical terms (1 to 4 words).\n"
            "   - For each concept, write a 1-sentence description based ONLY on what the document says about it.\n"
            "2. Extract 2 to 4 BROAD TOPICS that group these concepts.\n"
            "   - Topics MUST be grounded in this document's content.\n"
            "Return ONLY valid JSON with this exact structure:\n"
            '{"concepts": [{"name": "Concept Name", "description": "One sentence from the document about it."},...], '
            '"topics": ["Topic One", "Topic Two",...]}'
        )
        user_prompt = (
            f"DOCUMENT TEXT (from uploaded PDF):\n{full_text}\n\n"
            "Extract concepts with descriptions and topics from THIS document only."
        )
        raw_json = provider.generate_json_completion(sys_prompt, user_prompt)
        raw_concept_items = raw_json.get("concepts", [])
        topic_names = raw_json.get("topics", [])

        # Support both list-of-objects [{name, description}] and legacy list-of-strings ["name"]
        concept_items = []
        for item in raw_concept_items:
            if isinstance(item, dict):
                concept_items.append((item.get("name", ""), item.get("description", "")))
            elif isinstance(item, str):
                concept_items.append((item, ""))

        if not concept_items:
            raise ValueError("Invalid LLM output — no concepts returned")

        for name, description in concept_items:
            if not isinstance(name, str) or len(name) < 3:
                continue

            # Ground concept to its actual page(s) and material(s) in the PDF
            found_page = 1
            found_mat = chunks[0]["material_id"] if chunks else ""
            found_pages: List[int] = []
            found_mats: List[str] = []
            for c in chunks:
                if name.lower() in c.get("chunk_text", "").lower():
                    pg = c.get("page_number", 1)
                    mid = c["material_id"]
                    if pg not in found_pages:
                        found_pages.append(pg)
                    if mid not in found_mats:
                        found_mats.append(mid)

            # Use LLM description if provided, else generate a fallback
            concept_desc = description.strip() if description.strip() else f"{name} — key concept from your uploaded PDF."

            extracted_concepts.append({
                "name": name,
                "description": concept_desc,
                "source_material_ids": found_mats if found_mats else [found_mat],
                "source_pages": sorted(found_pages) if found_pages else [found_page],
            })

        # Build PDF-grounded topics from LLM output
        if isinstance(topic_names, list):
            for tname in topic_names:
                if not isinstance(tname, str) or len(tname) < 3:
                    continue
                t_pages: List[int] = []
                t_mats: List[str] = []
                for c in chunks:
                    if tname.lower() in c.get("chunk_text", "").lower():
                        pg = c.get("page_number", 1)
                        mid = c["material_id"]
                        if pg not in t_pages:
                            t_pages.append(pg)
                        if mid not in t_mats:
                            t_mats.append(mid)
                llm_topics.append({
                    "name": tname,
                    "description": f"Topic extracted from uploaded PDF.",
                    "source_material_ids": t_mats if t_mats else ([chunks[0]["material_id"]] if chunks else []),
                    "source_pages": sorted(t_pages) if t_pages else [1],
                })

    except Exception as e:
        logger.warning(f"LLM concept/topic extraction failed: {e}. Falling back to regex on PDF text.")
        import collections
        phrase_counter: collections.Counter = collections.Counter()
        phrase_to_pages: Dict[str, set] = collections.defaultdict(set)
        phrase_to_mats: Dict[str, set] = collections.defaultdict(set)

        # Regex fallback: only looks at actual chunk text from the PDF
        for chunk in chunks:
            text = chunk.get("chunk_text", "")
            phrases = re.findall(r'\b([A-Z][A-Za-z\-]+(?:\s+[A-Z][A-Za-z\-]+){0,2})\b', text)
            for p in phrases:
                if len(p.split()) >= 2:
                    phrase_counter[p] += 1
                    phrase_to_pages[p].add(chunk.get("page_number", 1))
                    phrase_to_mats[p].add(chunk["material_id"])

        for p, count in phrase_counter.most_common(12):
            extracted_concepts.append({
                "name": p,
                "description": "Core concept extracted from uploaded PDF.",
                "source_material_ids": list(phrase_to_mats[p]),
                "source_pages": sorted(list(phrase_to_pages[p])),
            })

    # Use LLM-extracted PDF-grounded topics if available, else fall back to keyword-matched ones
    extracted_topics = llm_topics if llm_topics else list(topics_map.values())
    
    # Consolidate sections with consecutive page ranges
    consolidated_sections = []
    seen_section_titles = set()
    for idx, sec in enumerate(sections_list):
        s_title = sec["title"].lower()
        if s_title not in seen_section_titles:
            seen_section_titles.add(s_title)
            sec["section_order"] = len(consolidated_sections) + 1
            consolidated_sections.append(sec)

    return extracted_concepts, extracted_topics, consolidated_sections


async def extract_project_knowledge(project_id: str, user_id: str) -> ProjectKnowledgeResponse:
    """
    Run Knowledge Extraction for a project.
    Reads chunks from all READY materials, extracts grounded concepts, topics, and sections,
    validates structured models, and updates DB with deduplication.
    """
    # 1. Validate project ownership
    await get_project(project_id, user_id)
    db = get_database()

    # 2. Fetch all chunks for this project
    cursor = db["chunks"].find({"project_id": project_id}).sort("chunk_index", 1)
    chunks = [doc async for doc in cursor]

    if not chunks:
        logger.info(f"No chunks found for project {project_id} — returning empty knowledge.")
        return ProjectKnowledgeResponse(project_id=project_id, concepts=[], topics=[], sections=[])

    # 3. Perform knowledge extraction logic
    raw_concepts, raw_topics, raw_sections = _extract_knowledge_from_chunk_texts(chunks)

    now = datetime.now(timezone.utc)

    # 4a. Clear stale concepts & topics from previous runs so only PDF-grounded data remains
    logger.info(f"Clearing existing concepts and topics for project {project_id} before re-extraction.")
    await db["concepts"].delete_many({"project_id": project_id})
    await db["topics"].delete_many({"project_id": project_id})

    # 4b. Insert fresh PDF-grounded Concepts
    for c_raw in raw_concepts:
        norm_name = c_raw["name"].strip().lower()
        existing = await db["concepts"].find_one({"project_id": project_id, "name": {"$regex": f"^{re.escape(c_raw['name'])}$", "$options": "i"}})
        
        if existing:
            # Merge source_material_ids and source_pages
            m_ids = list(set(existing.get("source_material_ids", []) + c_raw["source_material_ids"]))
            p_nums = sorted(list(set(existing.get("source_pages", []) + c_raw["source_pages"])))
            await db["concepts"].update_one(
                {"_id": existing["_id"]},
                {
                    "$set": {
                        "source_material_ids": m_ids,
                        "source_pages": p_nums,
                        "updated_at": now,
                    }
                }
            )
        else:
            # Validate model before insert
            c_model = ConceptModel(
                project_id=project_id,
                name=c_raw["name"],
                description=c_raw["description"],
                source_material_ids=c_raw["source_material_ids"],
                source_pages=c_raw["source_pages"],
                created_at=now,
                updated_at=now,
            )
            doc_dict = c_model.model_dump(by_alias=True, exclude=["id"])
            await db["concepts"].insert_one(doc_dict)

    # 5. Upsert & deduplicate Topics
    for t_raw in raw_topics:
        existing = await db["topics"].find_one({"project_id": project_id, "name": {"$regex": f"^{re.escape(t_raw['name'])}$", "$options": "i"}})
        if existing:
            m_ids = list(set(existing.get("source_material_ids", []) + t_raw["source_material_ids"]))
            p_nums = sorted(list(set(existing.get("source_pages", []) + t_raw["source_pages"])))
            await db["topics"].update_one(
                {"_id": existing["_id"]},
                {
                    "$set": {
                        "source_material_ids": m_ids,
                        "source_pages": p_nums,
                        "updated_at": now,
                    }
                }
            )
        else:
            t_model = TopicModel(
                project_id=project_id,
                name=t_raw["name"],
                description=t_raw["description"],
                source_material_ids=t_raw["source_material_ids"],
                source_pages=t_raw["source_pages"],
                created_at=now,
                updated_at=now,
            )
            doc_dict = t_model.model_dump(by_alias=True, exclude=["id"])
            await db["topics"].insert_one(doc_dict)

    # 6. Replace/update Sections for project
    for s_raw in raw_sections:
        existing = await db["sections"].find_one({"project_id": project_id, "material_id": s_raw["material_id"], "title": s_raw["title"]})
        if not existing:
            s_model = SectionModel(
                project_id=project_id,
                material_id=s_raw["material_id"],
                title=s_raw["title"],
                page_start=s_raw["page_start"],
                page_end=s_raw["page_end"],
                section_order=s_raw["section_order"],
                created_at=now,
                updated_at=now,
            )
            doc_dict = s_model.model_dump(by_alias=True, exclude=["id"])
            await db["sections"].insert_one(doc_dict)

    logger.info(f"Knowledge extraction complete for project {project_id}.")
    return await get_project_knowledge(project_id, user_id)


async def get_project_knowledge(project_id: str, user_id: str) -> ProjectKnowledgeResponse:
    """Return all extracted concepts, topics, and sections for a project."""
    await get_project(project_id, user_id)
    db = get_database()

    c_cursor = db["concepts"].find({"project_id": project_id}).sort("name", 1)
    t_cursor = db["topics"].find({"project_id": project_id}).sort("name", 1)
    s_cursor = db["sections"].find({"project_id": project_id}).sort("section_order", 1)

    concepts = [_doc_to_concept_response(doc) async for doc in c_cursor]
    topics = [_doc_to_topic_response(doc) async for doc in t_cursor]
    sections = [_doc_to_section_response(doc) async for doc in s_cursor]

    return ProjectKnowledgeResponse(
        project_id=project_id,
        concepts=concepts,
        topics=topics,
        sections=sections,
    )
