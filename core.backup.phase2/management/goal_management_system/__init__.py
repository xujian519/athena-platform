#!/usr/bin/env python3
from __future__ import annotations
"""
目标管理系统 - 公共接口
Goal Management System - Public Interface

作者: Athena AI系统
创建时间: 2025-12-04
重构时间: 2026-01-27
版本: 2.0.0

提供目标管理、进度跟踪、智能分析和报告功能。
"""

from .analyzers import GoalOptimizer, NotificationSystem, ProgressAnalyzer
from .decomposer import GoalDecomposer
from .manager import GoalManagementSystem
from .types import (
    Goal,
    GoalPriority,
    GoalStatus,
    MetricType,
    ProgressMetric,
    ProgressReport,
    SubGoal,
)


# 使用示例
async def main():
    """使用示例"""
    goal_manager = GoalManagementSystem()

    # 示例1: 创建专利检索目标
    print("=" * 50)
    print("示例1: 创建专利检索目标")
    print("=" * 50)

    goal1 = goal_manager.create_goal({
        'title': '完成AI相关专利检索分析',
        'description': '检索和分析人工智能领域的专利技术,生成综合报告',
        'priority': 4,  # HIGH
        'due_date': 7,  # 7天后
        'context': {
            'user_domain': 'AI研究',
            'search_scope': 'global',
            'language': 'chinese'
        }
    })

    # 示例2: 更新目标进度
    print("\n" + "=" * 50)
    print("示例2: 更新目标进度")
    print("=" * 50)

    goal_manager.update_goal_progress(goal1.id, {
        'subgoal_updates': {
            goal1.subgoals[0].id: {
                'status': 'completed',
                'metrics': [
                    {'name': 'completion_status', 'value': True},
                    {'name': 'quality_rating', 'value': 85}
                ]
            },
            goal1.subgoals[1].id: {
                'status': 'in_progress',
                'metrics': [
                    {'name': 'completion_status', 'value': False},
                    {'name': 'quality_rating', 'value': 60}
                ]
            }
        },
        'metric_updates': {
            'subgoal_completion_rate': 25
        }
    })

    # 示例3: 获取目标仪表板
    print("\n" + "=" * 50)
    print("示例3: 目标仪表板")
    print("=" * 50)

    dashboard = goal_manager.get_goal_dashboard()
    print("📊 总体统计:")
    print(f"   总目标数: {dashboard['summary']['total_goals']}")
    print(f"   进行中: {dashboard['summary']['in_progress_goals']}")
    print(f"   已完成: {dashboard['summary']['completed_goals']}")

    # 示例4: 生成目标洞察
    print("\n" + "=" * 50)
    print("示例4: 目标洞察")
    print("=" * 50)

    insights = goal_manager.generate_goal_insights()
    print("💡 智能洞察:")
    for recommendation in insights['recommendations']:
        print(f"   - {recommendation}")


# 导出公共类
__all__ = [
    # 类型定义
    "GoalStatus",
    "GoalPriority",
    "MetricType",
    "Goal",
    "SubGoal",
    "ProgressMetric",
    "ProgressReport",
    # 主管理类
    "GoalManagementSystem",
    # 别名 (向后兼容)
    "GoalManager",
    # 分析器
    "ProgressAnalyzer",
    "GoalOptimizer",
    "NotificationSystem",
    # 分解器
    "GoalDecomposer",
    # 示例函数
    "main",
]

# 向后兼容别名
GoalManager = GoalManagementSystem
