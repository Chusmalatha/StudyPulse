"""
LLM Provider Abstraction.
Supports Groq API, OpenAI API (or compatible), and deterministic local mock for testing/offline mode.
"""
import json
import logging
from typing import Dict, Any, List, Optional
import urllib.request
import urllib.error

from app.core.config import settings

logger = logging.getLogger(__name__)


class LLMProvider:
    """Interface for invoking LLMs with structured output constraints."""

    def __init__(self, provider: str = None, model: str = None, api_key: str = None):
        self.provider = (provider or settings.LLM_PROVIDER).lower()
        self.model = model or settings.LLM_MODEL
        self.api_key = api_key or settings.GROQ_API_KEY

    def generate_json_completion(
        self,
        system_prompt: str,
        user_prompt: str,
    ) -> Dict[str, Any]:
        """Generic method to send prompts and get parsed JSON output from LLM or mock."""
        if self.provider == "groq" and self.api_key:
            return self._call_groq_api(system_prompt, user_prompt)
        elif self.provider == "openai" and self.api_key:
            return self._call_openai_api(system_prompt, user_prompt)
        else:
            return self._fallback_json_completion(system_prompt, user_prompt)

    def generate_tutor_response(
        self,
        system_prompt: str,
        user_prompt: str,
    ) -> Dict[str, Any]:
        """Send system & user prompts to LLM provider for Tutor Q&A."""
        parsed = self.generate_json_completion(system_prompt, user_prompt)
        return self._sanitize_tutor_json(parsed)

    def _call_groq_api(self, system_prompt: str, user_prompt: str) -> Dict[str, Any]:
        """Call Groq Cloud Chat Completion endpoint using standard urllib."""
        url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
        }
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "response_format": {"type": "json_object"},
            "temperature": 0.2,
            "max_tokens": 1024
        }

        try:
            req = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"), headers=headers, method="POST")
            with urllib.request.urlopen(req, timeout=30) as resp:
                res_data = json.loads(resp.read().decode("utf-8"))
                content = res_data["choices"][0]["message"]["content"]
                return json.loads(content)
        except Exception as exc:
            logger.error(f"Groq API call failed: {exc}. Falling back to deterministic mock.")
            return self._fallback_json_completion(system_prompt, user_prompt)

    def _call_openai_api(self, system_prompt: str, user_prompt: str) -> Dict[str, Any]:
        """Call OpenAI Chat Completion endpoint using standard urllib."""
        url = "https://api.openai.com/v1/chat/completions"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
        }
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "response_format": {"type": "json_object"},
            "temperature": 0.2,
            "max_tokens": 1024
        }

        try:
            req = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"), headers=headers, method="POST")
            with urllib.request.urlopen(req, timeout=30) as resp:
                res_data = json.loads(resp.read().decode("utf-8"))
                content = res_data["choices"][0]["message"]["content"]
                return json.loads(content)
        except Exception as exc:
            logger.error(f"OpenAI API call failed: {exc}. Falling back to deterministic mock.")
            return self._fallback_json_completion(system_prompt, user_prompt)

    def _sanitize_tutor_json(self, parsed: dict) -> Dict[str, Any]:
        """Verify and sanitize Tutor LLM JSON fields."""
        answer = str(parsed.get("answer", "")).strip()
        grounded = bool(parsed.get("grounded", True))
        unsupported = bool(parsed.get("unsupported", False))
        citation_ids = parsed.get("citation_chunk_ids", [])
        if not isinstance(citation_ids, list):
            citation_ids = []

        citation_chunk_ids = [str(cid) for cid in citation_ids if isinstance(cid, (str, int))]

        if unsupported or not answer:
            grounded = False
            unsupported = True
            citation_chunk_ids = []

        return {
            "answer": answer,
            "grounded": grounded,
            "citation_chunk_ids": citation_chunk_ids,
            "unsupported": unsupported,
        }

    def _fallback_json_completion(self, system_prompt: str, user_prompt: str) -> Dict[str, Any]:
        """
        Fallback mock logic when no API key is provided or API call fails.
        Handles Tutor Q&A, Question Generation (MCQ & Open-Ended), and Open-Ended Evaluation prompts.
        """
        import re

        # 1. Question Generation Mock
        if "GENERATE_QUESTION" in system_prompt or "GENERATE_QUESTION" in user_prompt:
            target_concept = "Learning Concepts"
            c_match = re.search(r'TARGET CONCEPT: ([^\n]+)', user_prompt)
            if c_match:
                target_concept = c_match.group(1).strip()

            diff_match = re.search(r'DIFFICULTY: ([^\n]+)', user_prompt)
            difficulty = diff_match.group(1).strip() if diff_match else "MEDIUM"

            q_type = "MCQ"
            if "QUESTION_TYPE: OPEN_ENDED" in user_prompt:
                q_type = "OPEN_ENDED"

            chunk_ids = re.findall(r'\[Chunk ID: ([^\]]+)\]', user_prompt)
            
            # Extract actual evidence snippet from user_prompt if available
            snippets = re.findall(r'Page \d+\): ([^\n]+)', user_prompt)
            snippet = snippets[0][:120].strip() if snippets else f"the foundational concepts of {target_concept}"

            # Create seed hash from snippet and concept to vary questions deterministically
            var_seed = abs(hash(f"{target_concept}_{difficulty}_{snippet}")) % 3

            if q_type == "MCQ":
                if var_seed == 0:
                    q_text = f"According to your study material, how is {target_concept} defined and applied?"
                    correct = "A"
                    options = {
                        "A": f"It focuses on {snippet[:60]}...",
                        "B": f"It is an obsolete algorithm replaced by traditional linear regression.",
                        "C": f"It requires manual annotation for every single sample.",
                        "D": f"It operates without any input data."
                    }
                elif var_seed == 1:
                    q_text = f"In the context of {target_concept}, what is a primary operational objective described in the document?"
                    correct = "B"
                    options = {
                        "A": f"To maximize computational latency across network nodes.",
                        "B": f"To process features related to {snippet[:50]}...",
                        "C": f"To bypass feature extraction entirely.",
                        "D": f"To disable loss function evaluation."
                    }
                else:
                    q_text = f"Which aspect of {target_concept} is highlighted in your course materials?"
                    correct = "C"
                    options = {
                        "A": f"Its incompatibility with modern deep learning frameworks.",
                        "B": f"Its restriction to binary integer outputs.",
                        "C": f"Its role in modeling {snippet[:50]}...",
                        "D": f"Its reliance on hardware-level memory locks."
                    }

                return {
                    "question_type": "MCQ",
                    "question_text": q_text,
                    "options": options,
                    "correct_answer": correct,
                    "explanation": f"Based on page evidence in your project material: '{snippet}'",
                    "difficulty": difficulty,
                    "source_chunk_ids": chunk_ids[:1] if chunk_ids else []
                }
            else:
                return {
                    "question_type": "OPEN_ENDED",
                    "question_text": f"Based on your study material regarding {target_concept}, explain how '{snippet[:80]}' functions and why it is important.",
                    "explanation": f"A complete answer should discuss the mechanism of {target_concept} as described in your study material.",
                    "difficulty": difficulty,
                    "source_chunk_ids": chunk_ids[:1] if chunk_ids else []
                }

        # 2. Open-Ended Evaluation Mock
        if "EVALUATE_OPEN_ENDED" in system_prompt or "EVALUATE_OPEN_ENDED" in user_prompt:
            # Use answer length as a proxy for effort rather than checking for domain-specific terms
            ans_length = len(user_prompt)
            is_detailed = ans_length > 50

            return {
                "understanding": {
                    "status": "GOOD" if is_detailed else "NEEDS_IMPROVEMENT",
                    "feedback": "Demonstrates clear conceptual understanding of the core topic." if is_detailed else "Response is very brief — try to elaborate more."
                },
                "accuracy": {
                    "status": "GOOD",
                    "feedback": "The explanation aligns with the grounded project materials."
                },
                "relevance": {
                    "status": "GOOD",
                    "feedback": "The student directly addressed the prompt."
                },
                "key_concepts_present": ["core concept"],
                "missing_concepts": [],
                "reasoning_feedback": "The answer explains the main idea. Consider providing more depth and examples from your study material.",
                "strengths": ["Correctly identified the main purpose", "Used clear language"],
                "areas_to_improve": [] if is_detailed else ["Provide more detail and specific examples"],
                "suggestion": "Review the relevant sections in your study material to solidify your understanding."
            }


        # 3. Default Tutor Q&A Mock
        if "NO_EVIDENCE_AVAILABLE" in user_prompt or "EVIDENCE CHUNKS:\n- None" in user_prompt:
            return {
                "answer": "I don't have enough information about that in the learning material for this Project, so I can't answer reliably from the available sources.",
                "grounded": False,
                "citation_chunk_ids": [],
                "unsupported": True,
            }

        chunk_ids = re.findall(r'\[Chunk ID: ([^\]]+)\]', user_prompt)
        lines = user_prompt.splitlines()
        
        chunk_texts = []
        for line in lines:
            if "- [Chunk ID:" in line and "): " in line:
                parts = line.split("): ", 1)
                if len(parts) > 1:
                    chunk_texts.append(parts[1].strip())

        extracted_info = " ".join(chunk_texts)
        if len(extracted_info) > 400:
            extracted_info = extracted_info[:400] + "..."
            
        user_question = "your query"
        for line in lines:
            if line.startswith("USER QUESTION:"):
                user_question = line.replace("USER QUESTION:", "").strip()

        if extracted_info:
            answer = f"Based on your Project learning materials, regarding '{user_question}':\n\n{extracted_info}"
        else:
            answer = f"Based on your Project learning materials, regarding '{user_question}': the material explains key concepts related to this topic in detail."

        return {
            "answer": answer,
            "grounded": True,
            "citation_chunk_ids": chunk_ids[:1] if chunk_ids else [],
            "unsupported": False,
        }
