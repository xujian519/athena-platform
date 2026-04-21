# XiaonuoAgentV2 - 小诺·协调者

## 概述

XiaonuoAgentV2（小诺·协调者V2）是Athena平台的任务协调和流程编排中心，负责协调多个Agent完成复杂的专利代理工作流程。

## 核心能力

| 能力名称 | 描述 | 输入类型 | 输出类型 |
|---------|-----|---------|---------|
| task_coordination | 任务协调 | 用户请求 | 协调结果 |
| workflow_execution | 工作流执行 | 工作流定义 | 执行结果 |
| agent_delegation | Agent委派 | 委派请求 | 委派结果 |

## 使用示例

```python
from core.agents.xiaonuo.xiaonuo_agent_v2 import XiaonuoAgentV2

# 创建协调者
agent = XiaonuoAgentV2(agent_id="xiaonuo_001")

# 执行协调任务
request = {
    "task": "专利检索+分析",
    "agents": ["retriever", "analyzer"],
    "parameters": {
        "query": "激光传感器"
    }
}

result = agent.execute(request)
```

## 支持的工作流

1. **检索分析流程**: retriever → analyzer → writer
2. **无效宣告流程**: analyzer → retriever → writer
3. **专利申请流程**: retriever → writer → reviewer

## 认证状态

- **认证级别**: 🥉 Bronze
- **总分**: 73/100
- **接口合规性**: ✅ 25/25
- **测试覆盖率**: ✅ 20/20
- **代码质量**: ✅ 14/15

## 相关链接

- 源代码: `core/agents/xiaonuo/xiaonuo_agent_v2.py`
- 测试文件: `tests/agents/test_xiaonuo_agent_v2.py`
