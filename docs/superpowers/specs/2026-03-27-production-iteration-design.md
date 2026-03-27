# RAG 系统生产级迭代设计文档

**日期：** 2026-03-27  
**版本：** 1.0

---

## 概述

本文档描述 RAG 系统的生产级迭代方案，包括问题修复和功能增强。目标是修复现有问题、集成关键优化，并确保前后端全流程测通。

---

## 目标

### 修复问题
1. 测试 conftest.py 模块引用错误
2. 前端 TypeScript 类型错误（9个）
3. 前后端联调验证

### 新增功能
1. FAISS 向量数据库集成
2. Redis 查询缓存
3. 并行文档处理
4. 前端代码分割与懒加载

### 交付标准
- 所有测试通过
- 前后端联调成功
- 核心功能可用

---

## 阶段一：修复基础问题

### 1.1 测试修复

**问题：** `tests/conftest.py` 引用旧模块名 `app`，需要改为 `rag_system`

**修复范围：**
- `tests/conftest.py` - 主要修复文件
- `tests/unit/*.py` - 可能需要更新的导入
- `tests/integration/*.py` - 可能需要更新的导入

**修复策略：**
更新 `conftest.py` 的 import 语句：
- 从 `rag_system.core.base` 导入基类和模型（Chunk, SourceDocument, CandidateScore, SearchHit, RagResponse, IndexSnapshot）
- 从 `rag_system.backends.embedding` 导入嵌入后端（EmbeddingBackend, LocalHashEmbeddingBackend）
- 从 `rag_system.backends.reranker` 导入重排序后端（RerankerBackend, LocalHeuristicReranker）
- 从 `rag_system.rag_engine` 导入 RAGEngine
- 从 `rag_system.utils.text` 导入文本处理函数（tokenize, chunk_text, cosine_similarity, normalize_vector）

**验证标准：** `pytest tests/unit -v` 全部通过

---

### 1.2 前端 TypeScript 修复

**问题清单（9个错误）：**

| 文件 | 行号 | 问题 | 修复方案 |
|------|------|------|----------|
| LibraryPanel.tsx | 115 | LibraryFile[] 与 FileItem[] 类型不匹配 | 统一类型定义 |
| UploadArea.tsx | 26 | UploadProgressEvent 类型错误 | 修复为 number |
| UploadArea.tsx | 29 | UploadResponse 缺少 success 属性 | 添加 success 字段 |
| ResultPanel.tsx | 4 | 未使用的 SearchParams 导入 | 删除导入 |
| SearchHistory.tsx | 2 | 未使用的 Empty 导入 | 删除导入 |
| SearchHistory.tsx | 62 | Tag 组件 size 属性不存在 | 使用 style 替代 |
| Home.tsx | 23 | 未使用的 refetchLibrary 变量 | 删除变量或使用下划线前缀 |
| Home.tsx | 84 | null 不能赋值给 undefined 类型 | 统一使用 undefined |
| highlight.ts | 23 | 未使用的 match 变量 | 删除或使用下划线前缀 |

**验证标准：** `npm run typecheck` 无错误

---

### 1.3 前后端联调验证

**验证项：**

1. 后端启动验证
   ```bash
   uvicorn rag_system.api.server:create_app --factory
   ```

2. 前端启动验证
   ```bash
   cd web-new && npm run dev
   ```

3. API 连通性测试
   - `GET /health` - 健康检查
   - `GET /api/search?q=test` - 搜索功能
   - `POST /api/query` - 查询功能
   - `POST /api/upload` - 文件上传
   - `GET /api/files` - 文件列表

**验证方式：** 手动测试 + 自动化测试脚本

---

## 阶段二：后端核心优化

### 2.1 FAISS 向量数据库集成

**背景：**
- 当前使用 numpy 数组做余弦相似度，O(n) 复杂度
- 无法扩展到超过 ~1万文档

**架构设计：**

```
rag_system/
├── backends/
│   └── vector_store/
│       ├── __init__.py
│       ├── base.py           # VectorStore 抽象基类
│       ├── faiss_store.py    # FAISS 实现
│       └── numpy_store.py    # 原有 numpy 实现（保留作为备选）
```

**核心接口：**

```python
class VectorStore(ABC):
    """向量存储抽象基类"""
    
    @abstractmethod
    def add(self, embeddings: List[np.ndarray], ids: List[int]) -> None:
        """添加向量和对应ID"""
        pass
    
    @abstractmethod
    def search(self, query: np.ndarray, k: int) -> List[Tuple[int, float]]:
        """搜索最相似的k个向量，返回 (id, score) 列表"""
        pass
    
    @abstractmethod
    def save(self, path: Path) -> None:
        """持久化索引"""
        pass
    
    @abstractmethod
    def load(self, path: Path) -> None:
        """加载索引"""
        pass
    
    @abstractmethod
    def clear(self) -> None:
        """清空索引"""
        pass
```

**FAISS 实现要点：**
- 使用 `faiss.IndexFlatIP`（内积索引）
- 归一化向量后，内积等价于余弦相似度
- 支持持久化到 `.index_cache/faiss.index`
- 无需训练，适合中小规模数据

**Numpy 实现要点：**
- 保留原有实现作为备选
- 适用于不想安装 FAISS 的场景

**集成位置：**
- `rag_engine.py` 的 `_build_index()` 方法中创建索引
- `_search()` 方法中使用向量搜索
- 通过配置选择后端

**配置项：**
```yaml
vector_store:
  backend: "faiss"  # 或 "numpy"
```

---

### 2.2 Redis 查询缓存

**架构设计：**

```
rag_system/
├── cache/
│   ├── __init__.py
│   ├── base.py           # QueryCache 抽象基类
│   ├── redis_cache.py    # Redis 实现
│   └── memory_cache.py   # 内存 LRU 实现（开发/测试用）
```

**核心接口：**

```python
class QueryCache(ABC):
    """查询缓存抽象基类"""
    
    @abstractmethod
    async def get(self, key: str) -> Optional[dict]:
        """获取缓存结果"""
        pass
    
    @abstractmethod
    async def set(self, key: str, value: dict, ttl: int = 3600) -> None:
        """设置缓存"""
        pass
    
    @abstractmethod
    async def delete(self, pattern: str) -> None:
        """删除匹配的缓存"""
        pass
    
    @abstractmethod
    async def clear(self) -> None:
        """清空所有缓存"""
        pass
```

**Redis 实现要点：**
- 使用 `aioredis` 异步客户端
- 支持 key pattern 删除（SCAN + DEL）
- 连接池管理

**Memory 实现要点：**
- 使用 `collections.OrderedDict` 实现 LRU
- 适用于开发测试环境
- 进程内缓存，无需额外依赖

**缓存策略：**
- 缓存键：`rag:query:{hash(query:top_k)}`
- TTL：1 小时（可配置）
- 索引重载时清除所有缓存

**配置项：**
```yaml
cache:
  query_cache:
    enabled: true
    backend: "redis"  # 或 "memory"
    redis_url: "redis://localhost:6379/0"
    ttl: 3600
    key_prefix: "rag:query:"
```

**集成位置：**
- `rag_engine.py` 的 `answer_async()` 方法：查询前检查缓存，结果写入缓存
- `search_async()` 方法：同样添加缓存逻辑
- `reload_async()` 方法：清空缓存

---

### 2.3 并行文档处理

**当前问题：**
- 文档加载和分块是顺序执行
- 大型文档库初始化缓慢

**优化方案：**

**1. 并行文档加载**

```python
from concurrent.futures import ThreadPoolExecutor, as_completed

def _load_documents_parallel(self, files: List[Path]) -> List[SourceDocument]:
    """并行加载文档"""
    documents = []
    with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
        future_to_file = {
            executor.submit(self._load_single_document, f): f 
            for f in files
        }
        for future in as_completed(future_to_file):
            result = future.result()
            if result:
                documents.append(result)
    return documents
```

**2. 并行嵌入生成**

```python
async def _embed_chunks_parallel(self, chunks: List[Chunk]) -> List[np.ndarray]:
    """并行生成嵌入"""
    batch_size = 32
    batches = [chunks[i:i+batch_size] for i in range(0, len(chunks), batch_size)]
    
    tasks = [
        self._embed_batch([c.text for c in batch])
        for batch in batches
    ]
    results = await asyncio.gather(*tasks)
    
    # 合并结果
    embeddings = []
    for batch_result in results:
        embeddings.extend(batch_result)
    return embeddings
```

**配置项：**
```yaml
performance:
  parallel_loading: true
  max_workers: 4
  embed_batch_size: 32
```

**集成位置：**
- `rag_engine.py` 的 `_reload()` 方法中调用并行加载
- 保持顺序兼容，可通过配置关闭

---

### 2.4 配置更新

**完整配置示例：**

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
    backend: "redis"
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

---

## 阶段三：前端优化

### 3.1 代码分割

**当前问题：**
- 单一大包，初始加载慢
- 所有第三方库打包在一起

**优化方案：**

修改 `vite.config.ts`：

```typescript
export default defineConfig({
  build: {
    rollupOptions: {
      output: {
        manualChunks: {
          'vendor-react': ['react', 'react-dom', 'react-router-dom'],
          'vendor-antd': ['antd', '@ant-design/icons'],
          'vendor-query': ['@tanstack/react-query'],
          'vendor-utils': ['axios', 'dayjs', 'lodash-es'],
        }
      }
    },
    chunkSizeWarningLimit: 500,
  }
})
```

**预期包大小：**
- vendor-react: ~150KB
- vendor-antd: ~400KB
- vendor-query: ~50KB
- vendor-utils: ~50KB
- 主包: ~150KB

---

### 3.2 路由懒加载

**当前问题：**
- 所有页面组件同步加载
- 首屏加载不必要代码

**优化方案：**

修改 `src/App.tsx`：

```typescript
import { lazy, Suspense } from 'react'
import { Routes, Route } from 'react-router-dom'
import { Spin } from 'antd'
import MainLayout from './layouts/MainLayout/MainLayout'

// 懒加载页面组件
const HomePage = lazy(() => import('./pages/Home/Home'))
const LibraryPage = lazy(() => import('./pages/Library/Library'))

function App() {
  return (
    <MainLayout>
      <Suspense 
        fallback={
          <div style={{ display: 'flex', justifyContent: 'center', padding: '100px 0' }}>
            <Spin size="large" />
          </div>
        }
      >
        <Routes>
          <Route path="/" element={<HomePage />} />
          <Route path="/library" element={<LibraryPage />} />
        </Routes>
      </Suspense>
    </MainLayout>
  )
}

export default App
```

---

### 3.3 组件懒加载

**适合懒加载的组件：**
- Markdown 渲染器（prismjs 较大）
- 大型列表组件
- 模态框/抽屉内容

**实现示例：**

```typescript
import { lazy, Suspense } from 'react'

const MarkdownRenderer = lazy(() => import('./components/MarkdownRenderer'))

function ResultPanel({ content }: { content: string }) {
  return (
    <Suspense fallback={<Spin />}>
      <MarkdownRenderer content={content} />
    </Suspense>
  )
}
```

---

### 3.4 优化效果预期

| 指标 | 优化前 | 优化后 | 提升 |
|------|--------|--------|------|
| 初始包大小 | ~800KB | ~300KB | 62.5% |
| 首屏加载时间 | ~3s | ~1s | 66.7% |
| 路由切换延迟 | 无 | ~200ms | 按需加载 |

---

## 实施计划

### 阶段一（预计 2-3 小时）
1. 修复测试 conftest.py
2. 运行测试验证
3. 修复前端 TypeScript 错误
4. 验证前后端联调

### 阶段二（预计 4-5 小时）
1. 实现向量存储抽象和 FAISS 集成
2. 实现查询缓存抽象和 Redis 集成
3. 实现并行文档处理
4. 更新配置和文档
5. 编写单元测试

### 阶段三（预计 1-2 小时）
1. 配置代码分割
2. 实现路由懒加载
3. 优化大型组件加载
4. 验证打包效果

### 最终验证（预计 1 小时）
1. 运行完整测试套件
2. 前后端联调测试
3. 性能基准测试
4. 文档更新

---

## 依赖项

### 新增 Python 依赖
```
faiss-cpu>=1.7.4
redis>=5.0.0
```

### 新增前端依赖
无（使用现有依赖）

---

## 风险与缓解

| 风险 | 影响 | 缓解措施 |
|------|------|----------|
| FAISS 安装问题 | 无法使用向量索引 | 保留 numpy 后端作为备选 |
| Redis 连接失败 | 缓存不可用 | 回退到内存缓存 |
| 并行处理竞态条件 | 数据不一致 | 使用线程安全数据结构 |
| 前端懒加载闪烁 | 用户体验差 | 优化加载动画 |

---

## 验收标准

1. **测试覆盖**
   - 单元测试全部通过
   - 集成测试全部通过
   - 测试覆盖率 ≥ 80%

2. **功能验证**
   - 前后端联调成功
   - 所有 API 端点正常
   - 搜索/查询功能正确

3. **性能指标**
   - 向量搜索 O(log n)
   - 缓存命中率 ≥ 80%（重复查询）
   - 前端首屏加载 ≤ 1.5s

4. **代码质量**
   - TypeScript 无类型错误
   - Python 代码通过 mypy 检查
   - 代码通过 lint 检查