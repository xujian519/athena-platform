# 专利知识图谱API服务

## 🚀 概述

这是基于三个核心知识图谱的统一智能后端服务，为各种专利应用提供动态提示词和规则提取能力。

### 核心知识源
- **SQLite专利知识图谱** - 125万+实体，329万+关系 (2.8GB)
- **专利法律法规知识图谱** - 45个实体，202个关系
- **审查指南向量数据库** - 53个768维向量
- **专利法律1024维向量库** - 191个1024维向量

## 📡 API端点

### 基础信息
- **基础URL**: `http://localhost:8000`
- **协议**: RESTful API
- **数据格式**: JSON
- **认证**: Bearer Token (可选)

### 端点列表

| 方法 | 端点 | 描述 |
|------|------|------|
| GET | `/` | 服务根信息 |
| GET | `/health` | 健康检查 |
| POST | `/query` | 单个知识查询 |
| POST | `/batch/query` | 批量知识查询 |
| POST | `/rules/extract` | 提取专利规则 |
| POST | `/search/similarity` | 相似度搜索 |
| GET | `/stats` | 获取服务统计 |
| GET | `/capabilities` | 获取服务能力 |
| GET | `/docs` | API文档 |

## 🔍 使用指南

### 1. 单个知识查询

**请求**:
```json
POST /query
{
  "query": "这个专利是否符合新颖性要求？",
  "patent_text": "本发明涉及一种基于AI的图像识别方法...",
  "context_type": "patent_review",
  "context": {
    "application_number": "CN202410001234.5"
  },
  "user_id": "user123",
  "application_id": "patent_review_system"
}
```

**响应**:
```json
{
  "query_id": "20241215_1015_1234",
  "intent": "patent_review",
  "prompts": {
    "system_role": "你是一位资深的专利审查员...",
    "task_description": "请对以下专利申请进行审查...",
    "knowledge_guidance": "### 相关规则...",
    "novelty_assessment": "## 新颖性评估...",
    "output_format": "## 审查意见格式..."
  },
  "suggested_actions": [
    {
      "action": "generate_review_opinion",
      "label": "生成审查意见"
    }
  ],
  "knowledge_sources": [...],
  "metadata": {
    "query_length": 25,
    "patent_text_length": 500,
    "timestamp": "2024-12-15T10:15:00"
  }
}
```

### 2. 批量查询

**请求**:
```json
POST /batch/query
{
  "queries": [
    {
      "query": "什么是专利的三性？",
      "user_id": "user001"
    },
    {
      "query": "如何撰写权利要求？",
      "user_id": "user002"
    }
  ],
  "max_parallel": 5
}
```

**响应**:
```json
{
  "batch_id": "batch-12345",
  "total_queries": 2,
  "processed_at": "2024-12-15T10:15:00",
  "results": [
    {
      "query_id": "20241215_1015_1235",
      "intent": "general_inquiry",
      ...
    },
    {
      "query_id": "20241215_1015_1236",
      "intent": "patent_filing",
      ...
    }
  ]
}
```

### 3. 规则提取

**请求**:
```json
POST /rules/extract
{
  "patent_text": "本发明公开了一种新材料的制备方法...",
  "rule_types": ["novelty", "creativity"],
  "keywords": ["创新点", "技术效果"]
}
```

**响应**:
```json
{
  "patent_text_length": 1000,
  "extracted_rules": {
    "novelty": [
      {
        "source": "SQLite知识图谱",
        "title": "申请日前现有技术判断",
        "content": "现有技术是指申请日以前..."
      }
    ],
    "creativity": [
      {
        "source": "SQLite知识图谱",
        "title": "创造性判断标准",
        "content": "创造性是指与现有技术相比..."
      }
    ]
  },
  "rule_count": 10,
  "extraction_time": "2024-12-15T10:15:00"
}
```

### 4. 相似度搜索

**请求**:
```json
POST /search/similarity
{
  "text": "深度学习图像识别技术",
  "similarity_threshold": 0.7,
  "max_results": 10,
  "collection": "patent_legal_vectors_1024"
}
```

**响应**:
```json
{
  "query": "深度学习图像识别技术",
  "collection": "patent_legal_vectors_1024",
  "threshold": 0.7,
  "results": [
    {
      "id": "doc_001",
      "content": "基于深度学习的图像识别方法...",
      "similarity": 0.95,
      "metadata": {
        "type": "patent",
        "year": "2023"
      }
    }
  ],
  "total_found": 1
}
```

## 📊 查询类型 (context_type)

| 类型 | 说明 | 应用场景 |
|------|------|----------|
| `patent_review` | 专利审查 | 专利审查系统 |
| `legal_advice` | 法律咨询 | 法律咨询服务 |
| `technical_analysis` | 技术分析 | 技术评估工具 |
| `patent_search` | 专利检索 | 搜索平台 |
| `patent_filing` | 专利申请 | 申请辅助工具 |
| `patent_value` | 价值评估 | 价值分析系统 |
| `general_inquiry` | 一般咨询 | 通用问答 |

## 🔧 快速开始

### Python SDK

```python
from services.knowledge_unified.client_sdk import create_client

# 创建客户端
client = create_client()

# 查询知识
response = client.query_knowledge(
    query="如何判断专利的新颖性？",
    patent_text="专利文本内容...",
    context_type="patent_review"
)

# 提取规则
rules = client.extract_rules(
    patent_text="专利文本...",
    rule_types=["novelty", "creativity"]
)

# 批量查询
queries = [
    {"query": "问题1", "patent_text": "文本1"},
    {"query": "问题2", "patent_text": "文本2"}
]
batch_result = client.batch_query(queries)
```

### JavaScript

```javascript
// 使用fetch API
const response = await fetch('http://localhost:8000/query', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    query: '查询问题',
    patent_text: '专利文本',
    context_type: 'patent_review'
  })
});

const result = await response.json();
console.log(result);
```

### cURL

```bash
# 健康检查
curl -X GET http://localhost:8000/health

# 查询知识
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "这个专利是否具有新颖性？",
    "patent_text": "专利文本内容",
    "context_type": "patent_review"
  }'

# 批量查询
curl -X POST http://localhost:8000/batch/query \
  -H "Content-Type: application/json" \
  -d '{
    "queries": [
      {"query": "问题1"},
      {"query": "问题2"}
    ]
  }'
```

## 🐳 Docker部署

### 1. 使用Docker Compose

```bash
cd services/knowledge-unified
docker-compose up -d
```

### 2. 构建镜像

```bash
docker build -t patent-kg-api .
docker run -p 8000:8000 patent-kg-api
```

### 3. Kubernetes

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: patent-kg-api
spec:
  replicas: 3
  selector:
    matchLabels:
      app: patent-kg-api
  template:
    spec:
      containers:
      - name: api
        image: patent-kg-api:latest
        ports:
        - containerPort: 8000
```

## 📈 监控

### 健康检查

```bash
curl http://localhost:8000/health
```

响应示例：
```json
{
  "status": "healthy",
  "timestamp": "2024-12-15T10:15:00",
  "service_stats": {
    "total_queries": 1234,
    "prompt_generated": 1200,
    "knowledge_hits": 1150
  }
}
```

### 服务统计

```bash
curl http://localhost:8000/stats
```

### 能力查询

```bash
curl http://localhost:8000/capabilities
```

## ⚡ 性能优化

### 1. 缓存策略

- 查询结果缓存1小时
- 规则提取结果缓存
- 会话历史保存

### 2. 批量处理

- 支持批量查询（最大50个）
- 并行处理优化
- 结果流式返回

### 3. 异步支持

- 提供异步API
- 非阻塞处理
- 支持长连接

## 🔒 安全

### API密钥

```python
# 使用API密钥
client = create_client(api_key="your-secret-key")
```

### 输入验证

- 自动输入长度限制
- SQL注入防护
- XSS防护

## 🚨 错误处理

### HTTP状态码

| 状态码 | 说明 |
|--------|------|
| 200 | 成功 |
| 400 | 请求参数错误 |
| 401 | 未授权 |
| 403 | 禁止访问 |
| 429 | 请求过于频繁 |
| 500 | 服务器错误 |
| 503 | 服务不可用 |

### 错误响应格式

```json
{
  "error": "Invalid input",
  "message": "Query text is too long",
  "timestamp": "2024-12-15T10:15:00"
}
```

## 📝 更新日志

### v1.0.0 (2024-12-15)
- 初始版本发布
- 支持三个知识图谱集成
- 提供完整的API接口
- 支持多种查询类型

## 🤝 技术支持

- **文档**: [API文档](http://localhost:8000/docs)
- **健康检查**: http://localhost:8000/health
- **邮件**: support@patent-kg.com

## 📄 许可证

MIT License