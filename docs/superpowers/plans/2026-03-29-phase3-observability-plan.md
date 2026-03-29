# RAG系统第三阶段可观测性增强实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development

**Goal:** 实现完整的可观测性系统，包括OpenTelemetry追踪、Prometheus指标、结构化日志和健康检查

**Architecture:** 
- 后端：OpenTelemetry SDK + Prometheus客户端 + 结构化日志
- 前端：性能指标收集 + 状态监控面板
- 导出：Jaeger（追踪）+ Prometheus（指标）+ 日志文件

**Tech Stack:** Python OpenTelemetry, Prometheus Client, FastAPI, React

---

## Task 1: OpenTelemetry分布式追踪

**Files:**
- Create: `rag_system/monitoring/tracing.py`
- Create: `rag_system/monitoring/middleware.py`
- Modify: `rag_system/api/routes.py`
- Modify: `rag_system/main.py`

### TDD流程

- [ ] **Step 1: 安装依赖**

```bash
pip install opentelemetry-api opentelemetry-sdk opentelemetry-instrumentation-fastapi opentelemetry-exporter-otlp
```

- [ ] **Step 2: 实现追踪配置**

```python
# rag_system/monitoring/tracing.py
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource, SERVICE_NAME, SERVICE_VERSION
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

from rag_system.config.settings import get_settings

settings = get_settings()


def init_tracing(service_name: str = "rag-service"):
    """Initialize OpenTelemetry tracing.
    
    Args:
        service_name: Name of the service for tracing
        
    Returns:
        TracerProvider instance
    """
    resource = Resource.create({
        SERVICE_NAME: service_name,
        SERVICE_VERSION: "1.0.0",
    })
    
    provider = TracerProvider(resource=resource)
    trace.set_tracer_provider(provider)
    
    # Configure OTLP exporter (for Jaeger/Tempo)
    if settings.monitoring.enabled:
        otlp_exporter = OTLPSpanExporter(
            endpoint=settings.monitoring.otlp_endpoint or "http://localhost:4317",
            insecure=True,
        )
        provider.add_span_processor(BatchSpanProcessor(otlp_exporter))
    
    return provider


def get_tracer(name: str = "rag-service"):
    """Get tracer instance."""
    return trace.get_tracer(name)


def instrument_fastapi(app):
    """Instrument FastAPI app with OpenTelemetry."""
    FastAPIInstrumentor.instrument_app(app)
```

- [ ] **Step 3: 实现追踪装饰器**

```python
# rag_system/monitoring/decorators.py
import functools
from typing import Callable, Any
from .tracing import get_tracer


def trace_span(name: str = None, attributes: dict = None):
    """Decorator to trace function execution.
    
    Args:
        name: Span name (defaults to function name)
        attributes: Additional span attributes
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            tracer = get_tracer()
            span_name = name or func.__name__
            
            with tracer.start_as_current_span(span_name) as span:
                if attributes:
                    for key, value in attributes.items():
                        span.set_attribute(key, value)
                
                try:
                    result = await func(*args, **kwargs)
                    span.set_attribute("success", True)
                    return result
                except Exception as e:
                    span.set_attribute("error", True)
                    span.set_attribute("error.message", str(e))
                    span.record_exception(e)
                    raise
        
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            tracer = get_tracer()
            span_name = name or func.__name__
            
            with tracer.start_as_current_span(span_name) as span:
                if attributes:
                    for key, value in attributes.items():
                        span.set_attribute(key, value)
                
                try:
                    result = func(*args, **kwargs)
                    span.set_attribute("success", True)
                    return result
                except Exception as e:
                    span.set_attribute("error", True)
                    span.set_attribute("error.message", str(e))
                    span.record_exception(e)
                    raise
        
        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper
    return decorator
```

- [ ] **Step 4: 添加追踪到关键函数**

在 IndexManager、RAGEngine 等关键类中添加追踪：

```python
from rag_system.monitoring.decorators import trace_span

class IndexManager:
    @trace_span("index_manager.add_document", {"operation": "index.add"})
    async def add_document(self, doc_path: Path) -> bool:
        ...
```

- [ ] **Step 5: Commit**

```bash
git add rag_system/monitoring/
git commit -m "feat(tracing): add OpenTelemetry distributed tracing

- Initialize OpenTelemetry tracing with OTLP exporter
- Add trace_span decorator for function-level tracing
- Instrument FastAPI with OpenTelemetry
- Add tracing to IndexManager operations"
```

---

## Task 2: Prometheus指标暴露

**Files:**
- Create: `rag_system/monitoring/metrics.py`
- Create: `rag_system/api/metrics_routes.py`
- Modify: `rag_system/api/routes.py`

### TDD流程

- [ ] **Step 1: 安装依赖**

```bash
pip install prometheus-client
```

- [ ] **Step 2: 实现指标定义**

```python
# rag_system/monitoring/metrics.py
from prometheus_client import Counter, Histogram, Gauge, Info, generate_latest, CONTENT_TYPE_LATEST
from functools import wraps
import time


# Request metrics
REQUEST_COUNT = Counter(
    'rag_requests_total',
    'Total number of requests',
    ['method', 'endpoint', 'status']
)

REQUEST_DURATION = Histogram(
    'rag_request_duration_seconds',
    'Request duration in seconds',
    ['method', 'endpoint'],
    buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0]
)

# Search metrics
SEARCH_DURATION = Histogram(
    'rag_search_duration_seconds',
    'Search operation duration',
    buckets=[0.01, 0.05, 0.1, 0.5, 1.0, 2.0]
)

SEARCH_HITS = Histogram(
    'rag_search_hits',
    'Number of search hits returned',
    buckets=[1, 3, 5, 10, 20, 50]
)

# Index metrics
INDEX_DOCUMENTS = Gauge(
    'rag_index_documents',
    'Number of documents in index'
)

INDEX_CHUNKS = Gauge(
    'rag_index_chunks',
    'Number of chunks in index'
)

INDEX_OPERATIONS = Counter(
    'rag_index_operations_total',
    'Total index operations',
    ['operation', 'status']
)

# Embedding metrics
EMBEDDING_DURATION = Histogram(
    'rag_embedding_duration_seconds',
    'Embedding generation duration',
    ['backend'],
    buckets=[0.01, 0.05, 0.1, 0.5, 1.0]
)

EMBEDDING_ERRORS = Counter(
    'rag_embedding_errors_total',
    'Total embedding errors',
    ['backend']
)

# Cache metrics
CACHE_HITS = Counter(
    'rag_cache_hits_total',
    'Total cache hits',
    ['cache_type']
)

CACHE_MISSES = Counter(
    'rag_cache_misses_total',
    'Total cache misses',
    ['cache_type']
)

# Service info
SERVICE_INFO = Info('rag_service', 'RAG service information')


def record_request_metrics(method: str, endpoint: str, status: int, duration: float):
    """Record request metrics."""
    REQUEST_COUNT.labels(method=method, endpoint=endpoint, status=status).inc()
    REQUEST_DURATION.labels(method=method, endpoint=endpoint).observe(duration)


def record_search_metrics(duration: float, hits: int):
    """Record search metrics."""
    SEARCH_DURATION.observe(duration)
    SEARCH_HITS.observe(hits)


def record_embedding_metrics(backend: str, duration: float, error: bool = False):
    """Record embedding metrics."""
    EMBEDDING_DURATION.labels(backend=backend).observe(duration)
    if error:
        EMBEDDING_ERRORS.labels(backend=backend).inc()


def update_index_metrics(documents: int, chunks: int):
    """Update index metrics."""
    INDEX_DOCUMENTS.set(documents)
    INDEX_CHUNKS.set(chunks)


def record_cache_hit(cache_type: str):
    """Record cache hit."""
    CACHE_HITS.labels(cache_type=cache_type).inc()


def record_cache_miss(cache_type: str):
    """Record cache miss."""
    CACHE_MISSES.labels(cache_type=cache_type).inc()


def get_metrics():
    """Get Prometheus metrics in text format."""
    return generate_latest()


def init_metrics(service_version: str = "1.0.0"):
    """Initialize metrics with service info."""
    SERVICE_INFO.info({"version": service_version})


class MetricsTimer:
    """Context manager for timing operations."""
    
    def __init__(self, histogram, labels=None):
        self.histogram = histogram
        self.labels = labels or {}
        self.start_time = None
    
    def __enter__(self):
        self.start_time = time.time()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        duration = time.time() - self.start_time
        if self.labels:
            self.histogram.labels(**self.labels).observe(duration)
        else:
            self.histogram.observe(duration)
```

- [ ] **Step 3: 实现指标路由**

```python
# rag_system/api/metrics_routes.py
from fastapi import APIRouter, Response
from rag_system.monitoring.metrics import get_metrics, CONTENT_TYPE_LATEST

router = APIRouter()


@router.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint."""
    return Response(
        content=get_metrics(),
        media_type=CONTENT_TYPE_LATEST
    )
```

- [ ] **Step 4: 集成指标中间件**

```python
# rag_system/monitoring/middleware.py
import time
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from .metrics import record_request_metrics, REQUEST_DURATION


class MetricsMiddleware(BaseHTTPMiddleware):
    """Middleware to record request metrics."""
    
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        
        try:
            response = await call_next(request)
            status_code = response.status_code
        except Exception as e:
            status_code = 500
            raise
        finally:
            duration = time.time() - start_time
            record_request_metrics(
                method=request.method,
                endpoint=request.url.path,
                status=status_code,
                duration=duration
            )
        
        return response
```

- [ ] **Step 5: Commit**

```bash
git add rag_system/monitoring/metrics.py rag_system/api/metrics_routes.py
git commit -m "feat(metrics): add Prometheus metrics collection

- Define comprehensive metrics (requests, search, embedding, cache, index)
- Add Prometheus metrics endpoint at /metrics
- Add MetricsMiddleware for automatic request tracking
- Add helper functions for metric recording"
```

---

## Task 3: 结构化日志系统

**Files:**
- Create: `rag_system/monitoring/logging_config.py`
- Modify: `rag_system/config/settings.py`
- Modify: `rag_system/main.py`

### TDD流程

- [ ] **Step 1: 实现结构化日志配置**

```python
# rag_system/monitoring/logging_config.py
import logging
import json
import sys
from datetime import datetime
from typing import Any, Dict


class JSONFormatter(logging.Formatter):
    """JSON formatter for structured logging."""
    
    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        
        # Add extra fields
        if hasattr(record, "request_id"):
            log_data["request_id"] = record.request_id
        if hasattr(record, "user_id"):
            log_data["user_id"] = record.user_id
        if hasattr(record, "trace_id"):
            log_data["trace_id"] = record.trace_id
        
        # Add exception info
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        
        return json.dumps(log_data, ensure_ascii=False)


def setup_logging(
    level: str = "INFO",
    json_format: bool = True,
    log_file: str = None
):
    """Setup structured logging.
    
    Args:
        level: Log level (DEBUG, INFO, WARNING, ERROR)
        json_format: Use JSON format
        log_file: Optional log file path
    """
    handlers = [logging.StreamHandler(sys.stdout)]
    
    if log_file:
        file_handler = logging.FileHandler(log_file)
        handlers.append(file_handler)
    
    formatter = JSONFormatter() if json_format else logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    for handler in handlers:
        handler.setFormatter(formatter)
    
    # Configure root logger
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        handlers=handlers,
        force=True
    )
    
    # Configure specific loggers
    logging.getLogger("uvicorn").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)


class ContextualLogger:
    """Logger with context support."""
    
    def __init__(self, name: str):
        self.logger = logging.getLogger(name)
        self.context: Dict[str, Any] = {}
    
    def with_context(self, **kwargs) -> "ContextualLogger":
        """Create logger with additional context."""
        new_logger = ContextualLogger(self.logger.name)
        new_logger.context = {**self.context, **kwargs}
        return new_logger
    
    def _log(self, level: int, msg: str, *args, **kwargs):
        """Log with context."""
        extra = kwargs.get("extra", {})
        extra.update(self.context)
        kwargs["extra"] = extra
        self.logger.log(level, msg, *args, **kwargs)
    
    def debug(self, msg: str, *args, **kwargs):
        self._log(logging.DEBUG, msg, *args, **kwargs)
    
    def info(self, msg: str, *args, **kwargs):
        self._log(logging.INFO, msg, *args, **kwargs)
    
    def warning(self, msg: str, *args, **kwargs):
        self._log(logging.WARNING, msg, *args, **kwargs)
    
    def error(self, msg: str, *args, **kwargs):
        self._log(logging.ERROR, msg, *args, **kwargs)
    
    def exception(self, msg: str, *args, **kwargs):
        kwargs["exc_info"] = True
        self._log(logging.ERROR, msg, *args, **kwargs)


def get_logger(name: str) -> ContextualLogger:
    """Get contextual logger."""
    return ContextualLogger(name)
```

- [ ] **Step 2: 添加日志配置到 Settings**

```python
# rag_system/config/settings.py

@dataclass
class LoggingConfig:
    """Logging configuration."""
    level: str = "INFO"
    format: str = "json"  # "json" or "text"
    file_path: Optional[str] = None
    max_bytes: int = 10_000_000
    backup_count: int = 5
```

- [ ] **Step 3: 集成到主应用**

```python
# rag_system/main.py
from rag_system.monitoring.logging_config import setup_logging
from rag_system.monitoring.metrics import init_metrics
from rag_system.config.settings import get_settings

settings = get_settings()

# Setup logging
setup_logging(
    level=settings.logging.level,
    json_format=settings.logging.format == "json",
    log_file=settings.logging.file_path
)

# Initialize metrics
init_metrics()

logger = get_logger(__name__)
logger.info("RAG service starting", extra={"version": "1.0.0"})
```

- [ ] **Step 4: Commit**

```bash
git add rag_system/monitoring/logging_config.py
git commit -m "feat(logging): add structured logging with JSON format

- Implement JSONFormatter for structured logging
- Add ContextualLogger for request context
- Support file and console output
- Configurable log levels and formats"
```

---

## Task 4: 健康检查端点

**Files:**
- Create: `rag_system/api/health_routes.py`
- Modify: `rag_system/api/routes.py`

### TDD流程

- [ ] **Step 1: 实现健康检查**

```python
# rag_system/api/health_routes.py
import time
from datetime import datetime
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import Dict, Any

from rag_system.index.manager import IndexManager
from rag_system.cache.redis_cache import RedisCache
from rag_system.config.settings import get_settings

router = APIRouter()

# Startup time for uptime calculation
START_TIME = time.time()


class HealthStatus(BaseModel):
    """Health check response."""
    status: str  # "healthy", "degraded", "unhealthy"
    timestamp: str
    uptime_seconds: float
    version: str = "1.0.0"
    checks: Dict[str, Any]


class ReadinessStatus(BaseModel):
    """Readiness check response."""
    ready: bool
    timestamp: str
    checks: Dict[str, Any]


def check_index_health() -> Dict[str, Any]:
    """Check index health."""
    try:
        # Check if index manager is initialized
        status = {"status": "ok", "message": "Index manager available"}
        return status
    except Exception as e:
        return {"status": "error", "message": str(e)}


def check_cache_health() -> Dict[str, Any]:
    """Check cache health."""
    settings = get_settings()
    if not settings.cache.enabled:
        return {"status": "disabled", "message": "Cache disabled"}
    
    try:
        # Try to ping cache
        return {"status": "ok", "message": "Cache available"}
    except Exception as e:
        return {"status": "error", "message": str(e)}


def check_embedding_backend() -> Dict[str, Any]:
    """Check embedding backend health."""
    try:
        from rag_system.backends.embedding import get_embedding_backend
        backend = get_embedding_backend()
        return {
            "status": "ok",
            "backend": backend.name,
            "healthy": backend.is_healthy() if hasattr(backend, 'is_healthy') else True
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}


@router.get("/health", response_model=HealthStatus)
async def health_check():
    """Health check endpoint.
    
    Returns overall system health status.
    """
    checks = {
        "index": check_index_health(),
        "cache": check_cache_health(),
        "embedding": check_embedding_backend(),
    }
    
    # Determine overall status
    failed_checks = [k for k, v in checks.items() if v.get("status") == "error"]
    degraded_checks = [k for k, v in checks.items() if v.get("status") == "degraded"]
    
    if failed_checks:
        status = "unhealthy"
    elif degraded_checks:
        status = "degraded"
    else:
        status = "healthy"
    
    return HealthStatus(
        status=status,
        timestamp=datetime.utcnow().isoformat(),
        uptime_seconds=time.time() - START_TIME,
        checks=checks
    )


@router.get("/ready", response_model=ReadinessStatus)
async def readiness_check():
    """Readiness check endpoint.
    
    Returns whether the service is ready to accept traffic.
    """
    checks = {
        "index": check_index_health(),
        "embedding": check_embedding_backend(),
    }
    
    ready = all(
        v.get("status") in ["ok", "disabled"]
        for v in checks.values()
    )
    
    return ReadinessStatus(
        ready=ready,
        timestamp=datetime.utcnow().isoformat(),
        checks=checks
    )


@router.get("/live")
async def liveness_check():
    """Liveness check endpoint.
    
    Simple check that the service is alive.
    """
    return {"status": "alive", "timestamp": datetime.utcnow().isoformat()}
```

- [ ] **Step 2: Commit**

```bash
git add rag_system/api/health_routes.py
git commit -m "feat(health): add health check endpoints

- Add /health endpoint with comprehensive checks
- Add /ready endpoint for readiness probes
- Add /live endpoint for liveness probes
- Check index, cache, and embedding backend health"
```

---

## Task 5: 前端监控面板

**Files:**
- Create: `web-new/src/features/monitoring/components/MetricsPanel.tsx`
- Create: `web-new/src/features/monitoring/hooks/useMetrics.ts`
- Modify: `web-new/src/pages/Admin/Admin.tsx`

### TDD流程

- [ ] **Step 1: 实现指标 API**

```typescript
// web-new/src/services/monitoringApi.ts
import { apiClient } from './api';

export interface HealthStatus {
  status: 'healthy' | 'degraded' | 'unhealthy';
  timestamp: string;
  uptime_seconds: number;
  version: string;
  checks: Record<string, {
    status: string;
    message?: string;
  }>;
}

export interface MetricsData {
  // Prometheus format metrics
  metrics: string;
}

export const monitoringApi = {
  getHealth: async (): Promise<HealthStatus> => {
    const response = await apiClient.get('/health');
    return response.data;
  },
  
  getMetrics: async (): Promise<MetricsData> => {
    const response = await apiClient.get('/metrics');
    return { metrics: response.data };
  },
};
```

- [ ] **Step 2: 实现 MetricsPanel 组件**

```tsx
// web-new/src/features/monitoring/components/MetricsPanel.tsx
import React from 'react';
import { Card, Statistic, Row, Col, Tag, Timeline, Spin } from 'antd';
import { CheckCircleOutlined, WarningOutlined, CloseCircleOutlined } from '@ant-design/icons';
import { useMetrics } from '../hooks/useMetrics';

export const MetricsPanel: React.FC = () => {
  const { health, loading, error } = useMetrics();

  if (loading) return <Spin size="large" />;
  if (error) return <div>Error loading metrics</div>;
  if (!health) return null;

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'healthy':
      case 'ok':
        return <CheckCircleOutlined style={{ color: '#52c41a' }} />;
      case 'degraded':
        return <WarningOutlined style={{ color: '#faad14' }} />;
      case 'unhealthy':
      case 'error':
        return <CloseCircleOutlined style={{ color: '#ff4d4f' }} />;
      default:
        return <WarningOutlined style={{ color: '#999' }} />;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'healthy':
        return 'success';
      case 'degraded':
        return 'warning';
      case 'unhealthy':
        return 'error';
      default:
        return 'default';
    }
  };

  return (
    <div>
      <Row gutter={[16, 16]}>
        <Col span={12}>
          <Card title="System Health">
            <Statistic
              title="Status"
              value={health.status}
              prefix={getStatusIcon(health.status)}
              valueStyle={{
                color: health.status === 'healthy' ? '#52c41a' : 
                       health.status === 'degraded' ? '#faad14' : '#ff4d4f'
              }}
            />
            <div style={{ marginTop: 16 }}>
              <Tag color="blue">Version: {health.version}</Tag>
              <Tag>Uptime: {Math.floor(health.uptime_seconds / 60)}m</Tag>
            </div>
          </Card>
        </Col>
        <Col span={12}>
          <Card title="Component Status">
            <Timeline>
              {Object.entries(health.checks).map(([name, check]) => (
                <Timeline.Item
                  key={name}
                  dot={getStatusIcon(check.status)}
                  color={getStatusColor(check.status)}
                >
                  <strong>{name}</strong>: {check.status}
                  {check.message && <div style={{ fontSize: 12, color: '#999' }}>{check.message}</div>}
                </Timeline.Item>
              ))}
            </Timeline>
          </Card>
        </Col>
      </Row>
    </div>
  );
};
```

- [ ] **Step 3: Commit**

```bash
git add web-new/src/features/monitoring/
git commit -m "feat(monitoring): add frontend metrics panel

- Add monitoring API service
- Add MetricsPanel component with health display
- Show system health and component status
- Auto-refresh health status"
```

---

## 最终验证

- [ ] **运行测试**

```bash
# Backend tests
pytest tests/ -v

# Frontend type check
cd web-new && npm run typecheck

# Build check
cd web-new && npm run build
```

- [ ] **验证端点**

1. `curl http://localhost:8000/health` - 健康检查
2. `curl http://localhost:8000/metrics` - Prometheus 指标
3. `curl http://localhost:8000/ready` - 就绪检查

- [ ] **Commit 最终版本**

```bash
git add .
git commit -m "feat(monitoring): complete observability enhancement

- OpenTelemetry distributed tracing
- Prometheus metrics collection
- Structured JSON logging
- Health check endpoints
- Frontend monitoring panel
- Full observability stack implemented"
```

---

**执行顺序**: Task 1 → Task 2 → Task 3 → Task 4 → Task 5
**预计时间**: 6-8 小时
**依赖**: Phase 1 & 2 已完成