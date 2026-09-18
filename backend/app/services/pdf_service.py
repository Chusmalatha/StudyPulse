"""
PDF text extraction and page-aware chunking service.

Preserves page_number on every extracted text block and chunk for grounded AI Tutor citations.
"""
import logging
import re
from typing import List, Dict, Any
from pypdf import PdfReader

logger = logging.getLogger(__name__)


def extract_pdf_pages(file_path: str) -> List[Dict[str, Any]]:
    """
    Extract text page-by-page from a PDF file.

    Returns:
        List of dicts: [{"page_number": 1, "text": "..."}, ...]
    Raises:
        ValueError if the file cannot be parsed or has no text.
    """
    try:
        reader = PdfReader(file_path)
    except Exception as exc:
        logger.error(f"Failed to open PDF file '{file_path}': {exc}")
        raise ValueError(f"Corrupt or unreadable PDF file: {exc}")

    if not reader.pages:
        raise ValueError("PDF file contains no pages.")

    extracted_pages = []
    total_text_length = 0

    for idx, page in enumerate(reader.pages):
        page_num = idx + 1
        raw_text = page.extract_text() or ""
        # Clean up excessive internal whitespace but preserve words and sentences
        cleaned_text = re.sub(r'\s+', ' ', raw_text).strip()

        if cleaned_text:
            extracted_pages.append({
                "page_number": page_num,
                "text": cleaned_text
            })
            total_text_length += len(cleaned_text)

    if total_text_length == 0:
        raise ValueError("PDF file contains no extractable text (it may be image-only or scanned).")

    logger.info(f"Extracted {len(extracted_pages)} non-empty pages from {file_path}")
    return extracted_pages


def chunk_pages(
    pages: List[Dict[str, Any]],
    chunk_size: int = 500,
    overlap: int = 50,
) -> List[Dict[str, Any]]:
    """
    Split extracted page text into reasonable chunks while explicitly preserving page_number.

    Args:
        pages: List of page dicts [{"page_number": int, "text": str}]
        chunk_size: Target characters per chunk
        overlap: Character overlap between consecutive chunks on the same page

    Returns:
        List of chunk dicts: [{"page_number": int, "chunk_index": int, "chunk_text": str}]
    """
    chunks = []
    global_chunk_index = 0

    for page in pages:
        page_num = page["page_number"]
        text = page["text"]

        if not text:
            continue

        # If page text is smaller than chunk_size, make a single chunk for this page
        if len(text) <= chunk_size:
            chunks.append({
                "page_number": page_num,
                "chunk_index": global_chunk_index,
                "chunk_text": text,
            })
            global_chunk_index += 1
            continue

        # Split text using sliding window with overlap
        start = 0
        text_len = len(text)

        while start < text_len:
            end = start + chunk_size

            # Avoid splitting words mid-way if possible
            if end < text_len:
                space_idx = text.rfind(' ', start, end)
                if space_idx > start + (chunk_size // 2):
                    end = space_idx

            chunk_str = text[start:end].strip()
            if chunk_str:
                chunks.append({
                    "page_number": page_num,
                    "chunk_index": global_chunk_index,
                    "chunk_text": chunk_str,
                })
                global_chunk_index += 1

            if end >= text_len:
                break

            start = max(start + 1, end - overlap)

    logger.info(f"Created {len(chunks)} page-aware chunks across {len(pages)} pages")
    return chunks
