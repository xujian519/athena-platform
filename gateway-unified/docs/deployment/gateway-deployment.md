# Athena Gateway 部署文档

**版本**: v1.0
**最后更新**: 2026-02-24
**部署模式**: 本地运行简化部署

---

## 目录

- [本地运行部署](#本地运行部署)
- [配置说明](#配置说明)
- [启动与停止](#启动与停止)
- [健康检查](#健康检查)
- [故障排查](#故障排查)

---

## 本地运行部署

### 方式一：直接运行二进制文件（推荐）

#### 1. 构建网关

```bash
cd /Users/xujian/Athena工作平台/gateway-unified

# 构建
go build -o bin/gateway cmd/gateway/main.go
```

#### 2. 创建配置文件

创建 `configs/config.yaml`：

```yaml
# 服务器配置
server:
  port: 8085
  host: "127.0.0.1"  # 本地运行只监听本地
  read_timeout: 30s
  write_timeout: 30s

# 连接池配置
pool:
  max_idle_conns: 100
  max_idle_conns_per_host: 25
  idle_conn_timeout: 90s
  request_timeout: 60s
  enable_health_check: true

# 缓存配置
cache:
  l1_max_size: 5000
  l1_ttl: 5m
  l2_enabled: false
  cleanup_interval: 1m

# 并发配置
concurrent:
  min_workers: 2
  max_workers: 8
  max_tasks: 500
  idle_timeout: 30s

# 日志配置
logging:
  level: info
  format: text
  output: stdout

# 服务发现配置
discovery:
  enabled: true
  auto_register: false
```

#### 3. 启动网关

```bash
# 前台运行（开发调试）
./bin/gateway

# 后台运行
./bin/gateway &
```

#### 4. 停止网关

```bash
# 查找进程
ps aux | grep gateway

# 停止进程
pkill gateway

# 或使用 Ctrl+C (前台运行时)
```

---

### 方式二：Docker 快速部署

#### 1. 创建 Dockerfile

```dockerfile
FROM golang:1.21-alpine AS builder

WORKDIR /app
COPY go.mod go.sum ./
RUN go mod download

COPY . .
RUN CGO_ENABLED=0 go build -o gateway cmd/gateway/main.go

FROM alpine:latest
WORKDIR /app
COPY --from=builder /app/gateway /usr/local/bin/

EXPOSE 8085
CMD ["gateway"]
```

#### 2. 构建镜像

```bash
cd /Users/xujian/Athena工作平台/gateway-unified

docker build -t athena-gateway:local .
```

#### 3. 运行容器

```bash
docker run -d \
  --name athena-gateway \
  -p 8085:8085 \
  -v $(pwd)/configs:/app/configs \
  athena-gateway:local
```

#### 4. 停止容器

```bash
docker stop athena-gateway
docker rm athena-gateway
```

---

## 配置说明

### 最小配置示例

```yaml
server:
  port: 8085
  host: "127.0.0.1"

logging:
  level: info
```

### 环境变量配置

| 变量名 | 说明 | 默认值 |
|--------|------|--------|
| `GATEWAY_PORT` | 监听端口 | 8085 |
| `GATEWAY_HOST` | 监听地址 | 127.0.0.1 |
| `LOG_LEVEL` | 日志级别 | info |
| `GIN_MODE` | 运行模式 | debug |

### 使用环境变量启动

```bash
# 设置端口
export GATEWAY_PORT=9000

# 设置日志级别
export LOG_LEVEL=debug

# 启动网关
./bin/gateway
```

### 快速启动

```bash
# 1. 构建镜像
cd /Users/xujian/Athena工作平台/gateway-unified
docker build -t athena-gateway:latest .

# 2. 运行容器
docker run -d \
  --name athena-gateway \
  -p 8080:8080 \
  -v $(pwd)/configs:/app/configs \
  -e LOG_LEVEL=info \
  athena-gateway:latest
```

### Docker Compose 部署

创建 `docker-compose.yml`:

```yaml
version: '3.8'

services:
  gateway:
    image: athena-gateway:latest
    container_name: athena-gateway
    ports:
      - "8080:8080"
    environment:
      - LOG_LEVEL=info
      - GIN_MODE=release
      - MAX_IDLE_CONNS=200
      - MAX_IDLE_CONNS_PER_HOST=50
    volumes:
      - ./configs:/app/configs
      - ./logs:/app/logs
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8080/health"]
      interval: 30s
      timeout: 10s
      retries: 3
    networks:
      - athena-network

  # 可选：Redis (用于L2缓存)
  redis:
    image: redis:7-alpine
    container_name: athena-redis
    ports:
      - "6379:6379"
    volumes:
      - redis-data:/data
    restart: unless-stopped
    networks:
      - athena-network

  # 可选：Prometheus (监控)
  prometheus:
    image: prom/prometheus:latest
    container_name: athena-prometheus
    ports:
      - "9090:9090"
    volumes:
      - ./monitoring/prometheus/prometheus.yml:/etc/prometheus/prometheus.yml
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
      - '--web.console.libraries=/etc/prometheus/console_libraries'
      - '--web.console.templates=/etc/prometheus/consoles'
      - '--storage.tsdb.retention.time=200h'
      - '--web.enable-lifecycle'
    restart: unless-stopped
    networks:
      - athena-network

volumes:
  redis-data:

networks:
  athena-network:
    driver: bridge
```

启动服务：

```bash
docker-compose up -d
```

---

## 启动与停止

### 一键启动脚本

创建 `scripts/start.sh`：

```bash
#!/bin/bash
set -e

cd "$(dirname "$0")/.."
GATEWAY_BIN="./gateway"
CONFIG_DIR="./configs"

echo "🚀 启动 Athena Gateway..."

# 检查二进制文件
if [ ! -f "$GATEWAY_BIN" ]; then
    echo "❌ 二进制文件不存在，请先执行: go build -o bin/gateway cmd/gateway/main.go"
    exit 1
fi

# 检查配置文件
if [ ! -f "$CONFIG_DIR/config.yaml" ]; then
    echo "⚠️  配置文件不存在，使用默认配置"
    mkdir -p "$CONFIG_DIR"
    cat > "$CONFIG_DIR/config.yaml" <<EOF
server:
  port: 8085
  host: "127.0.0.1"
logging:
  level: info
EOF
fi

# 启动网关
echo "📡 监听地址: http://127.0.0.1:8085"
echo "📚 API文档: http://127.0.0.1:8085/swagger"
echo "💚 健康检查: http://127.0.0.1:8085/health"

exec $GATEWAY_BIN
```

### 停止脚本

创建 `scripts/stop.sh`：

```bash
#!/bin/bash

echo "🛑 停止 Athena Gateway..."

# 查找并停止进程
GATEWAY_PID=$(pgrep -f "gateway|athena-gateway" || true)

if [ -n "$GATEWAY_PID" ]; then
    echo "找到进程 PID: $GATEWAY_PID"
    kill $GATEWAY_PID
    sleep 1

    # 如果进程仍在运行，强制停止
    if pgrep -f "gateway|athena-gateway" > /dev/null; then
        echo "强制停止进程..."
        pkill -9 -f "gateway|athena-gateway"
    fi

    echo "✅ Gateway 已停止"
else
    echo "ℹ️  Gateway 未运行"
fi
```

### 重启脚本

创建 `scripts/restart.sh`：

```bash
#!/bin/bash

echo "🔄 重启 Athena Gateway..."

# 停止
./scripts/stop.sh

# 等待进程完全退出
sleep 1

# 启动
./scripts/start.sh
```

---

## 健康检查

### 健康检查脚本

创建 `scripts/health-check.sh`：

```bash
#!/bin/bash

GATEWAY_URL="http://127.0.0.1:8085"

echo "🔍 健康检查..."

# 基本健康检查
echo -n "  基本健康: "
if curl -sf "$GATEWAY_URL/health" > /dev/null; then
    echo "✅ 正常"
else
    echo "❌ 异常"
    exit 1
fi

# 就绪检查
echo -n "  就绪状态: "
if curl -sf "$GATEWAY_URL/ready" > /dev/null; then
    echo "✅ 就绪"
else
    echo "⚠️  未就绪"
fi

# 存活检查
echo -n "  存活状态: "
if curl -sf "$GATEWAY_URL/live" > /dev/null; then
    echo "✅ 存活"
else
    echo "❌ 不存活"
    exit 1
fi

# 指标检查
echo -n "  指标端点: "
if curl -sf "$GATEWAY_URL/metrics" > /dev/null; then
    echo "✅ 可用"
else
    echo "⚠️  不可用"
fi

echo "✅ 所有检查通过"
```

---

## 监控与调试

### 本地监控

#### 1. 查看日志

```bash
# 实时日志
tail -f logs/gateway.log
```

#### 2. 查看指标

```bash
# 获取 Prometheus 指标
curl http://127.0.0.1:8085/metrics
```

#### 3. 性能分析

```bash
# 启用 pprof（需要在代码中集成）
curl http://127.0.0.1:8085/debug/pprof/
```

---

## 故障排查

### 常见问题

#### 1. 端口被占用

**症状**: 启动时提示 "bind: address already in use"

**解决方案**:
```bash
# 查找占用端口的进程
lsof -i :8085

# 或
netstat -an | grep 8085

# 更改配置文件中的端口
# 或停止占用端口的进程
```

#### 2. 配置文件错误

**症状**: 启动失败，提示配置解析错误

**解决方案**:
```bash
# 验证配置文件格式
cat configs/config.yaml

# 使用默认配置启动
rm configs/config.yaml
./bin/gateway  # 会使用内置默认配置
```

#### 3. 服务注册失败

**症状**: 后端服务无法注册

**解决方案**:
```bash
# 检查网关是否启动
curl http://127.0.0.1:8085/health

# 检查服务注册API
curl -X POST http://127.0.0.1:8085/api/v1/services/batch \
  -H "Content-Type: application/json" \
  -d '{
    "services": [{
      "name": "test-service",
      "host": "localhost",
      "port": 8081
    }]
  }'
```

#### 4. 内存占用过高

**症状**: 内存使用持续增长

**解决方案**:
```bash
# 减少缓存大小
# 修改 configs/config.yaml
cache:
  l1_max_size: 1000  # 从 5000 减少到 1000

# 重启网关
./scripts/restart.sh
```

---

## 附录

### 快速命令

```bash
# 构建
go build -o bin/gateway cmd/gateway/main.go

# 启动
./scripts/start.sh

# 停止
./scripts/stop.sh

# 重启
./scripts/restart.sh

# 健康检查
./scripts/health-check.sh
```

### 目录结构

```
gateway-unified/
├── bin/
│   └── gateway           # 编译后的二进制文件
├── cmd/
│   └── gateway/
│       └── main.go       # 网关入口
├── configs/
│   └── config.yaml      # 配置文件
├── scripts/
│   ├── start.sh          # 启动脚本
│   ├── stop.sh           # 停止脚本
│   ├── restart.sh        # 重启脚本
│   └── health-check.sh   # 健康检查脚本
├── logs/
│   └── gateway.log       # 日志文件
└── docs/
    ├── api/
    │   └── gateway-api.md     # API文档
    ├── architecture/
    │   └── gateway-architecture.md  # 架构文档
    └── deployment/
        └── gateway-deployment.md     # 部署文档
```

### 开发调试

#### 启用调试模式

```bash
# 设置环境变量
export GIN_MODE=debug
export LOG_LEVEL=debug

# 启动网关
./bin/gateway
```

#### 查看详细日志

```bash
# 实时查看日志
tail -f logs/gateway.log

# 或查看最近的错误
grep ERROR logs/gateway.log | tail -20
```

---

**文档版本**: v1.0 (简化版)
**适用场景**: 本地运行部署
**维护者**: Athena 团队
**最后更新**: 2026-02-24

### 命名空间

创建命名空间：

```bash
kubectl create namespace athena-gateway
```

### ConfigMap

创建 `configmap.yaml`:

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: gateway-config
  namespace: athena-gateway
data:
  config.yaml: |
    server:
      port: 8080
      read_timeout: 30s
      write_timeout: 30s

    pool:
      max_idle_conns: 200
      max_idle_conns_per_host: 50
      idle_conn_timeout: 90s
      request_timeout: 60s

    cache:
      l1_max_size: 10000
      l1_ttl: 5m
      cleanup_interval: 1m

    concurrent:
      min_workers: 4
      max_workers: 16
      max_tasks: 1000

    logging:
      level: info
      format: json
```

应用 ConfigMap：

```bash
kubectl apply -f configmap.yaml
```

### Deployment

创建 `deployment.yaml`:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: gateway
  namespace: athena-gateway
  labels:
    app: gateway
    version: v1.0
spec:
  replicas: 3
  selector:
    matchLabels:
      app: gateway
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 1
      maxUnavailable: 0
  template:
    metadata:
      labels:
        app: gateway
        version: v1.0
    spec:
      containers:
      - name: gateway
        image: athena-gateway:v1.0
        imagePullPolicy: Always
        ports:
        - containerPort: 8080
          name: http
          protocol: TCP
        env:
        - name: LOG_LEVEL
          value: "info"
        - name: GIN_MODE
          value: "release"
        - name: MAX_IDLE_CONNS
          value: "200"
        - name: MAX_IDLE_CONNS_PER_HOST
          value: "50"
        volumeMounts:
        - name: config
          mountPath: /app/configs
        - name: logs
          mountPath: /app/logs
        livenessProbe:
          httpGet:
            path: /health
            port: 8080
          initialDelaySeconds: 10
          periodSeconds: 10
          timeoutSeconds: 5
          successThreshold: 1
          failureThreshold: 3
        readinessProbe:
          httpGet:
            path: /ready
            port: 8080
          initialDelaySeconds: 5
          periodSeconds: 5
          timeoutSeconds: 3
          successThreshold: 1
          failureThreshold: 3
        resources:
          requests:
            memory: "128Mi"
            cpu: "100m"
          limits:
            memory: "512Mi"
            cpu: "500m"
      volumes:
      - name: config
        configMap:
          name: gateway-config
      - name: logs
        emptyDir: {}
---
apiVersion: v1
kind: Service
metadata:
  name: gateway
  namespace: athena-gateway
  labels:
    app: gateway
spec:
  type: LoadBalancer
  selector:
    app: gateway
  ports:
  - port: 80
    targetPort: 8080
    name: http
    protocol: TCP
  sessionAffinity: ClientIP
  sessionAffinityConfig:
    clientIP:
      timeoutSeconds: 10800
```

部署：

```bash
kubectl apply -f deployment.yaml
```

### HorizontalPodAutoscaler

创建 `hpa.yaml`:

```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: gateway-hpa
  namespace: athena-gateway
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: gateway
  minReplicas: 3
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
  behavior:
    scaleDown:
      stabilizationWindowSeconds: 300
      policies:
      - type: Percent
        value: 50
        periodSeconds: 60
    scaleUp:
      stabilizationWindowSeconds: 60
      policies:
      - type: Percent
        value: 100
        periodSeconds: 30
```

部署：

```bash
kubectl apply -f hpa.yaml
```

### Ingress

创建 `ingress.yaml`:

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: gateway-ingress
  namespace: athena-gateway
  annotations:
    kubernetes.io/ingress.class: "nginx"
    nginx.ingress.kubernetes.io/ssl-redirect: "true"
    nginx.ingress.kubernetes.io/proxy-body-size: "100m"
    nginx.ingress.kubernetes.io/proxy-connect-timeout: "60"
    nginx.ingress.kubernetes.io/proxy-send-timeout: "60"
    cert-manager.io/cluster-issuer: "letsencrypt-prod"
spec:
  tls:
  - hosts:
    - gateway.example.com
    secretName: gateway-tls
  rules:
  - host: gateway.example.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: gateway
            port:
              number: 80
```

部署：

```bash
kubectl apply -f ingress.yaml
```

---

## 配置说明

### 环境变量

| 变量名 | 说明 | 默认值 |
|--------|------|--------|
| `LOG_LEVEL` | 日志级别 | `info` |
| `GIN_MODE` | Gin 模式 | `release` |
| `MAX_IDLE_CONNS` | 最大空闲连接数 | `200` |
| `MAX_IDLE_CONNS_PER_HOST` | 每主机最大空闲连接 | `50` |
| `IDLE_CONN_TIMEOUT` | 空闲连接超时 | `90s` |
| `REQUEST_TIMEOUT` | 请求超时 | `60s` |
| `L1_MAX_SIZE` | L1缓存大小 | `10000` |
| `L1_TTL` | L1缓存TTL | `5m` |
| `MIN_WORKERS` | 最小worker数 | `4` |
| `MAX_WORKERS` | 最大worker数 | `16` |

### 配置文件

主配置文件: `configs/config.yaml`

```yaml
server:
  port: 8080
  host: "0.0.0.0"
  read_timeout: 30s
  write_timeout: 30s

# 连接池配置
pool:
  max_idle_conns: 200
  max_idle_conns_per_host: 50
  max_conns_per_host: 0
  idle_conn_timeout: 90s
  dial_timeout: 10s
  request_timeout: 60s

# 缓存配置
cache:
  l1_max_size: 10000
  l1_ttl: 5m
  l2_enabled: false
  cleanup_interval: 1m

# 并发配置
concurrent:
  min_workers: 4
  max_workers: 16
  max_tasks: 1000
  idle_timeout: 30s

# 日志配置
logging:
  level: info
  format: json
  output: stdout

# 监控配置
monitoring:
  prometheus:
    enabled: true
    port: 9090
    path: /metrics
  tracing:
    enabled: true
    exporter: otlp
    endpoint: http://jaeger:14268/api/traces
```

---

## 监控告警

### Prometheus 监控

已暴露的指标：

| 指标名 | 类型 | 说明 |
|--------|------|------|
| `http_requests_total` | Counter | HTTP请求总数 |
| `http_request_duration_seconds` | Histogram | 请求延迟 |
| `http_requests_in_flight` | Gauge | 处理中的请求数 |
| `pool_active_connections` | Gauge | 活跃连接数 |
| `cache_hits_total` | Counter | 缓存命中数 |
| `cache_misses_total` Counter | 缓存未命中数 |

### Grafana 仪表板

导入仪表板：`monitoring/grafana/dashboards/gateway-dashboard.json`

关键面板：
- 请求速率
- P50/P95/P99 延迟
- 错误率
- 连接池使用率
- 缓存命中率

### 告警规则

Prometheus 告警规则：`monitoring/prometheus/alerts.yml`

```yaml
groups:
- name: gateway
  interval: 30s
  rules:
  # 高错误率告警
  - alert: GatewayHighErrorRate
    expr: |
      (sum(rate(http_requests_total{status=~"5.."}[5m]))
      /
      (sum(rate(http_requests_total[5m]))) > 0.01
    for: 10m
    labels:
      severity: critical
    annotations:
      summary: "网关错误率过高"
      description: "5分钟内错误率超过1%"

  # 高延迟告警
  - alert: GatewayHighLatency
    expr: |
      histogram_quantile(0.95,
      rate(http_request_duration_seconds_bucket[5m])) > 0.1
    for: 10m
    labels:
      severity: warning
    annotations:
      summary: "网关延迟过高"
      description: "P95延迟超过100ms"

  # 连接池耗尽告警
  - alert: GatewayPoolExhausted
    expr: |
      pool_active_connections / pool_max_connections > 0.9
    for: 5m
    labels:
      severity: critical
    annotations:
      summary: "连接池接近耗尽"
      description: "连接池使用率超过90%"
```

---

## 故障排查

### 常见问题

#### 1. 容器启动失败

**症状**: 容器反复重启

**排查**:
```bash
# 查看容器日志
docker logs athena-gateway

# 查看容器状态
docker inspect athena-gateway
```

**解决方案**:
- 检查配置文件格式
- 确认端口未被占用
- 检查资源限制

#### 2. 健康检查失败

**症状**: `/health` 返回非 200

**排查**:
```bash
curl http://localhost:8080/health
curl http://localhost:8080/ready
```

**解决方案**:
- 检查后端服务连接
- 确认数据库连接正常
- 检查依赖服务状态

#### 3. 内存泄漏

**症状**: 内存持续增长

**排查**:
```bash
# 查看内存使用
docker stats athena-gateway

# 进入容器分析
docker exec -it athena-gateway pprof heap
```

**解决方案**:
- 重启服务
- 调整缓存大小
- 优化 goroutine 数量

#### 4. 连接超时

**症状**: 请求经常超时

**排查**:
```bash
# 查看连接池状态
curl http://localhost:8080/metrics | grep pool
```

**解决方案**:
- 增加连接池大小
- 调整超时时间
- 检查后端服务性能

---

## 附录

### 健康检查脚本

```bash
#!/bin/bash
# health-check.sh

GATEWAY_URL="http://localhost:8080"

# 基本健康检查
curl -f ${GATEWAY_URL}/health || exit 1

# 就绪检查
curl -f ${GATEWAY_URL}/ready || exit 1

echo "Gateway is healthy"
```

### 部署脚本

```bash
#!/bin/bash
# deploy.sh

set -e

IMAGE="athena-gateway:v1.0"
NAMESPACE="athena-gateway"

# 构建镜像
echo "Building Docker image..."
docker build -t $IMAGE .

# 推送镜像 (如果使用私有仓库)
# docker push $IMAGE

# 部署到 Kubernetes
echo "Deploying to Kubernetes..."
kubectl apply -f configmap.yaml
kubectl apply -f deployment.yaml
kubectl apply -f service.yaml
kubectl apply -f hpa.yaml

echo "Deployment completed!"
```

### 回滚脚本

```bash
#!/bin/bash
# rollback.sh

set -e

NAMESPACE="athena-gateway"
DEPLOYMENT_NAME="gateway"

echo "Rolling back deployment..."
kubectl rollout undo deployment/$DEPLOYMENT_NAME -n $NAMESPACE

echo "Rollback completed!"
```

---

**文档版本**: v1.0
**维护者**: Athena 团队
**最后更新**: 2026-02-24
