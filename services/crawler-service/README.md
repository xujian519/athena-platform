# Athena Crawler Service

Athena平台智能爬虫服务，支持多引擎智能路由、成本控制和高效并发处理。

## 🚀 核心特性

### 智能路由系统
- **自动引擎选择** - 根据网站特征自动选择最佳爬虫引擎
- **成本优化** - 智能控制外部服务使用，优化成本
- **故障转移** - 多引擎备份，确保服务可用性
- **性能优化** - 并发控制和连接池复用

### 多引擎支持
1. **内部爬虫** - 基于aiohttp的高性能基础爬虫
2. **Crawl4AI** - AI增强的内容提取和智能解析
3. **FireCrawl** - 商业级爬虫服务，处理复杂网站

### 企业级功能
- **批量处理** - 支持大规模并发爬取任务
- **成本监控** - 实时监控和控制爬取成本
- **缓存系统** - 智能缓存减少重复请求
- **代理支持** - 代理轮换和IP管理
- **数据存储** - 多种存储后端支持

## 📁 项目结构

```
crawler/
├── main.py                    # 服务主入口
├── requirements.txt           # Python依赖
├── README.md                 # 项目文档
├── .env.example              # 环境变量示例
├── adapters/                 # 适配器层
│   ├── crawl4ai_adapter.py   # Crawl4AI集成
│   └── firecrawl_adapter.py  # FireCrawl集成
├── api/                      # API层
│   ├── crawler_api.py        # 基础API
│   └── hybrid_crawler_api.py # 混合爬虫API
├── config/                   # 配置管理
│   ├── default_config.json   # 默认配置
│   └── hybrid_config.py      # 混合配置
├── core/                     # 核心业务
│   ├── batch_processor.py    # 批量处理器
│   ├── hybrid_crawler_manager.py # 管理器
│   └── universal_crawler.py  # 通用爬虫
├── storage/                  # 存储层
│   └── data_storage_manager.py # 存储管理器
└── utils/                    # 工具模块
    └── data_processor.py     # 数据处理器
```

## 🛠️ 安装和运行

### 1. 环境准备
```bash
# 安装浏览器驱动（用于Selenium/Playwright）
playwright install
```

### 2. 安装依赖
```bash
pip install -r requirements.txt
```

### 3. 配置环境变量
```bash
cp .env.example .env
# 编辑.env文件，配置API密钥等
```

### 4. 启动服务
```bash
# 开发模式
python main.py

# 生产模式
uvicorn main:app --host 0.0.0.0 --port 8001
```

## 📚 API文档

### 基础端点

#### GET /
获取服务基本信息

#### GET /health
获取服务和组件健康状态

#### GET /api/v2/stats
获取服务统计信息

### 爬取端点

#### POST /api/v2/crawl
单URL智能爬取

**请求体**:
```json
{
  "url": "https://example.com",
  "engine": "auto",  // auto, internal, crawl4ai, firecrawl
  "options": {
    "extract_links": true,
    "use_ai_extraction": false,
    "wait_for_selector": ".content"
  },
  "priority": 1,
  "callback_url": "https://your-site.com/callback"
}
```

**响应**:
```json
{
  "task_id": "uuid",
  "url": "https://example.com",
  "status": "completed",
  "result": {
    "title": "Page Title",
    "content": "Extracted content",
    "links": ["https://..."]
  },
  "metadata": {
    "engine_used": "internal",
    "processing_time": 1.23,
    "cost": 0.002
  }
}
```

#### POST /api/v2/batch/crawl
批量URL爬取

**请求体**:
```json
{
  "urls": [
    "https://example1.com",
    "https://example2.com"
  ],
  "engine": "auto",
  "max_concurrent": 5
}
```

**响应**:
```json
{
  "batch_id": "uuid",
  "total_urls": 100,
  "status": "processing"
}
```

#### GET /api/v2/task/{task_id}
获取任务状态

#### GET /api/v2/batch/{batch_id}
获取批量任务状态

## ⚙️ 配置说明

### 环境变量

```bash
# 服务配置
APP_NAME=Athena Crawler Service
PORT=8001
DEBUG=false

# 爬虫配置
MAX_CONCURRENT_CRAWLS=5
DEFAULT_TIMEOUT=30
ENABLE_CACHE=true
CACHE_TTL=3600

# 成本控制
MONTHLY_COST_LIMIT=100.0
DAILY_COST_LIMIT=10.0
ENABLE_COST_MONITORING=true

# 存储配置
STORAGE_TYPE=file  # file, redis, postgresql
STORAGE_PATH=./data/crawler

# 代理配置
ENABLE_PROXY=false
PROXY_LIST=http://proxy1:8080,http://proxy2:8080

# 外部服务API密钥
CRAWL4AI_API_KEY=your_crawl4ai_key
FIRECRAWL_API_KEY=your_firecrawl_key
OPENAI_API_KEY=your_openai_key
```

### 引擎选择策略

| 网站特征 | 推荐引擎 | 说明 |
|---------|---------|------|
| 静态HTML | internal | 速度快，成本低 |
| JavaScript渲染 | firecrawl | 完整渲染支持 |
| 需要AI提取 | crawl4ai | 智能内容提取 |
| 反爬虫网站 | firecrawl | 专业反检测 |
| 大规模爬取 | internal + 代理 | 成本优化 |

### 成本控制

各引擎的预估成本：
- **Internal**: 免费
- **Crawl4AI**: ~$0.005/请求
- **FireCrawl**: ~$0.001/请求
- **AI提取**: 额外 $0.003/请求

## 🔧 高级功能

### 智能提取配置
```json
{
  "options": {
    "extract_links": true,
    "extract_images": true,
    "extract_tables": true,
    "use_ai_extraction": true,
    "ai_extraction_schema": {
      "title": "string",
      "content": "string",
      "author": "string",
      "publish_date": "date"
    }
  }
}
```

### 代理配置
```json
{
  "options": {
    "proxy": {
      "enabled": true,
      "rotation": "round_robin",
      "proxies": [
        {"url": "http://proxy1:8080", "country": "US"},
        {"url": "http://proxy2:8080", "country": "UK"}
      ]
    }
  }
}
```

### 缓存策略
- **内存缓存**: 热点数据快速访问
- **文件缓存**: 持久化存储
- **TTL控制**: 自动过期机制
- **MD5校验**: 避免重复爬取

## 📊 监控和统计

### 统计指标
- 总请求数和成功率
- 各引擎使用分布
- 响应时间分析
- 成本消耗统计
- 缓存命中率

### 健康检查
```json
{
  "status": "healthy",
  "components": {
    "crawler_manager": {"status": "healthy"},
    "storage_manager": {"status": "healthy"}
  }
}
```

## 🚨 错误处理

### 常见错误码
- 400: URL格式错误
- 404: 任务不存在
- 429: 请求频率限制
- 503: 服务未初始化
- 502: 外部引擎不可用

### 重试机制
- 自动重试失败的请求
- 指数退避策略
- 最大重试次数限制

## 🔐 安全最佳实践

1. **User-Agent轮换** - 避免被识别为爬虫
2. **请求延迟** - 控制请求频率
3. **代理使用** - 分散IP地址
4. **robots.txt尊重** - 遵守网站规则
5. **数据脱敏** - 处理敏感信息

## 🔄 性能优化

### 批量处理优化
- 合理设置并发数
- 使用连接池
- 实现请求队列
- 监控资源使用

### 缓存优化
- 命中率提升
- 过期策略调整
- 存储空间管理

## 📝 使用示例

### Python客户端示例
```python
import httpx

async def crawl_example():
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:8001/api/v2/crawl",
            json={
                "url": "https://example.com",
                "engine": "auto",
                "options": {"extract_links": True}
            }
        )
        result = response.json()
        print(result)
```

### 批量爬取示例
```python
urls = [f"https://example.com/page/{i}" for i in range(1, 101)]

response = await client.post(
    "/api/v2/batch/crawl",
    json={
        "urls": urls,
        "max_concurrent": 10
    }
)
batch_id = response.json()["batch_id"]
```

## 🤝 贡献指南

1. Fork项目
2. 创建特性分支
3. 编写测试用例
4. 提交更改
5. 发起Pull Request

## 📄 许可证

MIT License

---

**维护团队**: Athena AI Team
**最后更新**: 2025-12-13