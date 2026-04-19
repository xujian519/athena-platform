# 部署指南

> Athena浏览器自动化服务 - 部署指南

本文档提供详细的部署说明，包括开发环境、生产环境和Docker部署。

---

## 目录

- [环境要求](#环境要求)
- [开发环境部署](#开发环境部署)
- [生产环境部署](#生产环境部署)
- [Docker部署](#docker部署)
- [Kubernetes部署](#kubernetes部署)
- [监控和日志](#监控和日志)
- [安全加固](#安全加固)

---

## 环境要求

### 系统要求

- **操作系统**: Linux (Ubuntu 20.04+, CentOS 8+), macOS 10.15+, Windows 10+
- **Python**: 3.10 或更高版本
- **内存**: 最低 2GB，推荐 4GB+
- **磁盘**: 最低 10GB 可用空间
- **网络**: 稳定的互联网连接

### 依赖服务

- **PostgreSQL** (可选，用于持久化存储)
- **Redis** (可选，用于缓存和会话管理)
- **Nginx** (可选，用于反向代理)

---

## 开发环境部署

### 1. 克隆项目

```bash
cd /path/to/your/workspace
cd services/browser_automation_service
```

### 2. 创建虚拟环境

```bash
python3.10 -m venv venv
source venv/bin/activate  # Linux/macOS
# venv\Scripts\activate  # Windows
```

### 3. 安装依赖

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 4. 安装Playwright浏览器

```bash
playwright install chromium
```

### 5. 配置环境变量

```bash
# 复制配置模板
cp .env.example .env

# 编辑配置
nano .env
```

**开发环境配置示例：**
```bash
# 服务配置
HOST=127.0.0.1
PORT=8030
LOG_LEVEL=debug

# 浏览器配置
BROWSER_TYPE=chromium
BROWSER_HEADLESS=false  # 开发环境建议关闭无头模式

# 功能开关
ENABLE_AUTH=false  # 开发环境可以关闭认证
```

### 6. 启动服务

```bash
# 开发模式（自动重载）
python main.py

# 或使用uvicorn直接启动
uvicorn main:app --host 127.0.0.1 --port 8030 --reload
```

### 7. 验证安装

```bash
# 健康检查
curl http://localhost:8030/health

# 访问API文档
open http://localhost:8030/docs
```

---

## 生产环境部署

### 1. 系统准备

```bash
# 更新系统
sudo apt update && sudo apt upgrade -y  # Ubuntu/Debian

# 安装系统依赖
sudo apt install -y python3.10 python3.10-venv python3-pip
sudo apt install -y nginx postgresql redis-server
```

### 2. 创建专用用户

```bash
# 创建服务用户
sudo useradd -r -s /bin/false browser-service

# 创建目录
sudo mkdir -p /opt/browser-automation
sudo chown browser-service:browser-service /opt/browser-automation
```

### 3. 部署应用

```bash
# 切换到服务用户
sudo -u browser-service -i

# 进入部署目录
cd /opt/browser-automation

# 创建虚拟环境
python3.10 -m venv venv
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt
playwright install chromium --with-deps
```

### 4. 配置环境

```bash
# 生产环境配置
sudo nano /opt/browser-automation/.env
```

**生产环境配置示例：**
```bash
# 服务配置
HOST=0.0.0.0
PORT=8030
WORKERS=4
LOG_LEVEL=info
ENVIRONMENT=production

# 安全配置
SECRET_KEY=$(python -c "import secrets; print(secrets.token_urlsafe(32))")
ENABLE_AUTH=true

# 浏览器配置
BROWSER_TYPE=chromium
BROWSER_HEADLESS=true
BROWSER_WINDOW_WIDTH=1920
BROWSER_WINDOW_HEIGHT=1080

# 会话配置
MAX_CONCURRENT_SESSIONS=20
SESSION_TIMEOUT=3600

# 性能配置
MAX_CONCURRENT_TASKS=10
RATE_LIMIT_PER_MINUTE=120

# 日志配置
LOG_FILE=/var/log/browser-automation/app.log
LOG_ROTATION=1 day
LOG_RETENTION=7 days
```

### 5. 配置Systemd服务

```bash
sudo nano /etc/systemd/system/browser-automation.service
```

**服务配置：**
```ini
[Unit]
Description=Athena Browser Automation Service
After=network.target postgresql.service redis.service

[Service]
Type=notify
User=browser-service
Group=browser-service
WorkingDirectory=/opt/browser-automation
Environment="PATH=/opt/browser-automation/venv/bin"
ExecStart=/opt/browser-automation/venv/bin/gunicorn main:app \
    --workers 4 \
    --worker-class uvicorn.workers.UvicornWorker \
    --bind 0.0.0.0:8030 \
    --access-logfile /var/log/browser-automation/access.log \
    --error-logfile /var/log/browser-automation/error.log \
    --log-level info

Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

**启动服务：**
```bash
# 创建日志目录
sudo mkdir -p /var/log/browser-automation
sudo chown browser-service:browser-service /var/log/browser-automation

# 重载systemd
sudo systemctl daemon-reload

# 启动服务
sudo systemctl start browser-automation

# 设置开机自启
sudo systemctl enable browser-automation

# 检查状态
sudo systemctl status browser-automation
```

### 6. 配置Nginx反向代理

```bash
sudo nano /etc/nginx/sites-available/browser-automation
```

**Nginx配置：**
```nginx
upstream browser_automation {
    server 127.0.0.1:8030;
}

server {
    listen 80;
    server_name your-domain.com;

    # 日志
    access_log /var/log/nginx/browser-automation-access.log;
    error_log /var/log/nginx/browser-automation-error.log;

    # 请求体大小限制
    client_max_body_size 10M;

    # 超时配置
    proxy_connect_timeout 60s;
    proxy_send_timeout 60s;
    proxy_read_timeout 60s;

    location / {
        proxy_pass http://browser_automation;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # WebSocket支持（如果需要）
    location /ws {
        proxy_pass http://browser_automation;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

**启用配置：**
```bash
sudo ln -s /etc/nginx/sites-available/browser-automation /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

---

## Docker部署

### 1. 创建Dockerfile

```dockerfile
FROM python:3.10-slim

# 设置工作目录
WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    ca-certificates \
    fonts-liberation \
    libappindicator3-1 \
    libasound2 \
    libatk-bridge2.0-0 \
    libatk1.0-0 \
    libcups2 \
    libdbus-1-3 \
    libdrm2 \
    libgbm1 \
    libgtk-3-0 \
    libnspr4 \
    libnss3 \
    libxcomposite1 \
    libxdamage1 \
    libxfixes3 \
    libxrandr2 \
    libxss1 \
    xdg-utils \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件
COPY requirements.txt .

# 安装Python依赖
RUN pip install --no-cache-dir -r requirements.txt

# 安装Playwright浏览器
RUN playwright install chromium --with-deps

# 复制应用代码
COPY . .

# 创建日志目录
RUN mkdir -p /app/logs

# 暴露端口
EXPOSE 8030

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8030/health || exit 1

# 启动命令
CMD ["gunicorn", "main:app", "--workers", "4", "--worker-class", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:8030"]
```

### 2. 构建和运行

```bash
# 构建镜像
docker build -t browser-automation:latest .

# 运行容器
docker run -d \
  --name browser-automation \
  -p 8030:8030 \
  -v $(pwd)/logs:/app/logs \
  -v $(pwd)/downloads:/app/downloads \
  --env-file .env \
  --restart unless-stopped \
  browser-automation:latest

# 查看日志
docker logs -f browser-automation
```

### 3. Docker Compose部署

**docker-compose.yml：**
```yaml
version: '3.8'

services:
  browser-automation:
    build: .
    container_name: browser-automation
    ports:
      - "8030:8030"
    volumes:
      - ./logs:/app/logs
      - ./downloads:/app/downloads
    env_file:
      - .env
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8030/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 5s
    networks:
      - browser-net

  redis:
    image: redis:7-alpine
    container_name: browser-redis
    ports:
      - "6379:6379"
    volumes:
      - redis-data:/data
    restart: unless-stopped
    networks:
      - browser-net

  postgres:
    image: postgres:15-alpine
    container_name: browser-postgres
    ports:
      - "5432:5432"
    environment:
      POSTGRES_DB: browser_automation
      POSTGRES_USER: browser_user
      POSTGRES_PASSWORD: ${DB_PASSWORD:-changeme}
    volumes:
      - postgres-data:/var/lib/postgresql/data
    restart: unless-stopped
    networks:
      - browser-net

volumes:
  redis-data:
  postgres-data:

networks:
  browser-net:
    driver: bridge
```

**启动：**
```bash
# 启动所有服务
docker-compose up -d

# 查看状态
docker-compose ps

# 查看日志
docker-compose logs -f

# 停止服务
docker-compose down
```

---

## Kubernetes部署

### 1. 创建部署配置

**deployment.yaml：**
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: browser-automation
  labels:
    app: browser-automation
spec:
  replicas: 3
  selector:
    matchLabels:
      app: browser-automation
  template:
    metadata:
      labels:
        app: browser-automation
    spec:
      containers:
      - name: browser-automation
        image: browser-automation:latest
        ports:
        - containerPort: 8030
        env:
        - name: HOST
          value: "0.0.0.0"
        - name: PORT
          value: "8030"
        - name: BROWSER_HEADLESS
          value: "true"
        envFrom:
        - secretRef:
            name: browser-secrets
        resources:
          requests:
            memory: "512Mi"
            cpu: "500m"
          limits:
            memory: "2Gi"
            cpu: "2000m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8030
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health
            port: 8030
          initialDelaySeconds: 10
          periodSeconds: 5
        volumeMounts:
        - name: logs
          mountPath: /app/logs
      volumes:
      - name: logs
        emptyDir: {}
---
apiVersion: v1
kind: Service
metadata:
  name: browser-automation
spec:
  selector:
    app: browser-automation
  ports:
  - protocol: TCP
    port: 80
    targetPort: 8030
  type: LoadBalancer
---
apiVersion: v1
kind: Secret
metadata:
  name: browser-secrets
type: Opaque
stringData:
  SECRET_KEY: "your-secret-key-here"
  API_KEY: "your-api-key-here"
```

### 2. 部署到Kubernetes

```bash
# 构建并推送镜像
docker build -t your-registry/browser-automation:latest .
docker push your-registry/browser-automation:latest

# 部署
kubectl apply -f deployment.yaml

# 查看状态
kubectl get pods
kubectl logs -f deployment/browser-automation

# 暴露服务
kubectl expose deployment browser-automation --type=LoadBalancer --port=80
```

---

## 监控和日志

### 日志管理

```bash
# 查看应用日志
tail -f /var/log/browser-automation/app.log

# 使用journal查看系统日志
sudo journalctl -u browser-automation -f

# 日志轮转配置（logrotate）
sudo nano /etc/logrotate.d/browser-automation
```

**logrotate配置：**
```
/var/log/browser-automation/*.log {
    daily
    rotate 7
    compress
    delaycompress
    missingok
    notifempty
    create 0640 browser-service browser-service
    sharedscripts
    postrotate
        systemctl reload browser-automation > /dev/null 2>&1 || true
    endscript
}
```

### 性能监控

使用Prometheus和Grafana监控服务：

**prometheus.yml：**
```yaml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'browser-automation'
    static_configs:
      - targets: ['localhost:8030']
    metrics_path: '/metrics'
```

---

## 安全加固

### 1. 使用HTTPS

```bash
# 安装certbot
sudo apt install certbot python3-certbot-nginx

# 获取SSL证书
sudo certbot --nginx -d your-domain.com

# 自动续期
sudo certbot renew --dry-run
```

### 2. 配置防火墙

```bash
# UFW防火墙
sudo ufw allow 22/tcp    # SSH
sudo ufw allow 80/tcp    # HTTP
sudo ufw allow 443/tcp   # HTTPS
sudo ufw enable
```

### 3. 定期更新

```bash
# 更新依赖
pip install --upgrade -r requirements.txt

# 更新Playwright
playwright install chromium --with-deps
```

---

## 验证部署

### 健康检查脚本

```bash
#!/bin/bash
# health_check.sh

echo "检查浏览器自动化服务..."

# 检查服务状态
systemctl is-active browser-automation

# 检查端口
ss -tlnp | grep 8030

# 健康检查
curl -f http://localhost:8030/health

echo "部署验证完成！"
```

### 负载测试

```bash
# 使用locust进行负载测试
pip install locust

# 创建locustfile.py
cat > locustfile.py << 'EOF'
from locust import HttpUser, task, between

class BrowserUser(HttpUser):
    wait_time = between(1, 3)

    @task
    def health_check(self):
        self.client.get("/health")

    @task(3)
    def navigate(self):
        self.client.post("/api/v1/navigate", json={
            "url": "https://www.baidu.com"
        })
EOF

# 运行测试
locust -f locustfile.py --host=http://localhost:8030
```

---

## 故障排查

部署后遇到问题？

查看 [故障排查指南](./TROUBLESHOOTING.md) 获取详细帮助。

---

## 相关文档

- [API使用示例](./API_USAGE.md)
- [故障排查指南](./TROUBLESHOOTING.md)
- [测试指南](./TESTING.md)
