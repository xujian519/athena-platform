# 浏览器自动化工具 - 快速参考指南

> **最后更新**: 2026-04-19
> **工具版本**: v1.0.0
> **状态**: ✅ 已验证并注册

---

## 🚀 快速开始

### 1. 启动服务（必需）

```bash
# 进入服务目录
cd /Users/xujian/Athena工作平台/services/browser_automation_service

# 首次使用：安装浏览器
playwright install chromium

# 启动服务
python main.py

# 服务将在 http://localhost:8030 启动
```

### 2. 验证服务

```bash
# 检查健康状态
curl http://localhost:8030/health

# 访问API文档
open http://localhost:8030/docs
```

### 3. 使用工具

```python
from core.tools.unified_registry import get_unified_registry
import asyncio

async def main():
    registry = get_unified_registry()

    # 健康检查
    result = await registry.call(
        "browser_automation",
        {"action": "health_check"}
    )
    print(result)

asyncio.run(main())
```

---

## 📖 核心功能

### 操作列表

| 操作 | Action | 必需参数 | 可选参数 |
|------|--------|---------|---------|
| **健康检查** | `health_check` | - | - |
| **页面导航** | `navigate` | `url` | `wait_until` |
| **元素点击** | `click` | `selector` | `timeout` |
| **表单填充** | `fill` | `selector`, `value` | `timeout` |
| **页面截图** | `screenshot` | - | `full_page`, `save_path` |
| **获取内容** | `get_content` | - | - |
| **执行JS** | `evaluate` | `script` | - |
| **智能任务** | `execute_task` | `task` | - |

---

## 💡 使用示例

### 示例1：导航到网页

```python
from core.tools.browser_automation_handler import navigate_to_url
import asyncio

async def main():
    result = await navigate_to_url("https://www.baidu.com")
    if result["success"]:
        print("✅ 导航成功")
    else:
        print(f"❌ 导航失败: {result.get('error')}")

asyncio.run(main())
```

### 示例2：页面交互

```python
from core.tools.unified_registry import get_unified_registry
import asyncio

async def search_baidu(keyword):
    registry = get_unified_registry()

    # 1. 导航到百度
    result = await registry.call(
        "browser_automation",
        {
            "action": "navigate",
            "url": "https://www.baidu.com"
        }
    )

    # 2. 填写搜索框
    result = await registry.call(
        "browser_automation",
        {
            "action": "fill",
            "selector": "#kw",  # 百度搜索框选择器
            "value": keyword
        }
    )

    # 3. 点击搜索按钮
    result = await registry.call(
        "browser_automation",
        {
            "action": "click",
            "selector": "#su"  # 百度搜索按钮选择器
        }
    )

    # 4. 截图
    result = await registry.call(
        "browser_automation",
        {
            "action": "screenshot",
            "full_page": False,
            "save_path": "/tmp/baidu_search.png"
        }
    )

    print("✅ 搜索完成")

asyncio.run(search_baidu("人工智能"))
```

### 示例3：智能任务执行

```python
from core.tools.browser_automation_handler import execute_browser_task
import asyncio

async def main():
    # 使用自然语言描述任务
    result = await execute_browser_task(
        "打开百度首页并搜索'小诺双鱼公主'"
    )

    if result["success"]:
        print("✅ 任务执行成功")
        print(f"结果: {result}")
    else:
        print(f"❌ 任务执行失败: {result.get('error')}")

asyncio.run(main())
```

### 示例4：获取页面内容

```python
from core.tools.unified_registry import get_unified_registry
import asyncio

async def main():
    registry = get_unified_registry()

    # 导航到网页
    await registry.call(
        "browser_automation",
        {"action": "navigate", "url": "https://www.baidu.com"}
    )

    # 获取页面内容
    result = await registry.call(
        "browser_automation",
        {"action": "get_content"}
    )

    if result["success"]:
        print(f"页面标题: {result['title']}")
        print(f"页面URL: {result['url']}")
        print(f"页面文本长度: {len(result['text'])} 字符")
    else:
        print(f"❌ 获取失败: {result.get('error')}")

asyncio.run(main())
```

### 示例5：执行JavaScript

```python
from core.tools.unified_registry import get_unified_registry
import asyncio

async def main():
    registry = get_unified_registry()

    # 导航到网页
    await registry.call(
        "browser_automation",
        {"action": "navigate", "url": "https://www.baidu.com"}
    )

    # 执行JavaScript获取页面高度
    result = await registry.call(
        "browser_automation",
        {
            "action": "evaluate",
            "script": "document.body.scrollHeight"
        }
    )

    if result["success"]:
        print(f"页面高度: {result['result']} 像素")
    else:
        print(f"❌ 执行失败: {result.get('error')}")

asyncio.run(main())
```

---

## 🔧 高级用法

### 批量操作

```python
from core.tools.unified_registry import get_unified_registry
import asyncio

async def batch_screenshot(urls):
    """批量截图多个URL"""
    registry = get_unified_registry()

    for i, url in enumerate(urls):
        # 导航
        await registry.call(
            "browser_automation",
            {"action": "navigate", "url": url}
        )

        # 截图
        await registry.call(
            "browser_automation",
            {
                "action": "screenshot",
                "save_path": f"/tmp/screenshot_{i}.png"
            }
        )

        print(f"✅ 已截图: {url}")

asyncio.run(batch_screenshot([
    "https://www.baidu.com",
    "https://www.bing.com",
    "https://www.google.com"
]))
```

### 表单填写

```python
from core.tools.unified_registry import get_unified_registry
import asyncio

async def fill_login_form(username, password):
    """填写登录表单"""
    registry = get_unified_registry()

    # 导航到登录页
    await registry.call(
        "browser_automation",
        {"action": "navigate", "url": "https://example.com/login"}
    )

    # 填写用户名
    await registry.call(
        "browser_automation",
        {
            "action": "fill",
            "selector": "#username",
            "value": username
        }
    )

    # 填写密码
    await registry.call(
        "browser_automation",
        {
            "action": "fill",
            "selector": "#password",
            "value": password
        }
    )

    # 点击登录按钮
    result = await registry.call(
        "browser_automation",
        {
            "action": "click",
            "selector": "button[type='submit']"
        }
    )

    return result

asyncio.run(fill_login_form("user@example.com", "password123"))
```

---

## ⚙️ 配置选项

### 服务配置

环境变量位置: `services/browser_automation_service/.env`

```bash
# 浏览器配置
BROWSER_TYPE=chromium          # 浏览器类型
BROWSER_HEADLESS=true          # 无头模式
BROWSER_WINDOW_WIDTH=1920      # 窗口宽度
BROWSER_WINDOW_HEIGHT=1080     # 窗口高度

# 服务配置
HOST=0.0.0.0                   # 监听地址
PORT=8030                      # 监听端口
LOG_LEVEL=info                 # 日志级别

# 性能配置
MAX_CONCURRENT_SESSIONS=10     # 最大并发会话数
SESSION_TIMEOUT=3600           # 会话超时（秒）
MAX_CONCURRENT_TASKS=5         # 最大并发任务数
TASK_TIMEOUT=300               # 任务超时（秒）
```

### 客户端配置

```python
# 自定义服务URL
result = await registry.call(
    "browser_automation",
    {
        "action": "navigate",
        "url": "https://www.baidu.com",
        "service_url": "http://custom-service:8030"  # 自定义服务地址
    }
)

# 设置超时
result = await registry.call(
    "browser_automation",
    {
        "action": "navigate",
        "url": "https://www.baidu.com",
        "wait_until": "networkidle"  # 等待网络空闲
    }
)
```

---

## 🐛 故障排查

### 问题1：连接失败

```python
# 错误信息
{
    "success": False,
    "error": "connection_error",
    "message": "❌ 无法连接到浏览器自动化服务"
}

# 解决方案
# 1. 检查服务是否启动
lsof -i :8030

# 2. 启动服务
cd services/browser_automation_service && python main.py

# 3. 检查防火墙设置
```

### 问题2：元素未找到

```python
# 错误信息
{
    "success": False,
    "error": "Element not found: #invalid-selector"
}

# 解决方案
# 1. 检查选择器是否正确
# 2. 增加超时时间
result = await registry.call(
    "browser_automation",
    {
        "action": "click",
        "selector": "#my-button",
        "timeout": 10000  # 10秒超时
    }
)

# 3. 使用浏览器开发工具检查选择器
```

### 问题3：截图保存失败

```python
# 错误信息
{
    "success": True,
    "message": "⚠️ 截图成功但保存失败"
}

# 解决方案
# 1. 检查目录是否存在
import os
os.makedirs("/tmp/screenshots", exist_ok=True)

# 2. 检查文件写入权限
# 3. 使用绝对路径
result = await registry.call(
    "browser_automation",
    {
        "action": "screenshot",
        "save_path": "/tmp/screenshots/screenshot.png"  # 绝对路径
    }
)
```

---

## 📊 性能优化建议

1. **复用会话**: 同一任务序列尽量使用同一会话
2. **合理超时**: 根据页面加载时间设置合理的超时
3. **并发控制**: 避免创建过多并发会话（默认最多10个）
4. **资源清理**: 任务完成后及时清理会话

---

## 📚 相关资源

- [完整验证报告](../reports/BROWSER_AUTOMATION_TOOL_VERIFICATION_REPORT_20260419.md)
- [服务API文档](http://localhost:8030/docs)
- [Playwright官方文档](https://playwright.dev/python/)
- [工具系统指南](./TOOL_SYSTEM_GUIDE.md)

---

**最后更新**: 2026-04-19
**维护者**: Athena平台团队
