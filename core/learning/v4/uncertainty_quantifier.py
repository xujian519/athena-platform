#!/usr/bin/env python3
from __future__ import annotations
"""
不确定性量化器 v4.0
Uncertainty Quantifier

基于维特根斯坦《逻辑哲学论》的不确定性量化:
- 诚实:明确表达知道什么、不知道什么
- 精确:量化不确定性程度
- 可追溯:每个不确定性都有来源

作者: 小诺·双鱼公主 v4.0
创建时间: 2026-01-28
版本: v4.0.0
"""

import asyncio
import json
import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class UncertaintyLevel(Enum):
    """不确定性等级"""
    CERTAIN = "certain"  # 确定 (0.9-1.0)
    LIKELY = "likely"  # 很可能 (0.7-0.9)
    POSSIBLE = "possible"  # 可能 (0.5-0.7)
    UNCERTAIN = "uncertain"  # 不确定 (0.3-0.5)
    UNLIKELY = "unlikely"  # 不太可能 (0.1-0.3)
    IMPOSSIBLE = "impossible"  # 不可能 (0.0-0.1)


@dataclass
class Confidence:
    """
    置信度数据结构

    基于维特根斯坦原则:
    - value: 置信度值 [0, 1]
    - level: 置信度等级
    - evidence: 支持证据列表
    - limitations: 局限性和不确定性来源
    """

    value: float = 0.5  # 置信度值 [0, 1]
    level: UncertaintyLevel = UncertaintyLevel.POSSIBLE
    evidence: list[str] = field(default_factory=list)
    limitations: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """初始化后验证和更新"""
        # 确保值在[0, 1]范围内
        self.value = max(0.0, min(1.0, self.value))

        # 根据值自动更新等级
        self._update_level()

    def _update_level(self):
        """根据置信度值更新等级"""
        if self.value >= 0.9:
            self.level = UncertaintyLevel.CERTAIN
        elif self.value >= 0.7:
            self.level = UncertaintyLevel.LIKELY
        elif self.value >= 0.5:
            self.level = UncertaintyLevel.POSSIBLE
        elif self.value >= 0.3:
            self.level = UncertaintyLevel.UNCERTAIN
        elif self.value >= 0.1:
            self.level = UncertaintyLevel.UNLIKELY
        else:
            self.level = UncertaintyLevel.IMPOSSIBLE

    def add_evidence(self, evidence: str):
        """添加支持证据"""
        if evidence and evidence not in self.evidence:
            self.evidence.append(evidence)

    def add_limitation(self, limitation: str):
        """添加局限性"""
        if limitation and limitation not in self.limitations:
            self.limitations.append(limitation)

    def adjust(self, delta: float, reason: str | None = None):
        """
        调整置信度

        Args:
            delta: 调整量 (正数增加，负数减少)
            reason: 调整原因
        """
        old_value = self.value
        self.value = max(0.0, min(1.0, self.value + delta))
        self._update_level()

        if reason:
            change = "增加" if delta > 0 else "减少"
            self.add_limitation(f"置信度{change}: {reason} (从{old_value:.2f}到{self.value:.2f})")


class UncertaintyQuantifier:
    """
    不确定性量化器 v4.0

    职责:
    1. 量化主张的不确定性
    2. 追踪证据来源
    3. 识别知识边界
    4. 诚实表达无知

    使用方法:
        quantifier = UncertaintyQuantifier()
        confidence = quantifier.quantify(
            claim="巴黎是法国首都",
            evidence=["地理教科书", "常识知识"],
            information_completeness=0.95
        )
    """

    def __init__(self):
        # 量化历史记录
        self.quantification_history = []

        # 证据权重配置
        self.evidence_weights = {
            "direct_observation": 1.0,  # 直接观察
            "expert_consensus": 0.9,  # 专家共识
            "peer_reviewed": 0.85,  # 同行评审
            "reliable_source": 0.7,  # 可靠来源
            "corroborated": 0.6,  # 相互印证
            "single_source": 0.4,  # 单一来源
            "hearsay": 0.2,  # 传闻
            "speculation": 0.1,  # 推测
        }

        # 信息完整性对置信度的影响
        self.completeness_factors = {
            "complete": 1.0,  # 完整信息
            "substantial": 0.8,  # 主要信息
            "partial": 0.5,  # 部分信息
            "minimal": 0.3,  # 最少信息
            "unknown": 0.1,  # 未知
        }

        # 主题复杂度调整
        self.complexity_penalty = {
            "simple": 0.0,  # 简单主题
            "moderate": 0.1,  # 中等复杂
            "complex": 0.2,  # 复杂主题
            "very_complex": 0.3,  # 非常复杂
        }

        logger.info("✅ 不确定性量化器v4.0初始化完成")

    def quantify(
        self,
        claim: str,
        evidence: list[str],
        information_completeness: float = 0.5,
        evidence_quality: str = "reliable_source",
        topic_complexity: str = "moderate",
        context: dict[str, Any] | None = None,
    ) -> Confidence:
        """
        量化不确定性

        Args:
            claim: 主张或断言
            evidence: 支持证据列表
            information_completeness: 信息完整性 [0, 1]
            evidence_quality: 证据质量类型
            topic_complexity: 主题复杂度
            context: 额外上下文信息

        Returns:
            Confidence: 置信度对象
        """
        try:
            # 1. 评估证据权重
            evidence_score = self._assess_evidence(evidence, evidence_quality)

            # 2. 应用信息完整性调整
            completeness_factor = self._get_completeness_factor(information_completeness)

            # 3. 应用复杂度惩罚
            complexity_penalty = self.complexity_penalty.get(topic_complexity, 0.1)

            # 4. 计算基础置信度
            base_confidence = evidence_score * completeness_factor

            # 5. 应用复杂度调整
            final_confidence = max(0.0, min(1.0, base_confidence - complexity_penalty))

            # 6. 创建置信度对象
            confidence = Confidence(value=final_confidence)
            confidence.evidence = evidence.copy()

            # 7. 添加局限性说明
            self._add_limitations(confidence, information_completeness, evidence_quality, topic_complexity)

            # 8. 记录量化历史
            self._record_quantification(claim, confidence, context)

            return confidence

        except Exception as e:
            logger.error(f"❌ 不确定性量化失败: {e}")
            # 返回低置信度
            return Confidence(value=0.3, limitations=[f"量化过程出错: {e}"])

    def _assess_evidence(self, evidence: list[str], evidence_quality: str) -> float:
        """
        评估证据权重

        Args:
            evidence: 证据列表
            evidence_quality: 证据质量类型

        Returns:
            float: 证据权重分数 [0, 1]
        """
        if not evidence:
            return 0.1  # 无证据时极低置信度

        # 基础权重
        base_weight = self.evidence_weights.get(evidence_quality, 0.5)

        # 证据数量加成 (边际递减)
        evidence_count_bonus = min(len(evidence) * 0.1, 0.3)

        # 证据多样性加成
        diversity_bonus = self._assess_evidence_diversity(evidence) * 0.1

        # 计算最终证据分数
        evidence_score = base_weight + evidence_count_bonus + diversity_bonus

        return min(1.0, evidence_score)

    def _assess_evidence_diversity(self, evidence: list[str]) -> float:
        """
        评估证据多样性

        Args:
            evidence: 证据列表

        Returns:
            float: 多样性分数 [0, 1]
        """
        if not evidence:
            return 0.0

        # 简化实现: 检查证据来源类型的多样性
        # 实际应用中可以使用更复杂的文本相似度分析

        # 关键词集合
        source_keywords = {
            "academic": ["论文", "研究", "期刊", "学术", "university", "research"],
            "official": ["官方", "政府", "权威", "规范", "标准", "official"],
            "expert": ["专家", "学者", "教授", "professional"],
            "media": ["新闻", "报道", "媒体", "article"],
            "personal": ["个人", "经验", "观察", "personal"],
        }

        detected_types = set()
        for ev in evidence:
            ev_lower = ev.lower()
            for source_type, keywords in source_keywords.items():
                if any(keyword in ev_lower for keyword in keywords):
                    detected_types.add(source_type)

        # 多样性比例
        diversity_ratio = len(detected_types) / len(source_keywords)

        return diversity_ratio

    def _get_completeness_factor(self, completeness: float) -> float:
        """
        获取信息完整性因子

        Args:
            completeness: 完整性分数 [0, 1]

        Returns:
            float: 完整性因子 [0, 1]
        """
        if completeness >= 0.9:
            return self.completeness_factors["complete"]
        elif completeness >= 0.7:
            return self.completeness_factors["substantial"]
        elif completeness >= 0.4:
            return self.completeness_factors["partial"]
        elif completeness >= 0.2:
            return self.completeness_factors["minimal"]
        else:
            return self.completeness_factors["unknown"]

    def _add_limitations(
        self,
        confidence: Confidence,
        information_completeness: float,
        evidence_quality: str,
        topic_complexity: str,
    ):
        """添加局限性说明"""
        # 信息完整性局限
        if information_completeness < 0.7:
            confidence.add_limitation(f"信息不完整 (完整性: {information_completeness:.0%})")

        # 证据质量局限
        if evidence_quality in ["single_source", "hearsay", "speculation"]:
            confidence.add_limitation(f"证据质量有限: {evidence_quality}")

        # 复杂度局限
        if topic_complexity in ["complex", "very_complex"]:
            confidence.add_limitation(f"主题复杂度高: {topic_complexity}")

    def _record_quantification(
        self, claim: str, confidence: Confidence, context: dict[str, Any] | None
    ):
        """记录量化历史"""
        record = {
            "timestamp": datetime.now().isoformat(),
            "claim": claim[:100],  # 截断过长主张
            "confidence_value": confidence.value,
            "confidence_level": confidence.level.value,
            "evidence_count": len(confidence.evidence),
            "limitations_count": len(confidence.limitations),
            "context": context,
        }

        self.quantification_history.append(record)

        # 限制历史记录大小
        if len(self.quantification_history) > 1000:
            self.quantification_history = self.quantification_history[-1000:]

    def get_quantification_statistics(self) -> dict[str, Any]:
        """获取量化统计信息"""
        if not self.quantification_history:
            return {"total_quantifications": 0}

        # 计算平均置信度
        avg_confidence = sum(r["confidence_value"] for r in self.quantification_history) / len(
            self.quantification_history
        )

        # 置信度分布
        level_distribution = {}
        for record in self.quantification_history:
            level = record["confidence_level"]
            level_distribution[level] = level_distribution.get(level, 0) + 1

        return {
            "total_quantifications": len(self.quantification_history),
            "average_confidence": avg_confidence,
            "level_distribution": level_distribution,
            "recent_quantifications": len([r for r in self.quantification_history if self._is_recent(r)]),
        }

    def _is_recent(self, record: dict[str, Any]) -> bool:
        """检查记录是否最近 (24小时内)"""
        try:
            timestamp = datetime.fromisoformat(record["timestamp"])
            return (datetime.now() - timestamp).total_seconds() < 86400
        except (ValueError, KeyError):
            return False

    def export_history(self, file_path: str):
        """导出量化历史"""
        try:
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(self.quantification_history, f, indent=2, ensure_ascii=False)
            logger.info(f"✅ 量化历史已导出: {file_path}")
        except Exception as e:
            logger.error(f"❌ 导出失败: {e}")

    def create_joint_confidence(
        self, confidences: list[Confidence], weights: list[float] | None = None
    ) -> Confidence:
        """
        创建联合置信度 (多个置信度的组合)

        Args:
            confidences: 置信度列表
            weights: 权重列表 (可选)

        Returns:
            Confidence: 联合置信度
        """
        if not confidences:
            return Confidence(value=0.0, limitations=["无置信度输入"])

        n = len(confidences)

        # 如果没有提供权重,使用均等权重
        if weights is None:
            weights = [1.0 / n] * n
        else:
            # 归一化权重
            total_weight = sum(weights)
            weights = [w / total_weight for w in weights]

        # 计算加权平均置信度
        weighted_value = sum(c.value * w for c, w in zip(confidences, weights, strict=False))

        # 创建联合置信度
        joint_confidence = Confidence(value=weighted_value)

        # 合并证据
        all_evidence = set()
        for conf in confidences:
            all_evidence.update(conf.evidence)
        joint_confidence.evidence = list(all_evidence)

        # 合并局限性
        all_limitations = set()
        for conf in confidences:
            all_limitations.update(conf.limitations)
        joint_confidence.limitations = list(all_limitations)

        # 添加元数据
        joint_confidence.metadata = {
            "joint_confidence": True,
            "source_count": n,
            "individual_values": [c.value for c in confidences],
        }

        return joint_confidence


# 全局单例
_uncertainty_quantifier: UncertaintyQuantifier | None = None


def get_uncertainty_quantifier() -> UncertaintyQuantifier:
    """获取不确定性量化器单例"""
    global _uncertainty_quantifier
    if _uncertainty_quantifier is None:
        _uncertainty_quantifier = UncertaintyQuantifier()
    return _uncertainty_quantifier


# 使用示例
async def example_usage():
    """使用示例"""
    quantifier = UncertaintyQuantifier()

    # 示例1: 高置信度
    confidence1 = quantifier.quantify(
        claim="Python是一种编程语言",
        evidence=["官方文档", "广泛使用", "教育机构教授"],
        information_completeness=0.95,
        evidence_quality="expert_consensus",
        topic_complexity="simple",
    )
    print(f"示例1 - 置信度: {confidence1.value:.1%} ({confidence1.level.value})")

    # 示例2: 中等置信度
    confidence2 = quantifier.quantify(
        claim="AI将在未来10年内取代所有程序员",
        evidence=["一些专家预测"],
        information_completeness=0.4,
        evidence_quality="speculation",
        topic_complexity="complex",
    )
    print(f"示例2 - 置信度: {confidence2.value:.1%} ({confidence2.level.value})")

    # 示例3: 低置信度
    confidence3 = quantifier.quantify(
        claim="外星人存在",
        evidence=["一些不明飞行物目击报告"],
        information_completeness=0.1,
        evidence_quality="hearsay",
        topic_complexity="very_complex",
    )
    print(f"示例3 - 置信度: {confidence3.value:.1%} ({confidence3.level.value})")

    # 获取统计信息
    stats = quantifier.get_quantification_statistics()
    print(f"\n统计信息: {json.dumps(stats, indent=2, ensure_ascii=False)}")


class UncertaintyQuantifierV4(UncertaintyQuantifier):
    """不确定性量化器 v4.0 版本别名，用于向后兼容"""

    pass


def get_uncertainty_quantifier_v4() -> UncertaintyQuantifierV4:
    """获取不确定性量化器v4单例"""
    global _uncertainty_quantifier
    if _uncertainty_quantifier is None:
        _uncertainty_quantifier = UncertaintyQuantifierV4()
    return _uncertainty_quantifier


__all__ = [
    "UncertaintyLevel",
    "Confidence",
    "UncertaintyQuantifier",
    "UncertaintyQuantifierV4",
    "get_uncertainty_quantifier",
    "get_uncertainty_quantifier_v4",
]


if __name__ == "__main__":
    asyncio.run(example_usage())
