#!/usr/bin/env python3
from __future__ import annotations
"""
目标管理系统 - 分析器类
Goal Management System - Analyzer Classes

作者: Athena AI系统
创建时间: 2025-12-04
重构时间: 2026-01-27
版本: 2.0.0
"""

from datetime import datetime
from typing import Any

from .types import Goal, GoalPriority, GoalStatus, ProgressReport


class ProgressAnalyzer:
    """进度分析器

    负责进度报告的存储、检索和分析。
    """

    def __init__(self):
        """初始化进度分析器"""
        self.progress_reports: list[ProgressReport] = []

    def save_progress_report(self, report: ProgressReport) -> None:
        """保存进度报告

        Args:
            report: 进度报告对象
        """
        self.progress_reports.append(report)

    def get_latest_report(self, goal_id: str) -> ProgressReport | None:
        """获取最新的进度报告

        Args:
            goal_id: 目标ID

        Returns:
            最新的进度报告,如果不存在返回None
        """
        goal_reports = [r for r in self.progress_reports if r.goal_id == goal_id]
        return max(goal_reports, key=lambda r: r.timestamp) if goal_reports else None

    def get_recent_reports(self, limit: int = 10) -> list[ProgressReport]:
        """获取最近的进度报告

        Args:
            limit: 返回数量限制

        Returns:
            最近的进度报告列表
        """
        return sorted(self.progress_reports, key=lambda r: r.timestamp, reverse=True)[:limit]

    def analyze_progress(self, report: ProgressReport, goal: Goal) -> dict[str, Any]:
        """分析进度并生成问题和建议

        Args:
            report: 进度报告
            goal: 目标对象

        Returns:
            包含issues和recommendations的字典
        """
        analysis = {
            'issues': [],
            'recommendations': []
        }

        # 检查进度问题
        if report.overall_progress < 25:
            analysis['issues'].append("进度偏慢,需要加快执行速度")
            analysis['recommendations'].append("考虑分解任务或调整资源分配")

        if report.confidence_level < 0.7:
            analysis['issues'].append("进度预估置信度较低")
            analysis['recommendations'].append("重新评估时间规划和资源需求")

        # 检查子目标问题
        delayed_subgoals = [
            sid for sid, progress in report.subgoal_progress.items()
            if progress < 50 and self._is_subgoal_delayed(goal, sid)
        ]
        if delayed_subgoals:
            analysis['issues'].append(f"发现 {len(delayed_subgoals)} 个子目标进度滞后")
            analysis['recommendations'].append("重点关注滞后子目标的执行")

        return analysis

    def _is_subgoal_delayed(self, goal: Goal, subgoal_id: str) -> bool:
        """检查子目标是否延迟

        Args:
            goal: 目标对象
            subgoal_id: 子目标ID

        Returns:
            是否延迟
        """
        subgoal = next((sg for sg in goal.subgoals if sg.id == subgoal_id), None)
        if subgoal and subgoal.due_date:
            return datetime.now() > subgoal.due_date and subgoal.status != GoalStatus.COMPLETED
        return False

    def analyze_performance_trends(self) -> dict[str, Any]:
        """分析性能趋势

        Returns:
            包含趋势指标的字典
        """
        # 这里可以实现更复杂的趋势分析
        return {
            'average_completion_time': 0,  # 平均完成时间
            'success_rate': 0,  # 成功率
            'progress_velocity': 0  # 进度速度
        }


class GoalOptimizer:
    """目标优化器

    负责分析目标并生成优化建议。
    """

    def generate_optimization_recommendations(self, active_goals: dict[str, Goal]) -> list[str]:
        """生成优化建议

        Args:
            active_goals: 活跃目标字典

        Returns:
            优化建议列表
        """
        recommendations = []

        # 分析目标分布
        high_priority_goals = [
            g for g in active_goals.values()
            if g.priority in [GoalPriority.CRITICAL, GoalPriority.URGENT]
        ]
        if len(high_priority_goals) > 5:
            recommendations.append("高优先级目标过多,建议重新评估优先级或分配更多资源")

        # 分析时间规划
        overdue_goals = [
            g for g in active_goals.values()
            if g.due_date and datetime.now() > g.due_date and g.status != GoalStatus.COMPLETED
        ]
        if overdue_goals:
            recommendations.append(f"发现 {len(overdue_goals)} 个逾期目标,建议重新规划时间或调整范围")

        return recommendations


class NotificationSystem:
    """通知系统

    负责发送进度通知。
    """

    def send_progress_notification(self, goal: Goal, progress_report: ProgressReport) -> Any:
        """发送进度通知

        Args:
            goal: 目标对象
            progress_report: 进度报告
        """
        print(f"🔔 通知: 目标 '{goal.title}' 进度更新 - {progress_report.overall_progress:.1f}%")
