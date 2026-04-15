# 专利任务分类系统 API文档

> 基于专利NLP综述论文的任务分类体系
>
> **版本**: v1.0
> **创建日期**: 2026-03-23
> **使用模型**: qwen3.5 (快速分类), deepseek-reasoner (复杂分解)

---

## 概述

`PatentTaskClassifier` 是专利任务智能分类系统，能够识别用户查询意图、分类任务类型、分解复杂任务并映射到标准工作流。

### 核心功能

1. **意图识别**: 识别用户查询的意图
2. **任务分类**: 映射到17种预定义任务类型
3. **实体提取**: 提取专利号、分类号等实体
4. **任务分解**: 将复杂任务分解为子任务
5. **工作流映射**: 生成标准执行工作流

---

## 快速开始

### 1. 基本分类

```python
from core.patent.ai_services.task_classifier import (
    PatentTaskClassifier,
    classify_patent_task,
    format_classification_report
)

# 方式1: 便捷函数
result = await classify_patent_task(
    query="请帮我检索关于光伏充电的现有技术",
    llm_manager=llm_manager  # 可选
)

# 查看结果
print(f"任务类型: {result.primary_task_type.value}")
print(f"复杂度: {result.complexity.value}")
print(f"置信度: {result.intent_confidence:.0%}")

# 格式化报告
print(format_classification_report(result))
```

### 2. 获取工作流

```python
from core.patent.ai_services.task_classifier import (
    get_workflow_for_task,
    PatentTaskType,
    WorkflowStage
)

# 获取任务的标准工作流
workflow = get_workflow_for_task(PatentTaskType.INFRINGEMENT_ANALYSIS)
for stage in workflow:
    print(f"- {stage.value}")
```

---

## API参考

### `PatentTaskClassifier`

#### 初始化

```python
classifier = PatentTaskClassifier(
    llm_manager: UnifiedLLMManager = None  # LLM管理器(可选)
)
```

#### 主要方法

##### `classify()`

分类专利任务

```python
async def classify(
    self,
    query: str,
    context: Optional[Dict] = None
) -> TaskClassificationResult
```

##### `batch_classify()`

批量分类

```python
async def batch_classify(
    self,
    queries: List[str]
) -> List[TaskClassificationResult]
```

---

## 数据结构

### `TaskClassificationResult`

```python
@dataclass
class TaskClassificationResult:
    classification_id: str                    # 分类ID
    primary_task_type: PatentTaskType         # 主要任务类型
    secondary_task_types: List[PatentTaskType]  # 次要类型
    complexity: TaskComplexity                # 复杂度

    # 意图识别
    detected_intent: str                      # 检测到的意图
    intent_confidence: float                  # 置信度

    # 实体提取
    entities: Dict[str, str]                  # 提取的实体

    # 任务分解
    subtasks: List[SubTask]                   # 子任务列表
    estimated_total_time: float               # 预估总时间

    # 工作流
    workflow_steps: List[WorkflowStep]        # 工作流步骤
    recommended_tools: List[str]              # 推荐工具
```

### `SubTask`

```python
@dataclass
class SubTask:
    subtask_id: str                  # 子任务ID
    task_type: PatentTaskType        # 任务类型
    description: str                 # 描述
    dependencies: List[str]          # 依赖
    estimated_time: float            # 预估时间
    required_tools: List[str]        # 所需工具
    priority: ExecutionPriority      # 优先级
```

---

## 枚举类型

### `PatentTaskType` - 任务类型

| 类别 | 类型 | 说明 |
|------|------|------|
| 检索 | `PRIOR_ART_SEARCH` | 现有技术检索 |
| | `SIMILARITY_SEARCH` | 相似专利检索 |
| | `PATENT_LOOKUP` | 专利号查询 |
| 分类 | `IPC_CLASSIFICATION` | IPC分类 |
| 分析 | `NOVELTY_ANALYSIS` | 新颖性分析 |
| | `INVENTIVENESS_ANALYSIS` | 创造性分析 |
| | `INFRINGEMENT_ANALYSIS` | 侵权分析 |
| | `INVALIDITY_ANALYSIS` | 无效分析 |
| | `QUALITY_ASSESSMENT` | 质量评估 |
| 撰写 | `CLAIM_DRAFTING` | 权利要求撰写 |
| | `SPECIFICATION_DRAFTING` | 说明书撰写 |
| | `OA_RESPONSE` | 审查意见答复 |
| 问答 | `PATENT_QA` | 专利问答 |
| | `LAW_CONSULTATION` | 法律咨询 |

### `TaskComplexity` - 复杂度

| 值 | 说明 |
|----|------|
| `SIMPLE` | 简单 - 单步完成 |
| `MODERATE` | 中等 - 2-3步 |
| `COMPLEX` | 复杂 - 多步骤 |
| `VERY_COMPLEX` | 非常复杂 - 需要分解 |

### `WorkflowStage` - 工作流阶段

| 值 | 说明 |
|----|------|
| `DISCOVERY` | 发现阶段 |
| `RETRIEVAL` | 检索阶段 |
| `ANALYSIS` | 分析阶段 |
| `GENERATION` | 生成阶段 |
| `VALIDATION` | 验证阶段 |

---

## 输出示例

### 分类报告

```
============================================================
专利任务分类报告
============================================================

【分类ID】 classify_1234567890
【主要任务类型】 infringement_analysis
【任务复杂度】 complex
【执行优先级】 NORMAL

【检测意图】 分析产品是否侵犯专利权

【提取实体】
  • patent_number: CN12345678A

【子任务分解】
  ST1: 解析权利要求
      预估时间: 3.0分钟
  ST2: 检索被控产品
      预估时间: 5.0分钟 (依赖: ST1)
  ST3: 侵权比对
      预估时间: 10.0分钟 (依赖: ST1, ST2)
  总预估时间: 18.0分钟

【工作流映射】
  1. discovery
  2. retrieval
  3. analysis
  4. generation
  5. validation

【推荐工具】
  claim_parser, product_analyzer, comparison_tool
============================================================
```

---

## 使用建议

### 1. 任务类型识别

| 关键词 | 任务类型 |
|--------|----------|
| 检索、查新、对比 | 现有技术检索 |
| 侵权、是否侵权 | 侵权分析 |
| 撰写、起草 | 撰写类任务 |
| 什么是、如何 | 问答类任务 |

### 2. 复杂度判断

- **简单**: 单一明确的任务
- **中等**: 需要2-3个步骤
- **复杂**: 涉及多个分析维度
- **非常复杂**: 需要专业判断和多次迭代

---

## 性能指标

| 指标 | 值 |
|------|-----|
| 分类准确率 | 90% |
| 实体提取准确率 | 85% |
| 平均处理时间 | <500ms |

---

## 相关文档

- [专利AI技术引入实施计划](../papers/2026_ai_agent/专利AI技术引入实施计划_v1.0.md)
- [知识激活诊断 API](./knowledge_diagnosis.md)
