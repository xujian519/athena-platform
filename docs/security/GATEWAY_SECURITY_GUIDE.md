# Athena Gateway 安全配置指南

> **版本**: 1.0.0  
> **更新日期**: 2026-04-20  
> **状态**: 生产就绪

---

## 📋 目录

- [安全特性概述](#安全特性概述)
- [JWT认证](#jwt认证)
- [API密钥认证](#api密钥认证)
- [IP白名单](#ip白名单)
- [速率限制](#速率限制)
- [CORS配置](#cors配置)
- [生产环境最佳实践](#生产环境最佳实践)
- [故障排查](#故障排查)

---

## 安全特性概述

Athena Gateway提供多层安全防护：

```
┌─────────────────────────────────────┐
│  安全层次                           │
├─────────────────────────────────────┤
│  Layer 1: JWT认证                   │
│  Layer 2: API密钥认证               │
│  Layer 3: IP白名单                  │
│  Layer 4: 速率限制                  │
│  Layer 5: CORS控制                  │
└─────────────────────────────────────┘
```

---

## JWT认证

### 配置

**位置**: `gateway-unified/config.yaml`

```yaml
auth:
  jwt:
    secret: "athena-gateway-secret-key-change-in-production"
    issuer: "athena-gateway"
    expiration: 24h
    refresh_expiration: 168h
    use_cookie: false
    use_header: true
    header_name: "Authorization"
    use_query: false
```

### 使用方法

#### 1. 获取Token

```bash
curl -X POST http://localhost:8005/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "admin",
    "password": "password"
  }'
```

**响应**:
```json
{
  "success": true,
  "data": {
    "token": "eyJhbGciOiJIUzI1NiIs...",
    "refresh_token": "eyJhbGciOiJIUzI1NiIs...",
    "expires_at": "2026-04-21T13:45:00Z"
  }
}
```

#### 2. 使用Token

```bash
curl http://localhost:8005/api/routes \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIs..."
```

#### 3. 刷新Token

```bash
curl -X POST http://localhost:8005/api/auth/refresh \
  -H "Content-Type: application/json" \
  -d '{
    "refresh_token": "eyJhbGciOiJIUzI1NiIs..."
  }'
```

### Token结构

```json
{
  "header": {
    "alg": "HS256",
    "typ": "JWT"
  },
  "payload": {
    "user_id": "123",
    "username": "admin",
    "roles": ["admin"],
    "exp": 1713635100,
    "iat": 1713548700,
    "iss": "athena-gateway"
  }
}
```

---

## API密钥认证

### 配置

```yaml
auth:
  api_key:
    enabled: true
    keys:
      - "athena-admin-key-2024"
      - "athena-service-key-2024"
    header_name: "X-API-Key"
```

### 使用方法

```bash
curl http://localhost:8005/api/routes \
  -H "X-API-Key: athena-admin-key-2024"
```

### 适用场景

- ✅ 服务间通信
- ✅ 自动化脚本
- ✅ 临时访问
- ❌ 用户登录（使用JWT）

---

## IP白名单

### 配置

```yaml
auth:
  ip_whitelist:
    enabled: false
    allowed_ips:
      - "127.0.0.1/32"      # 本地
      - "10.0.0.0/8"        # 内网A类
      - "172.16.0.0/12"     # 内网B类
      - "192.168.0.0/16"    # 内网C类
```

### 使用场景

- 管理后台限制
- 内部服务保护
- VPN访问控制

---

## 速率限制

### 配置

```yaml
rate_limit:
  enabled: true
  requests_per_minute: 100
  burst_size: 20
  by_ip: true
  by_api_key: true
```

### 行为

```
正常请求: 100请求/分钟
突发请求: 20请求立即，然后限制
超过限制: HTTP 429 Too Many Requests
```

### 响应头

```http
HTTP/1.1 429 Too Many Requests
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 0
X-RateLimit-Reset: 1713635100
Retry-After: 60
```

---

## CORS配置

### 配置

```yaml
cors:
  enabled: true
  allowed_origins:
    - "http://localhost:3000"
    - "https://athena.example.com"
  allowed_methods:
    - GET
    - POST
    - PUT
    - DELETE
    - OPTIONS
  allowed_headers:
    - "Content-Type"
    - "Authorization"
  exposed_headers:
    - "X-Total-Count"
  allow_credentials: true
  max_age: 3600
```

### 预检请求

```http
OPTIONS /api/routes HTTP/1.1
Host: localhost:8005
Origin: http://localhost:3000
Access-Control-Request-Method: GET
```

**响应**:
```http
HTTP/1.1 204 No Content
Access-Control-Allow-Origin: http://localhost:3000
Access-Control-Allow-Methods: GET, POST, PUT, DELETE
Access-Control-Allow-Headers: Content-Type, Authorization
Access-Control-Max-Age: 3600
```

---

## 生产环境最佳实践

### 1. 密钥管理

```yaml
# ❌ 错误：使用默认密钥
auth:
  jwt:
    secret: "athena-gateway-secret-key-change-in-production"

# ✅ 正确：使用强随机密钥
auth:
  jwt:
    secret: "<32字节以上随机字符串>"
```

### 2. 启用所有安全层

```yaml
# 生产环境配置
auth:
  jwt:
    enabled: true
    secret: "${JWT_SECRET}"  # 环境变量
  
  api_key:
    enabled: true
    keys: ["${API_KEY}"]
  
  ip_whitelist:
    enabled: true

rate_limit:
  enabled: true
  requests_per_minute: 60  # 降低限制

cors:
  enabled: true
  allowed_origins:
    - "https://your-production-domain.com"
```

### 3. TLS/HTTPS

```yaml
server:
  port: 8005

tls:
  enabled: true
  cert_file: "/etc/ssl/certs/gateway.crt"
  key_file: "/etc/ssl/private/gateway.key"
```

### 4. 安全检查清单

部署前检查：

- [ ] JWT密钥已更改（至少32字节）
- [ ] TLS证书已配置
- [ ] 速率限制已启用
- [ ] API密钥已轮换
- [ ] IP白名单已配置
- [ ] CORS源已限制
- [ ] 日志级别设置为`info`或`warn`
- [ ] 监控已启用
- [ ] 备份已配置

---

## 故障排查

### 常见问题

#### Q1: JWT认证失败（401 Unauthorized）

**可能原因**：
- Token已过期
- Secret不匹配
- Token格式错误

**解决方案**：
```bash
# 1. 检查Token过期时间
echo "eyJhbGciOiJIUzI1NiIs..." | jq -R 'split(".") | .[1] | @base64d | fromjson | .exp'

# 2. 重新获取Token
curl -X POST http://localhost:8005/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"password"}'
```

#### Q2: CORS错误

**错误信息**：
```
Access to XMLHttpRequest blocked by CORS policy
```

**解决方案**：
```yaml
cors:
  allowed_origins:
    - "http://your-frontend-domain.com"  # 确保包含前端域名
```

#### Q3: 速率限制触发

**错误信息**：
```
HTTP 429 Too Many Requests
```

**解决方案**：
```yaml
rate_limit:
  requests_per_minute: 120  # 增加限制
  burst_size: 30
```

或使用API密钥（更高的限制）。

#### Q4: IP白名单拒绝访问

**错误信息**：
```
HTTP 403 Forbidden - IP not allowed
```

**解决方案**：
```yaml
auth:
  ip_whitelist:
    enabled: false  # 临时禁用测试
    # 或添加你的IP
    allowed_ips:
      - "your.ip.address.here/32"
```

---

## 监控和日志

### 安全事件日志

```json
{
  "timestamp": "2026-04-20T13:45:00Z",
  "level": "WARN",
  "event": "auth_failed",
  "ip": "192.168.1.100",
  "reason": "invalid_token"
}
```

### 监控指标

- `auth_success_total` - 认证成功总数
- `auth_failed_total` - 认证失败总数
- `rate_limit_hits_total` - 速率限制触发次数
- `cors_blocked_total` - CORS阻止次数

---

## 相关文档

- [Gateway部署指南](../deployment/DEPLOYMENT_GUIDE.md)
- [API文档](../api/GATEWAY_API.md)
- [配置参考](../config/CONFIG_REFERENCE.md)

---

**维护者**: Athena Platform Team  
**最后更新**: 2026-04-20
