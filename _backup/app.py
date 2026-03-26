from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import pickle
import re
import subprocess
import sys
import textwrap
import threading
import time
import urllib.error
import urllib.request
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Set, Tuple


ROOT = Path(__file__).resolve().parent
DEPS_DIR = ROOT / ".deps"
if DEPS_DIR.exists():
    sys.path.insert(0, str(DEPS_DIR))

DOCUMENT_LIBRARY_DIR = ROOT / "document_library"
KNOWLEDGE_DIR = DOCUMENT_LIBRARY_DIR
SUPPORTED_EXTENSIONS = {
    ".md": "markdown",
    ".markdown": "markdown",
    ".txt": "text",
    ".doc": "word",
    ".docx": "word",
    ".pdf": "pdf",
}

try:
    from pypdf import PdfReader
except ImportError:
    PdfReader = None


def tokenize(text: str) -> List[str]:
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
            tokens.extend(block[index : index + size] for index in range(len(block) - size + 1))

    return tokens


def split_sentences(text: str) -> List[str]:
    normalized = re.sub(r"\s+", " ", text).strip()
    if not normalized:
        return []
    parts = re.split(r"(?<=[。！？!?])\s+|(?<=[。！？!?])", normalized)
    return [part.strip() for part in parts if part.strip()]


def split_paragraphs(text: str) -> List[str]:
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
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("#"):
            return stripped.lstrip("# ").strip()
    return fallback


def first_non_empty_line(text: str, fallback: str) -> str:
    for line in text.splitlines():
        stripped = line.strip().lstrip("#").strip()
        if stripped:
            return stripped
    return fallback


def shorten(text: str, width: int = 88) -> str:
    return text if len(text) <= width else text[: width - 3] + "..."


def read_text_file(path: Path) -> str:
    for encoding in ("utf-8", "utf-8-sig", "gb18030"):
        try:
            return path.read_text(encoding=encoding)
        except UnicodeDecodeError:
            continue
    return path.read_text(encoding="utf-8", errors="ignore")


def extract_word_file(path: Path) -> str:
    try:
        result = subprocess.run(
            ["textutil", "-convert", "txt", "-stdout", "-encoding", "UTF-8", str(path)],
            check=True,
            capture_output=True,
        )
    except FileNotFoundError as exc:
        raise RuntimeError("系统缺少 textutil，无法解析 Word 文件。") from exc
    except subprocess.CalledProcessError as exc:
        stderr = exc.stderr.decode("utf-8", errors="ignore").strip()
        raise RuntimeError(stderr or "Word 文件解析失败。") from exc

    return result.stdout.decode("utf-8", errors="ignore")


def extract_pdf_file(path: Path) -> str:
    if PdfReader is not None:
        reader = PdfReader(str(path))
        parts: List[str] = []
        for page in reader.pages:
            text = page.extract_text() or ""
            if text.strip():
                parts.append(text)
        return "\n".join(parts)

    swift_script = f"""
import Foundation
import PDFKit

let url = URL(fileURLWithPath: "{str(path)}")
guard let document = PDFDocument(url: url) else {{
    fputs("failed to open pdf\\n", stderr)
    exit(1)
}}

var parts: [String] = []
for index in 0..<document.pageCount {{
    if let page = document.page(at: index), let text = page.string, !text.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty {{
        parts.append(text)
    }}
}}
print(parts.joined(separator: "\\n"))
"""
    try:
        result = subprocess.run(
            [
                "swift",
                "-",
            ],
            input=swift_script.encode("utf-8"),
            check=True,
            capture_output=True,
            env={
                **os.environ,
                "SWIFT_MODULECACHE_PATH": "/tmp/rag_swift_cache",
                "CLANG_MODULE_CACHE_PATH": "/tmp/rag_swift_cache",
            },
        )
    except FileNotFoundError as exc:
        raise RuntimeError("系统缺少可用的 PDF 解析能力，请安装 pypdf。") from exc
    except subprocess.CalledProcessError as exc:
        stderr = exc.stderr.decode("utf-8", errors="ignore").strip()
        raise RuntimeError(stderr or "PDF 文件解析失败。") from exc

    return result.stdout.decode("utf-8", errors="ignore")


def normalize_vector(values: Sequence[float]) -> Tuple[float, ...]:
    norm = math.sqrt(sum(value * value for value in values))
    if not norm:
        return tuple(0.0 for _ in values)
    return tuple(value / norm for value in values)


def dot_product(left: Sequence[float], right: Sequence[float]) -> float:
    return sum(l * r for l, r in zip(left, right))


def cosine_similarity(left: Sequence[float], right: Sequence[float]) -> float:
    if not left or not right:
        return 0.0
    return dot_product(left, right)


def batch_items(items: Sequence[str], batch_size: int) -> List[Sequence[str]]:
    return [items[index : index + batch_size] for index in range(0, len(items), batch_size)]


def extract_json_object(text: str) -> str:
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end < start:
        raise RuntimeError("model response does not contain a JSON object")
    return text[start : end + 1]


def post_json(url: str, headers: Dict[str, str], payload: Dict[str, object], timeout: int) -> Dict[str, object]:
    request = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers=headers,
        method="POST",
    )

    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="ignore")
        raise RuntimeError(f"request failed: {exc.code} {body}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"request failed: {exc.reason}") from exc


def chat_message_to_text(content: object) -> str:
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts: List[str] = []
        for item in content:
            if isinstance(item, dict):
                if item.get("type") == "text" and isinstance(item.get("text"), str):
                    parts.append(item["text"])
                elif isinstance(item.get("text"), dict) and isinstance(item["text"].get("value"), str):
                    parts.append(item["text"]["value"])
        return "\n".join(parts)
    raise RuntimeError("model response content is not supported")


@dataclass(frozen=True)
class SourceDocument:
    source: str
    title: str
    text: str
    file_type: str


@dataclass(frozen=True)
class Chunk:
    chunk_id: int
    source: str
    title: str
    text: str


@dataclass(frozen=True)
class CandidateScore:
    index: int
    retrieve_score: float
    lexical_score: float
    title_score: float
    rerank_score: float
    llm_score: float = 0.0


@dataclass
class SearchHit:
    chunk: Chunk
    score: float
    retrieve_score: float
    rerank_score: float
    lexical_score: float
    title_score: float
    llm_score: float


@dataclass
class RagResponse:
    query: str
    answer_lines: List[str]
    hits: List[SearchHit]

    def to_dict(self) -> Dict[str, object]:
        return {
            "query": self.query,
            "answer_lines": self.answer_lines,
            "hits": [
                {
                    "score": round(hit.score, 4),
                    "retrieve_score": round(hit.retrieve_score, 4),
                    "rerank_score": round(hit.rerank_score, 4),
                    "lexical_score": round(hit.lexical_score, 4),
                    "title_score": round(hit.title_score, 4),
                    "llm_score": round(hit.llm_score, 4),
                    "source": hit.chunk.source,
                    "title": hit.chunk.title,
                    "text": hit.chunk.text,
                    "chunk_id": hit.chunk.chunk_id,
                }
                for hit in self.hits
            ],
        }


@dataclass(frozen=True)
class IndexSnapshot:
    library_dir: Path
    documents: Tuple[SourceDocument, ...]
    skipped_files: Tuple[Tuple[str, str], ...]
    chunks: Tuple[Chunk, ...]
    chunk_embeddings: Tuple[Tuple[float, ...], ...]
    chunk_token_counts: Tuple[Dict[str, int], ...]
    chunk_title_token_sets: Tuple[frozenset, ...]
    idf: Dict[str, float]
    avgdl: float
    supported_formats: Tuple[str, ...]
    embedding_backend: str
    reranker_backend: str
    retrieval_strategy: str
    rerank_strategy: str


class EmbeddingBackend:
    name = "embedding-backend"

    def embed_texts(self, texts: Sequence[str]) -> List[Tuple[float, ...]]:
        raise NotImplementedError

    def embed_query(self, text: str) -> Tuple[float, ...]:
        return self.embed_texts([text])[0]


class LocalHashEmbeddingBackend(EmbeddingBackend):
    def __init__(self, dimensions: int = 256, projections_per_token: int = 8) -> None:
        self.dimensions = dimensions
        self.projections_per_token = projections_per_token
        self.name = f"local-hash-{dimensions}d"
        self._token_cache: Dict[str, List[Tuple[int, float]]] = {}

    def _token_projection(self, token: str) -> List[Tuple[int, float]]:
        cached = self._token_cache.get(token)
        if cached is not None:
            return cached

        digest = hashlib.sha256(token.encode("utf-8")).digest()
        projection: List[Tuple[int, float]] = []
        for offset in range(self.projections_per_token):
            start = offset * 4
            idx = int.from_bytes(digest[start : start + 2], "big") % self.dimensions
            sign = 1.0 if digest[start + 2] % 2 == 0 else -1.0
            magnitude = 0.35 + (digest[start + 3] / 255.0)
            projection.append((idx, sign * magnitude))

        self._token_cache[token] = projection
        return projection

    def embed_texts(self, texts: Sequence[str]) -> List[Tuple[float, ...]]:
        vectors: List[Tuple[float, ...]] = []
        for text in texts:
            dense = [0.0] * self.dimensions
            token_counts = Counter(tokenize(text))
            for token, frequency in token_counts.items():
                weight = 1.0 + math.log(frequency)
                for idx, signed_weight in self._token_projection(token):
                    dense[idx] += signed_weight * weight
            vectors.append(normalize_vector(dense))
        return vectors


class OpenAICompatibleEmbeddingBackend(EmbeddingBackend):
    def __init__(self, api_key: str, model: str, base_url: str, timeout: int = 30) -> None:
        self.api_key = api_key
        self.model = model
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.name = f"openai-compatible:{model}"

    def _request_batch(self, texts: Sequence[str]) -> List[Tuple[float, ...]]:
        data = post_json(
            f"{self.base_url}/v1/embeddings",
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            payload={"model": self.model, "input": list(texts)},
            timeout=self.timeout,
        )
        ordered = sorted(data["data"], key=lambda item: item["index"])
        return [normalize_vector(item["embedding"]) for item in ordered]

    def embed_texts(self, texts: Sequence[str]) -> List[Tuple[float, ...]]:
        embeddings: List[Tuple[float, ...]] = []
        for batch in batch_items(list(texts), batch_size=32):
            embeddings.extend(self._request_batch(batch))
        return embeddings


class RerankerBackend:
    name = "reranker-backend"
    strategy = "rerank"

    def candidate_pool_size(self, top_k: int) -> int:
        return max(top_k * 6, 8)

    def rerank(
        self,
        query: str,
        snapshot: IndexSnapshot,
        candidates: Sequence[CandidateScore],
    ) -> List[CandidateScore]:
        raise NotImplementedError


class LocalHeuristicReranker(RerankerBackend):
    name = "local-heuristic"
    strategy = "embedding+lexical-overlap"

    def rerank(
        self,
        query: str,
        snapshot: IndexSnapshot,
        candidates: Sequence[CandidateScore],
    ) -> List[CandidateScore]:
        if not candidates:
            return []

        max_lexical = max((c.lexical_score for c in candidates), default=1.0)
        max_lexical = max_lexical if max_lexical > 0 else 1.0

        ranked: List[CandidateScore] = []
        for candidate in candidates:
            normalized_lexical = candidate.lexical_score / max_lexical
            # Adjust weights: Semantic 0.60, Lexical 0.30, Title 0.10
            score = candidate.retrieve_score * 0.60 + normalized_lexical * 0.30 + candidate.title_score * 0.10
            ranked.append(
                CandidateScore(
                    index=candidate.index,
                    retrieve_score=candidate.retrieve_score,
                    lexical_score=candidate.lexical_score,
                    title_score=candidate.title_score,
                    rerank_score=score,
                    llm_score=0.0,
                )
            )
        ranked.sort(
            key=lambda item: (item.rerank_score, item.retrieve_score, item.lexical_score, item.title_score),
            reverse=True,
        )
        return ranked


class OpenAICompatibleListwiseReranker(RerankerBackend):
    def __init__(
        self,
        api_key: str,
        model: str,
        base_url: str,
        fallback: RerankerBackend,
        timeout: int = 45,
        max_candidates: int = 12,
    ) -> None:
        self.api_key = api_key
        self.model = model
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.max_candidates = max_candidates
        self.fallback = fallback
        self.name = f"openai-compatible:{model}"
        self.strategy = "embedding+llm-listwise-rerank"

    def candidate_pool_size(self, top_k: int) -> int:
        return max(top_k * 8, self.max_candidates)

    def _request_scores(
        self,
        query: str,
        snapshot: IndexSnapshot,
        candidates: Sequence[CandidateScore],
    ) -> Dict[int, float]:
        prompt_id_to_index: Dict[int, int] = {}
        candidate_blocks: List[str] = []

        for prompt_id, candidate in enumerate(candidates):
            chunk = snapshot.chunks[candidate.index]
            prompt_id_to_index[prompt_id] = candidate.index
            candidate_blocks.append(
                f"[{prompt_id}]\n"
                f"source: {chunk.source}\n"
                f"title: {chunk.title}\n"
                f"text: {shorten(chunk.text.replace(chr(10), ' '), width=360)}"
            )

        data = post_json(
            f"{self.base_url}/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            payload={
                "model": self.model,
                "temperature": 0,
                "messages": [
                    {
                        "role": "system",
                        "content": (
                            "You are a retrieval reranker. Score each candidate chunk from 0 to 1 based on "
                            "how well it can answer the user query. Return JSON only in the format "
                            '{"scores":[{"id":0,"score":0.0}]}.'
                        ),
                    },
                    {
                        "role": "user",
                        "content": (
                            f"Query:\n{query}\n\nCandidates:\n\n" + "\n\n".join(candidate_blocks)
                        ),
                    },
                ],
                "max_tokens": 500,
            },
            timeout=self.timeout,
        )

        raw_content = data["choices"][0]["message"]["content"]
        content = chat_message_to_text(raw_content)
        payload = json.loads(extract_json_object(content))

        scores: Dict[int, float] = {}
        for item in payload.get("scores", []):
            try:
                prompt_id = int(item["id"])
                score = max(0.0, min(float(item["score"]), 1.0))
            except (KeyError, TypeError, ValueError):
                continue
            original_index = prompt_id_to_index.get(prompt_id)
            if original_index is not None:
                scores[original_index] = score
        return scores

    def rerank(
        self,
        query: str,
        snapshot: IndexSnapshot,
        candidates: Sequence[CandidateScore],
    ) -> List[CandidateScore]:
        base_ranked = self.fallback.rerank(query, snapshot, candidates)
        prompt_candidates = base_ranked[: min(len(base_ranked), self.max_candidates)]

        try:
            llm_scores = self._request_scores(query, snapshot, prompt_candidates)
        except Exception:
            return base_ranked

        merged: List[CandidateScore] = []
        for candidate in base_ranked:
            llm_score = llm_scores.get(candidate.index, 0.0)
            if candidate.index in llm_scores:
                final_score = candidate.rerank_score * 0.45 + llm_score * 0.55
            else:
                final_score = candidate.rerank_score
            merged.append(
                CandidateScore(
                    index=candidate.index,
                    retrieve_score=candidate.retrieve_score,
                    lexical_score=candidate.lexical_score,
                    title_score=candidate.title_score,
                    rerank_score=final_score,
                    llm_score=llm_score,
                )
            )

        merged.sort(
            key=lambda item: (item.rerank_score, item.llm_score, item.retrieve_score, item.lexical_score),
            reverse=True,
        )
        return merged


def build_embedding_backend() -> EmbeddingBackend:
    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    model = os.getenv("OPENAI_EMBED_MODEL", "").strip()
    base_url = os.getenv("OPENAI_BASE_URL", "https://api.openai.com").strip()
    if api_key and model:
        return OpenAICompatibleEmbeddingBackend(api_key=api_key, model=model, base_url=base_url)
    return LocalHashEmbeddingBackend()


def build_reranker_backend(fallback: Optional[RerankerBackend] = None) -> RerankerBackend:
    fallback_backend = fallback or LocalHeuristicReranker()
    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    model = os.getenv("OPENAI_RERANK_MODEL", "").strip()
    base_url = os.getenv("OPENAI_RERANK_BASE_URL", os.getenv("OPENAI_BASE_URL", "https://api.openai.com")).strip()

    if not api_key or not model:
        return fallback_backend

    timeout = int(os.getenv("OPENAI_RERANK_TIMEOUT", "45"))
    max_candidates = int(os.getenv("OPENAI_RERANK_MAX_CANDIDATES", "12"))
    return OpenAICompatibleListwiseReranker(
        api_key=api_key,
        model=model,
        base_url=base_url,
        timeout=timeout,
        max_candidates=max_candidates,
        fallback=fallback_backend,
    )


def load_source_document(path: Path, library_dir: Path) -> SourceDocument:
    suffix = path.suffix.lower()
    file_type = SUPPORTED_EXTENSIONS.get(suffix)
    if file_type is None:
        raise ValueError(f"unsupported format: {suffix}")

    if suffix in {".md", ".markdown", ".txt"}:
        raw_text = read_text_file(path)
    elif suffix in {".doc", ".docx"}:
        raw_text = extract_word_file(path)
    else:
        raw_text = extract_pdf_file(path)

    normalized_text = raw_text.replace("\x00", "")
    normalized_text = re.sub(r"\n{3,}", "\n\n", normalized_text).strip()
    if not normalized_text:
        raise ValueError("file is empty after extraction")

    relative_source = str(path.relative_to(library_dir))
    if suffix in {".md", ".markdown"}:
        title = first_heading(normalized_text, path.stem)
    else:
        title = first_non_empty_line(normalized_text, path.stem)

    return SourceDocument(
        source=relative_source,
        title=title,
        text=normalized_text,
        file_type=file_type,
    )


class TinyRAG:
    def __init__(
        self,
        library_dir: Path,
        embedding_backend: Optional[EmbeddingBackend] = None,
        reranker_backend: Optional[RerankerBackend] = None,
    ) -> None:
        self.library_dir = library_dir
        self.supported_extensions = sorted(SUPPORTED_EXTENSIONS.keys())
        self.embedding_backend = embedding_backend or build_embedding_backend()
        self.local_reranker = LocalHeuristicReranker()
        self.reranker_backend = reranker_backend or build_reranker_backend(self.local_reranker)
        self._lock = threading.RLock()
        self._snapshot = self._build_snapshot(library_dir)

    def _discover_source_files(self, library_dir: Path) -> List[Path]:
        return sorted(
            [
                path
                for path in library_dir.rglob("*")
                if path.is_file() and path.suffix.lower() in SUPPORTED_EXTENSIONS
            ],
            key=lambda path: str(path.relative_to(library_dir)),
        )

    def _build_snapshot(self, library_dir: Path) -> IndexSnapshot:
        source_files = self._discover_source_files(library_dir)
        if not source_files:
            supported = ", ".join(self.supported_extensions)
            raise FileNotFoundError(
                f"document library is empty: {library_dir} (supported: {supported})"
            )

        # Cache Check
        cache_path = ROOT / ".index_cache.pkl"
        try:
            if cache_path.exists():
                last_modified = max(p.stat().st_mtime for p in source_files)
                if cache_path.stat().st_mtime > last_modified:
                    with open(cache_path, "rb") as f:
                        cached: IndexSnapshot = pickle.load(f)
                    if (
                        cached.library_dir == library_dir
                        and cached.embedding_backend == self.embedding_backend.name
                        and cached.reranker_backend == self.reranker_backend.name
                    ):
                        return cached
        except Exception:
            pass  # Ignore cache errors

        documents: List[SourceDocument] = []
        skipped_files: List[Tuple[str, str]] = []
        chunks: List[Chunk] = []
        chunk_id = 0

        for path in source_files:
            relative_source = str(path.relative_to(library_dir))
            try:
                document = load_source_document(path, library_dir)
            except Exception as exc:
                skipped_files.append((relative_source, str(exc)))
                continue

            documents.append(document)
            for text in chunk_text(document.text):
                chunks.append(
                    Chunk(
                        chunk_id=chunk_id,
                        source=document.source,
                        title=document.title,
                        text=text,
                    )
                )
                chunk_id += 1

        if not chunks:
            raise FileNotFoundError("document library has no readable content after extraction")

        token_counters: List[Counter] = []
        document_frequencies: Counter = Counter()
        for chunk in chunks:
            counter = Counter(tokenize(chunk.text))
            token_counters.append(counter)
            document_frequencies.update(counter.keys())

        total_chunks = len(chunks)
        idf: Dict[str, float] = {}
        for token, frequency in document_frequencies.items():
            idf[token] = math.log((total_chunks + 1) / (frequency + 0.5)) + 1.0

        chunk_embeddings = tuple(self.embedding_backend.embed_texts([chunk.text for chunk in chunks]))
        chunk_token_counts = tuple(token_counters)
        chunk_title_token_sets = tuple(frozenset(tokenize(chunk.title)) for chunk in chunks)

        total_tokens = sum(sum(c.values()) for c in token_counters)
        avgdl = total_tokens / total_chunks if total_chunks else 0.0

        snapshot = IndexSnapshot(
            library_dir=library_dir,
            documents=tuple(documents),
            skipped_files=tuple(skipped_files),
            chunks=tuple(chunks),
            chunk_embeddings=chunk_embeddings,
            chunk_token_counts=chunk_token_counts,
            chunk_title_token_sets=chunk_title_token_sets,
            idf=idf,
            avgdl=avgdl,
            supported_formats=tuple(self.supported_extensions),
            embedding_backend=self.embedding_backend.name,
            reranker_backend=self.reranker_backend.name,
            retrieval_strategy="dense-embedding-cosine",
            rerank_strategy=self.reranker_backend.strategy,
        )

        try:
            with open(cache_path, "wb") as f:
                pickle.dump(snapshot, f)
        except Exception:
            pass

        return snapshot

    def _snapshot_ref(self) -> IndexSnapshot:
        with self._lock:
            return self._snapshot

    def reload(self, library_dir: Optional[Path] = None) -> None:
        target_dir = library_dir or self.library_dir
        snapshot = self._build_snapshot(target_dir)
        with self._lock:
            self.library_dir = target_dir
            self._snapshot = snapshot

    def list_documents(self) -> List[Dict[str, object]]:
        snapshot = self._snapshot_ref()
        return [
            {
                "source": document.source,
                "title": document.title,
                "file_type": document.file_type,
                "chars": len(document.text),
            }
            for document in snapshot.documents
        ]

    def stats(self) -> Dict[str, object]:
        snapshot = self._snapshot_ref()
        return {
            "library_dir": str(snapshot.library_dir),
            "documents": len(snapshot.documents),
            "chunks": len(snapshot.chunks),
            "supported_formats": list(snapshot.supported_formats),
            "files": self.list_documents(),
            "skipped": [{"source": source, "error": error} for source, error in snapshot.skipped_files],
            "embedding_backend": snapshot.embedding_backend,
            "reranker_backend": snapshot.reranker_backend,
            "retrieval_strategy": snapshot.retrieval_strategy,
            "rerank_strategy": snapshot.rerank_strategy,
        }

    @staticmethod
    def _weighted_overlap(query_tokens: Set[str], candidate_tokens: Set[str], idf: Dict[str, float]) -> float:
        if not query_tokens:
            return 0.0

        overlap = query_tokens & candidate_tokens
        if not overlap:
            return 0.0

        numerator = sum(idf.get(token, 1.0) for token in overlap)
        denominator = sum(idf.get(token, 1.0) for token in query_tokens)
        return numerator / denominator if denominator else 0.0

    @staticmethod
    def _bm25_score(
        query_tokens: Set[str],
        chunk_tokens: Dict[str, int],
        idf: Dict[str, float],
        avgdl: float,
        k1: float = 1.5,
        b: float = 0.75,
    ) -> float:
        score = 0.0
        doc_len = sum(chunk_tokens.values())
        if avgdl == 0:
            return 0.0

        for token in query_tokens:
            if token not in chunk_tokens:
                continue
            tf = chunk_tokens[token]
            idf_val = idf.get(token, 0.0)
            numerator = idf_val * tf * (k1 + 1)
            denominator = tf + k1 * (1 - b + b * doc_len / avgdl)
            score += numerator / denominator
        return score

    def search(self, query: str, top_k: int = 3) -> List[SearchHit]:
        snapshot = self._snapshot_ref()
        query_tokens = set(tokenize(query))
        if not query_tokens:
            return []

        query_embedding = self.embedding_backend.embed_query(query)
        if not any(query_embedding):
            return []

        retrieve_hits: List[Tuple[int, float]] = []
        for index, chunk_embedding in enumerate(snapshot.chunk_embeddings):
            retrieve_score = cosine_similarity(query_embedding, chunk_embedding)
            if retrieve_score > 0:
                retrieve_hits.append((index, retrieve_score))

        if not retrieve_hits:
            return []

        retrieve_hits.sort(key=lambda item: item[1], reverse=True)
        candidate_size = min(self.reranker_backend.candidate_pool_size(top_k), len(retrieve_hits))
        candidates: List[CandidateScore] = []
        for index, retrieve_score in retrieve_hits[:candidate_size]:
            candidates.append(
                CandidateScore(
                    index=index,
                    retrieve_score=retrieve_score,
                    lexical_score=self._bm25_score(
                        query_tokens, snapshot.chunk_token_counts[index], snapshot.idf, snapshot.avgdl
                    ),
                    title_score=self._weighted_overlap(
                        query_tokens, set(snapshot.chunk_title_token_sets[index]), snapshot.idf
                    ),
                    rerank_score=retrieve_score,
                    llm_score=0.0,
                )
            )

        ranked_candidates = self.reranker_backend.rerank(query, snapshot, candidates)
        hits: List[SearchHit] = []
        for candidate in ranked_candidates[:top_k]:
            hits.append(
                SearchHit(
                    chunk=snapshot.chunks[candidate.index],
                    score=candidate.rerank_score,
                    retrieve_score=candidate.retrieve_score,
                    rerank_score=candidate.rerank_score,
                    lexical_score=candidate.lexical_score,
                    title_score=candidate.title_score,
                    llm_score=candidate.llm_score,
                )
            )
        return hits

    def answer(self, query: str, top_k: int = 3) -> RagResponse:
        hits = self.search(query=query, top_k=top_k)
        if not hits:
            return RagResponse(
                query=query,
                answer_lines=["文档库里没有找到足够相关的内容，建议换个问法或者补充文档。"],
                hits=[],
            )

        query_tokens = set(tokenize(query))
        sentence_candidates: List[Tuple[float, str]] = []

        for hit in hits:
            for sentence in split_sentences(hit.chunk.text):
                if sentence.rstrip("。！？!? ").strip() == hit.chunk.title.strip():
                    continue
                sentence_tokens = set(tokenize(sentence))
                overlap = len(query_tokens & sentence_tokens)
                if overlap == 0:
                    continue
                score = hit.score * (1 + overlap / max(len(query_tokens), 1))
                sentence_candidates.append((score, sentence.strip()))

        sentence_candidates.sort(key=lambda item: item[0], reverse=True)
        best_score = sentence_candidates[0][0] if sentence_candidates else 0.0

        answer_lines: List[str] = []
        seen = set()
        for score, sentence in sentence_candidates:
            if best_score and score < best_score * 0.35:
                continue
            normalized = sentence.strip()
            if len(normalized) < 6 or normalized in seen:
                continue
            seen.add(normalized)
            answer_lines.append(normalized if normalized.endswith("。") else normalized + "。")
            if len(answer_lines) == 3:
                break

        if not answer_lines:
            fallback = hits[0].chunk.text.strip()
            answer_lines = [fallback if fallback.endswith("。") else fallback + "。"]

        return RagResponse(query=query, answer_lines=answer_lines, hits=hits)


def print_response(response: RagResponse) -> None:
    print(f"\n问题: {response.query}\n")
    print("回答:")
    for line in response.answer_lines:
        print(f"- {line}")

    if not response.hits:
        return

    print("\n检索到的上下文:")
    for index, hit in enumerate(response.hits, start=1):
        excerpt = shorten(hit.chunk.text.replace("\n", " "))
        print(
            f"[{index}] {hit.chunk.source} | score={hit.score:.3f} "
            f"(retrieve={hit.retrieve_score:.3f}, rerank={hit.rerank_score:.3f}, llm={hit.llm_score:.3f})"
        )
        print(textwrap.indent(excerpt, prefix="    "))


def print_json_response(response: RagResponse) -> None:
    print(json.dumps(response.to_dict(), ensure_ascii=False, indent=2))


def print_document_list(rag: TinyRAG) -> None:
    stats = rag.stats()
    print("Document Library")
    print("=" * 40)
    print(f"目录: {stats['library_dir']}")
    print(f"文档数: {stats['documents']} | Chunk 数: {stats['chunks']}")
    print(f"支持格式: {', '.join(stats['supported_formats'])}")
    print(f"Embedding: {stats['embedding_backend']}")
    print(f"Reranker: {stats['reranker_backend']}")
    print(f"检索链路: {stats['retrieval_strategy']} -> {stats['rerank_strategy']}")

    print("\n已入库文件:")
    for item in rag.list_documents():
        print(f"- {item['source']} | {item['file_type']} | {item['chars']} chars")

    if stats["skipped"]:
        print("\n跳过的文件:")
        for item in stats["skipped"]:
            print(f"- {item['source']} | {item['error']}")


def run_demo(rag: TinyRAG) -> None:
    documents = rag.list_documents()
    sample_queries = [item["title"] for item in documents[:3] if item.get("title")]
    if not sample_queries:
        sample_queries = ["这个文档库主要讲什么？"]

    print("Tiny RAG Demo")
    print("=" * 40)
    for query in sample_queries:
        print_response(rag.answer(query))
        print("-" * 40)


def interactive_chat(rag: TinyRAG) -> None:
    print("进入交互模式，直接输入问题即可，输入 exit 结束。\n")
    while True:
        try:
            query = input("你 > ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n已退出。")
            return
        if query.lower() in {"exit", "quit"}:
            print("已退出。")
            return
        if not query:
            continue
        print_response(rag.answer(query))
        print()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="A tiny offline RAG demo.")
    parser.add_argument("--query", "-q", help="Ask one question and print the answer.")
    parser.add_argument("--top-k", type=int, default=3, help="How many chunks to retrieve.")
    parser.add_argument("--demo", action="store_true", help="Run bundled sample queries.")
    parser.add_argument("--json", action="store_true", help="Print one query result as JSON.")
    parser.add_argument("--list-docs", action="store_true", help="List ingested documents.")
    parser.add_argument(
        "--library-dir",
        "--knowledge-dir",
        dest="library_dir",
        type=Path,
        default=DOCUMENT_LIBRARY_DIR,
        help="Directory that stores source documents.",
    )
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    rag = TinyRAG(args.library_dir)
    if args.list_docs:
        print_document_list(rag)
        return

    if args.demo:
        run_demo(rag)
        return

    if args.query:
        response = rag.answer(args.query, top_k=args.top_k)
        if args.json:
            print_json_response(response)
        else:
            print_response(response)
        return

    interactive_chat(rag)


if __name__ == "__main__":
    main()
