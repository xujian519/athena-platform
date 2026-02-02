#!/usr/bin/env python3
"""
因果归因分析器 (Causal Attribution)
分析决策因果链和责任归因

作者: 小诺·双鱼公主
版本: v1.0.0
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class AttributionMethod(str, Enum):
    """归因方法"""

    DIRECT = "direct"  # 直接归因
    COUNTERFACTUAL = "counterfactual"  # 反事实归因
    SHAPLEY = "shapley"  # Shapley值归因
    GRADIENT = "gradient"  # 梯度归因


@dataclass
class CausalAttribution:
    """因果归因结果"""

    attribution_id: str
    decision: str
    outcome: Any
    attributions: dict[str, float]  # 因素 -> 归因分数
    method: AttributionMethod
    confidence: float = 0.0
    causal_chains: list[list[str]] = field(default_factory=list)
    explanation: str = ""


@dataclass
class ResponsibilityScore:
    """责任分数"""

    factor: str
    direct_responsibility: float  # 直接责任 (0-1)
    indirect_responsibility: float  # 间接责任 (0-1)
    total_responsibility: float  # 总责任 (0-1)
    rank: int = 0  # 排名


class CausalAttributor:
    """
    因果归因分析器

    功能:
    1. 分析决策因果链
    2. 计算因素归因分数
    3. 识别关键责任因素
    4. 生成归因报告
    """

    def __init__(self):
        self.name = "因果归因分析器"
        self.version = "1.0.0"
        self.attributions_performed = 0

        logger.info(f"✅ {self.name} 初始化完成")

    async def attribute(
        self,
        decision: str,
        outcome: Any,
        factors: dict[str, Any],        causal_graph: Any | None = None,
        method: AttributionMethod = AttributionMethod.DIRECT,
    ) -> CausalAttribution:
        """
        执行因果归因分析

        Args:
            decision: 决策描述
            outcome: 实际结果
            factors: 影响因素字典
            causal_graph: 因果图(可选)
            method: 归因方法

        Returns:
            因果归因结果
        """
        attribution_id = f"attr_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        # 根据方法计算归因
        if method == AttributionMethod.DIRECT:
            attributions = await self._direct_attribution(factors, outcome)
        elif method == AttributionMethod.COUNTERFACTUAL:
            attributions = await self._counterfactual_attribution(factors, outcome)
        elif method == AttributionMethod.SHAPLEY:
            attributions = await self._shapley_attribution(factors, outcome)
        else:
            attributions = await self._gradient_attribution(factors, outcome)

        # 计算因果链
        causal_chains = []
        if causal_graph:
            causal_chains = self._extract_causal_chains(causal_graph, list(attributions.keys()))

        # 计算置信度
        confidence = self._calculate_attribution_confidence(attributions)

        # 生成解释
        explanation = self._generate_attribution_explanation(decision, attributions, causal_chains)

        self.attributions_performed += 1

        return CausalAttribution(
            attribution_id=attribution_id,
            decision=decision,
            outcome=outcome,
            attributions=attributions,
            method=method,
            confidence=confidence,
            causal_chains=causal_chains,
            explanation=explanation,
        )

    async def _direct_attribution(self, factors: dict[str, Any], outcome: Any) -> dict[str, float]:
        """直接归因"""
        attributions = {}

        # 简化版:使用相关性
        total = sum(abs(v) if isinstance(v, (int, float)) else 1 for v in factors.values())

        for key, value in factors.items():
            if isinstance(value, (int, float)):
                attributions[key] = abs(value) / total if total > 0 else 0
            else:
                attributions[key] = 1.0 / len(factors)

        return attributions

    async def _counterfactual_attribution(
        self, factors: dict[str, Any], outcome: Any
    ) -> dict[str, float]:
        """反事实归因"""
        attributions = {}

        # 对每个因素计算反事实影响
        for key, _value in factors.items():
            # 模拟移除该因素
            counterfactual_factors = factors.copy()
            counterfactual_factors[key] = 0  # 设为中性值

            # 简化版:使用差异作为归因
            original_score = sum(
                abs(v) if isinstance(v, (int, float)) else 0 for v in factors.values()
            )
            counterfactual_score = sum(
                abs(v) if isinstance(v, (int, float)) else 0
                for v in counterfactual_factors.values()
            )

            impact = original_score - counterfactual_score
            attributions[key] = max(0, impact)

        # 归一化
        total = sum(attributions.values())
        if total > 0:
            attributions = {k: v / total for k, v in attributions.items()}

        return attributions

    async def _shapley_attribution(self, factors: dict[str, Any], outcome: Any) -> dict[str, float]:
        """Shapley值归因"""
        # Shapley值考虑所有可能的特征组合
        attributions = {}

        factor_keys = list(factors.keys())
        n = len(factor_keys)

        for key in factor_keys:
            shapley_value = 0.0

            # 遍历所有可能的子集
            for _i in range(n):
                # 简化版:只考虑边际贡献
                marginal_contribution = (
                    factors[key] if isinstance(factors[key], (int, float)) else 0
                )
                shapley_value += marginal_contribution / n

            attributions[key] = shapley_value

        # 归一化为正值
        total = sum(abs(v) for v in attributions.values())
        if total > 0:
            attributions = {k: abs(v) / total for k, v in attributions.items()}

        return attributions

    async def _gradient_attribution(
        self, factors: dict[str, Any], outcome: Any
    ) -> dict[str, float]:
        """梯度归因"""
        # 简化版:使用值大小的梯度
        attributions = {}

        values = [abs(v) if isinstance(v, (int, float)) else 0 for v in factors.values()]

        max_val = max(values) if values else 1
        if max_val == 0:
            max_val = 1

        for key, value in factors.items():
            if isinstance(value, (int, float)):
                attributions[key] = abs(value) / max_val
            else:
                attributions[key] = 0.5

        return attributions

    def _extract_causal_chains(self, causal_graph: Any, factors: list[str]) -> list[list[str]]:
        """提取因果链"""
        chains = []

        # 简化版:从每个因素到结果的路径
        for _factor in factors:
            # 这里应该调用causal_graph的方法
            # 暂时返回空列表
            pass

        return chains

    def _calculate_attribution_confidence(self, attributions: dict[str, float]) -> float:
        """计算归因置信度"""
        # 基于归因分布的集中度
        values = list(attributions.values())

        if not values:
            return 0.0

        # 计算基尼系数
        sorted_values = sorted(values)
        len(sorted_values)
        cumsum = [0]
        for v in sorted_values:
            cumsum.append(cumsum[-1] + v)

        # 简化版置信度计算
        max_ratio = max(values) / sum(values) if sum(values) > 0 else 0
        confidence = min(1.0, max_ratio * 2)  # 最大值占比较高则置信度高

        return confidence

    def _generate_attribution_explanation(
        self, decision: str, attributions: dict[str, float], causal_chains: list[list[str]]
    ) -> str:
        """生成归因解释"""
        # 按归因分数排序
        sorted_attrs = sorted(attributions.items(), key=lambda x: x[1], reverse=True)

        top_factors = sorted_attrs[:5]

        explanation_parts = [f"决策: {decision}", "主要影响因素:"]

        for i, (factor, score) in enumerate(top_factors, 1):
            explanation_parts.append(f"  {i}. {factor}: {score:.2%} 贡献度")

        return "\n".join(explanation_parts)

    def calculate_responsibility_scores(
        self, attribution: CausalAttribution
    ) -> list[ResponsibilityScore]:
        """
        计算责任分数

        Args:
            attribution: 归因结果

        Returns:
            责任分数列表
        """
        scores = []

        for factor, score in attribution.attributions.items():
            # 计算直接和间接责任
            direct = score * 0.7  # 假设70%是直接责任
            indirect = score * 0.3  # 30%是间接责任

            responsibility_score = ResponsibilityScore(
                factor=factor,
                direct_responsibility=direct,
                indirect_responsibility=indirect,
                total_responsibility=score,
            )

            scores.append(responsibility_score)

        # 按总责任排序并分配排名
        scores.sort(key=lambda x: x.total_responsibility, reverse=True)
        for i, score in enumerate(scores):
            score.rank = i + 1

        return scores

    def get_status(self) -> dict[str, Any]:
        """获取归因分析器状态"""
        return {
            "name": self.name,
            "version": self.version,
            "attributions_performed": self.attributions_performed,
            "supported_methods": [m.value for m in AttributionMethod],
        }


# 全局单例
_attribution_instance: CausalAttributor | None = None


def get_causal_attribution() -> CausalAttributor:
    """获取因果归因分析器实例"""
    global _attribution_instance
    if _attribution_instance is None:
        _attribution_instance = CausalAttributor()
    return _attribution_instance
