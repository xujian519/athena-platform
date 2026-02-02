#!/usr/bin/env python3
"""
快速学习机制 - 公共接口
Rapid Learning - Public Interface

作者: Athena AI系统
创建时间: 2025-12-11
重构时间: 2026-01-27
版本: 2.0.0

支持在线学习、增量学习和元学习的智能体快速适应系统。
"""

from typing import Any

from .engine import RapidLearningEngine, SKLEARN_AVAILABLE, TORCH_AVAILABLE
from .learners import ActiveLearner, CurriculumScheduler, MetaLearner
from .replay_buffer import PrioritizedReplayBuffer
from .types import (
    AdaptationStrategy,
    LearningExperience,
    LearningMode,
    LearningTask,
    LearningType,
    ModelSnapshot,
)

# 创建全局快速学习引擎实例
rapid_learning_engine = RapidLearningEngine()

# 便捷函数
async def learn_from_data(
    input_data: Any,
    output_data: Any,
    task_type: str = "supervised",
    importance: float = 1.0,
) -> bool:
    """从数据学习"""
    from datetime import datetime
    import uuid

    experience = LearningExperience(
        experience_id=str(uuid.uuid4()),
        task_type=task_type,
        input_data=input_data,
        output_data=output_data,
        context={},
        reward=importance,
        timestamp=datetime.now(),
        importance=importance,
    )
    return await rapid_learning_engine.learn_from_experience(experience)


async def create_learning_task(
    task_id: str, model_type: str, target_performance: float = 0.8
) -> bool:
    """创建学习任务"""
    task = LearningTask(
        task_id=task_id,
        task_type=LearningType.SUPERVISED,
        learning_mode=LearningMode.ONLINE,
        data_source="experience_buffer",
        model_type=model_type,
        hyperparameters={},
        performance_metric="accuracy",
        target_performance=target_performance,
    )
    return await rapid_learning_engine.create_learning_task(task)


def get_learning_stats() -> dict[str, Any]:
    """获取学习统计"""
    return rapid_learning_engine.get_learning_statistics()


# 导出公共接口
__all__ = [
    # 类型
    "LearningType",
    "LearningMode",
    "AdaptationStrategy",
    "LearningExperience",
    "LearningTask",
    "ModelSnapshot",
    # 核心类
    "RapidLearningEngine",
    "PrioritizedReplayBuffer",
    "MetaLearner",
    "CurriculumScheduler",
    "ActiveLearner",
    # 全局实例和便捷函数
    "rapid_learning_engine",
    "learn_from_data",
    "create_learning_task",
    "get_learning_stats",
    # 常量
    "TORCH_AVAILABLE",
    "SKLEARN_AVAILABLE",
]
