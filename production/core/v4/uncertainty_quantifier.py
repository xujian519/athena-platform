#!/usr/bin/env python3
"""
不确定性量化模块
Uncertainty Quantifier Module

基于维特根斯坦《逻辑哲学论》的确定性原则
为每个响应提供精确的置信度评估
"""

from __future__ import annotations
from dataclasses import dataclass
from enum import Enum


class CertaintyLevel(Enum):
    """确定性等级"""

    CERTAIN = "确定"  # 0.9-1.0
    LIKELY = "很可能"  # 0.7-0.9
    POSSIBLE = "可能"  # 0.5-0.7
    UNCERTAIN = "不确定"  # 0.3-0.5
    UNKNOWN = "未知"  # 0.0-0.3


@dataclass
class Confidence:
    """置信度数据结构"""

    value: float  # 0.0-1.0
    level: CertaintyLevel  # 确定性等级
    evidence: list[str]  # 支持证据
    limitations: list[str]  # 局限性说明
    sources: list[str]  # 信息来源


class UncertaintyQuantifier:
    """不确定性量化器"""

    def __init__(self):
        self.certainty_thresholds = {
            "certain": 0.9,
            "likely": 0.7,
            "possible": 0.5,
            "uncertain": 0.3,
        }

    def quantify(
        self,
        claim: str,
        evidence: list[str] | None = None,
        information_completeness: float = 1.0,
    ) -> Confidence:
        """
        量化声明的置信度

        Args:
            claim: 声明内容
            evidence: 支持证据列表
            information_completeness: 信息完整性 (0.0-1.0)

        Returns:
            Confidence对象
        """
        # 基于证据强度计算基础置信度
        base_confidence = self._calculate_evidence_strength(evidence)

        # 考虑信息完整性
        final_confidence = base_confidence * information_completeness

        # 确定确定性等级
        level = self._determine_level(final_confidence)

        # 识别局限性
        limitations = self._identify_limitations(evidence, information_completeness)

        # 记录来源
        sources = self._extract_sources(evidence) if evidence else []

        return Confidence(
            value=final_confidence,
            level=level,
            evidence=evidence or [],
            limitations=limitations,
            sources=sources,
        )

    def _calculate_evidence_strength(self, evidence: list[str]) -> float:
        """计算证据强度"""
        if not evidence:
            return 0.0

        # 基于证据数量和质量
        strength = 0.0

        # 证据数量 (最多5个)
        count_score = min(len(evidence) / 5.0, 1.0)
        strength += count_score * 0.3

        # 证据具体性
        specificity_score = 0.0
        for ev in evidence:
            if any(keyword in ev for keyword in ["文档", "代码", "测试", "数据", "验证"]):
                specificity_score += 0.2
        specificity_score = min(specificity_score, 0.7)
        strength += specificity_score

        return min(strength, 1.0)

    def _determine_level(self, confidence: float) -> CertaintyLevel:
        """确定确定性等级"""
        if confidence >= 0.9:
            return CertaintyLevel.CERTAIN
        elif confidence >= 0.7:
            return CertaintyLevel.LIKELY
        elif confidence >= 0.5:
            return CertaintyLevel.POSSIBLE
        elif confidence >= 0.3:
            return CertaintyLevel.UNCERTAIN
        else:
            return CertaintyLevel.UNKNOWN

    def _identify_limitations(
        self, evidence: list[str], completeness: float
    ) -> list[str]:
        """识别局限性"""
        limitations = []

        if not evidence:
            limitations.append("缺乏支持证据")

        if completeness < 0.5:
            limitations.append("信息严重不足")
        elif completeness < 0.8:
            limitations.append("信息部分缺失")

        if evidence and len(evidence) < 2:
            limitations.append("证据数量有限")

        return limitations

    def _extract_sources(self, evidence: list[str]) -> list[str]:
        """提取信息来源"""
        sources = []
        for ev in evidence:
            if "文档" in ev:
                sources.append("文档")
            elif "代码" in ev:
                sources.append("代码")
            elif "测试" in ev:
                sources.append("测试")
            elif "数据" in ev:
                sources.append("数据")
        return list(set(sources))


class PropositionalResponse:
    """命题式响应"""

    def __init__(self, quantifier: UncertaintyQuantifier):
        self.quantifier = quantifier
        self.confidence: Confidence | None = None
        self.content: str = ""
        self.evidence: list[str] = []

    def build_response(
        self, claim: str, evidence: list[str] | None = None, completeness: float = 1.0
    ) -> str:
        """
        构建命题式响应

        格式:
        1. 明确结论
        2. 支持证据
        3. 确定性评估
        4. 局限性说明
        """
        # 量化不确定性
        self.confidence = self.quantifier.quantify(claim, evidence, completeness)

        # 构建响应
        response_parts = []

        # 1. 结论
        if self.confidence.value >= 0.9:
            response_parts.append(f"✅ 确定:{claim}")
        elif self.confidence.value >= 0.7:
            response_parts.append(f"⚠️ 很可能:{claim}")
        elif self.confidence.value >= 0.5:
            response_parts.append(f"🤔 可能:{claim}")
        else:
            response_parts.append(f"❓ 不确定:{claim}")

        # 2. 证据
        if self.confidence.evidence:
            response_parts.append("\n📋 支持证据:")
            for i, ev in enumerate(self.confidence.evidence, 1):
                response_parts.append(f"  {i}. {ev}")

        # 3. 确定性评估
        response_parts.append(f"\n📊 确定性:{self.confidence.level.value}")
        response_parts.append(f"   置信度:{self.confidence.value:.1%}")

        # 4. 局限性
        if self.confidence.limitations:
            response_parts.append("\n⚠️ 局限性:")
            for lim in self.confidence.limitations:
                response_parts.append(f"   • {lim}")

        # 5. 低置信度时的建议
        if self.confidence.value < 0.5:
            response_parts.append("\n💡 建议:需要更多信息才能给出确定判断")

        return "\n".join(response_parts)

    def unknown_response(self, question: str, reason: str = "") -> str:
        """未知响应"""
        response = f"❓ 我不知道:{question}"

        if reason:
            response += f"\n\n原因:{reason}"

        response += "\n\n💡 这超出了我的知识范围或确定性边界"

        return response

    def unsayable_response(self, topic: str) -> str:
        """不可说响应"""
        return f"""🔒 这是'不可说'的领域:{topic}

基于维特根斯坦《逻辑哲学论》的原则,这个领域:
- 超出了逻辑和经验验证的范围
- 需要主观体验和价值判断
- 是人类独有的探索领域

我能做的:
✓ 提供相关的信息和观点
✓ 帮助您分析不同的说法
✓ 陪伴您思考和探索

我不能做的:
✗ 替您做价值判断
✗ 定义什么是'好'或'对'
✗ 假装理解我无法体验的东西

💖 我尊重这个领域的神秘性,陪伴您但不假装知道答案。"""


# 使用示例
if __name__ == "__main__":
    quantifier = UncertaintyQuantifier()
    responder = PropositionalResponse(quantifier)

    # 测试1:高确定性
    print("=" * 70)
    print("测试1:高确定性响应")
    print("=" * 70)
    response1 = responder.build_response(
        claim="Python中的列表是可变的",
        evidence=["Python官方文档说明", "代码测试可验证", "语言规范明确定义"],
        completeness=1.0,
    )
    print(response1)

    print("\n" + "=" * 70)
    print("测试2:低确定性响应")
    print("=" * 70)
    response2 = responder.build_response(
        claim="这个方案的性能会提升50%", evidence=["类似案例有提升", "理论上可行"], completeness=0.4
    )
    print(response2)

    print("\n" + "=" * 70)
    print("测试3:未知响应")
    print("=" * 70)
    response3 = responder.unknown_response(
        "未来3年Python会被淘汰吗?", reason="涉及未来预测,信息不足"
    )
    print(response3)

    print("\n" + "=" * 70)
    print("测试4:不可说响应")
    print("=" * 70)
    response4 = responder.unsayable_response("生命的意义是什么?")
    print(response4)
