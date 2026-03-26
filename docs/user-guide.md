# 用户手册

欢迎使用 Tiny RAG Demo！本手册详细介绍系统的各项功能和使用方法。

## 📋 目录

- [功能说明](#功能说明)
- [操作指南](#操作指南)
- [最佳实践](#最佳实践)
- [FAQ](#faq)
- [故障排除](#故障排除)

## 功能说明

### 系统概述

Tiny RAG Demo 是一个轻量级的检索增强生成系统，支持：

- 📚 **多格式文档**: Markdown, Text, Word, PDF
- 🔍 **智能检索**: Dense Embedding + BM25 混合检索
- 🎯 **精准重排**: 多维度评分和重排序
- 💬 **自然问答**: 基于文档内容的智能回答
- 🌐 **Web 界面**: 美观的响应式用户界面
- 💾 **自动索引**: 智能缓存和自动更新

### 功能模块

#### 1. 文档管理

**支持的格式**:

| 格式 | 扩展名 | 说明 |
|------|--------|------|
| Markdown | `.md`, `.markdown` | 推荐格式，支持标题提取 |
| 纯文本 | `.txt` | 通用格式 |
| Word | `.doc`, `.docx` | 需 macOS textutil |
| PDF | `.pdf` | 优先 pypdf，回退 Swift |

**文档组织**:

```
document_library/
├── 产品文档/
│   ├── 用户手册.md
│   └── API文档.md
├── 公司制度/
│   ├── 请假制度.docx
│   └── 访客政策.pdf
└── FAQ/
    └── 常见问题.txt
```

#### 2. 检索系统

**两阶段检索**:

1. **Embedding 召回**
   - 语义相似度匹配
   - 默认使用本地 Hash Embedding
   - 可选 OpenAI API

2. **Rerank 重排**
   - BM25 词汇匹配
   - 标题匹配
   - 加权融合排序
   - 可选 LLM 评分

**评分维度**:

| 分数类型 | 说明 | 权重 |
|----------|------|------|
| Retrieve | Embedding 余弦相似度 | 60% |
| Lexical | BM25 词汇匹配 | 30% |
| Title | 标题匹配 | 10% |

#### 3. 回答生成

**生成流程**:

1. 检索相关上下文
2. 提取关键句子
3. 词汇重叠评分
4. 去重和格式化
5. 返回结构化回答

#### 4. Web 界面

**主要区域**:

- **提问区**: 输入问题，设置参数
- **文档库信息**: 显示入库文档列表
- **回答区**: 显示生成的答案
- **上下文区**: 显示命中的文档片段

## 操作指南

### 文档入库

#### 1. 准备文档

**Markdown 最佳实践**:

```markdown
# 文档标题

## 章节标题

正文内容，尽量使用自然语言描述。

### 子章节

- 要点 1
- 要点 2
- 要点 3

## 另一个章节

详细说明...
```

**注意事项**:
- 使用清晰的标题层级
- 每段内容不宜过长
- 避免过多特殊字符
- 保持文档结构清晰

#### 2. 添加文档

**命令行模式**:

```bash
# 复制文档到库目录
cp /path/to/doc.md document_library/

# 重新运行程序
python app.py --list-docs
```

**Web 模式**:

```bash
# 1. 复制文档到库目录
cp /path/to/doc.md document_library/

# 2. 点击「重新入库」按钮
```

#### 3. 验证入库

```bash
python app.py --list-docs
```

输出示例：
```
Document Library
========================================
目录: /path/to/document_library
文档数: 3 | Chunk 数: 15

已入库文件:
- 产品/用户手册.md | markdown | 2340 chars
- 公司/请假制度.docx | word | 1567 chars
- FAQ/常见问题.txt | text | 890 chars
```

### 执行查询

#### 1. 命令行查询

**单次查询**:

```bash
python app.py --query "企业版支持哪些功能？"
```

输出：
```
问题: 企业版支持哪些功能？

回答:
- 企业版提供 SSO 单点登录功能
- 支持自定义域名和品牌配置
- 提供高级数据分析和报表功能

检索到的上下文:
[1] product/enterprise.md | score=0.912 ...
    企业版支持 SSO 单点登录...
```

**交互模式**:

```bash
python app.py
```

示例对话：
```
进入交互模式，直接输入问题即可，输入 exit 结束。

你 > 如何申请请假？

问题: 如何申请请假？

回答:
- 登录 OA 系统提交请假申请
- 选择请假类型和日期
- 等待上级审批

你 > 支持哪些请假类型？
...

你 > exit
已退出。
```

#### 2. Web 界面查询

**操作步骤**:

1. 打开浏览器访问 `http://127.0.0.1:8000`
2. 在「你的问题」文本框中输入问题
3. 选择「召回条数」（推荐 3-5）
4. 点击「开始检索」
5. 查看生成的回答和上下文

**界面说明**:

```
┌─────────────────────────────────────────────────────────┐
│ [问题输入区]                                            │
│ ┌──────────────────────────────────────────────┐       │
│ │ 如何申请请假？                               │       │
│ └──────────────────────────────────────────────┘       │
│                                                         │
│ 召回条数: [3 ▼]                              [开始检索] │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│ 回答                                                    │
│ ──────────────────────────────────────────────────────  │
│ • 登录 OA 系统提交请假申请                              │
│ • 选择请假类型和日期                                    │
│ • 等待上级审批                                          │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│ 命中的文档片段                                          │
│ ──────────────────────────────────────────────────────  │
│ [1] hr/leave_policy.docx (Score: 0.923)                 │
│     员工请假需通过 OA 系统提交申请...                   │
└─────────────────────────────────────────────────────────┘
```

### 高级配置

#### 1. 切换 Embedding 后端

**本地模式（默认）**:

无需配置，开箱即用。

**OpenAI 模式**:

```bash
export OPENAI_API_KEY="sk-..."
export OPENAI_EMBED_MODEL="text-embedding-3-small"
export OPENAI_BASE_URL="https://api.openai.com"

python web_app.py
```

#### 2. 启用 LLM Rerank

```bash
export OPENAI_RERANK_MODEL="gpt-4o-mini"
export OPENAI_RERANK_TIMEOUT=45
export OPENAI_RERANK_MAX_CANDIDATES=12

python web_app.py
```

#### 3. 自定义参数

```bash
# 指定文档库目录
python web_app.py --library-dir /path/to/docs

# 自定义端口
python web_app.py --port 8080

# 绑定到所有接口
python web_app.py --host 0.0.0.0
```

### 结果解读

#### 分数说明

**综合分数 (Score)**:
- 范围：0-1
- 越高表示越相关
- 基于多维度加权计算

**各项分数**:

| 分数 | 说明 | 参考值 |
|------|------|--------|
| Retrieve | Embedding 相似度 | > 0.7 较好 |
| Lexical | BM25 词汇匹配 | > 0.5 较好 |
| Title | 标题匹配 | > 0.3 较好 |

#### 回答质量

**高质量回答特征**:
- 包含多个相关句子
- 来源文档分数较高
- 上下文覆盖全面

**低质量回答特征**:
- 句子数量少
- 来源分数较低
- 与问题相关性弱

## 最佳实践

### 文档准备

1. **文档质量**
   - 使用清晰的语言
   - 保持格式统一
   - 定期更新内容

2. **内容组织**
   ```
   document_library/
   ├── 01-产品文档/       # 按类别组织
   ├── 02-技术文档/
   ├── 03-操作手册/
   └── README.md          # 说明文件
   ```

3. **命名规范**
   - 使用有意义的文件名
   - 避免特殊字符
   - 使用连字符分隔：`user-guide.md`

### 查询技巧

1. **明确具体**
   - ❌ "告诉我关于这个的信息"
   - ✅ "企业版支持哪些 SSO 协议？"

2. **使用关键词**
   - 包含文档中的专业术语
   - 使用具体的功能名称
   - 避免模糊的描述

3. **分步提问**
   - 先问整体概念
   - 再问具体细节
   - 最后确认理解

4. **调整召回条数**
   - 简单问题：top_k=3
   - 复杂问题：top_k=5-8
   - 探索性查询：top_k=8

### 性能优化

1. **索引缓存**
   - 首次启动会建立索引
   - 文档变更后点击「重新入库」
   - 缓存文件 `.index_cache.pkl`

2. **批量操作**
   - 一次添加多个文档
   - 然后统一重新入库
   - 避免频繁重建索引

3. **硬件配置**
   - 内存：1GB+
   - 磁盘：SSD 推荐
   - CPU：多核有助并发

## FAQ

### 一般问题

**Q: Tiny RAG Demo 适合什么场景？**

A: 适合以下场景：
- 企业内部知识库问答
- 个人文档检索系统
- RAG 技术学习和研究
- 原型快速验证

**Q: 支持多语言吗？**

A: 是的，支持中文、英文混合内容：
- 中文使用 n-gram（2-gram, 3-gram）
- 英文使用空格分词
- 可同时处理多语言文档

**Q: 数据会发送到外部吗？**

A: 默认情况下不会：
- 本地 Hash Embedding 完全离线
- 文档库完全本地存储
- 仅在使用 OpenAI API 时发送数据

### 安装问题

**Q: 安装 pypdf 失败？**

A: 尝试以下方案：
```bash
# 使用 --target 参数
python3 -m pip install --target ./.deps pypdf

# 或手动添加路径
export PYTHONPATH="${PYTHONPATH}:./.deps"
```

**Q: Word 文档无法解析？**

A: Word 解析依赖 macOS textutil：
- macOS: 默认支持
- Linux: 需安装转换工具（如 antiword）
- Windows: 建议转换为 PDF 或 Markdown

### 使用问题

**Q: 为什么查询没有结果？**

A: 检查以下方面：
1. 文档库目录是否正确
2. 是否包含支持的文件格式
3. 问题是否与文档内容相关
4. 运行 `--list-docs` 确认文档已入库

**Q: 回答不准确怎么办？**

A: 改进建议：
1. 完善文档内容
2. 使用更具体的问题
3. 增加召回条数
4. 启用 LLM Rerank

**Q: 如何更新文档库？**

A: 三种方式：
1. 命令行：重新运行程序
2. Web：点击「重新入库」
3. 删除 `.index_cache.pkl` 后重启

**Q: 可以同时处理多少文档？**

A: 取决于硬件：
- 内存：100MB 文本约需 200MB 内存
- 磁盘：索引文件约为原文本的 10-20%
- 建议：单库不超过 1000 个文档

### 配置问题

**Q: 如何切换 Embedding 模型？**

A: 通过环境变量：
```bash
# 使用 OpenAI
export OPENAI_API_KEY="sk-..."
export OPENAI_EMBED_MODEL="text-embedding-3-small"

# 使用本地（默认）
# 无需配置
```

**Q: 支持哪些 LLM 模型？**

A: 任何兼容 OpenAI API 的模型：
- OpenAI: gpt-4o, gpt-4o-mini
- Azure OpenAI
- Claude (通过兼容层)
- 本地模型 (如 llama.cpp)

**Q: 如何配置代理？**

A: 标准 HTTP 代理：
```bash
export HTTP_PROXY="http://proxy:port"
export HTTPS_PROXY="http://proxy:port"
export NO_PROXY="localhost,127.0.0.1"
```

## 故障排除

### 启动问题

#### 1. 端口被占用

**现象**:
```
OSError: [Errno 48] Address already in use
```

**解决**:
```bash
# 查找占用进程
lsof -i :8000

# 使用其他端口
python web_app.py --port 8080
```

#### 2. 文档库目录不存在

**现象**:
```
FileNotFoundError: document library is empty: /path/to/docs
```

**解决**:
```bash
# 创建目录
mkdir -p document_library

# 或指定其他目录
python web_app.py --library-dir /path/to/existing/docs
```

#### 3. 权限不足

**现象**:
```
PermissionError: [Errno 13] Permission denied
```

**解决**:
```bash
# 检查权限
ls -la document_library/

# 修改权限
chmod -R 755 document_library/
chown -R $USER:$USER document_library/
```

### 运行时问题

#### 1. 文档解析失败

**现象**:
```
RuntimeError: Word 文件解析失败
```

**解决**:
1. 检查文件是否损坏
2. 尝试转换为其他格式
3. 确认依赖已安装

#### 2. API 请求失败

**现象**:
```
RuntimeError: request failed: 401 Unauthorized
```

**解决**:
```bash
# 检查 API 密钥
echo $OPENAI_API_KEY

# 检查网络连接
curl -I https://api.openai.com

# 检查余额和配额
```

#### 3. 内存不足

**现象**:
```
MemoryError: Unable to allocate array
```

**解决**:
1. 减少文档数量
2. 增加系统内存
3. 使用更大的交换空间

### 性能问题

#### 1. 查询响应慢

**原因和解决**:

| 可能原因 | 解决方案 |
|----------|----------|
| 首次启动无缓存 | 等待索引建立完成 |
| 文档库过大 | 分库管理 |
| 使用 LLM Rerank | 增加超时时间或关闭 |
| 硬件资源不足 | 升级配置 |

#### 2. 索引重建频繁

**原因**:
- 文档频繁变动
- 缓存失效

**解决**:
```bash
# 检查缓存文件
ls -la .index_cache.pkl

# 手动锁定缓存（不推荐用于生产）
# 添加文档后手动触发重建
```

### 其他问题

#### 1. 中文显示乱码

**解决**:
```bash
# 检查系统编码
echo $LANG

# 设置 UTF-8
export LANG=en_US.UTF-8
export LC_ALL=en_US.UTF-8
```

#### 2. Web 界面样式异常

**解决**:
1. 清除浏览器缓存
2. 检查网络连接
3. 查看浏览器控制台错误

#### 3. 无法连接到服务

**排查步骤**:
```bash
# 1. 检查服务状态
ps aux | grep web_app

# 2. 检查端口监听
netstat -tlnp | grep 8000

# 3. 测试本地连接
curl http://127.0.0.1:8000/api/health

# 4. 检查防火墙
sudo ufw status
```

### 获取帮助

如果以上方法无法解决问题：

1. **查看日志**
   ```bash
   # 命令行模式
   python app.py --query "test" 2>&1 | tee log.txt
   
   # Web 模式
   python web_app.py 2>&1 | tee log.txt
   ```

2. **运行诊断**
   ```bash
   python app.py --list-docs
   python -c "from app import TinyRAG; print('导入成功')"
   ```

3. **提交 Issue**
   - 描述问题现象
   - 提供错误日志
   - 说明操作步骤
   - 列出环境信息

---

**提示**: 更多技术细节请参考 [架构文档](architecture.md)。
