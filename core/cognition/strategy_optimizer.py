#!/usr/bin/env python3
from __future__ import annotations
"""
策略优化器
Strategy Optimizer

功能:
1. 基于反馈优化规划策略
2. 学习最佳实践
3. 调整参数配置
4. 提供优化建议

Author: Athena Team
Version: 1.0.0
Date: 2026-02-24
"""

import json
import logging
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any

from .feedback_collector import ExecutionFeedback
from .multi_plan_generator import PlanStrategy
from .plan_evaluator import PlanEvaluation

logger = logging.getLogger(__name__)


class OptimizationType(Enum):
    """优化类型"""
    PARAMETER_TUNING = "parameter_tuning"  # 参数调优
    STRATEGY_SELECTION = "strategy_selection"  # 策略选择优化
    TEMPLATE_IMPROVEMENT = "template_improvement"  # 模板改进
    WEIGHT_ADJUSTMENT = "weight_adjustment"  # 权重调整


@dataclass
class OptimizationRecommendation:
    """优化建议"""
    recommendation_id: str
    optimization_type: OptimizationType
    description: str
    current_value: Any
    suggested_value: Any
    expected_improvement: str
    confidence: float  # 0-1
    priority: str  # high/medium/low


@dataclass
class StrategyPerformance:
    """策略性能数据"""
    strategy: PlanStrategy
    total_uses: int
    average_score: float
    success_rate: float
    average_time: int
    user_satisfaction: float
    last_used: datetime


class StrategyOptimizer:
    """
    策略优化器

    核心功能:
    1. 分析策略性能
    2. 识别优化机会
    3. 生成优化建议
    4. 维护优化历史
    """

    def __init__(self, storage_path: str | None = None):
        self.logger = logging.getLogger(__name__)
        self.storage_path = storage_path or "data/strategy_optimization.json"

        # 策略性能跟踪
        self.strategy_performance: dict[PlanStrategy, StrategyPerformance] = {}

        # 优化建议历史
        self.optimization_history: list[OptimizationRecommendation] = []

        # 可优化参数
        self.optimizable_parameters = {
            "time_estimation_multiplier": 1.0,  # 时间估算乘数
            "confidence_threshold": 0.6,  # 置信度阈值
            "max_parallel_steps": 5,  # 最大并行步骤数
            "resource_safety_margin": 0.2,  # 资源安全边际
        }

        # 维度权重（可调整）
        self.dimension_weights = {
            "time_accuracy": 0.2,
            "success_rate": 0.3,
            "user_satisfaction": 0.25,
            "resource_efficiency": 0.15,
            "reliability": 0.1,
        }

        self._load_optimization_data()

        self.logger.info("🔧 策略优化器初始化完成")

    def _load_optimization_data(self) -> None:
        """加载优化数据"""
        try:
            with open(self.storage_path, encoding="utf-8") as f:
                data = json.load(f)

                # 加载参数
                if "parameters" in data:
                    self.optimizable_parameters.update(data["parameters"])

                # 加载权重
                if "weights" in data:
                    self.dimension_weights.update(data["weights"])

                # 加载历史
                if "history" in data:
                    for item in data["history"]:
                        rec = OptimizationRecommendation(
                            recommendation_id=item["recommendation_id"],
                            optimization_type=OptimizationType(item["optimization_type"]),
                            description=item["description"],
                            current_value=item["current_value"],
                            suggested_value=item["suggested_value"],
                            expected_improvement=item["expected_improvement"],
                            confidence=item["confidence"],
                            priority=item["priority"],
                        )
                        self.optimization_history.append(rec)

                self.logger.info("   📂 加载优化数据成功")
        except FileNotFoundError:
            self.logger.info("   📂 未找到优化数据文件，创建新的")
        except Exception as e:
            self.logger.warning(f"   ⚠️ 加载优化数据失败: {e}")

    def _save_optimization_data(self) -> None:
        """保存优化数据"""
        try:
            import os
            os.makedirs(os.path.dirname(self.storage_path), exist_ok=True)

            data = {
                "parameters": self.optimizable_parameters,
                "weights": self.dimension_weights,
                "history": [
                    {
                        "recommendation_id": r.recommendation_id,
                        "optimization_type": r.optimization_type.value,
                        "description": r.description,
                        "current_value": r.current_value,
                        "suggested_value": r.suggested_value,
                        "expected_improvement": r.expected_improvement,
                        "confidence": r.confidence,
                        "priority": r.priority,
                    }
                    for r in self.optimization_history
                ],
                "last_updated": datetime.now().isoformat(),
            }

            with open(self.storage_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            self.logger.error(f"   ❌ 保存优化数据失败: {e}")

    def analyze_strategy_performance(
        self,
        evaluations: list[PlanEvaluation],
        feedback_list: list[ExecutionFeedback]
    ) -> dict[PlanStrategy, StrategyPerformance]:
        """分析策略性能"""
        self.logger.info("📊 分析策略性能")

        # 按策略分组评估
        strategy_evals = {}
        strategy_feedback = {}

        for eval in evaluations:
            # 从元数据中获取策略
            strategy_str = eval.metadata.get("plan_strategy", "balanced")
            try:
                strategy = PlanStrategy(strategy_str)
                if strategy not in strategy_evals:
                    strategy_evals[strategy] = []
                strategy_evals[strategy].append(eval)
            except ValueError:
                pass

        # 按策略分组反馈
        for feedback in feedback_list:
            strategy_str = feedback.metadata.get("plan_strategy", "balanced")
            try:
                strategy = PlanStrategy(strategy_str)
                if strategy not in strategy_feedback:
                    strategy_feedback[strategy] = []
                strategy_feedback[strategy].append(feedback)
            except ValueError:
                pass

        # 分析每个策略
        performance_data = {}
        for strategy in PlanStrategy:
            evals = strategy_evals.get(strategy, [])
            feedbacks = strategy_feedback.get(strategy, [])

            if not evals and not feedbacks:
                continue

            # 计算统计数据
            total_uses = len(evals) + len(feedbacks)

            # 平均得分
            if evals:
                average_score = sum(e.overall_score for e in evals) / len(evals)
            else:
                average_score = 0.5

            # 成功率
            if feedbacks:
                success_count = sum(
                    1 for f in feedbacks
                    if f.feedback_type.value == "execution_success" or
                    (f.success_rate and f.success_rate > 0.8)
                )
                success_rate = success_count / len(feedbacks)
            else:
                success_rate = 0.8

            # 平均时间
            times = [f.execution_time for f in feedbacks if f.execution_time]
            average_time = int(sum(times) / len(times)) if times else 0

            # 用户满意度
            satisfaction_scores = []
            for f in feedbacks:
                if f.satisfaction:
                    score_map = {
                        "very_satisfied": 1.0,
                        "satisfied": 0.8,
                        "neutral": 0.6,
                        "dissatisfied": 0.4,
                        "very_dissatisfied": 0.2,
                    }
                    satisfaction_scores.append(score_map.get(f.satisfaction.value, 0.5))
            user_satisfaction = (
                sum(satisfaction_scores) / len(satisfaction_scores)
                if satisfaction_scores else 0.7
            )

            performance = StrategyPerformance(
                strategy=strategy,
                total_uses=total_uses,
                average_score=average_score,
                success_rate=success_rate,
                average_time=average_time,
                user_satisfaction=user_satisfaction,
                last_used=datetime.now(),
            )

            performance_data[strategy] = performance
            self.logger.info(
                f"   {strategy.value}: 得分={average_score:.2f}, "
                f"成功率={success_rate:.2f}"
            )

        self.strategy_performance = performance_data
        return performance_data

    def generate_optimization_recommendations(
        self,
        evaluations: list[PlanEvaluation],
        feedback_list: list[ExecutionFeedback]
    ) -> list[OptimizationRecommendation]:
        """生成优化建议"""
        self.logger.info("💡 生成优化建议")

        recommendations = []

        # 1. 分析策略性能差异
        performance = self.analyze_strategy_performance(evaluations, feedback_list)

        if len(performance) > 1:
            best_strategy = max(performance.items(), key=lambda x: x[1].average_score)
            worst_strategy = min(performance.items(), key=lambda x: x[1].average_score)

            score_diff = best_strategy[1].average_score - worst_strategy[1].average_score
            if score_diff > 0.15:
                recommendations.append(OptimizationRecommendation(
                    recommendation_id=f"opt_{datetime.now().strftime('%Y%m%d%H%M%S')}_strategy",
                    optimization_type=OptimizationType.STRATEGY_SELECTION,
                    description=(
                        f"策略 '{best_strategy[0].value}' 表现显著优于 "
                        f"'{worst_strategy[0].value}'"
                    ),
                    current_value=worst_strategy[0].value,
                    suggested_value=best_strategy[0].value,
                    expected_improvement=f"提升得分 {score_diff:.2f}",
                    confidence=0.8,
                    priority="high",
                ))

        # 2. 参数优化建议
        # 时间估算
        time_feedback = [
            f for f in feedback_list
            if f.execution_time and f.metadata.get("estimated_time")
        ]
        if time_feedback:
            deviations = []
            for f in time_feedback:
                estimated = f.metadata.get("estimated_time", 1)
                actual = f.execution_time
                if estimated > 0:
                    deviations.append(actual / estimated)

            if deviations:
                avg_ratio = sum(deviations) / len(deviations)
                current_multiplier = self.optimizable_parameters.get(
                    "time_estimation_multiplier", 1.0
                )

                if abs(avg_ratio - current_multiplier) > 0.1:
                    abs(avg_ratio - current_multiplier) * 100
                    recommendations.append(OptimizationRecommendation(
                        recommendation_id=f"opt_{datetime.now().strftime('%Y%m%d%H%M%S')}_time",
                        optimization_type=OptimizationType.PARAMETER_TUNING,
                        description=f"时间估算需要调整，当前平均比率为 {avg_ratio:.2f}",
                        current_value=current_multiplier,
                        suggested_value=round(avg_ratio, 2),
                        expected_improvement=f"时间估算准确性提升 {abs(avg_ratio - current_multiplier)*100:.1f}%",
                        confidence=0.7,
                        priority="medium",
                    ))

        # 3. 维度权重调整
        # 基于评估结果分析哪些维度最需要改进
        if evaluations:
            dimension_scores = {}
            for eval in evaluations:
                for ds in eval.dimension_scores:
                    if ds.dimension.value not in dimension_scores:
                        dimension_scores[ds.dimension.value] = []
                    dimension_scores[ds.dimension.value].append(ds.score)

            # 找出表现最差的维度
            worst_dimension = min(dimension_scores.items(), key=lambda x: sum(x[1]) / len(x[1]))

            avg_scores = {k: sum(v) / len(v) for k, v in dimension_scores.items()}
            min_score = avg_scores[worst_dimension[0]]

            if min_score < 0.7:
                current_weight = self.dimension_weights.get(worst_dimension[0], 0.2)
                suggested_weight = min(0.4, current_weight + 0.1)

                recommendations.append(OptimizationRecommendation(
                    recommendation_id=f"opt_{datetime.now().strftime('%Y%m%d%H%M%S')}_weight",
                    optimization_type=OptimizationType.WEIGHT_ADJUSTMENT,
                    description=f"维度 '{worst_dimension[0]}' 表现较差，建议提高其权重",
                    current_value=current_weight,
                    suggested_value=suggested_weight,
                    expected_improvement=f"促进 '{worst_dimension[0]}' 的改进",
                    confidence=0.6,
                    priority="low",
                ))

        # 4. 保存到历史
        self.optimization_history.extend(recommendations)
        self._save_optimization_data()

        self.logger.info(f"   ✅ 生成 {len(recommendations)} 条优化建议")

        return recommendations

    def apply_optimization(self, recommendation: OptimizationRecommendation) -> bool:
        """应用优化建议"""
        self.logger.info(f"🔧 应用优化: {recommendation.description}")

        try:
            if recommendation.optimization_type == OptimizationType.PARAMETER_TUNING:
                param_name = None
                if "time" in recommendation.description.lower():
                    param_name = "time_estimation_multiplier"
                elif "confidence" in recommendation.description.lower():
                    param_name = "confidence_threshold"
                elif "parallel" in recommendation.description.lower():
                    param_name = "max_parallel_steps"

                if param_name and param_name in self.optimizable_parameters:
                    self.optimizable_parameters[param_name] = recommendation.suggested_value
                    self._save_optimization_data()
                    self.logger.info(
                        f"   ✅ 参数 {param_name} 已更新为 "
                        f"{recommendation.suggested_value}"
                    )
                    return True

            elif recommendation.optimization_type == OptimizationType.WEIGHT_ADJUSTMENT:
                # 从描述中提取维度名称
                for dim in self.dimension_weights:
                    if dim in recommendation.description:
                        self.dimension_weights[dim] = recommendation.suggested_value
                        self._save_optimization_data()
                        self.logger.info(
                            f"   ✅ 权重 {dim} 已更新为 "
                            f"{recommendation.suggested_value}"
                        )
                        return True

            return False

        except Exception as e:
            self.logger.error(f"   ❌ 应用优化失败: {e}")
            return False

    def get_current_parameters(self) -> dict[str, Any]:
        """获取当前参数"""
        return {
            "optimizable_parameters": self.optimizable_parameters.copy(),
            "dimension_weights": self.dimension_weights.copy(),
        }

    def get_strategy_recommendation(
        self,
        intent_context: dict[str, Any] | None = None
    ) -> PlanStrategy:
        """获取策略推荐"""
        # 如果有性能数据，推荐表现最好的策略
        if self.strategy_performance:
            best_strategy = max(
                self.strategy_performance.items(),
                key=lambda x: x[1].average_score * 0.6 + x[1].success_rate * 0.4
            )
            self.logger.info(
                f"💡 推荐策略: {best_strategy[0].value} "
                f"(得分: {best_strategy[1].average_score:.2f})"
            )
            return best_strategy[0]

        # 根据上下文推荐
        if intent_context:
            priority = intent_context.get("priority", "").lower()
            if "fast" in priority or "quick" in priority:
                return PlanStrategy.FAST
            elif "reliable" in priority or "safe" in priority:
                return PlanStrategy.RELIABLE
            elif "cost" in priority or "cheap" in priority:
                return PlanStrategy.ECONOMICAL

        return PlanStrategy.BALANCED

    def get_optimization_stats(self) -> dict[str, Any]:
        """获取优化统计"""
        applied_count = sum(
            1 for r in self.optimization_history
            if r.description in str(self.optimizable_parameters) or
            r.description in str(self.dimension_weights)
        )
        return {
            "total_recommendations": len(self.optimization_history),
            "applied_optimizations": applied_count,
            "current_parameters": self.optimizable_parameters,
            "strategy_performance": {
                s.value: {
                    "average_score": p.average_score,
                    "success_rate": p.success_rate,
                    "total_uses": p.total_uses,
                }
                for s, p in self.strategy_performance.items()
            },
        }
