# Athena Gateway API使用指南

> **版本**: 1.0.0  
> **更新日期**: 2026-04-20  
> **Gateway匹配度**: 95%

---

## 📋 目录

- [API概述](#api概述)
- [认证方式](#认证方式)
- [核心API](#核心api)
- [版本管理](#版本管理)
- [错误处理](#错误处理)
- [使用示例](#使用示例)

---

## API概述

### 基础信息

```
Base URL: http://localhost:8005
API版本: v1, v2
协议: HTTP/HTTPS
数据格式: JSON
```

### API结构

```
/api/{version}/{endpoint}

示例:
- /api/v1/routes
- /api/v2/services
- /health (无版本)
```

---

## 认证方式

### 1. JWT认证

**获取Token**:
```bash
curl -X POST http://localhost:8005/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "admin",
    "password": "your_password"
  }'
```

**使用Token**:
```bash
curl http://localhost:8005/api/routes \
  -H "Authorization: Bearer <your_token>"
```

### 2. API密钥认证

```bash
curl http://localhost:8005/api/routes \
  -H "X-API-Key: athena-admin-key-2024"
```

### 3. 无认证端点

以下端点无需认证：
- `GET /` - Gateway信息
- `GET /health` - 健康检查
- `GET /ready` - 就绪状态
- `GET /live` - 存活状态

---

## 核心API

### 路由管理

#### 获取所有路由

```bash
GET /api/routes
```

**响应**:
```json
{
  "success": true,
  "data": {
    "count": 2,
    "data": [
      {
        "id": "xiaona-legal",
        "path": "/api/xiaona/*",
        "target_service": "xiaona-legal",
        "methods": ["GET", "POST"],
        "enabled": true
      }
    ]
  }
}
```

#### 创建路由

```bash
POST /api/routes
Content-Type: application/json

{
  "id": "new-route",
  "path": "/api/new/*",
  "target_service": "new-service",
  "methods": ["GET", "POST"],
  "strip_prefix": true,
  "timeout": 30,
  "retries": 3,
  "enabled": true
}
```

#### 更新路由

```bash
PATCH /api/routes/{route_id}
Content-Type: application/json

{
  "enabled": false
}
```

#### 删除路由

```bash
DELETE /api/routes/{route_id}
```

### 服务管理

#### 获取所有服务实例

```bash
GET /api/services/instances
```

**响应**:
```json
{
  "success": true,
  "data": {
    "count": 3,
    "data": [
      {
        "id": "xiaona-legal-123abc",
        "service_name": "xiaona-legal",
        "host": "127.0.0.1",
        "port": 8001,
        "status": "UP",
        "weight": 1
      }
    ]
  }
}
```

#### 注册服务实例

```bash
POST /api/services/instances
Content-Type: application/json

{
  "service_name": "test-service",
  "host": "127.0.0.1",
  "port": 9000,
  "weight": 1,
  "metadata": {
    "description": "Test service"
  }
}
```

#### 更新服务实例

```bash
PUT /api/services/instances/{instance_id}
Content-Type: application/json

{
  "status": "DOWN",
  "weight": 0
}
```

#### 删除服务实例

```bash
DELETE /api/services/instances/{instance_id}
```

### 依赖管理

#### 设置服务依赖

```bash
POST /api/dependencies
Content-Type: application/json

{
  "service": "xiaona-legal",
  "depends_on": ["redis", "postgres"]
}
```

#### 获取服务依赖

```bash
GET /api/dependencies/{service}
```

---

## 版本管理

### 获取所有版本

```bash
GET /api/versions
```

**响应**:
```json
{
  "success": true,
  "data": {
    "versions": [
      {
        "version": "v1",
        "deprecated": false
      },
      {
        "version": "v2",
        "deprecated": false
      }
    ],
    "default_version": "v1"
  }
}
```

### 获取版本详情

```bash
GET /api/versions/{version}
```

### 注册新版本

```bash
POST /api/versions
Content-Type: application/json

{
  "version": "v3",
  "deprecated": false
}
```

### 废弃版本

```bash
POST /api/versions/{version}/deprecate
Content-Type: application/json

{
  "unset_date": "2026-12-31",
  "migration_guide": "https://docs.example.com/migration"
}
```

### 设置默认版本

```bash
PUT /api/versions/default
Content-Type: application/json

{
  "version": "v2"
}
```

---

## 错误处理

### 错误响应格式

```json
{
  "success": false,
  "error": "错误描述",
  "code": "ERROR_CODE",
  "timestamp": "2026-04-20T13:45:00Z"
}
```

### HTTP状态码

| 状态码 | 说明 | 示例 |
|--------|------|------|
| 200 | 成功 | 请求成功 |
| 201 | 已创建 | 资源创建成功 |
| 400 | 请求错误 | 参数验证失败 |
| 401 | 未认证 | Token无效或缺失 |
| 403 | 禁止访问 | 权限不足 |
| 404 | 未找到 | 资源不存在 |
| 409 | 冲突 | 资源已存在 |
| 422 | 无法处理 | 语义错误 |
| 429 | 请求过多 | 触发速率限制 |
| 500 | 服务器错误 | 内部错误 |

### 错误码

| 错误码 | 说明 |
|--------|------|
| INVALID_PARAMS | 参数无效 |
| AUTH_FAILED | 认证失败 |
| TOKEN_EXPIRED | Token过期 |
| RATE_LIMIT_EXCEEDED | 超过速率限制 |
| SERVICE_NOT_FOUND | 服务不存在 |
| ROUTE_CONFLICT | 路由冲突 |

---

## 使用示例

### 示例1: 完整的路由管理流程

```bash
# 1. 创建路由
curl -X POST http://localhost:8005/api/routes \
  -H "Content-Type: application/json" \
  -H "X-API-Key: athena-admin-key-2024" \
  -d '{
    "id": "xiaona-analysis",
    "path": "/api/xiaona/analysis/*",
    "target_service": "xiaona-legal",
    "methods": ["POST"],
    "enabled": true
  }'

# 2. 查看路由
curl http://localhost:8005/api/routes \
  -H "X-API-Key: athena-admin-key-2024"

# 3. 测试路由
curl -X POST http://localhost:8005/api/xiaona/analysis \
  -H "Content-Type: application/json" \
  -d '{"patent_id": "CN123456789A"}'

# 4. 更新路由
curl -X PATCH http://localhost:8005/api/routes/xiaona-analysis \
  -H "X-API-Key: athena-admin-key-2024" \
  -d '{"enabled": false}'
```

### 示例2: 服务发现和注册

```bash
# 1. 注册服务
curl -X POST http://localhost:8005/api/services/instances \
  -H "Content-Type: application/json" \
  -H "X-API-Key: athena-admin-key-2024" \
  -d '{
    "service_name": "xiaona-legal",
    "host": "127.0.0.1",
    "port": 8001,
    "weight": 10,
    "metadata": {
      "description": "小娜法律专家服务"
    }
  }'

# 2. 查看所有服务
curl http://localhost:8005/api/services/instances \
  -H "X-API-Key: athena-admin-key-2024"

# 3. 更新服务状态
curl -X PUT http://localhost:8005/api/services/instances/xiaona-legal-123abc \
  -H "Content-Type: application/json" \
  -H "X-API-Key: athena-admin-key-2024" \
  -d '{"status": "UP"}'
```

### 示例3: API版本管理

```bash
# 1. 查看当前版本
curl http://localhost:8005/api/versions

# 2. 注册v2版本
curl -X POST http://localhost:8005/api/versions \
  -H "Content-Type: application/json" \
  -d '{
    "version": "v2",
    "deprecated": false
  }'

# 3. 废弃v1版本
curl -X POST http://localhost:8005/api/versions/v1/deprecate \
  -H "Content-Type: application/json" \
  -d '{
    "unset_date": "2026-12-31",
    "migration_guide": "https://docs.example.com/v1-to-v2"
  }'

# 4. 设置v2为默认版本
curl -X PUT http://localhost:8005/api/versions/default \
  -H "Content-Type: application/json" \
  -d '{"version": "v2"}'
```

### 示例4: 带认证的完整请求

```bash
# 1. 登录获取Token
TOKEN=$(curl -s -X POST http://localhost:8005/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"password"}' \
  | jq -r '.data.token')

# 2. 使用Token访问API
curl http://localhost:8005/api/routes \
  -H "Authorization: Bearer $TOKEN"

# 3. 刷新Token
curl -X POST http://localhost:8005/api/auth/refresh \
  -H "Content-Type: application/json" \
  -d "{\"refresh_token\": $REFRESH_TOKEN}"
```

---

## 最佳实践

### 1. 认证使用

**推荐**:
- 生产环境使用JWT认证
- 服务间通信使用API密钥
- 定期轮换密钥

**避免**:
- 不要在URL中传递Token
- 不要硬编码密钥
- 不要使用默认密钥

### 2. 错误处理

**推荐**:
- 始终检查响应状态码
- 实现重试机制
- 记录错误日志

**示例**:
```python
import requests
import time

def call_api(url, retries=3):
    for i in range(retries):
        try:
            response = requests.get(url)
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 429:
                # 速率限制，等待后重试
                time.sleep(2)
                continue
            else:
                response.raise_for_status()
        except requests.RequestException as e:
            if i == retries - 1:
                raise
            time.sleep(1)
```

### 3. 版本管理

**推荐**:
- 使用默认版本号
- 检查废弃警告
- 及时迁移到新版本

**示例**:
```python
headers = {
    "Accept": "application/json",
    "X-API-Version": "v2"  # 指定版本
}

response = requests.get(url, headers=headers)

# 检查废弃警告
if "X-API-Deprecated" in response.headers:
    logger.warning(f"API deprecated: {response.headers['X-API-Deprecated']}")
```

---

## 相关文档

- [部署指南](../deployment/GATEWAY_DEPLOYMENT_GUIDE.md)
- [安全配置指南](../security/GATEWAY_SECURITY_GUIDE.md)
- [端口分配规范](../PORT_ALLOCATION.md)

---

**维护者**: Athena Platform Team  
**最后更新**: 2026-04-20
