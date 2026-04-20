#!/usr/bin/env python3
"""Coordinator调度策略

作者: Athena平台团队
创建时间: 2026-04-20
版本: 1.0.0

提供多种任务调度策略:
- 轮询调度 (RoundRobin)
- 最少负载调度 (LeastLoaded)
- 优先级调度 (Priority)
- 加权调度 (Weighted)
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from typing import Any

from .base import AgentInfo, TaskAssignment

logger = logging.getLogger(__name__)


class SchedulingStrategy(ABC):
    """调度策略抽象基类"""

    @abstractmethod
    def select_agent(
        self,
        agents: list[AgentInfo],
        task: TaskAssignment,
    ) -> AgentInfo | None:
        """选择Agent处理任务

        Args:
            agents: 候选Agent列表
            task: 任务分配对象

        Returns:
            AgentInfo | None: 选中的Agent
        """
        pass

    @abstractmethod
    def get_name(self) -> str:
        """获取策略名称"""
        pass


class RoundRobinStrategy(SchedulingStrategy):
    """轮询调度策略

    按顺序依次选择Agent，确保负载均匀分配。
    """

    def __init__(self):
        self._last_index = -1

    def select_agent(
        self,
        agents: list[AgentInfo],
        task: TaskAssignment,
    ) -> AgentInfo | None:
        """选择下一个Agent"""
        if not agents:
            return None

        # 过滤可用Agent
        available = [
            a for a in agents if a.can_handle_task(task.task_type)
        ]
        if not available:
            return None

        # 轮询选择
        self._last_index = (self._last_index + 1) % len(available)
        return available[self._last_index]

    def get_name(self) -> str:
        return "round_robin"


class LeastLoadedStrategy(SchedulingStrategy):
    """最少负载调度策略

    选择当前任务数最少的Agent。
    """

    def select_agent(
        self,
        agents: list[AgentInfo],
        task: TaskAssignment,
    ) -> AgentInfo | None:
        """选择负载最少的Agent"""
        if not agents:
            return None

        # 过滤可用Agent
        available = [
            a for a in agents if a.can_handle_task(task.task_type)
        ]
        if not available:
            return None

        # 选择当前任务最少的
        return min(available, key=lambda a: a.current_tasks)

    def get_name(self) -> str:
        return "least_loaded"


class PriorityStrategy(SchedulingStrategy):
    """优先级调度策略

    优先选择高优先级的Agent处理任务。
    """

    def select_agent(
        self,
        agents: list[AgentInfo],
        task: TaskAssignment,
    ) -> AgentInfo | None:
        """选择最高优先级的可用Agent"""
        if not agents:
            return None

        # 过滤可用Agent
        available = [
            a for a in agents if a.can_handle_task(task.task_type)
        ]
        if not available:
            return None

        # 按Agent优先级排序（高优先级在前）
        return max(available, key=lambda a: a.priority)

    def get_name(self) -> str:
        return "priority"


class WeightedStrategy(SchedulingStrategy):
    """加权调度策略

    根据Agent的权重（如性能、容量）进行调度。
    """

    def __init__(self, weight_key: str = "weight"):
        """初始化加权策略

        Args:
            weight_key: 元数据中权重字段的键名
        """
        self.weight_key = weight_key

    def select_agent(
        self,
        agents: list[AgentInfo],
        task: TaskAssignment,
    ) -> AgentInfo | None:
        """根据权重选择Agent"""
        if not agents:
            return None

        # 过滤可用Agent并获取权重
        available = []
        for agent in agents:
            if agent.can_handle_task(task.task_type):
                weight = agent.metadata.get(self.weight_key, 1.0)
                available.append((agent, weight))

        if not available:
            return None

        # 选择权重最高的Agent
        return max(available, key=lambda x: x[1])[0]

    def get_name(self) -> str:
        return "weighted"


class StrategyFactory:
    """调度策略工厂"""

    _strategies: dict[str, type[SchedulingStrategy]] = {
        "round_robin": RoundRobinStrategy,
        "least_loaded": LeastLoadedStrategy,
        "priority": PriorityStrategy,
        "weighted": WeightedStrategy,
    }

    @classmethod
    def create_strategy(
        cls,
        strategy_type: str,
        **kwargs: Any,
    ) -> SchedulingStrategy:
        """创建调度策略

        Args:
            strategy_type: 策略类型
            **kwargs: 策略参数

        Returns:
            SchedulingStrategy: 策略实例

        Raises:
            ValueError: 未知策略类型
        """
        strategy_class = cls._strategies.get(strategy_type.lower())
        if not strategy_class:
            raise ValueError(f"未知的调度策略: {strategy_type}")

        return strategy_class(**kwargs)

    @classmethod
    def register_strategy(
        cls,
        name: str,
        strategy_class: type[SchedulingStrategy],
    ) -> None:
        """注册自定义调度策略

        Args:
            name: 策略名称
            strategy_class: 策略类
        """
        cls._strategies[name.lower()] = strategy_class
        logger.info(f"注册调度策略: {name}")

    @classmethod
    def get_available_strategies(cls) -> list[str]:
        """获取可用的调度策略列表"""
        return list(cls._strategies.keys())
