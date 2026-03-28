"""BM25 statistics persistence storage."""

import gzip
import math
import pickle
import threading
from pathlib import Path
from typing import Dict, List

from rag_system.core.base import Chunk
from rag_system.utils.text import tokenize


class BM25Store:
    """BM25统计信息存储"""

    def __init__(self, cache_dir: Path, k1: float = 1.5, b: float = 0.75):
        self._cache_dir = cache_dir
        self._k1 = k1
        self._b = b

        # 统计数据
        self._term_freq: Dict[str, Dict[int, int]] = {}  # {term: {chunk_id: freq}}
        self._doc_freq: Dict[str, int] = {}  # {term: doc_freq}
        self._doc_length: Dict[int, int] = {}  # {chunk_id: length}
        self._avg_doc_length: float = 0.0
        self._total_docs: int = 0

        self._lock = threading.RLock()

    def update_terms(self, chunk: Chunk, chunk_id: int) -> None:
        """更新词频统计

        流程：
        1. 分词
        2. 计算词频
        3. 更新term_freq和doc_freq
        4. 更新doc_length和avg_doc_length
        """
        with self._lock:
            # 1. 分词
            tokens = tokenize(chunk.text)

            # 2. 计算词频
            term_counts: Dict[str, int] = {}
            for term in tokens:
                term_counts[term] = term_counts.get(term, 0) + 1

            # 3. 更新term_freq
            for term, freq in term_counts.items():
                if term not in self._term_freq:
                    self._term_freq[term] = {}
                self._term_freq[term][chunk_id] = freq

                # 更新doc_freq
                self._doc_freq[term] = self._doc_freq.get(term, 0) + 1

            # 4. 更新doc_length和统计信息
            doc_len = len(tokens)
            self._doc_length[chunk_id] = doc_len
            self._total_docs += 1

            # 重新计算avg_doc_length
            if self._total_docs > 0:
                total_len = sum(self._doc_length.values())
                self._avg_doc_length = total_len / self._total_docs

    def remove_terms(self, chunk_ids: List[int]) -> None:
        """删除词频统计

        流程：
        1. 从term_freq中删除对应chunk_id的记录
        2. 更新doc_freq（减少计数）
        3. 从doc_length中删除
        4. 重新计算avg_doc_length
        """
        with self._lock:
            for chunk_id in chunk_ids:
                if chunk_id not in self._doc_length:
                    continue

                # 1 & 2. 从term_freq中删除并更新doc_freq
                terms_to_remove = []
                for term, freq_map in self._term_freq.items():
                    if chunk_id in freq_map:
                        del freq_map[chunk_id]
                        self._doc_freq[term] -= 1
                        if self._doc_freq[term] <= 0:
                            del self._doc_freq[term]
                        if not freq_map:
                            terms_to_remove.append(term)

                # 清理空的term
                for term in terms_to_remove:
                    del self._term_freq[term]

                # 3. 从doc_length中删除
                del self._doc_length[chunk_id]
                self._total_docs -= 1

            # 4. 重新计算avg_doc_length
            if self._total_docs > 0:
                total_len = sum(self._doc_length.values())
                self._avg_doc_length = total_len / self._total_docs
            else:
                self._avg_doc_length = 0.0

    def get_bm25_score(self, query: str, chunk_id: int) -> float:
        """计算BM25分数

        公式：
        score = sum(
            IDF(term) * (freq * (k1 + 1)) / (freq + k1 * (1 - b + b * doc_length / avg_doc_length))
        )

        其中：
        IDF(term) = log((N - n + 0.5) / (n + 0.5) + 1)
        N = total_docs
        n = doc_freq[term]
        freq = term_freq[term][chunk_id]
        """
        with self._lock:
            # 分词
            query_terms = tokenize(query)

            if chunk_id not in self._doc_length:
                return 0.0

            doc_len = self._doc_length[chunk_id]
            score = 0.0

            for term in query_terms:
                if term not in self._doc_freq:
                    continue

                # IDF计算
                n = self._doc_freq[term]
                N = self._total_docs
                idf = math.log((N - n + 0.5) / (n + 0.5) + 1)

                # 词频
                freq = self._term_freq.get(term, {}).get(chunk_id, 0)
                if freq == 0:
                    continue

                # BM25公式
                numerator = freq * (self._k1 + 1)
                denominator = freq + self._k1 * (
                    1 - self._b + self._b * doc_len / self._avg_doc_length
                )

                score += idf * numerator / denominator

            return score

    def save(self) -> None:
        """持久化到磁盘"""
        self._cache_dir.mkdir(parents=True, exist_ok=True)

        with self._lock:
            data = {
                "term_freq": self._term_freq,
                "doc_freq": self._doc_freq,
                "doc_length": self._doc_length,
                "avg_doc_length": self._avg_doc_length,
                "total_docs": self._total_docs,
                "k1": self._k1,
                "b": self._b,
            }

        # 保存到单个文件
        cache_file = self._cache_dir / "bm25_stats.pkl.gz"
        with gzip.open(cache_file, "wb") as f:
            pickle.dump(data, f)

    def load(self) -> bool:
        """从磁盘加载"""
        cache_file = self._cache_dir / "bm25_stats.pkl.gz"

        if not cache_file.exists():
            return False

        try:
            with gzip.open(cache_file, "rb") as f:
                data = pickle.load(f)

            with self._lock:
                self._term_freq = data["term_freq"]
                self._doc_freq = data["doc_freq"]
                self._doc_length = data["doc_length"]
                self._avg_doc_length = data["avg_doc_length"]
                self._total_docs = data["total_docs"]
                self._k1 = data.get("k1", 1.5)
                self._b = data.get("b", 0.75)

            return True
        except (EOFError, pickle.UnpicklingError, KeyError):
            return False

    def clear(self) -> None:
        """清空所有统计"""
        with self._lock:
            self._term_freq.clear()
            self._doc_freq.clear()
            self._doc_length.clear()
            self._avg_doc_length = 0.0
            self._total_docs = 0
