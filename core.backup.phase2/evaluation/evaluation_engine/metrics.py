#!/usr/bin/env python3
from __future__ import annotations
"""
评估引擎 - 指标计算器
Evaluation Engine - Metrics Calculator

作者: Athena平台团队
创建时间: 2025-12-11
重构时间: 2026-01-26
版本: 2.0.0

提供评估指标的计算功能。
"""

import logging
import statistics
from typing import Any

from .types import EvaluationLevel

logger = logging.getLogger(__name__)


class MetricsCalculator:
    """指标计算器"""

    @staticmethod
    def calculate_weighted_score(criteria_results: dict[str, dict[str, Any]]) -> float:
        """计算加权得分"""
        total_weight = 0
        weighted_score = 0

        for _criterion_id, result in criteria_results.items():
            weight = result.get("weight", 1.0)
            score = result.get("score", 0.0)

            weighted_score += score * weight
            total_weight += weight

        return weighted_score / total_weight if total_weight > 0 else 0.0

    @staticmethod
    def determine_level(score: float) -> EvaluationLevel:
        """确定评估等级"""
        if score >= 90:
            return EvaluationLevel.EXCELLENT
        elif score >= 80:
            return EvaluationLevel.GOOD
        elif score >= 70:
            return EvaluationLevel.SATISFACTORY
        elif score >= 60:
            return EvaluationLevel.NEEDS_IMPROVEMENT
        else:
            return EvaluationLevel.POOR

    @staticmethod
    def calculate_confidence(criteria_results: dict[str, dict[str, Any]]) -> float:
        """计算置信度"""
        if not criteria_results:
            return 0.0

        evidence_counts = []
        for result in criteria_results.values():
            evidence_count = len(result.get("evidence", []))
            evidence_counts.append(evidence_count)

        if not evidence_counts:
            return 0.0

        # 基于证据数量计算置信度
        avg_evidence = statistics.mean(evidence_counts)
        confidence = min(1.0, avg_evidence / 3)  # 平均3个证据为满分置信度

        return confidence

    @staticmethod
    def detect_trends(scores: list[float], window_size: int = 5) -> dict[str, Any]:
        """检测趋势"""
        if len(scores) < window_size:
            return {"trend": "insufficient_data", "slope": 0.0}

        recent_scores = scores[-window_size:]
        older_scores = (
            scores[-(window_size * 2) : -window_size]
            if len(scores) >= window_size * 2
            else scores[:-window_size]
        )

        if not older_scores:
            return {"trend": "insufficient_data", "slope": 0.0}

        recent_avg = statistics.mean(recent_scores)
        older_avg = statistics.mean(older_scores)

        # 计算趋势斜率
        slope = (recent_avg - older_avg) / window_size

        # 确定趋势方向
        if slope > 2.0:
            trend = "improving_rapidly"
        elif slope > 0.5:
            trend = "improving"
        elif slope > -0.5:
            trend = "stable"
        elif slope > -2.0:
            trend = "declining"
        else:
            trend = "declining_rapidly"

        return {"trend": trend, "slope": slope, "recent_avg": recent_avg, "older_avg": older_avg}


# =============================================================================
# === 别名和兼容性 ===
# =============================================================================

# 为保持兼容性，提供 EvaluationMetrics 作为别名
EvaluationMetrics = MetricsCalculator


__all__ = [
    "MetricsCalculator",
    "EvaluationMetrics",  # 别名
]
