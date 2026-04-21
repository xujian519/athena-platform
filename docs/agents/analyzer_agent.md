# AnalyzerAgent - 小娜·分析者

## 概述

AnalyzerAgent（小娜·分析者）是Athena平台中负责专利技术分析和创新性评估的核心智能体，专注于对检索到的专利进行深度技术分析。

## 核心能力

| 能力名称 | 描述 | 输入类型 | 输出类型 |
|---------|-----|---------|---------|
| technical_analysis | 技术分析 | 专利文本 | 技术特征分析报告 |
- novelty_assessment | 新颖性评估 | 对比专利组 | 新颖性分析结论 |
| inventive_step | 创造性判断 | 技术方案+对比文件 | 创造性评估意见 |

## 使用示例

```python
from core.agents.xiaona.analyzer_agent import AnalyzerAgent

# 创建Agent实例
agent = AnalyzerAgent(agent_id="analyzer_001")

# 执行技术分析
request = {
    "patent_id": "CN123456789A",
    "contrast_patents": ["CN987654321A", "US20230012345A"],
    "analysis_type": "novelty"
}

result = agent.execute(request)
```

## 配置参数

| 参数 | 类型 | 默认值 | 描述 |
|-----|------|-------|------|
| agent_id | str | 必填 | Agent唯一标识 |
| analysis_depth | str | "standard" | 分析深度: basic/standard/deep |
| enable_llm | bool | True | 是否使用LLM增强分析 |

## 认证状态

- **认证级别**: 🥉 Bronze
- **总分**: 69/100
- **接口合规性**: ✅ 25/25
- **测试覆盖率**: ✅ 20/20
- **代码质量**: ✅ 13/15

## 相关链接

- 源代码: `core/agents/xiaona/analyzer_agent.py`
- 测试文件: `tests/agents/test_analyzer_agent.py`
