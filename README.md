# RAG 系统 - 生产级版本

一个生产就绪的检索增强生成系统，采用模块化架构、支持异步处理和完善的监控体系。

## 目录

- [系统架构](#系统架构)
- [模块详解](#模块详解)
- [核心优势](#核心优势)
- [优化建议](#优化建议)
- [功能特性](#功能特性)
- [安装部署](#安装部署)
- [配置说明](#配置说明)
- [使用指南](#使用指南)
- [开发指南](#开发指南)

---

## 系统架构

### 整体架构图

```
┌─────────────────────────────────────────────────────────────────────────┐
│                              前端层                                      │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │  React + TypeScript + Ant Design + React Query                   │   │
│  │  - 搜索界面 │ 文档库管理 │ 上传历史                              │   │
│  └─────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼ HTTP/REST API
┌─────────────────────────────────────────────────────────────────────────┐
│                              API 层                                      │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────┐    │
│  │   安全中间件  │  │  验证中间件  │  │    路由     │  │  健康检查 │    │
│  │              │  │              │  │   (REST)    │  │          │    │
│  └──────────────┘  └──────────────┘  └──────────────┘  └──────────┘    │
│  端点: /api/ask, /api/search, /api/upload, /api/files, /health          │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                            RAG 引擎                                      │
│  ┌────────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────┐  │
│  │   文档加载器   │  │   索引管理   │  │    搜索引擎   │  │  答案生成 │  │
│  │     注册表     │  │    快照      │  │              │  │          │  │
│  └────────────────┘  └──────────────┘  └──────────────┘  └──────────┘  │
│  核心特性: 缓存、指标、线程安全、异步支持                                 │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                    ┌───────────────┼───────────────┐
                    ▼               ▼               ▼
┌───────────────────────┐ ┌──────────────────┐ ┌──────────────────┐
│     嵌入后端          │ │    重排序后端    │ │     缓存层       │
│ ┌───────────────────┐ │ │ ┌──────────────┐ │ │ ┌──────────────┐ │
│ │   本地哈希嵌入    │ │ │ │  本地启发式  │ │ │ │   文件缓存   │ │
│ │   (256维, 基于哈希)│ │ │ │   重排序器   │ │ │ │ (gzip+pickle)│ │
│ └───────────────────┘ │ │ └──────────────┘ │ │ └──────────────┘ │
│ ┌───────────────────┐ │ │ ┌──────────────┐ │ └──────────────────┘
│ │   OpenAI 兼容     │ │ │ │ OpenAI LLM   │ │
│ │   (API 集成)      │ │ │ │ 列表式重排序  │ │
│ └───────────────────┘ │ │ │ └──────────────┘ │
└───────────────────────┘ │ └──────────────────┘
                          └─────────────────────┘
```

### 技术栈

| 层级 | 技术 |
|------|------|
| 前端 | React 18 + TypeScript + Ant Design + Vite |
| 后端 API | FastAPI + Python 3.10+ |
| 文档处理 | 自定义加载器 (PDF、Word、Markdown、Text) |
| 嵌入模型 | 本地哈希 (256维) / OpenAI API |
| 重排序 | 本地启发式 / OpenAI LLM |
| 缓存 | 基于文件 (gzip + pickle) |
| 测试 | pytest + pytest-asyncio |

---

## 模块详解

### 1. 前端 (`/web-new/`)

**用途**: 基于 React 的现代化 Web 界面，用于文档管理和搜索

**核心组件**:
- **搜索界面**: 查询输入、top-k 配置、搜索历史
- **文档库管理**: 文档上传（拖拽）、文件列表（元数据）、上传历史
- **结果展示**: 生成答案（带引用来源）、检索片段（相关性分数）

**架构模式**:
- 基于特性的文件夹结构 (`features/search/`、`features/library/`、`features/result/`)
- React Query 管理服务端状态（缓存、后台刷新）
- Zustand 管理客户端状态（主题、搜索历史）
- 国际化支持（中英文）

**API 集成**:
- Axios 客户端，带拦截器处理错误
- TypeScript 接口实现类型安全的 API 函数

---

### 2. API 层 (`/rag_system/api/`)

**用途**: RESTful API 端点，集成安全和验证功能

**模块组成**:

#### 2.1 服务器 (`server.py`)
- FastAPI 应用工厂，带生命周期管理
- CORS 中间件支持跨域请求
- 全局异常处理器，返回结构化错误响应

#### 2.2 路由
- `upload.py`: 文件上传端点（验证：最大100MB、支持的扩展名）
- `files.py`: 文件列表和删除端点
- `library.py`: 文档库统计和重载功能
- `history.py`: 上传历史追踪（SQLite 后端）

#### 2.3 安全 (`security.py`)
- **APIKeyValidator**: 可选的 X-API-Key 请求头验证
- **RateLimiter**: 滑动窗口限流（默认：100 请求/分钟）
- **InputValidator**: 查询净化、长度限制（最大1000字符）
- **SecurityMiddleware**: 组合安全功能（健康检查可配置跳过）

#### 2.4 文档加载器 (`loader.py`)
注册表模式实现可扩展文档加载：

| 加载器 | 支持的扩展名 | 提取方法 |
|--------|-----------|-------------------|
| `TextDocumentLoader` | .md、.markdown、.txt | Python 文件读取（自动编码检测） |
| `WordDocumentLoader` | .doc、.docx | macOS textutil 命令（原生） |
| `PDFDocumentLoader` | .pdf | pypdf 库（Swift 回退） |

**特性**:
- 自动标题提取（从标题或首行）
- 多编码支持（UTF-8、UTF-8-SIG、GB18030）
- 文本规范化（移除空字节、折叠空白）

---

### 3. 核心模块 (`/rag_system/core/`)

**用途**: 基础抽象和数据模型

**数据模型**:
- `SourceDocument`: 源文档（source、title、text、file_type）
- `Chunk`: 文本片段（chunk_id、source、title、text）
- `CandidateScore`: 重排序评分数据（index、retrieve_score、lexical_score、title_score）
- `SearchHit`: 搜索结果（chunk、scores、metadata）
- `RagResponse`: 完整响应（query、answer_lines、hits、metadata）
- `IndexSnapshot`: 不可变索引状态（线程安全检索）

**抽象基类**:
- `EmbeddingBackend`: 嵌入实现接口
- `RerankerBackend`: 重排序实现接口
- `DocumentLoader`: 文档加载器接口
- `SearchEngine`: 搜索引擎接口

---

### 4. RAG 引擎 (`/rag_system/rag_engine.py`)

**用途**: 核心编排组件，实现 `SearchEngine` 接口

**职责**:
1. **文档发现**: 扫描文档库目录，通过注册表加载文档
2. **文本分块**: 段落感知分块，可配置重叠
3. **索引构建**: 生成嵌入和 BM25 统计信息，保存到缓存
4. **密集检索**: 余弦相似度计算（归一化嵌入）
5. **词汇评分**: BM25 算法关键词匹配
6. **重排序**: 组合语义（60%）、词汇（30%）和标题（10%）分数
7. **答案生成**: 从顶级片段提取相关句子

**线程安全**:
- `threading.RLock` 保护快照访问
- 不可变 `IndexSnapshot` 支持安全并发读取
- 支持后台重载

---

### 5. 嵌入后端 (`/rag_system/backends/embedding.py`)

**两种后端选项**:

| 后端 | 描述 | 适用场景 |
|---------|-------------|----------|
| `LocalHashEmbeddingBackend` | 基于哈希的本地嵌入（256维） | 离线部署、无 API 成本、确定性输出 |
| `OpenAICompatibleEmbeddingBackend` | OpenAI API（带重试逻辑） | 高质量嵌入、需要 API 密钥 |
| `CachedEmbeddingBackend` | 嵌入缓存装饰器 | 减少 API 调用、提升性能 |

**特性**:
- `aiohttp` 连接池支持异步 HTTP
- 信号量并发限制（默认：5 并发）
- 指数退避重试（带抖动）
- 批处理（默认：32 项/批次）
- 本地哈希使用 xxHash 算法实现快速、确定性向量

---

### 6. 重排序后端 (`/rag_system/backends/reranker.py`)

**两种后端选项**:

| 后端 | 描述 | 策略 |
|---------|-------------|----------|
| `LocalHeuristicReranker` | 基于规则的评分 | 60% 语义 + 30% 词汇 + 10% 标题 |
| `OpenAICompatibleListwiseReranker` | 基于 LLM 的列表式评分 | 查询 + 候选发送至 LLM 返回 0-1 分数 |

**评分公式**:
- **本地启发式**: `score = 0.6 * semantic + 0.3 * lexical_norm + 0.1 * title_overlap`
- **LLM 重排序**: `score = 0.45 * heuristic + 0.55 * llm_score`（失败时回退到启发式）

---

### 7. 配置 (`/rag_system/config/`)

**用途**: 分层配置管理

**配置类**:
- `EmbeddingConfig`: 后端选择、维度、投影
- `RerankerConfig`: 重排序后端、模型选择
- `RetrievalConfig`: BM25 参数（k1=1.5、b=0.75）、top_k
- `ChunkingConfig`: max_chars（240）、overlap（1）
- `CacheConfig`: 启用、cache_dir、压缩
- `SecurityConfig`: 限流、API 密钥、CORS
- `ServerConfig`: 主机、端口、工作进程

**配置优先级**（从高到低）:
1. 环境变量
2. YAML/JSON 配置文件
3. 默认值

---

### 8. 服务 (`/rag_system/services/`)

**文件服务** (`file_service.py`):
- 安全文件上传（防止路径遍历）
- 文件名净化（移除特殊字符）
- 可配置最大值的文件大小限制
- 白名单扩展名验证
- 重复检测和孤立文件清理

**历史服务** (`history_service.py`):
- SQLite 数据库存储上传记录
- 记录：original_name、saved_name、file_path、status、timestamps
- 支持状态：SUCCESS、FAILED、PENDING、DELETED
- 异步操作，带连接池

---

### 9. 工具类 (`/rag_system/utils/`)

**文本处理** (`text.py`):
- `tokenize()`: 英文分词 + 中文 n-gram（2-3 字符）
- `chunk_text()`: 段落感知分块，句子边界检测
- `split_sentences()`: 智能句子分割，处理缩写
- `cosine_similarity()`: 优化的向量相似度计算
- `normalize_vector()`: L2 归一化嵌入

**文件操作** (`file.py`):
- 多编码文本文件读取（带回退）
- macOS textutil 提取 Word 文档
- pypdf 或 Swift 脚本回退提取 PDF

**重试逻辑** (`retry.py`):
- `@retry` 装饰器，支持指数退避
- 可配置最大尝试次数、延迟、退避因子
- 支持异步和同步函数
- 基于异常类型的条件重试

---

### 10. 监控 (`/rag_system/monitoring/`)

**指标** (`metrics.py`):
- `MetricsCollector`: 线程安全指标收集（RLock）
- 指标类型：计数器、计量器、计时器
- 追踪指标：embedding_time_ms、retrieval_time_ms、rerank_time_ms、search_total_time_ms
- 可配置保留期（默认：1000 个数据点）

**健康检查** (`health.py`):
- `HealthCheck` 管理器，带后台监控线程
- 组件检查：文档库、嵌入后端、重排序后端
- 状态级别：HEALTHY、DEGRADED、UNHEALTHY、UNKNOWN
- 自动检查间隔（默认：30 秒）

**日志** (`logging_config.py`):
- 结构化 JSON 日志，可配置格式
- 日志级别：DEBUG、INFO、WARNING、ERROR、CRITICAL
- 文件轮转支持
- 请求 ID 追踪（分布式追踪）

---

### 11. 异常处理 (`/rag_system/exceptions/`)

**自定义异常层次结构**:
```
RAGError (基类)
├── ConfigurationError（配置错误）
├── ValidationError（验证错误）
├── AuthenticationError（认证错误）
├── RateLimitError（限流错误）
├── RetrievalError（检索错误）
├── EmbeddingError（嵌入错误）
├── ExternalServiceError（外部服务错误）
└── 文件相关错误
    ├── FileTooLargeError（文件过大）
    ├── InvalidFileTypeError（无效文件类型）
    └── FileNotFoundError（文件未找到）
```

每个异常包含：
- HTTP 状态码
- 错误消息
- 结构化 `to_dict()` 方法（用于 API 响应）

---

## 核心优势

### 1. 模块化架构
- **职责分离**: 每个模块有单一、明确的职责
- **可插拔后端**: 轻松切换嵌入/重排序实现，无需修改核心逻辑
- **注册表模式**: 文档加载器可扩展，无需修改现有代码
- **依赖注入**: 通过构造函数注入实现干净的依赖管理

### 2. 性能优化
- **异步/等待**: 完整异步 I/O，提升并发和资源利用率
- **连接池**: API 调用复用 HTTP 连接，减少开销
- **批处理**: 嵌入 API 的 32 项批次最小化往返次数
- **缓存**: 压缩索引缓存（gzip + pickle）消除冗余处理
- **线程安全**: 基于 RLock 的同步支持并发读取和安全写入
- **中文文本优化**: N-gram 分词（2-3 字符）提升中文搜索质量

### 3. 生产级特性
- **健康监控**: 组件级状态的全面健康检查
- **指标收集**: 延迟、吞吐量和错误率追踪
- **限流**: 滑动窗口防滥用（默认 100 请求/分钟）
- **输入验证**: 安全导向的净化和边界检查
- **错误处理**: 结构化异常，有意义的 HTTP 状态码
- **优雅降级**: 外部 API 失败时回退到本地后端

### 4. 开发者体验
- **类型安全**: TypeScript 前端，严格类型检查
- **全面测试**: 单元测试、集成测试、API 测试、性能测试
- **配置灵活**: YAML/JSON 配置，环境变量覆盖
- **热重载**: 开发服务器代码变更自动重载
- **结构化日志**: JSON 格式日志，易于解析和分析

### 5. 多格式文档支持
- **文本文件**: Markdown、纯文本（编码检测）
- **Word 文档**: .doc 和 .docx（macOS textutil 或 python-docx）
- **PDF 文件**: pypdf 提取（Swift 回退处理复杂 PDF）
- **智能标题提取**: 自动从标题提取文档标题

### 6. 混合搜索策略
- **密集检索**: 语义相似度嵌入捕获含义
- **词汇评分**: BM25 算法关键词匹配
- **多阶段重排序**: 组合语义（60%）、词汇（30%）、标题（10%）分数
- **句子级答案生成**: 提取相关句子而非整个片段

### 7. 健壮性
- **重试机制**: 指数退避（带抖动）实现弹性 API 调用
- **断路器模式**: 防止级联故障
- **边界验证**: API 层输入净化
- **文件安全**: 防止路径遍历、扩展名验证

---

## 优化建议

### 高优先级

#### 1. 向量数据库集成
**现状**: 基于 numpy 数组的余弦相似度（内存中）
**问题**: O(n) 复杂度，无法扩展到超过 ~1万 文档
**解决方案**:
- 集成 FAISS（Facebook AI 相似度搜索）实现近似最近邻
- 或使用专用向量数据库：Pinecone、Weaviate、Milvus
- 预期改进：查询时间从 O(n) 降至 O(log n)

#### 2. 增量索引更新
**现状**: 每次文档变更都完全重新索引
**问题**: 添加单个文档需要 O(n) 处理时间
**解决方案**:
- 实现增量索引更新
- 仅追加索引，带版本控制
- 后台索引合并
- 预期改进：添加文档从 O(n) 降至 O(1) 摊销

#### 3. 查询缓存
**现状**: 无查询结果缓存
**问题**: 重复相同查询会重新计算嵌入和搜索
**解决方案**:
- Redis 或内存 LRU 缓存查询结果
- 缓存键：hash(query + top_k)
- 基于 TTL 的过期（如 1 小时）
- 预期改进：常见查询 90%+ 缓存命中率

### 中优先级

#### 4. 嵌入模型优化
**现状**: 本地基于哈希（确定性但质量低）或 OpenAI API（高延迟）
**问题**: 本地嵌入缺乏语义质量；API 调用增加 100-500ms 延迟
**解决方案**:
- 添加 ONNX Runtime 支持本地 Transformer 模型（all-MiniLM-L6-v2）
- 量化嵌入（int8）加速推理
- GPU 加速支持
- 预期改进：50-100ms 本地嵌入 vs 300-500ms API

#### 5. 并行文档处理
**现状**: 顺序文档加载和分块
**问题**: 大型文档库初始化缓慢
**解决方案**:
- 使用 ThreadPoolExecutor 并行处理文档
- asyncio.gather 异步文档加载
- 预期改进：初始化速度提升 3-5 倍

#### 6. BM25 索引持久化
**现状**: 每次重载都重新计算 BM25 统计信息
**问题**: 大型文档库的开销为 O(n)
**解决方案**:
- 与嵌入一起持久化 BM25 索引
- 存储词频和文档长度
- 预期改进：重载时消除 BM25 计算时间

#### 7. 前端包优化
**现状**: 单一大包，无代码分割
**问题**: 初始页面加载缓慢
**解决方案**:
- 按路由实现代码分割
- 懒加载重型组件（PDF 查看器、图表）
- Tree-shake 未使用的 Ant Design 组件
- 预期改进：初始包大小减少 50%+

### 低优先级

#### 8. 高级重排序模型
**现状**: 简单启发式或 OpenAI LLM 评分
**问题**: 启发式缺乏细微差别；LLM 成本高
**解决方案**:
- 添加交叉编码器模型（如 ms-marco-MiniLM-L-6-v2）
- 领域特定的微调重排序器
- 重排序器分数缓存
- 预期改进：更低成本下更好的排序质量

#### 9. 查询扩展
**现状**: 精确查询匹配
**问题**: 使用不同术语时遗漏相关文档
**解决方案**:
- 使用 WordNet 进行同义词扩展
- 基于 LLM 的查询重写
- 伪相关反馈
- 预期改进：召回率提升 10-20%

#### 10. 文档预处理管道
**现状**: 基础文本提取
**问题**: 表格、页眉、页脚被视为普通文本
**解决方案**:
- 结构化文档解析（表格、列表、标题）
- 语义分块（保留段落边界）
- 扫描 PDF 的 OCR
- 预期改进：更好的片段质量，更准确的检索

#### 11. 可观测性增强
**现状**: 基础指标和健康检查
**问题**: 查询性能可见性有限
**解决方案**:
- 分布式追踪（OpenTelemetry）
- 查询性能分析仪表板
- 嵌入质量监控（漂移检测）
- 告警集成（PagerDuty、Slack）

#### 12. 安全加固
**现状**: 基础限流和输入验证
**问题**: 无针对复杂攻击的保护
**解决方案**:
- 内容安全策略（CSP）请求头
- 历史数据库的 SQL 注入防护
- 基于 IP 的限流 DDoS 防护
- 安全事件的审计日志

---

## 功能特性

- **模块化架构**: 职责分离，抽象基类
- **异步/等待支持**: 完整异步 I/O 提升性能
- **连接池**: 高效 HTTP 连接管理
- **重试机制**: 指数退避实现弹性的外部 API 调用
- **结构化日志**: JSON 格式日志便于可观测性
- **健康检查**: 全面系统健康监控
- **限流**: 防滥用保护（默认 100 请求/分钟）
- **输入验证**: 安全导向的输入净化
- **配置管理**: YAML/JSON 配置，热重载
- **依赖注入**: 干净的依赖管理

---

## 安装部署

```bash
# 克隆仓库
cd rag_system

# 安装依赖
pip install -e .

# 或安装开发依赖
pip install -e ".[dev]"

# 安装前端依赖
cd web-new
npm install
```

---

## 配置说明

创建 `config.yaml` 文件：

```yaml
server:
  host: "127.0.0.1"
  port: 8000
  workers: 1

embedding:
  backend: "local-hash"  # 或 "openai-compatible"
  dimensions: 256
  projections_per_token: 8
  # OpenAI 后端配置：
  # api_key: "${OPENAI_API_KEY}"
  # model: "text-embedding-3-small"
  # base_url: "https://api.openai.com"

reranker:
  backend: "local-heuristic"  # 或 "openai-compatible"
  # OpenAI 后端配置：
  # api_key: "${OPENAI_API_KEY}"
  # model: "gpt-4"

retrieval:
  top_k: 3
  bm25_k1: 1.5
  bm25_b: 0.75

chunking:
  max_chars: 240
  overlap: 1

cache:
  enabled: true
  cache_dir: ".index_cache"

logging:
  level: "INFO"
  format: "json"

monitoring:
  enabled: true
  health_check_interval: 30

security:
  rate_limit_enabled: true
  rate_limit_requests: 100
  rate_limit_window: 60
  max_query_length: 1000
  max_file_size: 104857600  # 100MB
```

### 环境变量

| 变量 | 描述 | 默认值 |
|----------|-------------|---------|
| `OPENAI_API_KEY` | OpenAI API 密钥 | - |
| `OPENAI_EMBED_MODEL` | OpenAI 嵌入模型 | text-embedding-3-small |
| `OPENAI_RERANK_MODEL` | OpenAI 重排序模型 | gpt-4 |
| `OPENAI_BASE_URL` | OpenAI API 基础 URL | https://api.openai.com |
| `RAG_HOST` | 服务器主机 | 127.0.0.1 |
| `RAG_PORT` | 服务器端口 | 8000 |
| `RAG_DEBUG` | 调试模式 | false |

---

## 使用指南

### 启动后端

```bash
# 使用默认设置运行
python -m rag_system

# 使用自定义文档库目录运行
python -m rag_system --library-dir ./my_docs

# 交互模式运行
python -m rag_system --interactive

# 仅启动 API 服务器
python -m rag_system.api.server

# 或直接 uvicorn
uvicorn rag_system.api.server:create_app --factory --reload
```

### 启动前端

```bash
cd web-new
npm run dev
```

### Python API

```python
from rag_system import RAGEngine

# 初始化引擎
engine = RAGEngine(library_dir="./documents")

# 提问
response = engine.answer("什么是机器学习？")
print(response.answer_lines)

# 搜索文档
hits = engine.search("神经网络", top_k=5)
for hit in hits:
    print(f"{hit.score:.3f}: {hit.chunk.text[:100]}...")

# 异步使用
import asyncio

async def main():
    response = await engine.answer_async("你的问题？")
    print(response.answer_lines)

asyncio.run(main())
```

### API 端点

```bash
# 健康检查
curl http://localhost:8000/health

# 提问（带答案生成）
curl -X POST http://localhost:8000/api/ask \
  -H "Content-Type: application/json" \
  -d '{"query": "什么是人工智能？", "top_k": 3}'

# 搜索（仅检索）
curl "http://localhost:8000/api/search?q=机器学习&top_k=5"

# 获取文档库统计
curl http://localhost:8000/api/library

# 重载文档库
curl -X POST http://localhost:8000/api/reload

# 上传文件
curl -X POST http://localhost:8000/api/upload \
  -F "file=@document.pdf"

# 列出文件
curl http://localhost:8000/api/files

# 删除文件
curl -X DELETE http://localhost:8000/api/files/document.pdf

# 获取上传历史
curl http://localhost:8000/api/upload-history
```

---

## 开发指南

### 项目结构

```
rag_system/
├── api/                    # API 层 (FastAPI)
│   ├── loader.py          # 文档加载器
│   ├── security.py        # 安全中间件
│   ├── server.py          # HTTP 服务器
│   ├── routes/            # API 路由
│   └── deps.py            # 依赖
├── backends/              # 后端实现
│   ├── embedding.py       # 嵌入后端
│   └── reranker.py        # 重排序后端
├── config/                # 配置管理
│   ├── settings.py        # 配置类
│   └── loader.py          # 配置加载器
├── core/                  # 核心抽象
│   ├── base.py            # 基类和模型
│   └── dependency_injection.py  # 依赖注入容器
├── exceptions/            # 异常处理
│   ├── base.py            # 自定义异常
│   └── handlers.py        # 异常处理器
├── monitoring/            # 监控与日志
│   ├── logging_config.py  # 结构化日志
│   ├── metrics.py         # 指标收集
│   └── health.py          # 健康检查
├── services/              # 业务逻辑
│   ├── file_service.py    # 文件操作
│   └── history_service.py # 上传历史
├── utils/                 # 工具类
│   ├── retry.py           # 重试逻辑
│   ├── text.py            # 文本处理
│   ├── file.py            # 文件操作
│   └── json_utils.py      # JSON 工具
├── __init__.py            # 包导出
└── rag_engine.py          # 主 RAG 引擎

web-new/                   # React 前端
├── src/
│   ├── pages/             # 页面组件
│   ├── features/          # 特性模块
│   ├── components/        # 共享组件
│   ├── services/          # API 客户端
│   ├── hooks/             # 自定义 hooks
│   ├── stores/            # 状态管理
│   ├── utils/             # 工具类
│   └── types/             # TypeScript 类型

config/                    # 基础设施配置
├── nginx.conf             # Nginx 反向代理
├── prometheus.yml         # Prometheus 监控
└── logging.conf           # 日志配置

tests/                     # 测试套件
├── unit/                  # 单元测试
├── integration/           # 集成测试
├── api/                   # API 测试
└── performance/           # 负载测试
```

### 运行测试

```bash
# 运行所有测试
pytest tests/ -v --cov=rag_system

# 运行特定测试类别
pytest tests/unit/ -v
pytest tests/integration/ -v
pytest tests/api/ -v

# 运行并生成覆盖率报告
pytest tests/ --cov=rag_system --cov-report=html
```

### 代码质量

```bash
# 运行代码检查
flake8 rag_system

# 运行类型检查
mypy rag_system

# 格式化代码
black rag_system
isort rag_system

# 安全扫描
bandit -r rag_system
```

### Docker

```bash
# 构建镜像
docker build -t rag-system .

# 运行容器
docker run -p 8000:8000 -v $(pwd)/documents:/app/document_library rag-system

# 使用 docker-compose
docker-compose up -d
```

---

## 许可证

MIT License

---

## 贡献指南

1. Fork 仓库
2. 创建特性分支 (`git checkout -b feature/amazing-feature`)
3. 提交更改 (`git commit -m '添加特性'`)
4. 推送到分支 (`git push origin feature/amazing-feature`)
5. 发起 Pull Request

---

## 支持

如有问题或建议，请在 GitHub 上提交 Issue。
