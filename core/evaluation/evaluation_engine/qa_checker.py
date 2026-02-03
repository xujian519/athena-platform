#!/usr/bin/env python3
"""
评估引擎 - 质量保证检查器
Evaluation Engine - Quality Assurance Checker

作者: Athena平台团队
创建时间: 2025-12-11
重构时间: 2026-01-26
版本: 2.0.0

提供评估结果的质量保证检查功能。
"""

import logging
import statistics
from dataclasses import dataclass
from typing import Any

from .metrics import MetricsCalculator
from .types import EvaluationResult

logger = logging.getLogger(__name__)


class QualityAssuranceChecker:
    """质量保证检查器"""

    def __init__(self):
        self.check_rules = {}
        self._initialize_default_rules()

    def _initialize_default_rules(self) -> Any:
        """初始化默认检查规则"""
        self.check_rules = {
            "completeness": {
                "description": "检查评估的完整性",
                "check_function": self._check_completeness,
            },
            "consistency": {
                "description": "检查评估的一致性",
                "check_function": self._check_consistency,
            },
            "bias_detection": {"description": "检测潜在偏见", "check_function": self._check_bias},
            "evidence_quality": {
                "description": "检查证据质量",
                "check_function": self._check_evidence_quality,
            },
        }

    async def perform_qa_check(self, evaluation_result: EvaluationResult) -> dict[str, Any]:
        """执行质量保证检查"""
        qa_results = {}

        for rule_name, rule_config in self.check_rules.items():
            try:
                check_result = await rule_config.get("check_function")(evaluation_result)
                qa_results[rule_name] = {
                    "passed": check_result.get("passed", False),
                    "score": check_result.get("score", 0.0),
                    "issues": check_result.get("issues", []),
                    "recommendations": check_result.get("recommendations", []),
                }
            except Exception as e:
                qa_results[rule_name] = {
                    "passed": False,
                    "score": 0.0,
                    "issues": [f"检查执行失败: {e!s}"],
                    "recommendations": [],
                }

        # 计算总体质量分数
        total_score = sum(result.get("score") for result in qa_results.values())
        overall_quality = total_score / len(qa_results)

        return {
            "overall_quality": overall_quality,
            "passed_all": all(result.get("passed") for result in qa_results.values()),
            "checks": qa_results,
        }

    async def _check_completeness(self, evaluation_result: EvaluationResult) -> dict[str, Any]:
        """检查完整性"""
        issues = []
        score = 100.0

        # 检查是否有评估标准
        if not evaluation_result.criteria_results:
            issues.append("缺少评估标准")
            score -= 50

        # 检查是否有强项和弱项
        if not evaluation_result.strengths:
            issues.append("缺少强项分析")
            score -= 10

        if not evaluation_result.weaknesses:
            issues.append("缺少弱项分析")
            score -= 10

        # 检查是否有改进建议
        if not evaluation_result.recommendations:
            issues.append("缺少改进建议")
            score -= 20

        # 检查评分是否在合理范围
        if not 0 <= evaluation_result.overall_score <= 100:
            issues.append("总体评分超出有效范围")
            score -= 30

        return {
            "passed": score >= 70,
            "score": max(0, score),
            "issues": issues,
            "recommendations": [
                "确保所有评估要素都被考虑",
                "提供详细的优缺点分析",
                "给出具体的改进建议",
            ],
        }

    async def _check_consistency(self, evaluation_result: EvaluationResult) -> dict[str, Any]:
        """检查一致性"""
        issues = []
        score = 100.0

        # 检查评分与等级的一致性
        expected_level = MetricsCalculator.determine_level(evaluation_result.overall_score)
        if evaluation_result.level != expected_level:
            issues.append(
                f"评分({evaluation_result.overall_score})与等级({evaluation_result.level.value})不一致"
            )
            score -= 30

        # 检查各标准评分的分布是否合理
        scores = [result.get("score", 0) for result in evaluation_result.criteria_results.values()]
        if scores:
            score_std = statistics.stdev(scores) if len(scores) > 1 else 0
            if score_std > 30:
                issues.append("各标准评分差异过大,可能存在评估不一致")
                score -= 20

        return {
            "passed": score >= 70,
            "score": max(0, score),
            "issues": issues,
            "recommendations": [
                "确保评分与评估等级一致",
                "保持各评估标准间的一致性",
                "使用统一的评估标准",
            ],
        }

    async def _check_bias(self, evaluation_result: EvaluationResult) -> dict[str, Any]:
        """检查潜在偏见"""
        issues = []
        score = 100.0

        # 检查极端评分
        extreme_scores = [
            s for s in evaluation_result.criteria_results.values() if s.get("score", 0) in (0, 100)
        ]
        if len(extreme_scores) > len(evaluation_result.criteria_results) * 0.3:
            issues.append("存在过多的极端评分,可能有偏见")
            score -= 25

        # 检查证据缺失
        criteria_without_evidence = [
            k for k, v in evaluation_result.criteria_results.items() if not v.get("evidence")
        ]
        if criteria_without_evidence:
            issues.append(f"{len(criteria_without_evidence)}个标准缺少证据支持")
            score -= 20

        return {
            "passed": score >= 70,
            "score": max(0, score),
            "issues": issues,
            "recommendations": [
                "避免极端评分,提供更平衡的评估",
                "为所有评估标准提供充分的证据",
                "考虑使用多角度评估",
            ],
        }

    async def _check_evidence_quality(self, evaluation_result: EvaluationResult) -> dict[str, Any]:
        """检查证据质量"""
        issues = []
        score = 100.0
        total_evidence = 0

        for criterion_id, result in evaluation_result.criteria_results.items():
            evidence = result.get("evidence", [])
            total_evidence += len(evidence)

            # 检查证据的描述性
            for ev in evidence:
                if not isinstance(ev, dict) or "description" not in ev:
                    issues.append(f"标准{criterion_id}存在格式不规范的证据")
                    score -= 5

        # 检查证据数量
        if total_evidence < len(evaluation_result.criteria_results) * 2:
            issues.append("证据数量不足")
            score -= 20

        return {
            "passed": score >= 70,
            "score": max(0, score),
            "issues": issues,
            "recommendations": [
                "为每个评估标准提供充分的高质量证据",
                "确保证据描述清晰、具体",
                "使用多样化的证据来源",
            ],
        }


# =============================================================================
# === 别名和兼容性 ===
# =============================================================================

# 为保持兼容性，提供 QAChecker 作为别名
QAChecker = QualityAssuranceChecker


# QACheckResult 类
@dataclass
class QACheckResult:
    """QA检查结果"""
    passed: bool
    score: float
    issues: list[str]
    recommendations: list[str]

    def to_dict(self) -> dict:
        return {
            "passed": self.passed,
            "score": self.score,
            "issues": self.issues,
            "recommendations": self.recommendations,
        }


__all__ = [
    "QualityAssuranceChecker",
    "QAChecker",  # 别名
    "QACheckResult",
]
