# LLM服务部署指南

## 📋 概述

本文档提供LLM服务的生产环境部署指南。

---

## 🚀 部署前准备

### 1. 环境要求

**系统要求**：
- macOS 10.15+ 或 Linux (Ubuntu 20.04+)
- Go 1.21+
- OpenAI API密钥或兼容的LLM服务
- Redis 6.0+（可选，用于分布式缓存）

**API密钥**：
```bash
# OpenAI API
export OPENAI_API_KEY=sk-...

# 或其他兼容API
export LLM_API_BASE_URL=https://api.openai.com/v1
export LLM_API_KEY=sk-...
```

### 2. 配置检查

**环境变量**：
```bash
# LLM API配置
export LLM_API_BASE_URL=https://api.openai.com/v1
export LLM_API_KEY=sk-...
export LLM_MODEL=gpt-3.5-turbo
export LLM_TIMEOUT=30

# Redis配置（可选）
export REDIS_HOST=localhost
export REDIS_PORT=16379
export REDIS_DB=0

# 缓存配置
export CACHE_LOCAL_SIZE=500
export CACHE_TTL=86400  # 24小时

# 并发配置
export MAX_CONCURRENCY=10
```

---

## 🔧 编译和安装

### 1. 编译Go二进制

```bash
cd gateway-unified/services/llm

# 整理依赖
go mod tidy

# 编译为可执行文件
go build -o llm-service

# 或编译为静态链接二进制（推荐用于生产）
CGO_ENABLED=0 go build -a -ldflags '-extldflags "-static"' -o llm-service
```

### 2. 验证编译

```bash
# 检查二进制文件
./llm-service --help

# 或运行测试
go test -v ./...
```

---

## 📦 部署方式

### 方式1：独立服务部署

#### 1. 创建systemd服务（Linux）

```bash
# 创建服务文件
sudo vim /etc/systemd/system/athena-llm.service
```

**服务配置**：
```ini
[Unit]
Description=Athena LLM Service
After=network.target

[Service]
Type=simple
User=athena
Group=athena
WorkingDirectory=/opt/athena/llm-service
ExecStart=/opt/athena/llm-service/llm-service
Restart=always
RestartSec=5

# 环境变量
Environment="LLM_API_BASE_URL=https://api.openai.com/v1"
Environment="LLM_API_KEY=sk-..."
Environment="LLM_MODEL=gpt-3.5-turbo"
Environment="REDIS_HOST=localhost"
Environment="REDIS_PORT=16379"
Environment="CACHE_LOCAL_SIZE=500"
Environment="MAX_CONCURRENCY=10"

# 日志
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

#### 2. 启动服务

```bash
# 重载systemd配置
sudo systemctl daemon-reload

# 启用开机自启
sudo systemctl enable athena-llm

# 启动服务
sudo systemctl start athena-llm

# 查看状态
sudo systemctl status athena-llm

# 查看日志
sudo journalctl -u athena-llm -f
```

### 方式2：Docker部署

#### 1. 创建Dockerfile

```dockerfile
FROM golang:1.21-alpine AS builder

WORKDIR /app
COPY go.mod go.sum ./
RUN go mod download

COPY . .
RUN CGO_ENABLED=0 go build -o llm-service

FROM alpine:latest
RUN apk --no-cache add ca-certificates
WORKDIR /root/

COPY --from=builder /app/llm-service .
COPY config.yaml .

EXPOSE 8024

CMD ["./llm-service"]
```

#### 2. Docker Compose

```yaml
version: '3.8'

services:
  llm-service:
    build: .
    ports:
      - "8024:8024"
    environment:
      - LLM_API_BASE_URL=https://api.openai.com/v1
      - LLM_API_KEY=${LLM_API_KEY}
      - REDIS_HOST=redis
      - REDIS_PORT=6379
      - CACHE_LOCAL_SIZE=500
      - MAX_CONCURRENCY=10
    depends_on:
      - redis
    restart: unless-stopped

  redis:
    image: redis:7-alpine
    ports:
      - "16379:6379"
    volumes:
      - redis-data:/data
    restart: unless-stopped

volumes:
  redis-data:
```

#### 3. 构建和运行

```bash
# 构建并启动
docker-compose up -d

# 查看日志
docker-compose logs -f llm-service

# 停止服务
docker-compose down
```

### 方式3：Kubernetes部署

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: athena-llm
spec:
  replicas: 3
  selector:
    matchLabels:
      app: athena-llm
  template:
    metadata:
      labels:
        app: athena-llm
    spec:
      containers:
      - name: llm-service
        image: athena-llm:latest
        ports:
        - containerPort: 8024
        env:
        - name: LLM_API_BASE_URL
          value: "https://api.openai.com/v1"
        - name: LLM_API_KEY
          valueFrom:
            secretKeyRef:
              name: llm-secrets
              key: api-key
        - name: REDIS_HOST
          value: "redis"
        resources:
          requests:
            memory: "256Mi"
            cpu: "200m"
          limits:
            memory: "1Gi"
            cpu: "1000m"
---
apiVersion: v1
kind: Service
metadata:
  name: athena-llm
spec:
  selector:
    app: athena-llm
  ports:
  - port: 8024
    targetPort: 8024
  type: ClusterIP
```

---

## 🔍 健康检查

### 1. 检查服务状态

```bash
# 检查进程
ps aux | grep llm-service

# 检查端口
lsof -i :8024

# 检查健康端点
curl http://localhost:8024/health
```

### 2. API测试

```bash
# 测试聊天端点
curl -X POST http://localhost:8024/chat \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [
      {"role": "user", "content": "Hello!"}
    ]
  }'
```

---

## 📊 监控和日志

### 1. Prometheus指标

```bash
# 访问指标端点
curl http://localhost:8024/metrics
```

**关键指标**：
- `llm_requests_total` - 总请求数
- `llm_response_time_milliseconds` - 响应时间
- `llm_cache_hits_total` - 缓存命中数
- `llm_cost_total_dollars` - 总成本

### 2. Grafana仪表板

**推荐面板**：
1. 请求QPS和延迟
2. 缓存命中率
3. 成本统计
4. 模型使用分布

### 3. 日志配置

```yaml
# config.yaml
logging:
  level: info
  format: json
  output: stdout
```

---

## 🛠️ 故障排查

### 问题1：API调用失败

**症状**：
```
Error: LLM API request failed: 401 Unauthorized
```

**解决**：
```bash
# 检查API密钥
echo $LLM_API_KEY

# 验证API密钥
curl https://api.openai.com/v1/models \
  -H "Authorization: Bearer $LLM_API_KEY"

# 更新API密钥
export LLM_API_KEY=sk-new-key
sudo systemctl restart athena-llm
```

### 问题2：缓存未命中

**症状**：
- 缓存命中率< 50%

**解决**：
```bash
# 检查Redis状态
docker ps | grep redis

# 增加缓存容量
export CACHE_LOCAL_SIZE=1000

# 延长TTL
export CACHE_TTL=86400  # 24小时
```

### 问题3：并发限制

**症状**：
```
Error: too many concurrent requests
```

**解决**：
```bash
# 增加并发限制
export MAX_CONCURRENCY=20

# 或使用队列
export ENABLE_QUEUE=true
export QUEUE_SIZE=100
```

---

## 📝 配置参考

### 完整配置文件

```yaml
# config.yaml
server:
  port: 8024
  host: "0.0.0.0"
  read_timeout: 60
  write_timeout: 60

llm:
  api_base_url: "https://api.openai.com/v1"
  api_key: "sk-..."
  model: "gpt-3.5-turbo"
  timeout: 30
  max_retries: 3

routing:
  enabled: true
  default_tier: "balanced"

cache:
  redis_addr: "localhost:16379"
  redis_db: 0
  local_size: 500
  ttl: 86400  # 24小时
  min_tokens: 50
  max_entry_size: 10240  # 10KB
  enabled: true

concurrent:
  max_concurrency: 10
  queue_size: 100
  timeout: 30

monitoring:
  enabled: true
  metrics_path: "/metrics"
  health_path: "/health"
```

### 智能路由配置

```yaml
routing:
  models:
    economy:
      model_name: "gpt-3.5-turbo"
      cost_per_1k: 0.002
      speed: 10
      quality: 6

    balanced:
      model_name: "gpt-4o-mini"
      cost_per_1k: 0.15
      speed: 7
      quality: 8

    premium:
      model_name: "gpt-4o"
      cost_per_1k: 2.50
      speed: 5
      quality: 10

  rules:
    - name: "simple_qa"
      keywords: ["什么是", "如何", "怎么"]
      target_tier: "economy"
      priority: 10

    - name: "patent_analysis"
      keywords: ["专利", "创造性", "侵权"]
      target_tier: "premium"
      priority: 100
```

---

## 🎯 性能调优

### 1. 连接池优化

```yaml
llm:
  max_idle_conns: 100
  max_idle_conns_per_host: 20
  idle_conn_timeout: 90
```

### 2. 缓存优化

```yaml
cache:
  local_size: 1000       # 增加本地缓存
  ttl: 86400            # 延长TTL到24小时
  min_tokens: 10        # 降低最小token数
```

### 3. 并发优化

```yaml
concurrent:
  max_concurrency: 20   # 增加并发数
  queue_size: 200       # 增加队列大小
```

---

## 🔄 升级和回滚

### 1. 滚动升级

```bash
# 1. 编译新版本
go build -o llm-service-new

# 2. 备份当前版本
cp llm-service llm-service.old

# 3. 替换二进制
mv llm-service-new llm-service

# 4. 重启服务
sudo systemctl restart athena-llm

# 5. 验证
curl http://localhost:8024/health
```

### 2. 回滚

```bash
# 如果出现问题，快速回滚
mv llm-service.old llm-service
sudo systemctl restart athena-llm
```

---

## 💰 成本优化建议

### 1. 启用智能路由

```yaml
routing:
  enabled: true
  # 70%使用经济型模型
  economy_ratio: 0.7
```

**预期节省**: 30%

### 2. 增加缓存容量

```yaml
cache:
  local_size: 1000
  ttl: 86400
```

**预期节省**: 20%

### 3. 使用批量请求

```bash
# 批量请求可减少API调用次数
curl -X POST http://localhost:8024/batch_chat \
  -H "Content-Type: application/json" \
  -d '{
    "requests": [
      {"messages": [{"role": "user", "content": "问题1"}]},
      {"messages": [{"role": "user", "content": "问题2"}]}
    ]
  }'
```

---

## 📚 参考资料

- [OpenAI API文档](https://platform.openai.com/docs/api-reference)
- [Go HTTP客户端](https://golang.org/pkg/net/http/)
- [Redis缓存](https://redis.io/documentation)
- [Prometheus监控](https://prometheus.io/docs/)

---

## 🔒 安全建议

### 1. API密钥管理

```bash
# 使用环境变量或密钥管理工具
export LLM_API_KEY=sk-...

# 或使用Vault
vault kv get -field=api-key secret/llm/openai
```

### 2. 访问控制

```yaml
server:
  # 限制访问IP
  allowed_ips:
    - "10.0.0.0/8"
    - "192.168.0.0/16"

  # API密钥认证
  api_keys:
    - "client-key-1"
    - "client-key-2"
```

### 3. 速率限制

```yaml
server:
  # 每个客户端每分钟请求数
  rate_limit: 100
  rate_limit_window: 60
```

---

**维护者**: Athena平台团队
**更新时间**: 2026-04-20
