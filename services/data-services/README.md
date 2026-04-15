# Data Services

数据处理相关服务集合，为Athena平台提供数据存储、检索和分析能力。

## 服务列表

### 1. patent-analysis
专利分析服务
- 端口: 9100
- 功能: 专利文档分析和处理
- 状态: ✅ 运行中

### 2. crawler
数据爬虫服务
- 端口: 9101
- 功能: 多源数据爬取
- 状态: 🚧 开发中

### 3. optimization
数据优化服务
- 端口: 9102
- 功能: 数据处理优化
- 状态: 🚧 开发中

## 快速开始

### 启动所有数据服务
```bash
./start_all.sh
```

### 单独启动服务
```bash
cd patent-analysis
python main.py
```

## API接口

### 专利分析API
- `POST /api/v1/patent/analyze` - 分析专利文档
- `GET /api/v1/patent/{id}` - 获取专利分析结果
- `GET /api/v1/patent/search` - 搜索专利

### 数据爬虫API
- `POST /api/v1/crawler/start` - 开始爬取任务
- `GET /api/v1/crawler/status/{task_id}` - 查看爬取状态
- `GET /api/v1/crawler/results` - 获取爬取结果

## 配置

统一的配置文件 `config/data-services.json`：

```json
{
  "patent_analysis": {
    "port": 9100,
    "storage_path": "./data/patents",
    "ai_service_url": "http://localhost:9001"
  },
  "crawler": {
    "port": 9101,
    "concurrent_limit": 10,
    "user_agent": "Athena-Crawler/1.0"
  },
  "optimization": {
    "port": 9102,
    "batch_size": 1000,
    "timeout": 300
  }
}
```

## 数据流

```
外部数据源 → Crawler → 原始数据存储
                ↓
            Optimization → 清洗和结构化
                ↓
        Patent Analysis → 智能分析
                ↓
        AI Services → 高级处理
```

## 监控

访问监控仪表板：
- http://localhost:9100/metrics
- http://localhost:9101/status
- http://localhost:9102/health

## 开发

### 运行测试
```bash
cd patent-analysis
pytest
```

### 添加新的数据处理逻辑
1. 在相应服务目录下创建模块
2. 更新API路由
3. 添加测试用例

## 负责人

- 团队：Athena数据团队
- 联系：data@athena.com