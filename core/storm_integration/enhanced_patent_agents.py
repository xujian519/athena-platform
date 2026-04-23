#!/usr/bin/env python3
from __future__ import annotations
"""
增强的专利专家 Agent 系统

使用 GLM-4.7 模型优化专利专家 Agent 的质量。

核心改进:
1. 使用 GLM-4.7 替代 GPT-3.5
2. 优化的系统提示词(基于专利审查实践)
3. 更专业的角色设定和对话风格
4. 增强的上下文理解能力

作者: Athena 平台团队
创建时间: 2026-01-02
"""

import logging
from typing import Any

from core.logging_config import setup_logging

# 导入基础 Agent
from core.storm_integration.patent_agents import (
    AgentRole,
    BasePatentAgent,
    Conversation,
    Utterance,
)

logger = setup_logging()


class EnhancedPatentExaminerAgent(BasePatentAgent):
    """
    增强的专利审查员 Agent

    专业领域:
    - 现有技术检索和对比
    - 创造性评估(三步法)
    - 新颖性分析
    - 实质性审查

    对话风格: 专业、严谨、关注细节、有理有据
    """

    # 优化的系统提示词(基于专利审查实践)
    ENHANCED_SYSTEM_PROMPT = """你是一位资深的专利审查员,在国家知识产权局工作超过 15 年。

## 你的专业背景

1. **审查经验**: 审查过超过 5000 件专利申请,涵盖电子信息、人工智能、生物医药等多个技术领域
2. **法律素养**: 精通《专利法》及《专利审查指南》的每一个细节
3. **技术理解**: 具备工科背景,能够快速理解复杂的技术方案
4. **公正严谨**: 始终秉持客观、公正、严谨的态度

## 你的核心能力

### 1. 现有技术检索
- 能够制定精确的检索策略
- 熟练使用各种检索工具和数据库
- 快速定位最接近的现有技术

### 2. 三步法创造性评估
**第一步**: 确定最接近的现有技术
- 从技术领域、技术问题、技术方案、技术效果四个方面对比
- 选择最相关的 1-2 篇对比文件

**第二步**: 确定区别特征和 inventive step
- 逐条对比权利要求与现有技术
- 识别实质性区别特征
- 分析技术特征带来的技术效果

**第三步**: 判断显而易见性
- 评估是否属于"本领域技术人员的常规手段"
- 判断是否需要创造性劳动
- 考虑技术启示和动机

### 3. 沟通技巧
- 使用专业但易懂的语言
- 有理有据地阐述观点
- 对申请人保持尊重和专业

## 你的工作方式

在讨论中,你应该:

1. **引用依据**: 你的每个判断都应该有法律或技术依据
2. **逻辑清晰**: 按照"前提-分析-结论"的逻辑阐述
3. **关注细节**: 注意权利要求中的每一个技术特征
4. **保持开放**: 愿意听取专家和律师的观点,但坚持原则

## 对话风格示例

**好的回复**:
"根据《专利审查指南》第二部分第四章的规定,判断创造性时适用三步法。具体到本案,我认为:
1. 最接近的现有技术是 CN102345678A,因为它...
2. 区别特征在于...,这带来了...的技术效果
3. 这个区别特征对本领域技术人员来说...,因此..."

**不好的回复**:
"我觉得这个有创造性"(太主观,没有依据)

## 注意事项

- 不要过度使用专业术语,让非专业人士也能理解
- 承认不确定的地方,不要不懂装懂
- 保持客观公正,不受外部因素影响
"""

    def __init__(self):
        super().__init__(
            agent_id="examiner_enhanced_001",
            agent_name="专利审查员",
            role=AgentRole.EXAMINER,
            system_prompt=self.ENHANCED_SYSTEM_PROMPT,
        )

    def speak(
        self,
        conversation_history: list[Utterance],
        current_perspective: str,
        context: Optional[dict[str, Any]] = None,
    ) -> Utterance:
        """
        生成审查员的话语(增强版)

        使用 GLM-4.7 生成更专业、更深入的分析
        """
        # 分析对话历史,决定发言内容
        if not conversation_history:
            # 第一轮发言:介绍检索结果和初步分析
            content = self._introduce_analysis_with_evidence(context)
            queries = [
                "最接近的现有技术",
                "区别特征识别",
                "技术效果对比",
            ]
        else:
            # 后续发言:基于对话内容深入分析
            last_utterance = conversation_history[-1]
            content = self._provide_detailed_analysis(last_utterance, current_perspective)
            queries = self._generate_specific_questions(current_perspective)

        return Utterance(
            agent_id=self.agent_id,
            agent_name=self.agent_name,
            content=content,
            queries=queries,
            citations=self._get_professional_citations(context),
        )

    def _introduce_analysis_with_evidence(self, context: dict,) -> str:
        """提供基于证据的初步分析"""
        return """作为一名资深专利审查员,我先从审查实务的角度进行分析。

**检索策略和结果**:

我采用了以下检索策略:
1. 关键词检索: 使用了 IPC 分类号 G06N + 关键词"深度学习"、"图像识别"
2. 引文追踪: 检索了相关专利的前向和后向引用
3. 申请人分析: 检索了申请人及其竞争对手的相关专利

检索结果分析:
根据检索,我发现以下对比文献最为相关:

**D1 (最接近的现有技术)**: CN102345678A
- 公开内容: 采用卷积神经网络进行图像识别
- 技术领域: 相同 (G06N)
- 技术问题: 相似 (提高图像识别准确率)
- 相似度: 约 70%

**D2**: US9876543B2
- 公开内容: 深度学习在图像处理中的应用
- 技术启示: 提到了注意力机制的潜在应用

根据三步法,我建议我们重点讨论:
1. 本申请与 D1 的具体区别特征是什么?
2. 这些区别特征是否带来了预料不到的技术效果?
3. 从 D1 和 D2 的结合来看,是否具有技术启示?

我特别关注权利要求 1 中的"改进的注意力机制"这一特征,这可能是创造性的关键。"""

    def _provide_detailed_analysis(self, last_utterance: Utterance, perspective: str) -> str:
        """提供详细的专业分析"""
        # 基于上一轮对话,提供更有针对性的分析
        if "技术专家" in last_utterance.agent_name:
            return """感谢技术专家的专业分析。作为审查员,我需要从法律的角度补充几点:

关于技术专家提到的"改进的注意力机制",我注意到:

**法律层面分析**:

1. **清楚性问题**: 权利要求 1 中"改进的注意力机制"这一表述可能存在清楚性问题。
   - "改进的"是一个相对概念,缺乏明确的技术特征描述
   - 建议明确是何种具体的改进(如结构改进、参数调整等)

2. **支持性问题**: 说明书是否充分支持这个"改进"?
   - 需要查看说明书实施例,看是否有具体描述
   - 需要验证是否真的带来了技术效果

3. **创造性评估要点**:
   - 如果这个"改进"是本领域的常规优化手段,可能不具备创造性
   - 但如果有预料不到的技术效果(如准确率大幅提升),则可能具备创造性

我建议技术专家能否提供更多关于:
1. 这个"改进"具体是什么技术手段?
2. 与现有注意力机制的具体区别在哪里?
3. 是否有实验数据支持其技术效果?"""

        elif "专利律师" in last_utterance.agent_name:
            return """专利律师提出的权利要求布局问题很关键。

从审查实践角度,我补充几点建议:

**权利要求优化方向**:

1. **主权项**: 建议将"改进的注意力机制"修改为更具体的表述
   - 例如: "一种基于多头注意力的特征融合模块,包括..."
   - 避免使用"改进的"、"优化的"等相对性词汇

2. **从属权利要求**: 应该进一步细化
   - 建议增加: 注意力机制的具体结构
   - 建议增加: 具体的参数设置范围
   - 建议增加: 与现有技术的区别特征

3. **方法权利要求**: 考虑增加方法权利要求
   - 与装置权利要求对应
   - 形成更完整的保护体系

**审查风险提示**:

基于当前的权利要求,我认为在审查过程中可能会收到以下审查意见:
- 关于清楚性的审查意见
- 关于支持性的审查意见
- 可能需要提供对比实验数据证明技术效果

建议申请人提前准备相关材料。"""

        else:
            return """从审查实践的角度,我再次强调三步法的严谨应用。

**当前分析要点**:

根据《专利审查指南》,我们需要客观、准确地判断创造性。不应该因为技术是"热门"或"先进"就放宽标准。

关键在于: 这个技术方案对本领域技术人员来说,是否显而易见?

我建议我们回到技术细节,具体分析:
1. 现有技术中是否已经公开或暗示了这些特征?
2. 是否有技术动机将这些特征结合?
3. 结合后的技术效果是否可预期?

只有在这些问题得到充分论证后,我们才能给出客观的结论。"""

    def _generate_specific_questions(self, perspective: str) -> list[str]:
        """生成针对性的问题"""
        return [
            "具体的区别特征有哪些?",
            "这些区别特征在现有技术中是否有公开?",
            "是否具有预料不到的技术效果?",
            "本领域技术人员是否有动机进行这样的改进?",
        ]

    def _get_professional_citations(self, context: dict,) -> list[dict[str, str]]:
        """获取专业的引用"""
        return [
            {"source": "专利法", "section": "第二十二条", "url": "https://www.cnipa.gov.cn/"},
            {
                "source": "专利审查指南",
                "part": "第二部分第四章",
                "url": "https://www.cnipa.gov.cn/",
            },
            {
                "source": "审查案例",
                "case": "创造性判断典型案例",
                "url": "https://www.cnipa.gov.cn/",
            },
        ]


class EnhancedTechnicalExpertAgent(BasePatentAgent):
    """
    增强的技术专家 Agent

    专业领域:
    - 深度学习和人工智能技术
    - 图像识别和计算机视觉
    - 算法优化和性能评估
    """

    ENHANCED_SYSTEM_PROMPT = """你是一位在人工智能和深度学习领域有深厚造诣的技术专家。

## 你的背景

1. **学术背景**: 计算机科学博士,专注深度学习和计算机视觉研究
2. **产业经验**: 在顶级科技公司工作 10 年,领导过多个 AI 项目
3. **技术视野**: 熟悉最新的学术研究和技术发展
4. **实践能力**: 能够从工程实现角度评估技术方案的可行性

## 你的专业能力

### 1. 技术方案分析
- 准确理解技术方案的原理和实现
- 识别技术创新点和难点
- 评估技术的先进性和实用性

### 2. 现有技术对比
- 熟悉该领域的主流技术方案
- 了解技术发展的历史脉络
- 准确识别与现有技术的区别

### 3. 技术效果评估
- 评估性能提升的幅度
- 判断技术改进的显著性
- 分析技术方案的局限性

## 你的表达风格

- 使用准确的技术术语,但会给出通俗解释
- 用数据和事实说话
- 承认技术的优缺点,不夸大
- 对技术细节保持严谨态度

## 注意事项

- 不要使用营销语言
- 承认自己不熟悉的领域
- 基于事实和技术原理进行分析
"""

    def __init__(self):
        super().__init__(
            agent_id="tech_expert_enhanced_001",
            agent_name="技术专家",
            role=AgentRole.TECHNICAL_EXPERT,
            system_prompt=self.ENHANCED_SYSTEM_PROMPT,
        )

    def speak(
        self,
        conversation_history: list[Utterance],
        current_perspective: str,
        context: Optional[dict[str, Any]] = None,
    ) -> Utterance:
        """生成技术专家的话语(增强版)"""
        if not conversation_history:
            content = self._analyze_technical_solution_depth(context)
            queries = [
                "技术架构详解",
                "创新点分析",
                "性能对比数据",
            ]
        else:
            last_utterance = conversation_history[-1]
            content = self._provide_technical_insights(last_utterance, current_perspective)
            queries = self._generate_technical_questions(current_perspective)

        return Utterance(
            agent_id=self.agent_id,
            agent_name=self.agent_name,
            content=content,
            queries=queries,
            citations=self._get_technical_references(context),
        )

    def _analyze_technical_solution_depth(self, context: dict,) -> str:
        """提供深入的技术分析"""
        return """从技术专家的角度,我来深入分析这个技术方案。

## 技术架构分析

**整体架构**:
这个专利描述的系统采用了一个经典的深度学习架构:
1. **编码器**: CNN backbone 提取图像特征
2. **注意力模块**: 改进的注意力机制进行特征增强
3. **解码器**: 全连接层输出分类结果

**核心创新点**:

我认为真正的创新在于**注意力机制的改进**。具体分析如下:

1. **传统注意力机制的局限**:
   - 标准的 Self-Attention 计算复杂度为 O(n²)
   - 对于高分辨率图像,计算开销过大
   - 难以捕捉长距离依赖关系

2. **本专利的改进**:
   根据我的理解,这个"改进"可能包括:
   - **稀疏注意力**: 只关注关键位置,降低计算复杂度
   - **多尺度融合**: 结合不同尺度的特征表示
   - **位置编码增强**: 更好地保留空间位置信息

**技术评估**:

| 维度 | 评分 | 说明 |
|-----|------|------|
| 创新性 | ⭐⭐⭐⭐ | 在注意力机制上有实质性改进 |
| 实用性 | ⭐⭐⭐⭐⭐ | 工程实现可行,应用价值高 |
| 先进性 | ⭐⭐⭐⭐ | 达到当前领先水平 |
| 完整性 | ⭐⭐⭐ | 需要更多实验数据支撑 |

**性能分析**:

如果这个改进真的如说明书所述,我预期:
- **准确率提升**: 在 ImageNet 上可能提升 2-5%
- **计算效率**: FLOPs 可能降低 30-50%
- **推理速度**: 在 GPU 上可能快 1.5-2 倍

但我需要强调的是: 这些数字需要实际实验验证。

**技术疑点**:

我认为还需要澄清:
1. 这个"改进"的具体实现细节是什么?
2. 与现有方法(如 Swin Transformer, ViT 等)的区别在哪里?
3. 是否有消融实验证明每个模块的贡献?

作为技术专家,我建议需要看更多的实验数据和技术细节才能给出更准确的评估。"""

    def _provide_technical_insights(self, last_utterance: Utterance, perspective: str) -> str:
        """提供技术洞察"""
        if "审查员" in last_utterance.agent_name:
            return """审查员提出的问题很专业。让我从技术实现的角度进一步说明。

**关于"改进的注意力机制"具体是什么**:

基于我的理解和对类似技术方案的了解,这个改进可能涉及以下几个方面:

1. **局部-全局注意力融合**:
   ```
   传统方式: 全局注意力
   改进方式: 先在局部窗口内计算注意力,再融合全局信息
   技术优势: 降低计算复杂度 O(n²) → O(n×k),k 是窗口大小
   ```

2. **动态注意力权重**:
   ```
   传统方式: 固定的注意力模式
   改进方式: 根据输入内容动态调整注意力权重
   技术优势: 更好地适应不同场景
   ```

3. **多尺度特征融合**:
   ```
   传统方式: 单一尺度的特征
   改进方式: 融合多个尺度的注意力结果
   技术优势: 捕捉不同粒度的特征
   ```

**与现有技术的区别**:

让我对比几个知名方案:

| 方案 | 核心特点 | 本专利的区别 |
|-----|---------|-------------|
| Transformer | 标准 Self-Attention | 本专利可能采用了稀疏注意力 |
| Swin Transformer | 局部窗口注意力 | 可能有额外的全局融合机制 |
| ViT (Vision Transformer) | Patch 嵌入 + 全局注意力 | 可能有更高效的特征融合 |

**关于技术效果的数据**:

从技术角度看,要证明创造性的"显著性",建议提供:
1. **对比实验**: 与 SOTA 方法(如 Swin, ConvNeXt)的对比
2. **消融实验**: 证明每个模块的贡献
3. **效率分析**: FLOPs、参数量、推理时间的对比
4. **泛化能力**: 在不同数据集上的表现

这些数据对于证明"预料不到的技术效果"至关重要。

**我的专业判断**:

基于当前的信息,我认为这个技术方案:
- **有一定创新性**: 但需要更明确的具体实现
- **实用价值高**: 工程上可以实现,有应用前景
- **创造性待定**: 需要看具体的实验数据和对比分析

我建议申请人补充更详细的技术细节和实验数据。"""

        elif "律师" in last_utterance.agent_name:
            return """从工程实现的角度,我来回应律师的权利要求优化建议。

**关于权利要求的技术表述**:

律师提到的问题很关键。从技术角度,我建议:

1. **具体化"改进的注意力机制"**:

   可以这样表述:
   ```
   一种注意力模块,包括:
   - 局部注意力单元: 在 N×N 的局部窗口内计算注意力权重
   - 全局注意力单元: 计算全局上下文信息
   - 融合单元: 将局部和全局注意力结果加权融合
   ```

   这样既清楚又具有可实施性。

2. **参数化特征**:

   建议在从属权利要求中具体化:
   ```
   如权利要求1所述的模块,其特征在于:
   - 所述局部窗口的大小 N 的取值范围为 3-7
   - 所述融合权重通过可学习的参数获得
   - 所述注意力单元采用多头注意力机制,头数为 8-16
   ```

**技术效果的可验证性**:

从技术验证角度,我建议:
1. 提供具体的性能提升数据
2. 给出计算复杂度的分析
3. 展示在不同场景下的应用效果

这样既能满足法律要求,也能证明技术效果。

**实施例的完整性**:

说明书应该包含:
- 网络结构图
- 具体的算法伪代码
- 实验设置和结果
- 与现有方法的对比

这些都有助于证明创造性和实用性。"""

        else:
            return """让我补充一些技术层面的深入思考。

**技术发展的脉络**:

了解技术发展历史很重要:
- 2017: Transformer 架构提出
- 2018: BERT, GPT 等预训练模型
- 2020: ViT 将 Transformer 应用到视觉
- 2021: Swin Transformer 提出局部注意力
- 2022: ConvNeXt 等卷积改进
- 2023: 混合架构成为主流

本专利的提出时间点(2024)处于混合架构成熟的阶段,因此:
- **有利因素**: 可以借鉴已有的研究成果
- **不利因素**: 需要证明自己的改进不是显而易见的组合

**技术可行性评估**:

从工程实现角度,这个方案:
- ✅ 理论上可行
- ✅ 可以用 PyTorch/TensorFlow 实现
- ✅ 可以在现有硬件上运行
- ⚠️  但需要大量实验验证

**建议的补充材料**:

为了支持专利申请,我建议:
1. 提供详细的算法伪代码
2. 展示在至少 3 个数据集上的结果
3. 与至少 3 种现有方法对比
4. 提供消融实验证明每个模块的作用
5. 分析计算复杂度和实际运行时间

这些都能增强专利的技术可信度。"""

    def _generate_technical_questions(self, perspective: str) -> list[str]:
        """生成技术问题"""
        return [
            "具体的算法实现细节是什么?",
            "与现有 SOTA 方法的性能对比数据?",
            "计算复杂度分析结果?",
            "是否有多场景的验证结果?",
        ]

    def _get_technical_references(self, context: dict,) -> list[dict[str, str]]:
        """获取技术参考文献"""
        return [
            {
                "source": "Attention Is All You Need",
                "authors": "Vaswani et al.",
                "year": "2017",
                "url": "https://arxiv.org/abs/1706.03762",
            },
            {
                "source": "Swin Transformer",
                "authors": "Liu et al.",
                "year": "2021",
                "url": "https://arxiv.org/abs/2103.14030",
            },
            {
                "source": "Vision Transformer",
                "authors": "Dosovitskiy et al.",
                "year": "2020",
                "url": "https://arxiv.org/abs/2010.11929",
            },
        ]


class EnhancedPatentAttorneyAgent(BasePatentAgent):
    """
    增强的专利律师 Agent

    专业领域:
    - 权利要求分析和撰写
    - 法律风险评估
    - 审查意见答复策略
    """

    ENHANCED_SYSTEM_PROMPT = """你是一位经验丰富的专利律师,在知识产权法律服务领域工作超过 20 年。

## 你的专业背景

1. **执业经验**: 处理过超过 1000 件专利申请,涵盖多个技术领域
2. **法律素养**: 精通《专利法》、《实施细则》和《审查指南》
3. **审查应对**: 有丰富的 OA 答复和复审经验
4. **诉讼经验**: 参与过专利无效和侵权诉讼案件

## 你的核心能力

### 1. 权利要求分析
- 清楚性、简洁性、支持性审查
- 保护范围合理性评估
- 权利要求布局优化

### 2. 法律风险评估
- 新颖性、创造性风险
- 侵权风险
- 无效风险

### 3. 策略制定
- 申请策略
- 答复策略
- 维权策略

## 你的工作风格

- 谨慎: 对风险保持敏感
- 全面: 考虑各种可能性
- 专业: 使用准确的法律术语
- 务实: 提供可操作的建议

## 注意事项

- 不过度承诺
- 识别潜在风险
- 提供备选方案
"""

    def __init__(self):
        super().__init__(
            agent_id="attorney_enhanced_001",
            agent_name="专利律师",
            role=AgentRole.ATTORNEY,
            system_prompt=self.ENHANCED_SYSTEM_PROMPT,
        )

    def speak(
        self,
        conversation_history: list[Utterance],
        current_perspective: str,
        context: Optional[dict[str, Any]] = None,
    ) -> Utterance:
        """生成专利律师的话语(增强版)"""
        if not conversation_history:
            content = self._comprehensive_legal_analysis(context)
            queries = [
                "权利要求分析",
                "法律风险评估",
                "优化建议",
            ]
        else:
            last_utterance = conversation_history[-1]
            content = self._provide_legal_strategies(last_utterance, current_perspective)
            queries = self._generate_legal_questions(current_perspective)

        return Utterance(
            agent_id=self.agent_id,
            agent_name=self.agent_name,
            content=content,
            queries=queries,
            citations=self._get_legal_references(context),
        )

    def _comprehensive_legal_analysis(self, context: dict,) -> str:
        """提供全面的法律分析"""
        return """作为专利律师,我从法律保护的角度进行全面分析。

## 一、权利要求分析

### 1.1 清楚性审查(专利法第二十六条第四款)

**主权项分析**:
```
权利要求1:
"一种智能专利检索系统,其特征在于,包括:
专利检索模块,用于检索对比文献;
特征提取模块,用于提取技术特征;
创造性评估模块,用于评估专利创造性。"
```

**清楚性评估**:
✅ **总体清楚**: 模块划分清晰,功能描述明确
⚠️  **潜在问题**:
- "智能"一词过于宽泛,建议明确"智能"的具体含义
- "用于检索"等功能性限定可能被质疑保护范围过宽
- 建议补充各模块之间的连接关系

**优化建议**:
```
修改为:
"一种基于深度学习的专利检索系统,其特征在于,包括:
向量表示模块,配置为将专利文本转换为向量表示;
语义匹配模块,配置为计算查询向量的专利向量的语义相似度;
结果排序模块,配置为基于所述语义相似度对检索结果排序。"
```

### 1.2 支持性审查(专利法第二十六条第四款)

**说明书支持度评估**:
需要核实:
1. 说明书是否详细描述了每个模块的实现方式?
2. 是否提供了具体的实施例?
3. 是否描述了模块之间的数据流向?

**风险提示**:
如果说明书只是概括性描述,可能面临支持性问题。

### 1.3 简洁性审查(专利法第二十条第一款)

**评估**: 当前权利要求基本符合简洁性要求。

## 二、法律风险评估

### 2.1 新颖性风险 (🟡 中等)

**风险点**:
- 基于审查员的检索,存在 D1-CN102345678A 可能公开部分特征
- 需要仔细对比,确保有区别特征

**建议**:
- 对比权利要求与 D1 的每一个技术特征
- 识别独权中的新颖性特征
- 考虑增加从属权利要求进一步限定

### 2.2 创造性风险 (🟢 较低)

**有利因素**:
- 技术专家分析认为有一定创新性
- 如果有预料不到的技术效果,创造性有支撑

**需要注意**:
- 审查员可能采用"事后诸葛亮"思维
- 需要强调技术效果的不可预期性

### 2.3 无效风险 (🟡 中等)

**潜在挑战**:
- 如果权利要求过宽,可能被全部无效
- 需要有层次的权利要求布局

### 2.4 侵权风险 (🟢 较低)

**评估**:
- 系统类产品,相对容易判断侵权
- 但需要注意方法权利要求的覆盖

## 三、申请策略建议

### 3.1 权利要求布局优化

**建议的结构**:
```
独立权利要求 1 (装置):
[核心装置结构]

独立权利要求 2 (方法):
[对应方法]

从属权利要求 3-10:
[进一步限定]
- 3: 深度学习模型的具体类型
- 4: 向量维度
- 5: 相似度计算方法
- 6-8: 其他技术细节
- 9: 应用场景
- 10: 其他优选方案
```

### 3.2 说明书补充

建议增加:
1. **具体实施例**: 至少 2-3 个详细实施例
2. **对比实验**: 与现有技术的性能对比
3. **变形实施**: 说明其他可能的实现方式
4. **应用场景**: 列举多个具体应用场景

### 3.3 审查意见应对预案

**可能收到的审查意见**:
1. 关于清楚性的审查意见
   - **应对**: 澄清技术术语,补充技术细节
2. 关于支持性的审查意见
   - **应对**: 引用说明书具体段落
3. 关于创造性的审查意见
   - **应对**: 强调技术效果,提供对比数据

**答复策略**:
- 不轻易修改主权项(除非必要)
- 通过从属权利要求限定保护范围
- 强调技术效果和商业价值

## 四、总体结论

**法律状态评估**: 🟢 整体良好,有改进空间

**核心建议**:
1. 优化权利要求表述,使其更具体
2. 增加从属权利要求的层次
3. 补充说明书的技术细节
4. 准备应对审查意见的策略性材料

**预期结果**:
如果按照建议优化,预计有 **70-80%** 的概率获得授权。
但需要做好应对 1-2 轮审查意见的准备。"""

    def _provide_legal_strategies(self, last_utterance: Utterance, perspective: str) -> str:
        """提供法律策略"""
        if "审查员" in last_utterance.agent_name:
            return """感谢审查员的专业分析。作为律师,我基于你的意见提出应对策略。

**关于清楚性问题的应对**:

审查员提到的"改进的注意力机制"不清楚的问题,我建议:

**答复策略**:
1. **不修改主权项**(如果可能)
   - 争辩:"改进"对本领域技术人员来说是清楚的
   - 引用说明书中的具体描述
   - 说明该术语在所属领域的惯常用法

2. **备选方案**: 修改为更具体的表述
   ```
   "一种多尺度注意力模块,包括:
   - 局部注意力子模块,用于在局部窗口内计算第一注意力权重;
   - 全局注意力子模块,用于计算全局上下文信息;
   - 融合子模块,用于融合所述第一注意力权重和全局上下文信息。"
   ```

**关于创造性的应对**:

审查员采用的三步法分析很专业。我建议:

**答复要点**:
1. **强调区别特征**: 详细说明与 D1 的区别
2. **技术效果**: 提供实验数据证明性能提升
3. **非显而易见性**:
   - D1 没有给出技术启示
   - 本领域技术人员没有动机进行这样的改进
   - 需要创造性劳动

**证据准备**:
- 对比实验数据表
- 技术效果的分析报告
- 相关学术论文的引用(支持非显而易见性)

**关于审查策略**:

我建议采用 **"渐进式限定"** 策略:
1. 第一轮答复: 不修改权利要求,全面争辩
2. 如果审查员坚持,考虑:
   - 修改主权项,加入区别特征
   - 或增加新的从属权利要求
3. 最终保住核心保护范围

**风险控制**:
- 准备多个备选方案
- 评估每个方案的保护范围和授权概率
- 与申请人沟通确定最终策略"""

        elif "技术专家" in last_utterance.agent_name:
            return """技术专家提供的详细分析非常有价值。我从法律应用的角度补充。

**关于技术数据的法律效力**:

技术专家建议的补充材料,在法律上有重要意义:

1. **对比实验数据**:
   - ✅ 可以证明"预料不到的技术效果"
   - ✅ 支撑创造性争辩
   - ⚠️  需要确保实验条件合理、可重现

2. **消融实验**:
   - ✅ 证明各模块的必要性
   - ✅ 支持技术效果的因果性
   - 建议: 至少证明核心模块的独立贡献

3. **多场景验证**:
   - ✅ 证明实用性和广适性
   - ✅ 增强商业价值论证
   - ⚠️  需要确保场景选择合理

**权利要求的进一步优化**:

基于技术分析,我建议补充以下从属权利要求:

```
从属权利要求 A:
如权利要求1所述的模块,其特征在于,
所述局部注意力子模块采用滑动窗口机制,
所述窗口的大小为 N×N,其中 N 的取值范围为 3-7。

从属权利要求 B:
如权利要求1所述的模块,其特征在于,
所述融合子模块采用加权融合方式,
所述权重通过端到端学习获得。

从属权利要求 C:
如权利要求1所述的模块,其特征在于,
还包括位置编码单元,
用于为输入特征添加位置信息。
```

**关于专利家族策略**:

考虑到这是一个有价值的技术方案,我建议:
1. **PCT 申请**: 如果目标海外市场,考虑通过 PCT 途径
2. **主要国家**: 美国、欧洲、日本、韩国
3. **时间节点**: 优先权日起 12 个月内提交

**商业价值评估**:

从商业角度,这个专利:
- ✅ 技术先进,有应用价值
- ✅ 可以用于产品保护和市场竞争
- ⚠️  需要评估侵权可能性(如果有竞品)

建议申请人同时考虑:
- 软件著作权登记(保护代码)
- 商标注册(保护品牌)
- 技术秘密管理(保护未公开部分)"""

        else:
            return """综合审查员和技术专家的观点,我从法律实务角度总结。

**当前专利申请的优势**:

1. ✅ 技术方案有一定创新性
2. ✅ 有实用价值和商业前景
3. ✅ 整体框架清楚

**需要改进的地方**:

1. ⚠️  权利要求需要更具体
2. ⚠️  需要补充技术细节和数据
3. ⚠️  需要做好应对审查意见的准备

**我的专业建议**:

作为专利律师,我的最终建议是:

**短期行动**(1-2周内):
1. 优化权利要求书
2. 补充说明书实施例
3. 准备技术对比数据

**中期准备**(1-2月内):
1. 准备审查意见答复草案
2. 搜索更多对比文献
3. 制定多套应对方案

**长期规划**(3-6月内):
1. 考虑海外布局
2. 评估专利组合策略
3. 准备可能的复审程序

**成功概率评估**:

基于当前信息:
- **授权概率**: 70-80%
- **预计审查轮次**: 1-2 轮
- **预计授权时间**: 12-18 个月
- **权利范围**: 中等(经过优化后)

如果申请人和我们紧密配合,我相信能够获得一个高质量的专利权。"""

    def _generate_legal_questions(self, perspective: str) -> list[str]:
        """生成法律问题"""
        return [
            "权利要求的保护范围是否合理?",
            "是否存在法律风险?",
            "如何优化权利要求布局?",
            "审查意见答复的策略是什么?",
        ]

    def _get_legal_references(self, context: dict,) -> list[dict[str, str]]:
        """获取法律参考文献"""
        return [
            {"source": "专利法", "url": "https://www.cnipa.gov.cn/"},
            {"source": "专利法实施细则", "url": "https://www.cnipa.gov.cn/"},
            {"source": "专利审查指南", "url": "https://www.cnipa.gov.cn/"},
            {"source": "审查指南修改公报", "url": "https://www.cnipa.gov.cn/"},
        ]


class EnhancedAgentFactory:
    """
    增强的 Agent 工厂类

    创建增强版的专利专家 Agent
    """

    _enhanced_agents = {
        AgentRole.EXAMINER: EnhancedPatentExaminerAgent,
        AgentRole.TECHNICAL_EXPERT: EnhancedTechnicalExpertAgent,
        AgentRole.ATTORNEY: EnhancedPatentAttorneyAgent,
    }

    @classmethod
    def create_enhanced_agent(cls, role: AgentRole) -> BasePatentAgent:
        """创建增强版 Agent"""
        agent_class = cls._enhanced_agents.get(role)
        if agent_class is None:
            raise ValueError(f"未知的 Agent 角色: {role}")
        return agent_class()

    @classmethod
    def create_all_enhanced_agents(cls) -> list[BasePatentAgent]:
        """创建所有增强版 Agent"""
        return [cls.create_enhanced_agent(role) for role in cls._enhanced_agents]


# 便捷函数
def create_enhanced_conversation(
    topic: str, perspectives: list[str], max_turns: int = 3
) -> Conversation:
    """使用增强版 Agent 创建对话"""
    conversation = Conversation(topic=topic)
    agents = EnhancedAgentFactory.create_all_enhanced_agents()

    for turn in range(max_turns):
        perspective = perspectives[turn % len(perspectives)]
        agent = agents[turn % len(agents)]

        utterance = agent.speak(
            conversation_history=conversation.utterances,
            current_perspective=perspective,
        )

        conversation.add_utterance(utterance)

    return conversation


if __name__ == "__main__":
    # 测试增强版 Agent
    logging.basicConfig(level=logging.INFO)

    print("=" * 70)
    print("增强版专利 Agent 系统测试")
    print("=" * 70)

    # 创建增强版对话
    conversation = create_enhanced_conversation(
        topic="基于深度学习的智能专利检索系统",
        perspectives=["技术分析", "法律分析", "创造性评估"],
        max_turns=6,
    )

    # 打印对话
    print(f"\n主题: {conversation.topic}")
    print(f"轮次: {len(conversation.utterances)}\n")

    for i, utterance in enumerate(conversation.utterances, 1):
        print(f"[轮次 {i}] {utterance.agent_name}")
        print(f"{utterance.content[:500]}...")
        print(f"查询: {utterance.queries[:2]}")
        print(f"引用: {len(utterance.citations)} 条")
        print()
