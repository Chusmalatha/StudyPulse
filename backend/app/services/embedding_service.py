"""
Embedding service abstraction.

Converts text chunks into numerical vector embeddings for vector storage and semantic retrieval.
Isolated behind a clean service function so the underlying model/provider (e.g. OpenAI, HuggingFace, sentence-transformers) can be swapped without changing business logic.
"""
import hashlib
import math
import logging
from typing import List

from app.core.config import settings

logger = logging.getLogger(__name__)

EMBEDDING_DIMENSION = 384


def _text_to_deterministic_vector(text: str, dim: int = EMBEDDING_DIMENSION) -> List[float]:
    """
    Fast, deterministic vector generator for prototype chunk embeddings.
    Produces a normalized float vector of length `dim` based on text tokens and hashes.
    """
    vector = [0.0] * dim
    words = text.lower().split()
    if not words:
        return vector

    for idx, word in enumerate(words):
        # Generate hash for each word
        h = int(hashlib.md5(word.encode('utf-8')).hexdigest(), 16)
        target_dim = h % dim
        vector[target_dim] += (1.0 + (idx % 3) * 0.1)

    # L2 Normalization
    magnitude = math.sqrt(sum(v * v for v in vector))
    if magnitude > 0:
        vector = [round(v / magnitude, 6) for v in vector]

    return vector


async def generate_embeddings(texts: List[str]) -> List[List[float]]:
    """
    Generate embedding vectors for a list of text strings.

    Args:
        texts: List of text chunk strings

    Returns:
        List of float vectors, matching the order of input texts.
    """
    if not texts:
        return []

    provider = settings.EMBEDDING_PROVIDER.lower()
    if provider == "disabled" or not provider:
        logger.error("Embedding generation failed: Provider is disabled or unconfigured.")
        raise ValueError("Embedding provider is not configured.")

    logger.info(f"Generating embeddings for {len(texts)} text chunks using provider '{settings.EMBEDDING_PROVIDER}' ({settings.EMBEDDING_MODEL})...")
    
    # HuggingFace Inference API
    if provider == "huggingface":
        if not settings.HF_API_KEY:
            raise ValueError("HF_API_KEY is not configured.")
        import urllib.request
        import urllib.error
        import json
        import time
        
        api_url = f"https://api-inference.huggingface.co/pipeline/feature-extraction/{settings.EMBEDDING_MODEL}"
        headers = {
            "Authorization": f"Bearer {settings.HF_API_KEY}",
            "Content-Type": "application/json"
        }
        
        payload = {"inputs": texts}
        
        for attempt in range(5):
            try:
                req = urllib.request.Request(api_url, data=json.dumps(payload).encode("utf-8"), headers=headers, method="POST")
                with urllib.request.urlopen(req, timeout=30) as resp:
                    res_data = json.loads(resp.read().decode("utf-8"))
                    if isinstance(res_data, list) and len(res_data) == len(texts):
                        return res_data
                    else:
                        raise ValueError(f"Unexpected HF API response shape: {type(res_data)}")
            except urllib.error.HTTPError as e:
                err_content = e.read().decode()
                if e.code == 503 and "currently loading" in err_content.lower():
                    logger.warning("HuggingFace model is loading, waiting 10s...")
                    time.sleep(10)
                    continue
                else:
                    logger.error(f"HF API HTTP Error {e.code}: {err_content}")
                    raise ValueError(f"HF API Error: {err_content}")
            except Exception as e:
                logger.error(f"HF API Request failed: {str(e)}")
                raise
        
        raise ValueError("HF API failed after retries (model still loading).")

    # Supported prototype providers
    if provider in ("local", "deterministic", "default"):
        embeddings = [_text_to_deterministic_vector(text) for text in texts]
        return embeddings

    # Fallback to local/deterministic for development
    embeddings = [_text_to_deterministic_vector(text) for text in texts]
    return embeddings

