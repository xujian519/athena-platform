#!/usr/bin/env python3
from __future__ import annotations
"""
高级推理算法

Advanced Reasoning Algorithms

实现基于最新研究的高级推理算法:
- 贝叶斯推理 (Bayesian Reasoning)
- 概率推理 (Probabilistic Reasoning)
- 模糊推理 (Fuzzy Reasoning)
- 模态推理 (Modal Reasoning)
- 定性推理 (Qualitative Reasoning)
- 反事实推理 (Counterfactual Reasoning)
"""

import math
import time
from dataclasses import dataclass, field
from typing import Any

import numpy as np

from .enhanced_reasoning_base import (
    BaseReasoner,
    ReasoningChain,
    ReasoningContext,
    ReasoningResult,
    ReasoningStep,
    ReasoningType,
)


@dataclass
class BayesianNetwork:
    """贝叶斯网络结构"""

    nodes: dict[str, dict[str, Any]] = field(default_factory=dict)
    edges: dict[str, list[str]] = field(default_factory=dict)  # node -> [parents]
    conditional_probabilities: dict[str, dict[str, float]] = field(default_factory=dict)
    prior_probabilities: dict[str, float] = field(default_factory=dict)

    def add_node(
        self, node_id: str, node_type: str = "discrete", states: list[str] | None = None
    ) -> None:
        """添加节点"""
        self.nodes[node_id] = {"type": node_type, "states": states or ["True", "False"]}
        if node_id not in self.edges:
            self.edges[node_id] = []

    def add_edge(self, parent: str, child: str) -> None:
        """添加边(父子关系)"""
        if child not in self.edges:
            self.edges[child] = []
        if parent not in self.edges[child]:
            self.edges[child].append(parent)

    def set_prior_probability(self, node: str, probability: float) -> None:
        """设置先验概率"""
        self.prior_probabilities[node] = probability

    def set_conditional_probability(
        self, node: str, parent_config: str, probability: float
    ) -> None:
        """设置条件概率"""
        if node not in self.conditional_probabilities:
            self.conditional_probabilities[node] = {}
        self.conditional_probabilities[node][parent_config] = probability


@dataclass
class FuzzySet:
    """模糊集合定义"""

    name: str
    membership_function: str  # 'triangular', 'trapezoidal', 'gaussian'
    parameters: list[float]  # 函数参数
    universe: tuple[float, float] = (0.0, 1.0)

    def membership_degree(self, x: float) -> float:
        """计算隶属度"""
        if self.membership_function == "triangular":
            a, b, c = self.parameters
            if x <= a or x >= c:
                return 0.0
            elif a < x <= b:
                return (x - a) / (b - a)
            else:  # b < x < c
                return (c - x) / (c - b)

        elif self.membership_function == "trapezoidal":
            a, b, c, d = self.parameters
            if x <= a or x >= d:
                return 0.0
            elif a < x <= b:
                return (x - a) / (b - a)
            elif b < x <= c:
                return 1.0
            else:  # c < x < d
                return (d - x) / (d - c)

        elif self.membership_function == "gaussian":
            mean, sigma = self.parameters
            return math.exp(-((x - mean) ** 2) / (2 * sigma**2))

        return 0.0


@dataclass
class ModalLogicFrame:
    """模态逻辑框架"""

    accessibility_relations: dict[str, list[tuple[str, str]]] = field(default_factory=dict)
    possible_worlds: list[str] = field(default_factory=list)
    valuation: dict[str, dict[str, bool]] = field(default_factory=dict)

    def add_possible_world(self, world_id: str) -> None:
        """添加可能世界"""
        if world_id not in self.possible_worlds:
            self.possible_worlds.append(world_id)

    def add_accessibility_relation(self, agent: str, from_world: str, to_world: str) -> None:
        """添加可及关系"""
        if agent not in self.accessibility_relations:
            self.accessibility_relations[agent] = []
        self.accessibility_relations[agent].append((from_world, to_world))

    def set_truth_value(self, proposition: str, world: str, truth_value: bool) -> None:
        """设置真值"""
        if proposition not in self.valuation:
            self.valuation[proposition] = {}
        self.valuation[proposition][world] = truth_value


class BayesianReasoner(BaseReasoner):
    """贝叶斯推理器"""

    def __init__(self, config: dict[str, Any] | None = None):
        super().__init__(config or {})
        self.network = BayesianNetwork()
        self.evidence: dict[str, bool] = {}
        self.inference_method = (self.config or {}).get(
            "inference_method", "exact"
        )  # 'exact', 'approximate'

    def _get_reasoning_type(self) -> ReasoningType:
        return ReasoningType.BAYESIAN

    async def reason(
        self, query: str, context: ReasoningContext | None = None
    ) -> ReasoningResult:
        """贝叶斯推理"""
        # 创建或使用现有上下文
        ctx: ReasoningContext = context or ReasoningContext(input_data={"query": query})
        start_time = time.time()
        reasoning_chain = ReasoningChain(reasoning_type=ReasoningType.BAYESIAN)

        # 第1步:构建贝叶斯网络
        network_step = await self._construct_bayesian_network(ctx)
        reasoning_chain.add_step(network_step)

        # 第2步:输入证据
        evidence_step = await self._incorporate_evidence(ctx)
        reasoning_chain.add_step(evidence_step)

        # 第3步:执行推理
        inference_step = await self._perform_inference(ctx, evidence_step.output_state)
        reasoning_chain.add_step(inference_step)

        # 第4步:更新信念
        belief_update_step = await self._update_beliefs(inference_step.output_state)
        reasoning_chain.add_step(belief_update_step)

        # 计算执行时间
        execution_time = time.time() - start_time
        reasoning_chain.total_time = execution_time
        reasoning_chain.completed_at = time.time()

        # 创建推理结果
        final_posteriors = belief_update_step.output_state.get("updated_beliefs", {})
        conclusion = self._generate_conclusion_from_posteriors(final_posteriors)

        result = ReasoningResult(
            conclusion=conclusion,
            reasoning_chain=reasoning_chain,
            confidence=belief_update_step.confidence,
            reasoning_type=ReasoningType.BAYESIAN,
            performance_metrics={
                "execution_time": execution_time,
                "network_size": len(self.network.nodes),
                "evidence_count": len(self.evidence),
                "inference_method": self.inference_method,
            },
        )

        return result

    async def _construct_bayesian_network(self, context: ReasoningContext) -> ReasoningStep:
        """构建贝叶斯网络"""
        start_time = time.time()

        # 从输入数据中提取变量
        input_data = context.input_data
        variables = self._extract_variables(input_data)

        # 创建节点
        for var in variables:
            self.network.add_node(var["name"], var.get("type", "discrete"), var.get("states"))

        # 创建边(因果关系)
        relationships = self._extract_relationships(input_data, variables)
        for relationship in relationships:
            self.network.add_edge(relationship["parent"], relationship["child"])

        # 设置先验概率
        priors = self._extract_priors(input_data, variables)
        for prior in priors:
            self.network.set_prior_probability(prior["node"], prior["probability"])

        # 设置条件概率
        conditional_probs = self._extract_conditionals(input_data, relationships)
        for cp in conditional_probs:
            self.network.set_conditional_probability(cp["node"], cp["config"], cp["probability"])

        computation_time = time.time() - start_time

        return ReasoningStep(
            reasoning_type=ReasoningType.BAYESIAN,
            operation="construct_bayesian_network",
            input_state={"input_data": input_data},
            output_state={
                "network_nodes": list(self.network.nodes.keys()),
                "network_edges": self.network.edges,
                "node_count": len(self.network.nodes),
                "edge_count": sum(len(edges) for edges in self.network.edges.values()),
            },
            confidence=0.8,
            computation_time=computation_time,
            justification=f"构建了包含 {len(self.network.nodes)} 个节点的贝叶斯网络",
        )

    async def _incorporate_evidence(self, context: ReasoningContext) -> ReasoningStep:
        """输入证据"""
        start_time = time.time()

        # 从上下文中提取证据
        evidence_data = context.input_data.get("evidence", {})
        self.evidence = {}

        for node, value in evidence_data.items():
            if node in self.network.nodes:
                self.evidence[node] = bool(value)

        computation_time = time.time() - start_time

        return ReasoningStep(
            reasoning_type=ReasoningType.BAYESIAN,
            operation="incorporate_evidence",
            input_state={"evidence_data": evidence_data},
            output_state={"evidence": self.evidence.copy(), "evidence_count": len(self.evidence)},
            confidence=0.9,
            computation_time=computation_time,
            justification=f"输入了 {len(self.evidence)} 个证据",
        )

    async def _perform_inference(
        self, context: ReasoningContext, previous_output: dict[str, Any]
    ) -> ReasoningStep:
        """执行推理"""
        start_time = time.time()

        if self.inference_method == "exact":
            posteriors = self._exact_inference()
        else:
            posteriors = self._approximate_inference()

        computation_time = time.time() - start_time

        return ReasoningStep(
            reasoning_type=ReasoningType.BAYESIAN,
            operation="perform_inference",
            input_state=previous_output,
            output_state={
                "posterior_probabilities": posteriors,
                "inference_method": self.inference_method,
            },
            confidence=0.85,
            computation_time=computation_time,
            justification=f"使用 {self.inference_method} 方法执行推理",
        )

    async def _update_beliefs(self, previous_output: dict[str, Any]) -> ReasoningStep:
        """更新信念"""
        start_time = time.time()

        posteriors = previous_output.get("posterior_probabilities", {})

        # 计算信念更新
        updated_beliefs = {}
        for node, posterior in posteriors.items():
            if node in self.network.prior_probabilities:
                prior = self.network.prior_probabilities[node]
                belief_change = posterior - prior
                updated_beliefs[node] = {
                    "prior": prior,
                    "posterior": posterior,
                    "change": belief_change,
                    "confidence": posterior,
                }

        # 计算整体置信度
        avg_confidence = (
            float(np.mean([beliefs["confidence"] for beliefs in updated_beliefs.values()]))
            if updated_beliefs
            else 0.5
        )

        computation_time = time.time() - start_time

        return ReasoningStep(
            reasoning_type=ReasoningType.BAYESIAN,
            operation="update_beliefs",
            input_state=previous_output,
            output_state={
                "updated_beliefs": updated_beliefs,
                "average_confidence": avg_confidence,
                "significant_changes": [
                    node
                    for node, beliefs in updated_beliefs.items()
                    if abs(beliefs["change"]) > 0.2
                ],
            },
            confidence=avg_confidence,
            computation_time=computation_time,
            justification=f"更新了 {len(updated_beliefs)} 个节点的信念",
        )

    def _extract_variables(self, input_data: dict[str, Any]) -> list[dict[str, Any]]:
        """提取变量"""
        # 简化的变量提取
        variables = [
            {"name": "A", "type": "discrete", "states": ["True", "False"]},
            {"name": "B", "type": "discrete", "states": ["True", "False"]},
            {"name": "C", "type": "discrete", "states": ["True", "False"]},
        ]
        return variables

    def _extract_relationships(
        self, input_data: dict[str, Any], variables: list[dict[str, Any]]
    ) -> list[dict[str, str]]:
        """提取关系"""
        # 简化的关系提取:A -> B, B -> C
        if len(variables) >= 3:
            return [{"parent": "A", "child": "B"}, {"parent": "B", "child": "C"}]
        return []

    def _extract_priors(
        self, input_data: dict[str, Any], variables: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        """提取先验概率"""
        priors = []
        for var in variables:
            # 默认先验概率为0.5
            priors.append({"node": var["name"], "probability": 0.5})
        return priors

    def _extract_conditionals(
        self, input_data: dict[str, Any], relationships: list[dict[str, str]]
    ) -> list[dict[str, Any]]:
        """提取条件概率"""
        conditionals = []
        for rel in relationships:
            child = rel["child"]
            parent = rel["parent"]

            # P(C=True|B=True) = 0.8, P(C=True|B=False) = 0.3
            if child == "C" and parent == "B":
                conditionals.extend(
                    [
                        {"node": "C", "config": "B=True", "probability": 0.8},
                        {"node": "C", "config": "B=False", "probability": 0.3},
                    ]
                )

            # P(B=True|A=True) = 0.7, P(B=True|A=False) = 0.4
            elif child == "B" and parent == "A":
                conditionals.extend(
                    [
                        {"node": "B", "config": "A=True", "probability": 0.7},
                        {"node": "B", "config": "A=False", "probability": 0.4},
                    ]
                )

        return conditionals

    def _exact_inference(self) -> dict[str, float]:
        """精确推理(变量消元)"""
        # 简化的精确推理实现
        posteriors = {}

        # 基于证据和条件概率计算后验
        for node in self.network.nodes:
            if node in self.evidence:
                posteriors[node] = 1.0 if self.evidence[node] else 0.0
            else:
                # 简化的后验计算
                prior = self.network.prior_probabilities.get(node, 0.5)

                # 考虑证据的影响
                evidence_effect = 0.0
                for evidence_node, evidence_value in self.evidence.items():
                    if evidence_node in self.network.edges.get(node, []):
                        # 如果存在因果关系,调整概率
                        if evidence_value:
                            evidence_effect += 0.2
                        else:
                            evidence_effect -= 0.2

                posterior = max(0.0, min(1.0, prior + evidence_effect))
                posteriors[node] = posterior

        return posteriors

    def _approximate_inference(self) -> dict[str, float]:
        """近似推理(采样)"""
        # 简化的采样推理
        return self._exact_inference()  # 暂时使用精确推理

    def _generate_conclusion_from_posteriors(self, posteriors: dict[str, float]) -> str:
        """从后验概率生成结论"""
        if not posteriors:
            return "贝叶斯推理完成,但无具体结论"

        # 找出概率最高的变量
        max_node = max(posteriors.keys(), key=lambda k: posteriors.get(k, 0.0))
        max_prob = float(posteriors[max_node])  # 确保是 Python float

        if max_prob > 0.8:
            return f"根据贝叶斯推理,{max_node} 为真的概率很高 ({max_prob:.2f})"
        elif max_prob > 0.6:
            return f"根据贝叶斯推理,{max_node} 可能为真 (概率: {max_prob:.2f})"
        elif max_prob > 0.4:
            return f"根据贝叶斯推理,{max_node} 真假不确定 (概率: {max_prob:.2f})"
        else:
            return f"根据贝叶斯推理,{max_node} 可能为假 (概率: {max_prob:.2f})"


class FuzzyReasoner(BaseReasoner):
    """模糊推理器"""

    def __init__(self, config: dict[str, Any] | None = None):
        super().__init__(config or {})
        self.fuzzy_sets: dict[str, list[FuzzySet]] = {}
        self.fuzzy_rules: list[dict[str, Any]] = []
        self.inference_method = (self.config or {}).get(
            "fuzzy_method", "mamdani"
        )  # 'mamdani', 'sugeno', 'tsk'

    def _get_reasoning_type(self) -> ReasoningType:
        return ReasoningType.FUZZY

    async def reason(
        self, query: str, context: ReasoningContext | None = None
    ) -> ReasoningResult:
        """模糊推理"""
        ctx: ReasoningContext = context or ReasoningContext(input_data={"query": query})
        start_time = time.time()
        reasoning_chain = ReasoningChain(reasoning_type=ReasoningType.FUZZY)

        # 第1步:模糊化
        fuzzification_step = await self._fuzzification(ctx)
        reasoning_chain.add_step(fuzzification_step)

        # 第2步:规则推理
        rule_inference_step = await self._rule_inference(fuzzification_step.output_state)
        reasoning_chain.add_step(rule_inference_step)

        # 第3步:合成
        composition_step = await self._composition(rule_inference_step.output_state)
        reasoning_chain.add_step(composition_step)

        # 第4步:解模糊化
        defuzzification_step = await self._defuzzification(composition_step.output_state)
        reasoning_chain.add_step(defuzzification_step)

        # 计算执行时间
        execution_time = time.time() - start_time
        reasoning_chain.total_time = execution_time
        reasoning_chain.completed_at = time.time()

        # 创建推理结果
        final_output = defuzzification_step.output_state.get("crisp_output", 0.0)

        result = ReasoningResult(
            conclusion=f"模糊推理结果: {final_output:.2f}",
            reasoning_chain=reasoning_chain,
            confidence=defuzzification_step.confidence,
            reasoning_type=ReasoningType.FUZZY,
            performance_metrics={
                "execution_time": execution_time,
                "fuzzy_sets_count": len(self.fuzzy_sets),
                "rules_count": len(self.fuzzy_rules),
                "inference_method": self.inference_method,
            },
        )

        return result

    async def _fuzzification(self, context: ReasoningContext) -> ReasoningStep:
        """模糊化"""
        start_time = time.time()

        input_data = context.input_data
        fuzzified_inputs = {}

        # 初始化模糊集合
        self._initialize_fuzzy_sets()

        # 对每个输入变量进行模糊化
        for var_name, var_value in input_data.items():
            if var_name in self.fuzzy_sets:
                fuzzified_inputs[var_name] = {}
                for fuzzy_set in self.fuzzy_sets[var_name]:
                    membership_degree = fuzzy_set.membership_degree(float(var_value))
                    fuzzified_inputs[var_name][fuzzy_set.name] = membership_degree

        computation_time = time.time() - start_time

        return ReasoningStep(
            reasoning_type=ReasoningType.FUZZY,
            operation="fuzzification",
            input_state={"input_data": input_data},
            output_state={
                "fuzzified_inputs": fuzzified_inputs,
                "fuzzified_variables": list(fuzzified_inputs.keys()),
            },
            confidence=0.8,
            computation_time=computation_time,
            justification=f"对 {len(fuzzified_inputs)} 个变量进行了模糊化",
        )

    async def _rule_inference(self, previous_output: dict[str, Any]) -> ReasoningStep:
        """规则推理"""
        start_time = time.time()

        fuzzified_inputs = previous_output.get("fuzzified_inputs", {})
        rule_strengths = []

        # 初始化模糊规则
        self._initialize_fuzzy_rules()

        # 计算每条规则的激活强度
        for rule in self.fuzzy_rules:
            strength = self._calculate_rule_strength(rule, fuzzified_inputs)
            rule_strengths.append(
                {"rule": rule, "strength": strength, "conclusion": rule["conclusion"]}
            )

        computation_time = time.time() - start_time

        return ReasoningStep(
            reasoning_type=ReasoningType.FUZZY,
            operation="rule_inference",
            input_state=previous_output,
            output_state={
                "rule_strengths": rule_strengths,
                "active_rules": [rs for rs in rule_strengths if rs["strength"] > 0.1],
            },
            confidence=0.75,
            computation_time=computation_time,
            justification=f"评估了 {len(self.fuzzy_rules)} 条模糊规则的强度",
        )

    async def _composition(self, previous_output: dict[str, Any]) -> ReasoningStep:
        """合成"""
        start_time = time.time()

        rule_strengths = previous_output.get("rule_strengths", [])
        aggregated_output = {}

        # 按结论类型聚合规则强度
        conclusion_groups = {}
        for rs in rule_strengths:
            conclusion = rs["conclusion"]
            if conclusion not in conclusion_groups:
                conclusion_groups[conclusion] = []
            conclusion_groups[conclusion].append(rs["strength"])

        # 使用最大值合成方法
        for conclusion, strengths in conclusion_groups.items():
            aggregated_output[conclusion] = max(strengths)

        computation_time = time.time() - start_time

        return ReasoningStep(
            reasoning_type=ReasoningType.FUZZY,
            operation="composition",
            input_state=previous_output,
            output_state={
                "aggregated_output": aggregated_output,
                "conclusion_count": len(aggregated_output),
            },
            confidence=0.8,
            computation_time=computation_time,
            justification=f"合成了 {len(aggregated_output)} 个模糊结论",
        )

    async def _defuzzification(self, previous_output: dict[str, Any]) -> ReasoningStep:
        """解模糊化"""
        start_time = time.time()

        aggregated_output = previous_output.get("aggregated_output", {})

        # 使用重心法解模糊化
        crisp_output = self._centroid_defuzzification(aggregated_output)

        # 计算置信度
        max_strength = max(aggregated_output.values()) if aggregated_output else 0.0
        confidence = min(max_strength + 0.2, 1.0)  # 基于最大强度计算置信度

        computation_time = time.time() - start_time

        return ReasoningStep(
            reasoning_type=ReasoningType.FUZZY,
            operation="defuzzification",
            input_state=previous_output,
            output_state={
                "crisp_output": crisp_output,
                "defuzzification_method": "centroid",
                "max_rule_strength": max_strength,
            },
            confidence=confidence,
            computation_time=computation_time,
            justification=f"使用重心法解模糊化,得到精确输出 {crisp_output:.2f}",
        )

    def _initialize_fuzzy_sets(self) -> Any:
        """初始化模糊集合"""
        if not self.fuzzy_sets:
            # 为变量 "input" 创建模糊集合
            self.fuzzy_sets["input"] = [
                FuzzySet("low", "triangular", [0.0, 0.25, 0.5]),
                FuzzySet("medium", "triangular", [0.25, 0.5, 0.75]),
                FuzzySet("high", "triangular", [0.5, 0.75, 1.0]),
            ]

            # 为输出变量 "output" 创建模糊集合
            self.fuzzy_sets["output"] = [
                FuzzySet("low", "triangular", [0.0, 2.5, 5.0]),
                FuzzySet("medium", "triangular", [2.5, 5.0, 7.5]),
                FuzzySet("high", "triangular", [5.0, 7.5, 10.0]),
            ]

    def _initialize_fuzzy_rules(self) -> Any:
        """初始化模糊规则"""
        if not self.fuzzy_rules:
            self.fuzzy_rules = [
                {"antecedents": [("input", "low")], "conclusion": ("output", "low"), "weight": 1.0},
                {
                    "antecedents": [("input", "medium")],
                    "conclusion": ("output", "medium"),
                    "weight": 1.0,
                },
                {
                    "antecedents": [("input", "high")],
                    "conclusion": ("output", "high"),
                    "weight": 1.0,
                },
            ]

    def _calculate_rule_strength(
        self, rule: dict[str, Any], fuzzified_inputs: dict[str, Any]
    ) -> float:
        """计算规则强度"""
        antecedents = rule["antecedents"]
        strengths = []

        for var_name, fuzzy_set_name in antecedents:
            if var_name in fuzzified_inputs and fuzzy_set_name in fuzzified_inputs[var_name]:
                strengths.append(fuzzified_inputs[var_name][fuzzy_set_name])
            else:
                strengths.append(0.0)

        # 使用最小值作为规则强度
        return min(strengths) if strengths else 0.0

    def _centroid_defuzzification(self, aggregated_output: dict[str, float]) -> float:
        """重心法解模糊化"""
        if not aggregated_output:
            return 0.0

        # 简化的重心计算
        weighted_sum = 0.0
        total_weight = 0.0

        # 为每个模糊结论分配代表性值
        conclusion_values = {"low": 2.5, "medium": 5.0, "high": 7.5}

        for conclusion, strength in aggregated_output.items():
            value = conclusion_values.get(conclusion, 5.0)
            weighted_sum += value * strength
            total_weight += strength

        return weighted_sum / total_weight if total_weight > 0 else 0.0


class ModalReasoner(BaseReasoner):
    """模态推理器"""

    def __init__(self, config: dict[str, Any] | None = None):
        super().__init__(config or {})
        self.modal_frame = ModalLogicFrame()
        self.modal_operators = ["□", "◇"]  # 必然性、可能性
        self.accessibility_type = (self.config or {}).get(
            "accessibility_type", "serial"
        )  # serial, reflexive, symmetric, transitive

    def _get_reasoning_type(self) -> ReasoningType:
        return ReasoningType.MODAL

    async def reason(
        self, query: str, context: ReasoningContext | None = None
    ) -> ReasoningResult:
        """模态推理"""
        # 确保上下文存在
        if context is None:
            context = ReasoningContext(input_data={"query": query})
        start_time = time.time()
        reasoning_chain = ReasoningChain(reasoning_type=ReasoningType.MODAL)

        # 第1步:构建可能世界
        world_construction_step = await self._construct_possible_worlds(context)
        reasoning_chain.add_step(world_construction_step)

        # 第2步:建立可及关系
        accessibility_step = await self._establish_accessibility(context)
        reasoning_chain.add_step(accessibility_step)

        # 第3步:模态逻辑推理
        modal_inference_step = await self._modal_inference(context, accessibility_step.output_state)
        reasoning_chain.add_step(modal_inference_step)

        # 第4步:语义评估
        semantic_evaluation_step = await self._semantic_evaluation(
            modal_inference_step.output_state
        )
        reasoning_chain.add_step(semantic_evaluation_step)

        # 计算执行时间
        execution_time = time.time() - start_time
        reasoning_chain.total_time = execution_time
        reasoning_chain.completed_at = time.time()

        # 创建推理结果
        evaluation_result = semantic_evaluation_step.output_state.get("evaluation_result", {})

        result = ReasoningResult(
            conclusion=self._generate_modal_conclusion(evaluation_result),
            reasoning_chain=reasoning_chain,
            confidence=semantic_evaluation_step.confidence,
            reasoning_type=ReasoningType.MODAL,
            performance_metrics={
                "execution_time": execution_time,
                "possible_worlds_count": len(self.modal_frame.possible_worlds),
                "accessibility_relations_count": sum(
                    len(relations)
                    for relations in self.modal_frame.accessibility_relations.values()
                ),
                "accessibility_type": self.accessibility_type,
            },
        )

        return result

    async def _construct_possible_worlds(self, context: ReasoningContext) -> ReasoningStep:
        """构建可能世界"""
        start_time = time.time()

        # 基于输入数据构建可能世界
        input_data = context.input_data
        scenarios = input_data.get("scenarios", ["default", "alternative1", "alternative2"])

        # 创建可能世界
        for i, _scenario in enumerate(scenarios):
            world_id = f"w{i}"
            self.modal_frame.add_possible_world(world_id)

        computation_time = time.time() - start_time

        return ReasoningStep(
            reasoning_type=ReasoningType.MODAL,
            operation="construct_possible_worlds",
            input_state={"input_data": input_data},
            output_state={
                "possible_worlds": self.modal_frame.possible_worlds.copy(),
                "world_count": len(self.modal_frame.possible_worlds),
            },
            confidence=0.8,
            computation_time=computation_time,
            justification=f"构建了 {len(self.modal_frame.possible_worlds)} 个可能世界",
        )

    async def _establish_accessibility(self, context: ReasoningContext) -> ReasoningStep:
        """建立可及关系"""
        start_time = time.time()

        # 根据可及关系类型建立关系
        worlds = self.modal_frame.possible_worlds
        agent = "default_agent"

        if self.accessibility_type == "serial":
            # 串行:每个世界都可以访问到某个世界
            for i, from_world in enumerate(worlds):
                for to_world in worlds[i + 1 :]:
                    self.modal_frame.add_accessibility_relation(agent, from_world, to_world)

        elif self.accessibility_type == "reflexive":
            # 自反:每个世界都可以访问自己
            for world in worlds:
                self.modal_frame.add_accessibility_relation(agent, world, world)

        elif self.accessibility_type == "symmetric":
            # 对称:关系是对称的
            for i, world1 in enumerate(worlds):
                for world2 in worlds[i + 1 :]:
                    self.modal_frame.add_accessibility_relation(agent, world1, world2)
                    self.modal_frame.add_accessibility_relation(agent, world2, world1)

        elif self.accessibility_type == "transitive":
            # 传递:关系是传递的
            for i in range(len(worlds)):
                for j in range(i + 1, len(worlds)):
                    for k in range(j + 1, len(worlds)):
                        self.modal_frame.add_accessibility_relation(agent, worlds[i], worlds[j])
                        self.modal_frame.add_accessibility_relation(agent, worlds[j], worlds[k])
                        self.modal_frame.add_accessibility_relation(agent, worlds[i], worlds[k])

        computation_time = time.time() - start_time

        return ReasoningStep(
            reasoning_type=ReasoningType.MODAL,
            operation="establish_accessibility",
            input_state={},
            output_state={
                "accessibility_relations": self.modal_frame.accessibility_relations.copy(),
                "relation_count": sum(
                    len(relations)
                    for relations in self.modal_frame.accessibility_relations.values()
                ),
            },
            confidence=0.85,
            computation_time=computation_time,
            justification=f"建立了 {self.accessibility_type} 类型的可及关系",
        )

    async def _modal_inference(
        self, context: ReasoningContext, previous_output: dict[str, Any]
    ) -> ReasoningStep:
        """模态逻辑推理"""
        start_time = time.time()

        input_data = context.input_data
        propositions = input_data.get("propositions", ["P", "Q"])

        # 为每个命题在每个可能世界中设置真值
        for proposition in propositions:
            for world in self.modal_frame.possible_worlds:
                # 简化的真值分配
                truth_value = hash(f"{proposition}_{world}") % 2 == 0
                self.modal_frame.set_truth_value(proposition, world, truth_value)

        # 执行模态推理
        modal_results = {}
        for proposition in propositions:
            # 必然性:在所有可及世界中为真
            necessity_result = self._evaluate_necessity(proposition)
            # 可能性:在某个可及世界中为真
            possibility_result = self._evaluate_possibility(proposition)

            modal_results[proposition] = {
                "necessity": necessity_result,
                "possibility": possibility_result,
            }

        computation_time = time.time() - start_time

        return ReasoningStep(
            reasoning_type=ReasoningType.MODAL,
            operation="modal_inference",
            input_state=previous_output,
            output_state={
                "modal_results": modal_results,
                "propositions_evaluated": list(modal_results.keys()),
            },
            confidence=0.8,
            computation_time=computation_time,
            justification=f"评估了 {len(modal_results)} 个命题的模态真值",
        )

    async def _semantic_evaluation(self, previous_output: dict[str, Any]) -> ReasoningStep:
        """语义评估"""
        start_time = time.time()

        modal_results = previous_output.get("modal_results", {})
        evaluation_result = {}

        # 评估模态公式的满足性
        for proposition, results in modal_results.items():
            necessity = results.get("necessity")
            possibility = results.get("possibility")

            # 计算语义评估分数
            necessity_score = (
                necessity["true_worlds"] / necessity["total_worlds"]
                if necessity["total_worlds"] > 0
                else 0.0
            )
            possibility_score = (
                possibility["true_worlds"] / possibility["total_worlds"]
                if possibility["total_worlds"] > 0
                else 0.0
            )

            evaluation_result[proposition] = {
                "necessity_score": necessity_score,
                "possibility_score": possibility_score,
                "modal_consistency": necessity_score <= possibility_score,  # □P → ◇P
                "overall_confidence": (necessity_score + possibility_score) / 2,
            }

        # 计算整体置信度
        overall_confidence = (
            float(np.mean([result.get("overall_confidence") for result in evaluation_result.values()]))
            if evaluation_result
            else 0.5
        )

        computation_time = time.time() - start_time

        return ReasoningStep(
            reasoning_type=ReasoningType.MODAL,
            operation="semantic_evaluation",
            input_state=previous_output,
            output_state={
                "evaluation_result": evaluation_result,
                "modal_consistency_check": all(
                    result.get("modal_consistency") for result in evaluation_result.values()
                ),
            },
            confidence=overall_confidence,
            computation_time=computation_time,
            justification=f"完成了 {len(evaluation_result)} 个命题的语义评估",
        )

    def _evaluate_necessity(self, proposition: str) -> dict[str, Any]:
        """评估必然性 □P"""
        agent = "default_agent"
        true_worlds = 0
        total_worlds = 0

        for from_world in self.modal_frame.possible_worlds:
            # 检查从from_world可及的所有世界
            accessible_worlds = [
                to_world
                for (f, to_world) in self.modal_frame.accessibility_relations.get(agent, [])
                if f == from_world
            ]

            # 如果没有可及关系,只考虑自身
            if not accessible_worlds:
                accessible_worlds = [from_world]

            # 检查在所有可及世界中P是否为真
            proposition_true_in_all = True
            for to_world in accessible_worlds:
                if not self.modal_frame.valuation.get(proposition, {}).get(to_world, False):
                    proposition_true_in_all = False
                    break

            if proposition_true_in_all:
                true_worlds += 1
            total_worlds += 1

        return {"true_worlds": true_worlds, "total_worlds": total_worlds}

    def _evaluate_possibility(self, proposition: str) -> dict[str, Any]:
        """评估可能性 ◇P"""
        agent = "default_agent"
        true_worlds = 0
        total_worlds = 0

        for from_world in self.modal_frame.possible_worlds:
            # 检查从from_world可及的所有世界
            accessible_worlds = [
                to_world
                for (f, to_world) in self.modal_frame.accessibility_relations.get(agent, [])
                if f == from_world
            ]

            # 如果没有可及关系,只考虑自身
            if not accessible_worlds:
                accessible_worlds = [from_world]

            # 检查在某个可及世界中P是否为真
            proposition_true_in_some = False
            for to_world in accessible_worlds:
                if self.modal_frame.valuation.get(proposition, {}).get(to_world, False):
                    proposition_true_in_some = True
                    break

            if proposition_true_in_some:
                true_worlds += 1
            total_worlds += 1

        return {"true_worlds": true_worlds, "total_worlds": total_worlds}

    def _generate_modal_conclusion(self, evaluation_result: dict[str, Any]) -> str:
        """生成模态推理结论"""
        if not evaluation_result:
            return "模态推理完成,但无具体结论"

        conclusions = []
        for proposition, result in evaluation_result.items():
            necessity_score = result.get("necessity_score")
            possibility_score = result.get("possibility_score")
            consistency = result.get("modal_consistency")

            if necessity_score > 0.8:
                conclusions.append(f"命题 {proposition} 必然为真")
            elif possibility_score > 0.8:
                conclusions.append(f"命题 {proposition} 可能为真")
            elif necessity_score < 0.2:
                conclusions.append(f"命题 {proposition} 必然为假")
            elif possibility_score < 0.2:
                conclusions.append(f"命题 {proposition} 可能为假")

            if not consistency:
                conclusions.append(f"命题 {proposition} 的模态推理存在不一致")

        if conclusions:
            return "模态推理结论:" + ";".join(conclusions)
        else:
            return "模态推理完成,但所有命题的模态真值都不确定"


class CounterfactualReasoner(BaseReasoner):
    """反事实推理器"""

    def __init__(self, config: dict[str, Any] | None = None):
        super().__init__(config or {})
        self.causal_model: dict[str, Any] = {}
        self.actual_world: dict[str, Any] = {}
        self.counterfactual_worlds: list[dict[str, Any]] = []

    def _get_reasoning_type(self) -> ReasoningType:
        return ReasoningType.COUNTERFACTUAL

    async def reason(
        self, query: str, context: ReasoningContext | None = None
    ) -> ReasoningResult:
        """反事实推理"""
        # 确保上下文存在
        if context is None:
            context = ReasoningContext(input_data={"query": query})
        start_time = time.time()
        reasoning_chain = ReasoningChain(reasoning_type=ReasoningType.COUNTERFACTUAL)

        # 第1步:建立现实世界模型
        actual_world_step = await self._establish_actual_world(context)
        reasoning_chain.add_step(actual_world_step)

        # 第2步:构建反事实假设
        counterfactual_step = await self._construct_counterfactual(context)
        reasoning_chain.add_step(counterfactual_step)

        # 第3步:因果推理
        causal_inference_step = await self._causal_inference(counterfactual_step.output_state)
        reasoning_chain.add_step(causal_inference_step)

        # 第4步:结果比较
        comparison_step = await self._compare_results(
            actual_world_step.output_state, causal_inference_step.output_state
        )
        reasoning_chain.add_step(comparison_step)

        # 计算执行时间
        execution_time = time.time() - start_time
        reasoning_chain.total_time = execution_time
        reasoning_chain.completed_at = time.time()

        # 创建推理结果
        comparison_result = comparison_step.output_state.get("comparison_result", {})

        result = ReasoningResult(
            conclusion=self._generate_counterfactual_conclusion(comparison_result),
            reasoning_chain=reasoning_chain,
            confidence=comparison_step.confidence,
            reasoning_type=ReasoningType.COUNTERFACTUAL,
            performance_metrics={
                "execution_time": execution_time,
                "counterfactual_scenarios": len(self.counterfactual_worlds),
                "causal_factors": len(self.causal_model),
            },
        )

        return result

    async def _establish_actual_world(self, context: ReasoningContext) -> ReasoningStep:
        """建立现实世界模型"""
        start_time = time.time()

        input_data = context.input_data
        self.actual_world = {
            "facts": input_data.get("facts", {}),
            "causes": input_data.get("causes", {}),
            "effects": input_data.get("effects", {}),
            "conditions": input_data.get("conditions", {}),
        }

        # 构建因果模型
        self.causal_model = {
            "variables": list(self.actual_world["facts"].keys()),
            "causal_relations": input_data.get("causal_relations", []),
            "intervention_points": input_data.get("intervention_points", []),
        }

        computation_time = time.time() - start_time

        return ReasoningStep(
            reasoning_type=ReasoningType.COUNTERFACTUAL,
            operation="establish_actual_world",
            input_state={"input_data": input_data},
            output_state={
                "actual_world": self.actual_world.copy(),
                "causal_model": self.causal_model.copy(),
                "variables_count": len(self.causal_model["variables"]),
            },
            confidence=0.9,
            computation_time=computation_time,
            justification="建立了现实世界的因果模型",
        )

    async def _construct_counterfactual(self, context: ReasoningContext) -> ReasoningStep:
        """构建反事实假设"""
        start_time = time.time()

        input_data = context.input_data
        counterfactual_assumptions = input_data.get("counterfactual_assumptions", {})

        self.counterfactual_worlds = []

        # 为每个反事实假设创建可能世界
        for i, (variable, new_value) in enumerate(counterfactual_assumptions.items()):
            # 复制现实世界
            counterfactual_world = self.actual_world.copy()
            counterfactual_world["facts"] = self.actual_world["facts"].copy()

            # 修改反事实变量
            counterfactual_world["facts"][variable] = new_value
            counterfactual_world["counterfactual_change"] = {variable: new_value}
            counterfactual_world["world_id"] = f"counterfactual_{i}"

            # 传播因果影响
            self._propagate_causal_effects(counterfactual_world, variable, new_value)

            self.counterfactual_worlds.append(counterfactual_world)

        computation_time = time.time() - start_time

        return ReasoningStep(
            reasoning_type=ReasoningType.COUNTERFACTUAL,
            operation="construct_counterfactual",
            input_state={"counterfactual_assumptions": counterfactual_assumptions},
            output_state={
                "counterfactual_worlds": self.counterfactual_worlds.copy(),
                "worlds_count": len(self.counterfactual_worlds),
            },
            confidence=0.8,
            computation_time=computation_time,
            justification=f"构建了 {len(self.counterfactual_worlds)} 个反事实世界",
        )

    async def _causal_inference(self, previous_output: dict[str, Any]) -> ReasoningStep:
        """因果推理"""
        start_time = time.time()

        counterfactual_worlds = previous_output.get("counterfactual_worlds", [])
        causal_inferences = []

        for world in counterfactual_worlds:
            # 推断反事实变化的结果
            inferred_effects = self._infer_causal_effects(world)

            causal_inferences.append(
                {
                    "world_id": world["world_id"],
                    "counterfactual_change": world["counterfactual_change"],
                    "inferred_effects": inferred_effects,
                    "causal_chain": self._trace_causal_chain(world),
                }
            )

        computation_time = time.time() - start_time

        return ReasoningStep(
            reasoning_type=ReasoningType.COUNTERFACTUAL,
            operation="causal_inference",
            input_state=previous_output,
            output_state={
                "causal_inferences": causal_inferences,
                "inferences_count": len(causal_inferences),
            },
            confidence=0.75,
            computation_time=computation_time,
            justification=f"完成了 {len(causal_inferences)} 个反事实世界的因果推理",
        )

    async def _compare_results(
        self, actual_output: dict[str, Any], inference_output: dict[str, Any]
    ) -> ReasoningStep:
        """结果比较"""
        start_time = time.time()

        actual_world = actual_output.get("actual_world", {})
        causal_inferences = inference_output.get("causal_inferences", [])

        comparison_result = {"differences": [], "similarities": [], "causal_strengths": []}

        for inference in causal_inferences:
            world_id = inference["world_id"]
            counterfactual_change = inference["counterfactual_change"]
            inferred_effects = inference["inferred_effects"]

            # 比较反事实世界与现实世界的差异
            differences = self._compare_worlds(
                actual_world, counterfactual_change, inferred_effects
            )

            comparison_result.get("differences").extend(differences)

            # 计算因果强度
            causal_strength = self._calculate_causal_strength(
                counterfactual_change, inferred_effects
            )
            comparison_result.get("causal_strengths").append(
                {"world_id": world_id, "causal_strength": causal_strength}
            )

        # 计算整体置信度
        avg_causal_strength = (
            float(np.mean([cs["causal_strength"] for cs in comparison_result.get("causal_strengths")]))
            if comparison_result.get("causal_strengths")
            else 0.5
        )

        computation_time = time.time() - start_time

        return ReasoningStep(
            reasoning_type=ReasoningType.COUNTERFACTUAL,
            operation="compare_results",
            input_state={"actual_output": actual_output, "inference_output": inference_output},
            output_state={
                "comparison_result": comparison_result,
                "average_causal_strength": avg_causal_strength,
            },
            confidence=avg_causal_strength,
            computation_time=computation_time,
            justification=f"比较了反事实世界与现实世界,平均因果强度为 {avg_causal_strength:.2f}",
        )

    def _propagate_causal_effects(
        self, world: dict[str, Any], changed_variable: str, new_value: Any
    ) -> Any:
        """传播因果影响"""
        # 简化的因果传播
        causal_relations = self.causal_model.get("causal_relations", [])

        for relation in causal_relations:
            if relation["cause"] == changed_variable:
                effect_var = relation["effect"]
                # 简单的线性影响模型
                effect_change = relation.get("strength", 0.5) * (
                    new_value - self.actual_world["facts"].get(changed_variable, 0)
                )
                current_effect = world["facts"].get(
                    effect_var, self.actual_world["facts"].get(effect_var, 0)
                )
                world["facts"][effect_var] = current_effect + effect_change

    def _infer_causal_effects(self, world: dict[str, Any]) -> dict[str, Any]:
        """推断因果效应"""
        return world.get("facts", {})

    def _trace_causal_chain(self, world: dict[str, Any]) -> list[dict[str, Any]]:
        """追踪因果链"""
        causal_relations = self.causal_model.get("causal_relations", [])
        chain = []

        for relation in causal_relations:
            if relation["cause"] in world.get("counterfactual_change", {}):
                chain.append(relation)

        return chain

    def _compare_worlds(
        self,
        actual_world: dict[str, Any],        counterfactual_change: dict[str, Any],        inferred_effects: dict[str, Any],    ) -> list[dict[str, Any]]:
        """比较世界差异"""
        differences = []

        for var, new_value in inferred_effects.items():
            actual_value = actual_world.get("facts", {}).get(var, 0)
            if abs(new_value - actual_value) > 0.01:  # 显著差异阈值
                differences.append(
                    {
                        "variable": var,
                        "actual_value": actual_value,
                        "counterfactual_value": new_value,
                        "difference": new_value - actual_value,
                        "relative_change": (
                            (new_value - actual_value) / actual_value if actual_value != 0 else 0
                        ),
                    }
                )

        return differences

    def _calculate_causal_strength(
        self, counterfactual_change: dict[str, Any], inferred_effects: dict[str, Any]
    ) -> float:
        """计算因果强度"""
        if not counterfactual_change or not inferred_effects:
            return 0.0

        # 简化的因果强度计算
        total_change = sum(abs(change) for change in inferred_effects.values())
        change_count = len(inferred_effects)

        if change_count == 0:
            return 0.0

        # 归一化因果强度
        return min(total_change / change_count, 1.0)

    def _generate_counterfactual_conclusion(self, comparison_result: dict[str, Any]) -> str:
        """生成反事实推理结论"""
        if not comparison_result:
            return "反事实推理完成,但无具体结论"

        avg_strength = comparison_result.get("average_causal_strength", 0.0)
        causal_strengths = comparison_result.get("causal_strengths", [])

        conclusions = []

        if avg_strength > 0.7:
            conclusions.append("反事实推理显示强因果关系")
        elif avg_strength > 0.4:
            conclusions.append("反事实推理显示中等因果关系")
        elif avg_strength > 0.1:
            conclusions.append("反事实推理显示弱因果关系")
        else:
            conclusions.append("反事实推理未显示明显因果关系")

        # 添加具体细节
        for cs in causal_strengths[:2]:  # 最多显示2个结果
            if cs["causal_strength"] > 0.5:
                conclusions.append(
                    f"世界 {cs['world_id']} 中因果强度为 {cs['causal_strength']:.2f}"
                )

        return ";".join(conclusions)


# 导出的主要接口
__all__ = [
    "BayesianNetwork",
    "BayesianReasoner",
    "CounterfactualReasoner",
    "FuzzyReasoner",
    "FuzzySet",
    "ModalLogicFrame",
    "ModalReasoner",
]
