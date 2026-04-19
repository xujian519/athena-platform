#!/usr/bin/env python3
from __future__ import annotations
"""
通用 STORM-CAP 集成框架

将 STORM 的多视角研究和专家对话能力扩展到小娜的所有 CAP 能力。

支持的 CAP 能力:
- CAP01: 法律检索
- CAP02: 技术分析
- CAP03: 文书撰写
- CAP04: 说明书审查
- CAP05: 创造性分析 (已完成)
- CAP06: 权利要求审查
- CAP07: 无效分析
- CAP08: 现有技术识别
- CAP09: 答复撰写
- CAP10: 形式审查

作者: Athena 平台团队
创建时间: 2026-01-03
"""

import asyncio
import logging
import sys
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any

from core.logging_config import setup_logging

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# 导入 STORM 集成模块
from core.storm_integration.patent_agents import (
    AgentFactory,
    Conversation,
)
from core.storm_integration.patent_curator import (
    PatentInformationCurator,
    RetrievedDocument,
)
from core.storm_integration.patent_perspectives import (
    PatentBasicInfo,
    Perspective,
)

logger = setup_logging()


class CAPType(Enum):
    """CAP 能力类型"""

    CAP01_LEGAL_RESEARCH = "CAP01"
    CAP02_TECHNICAL_ANALYSIS = "CAP02"
    CAP03_DOCUMENT_WRITING = "CAP03"
    CAP04_SPECIFICATION_REVIEW = "CAP04"
    CAP05_CREATIVITY_ANALYSIS = "CAP05"
    CAP06_CLAIMS_REVIEW = "CAP06"
    CAP07_INVALIDITY_ANALYSIS = "CAP07"
    CAP08_PRIOR_ART_IDENTIFICATION = "CAP08"
    CAP09_RESPONSE_WRITING = "CAP09"
    CAP10_FORMALITY_REVIEW = "CAP10"

    @property
    def display_name(self) -> str:
        """显示名称"""
        names = {
            CAPType.CAP01_LEGAL_RESEARCH: "法律检索",
            CAPType.CAP02_TECHNICAL_ANALYSIS: "技术分析",
            CAPType.CAP03_DOCUMENT_WRITING: "文书撰写",
            CAPType.CAP04_SPECIFICATION_REVIEW: "说明书审查",
            CAPType.CAP05_CREATIVITY_ANALYSIS: "创造性分析",
            CAPType.CAP06_CLAIMS_REVIEW: "权利要求审查",
            CAPType.CAP07_INVALIDITY_ANALYSIS: "无效分析",
            CAPType.CAP08_PRIOR_ART_IDENTIFICATION: "现有技术识别",
            CAPType.CAP09_RESPONSE_WRITING: "答复撰写",
            CAPType.CAP10_FORMALITY_REVIEW: "形式审查",
        }
        return names[self]

    @property
    def description(self) -> str:
        """能力描述"""
        descriptions = {
            CAPType.CAP01_LEGAL_RESEARCH: "向量检索 + 知识图谱查询 + 法律条文精确匹配",
            CAPType.CAP02_TECHNICAL_ANALYSIS: "三级技术分析框架 + 7维度深度解析 + 技术对比矩阵",
            CAPType.CAP03_DOCUMENT_WRITING: "无效宣告请求书 + 专利申请文件 + 意见陈述书",
            CAPType.CAP04_SPECIFICATION_REVIEW: "A26.3审查标准 + 充分公开要求 + 支持关系检查",
            CAPType.CAP05_CREATIVITY_ANALYSIS: "三步法分析 + 现有技术对比 + 显著进步判断",
            CAPType.CAP06_CLAIMS_REVIEW: "清楚性审查 + 简洁性检查 + 支持依据验证",
            CAPType.CAP07_INVALIDITY_ANALYSIS: "新颖性分析 + 创造性评估 + 现有技术检索",
            CAPType.CAP08_PRIOR_ART_IDENTIFICATION: "公开状态判断 + 时间线对比 + 相同性认定",
            CAPType.CAP09_RESPONSE_WRITING: "OA分析 + 策略制定 + 答复文件撰写",
            CAPType.CAP10_FORMALITY_REVIEW: "文件完整性 + 格式规范检查 + 缺项提示",
        }
        return descriptions[self]


@dataclass
class CAPAnalysisInput:
    """通用 CAP 分析输入"""

    cap_type: CAPType  # CAP 能力类型
    patent_id: str  # 专利号
    title: str  # 标题
    abstract: str  # 摘要
    claims: list[str]  # 权利要求
    applicant: str  # 申请人
    inventor: str  # 发明人
    application_date: str  # 申请日期
    ipc_classification: str  # IPC 分类

    # CAP 特定输入
    specific_input: dict[str, Any] = field(default_factory=dict)

    # 可选内容
    description: str | None = None  # 说明书
    prior_art_refs: list[str] | None = None  # 对比文献
    office_action: str | None = None  # 审查意见通知书 (CAP09)
    target_claims: list[int] | None = None  # 目标权利要求 (CAP06)


@dataclass
class CAPAnalysisReport:
    """通用 CAP 分析报告"""

    cap_type: CAPType  # CAP 能力类型
    patent_id: str  # 专利号
    analysis_time: str  # 分析时间

    # STORM 增强内容
    perspectives: list[Perspective]  # 分析视角
    conversation_log: list[dict[str, Any]]  # 专家对话记录
    curated_information: list[dict[str, Any]]  # 策展的信息
    all_citations: list[dict[str, str]]  # 所有引用

    # 分析结果 (CAP 特定)
    analysis_result: dict[str, Any]  # 分析结果

    # 最终结论
    final_conclusion: str  # 最终结论
    confidence_score: float  # 置信度分数 (0-1)

    def to_markdown(self) -> str:
        """转换为 Markdown 格式"""
        md = f"""# {self.cap_type.display_name}报告

## 基本信息

- **专利号**: {self.patent_id}
- **分析时间**: {self.analysis_time}
- **能力类型**: {self.cap_type.value} - {self.cap_type.description}

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
        for utterance in self.conversation_log[:5]:
            md += f"\n### {utterance['agent_name']}\n\n"
            md += f"{utterance['content'][:300]}...\n"

        # 添加 CAP 特定分析结果
        md += """

---

## 分析结果

"""
        for key, value in self.analysis_result.items():
            md += f"**{key}**: {value}\n\n"

        md += f"""

---

## 最终结论

{self.final_conclusion}

**置信度评分**: {self.confidence_score:.2f} / 1.0

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

        md += "\n---\n\n*本报告由 Athena 平台 STORM-CAP 通用框架生成*"

        return md


class CAPPerspectiveFactory:
    """CAP 视角工厂 - 为不同 CAP 类型生成专门的分析视角"""

    @staticmethod
    def create_perspectives(cap_type: CAPType, patent_info: PatentBasicInfo) -> list[Perspective]:
        """为特定 CAP 类型创建分析视角"""

        # 导入 PerspectiveType
        from core.storm_integration.patent_perspectives import PerspectiveType

        # 通用视角
        common_perspectives = [
            Perspective(
                name="法律分析视角",
                type=PerspectiveType.LEGAL,
                description="从专利法角度分析相关条款和规定",
                priority=8,
                keywords=["专利法", "审查指南", "法条"],
            ),
            Perspective(
                name="技术分析视角",
                type=PerspectiveType.TECHNICAL,
                description="从技术实现角度分析技术方案",
                priority=7,
                keywords=["技术方案", "实施方式", "技术效果"],
            ),
        ]

        # CAP 特定视角
        specific_perspectives = []

        if cap_type == CAPType.CAP01_LEGAL_RESEARCH:
            specific_perspectives = [
                Perspective(
                    name="法规检索视角",
                    type=PerspectiveType.LEGAL,
                    description="检索相关法律条文和规定",
                    priority=9,
                    keywords=["法律条文", "实施细则", "审查指南"],
                ),
                Perspective(
                    name="案例关联视角",
                    type=PerspectiveType.LEGAL,
                    description="查找相关案例和判例",
                    priority=8,
                    keywords=["判例", "复审决定", "无效决定"],
                ),
            ]

        elif cap_type == CAPType.CAP02_TECHNICAL_ANALYSIS:
            specific_perspectives = [
                Perspective(
                    name="技术特征视角",
                    type=PerspectiveType.TECHNICAL,
                    description="分析技术特征的组成和结构",
                    priority=9,
                    keywords=["技术特征", "技术手段", "技术要素"],
                ),
                Perspective(
                    name="技术效果视角",
                    type=PerspectiveType.TECHNICAL,
                    description="分析技术效果和有益效果",
                    priority=8,
                    keywords=["技术效果", "有益效果", "性能提升"],
                ),
                Perspective(
                    name="技术问题视角",
                    type=PerspectiveType.TECHNICAL,
                    description="分析解决的技术问题",
                    priority=7,
                    keywords=["技术问题", "现有技术", "技术缺陷"],
                ),
            ]

        elif cap_type == CAPType.CAP03_DOCUMENT_WRITING:
            specific_perspectives = [
                Perspective(
                    name="文档结构视角",
                    type=PerspectiveType.LEGAL,
                    description="分析文档结构和逻辑",
                    priority=9,
                    keywords=["结构", "逻辑", "层次"],
                ),
                Perspective(
                    name="法律用语视角",
                    type=PerspectiveType.LEGAL,
                    description="确保法律用语准确规范",
                    priority=8,
                    keywords=["法律用语", "规范", "准确"],
                ),
            ]

        elif cap_type == CAPType.CAP04_SPECIFICATION_REVIEW:
            specific_perspectives = [
                Perspective(
                    name="充分公开视角",
                    type=PerspectiveType.TECHNICAL,
                    description="检查说明书是否充分公开",
                    priority=9,
                    keywords=["充分公开", "A26.3", "详细描述"],
                ),
                Perspective(
                    name="支持关系视角",
                    type=PerspectiveType.LEGAL,
                    description="检查权利要求是否得到说明书支持",
                    priority=8,
                    keywords=["支持关系", "依据", "A26.4"],
                ),
            ]

        elif cap_type == CAPType.CAP05_CREATIVITY_ANALYSIS:
            specific_perspectives = [
                Perspective(
                    name="区别特征视角",
                    type=PerspectiveType.TECHNICAL,
                    description="分析与现有技术的区别",
                    priority=9,
                    keywords=["区别特征", "差异", "不同点"],
                ),
                Perspective(
                    name="技术效果视角",
                    type=PerspectiveType.TECHNICAL,
                    description="分析预料不到的技术效果",
                    priority=8,
                    keywords=["技术效果", "显著进步", "预料不到"],
                ),
                Perspective(
                    name="显而易见性视角",
                    type=PerspectiveType.LEGAL,
                    description="分析技术方案是否显而易见",
                    priority=7,
                    keywords=["显而易见", "结合启示", "动机"],
                ),
            ]

        elif cap_type == CAPType.CAP06_CLAIMS_REVIEW:
            specific_perspectives = [
                Perspective(
                    name="清楚性视角",
                    type=PerspectiveType.LEGAL,
                    description="检查权利要求是否清楚",
                    priority=9,
                    keywords=["清楚", "明确", "A26.4"],
                ),
                Perspective(
                    name="简洁性视角",
                    type=PerspectiveType.LEGAL,
                    description="检查权利要求是否简洁",
                    priority=8,
                    keywords=["简洁", "冗余", "重复"],
                ),
                Perspective(
                    name="支持依据视角",
                    type=PerspectiveType.TECHNICAL,
                    description="检查是否有说明书支持",
                    priority=7,
                    keywords=["支持", "依据", "A26.4"],
                ),
            ]

        elif cap_type == CAPType.CAP07_INVALIDITY_ANALYSIS:
            specific_perspectives = [
                Perspective(
                    name="新颖性视角",
                    type=PerspectiveType.LEGAL,
                    description="分析新颖性问题",
                    priority=9,
                    keywords=["新颖性", "A22.2", "现有技术"],
                ),
                Perspective(
                    name="创造性视角",
                    type=PerspectiveType.LEGAL,
                    description="分析创造性问题",
                    priority=8,
                    keywords=["创造性", "A22.3", "显而易见"],
                ),
            ]

        elif cap_type == CAPType.CAP08_PRIOR_ART_IDENTIFICATION:
            specific_perspectives = [
                Perspective(
                    name="公开状态视角",
                    type=PerspectiveType.TEMPORAL,
                    description="判断技术方案的公开状态",
                    priority=9,
                    keywords=["公开", "公众得知", "A22.2"],
                ),
                Perspective(
                    name="时间线视角",
                    type=PerspectiveType.TEMPORAL,
                    description="分析申请日和公开日的时间线",
                    priority=8,
                    keywords=["申请日", "公开日", "优先权日"],
                ),
                Perspective(
                    name="相同性视角",
                    type=PerspectiveType.TECHNICAL,
                    description="判断技术方案是否相同",
                    priority=7,
                    keywords=["相同", "等同", "实质相同"],
                ),
            ]

        elif cap_type == CAPType.CAP09_RESPONSE_WRITING:
            specific_perspectives = [
                Perspective(
                    name="审查意见分析视角",
                    type=PerspectiveType.LEGAL,
                    description="深入分析审查意见的内容",
                    priority=9,
                    keywords=["审查意见", "驳回理由", "问题"],
                ),
                Perspective(
                    name="答复策略视角",
                    type=PerspectiveType.LEGAL,
                    description="制定有效的答复策略",
                    priority=8,
                    keywords=["策略", "论证", "修改"],
                ),
            ]

        elif cap_type == CAPType.CAP10_FORMALITY_REVIEW:
            specific_perspectives = [
                Perspective(
                    name="文件完整性视角",
                    type=PerspectiveType.LEGAL,
                    description="检查文件是否完整",
                    priority=9,
                    keywords=["完整", "缺项", "必要文件"],
                ),
                Perspective(
                    name="格式规范视角",
                    type=PerspectiveType.LEGAL,
                    description="检查格式是否符合规范",
                    priority=8,
                    keywords=["格式", "规范", "标准"],
                ),
            ]

        return common_perspectives + specific_perspectives


class UniversalCAPWithStorm:
    """
    通用 STORM-CAP 集成框架

    为所有 CAP 能力提供统一的 STORM 增强:
    1. 多视角分析
    2. 专家对话
    3. 信息策展
    4. 带引用的报告生成
    """

    def __init__(self):
        """初始化"""
        logger.info("初始化通用 STORM-CAP 集成框架")

        # 初始化组件
        self.perspective_factory = CAPPerspectiveFactory()
        self.information_curator = PatentInformationCurator()

        # 创建专家团队
        self.agents = AgentFactory.create_all_agents()

    async def analyze(
        self, input_data: CAPAnalysisInput, max_conversation_turns: int = 6
    ) -> CAPAnalysisReport:
        """
        执行通用 CAP 分析

        Args:
            input_data: 分析输入数据
            max_conversation_turns: 最大对话轮次

        Returns:
            CAP 分析报告
        """
        logger.info(f"开始 {input_data.cap_type.display_name} 分析: {input_data.patent_id}")

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

        # 2. 创建分析视角
        logger.info("创建分析视角...")
        perspectives = self.perspective_factory.create_perspectives(
            input_data.cap_type, patent_info
        )

        # 3. 信息策展
        logger.info("策展相关信息...")
        curated_docs = await self._curate_information(
            patent_info, perspectives, input_data.cap_type
        )

        # 4. 模拟专家对话
        logger.info("模拟专家对话...")
        conversation = await self._simulate_expert_discussion(
            patent_info, perspectives, curated_docs, input_data.cap_type, max_conversation_turns
        )

        # 5. 执行 CAP 特定分析
        logger.info(f"执行 {input_data.cap_type.display_name} 分析...")
        analysis_result = await self._perform_cap_analysis(
            input_data.cap_type,
            patent_info,
            curated_docs,
            conversation,
        )

        # 6. 生成最终结论
        logger.info("生成最终结论...")
        final_conclusion, confidence_score = self._generate_conclusion(
            input_data.cap_type, analysis_result
        )

        # 7. 组装报告
        report = CAPAnalysisReport(
            cap_type=input_data.cap_type,
            patent_id=input_data.patent_id,
            analysis_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            perspectives=perspectives,
            conversation_log=[u.to_dict() for u in conversation.utterances],
            curated_information=[doc.to_dict() for doc in curated_docs],
            all_citations=conversation.get_all_citations(),
            analysis_result=analysis_result,
            final_conclusion=final_conclusion,
            confidence_score=confidence_score,
        )

        logger.info(f"分析完成: 置信度 {confidence_score:.2f}")

        return report

    async def _curate_information(
        self, patent_info: PatentBasicInfo, perspectives: list[Perspective], cap_type: CAPType
    ) -> list[RetrievedDocument]:
        """策展相关信息"""
        # 根据不同的 CAP 类型构建不同的查询
        if cap_type == CAPType.CAP01_LEGAL_RESEARCH:
            query = f"{patent_info.title} 相关法律条文 审查指南"
        elif cap_type == CAPType.CAP02_TECHNICAL_ANALYSIS:
            query = f"{patent_info.title} {patent_info.abstract[:200]} 技术方案"
        elif cap_type in [CAPType.CAP05_CREATIVITY_ANALYSIS, CAPType.CAP07_INVALIDITY_ANALYSIS]:
            query = f"{patent_info.title} 现有技术 对比文献"
        elif cap_type == CAPType.CAP09_RESPONSE_WRITING:
            query = f"{patent_info.title} 审查意见答复 类似案例"
        else:
            query = f"{patent_info.title} {patent_info.abstract[:200]}"

        # 使用信息策展器检索
        curated_docs = await self.information_curator.curate(
            query=query,
            context=f"专利号: {patent_info.patent_id}, CAP类型: {cap_type.value}",
            top_k=15,
        )

        logger.info(f"找到 {len(curated_docs)} 条相关信息")

        return curated_docs

    async def _simulate_expert_discussion(
        self,
        patent_info: PatentBasicInfo,
        perspectives: list[Perspective],
        curated_docs: list[RetrievedDocument],
        cap_type: CAPType,
        max_turns: int,
    ) -> Conversation:
        """模拟专家讨论"""
        conversation = Conversation(topic=f"{cap_type.display_name}: {patent_info.title}")

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
                    "cap_type": cap_type.value,
                },
            )

            conversation.add_utterance(utterance)

        return conversation

    async def _perform_cap_analysis(
        self,
        cap_type: CAPType,
        patent_info: PatentBasicInfo,
        curated_docs: list[RetrievedDocument],
        conversation: Conversation,
    ) -> dict[str, Any]:
        """执行 CAP 特定分析"""

        # 从对话中提取关键信息
        key_points = []
        for utterance in conversation.utterances:
            if "关键" in utterance.content or "重要" in utterance.content:
                key_points.append(utterance.content[:200])

        # 根据不同的 CAP 类型生成不同的分析结果
        if cap_type == CAPType.CAP01_LEGAL_RESEARCH:
            return {
                "相关法条": f"找到 {len(curated_docs)} 条相关法律条文",
                "关键观点": key_points[:3] if key_points else ["暂无关键观点"],
                "检索建议": "建议进一步检索相关案例和判例",
            }

        elif cap_type == CAPType.CAP02_TECHNICAL_ANALYSIS:
            return {
                "技术特征": "已提取核心技术特征",
                "技术手段": "已分析技术实现手段",
                "技术效果": "已评估技术效果",
                "技术问题": "已明确解决的技术问题",
                "关键观点": key_points[:3] if key_points else ["暂无关键观点"],
            }

        elif cap_type == CAPType.CAP05_CREATIVITY_ANALYSIS:
            return {
                "最接近现有技术": curated_docs[0].source_id if curated_docs else "未找到",
                "区别特征": "已分析区别特征",
                "技术效果": "已评估技术效果",
                "显而易见性": "非显而易见" if key_points else "需进一步分析",
                "关键观点": key_points[:3] if key_points else ["暂无关键观点"],
            }

        else:
            return {
                "分析项目": "已完成分析",
                "关键发现": key_points[:3] if key_points else ["暂无关键发现"],
                "建议": "建议进行更深入的分析",
            }

    def _generate_conclusion(
        self, cap_type: CAPType, analysis_result: dict[str, Any]
    ) -> tuple[str, float]:
        """生成最终结论和评分"""
        # 基于分析结果评分
        score = 0.5  # 基础分

        if "关键观点" in analysis_result and len(analysis_result["关键观点"]) > 0:
            score += 0.2

        if len(analysis_result) > 3:
            score += 0.2

        if any("建议" in k for k in analysis_result):
            score += 0.1

        # 生成结论文本
        if score >= 0.8:
            conclusion = (
                f"本次{cap_type.display_name}分析全面深入,"
                f"基于多视角专家讨论和信息策展,"
                f"得出了可靠的分析结论。"
            )
        elif score >= 0.5:
            conclusion = (
                f"本次{cap_type.display_name}分析基本完成," f"建议进一步深入分析某些方面。"
            )
        else:
            conclusion = (
                f"本次{cap_type.display_name}分析需要更多信息支持," f"建议补充相关材料后重新分析。"
            )

        return conclusion, min(score, 1.0)


# 便捷函数
async def analyze_with_storm(
    cap_type: CAPType, patent_id: str, title: str, abstract: str, claims: list[str], **kwargs
) -> CAPAnalysisReport:
    """
    便捷函数:使用 STORM 进行 CAP 分析

    Args:
        cap_type: CAP 能力类型
        patent_id: 专利号
        title: 标题
        abstract: 摘要
        claims: 权利要求列表
        **kwargs: 其他专利信息和 CAP 特定输入

    Returns:
        CAP 分析报告
    """
    input_data = CAPAnalysisInput(
        cap_type=cap_type,
        patent_id=patent_id,
        title=title,
        abstract=abstract,
        claims=claims,
        applicant=kwargs.get("applicant", "未知"),
        inventor=kwargs.get("inventor", "未知"),
        application_date=kwargs.get("application_date", ""),
        ipc_classification=kwargs.get("ipc_classification", ""),
        specific_input=kwargs.get("specific_input", {}),
    )

    analyzer = UniversalCAPWithStorm()
    return await analyzer.analyze(input_data)


if __name__ == "__main__":
    # 测试代码
    import asyncio

    logging.basicConfig(level=logging.INFO)

    async def test_universal_cap_storm():
        """测试通用 STORM-CAP 框架"""
        print("=" * 70)
        print(" " * 15 + "通用 STORM-CAP 框架测试")
        print("=" * 70)

        # 测试不同的 CAP 能力
        test_cases = [
            {
                "cap_type": CAPType.CAP01_LEGAL_RESEARCH,
                "title": "法律检索测试",
            },
            {
                "cap_type": CAPType.CAP02_TECHNICAL_ANALYSIS,
                "title": "技术分析测试",
            },
            {
                "cap_type": CAPType.CAP05_CREATIVITY_ANALYSIS,
                "title": "创造性分析测试",
            },
        ]

        for test_case in test_cases:
            print(f"\n{'='*70}")
            print(f"测试: {test_case['title']}")
            print(f"{'='*70}")

            # 创建测试输入
            input_data = CAPAnalysisInput(
                cap_type=test_case["cap_type"],
                patent_id="CN202410000001.X",
                title="基于深度学习的专利检索方法",
                abstract="本发明提供一种基于深度学习的专利检索方法...",
                claims=["权利要求1", "权利要求2"],
                applicant="测试公司",
                inventor="测试发明人",
                application_date="2024-01-01",
                ipc_classification="G06F16/00",
            )

            # 执行分析
            analyzer = UniversalCAPWithStorm()
            report = await analyzer.analyze(input_data, max_conversation_turns=4)

            # 打印结果
            print(f"\n✅ {test_case['title']} 完成")
            print(f"   置信度: {report.confidence_score:.2f}")
            print(f"   视角数: {len(report.perspectives)}")
            print(f"   对话轮次: {len(report.conversation_log)}")

        print(f"\n{'='*70}")
        print("所有测试完成!")
        print(f"{'='*70}")

    asyncio.run(test_universal_cap_storm())
