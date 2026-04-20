# Athena Gateway 部署指南

> **版本**: 1.0.0  
> **更新日期**: 2026-04-20  
> **状态**: 生产就绪

---

## 📋 目录

- [部署概述](#部署概述)
- [环境要求](#环境要求)
- [快速部署](#快速部署)
- [配置说明](#配置说明)
- [启动和停止](#启动和停止)
- [健康检查](#健康检查)
- [监控和日志](#监控和日志)
- [故障排查](#故障排查)

---

## 部署概述

Athena Gateway是统一网关服务，提供：

```
┌─────────────────────────────────────┐
│  Athena Gateway (8005)              │
│  ├─ 路由管理                        │
│  ├─ 服务发现                        │
│  ├─ Agent通信                        │
│  ├─ API版本管理                      │
│  └─ 安全认证                        │
└─────────────────────────────────────┘
         │
    ┌────┴────┐
    │  所有服务  │
    └─────────┘
```

---

## 环境要求

### 系统要求

- **操作系统**: Linux/macOS/Windows
- **架构**: amd64/arm64
- **内存**: 最低512MB，推荐1GB
- **CPU**: 最低1核，推荐2核

### 软件依赖

**必需**:
- Go 1.19+ (编译时)
- Docker 20.10+ (容器部署)

**可选**:
- PostgreSQL 15+ (持久化存储)
- Redis 7+ (缓存)
- Qdrant 1.7+ (向量检索)
- Neo4j 5.15+ (知识图谱)

---

## 快速部署

### 方式1: 二进制部署

#### 1. 下载Gateway

```bash
# 编译（如果需要）
cd gateway-unified
go build -o bin/gateway ./cmd/gateway

# 或使用预编译二进制
wget https://github.com/athena-workspace/gateway/releases/download/v1.0.0/gateway-linux-amd64
chmod +x gateway-linux-amd64
```

#### 2. 配置Gateway

```bash
# 复制配置文件
cp gateway-config.yaml.example config.yaml

# 编辑配置
vim config.yaml
```

#### 3. 启动Gateway

```bash
# 前台启动（测试）
./bin/gateway

# 后台启动
nohup ./bin/gateway > logs/gateway.log 2>&1 &

# 使用系统服务（推荐）
sudo ./install-service.sh
sudo systemctl start athena-gateway
```

### 方式2: Docker部署

#### 1. 拉取镜像

```bash
docker pull athena/gateway:latest
```

#### 2. 运行容器

```bash
docker run -d \
  --name athena-gateway \
  -p 8005:8005 \
  -v $(pwd)/config.yaml:/app/config.yaml \
  -v $(pwd)/logs:/app/logs \
  athena/gateway:latest
```

#### 3. Docker Compose

```bash
# 使用项目docker-compose
docker-compose up -d gateway

# 查看日志
docker-compose logs -f gateway
```

### 方式3: systemd服务

#### 1. 创建服务文件

```bash
sudo vim /etc/systemd/system/athena-gateway.service
```

**服务文件内容**:

```ini
[Unit]
Description=Athena Gateway
After=network.target

[Service]
Type=simple
User=athena
WorkingDirectory=/opt/athena-gateway
ExecStart=/opt/athena-gateway/bin/gateway
Restart=always
RestartSec=5

Environment=GATEWAY_CONFIG_PATH=/opt/athena-gateway/config.yaml

[Install]
WantedBy=multi-user.target
```

#### 2. 启动服务

```bash
sudo systemctl daemon-reload
sudo systemctl enable athena-gateway
sudo systemctl start athena-gateway
```

---

## 配置说明

### 最小配置

```yaml
server:
  port: 8005
  production: true

logging:
  level: info
  format: json
```

### 完整配置

```yaml
# 服务器配置
server:
  port: 8005
  production: true
  read_timeout: 30
  write_timeout: 30
  idle_timeout: 120

# 日志配置
logging:
  level: info
  format: json
  output: /var/log/athena/gateway.log

# 监控配置
monitoring:
  enabled: true
  port: 9091
  path: /metrics

# WebSocket配置
websocket:
  enabled: true
  path: /ws
  heartbeat_interval: 30
  session_timeout: 600

# TLS配置
tls:
  enabled: true
  cert_file: /etc/ssl/certs/gateway.crt
  key_file: /etc/ssl/private/gateway.key

# 认证配置
auth:
  jwt:
    secret: "${JWT_SECRET}"
    expiration: 24h
  api_key:
    enabled: true
    keys: ["${API_KEY}"]

# 速率限制
rate_limit:
  enabled: true
  requests_per_minute: 100

# CORS配置
cors:
  enabled: true
  allowed_origins:
    - "https://your-domain.com"
```

---

## 启动和停止

### 启动Gateway

```bash
# 1. 检查配置
./bin/gateway -config config.yaml -check

# 2. 启动服务
./bin/gateway -config config.yaml

# 3. 验证启动
curl http://localhost:8005/health
```

### 停止Gateway

```bash
# 发送SIGTERM信号
kill $(cat data/gateway.pid)

# 或使用systemctl
sudo systemctl stop athena-gateway

# Docker容器
docker stop athena-gateway
```

### 重启Gateway

```bash
# 优雅重启（推荐）
kill -HUP $(cat data/gateway.pid)

# systemctl
sudo systemctl restart athena-gateway

# Docker
docker restart athena-gateway
```

---

## 健康检查

### 基本检查

```bash
# 健康状态
curl http://localhost:8005/health

# 就绪状态
curl http://localhost:8005/ready

# 存活状态
curl http://localhost:8005/live
```

### 预期响应

**健康检查成功**:
```json
{
  "success": true,
  "data": {
    "status": "UP",
    "timestamp": "2026-04-20T13:45:00Z",
    "instances": 5,
    "routes": 6
  }
}
```

**健康检查失败**:
```json
{
  "success": false,
  "error": "Service unhealthy",
  "data": {
    "status": "DOWN",
    "issues": ["Database connection failed"]
  }
}
```

---

## 监控和日志

### Prometheus监控

Gateway默认暴露Prometheus指标：

```
http://localhost:9091/metrics
```

**关键指标**:
- `gateway_requests_total` - 总请求数
- `gateway_request_duration_seconds` - 请求延迟
- `gateway_services_total` - 注册服务数
- `gateway_active_sessions` - 活跃会话数

### Grafana仪表板

导入仪表板：
```
docs/monitoring/gateway-dashboard.json
```

### 日志位置

```
logs/
├── gateway.log       # 主日志
├── access.log        # 访问日志
└── error.log         # 错误日志
```

### 日志级别

| 级别 | 说明 | 使用场景 |
|------|------|---------|
| DEBUG | 详细调试信息 | 开发环境 |
| INFO | 一般信息 | 生产环境 |
| WARN | 警告信息 | 生产环境 |
| ERROR | 错误信息 | 所有环境 |

---

## 故障排查

### 常见问题

#### Q1: Gateway无法启动

**症状**: 执行./bin/gateway无响应

**排查步骤**:
```bash
# 1. 检查端口占用
lsof -i :8005

# 2. 检查配置文件语法
./bin/gateway -config config.yaml -check

# 3. 查看详细日志
tail -f logs/gateway.log
```

#### Q2: 路由不工作

**症状**: 请求返回404

**排查步骤**:
```bash
# 1. 检查路由配置
curl http://localhost:8005/api/routes

# 2. 检查服务状态
curl http://localhost:8005/api/services/instances

# 3. 查看Gateway日志
tail -50 logs/gateway.log
```

#### Q3: 服务发现失败

**症状**: 服务未自动注册

**排查步骤**:
```bash
# 1. 检查配置文件
cat config/service_discovery.json

# 2. 检查服务健康状态
curl http://localhost:8005/api/services/instances

# 3. 手动注册服务
curl -X POST http://localhost:8005/api/services/instances \
  -H "Content-Type: application/json" \
  -d '{"service_name":"test","host":"127.0.0.1","port":8000}'
```

#### Q4: WebSocket连接失败

**症状**: Agent无法连接Gateway

**排查步骤**:
```bash
# 1. 检查WebSocket端点
curl -i -N \
  -H "Connection: Upgrade" \
  -H "Upgrade: websocket" \
  http://localhost:8005/ws

# 2. 检查WebSocket配置
curl http://localhost:8005/api/websocket/stats

# 3. 查看会话状态
curl http://localhost:8005/api/websocket/sessions
```

### 性能调优

#### 内存优化

```yaml
# 限制内存使用
server:
  max_connections: 1000

websocket:
  session_timeout: 300  # 减少会话超时
```

#### 并发优化

```yaml
# 增加并发处理
server:
  read_timeout: 10
  write_timeout: 10
```

---

## 生产环境检查清单

部署前检查：

- [ ] 配置文件已更新
- [ ] TLS证书已配置
- [ ] JWT密钥已更改
- [ ] 日志目录已创建
- [ ] 监控已配置
- [ ] 健康检查端点可访问
- [ ] 服务发现配置正确
- [ ] 速率限制已启用
- [ ] 备份策略已制定
- [ ] 文档已更新

---

## 升级指南

### 滚动升级

```bash
# 1. 备份当前版本
cp bin/gateway bin/gateway.backup

# 2. 下载新版本
wget https://github.com/athena-workspace/gateway/releases/download/v1.0.1/gateway-linux-amd64
mv gateway-linux-amd64 bin/gateway

# 3. 测试新版本
./bin/gateway -version
./bin/gateway -config config.yaml -check

# 4. 优雅重启
kill -HUP $(cat data/gateway.pid)

# 5. 验证升级
curl http://localhost:8005/health
```

### 回滚

```bash
# 如果升级失败，回滚到备份版本
cp bin/gateway.backup bin/gateway
kill -HUP $(cat data/gateway.pid)
```

---

## 相关文档

- [安全配置指南](../security/GATEWAY_SECURITY_GUIDE.md)
- [API文档](../api/GATEWAY_API.md)
- [端口分配规范](../PORT_ALLOCATION.md)
- [实施计划](../plans/GATEWAY_OPTIMIZATION_IMPLEMENTATION_PLAN.md)

---

**维护者**: Athena Platform Team  
**最后更新**: 2026-04-20
