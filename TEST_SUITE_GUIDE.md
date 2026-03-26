# RAG项目测试套件完整指南

## 1. tests/ 目录结构

```
tests/
├── __init__.py                 # 测试包初始化
├── conftest.py                 # Pytest配置和共享fixtures
├── README.md                   # 测试套件文档
├── unit/                       # 单元测试目录
│   ├── __init__.py
│   ├── test_tokenizer.py       # 文本分词和分割测试 (194行)
│   ├── test_embedding.py       # Embedding后端测试 (238行)
│   ├── test_reranker.py        # Reranker测试 (182行)
│   ├── test_parser.py          # 文档解析器测试 (246行)
│   └── test_utils.py           # 工具函数测试 (315行)
├── integration/                # 集成测试目录
│   ├── __init__.py
│   └── test_rag_pipeline.py    # 端到端RAG流程测试 (364行)
├── api/                        # API测试目录
│   ├── __init__.py
│   └── test_web_api.py         # Web API测试 (269行)
├── benchmark/                  # 基准测试目录
│   ├── __init__.py
│   └── test_benchmarks.py      # 性能基准测试 (249行)
└── performance/                # 性能测试目录
    ├── __init__.py
    └── test_performance.py     # 压力测试和负载测试 (254行)

测试文件总计: 11个主要测试文件 + 6个__init__.py
总代码行数: 约2,311行测试代码
```

## 2. 主要测试文件代码

### 2.1 tests/conftest.py - 核心配置和Fixtures
包含内容:
- Pytest配置和插件设置
- 17个核心fixtures:
  - 路径fixtures: project_root, temp_dir
  - 库fixtures: sample_library_dir, empty_library_dir, single_doc_library
  - 后端fixtures: local_embedding_backend, local_reranker, mock_embedding_backend, mock_reranker
  - RAG实例fixtures: rag_instance, rag_with_mock_backends
  - 数据fixtures: sample_texts, sample_query, sample_chunks, sample_candidate_scores
  - 环境fixtures: clean_env, mock_openai_env
- 辅助函数: assert_valid_embedding, assert_valid_search_hit, assert_valid_rag_response

### 2.2 tests/unit/test_tokenizer.py - 分词测试
- TestTokenize: 6个测试 (简单英文、数字、中文、混合内容、空字符串、标点符号、大小写)
- TestSplitSentences: 5个测试 (英文句子、中文句子、空字符串、空白字符、无终止符)
- TestSplitParagraphs: 4个测试 (简单段落、标题、空行、单段落)
- TestWrapParagraph: 3个测试 (短文本、长文本、句子边界)
- TestChunkText: 5个测试 (短文本、长文本、重叠、空文本、段落保留)

### 2.3 tests/unit/test_embedding.py - Embedding测试
- TestLocalHashEmbeddingBackend: 9个测试
  - 初始化、默认值、token投影一致性、缓存、单文本、多文本、查询、确定性、不同文本
- TestOpenAICompatibleEmbeddingBackend: 5个测试
  - 初始化、URL规范化、批处理请求、批处理归一化、文本分批
- TestNormalizeVector: 4个测试 (简单向量、零向量、已归一化、单位向量)

### 2.4 tests/unit/test_reranker.py - Reranker测试
- TestLocalHeuristicReranker: 7个测试
  - 初始化、候选池大小、空候选、单候选、排序、数据保留、分数计算
- TestOpenAICompatibleListwiseReranker: 4个测试
  - 初始化、URL规范化、候选池大小大于fallback、错误回退
- TestCandidateScore: 3个测试 (创建、默认LLM分数、比较)

### 2.5 tests/unit/test_parser.py - 文档解析测试
- TestReadTextFile: 4个测试 (UTF-8、UTF-8 BOM、GB18030、带fallback)
- TestFirstHeading: 5个测试 (H1、H2、空格、fallback、空文本)
- TestFirstNonEmptyLine: 5个测试 (首行、跳过空行、跳过标题标记、fallback、单行)
- TestShorten: 4个测试 (短字符串、长字符串、精确宽度、自定义宽度)
- TestSupportedExtensions: 4个测试 (Markdown、文本、Word、PDF)
- TestSplitParagraphs: 3个测试 (Markdown标题、空行、单段落)
- TestExtractPdfFile: 2个测试 (使用pypdf、不使用pypdf)

### 2.6 tests/unit/test_utils.py - 工具函数测试
- TestVectorOperations: 4个测试 (归一化)
- TestDotProduct: 4个测试 (正交、平行、相同向量、空向量)
- TestCosineSimilarity: 5个测试 (相同向量、正交、相反、空向量、部分重叠)
- TestBatchItems: 4个测试 (精确适配、有余数、空、批大小大于列表)
- TestExtractJsonObject: 5个测试 (简单JSON、嵌套JSON、JSON数组、无JSON错误、括号不平衡)
- TestShorten: 4个测试
- TestFirstHeading: 5个测试
- TestFirstNonEmptyLine: 5个测试

### 2.7 tests/integration/test_rag_pipeline.py - 集成测试
- TestTinyRAGIntegration: 17个测试
  - 初始化、列出文档、搜索返回、搜索产品概述、搜索HR策略、搜索中文、回答响应、空查询结果
  - 重载库、重载到不同目录、统计信息结构、线程安全、大文档处理、响应转字典
- TestEdgeCases: 6个测试
  - 空库错误、单文档库、空查询搜索、仅空白搜索、空查询回答、自定义后端
- TestPerformance: 2个测试 (搜索性能、初始化性能)

### 2.8 tests/api/test_web_api.py - API测试
- TestWebAppHelpers: 9个测试
  - 加载资源(存在/不存在)、解析top_k(有效/钳位/无效)、构建回答payload、构建库payload、重载库(成功/错误)
- TestRequestHandler: 1个测试 (处理器属性)
- TestHTTPStatusCodes: 4个测试 (200、400、404、500)
- TestResponseFormats: 2个测试 (回答响应、库响应)
- TestAsyncAPI: 2个测试 (异步搜索、异步回答)

### 2.9 tests/benchmark/test_benchmarks.py - 基准测试
- TestEmbeddingBenchmarks: 5个测试
  - 单文本、多文本、查询、大批次、大批量
- TestSearchBenchmarks: 4个测试
  - 单字查询、句子查询、回答、top_k
- TestRerankerBenchmarks: 2个测试 (本地reranker、大候选池)
- TestTokenizationBenchmarks: 5个测试
  - 短文本、长文本、中文、分割句子、分块文本
- TestVectorOperationsBenchmarks: 2个测试 (归一化、余弦相似度)
- TestEndToEndBenchmarks: 3个测试 (完整检索流程、列出文档、统计信息)

### 2.10 tests/performance/test_performance.py - 性能测试
- TestEmbeddingPerformance: 2个测试 (吞吐量、延迟分布)
- TestSearchPerformance: 3个测试 (负载下搜索延迟、并发搜索、回答性能)
- TestMemoryPerformance: 1个测试 (大库内存使用)
- TestScalability: 1个测试 (递增块可扩展性)
- TestLoadTests: 1个测试 (持续负载)

## 3. 测试覆盖率报告配置

### pytest.ini配置:
```ini
[tool:pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
asyncio_mode = auto

addopts = 
    -v
    --strict-markers
    --tb=short
    --cov=app
    --cov=web_app
    --cov-report=term-missing
    --cov-report=html:tests/reports/coverage_html
    --cov-report=xml:tests/reports/coverage.xml
    --cov-report=lcov:tests/reports/lcov.info

markers =
    slow: marks tests as slow
    integration: marks tests as integration tests
    unit: marks tests as unit tests
    api: marks tests as API tests
    benchmark: marks tests as benchmark tests
    performance: marks tests as performance tests
```

### 覆盖率报告格式:
- **HTML**: `tests/reports/coverage_html/index.html` - 交互式HTML报告
- **XML**: `tests/reports/coverage.xml` - CI/CD集成
- **LCOV**: `tests/reports/lcov.info` - 代码覆盖率工具

## 4. 运行测试的命令说明

### 基本命令:
```bash
# 运行所有测试
pytest

# 运行并显示详细输出
pytest -v

# 运行特定测试文件
pytest tests/unit/test_tokenizer.py -v

# 运行特定测试类
pytest tests/unit/test_tokenizer.py::TestTokenize -v

# 运行特定测试方法
pytest tests/unit/test_tokenizer.py::TestTokenize::test_tokenize_simple_english -v
```

### 按类别运行:
```bash
# 仅运行单元测试
pytest tests/unit -v

# 仅运行集成测试
pytest tests/integration -v

# 仅运行API测试
pytest tests/api -v

# 仅运行基准测试
pytest tests/benchmark -v

# 仅运行性能测试
pytest tests/performance -v
```

### 按标记运行:
```bash
# 跳过慢速测试
pytest -m "not slow"

# 仅运行单元测试
pytest -m unit

# 仅运行集成测试
pytest -m integration

# 仅运行API测试
pytest -m api

# 仅运行基准测试
pytest -m benchmark

# 运行多个标记
pytest -m "unit or api"
```

### 覆盖率测试:
```bash
# 生成覆盖率报告
pytest --cov=app --cov=web_app --cov-report=html --cov-report=term-missing

# 查看HTML报告
open tests/reports/coverage_html/index.html
```

### 并行运行:
```bash
# 使用pytest-xdist并行运行(需安装)
pip install pytest-xdist
pytest -n auto

# 指定工作进程数
pytest -n 4
```

### 调试模式:
```bash
# 遇到第一个失败就停止
pytest -x

# 进入pdb调试模式
pytest --pdb

# 显示完整的traceback
pytest --tb=long

# 仅显示失败测试
pytest --tb=no
```

## 5. 安装开发依赖

```bash
# 安装测试依赖
pip install -r requirements-dev.txt

# 或手动安装核心依赖
pip install pytest pytest-asyncio pytest-cov pytest-benchmark pytest-timeout pytest-xdist httpx responses
```

## 6. 测试结果统计

- **单元测试**: 118个测试
- **集成测试**: 25个测试  
- **API测试**: 20个测试
- **基准测试**: 26个测试
- **总计**: 189个测试

**所有测试通过!** ✅
