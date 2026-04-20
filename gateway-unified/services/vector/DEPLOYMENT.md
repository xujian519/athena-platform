# 向量检索服务部署指南

## 📋 概述

本文档提供向量检索服务的生产环境部署指南。

---

## 🚀 部署前准备

### 1. 环境要求

**系统要求**：
- macOS 10.15+ 或 Linux (Ubuntu 20.04+)
- Go 1.21+
- Qdrant 1.7+
- Redis 6.0+（可选，用于分布式缓存）

**依赖服务**：
```bash
# Qdrant向量数据库
docker run -d -p 16333:6333 qdrant/qdrant:v1.7.0

# Redis缓存（可选）
docker run -d -p 16379:6379 redis:7-alpine
```

### 2. 配置检查

**环境变量**：
```bash
# Qdrant配置
export QDRANT_HOST=localhost
export QDRANT_PORT=16333

# Redis配置（可选）
export REDIS_HOST=localhost
export REDIS_PORT=16379
export REDIS_DB=0
```

---

## 🔧 编译和安装

### 1. 编译Go二进制

```bash
cd gateway-unified/services/vector

# 整理依赖
go mod tidy

# 编译为可执行文件
go build -o vector-service

# 或编译为静态链接二进制（推荐用于生产）
CGO_ENABLED=0 go build -a -ldflags '-extldflags "-static"' -o vector-service
```

### 2. 验证编译

```bash
# 检查二进制文件
./vector-service --help

# 或运行测试
go test -v ./...
```

---

## 📦 部署方式

### 方式1：独立服务部署

#### 1. 创建systemd服务（Linux）

```bash
# 创建服务文件
sudo vim /etc/systemd/system/athena-vector.service
```

**服务配置**：
```ini
[Unit]
Description=Athena Vector Search Service
After=network.target

[Service]
Type=simple
User=athena
Group=athena
WorkingDirectory=/opt/athena/vector-service
ExecStart=/opt/athena/vector-service/vector-service
Restart=always
RestartSec=5

# 环境变量
Environment="QDRANT_HOST=localhost"
Environment="QDRANT_PORT=16333"
Environment="REDIS_HOST=localhost"
Environment="REDIS_PORT=16379"

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
sudo systemctl enable athena-vector

# 启动服务
sudo systemctl start athena-vector

# 查看状态
sudo systemctl status athena-vector

# 查看日志
sudo journalctl -u athena-vector -f
```

### 方式2：Docker部署

#### 1. 创建Dockerfile

```dockerfile
FROM golang:1.21-alpine AS builder

WORKDIR /app
COPY go.mod go.sum ./
RUN go mod download

COPY . .
RUN CGO_ENABLED=0 go build -o vector-service

FROM alpine:latest
RUN apk --no-cache add ca-certificates
WORKDIR /root/

COPY --from=builder /app/vector-service .
COPY config.yaml .

EXPOSE 8023

CMD ["./vector-service"]
```

#### 2. 构建和运行

```bash
# 构建镜像
docker build -t athena-vector:latest .

# 运行容器
docker run -d \
  --name athena-vector \
  -p 8023:8023 \
  -e QDRANT_HOST=qdrant \
  -e QDRANT_PORT=6333 \
  -e REDIS_HOST=redis \
  -e REDIS_PORT=6379 \
  athena-vector:latest

# 查看日志
docker logs -f athena-vector
```

### 方式3：Kubernetes部署

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: athena-vector
spec:
  replicas: 3
  selector:
    matchLabels:
      app: athena-vector
  template:
    metadata:
      labels:
        app: athena-vector
    spec:
      containers:
      - name: vector-service
        image: athena-vector:latest
        ports:
        - containerPort: 8023
        env:
        - name: QDRANT_HOST
          value: "qdrant"
        - name: QDRANT_PORT
          value: "6333"
        resources:
          requests:
            memory: "128Mi"
            cpu: "100m"
          limits:
            memory: "512Mi"
            cpu: "500m"
---
apiVersion: v1
kind: Service
metadata:
  name: athena-vector
spec:
  selector:
    app: athena-vector
  ports:
  - port: 8023
    targetPort: 8023
  type: ClusterIP
```

---

## 🔍 健康检查

### 1. 检查服务状态

```bash
# 检查进程
ps aux | grep vector-service

# 检查端口
lsof -i :8023

# 检查连接
curl http://localhost:8023/health
```

### 2. 性能测试

```bash
# 使用ab测试
ab -n 1000 -c 10 http://localhost:8023/search

# 使用wrk测试
wrk -t4 -c100 -d30s http://localhost:8023/search
```

---

## 📊 监控和日志

### 1. Prometheus指标

```bash
# 访问指标端点
curl http://localhost:8023/metrics
```

**关键指标**：
- `vector_search_duration_milliseconds` - 搜索延迟
- `vector_cache_hits_total` - 缓存命中数
- `vector_cache_misses_total` - 缓存未命中数

### 2. Grafana仪表板

**推荐面板**：
1. 搜索QPS和延迟
2. 缓存命中率
3. 并发连接数
4. 错误率

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

### 问题1：服务启动失败

**症状**：
```
Error: bind: address already in use
```

**解决**：
```bash
# 检查端口占用
lsof -i :8023

# 杀死占用进程
kill -9 <PID>

# 或更换端口
export VECTOR_SERVICE_PORT=8024
```

### 问题2：Qdrant连接失败

**症状**：
```
Error: connection refused to Qdrant
```

**解决**：
```bash
# 检查Qdrant状态
docker ps | grep qdrant

# 检查Qdrant日志
docker logs -f qdrant

# 检查网络连接
curl http://localhost:16333/health
```

### 问题3：缓存未命中

**症状**：
- 缓存命中率< 50%

**解决**：
```bash
# 检查Redis状态
docker ps | grep redis

# 增加缓存容量
export CACHE_LOCAL_SIZE=1000

# 延长TTL
export CACHE_TTL=3600
```

---

## 📝 配置参考

### 完整配置文件

```yaml
# config.yaml
server:
  port: 8023
  host: "0.0.0.0"
  read_timeout: 30
  write_timeout: 30

qdrant:
  host: "localhost"
  port: 16333
  timeout: 30
  max_idle_conns: 100
  max_conns_per_host: 10

cache:
  redis_addr: "localhost:16379"
  redis_db: 0
  local_size: 1000
  ttl: 300  # 5分钟
  enabled: true

monitoring:
  enabled: true
  metrics_path: "/metrics"
  health_path: "/health"
```

---

## 🎯 性能调优

### 1. 连接池优化

```yaml
qdrant:
  max_idle_conns: 200      # 增加空闲连接
  max_conns_per_host: 20   # 增加每主机连接
  idle_conn_timeout: 90    # 空闲连接超时
```

### 2. 缓存优化

```yaml
cache:
  local_size: 2000        # 增加本地缓存
  ttl: 1800              # 延长TTL到30分钟
```

### 3. 并发优化

```yaml
server:
  max_concurrent_requests: 100  # 最大并发请求
```

---

## 🔄 升级和回滚

### 1. 滚动升级

```bash
# 1. 编译新版本
go build -o vector-service-new

# 2. 备份当前版本
cp vector-service vector-service.old

# 3. 替换二进制
mv vector-service-new vector-service

# 4. 重启服务
sudo systemctl restart athena-vector

# 5. 验证
curl http://localhost:8023/health
```

### 2. 回滚

```bash
# 如果出现问题，快速回滚
mv vector-service.old vector-service
sudo systemctl restart athena-vector
```

---

## 📚 参考资料

- [Qdrant文档](https://qdrant.tech/documentation/)
- [Go HTTP服务器](https://golang.org/pkg/net/http/)
- [Redis缓存](https://redis.io/documentation)
- [Prometheus监控](https://prometheus.io/docs/)

---

**维护者**: Athena平台团队
**更新时间**: 2026-04-20
