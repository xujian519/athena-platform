#!/usr/bin/env python3
from __future__ import annotations
"""
轻量级评估引擎
Lightweight Evaluation Engine

小娜评估与反思模块的轻量级实现,减少外部依赖
提供基础的评估和反思能力
"""

import logging
import statistics
from dataclasses import asdict, dataclass
from datetime import datetime
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class EvaluationType(Enum):
    """评估类型"""

    PERFORMANCE = "performance"
    QUALITY = "quality"
    REFLECTION = "reflection"
    COMPREHENSIVE = "comprehensive"


class EvaluationGrade(Enum):
    """评估等级"""

    EXCELLENT = "excellent"
    GOOD = "good"
    SATISFACTORY = "satisfactory"
    NEEDS_IMPROVEMENT = "needs_improvement"
    POOR = "poor"


@dataclass
class EvaluationResult:
    """评估结果"""

    task_id: str
    evaluation_type: EvaluationType
    grade: EvaluationGrade
    score: float
    metrics: dict[str, float]
    feedback: str
    timestamp: datetime
    details: dict | None = None


class LightweightEvaluationEngine:
    """轻量级评估引擎"""

    def __init__(self):
        """初始化轻量级评估引擎"""
        self.name = "LightweightEvaluationEngine"
        self.version = "1.0.0"
        self.evaluation_history: list[EvaluationResult] = []
        self.performance_thresholds = {
            "response_time": 5.0,  # 秒
            "success_rate": 0.9,
            "accuracy": 0.85,
        }
        self.max_history_size = 1000

    async def evaluate(
        self, task_id: str, data: dict[str, Any], evaluation_type: str = "comprehensive"
    ) -> EvaluationResult:
        """执行评估"""
        try:
            eval_type = EvaluationType(evaluation_type)

            if eval_type == EvaluationType.PERFORMANCE:
                result = await self._evaluate_performance(task_id, data)
            elif eval_type == EvaluationType.QUALITY:
                result = await self._evaluate_quality(task_id, data)
            elif eval_type == EvaluationType.REFLECTION:
                result = await self._evaluate_reflection(task_id, data)
            else:  # COMPREHENSIVE
                result = await self._evaluate_comprehensive(task_id, data)

            # 保存到历史记录
            self._save_to_history(result)

            return result
        except Exception as e:
            logger.error(f"捕获异常: {e}", exc_info=True)
            # 返回默认的失败评估
            return EvaluationResult(
                task_id=task_id,
                evaluation_type=EvaluationType(evaluation_type),
                grade=EvaluationGrade.POOR,
                score=0.0,
                metrics={"error": 1.0},
                feedback=f"评估过程出错: {e!s}",
                timestamp=datetime.now(),
            )

    async def _evaluate_performance(self, task_id: str, data: dict[str, Any]) -> EvaluationResult:
        """性能评估"""
        metrics = {}

        # 响应时间评估
        response_time = data.get("response_time", 0)
        metrics["response_time"] = response_time
        metrics["response_time_score"] = max(
            0, 1 - (response_time / self.performance_thresholds["response_time"])
        )

        # 成功率评估
        success = data.get("success", False)
        metrics["success"] = 1.0 if success else 0.0

        # 资源使用评估
        cpu_usage = data.get("cpu_usage", 0)
        memory_usage = data.get("memory_usage", 0)
        metrics["cpu_usage"] = cpu_usage
        metrics["memory_usage"] = memory_usage
        metrics["resource_score"] = max(0, 1 - (cpu_usage + memory_usage) / 200)

        # 计算综合分数
        performance_score = (
            metrics["response_time_score"] * 0.4
            + metrics["success"] * 0.4
            + metrics["resource_score"] * 0.2
        )

        # 确定等级
        grade = self._determine_grade(performance_score)

        return EvaluationResult(
            task_id=task_id,
            evaluation_type=EvaluationType.PERFORMANCE,
            grade=grade,
            score=performance_score,
            metrics=metrics,
            feedback=self._generate_performance_feedback(metrics),
            timestamp=datetime.now(),
        )

    async def _evaluate_quality(self, task_id: str, data: dict[str, Any]) -> EvaluationResult:
        """质量评估"""
        metrics = {}

        # 准确性评估
        accuracy = data.get("accuracy", 0.8)  # 默认值
        metrics["accuracy"] = accuracy

        # 完整性评估
        completeness = data.get("completeness", 0.8)
        metrics["completeness"] = completeness

        # 相关性评估
        relevance = data.get("relevance", 0.8)
        metrics["relevance"] = relevance

        # 可读性评估(文本长度和结构)
        if "output" in data:
            output = str(data.get("output"))
            metrics["output_length"] = len(output)
            metrics["has_structure"] = 1.0 if any(c in output for c in ["\n", ".", "。"]) else 0.0
        else:
            metrics["output_length"] = 0
            metrics["has_structure"] = 0.0

        # 计算综合分数
        quality_score = (
            accuracy * 0.4 + completeness * 0.3 + relevance * 0.2 + metrics["has_structure"] * 0.1
        )

        grade = self._determine_grade(quality_score)

        return EvaluationResult(
            task_id=task_id,
            evaluation_type=EvaluationType.QUALITY,
            grade=grade,
            score=quality_score,
            metrics=metrics,
            feedback=self._generate_quality_feedback(metrics),
            timestamp=datetime.now(),
        )

    async def _evaluate_reflection(self, task_id: str, data: dict[str, Any]) -> EvaluationResult:
        """反思评估"""
        metrics = {}

        # 自我认知
        self_awareness = data.get("self_awareness", 0.7)
        metrics["self_awareness"] = self_awareness

        # 学习能力
        learning_score = data.get("learning_score", 0.7)
        metrics["learning_score"] = learning_score

        # 改进建议数量
        improvements = data.get("improvements", [])
        metrics["improvement_count"] = len(improvements)
        metrics["improvement_score"] = min(1.0, len(improvements) / 3)

        # 错误分析
        error_analysis = data.get("error_analysis", {})
        metrics["has_error_analysis"] = 1.0 if error_analysis else 0.0

        # 计算综合分数
        reflection_score = (
            self_awareness * 0.3
            + learning_score * 0.3
            + metrics["improvement_score"] * 0.2
            + metrics["has_error_analysis"] * 0.2
        )

        grade = self._determine_grade(reflection_score)

        return EvaluationResult(
            task_id=task_id,
            evaluation_type=EvaluationType.REFLECTION,
            grade=grade,
            score=reflection_score,
            metrics=metrics,
            feedback=self._generate_reflection_feedback(metrics),
            timestamp=datetime.now(),
        )

    async def _evaluate_comprehensive(self, task_id: str, data: dict[str, Any]) -> EvaluationResult:
        """综合评估"""
        # 执行所有类型的评估
        performance = await self._evaluate_performance(task_id, data)
        quality = await self._evaluate_quality(task_id, data)
        reflection = await self._evaluate_reflection(task_id, data)

        # 综合所有评估结果
        metrics = {
            "performance_score": performance.score,
            "quality_score": quality.score,
            "reflection_score": reflection.score,
        }

        # 加权平均
        comprehensive_score = performance.score * 0.4 + quality.score * 0.4 + reflection.score * 0.2

        grade = self._determine_grade(comprehensive_score)

        feedback = "\n".join(
            [
                "综合评估结果:",
                f"- 性能评分: {performance.score:.2f} ({performance.grade.value})",
                f"- 质量评分: {quality.score:.2f} ({quality.grade.value})",
                f"- 反思评分: {reflection.score:.2f} ({reflection.grade.value})",
                f"- 综合评分: {comprehensive_score:.2f} ({grade.value})",
            ]
        )

        return EvaluationResult(
            task_id=task_id,
            evaluation_type=EvaluationType.COMPREHENSIVE,
            grade=grade,
            score=comprehensive_score,
            metrics=metrics,
            feedback=feedback,
            timestamp=datetime.now(),
            details={
                "performance": asdict(performance),
                "quality": asdict(quality),
                "reflection": asdict(reflection),
            },
        )

    def _determine_grade(self, score: float) -> EvaluationGrade:
        """根据分数确定等级"""
        if score >= 0.9:
            return EvaluationGrade.EXCELLENT
        elif score >= 0.8:
            return EvaluationGrade.GOOD
        elif score >= 0.7:
            return EvaluationGrade.SATISFACTORY
        elif score >= 0.6:
            return EvaluationGrade.NEEDS_IMPROVEMENT
        else:
            return EvaluationGrade.POOR

    def _generate_performance_feedback(self, metrics: dict[str, float]) -> str:
        """生成性能反馈"""
        feedback_parts = []

        if metrics["response_time_score"] < 0.8:
            feedback_parts.append("响应时间需要优化")
        if metrics["success"] < 1.0:
            feedback_parts.append("存在执行失败的情况")
        if metrics["resource_score"] < 0.7:
            feedback_parts.append("资源使用偏高")

        if not feedback_parts:
            return "性能表现良好"
        return "需要改进的方面:" + "、".join(feedback_parts)

    def _generate_quality_feedback(self, metrics: dict[str, float]) -> str:
        """生成质量反馈"""
        feedback_parts = []

        if metrics["accuracy"] < 0.9:
            feedback_parts.append("准确性有待提高")
        if metrics["completeness"] < 0.9:
            feedback_parts.append("输出不够完整")
        if metrics["relevance"] < 0.9:
            feedback_parts.append("相关性需要加强")

        if not feedback_parts:
            return "输出质量优秀"
        return "质量改进建议:" + "、".join(feedback_parts)

    def _generate_reflection_feedback(self, metrics: dict[str, float]) -> str:
        """生成反思反馈"""
        feedback_parts = []

        if metrics["self_awareness"] < 0.8:
            feedback_parts.append("需要增强自我认知")
        if metrics["learning_score"] < 0.8:
            feedback_parts.append("学习能力需要提升")
        if metrics["improvement_count"] == 0:
            feedback_parts.append("应该提出改进建议")

        if not feedback_parts:
            return "反思深入,有改进意识"
        return "反思改进:" + "、".join(feedback_parts)

    def _save_to_history(self, result: EvaluationResult) -> Any:
        """保存评估结果到历史记录"""
        self.evaluation_history.append(result)

        # 限制历史记录大小
        if len(self.evaluation_history) > self.max_history_size:
            self.evaluation_history = self.evaluation_history[-self.max_history_size :]

    def get_evaluation_history(
        self, task_id: str | None = None, limit: int = 50
    ) -> list[EvaluationResult]:
        """获取评估历史"""
        history = self.evaluation_history

        if task_id:
            history = [r for r in history if r.task_id == task_id]

        return history[-limit:]

    def get_statistics(self) -> dict[str, Any]:
        """获取统计信息"""
        if not self.evaluation_history:
            return {"total_evaluations": 0}

        # 计算各项统计
        total = len(self.evaluation_history)
        scores = [r.score for r in self.evaluation_history]

        grade_counts = {}
        for grade in EvaluationGrade:
            grade_counts[grade.value] = sum(1 for r in self.evaluation_history if r.grade == grade)

        type_counts = {}
        for eval_type in EvaluationType:
            type_counts[eval_type.value] = sum(
                1 for r in self.evaluation_history if r.evaluation_type == eval_type
            )

        return {
            "total_evaluations": total,
            "average_score": statistics.mean(scores),
            "max_score": max(scores),
            "min_score": min(scores),
            "grade_distribution": grade_counts,
            "type_distribution": type_counts,
            "last_evaluation": (
                self.evaluation_history[-1].timestamp.isoformat()
                if self.evaluation_history
                else None
            ),
        }

    async def health_check(self) -> dict[str, Any]:
        """健康检查"""
        return {
            "status": "healthy",
            "engine": self.name,
            "version": self.version,
            "history_size": len(self.evaluation_history),
            "performance_thresholds": self.performance_thresholds,
            "statistics": self.get_statistics(),
        }


# =============================================================================
# === 便捷函数 ===
# =============================================================================

# 全局引擎实例
_global_lightweight_evaluator: LightweightEvaluationEngine | None = None


def get_lightweight_evaluator() -> LightweightEvaluationEngine:
    """
    获取或创建轻量级评估引擎实例

    Returns:
        LightweightEvaluationEngine 实例
    """
    global _global_lightweight_evaluator

    if _global_lightweight_evaluator is None:
        _global_lightweight_evaluator = LightweightEvaluationEngine()

    return _global_lightweight_evaluator


__all__ = [
    "EvaluationType",
    "EvaluationGrade",
    "EvaluationResult",
    "LightweightEvaluationEngine",
    "get_lightweight_evaluator",
]
