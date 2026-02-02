# 统一智能后端服务

## 🚀 概述

基于向量库+知识图谱的通用智能基础设施，支持多专业领域的智能应用。

### 核心理念
- **统一基础设施**：向量库+知识图谱作为底层智能支撑
- **多领域支持**：专利、法律、医疗、金融等专业领域
- **智能响应**：根据领域自动适配相应的向量和知识源
- **可扩展架构**：易于添加新的专业领域

### 系统架构

```
┌──────────────────────────────────────────────────────────────┐
│                    统一智能后端服务                        │
│                    (Port: 8002)                           │
├──────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │
│  │ 专利领域适配 │  │ 法律领域适配 │  │ 医疗领域适配 │  ...   │
│  │    器       │  │    器       │  │    器       │        │
│  └─────────────┘  └─────────────┘  └─────────────┘        │
├──────────────────────────────────────────────────────────────┤
│                向量+知识图谱统一基础设施                     │
│  ┌─────────────────┐  ┌─────────────────┐                  │
│  │   向量数据库     │  │   知识图谱      │                  │
│  │ Qdrant Collections │  │ SQLite/NetworkX │                  │
│  │ - patent_legal   │  │ - patent_kg     │                  │
│  │ - patent_guide   │  │ - legal_kg      │                  │
│  │ - technical      │  │ - medical_kg    │                  │
│  │ - medical        │  │ - technical_kg  │                  │
│  └─────────────────┘  └─────────────────┘                  │
└──────────────────────────────────────────────────────────────┘
```

## 📡 API端点

### 基础信息
- **基础URL**: `http://localhost:8002`
- **协议**: RESTful API
- **数据格式**: JSON
- **支持领域**: patent, legal, medical, technical, education, general

### 核心端点

| 方法 | 端点 | 描述 | 支持领域 |
|------|------|------|----------|
| GET | `/` | 服务根信息 | - |
| GET | `/health` | 健康检查 | - |
| POST | `/query` | 领域智能查询 | 所有领域 |
| POST | `/batch/query` | 批量领域查询 | 所有领域 |
| POST | `/rules/extract` | 提取领域规则 | 所有领域 |
| POST | `/chat/intelligent` | 智能对话 | 所有领域 |
| POST | `/search/hybrid` | 通用混合搜索 | 跨领域 |
| GET | `/domains/list` | 获取支持领域 | - |
| GET | `/infrastructure/stats` | 基础设施统计 | - |

## 🔍 使用指南

### 1. 专利领域查询

**请求**:
```json
POST /query
{
  "query": "这个专利符合新颖性要求吗？",
  "domain": "patent",
  "context": {
    "patent_text": "本发明涉及一种基于AI的图像识别方法...",
    "application_number": "CN202410001234.5"
  },
  "user_id": "user123",
  "application_id": "patent_review_system"
}
```

**响应**:
```json
{
  "domain": "patent",
  "intent": "novelty",
  "prompts": {
    "system_role": "你是一位专业的专利审查员",
    "task_description": "请根据查询'这个专利符合新颖性要求吗？'提供专业的专利分析",
    "knowledge_guidance": "- 专利法第22条规定...\n- 新颖性判断标准...",
    "assessment_framework": "1. 查询现有技术数据库\n2. 对比技术特征\n3. 判断是否构成抵触申请\n4. 评估新颖性",
    "output_format": "## 新颖性分析\n### 技术特征对比\n### 现有技术检索\n### 结论"
  },
  "suggested_actions": [
    {"action": "search_prior_art", "label": "检索现有技术"},
    {"action": "compare_features", "label": "对比技术特征"}
  ],
  "confidence": 0.85,
  "search_results": {
    "vector_results": [...],
    "graph_results": [...],
    "hybrid_insights": [...]
  }
}
```

### 2. 法律领域查询

**请求**:
```json
POST /query
{
  "query": "这种情况是否构成合同违约？",
  "domain": "legal",
  "context": {
    "contract_type": "销售合同",
    "case_description": "甲方未按时交付货物..."
  }
}
```

### 3. 医疗领域查询

**请求**:
```json
POST /query
{
  "query": "这些症状可能是什么疾病？",
  "domain": "medical",
  "context": {
    "symptoms": ["发热", "咳嗽", "乏力"],
    "patient_age": 35,
    "duration": "3天"
  }
}
```

### 4. 批量查询

**请求**:
```json
POST /batch/query
{
  "queries": [
    {
      "query": "专利的新颖性如何判断？",
      "domain": "patent"
    },
    {
      "query": "合同违约的法律后果？",
      "domain": "legal"
    },
    {
      "query": "高血压的治疗建议？",
      "domain": "medical"
    }
  ],
  "max_parallel": 3
}
```

### 5. 规则提取

**请求**:
```json
POST /rules/extract
{
  "text": "本发明公开了一种新材料的制备方法，包括以下步骤：...",
  "domain": "patent",
  "rule_types": ["novelty", "creativity", "practicality"]
}
```

### 6. 跨领域混合搜索

**请求**:
```json
POST /search/hybrid
{
  "query": "人工智能在医疗诊断中的应用",
  "domain": "technical",
  "collections": ["technical_patents_1024", "medical_literature_vectors"],
  "max_vector_results": 10,
  "max_graph_paths": 5
}
```

## 🏗️ 集成示例

### Python SDK

```python
from unified_intelligent_backend import UnifiedIntelligentBackend

# 创建客户端
backend = UnifiedIntelligentBackend(base_url="http://localhost:8002")

# 专利查询
patent_result = backend.query(
    query="评估专利的新颖性",
    domain="patent",
    context={"patent_text": "专利文本..."}
)

# 法律咨询
legal_result = backend.query(
    query="分析合同条款的法律风险",
    domain="legal",
    context={"contract_text": "合同内容..."}
)

# 批量查询
queries = [
    {"query": "问题1", "domain": "patent"},
    {"query": "问题2", "domain": "legal"}
]
batch_results = backend.batch_query(queries)
```

### JavaScript 客户端

```javascript
class IntelligentBackendClient {
    constructor(baseUrl = 'http://localhost:8002') {
        this.baseUrl = baseUrl;
    }

    async query({ query, domain = 'patent', context = {} }) {
        const response = await fetch(`${this.baseUrl}/query`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ query, domain, context })
        });
        return await response.json();
    }

    async extractRules({ text, domain, ruleTypes }) {
        const response = await fetch(`${this.baseUrl}/rules/extract`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                text,
                domain,
                rule_types: ruleTypes
            })
        });
        return await response.json();
    }
}

// 使用示例
const client = new IntelligentBackendClient();

// 专利分析
const patentAnalysis = await client.query({
    query: '这个专利有创造性吗？',
    domain: 'patent',
    context: { patentText: '技术方案...' }
});
```

## 🚀 快速开始

### 1. 环境准备

```bash
# 安装依赖
pip install -r requirements.txt

# 启动向量数据库（Qdrant）
docker run -p 6333:6333 qdrant/qdrant:latest

# 确保知识图谱数据库可访问
ls /Users/xujian/Athena工作平台/data/knowledge_graph_sqlite/databases/
```

### 2. 启动服务

```bash
# 方式1：直接运行
python unified_intelligent_backend.py

# 方式2：使用uvicorn
uvicorn unified_intelligent_backend:app --host 0.0.0.0 --port 8002

# 方式3：使用Docker
docker-compose up -d
```

### 3. 验证服务

```bash
# 健康检查
curl http://localhost:8002/health

# 获取支持的领域
curl http://localhost:8002/domains/list

# 测试查询
curl -X POST http://localhost:8002/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "什么是专利的三性？",
    "domain": "patent"
  }'
```

## 🎯 应用场景

### 1. 专利审查系统
- 新颖性、创造性、实用性评估
- 现有技术检索
- 审查意见生成
- 申请指导

### 2. 法律咨询平台
- 合同审查
- 侵权分析
- 法律风险评估
- 案例检索

### 3. 医疗辅助诊断
- 症状分析
- 疾病鉴别
- 治疗方案建议
- 药物相互作用检查

### 4. 技术分析平台
- 技术趋势分析
- 创新点识别
- 竞品分析
- 技术可行性评估

## 📊 性能指标

### 查询性能
- 响应时间: < 500ms (95%)
- 并发支持: 100+ QPS
- 准确率: > 90%

### 基础设施
- 向量存储: 191+ 1024维向量
- 知识图谱: 125万+ 实体
- 混合搜索: 向量(60%) + 图谱(40%)

## 🔧 配置说明

### 环境变量

```bash
# 服务配置
PORT=8002
HOST=0.0.0.0
LOG_LEVEL=INFO

# 向量数据库
QDRANT_HOST=localhost
QDRANT_PORT=6333

# 知识图谱
PATENT_KG_PATH=/path/to/patent_kg.db
LEGAL_KG_PATH=/path/to/legal_kg
```

### 领域配置

每个领域适配器可以独立配置：
- 向量集合列表
- 知识图谱列表
- 意图关键词
- 响应模板
- 评估框架

## 🚦 扩展新领域

### 1. 创建领域适配器

```python
class NewDomainAdapter(DomainAdapter):
    def __init__(self, infrastructure):
        super().__init__(DomainType.NEW_DOMAIN, infrastructure)

    def _get_domain_config(self):
        return {
            "vector_collections": ["new_domain_vectors"],
            "knowledge_graphs": ["new_domain_kg"],
            "intent_keywords": {...}
        }

    async def process_query(self, query, context):
        # 实现领域特定的查询处理
        pass

    def extract_domain_rules(self, text, rule_types):
        # 实现领域规则提取
        pass
```

### 2. 注册新领域

```python
# 在DomainAdapterFactory中添加
adapters = {
    DomainType.PATENT: PatentDomainAdapter,
    DomainType.LEGAL: LegalDomainAdapter,
    DomainType.NEW_DOMAIN: NewDomainAdapter  # 新增
}
```

## 📈 监控和日志

### 监控指标
- API响应时间
- 查询成功率
- 领域使用分布
- 资源使用率

### 日志级别
- INFO: 一般信息
- WARNING: 警告信息
- ERROR: 错误信息
- DEBUG: 调试信息

## 🔒 安全考虑

- API密钥认证（可选）
- 输入长度限制
- SQL注入防护
- XSS防护
- 请求频率限制

## 🚨 错误处理

### 常见错误码
- 400: 请求参数错误
- 401: 未授权
- 404: 资源不存在
- 429: 请求过于频繁
- 500: 服务器内部错误
- 503: 服务不可用

### 错误响应格式
```json
{
  "error": "Invalid domain",
  "message": "不支持领域: xxx",
  "timestamp": "2024-12-15T10:15:00"
}
```

## 📝 更新日志

### v2.0.0 (2024-12-15)
- ✨ 新增多领域支持
- ✨ 实现领域适配器模式
- ✨ 支持跨领域混合搜索
- 🚀 优化性能和响应时间
- 📚 完善文档和示例

### v1.0.0 (2024-12-10)
- 🎉 初始版本发布
- ✨ 基础向量+知识图谱集成
- ✨ 专利领域支持

## 🤝 技术支持

- **文档**: [API文档](http://localhost:8002/docs)
- **健康检查**: http://localhost:8002/health
- **GitHub**: [项目地址](https://github.com/your-org/unified-intelligent-backend)

## 📄 许可证

MIT License