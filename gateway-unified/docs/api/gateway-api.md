# Athena Gateway API 文档

**版本**: v1.0
**基础路径**: `/api/v1`
**协议**: HTTP/HTTPS
**格式**: JSON

---

## 概述

Athena Gateway 是企业级 API 网关，提供统一的服务注册、路由管理、依赖管理、配置管理和健康检查功能。

### 特性

- ✅ 服务注册与发现
- ✅ 动态路由管理
- ✅ 服务依赖关系管理
- ✅ 动态配置加载
- ✅ 多级健康检查
- ✅ 连接池优化
- ✅ 多级缓存
- ✅ 并发控制

---

## 通用规范

### 请求格式

```http
POST /api/v1/services/batch HTTP/1.1
Host: gateway.example.com
Content-Type: application/json
Authorization: Bearer <token>
X-Request-ID: <unique-request-id>
```

### 响应格式

所有 API 响应遵循统一的格式：

**成功响应**:
```json
{
  "success": true,
  "data": { ... }
}
```

**错误响应**:
```json
{
  "success": false,
  "error": "错误描述"
}
```

### HTTP 状态码

| 状态码 | 说明 |
|--------|------|
| 200 | 请求成功 |
| 201 | 创建成功 |
| 202 | 已接受（异步处理中） |
| 400 | 请求参数错误 |
| 401 | 未授权 |
| 403 | 禁止访问 |
| 404 | 资源不存在 |
| 422 | 验证失败 |
| 500 | 服务器内部错误 |
| 503 | 服务不可用 |

---

## 服务管理 API

### 批量注册服务

批量注册多个服务实例到网关。

**请求**:
```http
POST /api/v1/services/batch
```

**请求体**:
```json
{
  "services": [
    {
      "name": "user-service",
      "host": "192.168.1.100",
      "port": 8080,
      "metadata": {
        "version": "1.0.0",
        "environment": "production"
      }
    },
    {
      "name": "order-service",
      "host": "192.168.1.101",
      "port": 8081,
      "metadata": {
        "version": "1.2.0",
        "environment": "production"
      }
    }
  ]
}
```

**参数说明**:

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| services | array | 是 | 服务实例列表 |
| services[].name | string | 是 | 服务名称 |
| services[].host | string | 是 | 服务主机地址 |
| services[].port | integer | 是 | 服务端口 (1-65535) |
| services[].metadata | object | 否 | 服务元数据 |

**响应**:
```json
{
  "success": true,
  "data": [
    {
      "id": "user-service:192.168.1.100:8080:1",
      "service_name": "user-service",
      "host": "192.168.1.100",
      "port": 8080,
      "weight": 1,
      "status": "UP",
      "metadata": {
        "version": "1.0.0",
        "environment": "production"
      }
    },
    {
      "id": "order-service:192.168.1.101:8081:2",
      "service_name": "order-service",
      "host": "192.168.1.101",
      "port": 8081,
      "weight": 1,
      "status": "UP",
      "metadata": {
        "version": "1.2.0",
        "environment": "production"
      }
    }
  ]
}
```

### 查询服务实例

查询所有已注册的服务实例。

**请求**:
```http
GET /api/v1/services/instances
```

**查询参数**:

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| service_name | string | 否 | 按服务名过滤 |
| status | string | 否 | 按状态过滤 (UP/DOWN) |
| page | integer | 否 | 页码（从1开始） |
| page_size | integer | 否 | 每页数量（默认50） |

**响应**:
```json
{
  "success": true,
  "data": [
    {
      "id": "user-service:192.168.1.100:8080:1",
      "service_name": "user-service",
      "host": "192.168.1.100",
      "port": 8080,
      "weight": 1,
      "status": "UP",
      "metadata": { ... }
    }
  ],
  "pagination": {
    "total": 100,
    "page": 1,
    "page_size": 50
  }
}
```

### 获取服务实例详情

获取单个服务实例的详细信息。

**请求**:
```http
GET /api/v1/services/instances/{inst_id}
```

**路径参数**:

| 参数 | 类型 | 说明 |
|------|------|------|
| inst_id | string | 实例ID |

**响应**:
```json
{
  "success": true,
  "data": {
    "id": "user-service:192.168.1.100:8080:1",
    "service_name": "user-service",
    "host": "192.168.1.100",
    "port": 8080,
    "weight": 1,
    "status": "UP",
    "metadata": { ... }
  }
}
```

### 更新服务实例

更新服务实例的配置。

**请求**:
```http
PUT /api/v1/services/instances/{inst_id}
```

**请求体**:
```json
{
  "host": "192.168.1.102",
  "port": 8082,
  "weight": 2,
  "metadata": {
    "version": "1.0.1"
  }
}
```

**参数说明**:

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| host | string | 否 | 新的主机地址 |
| port | integer | 否 | 新的端口 |
| weight | integer | 否 | 负载均衡权重 |
| metadata | object | 否 | 更新的元数据 |

**响应**:
```json
{
  "success": true,
  "data": { ... }
}
```

### 删除服务实例

从网关注册表中删除服务实例。

**请求**:
```http
DELETE /api/v1/services/instances/{inst_id}
```

**响应**:
```json
{
  "success": true,
  "data": {
    "deleted": "user-service:192.168.1.100:8080:1"
  }
}
```

---

## 路由管理 API

### 查询路由规则

查询所有路由规则。

**请求**:
```http
GET /api/v1/routes
```

**查询参数**:

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| enabled | boolean | 否 | 是否只返回启用的路由 |
| target_service | string | 否 | 按目标服务过滤 |

**响应**:
```json
{
  "success": true,
  "data": [
    {
      "id": "route-1",
      "path": "/api/users",
      "target_service": "user-service",
      "methods": ["GET", "POST"],
      "weight": 1,
      "enabled": true
    }
  ]
}
```

### 创建路由规则

创建新的路由规则。

**请求**:
```http
POST /api/v1/routes
```

**请求体**:
```json
{
  "id": "route-users",
  "path": "/api/users",
  "target_service": "user-service",
  "methods": ["GET", "POST", "PUT", "DELETE"],
  "weight": 1,
  "enabled": true
}
```

**参数说明**:

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| id | string | 是 | 路由规则ID |
| path | string | 是 | 路由路径 |
| target_service | string | 是 | 目标服务名 |
| methods | array | 否 | 支持的HTTP方法 |
| weight | integer | 否 | 路由权重 |
| enabled | boolean | 否 | 是否启用 |

**响应**:
```json
{
  "success": true,
  "data": {
    "id": "route-users",
    "path": "/api/users",
    "target_service": "user-service",
    "methods": ["GET", "POST", "PUT", "DELETE"],
    "weight": 1,
    "enabled": true
  }
}
```

### 更新路由规则

更新已有的路由规则。

**请求**:
```http
PATCH /api/v1/routes/{route_id}
```

**请求体**:
```json
{
  "enabled": false
}
```

**响应**:
```json
{
  "success": true,
  "data": { ... }
}
```

### 删除路由规则

删除路由规则。

**请求**:
```http
DELETE /api/v1/routes/{route_id}
```

**响应**:
```json
{
  "success": true,
  "data": {
    "deleted": "route-users"
  }
}
```

---

## 依赖管理 API

### 设置服务依赖

设置服务的依赖关系。

**请求**:
```http
POST /api/v1/dependencies
```

**请求体**:
```json
{
  "service": "order-service",
  "depends_on": ["user-service", "inventory-service"]
}
```

**参数说明**:

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| service | string | 是 | 服务名称 |
| depends_on | array | 是 | 依赖的服务列表 |

**响应**:
```json
{
  "success": true,
  "data": {
    "service": "order-service",
    "dependencies": ["user-service", "inventory-service"]
  }
}
```

### 查询服务依赖

查询指定服务的依赖关系。

**请求**:
```http
GET /api/v1/dependencies/{service}
```

**路径参数**:

| 参数 | 类型 | 说明 |
|------|------|------|
| service | string | 服务名称 |

**响应**:
```json
{
  "success": true,
  "data": {
    "service": "order-service",
    "dependencies": ["user-service", "inventory-service"]
  }
}
```

### 查询所有依赖关系

查询所有服务的依赖关系。

**请求**:
```http
GET /api/v1/dependencies
```

**响应**:
```json
{
  "success": true,
  "data": {
    "order-service": ["user-service", "inventory-service"],
    "payment-service": ["user-service"]
  }
}
```

### 删除服务依赖

删除服务的依赖关系。

**请求**:
```http
DELETE /api/v1/dependencies/{service}
```

**响应**:
```json
{
  "success": true,
  "data": {
    "deleted": "order-service"
  }
}
```

---

## 配置管理 API

### 动态加载配置

动态加载并应用配置。

**请求**:
```http
POST /api/v1/config/load
```

**请求体**:
```json
{
  "config": "# YAML或JSON格式的配置\nserver:\n  port: 8080"
}
```

**支持格式**:
- YAML
- JSON

**响应**:
```json
{
  "success": true,
  "data": {
    "parsed_config": { ... }
  }
}
```

### 获取当前配置

获取网关当前配置。

**请求**:
```http
GET /api/v1/config
```

**响应**:
```json
{
  "success": true,
  "data": {
    "server": {
      "port": 8080
    }
  }
}
```

### 重新加载配置

从配置文件重新加载配置。

**请求**:
```http
POST /api/v1/config/reload
```

**响应**:
```json
{
  "success": true,
  "data": {
    "message": "配置已重新加载"
  }
}
```

---

## 健康检查 API

### 基本健康检查

检查网关基本健康状态。

**请求**:
```http
GET /health
```

**响应**:
```json
{
  "success": true,
  "data": {
    "status": "UP",
    "timestamp": "2024-02-24T15:00:00Z",
    "version": "1.0.0",
    "uptime": 86400
  }
}
```

### 就绪检查

检查网关是否就绪（依赖服务是否可用）。

**请求**:
```http
GET /ready
```

**响应**:
```json
{
  "success": true,
  "data": {
    "status": "READY"
  }
}
```

### 存活检查

检查网关是否存活。

**请求**:
```http
GET /live
```

**响应**:
```json
{
  "success": true,
  "data": {
    "status": "ALIVE"
  }
}
```

---

## 错误代码

| 代码 | 说明 |
|------|------|
| E001 | 服务已存在 |
| E002 | 服务不存在 |
| E003 | 路由已存在 |
| E004 | 路由不存在 |
| E005 | 依赖服务不可用 |
| E006 | 配置格式错误 |
| E007 | 配置应用失败 |

---

## 使用示例

### cURL 示例

#### 批量注册服务

```bash
curl -X POST http://localhost:8080/api/v1/services/batch \
  -H "Content-Type: application/json" \
  -d '{
    "services": [
      {
        "name": "user-service",
        "host": "192.168.1.100",
        "port": 8080,
        "metadata": {"version": "1.0.0"}
      }
    ]
  }'
```

#### 创建路由

```bash
curl -X POST http://localhost:8080/api/v1/routes \
  -H "Content-Type: application/json" \
  -d '{
    "id": "route-users",
    "path": "/api/users",
    "target_service": "user-service",
    "methods": ["GET", "POST"],
    "enabled": true
  }'
```

### Go 示例

```go
package main

import (
    "bytes"
    "encoding/json"
    "net/http"
)

func main() {
    // 批量注册服务
    payload := map[string]interface{}{
        "services": []map[string]interface{}{
            {
                "name": "user-service",
                "host": "192.168.1.100",
                "port": 8080,
                "metadata": map[string]interface{}{
                    "version": "1.0.0",
                },
            },
        },
    }

    body, _ := json.Marshal(payload)
    resp, err := http.Post(
        "http://localhost:8080/api/v1/services/batch",
        "application/json",
        bytes.NewReader(body),
    )
    if err != nil {
        panic(err)
    }
    defer resp.Body.Close()

    // 处理响应...
}
```

### Python 示例

```python
import requests

# 批量注册服务
url = "http://localhost:8080/api/v1/services/batch"
payload = {
    "services": [
        {
            "name": "user-service",
            "host": "192.168.1.100",
            "port": 8080,
            "metadata": {"version": "1.0.0"}
        }
    ]
}

response = requests.post(url, json=payload)
print(response.json())
```

---

## 附录

### 更新日志

| 版本 | 日期 | 变更说明 |
|------|------|----------|
| v1.0 | 2024-02-24 | 初始版本 |

### 支持

如有问题，请联系 [Athena Gateway 团队](mailto:support@athena.com)
