# Athena平台API参考文档

**版本**: v2.2.0
**更新日期**: 2026-03-26
**基础URL**: `http://localhost:8005`

---

## 📋 概述

Athena平台提供RESTful API接口，支持以下核心功能：
- 意图识别与分析
- 法律世界模型
- 智能体协作
- 提示词系统管理
- 健康检查与监控

---

## 🔐 认证

所有API请求需要包含认证头：

```http
Authorization: Bearer <api_key>
X-API-Key: <your_api_key>
```

---

## 📚 API端点

### 1. 健康检查 (`/health`)

#### 获取基本健康状态
```http
GET /health
```

**响应示例**:
```json
{
  "status": "healthy",
  "version": "2.2.0",
  "uptime_seconds": 3600
}
```

#### 获取详细健康状态
```http
GET /health/detailed
```

**响应示例**:
```json
{
  "status": "healthy",
  "components": {
    "database": "healthy",
    "redis": "healthy",
    "neo4j": "healthy",
    "qdrant": "healthy"
  },
  "metrics": {
    "requests_per_second": 15.3,
    "avg_response_time_ms": 45.2
  }
}
```

#### 组件状态检查
```http
GET /health/components
```

#### Ping测试
```http
GET /health/ping
```

#### 组件测试
```http
POST /health/test/{component_name}
```

---

### 2. 意图识别 (`/api/v1/intent`)

#### 识别用户意图
```http
POST /api/v1/intent/recognize
Content-Type: application/json

{
  "text": "帮我检索人工智能相关专利",
  "user_id": "user123",
  "context": {}
}
```

**响应示例**:
```json
{
  "intent": "PATENT_SEARCH",
  "confidence": 0.95,
  "category": "PATENT",
  "entities": ["人工智能", "专利"],
  "key_concepts": ["专利检索", "人工智能"],
  "complexity": "MEDIUM",
  "suggested_tools": ["patent_search", "vector_search"]
}
```

#### 批量意图识别
```http
POST /api/v1/intent/batch
Content-Type: application/json

{
  "texts": ["文本1", "文本2", "文本3"]
}
```

#### 获取意图统计
```http
GET /api/v1/intent/stats
```

#### 健康检查
```http
GET /api/v1/intent/health
```

#### 就绪检查
```http
GET /api/v1/intent/ready
```

#### 指标获取
```http
GET /api/v1/intent/metrics
```

---

### 3. 提示词系统 (`/api/v1/prompt`)

#### 场景识别
```http
POST /api/v1/prompt/scenario/identify
Content-Type: application/json

{
  "query": "分析专利侵权风险",
  "context": {}
}
```

**响应示例**:
```json
{
  "scenario_type": "INFRINGEMENT_ANALYSIS",
  "confidence": 0.89,
  "suggested_prompts": ["infringement_analysis_v1", "legal_opinion_v2"]
}
```

#### 规则检索
```http
POST /api/v1/prompt/rules/retrieve
Content-Type: application/json

{
  "scenario": "PATENT_SEARCH",
  "context": {}
}
```

#### 配置状态
```http
GET /api/v1/prompt/config/status
```

#### 重载配置
```http
POST /api/v1/prompt/config/reload
```

#### 扩展健康检查
```http
GET /api/v1/prompt/health/extended
```

---

### 4. 客户端管理 (`/api/v1/client`)

#### 注册客户端
```http
POST /api/v1/client/register
Content-Type: application/json

{
  "client_type": "web",
  "metadata": {
    "version": "1.0.0",
    "platform": "browser"
  }
}
```

**响应示例**:
```json
{
  "client_id": "client_abc123",
  "session_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "expires_at": "2026-03-27T00:00:00Z"
}
```

#### 获取客户端信息
```http
GET /api/v1/client/{client_id}
```

#### 获取客户端状态
```http
GET /api/v1/client/{client_id}/status
```

---

### 5. 学习与适应模块 (`/api/v1/learning`)

#### 学习任务执行
```http
POST /api/v1/learning/execute
Content-Type: application/json

{
  "task_type": "pattern_recognition",
  "data": {...},
  "config": {}
}
```

#### 健康检查
```http
GET /api/v1/learning/health
```

#### 获取统计信息
```http
GET /api/v1/learning/stats
```

#### 强化学习交互
```http
POST /api/v1/learning/rl/step
Content-Type: application/json

{
  "state": {...},
  "action": "explore",
  "reward": 1.0
}
```

---

### 6. 智能体协作 (`/api/v1/agent`)

#### 创建智能体会话
```http
POST /api/v1/agent/session
Content-Type: application/json

{
  "agent_type": "xiaona",
  "task": "专利分析",
  "context": {}
}
```

#### 发送消息
```http
POST /api/v1/agent/session/{session_id}/message
Content-Type: application/json

{
  "content": "请分析这个专利的创新点",
  "attachments": []
}
```

#### 获取会话状态
```http
GET /api/v1/agent/session/{session_id}/status
```

---

### 7. 法律世界模型 (`/api/v1/legal`)

#### 场景检索
```http
POST /api/v1/legal/scenario/retrieve
Content-Type: application/json

{
  "query": "专利侵权判定",
  "top_k": 5
}
```

#### 知识图谱查询
```http
POST /api/v1/legal/knowledge/query
Content-Type: application/json

{
  "query": "查找与专利无效相关的法律条文",
  "filters": {}
}
```

---

## 📊 监控指标

### Prometheus端点
```http
GET /metrics
```

### 可用指标

| 指标名称 | 类型 | 描述 |
|---------|------|-----|
| `athena_requests_total` | Counter | 总请求数 |
| `athena_request_duration_seconds` | Histogram | 请求延迟 |
| `athena_intent_recognition_total` | Counter | 意图识别总数 |
| `athena_agent_sessions_active` | Gauge | 活跃智能体会话 |
| `athena_llm_calls_total` | Counter | LLM调用总数 |
| `athena_cache_hits_total` | Counter | 缓存命中数 |

---

## 🔧 错误处理

### 标准错误响应格式

```json
{
  "error": {
    "code": "INVALID_REQUEST",
    "message": "请求参数无效",
    "details": {
      "field": "text",
      "reason": "不能为空"
    }
  },
  "request_id": "req_abc123"
}
```

### 错误码

| 错误码 | HTTP状态 | 描述 |
|-------|---------|-----|
| `INVALID_REQUEST` | 400 | 请求参数无效 |
| `UNAUTHORIZED` | 401 | 未授权 |
| `FORBIDDEN` | 403 | 禁止访问 |
| `NOT_FOUND` | 404 | 资源不存在 |
| `RATE_LIMITED` | 429 | 请求频率超限 |
| `INTERNAL_ERROR` | 500 | 内部错误 |
| `SERVICE_UNAVAILABLE` | 503 | 服务不可用 |

---

## 🚀 快速开始

### 使用curl测试

```bash
# 健康检查
curl http://localhost:8005/health

# 意图识别
curl -X POST http://localhost:8005/api/v1/intent/recognize \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -d '{"text": "帮我检索专利"}'

# 智能体会话
curl -X POST http://localhost:8005/api/v1/agent/session \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -d '{"agent_type": "xiaona", "task": "专利分析"}'
```

### Python示例

```python
import requests

base_url = "http://localhost:8005"
headers = {
    "Authorization": "Bearer YOUR_API_KEY",
    "Content-Type": "application/json"
}

# 意图识别
response = requests.post(
    f"{base_url}/api/v1/intent/recognize",
    headers=headers,
    json={"text": "帮我检索人工智能专利"}
)
print(response.json())
```

---

## 📝 版本控制

API支持多版本共存：

| 版本 | 状态 | 说明 |
|-----|------|-----|
| v1 | 当前 | 稳定版本 |
| v2 | 开发中 | 增强功能 |

通过请求头指定版本：
```http
Accept: application/vnd.athena.v1+json
```

---

**维护者**: Athena平台团队
**反馈**: xujian519@gmail.com
