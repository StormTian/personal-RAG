"""Text processing utilities."""

import math
import re
from typing import List, Sequence, Tuple


def tokenize(text: str) -> List[str]:
    """Tokenize text with support for English and Chinese."""
    text = text.lower()
    tokens: List[str] = []
    tokens.extend(re.findall(r"[a-z0-9]+", text))
    
    for block in re.findall(r"[\u4e00-\u9fff]+", text):
        if len(block) == 1:
            tokens.append(block)
            continue
        for size in (2, 3):
            if len(block) < size:
                continue
            tokens.extend(block[index:index + size] for index in range(len(block) - size + 1))
    
    return tokens


def split_sentences(text: str) -> List[str]:
    """Split text into sentences."""
    normalized = re.sub(r"\s+", " ", text).strip()
    if not normalized:
        return []
    parts = re.split(r"(?<=[。！？!?])\s+|(?<=[。！？!?])", normalized)
    return [part.strip() for part in parts if part.strip()]


def split_paragraphs(text: str) -> List[str]:
    """Split text into paragraphs."""
    paragraphs: List[str] = []
    buffer: List[str] = []
    
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line:
            if buffer:
                paragraphs.append(" ".join(buffer))
                buffer = []
            continue
        if line.startswith("#"):
            if buffer:
                paragraphs.append(" ".join(buffer))
                buffer = []
            paragraphs.append(line.lstrip("# ").strip() + "。")
            continue
        buffer.append(line)
    
    if buffer:
        paragraphs.append(" ".join(buffer))
    return paragraphs


def wrap_paragraph(paragraph: str, max_chars: int) -> List[str]:
    """Wrap paragraph into chunks of max_chars."""
    if len(paragraph) <= max_chars:
        return [paragraph]
    
    pieces: List[str] = []
    current = ""
    for sentence in split_sentences(paragraph):
        candidate = f"{current} {sentence}".strip()
        if current and len(candidate) > max_chars:
            pieces.append(current)
            current = sentence
        else:
            current = candidate
    
    if current:
        pieces.append(current)
    
    return pieces or [paragraph]


def chunk_text(text: str, max_chars: int = 240, overlap: int = 1) -> List[str]:
    """Chunk text into overlapping segments."""
    units: List[str] = []
    for paragraph in split_paragraphs(text):
        units.extend(wrap_paragraph(paragraph, max_chars))
    
    if not units:
        return []
    
    chunks: List[str] = []
    current: List[str] = []
    
    for unit in units:
        candidate = " ".join(current + [unit]).strip()
        if current and len(candidate) > max_chars:
            chunks.append(" ".join(current).strip())
            current = current[-overlap:] + [unit] if overlap else [unit]
        else:
            current.append(unit)
    
    if current:
        chunks.append(" ".join(current).strip())
    
    return chunks


def first_heading(text: str, fallback: str) -> str:
    """Extract first heading from markdown text."""
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("#"):
            return stripped.lstrip("# ").strip()
    return fallback


def first_non_empty_line(text: str, fallback: str) -> str:
    """Extract first non-empty line."""
    for line in text.splitlines():
        stripped = line.strip().lstrip("#").strip()
        if stripped:
            return stripped
    return fallback


def shorten(text: str, width: int = 88) -> str:
    """Shorten text to width characters."""
    return text if len(text) <= width else text[:width - 3] + "..."


def normalize_vector(values: Sequence[float]) -> Tuple[float, ...]:
    """Normalize vector to unit length."""
    norm = math.sqrt(sum(value * value for value in values))
    if not norm:
        return tuple(0.0 for _ in values)
    return tuple(value / norm for value in values)


def dot_product(left: Sequence[float], right: Sequence[float]) -> float:
    """Calculate dot product of two vectors."""
    return sum(l * r for l, r in zip(left, right))


def cosine_similarity(left: Sequence[float], right: Sequence[float]) -> float:
    """Calculate cosine similarity between two vectors."""
    if not left or not right:
        return 0.0
    return dot_product(left, right)


def batch_items(items: Sequence[str], batch_size: int) -> List[Sequence[str]]:
    """Split items into batches."""
    return [items[i:i + batch_size] for i in range(0, len(items), batch_size)]
