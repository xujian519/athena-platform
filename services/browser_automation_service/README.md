# Athena浏览器自动化服务

> **Browser Automation Service for Athena Platform**

基于 FastAPI + Playwright 的企业级浏览器自动化微服务

## 功能特性

- 🌐 **页面导航** - 智能URL导航，支持多种等待条件
- 🖱️ **元素交互** - 点击、填充表单等完整交互支持
- 📸 **页面截图** - 全屏或区域截图，Base64返回
- 📄 **内容提取** - 提取页面文本、链接等结构化内容
- 🔨 **JavaScript执行** - 在页面上下文中执行自定义脚本（沙箱保护）
- 🤖 **智能任务** - 自然语言描述执行复杂自动化任务
- 🔐 **会话隔离** - 多会话支持，完全隔离
- 📊 **健康监控** - 完善的健康检查和状态监控
- 🔒 **安全认证** - JWT/API Key双重认证支持
- ⚡ **性能优化** - 并发控制、速率限制、熔断保护
- 📈 **结构化日志** - JSON格式日志、请求追踪、性能指标

## 快速开始

### 1. 安装依赖

```bash
cd services/browser_automation_service
pip install -r requirements.txt
```

### 2. 安装Playwright浏览器

```bash
playwright install chromium
```

### 3. 启动服务

```bash
python main.py
```

服务将在 `http://localhost:8030` 启动

### 4. 访问API文档

- Swagger UI: http://localhost:8030/docs
- ReDoc: http://localhost:8030/redoc

## API端点

### 系统端点

| 端点 | 方法 | 功能 |
|------|------|------|
| `/health` | GET | 健康检查 |
| `/api/v1/status` | GET | 获取服务状态 |
| `/api/v1/config` | GET | 获取服务配置 |

### 浏览器操作端点

| 端点 | 方法 | 功能 |
|------|------|------|
| `/api/v1/navigate` | POST | 导航到URL |
| `/api/v1/click` | POST | 点击元素 |
| `/api/v1/fill` | POST | 填写表单 |
| `/api/v1/screenshot` | POST | 截取页面 |
| `/api/v1/content` | GET | 获取页面内容 |
| `/api/v1/evaluate` | POST | 执行JavaScript |
| `/api/v1/task` | POST | 执行智能任务 |

## 使用示例

### 导航到URL

```bash
curl -X POST http://localhost:8030/api/v1/navigate \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://www.baidu.com",
    "wait_until": "load"
  }'
```

### 执行智能任务

```bash
curl -X POST http://localhost:8030/api/v1/task \
  -H "Content-Type: application/json" \
  -d '{
    "task": "打开百度并搜索小诺双鱼公主"
  }'
```

### Python客户端

```python
from core.tools.browser_automation_tool import get_browser_tool

tool = get_browser_tool()

# 健康检查
print(tool.health_check())

# 导航
result = tool.navigate("https://www.baidu.com")

# 执行任务
result = tool.execute_task("打开百度并搜索人工智能")
print(result)
```

## 配置说明

环境变量配置文件 `.env`:

```bash
# 服务配置
HOST=0.0.0.0
PORT=8030
LOG_LEVEL=info

# 浏览器配置
BROWSER_TYPE=chromium
BROWSER_HEADLESS=true
BROWSER_WINDOW_WIDTH=1920
BROWSER_WINDOW_HEIGHT=1080

# 会话配置
MAX_CONCURRENT_SESSIONS=10
SESSION_TIMEOUT=3600

# 任务配置
MAX_CONCURRENT_TASKS=5
TASK_TIMEOUT=300
```

## 项目结构

```
browser_automation_service/
├── main.py                      # 服务主入口
├── requirements.txt             # Python依赖
├── README.md                    # 项目文档
├── .env                         # 环境配置
├── .env.example                # 配置模板
├── config/                      # 配置模块
│   ├── settings.py             # 设置管理
│   └── browser_config.py       # 浏览器配置
├── core/                        # 核心模块
│   ├── browser_manager.py       # 浏览器管理器
│   ├── playwright_engine.py     # Playwright引擎
│   ├── session_manager.py       # 会话管理器
│   ├── task_executor.py         # 任务执行器
│   ├── exceptions.py            # 异常处理
│   ├── concurrency.py           # 并发控制
│   ├── logging_config.py        # 日志配置
│   └── monitoring.py            # 监控模块
├── api/                         # API模块
│   ├── routes/                  # API路由
│   ├── models/                  # 数据模型
│   └── middleware/              # 中间件
│       └── auth_middleware.py    # 认证中间件
├── docs/                       # 文档
│   ├── API_USAGE.md            # API使用指南
│   ├── DEPLOYMENT.md           # 部署指南
│   ├── TROUBLESHOOTING.md      # 故障排查
│   └── TESTING.md             # 测试指南
└── tests/                      # 测试模块
    ├── test_api.py             # API集成测试
    ├── test_browser.py         # 浏览器操作测试
    ├── test_exceptions.py      # 异常处理测试
    ├── test_concurrency.py     # 并发控制测试
    ├── test_security.py        # 安全功能测试
    └── test_performance.py     # 性能测试
```

## 技术栈

- **FastAPI** - 现代化的Web框架
- **Playwright** - 强大的浏览器自动化库
- **Pydantic** - 数据验证和设置管理
- **Uvicorn** - ASGI服务器

## 开发

### 运行测试

```bash
pytest tests/ -v
```

### 代码格式化

```bash
black . --line-length 100
```

### 类型检查

```bash
mypy .
```

## 部署

### 快速部署

```bash
# Docker方式
docker-compose up -d

# 开发模式
python main.py
```

### 详细文档

- 📘 [API使用示例](./docs/API_USAGE.md) - 完整的API使用指南
- 🚀 [部署指南](./docs/DEPLOYMENT.md) - 生产环境部署说明
- 🔧 [故障排查](./docs/TROUBLESHOOTING.md) - 常见问题解决方案
- 🧪 [测试指南](./docs/TESTING.md) - 测试编写和运行指南

## 作者

**小诺·双鱼公主** (Xiaonuo Pisces Princess)

## 许可证

MIT License
