# Athena Gateway统一标准

**版本**: v1.0
**创建时间**: 2026-02-20
**基于**: api-gateway/
**目标**: 建立统一的Gateway架构、API和代码标准

---

## 🏗️ 架构标准

### 分层架构

```
┌──────────────────────────────────────────────────────┐
│                   API层                              │
│  ┌──────────────┐  ┌──────────────┐  ┌───────────┐  │
│  │  REST API    │  │  GraphQL     │  │ gRPC      │  │
│  └──────────────┘  └──────────────┘  └───────────┘  │
├──────────────────────────────────────────────────────┤
│                   Gateway层                          │
│  ┌────────────────────────────────────────────────┐  │
│  │  Athena Gateway (统一实现)                     │  │
│  │  - 路由管理    - 服务发现                       │  │
│  │  - 负载均衡    - 认证授权                       │  │
│  │  - 限流熔断    - 缓存加速                       │  │
│  └────────────────────────────────────────────────┘  │
├──────────────────────────────────────────────────────┤
│                   中间件层                           │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌────────┐  │
│  │ 认证     │ │ 限流     │ │ 监控     │ │ 追踪   │  │
│  └──────────┘ └──────────┘ └──────────┘ └────────┘  │
├──────────────────────────────────────────────────────┤
│                   服务层                             │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌────────┐  │
│  │ 小娜     │ │ 小诺     │ │ 云熙     │ │ 其他   │  │
│  │ (Legal)  │ │(Coord)   │ │  (IP)    │ │ 服务   │  │
│  └──────────┘ └──────────┘ └──────────┘ └────────┘  │
├──────────────────────────────────────────────────────┤
│                   基础设施层                          │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌────────┐  │
│  │ PostgreSQL│ │ Redis    │ │ Qdrant   │ │ Neo4j  │  │
│  └──────────┘ └──────────┘ └──────────┘ └────────┘  │
└──────────────────────────────────────────────────────┘
```

### 模块划分

```
gateway-unified/
├── cmd/                          # 应用入口
│   └── gateway/
│       └── main.go               # 主程序入口
├── internal/                     # 内部实现
│   ├── auth/                     # 认证授权
│   │   ├── jwt.go               # JWT管理
│   │   ├── middleware.go         # 认证中间件
│   │   └── models.go             # 认证模型
│   ├── cache/                    # 缓存管理
│   │   ├── multilevel.go         # 多级缓存
│   │   ├── redis.go              # Redis缓存
│   │   └── memory.go             # 内存缓存
│   ├── config/                   # 配置管理
│   │   ├── config.go             # 配置结构
│   │   └── loader.go             # 配置加载
│   ├── discovery/                # 服务发现
│   │   ├── registry.go           # 服务注册
│   │   ├── selector.go           # 实例选择
│   │   └── health.go             # 健康检查
│   ├── gateway/                  # 网关核心
│   │   ├── gateway.go            # 网关实现
│   │   ├── router.go             # 路由管理
│   │   └── proxy.go              # 请求代理
│   ├── handlers/                 # HTTP处理器
│   │   ├── health.go             # 健康检查
│   │   ├── metrics.go            # 指标采集
│   │   └── admin.go              # 管理接口
│   ├── middleware/               # 中间件
│   │   ├── cors.go               # CORS处理
│   │   ├── ratelimit.go          # 限流
│   │   ├── metrics.go            # 指标收集中间件
│   │   ├── tracing.go            # 追踪中间件
│   │   └── recovery.go           # 恢复中间件
│   ├── monitoring/               # 监控
│   │   ├── prometheus.go         # Prometheus集成
│   │   ├── tracing.go            # 分布式追踪
│   │   └── logger.go             # 结构化日志
│   ├── pool/                     # 连接池
│   │   ├── database.go           # 数据库连接池
│   │   └── http.go               # HTTP客户端池
│   └── router/                   # 路由
│       ├── router.go             # 路由定义
│       └── group.go              # 路由组
├── pkg/                          # 公共包
│   ├── response/                 # 响应封装
│   │   └── response.go           # 统一响应格式
│   ├── errors/                   # 错误处理
│   │   └── errors.go             # 错误定义
│   └── utils/                    # 工具函数
│       └── utils.go              # 通用工具
├── configs/                      # 配置文件
│   ├── config.yaml               # 默认配置
│   ├── config.dev.yaml           # 开发配置
│   └── config.prod.yaml          # 生产配置
├── deployments/                  # 部署配置
│   ├── docker/                   # Docker配置
│   │   ├── Dockerfile            # Docker镜像
│   │   └── docker-compose.yml    # Compose配置
│   └── k8s/                      # Kubernetes配置
│       ├── deployment.yaml       # 部署配置
│       ├── service.yaml           # 服务配置
│       └── ingress.yaml          # Ingress配置
├── scripts/                      # 脚本工具
│   ├── build.sh                  # 构建脚本
│   ├── test.sh                   # 测试脚本
│   └── deploy.sh                 # 部署脚本
├── tests/                        # 测试
│   ├── unit/                     # 单元测试
│   ├── integration/              # 集成测试
│   └── performance/              # 性能测试
├── docs/                         # 文档
│   ├── api.md                    # API文档
│   ├── architecture.md           # 架构文档
│   └── deployment.md             # 部署文档
├── go.mod                        # Go模块定义
├── go.sum                        # Go依赖锁定
├── Makefile                      # 构建配置
└── README.md                     # 项目说明
```

---

## 🔌 API标准

### 1. 服务注册API

#### 批量注册服务
```http
POST /api/v1/services/batch
Content-Type: application/json

{
  "services": [
    {
      "name": "xiaona-service",
      "host": "localhost",
      "port": 8001,
      "protocol": "http",
      "health_endpoint": "/health",
      "metadata": {
        "version": "1.0.0",
        "tags": ["legal", "patent"]
      }
    }
  ]
}

Response 200:
{
  "success": true,
  "data": [
    {
      "id": "xiaona-service:localhost:8001:1",
      "service_name": "xiaona-service",
      "host": "localhost",
      "port": 8001,
      "status": "UP",
      "created_at": "2026-02-20T14:00:00Z"
    }
  ]
}
```

#### 查询服务实例
```http
GET /api/v1/services/instances?service=xiaona-service

Response 200:
{
  "success": true,
  "data": [
    {
      "id": "xiaona-service:localhost:8001:1",
      "service_name": "xiaona-service",
      "host": "localhost",
      "port": 8001,
      "weight": 1,
      "status": "UP"
    }
  ]
}
```

### 2. 路由管理API

#### 创建路由
```http
POST /api/v1/routes
Content-Type: application/json

{
  "id": "xiaona-patents",
  "path": "/api/patents/*",
  "target_service": "xiaona-service",
  "methods": ["GET", "POST", "PUT", "DELETE"],
  "strip_prefix": true,
  "timeout": 30,
  "retries": 3,
  "auth_required": true,
  "rate_limit": {
    "requests_per_minute": 100,
    "burst": 20
  }
}
```

#### 查询路由
```http
GET /api/v1/routes

Response 200:
{
  "success": true,
  "data": [
    {
      "id": "xiaona-patents",
      "path": "/api/patents/*",
      "target_service": "xiaona-service",
      "methods": ["GET", "POST", "PUT", "DELETE"]
    }
  ]
}
```

### 3. 健康检查API

```http
GET /health

Response 200:
{
  "status": "UP",
  "timestamp": "2026-02-20T14:00:00Z",
  "components": {
    "server": "UP",
    "database": "UP",
    "redis": "UP",
    "services": {
      "xiaona-service": "UP",
      "xiaonuo-service": "UP"
    }
  }
}
```

### 4. 监控指标API

```http
GET /metrics

# Prometheus格式
# HELP gateway_requests_total Total number of requests
# TYPE gateway_requests_total counter
gateway_requests_total{method="GET",path="/api/patents",status="200"} 1234

# HELP gateway_request_duration_seconds Request duration in seconds
# TYPE gateway_request_duration_seconds histogram
gateway_request_duration_seconds_bucket{le="0.1"} 1000
gateway_request_duration_seconds_bucket{le="0.5"} 1500
gateway_request_duration_seconds_bucket{le="1.0"} 1800
gateway_request_duration_seconds_bucket{le="+Inf"} 2000
```

---

## 📝 代码规范

### 命名规范

| 类型 | 规范 | 示例 |
|------|------|------|
| 包名 | 小写单词 | `gateway`, `auth`, `cache` |
| 接口 | 动词+名词 | `ServiceRegistry`, `HealthChecker` |
| 结构体 | 名词短语 | `ServiceInstance`, `RouteConfig` |
| 常量 | 大驼峰 | `DefaultTimeout`, `MaxRetries` |
| 变量 | 小驼峰 | `serviceName`, `healthCheck` |
| 私有成员 | 小写开头 | `cache`, `httpClient` |

### 错误处理

```go
// 定义错误
var (
    ErrServiceNotFound = errors.New("service not found")
    ErrInvalidConfig  = errors.New("invalid configuration")
    ErrHealthCheck    = errors.New("health check failed")
)

// 错误包装
if err := loadConfig(configPath); err != nil {
    return fmt.Errorf("failed to load config: %w", err)
}

// 错误断言
if errors.Is(err, ErrServiceNotFound) {
    // 处理服务未找到
}
```

### 日志规范

```go
// 结构化日志
logger.Info("Service registered",
    zap.String("service_name", serviceName),
    zap.String("host", host),
    zap.Int("port", port),
)

// 错误日志
logger.Error("Failed to register service",
    zap.String("service_name", serviceName),
    zap.Error(err),
)

// 调试日志
logger.Debug("Processing request",
    zap.String("method", r.Method),
    zap.String("path", r.URL.Path),
)
```

### 并发安全

```go
// 使用mutex保护共享状态
type ServiceRegistry struct {
    mu       sync.RWMutex
    services map[string]*ServiceInstance
}

func (r *ServiceRegistry) Get(name string) (*ServiceInstance, bool) {
    r.mu.RLock()
    defer r.mu.RUnlock()
    svc, ok := r.services[name]
    return svc, ok
}

// 使用channel进行通信
type Gateway struct {
    requestCh chan *Request
    stopCh    chan struct{}
}

func (g *Gateway) Run() {
    for {
        select {
        case req := <-g.requestCh:
            g.processRequest(req)
        case <-g.stopCh:
            return
        }
    }
}
```

---

## 🧪 测试标准

### 单元测试

```go
func TestServiceRegistry_Register(t *testing.T) {
    // Arrange
    registry := NewServiceRegistry()
    service := &ServiceInstance{
        ServiceName: "test-service",
        Host:        "localhost",
        Port:        8080,
    }

    // Act
    err := registry.Register(service)

    // Assert
    assert.NoError(t, err)
    retrieved, ok := registry.Get("test-service")
    assert.True(t, ok)
    assert.Equal(t, service.Host, retrieved.Host)
}
```

### 集成测试

```go
func TestGateway_E2E(t *testing.T) {
    // 启动测试网关
    gw := startTestGateway(t)
    defer gw.Stop()

    // 注册测试服务
    testServer := startTestServer(t)
    defer testServer.Stop()

    // 发送请求
    resp := makeRequest(t, gw.URL+"/api/test")

    // 验证响应
    assert.Equal(t, 200, resp.StatusCode)
}
```

### 基准测试

```go
func BenchmarkGateway_Route(b *testing.B) {
    gw := setupBenchmarkGateway()
    req := httptest.NewRequest("GET", "/api/test", nil)

    b.ResetTimer()
    for i := 0; i < b.N; i++ {
        w := httptest.NewRecorder()
        gw.ServeHTTP(w, req)
    }
}
```

---

## 📊 性能标准

### 目标指标

| 指标 | 目标值 | 测量方法 |
|------|--------|----------|
| 响应时间 (P50) | <10ms | Prometheus histogram |
| 响应时间 (P95) | <50ms | Prometheus histogram |
| 响应时间 (P99) | <100ms | Prometheus histogram |
| 吞吐量 | >10k QPS | 压力测试 |
| 错误率 | <0.1% | Prometheus counter |
| 可用性 | >99.5% | 健康检查 |
| 内存使用 | <512MB | 容器监控 |
| CPU使用 | <70% | 容器监控 |

### 性能优化原则

1. **连接池复用**: 数据库和HTTP客户端必须使用连接池
2. **缓存优先**: 热数据必须缓存（内存、Redis）
3. **异步处理**: 非关键路径异步处理
4. **批量操作**: 支持批量请求减少网络开销
5. **压缩传输**: 大数据传输必须压缩

---

## 🔒 安全标准

### 认证

```go
// JWT认证中间件
func AuthMiddleware(jwtManager *JWTManager) gin.HandlerFunc {
    return func(c *gin.Context) {
        token := extractToken(c)
        claims, err := jwtManager.Validate(token)
        if err != nil {
            c.AbortWithStatusJSON(401, gin.H{"error": "Unauthorized"})
            return
        }
        c.Set("claims", claims)
        c.Next()
    }
}
```

### 限流

```go
// 限流中间件
func RateLimitMiddleware(limiter *RateLimiter) gin.HandlerFunc {
    return func(c *gin.Context) {
        clientIP := c.ClientIP()
        if !limiter.Allow(clientIP) {
            c.AbortWithStatusJSON(429, gin.H{
                "error": "Too many requests",
            })
            return
        }
        c.Next()
    }
}
```

### CORS

```go
// CORS配置
func CORSMiddleware() gin.HandlerFunc {
    return cors.New(cors.Config{
        AllowOrigins:     []string{"http://localhost:3000"},
        AllowMethods:     []string{"GET", "POST", "PUT", "DELETE"},
        AllowHeaders:     []string{"Origin", "Content-Type", "Authorization"},
        ExposeHeaders:    []string{"Content-Length"},
        AllowCredentials: true,
        MaxAge:           12 * time.Hour,
    })
}
```

---

## 📈 监控标准

### Prometheus指标

```go
// 请求总数
var requestTotal = prometheus.NewCounterVec(
    prometheus.CounterOpts{
        Name: "gateway_requests_total",
        Help: "Total number of requests",
    },
    []string{"method", "path", "status"},
)

// 请求延迟
var requestDuration = prometheus.NewHistogramVec(
    prometheus.HistogramOpts{
        Name:    "gateway_request_duration_seconds",
        Help:    "Request duration in seconds",
        Buckets: prometheus.DefBuckets,
    },
    []string{"method", "path"},
)

// 服务健康状态
var serviceHealth = prometheus.NewGaugeVec(
    prometheus.GaugeOpts{
        Name: "gateway_service_health",
        Help: "Service health status (1=UP, 0=DOWN)",
    },
    []string{"service_name"},
)
```

### 分布式追踪

```go
// 追踪中间件
func TracingMiddleware(serviceName string) gin.HandlerFunc {
    return func(c *gin.Context) {
        tracer := otel.Tracer("gateway")
        ctx, span := tracer.Start(
            c.Request.Context(),
            c.Request.URL.Path,
            trace.WithAttributes(
                attribute.String("http.method", c.Request.Method),
                attribute.String("http.url", c.Request.URL.String()),
            ),
        )
        defer span.End()

        c.Request = c.Request.WithContext(ctx)
        c.Next()
    }
}
```

---

## 🚀 部署标准

### Docker镜像

```dockerfile
# 多阶段构建
FROM golang:1.21-alpine AS builder
WORKDIR /app
COPY go.mod go.sum ./
RUN go mod download
COPY . .
RUN CGO_ENABLED=0 go build -o gateway cmd/gateway/main.go

FROM alpine:latest
RUN apk --no-cache add ca-certificates
WORKDIR /root/
COPY --from=builder /app/gateway .
COPY configs/config.yaml ./configs/
EXPOSE 8080
CMD ["./gateway"]
```

### Kubernetes部署

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: athena-gateway
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
      - name: gateway
        image: athena-gateway:latest
        ports:
        - containerPort: 8080
        env:
        - name: CONFIG_PATH
          value: "/app/configs/config.prod.yaml"
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
          initialDelaySeconds: 10
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /ready
            port: 8080
          initialDelaySeconds: 5
          periodSeconds: 5
---
apiVersion: v1
kind: Service
metadata:
  name: athena-gateway
spec:
  selector:
    app: athena-gateway
  ports:
  - protocol: TCP
    port: 8080
    targetPort: 8080
  type: LoadBalancer
```

---

## 📚 文档标准

### API文档

使用Swagger/OpenAPI 3.0规范：
```yaml
openapi: 3.0.0
info:
  title: Athena Gateway API
  version: 1.0.0
  description: Athena工作平台统一API网关
paths:
  /api/v1/services:
    post:
      summary: 注册服务
      requestBody:
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/ServiceRegistration'
      responses:
        '200':
          description: 注册成功
```

### 架构文档

必须包含：
- 系统架构图
- 模块职责说明
- 数据流图
- 部署架构

### 运维文档

必须包含：
- 部署步骤
- 配置说明
- 监控指标
- 故障排查
- 应急预案

---

## ✅ 验收标准

### 功能验收

- [ ] 服务注册和发现
- [ ] 动态路由管理
- [ ] 负载均衡（轮询、随机、权重）
- [ ] 健康检查和自动摘除
- [ ] JWT认证
- [ ] 限流保护
- [ ] 缓存加速
- [ ] 请求追踪
- [ ] 指标采集
- [ ] 优雅关闭

### 性能验收

- [ ] P50响应时间 <10ms
- [ ] P95响应时间 <50ms
- [ ] P99响应时间 <100ms
- [ ] 吞吐量 >10k QPS
- [ ] 错误率 <0.1%
- [ ] 内存使用 <512MB
- [ ] CPU使用 <70%

### 质量验收

- [ ] 单元测试覆盖率 >80%
- [ ] 集成测试通过
- [ ] 性能基准测试通过
- [ ] 安全扫描无高危漏洞
- [ ] 文档完整

---

**版本历史**:
- v1.0 (2026-02-20): 初始版本，建立Gateway统一标准

**维护者**: Athena团队
**最后更新**: 2026-02-20
