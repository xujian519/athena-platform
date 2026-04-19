# Athena API Gateway 服务发现系统

> **完整的企业级服务发现和负载均衡解决方案**
> 
> 支持多协议、智能路由、健康检查和插件扩展的分布式服务发现系统

---

## 🎯 系统概述

Athena服务发现系统是为Athena API Gateway设计的全面服务发现解决方案，提供高性能、高可用的服务注册、发现和负载均衡功能。该系统采用现代微服务架构设计，支持HTTP、gRPC、GraphQL等多种协议，并提供丰富的插件扩展机制。

### 核心特性

- ✅ **服务注册与发现** - 自动服务注册和动态发现
- ✅ **智能健康检查** - 多协议健康检查和故障检测
- ✅ **高级负载均衡** - 8种负载均衡算法，自适应选择
- ✅ **多协议支持** - HTTP/gRPC/GraphQL统一支持
- ✅ **插件化架构** - 可扩展的插件系统
- ✅ **高可用设计** - 集群部署，无单点故障
- ✅ **实时监控** - 完整的指标收集和监控
- ✅ **动态配置** - 热更新和配置管理

---

## 📁 项目结构

```
services/api-gateway/src/service_discovery/
├── __init__.py                   # 统一入口和API服务
├── core_service_registry.py       # 核心服务注册中心
├── health_check.py               # 健康检查系统
├── load_balancing.py             # 负载均衡算法
├── plugin_integration.py         # 插件系统集成
└── README.md                   # 本文档

config/service_discovery.json       # 服务发现配置文件
docs/plans/                     # 架构设计文档
```

---

## 🚀 快速开始

### 1. 环境要求

- **Python**: 3.8+
- **Redis**: 6.0+ (用于服务注册存储)
- **PostgreSQL**: 13+ (可选，用于持久化存储)
- **Docker**: 20.10+ (可选，用于容器化部署)

### 2. 安装依赖

```bash
# 进入API Gateway目录
cd services/api-gateway

# 安装Python依赖
pip install -r requirements.txt

# 或使用poetry
poetry install
```

### 3. 配置系统

```bash
# 复制配置文件模板
cp config/service_discovery.json.example config/service_discovery.json

# 编辑配置
vim config/service_discovery.json
```

### 4. 启动服务

```bash
# 启动服务发现系统
python src/service_discovery/__init__.py

# 或使用模块方式
python -m service_discovery
```

服务将在 `http://localhost:8080` 启动

---

## 📋 API 接口

### 核心API端点

| 方法 | 端点 | 描述 |
|------|--------|------|
| GET | `/health` | 健康检查 |
| GET | `/status` | 系统状态 |
| GET | `/services/{service_name}/discover` | 发现服务 |
| POST | `/services/{service_name}/route` | 路由请求 |
| POST | `/services/register` | 注册服务 |
| DELETE | `/services/{service_id}` | 注销服务 |

### 服务注册示例

```bash
curl -X POST http://localhost:8080/services/register \
  -H "Content-Type: application/json" \
  -d '{
    "service_id": "user-service-1",
    "service_name": "user-service",
    "host": "localhost",
    "port": 9001,
    "protocol": "http",
    "health_check_url": "/health",
    "weight": 100,
    "tags": ["api", "user"],
    "metadata": {
      "version": "1.0.0",
      "region": "us-east-1"
    }
  }'
```

### 服务发现示例

```bash
curl http://localhost:8080/services/user-service/discover \
  -H "Accept: application/json"
```

响应示例：
```json
{
  "service_name": "user-service",
  "namespace": "default",
  "instances": [
    {
      "service_id": "user-service-1",
      "service_name": "user-service",
      "host": "localhost",
      "port": 9001,
      "protocol": "http",
      "health_status": "healthy",
      "weight": 100,
      "tags": ["api", "user"],
      "registration_time": "2026-02-20T04:00:00Z"
    }
  ],
  "count": 1
}
```

---

## ⚖️ 负载均衡算法

### 支持的算法

1. **轮询 (Round Robin)** - 依次轮询分发请求
2. **加权轮询 (Weighted Round Robin)** - 根据权重分配请求
3. **最少连接 (Least Connections)** - 选择连接数最少的实例
4. **响应时间优先 (Response Time Based)** - 选择响应时间最快的实例
5. **一致性哈希 (Consistent Hash)** - 基于请求特征的哈希分发
6. **随机 (Random)** - 随机选择实例
7. **IP哈希 (IP Hash)** - 基于客户端IP哈希分发
8. **公平调度 (Fair)** - 确保请求分配公平
9. **自适应 (Adaptive)** - 自动选择最优算法

### 算法配置示例

```json
{
  "load_balancing": {
    "default_algorithm": "response_time_based",
    "adaptive_enabled": true,
    "evaluation_interval": 60,
    "algorithms": {
      "user-service": "weighted_round_robin",
      "order-service": "least_connections",
      "payment-service": "adaptive"
    }
  }
}
```

---

## 🔍 健康检查系统

### 支持的检查类型

- **HTTP/HTTPS检查** - 基于HTTP状态码检查
- **TCP连接检查** - 检查TCP端口连通性
- **gRPC健康检查** - 使用标准gRPC健康检查协议
- **GraphQL健康检查** - 通过GraphQL introspection查询检查
- **脚本检查** - 执行自定义健康检查脚本

### 健康检查配置

```json
{
  "health_check": {
    "default_interval": 30,
    "default_timeout": 5,
    "failure_threshold": 3,
    "success_threshold": 2,
    "deregister_after": 300,
    "checks": {
      "user-service": {
        "enabled": true,
        "type": "http",
        "path": "/health",
        "expected_codes": [200, 201],
        "headers": {
          "User-Agent": "Athena-Health-Check/1.0"
        }
      }
    }
  }
}
```

### 健康状态

- **HEALTHY** - 服务健康可用
- **UNHEALTHY** - 服务不可用
- **DEGRADED** - 服务降级可用
- **UNKNOWN** - 状态未知
- **MAINTENANCE** - 维护模式

---

## 🔌 插件系统

### 内置插件

1. **MCP服务发现插件** - 自动发现和管理MCP服务
2. **Kubernetes服务发现插件** - 监听K8s服务变化

### 插件配置

```json
{
  "plugins": {
    "mcp": {
      "type": "mcp",
      "enabled": true,
      "priority": 1,
      "config": {
        "mcp_config_path": "config/athena_mcp_config.json",
        "auto_discover": true
      }
    },
    "kubernetes": {
      "type": "kubernetes",
      "enabled": false,
      "config": {
        "namespace": "athena",
        "label_selector": "athena-service-discovery=enabled"
      }
    }
  }
}
```

### 自定义插件开发

```python
from service_discovery.plugin_integration import ServiceDiscoveryPlugin

class CustomDiscoveryPlugin(ServiceDiscoveryPlugin):
    @property
    def name(self) -> str:
        return "custom-discovery"
    
    @property 
    def version(self) -> str:
        return "1.0.0"
    
    async def initialize(self, config: Dict) -> bool:
        # 初始化插件
        return True
    
    async def on_service_register(self, instance: ServiceInstance) -> None:
        # 服务注册回调
        pass
```

---

## 🗄️ 存储后端

### Redis存储 (推荐)

```json
{
  "registry": {
    "storage": {
      "type": "redis",
      "redis_url": "redis://localhost:6379",
      "key_prefix": "athena:service_discovery:",
      "ttl": 3600
    }
  }
}
```

### PostgreSQL存储 (可选)

```json
{
  "registry": {
    "storage": {
      "type": "postgresql",
      "connection_string": "postgresql://user:pass@localhost/athena",
      "pool_size": 20,
      "max_overflow": 30
    }
  }
}
```

---

## 📊 监控与指标

### 内置指标

- **服务注册数量** - 当前注册的服务总数
- **健康检查统计** - 成功/失败率
- **请求响应时间** - 平均和P95响应时间
- **负载均衡指标** - 各算法使用情况
- **插件状态** - 插件运行状态

### Prometheus集成

```bash
# 访问指标端点
curl http://localhost:8080/metrics

# Prometheus配置示例
scrape_configs:
  - job_name: 'athena-service-discovery'
    static_configs:
      - targets: ['localhost:8080']
    metrics_path: '/metrics'
```

### 日志格式

```json
{
  "timestamp": "2026-02-20T04:00:00Z",
  "level": "info",
  "component": "service_discovery",
  "message": "Service registered successfully",
  "service_id": "user-service-1",
  "service_name": "user-service"
}
```

---

## 🐳 部署方案

### Docker部署

```bash
# 构建镜像
docker build -t athena/service-discovery:v2.0 .

# 运行容器
docker run -d \
  --name athena-service-discovery \
  -p 8080:8080 \
  -e REDIS_URL=redis://redis:6379 \
  -v $(pwd)/config:/app/config \
  athena/service-discovery:v2.0
```

### Docker Compose部署

```yaml
version: '3.8'

services:
  service-discovery:
    build: .
    ports:
      - "8080:8080"
    environment:
      - REDIS_URL=redis://redis:6379
      - LOG_LEVEL=INFO
    volumes:
      - ./config:/app/config
      - ./logs:/app/logs
    depends_on:
      - redis
    restart: unless-stopped

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    restart: unless-stopped

volumes:
  redis_data:
```

### Kubernetes部署

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: athena-service-discovery
  namespace: athena
spec:
  replicas: 3
  selector:
    matchLabels:
      app: athena-service-discovery
  template:
    metadata:
      labels:
        app: athena-service-discovery
        athena-service-discovery: enabled
    spec:
      containers:
      - name: service-discovery
        image: athena/service-discovery:v2.0
        ports:
        - containerPort: 8080
        env:
        - name: REDIS_URL
          value: "redis://redis-service:6379"
        resources:
          requests:
            memory: "512Mi"
            cpu: "250m"
          limits:
            memory: "1Gi"
            cpu: "500m"
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

---
apiVersion: v1
kind: Service
metadata:
  name: athena-service-discovery
  namespace: athena
spec:
  selector:
    app: athena-service-discovery
  ports:
  - name: http
    port: 8080
    targetPort: 8080
  type: ClusterIP
```

---

## 🔧 配置详解

### 完整配置示例

详见 `config/service_discovery.json` 文件，包含以下配置段：

- **registry** - 服务注册中心配置
- **health_check** - 健康检查配置
- **load_balancing** - 负载均衡配置
- **api** - API服务配置
- **plugins** - 插件配置
- **monitoring** - 监控配置
- **security** - 安全配置

### 环境变量

| 变量名 | 默认值 | 描述 |
|---------|---------|------|
| `REDIS_URL` | `redis://localhost:6379` | Redis连接地址 |
| `LOG_LEVEL` | `INFO` | 日志级别 |
| `API_HOST` | `0.0.0.0` | API服务监听地址 |
| `API_PORT` | `8080` | API服务端口 |
| `NODE_ENV` | `development` | 运行环境 |

---

## 🧪 测试

### 运行测试

```bash
# 进入测试目录
cd tests

# 运行所有测试
python -m pytest tests/ -v

# 运行特定测试
python -m pytest tests/test_service_registry.py -v

# 生成覆盖率报告
python -m pytest tests/ --cov=service_discovery --cov-report=html
```

### 集成测试

```bash
# 启动测试环境
docker-compose -f docker-compose.test.yml up -d

# 运行集成测试
python tests/integration/test_api.py

# 清理环境
docker-compose -f docker-compose.test.yml down
```

---

## 🔍 故障排除

### 常见问题

1. **Redis连接失败**
   ```bash
   # 检查Redis是否运行
   redis-cli ping
   
   # 检查网络连通性
   telnet localhost 6379
   ```

2. **服务注册失败**
   ```bash
   # 检查配置文件
   cat config/service_discovery.json | jq .
   
   # 查看服务日志
   docker logs athena-service-discovery
   ```

3. **健康检查不工作**
   ```bash
   # 手动检查健康端点
   curl http://localhost:8080/health
   
   # 查看健康检查配置
   curl http://localhost:8080/services/{service_name}/health
   ```

### 调试模式

```bash
# 启用调试日志
export LOG_LEVEL=DEBUG
python src/service_discovery/__init__.py

# 或在配置中设置
{
  "monitoring": {
    "logging": {
      "level": "DEBUG"
    }
  }
}
```

---

## 📈 性能优化

### 推荐配置

1. **Redis优化**
   - 启用持久化
   - 配置合适的内存策略
   - 使用集群模式

2. **健康检查优化**
   - 调整检查间隔
   - 使用批量检查
   - 配置合适的超时时间

3. **负载均衡优化**
   - 启用自适应算法
   - 配置指标保留期
   - 使用一致性哈希减少缓存失效

### 性能指标

| 指标 | 目标值 | 说明 |
|------|---------|------|
| 服务发现延迟 | < 50ms | 95%分位数的响应时间 |
| 健康检查频率 | 30-60秒 | 平衡及时性和资源消耗 |
| 负载均衡决策时间 | < 1ms | 选择实例的耗时 |
| 内存使用 | < 512MB | 常驻内存占用 |

---

## 🤝 贡献指南

### 开发环境设置

```bash
# 克隆项目
git clone https://github.com/athena/service-discovery.git
cd service-discovery

# 创建虚拟环境
python -m venv venv
source venv/bin/activate

# 安装依赖
pip install -r requirements-dev.txt

# 安装pre-commit钩子
pre-commit install
```

### 代码规范

- 使用Black进行代码格式化
- 使用flake8进行代码检查
- 使用mypy进行类型检查
- 编写单元测试和文档

### 提交流程

```bash
# 创建功能分支
git checkout -b feature/your-feature-name

# 提交变更
git add .
git commit -m "feat: add new feature"

# 推送分支
git push origin feature/your-feature-name

# 创建Pull Request
```

---

## 📄 许可证

本项目采用MIT许可证，详见[LICENSE](LICENSE)文件。

---

## 📞 支持与联系

- **文档**: https://docs.athena.com/service-discovery
- **问题反馈**: https://github.com/athena/service-discovery/issues
- **讨论**: https://github.com/athena/service-discovery/discussions
- **邮件**: athena@example.com

---

**🌟 如果这个项目对您有帮助，请给我们一个星标！**

---

*Athena Service Discovery v2.0 - 让服务发现变得简单高效*