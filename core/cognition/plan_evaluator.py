#!/usr/bin/env python3
from __future__ import annotations
"""
方案评估器
Plan Evaluator

功能:
1. 评估方案执行效果
2. 对比预期与实际结果
3. 计算方案质量得分
4. 识别优化机会

Author: Athena Team
Version: 1.0.0
Date: 2026-02-24
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

from .feedback_collector import ExecutionFeedback, SatisfactionLevel
from .xiaonuo_planner_engine import ExecutionPlan, PlanConfidence

logger = logging.getLogger(__name__)


class EvaluationDimension(Enum):
    """评估维度"""
    TIME_ACCURACY = "time_accuracy"  # 时间准确性
    SUCCESS_RATE = "success_rate"  # 成功率
    USER_SATISFACTION = "user_satisfaction"  # 用户满意度
    RESOURCE_EFFICIENCY = "resource_efficiency"  # 资源效率
    RELIABILITY = "reliability"  # 可靠性


@dataclass
class DimensionScore:
    """维度得分"""
    dimension: EvaluationDimension
    score: float  # 0-1
    details: dict[str, Any] = field(default_factory=dict)


@dataclass
class PlanEvaluation:
    """方案评估结果"""
    evaluation_id: str
    plan_id: str
    overall_score: float  # 0-1
    dimension_scores: list[DimensionScore]
    grade: str  # A/B/C/D/F
    strengths: list[str]
    weaknesses: list[str]
    optimization_opportunities: list[str]
    evaluation_time: datetime = field(default_factory=datetime.now)
    metadata: dict[str, Any] = field(default_factory=dict)


class PlanEvaluator:
    """
    方案评估器

    核心功能:
    1. 多维度方案评估
    2. 预期vs实际对比
    3. 质量等级评定
    4. 优化机会识别
    """

    # 维度权重配置
    DIMENSION_WEIGHTS = {
        EvaluationDimension.TIME_ACCURACY: 0.2,
        EvaluationDimension.SUCCESS_RATE: 0.3,
        EvaluationDimension.USER_SATISFACTION: 0.25,
        EvaluationDimension.RESOURCE_EFFICIENCY: 0.15,
        EvaluationDimension.RELIABILITY: 0.1,
    }

    # 等级标准
    GRADE_THRESHOLDS = {
        "A": 0.9,  # 优秀
        "B": 0.8,  # 良好
        "C": 0.7,  # 中等
        "D": 0.6,  # 及格
        "F": 0.0,  # 不及格
    }

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.evaluation_history: list[PlanEvaluation] = []

        self.logger.info("📊 方案评估器初始化完成")

    def evaluate(
        self,
        plan: ExecutionPlan,
        feedback: list[ExecutionFeedback],
        actual_execution_time: Optional[int] = None,
        resource_usage: Optional[dict[str, Any]] = None,
    ) -> PlanEvaluation:
        """
        评估方案执行效果

        Args:
            plan: 执行的方案
            feedback: 反馈列表
            actual_execution_time: 实际执行时间
            resource_usage: 资源使用情况

        Returns:
            PlanEvaluation: 评估结果
        """
        self.logger.info(f"📊 评估方案: {plan.plan_id}")

        # 1. 评估各个维度
        dimension_scores = []

        # 时间准确性
        time_score = self._evaluate_time_accuracy(plan, feedback, actual_execution_time)
        dimension_scores.append(time_score)

        # 成功率
        success_score = self._evaluate_success_rate(plan, feedback)
        dimension_scores.append(success_score)

        # 用户满意度
        satisfaction_score = self._evaluate_user_satisfaction(plan, feedback)
        dimension_scores.append(satisfaction_score)

        # 资源效率
        resource_score = self._evaluate_resource_efficiency(plan, resource_usage)
        dimension_scores.append(resource_score)

        # 可靠性
        reliability_score = self._evaluate_reliability(plan, feedback)
        dimension_scores.append(reliability_score)

        # 2. 计算总体得分
        overall_score = self._calculate_overall_score(dimension_scores)

        # 3. 确定等级
        grade = self._determine_grade(overall_score)

        # 4. 分析优势和劣势
        strengths, weaknesses = self._analyze_strengths_weaknesses(dimension_scores)

        # 5. 识别优化机会
        opportunities = self._identify_opportunities(dimension_scores, plan)

        # 6. 创建评估结果
        evaluation = PlanEvaluation(
            evaluation_id=f"eval_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            plan_id=plan.plan_id,
            overall_score=overall_score,
            dimension_scores=dimension_scores,
            grade=grade,
            strengths=strengths,
            weaknesses=weaknesses,
            optimization_opportunities=opportunities,
            metadata={
                "plan_strategy": plan.mode.value,
                "steps_count": len(plan.steps),
                "feedback_count": len(feedback),
            },
        )

        # 7. 保存历史
        self.evaluation_history.append(evaluation)

        self.logger.info(f"   ✅ 评估完成: 等级={grade}, 得分={overall_score:.2f}")

        return evaluation

    def _evaluate_time_accuracy(
        self,
        plan: ExecutionPlan,
        feedback: list[ExecutionFeedback],
        actual_time: Optional[int]
    ) -> DimensionScore:
        """评估时间准确性"""
        # 优先使用实际执行时间
        if actual_time is not None:
            estimated = plan.estimated_time
            if estimated > 0:
                deviation = abs(actual_time - estimated) / estimated
                # 偏差越小越好
                score = max(0, 1 - deviation)
                details = {
                    "estimated_time": estimated,
                    "actual_time": actual_time,
                    "deviation": deviation,
                    "accuracy": "高" if deviation < 0.1 else "中" if deviation < 0.3 else "低",
                }
            else:
                score = 0.5
                details = {"message": "预估时间为0"}
        else:
            # 从反馈中获取
            time_feedback = [f for f in feedback if f.execution_time]
            if time_feedback:
                avg_actual = sum(f.execution_time for f in time_feedback) / len(time_feedback)
                estimated = plan.estimated_time
                if estimated > 0:
                    deviation = abs(avg_actual - estimated) / estimated
                    score = max(0, 1 - deviation)
                    details = {
                        "estimated_time": estimated,
                        "avg_actual_time": avg_actual,
                        "deviation": deviation,
                    }
                else:
                    score = 0.5
                    details = {"message": "预估时间为0"}
            else:
                score = 0.5  # 无数据，给中等分
                details = {"message": "无时间数据"}

        return DimensionScore(
            dimension=EvaluationDimension.TIME_ACCURACY,
            score=score,
            details=details,
        )

    def _evaluate_success_rate(
        self,
        plan: ExecutionPlan,
        feedback: list[ExecutionFeedback]
    ) -> DimensionScore:
        """评估成功率"""
        if not feedback:
            return DimensionScore(
                dimension=EvaluationDimension.SUCCESS_RATE,
                score=0.5,
                details={"message": "无反馈数据"},
            )

        # 计算平均成功率
        success_rates = [f.success_rate for f in feedback if f.success_rate is not None]

        if success_rates:
            avg_rate = sum(success_rates) / len(success_rates)
            score = avg_rate
            details = {
                "average_success_rate": avg_rate,
                "feedback_count": len(success_rates),
            }
        else:
            # 基于反馈类型
            success_count = sum(1 for f in feedback if f.feedback_type.value == "execution_success")
            total_count = len(feedback)
            score = success_count / total_count if total_count > 0 else 0.5
            details = {
                "success_count": success_count,
                "total_count": total_count,
            }

        return DimensionScore(
            dimension=EvaluationDimension.SUCCESS_RATE,
            score=score,
            details=details,
        )

    def _evaluate_user_satisfaction(
        self,
        plan: ExecutionPlan,
        feedback: list[ExecutionFeedback]
    ) -> DimensionScore:
        """评估用户满意度"""
        satisfaction_feedback = [f for f in feedback if f.satisfaction]

        if not satisfaction_feedback:
            return DimensionScore(
                dimension=EvaluationDimension.USER_SATISFACTION,
                score=0.5,
                details={"message": "无满意度数据"},
            )

        # 计算平均满意度得分
        score_map = {
            SatisfactionLevel.VERY_SATISFIED: 1.0,
            SatisfactionLevel.SATISFIED: 0.8,
            SatisfactionLevel.NEUTRAL: 0.6,
            SatisfactionLevel.DISSATISFIED: 0.4,
            SatisfactionLevel.VERY_DISSATISFIED: 0.2,
        }

        scores = [score_map.get(f.satisfaction, 0.5) for f in satisfaction_feedback]
        avg_score = sum(scores) / len(scores)

        details = {
            "average_satisfaction": avg_score,
            "feedback_count": len(satisfaction_feedback),
            "distribution": {
                "very_satisfied": sum(
                    1 for f in satisfaction_feedback
                    if f.satisfaction == SatisfactionLevel.VERY_SATISFIED
                ),
                "satisfied": sum(
                    1 for f in satisfaction_feedback
                    if f.satisfaction == SatisfactionLevel.SATISFIED
                ),
                "neutral": sum(
                    1 for f in satisfaction_feedback
                    if f.satisfaction == SatisfactionLevel.NEUTRAL
                ),
                "dissatisfied": sum(
                    1 for f in satisfaction_feedback
                    if f.satisfaction == SatisfactionLevel.DISSATISFIED
                ),
                "very_dissatisfied": sum(
                    1 for f in satisfaction_feedback
                    if f.satisfaction == SatisfactionLevel.VERY_DISSATISFIED
                ),
            },
        }

        return DimensionScore(
            dimension=EvaluationDimension.USER_SATISFACTION,
            score=avg_score,
            details=details,
        )

    def _evaluate_resource_efficiency(
        self,
        plan: ExecutionPlan,
        resource_usage: Optional[dict[str, Any]]
    ) -> DimensionScore:
        """评估资源效率"""
        # 基于方案配置估算
        steps_count = len(plan.steps)
        resource_count = len(plan.resource_requirements.services) + len(plan.resource_requirements.databases)

        # 简单评分：步骤和资源越少，效率越高
        efficiency_score = max(0, 1 - (steps_count / 20) - (resource_count / 10))

        details = {
            "steps_count": steps_count,
            "resource_count": resource_count,
            "estimated_memory_mb": plan.resource_requirements.memory_mb,
        }

        if resource_usage:
            # 如果有实际资源使用数据，更精确评估
            actual_memory = resource_usage.get("memory_mb", 0)
            estimated_memory = plan.resource_requirements.memory_mb
            if estimated_memory > 0:
                accuracy = 1 - abs(actual_memory - estimated_memory) / estimated_memory
                efficiency_score = (efficiency_score + accuracy) / 2
                details["actual_memory_mb"] = actual_memory
                details["memory_accuracy"] = accuracy

        return DimensionScore(
            dimension=EvaluationDimension.RESOURCE_EFFICIENCY,
            score=max(0, min(1, efficiency_score)),
            details=details,
        )

    def _evaluate_reliability(
        self,
        plan: ExecutionPlan,
        feedback: list[ExecutionFeedback]
    ) -> DimensionScore:
        """评估可靠性"""
        if not feedback:
            # 基于方案置信度
            confidence_score = {
                PlanConfidence.HIGH: 0.9,
                PlanConfidence.MEDIUM: 0.7,
                PlanConfidence.LOW: 0.5,
            }
            score = confidence_score.get(plan.confidence, 0.5)
            details = {"based_on": "plan_confidence", "confidence": plan.confidence.value}
        else:
            # 计算失败率
            failed_count = sum(1 for f in feedback if f.feedback_type.value == "execution_failure")
            total_count = len(feedback)
            failure_rate = failed_count / total_count if total_count > 0 else 0
            score = 1 - failure_rate
            details = {
                "failed_count": failed_count,
                "total_count": total_count,
                "failure_rate": failure_rate,
            }

        return DimensionScore(
            dimension=EvaluationDimension.RELIABILITY,
            score=score,
            details=details,
        )

    def _calculate_overall_score(self, dimension_scores: list[DimensionScore]) -> float:
        """计算总体得分"""
        weighted_sum = 0.0
        for ds in dimension_scores:
            weight = self.DIMENSION_WEIGHTS.get(ds.dimension, 0.2)
            weighted_sum += ds.score * weight
        return weighted_sum

    def _determine_grade(self, score: float) -> str:
        """确定等级"""
        for grade, threshold in sorted(self.GRADE_THRESHOLDS.items(), key=lambda x: x[1], reverse=True):
            if score >= threshold:
                return grade
        return "F"

    def _analyze_strengths_weaknesses(
        self,
        dimension_scores: list[DimensionScore]
    ) -> tuple[list[str], list[str]]:
        """分析优势和劣势"""
        strengths = []
        weaknesses = []

        for ds in dimension_scores:
            if ds.score >= 0.8:
                strengths.append(f"{ds.dimension.value}: 优秀 ({ds.score:.2f})")
            elif ds.score >= 0.6:
                strengths.append(f"{ds.dimension.value}: 良好 ({ds.score:.2f})")
            else:
                weaknesses.append(f"{ds.dimension.value}: 需改进 ({ds.score:.2f})")

        return strengths, weaknesses

    def _identify_opportunities(
        self,
        dimension_scores: list[DimensionScore],
        plan: ExecutionPlan
    ) -> list[str]:
        """识别优化机会"""
        opportunities = []

        for ds in dimension_scores:
            if ds.dimension == EvaluationDimension.TIME_ACCURACY and ds.score < 0.7:
                opportunities.append("优化时间估算算法，提高预估准确性")

            if ds.dimension == EvaluationDimension.SUCCESS_RATE and ds.score < 0.8:
                opportunities.append("分析失败步骤，增加容错机制")

            if ds.dimension == EvaluationDimension.USER_SATISFACTION and ds.score < 0.7:
                opportunities.append("收集用户反馈，改进交互体验")

            if ds.dimension == EvaluationDimension.RESOURCE_EFFICIENCY and ds.score < 0.7:
                opportunities.append("优化资源使用，减少不必要的依赖")

            if ds.dimension == EvaluationDimension.RELIABILITY and ds.score < 0.8:
                opportunities.append("增加重试机制和错误处理")

        return opportunities

    def get_evaluation_stats(self) -> dict[str, Any]:
        """获取评估统计"""
        if not self.evaluation_history:
            return {"total_evaluations": 0}

        grade_distribution = {}
        for eval in self.evaluation_history:
            grade_distribution[eval.grade] = grade_distribution.get(eval.grade, 0) + 1

        return {
            "total_evaluations": len(self.evaluation_history),
            "average_score": sum(e.overall_score for e in self.evaluation_history) / len(self.evaluation_history),
            "grade_distribution": grade_distribution,
            "recent_performance": self._get_recent_performance(),
        }

    def _get_recent_performance(self) -> dict[str, Any]:
        """获取最近性能"""
        if len(self.evaluation_history) < 2:
            return {"message": "数据不足"}

        # 对比前半部分和后半部分
        mid = len(self.evaluation_history) // 2
        early_avg = sum(e.overall_score for e in self.evaluation_history[:mid]) / mid if mid > 0 else 0
        late_avg = sum(e.overall_score for e in self.evaluation_history[mid:]) / (len(self.evaluation_history) - mid)

        return {
            "early_average": early_avg,
            "late_average": late_avg,
            "trend": "improving" if late_avg > early_avg else "declining" if late_avg < early_avg else "stable",
        }

    def get_best_plans(self, top_n: int = 5) -> list[dict[str, Any]]:
        """获取评分最高的方案"""
        sorted_evals = sorted(self.evaluation_history, key=lambda e: e.overall_score, reverse=True)

        return [
            {
                "plan_id": e.plan_id,
                "overall_score": e.overall_score,
                "grade": e.grade,
                "evaluation_id": e.evaluation_id,
            }
            for e in sorted_evals[:top_n]
        ]
