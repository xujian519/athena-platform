# RetrieverAgent - 小娜·检索者

## 概述

RetrieverAgent（小娜·检索者）是Athena平台中负责专利检索任务的核心智能体，专注于为专利分析和无效宣告提供高质量的对比文件检索服务。

## 核心能力

| 能力名称 | 描述 | 输入类型 | 输出类型 | 预计时间 |
|---------|-----|---------|---------|---------|
| patent_search | 专利检索 | 查询关键词、技术领域 | 专利列表、检索报告 | 15秒 |
| keyword_expansion | 关键词扩展 | 初始关键词 | 扩展关键词列表 | 5秒 |
| document_filtering | 对比文件筛选 | 专利列表、筛选标准 | 筛选后的专利列表 | 10秒 |

## 使用示例

```python
from core.agents.xiaona.retriever_agent import RetrieverAgent

# 创建Agent实例
agent = RetrieverAgent(agent_id="retriever_001")

# 执行专利检索
request = {
    "query": "激光位移传感器",
    "databases": ["cnipa", "wipo"],
    "limit": 20
}

result = agent.execute(request)
print(result)
```

## 配置参数

| 参数 | 类型 | 默认值 | 描述 |
|-----|------|-------|------|
| agent_id | str | 必填 | Agent唯一标识 |
| max_results | int | 100 | 最大检索结果数 |
| timeout | int | 30 | 检索超时时间（秒） |
| enable_cache | bool | True | 是否启用缓存 |

## 输入规范

### 专利检索请求
```json
{
  "query": "检索关键词",
  "databases": ["cnipa", "wipo", "epo"],
  "date_range": "2020-2024",
  "limit": 50,
  "filters": {
    "status": "granted",
    "country": "CN"
  }
}
```

## 输出格式

```json
{
  "status": "success",
  "results": [
    {
      "patent_id": "CN123456789A",
      "title": "专利标题",
      "abstract": "摘要内容",
      "relevance_score": 0.95
    }
  ],
  "total_count": 42,
  "execution_time": 12.3
}
```

## 认证状态

- **认证级别**: 🥉 Bronze
- **总分**: 69/100
- **接口合规性**: ✅ 25/25
- **测试覆盖率**: ✅ 20/20
- **代码质量**: ✅ 13/15
- **文档完整性**: ✅ 10/10
- **最佳实践**: ⚠️ 4/10
- **安全检查**: ✅ 7/10

## 相关链接

- 源代码: `core/agents/xiaona/retriever_agent.py`
- 测试文件: `tests/agents/test_retriever_agent.py`
- 基类: `core/agents/xiaona/base_component.py`
