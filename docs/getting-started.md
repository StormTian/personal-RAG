# 快速开始

本指南将帮助你在 5 分钟内运行起 Tiny RAG Demo。

## 📋 目录

- [环境要求](#环境要求)
- [安装](#安装)
- [准备文档](#准备文档)
- [第一个查询](#第一个查询)
- [启动 Web 界面](#启动-web-界面)
- [下一步](#下一步)

## 环境要求

- **Python**: 3.8 或更高版本
- **操作系统**: macOS（Word/PDF 解析依赖 textutil 或 Swift）
- **内存**: 最低 512MB，推荐 1GB+
- **磁盘空间**: 100MB+（取决于文档库大小）

## 安装

### 1. 克隆仓库

```bash
git clone <repository-url>
cd rag-demo
```

### 2. 安装依赖（可选）

如果需要 PDF 支持，安装 pypdf：

```bash
python3 -m pip install --target ./.deps -r requirements.txt
```

**注意**: 如果不安装，PDF 解析会回退到 Swift + PDFKit（仅限 macOS）。

### 3. 验证安装

```bash
python3 --version
python3 -c "from app import TinyRAG; print('安装成功！')"
```

## 准备文档

### 创建文档库目录

```bash
mkdir -p document_library
```

### 添加文档

支持的格式：
- `.md`, `.markdown` - Markdown 文件
- `.txt` - 文本文件
- `.doc`, `.docx` - Word 文档
- `.pdf` - PDF 文件

示例目录结构：

```
document_library/
├── product/
│   └── overview.md
├── hr/
│   └── policy.docx
└── faq.txt
```

### 快速测试文档

创建一个简单的 Markdown 文件：

```bash
cat > document_library/demo.md << 'EOF'
# Tiny RAG Demo

这是一个轻量级的 RAG 系统演示。

## 功能特性

- 本地运行，无需外部 API
- 支持多种文档格式
- 混合检索策略

## 使用方法

1. 准备文档库
2. 运行程序
3. 提问获取答案
EOF
```

## 第一个查询

### 命令行模式

```bash
# 查看文档库状态
python3 app.py --list-docs
```

输出示例：
```
Document Library
========================================
目录: /path/to/document_library
文档数: 1 | Chunk 数: 3
支持格式: .doc, .docx, .md, .markdown, .pdf, .txt
Embedding: local-hash-256d
Reranker: local-heuristic
检索链路: dense-embedding-cosine -> embedding+lexical-overlap

已入库文件:
- demo.md | markdown | 234 chars
```

### 运行查询

```bash
# 单次查询
python3 app.py --query "Tiny RAG 有什么功能？"
```

输出示例：
```
问题: Tiny RAG 有什么功能？

回答:
- 本地运行，无需外部 API
- 支持多种文档格式
- 混合检索策略

检索到的上下文:
[1] demo.md | score=0.892 (retrieve=0.912, rerank=0.892, llm=0.000)
    这是一个轻量级的 RAG 系统演示。
```

### 交互模式

```bash
# 启动交互式问答
python3 app.py
```

交互示例：
```
进入交互模式，直接输入问题即可，输入 exit 结束。

你 > 如何使用 Tiny RAG？

问题: 如何使用 Tiny RAG？

回答:
- 准备文档库
- 运行程序
- 提问获取答案

检索到的上下文:
[1] demo.md | score=0.876 ...
    
你 > exit
已退出。
```

## 启动 Web 界面

### 基本启动

```bash
python3 web_app.py
```

输出：
```
RAG Web UI is running at http://127.0.0.1:8000
Document library: /path/to/document_library
Press Ctrl+C to stop.
```

### 自定义配置

```bash
# 使用不同端口
python3 web_app.py --port 8080

# 使用不同文档目录
python3 web_app.py --library-dir /path/to/your/docs

# 绑定到所有网络接口
python3 web_app.py --host 0.0.0.0 --port 8080
```

### 访问界面

打开浏览器访问 http://127.0.0.1:8000

界面功能：
- **提问区**: 输入问题，设置召回条数
- **文档库信息**: 显示当前入库文档列表
- **重新入库**: 重新扫描文档库
- **回答区**: 显示生成的答案和命中的上下文

### Web 界面操作

1. **提问**
   - 在文本框中输入问题
   - 选择召回条数（1-8，默认 3）
   - 点击「开始检索」

2. **查看结果**
   - 上方显示生成的回答
   - 下方显示命中的文档片段及分数

3. **重新入库**
   - 添加/修改文档后点击「重新入库」
   - 系统会重新扫描并建立索引

## 下一步

- 📖 [详细 API 文档](api.md)
- 🏗️ [架构设计说明](architecture.md)
- 🔧 [配置高级选项](#配置)
- 🚀 [部署到生产环境](deployment.md)

## 常见问题

### Q: 为什么查询没有结果？

A: 请检查：
1. 文档库目录是否存在且包含支持的文件
2. 运行 `python3 app.py --list-docs` 确认文档已入库
3. 问题是否与文档内容相关

### Q: Word 文档无法解析？

A: Word 解析依赖 macOS 的 `textutil` 命令。在 Linux/Windows 上：
- 将 Word 文档转换为 PDF 或 Markdown
- 或安装兼容的文档解析库

### Q: PDF 解析失败？

A: 安装 pypdf：
```bash
pip install pypdf
```

### Q: 如何更新文档库？

A: 
- **命令行**: 直接添加/删除文件后重新运行
- **Web**: 点击「重新入库」按钮

---

**提示**: 更多问题请查看 [用户手册](user-guide.md)。
