# 🚀 部署指南

高德地图MCP服务器的完整部署指南。

## 📋 部署前准备

### 系统要求
- Python 3.8+
- 内存: 最少256MB
- 存储: 最少500MB
- 网络: 稳定的互联网连接

### API密钥获取
1. 访问[高德开放平台](https://lbs.amap.com/dev/)
2. 注册并登录账号
3. 创建应用，获取API Key和Secret Key
4. 选择所需的服务（Web服务API等）

## 🔧 本地部署

### 1. 环境准备

```bash
# 克隆项目
git clone https://github.com/athena-platform/amap-mcp-server.git
cd amap-mcp-server

# 创建虚拟环境
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# 或 venv\Scripts\activate  # Windows

# 安装依赖
pip install -r requirements.txt
```

### 2. 配置设置

```bash
# 复制配置文件
cp .env.example .env

# 编辑配置文件
nano .env
```

必要配置项：
```env
AMAP_API_KEY=your_api_key_here
AMAP_SECRET_KEY=your_secret_key_here
```

### 3. 运行测试

```bash
# 环境检查
./scripts/start.sh --check

# 运行测试
pytest tests/
```

### 4. 启动服务

```bash
# 开发模式启动
./scripts/start.sh

# 或直接运行Python模块
python -m amap_mcp_server.server
```

## 🐳 Docker部署

### 1. 构建镜像

```bash
# 使用项目提供的Dockerfile
docker build -t gaode-mcp-server:latest .

# 或直接拉取预构建镜像
docker pull athenaplatform/gaode-mcp-server:latest
```

### 2. 运行容器

```bash
# 简单运行
docker run -d \
  --name gaode-mcp-server \
  -e AMAP_API_KEY=your_api_key \
  -e AMAP_SECRET_KEY=your_secret_key \
  gaode-mcp-server:latest

# 挂载配置文件
docker run -d \
  --name gaode-mcp-server \
  -v $(pwd)/.env:/app/.env \
  -v $(pwd)/logs:/app/logs \
  gaode-mcp-server:latest
```

### 3. Docker Compose部署

创建 `docker-compose.yml`:

```yaml
version: '3.8'

services:
  gaode-mcp-server:
    image: gaode-mcp-server:latest
    container_name: gaode-mcp-server
    restart: unless-stopped
    environment:
      - AMAP_API_KEY=${AMAP_API_KEY}
      - AMAP_SECRET_KEY=${AMAP_SECRET_KEY}
      - MCP_LOG_LEVEL=INFO
    volumes:
      - ./logs:/app/logs
    networks:
      - amap-network

  # 可选：Redis缓存
  redis:
    image: redis:7-alpine
    container_name: gaode-redis
    restart: unless-stopped
    command: redis-server --appendonly yes
    volumes:
      - redis-data:/data
    networks:
      - amap-network

volumes:
  redis-data:

networks:
  amap-network:
    driver: bridge
```

启动服务：
```bash
# 设置环境变量
export AMAP_API_KEY=your_api_key
export AMAP_SECRET_KEY=your_secret_key

# 启动服务
docker-compose up -d
```

## ☸️ Kubernetes部署

### 1. 创建命名空间

```bash
kubectl create namespace gaode-mcp
```

### 2. 创建Secret

```yaml
# secrets.yaml
apiVersion: v1
kind: Secret
metadata:
  name: amap-secrets
  namespace: gaode-mcp
type: Opaque
data:
  api-key: <base64_encoded_api_key>
  secret-key: <base64_encoded_secret_key>
```

```bash
# 编码API密钥
echo -n "your_api_key" | base64
echo -n "your_secret_key" | base64

# 应用配置
kubectl apply -f secrets.yaml
```

### 3. 部署应用

```yaml
# deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: gaode-mcp-server
  namespace: gaode-mcp
  labels:
    app: gaode-mcp-server
spec:
  replicas: 2
  selector:
    matchLabels:
      app: gaode-mcp-server
  template:
    metadata:
      labels:
        app: gaode-mcp-server
    spec:
      containers:
      - name: gaode-mcp-server
        image: gaode-mcp-server:latest
        imagePullPolicy: IfNotPresent
        ports:
        - containerPort: 8080
        env:
        - name: AMAP_API_KEY
          valueFrom:
            secretKeyRef:
              name: amap-secrets
              key: api-key
        - name: AMAP_SECRET_KEY
          valueFrom:
            secretKeyRef:
              name: amap-secrets
              key: secret-key
        - name: MCP_LOG_LEVEL
          value: "INFO"
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "512Mi"
            cpu: "500m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8080
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /ready
            port: 8080
          initialDelaySeconds: 5
          periodSeconds: 5
```

### 4. 创建服务

```yaml
# service.yaml
apiVersion: v1
kind: Service
metadata:
  name: gaode-mcp-service
  namespace: gaode-mcp
spec:
  selector:
    app: gaode-mcp-server
  ports:
  - protocol: TCP
    port: 80
    targetPort: 8080
  type: ClusterIP
```

### 5. 应用部署

```bash
kubectl apply -f deployment.yaml
kubectl apply -f service.yaml
```

## 📊 监控和日志

### 日志配置

```bash
# 查看日志
docker logs gaode-mcp-server

# 实时日志
docker logs -f gaode-mcp-server

# Kubernetes日志
kubectl logs -n gaode-mcp deployment/gaode-mcp-server
```

### 监控指标

可以集成以下监控工具：

1. **Prometheus + Grafana**
   - 请求量统计
   - 响应时间监控
   - 错误率监控

2. **ELK Stack**
   - 日志收集和分析
   - 错误追踪
   - 性能分析

3. **健康检查端点**
   ```bash
   # 健康检查
   curl http://localhost:8080/health

   # 就绪检查
   curl http://localhost:8080/ready
   ```

## 🔧 性能优化

### 1. 缓存配置

```env
# 使用Redis缓存
CACHE_STRATEGY=redis
REDIS_HOST=your_redis_host
REDIS_PORT=6379
REDIS_PASSWORD=your_redis_password
AMAP_CACHE_TTL=300
```

### 2. 限流设置

```env
# 根据API配额调整
AMAP_RATE_LIMIT_RPM=100
AMAP_RATE_LIMIT_RPS=2
```

### 3. 资源限制

```yaml
# Kubernetes资源限制
resources:
  requests:
    memory: "256Mi"
    cpu: "250m"
  limits:
    memory: "1Gi"
    cpu: "1000m"
```

## 🚨 故障排除

### 常见问题

1. **API密钥错误**
   ```
   检查.env文件中的API密钥是否正确
   确认API密钥已开通相应服务权限
   ```

2. **网络连接问题**
   ```
   检查防火墙设置
   确认可以访问高德地图API服务
   验证DNS解析是否正常
   ```

3. **内存不足**
   ```
   增加容器内存限制
   检查是否存在内存泄漏
   调整缓存大小
   ```

4. **服务启动失败**
   ```bash
   # 检查日志
   docker logs gaode-mcp-server

   # 检查配置
   ./scripts/start.sh --check

   # 验证依赖
   pip list | grep mcp
   ```

### 调试模式

```bash
# 启用调试日志
export MCP_LOG_LEVEL=DEBUG
./scripts/start.sh

# 或在Docker中
docker run -e MCP_LOG_LEVEL=DEBUG gaode-mcp-server:latest
```

## 🔒 安全配置

### 1. API密钥安全

- 使用环境变量存储密钥
- 定期轮换API密钥
- 限制API密钥的权限范围

### 2. 网络安全

```yaml
# 网络策略示例
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: gaode-mcp-netpol
  namespace: gaode-mcp
spec:
  podSelector:
    matchLabels:
      app: gaode-mcp-server
  policyTypes:
  - Ingress
  - Egress
  ingress:
  - from: []
    ports:
    - protocol: TCP
      port: 8080
  egress:
  - to: []
    ports:
    - protocol: TCP
      port: 443
    - protocol: TCP
      port: 80
```

### 3. 访问控制

```env
# 限制允许的来源
MCP_ALLOWED_ORIGINS=["https://yourdomain.com"]
```

## 📈 扩展部署

### 水平扩展

```yaml
# 增加副本数
spec:
  replicas: 5
```

### 负载均衡

```yaml
# 使用LoadBalancer类型服务
apiVersion: v1
kind: Service
metadata:
  name: gaode-mcp-service
spec:
  type: LoadBalancer
  selector:
    app: gaode-mcp-server
  ports:
  - port: 80
    targetPort: 8080
```

### 自动扩缩容

```yaml
# HPA配置
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: gaode-mcp-hpa
  namespace: gaode-mcp
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: gaode-mcp-server
  minReplicas: 2
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
```

## 📞 支持和帮助

- 🐛 [提交Issue](https://github.com/athena-platform/amap-mcp-server/issues)
- 📧 邮件: xujian519@gmail.com
- 📖 [查看文档](https://github.com/athena-platform/amap-mcp-server/wiki)

---

🎉 **恭喜！** 你已成功部署高德地图MCP服务器。现在可以开始为AI模型提供强大的地理空间智能服务了！