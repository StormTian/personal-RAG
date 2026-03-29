# RAG系统第四阶段安全加固实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development

**Goal:** 实施全面的安全加固，包括CSP策略、审计日志、IP限流、SQL注入防护和输入验证

**Architecture:** 
- 后端：FastAPI中间件 + 安全装饰器 + 审计日志
- 前端：CSP安全策略 + CSRF防护
- 基础设施：Redis限流 + 输入验证

**Tech Stack:** Python FastAPI, React, Redis, slowapi

---

## Task 1: 审计日志系统

**Files:**
- Create: `rag_system/security/audit_logger.py`
- Create: `rag_system/security/middleware.py`
- Modify: `rag_system/config/settings.py`

### 功能描述
1. **操作审计**: 记录所有关键操作（搜索、上传、删除、登录）
2. **审计日志存储**: 异步写入文件或数据库
3. **敏感操作标记**: 标记高风险操作
4. **日志轮转**: 自动清理旧日志

---

## Task 2: IP限流和速率限制

**Files:**
- Create: `rag_system/security/rate_limiter.py`
- Modify: `rag_system/api/routes.py`
- Modify: `rag_system/main.py`

### 功能描述
1. **请求限流**: 基于IP的请求速率限制
2 **端点限流**: 不同端点不同限制（搜索、上传）
3. **Redis后端**: 分布式限流支持
4. **自定义响应**: 友好的限流提示

---

## Task 3: CSP安全策略和CSRF防护

**Files:**
- Modify: `rag_system/api/middleware.py` (添加CSP头)
- Modify: `web-new/index.html` (添加CSP meta)
- Modify: `web-new/src/utils/security.ts` (CSRF token)

### 功能描述
1. **CSP策略**: 限制资源加载来源
2. **CSRF防护**: 验证请求来源
3. **安全Header**: X-Frame-Options, X-Content-Type-Options等

---

## Task 4: 输入验证和SQL注入防护

**Files:**
- Create: `rag_system/security/validators.py`
- Modify: `rag_system/api/routes.py`

### 功能描述
1. **输入清洗**: 清理用户输入中的危险字符
2. **参数验证**: Pydantic模型严格验证
3. **SQL注入防护**: 参数化查询和输入转义
4. **文件上传验证**: 文件名和内容类型检查

---

## Task 5: 安全配置和密钥管理

**Files:**
- Modify: `rag_system/config/settings.py`
- Create: `.env.example`
- Modify: `web-new/vite.config.ts`

### 功能描述
1. **环境变量**: 敏感配置从环境变量读取
2. **密钥管理**: API密钥、数据库密码等
3. **配置加密**: 可选的配置加密存储
4. **安全默认值**: 安全的默认配置

---

**执行顺序**: Task 1 → Task 2 → Task 3 → Task 4 → Task 5
**预计时间**: 4-5 小时