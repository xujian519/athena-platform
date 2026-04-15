# API使用示例

> Athena浏览器自动化服务 - API使用指南

本文档提供所有API端点的详细使用示例。

---

## 目录

- [认证](#认证)
- [系统端点](#系统端点)
- [浏览器操作端点](#浏览器操作端点)
- [Python客户端](#python客户端)
- [错误处理](#错误处理)
- [最佳实践](#最佳实践)

---

## 认证

### JWT认证

```bash
# 1. 获取访问令牌（如果启用了认证）
curl -X POST http://localhost:8030/api/v1/auth/token \
  -H "Content-Type: application/json" \
  -d '{"user_id": "user123", "scopes": ["read", "write"]}'

# 响应
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "user_id": "user123",
  "expires_in": 1800
}

# 2. 使用令牌访问API
curl -X POST http://localhost:8030/api/v1/navigate \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..." \
  -H "Content-Type: application/json" \
  -d '{"url": "https://www.baidu.com"}'
```

### API Key认证

```bash
# 使用API Key
curl -X POST http://localhost:8030/api/v1/navigate \
  -H "X-API-Key: your_api_key_here" \
  -H "Content-Type: application/json" \
  -d '{"url": "https://www.baidu.com"}'
```

---

## 系统端点

### 健康检查

```bash
curl http://localhost:8030/health
```

**响应：**
```json
{
  "status": "healthy",
  "service": "browser_automation_service",
  "version": "1.0.0",
  "timestamp": "2024-01-01T12:00:00",
  "uptime_seconds": 3600.5,
  "active_sessions": 3
}
```

### 获取服务状态

```bash
curl http://localhost:8030/api/v1/status
```

**响应：**
```json
{
  "success": true,
  "active_sessions": 3,
  "total_sessions": 15,
  "sessions": [
    {
      "session_id": "sess-abc123",
      "context_id": "ctx-1",
      "created_at": "2024-01-01T12:00:00",
      "last_activity": "2024-01-01T12:05:00",
      "is_expired": false
    }
  ],
  "engine_initialized": true,
  "active_contexts": 3
}
```

### 获取配置

```bash
curl http://localhost:8030/api/v1/config
```

---

## 浏览器操作端点

### 1. 导航到URL

**端点：** `POST /api/v1/navigate`

```bash
curl -X POST http://localhost:8030/api/v1/navigate \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://www.baidu.com",
    "wait_until": "load"
  }'
```

**参数说明：**
| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| url | string | 是 | - | 目标URL |
| wait_until | string | 否 | "load" | 等待条件：load/domcontentloaded/networkidle |

**响应：**
```json
{
  "success": true,
  "url": "https://www.baidu.com",
  "title": "百度一下，你就知道",
  "status_code": 200
}
```

**Python示例：**
```python
import httpx

async def navigate_example():
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:8030/api/v1/navigate",
            json={
                "url": "https://www.baidu.com",
                "wait_until": "load"
            }
        )
        return response.json()
```

### 2. 点击元素

**端点：** `POST /api/v1/click`

```bash
curl -X POST http://localhost:8030/api/v1/click \
  -H "Content-Type: application/json" \
  -d '{
    "selector": "#su",
    "timeout": 5000
  }'
```

**参数说明：**
| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| selector | string | 是 | - | CSS选择器 |
| timeout | int | 否 | 5000 | 超时时间（毫秒） |

**响应：**
```json
{
  "success": true,
  "selector": "#su",
  "message": "成功点击元素: #su"
}
```

### 3. 填写表单

**端点：** `POST /api/v1/fill`

```bash
curl -X POST http://localhost:8030/api/v1/fill \
  -H "Content-Type: application/json" \
  -d '{
    "selector": "#kw",
    "value": "小诺双鱼公主",
    "timeout": 5000
  }'
```

**参数说明：**
| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| selector | string | 是 | - | CSS选择器 |
| value | string | 是 | - | 填充值 |
| timeout | int | 否 | 5000 | 超时时间（毫秒） |

### 4. 截取页面

**端点：** `POST /api/v1/screenshot`

```bash
curl -X POST http://localhost:8030/api/v1/screenshot \
  -H "Content-Type: application/json" \
  -d '{
    "full_page": false
  }' \
  --output screenshot.png
```

**参数说明：**
| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| full_page | boolean | 否 | false | 是否截取整个页面 |

**响应：**
```json
{
  "success": true,
  "screenshot": "iVBORw0KGgoAAAANSUhEUgAA...",
  "width": 1920,
  "height": 1080,
  "full_page": false
}
```

### 5. 获取页面内容

**端点：** `GET /api/v1/content`

```bash
curl http://localhost:8030/api/v1/content
```

**响应：**
```json
{
  "success": true,
  "url": "https://www.baidu.com",
  "title": "百度一下，你就知道",
  "text": "页面文本内容...",
  "links": ["https://www.baidu.com/link1", "https://www.baidu.com/link2"]
}
```

### 6. 执行JavaScript

**端点：** `POST /api/v1/evaluate`

```bash
curl -X POST http://localhost:8030/api/v1/evaluate \
  -H "Content-Type: application/json" \
  -d '{
    "script": "document.title"
  }'
```

**安全限制：**
- 禁止使用 `window.location`、`document.cookie`、`eval`、`fetch` 等危险操作
- 脚本长度限制：10000字符
- 执行超时：10秒

**参数说明：**
| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| script | string | 是 | - | JavaScript代码 |

**响应：**
```json
{
  "success": true,
  "result": "百度一下，你就知道",
  "script": "document.title"
}
```

### 7. 执行智能任务

**端点：** `POST /api/v1/task`

```bash
curl -X POST http://localhost:8030/api/v1/task \
  -H "Content-Type: application/json" \
  -d '{
    "task": "打开百度并搜索人工智能",
    "url": "https://www.baidu.com",
    "max_steps": 10,
    "enable_screenshots": true
  }'
```

**参数说明：**
| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| task | string | 是 | - | 任务描述（自然语言） |
| url | string | 否 | null | 起始URL |
| max_steps | int | 否 | 50 | 最大执行步数 |
| enable_screenshots | boolean | 否 | true | 是否启用截图 |

**响应：**
```json
{
  "success": true,
  "task_id": "TASK-abc123",
  "task": "打开百度并搜索人工智能",
  "status": "completed",
  "steps_taken": 3,
  "message": "任务执行成功",
  "screenshots": ["iVBORw0KGgoAAAANSUhEUgAA..."]
}
```

---

## Python客户端

### 基础客户端

```python
import httpx
import base64
from pathlib import Path
from typing import Any, Dict


class BrowserAutomationClient:
    """浏览器自动化客户端"""

    def __init__(
        self,
        base_url: str = "http://localhost:8030",
        api_key: str | None = None,
        token: str | None = None,
    ):
        """
        初始化客户端

        Args:
            base_url: API基础URL
            api_key: API密钥
            token: JWT令牌
        """
        self.base_url = base_url
        self.client = httpx.AsyncClient(timeout=60.0)

        # 设置认证
        self.headers = {"Content-Type": "application/json"}
        if token:
            self.headers["Authorization"] = f"Bearer {token}"
        elif api_key:
            self.headers["X-API-Key"] = api_key

    async def close(self):
        """关闭客户端"""
        await self.client.aclose()

    async def health_check(self) -> Dict[str, Any]:
        """健康检查"""
        response = await self.client.get(f"{self.base_url}/health")
        return response.json()

    async def navigate(
        self,
        url: str,
        wait_until: str = "load",
    ) -> Dict[str, Any]:
        """导航到URL"""
        response = await self.client.post(
            f"{self.base_url}/api/v1/navigate",
            headers=self.headers,
            json={"url": url, "wait_until": wait_until},
        )
        return response.json()

    async def click(
        self,
        selector: str,
        timeout: int = 5000,
    ) -> Dict[str, Any]:
        """点击元素"""
        response = await self.client.post(
            f"{self.base_url}/api/v1/click",
            headers=self.headers,
            json={"selector": selector, "timeout": timeout},
        )
        return response.json()

    async def fill(
        self,
        selector: str,
        value: str,
        timeout: int = 5000,
    ) -> Dict[str, Any]:
        """填写表单"""
        response = await self.client.post(
            f"{self.base_url}/api/v1/fill",
            headers=self.headers,
            json={"selector": selector, "value": value, "timeout": timeout},
        )
        return response.json()

    async def screenshot(
        self,
        full_page: bool = False,
        save_path: str | None = None,
    ) -> Dict[str, Any]:
        """截取页面"""
        response = await self.client.post(
            f"{self.base_url}/api/v1/screenshot",
            headers=self.headers,
            json={"full_page": full_page},
        )
        result = response.json()

        # 保存截图
        if result.get("success") and save_path:
            import base64

            screenshot_data = base64.b64decode(result["screenshot"])
            Path(save_path).write_bytes(screenshot_data)
            result["saved_to"] = save_path

        return result

    async def get_content(self) -> Dict[str, Any]:
        """获取页面内容"""
        response = await self.client.get(f"{self.base_url}/api/v1/content", headers=self.headers)
        return response.json()

    async def evaluate(self, script: str) -> Dict[str, Any]:
        """执行JavaScript"""
        response = await self.client.post(
            f"{self.base_url}/api/v1/evaluate",
            headers=self.headers,
            json={"script": script},
        )
        return response.json()

    async def execute_task(
        self,
        task: str,
        url: str | None = None,
        max_steps: int = 50,
    ) -> Dict[str, Any]:
        """执行智能任务"""
        response = await self.client.post(
            f"{self.base_url}/api/v1/task",
            headers=self.headers,
            json={
                "task": task,
                "url": url,
                "max_steps": max_steps,
            },
        )
        return response.json()


# 使用示例
async def main():
    """使用示例"""
    client = BrowserAutomationClient(api_key="your_api_key")

    try:
        # 1. 健康检查
        health = await client.health_check()
        print(f"健康状态: {health['status']}")

        # 2. 导航到百度
        nav_result = await client.navigate("https://www.baidu.com")
        print(f"页面标题: {nav_result.get('title')}")

        # 3. 填写搜索框
        await client.fill("#kw", "小诺双鱼公主")

        # 4. 截图
        screenshot = await client.screenshot(save_path="screenshot.png")
        print(f"截图已保存: {screenshot.get('saved_to')}")

        # 5. 执行智能任务
        task_result = await client.execute_task("搜索人工智能")
        print(f"任务状态: {task_result['status']}")

    finally:
        await client.close()


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
```

---

## 错误处理

### 错误响应格式

```json
{
  "success": false,
  "error": "BROWSER_ELEMENT_5000",
  "message": "元素未找到",
  "error_id": "ERR-ABC123",
  "details": {
    "selector": "#nonexistent",
    "timeout": 5000
  }
}
```

### 错误码参考

| 错误码 | 说明 |
|--------|------|
| BROWSER_AUTH_2000 | 未认证 |
| BROWSER_AUTH_2001 | 无效令牌 |
| BROWSER_AUTH_2002 | 令牌过期 |
| BROWSER_ENGINE_3000 | 浏览器未初始化 |
| BROWSER_NAVIGATE_4000 | 导航失败 |
| BROWSER_NAVIGATE_4001 | 无效URL |
| BROWSER_ELEMENT_5000 | 元素未找到 |
| BROWSER_ELEMENT_5001 | 元素不可见 |
| BROWSER_ELEMENT_5002 | 元素不可交互 |
| BROWSER_SESSION_6000 | 会话不存在 |
| BROWSER_SESSION_6001 | 会话已过期 |
| BROWSER_SESSION_6002 | 会话数量超限 |
| BROWSER_TASK_7000 | 任务执行失败 |
| BROWSER_JS_9000 | JavaScript执行失败 |
| BROWSER_JS_9003 | JavaScript沙箱违规 |

---

## 最佳实践

### 1. 连接管理

```python
# 使用异步上下文管理器
from contextlib import asynccontextmanager

@asynccontextmanager
async def browser_client():
    client = BrowserAutomationClient()
    try:
        yield client
    finally:
        await client.close()

# 使用
async with browser_client() as client:
    await client.navigate("https://www.baidu.com")
```

### 2. 错误重试

```python
import asyncio
from typing import Callable, TypeVar

T = TypeVar("T")

async def retry_async(
    func: Callable[..., T],
    max_retries: int = 3,
    delay: float = 1.0,
) -> T:
    """重试异步函数"""
    last_error = None

    for attempt in range(max_retries):
        try:
            return await func()
        except Exception as e:
            last_error = e
            if attempt < max_retries - 1:
                await asyncio.sleep(delay * (attempt + 1))

    raise last_error

# 使用
result = await retry_async(
    lambda: client.navigate("https://www.baidu.com"),
    max_retries=3
)
```

### 3. 并发控制

```python
import asyncio

async def concurrent_navigation(urls: list[str]):
    """并发导航多个URL"""
    client = BrowserAutomationClient()

    try:
        tasks = [client.navigate(url) for url in urls]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        return results
    finally:
        await client.close()

# 使用
urls = [
    "https://www.baidu.com",
    "https://www.bing.com",
    "https://www.google.com",
]
results = await concurrent_navigation(urls)
```

### 4. 会话管理

```python
# 使用同一个会话执行多个操作
async def session_example():
    client = BrowserAutomationClient()

    # 导航（会自动创建会话）
    await client.navigate("https://www.baidu.com")

    # 点击操作（使用同一会话）
    await client.click("#some-button")

    # 填写表单（使用同一会话）
    await client.fill("#input", "value")

    await client.close()
```

---

## 更多资源

- [API文档（Swagger UI）](http://localhost:8030/docs)
- [API文档（ReDoc）](http://localhost:8030/redoc)
- [故障排查指南](./TROUBLESHOOTING.md)
- [部署指南](./DEPLOYMENT.md)
