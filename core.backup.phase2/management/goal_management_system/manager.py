#!/usr/bin/env python3
from __future__ import annotations
"""
目标管理系统 - 主管理类
Goal Management System - Main Manager

作者: Athena AI系统
创建时间: 2025-12-04
重构时间: 2026-01-27
版本: 2.0.0
"""

import uuid
from datetime import datetime, timedelta
from typing import Any

from .analyzers import GoalOptimizer, NotificationSystem, ProgressAnalyzer
from .decomposer import GoalDecomposer
from .types import (
    Goal,
    GoalPriority,
    GoalStatus,
    MetricType,
    ProgressMetric,
    ProgressReport,
    SubGoal,
)


class GoalManagementSystem:
    """目标管理系统

    提供目标的创建、更新、跟踪和分析功能。
    """

    def __init__(self):
        """初始化目标管理系统"""
        self.active_goals: dict[str, Goal] = {}
        self.goal_history: list[Goal] = []
        self.progress_analyzer = ProgressAnalyzer()
        self.goal_optimizer = GoalOptimizer()
        self.notification_system = NotificationSystem()
        self.decomposer = GoalDecomposer()

    def create_goal(self, goal_definition: dict[str, Any]) -> Goal:
        """创建目标

        Args:
            goal_definition: 目标定义字典

        Returns:
            创建的目标对象
        """
        print(f"🎯 创建目标: {goal_definition.get('title', '未命名目标')}")

        # 1. 目标验证
        validated_goal = self._validate_goal_definition(goal_definition)

        # 2. 子目标分解
        subgoals = self.decomposer.decompose_goal(validated_goal)

        # 3. 进度指标设定
        metrics = self._define_progress_metrics(validated_goal, subgoals)

        # 4. 创建目标对象
        goal = Goal(
            id=f"goal_{uuid.uuid4().hex[:8]}",
            title=validated_goal['title'],
            description=validated_goal['description'],
            priority=GoalPriority(validated_goal.get('priority', GoalPriority.MEDIUM.value)),
            metrics=metrics,
            subgoals=subgoals,
            due_date=self._parse_due_date(validated_goal.get('due_date')),
            assigned_agent=validated_goal.get('assigned_agent', 'xiaonuo'),
            context=validated_goal.get('context', {}),
            tags=validated_goal.get('tags', [])
        )

        # 5. 目标激活
        goal.status = GoalStatus.ACTIVE
        goal.updated_at = datetime.now()

        # 6. 注册目标
        self.active_goals[goal.id] = goal

        # 7. 初始化进度跟踪
        self._initialize_progress_tracking(goal)

        print(f"   ✅ 目标创建成功: {goal.id}")
        print(f"   📊 子目标: {len(subgoals)} 个")
        print(f"   📈 进度指标: {len(metrics)} 个")

        return goal

    def _validate_goal_definition(self, goal_def: dict[str, Any]) -> dict[str, Any]:
        """验证目标定义

        Args:
            goal_def: 目标定义字典

        Returns:
            验证后的目标定义字典
        """
        validated = goal_def.copy()

        # 必需字段检查
        if 'title' not in validated or not validated['title'].strip():
            validated['title'] = "未命名目标"

        if 'description' not in validated:
            validated['description'] = validated['title']

        # 默认值设置
        if 'priority' not in validated:
            validated['priority'] = GoalPriority.MEDIUM.value

        if 'assigned_agent' not in validated:
            # 根据目标类型智能分配
            validated['assigned_agent'] = self._assign_agent_by_goal_type(validated)

        return validated

    def _assign_agent_by_goal_type(self, goal_def: dict[str, Any]) -> str:
        """根据目标类型分配智能体

        Args:
            goal_def: 目标定义字典

        Returns:
            智能体名称
        """
        title_lower = goal_def.get('title', '').lower()
        description_lower = goal_def.get('description', '').lower()

        if any(keyword in title_lower or keyword in description_lower
               for keyword in ['专利', 'patent', '法律', 'legal']):
            return 'xiaona'
        elif any(keyword in title_lower or keyword in description_lower
                  for keyword in ['ip', '知识产权', '管理', 'management']):
            return 'athena'
        elif any(keyword in title_lower or keyword in description_lower
                  for keyword in ['运营', '市场', '营销', 'marketing']):
            return 'xiaochen'
        else:
            return 'xiaonuo'

    def _define_progress_metrics(
        self, goal_def: dict[str, Any], subgoals: list[SubGoal]
    ) -> list[ProgressMetric]:
        """定义进度指标

        Args:
            goal_def: 目标定义字典
            subgoals: 子目标列表

        Returns:
            进度指标列表
        """
        metrics = []

        # 基于子目标数量的进度指标
        metrics.append(ProgressMetric(
            name="subgoal_completion_rate",
            metric_type=MetricType.PERCENTAGE,
            target_value=100,
            unit="%",
            description="子目标完成率",
            weight=0.6
        ))

        # 基于时间的进度指标
        if 'due_date' in goal_def:
            (self._parse_due_date(goal_def['due_date']) - datetime.now()).days
            metrics.append(ProgressMetric(
                name="timeline_adherence",
                metric_type=MetricType.PERCENTAGE,
                target_value=100,
                unit="%",
                description="时间线遵守度",
                weight=0.3
            ))

        # 质量指标
        metrics.append(ProgressMetric(
            name="quality_score",
            metric_type=MetricType.QUALITY_SCORE,
            target_value=90,
            unit="分",
            description="任务质量评分",
            weight=0.1
        ))

        # 为每个子目标添加指标
        for subgoal in subgoals:
            subgoal.metrics = [
                ProgressMetric(
                    name="completion_status",
                    metric_type=MetricType.BOOLEAN,
                    target_value=True,
                    description="完成状态"
                ),
                ProgressMetric(
                    name="quality_rating",
                    metric_type=MetricType.QUALITY_SCORE,
                    target_value=80,
                    unit="分",
                    description="子目标质量评分"
                )
            ]

        return metrics

    def _parse_due_date(self, due_date_str: str | None) -> datetime | None:
        """解析到期日期

        Args:
            due_date_str: 到期日期字符串或数字(天数)

        Returns:
            解析后的日期时间对象
        """
        if not due_date_str:
            return None

        try:
            if due_date_str.isdigit():
                # 如果是数字,假设是天数
                days = int(due_date_str)
                return datetime.now() + timedelta(days=days)
            else:
                # 尝试解析日期字符串
                return datetime.fromisoformat(due_date_str.replace('Z', '+00:00'))
        except Exception:
            return None

    def _initialize_progress_tracking(self, goal: Goal) -> Any:
        """初始化进度跟踪

        Args:
            goal: 目标对象
        """
        # 创建初始进度报告
        initial_report = ProgressReport(
            goal_id=goal.id,
            timestamp=datetime.now(),
            overall_progress=0.0,
            subgoal_progress={subgoal.id: 0.0 for subgoal in goal.subgoals},
            metrics_status={metric.name: {'current': 0, 'target': metric.target_value} for metric in goal.metrics},
            estimated_completion=goal.due_date,
            confidence_level=1.0
        )

        # 保存初始报告
        self.progress_analyzer.save_progress_report(initial_report)

    def update_goal_progress(self, goal_id: str, updates: dict[str, Any]) -> ProgressReport:
        """更新目标进度

        Args:
            goal_id: 目标ID
            updates: 更新数据字典

        Returns:
            更新后的进度报告
        """
        if goal_id not in self.active_goals:
            raise ValueError(f"目标不存在: {goal_id}")

        goal = self.active_goals[goal_id]
        print(f"📈 更新目标进度: {goal.title}")

        # 1. 更新子目标进度
        if 'subgoal_updates' in updates:
            for subgoal_id, progress_data in updates['subgoal_updates'].items():
                subgoal = next((sg for sg in goal.subgoals if sg.id == subgoal_id), None)
                if subgoal:
                    self._update_subgoal_progress(subgoal, progress_data)

        # 2. 更新指标状态
        if 'metric_updates' in updates:
            for metric_name, metric_value in updates['metric_updates'].items():
                metric = next((m for m in goal.metrics if m.name == metric_name), None)
                if metric:
                    metric.current_value = metric_value

        # 3. 重新计算整体进度
        progress_report = self._calculate_progress_report(goal)

        # 4. 分析进度并生成建议
        analysis = self.progress_analyzer.analyze_progress(progress_report, goal)

        progress_report.issues.extend(analysis['issues'])
        progress_report.recommendations.extend(analysis['recommendations'])

        # 5. 更新目标状态
        self._update_goal_status(goal, progress_report)

        # 6. 保存进度报告
        self.progress_analyzer.save_progress_report(progress_report)

        # 7. 发送通知
        if self._should_send_notification(goal, progress_report):
            self.notification_system.send_progress_notification(goal, progress_report)

        print(f"   📊 整体进度: {progress_report.overall_progress:.1f}%")
        print(f"   📋 子目标完成: {len([sg for sg in goal.subgoals if sg.status == GoalStatus.COMPLETED])}/{len(goal.subgoals)}")

        return progress_report

    def _update_subgoal_progress(self, subgoal: SubGoal, progress_data: dict[str, Any]) -> Any:
        """更新子目标进度

        Args:
            subgoal: 子目标对象
            progress_data: 进度数据字典
        """
        if 'status' in progress_data:
            subgoal.status = GoalStatus(progress_data['status'])

        if 'metrics' in progress_data:
            for metric_update in progress_data['metrics']:
                metric_name = metric_update.get('name')
                metric_value = metric_update.get('value')

                for metric in subgoal.metrics:
                    if metric.name == metric_name:
                        metric.current_value = metric_value
                        break

        subgoal.updated_at = datetime.now()

    def _calculate_progress_report(self, goal: Goal) -> ProgressReport:
        """计算进度报告

        Args:
            goal: 目标对象

        Returns:
            进度报告对象
        """
        # 计算子目标进度
        subgoal_progress = {}
        total_subgoal_weight = 0
        completed_subgoal_weight = 0

        for subgoal in goal.subgoals:
            # 计算子目标完成度
            if subgoal.status == GoalStatus.COMPLETED:
                subgoal_progress[subgoal.id] = 100.0
                completed_subgoal_weight += 1
            elif subgoal.status == GoalStatus.IN_PROGRESS:
                # 基于子目标的指标计算进度
                progress = self._calculate_subgoal_metrics_progress(subgoal)
                subgoal_progress[subgoal.id] = progress
                completed_subgoal_weight += progress / 100
            else:
                subgoal_progress[subgoal.id] = 0.0

            total_subgoal_weight += 1

        # 计算整体进度
        subgoal_completion_rate = (completed_subgoal_weight / total_subgoal_weight * 100) if total_subgoal_weight > 0 else 0

        # 计算指标进度
        metrics_status = {}
        total_metric_progress = 0
        total_metric_weight = 0

        for metric in goal.metrics:
            if metric.metric_type == MetricType.PERCENTAGE:
                progress = (metric.current_value / metric.target_value * 100) if metric.target_value > 0 else 0
            elif metric.metric_type == MetricType.BOOLEAN:
                progress = 100 if metric.current_value == metric.target_value else 0
            elif metric.metric_type == MetricType.COUNTER:
                progress = (metric.current_value / metric.target_value * 100) if metric.target_value > 0 else 0
            else:
                progress = 0  # 其他类型暂时设为0

            metrics_status[metric.name] = {
                'current': metric.current_value,
                'target': metric.target_value,
                'progress': progress
            }

            total_metric_progress += progress * metric.weight
            total_metric_weight += metric.weight

        metric_completion_rate = (total_metric_progress / total_metric_weight) if total_metric_weight > 0 else 0

        # 综合进度计算
        overall_progress = (subgoal_completion_rate * 0.7 + metric_completion_rate * 0.3)

        # 预估完成时间
        estimated_completion = self._estimate_completion_time(goal, overall_progress)

        return ProgressReport(
            goal_id=goal.id,
            timestamp=datetime.now(),
            overall_progress=overall_progress,
            subgoal_progress=subgoal_progress,
            metrics_status=metrics_status,
            estimated_completion=estimated_completion,
            confidence_level=self._calculate_confidence_level(goal, overall_progress)
        )

    def _calculate_subgoal_metrics_progress(self, subgoal: SubGoal) -> float:
        """计算子目标指标进度

        Args:
            subgoal: 子目标对象

        Returns:
            进度百分比
        """
        if not subgoal.metrics:
            return 0.0

        total_progress = 0
        total_weight = 0

        for metric in subgoal.metrics:
            if metric.metric_type == MetricType.BOOLEAN:
                progress = 100 if metric.current_value == metric.target_value else 0
            elif metric.metric_type in [MetricType.PERCENTAGE, MetricType.COUNTER]:
                progress = (metric.current_value / metric.target_value * 100) if metric.target_value > 0 else 0
            else:
                progress = 0

            total_progress += progress * metric.weight
            total_weight += metric.weight

        return (total_progress / total_weight) if total_weight > 0 else 0

    def _estimate_completion_time(self, goal: Goal, current_progress: float) -> datetime | None:
        """预估完成时间

        Args:
            goal: 目标对象
            current_progress: 当前进度

        Returns:
            预计完成时间
        """
        if not goal.due_date or current_progress >= 100:
            return None

        if current_progress <= 0:
            return goal.due_date

        # 基于当前进度预估
        elapsed_time = (datetime.now() - goal.created_at).total_seconds()
        estimated_total_time = elapsed_time / (current_progress / 100)
        estimated_completion = goal.created_at + timedelta(seconds=estimated_total_time)

        return estimated_completion

    def _calculate_confidence_level(self, goal: Goal, progress: float) -> float:
        """计算置信度

        Args:
            goal: 目标对象
            progress: 当前进度

        Returns:
            置信度(0-1)
        """
        confidence = 1.0

        # 基于进度减少置信度(进度越慢,置信度越低)
        if progress < 20:
            confidence *= 0.8
        elif progress < 50:
            confidence *= 0.9

        # 基于到期时间调整置信度
        if goal.due_date:
            remaining_days = (goal.due_date - datetime.now()).days
            if remaining_days < 0:
                confidence *= 0.3
            elif remaining_days < 7:
                confidence *= 0.7

        return max(0.1, confidence)

    def _update_goal_status(self, goal: Goal, progress_report: ProgressReport) -> Any:
        """更新目标状态

        Args:
            goal: 目标对象
            progress_report: 进度报告
        """
        if progress_report.overall_progress >= 100:
            goal.status = GoalStatus.COMPLETED
        elif progress_report.overall_progress > 0:
            if goal.status == GoalStatus.ACTIVE:
                goal.status = GoalStatus.IN_PROGRESS
        else:
            # 保持原状态,或根据情况设置
            pass

        goal.updated_at = datetime.now()

    def _should_send_notification(self, goal: Goal, progress_report: ProgressReport) -> bool:
        """判断是否应该发送通知

        Args:
            goal: 目标对象
            progress_report: 进度报告

        Returns:
            是否发送通知
        """
        # 进度达到关键节点时发送通知
        if progress_report.overall_progress >= 100:
            return True  # 目标完成
        elif progress_report.overall_progress >= 75:
            return True  # 即将完成
        elif progress_report.overall_progress >= 50:
            return True  # 过半完成
        elif progress_report.overall_progress >= 25:
            return True  # 初步进展

        # 有重要问题时发送通知
        if progress_report.issues:
            return True

        # 逾期警告
        if goal.due_date and datetime.now() > goal.due_date and goal.status != GoalStatus.COMPLETED:
            return True

        return False

    def get_goal_dashboard(self) -> dict[str, Any]:
        """获取目标仪表板

        Returns:
            仪表板数据字典
        """
        dashboard = {
            'summary': {
                'total_goals': len(self.active_goals),
                'completed_goals': len([g for g in self.active_goals.values() if g.status == GoalStatus.COMPLETED]),
                'in_progress_goals': len([g for g in self.active_goals.values() if g.status == GoalStatus.IN_PROGRESS]),
                'overdue_goals': len([g for g in self.active_goals.values()
                                    if g.due_date and datetime.now() > g.due_date and g.status != GoalStatus.COMPLETED])
            },
            'goals_by_priority': self._group_goals_by_priority(),
            'goals_by_agent': self._group_goals_by_agent(),
            'upcoming_deadlines': self._get_upcoming_deadlines(),
            'recent_activity': self._get_recent_activity()
        }

        return dashboard

    def _group_goals_by_priority(self) -> dict[str, list[dict[str, Any]]]:
        """按优先级分组目标

        Returns:
            按优先级分组的目标字典
        """
        groups = {
            'urgent': [],
            'critical': [],
            'high': [],
            'medium': [],
            'low': []
        }

        for goal in self.active_goals.values():
            priority_name = goal.priority.name.lower()
            if priority_name in groups:
                groups[priority_name].append({
                    'id': goal.id,
                    'title': goal.title,
                    'status': goal.status.value,
                    'progress': self._get_goal_current_progress(goal.id)
                })

        return groups

    def _group_goals_by_agent(self) -> dict[str, list[dict[str, Any]]]:
        """按智能体分组目标

        Returns:
            按智能体分组的目标字典
        """
        groups = {}

        for goal in self.active_goals.values():
            agent = goal.assigned_agent
            if agent not in groups:
                groups[agent] = []

            groups[agent].append({
                'id': goal.id,
                'title': goal.title,
                'status': goal.status.value,
                'priority': goal.priority.name,
                'due_date': goal.due_date.isoformat() if goal.due_date else None,
                'progress': self._get_goal_current_progress(goal.id)
            })

        return groups

    def _get_upcoming_deadlines(self) -> list[dict[str, Any]]:
        """获取即将到期的目标

        Returns:
            即将到期的目标列表
        """
        upcoming = []
        cutoff_date = datetime.now() + timedelta(days=7)

        for goal in self.active_goals.values():
            if (goal.due_date and
                goal.due_date <= cutoff_date and
                goal.status != GoalStatus.COMPLETED):

                upcoming.append({
                    'id': goal.id,
                    'title': goal.title,
                    'agent': goal.assigned_agent,
                    'due_date': goal.due_date.isoformat(),
                    'days_remaining': (goal.due_date - datetime.now()).days,
                    'progress': self._get_goal_current_progress(goal.id)
                })

        return sorted(upcoming, key=lambda x: x['days_remaining'])

    def _get_recent_activity(self) -> list[dict[str, Any]]:
        """获取最近活动

        Returns:
            最近活动列表
        """
        # 从进度分析器获取最近的进度报告
        recent_reports = self.progress_analyzer.get_recent_reports(limit=10)

        activity = []
        for report in recent_reports:
            goal = self.active_goals.get(report.goal_id)
            if goal:
                activity.append({
                    'goal_id': report.goal_id,
                    'goal_title': goal.title,
                    'timestamp': report.timestamp.isoformat(),
                    'progress': report.overall_progress,
                    'agent': goal.assigned_agent
                })

        return sorted(activity, key=lambda x: x['timestamp'], reverse=True)

    def _get_goal_current_progress(self, goal_id: str) -> float:
        """获取目标当前进度

        Args:
            goal_id: 目标ID

        Returns:
            当前进度百分比
        """
        latest_report = self.progress_analyzer.get_latest_report(goal_id)
        return latest_report.overall_progress if latest_report else 0.0

    def generate_goal_insights(self) -> dict[str, Any]:
        """生成目标洞察

        Returns:
            洞察数据字典
        """
        insights = {
            'performance_trends': self.progress_analyzer.analyze_performance_trends(),
            'bottleneck_analysis': self._analyze_bottlenecks(),
            'agent_performance': self._analyze_agent_performance(),
            'recommendations': self.goal_optimizer.generate_optimization_recommendations(self.active_goals)
        }

        return insights

    def _analyze_bottlenecks(self) -> list[str]:
        """分析瓶颈

        Returns:
            瓶颈描述列表
        """
        bottlenecks = []

        # 找出长时间未更新的目标
        stale_threshold = datetime.now() - timedelta(days=7)
        stale_goals = [
            g for g in self.active_goals.values()
            if g.updated_at < stale_threshold and g.status not in [GoalStatus.COMPLETED, GoalStatus.CANCELLED]
        ]

        if stale_goals:
            bottlenecks.append(f"发现 {len(stale_goals)} 个目标超过7天未更新")

        # 找出逾期的子目标
        overdue_subgoals = []
        for goal in self.active_goals.values():
            for subgoal in goal.subgoals:
                if (subgoal.due_date and
                    datetime.now() > subgoal.due_date and
                    subgoal.status != GoalStatus.COMPLETED):
                    overdue_subgoals.append(subgoal)

        if overdue_subgoals:
            bottlenecks.append(f"发现 {len(overdue_subgoals)} 个子目标已逾期")

        return bottlenecks

    def _analyze_agent_performance(self) -> dict[str, Any]:
        """分析智能体性能

        Returns:
            智能体性能统计字典
        """
        agent_stats = {}

        for agent in ['xiaonuo', 'xiaona', 'athena', 'xiaochen']:
            agent_goals = [g for g in self.active_goals.values() if g.assigned_agent == agent]

            completed_count = len([g for g in agent_goals if g.status == GoalStatus.COMPLETED])
            in_progress_count = len([g for g in agent_goals if g.status == GoalStatus.IN_PROGRESS])

            # 计算平均进度
            total_progress = sum(self._get_goal_current_progress(g.id) for g in agent_goals)
            avg_progress = total_progress / len(agent_goals) if agent_goals else 0

            agent_stats[agent] = {
                'total_goals': len(agent_goals),
                'completed_goals': completed_count,
                'in_progress_goals': in_progress_count,
                'completion_rate': (completed_count / len(agent_goals)) * 100 if agent_goals else 0,
                'average_progress': avg_progress
            }

        return agent_stats
