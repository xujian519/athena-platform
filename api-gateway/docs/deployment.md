# Athena API Gateway 部署指南

本文档详细说明如何在不同环境中部署Athena API Gateway。

## 📋 目录

1. [环境要求](#环境要求)
2. [快速开始](#快速开始)
3. [开发环境部署](#开发环境部署)
4. [生产环境部署](#生产环境部署)
5. [Docker部署](#docker部署)
6. [Kubernetes部署](#kubernetes部署)
7. [监控和维护](#监控和维护)
8. [故障排除](#故障排除)

---

## 环境要求

### 系统要求
- **操作系统**: Linux (Ubuntu 18.04+, CentOS 7+) / macOS 10.15+ / Windows 10+
- **架构**: x86_64, ARM64
- **内存**: 最低512MB，推荐2GB+
- **磁盘**: 最低100MB可用空间
- **网络**: 能够访问外部网络（用于上游服务调用）

### 运行时依赖
- **Go**: 1.21+ (仅源码部署)
- **Docker**: 20.10+ (Docker部署)
- **Kubernetes**: 1.20+ (K8s部署)

### 可选依赖
- **PostgreSQL**: 12+ (用于数据持久化)
- **Redis**: 6.0+ (用于缓存和会话)
- **Prometheus**: 2.30+ (用于监控)
- **Grafana**: 8.0+ (用于可视化)

---

## 快速开始

### 使用Makefile（推荐）

```bash
# 克隆项目
git clone <repository-url>
cd api-gateway

# 安装依赖
make deps

# 运行开发环境
make run

# 或者使用配置文件
go run cmd/server/main.go --config configs/config.yaml
```

### 直接运行

```bash
# 下载依赖
go mod download

# 运行服务
go run cmd/server/main.go

# 使用自定义配置
go run cmd/server/main.go --config /path/to/config.yaml
```

### Docker快速启动

```bash
# 构建镜像
make docker-build

# 运行容器
make docker-run
```

---

## 开发环境部署

### 1. 准备配置

```bash
# 复制开发配置模板
cp configs/config.dev.yaml configs/config.yaml

# 编辑配置文件
vim configs/config.yaml
```

### 2. 启动服务

```bash
# 开发模式启动
make run

# 或者
go run cmd/server/main.go --config configs/config.yaml
```

### 3. 验证部署

```bash
# 检查服务状态
curl http://localhost:8080/health

# 预期响应
{
  "success": true,
  "code": 200,
  "message": "操作成功",
  "data": {
    "status": "healthy",
    "timestamp": 1672531200,
    "uptime": "2m15s"
  },
  "timestamp": 1672531200
}
```

### 4. 开发工具

```bash
# 热重载开发
make dev

# 运行测试
make test

# 代码检查
make lint

# 格式化代码
make fmt
```

---

## 生产环境部署

### 1. 系统准备

```bash
# 创建应用用户
sudo useradd -r -s /bin/false athena

# 创建目录结构
sudo mkdir -p /opt/athena-gateway/{bin,configs,logs}
sudo mkdir -p /var/log/athena-gateway

# 设置权限
sudo chown -R athena:athena /opt/athena-gateway
sudo chown -R athena:athena /var/log/athena-gateway
```

### 2. 构建应用

```bash
# 克隆代码
git clone <repository-url> /opt/athena-gateway/src
cd /opt/athena-gateway/src

# 构建生产版本
make build-linux

# 复制到应用目录
sudo cp dist/athena-gateway-linux /opt/athena-gateway/bin/athena-gateway
sudo cp -r configs /opt/athena-gateway/
```

### 3. 配置环境变量

```bash
# 创建环境文件
sudo tee /opt/athena-gateway/.env > /dev/null <<EOF
ATHENA_GATEWAY_ENV=production
JWT_SECRET=your-super-secret-jwt-key-change-in-production
DB_HOST=localhost
DB_PORT=5432
DB_USER=athena
DB_PASSWORD=your-secure-password
DB_NAME=athena_gateway
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=your-redis-password
EOF

# 设置权限
sudo chown athena:athena /opt/athena-gateway/.env
sudo chmod 600 /opt/athena-gateway/.env
```

### 4. 创建Systemd服务

```bash
# 创建服务文件
sudo tee /etc/systemd/system/athena-gateway.service > /dev/null <<EOF
[Unit]
Description=Athena API Gateway
After=network.target

[Service]
Type=simple
User=athena
Group=athena
WorkingDirectory=/opt/athena-gateway
EnvironmentFile=/opt/athena-gateway/.env
ExecStart=/opt/athena-gateway/bin/athena-gateway --config configs/config.yaml
ExecReload=/bin/kill -HUP \$MAINPID
Restart=always
RestartSec=5
StandardOutput=journal
StandardError=journal
SyslogIdentifier=athena-gateway

[Install]
WantedBy=multi-user.target
EOF

# 重载systemd
sudo systemctl daemon-reload

# 启用服务
sudo systemctl enable athena-gateway

# 启动服务
sudo systemctl start athena-gateway
```

### 5. 配置Nginx反向代理

```bash
# 创建Nginx配置
sudo tee /etc/nginx/sites-available/athena-gateway > /dev/null <<EOF
server {
    listen 80;
    server_name api.example.com;

    location / {
        proxy_pass http://127.0.0.1:8080;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_read_timeout 300s;
        proxy_connect_timeout 75s;
    }
}
EOF

# 启用站点
sudo ln -s /etc/nginx/sites-available/athena-gateway /etc/nginx/sites-enabled/

# 测试配置
sudo nginx -t

# 重启Nginx
sudo systemctl restart nginx
```

---

## Docker部署

### 1. 单容器部署

```bash
# 构建镜像
docker build -f deployments/docker/Dockerfile -t athena-gateway:latest .

# 运行容器
docker run -d \
  --name athena-gateway \
  -p 8080:8080 \
  -v $(pwd)/configs:/app/configs \
  -v athena_logs:/var/log/athena-gateway \
  -e JWT_SECRET=your-secret-key \
  athena-gateway:latest
```

### 2. Docker Compose部署

```bash
# 启动完整服务栈
cd deployments/docker
docker-compose up -d

# 查看服务状态
docker-compose ps

# 查看日志
docker-compose logs -f athena-gateway
```

### 3. 环境配置

```yaml
# docker-compose.override.yml
version: '3.8'
services:
  athena-gateway:
    environment:
      - ATHENA_GATEWAY_ENV=production
      - JWT_SECRET=${JWT_SECRET}
      - DB_HOST=postgres
      - REDIS_HOST=redis
    volumes:
      - ./custom-configs:/app/configs
      - /var/log/athena-gateway:/var/log/athena-gateway
```

---

## Kubernetes部署

### 1. 创建Namespace

```yaml
# namespace.yaml
apiVersion: v1
kind: Namespace
metadata:
  name: athena-gateway
  labels:
    name: athena-gateway
```

### 2. 创建ConfigMap

```yaml
# configmap.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: athena-gateway-config
  namespace: athena-gateway
data:
  config.yaml: |
    server:
      host: "0.0.0.0"
      port: 8080
    auth:
      jwt_secret: "\${JWT_SECRET}"
      access_token_exp: 30
      refresh_token_exp: 8
    logging:
      level: "warn"
      format: "json"
      output: "stdout"
    upstream:
      timeout: 30
```

### 3. 创建Secret

```yaml
# secret.yaml
apiVersion: v1
kind: Secret
metadata:
  name: athena-gateway-secrets
  namespace: athena-gateway
type: Opaque
data:
  jwt-secret: eW91ci1zdXBlci1zamV0LWtleS1jaGFuZ2UtaW4tcHJvZHVjdGlvbg==  # base64编码
  db-password: eW91ci1kYXRhYmFzZS1wYXNzd29yZA==
```

### 4. 创建Deployment

```yaml
# deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: athena-gateway
  namespace: athena-gateway
  labels:
    app: athena-gateway
spec:
  replicas: 3
  selector:
    matchLabels:
      app: athena-gateway
  template:
    metadata:
      labels:
        app: athena-gateway
    spec:
      containers:
      - name: athena-gateway
        image: athena-gateway:latest
        ports:
        - containerPort: 8080
        env:
        - name: ATHENA_GATEWAY_ENV
          value: "production"
        - name: JWT_SECRET
          valueFrom:
            secretKeyRef:
              name: athena-gateway-secrets
              key: jwt-secret
        volumeMounts:
        - name: config
          mountPath: /app/configs
        livenessProbe:
          httpGet:
            path: /health
            port: 8080
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health/ready
            port: 8080
          initialDelaySeconds: 5
          periodSeconds: 5
      volumes:
      - name: config
        configMap:
          name: athena-gateway-config
```

### 5. 创建Service

```yaml
# service.yaml
apiVersion: v1
kind: Service
metadata:
  name: athena-gateway-service
  namespace: athena-gateway
spec:
  selector:
    app: athena-gateway
  ports:
  - protocol: TCP
    port: 80
    targetPort: 8080
  type: ClusterIP
```

### 6. 创建Ingress

```yaml
# ingress.yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: athena-gateway-ingress
  namespace: athena-gateway
  annotations:
    kubernetes.io/ingress.class: nginx
    cert-manager.io/cluster-issuer: letsencrypt-prod
spec:
  tls:
  - hosts:
    - api.example.com
    secretName: athena-gateway-tls
  rules:
  - host: api.example.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: athena-gateway-service
            port:
              number: 80
```

### 7. 部署到K8s

```bash
# 应用所有配置
kubectl apply -f deployments/k8s/

# 查看部署状态
kubectl get pods -n athena-gateway

# 查看服务
kubectl get svc -n athena-gateway

# 查看日志
kubectl logs -f deployment/athena-gateway -n athena-gateway
```

---

## 监控和维护

### 1. 健康检查

```bash
# 基本健康检查
curl http://localhost:8080/health

# 就绪检查
curl http://localhost:8080/health/ready

# 存活检查
curl http://localhost:8080/health/live
```

### 2. 日志管理

```bash
# 查看应用日志
tail -f /var/log/athena-gateway/app.log

# 查看系统日志
journalctl -u athena-gateway -f

# Docker日志
docker logs -f athena-gateway

# K8s日志
kubectl logs -f deployment/athena-gateway -n athena-gateway
```

### 3. 性能监控

```bash
# 查看系统指标
curl http://localhost:8080/api/v1/admin/metrics

# 查看系统状态
curl http://localhost:8080/api/v1/admin/status
```

### 4. 配置热重载

```bash
# 发送SIGHUP信号重载配置
sudo systemctl reload athena-gateway

# 或者重启服务
sudo systemctl restart athena-gateway
```

---

## 故障排除

### 常见问题

#### 1. 服务无法启动

**症状**: 服务启动失败或立即退出
**解决方案**:
```bash
# 检查配置文件
go run cmd/server/main.go --config configs/config.yaml --dry-run

# 检查端口占用
netstat -tlnp | grep 8080

# 查看详细错误
journalctl -u athena-gateway -n 50
```

#### 2. 认证失败

**症状**: JWT令牌验证失败
**解决方案**:
```bash
# 检查JWT密钥配置
grep jwt_secret configs/config.yaml

# 验证令牌格式
echo "Bearer your-token" | cut -d' ' -f2

# 检查时钟同步
date
```

#### 3. 上游服务连接失败

**症状**: 无法连接到后端服务
**解决方案**:
```bash
# 检查网络连通性
telnet upstream-host 8001

# 检查DNS解析
nslookup upstream-host

# 检查防火墙规则
sudo iptables -L | grep 8080
```

#### 4. 内存使用过高

**症状**: 服务内存占用持续增长
**解决方案**:
```bash
# 检查内存使用
ps aux | grep athena-gateway

# 启用GC调试
export GODEBUG=gctrace=1

# 检查内存泄漏
go tool pprof http://localhost:6060/debug/pprof/heap
```

### 性能优化

#### 1. 系统调优

```bash
# 增加文件描述符限制
echo "* soft nofile 65536" >> /etc/security/limits.conf
echo "* hard nofile 65536" >> /etc/security/limits.conf

# 优化内核参数
echo "net.core.somaxconn = 65535" >> /etc/sysctl.conf
echo "net.ipv4.tcp_max_syn_backlog = 65535" >> /etc/sysctl.conf
sysctl -p
```

#### 2. 应用优化

```yaml
# config.yaml
server:
  read_timeout: 15      # 减少读取超时
  write_timeout: 15     # 减少写入超时
  idle_timeout: 30      # 减少空闲超时

logging:
  level: "warn"        # 生产环境使用warn级别
  max_size: 200        # 增加日志文件大小
  max_backups: 5       # 减少备份数量
```

### 安全加固

#### 1. 网络安全

```bash
# 配置防火墙
sudo ufw allow 8080/tcp
sudo ufw enable

# 配置fail2ban
sudo apt install fail2ban
sudo systemctl enable fail2ban
```

#### 2. 应用安全

```yaml
# config.yaml
auth:
  jwt_secret: "${JWT_SECRET}"  # 使用环境变量
  access_token_exp: 15         # 减少令牌有效期
  
logging:
  level: "error"               # 生产环境减少日志
```

---

## 📞 获取帮助

如有部署问题，请联系：

- **文档**: 查看项目README.md
- **Issues**: 提交GitHub Issues
- **社区**: 加入讨论群组
- **邮件**: support@athena-platform.com

---

**🌸 Athena工作平台 - 星河智汇，光耀知途** 💕