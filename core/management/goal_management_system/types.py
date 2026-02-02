#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
目标管理系统 - 类型定义
Goal Management System - Type Definitions

作者: Athena AI系统
创建时间: 2025-12-04
重构时间: 2026-01-27
版本: 2.0.0
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Optional


class GoalStatus(Enum):
    """目标状态

    状态说明:
    - DRAFT: 草稿状态,目标刚创建未激活
    - ACTIVE: 活跃状态,目标已激活等待执行
    - IN_PROGRESS: 进行中,目标正在执行
    - COMPLETED: 已完成,目标已达成
    - PAUSED: 暂停,目标暂时停止执行
    - CANCELLED: 已取消,目标被取消不再执行
    - FAILED: 失败,目标执行失败
    """
    DRAFT = "draft"
    ACTIVE = "active"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    PAUSED = "paused"
    CANCELLED = "cancelled"
    FAILED = "failed"


class GoalPriority(Enum):
    """目标优先级

    优先级说明:
    - LOW (1): 低优先级,可延后处理
    - MEDIUM (2): 中等优先级,正常处理
    - HIGH (3): 高优先级,优先处理
    - CRITICAL (4): 关键优先级,紧急处理
    - URGENT (5): 紧急优先级,最高优先级
    """
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4
    URGENT = 5


class MetricType(Enum):
    """指标类型

    类型说明:
    - PERCENTAGE: 百分比类型,如完成率、增长率等
    - COUNTER: 计数器类型,如任务数、次数等
    - BOOLEAN: 布尔类型,是否完成、是否通过等
    - TIME_BASED: 基于时间的指标,如持续时间、剩余时间等
    - QUALITY_SCORE: 质量评分,如评分、等级等
    """
    PERCENTAGE = "percentage"
    COUNTER = "counter"
    BOOLEAN = "boolean"
    TIME_BASED = "time_based"
    QUALITY_SCORE = "quality_score"


@dataclass
class ProgressMetric:
    """进度指标

    用于跟踪目标或子目标的进度指标。

    Attributes:
        name: 指标名称
        metric_type: 指标类型
        target_value: 目标值
        current_value: 当前值
        unit: 单位
        description: 描述
        weight: 权重,用于综合计算时使用
    """
    name: str
    metric_type: MetricType
    target_value: Any
    current_value: Any = 0
    unit: str = ""
    description: str = ""
    weight: float = 1.0


@dataclass
class SubGoal:
    """子目标

    目标的子任务,用于分解复杂目标。

    Attributes:
        id: 子目标ID
        title: 标题
        description: 描述
        metrics: 进度指标列表
        status: 状态
        created_at: 创建时间
        updated_at: 更新时间
        due_date: 到期日期
        assigned_agent: 分配的智能体
    """
    id: str
    title: str
    description: str
    metrics: list[ProgressMetric] = field(default_factory=list)
    status: GoalStatus = GoalStatus.DRAFT
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    due_date: datetime | None = None
    assigned_agent: str | None = None


@dataclass
class Goal:
    """目标

    主要的目标对象,包含子目标和进度指标。

    Attributes:
        id: 目标ID
        title: 标题
        description: 描述
        priority: 优先级
        metrics: 进度指标列表
        subgoals: 子目标列表
        status: 状态
        created_at: 创建时间
        updated_at: 更新时间
        due_date: 到期日期
        assigned_agent: 分配的智能体(默认xiaonuo)
        context: 上下文信息
        tags: 标签列表
    """
    id: str
    title: str
    description: str
    priority: GoalPriority
    metrics: list[ProgressMetric] = field(default_factory=list)
    subgoals: list[SubGoal] = field(default_factory=list)
    status: GoalStatus = GoalStatus.DRAFT
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    due_date: datetime | None = None
    assigned_agent: str = "xiaonuo"  # 默认分配给小诺
    context: dict[str, Any] = field(default_factory=dict)
    tags: list[str] = field(default_factory=list)


@dataclass
class ProgressReport:
    """进度报告

    记录目标的进度状态。

    Attributes:
        goal_id: 目标ID
        timestamp: 报告时间戳
        overall_progress: 整体进度(0-100)
        subgoal_progress: 子目标进度字典 {subgoal_id: progress}
        metrics_status: 指标状态字典 {metric_name: status_info}
        issues: 问题列表
        recommendations: 建议列表
        estimated_completion: 预计完成时间
        confidence_level: 置信度(0-1)
    """
    goal_id: str
    timestamp: datetime
    overall_progress: float  # 0-100
    subgoal_progress: dict[str, float]
    metrics_status: dict[str, dict[str, Any]]
    issues: list[str] = field(default_factory=list)
    recommendations: list[str] = field(default_factory=list)
    estimated_completion: datetime | None = None
    confidence_level: float = 1.0  # 0-1
