# RAG 系统第一阶段增强设计文档

**日期：** 2026-03-28  
**版本：** 1.0  
**阶段：** 第一阶段 - 核心后端优化

---

## 概述

本设计文档描述 RAG 系统第一阶段的增强方案，包括增量索引系统、本地嵌入模型和高级搜索增强。目标是在现有架构基础上，通过模块化重构提升系统的扩展性、搜索质量和维护性。

---

## 目标

### 核心目标

1. **增量索引系统**：支持文档增删改时增量更新索引，避免全量重建
2. **本地嵌入模型**：使用 ONNX Runtime 运行本地 Transformer 模型，降低延迟
3. **高级搜索增强**：Cross-encoder 重排序、伪相关反馈、BM25 持久化

### 成功指标

| 指标 | 当前值 | 目标值 |
|------|--------|--------|
| 文档添加耗时 | O(n) 全量重建 | O(1) 增量添加 |
| 嵌入生成延迟 | 100-500ms (API) | 20-50ms (本地) |
| 搜索相关性 | 基础启发式 | 提升 10-30% |
| BM25 重载耗时 | 每次重新计算 | 加载持久化数据 |

---

## 架构设计

### 模块划分

```
rag_system/
├── index/                    # 新增：索引管理模块
│   ├── __init__.py
│   ├── manager.py            # IndexManager：索引生命周期管理
│   ├── watcher.py            # DocumentWatcher：文件变更检测
│   ├── version.py            # IndexVersion：版本控制
│   └── bm25_store.py         # BM25Store：BM25统计信息持久化
│
├── backends/
│   ├── embedding/
│   │   ├── base.py           # 现有：抽象基类
│   │   ├── local_hash.py     # 现有：哈希嵌入
│   │   ├── openai_compatible.py  # 现有：OpenAI API
│   │   ├── cached.py         # 现有：缓存装饰器
│   │   └── onnx_backend.py   # 新增：ONNX本地嵌入
│   │
│   ├── reranker/
│   │   ├── base.py           # 现有：抽象基类
│   │   ├── local_heuristic.py  # 现有：启发式重排序
│   │   ├── openai_compatible.py  # 现有：LLM重排序
│   │   ├── cross_encoder.py  # 新增：Cross-encoder重排序
│   │   └── prf_reranker.py   # 新增：伪相关反馈
│   │
│   └── vector_store/         # 现有：向量存储
│       ├── base.py
│       ├── faiss_store.py
│       └── numpy_store.py
│
├── cache/                    # 现有：查询缓存
│   ├── base.py
│   ├── memory_cache.py
│   └── redis_cache.py
│
├── rag_engine.py             # 修改：集成新模块
├── config/settings.py        # 修改：添加新配置类

models/                       # 新增：模型文件目录（项目根目录）
├── embedding/
│   └── all-MiniLM-L6-v2.onnx
└── reranker/
    └── ms-marco.onnx
```

### 职责划分

| 模块 | 职责 | 依赖 | 复杂度 |
|------|------|------|--------|
| **IndexManager** | 索引增删改、生命周期管理 | VectorStore、BM25Store、EmbeddingBackend | 中 |
| **DocumentWatcher** | 文件变更检测 | 文件系统、IndexManager | 低 |
| **IndexVersion** | 快照、版本管理、回滚 | IndexManager、持久化 | 低 |
| **BM25Store** | BM25统计持久化 | 文件系统 | 低 |
| **ONNXEmbeddingBackend** | 本地Transformer推理 | ONNX Runtime、Tokenizer | 中 |
| **CrossEncoderReranker** | Cross-encoder精细重排序 | ONNX Runtime | 中 |
| **PRFReranker** | 伪相关反馈扩展查询 | 搜索结果 | 低 |

### 组件交互流程

```
用户上传文档
    ↓
DocumentWatcher 检测变更
    ↓
IndexManager.add_document()
    ↓
┌─────────────────────────────────────┐
│  1. 加载文档 → Chunk                 │
│  2. ONNXEmbeddingBackend.embed()    │
│  3. VectorStore.add(new_vectors)    │
│  4. BM25Store.update_terms(chunks)  │
│  5. IndexVersion.create_snapshot()  │
└─────────────────────────────────────┘
    ↓
索引更新完成，通知查询缓存清除

用户搜索查询
    ↓
RAGEngine.search()
    ↓
┌─────────────────────────────────────┐
│  1. ONNXEmbeddingBackend.embed(query)│
│  2. VectorStore.search(query_vec)   │
│  3. BM25Store.lexical_score(query)  │
│  4. 启发式融合评分                   │
│  5. PRFReranker.expand_query()      │
│  6. CrossEncoderReranker.rerank()   │
└─────────────────────────────────────┘
    ↓
返回排序后的 SearchHit 结果
```

---

## 前置依赖

### tokenize 函数

项目中已存在 `tokenize()` 函数，位于 `rag_system/utils/text.py`：

```python
def tokenize(text: str) -> List[str]:
    """Tokenize text with support for English and Chinese.
    
    实现细节：
    - 英文：正则提取 [a-z0-9]+ 单词
    - 中文：N-gram 分词（2-3字符）
    - 返回小写化后的 token 列表
    
    用途：
    - BM25 词频统计
    - PRF 高频词提取
    """
```

BM25Store 和 PRFReranker 使用此函数进行词频统计，与 ONNX 后端的 Transformer tokenizer 分离（后者用于语义嵌入生成）。

---

## 详细设计

### 1. IndexManager - 索引生命周期管理

#### 1.1 类定义

```python
class IndexManager:
    """索引生命周期管理器，支持增量操作"""
    
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
        
    async def update_document(self, doc_path: Path) -> bool:
        """增量更新文档
        
        流程：先删除旧的chunk，再添加新的chunk
        """
        
    async def rebuild_full(self) -> None:
        """全量重建索引
        
        作为兜底方案，清空所有数据重新构建
        """
        
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
        
    def compress_if_needed(self) -> bool:
        """检查并执行索引压缩
        
        当deleted_ratio > 30%时触发
        压缩流程：重建向量索引，清理deleted_ids
        """
        
    def get_valid_chunks(self) -> List[Chunk]:
        """获取所有有效chunk（排除已删除）
        """
```

#### 1.2 增量添加算法

```python
def add_document(self, doc_path: Path) -> bool:
    with self._lock:
        # 1. 加载文档
        loader = self._get_loader(doc_path)
        if not loader:
            return False
        document = loader.load(doc_path)
        
        # 2. 分块
        chunks = chunk_text(
            document.text,
            max_chars=self._chunking_config.max_chars,
            overlap=self._chunking_config.overlap,
        )
        
        # 3. 生成嵌入（异步）
        embeddings = await self._embedding_backend.embed_batch(
            [c.text for c in chunks]
        )
        
        # 4. 分配chunk_id
        start_id = len(self._chunk_map)
        chunk_ids = list(range(start_id, start_id + len(chunks)))
        
        # 5. 添加到向量存储
        self._vector_store.add(embeddings, chunk_ids)
        
        # 6. 更新BM25统计
        for chunk_id, chunk in zip(chunk_ids, chunks):
            self._bm25_store.update_terms(chunk, chunk_id)
        
        # 7. 更新chunk_map
        for chunk_id, chunk in zip(chunk_ids, chunks):
            chunk.chunk_id = chunk_id
            chunk.source = str(doc_path)
            self._chunk_map[chunk_id] = chunk
        
        return True
```

#### 1.3 增量删除策略

由于 FAISS 不支持直接删除向量，采用"标记删除"策略：

```python
def remove_document(self, doc_path: Path) -> bool:
    with self._lock:
        # 1. 找到文档对应的所有chunk_id
        chunk_ids = [
            cid for cid, chunk in self._chunk_map.items()
            if chunk.source == str(doc_path)
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
        
        # 5. 检查是否需要压缩
        deleted_ratio = len(self._deleted_ids) / (
            len(self._chunk_map) + len(self._deleted_ids)
        )
        if deleted_ratio > 0.3:
            self._compress_index()
        
        return True
```

#### 1.4 索引压缩

```python
def _compress_index(self) -> None:
    """压缩索引，重建向量存储"""
    # 1. 获取所有有效向量
    valid_ids = list(self._chunk_map.keys())
    valid_embeddings = self._vector_store.get_vectors(valid_ids)
    
    # 2. 清空并重建向量存储
    self._vector_store.clear()
    self._vector_store.add(valid_embeddings, valid_ids)
    
    # 3. 清空deleted_ids
    self._deleted_ids.clear()
    
    # 4. 更新chunk_map的chunk_id
    # 需要重新映射ID，因为向量存储的ID顺序变了
    new_chunk_map = {}
    for new_id, old_id in enumerate(valid_ids):
        chunk = self._chunk_map[old_id]
        chunk.chunk_id = new_id
        new_chunk_map[new_id] = chunk
    self._chunk_map = new_chunk_map
```

---

### 2. DocumentWatcher - 文件变更检测

#### 2.1 类定义

```python
class DocumentWatcher:
    """文档库文件变更检测"""
    
    def __init__(
        self,
        library_dir: Path,
        index_manager: IndexManager,
        mode: str = "scan",  # "scan" or "watch"
        scan_interval: int = 30,
    ):
        self._library_dir = library_dir
        self._index_manager = index_manager
        self._mode = mode
        self._scan_interval = scan_interval
        self._file_hashes: Dict[str, str] = {}
        self._running = False
        self._thread: Optional[threading.Thread] = None
        
    def start(self) -> None:
        """启动后台监控"""
        self._running = True
        if self._mode == "watch":
            self._start_watchdog()
        else:
            self._thread = threading.Thread(target=self._scan_loop)
            self._thread.start()
        
    def stop(self) -> None:
        """停止监控"""
        self._running = False
        if self._thread:
            self._thread.join(timeout=5)
            
    def scan_changes(self) -> List[FileChange]:
        """扫描文件变更
        
        Returns:
            List of FileChange objects containing:
            - path: Path
            - change_type: "added" | "modified" | "deleted"
            - old_hash: Optional[str]
            - new_hash: Optional[str]
        """
```

#### 2.2 扫描模式实现

```python
def _scan_loop(self) -> None:
    """定时扫描线程"""
    while self._running:
        changes = self.scan_changes()
        for change in changes:
            self._handle_change(change)
        time.sleep(self._scan_interval)

def scan_changes(self) -> List[FileChange]:
    """扫描并检测变更"""
    changes = []
    
    # 获取当前文件列表
    current_files = {}
    for ext in SUPPORTED_EXTENSIONS:
        for f in self._library_dir.glob(f"*{ext}"):
            current_files[str(f)] = self._get_file_hash(f)
    
    # 检测新增和修改
    for path, hash in current_files.items():
        if path not in self._file_hashes:
            changes.append(FileChange(
                path=Path(path),
                change_type="added",
                old_hash=None,
                new_hash=hash,
            ))
        elif self._file_hashes[path] != hash:
            changes.append(FileChange(
                path=Path(path),
                change_type="modified",
                old_hash=self._file_hashes[path],
                new_hash=hash,
            ))
    
    # 检测删除
    for path in self._file_hashes:
        if path not in current_files:
            changes.append(FileChange(
                path=Path(path),
                change_type="deleted",
                old_hash=self._file_hashes[path],
                new_hash=None,
            ))
    
    # 更新哈希记录
    self._file_hashes = current_files
    
    return changes

def _get_file_hash(self, path: Path) -> str:
    """计算文件MD5哈希"""
    import hashlib
    hasher = hashlib.md5()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(4096), b''):
            hasher.update(chunk)
    return hasher.hexdigest()
```

#### 2.3 变更处理

```python
def _handle_change(self, change: FileChange) -> None:
    """处理文件变更"""
    if change.change_type == "added":
        logger.info(f"Document added: {change.path}")
        self._index_manager.add_document(change.path)
        
    elif change.change_type == "modified":
        logger.info(f"Document modified: {change.path}")
        self._index_manager.update_document(change.path)
        
    elif change.change_type == "deleted":
        logger.info(f"Document deleted: {change.path}")
        self._index_manager.remove_document(change.path)
```

---

### 3. BM25Store - BM25统计持久化

#### 3.1 类定义

```python
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
        
    def remove_terms(self, chunk_ids: List[int]) -> None:
        """删除词频统计
        
        流程：
        1. 从term_freq中删除对应chunk_id的记录
        2. 更新doc_freq（减少计数）
        3. 从doc_length中删除
        4. 重新计算avg_doc_length
        """
        
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
        
    def save(self) -> None:
        """持久化到磁盘"""
        
    def load(self) -> bool:
        """从磁盘加载"""
        
    def clear(self) -> None:
        """清空所有统计"""
```

#### 3.2 存储格式

```
.index_cache/
├── bm25_term_freq.pkl.gz    # {term: {chunk_id: freq}}
├── bm25_doc_freq.pkl.gz     # {term: doc_freq}
├── bm25_doc_length.pkl.gz   # {chunk_id: length}
└── bm25_metadata.pkl.gz     # {avg_doc_length, total_docs, k1, b}
```

#### 3.3 BM25评分计算

```python
def get_bm25_score(self, query: str, chunk_id: int) -> float:
    """计算BM25分数"""
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
```

---

### 4. IndexVersion - 版本控制

#### 4.1 类定义

```python
class IndexVersion:
    """索引版本管理"""
    
    def __init__(
        self,
        cache_dir: Path,
        max_snapshots: int = 5,
    ):
        self._cache_dir = cache_dir
        self._snapshots_dir = cache_dir / "snapshots"
        self._max_snapshots = max_snapshots
        
    def create_snapshot(self, name: Optional[str] = None) -> str:
        """创建索引快照
        
        Args:
            name: 可选的快照名称，默认使用时间戳
            
        Returns:
            快照名称
        """
        
    def list_snapshots(self) -> List[SnapshotInfo]:
        """列出所有快照
        
        Returns:
            List of SnapshotInfo containing:
            - name: str
            - timestamp: datetime
            - doc_count: int
            - chunk_count: int
            - checksum: str
        """
        
    def restore_snapshot(self, name: str) -> bool:
        """恢复到指定快照
        
        流程：
        1. 验证快照存在
        2. 验证checksum
        3. 复制文件到主索引目录
        4. 重新加载
        
        Returns:
            True if successful
        """
        
    def delete_snapshot(self, name: str) -> bool:
        """删除快照"""
        
    def cleanup_old_snapshots(self) -> int:
        """清理超出限制的旧快照
        
        Returns:
            删除的快照数量
        """
```

#### 4.2 快照结构

```
.index_cache/snapshots/
├── v1_20260328_120000/
│   ├── faiss.index
│   ├── faiss.ids.pkl
│   ├── bm25_term_freq.pkl.gz
│   ├── bm25_doc_freq.pkl.gz
│   ├── bm25_doc_length.pkl.gz
│   ├── bm25_metadata.pkl.gz
│   ├── chunk_map.pkl.gz
│   └── metadata.json
│
├── v2_20260328_150000/
│   └── ...
```

#### 4.3 元数据格式

```json
{
  "version": "v2_20260328_150000",
  "timestamp": "2026-03-28T15:00:00Z",
  "doc_count": 42,
  "chunk_count": 156,
  "checksum": "abc123...",
  "config": {
    "embedding_backend": "onnx",
    "vector_store_backend": "faiss",
    "chunking_max_chars": 240
  }
}
```

---

### 5. ONNXEmbeddingBackend - 本地嵌入

#### 5.1 类定义

```python
class ONNXEmbeddingBackend(EmbeddingBackend):
    """基于ONNX Runtime的本地嵌入后端"""
    
    def __init__(
        self,
        model_path: Path,
        dimension: int = 384,
        max_seq_length: int = 256,
    ):
        self._model_path = model_path
        self._dimension = dimension
        self._max_seq_length = max_seq_length
        
        # 加载ONNX模型
        self._session = onnxruntime.InferenceSession(
            str(model_path),
            providers=['CPUExecutionProvider']
        )
        
        # 加载tokenizer
        self._tokenizer = AutoTokenizer.from_pretrained(
            model_path.parent,
            use_fast=True,
        )
        
    async def embed(self, text: str) -> np.ndarray:
        """生成单个文本嵌入
        
        流程：
        1. Tokenize文本
        2. 运行ONNX推理
        3. Mean pooling
        4. L2归一化
        
        Returns:
            384维归一化向量
        """
        
    async def embed_batch(self, texts: List[str]) -> List[np.ndarray]:
        """批量生成嵌入
        
        批量处理比逐个处理效率更高
        """
        
    def get_dimension(self) -> int:
        return self._dimension
```

#### 5.2 嵌入生成流程

```python
async def embed(self, text: str) -> np.ndarray:
    # Tokenize
    inputs = self._tokenizer(
        text,
        padding=True,
        truncation=True,
        max_length=self._max_seq_length,
        return_tensors='np',
    )
    
    # ONNX推理
    outputs = self._session.run(
        None,
        {
            'input_ids': inputs['input_ids'],
            'attention_mask': inputs['attention_mask'],
        }
    )
    
    # outputs[0]: last_hidden_state (batch, seq_len, hidden_dim)
    # outputs[1]: pooler_output (batch, hidden_dim) - 可选
    
    last_hidden_state = outputs[0]
    attention_mask = inputs['attention_mask']
    
    # Mean pooling (考虑attention_mask)
    mask_expanded = np.expand_dims(attention_mask, -1)
    sum_embeddings = np.sum(last_hidden_state * mask_expanded, axis=1)
    sum_mask = np.sum(mask_expanded, axis=1)
    embeddings = sum_embeddings / np.clip(sum_mask, 1e-9, None)
    
    # L2归一化
    embeddings = embeddings / np.linalg.norm(embeddings, axis=1, keepdims=True)
    
    return embeddings[0]  # 单个文本，取第一个
```

#### 5.3 模型准备

```python
def prepare_onnx_model(model_name: str, output_dir: Path) -> None:
    """准备ONNX模型文件
    
    流程：
    1. 下载sentence-transformers模型
    2. 转换为ONNX格式
    3. 保存tokenizer
    """
    from sentence_transformers import SentenceTransformer
    from transformers import AutoTokenizer
    
    # 下载模型
    model = SentenceTransformer(model_name)
    
    # 导出ONNX
    model.save(str(output_dir))
    
    # 转换为ONNX格式（如果不是）
    onnx_path = output_dir / "model.onnx"
    if not onnx_path.exists():
        # 使用transformers的export功能
        from transformers.onnx import export
        export(model.tokenizer, model.model, onnx_path)
```

---

### 6. CrossEncoderReranker - 精细重排序

#### 6.1 类定义

```python
class CrossEncoderReranker(RerankerBackend):
    """基于Cross-encoder的重排序器"""
    
    def __init__(
        self,
        model_path: Path,
        max_candidates: int = 100,
    ):
        self._model_path = model_path
        self._max_candidates = max_candidates
        
        # 加载ONNX模型
        self._session = onnxruntime.InferenceSession(
            str(model_path),
            providers=['CPUExecutionProvider']
        )
        
        # 加载tokenizer
        self._tokenizer = AutoTokenizer.from_pretrained(
            model_path.parent,
            use_fast=True,
        )
        
    async def rerank(
        self,
        query: str,
        candidates: List[CandidateScore],
        chunks: List[Chunk],
        top_k: int,
    ) -> List[CandidateScore]:
        """重排序候选结果
        
        流程：
        1. 构建query+document对
        2. 批量运行cross-encoder推理
        3. 获取相关性分数（0-1）
        4. 融合原始分数和cross-encoder分数
        5. 按新分数排序
        
        Returns:
            重排序后的候选列表
        """
```

#### 6.2 重排序流程

```python
async def rerank(
    self,
    query: str,
    candidates: List[CandidateScore],
    chunks: List[Chunk],
    top_k: int,
) -> List[CandidateScore]:
    # 限制候选数量
    candidates = candidates[:self._max_candidates]
    
    # 构建输入对
    pairs = [(query, chunks[c.index].text) for c in candidates]
    
    # Tokenize
    inputs = self._tokenizer(
        [p[0] for p in pairs],
        [p[1] for p in pairs],
        padding=True,
        truncation=True,
        max_length=512,
        return_tensors='np',
    )
    
    # ONNX推理
    outputs = self._session.run(
        None,
        {
            'input_ids': inputs['input_ids'],
            'attention_mask': inputs['attention_mask'],
        }
    )
    
    # 输出是logits，转换为概率
    logits = outputs[0][:, 0]  # 取第一个位置
    scores = 1 / (1 + np.exp(-logits))  # sigmoid
    
    # 融合分数
    for i, candidate in enumerate(candidates):
        # 0.4 * heuristic + 0.6 * cross_encoder
        candidate.rerank_score = (
            0.4 * candidate.retrieve_score +
            0.6 * scores[i]
        )
    
    # 按新分数排序
    candidates.sort(key=lambda c: c.rerank_score, reverse=True)
    
    return candidates[:top_k]
```

---

### 7. PRFReranker - 伪相关反馈

#### 7.1 类定义

```python
class PRFReranker:
    """伪相关反馈查询扩展"""
    
    def __init__(
        self,
        num_terms: int = 3,
        min_doc_freq: int = 2,
        term_weight: float = 0.3,
    ):
        self._num_terms = num_terms
        self._min_doc_freq = min_doc_freq
        self._term_weight = term_weight
        
    def expand_query(
        self,
        query: str,
        initial_results: List[SearchHit],
        bm25_store: BM25Store,
    ) -> str:
        """扩展查询
        
        流程：
        1. 从初始结果中提取高频词
        2. 过滤掉已在query中的词
        3. 添加权重调整后的扩展词
        
        Returns:
            扩展后的查询字符串
        """
        
    def get_expansion_terms(
        self,
        query: str,
        initial_results: List[SearchHit],
        bm25_store: BM25Store,
    ) -> List[str]:
        """获取扩展词列表
        
        Args:
            query: 原始查询（用于过滤已存在词）
            initial_results: 初始搜索结果
            bm25_store: BM25统计存储
        """
```

#### 7.2 扩展算法

```python
def get_expansion_terms(
    self,
    query: str,
    initial_results: List[SearchHit],
    bm25_store: BM25Store,
) -> List[str]:
    """从初始结果提取扩展词"""
    # 收集所有结果的词频
    term_freq = defaultdict(int)
    
    for hit in initial_results[:10]:  # 取前10个结果
        chunk_text = hit.chunk.text
        terms = tokenize(chunk_text)
        
        for term in terms:
            term_freq[term] += 1
    
    # 过滤并排序（过滤掉原始query中已有的词）
    original_terms = set(tokenize(query))
    
    expansion_terms = []
    for term, freq in sorted(term_freq.items(), key=lambda x: -x[1]):
        # 过滤条件
        if term in original_terms:
            continue
        if freq < self._min_doc_freq:
            continue
        if len(term) < 2:  # 忽略单字符
            continue
        
        expansion_terms.append(term)
        if len(expansion_terms) >= self._num_terms:
            break
    
    return expansion_terms

def expand_query(
    self,
    query: str,
    initial_results: List[SearchHit],
    bm25_store: BM25Store,
) -> str:
    expansion_terms = self.get_expansion_terms(query, initial_results, bm25_store)
    
    if not expansion_terms:
        return query
    
    # 构建扩展查询
    # 原始query权重高，扩展词权重低
    expanded = query + " " + " ".join(expansion_terms[:self._num_terms])
    
    return expanded
```

---

### 8. 配置设计

#### 8.1 新增配置类

```python
@dataclass
class IndexConfig:
    """索引管理配置"""
    incremental: bool = True
    auto_compress_threshold: float = 0.3
    
@dataclass
class WatcherConfig:
    """文件监控配置"""
    enabled: bool = True
    mode: str = "scan"  # "scan" or "watch"
    scan_interval: int = 30
    
@dataclass
class VersionConfig:
    """版本控制配置"""
    enabled: bool = True
    max_snapshots: int = 5
    
@dataclass
class ONNXEmbeddingConfig:
    """ONNX嵌入配置"""
    model_path: str = "models/embedding/all-MiniLM-L6-v2.onnx"
    dimension: int = 384
    max_seq_length: int = 256
    
@dataclass
class CrossEncoderConfig:
    """Cross-encoder配置"""
    model_path: str = "models/reranker/ms-marco.onnx"
    max_candidates: int = 100
    
@dataclass
class PRFConfig:
    """伪相关反馈配置"""
    enabled: bool = True
    num_terms: int = 3
    min_doc_freq: int = 2
    term_weight: float = 0.3
```

#### 8.2 完整配置示例

```yaml
server:
  host: "127.0.0.1"
  port: 8000
  workers: 1

embedding:
  backend: "onnx"  # "local-hash" | "openai-compatible" | "onnx"
  model_path: "models/embedding/all-MiniLM-L6-v2.onnx"
  dimension: 384
  max_seq_length: 256

reranker:
  backend: "cross-encoder"  # "local-heuristic" | "openai-compatible" | "cross-encoder"
  model_path: "models/reranker/ms-marco.onnx"
  max_candidates: 100
  use_prf: true
  
prf:
  enabled: true
  num_terms: 3
  min_doc_freq: 2
  term_weight: 0.3

index:
  incremental: true
  auto_compress_threshold: 0.3
  
watcher:
  enabled: true
  mode: "scan"
  scan_interval: 30
  
version:
  enabled: true
  max_snapshots: 5

vector_store:
  backend: "faiss"
  
cache:
  enabled: true
  cache_dir: ".index_cache"
  query_cache:
    enabled: true
    backend: "redis"
    redis_url: "redis://localhost:6379/0"
    ttl: 3600

retrieval:
  top_k: 3
  bm25_k1: 1.5
  bm25_b: 0.75

chunking:
  max_chars: 240
  overlap: 1
```

---

## 测试策略

### 模块完成即测

每个功能模块完成后立即测试，确保稳定后再进入下一个。

### 测试覆盖

| 模块 | 单元测试 | 集成测试 | 性能测试 |
|------|----------|----------|----------|
| IndexManager | 增删改操作、并发安全 | 与VectorStore/BM25Store联调 | 增量添加性能 |
| DocumentWatcher | 变更检测、哈希计算 | 与IndexManager联调 | 扫描延迟 |
| BM25Store | 词频更新、评分计算 | 持久化/加载 | 评分性能 |
| IndexVersion | 快照创建/恢复 | 多版本管理 | 快照大小 |
| ONNXEmbeddingBackend | 嵌入生成、归一化 | 与IndexManager联调 | 推理延迟 |
| CrossEncoderReranker | 重排序逻辑 | 全流程搜索 | 重排序延迟 |
| PRFReranker | 词提取、查询扩展 | 全流程搜索 | 扩展效果 |

### 测试命令

```bash
# 单元测试
pytest tests/unit/test_index_manager.py -v
pytest tests/unit/test_bm25_store.py -v
pytest tests/unit/test_onnx_embedding.py -v
pytest tests/unit/test_cross_encoder.py -v
pytest tests/unit/test_prf.py -v

# 集成测试
pytest tests/integration/test_search_pipeline.py -v

# 性能测试
pytest tests/performance/test_incremental_index.py -v --benchmark

# 全量测试
pytest tests/ -v --cov=rag_system --cov-report=html
```

---

## 依赖项

### 新增 Python 依赖

```
# requirements.txt 新增
onnxruntime>=1.15.0
transformers>=4.30.0
sentence-transformers>=2.2.0
watchdog>=3.0.0  # 可选，用于watch模式
```

### 模型文件

```
models/
├── embedding/
│   ├── all-MiniLM-L6-v2.onnx    # ~45MB
│   ├── tokenizer.json
│   ├── tokenizer_config.json
│   └── vocab.txt
│
└── reranker/
│   ├── ms-marco.onnx            # ~80MB
│   ├── tokenizer.json
│   ├── tokenizer_config.json
│   └── vocab.txt
```

---

## 实施计划概览

### 阶段一：核心后端优化（预计 8-10 小时）

| 子任务 | 预估时间 | 依赖 |
|--------|----------|------|
| IndexManager 实现 | 2h | VectorStore、BM25Store |
| BM25Store 实现 | 1.5h | 无 |
| DocumentWatcher 实现 | 1h | IndexManager |
| IndexVersion 实现 | 1h | IndexManager |
| ONNXEmbeddingBackend 实现 | 2h | 模型准备 |
| CrossEncoderReranker 实现 | 1.5h | 模型准备 |
| PRFReranker 实现 | 1h | 无 |
| 配置更新与集成 | 1h | 所有模块 |

### 测试验证（预计 2-3 小时）

- 单元测试编写与执行
- 集成测试验证
- 性能基准测试
- 前后端联调验证

---

## 风险与缓解

| 风险 | 影响 | 缓解措施 |
|------|------|----------|
| ONNX模型下载失败 | 无法使用本地嵌入 | 提供模型下载脚本，支持手动下载 |
| FAISS删除性能 | 增量删除后索引膨胀 | 标记删除 + 定期压缩策略 |
| Cross-encoder延迟 | 重排序耗时增加 | 限制候选数量(100)，可选启用 |
| 文件监控误触发 | 频繁重建索引 | 哈希校验 + 延迟处理 |
| 内存占用增加 | 模型加载消耗内存 | 模型共享、量化压缩 |

---

## 后续阶段预告

### 阶段二：前端功能增强

- 搜索结果可视化增强
- 文档库管理界面优化
- 上传进度与状态展示
- 搜索历史与收藏功能

### 阶段三：可观测性增强

- OpenTelemetry 分布式追踪
- Prometheus 指标暴露
- 性能仪表板
- 告警集成

### 阶段四：安全加固

- CSP 安全策略
- 审计日志
- IP 限流
- SQL 注入防护

---

## 验收标准

1. **功能完整性**
   - 增量索引增删改操作正常
   - 本地嵌入生成正确（384维归一化向量）
   - Cross-encoder重排序生效
   - PRF查询扩展生效
   - BM25持久化正确

2. **性能指标**
   - 单文档增量添加 ≤ 100ms
   - 嵌入生成 ≤ 50ms（单文本）
   - 重排序(100候选) ≤ 2s
   - BM25加载 ≤ 500ms

3. **测试覆盖**
   - 单元测试全部通过
   - 集成测试全部通过
   - 测试覆盖率 ≥ 80%

4. **代码质量**
   - 类型检查通过（mypy）
   - 代码规范通过（flake8/black）
   - 无安全警告（bandit）