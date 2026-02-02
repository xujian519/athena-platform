#!/usr/bin/env python3
# pyright: ignore
"""
小娜增强反思引擎
Xiaona Enhanced Reflection Engine

为小娜专利法律专家设计的专业反思引擎
集成多维度质量评估、法律专业审核、人类专家协作

作者: 徐健 (xujian519@gmail.com)
创建时间: 2025-12-17
版本: v2.0.0 Professional
"""

import asyncio
import logging
import re
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

from ..collaboration.human_ai_collaboration_framework import (
    HumanInTheLoopEngine,
    TaskType,
)

logger = logging.getLogger(__name__)


class LegalReflectionCategory(Enum):
    """法律反思类别"""

    FACTUAL_ACCURACY = "factual_accuracy"  # 事实准确性
    LEGAL_BASIS = "legal_basis"  # 法律依据
    REASONING_LOGIC = "reasoning_logic"  # 推理逻辑
    COMPLETENESS = "completeness"  # 完整性
    PRACTICAL_APPLICABILITY = "practical_applicability"  # 实用性
    RISK_ASSESSMENT = "risk_assessment"  # 风险评估
    COMPLIANCE = "compliance"  # 合规性
    PROFESSIONAL_JUDGMENT = "professional_judgment"  # 专业判断


class PatentReflectionCategory(Enum):
    """专利反思类别"""

    TECHNICAL_DISCLOSURE = "technical_disclosure"  # 技术披露
    NOVELTY_ASSESSMENT = "novelty_assessment"  # 新颖性评估
    INVENTIVE_STEP = "inventive_step"  # 创造性判断
    CLAIM_DRAFTING = "claim_drafting"  # 权利要求起草
    PRIOR_ART_ANALYSIS = "prior_art_analysis"  # 现有技术分析
    PATENTABILITY = "patentability"  # 可专利性
    SCOPE_DETERMINATION = "scope_determination"  # 保护范围确定
    COMMERCIAL_VALUE = "commercial_value"  # 商业价值


@dataclass
class ReflectionCriterion:
    """反思标准"""

    category: str
    name: str
    description: str
    weight: float = 1.0
    threshold: float = 0.8
    evaluation_method: str = "auto"  # auto, manual, hybrid


@dataclass
class ReflectionScore:
    """反思评分"""

    category: str
    criterion: str
    score: float
    feedback: str
    suggestions: list[str] = field(default_factory=list)
    evidence: list[str] = field(default_factory=list)
    confidence: float = 1.0


@dataclass
class LegalReflectionResult:
    """法律反思结果"""

    task_id: str
    task_type: str
    overall_score: float
    category_scores: dict[str, float]
    detailed_scores: list[ReflectionScore]
    strengths: list[str]
    weaknesses: list[str]
    recommendations: list[str]
    should_refine: bool
    refinement_priority: int  # 1-5, 5最高
    human_review_required: bool
    confidence_level: float
    reflection_timestamp: datetime = field(default_factory=datetime.now)
    metadata: dict[str, Any] = field(default_factory=dict)


class XiaonaEnhancedReflectionEngine:
    """小娜增强反思引擎"""

    def __init__(
        self, llm_client: Any | None = None, collaboration_engine: HumanInTheLoopEngine | None = None  # type: ignore
    ):
        self.llm_client = llm_client
        self.collaboration_engine = collaboration_engine
        self.reflection_history: list[LegalReflectionResult] = []

        # 初始化反思标准
        self.legal_criteria = self._initialize_legal_criteria()
        self.patent_criteria = self._initialize_patent_criteria()

        # 专业关键词库
        self.legal_keywords = self._load_legal_keywords()
        self.patent_keywords = self._load_patent_keywords()

        # 质量阈值
        self.quality_thresholds = {
            "excellent": 0.95,
            "good": 0.85,
            "acceptable": 0.70,
            "needs_improvement": 0.55,
            "poor": 0.40,
        }

    def _initialize_legal_criteria(self) -> dict[str, list[ReflectionCriterion]]:
        """初始化法律反思标准"""
        return {
            LegalReflectionCategory.FACTUAL_ACCURACY.value: [
                ReflectionCriterion(
                    category=LegalReflectionCategory.FACTUAL_ACCURACY.value,
                    name="事实准确性",
                    description="分析中的事实描述是否准确无误",
                    weight=1.5,
                    threshold=0.95,
                    evaluation_method="hybrid",
                )
            ],
            LegalReflectionCategory.LEGAL_BASIS.value: [
                ReflectionCriterion(
                    category=LegalReflectionCategory.LEGAL_BASIS.value,
                    name="法律依据充分性",
                    description="是否引用了充分的法律条款和判例",
                    weight=1.3,
                    threshold=0.90,
                    evaluation_method="auto",
                ),
                ReflectionCriterion(
                    category=LegalReflectionCategory.LEGAL_BASIS.value,
                    name="法律适用正确性",
                    description="法律条款的适用是否正确",
                    weight=1.4,
                    threshold=0.90,
                    evaluation_method="manual",
                ),
            ],
            LegalReflectionCategory.REASONING_LOGIC.value: [
                ReflectionCriterion(
                    category=LegalReflectionCategory.REASONING_LOGIC.value,
                    name="逻辑推理严密性",
                    description="从事实到结论的推理过程是否严密",
                    weight=1.2,
                    threshold=0.85,
                    evaluation_method="auto",
                )
            ],
            LegalReflectionCategory.COMPLETENESS.value: [
                ReflectionCriterion(
                    category=LegalReflectionCategory.COMPLETENESS.value,
                    name="分析完整性",
                    description="是否考虑了所有相关因素和可能性",
                    weight=1.1,
                    threshold=0.80,
                    evaluation_method="auto",
                )
            ],
            LegalReflectionCategory.RISK_ASSESSMENT.value: [
                ReflectionCriterion(
                    category=LegalReflectionCategory.RISK_ASSESSMENT.value,
                    name="风险识别全面性",
                    description="是否识别了所有潜在的法律风险",
                    weight=1.2,
                    threshold=0.85,
                    evaluation_method="hybrid",
                )
            ],
        }

    def _initialize_patent_criteria(self) -> dict[str, list[ReflectionCriterion]]:
        """初始化专利反思标准"""
        return {
            PatentReflectionCategory.TECHNICAL_DISCLOSURE.value: [
                ReflectionCriterion(
                    category=PatentReflectionCategory.TECHNICAL_DISCLOSURE.value,
                    name="技术方案完整性",
                    description="技术方案的披露是否完整、清晰",
                    weight=1.4,
                    threshold=0.85,
                    evaluation_method="manual",
                ),
                ReflectionCriterion(
                    category=PatentReflectionCategory.TECHNICAL_DISCLOSURE.value,
                    name="技术细节充分性",
                    description="技术细节的描述是否足够详尽",
                    weight=1.2,
                    threshold=0.80,
                    evaluation_method="auto",
                ),
            ],
            PatentReflectionCategory.NOVELTY_ASSESSMENT.value: [
                ReflectionCriterion(
                    category=PatentReflectionCategory.NOVELTY_ASSESSMENT.value,
                    name="现有技术检索全面性",
                    description="现有技术的检索是否全面",
                    weight=1.3,
                    threshold=0.85,
                    evaluation_method="manual",
                ),
                ReflectionCriterion(
                    category=PatentReflectionCategory.NOVELTY_ASSESSMENT.value,
                    name="新颖性判断准确性",
                    description="新颖性判断是否准确",
                    weight=1.5,
                    threshold=0.90,
                    evaluation_method="hybrid",
                ),
            ],
            PatentReflectionCategory.CLAIM_DRAFTING.value: [
                ReflectionCriterion(
                    category=PatentReflectionCategory.CLAIM_DRAFTING.value,
                    name="权利要求清晰性",
                    description="权利要求的表述是否清晰",
                    weight=1.3,
                    threshold=0.90,
                    evaluation_method="manual",
                ),
                ReflectionCriterion(
                    category=PatentReflectionCategory.CLAIM_DRAFTING.value,
                    name="保护范围合理性",
                    description="保护范围的界定是否合理",
                    weight=1.2,
                    threshold=0.85,
                    evaluation_method="hybrid",
                ),
            ],
        }

    def _load_legal_keywords(self) -> dict[str, list[str]]:
        """加载法律关键词库"""
        return {
            "legal_basis": [
                "专利法",
                "实施细则",
                "审查指南",
                "最高法",
                "最高检",
                "司法解释",
                "判例",
                "案例",
                "条款",
                "规定",
            ],
            "legal_concepts": [
                "侵权",
                "无效",
                "撤销",
                "复审",
                "异议",
                "行政诉讼",
                "民事诉讼",
                "赔偿",
                "停止侵权",
                "证据",
                "举证责任",
            ],
            "procedural": [
                "申请",
                "审查",
                "授权",
                "公告",
                "缴费",
                "期限",
                "撤回",
                "放弃",
                "转让",
                "许可",
                "实施",
            ],
        }

    def _load_patent_keywords(self) -> dict[str, list[str]]:
        """加载专利关键词库"""
        return {
            "technical_terms": [
                "技术方案",
                "技术特征",
                "技术问题",
                "技术效果",
                "实施例",
                "具体实施方式",
                "背景技术",
                "发明内容",
            ],
            "patentability": [
                "新颖性",
                "创造性",
                "实用性",
                "现有技术",
                "对比文件",
                "区别技术特征",
                "技术启示",
                "进步",
                "显著进步",
            ],
            "claims": [
                "权利要求",
                "独立权利要求",
                "从属权利要求",
                "保护范围",
                "必要技术特征",
                "附加技术特征",
                "限定",
            ],
        }

    async def reflect_on_legal_analysis(
        self,
        task_id: str,
        original_prompt: str,
        legal_output: str,
        task_type: str = "patent_analysis",
        context: dict[str, Any] | None = None,
    ) -> LegalReflectionResult:
        """对法律分析进行反思"""

        logger.info(f"开始法律反思: {task_id}")

        context = context or {}

        # 选择反思标准
        criteria = self.patent_criteria if task_type == "patent_analysis" else self.legal_criteria

        # 执行详细评分
        detailed_scores = []
        category_scores = {}

        for category, criterion_list in criteria.items():
            category_score = 0.0
            total_weight = 0.0

            for criterion in criterion_list:
                score = await self._evaluate_criterion(
                    criterion, original_prompt, legal_output, context
                )

                detailed_scores.append(score)
                category_score += score.score * criterion.weight
                total_weight += criterion.weight

            # 计算类别平均分
            if total_weight > 0:
                category_scores[category] = category_score / total_weight

        # 计算总体评分
        overall_score = self._calculate_overall_score(category_scores, criteria)

        # 生成反思结果
        result = LegalReflectionResult(
            task_id=task_id,
            task_type=task_type,
            overall_score=overall_score,
            category_scores=category_scores,
            detailed_scores=detailed_scores,
            strengths=self._identify_strengths(detailed_scores),
            weaknesses=self._identify_weaknesses(detailed_scores),
            recommendations=self._generate_recommendations(detailed_scores),
            should_refine=overall_score < 0.80,
            refinement_priority=self._determine_refinement_priority(overall_score),
            human_review_required=self._requires_human_review(detailed_scores),
            confidence_level=self._calculate_confidence_level(detailed_scores),
            metadata={
                "criteria_count": len(detailed_scores),
                "evaluated_categories": list(category_scores.keys()),
                "reflection_engine_version": "v2.0.0",
            },
        )

        # 如果需要人类审查且配置了协作引擎
        if result.human_review_required and self.collaboration_engine:
            await self._request_human_review(result, original_prompt, legal_output, context)

        # 保存反思历史
        self.reflection_history.append(result)

        logger.info(f"法律反思完成: {task_id}, 总分: {overall_score:.2f}")
        return result

    async def _evaluate_criterion(
        self, criterion: ReflectionCriterion, prompt: str, output: str, context: dict[str, Any]
    ) -> ReflectionScore:
        """评估单个标准"""

        if criterion.evaluation_method == "auto":
            return await self._auto_evaluate(criterion, prompt, output, context)
        elif criterion.evaluation_method == "manual":
            return await self._manual_evaluate(criterion, prompt, output, context)
        else:  # hybrid
            auto_score = await self._auto_evaluate(criterion, prompt, output, context)
            # 在实际应用中,这里可以结合人工评估
            return auto_score

    async def _auto_evaluate(
        self, criterion: ReflectionCriterion, prompt: str, output: str, context: dict[str, Any]
    ) -> ReflectionScore:
        """自动评估"""

        # 基于关键词匹配和文本分析的基础评分
        base_score = self._analyze_text_quality(output, criterion.category)

        # 基于专业性的额外评分
        professional_score = self._analyze_professional_quality(output, criterion.category)

        # 基于完整性的评分
        completeness_score = self._analyze_completeness(output, criterion.category, context)

        # 综合评分
        final_score = base_score * 0.4 + professional_score * 0.4 + completeness_score * 0.2
        final_score = min(final_score, 1.0)

        # 生成反馈和建议
        feedback = self._generate_feedback(criterion, final_score)
        suggestions = self._generate_suggestions(criterion, final_score, output)

        return ReflectionScore(
            category=criterion.category,
            criterion=criterion.name,
            score=final_score,
            feedback=feedback,
            suggestions=suggestions,
            evidence=self._extract_evidence(output, criterion.category),
            confidence=0.8,  # 自动评估的置信度
        )

    async def _manual_evaluate(
        self, criterion: ReflectionCriterion, prompt: str, output: str, context: dict[str, Any]
    ) -> ReflectionScore:
        """人工评估(模拟)"""

        # 在实际应用中,这里应该调用人工评估接口
        # 这里返回一个中等评分作为示例
        return ReflectionScore(
            category=criterion.category,
            criterion=criterion.name,
            score=0.75,
            feedback="需要人工专家进一步评估",
            suggestions=["建议由法律专家进行专业审核"],
            evidence=[],
            confidence=0.5,
        )

    def _analyze_text_quality(self, text: str, category: str) -> float:
        """分析文本质量"""

        score = 0.0

        # 长度评分
        if len(text) > 100:
            score += 0.2
        elif len(text) > 500:
            score += 0.3
        elif len(text) > 1000:
            score += 0.4

        # 结构评分
        if "分析" in text:
            score += 0.1
        if "结论" in text:
            score += 0.1
        if "建议" in text:
            score += 0.1

        # 专业性评分
        if category in self.legal_keywords:
            keywords = self.legal_keywords[category]
        elif category in self.patent_keywords:
            keywords = self.patent_keywords.get(category, [])
        else:
            keywords = []

        keyword_count = sum(1 for keyword in keywords if keyword in text)
        if keywords:
            score += (keyword_count / len(keywords)) * 0.3

        return min(score, 1.0)

    def _analyze_professional_quality(self, text: str, category: str) -> float:
        """分析专业质量"""

        # 检查专业术语使用
        professional_terms = [
            "根据",
            "基于",
            "依据",
            "符合",
            "满足",
            "包括",
            "涵盖",
            "应当",
            "必须",
            "建议",
            "考虑",
            "评估",
            "判断",
        ]

        term_count = sum(1 for term in professional_terms if term in text)
        score = min(term_count / 10, 1.0) * 0.6

        # 检查逻辑连接词
        logic_connectors = [
            "因此",
            "所以",
            "然而",
            "但是",
            "此外",
            "另外",
            "首先",
            "其次",
            "最后",
            "总之",
            "综上所述",
        ]

        connector_count = sum(1 for connector in logic_connectors if connector in text)
        score += min(connector_count / 5, 1.0) * 0.4

        return min(score, 1.0)

    def _analyze_completeness(self, text: str, category: str, context: dict[str, Any]) -> float:
        """分析完整性"""

        # 检查是否回应了所有关键问题
        completeness_indicators = {
            "问题描述": ["问题", "情况", "背景"],
            "分析过程": ["分析", "考虑", "评估"],
            "依据说明": ["依据", "根据", "条款"],
            "结论得出": ["结论", "结果", "判断"],
            "建议措施": ["建议", "措施", "方案"],
        }

        score = 0.0
        for _aspect, indicators in completeness_indicators.items():
            if any(indicator in text for indicator in indicators):
                score += 0.2

        return min(score, 1.0)

    def _generate_feedback(self, criterion: ReflectionCriterion, score: float) -> str:
        """生成反馈"""

        if score >= criterion.threshold:
            return f"{criterion.name}表现良好,达到预期标准。"
        elif score >= criterion.threshold * 0.8:
            return f"{criterion.name}基本满足要求,但仍有改进空间。"
        else:
            return f"{criterion.name}需要重点改进,未达到预期标准。"

    def _generate_suggestions(
        self, criterion: ReflectionCriterion, score: float, output: str
    ) -> list[str]:
        """生成改进建议"""

        suggestions = []

        if score < 0.5:
            suggestions.append(f"建议重新审视{criterion.name}的相关要求")
            suggestions.append("参考相关的法律法规和案例")

        if score < 0.7:
            suggestions.append("补充更多支撑依据和详细分析")

        if len(output) < 200:
            suggestions.append("增加分析深度和详细说明")

        return suggestions

    def _extract_evidence(self, text: str, category: str) -> list[str]:
        """提取证据片段"""

        evidence = []
        sentences = re.split(r"[。!?]", text)

        for sentence in sentences:
            if len(sentence) > 10:
                # 提取包含关键信息的句子
                if any(keyword in sentence for keyword in ["分析", "结论", "建议", "依据"]):
                    evidence.append(sentence.strip())

        return evidence[:3]  # 最多返回3个证据片段

    def _calculate_overall_score(
        self, category_scores: dict[str, float], criteria: dict[str, list[ReflectionCriterion]]
    ) -> float:
        """计算总体评分"""

        total_score = 0.0
        total_weight = 0.0

        for category, score in category_scores.items():
            if category in criteria:
                # 计算该类别的总权重
                category_weight = sum(c.weight for c in criteria[category])
                total_score += score * category_weight
                total_weight += category_weight

        return total_score / total_weight if total_weight > 0 else 0.0

    def _identify_strengths(self, detailed_scores: list[ReflectionScore]) -> list[str]:
        """识别优势"""
        strengths = []
        for score in detailed_scores:
            if score.score >= 0.85:
                strengths.append(f"{score.criterion}表现优秀")
        return strengths

    def _identify_weaknesses(self, detailed_scores: list[ReflectionScore]) -> list[str]:
        """识别弱点"""
        weaknesses = []
        for score in detailed_scores:
            if score.score < 0.70:
                weaknesses.append(f"{score.criterion}需要改进")
        return weaknesses

    def _generate_recommendations(self, detailed_scores: list[ReflectionScore]) -> list[str]:
        """生成改进建议"""
        recommendations = []

        low_score_items = [s for s in detailed_scores if s.score < 0.75]
        if low_score_items:
            recommendations.append("重点改进评分较低的项目")

        for item in low_score_items:
            # 获取前2个建议，如果suggestions为空则使用空列表
            suggestions = item.suggestions if item.suggestions else []
            recommendations.extend(suggestions[:2])  # 每个项目最多2个建议

        return list(set(recommendations))  # 去重

    def _determine_refinement_priority(self, overall_score: float) -> int:
        """确定改进优先级"""
        if overall_score >= 0.90:
            return 1  # 低优先级
        elif overall_score >= 0.80:
            return 2
        elif overall_score >= 0.70:
            return 3
        elif overall_score >= 0.60:
            return 4
        else:
            return 5  # 高优先级

    def _requires_human_review(self, detailed_scores: list[ReflectionScore]) -> bool:
        """判断是否需要人工审查"""

        # 如果有任何关键项目评分过低,需要人工审查
        critical_categories = [
            "factual_accuracy",
            "legal_basis",
            "novelty_assessment",
            "claim_drafting",
        ]

        for score in detailed_scores:
            if (score.category in critical_categories and score.score < 0.80) or score.score < 0.60:
                return True

        return False

    def _calculate_confidence_level(self, detailed_scores: list[ReflectionScore]) -> float:
        """计算置信度"""
        if not detailed_scores:
            return 0.0

        avg_confidence = sum(score.confidence for score in detailed_scores) / len(detailed_scores)
        avg_score = sum(score.score for score in detailed_scores) / len(detailed_scores)

        # 置信度综合考虑评估置信度和评分一致性
        return avg_confidence * 0.6 + min(avg_score, 1.0) * 0.4

    async def _request_human_review(
        self,
        reflection_result: LegalReflectionResult,
        original_prompt: str,
        legal_output: str,
        context: dict[str, Any],    ):
        """请求人工审查"""

        if not self.collaboration_engine:
            return

        try:
            # 创建协作任务
            task_type = (
                TaskType.PATENT_ANALYSIS
                if "patent" in reflection_result.task_type
                else TaskType.LEGAL_RESEARCH
            )

            task = await self.collaboration_engine.create_collaboration_task(
                task_type=task_type,
                title=f"法律分析质量审查 - {reflection_result.task_id}",
                description=f"请对以下法律分析进行专业审核,评分: {reflection_result.overall_score:.2f}",
                context={
                    "original_prompt": original_prompt,
                    "reflection_result": reflection_result.__dict__,
                    **context,
                },
                ai_output=legal_output,
                ai_confidence=reflection_result.confidence_level,
                priority=reflection_result.refinement_priority,
            )

            logger.info(f"已请求人工审查: {task.task_id}")

        except Exception as e:
            # 人工审查创建失败，记录错误但不影响主流程
            logger.error(f"创建人工审查任务失败: {e}", exc_info=True)

    def get_reflection_statistics(self) -> dict[str, Any]:
        """获取反思统计信息"""

        if not self.reflection_history:
            return {
                "total_reflections": 0,
                "average_score": 0.0,
                "improvement_rate": 0.0,
                "human_review_rate": 0.0,
            }

        total_reflections = len(self.reflection_history)
        average_score = sum(r.overall_score for r in self.reflection_history) / total_reflections
        needs_improvement = sum(1 for r in self.reflection_history if r.should_refine)
        human_reviews = sum(1 for r in self.reflection_history if r.human_review_required)

        return {
            "total_reflections": total_reflections,
            "average_score": round(average_score, 3),
            "improvement_rate": round(needs_improvement / total_reflections, 3),
            "human_review_rate": round(human_reviews / total_reflections, 3),
            "score_distribution": self._get_score_distribution(),
            "category_performance": self._get_category_performance(),
        }

    def _get_score_distribution(self) -> dict[str, int]:
        """获取评分分布"""
        distribution = {"excellent": 0, "good": 0, "acceptable": 0, "poor": 0}

        for result in self.reflection_history:
            score = result.overall_score
            if score >= self.quality_thresholds["excellent"]:
                distribution["excellent"] += 1
            elif score >= self.quality_thresholds["good"]:
                distribution["good"] += 1
            elif score >= self.quality_thresholds["acceptable"]:
                distribution["acceptable"] += 1
            else:
                distribution["poor"] += 1

        return distribution

    def _get_category_performance(self) -> dict[str, float]:
        """获取各类别表现"""
        category_scores = {}
        category_counts = {}

        for result in self.reflection_history:
            for category, score in result.category_scores.items():
                if category not in category_scores:
                    category_scores[category] = score
                    category_counts[category] = 1
                else:
                    category_scores[category] += score
                    category_counts[category] += 1

        # 计算平均分
        for category in category_scores:
            category_scores[category] = category_scores[category] / category_counts[category]

        return {k: round(v, 3) for k, v in category_scores.items()}


# 示例使用
async def demo_xiaona_reflection():
    """演示小娜反思引擎"""

    # 创建反思引擎
    reflection_engine = XiaonaEnhancedReflectionEngine()

    # 模拟法律分析结果
    legal_output = """
    专利CN123456789A新颖性分析报告:

    1. 技术方案概述
    该专利涉及一种智能优化算法,通过机器学习模型自动调整参数。

    2. 现有技术检索
    经过检索,发现以下对比文件:
    - 对比文件1:CN987654321A,涉及基础优化算法
    - 对比文件2:US2020001234A1,涉及参数调整方法

    3. 新颖性分析
    该专利的技术方案与对比文件相比具有以下区别特征:
    - 使用了特定的神经网络架构
    - 采用自适应学习率调整策略

    结论:该专利具有新颖性。
    """

    # 执行反思
    reflection_result = await reflection_engine.reflect_on_legal_analysis(
        task_id="task_001",
        original_prompt="请分析专利CN123456789A的新颖性",
        legal_output=legal_output,
        task_type="patent_analysis",
        context={"patent_number": "CN123456789A", "analysis_type": "novelty_assessment"},
    )

    print("反思结果:")
    print(f"总分: {reflection_result.overall_score:.2f}")
    print(f"需要改进: {reflection_result.should_refine}")
    print(f"人类审查: {reflection_result.human_review_required}")
    print(f"优势: {reflection_result.strengths}")
    print(f"弱点: {reflection_result.weaknesses}")
    print(f"建议: {reflection_result.recommendations}")

    # 获取统计信息
    stats = reflection_engine.get_reflection_statistics()
    print(f"\n反思统计: {stats}")


if __name__ == "__main__":
    asyncio.run(demo_xiaona_reflection())
