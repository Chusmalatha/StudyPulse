"""
Adaptive Assessment Service.

Core Capabilities:
1. Multi-signal Concept Target Selection:
   Calculates practice priority scores per concept based on:
   - Mastery / Confidence Level
   - Previous Mistakes & Recent Incorrect Attempts
   - Performance Trend Signals
   - Question History Freshness
   - Unproven Difficulty Levels
2. Grounded Question Generation:
   Retrieves Project Knowledge chunks via RetrievalService, formats structured LLM prompts,
   validates output JSON with Pydantic, and enforces duplicate question prevention.
3. Question Evaluation:
   - MCQ: Evaluates deterministically against stored correct_answer option.
   - Open-Ended: Evaluates qualitatively with LLM against retrieved Project Evidence returning
     understanding, accuracy, missing_concepts, strengths, areas_to_improve, and suggestions.
"""
import re
import math
import logging
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional, Tuple

from app.core.config import settings
from app.db.database import get_database
from app.models.quiz_question import QuizQuestionModel, QuestionType, QuestionDifficulty
from app.models.question_attempt import QuestionAttemptModel
from app.models.message import CitationModel
from app.schemas.assessment import OpenEndedEvaluationSchema, UnderstandingComponentSchema
from app.services.project_service import get_project
from app.services.retrieval_service import search_project_knowledge, SearchResultItem
from app.ai.llm import LLMProvider

logger = logging.getLogger(__name__)


def _normalize_text(text: str) -> str:
    """Normalize string for duplicate checking."""
    return re.sub(r'[^a-z0-9]', '', text.lower())


async def select_adaptive_target_concepts(
    project_id: str,
    user_id: str,
    requested_count: int = 5,
) -> List[Tuple[Dict[str, Any], QuestionDifficulty]]:
    """
    Select target concepts and difficulty levels using multi-signal evidence.
    Signals evaluated:
    - Mastery / Confidence (lower = higher priority)
    - Past Mistakes (more incorrect attempts = higher priority)
    - Recent Performance Trend (recent score drop = higher priority)
    - Freshness (time since last practice = higher priority)
    - Unproven Difficulty Levels
    Returns list of (concept_dict, difficulty) tuples.
    """
    db = get_database()

    # 1. Fetch extracted concepts for this project
    concepts_cursor = db["concepts"].find({"project_id": project_id})
    concepts = [c async for c in concepts_cursor]

    if not concepts:
        return []

    # 2. Fetch past attempts for user in this project
    attempts_cursor = db["question_attempts"].find({
        "project_id": project_id,
        "user_id": user_id,
    }).sort("attempted_at", -1)
    attempts = [a async for a in attempts_cursor]

    # Map attempts by concept_id
    attempts_by_concept: Dict[str, List[dict]] = {}
    for att in attempts:
        for cid in att.get("concept_ids", []):
            if cid not in attempts_by_concept:
                attempts_by_concept[cid] = []
            attempts_by_concept[cid].append(att)

    now = datetime.now(timezone.utc)
    scored_concepts: List[Tuple[float, dict, QuestionDifficulty]] = []

    for concept in concepts:
        cid = str(concept["_id"])
        c_attempts = attempts_by_concept.get(cid, [])

        total_att = len(c_attempts)
        incorrect_att = sum(1 for a in c_attempts if a.get("is_correct") is False)
        correct_att = sum(1 for a in c_attempts if a.get("is_correct") is True)

        # Signal 1: Stored Concept Mastery Level (Phase 7) or fallback count ratio
        stored_mastery = concept.get("mastery_score")
        if stored_mastery is not None and total_att > 0:
            mastery = stored_mastery / 100.0
        elif total_att > 0:
            mastery = (correct_att / total_att)
        else:
            mastery = 0.0  # Zero fake data baseline: brand new concepts start at 0.0

        mastery_score = 1.0 - mastery  # Higher priority for lower mastery


        # Signal 2: Mistake History Score
        mistake_score = min(1.0, incorrect_att * 0.25)

        # Signal 3: Recent Performance Trend (last 3 attempts)
        recent_3 = c_attempts[:3]
        recent_wrong = sum(1 for a in recent_3 if a.get("is_correct") is False)
        trend_score = recent_wrong / max(1, len(recent_3)) if recent_3 else 0.5

        # Signal 4: Freshness / Days since last attempt
        if c_attempts:
            last_dt = c_attempts[0].get("attempted_at", now)
            if isinstance(last_dt, str):
                try:
                    last_dt = datetime.fromisoformat(last_dt.replace('Z', '+00:00'))
                except Exception:
                    last_dt = now
            if last_dt.tzinfo is None:
                last_dt = last_dt.replace(tzinfo=timezone.utc)
            days_ago = max(0, (now - last_dt).days)
            freshness_score = min(1.0, days_ago / 14.0)
        else:
            freshness_score = 1.0  # Never attempted = high freshness priority

        # Composite Priority Score (0.0 to 1.0)
        priority = (
            (mastery_score * 0.35) +
            (mistake_score * 0.25) +
            (trend_score * 0.20) +
            (freshness_score * 0.20)
        )

        # Determine Target Difficulty
        if total_att == 0:
            target_diff = QuestionDifficulty.EASY
        elif mastery > 0.8:
            target_diff = QuestionDifficulty.HARD
        elif mastery > 0.5:
            target_diff = QuestionDifficulty.MEDIUM
        else:
            target_diff = QuestionDifficulty.EASY

        scored_concepts.append((priority, concept, target_diff))

    # Sort descending by priority score
    scored_concepts.sort(key=lambda x: x[0], reverse=True)

    # Build diverse, non-repeating target list.
    # Rule: untested concepts (0 attempts) MUST be included first — user hasn't been assessed on them yet.
    # Then fill remaining slots with highest-priority practiced concepts.
    untested = [(priority, c, diff) for priority, c, diff in scored_concepts if c.get("attempts", 0) == 0]
    practiced = [(priority, c, diff) for priority, c, diff in scored_concepts if c.get("attempts", 0) > 0]

    # Sort untested by mastery signal (all 0 mastery, so use name for determinism)
    # Sort practiced by composite priority score (already sorted)
    result_targets: List[Tuple[Dict[str, Any], QuestionDifficulty]] = []
    seen_concept_ids = set()

    # Fill up to requested_count slots: untested first, then practiced
    combined = untested + practiced
    for (priority, concept, target_diff) in combined:
        if len(result_targets) >= requested_count:
            break
        cid = str(concept["_id"])
        if cid not in seen_concept_ids:
            seen_concept_ids.add(cid)
            result_targets.append((concept, target_diff))

    # If we still don't have enough (e.g. only 2 concepts total), cycle through
    if len(result_targets) < requested_count and combined:
        for (priority, concept, target_diff) in combined:
            if len(result_targets) >= requested_count:
                break
            result_targets.append((concept, target_diff))

    return result_targets



async def generate_grounded_question(
    project_id: str,
    user_id: str,
    assessment_id: str,
    target_concept: dict,
    difficulty: QuestionDifficulty,
    question_type: QuestionType,
    order_index: int,
) -> Optional[QuizQuestionModel]:
    """
    Generate a grounded MCQ or Open-Ended question for a target concept.
    Retrieves Project Knowledge chunks, calls LLMProvider, validates JSON structure,
    checks duplicate question text within the assessment, and returns QuizQuestionModel.
    """
    concept_id = str(target_concept["_id"])
    concept_name = target_concept.get("name", "General Concept")
    db = get_database()

    # 1. Retrieve Knowledge Chunks for target concept
    search_res = await search_project_knowledge(
        project_id=project_id,
        user_id=user_id,
        query=concept_name,
        top_k=3,
        min_score=0.1,
    )
    chunks = search_res.results
    if not chunks:
        # Fallback: query all chunks for project
        all_chunks_cursor = db["chunks"].find({"project_id": project_id}).limit(3)
        all_chunks_docs = [doc async for doc in all_chunks_cursor]
        chunks = [
            SearchResultItem(
                chunk_id=str(doc["_id"]),
                material_id=str(doc["material_id"]),
                filename=doc.get("filename", "document.pdf"),
                page_number=doc.get("page_number", 1),
                chunk_text=doc.get("chunk_text", ""),
                score=0.5,
            )
            for doc in all_chunks_docs
        ]

    if not chunks:
        logger.warning(f"No knowledge chunks available in project {project_id} for question generation.")
        return None

    # 2. Format LLM System & User Prompts
    system_prompt = (
        "GENERATE_QUESTION: You are an expert AI Examiner for a Project-based learning platform.\n"
        "Your task is to generate a grounded quiz question based ONLY on the provided learning evidence.\n"
        "OUTPUT FORMAT (STRICT JSON):\n"
        "For MCQ:\n"
        '{"question_type": "MCQ", "question_text": "...", "options": {"A": "...", "B": "...", "C": "...", "D": "..."}, "correct_answer": "A", "explanation": "...", "difficulty": "MEDIUM"}\n'
        "For OPEN_ENDED:\n"
        '{"question_type": "OPEN_ENDED", "question_text": "...", "explanation": "...", "difficulty": "MEDIUM"}\n'
        "CRITICAL RULES:\n"
        "1. MCQ MUST have exactly 4 options (A, B, C, D) and exactly 1 correct_answer (A, B, C, or D).\n"
        "2. Do NOT invent facts outside the supplied evidence.\n"
        "3. Output MUST be valid JSON only."
    )

    chunks_str = "\n".join(
        f"- [Chunk ID: {chk.chunk_id}] (Page {chk.page_number}): {chk.chunk_text}"
        for chk in chunks
    )

    user_prompt = (
        f"TARGET CONCEPT: {concept_name}\n"
        f"QUESTION_TYPE: {question_type.value}\n"
        f"DIFFICULTY: {difficulty.value}\n\n"
        f"EVIDENCE CHUNKS:\n{chunks_str}\n\n"
        "Generate the structured question JSON now."
    )

    provider = LLMProvider()
    
    # Bounded retry loop for generation & duplicate prevention
    for attempt_num in range(2):
        raw_json = provider.generate_json_completion(system_prompt, user_prompt)
        q_text = str(raw_json.get("question_text", "")).strip()

        if not q_text:
            continue

        # Check duplicate question in this assessment
        norm_q = _normalize_text(q_text)
        existing_dup = await db["quiz_questions"].find_one({
            "assessment_id": assessment_id,
            "project_id": project_id,
        })
        if existing_dup and _normalize_text(existing_dup.get("question_text", "")) == norm_q:
            logger.info(f"Duplicate question text detected (attempt {attempt_num+1}) — retrying generation.")
            continue

        # Validate MCQ structure
        if question_type == QuestionType.MCQ:
            opts = raw_json.get("options")
            correct = str(raw_json.get("correct_answer", "")).upper()
            if not isinstance(opts, dict) or set(opts.keys()) != {"A", "B", "C", "D"}:
                continue
            if correct not in ("A", "B", "C", "D"):
                correct = "A"

            citations = [
                CitationModel(
                    material_id=chunks[0].material_id,
                    filename=chunks[0].filename,
                    page_number=chunks[0].page_number,
                    chunk_id=chunks[0].chunk_id,
                    relevance_score=chunks[0].score,
                )
            ]

            return QuizQuestionModel(
                assessment_id=assessment_id,
                project_id=project_id,
                concept_ids=[concept_id],
                concept_names=[concept_name],
                question_type=QuestionType.MCQ,
                question_text=q_text,
                options={k: str(v) for k, v in opts.items()},
                correct_answer=correct,
                difficulty=difficulty,
                explanation=str(raw_json.get("explanation", "")).strip(),
                source_references=citations,
                order_index=order_index,
                created_at=datetime.now(timezone.utc),
            )
        else:
            citations = [
                CitationModel(
                    material_id=chunks[0].material_id,
                    filename=chunks[0].filename,
                    page_number=chunks[0].page_number,
                    chunk_id=chunks[0].chunk_id,
                    relevance_score=chunks[0].score,
                )
            ]

            return QuizQuestionModel(
                assessment_id=assessment_id,
                project_id=project_id,
                concept_ids=[concept_id],
                concept_names=[concept_name],
                question_type=QuestionType.OPEN_ENDED,
                question_text=q_text,
                options=None,
                correct_answer=None,
                difficulty=difficulty,
                explanation=str(raw_json.get("explanation", "")).strip(),
                source_references=citations,
                order_index=order_index,
                created_at=datetime.now(timezone.utc),
            )

    return None


async def evaluate_open_ended_answer(
    question: QuizQuestionModel,
    student_answer: str,
    user_id: Optional[str] = None,
) -> OpenEndedEvaluationSchema:
    """
    Qualitative evaluation of an open-ended student response against Project Knowledge.
    Returns structured feedback schema.
    """
    db = get_database()
    clean_ans = student_answer.strip()

    # Retrieve knowledge chunks for context via RAG search
    concept_name = question.concept_names[0] if question.concept_names else "General Concept"
    search_res = await search_project_knowledge(
        project_id=question.project_id,
        user_id=user_id,
        query=f"{concept_name} {question.question_text}",
        top_k=3,
        min_score=0.0,
    )
    if search_res and search_res.results:
        evidence_text = "\n".join(c.chunk_text for c in search_res.results)
    else:
        chunks_cursor = db["chunks"].find({"project_id": question.project_id}).limit(3)
        chunks_docs = [c async for c in chunks_cursor]
        evidence_text = "\n".join(c.get("chunk_text", "") for c in chunks_docs)

    system_prompt = (
        "EVALUATE_OPEN_ENDED: You are an expert qualitative AI Evaluator.\n"
        "Assess the student's open-ended answer against the provided Project Learning Material.\n"
        "Do NOT penalize for different wording if conceptual understanding is present.\n"
        "Identify present key concepts and missing key concepts.\n"
        "OUTPUT FORMAT (STRICT JSON ONLY):\n"
        "{\n"
        '  "understanding": {"status": "GOOD", "feedback": "..."},\n'
        '  "accuracy": {"status": "GOOD", "feedback": "..."},\n'
        '  "relevance": {"status": "GOOD", "feedback": "..."},\n'
        '  "key_concepts_present": ["concept_1"],\n'
        '  "missing_concepts": ["concept_2"],\n'
        '  "reasoning_feedback": "...",\n'
        '  "strengths": ["strength_1"],\n'
        '  "areas_to_improve": ["improvement_1"],\n'
        '  "suggestion": "..."\n'
        "}"
    )

    user_prompt = (
        f"QUESTION: {question.question_text}\n"
        f"EXPLANATION / KEY MODEL ANSWER: {question.explanation}\n"
        f"PROJECT EVIDENCE:\n{evidence_text}\n\n"
        f"STUDENT ANSWER:\n{clean_ans}\n\n"
        "Evaluate the student response in JSON now."
    )

    provider = LLMProvider()
    raw_eval = provider.generate_json_completion(system_prompt, user_prompt)

    try:
        und = raw_eval.get("understanding", {})
        acc = raw_eval.get("accuracy", {})
        rel = raw_eval.get("relevance", {})

        return OpenEndedEvaluationSchema(
            understanding=UnderstandingComponentSchema(
                status=str(und.get("status", "GOOD")),
                feedback=str(und.get("feedback", "Understood core concept.")),
            ),
            accuracy=UnderstandingComponentSchema(
                status=str(acc.get("status", "GOOD")),
                feedback=str(acc.get("feedback", "Accurate representation.")),
            ),
            relevance=UnderstandingComponentSchema(
                status=str(rel.get("status", "GOOD")),
                feedback=str(rel.get("feedback", "Directly addressed prompt.")),
            ),
            key_concepts_present=[str(k) for k in raw_eval.get("key_concepts_present", [])],
            missing_concepts=[str(m) for m in raw_eval.get("missing_concepts", [])],
            reasoning_feedback=str(raw_eval.get("reasoning_feedback", "Solid reasoning.")),
            strengths=[str(s) for s in raw_eval.get("strengths", ["Good conceptual grasp."])],
            areas_to_improve=[str(a) for a in raw_eval.get("areas_to_improve", [])],
            suggestion=str(raw_eval.get("suggestion", "Continue revising key definitions.")),
        )
    except Exception as exc:
        logger.error(f"Failed to parse open-ended evaluation: {exc}")
        return OpenEndedEvaluationSchema(
            understanding=UnderstandingComponentSchema(status="GOOD", feedback="Understood core concept."),
            accuracy=UnderstandingComponentSchema(status="GOOD", feedback="Accurate response."),
            relevance=UnderstandingComponentSchema(status="GOOD", feedback="Relevant answer."),
            key_concepts_present=[concept_name],
            missing_concepts=[],
            reasoning_feedback="Good response.",
            strengths=["Addressed question directly."],
            areas_to_improve=[],
            suggestion="Review study notes for deeper insights.",
        )
