#!/usr/bin/env python3
from __future__ import annotations
"""
反馈收集器
Feedback Collector

功能:
1. 收集方案执行反馈
2. 记录成功/失败案例
3. 分析用户满意度
4. 生成改进建议

Author: Athena Team
Version: 1.0.0
Date: 2026-02-24
"""

import json
import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

from .xiaonuo_planner_engine import ExecutionPlan

logger = logging.getLogger(__name__)


class FeedbackType(Enum):
    """反馈类型"""
    EXECUTION_SUCCESS = "execution_success"  # 执行成功
    EXECUTION_FAILURE = "execution_failure"  # 执行失败
    EXECUTION_PARTIAL = "execution_partial"  # 部分成功
    USER_SATISFACTION = "user_satisfaction"  # 用户满意度
    USER_COMPLAINT = "user_complaint"  # 用户投诉


class SatisfactionLevel(Enum):
    """满意度等级"""
    VERY_SATISFIED = "very_satisfied"  # 非常满意 (5星)
    SATISFIED = "satisfied"  # 满意 (4星)
    NEUTRAL = "neutral"  # 中立 (3星)
    DISSATISFIED = "dissatisfied"  # 不满意 (2星)
    VERY_DISSATISFIED = "very_dissatisfied"  # 非常不满意 (1星)


@dataclass
class ExecutionFeedback:
    """执行反馈"""
    feedback_id: str
    plan_id: str
    feedback_type: FeedbackType
    satisfaction: SatisfactionLevel | None = None
    execution_time: int | None = None  # 实际执行时间（秒）
    success_rate: float | None = None  # 成功率 0-1
    failed_steps: list[str] = field(default_factory=list)
    error_messages: list[str] = field(default_factory=list)
    user_comments: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class ImprovementSuggestion:
    """改进建议"""
    suggestion_id: str
    category: str  # 类别: strategy/resource/coordination/etc.
    description: str
    priority: str  # 优先级: high/medium/low
    expected_impact: str  # 预期影响
    implementation_difficulty: str  # 实施难度


class FeedbackCollector:
    """
    反馈收集器

    核心功能:
    1. 收集多种类型的反馈
    2. 分析反馈模式
    3. 生成改进建议
    4. 维护反馈历史
    """

    def __init__(self, storage_path: str | None = None):
        self.logger = logging.getLogger(__name__)
        self.feedback_history: list[ExecutionFeedback] = []
        self.storage_path = storage_path or "data/feedback_history.json"
        self._load_feedback_history()

        # 统计计数器
        self.stats = {
            "total_feedback": 0,
            "successful_executions": 0,
            "failed_executions": 0,
            "average_satisfaction": 0.0,
        }

        self._update_stats()

        self.logger.info("📝 反馈收集器初始化完成")

    def _load_feedback_history(self) -> None:
        """加载历史反馈"""
        try:
            with open(self.storage_path, encoding="utf-8") as f:
                data = json.load(f)
                for item in data:
                    feedback = self._deserialize_feedback(item)
                    self.feedback_history.append(feedback)
                self.logger.info(f"   📂 加载 {len(self.feedback_history)} 条历史反馈")
        except FileNotFoundError:
            self.logger.info("   📂 未找到历史反馈文件，创建新的")
        except Exception as e:
            self.logger.warning(f"   ⚠️ 加载历史反馈失败: {e}")

    def _save_feedback_history(self) -> None:
        """保存历史反馈"""
        try:
            import os
            os.makedirs(os.path.dirname(self.storage_path), exist_ok=True)

            data = [self._serialize_feedback(f) for f in self.feedback_history]
            with open(self.storage_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            self.logger.error(f"   ❌ 保存反馈历史失败: {e}")

    def _serialize_feedback(self, feedback: ExecutionFeedback) -> dict[str, Any]:
        """序列化反馈"""
        return {
            "feedback_id": feedback.feedback_id,
            "plan_id": feedback.plan_id,
            "feedback_type": feedback.feedback_type.value,
            "satisfaction": feedback.satisfaction.value if feedback.satisfaction else None,
            "execution_time": feedback.execution_time,
            "success_rate": feedback.success_rate,
            "failed_steps": feedback.failed_steps,
            "error_messages": feedback.error_messages,
            "user_comments": feedback.user_comments,
            "metadata": feedback.metadata,
            "timestamp": feedback.timestamp.isoformat(),
        }

    def _deserialize_feedback(self, data: dict[str, Any]) -> ExecutionFeedback:
        """反序列化反馈"""
        satisfaction = (
            SatisfactionLevel(data["satisfaction"]) if data.get("satisfaction")
            else None
        )
        timestamp = (
            datetime.fromisoformat(data["timestamp"]) if data.get("timestamp")
            else datetime.now()
        )

        return ExecutionFeedback(
            feedback_id=data["feedback_id"],
            plan_id=data["plan_id"],
            feedback_type=FeedbackType(data["feedback_type"]),
            satisfaction=satisfaction,
            execution_time=data.get("execution_time"),
            success_rate=data.get("success_rate"),
            failed_steps=data.get("failed_steps", []),
            error_messages=data.get("error_messages", []),
            user_comments=data.get("user_comments"),
            metadata=data.get("metadata", {}),
            timestamp=timestamp,
        )

    def _update_stats(self) -> None:
        """更新统计信息"""
        self.stats["total_feedback"] = len(self.feedback_history)
        self.stats["successful_executions"] = sum(
            1 for f in self.feedback_history
            if f.feedback_type == FeedbackType.EXECUTION_SUCCESS
        )
        self.stats["failed_executions"] = sum(
            1 for f in self.feedback_history
            if f.feedback_type == FeedbackType.EXECUTION_FAILURE
        )

        # 计算平均满意度
        satisfaction_scores = []
        for f in self.feedback_history:
            if f.satisfaction:
                score_map = {
                    SatisfactionLevel.VERY_SATISFIED: 5.0,
                    SatisfactionLevel.SATISFIED: 4.0,
                    SatisfactionLevel.NEUTRAL: 3.0,
                    SatisfactionLevel.DISSATISFIED: 2.0,
                    SatisfactionLevel.VERY_DISSATISFIED: 1.0,
                }
                satisfaction_scores.append(score_map.get(f.satisfaction, 3.0))

        if satisfaction_scores:
            self.stats["average_satisfaction"] = sum(satisfaction_scores) / len(satisfaction_scores)

    def collect(
        self,
        plan: ExecutionPlan,
        feedback_type: FeedbackType,
        satisfaction: SatisfactionLevel | None = None,
        execution_time: int | None = None,
        success_rate: float | None = None,
        failed_steps: list[str] | None = None,
        error_messages: list[str] | None = None,
        user_comments: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> ExecutionFeedback:
        """
        收集执行反馈

        Args:
            plan: 执行的方案
            feedback_type: 反馈类型
            satisfaction: 用户满意度
            execution_time: 实际执行时间（秒）
            success_rate: 成功率
            failed_steps: 失败的步骤列表
            error_messages: 错误消息列表
            user_comments: 用户评论
            metadata: 额外元数据

        Returns:
            ExecutionFeedback: 创建的反馈记录
        """
        self.logger.info(f"📝 收集反馈: {plan.plan_id} - {feedback_type.value}")

        feedback = ExecutionFeedback(
            feedback_id=f"feedback_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}",
            plan_id=plan.plan_id,
            feedback_type=feedback_type,
            satisfaction=satisfaction,
            execution_time=execution_time,
            success_rate=success_rate,
            failed_steps=failed_steps or [],
            error_messages=error_messages or [],
            user_comments=user_comments,
            metadata=metadata or {},
        )

        # 添加方案元数据
        feedback.metadata.update({
            "plan_strategy": plan.mode.value,
            "steps_count": len(plan.steps),
            "estimated_time": plan.estimated_time,
            "confidence": plan.confidence.value,
        })

        self.feedback_history.append(feedback)
        self._update_stats()
        self._save_feedback_history()

        self.logger.info(f"   ✅ 反馈已保存: {feedback.feedback_id}")

        return feedback

    def analyze_patterns(self) -> dict[str, Any]:
        """分析反馈模式"""
        if not self.feedback_history:
            return {"message": "暂无反馈数据"}

        success_rate = (
            self.stats["successful_executions"] / len(self.feedback_history)
            if self.feedback_history else 0
        )

        analysis = {
            "total_feedback": len(self.feedback_history),
            "success_rate": success_rate,
            "average_satisfaction": self.stats["average_satisfaction"],
            "common_failure_patterns": self._analyze_failure_patterns(),
            "time_accuracy": self._analyze_time_accuracy(),
            "satisfaction_trend": self._analyze_satisfaction_trend(),
        }

        return analysis

    def _analyze_failure_patterns(self) -> list[dict[str, Any]]:
        """分析失败模式"""
        failed_feedback = [
            f for f in self.feedback_history
            if f.feedback_type == FeedbackType.EXECUTION_FAILURE
        ]

        if not failed_feedback:
            return []

        # 统计失败步骤
        step_failures = {}
        for f in failed_feedback:
            for step in f.failed_steps:
                step_failures[step] = step_failures.get(step, 0) + 1

        # 排序
        sorted_failures = sorted(step_failures.items(), key=lambda x: x[1], reverse=True)

        return [
            {"step": step, "failure_count": count, "failure_rate": count / len(failed_feedback)}
            for step, count in sorted_failures[:10]
        ]

    def _analyze_time_accuracy(self) -> dict[str, Any]:
        """分析时间估算准确性"""
        time_feedback = [
            f for f in self.feedback_history
            if f.execution_time and f.metadata.get("estimated_time")
        ]

        if not time_feedback:
            return {"message": "暂无时间数据"}

        deviations = []
        for f in time_feedback:
            estimated = f.metadata.get("estimated_time", 0)
            actual = f.execution_time or 0
            if estimated > 0:
                deviation = abs(actual - estimated) / estimated
                deviations.append(deviation)

        if not deviations:
            return {"message": "无法计算偏差"}

        accuracy_rate = sum(1 for d in deviations if d < 0.2) / len(deviations)
        return {
            "average_deviation": sum(deviations) / len(deviations),
            "max_deviation": max(deviations),
            "min_deviation": min(deviations),
            "accuracy_rate": accuracy_rate,  # 20%以内算准确
        }

    def _analyze_satisfaction_trend(self) -> dict[str, Any]:
        """分析满意度趋势"""
        satisfaction_feedback = [
            f for f in self.feedback_history
            if f.satisfaction and f.feedback_type != FeedbackType.EXECUTION_FAILURE
        ]

        if len(satisfaction_feedback) < 2:
            return {"message": "数据不足"}

        # 将反馈按时间排序
        sorted_feedback = sorted(satisfaction_feedback, key=lambda f: f.timestamp)

        # 分前后两段对比
        mid = len(sorted_feedback) // 2
        early_scores = []
        late_scores = []

        score_map = {
            SatisfactionLevel.VERY_SATISFIED: 5,
            SatisfactionLevel.SATISFIED: 4,
            SatisfactionLevel.NEUTRAL: 3,
            SatisfactionLevel.DISSATISFIED: 2,
            SatisfactionLevel.VERY_DISSATISFIED: 1,
        }

        for f in sorted_feedback[:mid]:
            early_scores.append(score_map.get(f.satisfaction, 3))
        for f in sorted_feedback[mid:]:
            late_scores.append(score_map.get(f.satisfaction, 3))

        early_avg = sum(early_scores) / len(early_scores) if early_scores else 0
        late_avg = sum(late_scores) / len(late_scores) if late_scores else 0

        if sum(late_scores) > sum(early_scores):
            trend = "improving"
        elif sum(late_scores) < sum(early_scores):
            trend = "declining"
        else:
            trend = "stable"

        return {
            "early_average": early_avg,
            "late_average": late_avg,
            "trend": trend,
        }

    def generate_improvement_suggestions(self) -> list[ImprovementSuggestion]:
        """生成改进建议"""
        suggestions = []
        patterns = self.analyze_patterns()

        # 基于失败模式的建议
        if patterns.get("common_failure_patterns"):
            for pattern in patterns["common_failure_patterns"][:3]:
                if pattern["failure_rate"] > 0.3:  # 失败率超过30%
                    failure_rate_pct = pattern["failure_rate"] * 100
                    improvement_pct = pattern["failure_rate"] * 50
                    suggestions.append(ImprovementSuggestion(
                        suggestion_id=f"suggest_{datetime.now().strftime('%Y%m%d%H%M%S')}",
                        category="reliability",
                        description=(
                            f"优化步骤 '{pattern['step']}' 的执行逻辑，"
                            f"当前失败率 {failure_rate_pct:.1f}%"
                        ),
                        priority="high",
                        expected_impact=f"可能提升成功率 {improvement_pct:.1f}%",
                        implementation_difficulty="medium",
                    ))

        # 基于时间准确性的建议
        time_accuracy = patterns.get("time_accuracy", {})
        if isinstance(time_accuracy, dict) and time_accuracy.get("average_deviation", 0) > 0.3:
            deviation_pct = time_accuracy["average_deviation"] * 100
            suggestions.append(ImprovementSuggestion(
                suggestion_id=f"suggest_{datetime.now().strftime('%Y%m%d%H%M%S')}_time",
                category="accuracy",
                description=f"改进时间估算算法，当前平均偏差 {deviation_pct:.1f}%",
                priority="medium",
                expected_impact="提升用户体验和预期管理",
                implementation_difficulty="medium",
            ))

        # 基于满意度趋势的建议
        satisfaction_trend = patterns.get("satisfaction_trend", {})
        if isinstance(satisfaction_trend, dict) and satisfaction_trend.get("trend") == "declining":
            suggestions.append(ImprovementSuggestion(
                suggestion_id=f"suggest_{datetime.now().strftime('%Y%m%d%H%M%S')}_satisfaction",
                category="user_experience",
                description="用户满意度呈下降趋势，需要审查服务质量",
                priority="high",
                expected_impact="阻止满意度继续下降",
                implementation_difficulty="low",
            ))

        return suggestions

    def get_feedback_for_plan(self, plan_id: str) -> list[ExecutionFeedback]:
        """获取指定方案的反馈"""
        return [f for f in self.feedback_history if f.plan_id == plan_id]

    def get_stats(self) -> dict[str, Any]:
        """获取统计信息"""
        return self.stats.copy()
