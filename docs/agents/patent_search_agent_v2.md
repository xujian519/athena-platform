# PatentSearchAgentV2 - 专利搜索专家

## 概述

PatentSearchAgentV2是Athena平台的专利检索专家Agent，提供专业的专利数据库检索和分析服务。

## 核心能力

| 能力名称 | 描述 | 输入类型 | 输出类型 |
|---------|-----|---------|---------|
| keyword_search | 关键词搜索 | 查询关键词 | 专利列表 |
| applicant_search | 申请人检索 | 公司名称 | 申请人专利库 |
| advanced_search | 高级检索 | 复合检索式 | 精准结果 |

## 使用示例

```python
from core.patent.patent_search_agent_v2 import PatentSearchAgentV2

# 创建Agent
agent = PatentSearchAgentV2(agent_id="search_001")

# 关键词搜索
request = {
    "query": "machine learning",
    "search_type": "keyword",
    "limit": 50
}

result = agent.execute(request)
```

## 支持的数据库

- CNIPA (中国国家知识产权局)
- WIPO (世界知识产权组织)
- EPO (欧洲专利局)
- USPTO (美国专利商标局)

## 认证状态

- **认证级别**: 🥉 Bronze
- **总分**: 73/100
- **接口合规性**: ✅ 25/25
- **测试覆盖率**: ✅ 20/20
- **代码质量**: ✅ 14/15

## 相关链接

- 源代码: `core/patent/patent_search_agent_v2.py`
- 测试文件: `tests/agents/test_patent_search_agent_v2.py`
