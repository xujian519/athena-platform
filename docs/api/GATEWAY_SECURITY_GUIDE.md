# Gateway安全功能使用指南

> 最后更新: 2026-04-20

---

## 目录

- [概述](#概述)
- [JWT认证](#jwt认证)
- [速率限制](#速率限制)
- [CORS配置](#cors配置)
- [IP白名单](#ip白名单)
- [API密钥认证](#api密钥认证)
- [安全响应头](#安全响应头)
- [配置示例](#配置示例)

---

## 概述

Athena Gateway提供完整的安全功能套件，包括：

- **JWT认证**: 基于JSON Web Token的用户认证
- **速率限制**: 防止API滥用和DDoS攻击
- **CORS**: 跨域资源共享控制
- **IP白名单**: 基于IP地址的访问控制
- **API密钥**: 简单的API密钥认证
- **安全响应头**: 增强HTTP安全性

---

## JWT认证

### 功能特性

- 标准JWT (HS256) 签名
- 访问令牌 + 刷新令牌
- 支持Cookie、Header、Query传输
- 角色权限验证
- 可选认证（匿名访问）

### 配置示例

```yaml
jwt:
  enabled: true
  secret: ${JWT_SECRET:your-secret-key}
  issuer: "athena-gateway"
  access_token_expire: 24  # 小时
  refresh_token_expire: 7   # 天
  cookie_name: "jwt_token"
  use_cookie: true
  use_header: true
  header_name: "Authorization"
```

### 代码示例

```go
import (
    "github.com/athena-workspace/gateway-unified/internal/middleware"
)

// 创建JWT管理器
config := &middleware.JWTConfig{
    Secret:            "your-secret-key",
    Issuer:            "athena-gateway",
    Expiration:        24 * time.Hour,
    RefreshExpiration: 7 * 24 * time.Hour,
}
jwtManager := middleware.NewJWTManager(config)

// 生成Token
tokenPair, err := jwtManager.GenerateToken(
    "user123",
    "testuser",
    []string{"admin", "user"},
    map[string]interface{}{"department": "engineering"},
)

// 使用认证中间件
router.Use(jwtManager.AuthMiddleware())

// 角色验证
router.GET("/admin", jwtManager.RequireRoles("admin"), handler)

// 可选认证（允许匿名访问）
router.GET("/public", jwtManager.OptionalAuth(), handler)
```

### 环境变量

```bash
# 设置JWT密钥（生产环境必须设置）
export JWT_SECRET="your-very-secret-key-change-in-production"
```

---

## 速率限制

### 功能特性

- 令牌桶算法
- 自适应调整
- 分级限流（按角色/API Key）
- Redis支持（分布式）
- 内存模式（单机）

### 配置示例

```yaml
rate_limit:
  enabled: true
  global_limit: 1000      # 每分钟请求数
  per_ip_limit: 100      # 每IP每分钟请求数
  burst: 10              # 突发容量
  type: "memory"         # memory 或 redis

  # Redis配置（type=redis时使用）
  redis:
    host: ${REDIS_HOST:localhost}
    port: ${REDIS_PORT:6379}
    password: ${REDIS_PASSWORD:}
    db: ${REDIS_DB:0}

  # 分级限流
  tiers:
    - name: "admin"
      condition: "role:admin"
      limit: 10000
      burst: 100
      window: 1m
    - name: "user"
      condition: "default"
      limit: 100
      burst: 10
      window: 1m
```

### 代码示例

```go
import (
    "github.com/athena-workspace/gateway-unified/internal/middleware"
    "github.com/athena-workspace/gateway-unified/internal/ratelimit"
)

// 创建速率限制器
limiter, _ := ratelimit.NewAdaptiveRateLimiter(1000, 100)

// 使用速率限制中间件
router.Use(middleware.RateLimitMiddleware(limiter))
```

---

## CORS配置

### 功能特性

- 精确源匹配
- 通配符支持 (`*`)
- 子域名通配符 (`*.example.com`)
- 预检请求缓存
- 凭证支持

### 配置示例

```yaml
cors:
  enabled: true
  allowed_origins:
    - "http://localhost:3000"
    - "https://athena.example.com"
    - "*.example.com"  # 子域名通配符
  allowed_methods:
    - "GET"
    - "POST"
    - "PUT"
    - "DELETE"
    - "OPTIONS"
  allowed_headers:
    - "Origin"
    - "Content-Type"
    - "Authorization"
    - "X-API-Key"
  exposed_headers:
    - "Content-Length"
    - "X-Total-Count"
  allow_credentials: true
  max_age: 86400  # 24小时
```

### 代码示例

```go
import "github.com/athena-workspace/gateway-unified/internal/middleware"

// 使用默认配置
router.Use(middleware.CORSMiddleware(nil))

// 使用开发环境配置
router.Use(middleware.CORSMiddleware(middleware.DevelopmentCORSConfig()))

// 使用生产环境配置
router.Use(middleware.CORSMiddleware(
    middleware.ProductionCORSConfig([]string{"https://example.com"}),
))

// 动态CORS（基于函数）
router.Use(middleware.CORSByOrigin(func(origin string) bool {
    // 自定义逻辑
    return origin == "https://trusted.com"
}))
```

---

## IP白名单

### 功能特性

- CIDR格式支持
- 精确IP匹配
- 可选启用（不启用则允许所有）

### 配置示例

```yaml
ip_whitelist:
  enabled: false  # 生产环境建议启用
  allowed_ips:
    - "127.0.0.1/32"      # 本地回环
    - "10.0.0.0/8"        # 私有网络A类
    - "172.16.0.0/12"     # 私有网络B类
    - "192.168.0.0/16"    # 私有网络C类
    - "203.0.113.1"       # 特定IP
```

### 代码示例

```go
import "github.com/athena-workspace/gateway-unified/internal/middleware"

// 创建认证配置
authConfig := middleware.NewAuthConfig()

// 添加IP到白名单
authConfig.AddIPToWhitelist("127.0.0.1")
authConfig.AddIPToWhitelist("192.168.1.0/24")

// 启用IP白名单检查
authConfig.EnableIPWhitelist = true

// 使用认证中间件
router.Use(authConfig.AuthMiddleware())
```

---

## API密钥认证

### 功能特性

- Header/Query传输
- 多密钥支持
- 角色关联

### 配置示例

```yaml
api_keys:
  enabled: true
  keys:
    - name: "开发测试密钥"
      key: ${API_KEY_DEV:dev-test-key-123456}
      roles: ["read", "write", "admin"]
    - name: "生产只读密钥"
      key: ${API_KEY_PROD_READONLY:change-me-in-production}
      roles: ["read"]
```

### 使用方式

```bash
# 通过Header
curl -H "X-API-Key: your-api-key" http://localhost:8005/api/test

# 通过Query参数
curl "http://localhost:8005/api/test?api_key=your-api-key"
```

### 代码示例

```go
import "github.com/athena-workspace/gateway-unified/internal/middleware"

// 创建认证配置
authConfig := middleware.NewAuthConfig()

// 添加API密钥
authConfig.AddAPIKey("your-api-key-here")

// 启用API Key认证
authConfig.EnableAPIKey = true

// 使用认证中间件
router.Use(authConfig.AuthMiddleware())
```

---

## 安全响应头

### 功能特性

- X-Content-Type-Options
- X-Frame-Options
- X-XSS-Protection
- Strict-Transport-Security
- Content-Security-Policy
- Referrer-Policy
- Permissions-Policy

### 配置示例

```yaml
security_headers:
  enabled: true
  x_content_type_options: "nosniff"
  x_frame_options: "DENY"
  x_xss_protection: "1; mode=block"
  strict_transport_security: "max-age=31536000; includeSubDomains; preload"
  content_security_policy: "default-src 'self'; script-src 'self' 'unsafe-inline' 'unsafe-eval'"
  referrer_policy: "strict-origin-when-cross-origin"
  permissions_policy: "geolocation=(), microphone=(), camera=()"
```

### 代码示例

```go
import "github.com/athena-workspace/gateway-unified/internal/middleware"

// 使用默认安全头配置
router.Use(middleware.SecurityHeadersMiddleware(
    middleware.DefaultSecurityHeadersConfig(),
))

// 使用开发环境配置
router.Use(middleware.SecurityHeadersMiddleware(
    middleware.DevelopmentSecurityHeadersConfig(),
))

// 使用生产环境配置
router.Use(middleware.SecurityHeadersMiddleware(
    middleware.ProductionSecurityHeadersConfig(),
))

// 自定义CSP策略
csp := middleware.CSPForProduction("https://example.com")
config := middleware.DefaultSecurityHeadersConfig()
config.ContentSecurityPolicy = csp
router.Use(middleware.SecurityHeadersMiddleware(config))
```

---

## 配置示例

### 开发环境完整配置

```yaml
# config/security.dev.yaml
jwt:
  enabled: true
  secret: "dev-secret-key"
  issuer: "athena-gateway-dev"
  access_token_expire: 24
  refresh_token_expire: 7

rate_limit:
  enabled: true
  global_limit: 10000  # 开发环境限制宽松
  per_ip_limit: 1000
  type: "memory"

cors:
  enabled: true
  allowed_origins:
    - "http://localhost:3000"
    - "http://localhost:8080"
    - "http://127.0.0.1:3000"
  allow_credentials: true

ip_whitelist:
  enabled: false  # 开发环境禁用

api_keys:
  enabled: true
  keys:
    - name: "开发密钥"
      key: "dev-key-123456"
      roles: ["read", "write", "admin"]

security_headers:
  enabled: true
  x_frame_options: "SAMEORIGIN"  # 允许同源嵌入
  content_security_policy: "default-src 'self' 'unsafe-inline' 'unsafe-eval' localhost:*"
```

### 生产环境完整配置

```yaml
# config/security.prod.yaml
jwt:
  enabled: true
  secret: ${JWT_SECRET}  # 必须从环境变量读取
  issuer: "athena-gateway"
  access_token_expire: 1
  refresh_token_expire: 7

rate_limit:
  enabled: true
  global_limit: 1000
  per_ip_limit: 100
  type: "redis"  # 生产环境使用Redis
  redis:
    host: ${REDIS_HOST}
    port: ${REDIS_PORT}
    password: ${REDIS_PASSWORD}

cors:
  enabled: true
  allowed_origins:
    - "https://athena.example.com"
    - "*.example.com"
  allow_credentials: false  # 通配符时不允许凭证

ip_whitelist:
  enabled: true  # 生产环境启用
  allowed_ips:
    - "10.0.0.0/8"
    - "203.0.113.0/24"

api_keys:
  enabled: true
  keys:
    - name: "生产只读密钥"
      key: ${API_KEY_PROD}
      roles: ["read"]

security_headers:
  enabled: true
  x_frame_options: "DENY"
  strict_transport_security: "max-age=31536000; includeSubDomains; preload"
  content_security_policy: "default-src 'self'; script-src 'self'; object-src 'none'"
  referrer_policy: "no-referrer"
```

---

## 测试

### 运行安全测试

```bash
cd gateway-unified

# 运行所有中间件测试
go test ./internal/middleware/... -v

# 只运行JWT测试
go test ./internal/middleware/... -v -run TestJWT

# 只运行CORS测试
go test ./internal/middleware/... -v -run TestCORS

# 测试覆盖率
go test ./internal/middleware/... -cover -coverprofile=coverage.out
go tool cover -html=coverage.out
```

---

## 最佳实践

### 1. 密钥管理

- ✅ 使用环境变量存储敏感信息
- ✅ 定期轮换JWT密钥
- ✅ 生产环境使用强密钥（至少32字符）
- ❌ 不要将密钥硬编码在配置文件中
- ❌ 不要在日志中记录密钥

### 2. Token安全

- ✅ 使用HTTPS传输Token
- ✅ 设置合理的过期时间
- ✅ 实现Token撤销机制
- ❌ 不要在URL中传递敏感Token
- ❌ 不要将Token存储在LocalStorage

### 3. 速率限制

- ✅ 根据业务需求设置合理的限制
- ✅ 为不同用户角色设置不同限制
- ✅ 监控速率限制触发情况
- ❌ 不要设置过高的限制（失去保护作用）
- ❌ 不要设置过低的限制（影响用户体验）

### 4. CORS配置

- ✅ 生产环境明确指定允许的源
- ✅ 限制允许的方法和头
- ✅ 谨慎使用凭证模式
- ❌ 生产环境不要使用通配符`*`和凭证同时启用
- ❌ 不要允许所有头

### 5. IP白名单

- ✅ 使用CIDR格式简化配置
- ✅ 定期审查白名单
- ✅ 结合其他认证方式使用
- ❌ 不要仅依赖IP白名单（IP可能被伪造）
- ❌ 不要将公网IP加入白名单（除非必要）

---

## 故障排查

### JWT认证失败

**问题**: Token验证失败

**检查清单**:
1. JWT密钥是否一致
2. Token是否过期
3. Token格式是否正确（Bearer前缀）
4. 时钟是否同步

### CORS错误

**问题**: 跨域请求被阻止

**检查清单**:
1. 源是否在允许列表中
2. 方法是否被允许
3. 头是否被允许
4. 凭证配置是否正确

### 速率限制误触发

**问题**: 正常用户被限流

**检查清单**:
1. 限制是否设置过低
2. 突发容量是否足够
3. 是否有NAT/代理环境
4. 客户端是否有重试逻辑

---

## 参考资源

- [JWT规范](https://jwt.io/)
- [OWASP安全头](https://owasp.org/www-project-secure-headers/)
- [MDN CORS文档](https://developer.mozilla.org/zh-CN/docs/Web/HTTP/CORS)
- [速率限制最佳实践](https://cloud.google.com/architecture/rate-limiting-strategies-techniques)

---

**维护者**: Athena AI团队
**最后更新**: 2026-04-20
