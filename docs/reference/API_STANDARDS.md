# Athena工作平台 - API标准规范

## 📋 统一响应格式

### 成功响应
```json
{
  "success": true,
  "message": "操作成功",
  "data": {},
  "timestamp": "2025-12-24T12:00:00",
  "request_id": "optional-request-id"
}
```

### 错误响应
```json
{
  "success": false,
  "message": "错误描述",
  "error_code": "ERROR_CODE",
  "details": {},
  "timestamp": "2025-12-24T12:00:00",
  "path": "/api/v1/endpoint"
}
```

### 分页响应
```json
{
  "success": true,
  "message": "查询成功",
  "data": [],
  "pagination": {
    "page": 1,
    "page_size": 10,
    "total": 100,
    "pages": 10
  },
  "timestamp": "2025-12-24T12:00:00"
}
```

## 🔧 使用方法

### 1. 导入标准模块
```python
from core.api.standards import (
    APIError,
    NotFoundError,
    success_response,
    error_response,
    setup_api_middleware
)
from fastapi import FastAPI

app = FastAPI()
setup_api_middleware(app)
```

### 2. 在路由中使用
```python
@app.get("/api/v1/users/{user_id}")
async def get_user(user_id: str):
    user = await get_user_by_id(user_id)
    if not user:
        raise NotFoundError(f"用户 {user_id} 不存在")
    return success_response(data=user)
```

### 3. 自定义错误
```python
from core.api.standards import APIError

class CustomError(APIError):
    def __init__(self, message: str):
        super().__init__(
            message=message,
            status_code=400,
            error_code="CUSTOM_ERROR"
        )
```

## 📊 标准错误码

| 错误码 | HTTP状态码 | 说明 |
|--------|-----------|------|
| VALIDATION_ERROR | 400 | 请求验证失败 |
| AUTHENTICATION_ERROR | 401 | 认证失败 |
| PERMISSION_ERROR | 403 | 权限不足 |
| NOT_FOUND | 404 | 资源未找到 |
| CONFLICT_ERROR | 409 | 资源冲突 |
| RATE_LIMIT_EXCEEDED | 429 | 请求过于频繁 |
| INTERNAL_ERROR | 500 | 服务器内部错误 |

## 🚀 API版本控制

### URL版本控制
```
/api/v1/resource
/api/v2/resource
```

### Header版本控制
```
Accept: application/vnd.athena.v1+json
```

## 📝 最佳实践

1. **统一错误处理**: 使用标准错误类
2. **清晰的错误消息**: 提供有用的错误信息
3. **适当的HTTP状态码**: 使用语义化的状态码
4. **请求ID**: 在响应中包含request_id用于追踪
5. **时间戳**: 所有响应都包含ISO格式时间戳

## 🔍 示例代码

完整示例请参考: `core/api/standards.py`
