# API 文档

Tiny RAG Demo 提供 REST API 和 Python API 两种接口方式。

## 📋 目录

- [REST API](#rest-api)
  - [健康检查](#健康检查)
  - [文档库信息](#文档库信息)
  - [问答接口](#问答接口)
  - [重新入库](#重新入库)
- [Python API](#python-api)
  - [TinyRAG 类](#tinyrag-类)
  - [SearchHit](#searchhit)
  - [RagResponse](#ragresponse)
- [错误码](#错误码)
- [数据类型](#数据类型)

## REST API

Base URL: `http://127.0.0.1:8000`

### 健康检查

检查服务是否正常运行。

**请求**

```http
GET /api/health
```

**响应**

```json
{
  "status": "ok",
  "library_dir": "/path/to/document_library",
  "documents": 5,
  "chunks": 23,
  "supported_formats": [".doc", ".docx", ".md", ".markdown", ".pdf", ".txt"],
  "files": [...],
  "skipped": [],
  "embedding_backend": "local-hash-256d",
  "reranker_backend": "local-heuristic",
  "retrieval_strategy": "dense-embedding-cosine",
  "rerank_strategy": "embedding+lexical-overlap"
}
```

**字段说明**

| 字段 | 类型 | 说明 |
|------|------|------|
| `status` | string | 服务状态，"ok" 表示正常 |
| `library_dir` | string | 文档库目录路径 |
| `documents` | int | 已入库文档数量 |
| `chunks` | int | 切分后的文本块数量 |
| `supported_formats` | array | 支持的文件格式列表 |
| `files` | array | 文件详细信息列表 |
| `skipped` | array | 被跳过的文件列表 |
| `embedding_backend` | string | 使用的 embedding 后端 |
| `reranker_backend` | string | 使用的 reranker 后端 |
| `retrieval_strategy` | string | 检索策略 |
| `rerank_strategy` | string | 重排序策略 |

### 文档库信息

获取文档库的详细统计信息。

**请求**

```http
GET /api/library
```

**响应**: 同健康检查接口

### 问答接口

提交问题，获取基于文档库的答案。

**GET 请求**

```http
GET /api/ask?q=问题内容&top_k=3
```

**查询参数**

| 参数 | 类型 | 必需 | 说明 |
|------|------|------|------|
| `q` | string | 是 | 查询问题 |
| `top_k` | int | 否 | 召回条数，范围 1-8，默认 3 |

**POST 请求**

```http
POST /api/ask
Content-Type: application/json

{
  "query": "问题内容",
  "top_k": 3
}
```

**请求体字段**

| 字段 | 类型 | 必需 | 说明 |
|------|------|------|------|
| `query` | string | 是 | 查询问题 |
| `top_k` | int | 否 | 召回条数，默认 3 |

**成功响应**

```json
{
  "query": "Tiny RAG 有什么功能？",
  "answer_lines": [
    "本地运行，无需外部 API",
    "支持多种文档格式",
    "混合检索策略"
  ],
  "hits": [
    {
      "score": 0.8921,
      "retrieve_score": 0.9123,
      "rerank_score": 0.8921,
      "lexical_score": 0.7567,
      "title_score": 0.2345,
      "llm_score": 0.0000,
      "source": "demo.md",
      "title": "Tiny RAG Demo",
      "text": "这是一个轻量级的 RAG 系统演示。",
      "chunk_id": 0
    }
  ]
}
```

**响应字段**

| 字段 | 类型 | 说明 |
|------|------|------|
| `query` | string | 原始查询问题 |
| `answer_lines` | array | 生成的答案列表（句子级别） |
| `hits` | array | 命中的文档片段列表 |

**Hit 字段**

| 字段 | 类型 | 说明 |
|------|------|------|
| `score` | float | 最终综合分数（0-1） |
| `retrieve_score` | float | Embedding 召回分数 |
| `rerank_score` | float | Rerank 后的分数 |
| `lexical_score` | float | BM25 词汇匹配分数 |
| `title_score` | float | 标题匹配分数 |
| `llm_score` | float | LLM 评分（如启用） |
| `source` | string | 来源文件路径 |
| `title` | string | 文档标题 |
| `text` | string | 文本片段内容 |
| `chunk_id` | int | 文本块 ID |

**错误响应**

```json
{
  "error": "请输入问题。"
}
```

或

```json
{
  "error": "top_k 必须是整数。"
}
```

### 重新入库

重新扫描文档库并建立索引。

**请求**

```http
POST /api/reload
```

**成功响应**

```json
{
  "status": "ok",
  "message": "文档库重新入库完成。",
  "library_dir": "/path/to/document_library",
  "documents": 5,
  "chunks": 23,
  ...
}
```

**错误响应**

```json
{
  "error": "文档库目录不存在: /path/to/docs"
}
```

## Python API

### TinyRAG 类

核心 RAG 引擎类。

#### 构造函数

```python
TinyRAG(
    library_dir: Path,
    embedding_backend: Optional[EmbeddingBackend] = None,
    reranker_backend: Optional[RerankerBackend] = None
)
```

**参数**

| 参数 | 类型 | 必需 | 说明 |
|------|------|------|------|
| `library_dir` | Path | 是 | 文档库目录路径 |
| `embedding_backend` | EmbeddingBackend | 否 | 自定义 embedding 后端 |
| `reranker_backend` | RerankerBackend | 否 | 自定义 reranker 后端 |

#### 方法

##### `search(query: str, top_k: int = 3) -> List[SearchHit]`

执行检索，返回匹配的文档片段。

**参数**
- `query`: 查询字符串
- `top_k`: 返回结果数量（默认 3）

**返回**: `List[SearchHit]`

**示例**

```python
from app import TinyRAG
from pathlib import Path

rag = TinyRAG(Path("document_library"))
hits = rag.search("部署指南", top_k=5)

for hit in hits:
    print(f"{hit.chunk.source}: {hit.score:.3f}")
```

##### `answer(query: str, top_k: int = 3) -> RagResponse`

执行问答，返回答案和上下文。

**参数**
- `query`: 查询字符串
- `top_k`: 召回条数（默认 3）

**返回**: `RagResponse`

**示例**

```python
response = rag.answer("什么是 RAG？", top_k=3)

print("回答:")
for line in response.answer_lines:
    print(f"- {line}")

print("\n参考文档:")
for hit in response.hits:
    print(f"[{hit.chunk.source}] {hit.score:.3f}")
```

##### `stats() -> Dict[str, object]`

获取文档库统计信息。

**返回**: 包含统计信息的字典

**示例**

```python
stats = rag.stats()
print(f"文档数: {stats['documents']}")
print(f"Chunk 数: {stats['chunks']}")
print(f"Embedding: {stats['embedding_backend']}")
```

##### `list_documents() -> List[Dict[str, object]]`

列出所有已入库的文档。

**返回**: 文档信息列表

**示例**

```python
docs = rag.list_documents()
for doc in docs:
    print(f"{doc['source']} - {doc['title']}")
```

##### `reload(library_dir: Optional[Path] = None) -> None`

重新加载文档库。

**参数**
- `library_dir`: 新的文档库目录（可选，默认为当前目录）

**示例**

```python
# 重新扫描当前目录
rag.reload()

# 切换到新目录
rag.reload(Path("/new/library/path"))
```

### SearchHit

检索结果数据类。

```python
@dataclass
class SearchHit:
    chunk: Chunk           # 文本块
    score: float          # 最终分数
    retrieve_score: float # Embedding 分数
    rerank_score: float   # Rerank 分数
    lexical_score: float  # BM25 分数
    title_score: float    # 标题匹配分数
    llm_score: float      # LLM 评分
```

### RagResponse

问答响应数据类。

```python
@dataclass
class RagResponse:
    query: str            # 查询问题
    answer_lines: List[str]  # 答案行列表
    hits: List[SearchHit]    # 命中的上下文
```

**方法**

##### `to_dict() -> Dict[str, object]`

转换为字典格式（用于 JSON 序列化）。

**示例**

```python
import json

response = rag.answer("问题")
json_str = json.dumps(response.to_dict(), ensure_ascii=False, indent=2)
print(json_str)
```

## 错误码

### HTTP 状态码

| 状态码 | 说明 | 场景 |
|--------|------|------|
| 200 | OK | 请求成功 |
| 400 | Bad Request | 参数错误（如 query 为空） |
| 404 | Not Found | 接口不存在 |
| 500 | Internal Server Error | 服务器内部错误 |

### 错误消息

| 错误消息 | 说明 | 解决方案 |
|----------|------|----------|
| `请输入问题。` | query 参数为空 | 提供非空的问题文本 |
| `top_k 必须是整数。` | top_k 格式错误 | 提供 1-8 之间的整数 |
| `请求体不是合法 JSON。` | POST 请求体格式错误 | 检查 JSON 格式 |
| `文档库目录不存在` | 指定的目录不存在 | 检查路径是否正确 |
| `文档库是空的` | 目录中没有支持的文件 | 添加支持的文档格式 |

### 异常类型

| 异常 | 说明 | 处理建议 |
|------|------|----------|
| `FileNotFoundError` | 文档库目录或文件不存在 | 检查路径和文件 |
| `ValueError` | 不支持的文件格式 | 使用支持的格式 |
| `RuntimeError` | 文档解析失败 | 检查文件完整性 |
| `RuntimeError` | API 请求失败 | 检查网络连接和 API 配置 |

## 数据类型

### Chunk

```python
@dataclass(frozen=True)
class Chunk:
    chunk_id: int     # 文本块唯一 ID
    source: str       # 来源文件路径
    title: str        # 文档标题
    text: str         # 文本内容
```

### SourceDocument

```python
@dataclass(frozen=True)
class SourceDocument:
    source: str       # 相对路径
    title: str        # 文档标题
    text: str         # 完整文本
    file_type: str    # 文件类型
```

### CandidateScore

```python
@dataclass(frozen=True)
class CandidateScore:
    index: int              # chunk 索引
    retrieve_score: float   # Embedding 分数
    lexical_score: float    # BM25 分数
    title_score: float      # 标题匹配分数
    rerank_score: float     # 重排序分数
    llm_score: float = 0.0  # LLM 评分
```

## 使用示例

### cURL 示例

```bash
# 健康检查
curl http://localhost:8000/api/health

# 提交问题（GET）
curl "http://localhost:8000/api/ask?q=什么是RAG&top_k=3"

# 提交问题（POST）
curl -X POST http://localhost:8000/api/ask \
  -H "Content-Type: application/json" \
  -d '{"query":"什么是RAG","top_k":3}'

# 重新入库
curl -X POST http://localhost:8000/api/reload
```

### Python 示例

```python
import requests

# 提交问题
response = requests.post(
    "http://localhost:8000/api/ask",
    json={"query": "什么是RAG", "top_k": 3}
)
data = response.json()

print("回答:", data["answer_lines"])
print("命中:", len(data["hits"]), "条上下文")
```

### JavaScript 示例

```javascript
// 提交问题
fetch('/api/ask', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ query: '什么是RAG', top_k: 3 })
})
.then(response => response.json())
.then(data => {
  console.log('回答:', data.answer_lines);
  console.log('命中:', data.hits.length, '条上下文');
});
```

---

**注意**: 更多实现细节请参考源码中的类型定义。
