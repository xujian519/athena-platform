# 🕷️ Athena公共爬虫服务用户指南

## 📋 概述

Athena公共爬虫服务是Athena工作平台提供的通用数据抓取工具，支持多种网站的智能数据采集、处理和存储。

### 🎯 核心功能

- **通用爬虫引擎**: 支持任何网站的数据抓取
- **智能缓存机制**: 避免重复请求，提升效率
- **灵活配置**: 支持多种爬虫配置和规则
- **RESTful API**: 完整的HTTP接口服务
- **后台任务**: 支持异步批量处理
- **数据提取**: 智能文本、链接、图片提取
- **多格式输出**: JSON、CSV、XML等格式支持

## 🚀 快速开始

### 1. 启动爬虫服务

```bash
# 启动服务
./dev/scripts/start_public_crawler.sh start

# 检查服务状态
./dev/scripts/start_public_crawler.sh status

# 测试服务
./dev/scripts/start_public_crawler.sh test
```

### 2. 访问API文档

启动成功后，访问以下地址：
- **API服务**: http://localhost:8001
- **API文档**: http://localhost:8001/docs
- **健康检查**: http://localhost:8001/health

### 3. 基本使用示例

#### Python客户端示例

```python
import requests
import json

# API基础URL
BASE_URL = "http://localhost:8001"

# 爬虫配置
crawler_config = {
    "name": "测试爬虫",
    "base_url": "https://example.com",
    "rate_limit": 1.0,
    "cache_enabled": True
}

# 爬取请求
crawl_request = {
    "urls": ["https://example.com/page1", "https://example.com/page2"],
    "config": crawler_config,
    "extract_selector": "h1.title",  # 提取标题
    "save_format": "json",
    "background": False
}

# 发送请求
response = requests.post(f"{BASE_URL}/crawl", json=crawl_request)
result = response.json()

print(f"任务ID: {result['task_id']}")
print(f"状态: {result['status']}")
print(f"结果数量: {len(result['reports/reports/results'])}")
```

#### cURL示例

```bash
# 健康检查
curl http://localhost:8001/health

# 获取预定义配置
curl http://localhost:8001/presets

# 爬取单个URL
curl -X POST http://localhost:8001/crawl \
  -H "Content-Type: application/json" \
  -d '{
    "urls": ["https://example.com"],
    "config": {
      "name": "简单测试",
      "base_url": "https://example.com",
      "rate_limit": 1.0
    }
  }'
```

## 🔧 详细功能说明

### 1. 爬虫配置参数

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| name | string | 是 | - | 爬虫名称 |
| base_url | string | 是 | - | 基础URL |
| headers | dict | 否 | 默认User-Agent | 请求头 |
| timeout | int | 否 | 30 | 超时时间(秒) |
| max_retries | int | 否 | 3 | 最大重试次数 |
| rate_limit | float | 否 | 1.0 | 速率限制(请求/秒) |
| use_proxy | bool | 否 | false | 是否使用代理 |
| cache_enabled | bool | 否 | true | 是否启用缓存 |
| cache_ttl | int | 否 | 3600 | 缓存时间(秒) |

### 2. 预定义配置

系统提供以下预定义配置：

#### news (新闻网站)
```json
{
  "name": "新闻网站爬虫",
  "rate_limit": 0.5,
  "cache_enabled": true,
  "cache_ttl": 1800
}
```

#### ecommerce (电商网站)
```json
{
  "name": "电商网站爬虫",
  "rate_limit": 1.0,
  "cache_enabled": false,
  "max_retries": 5
}
```

#### social_media (社交媒体)
```json
{
  "name": "社交媒体爬虫",
  "rate_limit": 2.0,
  "cache_enabled": true,
  "cache_ttl": 600
}
```

### 3. 数据提取功能

#### 文本提取
```python
# 提取所有文本
extract_selector: "article"

# 提取特定元素文本
extract_selector: ".title"
```

#### 属性提取
```python
# 提取链接的href和title属性
extract_selector: "a"
extract_attributes: ["href", "title"]
```

#### 表格提取
```python
# 自动识别并提取表格数据
extract_selector: "table"
```

## 📊 API端点详解

### 核心端点

#### POST /crawl
批量爬取URL列表

**请求参数:**
```json
{
  "urls": ["https://example.com/page1"],
  "config": {
    "name": "爬虫名称",
    "base_url": "https://example.com"
  },
  "extract_selector": "CSS选择器",
  "extract_attributes": ["href", "title"],
  "save_format": "json",
  "background": false
}
```

**响应:**
```json
{
  "task_id": "uuid",
  "status": "completed",
  "reports/reports/results": [
    {
      "url": "https://example.com/page1",
      "status_code": 200,
      "content_length": 12345,
      "request_time": 1.23,
      "extracted_data": "提取的数据"
    }
  ],
  "stats": {
    "total_requests": 1,
    "success_count": 1,
    "success_rate": "100%"
  }
}
```

#### GET /task/{task_id}
查询任务状态和结果

#### GET /tasks
列出所有任务

#### GET /presets
获取预定义配置

#### GET /stats
获取爬虫统计信息

### 工具端点

#### GET /extract/{task_id}
从已爬取页面中提取特定数据

#### DELETE /task/{task_id}
删除任务和相关文件

## 💡 使用技巧

### 1. 高效爬取策略

- **合理设置速率限制**: 避免对目标服务器造成压力
- **启用缓存**: 减少重复请求，提升效率
- **使用后台任务**: 处理大量URL时避免阻塞
- **选择合适的选择器**: 提高数据提取准确性

### 2. 错误处理

```python
# 检查任务状态
task_status = requests.get(f"{BASE_URL}/task/{task_id}").json()
if task_status["status"] == "failed":
    print(f"任务失败: {task_status.get('error')}")

# 检查响应状态
if response["status_code"] != 200:
    print(f"HTTP错误: {response['status_code']}")
```

### 3. 数据处理

```python
# 保存为CSV
DataProcessor.save_to_csv(results, "output.csv")

# 保存为JSON
DataProcessor.save_to_json(results, "output.json")

# 提取链接
soup = BeautifulSoup(html_content)
links = DataProcessor.extract_links(soup, base_url="https://example.com")
```

## 🔧 高级功能

### 1. 代理配置

```json
{
  "use_proxy": true,
  "proxy_list": [
    "http://proxy1.example.com:8080",
    "http://proxy2.example.com:8080"
  ]
}
```

### 2. 自定义请求头

```json
{
  "headers": {
    "User-Agent": "自定义User-Agent",
    "Authorization": "Bearer token",
    "Accept": "application/json"
  }
}
```

### 3. 后台任务处理

```python
# 启动后台任务
request["background"] = True

# 轮询任务状态
while True:
    status = requests.get(f"{BASE_URL}/task/{task_id}").json()
    if status["status"] in ["completed", "failed"]:
        break
    time.sleep(5)
```

## 📈 监控和维护

### 1. 服务监控

```bash
# 查看服务状态
./dev/scripts/start_public_crawler.sh status

# 查看日志
./dev/scripts/start_public_crawler.sh logs

# 健康检查
curl http://localhost:8001/health
```

### 2. 性能优化

- **调整并发数**: 修改配置中的监控设置
- **缓存管理**: 定期清理过期缓存
- **日志管理**: 设置日志轮转和清理

### 3. 故障排除

**常见问题:**

1. **服务启动失败**
   - 检查端口是否被占用
   - 确认Python依赖已安装
   - 查看日志文件获取详细错误信息

2. **爬取失败**
   - 检查目标网站是否可访问
   - 验证爬虫配置是否正确
   - 查看是否触发反爬虫机制

3. **数据提取不准确**
   - 调整CSS选择器
   - 检查网页结构是否变化
   - 使用浏览器开发者工具验证选择器

## 🛠️ 管理命令

```bash
# 启动服务
./dev/scripts/start_public_crawler.sh start

# 停止服务
./dev/scripts/start_public_crawler.sh stop

# 重启服务
./dev/scripts/start_public_crawler.sh restart

# 查看状态
./dev/scripts/start_public_crawler.sh status

# 查看日志
./dev/scripts/start_public_crawler.sh logs

# 测试服务
./dev/scripts/start_public_crawler.sh test
```

## 📞 技术支持

- **服务API**: http://localhost:8001/docs
- **日志位置**: /Users/xujian/Athena工作平台/logs/crawler_api.log
- **配置文件**: /Users/xujian/Athena工作平台/services/crawler/config/

---

**Athena工作平台** - 通用爬虫服务，让数据获取更简单！🕷️

*最后更新: 2025年12月11日*