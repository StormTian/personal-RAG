# 部署指南

本文档详细介绍 Tiny RAG Demo 的部署方法和生产环境配置。

## 📋 目录

- [快速部署](#快速部署)
- [Docker 部署](#docker-部署)
- [生产环境配置](#生产环境配置)
- [环境变量](#环境变量)
- [性能调优](#性能调优)
- [监控和日志](#监控和日志)
- [安全建议](#安全建议)

## 快速部署

### 单服务器部署

#### 1. 准备服务器

```bash
# Ubuntu/Debian
sudo apt update
sudo apt install python3 python3-pip python3-venv

# CentOS/RHEL
sudo yum install python3 python3-pip

# macOS (假设已安装 Homebrew)
brew install python3
```

#### 2. 部署应用

```bash
# 创建应用目录
sudo mkdir -p /opt/rag-demo
cd /opt/rag-demo

# 克隆代码（或上传）
sudo git clone <repository-url> .

# 创建虚拟环境
sudo python3 -m venv .venv
source .venv/bin/activate

# 安装依赖
pip install -r requirements.txt

# 准备文档库
sudo mkdir -p document_library
sudo chown -R $USER:$USER document_library

# 复制文档到库
# cp /path/to/docs/* document_library/
```

#### 3. 配置 Systemd 服务

创建服务文件：

```bash
sudo tee /etc/systemd/system/rag-demo.service << 'EOF'
[Unit]
Description=Tiny RAG Demo
After=network.target

[Service]
Type=simple
User=ragdemo
Group=ragdemo
WorkingDirectory=/opt/rag-demo
Environment="PATH=/opt/rag-demo/.venv/bin"
Environment="PYTHONPATH=/opt/rag-demo/.deps"
ExecStart=/opt/rag-demo/.venv/bin/python web_app.py --host 0.0.0.0 --port 8000
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
EOF
```

创建用户并启动：

```bash
# 创建用户
sudo useradd -r -s /bin/false ragdemo
sudo chown -R ragdemo:ragdemo /opt/rag-demo

# 重载配置
sudo systemctl daemon-reload

# 启动服务
sudo systemctl start rag-demo
sudo systemctl enable rag-demo

# 查看状态
sudo systemctl status rag-demo
```

#### 4. 配置 Nginx（可选）

```bash
sudo tee /etc/nginx/sites-available/rag-demo << 'EOF'
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
    }
}
EOF

# 启用配置
sudo ln -s /etc/nginx/sites-available/rag-demo /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

## Docker 部署

### Dockerfile

```dockerfile
# Dockerfile
FROM python:3.11-slim

WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    git \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制代码
COPY app.py web_app.py ./
COPY web/ ./web/

# 创建文档库目录
RUN mkdir -p document_library

# 暴露端口
EXPOSE 8000

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/api/health')" || exit 1

# 启动命令
CMD ["python", "web_app.py", "--host", "0.0.0.0", "--port", "8000"]
```

### 构建和运行

```bash
# 构建镜像
docker build -t rag-demo:latest .

# 运行容器
docker run -d \
    --name rag-demo \
    -p 8000:8000 \
    -v $(pwd)/document_library:/app/document_library \
    -e OPENAI_API_KEY=${OPENAI_API_KEY} \
    --restart unless-stopped \
    rag-demo:latest

# 查看日志
docker logs -f rag-demo
```

### Docker Compose

```yaml
# docker-compose.yml
version: '3.8'

services:
  rag-demo:
    build: .
    container_name: rag-demo
    ports:
      - "8000:8000"
    volumes:
      - ./document_library:/app/document_library
      - ./.index_cache.pkl:/app/.index_cache.pkl
    environment:
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - OPENAI_EMBED_MODEL=${OPENAI_EMBED_MODEL}
      - OPENAI_RERANK_MODEL=${OPENAI_RERANK_MODEL}
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "python", "-c", "import urllib.request; urllib.request.urlopen('http://localhost:8000/api/health')"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 5s

  nginx:
    image: nginx:alpine
    container_name: rag-demo-nginx
    ports:
      - "80:80"
    volumes:
      - ./nginx.conf:/etc/nginx/conf.d/default.conf
    depends_on:
      - rag-demo
    restart: unless-stopped
```

### 多阶段构建优化

```dockerfile
# 多阶段构建
FROM python:3.11-slim as builder

WORKDIR /build
COPY requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt

FROM python:3.11-slim

# 从构建阶段复制依赖
COPY --from=builder /root/.local /root/.local

WORKDIR /app
COPY app.py web_app.py ./
COPY web/ ./web/

ENV PATH=/root/.local/bin:$PATH
ENV PYTHONPATH=/app/.deps

RUN mkdir -p document_library

EXPOSE 8000

CMD ["python", "web_app.py", "--host", "0.0.0.0", "--port", "8000"]
```

## 生产环境配置

### 配置文件

创建 `config/production.env`：

```bash
# 服务配置
RAG_HOST=0.0.0.0
RAG_PORT=8000
RAG_WORKERS=4

# 文档库配置
RAG_LIBRARY_DIR=/opt/rag-demo/document_library
RAG_CACHE_DIR=/opt/rag-demo/cache

# Embedding 配置（可选）
OPENAI_API_KEY=sk-...
OPENAI_EMBED_MODEL=text-embedding-3-small
OPENAI_BASE_URL=https://api.openai.com

# Rerank 配置（可选）
OPENAI_RERANK_MODEL=gpt-4o-mini
OPENAI_RERANK_TIMEOUT=45
OPENAI_RERANK_MAX_CANDIDATES=12

# 日志配置
RAG_LOG_LEVEL=INFO
RAG_LOG_FILE=/var/log/rag-demo/app.log
```

### 使用配置文件

```bash
# 加载环境变量
export $(cat config/production.env | xargs)

# 启动服务
python web_app.py
```

### Gunicorn 部署（可选）

```bash
# 安装 gunicorn
pip install gunicorn

# 创建启动脚本
gunicorn -w 4 -b 0.0.0.0:8000 --access-logfile /var/log/rag-demo/access.log \
    --error-logfile /var/log/rag-demo/error.log \
    --capture-output \
    --enable-stdio-inheritance \
    web_app:main
```

## 环境变量

### 完整环境变量列表

| 变量名 | 必需 | 默认值 | 说明 |
|--------|------|--------|------|
| `RAG_HOST` | 否 | 127.0.0.1 | 服务监听地址 |
| `RAG_PORT` | 否 | 8000 | 服务端口 |
| `RAG_LIBRARY_DIR` | 否 | document_library | 文档库目录 |
| `OPENAI_API_KEY` | 否 | - | OpenAI API 密钥 |
| `OPENAI_EMBED_MODEL` | 否 | - | Embedding 模型 |
| `OPENAI_BASE_URL` | 否 | https://api.openai.com | API 基础 URL |
| `OPENAI_RERANK_MODEL` | 否 | - | Rerank 模型 |
| `OPENAI_RERANK_BASE_URL` | 否 | OPENAI_BASE_URL | Rerank API URL |
| `OPENAI_RERANK_TIMEOUT` | 否 | 45 | Rerank 超时（秒） |
| `OPENAI_RERANK_MAX_CANDIDATES` | 否 | 12 | 最大候选数 |
| `RAG_LOG_LEVEL` | 否 | INFO | 日志级别 |
| `RAG_LOG_FILE` | 否 | - | 日志文件路径 |

### 环境变量示例

```bash
#!/bin/bash
# production.sh

export RAG_HOST=0.0.0.0
export RAG_PORT=8000
export RAG_LIBRARY_DIR=/data/documents

# OpenAI 配置（可选）
export OPENAI_API_KEY="sk-..."
export OPENAI_EMBED_MODEL="text-embedding-3-small"
export OPENAI_RERANK_MODEL="gpt-4o-mini"

# 日志配置
export RAG_LOG_LEVEL=INFO
export RAG_LOG_FILE=/var/log/rag-demo/app.log

# 启动
python web_app.py
```

## 性能调优

### 1. 索引优化

#### 预热缓存

```bash
# 启动时预建索引
python app.py --list-docs

# 将缓存文件放到内存盘（tmpfs）
sudo mount -t tmpfs -o size=1G tmpfs /opt/rag-demo/cache
ln -s /opt/rag-demo/cache/.index_cache.pkl /opt/rag-demo/.index_cache.pkl
```

#### 索引分片（大型文档库）

```python
# 按类别分片
document_library/
├── category_a/
├── category_b/
└── category_c/

# 为每个类别单独建立 RAG 实例
rag_a = TinyRAG(Path("document_library/category_a"))
rag_b = TinyRAG(Path("document_library/category_b"))
```

### 2. 并发优化

#### 多进程部署

```python
# web_app_multiprocess.py
from multiprocessing import Process
import web_app

def run_server(port):
    import sys
    sys.argv = ['', '--port', str(port)]
    web_app.main()

if __name__ == '__main__':
    ports = [8000, 8001, 8002, 8003]
    processes = []
    
    for port in ports:
        p = Process(target=run_server, args=(port,))
        p.start()
        processes.append(p)
    
    for p in processes:
        p.join()
```

#### Nginx 负载均衡

```nginx
upstream rag_demo {
    least_conn;
    server 127.0.0.1:8000;
    server 127.0.0.1:8001;
    server 127.0.0.1:8002;
    server 127.0.0.1:8003;
}

server {
    listen 80;
    
    location / {
        proxy_pass http://rag_demo;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

### 3. 缓存优化

#### 内存缓存

```python
# 添加内存缓存层
from functools import lru_cache

class CachedRAG:
    def __init__(self, rag: TinyRAG):
        self.rag = rag
    
    @lru_cache(maxsize=1000)
    def search(self, query: str, top_k: int = 3):
        return self.rag.search(query, top_k)
```

### 4. 资源限制

#### Systemd 资源限制

```ini
# /etc/systemd/system/rag-demo.service
[Service]
# 内存限制
MemoryMax=2G
MemorySwapMax=0

# CPU 限制
CPUQuota=200%

# 文件描述符
LimitNOFILE=65535

# 进程数
LimitNPROC=100
```

### 性能基准

```bash
# 使用 Apache Bench 测试
ab -n 1000 -c 10 -p post.json -T application/json \
   http://localhost:8000/api/ask

# post.json 内容:
# {"query":"测试问题","top_k":3}
```

## 监控和日志

### 日志配置

#### Python 日志

```python
# logging_config.py
import logging
import logging.handlers

def setup_logging():
    logger = logging.getLogger('rag_demo')
    logger.setLevel(logging.INFO)
    
    # 文件日志（轮转）
    file_handler = logging.handlers.RotatingFileHandler(
        '/var/log/rag-demo/app.log',
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5
    )
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    ))
    
    # 控制台日志
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(logging.Formatter(
        '%(levelname)s: %(message)s'
    ))
    
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
```

#### Logrotate 配置

```bash
# /etc/logrotate.d/rag-demo
/var/log/rag-demo/*.log {
    daily
    rotate 30
    compress
    delaycompress
    missingok
    notifempty
    create 644 ragdemo ragdemo
    postrotate
        systemctl reload rag-demo
    endscript
}
```

### 监控指标

#### 自定义指标

```python
# metrics.py
import time
from functools import wraps
from collections import defaultdict

class Metrics:
    def __init__(self):
        self.request_count = 0
        self.request_times = defaultdict(list)
        self.error_count = 0
    
    def record_request(self, endpoint: str, duration: float):
        self.request_count += 1
        self.request_times[endpoint].append(duration)
    
    def record_error(self):
        self.error_count += 1
    
    def get_stats(self):
        return {
            'request_count': self.request_count,
            'error_count': self.error_count,
            'avg_response_time': {
                k: sum(v)/len(v) if v else 0
                for k, v in self.request_times.items()
            }
        }

metrics = Metrics()
```

#### Prometheus 指标

```python
# prometheus_metrics.py
from prometheus_client import Counter, Histogram, start_http_server

request_count = Counter('rag_requests_total', 'Total requests')
request_duration = Histogram('rag_request_duration_seconds', 'Request duration')
error_count = Counter('rag_errors_total', 'Total errors')

start_http_server(9090)  # Prometheus 端点
```

### 健康检查

```bash
# 健康检查脚本
#!/bin/bash
HEALTH_URL="http://localhost:8000/api/health"

response=$(curl -s -w "%{http_code}" -o /tmp/health.json $HEALTH_URL)

if [ "$response" == "200" ]; then
    echo "Health check passed"
    cat /tmp/health.json | jq .
    exit 0
else
    echo "Health check failed with status $response"
    exit 1
fi
```

## 安全建议

### 1. 网络安全

#### 防火墙配置

```bash
# UFW (Ubuntu)
sudo ufw allow 22/tcp
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable

# Firewalld (CentOS)
sudo firewall-cmd --permanent --add-service=http
sudo firewall-cmd --permanent --add-service=https
sudo firewall-cmd --reload
```

### 2. API 密钥保护

```bash
# 使用文件权限限制
chmod 600 /opt/rag-demo/.env

# 或使用密钥管理服务
export OPENAI_API_KEY=$(aws secretsmanager get-secret-value --secret-id rag-demo/openai-key --query SecretString --output text)
```

### 3. HTTPS 配置

#### Let's Encrypt

```bash
# 安装 certbot
sudo apt install certbot python3-certbot-nginx

# 获取证书
sudo certbot --nginx -d your-domain.com

# 自动续期
sudo certbot renew --dry-run
```

#### 手动配置

```nginx
server {
    listen 443 ssl http2;
    server_name your-domain.com;
    
    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;
    
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;
    
    location / {
        proxy_pass http://127.0.0.1:8000;
        # ...
    }
}
```

### 4. 访问控制

#### Nginx 基本认证

```bash
# 创建密码文件
sudo htpasswd -c /etc/nginx/.htpasswd admin

# Nginx 配置
location / {
    auth_basic "RAG Demo";
    auth_basic_user_file /etc/nginx/.htpasswd;
    proxy_pass http://127.0.0.1:8000;
}
```

#### IP 限制

```nginx
location / {
    allow 192.168.1.0/24;
    allow 10.0.0.0/8;
    deny all;
    
    proxy_pass http://127.0.0.1:8000;
}
```

---

**提示**: 生产环境部署前，请务必进行充分测试。
