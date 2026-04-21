# WriterAgent - 小娜·撰写者

## 概述

WriterAgent（小娜·撰写者）是Athena平台中负责专利文书撰写和文档生成的核心智能体，专注于生成专业的专利申请文件和法律意见书。

## 核心能力

| 能力名称 | 描述 | 输入类型 | 输出类型 |
|---------|-----|---------|---------|
| draft_claims | 撰写权利要求 | 技术方案+创新点 | 权利要求书 |
| generate_description | 生成说明书 | 技术交底书 | 完整说明书 |
| write_opinion | 撰写法律意见 | 分析结论 | 法律意见书 |

## 使用示例

```python
from core.agents.xiaona.writer_agent import WriterAgent

# 创建Agent实例
agent = WriterAgent(agent_id="writer_001")

# 撰写权利要求
request = {
    "technical_solution": "一种激光位移传感器",
    "innovation_points": ["高精度测量", "抗干扰设计"],
    "claim_count": 10
}

result = agent.execute(request)
```

## 配置参数

| 参数 | 类型 | 默认值 | 描述 |
|-----|------|-------|------|
| agent_id | str | 必填 | Agent唯一标识 |
| writing_style | str | "formal" | 撰写风格: formal/casual/academic |
| output_format | str | "markdown" | 输出格式: markdown/html/word |

## 认证状态

- **认证级别**: 🥉 Bronze
- **总分**: 69/100
- **接口合规性**: ✅ 25/25
- **测试覆盖率**: ✅ 20/20
- **代码质量**: ✅ 13/15

## 相关链接

- 源代码: `core/agents/xiaona/writer_agent.py`
- 测试文件: `tests/agents/test_writer_agent.py`
