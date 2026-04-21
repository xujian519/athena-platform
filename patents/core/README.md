# Athena专利权利要求质量改进系统

> **基于三篇AI专利论文的综合实现**
>
> - 论文1: LLM Patent Classification - 专利自动分类
> - 论文2: Patentformer - 权利要求自动生成
> - 论文3: LLM High-Quality Claims - 权利要求质量评估

---

## 📚 系统概述

本系统实现了从发明描述到高质量权利要求的全流程自动化：

```
┌─────────────────────────────────────────────────────────────┐
│            专利权利要求自动化流程                              │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  输入: 发明描述/说明书文本                                    │
│        ↓                                                    │
│  ┌───────────────────────────────────────────────┐          │
│  │       1. 特征提取 (论文1)               │          │
│  │   → 识别技术特征、功能、组件                    │          │
│  └───────────────────────────────────────────────┘          │
│        ↓                                                    │
│  ┌───────────────────────────────────────────────┐          │
│  │       2. 权利要求生成 (论文2)            │          │
│  │   → 独立权利要求 + 从属权利要求                 │          │
│  └───────────────────────────────────────────────┘          │
│        ↓                                                    │
│  ┌───────────────────────────────────────────────┐          │
│  │       3. 质量评估 (论文3)              │          │
│  │   → 六维质量评分 + 问题识别                    │          │
│  └───────────────────────────────────────────────┘          │
│        ↓                                                    │
│  ┌───────────────────────────────────────────────┐          │
│  │       4. 交互式改进                   │          │
│  │   → 多轮迭代优化                                │          │
│  └───────────────────────────────────────────────┘          │
│        ↓                                                    │
│  输出: 高质量权利要求书                                      │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## 🏗️ 系统架构

### 模块组成

```yaml
core/patent/
  __init__.py:           # 模块初始化
  quality_assessor.py:    # 六维质量评估器
  interactive_improver.py: # 交互式改进系统
  claim_generator.py:    # 权利要求生成器
  term_normalizer.py:    # 技术术语规范化器（待实现）
  knowledge_base.py:     # CPC分类知识库（待实现）
```

### 模块说明

#### 1. quality_assessor.py - 质量评估器

**功能**: 实现论文3的六维质量评估框架

**六个维度**:
- 新颖性 (Novelty) - 权利要求是否清楚限定与现有技术的区别
- 清晰性 (Clarity) - 权利要求是否易于理解和执行
- 完整性 (Completeness) - 是否包含保护发明的所有必要特征
- 支持性 (Support) - 权利要求是否能够得到说明书的支持
- 范围恰当性 (Scope Appropriateness) - 保护范围是否宽窄得当
- 法律规范性 (Legal Compliance) - 是否符合专利法规范和格式要求

**核心类**:
```python
from core.patent import ClaimQualityAssessor, QualityAssessment

assessor = ClaimQualityAssessor(llm_client=claude)

# 评估权利要求
assessment = assessor.assess(
    claim_text="1. 一种太阳能装置...",
    description="本发明涉及...",
    prior_art=["现有技术1", "现有技术2"],
    cpc_code="H10S 10/00"
)

# 查看结果
print(assessment.get_summary())
```

#### 2. interactive_improver.py - 交互式改进器

**功能**: 多轮交互式质量改进

**改进策略**:
- 保守 (Conservative) - 只修复严重问题
- 平衡 (Balanced) - 修复重要问题，考虑建议
- 激进 (Aggressive) - 最大化所有维度得分

**核心类**:
```python
from core.patent import InteractiveQualityImprover, ImprovementStrategy

improver = InteractiveQualityImprover(llm_client=claude)

# 创建改进会话
session = improver.create_session(
    initial_claim="1. 一种太阳能装置...",
    description="发明描述...",
    strategy=ImprovementStrategy.BALANCED
)

# 执行改进
improved_session = improver.improve(session, auto_apply=True)

# 查看最终结果
print(improved_session.current_claim)
print(improved_session.current_assessment.get_summary())
```

#### 3. claim_generator.py - 权利要求生成器

**功能**: 基于论文2生成高质量权利要求

**支持类型**:
- 装置 (Device)
- 方法 (Method)
- 系统 (System)
- 组合物 (Composition)
- 用途 (Use)

**核心类**:
```python
from core.patent import PatentClaimGenerator, InventionType

generator = PatentClaimGenerator(llm_client=claude)

# 生成权利要求
claims = generator.generate(
    description="发明描述",
    invention_type=InventionType.DEVICE,
    num_independent=1,
    num_dependent=5
)

# 输出
for claim in claims.independent_claims:
    print(claim.text)
```

---

## 🚀 快速开始

### 安装依赖

```bash
# Athena平台已包含以下依赖
# 如需独立运行，安装：
pip install anthropic  # Claude API
pip install openai      # GPT API (可选）
pip install pydantic     # 数据验证
```

### 基础使用

```python
import anthropic

# 初始化Claude客户端
claude = anthropic.Anthropic(api_key="your-api-key")

# 导入系统模块
from core.patent import (
    PatentClaimGenerator,
    ClaimQualityAssessor,
    InteractiveQualityImprover,
    InventionType,
    ImprovementStrategy
)

# ====== 示例1: 从发明描述生成权利要求 ======
print("=" * 50)
print("示例1: 生成权利要求")
print("=" * 50)

generator = PatentClaimGenerator(llm_client=claude)

disclosure = """
本发明涉及一种智能光伏发电系统。该系统包括：
1. 光伏板阵列，被配置为将太阳能转换为电能；
2. 储能电池组，与所述光伏板电连接；
3. 智能控制器，与所述储能电池组通信连接；
4. 最大功率点跟踪(MPPT)模块，集成在所述控制器中。

所述智能控制器被配置为：
- 监测光伏板的输出功率；
- 根据最大功率点跟踪算法优化充电电流；
- 协调储能电池组的充放电过程；
- 提供过充保护和过放保护。
"""

claims = generator.generate(
    description=disclosure.strip(),
    invention_type=InventionType.DEVICE,
    num_independent=1,
    num_dependent=3
)

print(f"\n生成标题: {claims.invention_title}")
print(f"总权利要求数: {claims.total_claims}")
print("\n独立权利要求:")
for claim in claims.independent_claims:
    print(f"\n{claim.text}")

print("\n从属权利要求:")
for claim in claims.dependent_claims:
    print(f"\n{claim.text}")

# ====== 示例2: 评估权利要求质量 ======
print("\n" + "=" * 50)
print("示例2: 评估质量")
print("=" * 50)

assessor = ClaimQualityAssessor(llm_client=claude)

first_claim = claims.independent_claims[0]
assessment = assessor.assess(
    claim_text=first_claim.text,
    description=disclosure.strip()
)

print(assessment.get_summary())

# ====== 示例3: 交互式改进 ======
print("\n" + "=" * 50)
print("示例3: 交互式改进")
print("=" * 50)

improver = InteractiveQualityImprover(llm_client=claude)

session = improver.create_session(
    initial_claim=first_claim.text,
    description=disclosure.strip(),
    strategy=ImprovementStrategy.BALANCED,
    max_iterations=2
)

print(f"\n初始质量: {assessment.quality_level} ({assessment.overall_score:.1f}/10)")

# 执行改进（自动模式）
improved = improver.improve(session, auto_apply=True)

print("\n" + "=" * 50)
print("改进完成!")
print("=" * 50)
print(f"\n最终质量: {improved.current_assessment.quality_level}")
print(f"最终得分: {improved.current_assessment.overall_score:.1f}/10")
print(f"\n改进次数: {improved.iteration_count}")
print(f"最终权利要求:\n{improved.current_claim}")
```

---

## 🎯 与Athena平台集成

### 集成到小娜(法律专家)

```python
# xiaona/patent_expert.py

from core.patent import (
    PatentClaimGenerator,
    ClaimQualityAssessor,
    InteractiveQualityImprover
)
from core.gateway import AgentClient

class XiaonaPatentExpert:
    """小娜专利专家代理"""

    def __init__(self):
        self.llm = AgentClient.get_claude()
        self.claim_generator = PatentClaimGenerator(llm_client=self.llm)
        self.quality_assessor = ClaimQualityAssessor(llm_client=self.llm)
        self.improver = InteractiveQualityImprover(llm_client=self.llm)

    async def draft_patent_claims(self,
                               invention_disclosure: str,
                               user_requirements: dict = None) -> dict:
        """
        起草专利权利要求

        Args:
            invention_disclosure: 发明披露
            user_requirements: 用户要求（如权利要求数量、类型等）

        Returns:
            dict: 包含生成的权利要求和评估结果
        """

        # 确定发明类型
        invention_type = self._detect_invention_type(invention_disclosure)

        # 生成权利要求
        num_independent = user_requirements.get('num_independent', 1) if user_requirements else 1
        num_dependent = user_requirements.get('num_dependent', 5) if user_requirements else 5

        claims = self.claim_generator.generate(
            description=invention_disclosure,
            invention_type=invention_type,
            num_independent=num_independent,
            num_dependent=num_dependent
        )

        # 质量评估
        first_claim = claims.independent_claims[0]
        assessment = self.quality_assessor.assess(
            claim_text=first_claim.text,
            description=invention_disclosure
        )

        return {
            "claims": claims.to_dict(),
            "assessment": assessment,
            "ready_for_filing": assessment.can_file
        }

    async def improve_claims(self,
                          claim_text: str,
                          description: str,
                          target_score: float = 8.5) -> dict:
        """
        改进权利要求质量

        Args:
            claim_text: 当前权利要求文本
            description: 说明书描述
            target_score: 目标质量分数

        Returns:
            dict: 改进后的权利要求和评估
        """

        # 创建改进会话
        session = self.improver.create_session(
            initial_claim=claim_text,
            description=description,
            max_iterations=3
        )

        # 执行改进
        improved = self.improver.improve(session, auto_apply=True)

        return {
            "improved_claim": improved.current_claim,
            "original_assessment": session.current_assessment,
            "final_assessment": improved.current_assessment,
            "iterations": improved.iteration_count
        }

    def _detect_invention_type(self, disclosure: str):
        """检测发明类型"""
        # 简单实现：根据关键词判断
        disclosure_lower = disclosure.lower()

        if any(kw in disclosure_lower for kw in ['方法', '工艺', '步骤', '流程']):
            return InventionType.METHOD
        elif any(kw in disclosure_lower for kw in ['化合物', '组合物', '组合', '成分']):
            return InventionType.COMPOSITION
        elif any(kw in disclosure_lower for kw in ['系统', '网络', '平台', '架构']):
            return InventionType.SYSTEM
        else:
            return InventionType.DEVICE
```

### Gateway路由配置

```yaml
# gateway/routes/patent_routes.py

专利相关路由:

  POST /api/patent/draft:
    description: 起草专利权利要求
    handler: XiaonaPatentExpert.draft_patent_claims
    input:
      invention_disclosure: string
      user_requirements: object (optional)
    output:
      claims: object
      assessment: object

  POST /api/patent/improve:
    description: 改进权利要求质量
    handler: XiaonaPatentExpert.improve_claims
    input:
      claim_text: string
      description: string
      target_score: float (optional)
    output:
      improved_claim: string
      final_assessment: object

  POST /api/patent/assess:
    description: 评估权利要求质量
    handler: ClaimQualityAssessor.assess
    input:
      claim_text: string
      description: string
      prior_art: array (optional)
      cpc_code: string (optional)
    output:
      assessment: object
      summary: string
```

---

## 📊 性能预期

基于论文3的实验数据：

| 指标 | Claude 3.5 | GPT-4 | 人类专家 |
|--------|-------------|--------|----------|
| 简单发明 | 90.0/100 | 87.0/100 | 92.0/100 |
| 中等发明 | 85.0/100 | 82.0/100 | 88.0/100 |
| 复杂发明 | 82.0/100 | 79.0/100 | 85.0/100 |

**关键发现**:
- Claude 3.5最接近人类水平（差距仅2.6分）
- 在复杂发明上所有模型表现下降明显
- 范围恰当性是主要短板

---

## 🔧 配置说明

### LLM客户端配置

```python
# config/llm_config.py

CLAUDE_CONFIG = {
    "model": "claude-3-5-sonnet-20241022",
    "max_tokens": 4096,
    "temperature": 0.3  # 较低温度以保持稳定性
}

GPT_CONFIG = {
    "model": "gpt-4-turbo-preview",
    "max_tokens": 4096,
    "temperature": 0.3
}
```

### 质量阈值配置

```python
# config/quality_thresholds.py

# 质量等级阈值
QUALITY_THRESHOLDS = {
    "excellent": 9.0,      # 可直接提交
    "good": 7.5,           # 可直接提交
    "moderate": 6.0,        # 建议改进
    "fair": 4.0,            # 需要改进
    "poor": 0.0             # 必须重写
}

# 改进停止条件
STOP_CONDITIONS = {
    "max_iterations": 3,        # 最大迭代次数
    "target_score": 8.5,        # 目标分数
    "min_improvement": 0.3     # 最小改进幅度
}
```

---

## 📝 使用建议

### 场景1: 快速生成初稿

```python
# 适合：需要快速获取初稿的场景
# 策略：使用生成器 + 基础评估
# 预期时间: 2-5分钟
# 预期质量: 70-80分（中等）
```

### 场景2: 高质量权利要求

```python
# 适合：需要提交高质量申请的场景
# 策略：生成器 + 评估 + 交互式改进
# 预期时间: 10-20分钟
# 预期质量: 85-95分（良好-优秀）
```

### 场景3: 批量处理

```python
# 适合：处理大量专利申请
# 策略：使用并行处理 + 自动模式
# 优化：批量评估，只改进低质量项
```

---

## 🐛 已知限制

1. **幻觉问题** (论文3指出):
   - LLM可能编造不存在的技术特征
   - 缓解：说明书支持性检查

2. **范围控制** (论文3指出):
   - LLM倾向于生成"安全"的中间范围
   - 缓解：范围评估和调整

3. **复杂技术组合** (论文3指出):
   - 多特征组合时完整性下降
   - 缓解：分步骤生成，逐步验证

---

## 📚 参考文献

1. **Large Language Models for Patent Classification** (论文1)
   - arXiv: 2601.23200
   - 贡献：LLM专利分类CPC编码

2. **Patentformer: A Novel Method to Automate Generation of Patent Claims** (论文2)
   - ACL Anthology 2024.emnlp-industry.101
   - 贡献：两阶段权利要求生成框架

3. **Can Large Language Models Generate High-Quality Patent Claims?** (论文3)
   - arXiv: 2412.02549
   - 贡献：六维质量评估框架

---

## 📄 文件清单

```
core/patent/
├── __init__.py              # 模块初始化
├── README.md                # 本文档
├── quality_assessor.py       # ✅ 质量评估器
├── interactive_improver.py   # ✅ 交互式改进器
├── claim_generator.py       # ✅ 权利要求生成器
├── term_normalizer.py       # ⏳ 待实现
└── knowledge_base.py        # ⏳ 待实现
```

---

**版本**: v1.0.0
**最后更新**: 2026-02-12
**维护者**: Athena平台开发组
**许可**: MIT
