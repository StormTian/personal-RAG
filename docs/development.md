# 开发指南

本指南帮助开发者理解和参与 Tiny RAG Demo 项目开发。

## 📋 目录

- [开发环境](#开发环境)
- [项目结构](#项目结构)
- [代码规范](#代码规范)
- [核心模块](#核心模块)
- [调试技巧](#调试技巧)
- [贡献指南](#贡献指南)
- [测试](#测试)

## 开发环境

### 环境要求

- Python 3.8 或更高版本
- macOS（用于 Word/PDF 解析测试）
- Git

### 环境搭建

#### 1. 克隆仓库

```bash
git clone <repository-url>
cd rag-demo
```

#### 2. 创建虚拟环境

```bash
# 创建虚拟环境
python3 -m venv .venv

# 激活虚拟环境
source .venv/bin/activate  # Linux/Mac
# 或 .venv\Scripts\activate  # Windows
```

#### 3. 安装依赖

```bash
# 安装核心依赖
pip install pypdf

# 开发依赖（可选）
pip install pytest black flake8 mypy
```

#### 4. 验证环境

```bash
# 运行测试
python3 -m unittest test_app.py test_web_app.py

# 命令行测试
python3 app.py --list-docs
```

### IDE 配置

#### VS Code

推荐插件:
- Python
- Pylance
- Python Docstring Generator

配置 `.vscode/settings.json`:

```json
{
  "python.defaultInterpreterPath": "./.venv/bin/python",
  "python.analysis.typeCheckingMode": "basic",
  "python.formatting.provider": "black",
  "python.linting.enabled": true,
  "python.linting.flake8Enabled": true,
  "python.linting.mypyEnabled": true
}
```

#### PyCharm

1. 打开项目
2. File → Settings → Project → Python Interpreter
3. 选择虚拟环境中的 Python
4. 启用代码检查：
   - Editor → Inspections → Python
   - 启用 "Type checker"、"PEP 8"

## 项目结构

```
rag-demo/
├── app.py                    # RAG 核心引擎
│   ├── 文档处理模块
│   ├── 索引构建模块
│   ├── 检索模块
│   ├── Embedding 后端
│   └── Reranker 后端
│
├── web_app.py               # Web 服务
│   ├── HTTP 服务器
│   ├── 请求处理器
│   └── API 端点
│
├── web/                     # 前端界面
│   ├── index.html          # 页面结构
│   ├── styles.css          # 样式表
│   └── app.js              # 前端逻辑
│
├── document_library/        # 文档库（示例）
│
├── docs/                    # 项目文档
│   ├── README.md
│   ├── getting-started.md
│   ├── api.md
│   ├── architecture.md
│   ├── development.md
│   ├── deployment.md
│   ├── user-guide.md
│   └── CHANGELOG.md
│
├── test_app.py             # 单元测试
├── test_web_app.py         # Web 测试
├── requirements.txt        # 依赖文件
└── README.md               # 项目主页
```

## 代码规范

### Python 代码风格

#### 遵循 PEP 8

```python
# ✅ 正确
class TinyRAG:
    """RAG 引擎主类."""
    
    def __init__(self, library_dir: Path) -> None:
        self.library_dir = library_dir

# ❌ 错误
class tinyRAG:
    def __init__(self,library_dir):
        self.library_dir=library_dir
```

#### 命名规范

| 类型 | 命名风格 | 示例 |
|------|---------|------|
| 类 | PascalCase | `TinyRAG`, `SearchHit` |
| 函数/方法 | snake_case | `tokenize`, `load_document` |
| 变量 | snake_case | `query_text`, `chunk_id` |
| 常量 | UPPER_CASE | `SUPPORTED_EXTENSIONS` |
| 私有属性 | _leading_underscore | `_snapshot`, `_lock` |

#### 类型注解

```python
from typing import List, Dict, Optional, Tuple
from pathlib import Path

def search(
    self,
    query: str,
    top_k: int = 3
) -> List[SearchHit]:
    """搜索文档。
    
    Args:
        query: 搜索查询字符串
        top_k: 返回结果数量
        
    Returns:
        匹配的搜索结果列表
    """
    ...
```

#### Docstring 规范

使用 Google 风格：

```python
def calculate_bm25(
    query_tokens: Set[str],
    chunk_tokens: Dict[str, int],
    idf: Dict[str, float],
    avgdl: float
) -> float:
    """计算 BM25 评分。
    
    Args:
        query_tokens: 查询词集合
        chunk_tokens: 文本块的词频字典
        idf: 逆文档频率表
        avgdl: 平均文档长度
        
    Returns:
        BM25 评分值
        
    Raises:
        ValueError: 当 avgdl 为 0 时
    """
    ...
```

### 代码组织

#### 模块划分

```python
# app.py 结构
"""
Tiny RAG Demo - Core Module

该模块实现 RAG 引擎的核心功能，包括：
- 文档处理
- 索引构建
- 文本检索
- 回答生成
"""

# 1. 导入
from __future__ import annotations
import ...

# 2. 常量定义
SUPPORTED_EXTENSIONS = {...}
DOCUMENT_LIBRARY_DIR = ...

# 3. 工具函数
def tokenize(text: str) -> List[str]: ...
def chunk_text(text: str) -> List[str]: ...

# 4. 数据类
@dataclass
class Chunk: ...

# 5. 后端接口
class EmbeddingBackend: ...
class RerankerBackend: ...

# 6. 主类
class TinyRAG: ...

# 7. CLI 入口
if __name__ == "__main__": ...
```

#### 导入排序

```python
# 1. 标准库
import os
import sys
from typing import ...

# 2. 第三方库
import numpy as np  # 如果未来添加

# 3. 本地模块
from app import TinyRAG
```

### 错误处理

```python
# ✅ 正确：具体的错误处理
try:
    document = load_source_document(path, library_dir)
except FileNotFoundError as exc:
    logger.error(f"文件不存在: {path}")
    raise
except ValueError as exc:
    logger.warning(f"不支持的格式: {path.suffix}")
    skipped_files.append((str(path), str(exc)))

# ❌ 错误：捕获所有异常
try:
    document = load_source_document(path, library_dir)
except Exception:  # 太宽泛
    pass
```

### 日志记录

```python
import logging

logger = logging.getLogger(__name__)

# 不同级别
logger.debug("详细调试信息")
logger.info("一般信息")
logger.warning("警告信息")
logger.error("错误信息")
```

## 核心模块

### 1. 文档处理模块

**文件**: `app.py`
**关键函数**:
- `load_source_document()` - 加载文档
- `read_text_file()` - 读取文本文件
- `extract_word_file()` - 提取 Word 文本
- `extract_pdf_file()` - 提取 PDF 文本

**示例**:

```python
def load_source_document(path: Path, library_dir: Path) -> SourceDocument:
    """加载单个源文档。
    
    根据文件扩展名选择合适的提取器。
    """
    suffix = path.suffix.lower()
    file_type = SUPPORTED_EXTENSIONS.get(suffix)
    if file_type is None:
        raise ValueError(f"不支持的格式: {suffix}")
    
    # 选择提取器
    if suffix in {".md", ".markdown", ".txt"}:
        raw_text = read_text_file(path)
    elif suffix in {".doc", ".docx"}:
        raw_text = extract_word_file(path)
    else:
        raw_text = extract_pdf_file(path)
    
    # 标准化处理
    normalized_text = raw_text.replace("\x00", "")
    ...
```

### 2. 索引模块

**关键类**: `TinyRAG._build_snapshot()`

**处理流程**:
1. 发现源文件
2. 提取文本
3. 分块处理
4. 生成 Embedding
5. 构建 BM25 索引
6. 持久化缓存

### 3. 检索模块

**关键类**: `TinyRAG.search()`

**两阶段检索**:
```python
def search(self, query: str, top_k: int = 3) -> List[SearchHit]:
    # 阶段 1: Embedding 召回
    query_embedding = self.embedding_backend.embed_query(query)
    candidates = self._cosine_search(query_embedding, top_k * 6)
    
    # 阶段 2: Rerank
    ranked = self.reranker_backend.rerank(query, snapshot, candidates)
    
    return ranked[:top_k]
```

### 4. Web 服务模块

**文件**: `web_app.py`
**关键类**: `RagHTTPRequestHandler`

**请求处理**:
```python
class RagHTTPRequestHandler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path == "/api/health":
            self._send_json(build_library_payload(self.rag))
        elif parsed.path == "/api/ask":
            query = parse_qs(parsed.query).get("q", [""])[0]
            self._handle_question(query, "3")
    
    def do_POST(self) -> None:
        ...
```

## 调试技巧

### 1. 启用详细日志

```python
import logging

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
```

### 2. 检查索引状态

```bash
# 查看文档库状态
python3 app.py --list-docs

# 查看缓存文件
ls -la .index_cache.pkl
```

### 3. 单步调试

```python
# 在代码中插入断点
import pdb; pdb.set_trace()

# 或使用 breakpoint()（Python 3.7+）
breakpoint()
```

### 4. 测试特定模块

```python
# test_embedding.py
from app import LocalHashEmbeddingBackend

backend = LocalHashEmbeddingBackend(dimensions=256)
embeddings = backend.embed_texts(["测试文本", "另一个文本"])

print(f"Embedding shape: {len(embeddings)}x{len(embeddings[0])}")
print(f"Norm: {sum(x*x for x in embeddings[0])**0.5}")  # 应该接近 1.0
```

### 5. Web 调试

```bash
# 使用 curl 测试 API
curl -v "http://localhost:8000/api/ask?q=测试"

# 查看响应头
curl -I http://localhost:8000/api/health
```

### 6. 性能分析

```python
import time
import cProfile

# 简单计时
start = time.time()
result = rag.search("查询", top_k=5)
print(f"耗时: {time.time() - start:.3f}s")

# 详细分析
cProfile.run('rag.search("查询", top_k=5)', 'profile.stats')
```

## 贡献指南

### 如何贡献

1. **Fork 仓库**
   ```bash
   git clone <your-fork>
   cd rag-demo
   ```

2. **创建分支**
   ```bash
   git checkout -b feature/my-feature
   # 或
   git checkout -b fix/some-bug
   ```

3. **提交更改**
   ```bash
   git add .
   git commit -m "feat: 添加新功能"
   ```

4. **推送并创建 PR**
   ```bash
   git push origin feature/my-feature
   ```

### 提交信息规范

使用 [Conventional Commits](https://www.conventionalcommits.org/) 格式：

```
类型(范围): 简短描述

详细描述（可选）

Footer（可选）
```

**类型**:
- `feat`: 新功能
- `fix`: 修复
- `docs`: 文档更新
- `style`: 代码格式（不影响功能）
- `refactor`: 重构
- `test`: 测试相关
- `chore`: 构建/工具相关

**示例**:

```
feat(embedding): 添加 OpenAI embedding 支持

- 实现 OpenAICompatibleEmbeddingBackend
- 添加环境变量配置
- 更新文档

Closes #123
```

### 代码审查

提交 PR 前请确保：

- [ ] 代码符合 PEP 8 规范
- [ ] 添加了必要的测试
- [ ] 所有测试通过
- [ ] 更新了相关文档
- [ ] 提交了清晰的 commit message

### 开发工作流

```
main
  │
  ├── feature/new-backend
  │   └── PR #1 → Review → Merge
  │
  ├── fix/tokenization
  │   └── PR #2 → Review → Merge
  │
  └── docs/api-update
      └── PR #3 → Review → Merge
```

## 测试

### 运行测试

```bash
# 运行所有测试
python3 -m unittest test_app.py test_web_app.py

# 运行特定测试
python3 -m unittest test_app.TestTinyRAG.test_tokenize

# 详细输出
python3 -m unittest -v test_app.py
```

### 测试覆盖

```bash
# 安装 coverage
pip install coverage

# 运行测试并生成报告
coverage run -m unittest test_app.py test_web_app.py
coverage report
coverage html  # 生成 HTML 报告
```

### 添加新测试

```python
# test_feature.py
import unittest
from app import TinyRAG, tokenize
from pathlib import Path

class TestNewFeature(unittest.TestCase):
    def setUp(self):
        self.rag = TinyRAG(Path("test_library"))
    
    def test_new_feature(self):
        # Arrange
        query = "测试查询"
        
        # Act
        result = self.rag.search(query)
        
        # Assert
        self.assertIsNotNone(result)
        self.assertGreater(len(result), 0)
    
    def test_edge_case(self):
        # 测试边界情况
        pass

if __name__ == '__main__':
    unittest.main()
```

---

**提示**: 更多实现细节请参考源码中的注释。
