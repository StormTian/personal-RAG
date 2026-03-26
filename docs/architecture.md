# 架构文档

本文档详细描述 Tiny RAG Demo 的系统架构、组件设计和实现原理。

## 📋 目录

- [架构概览](#架构概览)
- [系统架构图](#系统架构图)
- [组件说明](#组件说明)
- [数据流](#数据流)
- [技术选型](#技术选型)
- [核心算法](#核心算法)
- [存储设计](#存储设计)

## 架构概览

Tiny RAG Demo 采用分层架构设计，包含以下主要层次：

```
┌─────────────────────────────────────────────┐
│                Web Interface                │
│         (index.html + styles.css + app.js)  │
├─────────────────────────────────────────────┤
│                HTTP Server                  │
│              (web_app.py)                   │
├─────────────────────────────────────────────┤
│                RAG Engine                   │
│               (app.py)                      │
│  ┌──────────┐ ┌──────────┐ ┌────────────┐  │
│  │ Document │ │ Embedding│ │  Reranker  │  │
│  │  Parser  │ │ Backend  │ │  Backend   │  │
│  └──────────┘ └──────────┘ └────────────┘  │
├─────────────────────────────────────────────┤
│              Storage Layer                  │
│     (document_library + .index_cache.pkl)   │
└─────────────────────────────────────────────┘
```

## 系统架构图

```
┌─────────────────────────────────────────────────────────────────┐
│                          Client                                 │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐  │
│  │    Browser   │  │  CLI Tool    │  │   Python Script      │  │
│  └──────┬───────┘  └──────┬───────┘  └──────────┬───────────┘  │
└─────────┼─────────────────┼─────────────────────┼──────────────┘
          │                 │                     │
          └─────────────────┴─────────────────────┘
                            │ HTTP / Python API
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                       Web Server                                │
│                    ThreadingHTTPServer                          │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │              RagHTTPRequestHandler                        │  │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐ │  │
│  │  │   GET    │  │   POST   │  │ /api/ask │  │/api/...  │ │  │
│  │  └──────────┘  └──────────┘  └──────────┘  └──────────┘ │  │
│  └──────────────────────────────────────────────────────────┘  │
└──────────────────────────────┬──────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│                        RAG Engine                               │
│                           TinyRAG                               │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                    Document Processing                    │  │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐   │  │
│  │  │ File Scanner │→ │ Text Extract │→ │  Chunk Split │   │  │
│  │  └──────────────┘  └──────────────┘  └──────────────┘   │  │
│  └──────────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                    Indexing Pipeline                      │  │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐   │  │
│  │  │ Tokenization │→ │ Embedding    │→ │ BM25 Index   │   │  │
│  │  └──────────────┘  └──────────────┘  └──────────────┘   │  │
│  └──────────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                   Retrieval Pipeline                      │  │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐   │  │
│  │  │ Embedding    │→ │ Candidate    │→ │ Rerank       │   │  │
│  │  │ Search       │  │ Generation   │  │              │   │  │
│  │  └──────────────┘  └──────────────┘  └──────────────┘   │  │
│  └──────────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                   Answer Generation                       │  │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐   │  │
│  │  │ Sentence     │→ │ Score &      │→ │ Answer       │   │  │
│  │  │ Extraction   │  │ Filter       │  │ Format       │   │  │
│  │  └──────────────┘  └──────────────┘  └──────────────┘   │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

## 组件说明

### 1. Web 界面层 (web/)

**文件**: `index.html`, `styles.css`, `app.js`

**职责**:
- 提供用户交互界面
- 展示问答结果和检索上下文
- 显示文档库状态
- 触发重新入库操作

**技术特点**:
- 纯前端实现，无框架依赖
- 响应式设计，支持移动端
- 使用 Marked.js 渲染 Markdown
- REST API 通信

### 2. HTTP 服务层 (web_app.py)

**类**: `RagHTTPRequestHandler`

**职责**:
- 处理 HTTP 请求
- 路由分发
- 参数解析和验证
- 响应格式化

**端点映射**:

| 端点 | 方法 | 处理器 | 说明 |
|------|------|--------|------|
| `/` | GET | `do_GET` | 返回主页 |
| `/app.js` | GET | `do_GET` | 返回 JS 文件 |
| `/styles.css` | GET | `do_GET` | 返回 CSS 文件 |
| `/api/health` | GET | `do_GET` | 健康检查 |
| `/api/library` | GET | `do_GET` | 文档库信息 |
| `/api/ask` | GET/POST | `do_GET/do_POST` | 问答接口 |
| `/api/reload` | POST | `do_POST` | 重新入库 |

### 3. RAG 引擎层 (app.py)

#### 3.1 文档处理模块

**类**: `TinyRAG`
**方法**: `_discover_source_files`, `load_source_document`

**流程**:
```
document_library/
    ↓
递归扫描 (*.md, *.txt, *.doc, *.docx, *.pdf)
    ↓
文本提取 (根据文件类型选择提取器)
    ↓
文本标准化 (清理、格式化)
    ↓
文档对象 (SourceDocument)
```

**文本提取器**:

| 格式 | 提取方式 | 依赖 |
|------|---------|------|
| `.md/.txt` | 直接读取 | Python 内置 |
| `.doc/.docx` | `textutil` | macOS |
| `.pdf` | `pypdf` 或 Swift | pypdf / macOS |

#### 3.2 索引模块

**方法**: `_build_snapshot`

**流程**:
```
SourceDocuments
    ↓
文本分块 (chunk_text)
    ↓
Tokenization (tokenize)
    ↓
BM25 索引 (idf, avgdl)
    ↓
Embedding 生成 (embed_texts)
    ↓
IndexSnapshot (持久化到 .index_cache.pkl)
```

#### 3.3 检索模块

**方法**: `search`

**两阶段检索**:

**阶段 1: Embedding 召回**
```
Query → Tokenize → Embed → Cosine Similarity → Top-K Candidates
```

**阶段 2: Rerank 重排**
```
Candidates → BM25 Score → Title Match → Weighted Fusion → Final Ranking
```

**分数计算公式**:
```
final_score = retrieve_score * 0.60 + normalized_lexical * 0.30 + title_score * 0.10
```

#### 3.4 回答生成模块

**方法**: `answer`

**流程**:
```
Query + Search Hits
    ↓
句子提取 (split_sentences)
    ↓
词汇重叠评分
    ↓
分数过滤 (threshold: best_score * 0.35)
    ↓
去重 & 格式化
    ↓
RagResponse
```

### 4. Embedding 后端

#### 4.1 本地 Hash Embedding (默认)

**类**: `LocalHashEmbeddingBackend`

**原理**:
- 使用 SHA-256 哈希生成伪随机投影
- 将 token 映射到高维空间
- TF-IDF 加权求和
- L2 归一化

**特点**:
- 无需外部依赖
- 零 API 调用
- 固定 256 维
- 适合离线场景

#### 4.2 OpenAI 兼容 Embedding

**类**: `OpenAICompatibleEmbeddingBackend`

**原理**:
- 调用 OpenAI `/v1/embeddings` API
- 支持批量处理
- 支持多种模型

**配置**:
```bash
export OPENAI_API_KEY=sk-...
export OPENAI_EMBED_MODEL=text-embedding-3-small
export OPENAI_BASE_URL=https://api.openai.com
```

### 5. Reranker 后端

#### 5.1 本地启发式 Reranker (默认)

**类**: `LocalHeuristicReranker`

**策略**: `embedding+lexical-overlap`

**分数融合**:
```python
score = (
    retrieve_score * 0.60 +      # Embedding 相似度
    lexical_score * 0.30 +       # BM25 分数
    title_score * 0.10           # 标题匹配
)
```

#### 5.2 LLM Listwise Reranker

**类**: `OpenAICompatibleListwiseReranker`

**策略**: `embedding+llm-listwise-rerank`

**流程**:
1. 先使用本地启发式 rerank
2. 取前 N 个候选
3. 发送给 LLM 评分
4. 融合分数重新排序

**配置**:
```bash
export OPENAI_RERANK_MODEL=gpt-4o-mini
export OPENAI_RERANK_TIMEOUT=45
export OPENAI_RERANK_MAX_CANDIDATES=12
```

## 数据流

### 文档入库流程

```
┌──────────────┐
│   User Add   │
│   Documents  │
└──────┬───────┘
       │
       ▼
┌──────────────┐     ┌──────────────┐
│ File Scanner │────→│  Check Cache │
└──────────────┘     └──────┬───────┘
                            │ Cache Hit?
                   ┌────────┴────────┐
                   ▼                 ▼
            ┌──────────┐      ┌──────────┐
            │   Load   │      │ Extract  │
            │   Cache  │      │   Text   │
            └──────────┘      └────┬─────┘
                                   │
                                   ▼
                            ┌──────────┐
                            │   Split  │
                            │  Chunks  │
                            └────┬─────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────┐
│                    Index Pipeline                    │
│  ┌─────────┐    ┌─────────┐    ┌─────────────────┐ │
│  │ Tokenize│───→│ Embed   │───→│  Build BM25     │ │
│  │         │    │ Texts   │    │  Index          │ │
│  └─────────┘    └─────────┘    └────────┬────────┘ │
└─────────────────────────────────────────┼───────────┘
                                          │
                                          ▼
                                   ┌──────────┐
                                   │  Create  │
                                   │ Snapshot │
                                   └────┬─────┘
                                        │
                                        ▼
                                   ┌──────────┐
                                   │  Save    │
                                   │  Cache   │
                                   └──────────┘
```

### 查询处理流程

```
┌──────────────┐
│ User Query   │
└──────┬───────┘
       │
       ▼
┌──────────────┐
│  Parse &     │
│  Validate    │
└──────┬───────┘
       │
       ▼
┌─────────────────────────────────────────────┐
│           Phase 1: Retrieval                 │
│  ┌─────────┐    ┌─────────┐    ┌─────────┐ │
│  │ Tokenize│───→│ Embed   │───→│ Cosine  │ │
│  │ Query   │    │ Query   │    │ Search  │ │
│  └─────────┘    └─────────┘    └────┬────┘ │
└─────────────────────────────────────┼──────┘
                                      │
                                      ▼
                              ┌──────────────┐
                              │ Top-K        │
                              │ Candidates   │
                              └──────┬───────┘
                                     │
       ┌─────────────────────────────┼─────────────────────────────┐
       │                             │                             │
       ▼                             ▼                             ▼
┌─────────────┐              ┌─────────────┐              ┌─────────────┐
│ BM25 Score  │              │ Title Match │              │ Retrieve    │
│             │              │             │              │ Score       │
└──────┬──────┘              └──────┬──────┘              └──────┬──────┘
       │                            │                            │
       └────────────────────────────┼────────────────────────────┘
                                    │
                                    ▼
┌──────────────────────────────────────────────────────────────────┐
│              Phase 2: Reranking (if enabled)                      │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────────────┐  │
│  │  Heuristic  │───→│  LLM Score  │───→│  Weighted Fusion    │  │
│  │  Rerank     │    │  (optional) │    │  & Sort             │  │
│  └─────────────┘    └─────────────┘    └─────────────────────┘  │
└──────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌──────────────────────────────────────────────────────────────────┐
│              Phase 3: Answer Generation                           │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────────────┐  │
│  │  Sentence   │───→│  Score &    │───→│  Format & Return    │  │
│  │  Extraction │    │  Filter     │    │                     │  │
│  └─────────────┘    └─────────────┘    └─────────────────────┘  │
└──────────────────────────────────────────────────────────────────┘
```

## 技术选型

### 编程语言

| 组件 | 语言 | 说明 |
|------|------|------|
| 后端核心 | Python 3.8+ | 主要开发语言 |
| PDF 解析 | Swift | macOS 回退方案 |
| 前端 | HTML/CSS/JS | 原生 Web 技术 |

### 核心依赖

| 依赖 | 版本 | 用途 | 必需 |
|------|------|------|------|
| Python Standard Library | 3.8+ | 所有核心功能 | ✅ |
| pypdf | 6.9.2 | PDF 解析 | ❌ |

### 设计原则

1. **最小依赖**: 仅使用 Python 标准库实现核心功能
2. **可扩展**: 插件化架构支持多种后端
3. **高性能**: 缓存机制避免重复计算
4. **易用性**: 开箱即用，无需复杂配置

## 核心算法

### 1. 文本分词 (tokenize)

```python
def tokenize(text: str) -> List[str]:
    # 1. 转换为小写
    text = text.lower()
    
    # 2. 提取英文和数字
    tokens = re.findall(r"[a-z0-9]+", text)
    
    # 3. 提取中文并进行 n-gram
    for block in re.findall(r"[\u4e00-\u9fff]+", text):
        if len(block) == 1:
            tokens.append(block)
        else:
            for size in (2, 3):
                if len(block) >= size:
                    tokens.extend(block[i:i+size] for i in range(len(block)-size+1))
    
    return tokens
```

### 2. 文本分块 (chunk_text)

```python
def chunk_text(text: str, max_chars: int = 240, overlap: int = 1) -> List[str]:
    # 1. 分段（按标题和空行）
    paragraphs = split_paragraphs(text)
    
    # 2. 句子级别切分
    units = []
    for paragraph in paragraphs:
        units.extend(wrap_paragraph(paragraph, max_chars))
    
    # 3. 滑动窗口合并
    chunks = []
    current = []
    for unit in units:
        candidate = " ".join(current + [unit]).strip()
        if current and len(candidate) > max_chars:
            chunks.append(" ".join(current).strip())
            current = current[-overlap:] + [unit]
        else:
            current.append(unit)
    
    if current:
        chunks.append(" ".join(current).strip())
    
    return chunks
```

### 3. BM25 评分

```python
def bm25_score(query_tokens, chunk_tokens, idf, avgdl, k1=1.5, b=0.75):
    score = 0.0
    doc_len = sum(chunk_tokens.values())
    
    for token in query_tokens:
        if token not in chunk_tokens:
            continue
        tf = chunk_tokens[token]
        idf_val = idf.get(token, 0.0)
        
        numerator = idf_val * tf * (k1 + 1)
        denominator = tf + k1 * (1 - b + b * doc_len / avgdl)
        score += numerator / denominator
    
    return score
```

### 4. Local Hash Embedding

```python
def embed_texts(self, texts: Sequence[str]) -> List[Tuple[float, ...]]:
    vectors = []
    for text in texts:
        dense = [0.0] * self.dimensions
        token_counts = Counter(tokenize(text))
        
        for token, frequency in token_counts.items():
            weight = 1.0 + math.log(frequency)
            for idx, signed_weight in self._token_projection(token):
                dense[idx] += signed_weight * weight
        
        vectors.append(normalize_vector(dense))
    return vectors
```

### 5. 向量投影

```python
def _token_projection(self, token: str) -> List[Tuple[int, float]]:
    digest = hashlib.sha256(token.encode("utf-8")).digest()
    projection = []
    
    for offset in range(self.projections_per_token):
        start = offset * 4
        idx = int.from_bytes(digest[start:start+2], "big") % self.dimensions
        sign = 1.0 if digest[start+2] % 2 == 0 else -1.0
        magnitude = 0.35 + (digest[start+3] / 255.0)
        projection.append((idx, sign * magnitude))
    
    return projection
```

## 存储设计

### 文档存储

- **位置**: `document_library/` 目录
- **格式**: 原始文件格式（md, txt, doc, pdf 等）
- **组织**: 支持子目录，递归扫描

### 索引缓存

- **位置**: `.index_cache.pkl`
- **格式**: Python pickle
- **内容**: IndexSnapshot 对象
- **自动刷新**: 文档修改时间 > 缓存时间时重建

### IndexSnapshot 结构

```python
@dataclass(frozen=True)
class IndexSnapshot:
    library_dir: Path                    # 文档库目录
    documents: Tuple[SourceDocument, ...] # 原始文档
    skipped_files: Tuple[...]            # 跳过的文件
    chunks: Tuple[Chunk, ...]            # 文本块
    chunk_embeddings: Tuple[...]         # Embedding 向量
    chunk_token_counts: Tuple[Counter, ...] # Token 计数
    chunk_title_token_sets: Tuple[...]   # 标题 Token 集合
    idf: Dict[str, float]                # IDF 值
    avgdl: float                         # 平均文档长度
    supported_formats: Tuple[str, ...]   # 支持的格式
    embedding_backend: str               # Embedding 后端名称
    reranker_backend: str                # Reranker 后端名称
    retrieval_strategy: str              # 检索策略
    rerank_strategy: str                 # Rerank 策略
```

### 缓存策略

1. **命中条件**:
   - 缓存文件存在
   - 缓存时间 > 所有源文件修改时间
   - 后端配置一致

2. **失效条件**:
   - 文档库目录变更
   - 后端配置变更
   - 任何源文件修改

3. **手动刷新**:
   - Web 界面「重新入库」按钮
   - API `/api/reload` 端点
   - 删除 `.index_cache.pkl` 文件

---

**注意**: 详细实现请参考源码中的注释和类型定义。
