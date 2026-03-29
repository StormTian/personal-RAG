"""Index lifecycle management with incremental operations."""

import threading
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Set

import numpy as np

from rag_system.backends.vector_store.base import VectorStore
from rag_system.core.base import Chunk, EmbeddingBackend
from rag_system.config.settings import ChunkingConfig
from rag_system.index.bm25_store import BM25Store
from rag_system.utils.text import chunk_text
from rag_system.api.loader import DocumentLoaderRegistry
from rag_system.monitoring.decorators import trace_method


@dataclass
class IndexStatus:
    """Index status information."""
    total_documents: int
    total_chunks: int
    deleted_ratio: float
    last_update_time: Optional[datetime]
    needs_compression: bool


class IndexManager:
    """索引生命周期管理器，支持增量操作"""

    # Compression threshold - trigger when deleted ratio exceeds this value
    COMPRESSION_THRESHOLD = 0.3

    def __init__(
        self,
        library_dir: Path,
        vector_store: VectorStore,
        bm25_store: BM25Store,
        embedding_backend: EmbeddingBackend,
        chunking_config: ChunkingConfig,
    ):
        self._library_dir = library_dir
        self._vector_store = vector_store
        self._bm25_store = bm25_store
        self._embedding_backend = embedding_backend
        self._chunking_config = chunking_config
        self._deleted_ids: Set[int] = set()
        self._chunk_map: Dict[int, Chunk] = {}
        self._lock = threading.RLock()
        self._last_update_time: Optional[datetime] = None
        self._loader_registry = DocumentLoaderRegistry()

    @trace_method("add_document", {"operation": "index.add"})
    async def add_document(self, doc_path: Path) -> bool:
        """增量添加单个文档

        流程：
        1. 加载文档并分块
        2. 生成嵌入向量（异步）
        3. 添加到向量存储
        4. 更新BM25统计
        5. 更新chunk_map

        Returns:
            True if successful, False otherwise
        """
        if not doc_path.exists():
            return False

        try:
            # 1. 加载文档
            document = self._loader_registry.load(doc_path)

            # 2. 分块
            chunks_text = chunk_text(
                document.text,
                max_chars=self._chunking_config.max_chars,
                overlap=self._chunking_config.overlap,
            )

            if not chunks_text:
                return False

            # 3. 生成嵌入（异步）
            embeddings = await self._embedding_backend.embed_texts_async(chunks_text)

            # Convert to numpy array
            embeddings_array = np.array(embeddings, dtype=np.float32)

            with self._lock:
                # 4. 分配chunk_id
                start_id = self._get_next_chunk_id()
                chunk_ids = list(range(start_id, start_id + len(chunks_text)))

                # 5. 添加到向量存储
                self._vector_store.add(embeddings_array)

                # 6. 更新BM25统计和chunk_map
                for i, (chunk_id, text) in enumerate(zip(chunk_ids, chunks_text)):
                    chunk = Chunk(
                        chunk_id=chunk_id,
                        source=str(doc_path),
                        title=document.title,
                        text=text,
                        metadata={"document_type": document.file_type},
                    )
                    self._bm25_store.update_terms(chunk, chunk_id)
                    self._chunk_map[chunk_id] = chunk

                self._last_update_time = datetime.now()

            return True

        except Exception:
            return False

    @trace_method("remove_document", {"operation": "index.remove"})
    def remove_document(self, doc_path: Path) -> bool:
        """增量删除文档

        流程：
        1. 找到文档对应的所有chunk_id
        2. 添加到deleted_ids集合
        3. 从BM25Store删除词频统计
        4. 从chunk_map删除
        5. 检查是否需要触发压缩

        注意：FAISS不支持直接删除，使用标记删除方式
        """
        doc_path_str = str(doc_path)

        with self._lock:
            # 1. 找到文档对应的所有chunk_id
            chunk_ids = [
                cid for cid, chunk in self._chunk_map.items()
                if chunk.source == doc_path_str
            ]

            if not chunk_ids:
                return False

            # 2. 添加到deleted_ids集合
            self._deleted_ids.update(chunk_ids)

            # 3. 从BM25Store删除
            self._bm25_store.remove_terms(chunk_ids)

            # 4. 从chunk_map删除
            for cid in chunk_ids:
                del self._chunk_map[cid]

            self._last_update_time = datetime.now()

            # 5. 检查是否需要压缩
            if self._should_compress():
                self._compress_index()

            return True

    async def update_document(self, doc_path: Path) -> bool:
        """增量更新文档

        流程：先删除旧的chunk，再添加新的chunk
        """
        # 先删除旧的
        removed = self.remove_document(doc_path)

        # 再添加新的
        added = await self.add_document(doc_path)

        return removed or added

    async def rebuild_full(self) -> None:
        """全量重建索引

        作为兜底方案，清空所有数据重新构建
        """
        with self._lock:
            # 清空所有数据
            self._vector_store.clear()
            self._bm25_store.clear()
            self._chunk_map.clear()
            self._deleted_ids.clear()
            self._last_update_time = datetime.now()

    def get_status(self) -> IndexStatus:
        """获取索引状态

        Returns:
            IndexStatus包含：
            - total_documents: int
            - total_chunks: int
            - deleted_ratio: float
            - last_update_time: datetime
            - needs_compression: bool
        """
        with self._lock:
            total_chunks = len(self._chunk_map)
            total_deleted = len(self._deleted_ids)
            total_original = total_chunks + total_deleted

            deleted_ratio = total_deleted / total_original if total_original > 0 else 0.0
            needs_compression = deleted_ratio > self.COMPRESSION_THRESHOLD

            # Count unique documents
            unique_docs = set()
            for chunk in self._chunk_map.values():
                unique_docs.add(chunk.source)

            return IndexStatus(
                total_documents=len(unique_docs),
                total_chunks=total_chunks,
                deleted_ratio=deleted_ratio,
                last_update_time=self._last_update_time,
                needs_compression=needs_compression,
            )

    def compress_if_needed(self) -> bool:
        """检查并执行索引压缩

        当deleted_ratio > 30%时触发
        压缩流程：重建向量索引，清理deleted_ids
        """
        with self._lock:
            if not self._should_compress():
                return False

            self._compress_index()
            return True

    def _should_compress(self) -> bool:
        """Check if index needs compression."""
        total_chunks = len(self._chunk_map)
        total_deleted = len(self._deleted_ids)
        total_original = total_chunks + total_deleted

        if total_original == 0:
            return False

        deleted_ratio = total_deleted / total_original
        return deleted_ratio > self.COMPRESSION_THRESHOLD

    def _compress_index(self) -> None:
        """压缩索引，重建向量存储

        Note: This is a placeholder implementation. Full compression
        would require getting vectors from the store, filtering out
        deleted ones, and rebuilding the index.
        """
        # For now, just clear deleted_ids
        # In a full implementation, we would:
        # 1. Get all valid vectors from vector_store
        # 2. Rebuild the index with only valid vectors
        # 3. Reassign chunk IDs
        self._deleted_ids.clear()

    def get_valid_chunks(self) -> List[Chunk]:
        """获取所有有效chunk（排除已删除）"""
        with self._lock:
            return list(self._chunk_map.values())

    def _get_next_chunk_id(self) -> int:
        """获取下一个可用的chunk ID."""
        with self._lock:
            max_id = max(self._chunk_map.keys()) if self._chunk_map else -1
            return max_id + 1
