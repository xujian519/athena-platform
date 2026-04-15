#!/usr/bin/env python3
"""
Agent核心模块
Agent Core Module

包含小诺和Athena的基础Agent类和具体实现。

作者: Athena AI系统
创建时间: 2025-12-04
版本: 3.0.0
"""

from __future__ import annotations
import asyncio
import logging
import uuid
from abc import ABC, abstractmethod
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Union, cast

logger = logging.getLogger(__name__)


class AgentState(Enum):
    """Agent状态"""

    INITIALIZING = "initializing"
    IDLE = "idle"
    PROCESSING = "processing"
    LEARNING = "learning"
    COMMUNICATING = "communicating"
    ERROR = "error"
    SHUTDOWN = "shutdown"


class AgentType(Enum):
    """
    Agent类型(整合后状态)

    整合说明(2026-01-22):
    - XIAONUO: 整合了Xiaochen媒体运营能力的统一智能体
    - ATHENA: 整合了Xiaona法律能力和Yunxi IP管理能力的统一智能体
    - CUSTOM: 自定义智能体类型

    已废弃的类型(仅保留历史记录):
    - XIAONA: 已整合到ATHENA
    - YUNXI: 已整合到ATHENA
    - XIAOCHEN: 已整合到XIAONUO
    """

    XIAONUO = "xiaonuo"  # 整合了Xiaochen的媒体运营能力
    ATHENA = "athena"  # 整合了Xiaona的法律能力的统一智能体
    CUSTOM = "custom"


@dataclass
class AgentProfile:
    """Agent档案"""

    agent_id: str
    agent_type: AgentType
    name: str
    description: str
    personality: dict[str, Any]
    capabilities: list[str]
    preferences: dict[str, Any]
    created_at: datetime


class BaseAgent(ABC):
    """基础Agent类"""

    # 声明引擎类型(将在_initialize_modules中初始化)
    perception_engine: Any
    cognitive_engine: Any
    memory_system: Any
    execution_engine: Any
    learning_engine: Any
    communication_engine: Any
    evaluation_engine: Any
    knowledge_manager: Any

    def __init__(self, agent_type: AgentType, config: dict[str, Any] | None = None):
        self.agent_id = str(uuid.uuid4())
        self.agent_type = agent_type
        self.config = config or {}
        self.state = AgentState.INITIALIZING
        self.profile: AgentProfile | None = None
        self.created_at = datetime.now()

        # 核心模块引用(初始化为None,后续在_initialize_modules中设置)
        self.perception_engine = None
        self.cognitive_engine = None
        self.memory_system = None
        self.execution_engine = None
        self.learning_engine = None
        self.communication_engine = None
        self.evaluation_engine = None
        self.knowledge_manager = None

        # 事件回调
        self.callbacks: dict[str, list[Callable]] = {}

        logger.info(f"🤖 创建Agent: {self.agent_id} ({agent_type.value})")

    async def initialize(self):
        """初始化Agent"""
        logger.info(f"🚀 初始化Agent: {self.agent_id}")

        try:
            self.state = AgentState.INITIALIZING

            # 设置Agent档案
            await self._setup_profile()

            # 初始化核心模块
            await self._initialize_modules()

            # 注册回调
            await self._register_callbacks()

            self.state = AgentState.IDLE
            logger.info(f"✅ Agent初始化完成: {self.agent_id}")

        except Exception as e:
            self.state = AgentState.ERROR
            logger.error(f"❌ Agent初始化失败 {self.agent_id}: {e}")
            raise

    @abstractmethod
    async def _setup_profile(self):
        """设置Agent档案"""
        pass

    async def _initialize_modules(self):
        """初始化核心模块"""
        from ..cognition import CognitiveEngine
        from ..communication.communication_engine import CommunicationEngine
        from ..evaluation.evaluation_engine import EvaluationEngine
        from ..execution.execution_engine import ExecutionEngine
        from ..knowledge import KnowledgeManager
        from ..learning.learning_engine import LearningEngine
        from ..memory import MemorySystem
        from ..perception import PerceptionEngine

        # 初始化各模块实例
        self.perception_engine = PerceptionEngine(self.agent_id, self.config.get("perception", {}))
        self.cognitive_engine = CognitiveEngine(self.agent_id, self.config.get("cognition", {}))
        self.memory_system = MemorySystem(self.agent_id, self.config.get("memory", {}))
        self.execution_engine = ExecutionEngine(self.agent_id, self.config.get("execution", {}))
        self.learning_engine = LearningEngine(self.agent_id, self.config.get("learning", {}))
        self.communication_engine = CommunicationEngine(
            self.agent_id, self.config.get("communication", {})
        )
        self.evaluation_engine = EvaluationEngine(self.agent_id, self.config.get("evaluation", {}))
        self.knowledge_manager = KnowledgeManager(self.agent_id, self.config.get("knowledge", {}))

        # 初始化所有模块
        await self.perception_engine.initialize()
        await self.cognitive_engine.initialize()
        await self.memory_system.initialize()
        await self.execution_engine.initialize()
        # 传递知识管理器给学习引擎
        await self.learning_engine.initialize(knowledge_manager=self.knowledge_manager)
        await self.communication_engine.initialize()
        await self.evaluation_engine.initialize()
        await self.knowledge_manager.initialize()

    async def _register_callbacks(self):
        """注册回调函数"""
        # 确保引擎已初始化
        if (
            self.perception_engine is None
            or self.cognitive_engine is None
            or self.memory_system is None
        ):
            raise RuntimeError("引擎未初始化,请先调用 _initialize_modules")

        # 注册模块间通信回调
        self.perception_engine.register_callback("input_processed", self._on_input_processed)
        self.cognitive_engine.register_callback("decision_made", self._on_decision_made)
        self.memory_system.register_callback("memory_updated", self._on_memory_updated)
        if self.execution_engine:
            self.execution_engine.register_callback("task_completed", self._on_task_completed)
        if self.learning_engine:
            self.learning_engine.register_callback(
                "learning_completed", self._on_learning_completed
            )
        if self.communication_engine:
            self.communication_engine.register_callback("message_sent", self._on_message_sent)
        if self.evaluation_engine:
            self.evaluation_engine.register_callback(
                "evaluation_completed", self._on_evaluation_completed
            )

    async def process_input(self, input_data: Any, input_type: str = "text") -> dict[str, Any]:
        """处理输入"""
        if self.state != AgentState.IDLE:
            raise RuntimeError(f"Agent不在空闲状态,当前状态: {self.state}")

        try:
            self.state = AgentState.PROCESSING
            logger.info(f"📥 处理输入: {input_type}")

            # 感知处理
            perception_result = await self.perception_engine.process(input_data, input_type)

            # 认知处理
            cognition_result = await self.cognitive_engine.process(perception_result)

            # 决策执行
            if cognition_result.get("action_required", False):
                execution_result = await self.execution_engine.execute(cognition_result["actions"])
                cognition_result["execution_result"] = execution_result

            # 学习和评估
            try:
                if hasattr(self.learning_engine, "learn_from_interaction"):
                    await self.learning_engine.learn_from_interaction(input_data, cognition_result)
                else:
                    await self.learning_engine.process_experience(
                        {
                            "input": input_data,
                            "cognition": cognition_result,
                            "timestamp": datetime.now().isoformat(),
                        }
                    )
            except Exception as e:
                logger.warning(f"⚠️ 学习引擎处理失败: {e}")

            try:
                evaluation_result = await self.evaluation_engine.evaluate_interaction(
                    input_data, cognition_result
                )
            except Exception as e:
                logger.warning(f"⚠️ 评估引擎处理失败: {e}")
                evaluation_result = {"status": "skipped", "reason": str(e)}

            self.state = AgentState.IDLE

            return {
                "agent_id": self.agent_id,
                "perception": perception_result,
                "cognition": cognition_result,
                "evaluation": evaluation_result,
                "timestamp": datetime.now().isoformat(),
            }

        except Exception as e:
            self.state = AgentState.ERROR
            logger.error(f"❌ 输入处理失败 {self.agent_id}: {e}")
            raise

    async def communicate(self, message: str, channel: str = "default") -> dict[str, Any]:
        """通信交互"""
        try:
            self.state = AgentState.COMMUNICATING

            result = await self.communication_engine.send_message(message, channel)

            self.state = AgentState.IDLE
            return result

        except Exception as e:
            self.state = AgentState.ERROR
            logger.error(f"❌ 通信失败 {self.agent_id}: {e}")
            raise

    async def learn(self, experience: dict[str, Any]) -> dict[str, Any]:
        """学习体验"""
        try:
            self.state = AgentState.LEARNING

            result = await self.learning_engine.process_experience(experience)

            self.state = AgentState.IDLE
            return result

        except Exception as e:
            self.state = AgentState.ERROR
            logger.error(f"❌ 学习失败 {self.agent_id}: {e}")
            raise

    async def get_status(self) -> dict[str, Any]:
        """获取Agent状态"""
        return {
            "agent_id": self.agent_id,
            "agent_type": self.agent_type.value,
            "state": self.state.value,
            "created_at": self.created_at.isoformat(),
            "profile": self.profile.__dict__ if self.profile else None,
            "modules": {
                "perception": self.perception_engine is not None,
                "cognition": self.cognitive_engine is not None,
                "memory": self.memory_system is not None,
                "execution": self.execution_engine is not None,
                "learning": self.learning_engine is not None,
                "communication": self.communication_engine is not None,
                "evaluation": self.evaluation_engine is not None,
                "knowledge": self.knowledge_manager is not None,
            },
        }

    # 回调处理方法
    async def _on_input_processed(self, data: dict[str, Any]):
        """输入处理完成回调"""
        logger.debug(f"输入处理完成: {data}")

    async def _on_decision_made(self, data: dict[str, Any]):
        """决策完成回调"""
        logger.debug(f"决策完成: {data}")

    async def _on_memory_updated(self, data: dict[str, Any]):
        """记忆更新回调"""
        logger.debug(f"记忆更新: {data}")

    async def _on_task_completed(self, data: dict[str, Any]):
        """任务完成回调"""
        logger.debug(f"任务完成: {data}")

    async def _on_learning_completed(self, data: dict[str, Any]):
        """学习完成回调"""
        logger.debug(f"学习完成: {data}")

    async def _on_message_sent(self, data: dict[str, Any]):
        """消息发送完成回调"""
        logger.debug(f"消息发送完成: {data}")

    async def _on_evaluation_completed(self, data: dict[str, Any]):
        """评估完成回调"""
        logger.debug(f"评估完成: {data}")

    def register_callback(self, event: str, callback: Callable) -> Any:
        """注册回调函数"""
        if event not in self.callbacks:
            self.callbacks[event] = []
        self.callbacks[event].append(callback)

    async def trigger_callbacks(self, event: str, data: Any):
        """触发回调函数"""
        if event in self.callbacks:
            for callback in self.callbacks[event]:
                try:
                    if asyncio.iscoroutinefunction(callback):
                        await callback(data)
                    else:
                        callback(data)
                except Exception as e:
                    logger.error(f"回调执行失败 {event}: {e}")

    # 属性访问器,提供更友好的API
    @property
    def perception(self) -> Any:
        """感知模块访问器"""
        return self.perception_engine

    @property
    def cognition(self) -> Any:
        """认知模块访问器"""
        return self.cognitive_engine

    @property
    def memory(self) -> Any:
        """记忆模块访问器"""
        return self.memory_system

    @property
    def execution(self) -> Any:
        """执行模块访问器"""
        return self.execution_engine

    @property
    def learning(self) -> Any:
        """学习模块访问器"""
        return self.learning_engine

    @property
    def communication(self) -> Any:
        """通信模块访问器"""
        return self.communication_engine

    @property
    def evaluation(self) -> Any:
        """评估模块访问器"""
        return self.evaluation_engine

    @property
    def knowledge(self) -> Any:
        """知识模块访问器"""
        return self.knowledge_manager

    async def shutdown(self):
        """关闭Agent"""
        logger.info(f"🔄 关闭Agent: {self.agent_id}")

        try:
            self.state = AgentState.SHUTDOWN

            # 关闭所有模块
            if self.perception_engine:
                await self.perception_engine.shutdown()
            if self.cognitive_engine:
                await self.cognitive_engine.shutdown()
            if self.memory_system:
                await self.memory_system.shutdown()
            if self.execution_engine:
                await self.execution_engine.shutdown()
            if self.learning_engine:
                await self.learning_engine.shutdown()
            if self.communication_engine:
                await self.communication_engine.shutdown()
            if self.evaluation_engine:
                await self.evaluation_engine.shutdown()
            if self.knowledge_manager:
                await self.knowledge_manager.shutdown()

            logger.info(f"✅ Agent已关闭: {self.agent_id}")

        except Exception as e:
            logger.error(f"❌ Agent关闭失败 {self.agent_id}: {e}")



# 导出具体的Agent类
from .agent_factory import AgentFactory
from .athena_agent import AthenaAgent
from .xiaonuo_agent import XiaonuoAgent

# 导出的类

__all__ = [
    "AgentFactory",
    "AgentProfile",
    "AgentState",
    "AgentType",
    "AthenaAgent",
    "BaseAgent",
    "XiaonuoAgent",
]
