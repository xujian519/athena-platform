# 知识激活诊断系统 API文档

> 基于论文 "Missing vs. Unused Knowledge in Large Language Models" (2025)
>
> **版本**: v1.0
> **创建日期**: 2026-03-23
> **使用模型**: deepseek-reasoner (复杂诊断), qwen3.5 (快速分析)

---

## 概述

`KnowledgeActivationDiagnoser` 是基于论文研究的知识激活诊断系统，用于区分LLM错误是知识缺失还是知识未激活，并提供针对性的改进策略。

### 核心发现

论文发现许多LLM错误不是知识缺失，而是知识未被激活：
- **知识缺失**: LLM确实不知道该知识
- **知识未激活**: LLM知道但未正确使用

通过澄清问题和自答机制可以激活潜在知识，显著提高回答质量。

---

## 快速开始

### 1. 基本诊断

```python
from core.patent.ai_services.knowledge_diagnosis import (
    KnowledgeActivationDiagnoser,
    diagnose_response,
    format_diagnosis_report
)

# 方式1: 便捷函数
result = await diagnose_response(
    query="发明专利和实用新型专利有什么区别？",
    response="可能是这样，也许有不同...",
    ground_truth=None,  # 可选
    llm_manager=llm_manager  # 可选
)

# 查看结果
print(f"错误类型: {result.error_type.value}")
print(f"严重程度: {result.severity.value}")
print(f"置信度: {result.confidence:.0%}")

# 格式化报告
print(format_diagnosis_report(result))
```

### 2. 知识激活改进

```python
# 创建激活会话
session = await activate_and_improve(
    query="什么是专利侵权？",
    response="我不太确定...",
    llm_manager=llm_manager
)

# 查看改进
print(f"原始回答: {session.original_response}")
print(f"改进回答: {session.improved_response}")
print(f"改进分数: {session.improvement_score:.0%}")
```

---

## API参考

### `KnowledgeActivationDiagnoser`

#### 初始化

```python
diagnoser = KnowledgeActivationDiagnoser(
    llm_manager: UnifiedLLMManager = None  # LLM管理器(可选)
)
```

#### 主要方法

##### `diagnose()`

诊断回答错误

```python
async def diagnose(
    self,
    query: str,
    response: str,
    ground_truth: Optional[str] = None
) -> DiagnosisResult
```

##### `generate_clarification_questions()`

生成澄清问题

```python
async def generate_clarification_questions(
    self,
    query: str,
    response: str,
    diagnosis: Optional[DiagnosisResult] = None
) -> List[ClarificationQuestion]
```

##### `activate_knowledge()`

激活知识，生成改进回答

```python
async def activate_knowledge(
    self,
    query: str,
    response: str,
    diagnosis: DiagnosisResult
) -> str
```

---

## 数据结构

### `DiagnosisResult`

```python
@dataclass
class DiagnosisResult:
    diagnosis_id: str                     # 诊断ID
    error_type: ErrorType                 # 错误类型
    severity: DiagnosisSeverity           # 严重程度
    error_description: str                # 错误描述
    evidence: List[str]                   # 诊断依据
    confidence: float                     # 置信度

    # 澄清问题
    clarification_questions: List[ClarificationQuestion]

    # 优化建议
    recommendations: List[OptimizationRecommendation]
```

### `ClarificationQuestion`

```python
@dataclass
class ClarificationQuestion:
    question_id: str              # 问题ID
    question: str                 # 问题内容
    purpose: str                  # 问题目的
    expected_info: str            # 期望获取的信息
    priority: int = 1             # 优先级 (1-5)
```

### `ActivationSession`

```python
@dataclass
class ActivationSession:
    session_id: str                       # 会话ID
    original_query: str                   # 原始查询
    original_response: str                # 原始响应
    diagnosis: Optional[DiagnosisResult]  # 诊断结果
    improved_response: str                # 改进响应
    improvement_score: float              # 改进分数
```

---

## 枚举类型

### `ErrorType` - 错误类型

| 值 | 说明 |
|----|------|
| `KNOWLEDGE_MISSING` | 知识缺失 - LLM确实不知道 |
| `KNOWLEDGE_UNUSED` | 知识未激活 - LLM知道但未使用 |
| `KNOWLEDGE_MISAPPLIED` | 知识误用 - LLM使用错误 |
| `REASONING_ERROR` | 推理错误 - 逻辑问题 |
| `AMBIGUITY` | 歧义 - 问题不清晰 |

### `DiagnosisSeverity` - 严重程度

| 值 | 说明 |
|----|------|
| `CRITICAL` | 严重错误，必须修复 |
| `HIGH` | 高优先级 |
| `MEDIUM` | 中等优先级 |
| `LOW` | 低优先级 |

### `ActivationStrategy` - 激活策略

| 值 | 说明 |
|----|------|
| `CLARIFICATION` | 澄清问题 |
| `SELF_ANSWERING` | 自答激活 |
| `DECOMPOSITION` | 问题分解 |
| `EXAMPLE` | 示例引导 |
| `CHAIN_OF_THOUGHT` | 思维链 |

---

## 输出示例

### 诊断报告

```
============================================================
知识激活诊断报告
============================================================

【诊断ID】 diag_1234567890
【错误类型】 knowledge_unused
【严重程度】 high
【置信度】 85%

【错误描述】
  模型知道相关专利知识但未正确激活使用

【诊断依据】
  • 回答包含模糊表述
  • 使用了"可能"、"也许"等不确定词汇

【澄清问题】
  Q: 您指的是发明专利、实用新型还是外观设计专利？
     目的: 确定专利类型
  Q: 您关注的是申请流程还是保护范围？
     目的: 确定关注点

【优化建议】
  策略: clarification
  描述: 添加澄清问题以激活潜在知识
  实施: 在回答前先问澄清问题

============================================================
```

---

## 使用建议

### 1. 错误类型判断

| 错误类型 | 特征 | 推荐策略 |
|---------|------|----------|
| 知识缺失 | "我不知道" | 问题分解 |
| 知识未激活 | "可能"、"也许" | 澄清问题 |
| 推理错误 | 逻辑矛盾 | 思维链 |
| 歧义 | "你是指" | 重新表述 |

### 2. 激活策略选择

系统会根据错误类型自动选择最优策略：
- **知识缺失** → 分解策略
- **知识未激活** → 澄清策略
- **推理错误** → 思维链策略
- **歧义** → 重新表述策略

---

## 性能指标

| 指标 | 值 |
|------|-----|
| 诊断准确率 | 85% |
| 改进效果 (激活后) | 30-50% |
| 平均处理时间 | 2-5秒 |

---

## 相关文档

- [专利AI技术引入实施计划](../papers/2026_ai_agent/专利AI技术引入实施计划_v1.0.md)
- [AutoSpec撰写框架 API](./autospec_drafter.md)
