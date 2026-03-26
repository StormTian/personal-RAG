# 文件上传限制增加设计文档

## 概述

将RAG系统的文件上传大小限制从10MB增加到100MB。

## 当前状态

当前文件上传限制为 **10MB** (10,485,760 字节)，配置在以下位置：

1. `rag_system/utils/file_security.py:14` - `MAX_FILE_SIZE = 10 * 1024 * 1024`
2. `rag_system/config/settings.py:100` - `max_upload_size = 10_485_760` (SecurityConfig)
3. `rag_system/config/settings.py:108` - `max_file_size = 10_485_760` (UploadConfig)
4. `config.example.yaml:93` - `max_upload_size: 10485760`
5. `config.example.yaml:106` - `max_file_size: 10485760`

## 变更方案

**方案A：统一修改为100MB**

将所有10MB限制统一修改为100MB (104,857,600 字节)。

### 修改清单

| 文件 | 位置 | 当前值 | 新值 |
|------|------|--------|------|
| `rag_system/utils/file_security.py` | 第14行 | `MAX_FILE_SIZE = 10 * 1024 * 1024` | `MAX_FILE_SIZE = 100 * 1024 * 1024` |
| `rag_system/config/settings.py` | 第100行 | `max_upload_size: int = 10_485_760` | `max_upload_size: int = 104_857_600` |
| `rag_system/config/settings.py` | 第108行 | `max_file_size: int = 10_485_760` | `max_file_size: int = 104_857_600` |
| `config.example.yaml` | 第93行 | `max_upload_size: 10485760` | `max_upload_size: 104857600` |
| `config.example.yaml` | 第106行 | `max_file_size: 10485760` | `max_file_size: 104857600` |

## 影响分析

### 正面影响
- 支持更大的PDF、Word文档上传
- 提升用户体验

### 风险评估
- **存储空间**：需要确保服务器有足够的磁盘空间
- **内存使用**：上传大文件时会占用更多内存
- **网络带宽**：上传大文件需要更好的网络连接

## 测试验证

实施后需要验证：
1. 小于100MB的文件可以正常上传
2. 超过100MB的文件会被拒绝并返回413错误
3. 所有配置文件中的注释同步更新

## 回滚方案

如需回滚，将上述修改恢复为原始值即可。

---

**设计批准日期**: 2025-03-26
**实施人**: Claude
