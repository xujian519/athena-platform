#!/usr/bin/env python3
from __future__ import annotations
"""
专家级规则推理引擎
Expert Rule Reasoning Engine

基于专利规则知识图谱的专家级推理系统,支持复杂规则链推理和智能判断
作者: 小诺·双鱼座
创建时间: 2025-12-21
版本: v1.0.0 "专家推理"
"""

import json
import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

import networkx as nx

from ..knowledge.patent_analysis.enhanced_knowledge_graph import EnhancedPatentKnowledgeGraph

logger = logging.getLogger(__name__)


class ReasoningType(Enum):
    """推理类型"""

    DEDUCTIVE = "deductive"  # 演绎推理
    INDUCTIVE = "inductive"  # 归纳推理
    ABDUCTIVE = "abductive"  # 反绎推理
    HYBRID = "hybrid"  # 混合推理


class RuleType(Enum):
    """规则类型"""

    CONDITIONAL = "conditional"  # 条件规则
    CAUSAL = "causal"  # 因果规则
    TEMPORAL = "temporal"  # 时序规则
    SPATIAL = "spatial"  # 空间规则
    LOGICAL = "logical"  # 逻辑规则
    LEGAL = "legal"  # 法律规则


class ConfidenceLevel(Enum):
    """置信度级别"""

    VERY_LOW = (0.0, 0.3)
    LOW = (0.3, 0.5)
    MEDIUM = (0.5, 0.7)
    HIGH = (0.7, 0.9)
    VERY_HIGH = (0.9, 1.0)


@dataclass
class RuleCondition:
    """规则条件"""

    condition_id: str
    condition_type: str  # AND, OR, NOT
    parameters: dict[str, Any]
    weight: float = 1.0
    description: str = ""


@dataclass
class RuleConclusion:
    """规则结论"""

    conclusion_id: str
    conclusion_type: str
    confidence: float
    explanation: str = ""
    supporting_evidence: list[str] = field(default_factory=list)


@dataclass
class ReasoningRule:
    """推理规则"""

    rule_id: str
    rule_name: str
    rule_type: RuleType
    reasoning_type: ReasoningType
    conditions: list[RuleCondition]
    conclusions: list[RuleConclusion]
    priority: int = 1
    applicability_scope: dict[str, Any] = field(default_factory=dict)
    references: list[str] = field(default_factory=list)


@dataclass
class ReasoningStep:
    """推理步骤"""

    step_id: str
    rule_id: str
    input_facts: list[str]
    applied_rule: ReasoningRule
    intermediate_results: dict[str, Any]
    confidence: float
    explanation: str
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class ReasoningChain:
    """推理链"""

    chain_id: str
    reasoning_type: ReasoningType
    initial_facts: list[str]
    reasoning_steps: list[ReasoningStep]
    final_conclusions: list[RuleConclusion]
    overall_confidence: float
    reasoning_path: list[str]  # 经过的规则ID路径


class ExpertRuleEngine:
    """专家级规则推理引擎"""

    def __init__(self):
        self.name = "专家级规则推理引擎"
        self.version = "1.0.0"
        self._initialized = False
        self.logger = logging.getLogger(self.name)

        # 知识图谱集成
        self.knowledge_graph: EnhancedPatentKnowledgeGraph | None = None

        # 规则库
        self.rules: dict[str, ReasoningRule] = {}
        self.rule_graph = nx.DiGraph()  # 规则依赖图

        # 推理缓存
        self.reasoning_cache: dict[str, ReasoningChain] = {}
        self.cache_ttl = 3600  # 1小时

        # 推理配置
        self.config = {
            "max_depth": 10,  # 最大推理深度
            "confidence_threshold": 0.6,  # 置信度阈值
            "enable_explanation": True,  # 启用解释生成
            "enable_parallel": True,  # 启用并行推理
            "cache_enabled": True,  # 启用缓存
            "rule_pruning": True,  # 启用规则剪枝
            "conflict_resolution": "priority",  # 冲突解决策略
        }

        # 推理统计
        self.stats = {
            "total_reasonings": 0,
            "successful_reasonings": 0,
            "average_confidence": 0.0,
            "average_steps": 0.0,
            "cache_hits": 0,
            "cache_misses": 0,
        }

        # LLM服务(用于智能判断)
        self.llm_service = None

    async def initialize(self):
        """初始化专家规则引擎"""
        try:
            # 初始化知识图谱
            self.knowledge_graph = await EnhancedPatentKnowledgeGraph.initialize()

            # 加载规则库
            await self._load_rule_library()

            # 构建规则依赖图
            await self._build_rule_graph()

            # 初始化LLM服务
            await self._init_llm_service()

            self._initialized = True
            self.logger.info("✅ ExpertRuleEngine 初始化完成")
            return True

        except Exception:
            return False

    async def _load_rule_library(self):
        """加载规则库"""
        try:
            # 专利审查核心规则
            patent_rules = await self._generate_patent_rules()
            self.rules.update(patent_rules)

            # 法律逻辑规则
            legal_rules = await self._generate_legal_rules()
            self.rules.update(legal_rules)

            # 技术创新规则
            innovation_rules = await self._generate_innovation_rules()
            self.rules.update(innovation_rules)

            self.logger.info(f"✅ 规则库加载完成: {len(self.rules)} 条规则")

        except Exception as e:
            self.logger.error(f"规则库加载失败: {e}")

    async def _generate_patent_rules(self) -> dict[str, ReasoningRule]:
        """生成专利审查规则"""
        rules = {}

        # 新颖性审查规则
        rules["novelty_check_001"] = ReasoningRule(
            rule_id="novelty_check_001",
            rule_name="技术方案新颖性审查",
            rule_type=RuleType.LEGAL,
            reasoning_type=ReasoningType.DEDUCTIVE,
            conditions=[
                RuleCondition(
                    condition_id="existing_art_found",
                    condition_type="NOT",
                    parameters={"search_results": "relevant_prior_art"},
                    weight=1.0,
                    description="未检索到相关现有技术",
                )
            ],
            conclusions=[
                RuleConclusion(
                    conclusion_id="novelty_confirmed",
                    conclusion_type="positive",
                    confidence=0.85,
                    explanation="经检索未发现相同技术方案,具备新颖性",
                    supporting_evidence=["现有技术检索报告", "对比分析结果"],
                )
            ],
            priority=1,
            applicability_scope={"patent_type": "invention", "jurisdiction": "CN"},
            references=["专利法第22条", "审查指南第二部分第三章"],
        )

        # 创造性审查规则
        rules["inventiveness_check_001"] = ReasoningRule(
            rule_id="inventiveness_check_001",
            rule_name="技术创造性审查",
            rule_type=RuleType.LEGAL,
            reasoning_type=ReasoningType.INDUCTIVE,
            conditions=[
                RuleCondition(
                    condition_id="technical_advancement",
                    condition_type="AND",
                    parameters={
                        "unexpected_effect": True,
                        "commercial_success": False,
                        "long_felt_need": False,
                    },
                    weight=0.7,
                ),
                RuleCondition(
                    condition_id="non_obviousness",
                    condition_type="AND",
                    parameters={"combine_difficulty": "high", "technical_gap": "significant"},
                    weight=0.8,
                ),
            ],
            conclusions=[
                RuleConclusion(
                    conclusion_id="inventiveness_confirmed",
                    conclusion_type="positive",
                    confidence=0.75,
                    explanation="技术方案具有突出的实质性特点和显著的进步",
                    supporting_evidence=["技术效果对比", "专家意见", "市场反馈"],
                )
            ],
            priority=2,
            applicability_scope={"patent_type": "invention"},
            references=["专利法第22条", "审查指南第二部分第四章"],
        )

        # 实用性审查规则
        rules["utility_check_001"] = ReasoningRule(
            rule_id="utility_check_001",
            rule_name="技术实用性审查",
            rule_type=RuleType.CAUSAL,
            reasoning_type=ReasoningType.DEDUCTIVE,
            conditions=[
                RuleCondition(
                    condition_id="industrial_applicability",
                    condition_type="AND",
                    parameters={
                        "manufacturable": True,
                        "reproducible": True,
                        "beneficial_use": True,
                    },
                    weight=1.0,
                )
            ],
            conclusions=[
                RuleConclusion(
                    conclusion_id="utility_confirmed",
                    conclusion_type="positive",
                    confidence=0.90,
                    explanation="技术方案能够在产业上制造或使用,并能产生积极效果",
                    supporting_evidence=["制造可行性分析", "使用效果验证"],
                )
            ],
            priority=3,
            applicability_scope={"patent_type": ["invention", "utility_model"]},
            references=["专利法第22条", "审查指南第二部分第五章"],
        )

        return rules

    async def _generate_legal_rules(self) -> dict[str, ReasoningRule]:
        """生成法律逻辑规则"""
        rules = {}

        # 权利要求范围规则
        rules["claim_scope_001"] = ReasoningRule(
            rule_id="claim_scope_001",
            rule_name="权利要求保护范围审查",
            rule_type=RuleType.LOGICAL,
            reasoning_type=ReasoningType.DEDUCTIVE,
            conditions=[
                RuleCondition(
                    condition_id="claim_clarity",
                    condition_type="AND",
                    parameters={
                        "clear_terminology": True,
                        "well_defined_boundaries": True,
                        "no_ambiguity": True,
                    },
                    weight=0.6,
                ),
                RuleCondition(
                    condition_id="technical_feature_support",
                    condition_type="AND",
                    parameters={"sufficient_disclosure": True, "enablement_met": True},
                    weight=0.8,
                ),
            ],
            conclusions=[
                RuleConclusion(
                    conclusion_id="claim_scope_appropriate",
                    conclusion_type="positive",
                    confidence=0.80,
                    explanation="权利要求保护范围清晰合理,得到说明书支持",
                )
            ],
            priority=1,
            references=["专利法第26条第4款", "审查指南第二部分第二章"],
        )

        return rules

    async def _generate_innovation_rules(self) -> dict[str, ReasoningRule]:
        """生成技术创新规则"""
        rules = {}

        # 技术进步判断规则
        rules["technical_progress_001"] = ReasoningRule(
            rule_id="technical_progress_001",
            rule_name="技术进步性判断",
            rule_type=RuleType.CAUSAL,
            reasoning_type=ReasoningType.INDUCTIVE,
            conditions=[
                RuleCondition(
                    condition_id="performance_improvement",
                    condition_type="OR",
                    parameters={
                        "efficiency_gain": ">20%",
                        "cost_reduction": ">15%",
                        "quality_enhancement": "significant",
                    },
                    weight=0.7,
                ),
                RuleCondition(
                    condition_id="market_advantage",
                    condition_type="AND",
                    parameters={"competitive_edge": True, "market_potential": "high"},
                    weight=0.5,
                ),
            ],
            conclusions=[
                RuleConclusion(
                    conclusion_id="significant_progress",
                    conclusion_type="positive",
                    confidence=0.75,
                    explanation="技术方案在性能或成本方面具有显著优势",
                )
            ],
            priority=2,
            references=["技术创新评价指标", "技术进步评估方法"],
        )

        return rules

    async def _build_rule_graph(self):
        """构建规则依赖图"""
        try:
            self.rule_graph.clear()

            # 添加规则节点
            for rule_id, rule in self.rules.items():
                self.rule_graph.add_node(
                    rule_id, rule=rule, priority=rule.priority, rule_type=rule.rule_type.value
                )

            # 构建规则依赖关系
            for rule_id, rule in self.rules.items():
                # 基于条件结论构建依赖
                for condition in rule.conditions:
                    # 查找可能满足此条件的规则结论
                    for other_rule_id, other_rule in self.rules.items():
                        if rule_id == other_rule_id:
                            continue

                        for conclusion in other_rule.conclusions:
                            if self._condition_matches_conclusion(condition, conclusion):
                                self.rule_graph.add_edge(other_rule_id, rule_id)
                                break

            self.logger.info(
                f"✅ 规则依赖图构建完成: {len(self.rule_graph.nodes)} 节点, {len(self.rule_graph.edges)} 边"
            )

        except Exception as e:
            self.logger.error(f"规则依赖图构建失败: {e}")

    def _condition_matches_conclusion(
        self, condition: RuleCondition, conclusion: RuleConclusion
    ) -> bool:
        """判断条件是否与结论匹配"""
        # 简化的匹配逻辑,实际应用中需要更复杂的语义匹配
        condition_keywords = {
            "novelty": ["novelty", "new", "original"],
            "inventiveness": ["inventive", "creative", "innovative"],
            "utility": ["useful", "practical", "applicable"],
            "claim": ["claim", "scope", "protection"],
        }

        for keyword, terms in condition_keywords.items():
            if keyword in condition.condition_id.lower():
                return any(term in conclusion.conclusion_id.lower() for term in terms)

        return False

    async def _init_llm_service(self):
        """初始化LLM服务"""
        try:
            # 这里可以集成具体的LLM服务
            self.llm_service = "mock_llm_service"  # 占位符
            self.logger.info("✅ LLM服务初始化完成")
        except Exception as e:
            self.logger.error(f"LLM服务初始化失败: {e}")

    async def reason(
        self,
        facts: list[str],
        reasoning_type: ReasoningType = ReasoningType.HYBRID,
        context: Optional[dict[str, Any]] = None,
    ) -> ReasoningChain:
        """
        执行专家推理

        Args:
            facts: 输入事实
            reasoning_type: 推理类型
            context: 上下文信息

        Returns:
            ReasoningChain: 推理链
        """
        if not self._initialized:
            raise RuntimeError("ExpertRuleEngine未初始化")

        self.stats["total_reasonings"] += 1

        # 生成推理ID
        chain_id = (
            f"reasoning_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{hash(str(facts)) % 10000:04d}"
        )

        # 检查缓存
        cache_key = self._generate_cache_key(facts, reasoning_type, context)
        if self.config.get("cache_enabled") and cache_key in self.reasoning_cache:
            self.stats["cache_hits"] += 1
            return self.reasoning_cache.get(cache_key)

        self.stats["cache_misses"] += 1

        try:
            # 执行推理
            reasoning_chain = await self._execute_reasoning(
                chain_id, facts, reasoning_type, context
            )

            # 缓存结果
            if self.config.get("cache_enabled"):
                self.reasoning_cache[cache_key] = reasoning_chain

            # 更新统计
            self.stats["successful_reasonings"] += 1
            self.stats["average_confidence"] = (
                self.stats["average_confidence"] * (self.stats["successful_reasonings"] - 1)
                + reasoning_chain.overall_confidence
            ) / self.stats["successful_reasonings"]

            self.logger.info(
                f"✅ 推理完成: {chain_id}, 置信度: {reasoning_chain.overall_confidence:.3f}"
            )
            return reasoning_chain

        except Exception:
            raise

    async def _execute_reasoning(
        self,
        chain_id: str,
        facts: list[str],
        reasoning_type: ReasoningType,
        context: dict[str, Any],    ) -> ReasoningChain:
        """执行具体推理过程"""
        reasoning_steps = []
        current_facts = facts.copy()
        applied_rules = set()
        reasoning_path = []

        # 选择起始规则
        candidate_rules = await self._select_applicable_rules(current_facts, context)

        depth = 0
        final_conclusions = []

        while candidate_rules and depth < self.config.get("max_depth"):
            depth += 1

            # 选择最优规则
            best_rule = await self._select_best_rule(candidate_rules, applied_rules)
            if not best_rule:
                break

            # 应用规则
            step = await self._apply_rule(best_rule, current_facts, context)
            reasoning_steps.append(step)
            applied_rules.add(best_rule.rule_id)
            reasoning_path.append(best_rule.rule_id)

            # 更新事实
            new_facts = await self._extract_new_facts(step)
            current_facts.extend(new_facts)

            # 收集结论
            final_conclusions.extend(
                [
                    c
                    for c in step.applied_rule.conclusions
                    if c.confidence >= self.config.get("confidence_threshold")
                ]
            )

            # 选择下一批规则
            candidate_rules = await self._select_applicable_rules(current_facts, context)

            # 过滤已应用的规则
            candidate_rules = [r for r in candidate_rules if r.rule_id not in applied_rules]

            # 规则剪枝
            if self.config.get("rule_pruning"):
                candidate_rules = await self._prune_rules(candidate_rules, reasoning_path)

        # 计算整体置信度
        overall_confidence = self._calculate_overall_confidence(final_conclusions)

        # 构建推理链
        reasoning_chain = ReasoningChain(
            chain_id=chain_id,
            reasoning_type=reasoning_type,
            initial_facts=facts,
            reasoning_steps=reasoning_steps,
            final_conclusions=final_conclusions,
            overall_confidence=overall_confidence,
            reasoning_path=reasoning_path,
        )

        # 更新统计
        self.stats["average_steps"] = (
            self.stats["average_steps"] * (self.stats["total_reasonings"] - 1)
            + len(reasoning_steps)
        ) / self.stats["total_reasonings"]

        return reasoning_chain

    async def _select_applicable_rules(
        self, facts: list[str], context: dict[str, Any]
    ) -> list[ReasoningRule]:
        """选择适用的规则"""
        applicable_rules = []

        for rule in self.rules.values():
            if await self._is_rule_applicable(rule, facts, context):
                applicable_rules.append(rule)

        return applicable_rules

    async def _is_rule_applicable(
        self, rule: ReasoningRule, facts: list[str], context: dict[str, Any]
    ) -> bool:
        """判断规则是否适用"""
        # 检查适用范围
        if rule.applicability_scope and context:
            for key, value in rule.applicability_scope.items():
                if key in context and context[key] not in value:
                    return False

        # 检查条件满足度
        for condition in rule.conditions:
            if not await self._evaluate_condition(condition, facts, context):
                return False

        return True

    async def _evaluate_condition(
        self, condition: RuleCondition, facts: list[str], context: dict[str, Any]
    ) -> bool:
        """评估条件是否满足"""
        # 简化的条件评估逻辑
        fact_text = " ".join(facts).lower()

        # 基于关键词匹配
        for _param_key, param_value in condition.parameters.items():
            if isinstance(param_value, str):
                if param_value.lower() in fact_text:
                    return condition.condition_type == "AND" or condition.condition_type == "OR"
            elif isinstance(param_value, dict):
                # 处理复杂参数
                pass

        # 默认返回True,实际应用中需要更复杂的逻辑
        return True

    async def _select_best_rule(
        self, candidate_rules: list[ReasoningRule], applied_rules: set[str]
    ) -> ReasoningRule | None:
        """选择最优规则"""
        if not candidate_rules:
            return None

        # 优先选择高优先级且未应用的规则
        best_rule = None
        best_score = -1

        for rule in candidate_rules:
            if rule.rule_id in applied_rules:
                continue

            # 计算规则评分
            score = rule.priority
            score += len(rule.conditions) * 0.1  # 复杂度加分
            score -= len(rule.conclusions) * 0.05  # 结论数量减分

            if score > best_score:
                best_score = score
                best_rule = rule

        return best_rule

    async def _apply_rule(
        self, rule: ReasoningRule, facts: list[str], context: dict[str, Any]
    ) -> ReasoningStep:
        """应用规则"""
        step_id = f"step_{datetime.now().strftime('%H%M%S')}_{rule.rule_id}"

        # 评估中间结果
        intermediate_results = {}
        for condition in rule.conditions:
            condition_result = await self._evaluate_condition(condition, facts, context)
            intermediate_results[condition.condition_id] = condition_result

        # 计算步骤置信度
        confidence = min(rule.conclusions, key=lambda c: c.confidence).confidence
        confidence *= sum(1 for r in intermediate_results.values() if r) / len(intermediate_results)

        # 生成解释
        explanation = f"应用规则'{rule.rule_name}'"
        if self.config.get("enable_explanation"):
            explanation += f",基于条件: {', '.join(rule.conditions[0].parameters.keys())}"

        return ReasoningStep(
            step_id=step_id,
            rule_id=rule.rule_id,
            input_facts=facts,
            applied_rule=rule,
            intermediate_results=intermediate_results,
            confidence=confidence,
            explanation=explanation,
        )

    async def _extract_new_facts(self, step: ReasoningStep) -> list[str]:
        """从推理步骤中提取新事实"""
        new_facts = []

        for conclusion in step.applied_rule.conclusions:
            if conclusion.confidence >= self.config.get("confidence_threshold"):
                # 将结论转化为新事实
                fact = conclusion.explanation
                if fact not in step.input_facts:
                    new_facts.append(fact)

        return new_facts

    async def _prune_rules(
        self, candidate_rules: list[ReasoningRule], reasoning_path: list[str]
    ) -> list[ReasoningRule]:
        """规则剪枝"""
        # 简单的剪枝策略:避免循环依赖
        pruned_rules = []

        for rule in candidate_rules:
            # 检查是否会造成循环
            would_create_cycle = False
            for applied_rule_id in reasoning_path:
                if self.rule_graph.has_edge(rule.rule_id, applied_rule_id):
                    would_create_cycle = True
                    break

            if not would_create_cycle:
                pruned_rules.append(rule)

        return pruned_rules

    def _calculate_overall_confidence(self, conclusions: list[RuleConclusion]) -> float:
        """计算整体置信度"""
        if not conclusions:
            return 0.0

        # 使用加权平均
        total_weight = sum(c.confidence for c in conclusions)
        weighted_sum = sum(c.confidence * c.confidence for c in conclusions)

        return weighted_sum / total_weight if total_weight > 0 else 0.0

    def _generate_cache_key(
        self, facts: list[str], reasoning_type: ReasoningType, context: dict[str, Any]
    ) -> str:
        """生成缓存键"""
        import hashlib

        combined = f"{reasoning_type.value}|{'|'.join(sorted(facts))}|{json.dumps(context or {}, sort_keys=True)}"
        return hashlib.md5(combined.encode('utf-8'), usedforsecurity=False).hexdigest()

    async def get_reasoning_explanation(self, chain_id: str) -> Optional[str]:
        """获取推理解释"""
        if chain_id not in self.reasoning_cache:
            return None

        chain = self.reasoning_cache.get(chain_id)

        explanation = f"推理链ID: {chain.chain_id}\n"
        explanation += f"推理类型: {chain.reasoning_type.value}\n"
        explanation += f"整体置信度: {chain.overall_confidence:.3f}\n\n"

        explanation += "初始事实:\n"
        for fact in chain.initial_facts:
            explanation += f"- {fact}\n"

        explanation += "\n推理步骤:\n"
        for i, step in enumerate(chain.reasoning_steps, 1):
            explanation += f"{i}. {step.explanation} (置信度: {step.confidence:.3f})\n"

        explanation += "\n最终结论:\n"
        for conclusion in chain.final_conclusions:
            explanation += f"- {conclusion.explanation} (置信度: {conclusion.confidence:.3f})\n"

        return explanation

    def get_statistics(self) -> dict[str, Any]:
        """获取统计信息"""
        return self.stats.copy()

    async def close(self):
        """关闭专家规则引擎"""
        self._initialized = False
        self.reasoning_cache.clear()
        self.logger.info("✅ ExpertRuleEngine 已关闭")


# 便捷函数
async def get_expert_rule_engine() -> ExpertRuleEngine:
    """获取专家规则引擎实例"""
    engine = ExpertRuleEngine()
    await engine.initialize()
    return engine


async def reason_patent_compliance(
    patent_facts: list[str], context: Optional[dict[str, Any]] = None
) -> ReasoningChain:
    """便捷函数:专利合规性推理"""
    engine = await get_expert_rule_engine()
    return await engine.reason(patent_facts, ReasoningType.HYBRID, context)


if __name__ == "__main__":
    print("专家规则推理引擎模块已加载")
