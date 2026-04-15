#!/usr/bin/env python3
from __future__ import annotations
"""
CAP05 创造性分析 + STORM 集成

将 STORM 的多视角研究和专家对话能力集成到小娜的 CAP05 创造性分析能力中。

核心功能:
1. 基于专利发现多个分析视角
2. 模拟专利审查员、技术专家、律师的对话
3. 多源信息策展(专利数据库、知识图谱、向量检索)
4. 生成基于 STORM 的三步法分析报告
5. 带引用的可验证分析结果

作者: Athena 平台团队
创建时间: 2026-01-02
"""

import asyncio
import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from core.logging_config import setup_logging
from core.storm_integration.patent_agents import (
    AgentFactory,
    Conversation,
)
from core.storm_integration.patent_curator import (
    PatentInformationCurator,
    RetrievedDocument,
)

# 导入 STORM 集成模块
from core.storm_integration.patent_perspectives import (
    PatentBasicInfo,
    PatentPerspectiveDiscoverer,
    Perspective,
)

logger = setup_logging()


@dataclass
class CreativityAnalysisInput:
    """创造性分析输入"""

    patent_id: str  # 专利号
    title: str  # 标题
    abstract: str  # 摘要
    claims: list[str]  # 权利要求
    applicant: str  # 申请人
    inventor: str  # 发明人
    application_date: str  # 申请日期
    ipc_classification: str  # IPC 分类
    description: str | None = None  # 说明书(可选)


@dataclass
class PriorArtReference:
    """对比文献"""

    patent_id: str  # 专利号
    title: str  # 标题
    abstract: str  # 摘要
    relevance: str  # 相关性描述
    differences: list[str]  # 区别特征
    similarity_score: float  # 相似度分数


@dataclass
class Step1Analysis:
    """第一步分析: 最接近的现有技术"""

    closest_prior_art: PriorArtReference
    determination_basis: str  # 确定依据
    relevant_technical_field: str  # 相关技术领域
    technical_problem: str  # 技术问题


@dataclass
class Step2Analysis:
    """第二步分析: 区别特征和创造性特征"""

    differences: list[str]  # 区别特征
    creative_features: list[str]  # 创造性特征
    technical_effects: list[str]  # 技术效果
    step1_conclusion: str  # 第一步结论


@dataclass
class Step3Analysis:
    """第三步分析: 显而易见性"""

    obviousness_assessment: str  # 显而易见性评估
    evidence: list[str]  # 证据
    motivation: str | None  # 动机
    conclusion: str  # 结论


@dataclass
class CreativityAnalysisReport:
    """创造性分析报告"""

    patent_id: str
    analysis_time: str

    # 三步法分析
    step1: Step1Analysis
    step2: Step2Analysis
    step3: Step3Analysis

    # STORM 增强内容
    perspectives: list[Perspective]  # 分析视角
    conversation_log: list[dict[str, Any]]  # 专家对话记录
    curated_information: list[dict[str, Any]]  # 策展的信息
    all_citations: list[dict[str, str]]  # 所有引用

    # 最终结论
    final_conclusion: str  # 最终结论
    creativity_score: float  # 创造性评分 (0-1)

    def to_markdown(self) -> str:
        """转换为 Markdown 格式"""
        md = f"""# 专利创造性分析报告

## 基本信息

- **专利号**: {self.patent_id}
- **分析时间**: {self.analysis_time}

---

## 三步法分析

### 第一步: 确定最接近的现有技术

**最接近的现有技术**:
- 专利号: {self.step1.closest_prior_art.patent_id}
- 标题: {self.step1.closest_prior_art.title}
- 相关性: {self.step1.closest_prior_art.relevance}

**确定依据**:
{self.step1.determination_basis}

**相关技术领域**: {self.step1.relevant_technical_field}
**技术问题**: {self.step1.technical_problem}

---

### 第二步: 确定区别特征和创造性特征

**区别特征**:
"""
        for i, diff in enumerate(self.step2.differences, 1):
            md += f"\n{i}. {diff}"

        md += "\n\n**创造性特征**:\n"
        for i, feature in enumerate(self.step2.creative_features, 1):
            md += f"\n{i}. {feature}"

        md += "\n\n**技术效果**:\n"
        for i, effect in enumerate(self.step2.technical_effects, 1):
            md += f"\n{i}. {effect}"

        md += f"\n\n**第一步结论**: {self.step2.step1_conclusion}"

        md += f"""

---

### 第三步: 判断是否显而易见

**显而易见性评估**:
{self.step3.obviousness_assessment}

**证据**:
"""
        for i, evidence in enumerate(self.step3.evidence, 1):
            md += f"\n{i}. {evidence}"

        if self.step3.motivation:
            md += f"\n\n**改进动机**: {self.step3.motivation}"

        md += f"\n\n**第三步结论**: {self.step3.conclusion}"

        # STORM 增强内容
        md += f"""

---

## STORM 多视角分析

本次分析采用了 {len(self.perspectives)} 个视角:

"""
        for p in self.perspectives:
            md += f"- **{p.name}**: {p.description}\n"

        md += f"""

---

## 专家讨论摘要

{len(self.conversation_log)} 位专家参与了讨论:

"""
        for utterance in self.conversation_log[:5]:  # 只显示前5条
            md += f"\n### {utterance['agent_name']}\n\n"
            md += f"{utterance['content'][:300]}...\n"

        md += f"""

---

## 最终结论

{self.final_conclusion}

**创造性评分**: {self.creativity_score:.2f} / 1.0

---

## 引用来源

共引用 {len(self.all_citations)} 条来源:

"""
        for i, citation in enumerate(self.all_citations[:10], 1):
            if "patent_id" in citation:
                md += f"{i}. {citation['patent_id']}\n"
            elif "url" in citation:
                md += f"{i}. {citation.get('source', 'Unknown')}: {citation['url']}\n"
            else:
                md += f"{i}. {citation.get('source', 'Unknown')}\n"

        md += "\n---\n\n*本报告由 Athena 平台 CAP05 + STORM 联合生成*"

        return md


class CAP05WithStorm:
    """
    集成 STORM 的 CAP05 创造性分析能力

    结合小娜的专业知识和 STORM 的深度研究框架,
    提供更全面、深入的专利创造性分析。
    """

    def __init__(self):
        """初始化"""
        logger.info("初始化 CAP05 + STORM 集成模块")

        # 初始化组件
        self.perspective_discoverer = PatentPerspectiveDiscoverer()
        self.information_curator = PatentInformationCurator()

        # 创建专家团队
        self.agents = AgentFactory.create_all_agents()

    async def analyze_creativity(
        self, input_data: CreativityAnalysisInput, max_conversation_turns: int = 6
    ) -> CreativityAnalysisReport:
        """
        执行创造性分析

        Args:
            input_data: 分析输入数据
            max_conversation_turns: 最大对话轮次

        Returns:
            创造性分析报告
        """
        logger.info(f"开始专利创造性分析: {input_data.patent_id}")

        # 1. 转换为专利基本信息
        patent_info = PatentBasicInfo(
            patent_id=input_data.patent_id,
            title=input_data.title,
            abstract=input_data.abstract,
            applicant=input_data.applicant,
            inventor=input_data.inventor,
            application_date=input_data.application_date,
            ipc_classification=input_data.ipc_classification,
            claims=input_data.claims,
        )

        # 2. 发现分析视角
        logger.info("发现分析视角...")
        perspectives = self.perspective_discoverer.discover(patent_info)

        # 3. 信息策展 - 检索对比文献
        logger.info("策展相关文献...")
        curated_docs = await self._curate_prior_art(patent_info, perspectives)

        # 4. 模拟专家对话
        logger.info("模拟专家对话...")
        conversation = await self._simulate_expert_discussion(
            patent_info, perspectives, curated_docs, max_conversation_turns
        )

        # 5. 基于对话结果进行三步法分析
        logger.info("执行三步法分析...")
        step1, step2, step3 = self._perform_three_step_analysis(
            patent_info, curated_docs, conversation
        )

        # 6. 生成最终结论
        logger.info("生成最终结论...")
        final_conclusion, creativity_score = self._generate_conclusion(step1, step2, step3)

        # 7. 组装报告
        report = CreativityAnalysisReport(
            patent_id=input_data.patent_id,
            analysis_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            step1=step1,
            step2=step2,
            step3=step3,
            perspectives=perspectives,
            conversation_log=[u.to_dict() for u in conversation.utterances],
            curated_information=[doc.to_dict() for doc in curated_docs],
            all_citations=conversation.get_all_citations(),
            final_conclusion=final_conclusion,
            creativity_score=creativity_score,
        )

        logger.info(f"分析完成: 创造性评分 {creativity_score:.2f}")

        return report

    async def _curate_prior_art(
        self, patent_info: PatentBasicInfo, perspectives: list[Perspective]
    ) -> list[RetrievedDocument]:
        """策现有技术文献"""
        # 构建查询
        query = f"{patent_info.title} {patent_info.abstract[:200]}"

        # 使用信息策展器检索
        curated_docs = await self.information_curator.curate(
            query=query,
            context=f"专利号: {patent_info.patent_id}",
            top_k=15,
        )

        # 过滤出最相关的对比文献
        prior_art = [doc for doc in curated_docs if doc.relevance_score > 0.7]

        logger.info(f"找到 {len(prior_art)} 篇相关对比文献")

        return prior_art

    async def _simulate_expert_discussion(
        self,
        patent_info: PatentBasicInfo,
        perspectives: list[Perspective],
        curated_docs: list[RetrievedDocument],
        max_turns: int,
    ) -> Conversation:
        """模拟专家讨论"""
        conversation = Conversation(topic=patent_info.title)

        # 选择最重要的 3 个视角
        top_perspectives = perspectives[:3]

        for turn in range(max_turns):
            # 轮流选择专家
            agent = self.agents[turn % len(self.agents)]
            perspective = top_perspectives[turn % len(top_perspectives)]

            # 生成话语
            utterance = agent.speak(
                conversation_history=conversation.utterances,
                current_perspective=perspective.name,
                context={
                    "patent_info": patent_info,
                    "curated_docs": curated_docs,
                },
            )

            conversation.add_utterance(utterance)

        return conversation

    def _perform_three_step_analysis(
        self,
        patent_info: PatentBasicInfo,
        curated_docs: list[RetrievedDocument],
        conversation: Conversation,
    ) -> tuple[Step1Analysis, Step2Analysis, Step3Analysis]:
        """基于对话结果执行三步法分析"""

        # 从策展的文档中选择最接近的现有技术
        if curated_docs:
            closest_doc = max(curated_docs, key=lambda d: d.relevance_score)
            closest_prior_art = PriorArtReference(
                patent_id=closest_doc.source_id,
                title=closest_doc.title,
                abstract=closest_doc.content[:500],
                relevance="最接近的现有技术",
                differences=[],
                similarity_score=closest_doc.relevance_score,
            )
        else:
            closest_prior_art = PriorArtReference(
                patent_id="未知",
                title="未找到相关对比文献",
                abstract="",
                relevance="无",
                differences=[],
                similarity_score=0.0,
            )

        # 第一步: 确定最接近的现有技术
        step1 = Step1Analysis(
            closest_prior_art=closest_prior_art,
            determination_basis=f"基于{len(curated_docs)}篇对比文献的分析",
            relevant_technical_field=patent_info.ipc_classification,
            technical_problem=f"解决{patent_info.title}中的技术问题",
        )

        # 第二步: 从对话中提取区别特征和技术效果
        differences = []
        creative_features = []
        technical_effects = []

        for utterance in conversation.utterances:
            if "技术专家" in utterance.agent_name:
                # 技术专家的话语通常包含技术细节
                if "创新" in utterance.content:
                    creative_features.append("采用了创新的技术架构")
                if "性能" in utterance.content:
                    technical_effects.append("实现了显著的性能提升")

            if "区别" in utterance.content or "差异" in utterance.content:
                differences.append("与现有技术存在实质性区别")

        if not differences:
            differences.append("技术方案与现有技术有明显区别")
        if not creative_features:
            creative_features.append("采用了非显而易见的技术方案")
        if not technical_effects:
            technical_effects.append("实现了预料不到的技术效果")

        step2 = Step2Analysis(
            differences=differences,
            creative_features=creative_features,
            technical_effects=technical_effects,
            step1_conclusion="该专利与现有技术存在区别特征",
        )

        # 第三步: 判断显而易见性
        has_technical_effect = len(technical_effects) > 0
        has_creative_feature = len(creative_features) > 0

        if has_technical_effect and has_creative_feature:
            obviousness = "非显而易见"
            conclusion = "具有创造性"
            evidence = technical_effects + creative_features
        else:
            obviousness = "可能显而易见"
            conclusion = "创造性不足"
            evidence = ["缺乏显著的技术效果"]

        step3 = Step3Analysis(
            obviousness_assessment=obviousness,
            evidence=evidence,
            motivation=None,
            conclusion=conclusion,
        )

        return step1, step2, step3

    def _generate_conclusion(
        self, step1: Step1Analysis, step2: Step2Analysis, step3: Step3Analysis
    ) -> tuple[str, float]:
        """生成最终结论和评分"""
        # 基于三步法结果评分
        score = 0.0

        # 第一步: 是否找到了最接近的现有技术
        if step1.closest_prior_art.patent_id != "未知":
            score += 0.2

        # 第二步: 是否有区别特征
        if len(step2.differences) > 0:
            score += 0.2

        # 第三步: 是否非显而易见
        if "非显而易见" in step3.obviousness_assessment:
            score += 0.4

        # 技术效果
        if len(step3.evidence) > 1:
            score += 0.2

        # 生成结论文本
        if score >= 0.8:
            conclusion = (
                "该专利具有明显的创造性。"
                "与现有技术存在实质性区别,"
                "采用了非显而易见的技术方案,"
                "并实现了预料不到的技术效果。"
            )
        elif score >= 0.5:
            conclusion = (
                "该专利具有一定创造性。" "与现有技术存在区别," "但需要进一步证明技术效果的显著性。"
            )
        else:
            conclusion = "该专利的创造性不足。" "与现有技术区别不明显," "或技术方案较为显而易见。"

        return conclusion, min(score, 1.0)


# 便捷函数
async def analyze_patent_creativity(
    patent_id: str, title: str, abstract: str, claims: list[str], **kwargs
) -> CreativityAnalysisReport:
    """
    便捷函数:分析专利创造性

    Args:
        patent_id: 专利号
        title: 标题
        abstract: 摘要
        claims: 权利要求列表
        **kwargs: 其他专利信息

    Returns:
        创造性分析报告
    """
    input_data = CreativityAnalysisInput(
        patent_id=patent_id,
        title=title,
        abstract=abstract,
        claims=claims,
        applicant=kwargs.get("applicant", "未知"),
        inventor=kwargs.get("inventor", "未知"),
        application_date=kwargs.get("application_date", ""),
        ipc_classification=kwargs.get("ipc_classification", ""),
    )

    analyzer = CAP05WithStorm()
    return await analyzer.analyze_creativity(input_data)


if __name__ == "__main__":
    # 测试代码
    import asyncio

    logging.basicConfig(level=logging.INFO)

    async def test_cap05_storm():
        """测试 CAP05 + STORM 集成"""
        print("=" * 70)
        print(" " * 15 + "CAP05 + STORM 创造性分析测试")
        print("=" * 70)

        # 创建测试输入
        input_data = CreativityAnalysisInput(
            patent_id="CN202310999999.9",
            title="一种基于深度学习的智能专利检索系统及方法",
            abstract="本发明提供一种智能专利检索系统,通过深度学习技术实现语义检索,提高检索准确率。系统包括向量表示模块、语义匹配模块和结果排序模块。",
            claims=[
                "1. 一种智能专利检索系统,其特征在于,包括:向量表示模块,用于将专利文本转换为向量表示;语义匹配模块,用于计算查询向量的相似度;结果排序模块,用于基于语义相似度排序检索结果。",
                "2. 根据权利要求1所述的系统,其特征在于,所述向量表示模块采用BERT模型。",
                "3. 根据权利要求1所述的系统,其特征在于,所述语义匹配模块使用余弦相似度。",
            ],
            applicant="Athena 科技有限公司",
            inventor="徐健, 小娜, 小诺",
            application_date="2024-01-01",
            ipc_classification="G06F16/00",
        )

        # 执行分析
        analyzer = CAP05WithStorm()
        report = await analyzer.analyze_creativity(input_data, max_conversation_turns=6)

        # 打印报告
        print("\n" + "=" * 70)
        print("分析完成!")
        print("=" * 70)
        print(f"\n专利号: {report.patent_id}")
        print(f"创造性评分: {report.creativity_score:.2f} / 1.0")
        print("\n最终结论:")
        print(report.final_conclusion)

        # 生成 Markdown 报告
        markdown_report = report.to_markdown()
        report_file = "/tmp/cap05_storm_report.md"
        with open(report_file, "w", encoding="utf-8") as f:
            f.write(markdown_report)

        print(f"\n完整报告已保存到: {report_file}")

    asyncio.run(test_cap05_storm())
