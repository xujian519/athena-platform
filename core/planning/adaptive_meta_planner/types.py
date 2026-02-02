#!/usr/bin/env python3
"""
自适应元规划器 - 数据类型
Adaptive Meta Planner - Data Types

作者: Athena平台团队
创建时间: 2026-01-20
重构时间: 2026-01-26
版本: 2.0.0
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from ..models import ComplexityLevel, StrategyType, Task
from .constants import WORKFLOW_EXPIRY_DAYS


logger = logging.getLogger(__name__)


@dataclass
class StrategyPerformance:
    """策略性能统计"""

    strategy: StrategyType
    task_type: str
    complexity: ComplexityLevel

    # 统计数据
    total_executions: int = 0
    successful_executions: int = 0
    total_execution_time: float = 0.0
    total_quality_score: float = 0.0

    @property
    def success_rate(self) -> float:
        """成功率"""
        if self.total_executions == 0:
            return 0.0
        return self.successful_executions / self.total_executions

    @property
    def avg_execution_time(self) -> float:
        """平均执行时间"""
        if self.total_executions == 0:
            return 0.0
        return self.total_execution_time / self.total_executions

    @property
    def avg_quality_score(self) -> float:
        """平均质量分数"""
        if self.total_executions == 0:
            return 0.0
        return self.total_quality_score / self.total_executions

    def update(self, success: bool, execution_time: float, quality_score: float) -> None:
        """更新性能统计"""
        self.total_executions += 1
        if success:
            self.successful_executions += 1
        self.total_execution_time += execution_time
        self.total_quality_score += quality_score


@dataclass
class WorkflowPattern:
    """工作流模式"""

    pattern_id: str
    name: str
    task_type: str
    description: str
    steps: list[dict[str, Any]]
    success_rate: float
    avg_execution_time: float
    usage_count: int
    created_at: datetime = field(default_factory=datetime.now)
    last_used: datetime | None = None
    keywords: list[str] = field(default_factory=list)
    complexity: ComplexityLevel = ComplexityLevel.MEDIUM

    def calculate_similarity(self, task: Task) -> float:
        """
        计算与任务的相似度

        Args:
            task: 任务对象

        Returns:
            float: 相似度分数 (0-1)
        """
        score = 0.0

        # 1. 任务类型匹配 (40%)
        if self.task_type == task.task_type:
            score += 0.4

        # 2. 关键词匹配 (30%)
        description_lower = task.description.lower()
        matched_keywords = sum(1 for kw in self.keywords if kw.lower() in description_lower)
        if self.keywords:
            keyword_score = matched_keywords / len(self.keywords)
            score += keyword_score * 0.3

        # 3. 长度相似度 (15%)
        desc_length = len(task.description)
        pattern_length = len(self.description)
        length_diff = abs(desc_length - pattern_length) / max(desc_length, pattern_length, 1)
        score += (1 - min(length_diff, 1.0)) * 0.15

        # 4. 领域匹配 (15%)
        if task.domain and self.task_type.lower() in task.domain.lower():
            score += 0.15

        return min(score, 1.0)

    def is_expired(self, max_days: int = WORKFLOW_EXPIRY_DAYS) -> bool:
        """检查模式是否过期"""
        if self.last_used is None:
            return (datetime.now() - self.created_at).days > max_days
        return (datetime.now() - self.last_used).days > max_days

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "pattern_id": self.pattern_id,
            "name": self.name,
            "task_type": self.task_type,
            "description": self.description,
            "success_rate": self.success_rate,
            "avg_execution_time": self.avg_execution_time,
            "usage_count": self.usage_count,
            "complexity": self.complexity.value,
            "keywords": self.keywords,
            "created_at": self.created_at.isoformat(),
            "last_used": self.last_used.isoformat() if self.last_used else None,
        }
