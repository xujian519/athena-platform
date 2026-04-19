#!/usr/bin/env python3
from __future__ import annotations
"""
不确定性量化器 v4.0
Uncertainty Quantifier v4.0

基于维特根斯坦《逻辑哲学论》的不确定性量化原则:
- 诚实:承认不确定性
- 精确:量化不确定性程度
- 证据驱动:基于证据评估置信度

作者: 小诺·双鱼公主 v4.0
创建时间: 2025-12-25
版本: v4.0.0
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

from core.async_main import async_main

logger = logging.getLogger(__name__)


class CertaintyLevel(Enum):
    """确定性等级"""

    HIGH = "high"  # 高确定性
    MEDIUM = "medium"  # 中等确定性
    LOW = "low"  # 低确定性
    UNKNOWN = "unknown"  # 未知


@dataclass
class Confidence:
    """
    置信度数据结构

    属性:
        level: 确定性等级
        value: 置信度数值 (0.0 - 1.0)
        evidence: 支持证据列表
        reasoning: 推理过程说明
        timestamp: 生成时间
        high_threshold: 高置信度阈值(默认0.8)
        medium_threshold: 中置信度阈值(默认0.5)
        low_threshold: 低置信度阈值(默认0.2)
    """

    level: CertaintyLevel
    value: float
    evidence: list[str] = field(default_factory=list)
    reasoning: str = ""
    timestamp: datetime = field(default_factory=datetime.now)
    limitations: list[str] = field(default_factory=list)
    high_threshold: float = 0.8
    medium_threshold: float = 0.5
    low_threshold: float = 0.2

    def __post_init__(self):
        """验证并标准化置信度值"""
        if not 0.0 <= self.value <= 1.0:
            logger.warning(f"置信度值 {self.value} 超出范围,将被裁剪到[0, 1]")
            self.value = max(0.0, min(1.0, self.value))
        if self.value >= self.high_threshold:
            self.level = CertaintyLevel.HIGH
        elif self.value >= self.medium_threshold:
            self.level = CertaintyLevel.MEDIUM
        elif self.value > self.low_threshold:
            self.level = CertaintyLevel.LOW
        else:
            self.level = CertaintyLevel.UNKNOWN

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "level": self.level.value,
            "value": self.value,
            "evidence": self.evidence,
            "reasoning": self.reasoning,
            "timestamp": self.timestamp.isoformat(),
            "limitations": self.limitations,
        }


class PropositionalResponse:
    """
    命题响应构建器

    根据维特根斯坦的命题逻辑,构建带有不确定性标注的响应
    """

    def __init__(self, uncertainty_quantifier):
        self.quantifier = uncertainty_quantifier

    def build_response(
        self, claim: str, evidence: list[str], information_completeness: float = 0.8
    ) -> dict[str, Any]:
        """
        构建命题响应

        Args:
            claim: 主张/命题
            evidence: 支持证据
            information_completeness: 信息完整度 (0.0 - 1.0)

        Returns:
            包含主张、置信度和元数据的响应
        """
        confidence = self.quantifier.quantify(
            claim=claim, evidence=evidence, information_completeness=information_completeness
        )

        return {
            "claim": claim,
            "confidence": confidence.to_dict(),
            "can_say": confidence.level != CertaintyLevel.UNKNOWN,
            "should_say": confidence.value >= 0.5,
            "recommendation": self._generate_recommendation(confidence),
        }

    def _generate_recommendation(self, confidence: Confidence) -> str:
        """生成建议"""
        if confidence.level == CertaintyLevel.HIGH:
            return "可以确信地表达"
        elif confidence.level == CertaintyLevel.MEDIUM:
            return "表达时保留一定谨慎"
        elif confidence.level == CertaintyLevel.LOW:
            return "明确表达不确定性"
        else:
            return "维特根斯坦:对不可说的保持沉默"


class UncertaintyQuantifier:
    """
    不确定性量化器

    核心功能:
    1. 量化命题的置信度
    2. 基于证据评估确定性
    3. 识别评估局限性
    4. 提供不确定性推理

    使用方法:
        quantifier = UncertaintyQuantifier()
        confidence = quantifier.quantify(
            claim="Python列表是有序的",
            evidence=["Python文档说明列表保持插入顺序"],
            information_completeness=0.9
        )
        print(confidence.level)  # CertaintyLevel.HIGH
    """

    def __init__(self, config: dict[str, Any] | None = None):
        self.config = config or {}

        # 置信度计算权重
        # 调整权重以更好地反映证据质量、信息完整度和一致性的重要性
        self.evidence_weight = self.config.get("evidence_weight", 0.7)  # 显著提高证据权重
        self.completeness_weight = self.config.get("completeness_weight", 0.2)
        self.consistency_weight = self.config.get("consistency_weight", 0.1)  # 显著降低一致性权重

        # 置信度阈值
        self.high_confidence_threshold = self.config.get(
            "high_confidence_threshold", 0.7
        )  # 降低高置信度阈值到0.7
        self.medium_confidence_threshold = self.config.get("medium_confidence_threshold", 0.5)
        self.low_confidence_threshold = self.config.get("low_confidence_threshold", 0.2)

        logger.info("✅ 不确定性量化器已初始化")

    def quantify(
        self,
        claim: str,
        evidence: list[str],
        information_completeness: float = 0.8,
        context: dict[str, Any] | None = None,
    ) -> Confidence:
        """
        量化命题的不确定性

        Args:
            claim: 待评估的命题/主张
            evidence: 支持证据列表
            information_completeness: 信息完整度 (0.0 - 1.0)
            context: 额外上下文信息

        Returns:
            Confidence 对象,包含置信度等级和数值
        """
        try:
            # 特殊情况:无证据时直接返回0.0置信度
            if not evidence:
                return Confidence(
                    level=CertaintyLevel.UNKNOWN,
                    value=0.0,
                    evidence=evidence,
                    reasoning="无支持证据,无法评估置信度",
                    limitations=["缺乏支持证据"],
                    high_threshold=self.high_confidence_threshold,
                    medium_threshold=self.medium_confidence_threshold,
                    low_threshold=self.low_confidence_threshold,
                )

            # 1. 评估证据质量
            evidence_score = self._evaluate_evidence_quality(evidence)

            # 2. 评估信息完整度
            completeness_score = self._evaluate_completeness(information_completeness, claim)

            # 3. 评估证据一致性
            consistency_score = self._evaluate_consistency(evidence, claim)

            # 4. 计算综合置信度
            confidence_value = self._calculate_confidence(
                evidence_score, completeness_score, consistency_score
            )

            # 5. 生成推理说明
            reasoning = self._generate_reasoning(
                evidence_score, completeness_score, consistency_score, confidence_value
            )

            # 6. 识别局限性
            limitations = self._identify_limitations(evidence, information_completeness, claim)

            # 7. 创建置信度对象
            confidence = Confidence(
                level=self._determine_level(confidence_value),
                value=confidence_value,
                evidence=evidence,
                reasoning=reasoning,
                limitations=limitations,
                high_threshold=self.high_confidence_threshold,
                medium_threshold=self.medium_confidence_threshold,
                low_threshold=self.low_confidence_threshold,
            )

            logger.debug(f"量化完成: {claim[:50]}... -> 置信度 {confidence_value:.2f}")

            return confidence

        except Exception as e:
            logger.error(f"不确定性量化失败: {e}")
            # 返回低置信度结果
            return Confidence(
                level=CertaintyLevel.UNKNOWN,
                value=0.0,
                evidence=evidence,
                reasoning=f"量化失败: {e!s}",
                limitations=["量化过程发生错误"],
                high_threshold=self.high_confidence_threshold,
                medium_threshold=self.medium_confidence_threshold,
                low_threshold=self.low_confidence_threshold,
            )

    def _evaluate_evidence_quality(self, evidence: list[str]) -> float:
        """
        评估证据质量

        考虑因素:
        - 证据数量
        - 证据具体性
        - 证据相关性
        """
        if not evidence:
            return 0.0

        # 基于数量评分 (最多1.0)
        quantity_score = min(1.0, len(evidence) / 3.0)

        # 基于具体性评分
        avg_length = sum(len(e) for e in evidence) / len(evidence) if evidence else 0
        specificity_score = min(1.0, avg_length / 50.0)

        # 综合评分
        return quantity_score * 0.6 + specificity_score * 0.4

    def _evaluate_completeness(self, information_completeness: float, claim: str) -> float:
        """
        评估信息完整度

        考虑因素:
        - 提供的完整度参数
        - 主题复杂性
        - 信息覆盖范围
        """
        # 基于参数
        base_score = max(0.0, min(1.0, information_completeness))

        # 检查主题复杂性
        claim_length = len(claim)
        if claim_length < 20:
            # 简单命题,容易评估
            complexity_penalty = 0.0
        elif claim_length < 100:
            complexity_penalty = 0.1
        else:
            complexity_penalty = 0.2

        return max(0.0, base_score - complexity_penalty)

    def _evaluate_consistency(self, evidence: list[str], claim: str) -> float:
        """
        评估证据一致性

        考虑因素:
        - 证据之间的相似性
        - 证据与主张的匹配度
        - 使用子串匹配而非分词,更好地支持中文
        """
        if not evidence:
            return 0.0

        # 使用子串匹配来评估一致性(更适合中文)
        consistency_scores = []

        for ev in evidence:
            # 将evidence和claim转为小写进行比较
            ev_lower = ev.lower()
            claim_lower = claim.lower()

            # 计算匹配的字符数(包含在evidence中的claim字符)
            matched_chars = sum(1 for c in claim_lower if c in ev_lower)

            # 一致性得分 = 匹配字符数 / claim长度
            # 至少给予0.5的基础分(因为evidence是相关的)
            char_match_ratio = matched_chars / len(claim_lower) if len(claim_lower) > 0 else 0.0

            # 结合子串匹配得分
            # 检查claim的任何连续片段是否在evidence中
            max_substring_match = 0.0
            for i in range(len(claim_lower)):
                for j in range(i + 1, min(i + 11, len(claim_lower) + 1)):  # 检查最多10字符的子串
                    substring = claim_lower[i:j]
                    if substring in ev_lower:
                        max_substring_match = max(
                            max_substring_match, len(substring) / len(claim_lower)
                        )

            # 综合得分:字符匹配和子串匹配的结合,至少0.3
            consistency_score = max(0.3, char_match_ratio * 0.5 + max_substring_match * 0.5)
            consistency_scores.append(consistency_score)

        if not consistency_scores:
            return 0.0

        return sum(consistency_scores) / len(consistency_scores)

    def _calculate_confidence(
        self, evidence_score: float, completeness_score: float, consistency_score: float
    ) -> float:
        """计算综合置信度"""
        confidence = (
            evidence_score * self.evidence_weight
            + completeness_score * self.completeness_weight
            + consistency_score * self.consistency_weight
        )
        return max(0.0, min(1.0, confidence))

    def _determine_level(self, confidence_value: float) -> CertaintyLevel:
        """确定置信度等级"""
        if confidence_value >= self.high_confidence_threshold:
            return CertaintyLevel.HIGH
        elif confidence_value >= self.medium_confidence_threshold:
            return CertaintyLevel.MEDIUM
        elif confidence_value >= self.low_confidence_threshold:
            return CertaintyLevel.LOW
        else:
            return CertaintyLevel.UNKNOWN

    def _generate_reasoning(
        self,
        evidence_score: float,
        completeness_score: float,
        consistency_score: float,
        confidence_value: float,
    ) -> str:
        """生成推理说明"""
        reasoning_parts = []

        reasoning_parts.append(f"证据质量评分: {evidence_score:.2f}")
        reasoning_parts.append(f"信息完整度: {completeness_score:.2f}")
        reasoning_parts.append(f"一致性评分: {consistency_score:.2f}")
        reasoning_parts.append(f"综合置信度: {confidence_value:.2f}")

        # 添加解释
        if confidence_value >= 0.8:
            reasoning_parts.append("评估基于充分的证据和完整的信息")
        elif confidence_value >= 0.5:
            reasoning_parts.append("评估基于部分证据,存在一定不确定性")
        else:
            reasoning_parts.append("评估缺乏充分证据支持,高度不确定")

        return " | ".join(reasoning_parts)

    def _identify_limitations(
        self, evidence: list[str], information_completeness: float, claim: str
    ) -> list[str]:
        """识别评估局限性"""
        limitations = []

        if not evidence:
            limitations.append("缺乏支持证据")

        if len(evidence) < 2:
            limitations.append("证据数量不足")

        if information_completeness < 0.7:
            limitations.append("信息不完整")

        if len(claim) > 200:
            limitations.append("命题过于复杂,难以精确评估")

        if information_completeness < 0.5:
            limitations.append("信息严重不足,建议收集更多数据")

        return limitations if limitations else ["无明显局限性"]

    def batch_quantify(
        self, claims: list[tuple[str, list[str]]], information_completeness: float = 0.8
    ) -> list[Confidence]:
        """
        批量量化多个命题

        Args:
            claims: (命题, 证据) 元组列表
            information_completeness: 信息完整度

        Returns:
            置信度列表
        """
        results = []
        for claim, evidence in claims:
            confidence = self.quantify(
                claim=claim, evidence=evidence, information_completeness=information_completeness
            )
            results.append(confidence)

        return results

    def compare_confidence(
        self, confidence1: Confidence, confidence2: Confidence
    ) -> dict[str, Any]:
        """
        比较两个置信度

        Returns:
            比较结果,包含哪个更高以及差异程度
        """
        diff = confidence1.value - confidence2.value

        if abs(diff) < 0.1:
            comparison = "similar"
        elif diff > 0:
            comparison = "higher"
        else:
            comparison = "lower"

        return {"comparison": comparison, "difference": abs(diff), "significant": abs(diff) >= 0.2}


# 便捷函数
def quantify_uncertainty(
    claim: str, evidence: list[str], information_completeness: float = 0.8
) -> Confidence:
    """
    快捷不确定性量化函数

    Args:
        claim: 主张/命题
        evidence: 支持证据
        information_completeness: 信息完整度

    Returns:
        Confidence 对象
    """
    quantifier = UncertaintyQuantifier()
    return quantifier.quantify(
        claim=claim, evidence=evidence, information_completeness=information_completeness
    )


# 使用示例
@async_main
async def main():
    """主函数(用于测试)"""
    print("=" * 80)
    print("🧠 测试不确定性量化器 v4.0")
    print("=" * 80)
    print()

    quantifier = UncertaintyQuantifier()

    # 示例1:高置信度命题
    print("测试1: 高置信度命题")
    confidence1 = quantifier.quantify(
        claim="Python列表是有序的数据结构",
        evidence=[
            "Python官方文档明确指出列表保持插入顺序",
            "Python 3.7+版本中,列表顺序已成为语言规范的一部分",
            "实际测试证明列表元素按照插入顺序存储和访问",
        ],
        information_completeness=0.95,
    )
    print(f"命题: {confidence1.level.value} ({confidence1.value:.2%})")
    print(f"推理: {confidence1.reasoning}")
    print()

    # 示例2:中等置信度命题
    print("测试2: 中等置信度命题")
    confidence2 = quantifier.quantify(
        claim="机器学习模型在NLP任务中表现良好",
        evidence=["多个基准测试显示模型性能提升", "实际应用中效果较好"],
        information_completeness=0.7,
    )
    print(f"命题: {confidence2.level.value} ({confidence2.value:.2%})")
    print(f"推理: {confidence2.reasoning}")
    print()

    # 示例3:低置信度命题
    print("测试3: 低置信度命题")
    confidence3 = quantifier.quantify(
        claim="未来五年内AI将完全取代程序员",
        evidence=["AI自动化能力在提升"],
        information_completeness=0.3,
    )
    print(f"命题: {confidence3.level.value} ({confidence3.value:.2%})")
    print(f"推理: {confidence3.reasoning}")
    print(f"局限性: {confidence3.limitations}")
    print()

    # 示例4:比较置信度
    print("测试4: 比较置信度")
    comparison = quantifier.compare_confidence(confidence1, confidence3)
    print(f"比较结果: {comparison}")
    print()

    print("=" * 80)
    print("✅ 测试完成")
    print("=" * 80)


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
