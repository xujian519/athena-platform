# Athena API网关部署文档和运维指南

## 1. 部署概述

### 1.1 架构简介

Athena API网关采用微服务架构，通过适配器模式将现有服务统一接入，提供标准化的API接口。

```
┌─────────────────────────────────────────────────────────────────┐
│                     API网关 (8080)                          │
├─────────────────────────────────────────────────────────────────┤
│                    适配层                                │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐       │
│  │专利检索适配器│ │专利撰写适配器│ │认证服务适配器│ ...     │
│  └─────────────┘ └─────────────┘ └─────────────┘       │
├─────────────────────────────────────────────────────────────────┤
│                      后端服务                             │
│  :8050       :8051       :8052       :8053        │
│ yunpat-agent  patent-writing  auth  technical-analysis  │
└─────────────────────────────────────────────────────────────────┘
```

### 1.2 服务清单

| 服务名称 | 端口 | 健康检查路径 | 描述 | 状态 |
|----------|------|--------------|------|------|
| API网关 | 8080 | `/health` | 统一入口 | 核心服务 |
| 专利检索 | 8050 | `/health` | yunpat-agent适配 | 已迁移 |
| 专利撰写 | 8051 | `/health` | 新建服务 | 新服务 |
| 认证服务 | 8052 | `/health` | 统一认证 | 新服务 |
| 技术分析 | 8053 | `/health` | 专利技术分析 | 新服务 |

## 2. 环境准备

### 2.1 系统要求

#### 硬件要求

**最低配置**:
- CPU: 4核心
- 内存: 8GB
- 存储: 50GB可用空间
- 网络: 100Mbps带宽

**推荐配置**:
- CPU: 8核心或更多
- 内存: 16GB或更多
- 存储: 100GB SSD
- 网络: 1Gbps带宽

#### 软件要求

- **操作系统**: Linux (Ubuntu 20.04+, CentOS 8+) 或 macOS 10.15+
- **Python**: 3.11或更高版本
- **Node.js**: 18.0+ (用于API网关)
- **Docker**: 20.10+ (可选，用于容器化部署)
- **Git**: 2.25+

### 2.2 依赖服务

#### 数据库服务
```bash
# PostgreSQL
sudo apt-get install postgresql postgresql-contrib
sudo systemctl start postgresql
sudo systemctl enable postgresql

# Redis
sudo apt-get install redis-server
sudo systemctl start redis-server
sudo systemctl enable redis-server

# MongoDB (用于专利撰写)
wget -qO - https://www.mongodb.org/static/pgp/server-5.0.asc | sudo apt-key add -
echo "deb [ arch=amd64,arm64 ] https://repo.mongodb.org/apt/ubuntu focal/mongodb-org/5.0 multiverse" | sudo tee /etc/apt/sources.list.d/mongodb-org-5.0.list
sudo apt-get update
sudo apt-get install -y mongodb-org
sudo systemctl start mongod
sudo systemctl enable mongod
```

#### 搜索引擎
```bash
# Elasticsearch
wget https://artifacts.elastic.co/downloads/elasticsearch/elasticsearch-8.5.0-linux-x86_64.tar.gz
tar -xzf elasticsearch-8.5.0-linux-x86_64.tar.gz
sudo mv elasticsearch-8.5.0 /usr/local/elasticsearch
sudo chown -R elasticsearch:elasticsearch /usr/local/elasticsearch
sudo systemctl enable elasticsearch
sudo systemctl start elasticsearch

# Qdrant (向量数据库)
curl -L https://github.com/qdrant/qdrant/releases/latest/download/qdrant-linux-x86_64.tar.gz | tar xz
sudo mv qdrant /usr/local/bin/
sudo chmod +x /usr/local/bin/qdrant
sudo systemctl enable qdrant
sudo systemctl start qdrant
```

## 3. 部署步骤

### 3.1 源码部署

#### 步骤1: 获取源码
```bash
# 克隆代码仓库
git clone https://github.com/athena/api-gateway.git
cd athena/api-gateway

# 切换到稳定分支
git checkout stable-v2.0
```

#### 步骤2: 环境配置
```bash
# 复制环境配置文件
cp config/adapters.yaml.example config/adapters.yaml
cp config/environments.yaml.example config/environments.yaml

# 编辑配置文件
vim config/adapters.yaml
```

**配置示例**:
```yaml
services:
  patent-search:
    service_url: "http://localhost:8050"
    health_threshold: 5000
    timeout: 30000
    retry_attempts: 3
  
  authentication:
    service_url: "http://localhost:8052"
    health_threshold: 3000
    timeout: 10000
    retry_attempts: 1
    circuit_breaker:
      secret: "your-jwt-secret-key"
      algorithm: "HS256"
      expires_in: 86400
```

#### 步骤3: 安装依赖
```bash
# Python依赖
pip install -r requirements.txt

# Node.js依赖 (API网关)
cd services/api-gateway
npm install
npm run build
```

#### 步骤4: 数据库初始化
```bash
# PostgreSQL数据库
sudo -u postgres createdb athena_platform
sudo -u postgres createuser athena_user
sudo -u postgres psql -c "ALTER USER athena_user PASSWORD 'secure_password';"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE athena_platform TO athena_user;"

# 运行迁移脚本
python3 scripts/init_database.py
```

#### 步骤5: 服务部署
```bash
# 部署适配器服务
cd adapters

# 专利检索服务 (已存在)
python3 patent_search_adapter.py --port 8050 &

# 新建服务
python3 patent_writing_adapter.py --port 8051 &
python3 authentication_adapter.py --port 8052 &
python3 technical_analysis_adapter.py --port 8053 &

# 部署API网关
cd ../services/api-gateway
npm start
```

### 3.2 Docker部署

#### 构建镜像
```bash
# 构建API网关镜像
cd services/api-gateway
docker build -t athena/api-gateway:v2.0 .

# 构建服务镜像
cd ../adapters
docker build -f Dockerfile.patent-search -t athena/patent-search:v2.0 .
docker build -f Dockerfile.patent-writing -t athena/patent-writing:v2.0 .
docker build -f Dockerfile.authentication -t athena/authentication:v2.0 .
docker build -f Dockerfile.technical-analysis -t athena/technical-analysis:v2.0 .
```

#### Docker Compose部署
```yaml
# docker-compose.yml
version: '3.8'

services:
  # 数据库服务
  postgresql:
    image: postgres:15
    environment:
      POSTGRES_DB: athena_platform
      POSTGRES_USER: athena_user
      POSTGRES_PASSWORD: secure_password
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U athena_user -d athena_platform"]
      interval: 30s
      timeout: 10s
      retries: 3

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 30s
      timeout: 10s
      retries: 3

  mongodb:
    image: mongo:6.0
    environment:
      MONGO_INITDB_ROOT_USERNAME: admin
      MONGO_INITDB_ROOT_PASSWORD: mongo_password
    volumes:
      - mongo_data:/data/db
    ports:
      - "27017:27017"

  # 搜索引擎
  elasticsearch:
    image: docker.elastic.co/elasticsearch/elasticsearch:8.5.0
    environment:
      - discovery.type=single-node
      - "ES_JAVA_OPTS=-Xms512m -Xmx512m"
    volumes:
      - es_data:/usr/share/elasticsearch/data
    ports:
      - "9200:9200"
      - "9300:9300"

  qdrant:
    image: qdrant/qdrant:latest
    volumes:
      - qdrant_data:/qdrant/storage
    ports:
      - "6333:6333"
      - "6334:6334"

  # 应用服务
  patent-search:
    image: athena/patent-search:v2.0
    environment:
      - SERVICE_URL=http://yunpat-agent:8050
      - REDIS_URL=redis://redis:6379
      - POSTGRES_URL=postgresql://athena_user:secure_password@postgresql:5432/athena_platform
    depends_on:
      - redis
      - postgresql
    ports:
      - "8050:8050"
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8050/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  patent-writing:
    image: athena/patent-writing:v2.0
    environment:
      - SERVICE_URL=http://localhost:8051
      - MONGODB_URL=mongodb://admin:mongo_password@mongodb:27017/patent_writing
      - ELASTICSEARCH_URL=http://elasticsearch:9200
    depends_on:
      - mongodb
      - elasticsearch
    ports:
      - "8051:8051"

  authentication:
    image: athena/authentication:v2.0
    environment:
      - SERVICE_URL=http://localhost:8052
      - REDIS_URL=redis://redis:6379
      - POSTGRES_URL=postgresql://athena_user:secure_password@postgresql:5432/athena_platform
      - JWT_SECRET=your-super-secret-jwt-key
    depends_on:
      - redis
      - postgresql
    ports:
      - "8052:8052"

  technical-analysis:
    image: athena/technical-analysis:v2.0
    environment:
      - SERVICE_URL=http://localhost:8053
      - QDRANT_URL=http://qdrant:6333
      - ELASTICSEARCH_URL=http://elasticsearch:9200
    depends_on:
      - qdrant
      - elasticsearch
    ports:
      - "8053:8053"

  # API网关
  api-gateway:
    image: athena/api-gateway:v2.0
    environment:
      - NODE_ENV=production
      - PORT=8080
      - JWT_SECRET=your-super-secret-jwt-key
      - REDIS_URL=redis://redis:6379
    depends_on:
      - patent-search
      - patent-writing
      - authentication
      - technical-analysis
    ports:
      - "8080:8080"
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8080/health"]
      interval: 30s
      timeout: 10s
      retries: 3

volumes:
  postgres_data:
  mongo_data:
  es_data:
  qdrant_data:
```

#### 启动Docker Compose
```bash
# 启动所有服务
docker-compose up -d

# 查看服务状态
docker-compose ps

# 查看日志
docker-compose logs -f api-gateway
```

### 3.3 Kubernetes部署

#### 命名空间创建
```bash
kubectl create namespace athena
kubectl config set-context --current --namespace=athena
```

#### ConfigMap配置
```yaml
# configmap.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: athena-config
  namespace: athena
data:
  adapters.yaml: |
    services:
      patent-search:
        service_url: "http://patent-search:8050"
        health_threshold: 5000
        timeout: 30000
      authentication:
        service_url: "http://authentication:8052"
        jwt_secret: "your-jwt-secret"
```

#### 部署文件
```yaml
# deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: api-gateway
  namespace: athena
spec:
  replicas: 3
  selector:
    matchLabels:
      app: api-gateway
  template:
    metadata:
      labels:
        app: api-gateway
    spec:
      containers:
      - name: api-gateway
        image: athena/api-gateway:v2.0
        ports:
        - containerPort: 8080
        env:
        - name: NODE_ENV
          value: "production"
        - name: PORT
          value: "8080"
        volumeMounts:
        - name: config-volume
          mountPath: /app/config
        livenessProbe:
          httpGet:
            path: /health
            port: 8080
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health
            port: 8080
          initialDelaySeconds: 5
          periodSeconds: 5
      volumes:
      - name: config-volume
        configMap:
          name: athena-config
---
apiVersion: v1
kind: Service
metadata:
  name: api-gateway
  namespace: athena
spec:
  selector:
    app: api-gateway
  ports:
  - port: 80
    targetPort: 8080
  type: LoadBalancer
```

#### 部署到Kubernetes
```bash
# 应用配置
kubectl apply -f configmap.yaml
kubectl apply -f deployment.yaml

# 查看部署状态
kubectl get pods -n athena
kubectl get services -n athena

# 查看日志
kubectl logs -f deployment/api-gateway -n athena
```

## 4. 运维指南

### 4.1 服务监控

#### 健康检查
```bash
# 检查网关状态
curl http://localhost:8080/health

# 检查各服务状态
curl http://localhost:8050/health
curl http://localhost:8051/health
curl http://localhost:8052/health
curl http://localhost:8053/health
```

#### 监控指标
```bash
# Prometheus指标
curl http://localhost:8080/metrics

# 自定义监控端点
curl http://localhost:8080/api/v1/monitoring/status
curl http://localhost:8080/api/v1/monitoring/metrics
```

#### 日志管理
```bash
# 查看应用日志
tail -f /var/log/athena/api-gateway.log
tail -f /var/log/athena/patent-search.log
tail -f /var/log/athena/authentication.log

# 使用journalctl (systemd)
sudo journalctl -u athena-api-gateway -f
sudo journalctl -u athena-patent-search -f
```

### 4.2 性能优化

#### 数据库优化
```sql
-- PostgreSQL配置优化
ALTER SYSTEM SET shared_buffers = '256MB';
ALTER SYSTEM SET effective_cache_size = '1GB';
ALTER SYSTEM SET maintenance_work_mem = '64MB';
ALTER SYSTEM SET checkpoint_completion_target = 0.9;
ALTER SYSTEM SET wal_buffers = '16MB';
```

#### 缓存策略
```yaml
# Redis缓存配置
cache_config:
  session_ttl: 3600  # 1小时
  api_cache_ttl: 300  # 5分钟
  search_cache_ttl: 1800  # 30分钟
  max_memory: "512MB"
```

#### 负载均衡
```nginx
# Nginx配置
upstream athena_gateway {
    server 10.0.1.10:8080 weight=3 max_fails=3 fail_timeout=30s;
    server 10.0.1.11:8080 weight=3 max_fails=3 fail_timeout=30s;
    server 10.0.1.12:8080 weight=3 max_fails=3 fail_timeout=30s;
}

server {
    listen 80;
    server_name api.athena.com;
    
    location / {
        proxy_pass http://athena_gateway;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # 健康检查
        proxy_next_upstream_timeout 30s;
        proxy_connect_timeout 5s;
        proxy_read_timeout 60s;
        proxy_send_timeout 60s;
    }
}
```

### 4.3 安全配置

#### SSL/TLS配置
```nginx
server {
    listen 443 ssl http2;
    server_name api.athena.com;
    
    ssl_certificate /etc/ssl/certs/athena.com.crt;
    ssl_certificate_key /etc/ssl/private/athena.com.key;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512;
    
    location / {
        proxy_pass http://athena_gateway;
        proxy_set_header Host $host;
        proxy_set_header X-Forwarded-Proto https;
    }
}
```

#### 防火墙配置
```bash
# UFW防火墙规则
sudo ufw allow 80/tcp    # HTTP
sudo ufw allow 443/tcp   # HTTPS
sudo ufw allow 8080/tcp # API网关
sudo ufw allow 8050:8053/tcp # 后端服务
sudo ufw enable
```

### 4.4 备份和恢复

#### 数据备份
```bash
#!/bin/bash
# backup.sh

BACKUP_DIR="/backup/athena"
DATE=$(date +%Y%m%d_%H%M%S)

# PostgreSQL备份
pg_dump -h localhost -U athena_user -d athena_platform > "$BACKUP_DIR/postgres_$DATE.sql"

# MongoDB备份
mongodump --host localhost --db patent_writing --out "$BACKUP_DIR/mongodb_$DATE"

# 配置文件备份
tar -czf "$BACKUP_DIR/config_$DATE.tar.gz" /opt/athena/config/

# 清理旧备份 (保留7天)
find $BACKUP_DIR -name "*.sql" -mtime +7 -delete
find $BACKUP_DIR -name "*.tar.gz" -mtime +7 -delete
```

#### 服务恢复
```bash
#!/bin/bash
# restore.sh

BACKUP_FILE=$1

if [ -z "$BACKUP_FILE" ]; then
    echo "Usage: $0 <backup_file>"
    exit 1
fi

# 停止服务
docker-compose down

# 恢复数据库
case $BACKUP_FILE in
    *postgres*)
        psql -h localhost -U athena_user -d athena_platform < $BACKUP_FILE
        ;;
    *mongodb*)
        mongorestore --host localhost --db patent_writing $BACKUP_FILE
        ;;
esac

# 重启服务
docker-compose up -d
```

### 4.5 故障排除

#### 常见问题

**问题1: 服务无法启动**
```bash
# 检查端口占用
netstat -tulpn | grep :8080
lsof -i :8080

# 检查配置文件语法
python3 -c "import yaml; yaml.safe_load(open('config/adapters.yaml'))"

# 检查依赖
pip list | grep -E "(fastapi|uvicorn|aiohttp)"
```

**问题2: 性能下降**
```bash
# 检查系统资源
top
htop
free -h
df -h

# 检查数据库性能
sudo -u postgres psql -c "SELECT * FROM pg_stat_activity;"
sudo -u postgres psql -c "SELECT * FROM pg_stat_user_tables;"

# 检查网络延迟
ping -c 10 database-server
```

**问题3: 连接超时**
```bash
# 检查网络连通性
telnet localhost 8080
nc -zv localhost 8080

# 检查DNS解析
nslookup api.athena.com
dig api.athena.com

# 检查防火墙规则
sudo ufw status
sudo iptables -L
```

#### 调试模式
```bash
# 启用调试日志
export DEBUG=athena:*
export LOG_LEVEL=DEBUG

# 启动调试模式
python3 api_gateway.py --debug --log-level DEBUG

# 使用调试工具
curl -v http://localhost:8080/health
wget --debug http://localhost:8080/health
```

### 4.6 升级和维护

#### 滚动升级
```bash
#!/bin/bash
# rolling_upgrade.sh

NEW_VERSION=$1
CURRENT_VERSION=$(docker inspect athena/api-gateway | jq -r '.[0].Config.Labels.version')

echo "Upgrading from $CURRENT_VERSION to $NEW_VERSION"

# 1. 拉取新镜像
docker pull athena/api-gateway:$NEW_VERSION

# 2. 逐个升级实例
for i in {1..3}; do
    echo "Upgrading instance $i"
    
    # 停止旧实例
    docker stop api-gateway-$i
    
    # 启动新实例
    docker run -d \
        --name api-gateway-$i \
        -p $((8080 + $i)):8080 \
        athena/api-gateway:$NEW_VERSION
    
    # 健康检查
    sleep 30
    curl -f http://localhost:$((8080 + $i))/health
    
    if [ $? -eq 0 ]; then
        echo "Instance $i upgraded successfully"
        docker rm api-gateway-$i-$(echo $CURRENT_VERSION | tr '.' '-')
    else
        echo "Instance $i upgrade failed, rolling back"
        docker stop api-gateway-$i
        docker run -d \
            --name api-gateway-$i \
            -p $((8080 + $i)):8080 \
            athena/api-gateway:$CURRENT_VERSION
    fi
done
```

#### 定期维护
```bash
#!/bin/bash
# maintenance.sh

# 清理日志
find /var/log/athena -name "*.log" -mtime +30 -delete
find /var/log/athena -name "*.log.gz" -mtime +90 -delete

# 清理临时文件
find /tmp -name "athena_*" -mtime +7 -delete

# 优化数据库
sudo -u postgres psql -d athena_platform -c "VACUUM ANALYZE;"
sudo -u postgres psql -d athena_platform -c "REINDEX DATABASE athena_platform;"

# 更新系统
sudo apt update
sudo apt upgrade -y
```

## 5. 监控和告警

### 5.1 Prometheus监控配置

```yaml
# prometheus.yml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'athena-gateway'
    static_configs:
      - targets: ['localhost:8080']
    metrics_path: /metrics
    scrape_interval: 5s

  - job_name: 'athena-services'
    static_configs:
      - targets: 
        - 'localhost:8050'
        - 'localhost:8051'
        - 'localhost:8052'
        - 'localhost:8053'
    metrics_path: /metrics
    scrape_interval: 10s
```

### 5.2 Grafana仪表板

```json
{
  "dashboard": {
    "title": "Athena API Gateway Monitoring",
    "panels": [
      {
        "title": "Request Rate",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(http_requests_total[5m])",
            "legendFormat": "{{method}} {{status}}"
          }
        ]
      },
      {
        "title": "Response Time",
        "type": "graph",
        "targets": [
          {
            "expr": "histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))",
            "legendFormat": "95th percentile"
          }
        ]
      }
    ]
  }
}
```

### 5.3 告警规则

```yaml
# alerting_rules.yml
groups:
  - name: athena_alerts
    rules:
      - alert: HighErrorRate
        expr: rate(http_requests_total{status=~"5.."}[5m]) > 0.1
        for: 2m
        labels:
          severity: warning
        annotations:
          summary: "High error rate detected"
          description: "Error rate is {{ $value }} errors per second"

      - alert: HighResponseTime
        expr: histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m])) > 1
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "High response time detected"
          description: "95th percentile response time is {{ $value }} seconds"
```

## 6. 应急响应

### 6.1 事件等级

- **P1 - 严重**: 服务完全不可用，影响所有用户
- **P2 - 高**: 核心功能故障，影响大部分用户
- **P3 - 中**: 部分功能异常，影响少数用户
- **P4 - 低**: 性能下降，用户体验受影响

### 6.2 应急流程

#### P1/P2事件处理
1. **立即响应** (5分钟内)
   - 确认事件影响范围
   - 启动应急响应团队
   - 建立沟通渠道

2. **快速诊断** (15分钟内)
   - 检查服务健康状态
   - 分析日志和监控数据
   - 确定故障根因

3. **应急措施** (30分钟内)
   - 执行故障恢复操作
   - 启用备用服务
   - 实施流量切换

4. **持续监控** (持续)
   - 监控恢复进度
   - 更新状态信息
   - 协调各团队行动

#### P3/P4事件处理
1. **标准响应** (30分钟内)
   - 分析问题影响
   - 制定修复计划
   - 安排处理优先级

2. **计划修复** (4小时内)
   - 实施修复方案
   - 测试验证效果
   - 部署到生产环境

### 6.3 联系信息

**应急响应团队**:
- **技术负责人**: +86-xxx-xxxx-0001
- **运维负责人**: +86-xxx-xxxx-0002
- **产品负责人**: +86-xxx-xxxx-0003

**外部支持**:
- **云服务商**: 24/7技术支持
- **安全团队**: 安全事件响应
- **法务团队**: 法律风险评估

---

**文档版本**: v2.0  
**最后更新**: 2026-02-20  
**维护团队**: Athena DevOps Team  
**联系方式**: devops@athena.com