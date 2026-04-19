# 综合质量评估增强系统 API文档

> 基于学术论文的专利质量评估框架
>
> **版本**: v1.0
> **创建日期**: 2026-03-23
> **使用模型**: qwen3.5 (快速评估), deepseek-reasoner (深度分析)

---

## 概述

`EnhancedQualityAssessor` 是综合质量评估系统，支持：
1. **多维度评估**: 8个质量维度的独立评估
2. **风险分析**: 识别和评估质量风险
3. **改进建议**: 生成优先级改进建议
4. **预测指标**: 有效性、可执行性、诉讼风险预测

### 核心功能

1. **完整评估**: 全面评估所有8个质量维度
2. **快速评估**: 仅评估核心3个维度
3. **专项评估**: 技术评估、法律评估、商业评估
4. **基准对比**: 与行业标准对比

---

## 快速开始

### 1. 基本评估

```python
from core.patent.ai_services.quality_assessment_enhanced import (
    EnhancedQualityAssessor,
    AssessmentType,
    format_assessment_report
)

# 创建评估器
assessor = EnhancedQualityAssessor()

# 执行评估
result = await assessor.assess(
    patent_number="CN1234567A",
    patent_data={
        "technical_features": ["特征1", "特征2", "特征3"],
        "claims": [{"type": "independent", "text": "权利要求"}],
        "description": "说明书内容"
    },
    assessment_type=AssessmentType.FULL
)

# 格式化报告
print(format_assessment_report(result))
```

### 2. 快速评估

```python
from core.patent.ai_services.quality_assessment_enhanced import (
    assess_patent_quality,
    AssessmentType
)

# 使用便捷函数
result = await assess_patent_quality(
    patent_number="CN1234567A",
    patent_data=patent_data,
    assessment_type=AssessmentType.QUICK
)

print(f"质量得分: {result.overall_score:.1f}")
print(f"质量等级: {result.overall_grade.value}")
```

---

## API参考

### `EnhancedQualityAssessor`

#### 初始化

```python
assessor = EnhancedQualityAssessor(
    llm_manager=None  # LLM管理器(可选)
)
```

#### 主要方法

##### `assess()`

执行质量评估

```python
async def assess(
    self,
    patent_number: str,                                    # 专利号
    patent_data: Dict[str, Any],                           # 专利数据
    assessment_type: AssessmentType = AssessmentType.FULL  # 评估类型
) -> EnhancedQualityAssessment
```

---

## 数据结构

### `EnhancedQualityAssessment`

评估结果

```python
@dataclass
class EnhancedQualityAssessment:
    assessment_id: str                    # 评估ID
    patent_number: str                    # 专利号
    assessment_type: AssessmentType       # 评估类型
    timestamp: datetime                   # 时间戳

    # 总体评估
    overall_score: float                  # 总分 0-100
    overall_grade: QualityGrade           # 质量等级
    confidence_level: float               # 置信度

    # 维度分数
    dimension_scores: List[DimensionScore]

    # 风险分析
    risks: List[QualityRisk]
    overall_risk_level: RiskLevel

    # 改进建议
    improvements: List[ImprovementSuggestion]

    # 基准对比
    benchmarks: List[BenchmarkComparison]

    # 预测
    predicted_validity: float             # 有效性概率
    predicted_enforceability: float       # 可执行性
    predicted_litigation_risk: float      # 诉讼风险
```

### `DimensionScore`

维度分数

```python
@dataclass
class DimensionScore:
    dimension: QualityDimension   # 维度
    score: float                  # 分数 0-100
    weight: float                 # 权重
    weighted_score: float         # 加权分数
    confidence: float             # 置信度
    analysis: str                 # 分析说明
    key_factors: List[str]        # 关键因素
```

---

## 枚举类型

### `QualityDimension` - 质量维度

| 维度 | 权重 | 说明 |
|------|------|------|
| `TECHNICAL_VALUE` | 20% | 技术价值 |
| `LEGAL_STABILITY` | 20% | 法律稳定性 |
| `COMMERCIAL_VALUE` | 15% | 商业价值 |
| `SCOPE_CLARITY` | 15% | 权利要求清晰度 |
| `DISCLOSURE_QUALITY` | 10% | 说明书质量 |
| `INNOVATION_LEVEL` | 10% | 创新程度 |
| `ENFORCEABILITY` | 5% | 可执行性 |
| `MARKET_RELEVANCE` | 5% | 市场相关性 |

### `QualityGrade` - 质量等级

| 等级 | 分数范围 |
|------|---------|
| `A+` (EXCELLENT) | ≥90 |
| `A` (VERY_GOOD) | 80-89 |
| `B+` (GOOD) | 70-79 |
| `B` (AVERAGE) | 60-69 |
| `C+` (BELOW_AVERAGE) | 50-59 |
| `C` (POOR) | 40-49 |
| `D` (VERY_POOR) | 30-39 |
| `F` (CRITICAL) | <30 |

### `AssessmentType` - 评估类型

| 类型 | 评估维度数 | 说明 |
|------|-----------|------|
| `FULL` | 8 | 完整评估 |
| `QUICK` | 3 | 快速评估 |
| `CLAIMS_ONLY` | 3 | 权利要求评估 |
| `TECHNICAL` | 3 | 技术评估 |
| `LEGAL` | 3 | 法律评估 |
| `COMMERCIAL` | 2 | 商业评估 |

### `RiskLevel` - 风险等级

| 等级 | 说明 |
|------|------|
| `LOW` | 低风险 |
| `MEDIUM` | 中风险 |
| `HIGH` | 高风险 |
| `CRITICAL` | 严重风险 |

---

## 使用示例

### 示例1: 完整评估

```python
from core.patent.ai_services.quality_assessment_enhanced import (
    assess_patent_quality,
    AssessmentType,
    format_assessment_report
)

# 准备专利数据
patent_data = {
    "technical_features": ["深度学习", "多模态融合", "注意力机制"],
    "technical_field": "人工智能",
    "embodiments": ["实施例1", "实施例2", "实施例3"],
    "claims": [
        {"type": "independent", "text": "一种方法，包括..."},
        {"type": "dependent", "text": "根据权利要求1..."}
    ],
    "description": "详细说明书" * 100,
    "figures": ["图1", "图2", "图3"],
    "keywords": ["新的", "改进", "优化"]
}

# 执行评估
result = await assess_patent_quality(
    patent_number="CN12345678A",
    patent_data=patent_data,
    assessment_type=AssessmentType.FULL
)

# 输出报告
print(format_assessment_report(result))
```

### 示例2: 风险分析

```python
# 查看风险
for risk in result.risks:
    print(f"[{risk.severity.value}] {risk.description}")
    print(f"  影响: {risk.impact}")
    print(f"  缓解: {risk.mitigation}")
```

### 示例3: 改进建议

```python
# 查看改进建议
for imp in result.improvements[:5]:
    print(f"[{imp.priority.value}] {imp.title}")
    print(f"  预期提升: +{imp.expected_improvement:.1f}")
    print(f"  工作量: {imp.effort_level}")
    print(f"  时间线: {imp.timeline}")
```

---

## 输出示例

### 评估报告

```
============================================================
专利质量评估报告
============================================================

【评估ID】 qa_1711234567890
【专利号】 CN1234567A
【评估类型】 full
【评估时间】 2026-03-23 15:30:00

【总体得分】 75.5
【质量等级】 B+
【置信度】 78%

【各维度得分】
------------------------------------------------------------
  technical_value           80.0 (权重: 20%)
  legal_stability           75.0 (权重: 20%)
  commercial_value          65.0 (权重: 15%)
  scope_clarity             78.0 (权重: 15%)
  disclosure_quality        72.0 (权重: 10%)
  innovation_level          70.0 (权重: 10%)
  enforceability            68.0 (权重: 5%)
  market_relevance          62.0 (权重: 5%)

【风险等级】 medium
【风险数量】 3 个

【改进建议】 5 条

【Top 3 改进建议】
  1. [high] 提升商业价值
     预期提升: +15.0
  2. [medium] 增强可执行性
     预期提升: +12.0
  3. [medium] 提高市场相关性
     预期提升: +10.0

【预测指标】
  有效性概率: 82.5%
  可执行性: 78.0%
  诉讼风险: 18.5%

------------------------------------------------------------
【处理耗时】 0.234 秒
============================================================
```

---

## 评估维度详解

### 1. 技术价值 (Technical Value)
- 技术特征丰富程度
- 技术领域热度
- 实施例数量

### 2. 法律稳定性 (Legal Stability)
- 权利要求数量和结构
- 独立权利要求设计
- 引用文献数量

### 3. 商业价值 (Commercial Value)
- 应用领域数量
- 专利族布局
- 许可情况

### 4. 权利要求清晰度 (Scope Clarity)
- 权利要求长度
- 术语定义
- 语言清晰度

### 5. 说明书质量 (Disclosure Quality)
- 说明书长度和详尽度
- 附图支持
- 实施例覆盖

### 6. 创新程度 (Innovation Level)
- 发明类型
- 创新关键词
- 技术问题解决

### 7. 可执行性 (Enforceability)
- 权利要求类型
- 侵权检测难度
- 保护范围

### 8. 市场相关性 (Market Relevance)
- 技术领域热度
- 申请时效性
- 市场需求

---

## 性能指标

| 指标 | 目标 | 说明 |
|------|------|------|
| 评估延迟 | <1s | 单次评估时间 |
| 准确率 | >80% | 评估结果一致性 |
| 建议相关性 | >85% | 改进建议实用性 |

---

## 相关文档

- [专利AI技术引入实施计划](../papers/2026_ai_agent/专利AI技术引入实施计划_v1.0.md)
- [任务分类 API](./task_classifier.md)
- [多模态检索 API](./multimodal_retrieval.md)
