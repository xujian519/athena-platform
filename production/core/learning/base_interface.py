#!/usr/bin/env python3
"""
学习引擎统一接口
Learning Engine Unified Interface

定义所有学习引擎必须遵循的统一接口，确保：
1. 接口一致性
2. 可替换性
3. 可测试性

作者: Athena平台团队
版本: 1.0.0
创建时间: 2026-01-28
"""

from __future__ import annotations
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class LearningStrategy(str, Enum):
    """学习策略类型"""

    SUPERVISED = "supervised"  # 监督学习
    REINFORCEMENT = "reinforcement"  # 强化学习
    UNSUPERVISED = "unsupervised"  # 无监督学习
    META_LEARNING = "meta_learning"  # 元学习
    TRANSFER = "transfer"  # 迁移学习
    HYBRID = "hybrid"  # 混合学习
    RAPID = "rapid"  # 快速学习
    ADAPTIVE = "adaptive"  # 自适应学习


class AdaptationMode(str, Enum):
    """适应模式"""

    REACTIVE = "reactive"  # 响应式适应（被动）
    PROACTIVE = "proactive"  # 主动适应
    ON_DEMAND = "on_demand"  # 按需适应
    SCHEDULED = "scheduled"  # 定时适应


@dataclass
class LearningExperience:
    """学习经验（统一数据结构）"""

    experience_id: str
    task: str
    action: str
    result: Any
    reward: float
    context: dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class LearningResult:
    """学习结果（统一数据结构）"""

    success: bool
    strategy_used: LearningStrategy
    performance_score: float
    adaptation_applied: bool
    insights: list[str] = field(default_factory=list)
    recommendations: list[str] = field(default_factory=list)
    metrics: dict[str, Any] = field(default_factory=dict)
    error: str | None = None


@dataclass
class LearningMetrics:
    """学习指标（统一数据结构）"""

    total_experiences: int = 0
    successful_experiences: int = 0
    average_reward: float = 0.0
    learning_rate: float = 0.01
    adaptation_count: int = 0
    pattern_discovered: int = 0
    last_update: datetime | None = None


class BaseLearningEngine(ABC):
    """
    学习引擎抽象基类

    所有学习引擎必须实现此接口，确保统一的行为和数据格式。
    """

    def __init__(self, agent_id: str, config: dict | None = None):
        """
        初始化学习引擎

        Args:
            agent_id: 智能体ID
            config: 配置参数
        """
        self.agent_id = agent_id
        self.config = config or {}
        self._initialized = False
        self._started = False
        self.logger = logging.getLogger(f"{__name__}.{agent_id}")

    @abstractmethod
    async def initialize(self) -> bool:
        """
        初始化学习引擎

        Returns:
            是否初始化成功
        """
        pass

    @abstractmethod
    async def start(self) -> bool:
        """
        启动学习引擎

        Returns:
            是否启动成功
        """
        pass

    @abstractmethod
    async def stop(self) -> bool:
        """
        停止学习引擎

        Returns:
            是否停止成功
        """
        pass

    @abstractmethod
    async def shutdown(self) -> bool:
        """
        关闭学习引擎

        Returns:
            是否关闭成功
        """
        pass

    @abstractmethod
    async def health_check(self) -> bool:
        """
        健康检查

        Returns:
            是否健康
        """
        pass

    @abstractmethod
    async def process_experience(
        self, experience_data: dict[str, Any] | LearningExperience
    ) -> LearningResult:
        """
        处理学习经验

        Args:
            experience_data: 经验数据

        Returns:
            学习结果
        """
        pass

    @abstractmethod
    async def get_statistics(self) -> dict[str, Any]:
        """
        获取学习统计信息

        Returns:
            统计信息字典
        """
        pass

    @abstractmethod
    async def adapt_strategy(
        self, current_performance: float, target_performance: float
    ) -> bool:
        """
        适应策略调整

        Args:
            current_performance: 当前性能
            target_performance: 目标性能

        Returns:
            是否调整成功
        """
        pass

    # 可选方法（子类可以选择性实现）

    async def get_strategy(self, task: str) -> dict[str, Any]:
        """
        获取任务策略

        Args:
            task: 任务名称

        Returns:
            策略信息
        """
        return {
            "task": task,
            "strategy": "default",
            "confidence": 0.0,
            "reason": "未实现策略获取",
        }

    async def save_state(self) -> bool:
        """
        保存状态

        Returns:
            是否保存成功
        """
        self.logger.warning("save_state未实现")
        return False

    async def load_state(self) -> bool:
        """
        加载状态

        Returns:
            是否加载成功
        """
        self.logger.warning("load_state未实现")
        return False

    def _validate_experience(self, experience: dict[str, Any] | LearningExperience) -> None:
        """
        验证学习经验数据的有效性

        Args:
            experience: 要验证的经验数据

        Raises:
            ValueError: 如果数据无效
            TypeError: 如果数据类型错误
        """

        # 转换为字典进行验证
        if isinstance(experience, LearningExperience):
            exp_dict = {
                "experience_id": experience.experience_id,
                "task": experience.task,
                "action": experience.action,
                "result": experience.result,
                "reward": experience.reward,
                "context": experience.context,
            }
        else:
            exp_dict = experience

        # 验证必需字段
        required_fields = ["task", "action", "result"]
        missing_fields = [f for f in required_fields if f not in exp_dict or exp_dict[f] is None]
        if missing_fields:
            raise ValueError(f"经验数据缺少必需字段: {', '.join(missing_fields)}")

        # 验证reward范围
        if "reward" in exp_dict:
            reward = exp_dict["reward"]
            if not isinstance(reward, (int, float)):
                raise TypeError(f"reward必须是数字类型，收到: {type(reward)}")
            if not (-1.0 <= reward <= 1.0):
                raise ValueError(f"reward值必须在[-1.0, 1.0]范围内，收到: {reward}")

        # 验证task类型
        task = exp_dict.get("task", "")
        if not isinstance(task, str) or len(task) == 0:
            raise ValueError("task必须是非空字符串")

        # 验证action类型
        action = exp_dict.get("action", "")
        if not isinstance(action, str) or len(action) == 0:
            raise ValueError("action必须是非空字符串")

        # 验证context是字典
        context = exp_dict.get("context", {})
        if not isinstance(context, dict):
            raise TypeError(f"context必须是字典类型，收到: {type(context)}")

        # 验证result不为None（对于成功的经验）
        result = exp_dict.get("result")
        if result is None:
            raise ValueError("result不能为None")

    def _validate_config(self, config: dict[str, Any] | None) -> dict[str, Any]:
        """
        验证并规范化配置参数

        Args:
            config: 配置参数字典

        Returns:
            验证后的配置字典

        Raises:
            ConfigurationError: 如果配置无效
        """
        from .exceptions import ConfigurationError

        if config is None:
            return {}

        if not isinstance(config, dict):
            raise ConfigurationError(
                "CONFIG_INVALID", f"config必须是字典类型，收到: {type(config)}"
            )

        # 验证学习率
        if "learning_rate" in config:
            lr = config["learning_rate"]
            if not isinstance(lr, (int, float)) or not (0 < lr <= 1):
                raise ConfigurationError(
                    "CONFIG_INVALID", f"learning_rate必须在(0, 1]范围内，收到: {lr}"
                )

        # 验证batch_size
        if "batch_size" in config:
            batch_size = config["batch_size"]
            if not isinstance(batch_size, int) or batch_size < 1:
                raise ConfigurationError(
                    "CONFIG_INVALID", f"batch_size必须是正整数，收到: {batch_size}"
                )

        # 验证temperature
        if "temperature" in config:
            temp = config["temperature"]
            if not isinstance(temp, (int, float)) or not (0 <= temp <= 2):
                raise ConfigurationError(
                    "CONFIG_INVALID", f"temperature必须在[0, 2]范围内，收到: {temp}"
                )

        return config


class LearningEngineRegistry:
    """
    学习引擎注册表

    管理所有可用的学习引擎实现，支持动态注册和获取。
    """

    _engines: dict[str, type[BaseLearningEngine]] = {}

    @classmethod
    def register(cls, name: str, engine_class: type[BaseLearningEngine]) -> None:
        """注册学习引擎"""
        if not issubclass(engine_class, BaseLearningEngine):
            raise TypeError(f"{engine_class} 必须继承 BaseLearningEngine")

        cls._engines[name] = engine_class
        logger.info(f"✅ 注册学习引擎: {name}")

    @classmethod
    def get(cls, name: str) -> type[BaseLearningEngine] | None:
        """获取学习引擎类"""
        return cls._engines.get(name)

    @classmethod
    def list_engines(cls) -> list[str]:
        """列出所有已注册的引擎"""
        return list(cls._engines.keys())

    @classmethod
    def create_engine(
        cls, name: str, agent_id: str, config: dict | None = None
    ) -> BaseLearningEngine | None:
        """创建学习引擎实例"""
        engine_class = cls.get(name)
        if engine_class:
            return engine_class(agent_id, config)

        logger.error(f"未找到学习引擎: {name}")
        return None


def create_learning_engine(
    engine_type: str,
    agent_id: str,
    config: dict | None = None,
) -> BaseLearningEngine:
    """
    工厂函数：创建学习引擎

    Args:
        engine_type: 引擎类型
        agent_id: 智能体ID
        config: 配置参数

    Returns:
        学习引擎实例

    Raises:
        ValueError: 如果引擎类型不存在
    """
    engine = LearningEngineRegistry.create_engine(engine_type, agent_id, config)

    if engine is None:
        available = ", ".join(LearningEngineRegistry.list_engines())
        raise ValueError(
            f"未知的引擎类型: {engine_type}. "
            f"可用类型: {available or '无'}"
        )

    return engine


# 为保持兼容性，提供别名
BaseLearningInterface = BaseLearningEngine


__all__ = [
    # 枚举
    "LearningStrategy",
    "AdaptationMode",
    # 数据类
    "LearningExperience",
    "LearningResult",
    "LearningMetrics",
    # 基类
    "BaseLearningEngine",
    "BaseLearningInterface",  # 别名
    # 注册表
    "LearningEngineRegistry",
    "create_learning_engine",
]
