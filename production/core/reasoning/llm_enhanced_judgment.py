#!/usr/bin/env python3
"""
LLM增强智能判断系统
LLM Enhanced Intelligent Judgment System

集成大语言模型的智能判断能力,为专利审查提供专家级的分析和建议
作者: 小诺·双鱼座
创建时间: 2025-12-21
版本: v1.0.0 "智能判断"
"""

from __future__ import annotations
import asyncio
import json
import logging
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING, Any

from .patent_rule_chain import PatentAnalysis

if TYPE_CHECKING:
    from .prior_art_analyzer import TechEvolution

logger = logging.getLogger(__name__)


class JudgmentType(Enum):
    """判断类型"""

    PATENTABILITY = "patentability"  # 可专利性
    INFRINGEMENT_RISK = "infringement_risk"  # 侵权风险
    TECHNICAL_MERIT = "technical_merit"  # 技术价值
    COMMERCIAL_POTENTIAL = "commercial_potential"  # 商业潜力
    STRATEGIC_VALUE = "strategic_value"  # 战略价值


class LLMProvider(Enum):
    """LLM提供商"""

    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    BAIDU = "baidu"
    ALIBABA = "alibaba"
    LOCAL = "local"


@dataclass
class JudgmentContext:
    """判断上下文"""

    patent_id: str
    technology_field: str
    market_context: dict[str, Any]
    legal_framework: str
    business_objectives: list[str]
    stakeholder_interests: list[str]


@dataclass
class EvidenceItem:
    """证据项"""

    evidence_id: str
    evidence_type: str
    content: str
    source: str
    reliability: float  # 0-1
    relevance: float  # 0-1
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class JudgmentResult:
    """判断结果"""

    judgment_id: str
    judgment_type: JudgmentType
    primary_conclusion: str
    confidence_score: float  # 0-1
    supporting_reasoning: list[str]
    counter_arguments: list[str]
    recommendations: list[str]
    risk_factors: list[str]
    evidence_items: list[EvidenceItem]
    llm_analysis: dict[str, Any] | None = None
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class ExpertInsight:
    """专家洞察"""

    insight_id: str
    insight_type: str
    content: str
    confidence: float
    supporting_data: dict[str, Any]
    actionable_advice: list[str]
    potential_impact: str


class LLMEnhancedJudgment:
    """LLM增强智能判断系统"""

    def __init__(self, llm_provider: LLMProvider = LLMProvider.LOCAL):
        self.name = "LLM增强智能判断系统"
        self.version = "1.0.0"
        self._initialized = False
        self.logger = logging.getLogger(self.name)

        # LLM配置
        self.llm_provider = llm_provider
        self.llm_client = None

        # 知识库
        self.knowledge_base = {
            "patent_law": {},  # 专利法知识
            "technical_domains": {},  # 技术领域知识
            "market_data": {},  # 市场数据
            "precedent_cases": {},  # 先例案例
            "industry_standards": {},  # 行业标准
        }

        # 判断缓存
        self.judgment_cache: dict[str, JudgmentResult] = {}
        self.insight_cache: dict[str, list[ExpertInsight]] = {}

        # 配置参数
        self.config = {
            "max_retries": 3,
            "temperature": 0.3,  # 保守的判断
            "max_tokens": 2048,
            "cache_ttl": 3600,
            "evidence_weight": 0.7,
            "llm_weight": 0.3,
            "enable_multi_perspective": True,
            "enable_risk_assessment": True,
        }

        # 统计信息
        self.stats = {
            "total_judgments": 0,
            "successful_judgments": 0,
            "llm_calls": 0,
            "cache_hits": 0,
            "average_confidence": 0.0,
            "judgment_types": defaultdict(int),
        }

    async def initialize(self):
        """初始化LLM增强判断系统"""
        try:
            # 初始化LLM客户端
            await self._init_llm_client()

            # 加载知识库
            await self._load_knowledge_base()

            # 构建判断模板
            await self._build_judgment_templates()

            self._initialized = True
            self.logger.info("✅ LLMEnhancedJudgment 初始化完成")
            return True

        except Exception:
            return False

    async def _init_llm_client(self):
        """初始化LLM客户端"""
        try:
            if self.llm_provider == LLMProvider.OPENAI:
                # OpenAI客户端初始化
                self.llm_client = "openai_client_placeholder"
            elif self.llm_provider == LLMProvider.ANTHROPIC:
                # Anthropic客户端初始化
                self.llm_client = "anthropic_client_placeholder"
            elif self.llm_provider == LLMProvider.LOCAL:
                # 本地模型客户端初始化
                self.llm_client = "local_llm_client_placeholder"

            self.logger.info(f"✅ LLM客户端初始化完成: {self.llm_provider.value}")

        except Exception:
            self.llm_client = "mock_llm_client"

    async def _load_knowledge_base(self):
        """加载知识库"""
        try:
            # 专利法知识
            self.knowledge_base["patent_law"] = {
                "novelty_requirements": "专利法第22条规定,授予专利权的发明应当具备新颖性",
                "inventiveness_criteria": "创造性要求具有突出的实质性特点和显著的进步",
                "utility_standard": "实用性要求能够在产业上制造或使用,并能产生积极效果",
                "disclosure_requirement": "说明书应当对发明作出清楚、完整的说明",
            }

            # 技术领域知识
            self.knowledge_base["technical_domains"] = {
                "ai_ml": "人工智能和机器学习领域具有快速迭代的特点",
                "biotechnology": "生物技术领域需要考虑伦理和安全因素",
                "telecommunications": "通信技术领域标准化程度高",
                "medical_devices": "医疗器械领域监管要求严格",
            }

            # 市场数据
            self.knowledge_base["market_data"] = {
                "tech_trends": "当前技术趋势向智能化、集成化发展",
                "patent_trends": "专利申请量持续增长,质量要求提高",
                "competition_landscape": "技术竞争全球化、跨行业化",
            }

            self.logger.info("✅ 知识库加载完成")

        except Exception as e:
            self.logger.error(f"知识库加载失败: {e}")

    async def _build_judgment_templates(self):
        """构建判断模板"""
        # 这里会预定义各种判断类型的提示模板
        pass

    async def judge_patentability(
        self,
        patent_data: dict[str, Any],        context: JudgmentContext,
        rule_analysis: PatentAnalysis | None = None,
        prior_art_analysis: TechEvolution | None = None,
    ) -> JudgmentResult:
        """
        判断专利可专利性

        Args:
            patent_data: 专利数据
            context: 判断上下文
            rule_analysis: 规则分析结果
            prior_art_analysis: 现有技术分析

        Returns:
            JudgmentResult: 判断结果
        """
        return await self._make_judgment(
            JudgmentType.PATENTABILITY, patent_data, context, rule_analysis, prior_art_analysis
        )

    async def _make_judgment(
        self,
        judgment_type: JudgmentType,
        patent_data: dict[str, Any],        context: JudgmentContext,
        rule_analysis: PatentAnalysis | None = None,
        prior_art_analysis: TechEvolution | None = None,
    ) -> JudgmentResult:
        """执行判断"""
        if not self._initialized:
            raise RuntimeError("LLMEnhancedJudgment未初始化")

        judgment_id = (
            f"{judgment_type.value}_{context.patent_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        )

        self.stats["total_judgments"] += 1
        self.stats["judgment_types"][judgment_type.value] += 1

        try:
            # 收集证据
            evidence_items = await self._collect_evidence(
                patent_data, context, rule_analysis, prior_art_analysis
            )

            # LLM增强分析
            llm_analysis = await self._llm_enhanced_analysis(
                judgment_type, patent_data, context, evidence_items
            )

            # 综合判断
            judgment_result = await self._synthesize_judgment(
                judgment_id, judgment_type, evidence_items, llm_analysis
            )

            # 生成专家洞察
            await self._generate_expert_insights(judgment_result, context)

            # 缓存结果
            self.judgment_cache[judgment_id] = judgment_result

            # 更新统计
            self.stats["successful_judgments"] += 1
            self.stats["average_confidence"] = (
                self.stats["average_confidence"] * (self.stats["successful_judgments"] - 1)
                + judgment_result.confidence_score
            ) / self.stats["successful_judgments"]

            self.logger.info(
                f"✅ 判断完成: {judgment_id}, 置信度: {judgment_result.confidence_score:.3f}"
            )
            return judgment_result

        except Exception:
            raise

    async def _collect_evidence(
        self,
        patent_data: dict[str, Any],        context: JudgmentContext,
        rule_analysis: PatentAnalysis,
        prior_art_analysis: TechEvolution,
    ) -> list[EvidenceItem]:
        """收集证据"""
        evidence_items = []

        try:
            # 专利内容证据
            if "title" in patent_data:
                evidence_items.append(
                    EvidenceItem(
                        evidence_id=f"title_{datetime.now().strftime('%H%M%S')}",
                        evidence_type="patent_title",
                        content=patent_data.get("title"),
                        source="patent_document",
                        reliability=1.0,
                        relevance=0.8,
                    )
                )

            if "abstract" in patent_data:
                evidence_items.append(
                    EvidenceItem(
                        evidence_id=f"abstract_{datetime.now().strftime('%H%M%S')}",
                        evidence_type="patent_abstract",
                        content=patent_data.get("abstract"),
                        source="patent_document",
                        reliability=0.9,
                        relevance=0.9,
                    )
                )

            # 规则分析证据
            if rule_analysis:
                for i, conclusion in enumerate(rule_analysis.final_conclusions):
                    evidence_items.append(
                        EvidenceItem(
                            evidence_id=f"rule_conclusion_{i}",
                            evidence_type="rule_analysis",
                            content=conclusion.explanation,
                            source="expert_rule_engine",
                            reliability=0.8,
                            relevance=0.85,
                        )
                    )

            # 现有技术证据
            if prior_art_analysis:
                for i, patent in enumerate(prior_art_analysis.evolution_path[:5]):
                    evidence_items.append(
                        EvidenceItem(
                            evidence_id=f"prior_art_{i}",
                            evidence_type="prior_art",
                            content=f"现有技术: {patent.title}",
                            source="prior_art_analysis",
                            reliability=0.9,
                            relevance=0.7,
                        )
                    )

            # 知识库证据
            if context.technology_field in self.knowledge_base.get("technical_domains", {}):
                evidence_items.append(
                    EvidenceItem(
                        evidence_id="domain_knowledge",
                        evidence_type="technical_domain",
                        content=self.knowledge_base["technical_domains"][context.technology_field],
                        source="knowledge_base",
                        reliability=0.7,
                        relevance=0.6,
                    )
                )

        except Exception as e:
            self.logger.warning(f"证据收集失败: {e}")

        return evidence_items

    async def _llm_enhanced_analysis(
        self,
        judgment_type: JudgmentType,
        patent_data: dict[str, Any],        context: JudgmentContext,
        evidence_items: list[EvidenceItem],
    ) -> dict[str, Any]:
        """LLM增强分析"""
        self.stats["llm_calls"] += 1

        try:
            # 构建分析提示
            prompt = await self._build_analysis_prompt(
                judgment_type, patent_data, context, evidence_items
            )

            # 调用LLM
            llm_response = await self._call_llm(prompt)

            # 解析响应
            analysis_result = await self._parse_llm_response(llm_response, judgment_type)

            return analysis_result

        except Exception:
            # 返回模拟分析结果
            return {
                "conclusion": "基于现有信息的初步判断",
                "reasoning": "需要更多信息进行详细分析",
                "confidence": 0.5,
                "recommendations": ["建议进行更深入的技术评估"],
            }

    async def _build_analysis_prompt(
        self,
        judgment_type: JudgmentType,
        patent_data: dict[str, Any],        context: JudgmentContext,
        evidence_items: list[EvidenceItem],
    ) -> str:
        """构建分析提示"""
        prompt_parts = []

        # 判断类型说明
        type_instructions = {
            JudgmentType.PATENTABILITY: "请基于以下信息分析该专利的可专利性,包括新颖性、创造性和实用性",
            JudgmentType.INFRINGEMENT_RISK: "请评估该专利的侵权风险,分析其与现有技术的重叠程度",
            JudgmentType.TECHNICAL_MERIT: "请评估该技术的技术价值和创新程度",
            JudgmentType.COMMERCIAL_POTENTIAL: "请分析该专利的商业潜力和市场机会",
            JudgmentType.STRATEGIC_VALUE: "请评估该专利的战略价值和竞争优势",
        }

        prompt_parts.append(f"任务: {type_instructions.get(judgment_type, '请进行综合分析')}")

        # 专利信息
        prompt_parts.append("\n专利信息:")
        if "title" in patent_data:
            prompt_parts.append(f"标题: {patent_data.get('title')}")
        if "abstract" in patent_data:
            prompt_parts.append(f"摘要: {patent_data.get('abstract')}")
        if "claims" in patent_data:
            prompt_parts.append(f"权利要求: {patent_data.get('claims')}")

        # 上下文信息
        prompt_parts.append(f"\n技术领域: {context.technology_field}")
        if context.legal_framework:
            prompt_parts.append(f"法律框架: {context.legal_framework}")
        if context.business_objectives:
            prompt_parts.append(f"商业目标: {', '.join(context.business_objectives)}")

        # 证据信息
        if evidence_items:
            prompt_parts.append("\n相关证据:")
            for evidence in evidence_items[:5]:  # 限制证据数量
                prompt_parts.append(f"- {evidence.evidence_type}: {evidence.content:100}...")

        # 输出要求
        prompt_parts.append("""
请提供结构化的分析结果,包括:
1. 主要结论
2. 支持理由
3. 反对理由
4. 建议
5. 风险因素
6. 置信度评分(0-1)

请以JSON格式返回分析结果。""")

        return "\n".join(prompt_parts)

    async def _call_llm(self, prompt: str) -> str:
        """调用LLM"""
        try:
            # 模拟LLM调用
            # 实际应用中这里会调用真实的LLM服务
            await asyncio.sleep(0.5)  # 模拟处理时间

            # 返回模拟响应
            mock_response = {
                "conclusion": "该专利具备一定创新性和实用性",
                "reasoning": ["技术方案解决了现有技术中的问题", "具有明显的技术进步"],
                "confidence": 0.75,
                "recommendations": ["建议完善技术细节披露", "加强权利要求的保护范围"],
                "risk_factors": ["可能面临现有技术挑战", "需要考虑专利规避设计"],
            }

            return json.dumps(mock_response, ensure_ascii=False, indent=2)

        except Exception:
            raise

    async def _parse_llm_response(
        self, llm_response: str, judgment_type: JudgmentType
    ) -> dict[str, Any]:
        """解析LLM响应"""
        try:
            # 尝试解析JSON响应
            if llm_response.strip().startswith("{"):
                return json.loads(llm_response)
            else:
                # 文本响应解析
                return {
                    "conclusion": llm_response,
                    "reasoning": [llm_response],
                    "confidence": 0.6,
                    "recommendations": ["建议进一步分析"],
                    "risk_factors": [],
                }

        except json.JSONDecodeError:
            return {
                "conclusion": llm_response[:200],
                "reasoning": [llm_response],
                "confidence": 0.5,
                "recommendations": ["建议重新分析"],
                "risk_factors": ["分析不确定性"],
            }

    async def _synthesize_judgment(
        self,
        judgment_id: str,
        judgment_type: JudgmentType,
        evidence_items: list[EvidenceItem],
        llm_analysis: dict[str, Any],    ) -> JudgmentResult:
        """综合判断"""
        try:
            # 计算证据权重
            evidence_weight = sum(item.reliability * item.relevance for item in evidence_items)
            evidence_weight = (
                min(1.0, evidence_weight / len(evidence_items)) if evidence_items else 0.0
            )

            # 计算LLM权重
            llm_weight = llm_analysis.get("confidence", 0.5)

            # 综合置信度
            overall_confidence = (
                evidence_weight * self.config.get("evidence_weight")
                + llm_weight * self.config.get("llm_weight")
            )

            # 构建支持理由
            supporting_reasoning = []
            supporting_reasoning.extend(llm_analysis.get("reasoning", []))

            for evidence in evidence_items:
                if evidence.relevance > 0.7:
                    supporting_reasoning.append(
                        f"{evidence.evidence_type}: {evidence.content:100}..."
                    )

            # 构建反对理由
            counter_arguments = []
            for evidence in evidence_items:
                if evidence.relevance < 0.5:
                    counter_arguments.append(
                        f"{evidence.evidence_type}相关性较低: {evidence.content:100}..."
                    )

            # 风险因素
            risk_factors = llm_analysis.get("risk_factors", [])
            if overall_confidence < 0.7:
                risk_factors.append("判断置信度较低,存在不确定性")

            # 建议
            recommendations = llm_analysis.get("recommendations", [])
            if overall_confidence < 0.6:
                recommendations.insert(0, "建议进行更深入的技术和法律分析")

            judgment_result = JudgmentResult(
                judgment_id=judgment_id,
                judgment_type=judgment_type,
                primary_conclusion=llm_analysis.get("conclusion", "基于当前信息的初步判断"),
                confidence_score=overall_confidence,
                supporting_reasoning=supporting_reasoning,
                counter_arguments=counter_arguments,
                recommendations=recommendations,
                risk_factors=risk_factors,
                evidence_items=evidence_items,
                llm_analysis=llm_analysis,
            )

            return judgment_result

        except Exception:
            raise

    async def _generate_expert_insights(
        self, judgment_result: JudgmentResult, context: JudgmentContext
    ) -> list[ExpertInsight]:
        """生成专家洞察"""
        insights = []

        try:
            # 基于判断结果生成洞察
            if judgment_result.confidence_score > 0.8:
                insights.append(
                    ExpertInsight(
                        insight_id=f"high_confidence_{datetime.now().strftime('%H%M%S')}",
                        insight_type="confidence_analysis",
                        content="判断具有高度可信度,建议积极推进相关决策",
                        confidence=judgment_result.confidence_score,
                        supporting_data={
                            "confidence_score": judgment_result.confidence_score,
                            "evidence_count": len(judgment_result.evidence_items),
                        },
                        actionable_advice=[
                            "可以基于此判断制定战略计划",
                            "建议向利益相关者传达判断结果",
                        ],
                        potential_impact="高置信度判断可显著降低决策风险",
                    )
                )

            # 技术洞察
            if context.technology_field:
                insights.append(
                    ExpertInsight(
                        insight_id=f"tech_insight_{datetime.now().strftime('%H%M%S')}",
                        insight_type="technical_analysis",
                        content=f"基于{context.technology_field}领域特点的技术分析",
                        confidence=0.7,
                        supporting_data={
                            "technology_field": context.technology_field,
                            "market_context": context.market_context,
                        },
                        actionable_advice=["关注该领域的最新技术动态", "考虑技术集成的可能性"],
                        potential_impact="技术洞察有助于把握发展方向",
                    )
                )

            # 缓存洞察
            if context.patent_id not in self.insight_cache:
                self.insight_cache[context.patent_id] = []
            self.insight_cache.get(context.patent_id).extend(insights)

        except Exception as e:
            self.logger.warning(f"洞察提取失败: {e}")

        return insights

    async def batch_judge_patents(
        self,
        patents_data: list[dict[str, Any]],        context_template: JudgmentContext,
        judgment_types: list[str] = None,
    ) -> list[JudgmentResult]:
        """批量判断专利"""
        if judgment_types is None:
            judgment_types = [JudgmentType.PATENTABILITY]

        results = []

        for patent_data in patents_data:
            try:
                # 为每个专利创建上下文
                context = JudgmentContext(
                    patent_id=patent_data.get("patent_id", "unknown"),
                    technology_field=context_template.technology_field,
                    market_context=context_template.market_context,
                    legal_framework=context_template.legal_framework,
                    business_objectives=context_template.business_objectives,
                    stakeholder_interests=context_template.stakeholder_interests,
                )

                # 执行所有类型的判断
                for judgment_type in judgment_types:
                    judgment = await self._make_judgment(judgment_type, patent_data, context)
                    results.append(judgment)

            except Exception:
                continue

        return results

    async def enhance_rule_analysis(
        self, rule_analysis: PatentAnalysis, patent_data: dict[str, Any], context: JudgmentContext
    ) -> PatentAnalysis:
        """增强规则分析"""
        try:
            # 获取LLM增强判断
            patentability_judgment = await self.judge_patentability(
                patent_data, context, rule_analysis
            )

            # 将LLM判断结果整合到规则分析中
            enhanced_analysis = PatentAnalysis(
                patent_id=rule_analysis.patent_id,
                analysis_type=rule_analysis.analysis_type,
                elements=rule_analysis.elements,
                applied_rule_chains=rule_analysis.applied_rule_chains,
                reasoning_results=rule_analysis.reasoning_results,
                overall_assessment=rule_analysis.overall_assessment,
                recommendations=rule_analysis.recommendations
                + patentability_judgment.recommendations,
                confidence=(rule_analysis.confidence + patentability_judgment.confidence_score) / 2,
                timestamp=rule_analysis.timestamp,
            )

            # 添加LLM分析信息
            enhanced_analysis.overall_assessment["llm_enhanced"] = True
            enhanced_analysis.overall_assessment["llm_judgment"] = (
                patentability_judgment.primary_conclusion
            )

            return enhanced_analysis

        except Exception:
            return rule_analysis

    def get_statistics(self) -> dict[str, Any]:
        """获取统计信息"""
        return {
            **self.stats,
            "cache_size": len(self.judgment_cache),
            "insight_cache_size": len(self.insight_cache),
        }

    async def close(self):
        """关闭LLM增强判断系统"""
        self.judgment_cache.clear()
        self.insight_cache.clear()
        self._initialized = False
        self.logger.info("✅ LLMEnhancedJudgment 已关闭")


# 便捷函数
async def get_llm_judgment_engine(
    llm_provider: LLMProvider = LLMProvider.LOCAL,
) -> LLMEnhancedJudgment:
    """获取LLM增强判断引擎实例"""
    engine = LLMEnhancedJudgment(llm_provider)
    await engine.initialize()
    return engine


async def intelligent_patent_assessment(
    patent_data: dict[str, Any], context: JudgmentContext
) -> JudgmentResult:
    """便捷函数:智能专利评估"""
    engine = await get_llm_judgment_engine()
    return await engine.judge_patentability(patent_data, context)


if __name__ == "__main__":
    print("LLM增强智能判断系统模块已加载")
