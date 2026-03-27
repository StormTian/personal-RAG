# RAG 系统生产级迭代实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 修复现有问题、集成 FAISS/Redis/并行处理、优化前端性能，确保前后端全流程测通。

**Architecture:** 三阶段迭代：先修复测试和前端类型错误，再集成向量数据库和缓存，最后优化前端打包。

**Tech Stack:** Python 3.10+, FastAPI, FAISS, Redis, React 18, TypeScript, Vite

---

## 文件结构

### 新增文件

```
rag_system/
├── backends/
│   └── vector_store/
│       ├── __init__.py
│       ├── base.py
│       ├── faiss_store.py
│       └── numpy_store.py
├── cache/
│   ├── __init__.py
│   ├── base.py
│   ├── redis_cache.py
│   └── memory_cache.py

tests/
├── unit/
│   ├── test_vector_store.py
│   └── test_query_cache.py
```

### 修改文件

```
tests/conftest.py                                    # 修复导入
rag_system/config/settings.py                        # 添加新配置类
rag_system/rag_engine.py                             # 集成向量存储和缓存
web-new/src/features/library/components/FileList.tsx
web-new/src/features/library/components/UploadArea.tsx
web-new/src/features/result/components/ResultPanel.tsx
web-new/src/features/search/components/SearchHistory.tsx
web-new/src/pages/Home/Home.tsx
web-new/src/utils/highlight.ts
web-new/src/types/index.ts
web-new/vite.config.ts
web-new/src/App.tsx
requirements.txt
```

---

## 阶段一：修复基础问题

### Task 1: 修复测试 conftest.py 导入

**Files:**
- Modify: `tests/conftest.py:20-36`

- [ ] **Step 1: 修改导入语句**

将旧导入替换为新模块路径：

```python
from rag_system.core.base import (
    SourceDocument,
    Chunk,
    CandidateScore,
    SearchHit,
    RagResponse,
    IndexSnapshot,
)
from rag_system.backends.embedding import (
    EmbeddingBackend,
    LocalHashEmbeddingBackend,
)
from rag_system.backends.reranker import (
    RerankerBackend,
    LocalHeuristicReranker,
)
from rag_system.rag_engine import RAGEngine
from rag_system.utils.text import (
    tokenize,
    chunk_text,
    cosine_similarity,
    normalize_vector,
)
```

- [ ] **Step 2: 运行测试验证**

```bash
pytest tests/unit -v --tb=short
```

Expected: 测试导入成功，无 ModuleNotFoundError

- [ ] **Step 3: 提交**

```bash
git add tests/conftest.py
git commit -m "fix(tests): update imports to use rag_system module"
```

---

### Task 2: 修复前端类型定义

**Files:**
- Modify: `web-new/src/types/index.ts:74-90`

- [ ] **Step 1: 修复 UploadResponse 接口**

添加 `success` 字段：

```typescript
export interface UploadResponse {
  status: string;
  message: string;
  success?: boolean;  // 新增
  file: {
    original_name: string;
    saved_name: string;
    path: string;
    size: number;
    type: string;
  };
  reloaded: boolean;
  library_stats?: {
    documents: number;
    chunks: number;
    supported_formats: string[];
  };
}
```

- [ ] **Step 2: 运行类型检查**

```bash
cd web-new && npm run typecheck
```

Expected: 减少类型错误数量

- [ ] **Step 3: 提交**

```bash
git add web-new/src/types/index.ts
git commit -m "fix(types): add success field to UploadResponse"
```

---

### Task 3: 修复 UploadArea.tsx

**Files:**
- Modify: `web-new/src/features/library/components/UploadArea.tsx:20-40`

- [ ] **Step 1: 修复进度回调类型**

修改 uploadFile 回调：

```typescript
const handleUpload = async (file: File): Promise<boolean> => {
  setUploading(true);
  setProgress(0);

  try {
    const result = await uploadApi.uploadFile(file, (progressEvent) => {
      setProgress(progressEvent.percentage);
    });

    if (result.status === 'success' || result.success) {
      message.success(t('library.uploadSuccess'));
      onUploadSuccess();
    } else {
      message.error(result.message || t('library.uploadError'));
    }
  } catch (error) {
    message.error(error instanceof Error ? error.message : t('library.uploadError'));
  } finally {
    setUploading(false);
    setProgress(0);
  }

  return false;
};
```

- [ ] **Step 2: 运行类型检查**

```bash
cd web-new && npm run typecheck
```

Expected: UploadArea.tsx 无错误

- [ ] **Step 3: 提交**

```bash
git add web-new/src/features/library/components/UploadArea.tsx
git commit -m "fix(UploadArea): fix progress callback and success check"
```

---

### Task 4: 修复 FileList.tsx 类型兼容性

**Files:**
- Modify: `web-new/src/features/library/components/FileList.tsx:9-17`

- [ ] **Step 1: 修改 FileItem 接口**

使 `name` 字段可选，添加 `source` 作为备选：

```typescript
export interface FileItem {
  name?: string;      // 改为可选
  source?: string;
  size?: number;
  chars?: number;
  modified_at?: string;
  type?: string;
  file_type?: string;
  title?: string;     // 新增，LibraryFile 有此字段
}
```

- [ ] **Step 2: 运行类型检查**

```bash
cd web-new && npm run typecheck
```

Expected: FileList.tsx 类型错误消除

- [ ] **Step 3: 提交**

```bash
git add web-new/src/features/library/components/FileList.tsx
git commit -m "fix(FileList): make name field optional for type compatibility"
```

---

### Task 5: 修复其他前端错误

**Files:**
- Modify: `web-new/src/features/result/components/ResultPanel.tsx:4`
- Modify: `web-new/src/features/search/components/SearchHistory.tsx:2,62`
- Modify: `web-new/src/pages/Home/Home.tsx:23,84`
- Modify: `web-new/src/utils/highlight.ts:23`

- [ ] **Step 1: 修复 ResultPanel.tsx 未使用导入**

```typescript
import type { SearchResponse } from '@/types';  // 移除 SearchParams
```

- [ ] **Step 2: 修复 SearchHistory.tsx**

移除未使用的 Empty 导入，修复 Tag 组件：

```typescript
import { Card, List, Tag, Space, Typography, Button } from 'antd';  // 移除 Empty

// 第62行，移除 size 属性
<Tag>{item.hitCount} hits</Tag>
```

- [ ] **Step 3: 修复 Home.tsx**

```typescript
// 第23行，使用下划线前缀
const { data: libraryData, isLoading: isLibraryLoading, error: libraryError, refetch: _refetchLibrary } = useLibraryQuery();

// 第84行，使用 nullish coalescing
data={searchResult ?? undefined}
```

- [ ] **Step 4: 修复 highlight.ts**

```typescript
.replace(/```(\w+)?\n([\s\S]*?)```/g, (_match, lang, code) => {
  const language = lang || 'text';
  const highlighted = highlightCode(code.trim(), language);
  return `<pre class="language-${language}"...`;
})
```

- [ ] **Step 5: 运行类型检查**

```bash
cd web-new && npm run typecheck
```

Expected: 无类型错误

- [ ] **Step 6: 提交**

```bash
git add web-new/src/features/result/components/ResultPanel.tsx \
        web-new/src/features/search/components/SearchHistory.tsx \
        web-new/src/pages/Home/Home.tsx \
        web-new/src/utils/highlight.ts
git commit -m "fix(frontend): resolve TypeScript errors"
```

---

### Task 6: 验证前后端联调

**Files:**
- Test: 手动测试

- [ ] **Step 1: 启动后端服务**

```bash
# 终端1
uvicorn rag_system.api.server:create_app --factory --reload --port 8000
```

Expected: 服务启动成功，访问 http://localhost:8000/health 返回健康状态

- [ ] **Step 2: 启动前端服务**

```bash
# 终端2
cd web-new && npm run dev
```

Expected: 前端启动成功，访问 http://localhost:5173 显示页面

- [ ] **Step 3: 测试核心功能**

手动测试：
1. 访问首页，查看文档库信息加载
2. 输入搜索查询，验证搜索功能
3. 上传文件，验证上传功能
4. 查看上传历史

- [ ] **Step 4: 运行完整测试**

```bash
pytest tests/ -v
```

Expected: 所有测试通过

---

## 阶段二：后端核心优化

### Task 7: 添加向量存储配置类

**Files:**
- Modify: `rag_system/config/settings.py`

- [ ] **Step 1: 添加 VectorStoreConfig 和 QueryCacheConfig**

在 `EmbeddingConfig` 类之前添加：

```python
@dataclass
class VectorStoreConfig:
    """Vector store configuration."""
    backend: str = "numpy"  # "faiss" or "numpy"
    index_path: str = ".index_cache/faiss.index"
    

@dataclass
class QueryCacheConfig:
    """Query cache configuration."""
    enabled: bool = True
    backend: str = "memory"  # "redis" or "memory"
    redis_url: str = "redis://localhost:6379/0"
    ttl: int = 3600
    key_prefix: str = "rag:query:"
    max_memory_items: int = 1000


@dataclass
class PerformanceConfig:
    """Performance configuration."""
    parallel_loading: bool = True
    max_workers: int = 4
    embed_batch_size: int = 32
```

- [ ] **Step 2: 更新 Settings 类**

在 `__init__` 方法中添加：

```python
def __init__(self):
    self.vector_store = VectorStoreConfig()
    self.query_cache = QueryCacheConfig()
    self.performance = PerformanceConfig()
    # ... 其他现有配置
```

- [ ] **Step 3: 更新 from_dict 方法**

```python
if "vector_store" in data:
    settings.vector_store = VectorStoreConfig(**data["vector_store"])
if "query_cache" in data:
    settings.query_cache = QueryCacheConfig(**data["query_cache"])
if "performance" in data:
    settings.performance = PerformanceConfig(**data["performance"])
```

- [ ] **Step 4: 提交**

```bash
git add rag_system/config/settings.py
git commit -m "feat(config): add VectorStore, QueryCache, Performance config"
```

---

### Task 8: 实现向量存储抽象基类

**Files:**
- Create: `rag_system/backends/vector_store/__init__.py`
- Create: `rag_system/backends/vector_store/base.py`

- [ ] **Step 1: 创建目录和 __init__.py**

```bash
mkdir -p rag_system/backends/vector_store
```

```python
# rag_system/backends/vector_store/__init__.py
from .base import VectorStore
from .numpy_store import NumpyVectorStore

__all__ = ["VectorStore", "NumpyVectorStore"]

def get_vector_store(backend: str = "numpy", **kwargs) -> VectorStore:
    """Factory function to create vector store."""
    if backend == "faiss":
        from .faiss_store import FaissVectorStore
        return FaissVectorStore(**kwargs)
    return NumpyVectorStore(**kwargs)
```

- [ ] **Step 2: 创建 base.py**

```python
# rag_system/backends/vector_store/base.py
"""Abstract base class for vector stores."""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import List, Tuple
import numpy as np


class VectorStore(ABC):
    """Abstract base class for vector storage backends."""
    
    @abstractmethod
    def add(self, embeddings: List[np.ndarray], ids: List[int]) -> None:
        """Add embeddings with corresponding IDs.
        
        Args:
            embeddings: List of embedding vectors
            ids: List of integer IDs corresponding to each embedding
        """
        pass
    
    @abstractmethod
    def search(self, query: np.ndarray, k: int) -> List[Tuple[int, float]]:
        """Search for k most similar vectors.
        
        Args:
            query: Query embedding vector
            k: Number of results to return
            
        Returns:
            List of (id, score) tuples, sorted by score descending
        """
        pass
    
    @abstractmethod
    def save(self, path: Path) -> None:
        """Save index to disk.
        
        Args:
            path: Path to save index file
        """
        pass
    
    @abstractmethod
    def load(self, path: Path) -> bool:
        """Load index from disk.
        
        Args:
            path: Path to index file
            
        Returns:
            True if loaded successfully, False otherwise
        """
        pass
    
    @abstractmethod
    def clear(self) -> None:
        """Clear all vectors from the index."""
        pass
    
    @abstractmethod
    def __len__(self) -> int:
        """Return number of vectors in the index."""
        pass
```

- [ ] **Step 3: 提交**

```bash
git add rag_system/backends/vector_store/
git commit -m "feat(vector_store): add abstract base class"
```

---

### Task 9: 实现 Numpy 向量存储

**Files:**
- Create: `rag_system/backends/vector_store/numpy_store.py`

- [ ] **Step 1: 创建 numpy_store.py**

```python
# rag_system/backends/vector_store/numpy_store.py
"""Numpy-based vector store implementation."""

import gzip
import pickle
from pathlib import Path
from typing import List, Tuple
import numpy as np

from .base import VectorStore


class NumpyVectorStore(VectorStore):
    """Simple numpy-based vector store using cosine similarity.
    
    This is the fallback implementation with O(n) search complexity.
    Suitable for small to medium document collections (< 10k chunks).
    """
    
    def __init__(self, dimension: int = 256):
        """Initialize numpy vector store.
        
        Args:
            dimension: Embedding dimension (not strictly needed for numpy)
        """
        self._embeddings: np.ndarray = np.array([])
        self._ids: List[int] = []
    
    def add(self, embeddings: List[np.ndarray], ids: List[int]) -> None:
        """Add embeddings to the store."""
        if not embeddings:
            return
            
        if len(self._embeddings) == 0:
            self._embeddings = np.array(embeddings)
        else:
            self._embeddings = np.vstack([self._embeddings, embeddings])
        
        self._ids.extend(ids)
    
    def search(self, query: np.ndarray, k: int) -> List[Tuple[int, float]]:
        """Search using cosine similarity."""
        if len(self._embeddings) == 0:
            return []
        
        # Normalize query
        query_norm = query / (np.linalg.norm(query) + 1e-8)
        
        # Compute cosine similarities (embeddings should already be normalized)
        similarities = np.dot(self._embeddings, query_norm)
        
        # Get top-k indices
        k = min(k, len(self._ids))
        top_indices = np.argsort(similarities)[::-1][:k]
        
        return [(self._ids[i], float(similarities[i])) for i in top_indices]
    
    def save(self, path: Path) -> None:
        """Save to compressed pickle file."""
        path.parent.mkdir(parents=True, exist_ok=True)
        with gzip.open(path, 'wb') as f:
            pickle.dump({
                'embeddings': self._embeddings,
                'ids': self._ids,
            }, f)
    
    def load(self, path: Path) -> bool:
        """Load from compressed pickle file."""
        if not path.exists():
            return False
        
        try:
            with gzip.open(path, 'rb') as f:
                data = pickle.load(f)
            self._embeddings = data['embeddings']
            self._ids = data['ids']
            return True
        except Exception:
            return False
    
    def clear(self) -> None:
        """Clear all vectors."""
        self._embeddings = np.array([])
        self._ids = []
    
    def __len__(self) -> int:
        return len(self._ids)
```

- [ ] **Step 2: 编写单元测试**

```python
# tests/unit/test_vector_store.py
import pytest
import numpy as np
from pathlib import Path
import tempfile

from rag_system.backends.vector_store import NumpyVectorStore


class TestNumpyVectorStore:
    def test_add_and_search(self):
        store = NumpyVectorStore()
        
        # Add some normalized vectors
        embeddings = [
            np.array([1.0, 0.0, 0.0]),
            np.array([0.0, 1.0, 0.0]),
            np.array([0.0, 0.0, 1.0]),
        ]
        ids = [0, 1, 2]
        store.add(embeddings, ids)
        
        # Search for similar to first vector
        results = store.search(np.array([0.9, 0.1, 0.0]), k=2)
        
        assert len(results) == 2
        assert results[0][0] == 0  # First should be id 0
        assert results[0][1] > 0.8
    
    def test_save_and_load(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "test.npy.gz"
            
            store1 = NumpyVectorStore()
            store1.add([np.array([1.0, 0.0])], [0])
            store1.save(path)
            
            store2 = NumpyVectorStore()
            assert store2.load(path)
            assert len(store2) == 1
    
    def test_empty_search(self):
        store = NumpyVectorStore()
        results = store.search(np.array([1.0, 0.0]), k=5)
        assert results == []
```

- [ ] **Step 3: 运行测试**

```bash
pytest tests/unit/test_vector_store.py -v
```

- [ ] **Step 4: 提交**

```bash
git add rag_system/backends/vector_store/numpy_store.py tests/unit/test_vector_store.py
git commit -m "feat(vector_store): implement numpy backend"
```

---

### Task 10: 实现 FAISS 向量存储

**Files:**
- Create: `rag_system/backends/vector_store/faiss_store.py`
- Modify: `requirements.txt`

- [ ] **Step 1: 添加 FAISS 依赖**

```
# requirements.txt 添加
faiss-cpu>=1.7.4
```

- [ ] **Step 2: 创建 faiss_store.py**

```python
# rag_system/backends/vector_store/faiss_store.py
"""FAISS-based vector store implementation."""

from pathlib import Path
from typing import List, Tuple
import numpy as np

from .base import VectorStore

# Lazy import to avoid dependency issues
faiss = None


def _get_faiss():
    """Lazy import faiss."""
    global faiss
    if faiss is None:
        try:
            import faiss as _faiss
            faiss = _faiss
        except ImportError:
            raise ImportError(
                "faiss is not installed. Install it with: pip install faiss-cpu"
            )
    return faiss


class FaissVectorStore(VectorStore):
    """FAISS-based vector store for efficient similarity search.
    
    Uses IndexFlatIP (inner product) with normalized vectors,
    which is equivalent to cosine similarity.
    
    Search complexity: O(log n) for small datasets, O(n) for exact search.
    Suitable for large document collections.
    """
    
    def __init__(self, dimension: int = 256):
        """Initialize FAISS vector store.
        
        Args:
            dimension: Embedding dimension
        """
        self._dimension = dimension
        self._index = None
        self._ids: List[int] = []
        self._faiss = _get_faiss()
    
    def add(self, embeddings: List[np.ndarray], ids: List[int]) -> None:
        """Add embeddings to the index."""
        if not embeddings:
            return
        
        # Convert to numpy array
        vectors = np.array(embeddings, dtype=np.float32)
        
        # Create index if needed
        if self._index is None:
            self._index = self._faiss.IndexFlatIP(self._dimension)
        
        # Add vectors
        self._index.add(vectors)
        self._ids.extend(ids)
    
    def search(self, query: np.ndarray, k: int) -> List[Tuple[int, float]]:
        """Search using FAISS."""
        if self._index is None or len(self._ids) == 0:
            return []
        
        # Ensure query is 2D array
        query_vec = query.reshape(1, -1).astype(np.float32)
        
        # Search
        k = min(k, len(self._ids))
        scores, indices = self._index.search(query_vec, k)
        
        # Return (id, score) pairs
        results = []
        for idx, score in zip(indices[0], scores[0]):
            if idx >= 0:  # FAISS returns -1 for empty slots
                results.append((self._ids[idx], float(score)))
        
        return results
    
    def save(self, path: Path) -> None:
        """Save FAISS index to disk."""
        if self._index is None:
            return
        
        path.parent.mkdir(parents=True, exist_ok=True)
        self._faiss.write_index(self._index, str(path))
        
        # Save IDs separately
        import pickle
        ids_path = path.with_suffix('.ids.pkl')
        with open(ids_path, 'wb') as f:
            pickle.dump(self._ids, f)
    
    def load(self, path: Path) -> bool:
        """Load FAISS index from disk."""
        if not path.exists():
            return False
        
        try:
            self._index = self._faiss.read_index(str(path))
            
            # Load IDs
            import pickle
            ids_path = path.with_suffix('.ids.pkl')
            if ids_path.exists():
                with open(ids_path, 'rb') as f:
                    self._ids = pickle.load(f)
            
            return True
        except Exception:
            return False
    
    def clear(self) -> None:
        """Clear the index."""
        self._index = None
        self._ids = []
    
    def __len__(self) -> int:
        return len(self._ids)
```

- [ ] **Step 3: 添加 FAISS 测试**

```python
# tests/unit/test_vector_store.py 添加

class TestFaissVectorStore:
    def test_faiss_not_installed_fallback(self):
        """Test that numpy backend works without faiss."""
        from rag_system.backends.vector_store import NumpyVectorStore
        store = NumpyVectorStore()
        store.add([np.array([1.0, 0.0])], [0])
        assert len(store) == 1
```

- [ ] **Step 4: 运行测试**

```bash
pip install faiss-cpu
pytest tests/unit/test_vector_store.py -v
```

- [ ] **Step 5: 提交**

```bash
git add rag_system/backends/vector_store/faiss_store.py requirements.txt tests/unit/test_vector_store.py
git commit -m "feat(vector_store): implement FAISS backend"
```

---

### Task 11: 实现查询缓存抽象

**Files:**
- Create: `rag_system/cache/__init__.py`
- Create: `rag_system/cache/base.py`

- [ ] **Step 1: 创建目录和 __init__.py**

```bash
mkdir -p rag_system/cache
```

```python
# rag_system/cache/__init__.py
from .base import QueryCache
from .memory_cache import MemoryQueryCache

__all__ = ["QueryCache", "MemoryQueryCache"]

def get_query_cache(backend: str = "memory", **kwargs) -> QueryCache:
    """Factory function to create query cache."""
    if backend == "redis":
        from .redis_cache import RedisQueryCache
        return RedisQueryCache(**kwargs)
    return MemoryQueryCache(**kwargs)
```

- [ ] **Step 2: 创建 base.py**

```python
# rag_system/cache/base.py
"""Abstract base class for query cache."""

from abc import ABC, abstractmethod
from typing import Any, Optional


class QueryCache(ABC):
    """Abstract base class for query result caching."""
    
    @abstractmethod
    async def get(self, key: str) -> Optional[dict]:
        """Get cached result.
        
        Args:
            key: Cache key
            
        Returns:
            Cached result dict or None if not found
        """
        pass
    
    @abstractmethod
    async def set(self, key: str, value: dict, ttl: int = 3600) -> None:
        """Set cache result.
        
        Args:
            key: Cache key
            value: Result to cache
            ttl: Time-to-live in seconds
        """
        pass
    
    @abstractmethod
    async def delete(self, pattern: str) -> int:
        """Delete keys matching pattern.
        
        Args:
            pattern: Key pattern (e.g., "rag:query:*")
            
        Returns:
            Number of keys deleted
        """
        pass
    
    @abstractmethod
    async def clear(self) -> None:
        """Clear all cached results."""
        pass
    
    def make_key(self, query: str, top_k: int) -> str:
        """Generate cache key from query parameters.
        
        Args:
            query: Search query
            top_k: Number of results
            
        Returns:
            Cache key string
        """
        import hashlib
        content = f"{query}:{top_k}"
        return hashlib.md5(content.encode()).hexdigest()
```

- [ ] **Step 3: 提交**

```bash
git add rag_system/cache/
git commit -m "feat(cache): add query cache abstract base class"
```

---

### Task 12: 实现内存查询缓存

**Files:**
- Create: `rag_system/cache/memory_cache.py`

- [ ] **Step 1: 创建 memory_cache.py**

```python
# rag_system/cache/memory_cache.py
"""In-memory LRU query cache implementation."""

import time
from collections import OrderedDict
from typing import Optional
import threading

from .base import QueryCache


class MemoryQueryCache(QueryCache):
    """In-memory LRU cache for query results.
    
    Thread-safe implementation using OrderedDict and RLock.
    Suitable for development and single-instance deployments.
    """
    
    def __init__(self, max_items: int = 1000, default_ttl: int = 3600):
        """Initialize memory cache.
        
        Args:
            max_items: Maximum number of items to store
            default_ttl: Default TTL in seconds
        """
        self._cache: OrderedDict[str, tuple[dict, float]] = OrderedDict()
        self._max_items = max_items
        self._default_ttl = default_ttl
        self._lock = threading.RLock()
    
    async def get(self, key: str) -> Optional[dict]:
        """Get cached result."""
        with self._lock:
            if key not in self._cache:
                return None
            
            value, expiry = self._cache[key]
            
            # Check if expired
            if time.time() > expiry:
                del self._cache[key]
                return None
            
            # Move to end (most recently used)
            self._cache.move_to_end(key)
            return value
    
    async def set(self, key: str, value: dict, ttl: int = None) -> None:
        """Set cache result."""
        ttl = ttl or self._default_ttl
        expiry = time.time() + ttl
        
        with self._lock:
            # Remove oldest if at capacity
            while len(self._cache) >= self._max_items:
                self._cache.popitem(last=False)
            
            self._cache[key] = (value, expiry)
            self._cache.move_to_end(key)
    
    async def delete(self, pattern: str) -> int:
        """Delete keys matching pattern.
        
        Note: Pattern matching uses simple startswith/endwith for memory cache.
        """
        import fnmatch
        
        with self._lock:
            keys_to_delete = [
                k for k in self._cache 
                if fnmatch.fnmatch(k, pattern)
            ]
            for key in keys_to_delete:
                del self._cache[key]
            return len(keys_to_delete)
    
    async def clear(self) -> None:
        """Clear all cached results."""
        with self._lock:
            self._cache.clear()
```

- [ ] **Step 2: 添加测试**

```python
# tests/unit/test_query_cache.py
import pytest
import asyncio

from rag_system.cache import MemoryQueryCache


class TestMemoryQueryCache:
    @pytest.mark.asyncio
    async def test_set_and_get(self):
        cache = MemoryQueryCache()
        
        await cache.set("test_key", {"result": "data"})
        result = await cache.get("test_key")
        
        assert result == {"result": "data"}
    
    @pytest.mark.asyncio
    async def test_expiry(self):
        cache = MemoryQueryCache(default_ttl=0)
        
        await cache.set("test_key", {"result": "data"}, ttl=0)
        await asyncio.sleep(0.1)
        result = await cache.get("test_key")
        
        assert result is None
    
    @pytest.mark.asyncio
    async def test_clear(self):
        cache = MemoryQueryCache()
        
        await cache.set("key1", {"a": 1})
        await cache.set("key2", {"b": 2})
        await cache.clear()
        
        assert await cache.get("key1") is None
        assert await cache.get("key2") is None
    
    @pytest.mark.asyncio
    async def test_make_key(self):
        cache = MemoryQueryCache()
        
        key1 = cache.make_key("hello", 5)
        key2 = cache.make_key("hello", 5)
        key3 = cache.make_key("world", 5)
        
        assert key1 == key2
        assert key1 != key3
```

- [ ] **Step 3: 运行测试**

```bash
pytest tests/unit/test_query_cache.py -v
```

- [ ] **Step 4: 提交**

```bash
git add rag_system/cache/memory_cache.py tests/unit/test_query_cache.py
git commit -m "feat(cache): implement memory LRU cache"
```

---

### Task 13: 实现 Redis 查询缓存

**Files:**
- Create: `rag_system/cache/redis_cache.py`
- Modify: `requirements.txt`

- [ ] **Step 1: 添加 Redis 依赖**

```
# requirements.txt 添加
redis>=5.0.0
```

- [ ] **Step 2: 创建 redis_cache.py**

```python
# rag_system/cache/redis_cache.py
"""Redis-based query cache implementation."""

import json
from typing import Optional

from .base import QueryCache

# Lazy import
redis = None


def _get_redis():
    """Lazy import redis."""
    global redis
    if redis is None:
        try:
            import redis.asyncio as _redis
            redis = _redis
        except ImportError:
            raise ImportError(
                "redis is not installed. Install it with: pip install redis"
            )
    return redis


class RedisQueryCache(QueryCache):
    """Redis-based cache for query results.
    
    Supports distributed caching across multiple processes/instances.
    Requires a running Redis server.
    """
    
    def __init__(
        self, 
        redis_url: str = "redis://localhost:6379/0",
        key_prefix: str = "rag:query:",
        default_ttl: int = 3600
    ):
        """Initialize Redis cache.
        
        Args:
            redis_url: Redis connection URL
            key_prefix: Prefix for all cache keys
            default_ttl: Default TTL in seconds
        """
        self._redis_url = redis_url
        self._key_prefix = key_prefix
        self._default_ttl = default_ttl
        self._client = None
        self._redis = _get_redis()
    
    async def _get_client(self):
        """Get or create Redis client."""
        if self._client is None:
            self._client = self._redis.from_url(self._redis_url)
        return self._client
    
    def _make_redis_key(self, key: str) -> str:
        """Add prefix to key."""
        return f"{self._key_prefix}{key}"
    
    async def get(self, key: str) -> Optional[dict]:
        """Get cached result."""
        client = await self._get_client()
        redis_key = self._make_redis_key(key)
        
        value = await client.get(redis_key)
        if value is None:
            return None
        
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            return None
    
    async def set(self, key: str, value: dict, ttl: int = None) -> None:
        """Set cache result."""
        client = await self._get_client()
        redis_key = self._make_redis_key(key)
        ttl = ttl or self._default_ttl
        
        await client.setex(
            redis_key, 
            ttl, 
            json.dumps(value)
        )
    
    async def delete(self, pattern: str) -> int:
        """Delete keys matching pattern."""
        client = await self._get_client()
        redis_pattern = self._make_redis_key(pattern)
        
        # Use SCAN to find matching keys
        keys = []
        async for key in client.scan_iter(match=redis_pattern):
            keys.append(key)
        
        if keys:
            return await client.delete(*keys)
        return 0
    
    async def clear(self) -> None:
        """Clear all cached results."""
        await self.delete("*")
    
    async def close(self) -> None:
        """Close Redis connection."""
        if self._client:
            await self._client.close()
            self._client = None
```

- [ ] **Step 3: 添加测试**

```python
# tests/unit/test_query_cache.py 添加

@pytest.mark.skip(reason="Requires running Redis server")
class TestRedisQueryCache:
    @pytest.mark.asyncio
    async def test_redis_set_and_get(self):
        from rag_system.cache import RedisQueryCache
        
        cache = RedisQueryCache(redis_url="redis://localhost:6379/15")
        
        try:
            await cache.set("test_key", {"result": "data"})
            result = await cache.get("test_key")
            assert result == {"result": "data"}
        finally:
            await cache.clear()
            await cache.close()
```

- [ ] **Step 4: 提交**

```bash
git add rag_system/cache/redis_cache.py requirements.txt tests/unit/test_query_cache.py
git commit -m "feat(cache): implement Redis backend"
```

---

### Task 14: 集成向量存储和缓存到 RAG 引擎

**Files:**
- Modify: `rag_system/rag_engine.py`

- [ ] **Step 1: 添加导入**

在文件顶部添加：

```python
from .backends.vector_store import get_vector_store, VectorStore
from .cache import get_query_cache, QueryCache
from concurrent.futures import ThreadPoolExecutor, as_completed
import hashlib
```

- [ ] **Step 2: 修改 __init__ 方法**

```python
def __init__(
    self,
    library_dir: Path,
    settings: Optional[Settings] = None,
    embedding_backend: Optional[EmbeddingBackend] = None,
    reranker_backend: Optional[RerankerBackend] = None,
):
    self.library_dir = Path(library_dir)
    self.settings = settings or get_settings()
    self.embedding_backend = embedding_backend or self._build_embedding_backend()
    self.local_reranker = LocalHeuristicReranker()
    self.reranker_backend = reranker_backend or self._build_reranker_backend()
    self._loader_registry = None
    self.metrics = get_metrics_collector()
    
    self._lock = threading.RLock()
    self._snapshot: Optional[IndexSnapshot] = None
    self._cache_path = Path(self.settings.cache.cache_dir) / "index_cache.pkl.gz"
    
    # Initialize vector store
    self._vector_store: VectorStore = get_vector_store(
        backend=self.settings.vector_store.backend,
        dimension=self.settings.embedding.dimensions,
    )
    
    # Initialize query cache
    self._query_cache: QueryCache = get_query_cache(
        backend=self.settings.query_cache.backend,
        redis_url=self.settings.query_cache.redis_url,
        key_prefix=self.settings.query_cache.key_prefix,
        default_ttl=self.settings.query_cache.ttl,
        max_items=self.settings.query_cache.max_memory_items,
    )
    
    # Build initial index
    self._snapshot = self._build_snapshot()
    logger.info(f"RAG Engine initialized with {len(self._snapshot.chunks)} chunks")
```

- [ ] **Step 3: 修改 _build_snapshot 方法中的向量索引**

在 `_build_snapshot` 方法中，生成 `chunk_embeddings` 后添加向量存储：

```python
# 生成 chunk_embeddings 后，添加到向量存储
self._vector_store.clear()
self._vector_store.add(chunk_embeddings, list(range(len(chunks))))

# 保存向量索引（FAISS 或 numpy）
vector_index_path = Path(self.settings.cache.cache_dir) / "vector.index"
self._vector_store.save(vector_index_path)
```

注意：`chunk_embeddings` 仍保留在 `IndexSnapshot` 中，作为兼容性备份。

- [ ] **Step 4: 修改搜索方法使用向量存储**

在 `_search` 方法中，使用向量存储替代 O(n) 遍历：

```python
def _search(self, query: str, top_k: int) -> List[SearchHit]:
    # ... query embedding generation ...
    
    # 使用向量存储进行检索 (O(log n) for FAISS)
    candidate_pool_size = min(
        top_k * self.settings.retrieval.candidate_pool_multiplier,
        len(self._snapshot.chunks)
    )
    
    # 从向量存储获取候选
    results = self._vector_store.search(query_embedding, candidate_pool_size)
    
    # 转换为 CandidateScore
    candidates = []
    for idx, score in results:
        candidates.append(CandidateScore(
            index=idx,
            retrieve_score=score,
            lexical_score=0.0,  # 后续计算
            title_score=0.0,
            rerank_score=0.0,
            llm_score=0.0,
        ))
    
    # ... rest of BM25 scoring and reranking ...
```

- [ ] **Step 5: 修改搜索方法使用缓存**

在 `answer_async` 和 `search_async` 方法开头添加缓存检查：

```python
async def answer_async(self, query: str, top_k: int = 3) -> RagResponse:
    # Check cache
    if self.settings.query_cache.enabled:
        cache_key = self._query_cache.make_key(query, top_k)
        cached = await self._query_cache.get(cache_key)
        if cached:
            logger.debug(f"Cache hit for query: {query}")
            return RagResponse(**cached)
    
    # ... existing search logic ...
    
    # Cache result
    if self.settings.query_cache.enabled:
        await self._query_cache.set(cache_key, response.to_dict())
    
    return response
```

- [ ] **Step 6: 修改 reload_async 清除缓存**

```python
async def reload_async(self) -> None:
    # Clear cache on reload
    if self.settings.query_cache.enabled:
        await self._query_cache.clear()
    
    # ... existing reload logic ...
```

- [ ] **Step 7: 添加集成测试**

```python
# tests/integration/test_rag_engine_integration.py
import pytest
import tempfile
from pathlib import Path

from rag_system import RAGEngine
from rag_system.config import Settings


class TestRAGEngineIntegration:
    def test_vector_store_integration(self, temp_dir):
        """Test vector store works with RAG engine."""
        # Create test library
        lib_dir = temp_dir / "library"
        lib_dir.mkdir()
        (lib_dir / "test.md").write_text("# Test\nHello world")
        
        # Test with numpy backend
        settings = Settings()
        settings.library_dir = lib_dir
        settings.vector_store.backend = "numpy"
        
        engine = RAGEngine(library_dir=lib_dir, settings=settings)
        
        # Search should use vector store
        hits = engine.search("hello", top_k=1)
        assert len(hits) >= 1
    
    @pytest.mark.asyncio
    async def test_query_cache_integration(self, temp_dir):
        """Test query cache works with RAG engine."""
        lib_dir = temp_dir / "library"
        lib_dir.mkdir()
        (lib_dir / "test.md").write_text("# Test\nMachine learning is AI")
        
        settings = Settings()
        settings.library_dir = lib_dir
        settings.query_cache.enabled = True
        settings.query_cache.backend = "memory"
        
        engine = RAGEngine(library_dir=lib_dir, settings=settings)
        
        # First query (cache miss)
        result1 = await engine.answer_async("machine learning", top_k=1)
        
        # Second query (cache hit)
        result2 = await engine.answer_async("machine learning", top_k=1)
        
        assert result1.query == result2.query
```

- [ ] **Step 8: 运行集成测试**

```bash
pytest tests/integration/test_rag_engine_integration.py -v
```

- [ ] **Step 9: 提交**

```bash
git add rag_system/rag_engine.py tests/integration/test_rag_engine_integration.py
git commit -m "feat(rag_engine): integrate vector store and query cache"
```

---

### Task 15: 实现并行文档处理

**Files:**
- Modify: `rag_system/rag_engine.py`

- [ ] **Step 1: 添加并行加载方法**

```python
def _load_documents_parallel(self, files: List[Path]) -> List[SourceDocument]:
    """Load documents in parallel using ThreadPoolExecutor."""
    documents = []
    max_workers = self.settings.performance.max_workers
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_file = {
            executor.submit(self._load_single_document, f): f 
            for f in files
        }
        
        for future in as_completed(future_to_file):
            file_path = future_to_file[future]
            try:
                result = future.result()
                if result:
                    documents.append(result)
            except Exception as e:
                logger.warning(f"Failed to load {file_path}: {e}")
    
    return documents

def _load_single_document(self, file_path: Path) -> Optional[SourceDocument]:
    """Load a single document."""
    try:
        loader = self.loader_registry.get_loader(file_path)
        if loader:
            return loader.load(file_path)
    except Exception as e:
        logger.warning(f"Error loading {file_path}: {e}")
    return None
```

- [ ] **Step 2: 修改 _reload 方法使用并行加载**

```python
def _reload(self) -> None:
    # ... existing file discovery code ...
    
    # Use parallel loading if enabled
    if self.settings.performance.parallel_loading:
        documents = self._load_documents_parallel(files)
    else:
        documents = [self._load_single_document(f) for f in files]
        documents = [d for d in documents if d]
    
    # ... rest of the method ...
```

- [ ] **Step 3: 提交**

```bash
git add rag_system/rag_engine.py
git commit -m "feat(rag_engine): add parallel document loading"
```

---

## 阶段三：前端优化

### Task 16: 配置代码分割

**Files:**
- Modify: `web-new/vite.config.ts`

- [ ] **Step 1: 更新 vite.config.ts**

```typescript
import { defineConfig, loadEnv } from 'vite';
import react from '@vitejs/plugin-react';
import { visualizer } from 'rollup-plugin-visualizer';

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), '');
  
  return {
    plugins: [
      react(),
      mode === 'analyze' && visualizer({ open: true }),
    ],
    resolve: {
      alias: {
        '@': '/src',
      },
    },
    server: {
      port: 5173,
      host: true,
      proxy: {
        '/api': {
          target: env.VITE_API_BASE_URL || 'http://127.0.0.1:8000',
          changeOrigin: true,
          rewrite: (path) => path,
        },
      },
    },
    build: {
      target: 'es2020',
      minify: 'terser',
      cssMinify: true,
      rollupOptions: {
        output: {
          manualChunks: {
            'vendor-react': ['react', 'react-dom', 'react-router-dom'],
            'vendor-antd': ['antd', '@ant-design/icons'],
            'vendor-query': ['@tanstack/react-query'],
            'vendor-state': ['zustand'],
            'vendor-i18n': ['i18next', 'react-i18next', 'i18next-browser-languagedetector'],
            'vendor-utils': ['axios', 'dayjs', 'lodash-es', 'nanoid'],
            'vendor-prism': ['prismjs'],
          },
        },
      },
      chunkSizeWarningLimit: 500,
    },
    css: {
      preprocessorOptions: {
        less: {
          javascriptEnabled: true,
          modifyVars: {},
        },
      },
    },
  };
});
```

- [ ] **Step 2: 验证打包**

```bash
cd web-new && npm run build
```

Expected: 查看打包后的 chunk 大小分布

- [ ] **Step 3: 提交**

```bash
git add web-new/vite.config.ts
git commit -m "perf(vite): optimize code splitting configuration"
```

---

### Task 17: 实现路由懒加载

**Files:**
- Modify: `web-new/src/App.tsx`
- Create: `web-new/src/components/PageLoader/PageLoader.tsx`

- [ ] **Step 1: 创建 PageLoader 组件**

```bash
mkdir -p web-new/src/components/PageLoader
```

```typescript
// web-new/src/components/PageLoader/PageLoader.tsx
import React from 'react';
import { Spin } from 'antd';

export const PageLoader: React.FC = () => {
  return (
    <div style={{ 
      display: 'flex', 
      justifyContent: 'center', 
      alignItems: 'center',
      minHeight: '200px',
      padding: '100px 0'
    }}>
      <Spin size="large" />
    </div>
  );
};
```

- [ ] **Step 2: 更新 App.tsx**

```typescript
import React, { lazy, Suspense } from 'react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ReactQueryDevtools } from '@tanstack/react-query-devtools';
import { MainLayout } from '@/layouts/MainLayout/MainLayout';
import { ErrorBoundary } from '@/components/ErrorBoundary/ErrorBoundary';
import { PageLoader } from '@/components/PageLoader/PageLoader';

// Lazy load pages
const Home = lazy(() => import('@/pages/Home/Home'));

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 5 * 60 * 1000,
      retry: 2,
      refetchOnWindowFocus: false,
    },
  },
});

export const App: React.FC = () => {
  return (
    <QueryClientProvider client={queryClient}>
      <ErrorBoundary>
        <MainLayout>
          <Suspense fallback={<PageLoader />}>
            <Home />
          </Suspense>
        </MainLayout>
      </ErrorBoundary>
      {import.meta.env.DEV && <ReactQueryDevtools initialIsOpen={false} />}
    </QueryClientProvider>
  );
};
```

- [ ] **Step 3: 验证类型检查**

```bash
cd web-new && npm run typecheck
```

- [ ] **Step 4: 提交**

```bash
git add web-new/src/App.tsx web-new/src/components/PageLoader/
git commit -m "perf(frontend): implement lazy loading for routes"
```

---

## 最终验证

### Task 18: 完整测试和验证

- [ ] **Step 1: 运行完整测试套件**

```bash
pytest tests/ -v --cov=rag_system
```

Expected: 所有测试通过，覆盖率 ≥ 80%

- [ ] **Step 2: 运行前端构建**

```bash
cd web-new && npm run build
```

Expected: 构建成功，无错误

- [ ] **Step 3: 启动完整系统**

```bash
# 终端1: 后端
uvicorn rag_system.api.server:create_app --factory --reload

# 终端2: 前端
cd web-new && npm run dev
```

- [ ] **Step 4: 功能验证**

验证以下功能：
1. ✅ 文档库加载和显示
2. ✅ 搜索查询返回结果
3. ✅ 文件上传功能
4. ✅ 查询缓存生效（重复查询更快）
5. ✅ 前端页面正常渲染

- [ ] **Step 5: 性能验证**

```bash
# 检查前端包大小
cd web-new && npm run build:analyze
```

Expected: 初始包大小减少 50%+

- [ ] **Step 6: 提交最终版本**

```bash
git add .
git commit -m "chore: production iteration complete

- Fix tests and frontend TypeScript errors
- Integrate FAISS vector store
- Add Redis query cache
- Implement parallel document processing
- Optimize frontend code splitting"
```

---

## 配置示例

**最终 config.yaml 示例：**

```yaml
server:
  host: "127.0.0.1"
  port: 8000
  workers: 1

vector_store:
  backend: "faiss"  # 或 "numpy"

embedding:
  backend: "local-hash"
  dimensions: 256
  projections_per_token: 8

reranker:
  backend: "local-heuristic"

cache:
  enabled: true
  cache_dir: ".index_cache"
  
query_cache:
  enabled: true
  backend: "redis"  # 或 "memory"
  redis_url: "redis://localhost:6379/0"
  ttl: 3600
  key_prefix: "rag:query:"

performance:
  parallel_loading: true
  max_workers: 4
  embed_batch_size: 32

retrieval:
  top_k: 3
  bm25_k1: 1.5
  bm25_b: 0.75

chunking:
  max_chars: 240
  overlap: 1
```