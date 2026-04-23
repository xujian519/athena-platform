#!/usr/bin/env python3
from __future__ import annotations
"""
小诺和Athena核心模块
Xiaonuo and Athena Core Modules

这是小诺和Athena AI Agent的核心架构,基于八大功能模块:
1. 感知模块 (Perception)
2. 认知与决策层 (Cognition & Decision)
3. 记忆模块 (Memory)
4. 执行模块 (Execution)
5. 学习与适应模块 (Learning & Adaptation)
6. 通信模块 (Communication)
7. 评估与反思模块 (Evaluation & Reflection)
8. 知识库与工具库 (Knowledge & Tools)

作者: Athena AI系统
创建时间: 2025-12-04
版本: 3.0.0
"""

import asyncio
import logging
from typing import TYPE_CHECKING, Any, cast

if TYPE_CHECKING:
    from .agent.agent_factory import AgentFactory
    from .agent.athena_agent import AthenaAgent
    from .agent.xiaonuo_agent import XiaonuoAgent


# 核心模块导入
from .agent import BaseAgent

# 基础模块导入
from .base_module import BaseModule, HealthStatus, ModuleStatus

# 任务模型导入
from .task_models import (
    Task,
    TaskFactory,
    TaskPriority,
    TaskQueue,
    TaskResult,
    TaskStatus,
    TaskType,
)

# 标准化模块导入（可选，避免阻塞新模块）
try:
    from .cognition import CognitiveEngine
except ImportError:
    CognitiveEngine = None

try:
    from .communication import CommunicationEngine
except ImportError:
    CommunicationEngine = None

try:
    from .evaluation import EvaluationEngine
except ImportError:
    EvaluationEngine = None

try:
    from .execution import ExecutionEngine
except ImportError:
    ExecutionEngine = None

try:
    from .learning import LearningEngine
except ImportError:
    LearningEngine = None

try:
    from .memory import MemorySystem
except ImportError:
    MemorySystem = None

try:
    from .monitoring import MonitoringEngine
except ImportError:
    MonitoringEngine = None

# 暂时注释掉perception导入，因为存在模块导入问题
# from .perception import PerceptionEngine

try:
    from .security import SecurityEngine
except ImportError:
    SecurityEngine = None

# 创建一个临时占位符
class PerceptionEngine:
    """临时占位符类，待perception模块修复后恢复"""

    @staticmethod
    async def initialize_global() -> None:
        """初始化全局实例（占位符实现）"""
        logger.warning("⚠️ PerceptionEngine 使用占位符实现")

    @staticmethod
    async def shutdown_global() -> None:
        """关闭全局实例（占位符实现）"""
        logger.warning("⚠️ PerceptionEngine 使用占位符实现")

# 版本信息
__version__ = "3.0.0"
__author__ = "Athena AI System"
__description__ = "小诺和Athena AI Agent核心架构"

# 配置日志
logger = logging.getLogger(__name__)

# 全局实例
_agent_factory: "AgentFactory | None" = None


def get_agent_factory() -> "AgentFactory":
    """获取全局Agent工厂实例"""
    global _agent_factory
    if _agent_factory is None:
        _agent_factory = AgentFactory()
    return _agent_factory


async def create_xiaonuo_agent(config: Optional[dict[str, Any]] = None) -> "XiaonuoAgent":
    """创建小诺Agent实例"""
    factory = get_agent_factory()
    agent = await factory.create_agent("xiaonuo", config)
    return cast(XiaonuoAgent, agent)


async def create_athena_agent(config: Optional[dict[str, Any]] = None) -> "AthenaAgent":
    """创建Athena Agent实例"""
    factory = get_agent_factory()
    agent = await factory.create_agent("athena", config)
    return cast(AthenaAgent, agent)


async def initialize_core_system(config: Optional[dict[str, Any]] = None):
    """初始化核心系统"""
    logger.info("🚀 初始化小诺和Athena核心系统...")

    try:
        # 初始化各模块（添加None检查）
        if PerceptionEngine is not None:
            await PerceptionEngine.initialize_global()
        if CognitiveEngine is not None:
            await CognitiveEngine.initialize_global()
        if MemorySystem is not None:
            await MemorySystem.initialize_global()
        if ExecutionEngine is not None:
            await ExecutionEngine.initialize_global()
        if LearningEngine is not None:
            await LearningEngine.initialize_global()
        if CommunicationEngine is not None:
            await CommunicationEngine.initialize_global()
        if EvaluationEngine is not None:
            await EvaluationEngine.initialize_global()
        # KnowledgeManager暂时注释掉（类不存在）
        # await KnowledgeManager.initialize_global()
        if MonitoringEngine is not None:
            await MonitoringEngine.initialize_global()
        if SecurityEngine is not None:
            await SecurityEngine.initialize_global()

        logger.info("✅ 核心系统初始化完成")

    except Exception as e:
        logger.error(f"❌ 核心系统初始化失败: {e}")
        raise


async def shutdown_core_system():
    """关闭核心系统"""
    logger.info("🔄 关闭小诺和Athena核心系统...")

    try:
        # 关闭各模块（添加None检查）
        if PerceptionEngine is not None:
            await PerceptionEngine.shutdown_global()
        if CognitiveEngine is not None:
            await CognitiveEngine.shutdown_global()
        if MemorySystem is not None:
            await MemorySystem.shutdown_global()
        if ExecutionEngine is not None:
            await ExecutionEngine.shutdown_global()
        if LearningEngine is not None:
            await LearningEngine.shutdown_global()
        if CommunicationEngine is not None:
            await CommunicationEngine.shutdown_global()
        if EvaluationEngine is not None:
            await EvaluationEngine.shutdown_global()
        # KnowledgeManager暂时注释掉（类不存在）
        # await KnowledgeManager.shutdown_global()
        if MonitoringEngine is not None:
            await MonitoringEngine.shutdown_global()
        if SecurityEngine is not None:
            await SecurityEngine.shutdown_global()

        logger.info("✅ 核心系统已关闭")

    except Exception as e:
        logger.error(f"❌ 核心系统关闭失败: {e}")


# 导出的公共接口
__all__ = [
    "AgentFactory",
    "AthenaAgent",
    # Agent相关
    "BaseAgent",
    # 标准化模块
    "BaseModule",
    "CognitiveEngine",
    "CommunicationEngine",
    "EvaluationEngine",
    "ExecutionEngine",
    "HealthStatus",
    # KnowledgeManager暂时注释掉（类不存在）
    # "KnowledgeManager",
    "LearningEngine",
    "MemorySystem",
    "ModuleStatus",
    "MonitoringEngine",
    # 核心模块
    "PerceptionEngine",
    "SecurityEngine",
    "Task",
    "TaskFactory",
    "TaskPriority",
    "TaskQueue",
    "TaskResult",
    # "TaskStatusEnum",  # 改为TaskStatus
    "TaskStatus",
    "TaskType",
    "XiaonuoAgent",
    "__author__",
    "__description__",
    # 版本信息
    "__version__",
    "create_athena_agent",
    "create_xiaonuo_agent",
    "get_agent_factory",
    # 系统管理
    "initialize_core_system",
    "shutdown_core_system",
]

if __name__ == "__main__":
    # 测试核心系统
    async def main():
        logger.info("🤖 小诺和Athena核心系统测试")
        logger.info(str("=" * 50))

        try:
            # 初始化系统
            await initialize_core_system()

            # 创建小诺Agent
            xiaonuo = await create_xiaonuo_agent()
            logger.info(f"✅ 小诺Agent创建成功: {xiaonuo.agent_id}")

            # 创建Athena Agent
            athena = await create_athena_agent()
            logger.info(f"✅ Athena Agent创建成功: {athena.agent_id}")

            # 获取系统状态
            factory = get_agent_factory()
            status = await factory.get_system_status()
            logger.info("\n📊 系统状态:")
            logger.info(f"  Agent数量: {status['agent_count']}")
            logger.info(f"  模块状态: {status['modules']}")

            await shutdown_core_system()
            logger.info("\n✅ 测试完成")

        except Exception as e:
            logger.info(f"❌ 测试失败: {e}")
            await shutdown_core_system()

    asyncio.run(main())
