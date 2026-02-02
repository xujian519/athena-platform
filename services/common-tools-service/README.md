# Common Tools Service

通用工具服务，提供浏览器自动化、网页爬虫、文本提取等通用功能的统一API接口。

## 🚀 功能特性

### 核心工具
1. **浏览器自动化** - 基于Selenium和Playwright的智能浏览器操作
2. **网页爬虫** - 高性能异步爬虫，支持JavaScript渲染
3. **文本提取** - 关键词、实体、摘要等智能提取
4. **GLM增强提取** - 基于GLM模型的智能文本分析

### 特性
- **统一API接口** - 所有工具通过RESTful API访问
- **异步处理** - 高性能异步架构
- **错误处理** - 完善的异常处理机制
- **健康检查** - 实时监控工具状态
- **批量处理** - 支持批量任务执行

## 📁 项目结构

```
common-tools-service/
├── main.py                     # 服务主入口
├── requirements.txt            # Python依赖
├── README.md                  # 项目文档
├── .env.example              # 环境变量示例
├── Dockerfile                # Docker配置
├── browser_automation_tool.py # 浏览器自动化工具
├── crawler_tool.py           # 爬虫工具
├── langextract_tool.py       # 文本提取工具
├── langextract_glm_tool.py   # GLM文本提取工具
└── tests/                    # 测试文件
```

## 🛠️ 安装和运行

### 1. 安装依赖
```bash
pip install -r requirements.txt

# 安装浏览器驱动
playwright install
```

### 2. 配置环境变量
```bash
cp .env.example .env
# 编辑.env文件配置参数
```

### 3. 启动服务
```bash
# 开发模式
python main.py

# 生产模式
uvicorn main:app --host 0.0.0.0 --port 8007
```

## 📚 API文档

### 基础端点

#### GET /
获取服务基本信息

#### GET /health
健康检查，返回所有工具状态

#### GET /api/v1/tools/status
获取各工具的详细状态

#### GET /api/v1/stats
获取服务统计信息

### 浏览器自动化

#### POST /api/v1/browser/execute
执行浏览器操作

**请求体**:
```json
{
  "action": "click|type|navigate|scroll",
  "url": "https://example.com",
  "selector": "#button",
  "text": "input text",
  "options": {
    "timeout": 30,
    "wait_for": "#element"
  }
}
```

#### GET /api/v1/browser/screenshot
网页截图

**参数**:
- url: 目标URL
- selector: CSS选择器（可选）

### 网页爬虫

#### POST /api/v1/crawler/crawl
爬取单个网页

**请求体**:
```json
{
  "url": "https://example.com",
  "options": {
    "depth": 2,
    "extract_links": true,
    "extract_images": false,
    "use_selenium": true
  }
}
```

#### POST /api/v1/crawler/batch
批量爬取

**请求体**:
```json
{
  "urls": ["https://example1.com", "https://example2.com"],
  "options": {
    "max_concurrent": 5,
    "delay": 1
  }
}
```

### 文本提取

#### POST /api/v1/text/extract
提取文本特征

**请求体**:
```json
{
  "text": "待处理的文本内容",
  "extract_type": "keywords|entities|summary",
  "options": {
    "language": "zh",
    "max_keywords": 10
  }
}
```

#### POST /api/v1/text/extract-glm
使用GLM模型智能提取

**请求体**:
```json
{
  "text": "待处理的文本内容",
  "extract_type": "sentiment|topics|intent",
  "options": {
    "model": "glm-4",
    "temperature": 0.7
  }
}
```

## ⚙️ 配置说明

### 环境变量

```bash
# 服务配置
APP_NAME=Common Tools Service
VERSION=1.0.0
DEBUG=false
PORT=8007

# 浏览器配置
BROWSER_HEADLESS=true
BROWSER_TIMEOUT=30

# 爬虫配置
CRAWLER_TIMEOUT=60
CRAWLER_USER_AGENT="Athena-Crawler/1.0"

# AI模型配置
OPENAI_API_KEY=your_openai_key
GLM_API_KEY=your_glm_key
```

## 🔧 使用示例

### Python客户端示例
```python
import httpx
import asyncio

async def example_usage():
    async with httpx.AsyncClient() as client:
        # 浏览器操作
        response = await client.post(
            "http://localhost:8007/api/v1/browser/execute",
            json={
                "action": "navigate",
                "url": "https://example.com"
            }
        )
        print(response.json())

        # 网页爬取
        response = await client.post(
            "http://localhost:8007/api/v1/crawler/crawl",
            json={
                "url": "https://example.com",
                "options": {"extract_links": True}
            }
        )
        print(response.json())

        # 文本提取
        response = await client.post(
            "http://localhost:8007/api/v1/text/extract",
            json={
                "text": "这是一段示例文本",
                "extract_type": "keywords"
            }
        )
        print(response.json())
```

### 批量爬取示例
```python
import httpx

async def batch_crawl():
    urls = [
        "https://site1.com",
        "https://site2.com",
        "https://site3.com"
    ]

    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:8007/api/v1/crawler/batch",
            json={
                "urls": urls,
                "options": {
                    "max_concurrent": 3,
                    "depth": 1
                }
            }
        )
        results = response.json()
        print(f"成功爬取: {results['successful']}/{results['total']}")
```

## 📊 监控和日志

### 健康检查
```bash
curl http://localhost:8007/health
```

返回示例：
```json
{
  "status": "healthy",
  "tools": {
    "browser_automation": true,
    "crawler": true,
    "langextract": true,
    "langextract_glm": true
  }
}
```

### 日志级别
- DEBUG: 详细调试信息
- INFO: 一般信息
- WARNING: 警告信息
- ERROR: 错误信息

## 🔒 安全注意事项

1. **浏览器安全**
   - 使用无头模式提高安全性
   - 限制文件访问权限
   - 定期清理浏览器缓存

2. **爬虫礼仪**
   - 遵守robots.txt
   - 控制请求频率
   - 使用合理的User-Agent

3. **API安全**
   - 实施速率限制
   - 验证输入参数
   - 使用HTTPS

## 🚀 性能优化

### 浏览器优化
- 复用浏览器实例
- 使用无痕模式
- 禁用图片加载（可选）

### 爬虫优化
- 异步并发处理
- 智能去重
- 缓存机制

### 文本处理优化
- 批量处理
- 缓存模型加载
- 使用GPU加速（如果可用）

## 🧪 测试

```bash
# 运行所有测试
pytest

# 运行特定测试
pytest tests/test_browser.py

# 运行异步测试
pytest tests/test_crawler_async.py -v
```

## 🤝 贡献指南

1. Fork项目
2. 创建特性分支
3. 提交更改
4. 创建Pull Request

## 📝 更新日志

### v1.0.0 (2025-12-13)
- 初始版本发布
- 集成四大核心工具
- 实现统一API接口
- 添加健康检查和监控

## 📄 许可证

MIT License

---

**维护团队**: Athena AI Team
**最后更新**: 2025-12-13