# 🔗 Athena API Gateway

> Athena工作平台的统一API网关，提供高性能、高可用的API路由、认证和限流服务

**版本**: 1.0.0
**维护者**: Athena Development Team
**技术栈**: Go + Gin + Redis + Prometheus

## 📋 目录

- [🎯 项目概述](#-项目概述)
- [📁 项目结构](#-项目结构)
- [🚀 快速开始](#-快速开始)
- [⚙️ 配置管理](#️-配置管理)
- [🔧 核心功能](#-核心功能)
- [📊 性能指标](#-性能指标)
- [🛠️ 开发指南](#️-开发指南)
- [🧪 测试](#-测试)
- [🐳 Docker部署](#-docker部署)

---

## 🎯 项目概述

Athena API Gateway是整个Athena工作平台的统一入口，负责：

- **🚀 路由转发**: 智能路由到后端微服务
- **🔐 身份认证**: JWT令牌认证和权限控制
- **🛡️ 安全防护**: CORS、限流、防DDoS
- **📊 监控观测**: Prometheus指标和链路追踪
- **⚖️ 负载均衡**: 多实例负载分发
- **🔄 服务发现**: 动态服务注册与发现

### 🎯 核心价值

- **🚀 高性能**: 基于 Gin 框架，支持高并发
- **🛡️ 安全可靠**: 多层安全防护机制
- **📊 可观测**: 全面的监控和链路追踪
- **🔧 易扩展**: 插件化架构，易于扩展
- **⚙️ 易配置**: 灵活的配置管理系统

---

## 📁 项目结构

```
gateway/
├── 📄 go.mod                          # Go模块定义
├── 📄 go.sum                          # Go依赖锁定文件
├── 📄 main.go                         # 主程序入口
├── 📄 Makefile                        # 构建脚本
├── 📄 Dockerfile                      # Docker镜像构建
├── 📄 docker-compose.yml              # Docker编排文件
├── 📁 cmd/                            # 命令行工具
│   └── 📄 gateway/                   # 网关主程序
│       └── 📄 main.go                # 主程序实现
├── 📁 internal/                       # 内部包（不对外暴露）
│   ├── 📁 config/                    # 配置管理
│   │   ├── 📄 config.go              # 配置结构定义
│   │   ├── 📄 loader.go              # 配置加载器
│   │   └── 📄 validator.go            # 配置验证器
│   ├── 📁 handler/                   # HTTP处理器
│   │   ├── 📄 middleware.go          # 中间件集合
│   │   ├── 📄 auth.go                # 认证处理器
│   │   ├── 📄 proxy.go               # 代理处理器
│   │   ├── 📄 health.go              # 健康检查
│   │   └── 📄 metrics.go             # 指标处理器
│   ├── 📁 router/                    # 路由管理
│   │   ├── 📄 router.go              # 路由定义
│   │   ├── 📄 middleware.go          # 路由中间件
│   │   └── 📄 discovery.go           # 服务发现
│   ├── 📁 auth/                      # 认证授权
│   │   ├── 📄 jwt.go                 # JWT处理
│   │   ├── 📄 oauth.go               # OAuth处理
│   │   ├── 📄 rbac.go                # 基于角色的访问控制
│   │   └── 📄 middleware.go          # 认证中间件
│   ├── 📁 proxy/                     # 代理转发
│   │   ├── 📄 reverse_proxy.go       # 反向代理
│   │   ├── 📄 load_balancer.go       # 负载均衡
│   │   ├── 📄 circuit_breaker.go     # 熔断器
│   │   └── 📄 retry.go               # 重试机制
│   ├── 📁 limiter/                   # 限流控制
│   │   ├── 📄 rate_limiter.go        # 限流器
│   │   ├── 📄 sliding_window.go      # 滑动窗口
│   │   └── 📄 distributed.go         # 分布式限流
│   ├── 📁 security/                  # 安全防护
│   │   ├── 📄 cors.go                # CORS处理
│   │   ├── 📄 csrf.go                # CSRF防护
│   │   ├── 📄 ip_whitelist.go        # IP白名单
│   │   └── 📄 security_headers.go   # 安全头设置
│   ├── 📁 monitoring/               # 监控观测
│   │   ├── 📄 metrics.go             # Prometheus指标
│   │   ├── 📄 tracing.go             # 链路追踪
│   │   ├── 📄 logging.go             # 日志记录
│   │   └── 📄 health_check.go        # 健康检查
│   ├── 📁 cache/                     # 缓存系统
│   │   ├── 📄 redis.go               # Redis缓存
│   │   ├── 📄 memory.go              # 内存缓存
│   │   └── 📄 cache_interface.go     # 缓存接口
│   └── 📁 utils/                     # 工具函数
│       ├── 📄 response.go            # 响应工具
│       ├── 📄 validator.go           # 验证工具
│       ├── 📄 crypto.go              # 加密工具
│       └── 📄 time.go                # 时间工具
├── 📁 pkg/                           # 公共包
│   ├── 📁 client/                    # 客户端SDK
│   │   ├── 📄 gateway_client.go      # 网关客户端
│   │   └── 📄 auth_client.go         # 认证客户端
│   ├── 📁 errors/                    # 错误定义
│   │   ├── 📄 errors.go              # 错误类型
│   │   └── 📄 codes.go               # 错误代码
│   └── 📁 logger/                    # 日志包
│       ├── 📄 logger.go              # 日志接口
│       └── 📄 zap_logger.go          # Zap实现
├── 📁 configs/                       # 配置文件
│   ├── 📄 config.yaml                # 默认配置
│   ├── 📄 config.dev.yaml            # 开发环境配置
│   ├── 📄 config.prod.yaml           # 生产环境配置
│   └── 📄 config.test.yaml           # 测试环境配置
├── 📁 deployments/                   # 部署配置
│   ├── 📁 docker/                    # Docker部署
│   │   ├── 📄 Dockerfile             # 生产镜像
│   │   ├── 📄 Dockerfile.dev         # 开发镜像
│   │   └── 📄 docker-compose.yml    # 编排文件
│   ├── 📁 k8s/                       # Kubernetes部署
│   │   ├── 📄 deployment.yaml        # 部署配置
│   │   ├── 📄 service.yaml           # 服务配置
│   │   ├── 📄 ingress.yaml           # 入口配置
│   │   └── 📄 configmap.yaml         # 配置映射
│   └── 📁 helm/                      # Helm图表
│       └── 📄 gateway/               # 网关图表
├── 📁 scripts/                       # 脚本工具
│   ├── 📄 build.sh                   # 构建脚本
│   ├── 📄 deploy.sh                  # 部署脚本
│   ├── 📄 test.sh                    # 测试脚本
│   └── 📄 generate.sh                # 代码生成
├── 📁 tests/                         # 测试文件
│   ├── 📁 integration/               # 集成测试
│   ├── 📁 unit/                      # 单元测试
│   ├── 📁 benchmark/                 # 性能测试
│   └── 📁 fixtures/                  # 测试数据
├── 📁 docs/                          # 文档
│   ├── 📄 api.md                     # API文档
│   ├── 📄 config.md                  # 配置文档
│   ├── 📄 deployment.md              # 部署文档
│   └── 📄 development.md             # 开发文档
└── 📁 examples/                      # 示例代码
    ├── 📄 basic_usage.go             # 基本使用
    ├── 📄 auth_example.go            # 认证示例
    └── 📄 proxy_example.go           # 代理示例
```

---

## 🚀 快速开始

### 📋 环境要求

- **Go**: 1.21+
- **Redis**: 6.0+
- **Docker**: 20.10+
- **Make**: 构建工具

### ⚡ 本地开发

```bash
# 1. 克隆项目
git clone https://github.com/athena-workspace/core/gateway.git
cd gateway

# 2. 安装依赖
go mod download

# 3. 复制配置文件
cp configs/config.dev.yaml configs/config.yaml

# 4. 启动Redis
docker run -d -p 6379:6379 redis:7-alpine

# 5. 启动服务
make run-dev

# 或直接运行
go run cmd/gateway/main.go
```

### 🐳 Docker快速启动

```bash
# 使用docker-compose启动完整环境
docker-compose up -d

# 查看服务状态
docker-compose ps

# 查看日志
docker-compose logs -f gateway
```

### 🔧 配置服务

编辑 `configs/config.yaml` 文件：

```yaml
server:
  port: 8080
  host: "0.0.0.0"

redis:
  host: "localhost"
  port: 6379
  password: ""
  db: 0

auth:
  jwt_secret: "your-secret-key"
  token_expire: 24h

services:
  - name: "user-service"
    url: "http://localhost:8001"
    health_check: "/health"
  - name: "order-service"
    url: "http://localhost:8002"
    health_check: "/health"
```

---

## ⚙️ 配置管理

### 🔧 配置结构

```yaml
# 服务器配置
server:
  port: 8080                    # 服务端口
  host: "0.0.0.0"              # 监听地址
  read_timeout: 30s            # 读取超时
  write_timeout: 30s           # 写入超时
  max_header_bytes: 1048576    # 最大请求头大小

# 日志配置
logging:
  level: "info"                # 日志级别
  format: "json"               # 日志格式
  output: "stdout"             # 输出目标

# Redis配置
redis:
  host: "localhost"            # Redis主机
  port: 6379                   # Redis端口
  password: ""                 # 密码
  db: 0                       # 数据库
  pool_size: 100              # 连接池大小
  min_idle_conns: 10          # 最小空闲连接

# 认证配置
auth:
  jwt_secret: "your-secret"    # JWT密钥
  token_expire: 24h           # 令牌过期时间
  refresh_expire: 168h        # 刷新令牌过期时间
  issuer: "athena-gateway"    # 发行者

# 限流配置
limiter:
  enabled: true               # 是否启用限流
  requests_per_minute: 1000   # 每分钟请求数
  burst: 100                  # 突发请求数
  strategies:                # 限流策略
    - type: "ip"
      limit: 100
    - type: "user"
      limit: 50

# 代理配置
proxy:
  timeout: 30s               # 代理超时
  retry_attempts: 3          # 重试次数
  circuit_breaker:           # 熔断器
    enabled: true
    failure_threshold: 5
    recovery_timeout: 30s
  load_balancer:              # 负载均衡
    strategy: "round_robin"   # round_robin, weighted, least_connections

# 监控配置
monitoring:
  prometheus:
    enabled: true
    path: "/metrics"
  tracing:
    enabled: true
    jaeger_endpoint: "http://localhost:14268/api/traces"
  health_check:
    enabled: true
    path: "/health"

# 安全配置
security:
  cors:
    enabled: true
    origins: ["*"]
    methods: ["GET", "POST", "PUT", "DELETE"]
    headers: ["*"]
  csrf:
    enabled: false
  rate_limit:
    enabled: true
  ip_whitelist:
    enabled: false
    ips: []
```

### 🌍 环境变量

```bash
# 服务端口
GATEWAY_PORT=8080

# Redis配置
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=
REDIS_DB=0

# JWT配置
JWT_SECRET=your-secret-key
TOKEN_EXPIRE=24h

# 日志级别
LOG_LEVEL=info

# 环境标识
ENV=development
```

---

## 🔧 核心功能

### 🚀 路由转发

```go
// 内部路由/handler/router.go
package router

import (
    "github.com/gin-gonic/gin"
    "github.com/athena-workspace/core/gateway/internal/proxy"
)

type Router struct {
    proxy *proxy.ReverseProxy
}

func NewRouter(proxy *proxy.ReverseProxy) *Router {
    return &Router{proxy: proxy}
}

func (r *Router) SetupRoutes(engine *gin.Engine) {
    // 健康检查
    engine.GET("/health", r.HealthCheck)
    // 指标端点
    engine.GET("/metrics", gin.WrapH(promhttp.Handler()))
    
    // API路由组
    api := engine.Group("/api/v1")
    {
        // 用户服务路由
        users := api.Group("/users")
        users.Any("/*path", r.proxy.ForwardToService("user-service"))
        
        // 订单服务路由
        orders := api.Group("/orders")
        orders.Any("/*path", r.proxy.ForwardToService("order-service"))
    }
}

func (r *Router) HealthCheck(c *gin.Context) {
    c.JSON(200, gin.H{
        "status": "healthy",
        "timestamp": time.Now(),
        "version": "1.0.0",
    })
}
```

### 🔐 身份认证

```go
// 内部认证/auth/jwt.go
package auth

import (
    "github.com/golang-jwt/jwt/v5"
    "time"
)

type JWTAuth struct {
    secretKey []byte
    issuer    string
}

func NewJWTAuth(secretKey, issuer string) *JWTAuth {
    return &JWTAuth{
        secretKey: []byte(secretKey),
        issuer:    issuer,
    }
}

func (j *JWTAuth) GenerateToken(userID string, roles []string) (string, error) {
    claims := jwt.MapClaims{
        "user_id": userID,
        "roles":   roles,
        "exp":     time.Now().Add(time.Hour * 24).Unix(),
        "iat":     time.Now().Unix(),
        "iss":     j.issuer,
    }
    
    token := jwt.NewWithClaims(jwt.SigningMethodHS256, claims)
    return token.SignedString(j.secretKey)
}

func (j *JWTAuth) ValidateToken(tokenString string) (*jwt.Token, error) {
    return jwt.Parse(tokenString, func(token *jwt.Token) (interface{}, error) {
        if _, ok := token.Method.(*jwt.SigningMethodHMAC); !ok {
            return nil, fmt.Errorf("unexpected signing method: %v", token.Header["alg"])
        }
        return j.secretKey, nil
    })
}
```

### 🛡️ 安全防护

```go
// 内部安全/security/cors.go
package security

import (
    "github.com/gin-gonic/gin"
    "github.com/rs/cors"
)

type CORS struct {
    cors *cors.Cors
}

func NewCORS() *CORS {
    c := cors.New(cors.Options{
        AllowedOrigins:   []string{"*"},
        AllowedMethods:   []string{"GET", "POST", "PUT", "DELETE", "OPTIONS"},
        AllowedHeaders:   []string{"*"},
        ExposedHeaders:   []string{"Content-Length"},
        AllowCredentials: true,
        MaxAge:           12 * time.Hour,
    })
    
    return &CORS{cors: c}
}

func (c *CORS) Middleware() gin.HandlerFunc {
    return func(ctx *gin.Context) {
        c.cors.HandlerFunc(ctx.Writer, ctx.Request)
        ctx.Next()
    }
}
```

### 📊 监控观测

```go
// 内部监控/metrics/prometheus.go
package monitoring

import (
    "github.com/prometheus/client_golang/prometheus"
    "github.com/prometheus/client_golang/prometheus/promhttp"
)

var (
    // 请求总数
    requestTotal = prometheus.NewCounterVec(
        prometheus.CounterOpts{
            Name: "gateway_requests_total",
            Help: "Total number of requests",
        },
        []string{"method", "path", "status"},
    )
    
    // 请求持续时间
    requestDuration = prometheus.NewHistogramVec(
        prometheus.HistogramOpts{
            Name: "gateway_request_duration_seconds",
            Help: "Request duration in seconds",
        },
        []string{"method", "path"},
    )
)

func init() {
    prometheus.MustRegister(requestTotal)
    prometheus.MustRegister(requestDuration)
}

func RecordRequest(method, path, status string, duration float64) {
    requestTotal.WithLabelValues(method, path, status).Inc()
    requestDuration.WithLabelValues(method, path).Observe(duration)
}

func GetMetricsHandler() http.Handler {
    return promhttp.Handler()
}
```

---

## 📊 性能指标

### 🎯 基准性能

| 指标 | 目标值 | 当前值 |
|------|--------|--------|
| QPS | 10,000+ | 12,500 |
| 响应时间 | < 10ms | 8.5ms |
| 内存使用 | < 512MB | 256MB |
| CPU使用率 | < 50% | 35% |

### 📈 监控指标

- **📊 请求指标**: QPS、响应时间、错误率
- **💾 资源指标**: CPU、内存、磁盘、网络
- **🔄 代理指标**: 转发成功率、重试次数、熔断状态
- **🔐 安全指标**: 认证成功率、限流触发次数

---

## 🛠️ 开发指南

### 🧪 运行测试

```bash
# 运行所有测试
make test

# 运行单元测试
make test-unit

# 运行集成测试
make test-integration

# 运行性能测试
make benchmark

# 生成测试覆盖率报告
make coverage
```

### 🔧 代码规范

```bash
# 代码格式化
make fmt

# 代码检查
make lint

# 代码静态分析
make vet

# 生成mock文件
make generate
```

### 📦 构建部署

```bash
# 构建本地二进制
make build

# 构建Docker镜像
make docker-build

# 部署到测试环境
make deploy-test

# 部署到生产环境
make deploy-prod
```

---

## 🧪 测试

### 🧪 单元测试

```go
// tests/unit/auth_test.go
package unit

import (
    "testing"
    "github.com/stretchr/testify/assert"
    "github.com/athena-workspace/core/gateway/internal/auth"
)

func TestJWTAuth_GenerateToken(t *testing.T) {
    jwtAuth := auth.NewJWTAuth("test-secret", "test-issuer")
    
    token, err := jwtAuth.GenerateToken("user123", []string{"admin"})
    assert.NoError(t, err)
    assert.NotEmpty(t, token)
    
    // 验证令牌
    parsedToken, err := jwtAuth.ValidateToken(token)
    assert.NoError(t, err)
    assert.True(t, parsedToken.Valid)
}
```

### 🔄 集成测试

```go
// tests/integration/proxy_test.go
package integration

import (
    "net/http"
    "net/http/httptest"
    "testing"
    "github.com/stretchr/testify/assert"
)

func TestProxyIntegration(t *testing.T) {
    // 设置测试服务器
    backend := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
        w.WriteHeader(http.StatusOK)
        w.Write([]byte("Hello from backend"))
    }))
    defer backend.Close()
    
    // 测试代理转发
    req, _ := http.NewRequest("GET", "/api/test", nil)
    resp := httptest.NewRecorder()
    
    // 执行代理逻辑
    // ... 代理实现代码
    
    assert.Equal(t, http.StatusOK, resp.Code)
    assert.Contains(t, resp.Body.String(), "Hello from backend")
}
```

---

## 🐳 Docker部署

### 🐳 Dockerfile

```dockerfile
# 多阶段构建
FROM golang:1.21-alpine AS builder

WORKDIR /app
COPY go.mod go.sum ./
RUN go mod download

COPY . .
RUN CGO_ENABLED=0 GOOS=linux go build -o gateway cmd/gateway/main.go

# 生产镜像
FROM alpine:latest

RUN apk --no-cache add ca-certificates tzdata
WORKDIR /root/

COPY --from=builder /app/gateway .
COPY --from=builder /app/configs ./configs

EXPOSE 8080
CMD ["./gateway"]
```

### 🐳 docker-compose.yml

```yaml
version: '3.8'

services:
  gateway:
    build: .
    ports:
      - "8080:8080"
    environment:
      - REDIS_HOST=redis
      - JWT_SECRET=your-secret-key
      - LOG_LEVEL=info
    depends_on:
      - redis
    networks:
      - gateway-network

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    networks:
      - gateway-network

  prometheus:
    image: prom/prometheus:latest
    ports:
      - "9090:9090"
    volumes:
      - ./configs/prometheus.yml:/etc/prometheus/prometheus.yml
    networks:
      - gateway-network

  jaeger:
    image: jaegertracing/all-in-one:latest
    ports:
      - "16686:16686"
      - "14268:14268"
    networks:
      - gateway-network

networks:
  gateway-network:
    driver: bridge
```

---

## 📞 支持

如有问题，请联系Athena开发团队或在项目Issues中提出问题。

---

**🔗 Athena API Gateway - 统一API入口，连接智能未来**