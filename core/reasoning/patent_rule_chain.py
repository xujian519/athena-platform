#!/usr/bin/env python3
from __future__ import annotations
"""
专利规则链推理系统
Patent Rule Chain Reasoning System

基于专利知识图谱的规则链推理,支持复杂的专利合规性分析和智能判断
作者: 小诺·双鱼座
创建时间: 2025-12-21
版本: v1.0.0 "规则链推理"
"""

import logging
import re
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

from ..knowledge.patent_analysis.enhanced_knowledge_graph import EnhancedPatentKnowledgeGraph
from .expert_rule_engine import ExpertRuleEngine, ReasoningChain, ReasoningRule

logger = logging.getLogger(__name__)


class PatentRuleType(Enum):
    """专利规则类型"""

    NOVELTY = "novelty"  # 新颖性
    INVENTIVENESS = "inventiveness"  # 创造性
    UTILITY = "utility"  # 实用性
    DISCLOSURE = "disclosure"  # 充分公开
    CLAIM_SCOPE = "claim_scope"  # 权利要求范围
    PRIORITY = "priority"  # 优先权
    UNITY = "unity"  # 单一性
    CLARITY = "clarity"  # 清晰性


class PatentElement(Enum):
    """专利要素"""

    TITLE = "title"  # 标题
    ABSTRACT = "abstract"  # 摘要
    CLAIMS = "claims"  # 权利要求
    DESCRIPTION = "description"  # 说明书
    DRAWINGS = "drawings"  # 附图
    PRIOR_ART = "prior_art"  # 现有技术
    TECHNICAL_FIELD = "technical_field"  # 技术领域


@dataclass
class PatentElement:
    """专利要素数据"""

    element_type: PatentElement
    content: str
    metadata: dict[str, Any] = field(default_factory=dict)
    extracted_features: dict[str, Any] = field(default_factory=dict)


@dataclass
class RuleChain:
    """规则链"""

    chain_id: str
    chain_name: str
    rule_type: PatentRuleType
    rules: list[ReasoningRule]
    execution_order: list[str]  # 规则执行顺序
    dependencies: dict[str, list[str]] = field(default_factory=dict)
    conditions: dict[str, Any] = field(default_factory=dict)


@dataclass
class PatentAnalysis:
    """专利分析结果"""

    patent_id: str
    analysis_type: PatentRuleType
    elements: dict[PatentElement, PatentElement]
    applied_rule_chains: list[RuleChain]
    reasoning_results: list[ReasoningChain]
    overall_assessment: dict[str, Any]
    recommendations: list[str]
    confidence: float
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class ComplianceCheck:
    """合规性检查结果"""

    check_id: str
    patent_id: str
    rule_type: PatentRuleType
    passed: bool
    score: float  # 0-100
    issues: list[dict[str, Any]]
    suggestions: list[str]
    evidence: list[str]
    confidence: float


class PatentRuleChainEngine:
    """专利规则链推理引擎"""

    def __init__(self):
        self.name = "专利规则链推理引擎"
        self.version = "1.0.0"
        self._initialized = False
        self.logger = logging.getLogger(self.name)

        # 核心组件
        self.expert_engine: ExpertRuleEngine | None = None
        self.knowledge_graph: EnhancedPatentKnowledgeGraph | None = None

        # 规则链库
        self.rule_chains: dict[PatentRuleType, list[RuleChain]] = defaultdict(list)

        # 分析缓存
        self.analysis_cache: dict[str, PatentAnalysis] = {}

        # 配置参数
        self.config = {
            "max_analysis_depth": 5,
            "confidence_threshold": 0.7,
            "enable_parallel_analysis": True,
            "cache_enabled": True,
            "include_relevant_rules": True,
            "strict_mode": False,
        }

        # 统计信息
        self.stats = {
            "total_patents_analyzed": 0,
            "successful_analyses": 0,
            "average_confidence": 0.0,
            "rule_chains_executed": 0,
            "compliance_checks": 0,
        }

    async def initialize(self):
        """初始化专利规则链引擎"""
        try:
            # 初始化专家规则引擎
            self.expert_engine = ExpertRuleEngine()
            await self.expert_engine.initialize()

            # 初始化知识图谱
            self.knowledge_graph = await EnhancedPatentKnowledgeGraph.initialize()

            # 构建专利规则链
            await self._build_patent_rule_chains()

            self._initialized = True
            self.logger.info("✅ PatentRuleChainEngine 初始化完成")
            return True

        except Exception:
            return False

    async def _build_patent_rule_chains(self):
        """构建专利规则链"""
        try:
            # 新颖性审查规则链
            novelty_chains = await self._build_novelty_chains()
            self.rule_chains[PatentRuleType.NOVELTY].extend(novelty_chains)

            # 创造性审查规则链
            inventiveness_chains = await self._build_inventiveness_chains()
            self.rule_chains[PatentRuleType.INVENTIVENESS].extend(inventiveness_chains)

            # 实用性审查规则链
            utility_chains = await self._build_utility_chains()
            self.rule_chains[PatentRuleType.UTILITY].extend(utility_chains)

            # 充分公开审查规则链
            disclosure_chains = await self._build_disclosure_chains()
            self.rule_chains[PatentRuleType.DISCLOSURE].extend(disclosure_chains)

            # 权利要求范围审查规则链
            claim_scope_chains = await self._build_claim_scope_chains()
            self.rule_chains[PatentRuleType.CLAIM_SCOPE].extend(claim_scope_chains)

            total_chains = sum(len(chains) for chains in self.rule_chains.values())
            self.logger.info(f"✅ 专利规则链构建完成: {total_chains} 条规则链")

        except Exception as e:
            self.logger.error(f"规则链构建失败: {e}")

    async def _build_novelty_chains(self) -> list[RuleChain]:
        """构建新颖性审查规则链"""
        chains = []

        # 基础新颖性检查链
        basic_novelty_chain = RuleChain(
            chain_id="novelty_basic_001",
            chain_name="基础新颖性审查",
            rule_type=PatentRuleType.NOVELTY,
            rules=[self.expert_engine.rules.get("novelty_check_001")],
            execution_order=["novelty_check_001"],
            conditions={"min_prior_art_checks": 3},
        )
        chains.append(basic_novelty_chain)

        # 详细新颖性检查链
        detailed_novelty_chain = RuleChain(
            chain_id="novelty_detailed_001",
            chain_name="详细新颖性审查",
            rule_type=PatentRuleType.NOVELTY,
            rules=[
                self.expert_engine.rules.get("novelty_check_001"),
                # 可以添加更多规则
            ],
            execution_order=["novelty_check_001"],
            conditions={"min_prior_art_checks": 10, "include_international_search": True},
        )
        chains.append(detailed_novelty_chain)

        return chains

    async def _build_inventiveness_chains(self) -> list[RuleChain]:
        """构建创造性审查规则链"""
        chains = []

        # 基础创造性检查链
        basic_inventiveness_chain = RuleChain(
            chain_id="inventiveness_basic_001",
            chain_name="基础创造性审查",
            rule_type=PatentRuleType.INVENTIVENESS,
            rules=[self.expert_engine.rules.get("inventiveness_check_001")],
            execution_order=["inventiveness_check_001"],
            conditions={"include_technical_comparison": True},
        )
        chains.append(basic_inventiveness_chain)

        return chains

    async def _build_utility_chains(self) -> list[RuleChain]:
        """构建实用性审查规则链"""
        chains = []

        # 基础实用性检查链
        basic_utility_chain = RuleChain(
            chain_id="utility_basic_001",
            chain_name="基础实用性审查",
            rule_type=PatentRuleType.UTILITY,
            rules=[self.expert_engine.rules.get("utility_check_001")],
            execution_order=["utility_check_001"],
            conditions={"check_manufacturability": True},
        )
        chains.append(basic_utility_chain)

        return chains

    async def _build_disclosure_chains(self) -> list[RuleChain]:
        """构建充分公开审查规则链"""
        chains = []

        # 基础充分公开检查链
        disclosure_rules = await self._generate_disclosure_rules()
        basic_disclosure_chain = RuleChain(
            chain_id="disclosure_basic_001",
            chain_name="基础充分公开审查",
            rule_type=PatentRuleType.DISCLOSURE,
            rules=disclosure_rules,
            execution_order=[f"disclosure_rule_{i:03d}" for i in range(len(disclosure_rules))],
            conditions={"check_enablement": True, "check_best_mode": False},
        )
        chains.append(basic_disclosure_chain)

        return chains

    async def _generate_disclosure_rules(self) -> list[ReasoningRule]:
        """生成充分公开规则"""
        rules = []

        # 实施方式充分性规则
        rules.append(
            ReasoningRule(
                rule_id="disclosure_rule_001",
                rule_name="实施方式充分性",
                rule_type="legal",
                reasoning_type="deductive",
                conditions=[],  # 需要具体实现
                conclusions=[],
                priority=1,
            )
        )

        return rules

    async def _build_claim_scope_chains(self) -> list[RuleChain]:
        """构建权利要求范围审查规则链"""
        chains = []

        # 基础权利要求范围检查链
        claim_scope_rules = [self.expert_engine.rules.get("claim_scope_001")]
        basic_claim_scope_chain = RuleChain(
            chain_id="claim_scope_basic_001",
            chain_name="基础权利要求范围审查",
            rule_type=PatentRuleType.CLAIM_SCOPE,
            rules=claim_scope_rules,
            execution_order=["claim_scope_001"],
            conditions={"check_ambiguity": True, "check_support": True},
        )
        chains.append(basic_claim_scope_chain)

        return chains

    async def analyze_patent(
        self,
        patent_data: dict[str, Any],        analysis_types: list[str] = None,
        context: dict[str, Any] | None = None,
    ) -> PatentAnalysis:
        """
        分析专利

        Args:
            patent_data: 专利数据
            analysis_types: 分析类型列表
            context: 上下文信息

        Returns:
            PatentAnalysis: 专利分析结果
        """
        if not self._initialized:
            raise RuntimeError("PatentRuleChainEngine未初始化")

        patent_id = patent_data.get("patent_id", "unknown")

        # 检查缓存
        if self.config.get("cache_enabled") and patent_id in self.analysis_cache:
            return self.analysis_cache.get(patent_id)

        self.stats["total_patents_analyzed"] += 1

        try:
            # 解析专利要素
            elements = await self._parse_patent_elements(patent_data)

            # 确定分析类型
            if analysis_types is None:
                analysis_types = list(PatentRuleType)

            # 执行规则链分析
            applied_chains = []
            reasoning_results = []
            overall_assessment = {}
            recommendations = []

            for rule_type in analysis_types:
                try:
                    # 选择适用的规则链
                    applicable_chains = await self._select_applicable_chains(
                        rule_type, elements, context
                    )

                    # 执行规则链
                    for chain in applicable_chains:
                        reasoning_result = await self._execute_rule_chain(chain, elements, context)

                        reasoning_results.append(reasoning_result)
                        applied_chains.append(chain)

                        # 收集评估和建议
                        assessment, recs = await self._extract_assessment_and_recommendations(
                            reasoning_result, rule_type
                        )

                        overall_assessment[rule_type.value] = assessment
                        recommendations.extend(recs)

                except Exception:
                    continue

            # 计算整体置信度
            overall_confidence = self._calculate_overall_confidence(reasoning_results)

            # 创建专利分析结果
            analysis = PatentAnalysis(
                patent_id=patent_id,
                analysis_type=rule_type if len(analysis_types) == 1 else None,
                elements=elements,
                applied_rule_chains=applied_chains,
                reasoning_results=reasoning_results,
                overall_assessment=overall_assessment,
                recommendations=list(set(recommendations)),  # 去重
                confidence=overall_confidence,
            )

            # 缓存结果
            if self.config.get("cache_enabled"):
                self.analysis_cache[patent_id] = analysis

            self.stats["successful_analyses"] += 1
            self.stats["average_confidence"] = (
                self.stats["average_confidence"] * (self.stats["successful_analyses"] - 1)
                + overall_confidence
            ) / self.stats["successful_analyses"]

            self.logger.info(f"✅ 专利分析完成: {patent_id}, 置信度: {overall_confidence:.3f}")
            return analysis

        except Exception:
            raise

    async def _parse_patent_elements(
        self, patent_data: dict[str, Any]
    ) -> dict[PatentElement, PatentElement]:
        """解析专利要素"""
        elements = {}

        # 解析标题
        if "title" in patent_data:
            elements[PatentElement.TITLE] = PatentElement(
                element_type=PatentElement.TITLE,
                content=patent_data.get("title"),
                metadata={"length": len(patent_data.get("title"))},
            )

        # 解析摘要
        if "abstract" in patent_data:
            elements[PatentElement.ABSTRACT] = PatentElement(
                element_type=PatentElement.ABSTRACT,
                content=patent_data.get("abstract"),
                metadata={"word_count": len(patent_data.get("abstract").split())},
            )

        # 解析权利要求
        if "claims" in patent_data:
            elements[PatentElement.CLAIMS] = PatentElement(
                element_type=PatentElement.CLAIMS,
                content=patent_data.get("claims"),
                metadata={
                    "claim_count": patent_data.get("claims").count("1."),
                    "independent_claims": len(
                        re.findall(r"^\d+\.\s", patent_data.get("claims"), re.MULTILINE)
                    ),
                },
            )

        # 解析说明书
        if "description" in patent_data:
            elements[PatentElement.DESCRIPTION] = PatentElement(
                element_type=PatentElement.DESCRIPTION,
                content=patent_data.get("description"),
                metadata={"word_count": len(patent_data.get("description").split())},
            )

        # 解析技术领域
        if "technical_field" in patent_data:
            elements[PatentElement.TECHNICAL_FIELD] = PatentElement(
                element_type=PatentElement.TECHNICAL_FIELD, content=patent_data.get("technical_field")
            )

        return elements

    async def _select_applicable_chains(
        self,
        rule_type: PatentRuleType,
        elements: dict[PatentElement, PatentElement],
        context: dict[str, Any],    ) -> list[RuleChain]:
        """选择适用的规则链"""
        applicable_chains = []

        for chain in self.rule_chains[rule_type]:
            # 检查条件是否满足
            if await self._is_chain_applicable(chain, elements, context):
                applicable_chains.append(chain)

        # 按优先级排序
        applicable_chains.sort(key=lambda c: min(r.priority for r in c.rules), reverse=True)

        return applicable_chains

    async def _is_chain_applicable(
        self,
        chain: RuleChain,
        elements: dict[PatentElement, PatentElement],
        context: dict[str, Any],    ) -> bool:
        """判断规则链是否适用"""
        # 检查必需的专利要素是否存在
        required_elements = {
            PatentRuleType.NOVELTY: [
                PatentElement.TITLE,
                PatentElement.ABSTRACT,
                PatentElement.CLAIMS,
            ],
            PatentRuleType.INVENTIVENESS: [PatentElement.DESCRIPTION, PatentElement.CLAIMS],
            PatentRuleType.UTILITY: [PatentElement.DESCRIPTION],
            PatentRuleType.DISCLOSURE: [PatentElement.DESCRIPTION, PatentElement.CLAIMS],
            PatentRuleType.CLAIM_SCOPE: [PatentElement.CLAIMS, PatentElement.DESCRIPTION],
        }

        if chain.rule_type in required_elements:
            for required_element in required_elements.get(chain.rule_type):
                if required_element not in elements:
                    return False

        # 检查额外条件
        for condition_key, condition_value in chain.conditions.items():
            if not await self._evaluate_chain_condition(
                condition_key, condition_value, elements, context
            ):
                return False

        return True

    async def _evaluate_chain_condition(
        self,
        condition_key: str,
        condition_value: Any,
        elements: dict[PatentElement, PatentElement],
        context: dict[str, Any],    ) -> bool:
        """评估规则链条件"""
        if condition_key == "min_prior_art_checks":
            # 检查现有技术检索数量
            if PatentElement.PRIOR_ART in elements:
                prior_art_count = len(elements.get(PatentElement.PRIOR_ART).content.split("\n"))
                return prior_art_count >= condition_value

        elif condition_key == "include_international_search":
            # 检查是否包含国际检索
            return context and context["international_search", False] == condition_value

        # 默认返回True
        return True

    async def _execute_rule_chain(
        self,
        chain: RuleChain,
        elements: dict[PatentElement, PatentElement],
        context: dict[str, Any],    ) -> ReasoningChain:
        """执行规则链"""
        # 将专利要素转换为事实
        facts = []
        for element in elements.values():
            facts.append(element.content)

        # 添加上下文信息
        if context:
            for key, value in context.items():
                facts.append(f"{key}: {value}")

        # 执行推理
        reasoning_result = await self.expert_engine.reason(facts, context=context)

        self.stats["rule_chains_executed"] += 1
        return reasoning_result

    async def _extract_assessment_and_recommendations(
        self, reasoning_result: ReasoningChain, rule_type: PatentRuleType
    ) -> tuple[dict[str, Any], list[str]]:
        """提取评估结果和建议"""
        assessment = {"passed": False, "score": 0.0, "key_issues": [], "strengths": []}

        recommendations = []

        # 分析推理结果
        if reasoning_result.final_conclusions:
            # 计算通过状态和分数
            positive_conclusions = [
                c
                for c in reasoning_result.final_conclusions
                if "positive" in c.conclusion_type or "confirmed" in c.conclusion_id
            ]

            assessment["passed"] = len(positive_conclusions) > 0
            assessment["score"] = reasoning_result.overall_confidence * 100

            # 提取优势和问题
            for conclusion in reasoning_result.final_conclusions:
                if conclusion.confidence > 0.8:
                    assessment["strengths"].append(conclusion.explanation)
                elif conclusion.confidence < 0.5:
                    assessment["key_issues"].append(conclusion.explanation)

            # 生成建议
            if not assessment["passed"]:
                recommendations.extend(
                    [
                        f"改进{rule_type.value}相关的技术内容",
                        "补充必要的技术细节和实施例",
                        "完善权利要求的表述方式",
                    ]
                )

        return assessment, recommendations

    def _calculate_overall_confidence(self, reasoning_results: list[ReasoningChain]) -> float:
        """计算整体置信度"""
        if not reasoning_results:
            return 0.0

        confidences = [r.overall_confidence for r in reasoning_results]
        return sum(confidences) / len(confidences)

    async def check_compliance(
        self, patent_data: dict[str, Any], rule_types: list[str] = None
    ) -> list[ComplianceCheck]:
        """
        执行合规性检查

        Args:
            patent_data: 专利数据
            rule_types: 检查的规则类型

        Returns:
            list[ComplianceCheck]: 合规性检查结果列表
        """
        if rule_types is None:
            rule_types = list(PatentRuleType)

        patent_id = patent_data.get("patent_id", "unknown")
        compliance_checks = []

        try:
            # 对每个规则类型进行检查
            for rule_type in rule_types:
                try:
                    # 执行分析
                    analysis = await self.analyze_patent(patent_data, [rule_type])

                    # 生成合规性检查结果
                    check = await self._generate_compliance_check(patent_id, rule_type, analysis)

                    compliance_checks.append(check)

                except Exception:
                    continue

            self.stats["compliance_checks"] += len(compliance_checks)

        except Exception as e:
            self.logger.error(f"合规性检查失败: {e}")

        return compliance_checks

    async def _generate_compliance_check(
        self, patent_id: str, rule_type: PatentRuleType, analysis: PatentAnalysis
    ) -> ComplianceCheck:
        """生成合规性检查结果"""
        check_id = f"compliance_{rule_type.value}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        # 获取对应类型的评估结果
        assessment = analysis.overall_assessment.get(rule_type.value, {})

        passed = assessment.get("passed", False)
        score = assessment.get("score", 0.0)

        # 构建问题和建议
        issues = []
        suggestions = []
        evidence = []

        for issue in assessment.get("key_issues", []):
            issues.append(
                {
                    "type": "compliance_issue",
                    "description": issue,
                    "severity": "high" if score < 50 else "medium",
                }
            )

        suggestions.extend(analysis.recommendations)

        # 收集证据
        for reasoning in analysis.reasoning_results:
            for conclusion in reasoning.final_conclusions:
                evidence.append(conclusion.explanation)

        confidence = analysis.confidence

        return ComplianceCheck(
            check_id=check_id,
            patent_id=patent_id,
            rule_type=rule_type,
            passed=passed,
            score=score,
            issues=issues,
            suggestions=suggestions,
            evidence=evidence,
            confidence=confidence,
        )

    def get_statistics(self) -> dict[str, Any]:
        """获取统计信息"""
        return self.stats.copy()

    async def close(self):
        """关闭专利规则链引擎"""
        if self.expert_engine:
            await self.expert_engine.close()

        self.analysis_cache.clear()
        self._initialized = False
        self.logger.info("✅ PatentRuleChainEngine 已关闭")


# 便捷函数
async def get_patent_rule_chain_engine() -> PatentRuleChainEngine:
    """获取专利规则链引擎实例"""
    engine = PatentRuleChainEngine()
    await engine.initialize()
    return engine


async def check_patent_compliance(
    patent_data: dict[str, Any], check_types: list[str] | None = None
) -> list[ComplianceCheck]:
    """便捷函数:检查专利合规性"""
    engine = await get_patent_rule_chain_engine()
    return await engine.check_compliance(patent_data, check_types)


if __name__ == "__main__":
    print("专利规则链推理系统模块已加载")
