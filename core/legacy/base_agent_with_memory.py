#!/usr/bin/env python3
from __future__ import annotations
"""
带记忆功能的智能体基类
Base Agent with Memory Support

所有Athena平台智能体的统一基类,集成UnifiedAgentMemorySystem

作者: Athena平台团队
创建时间: 2025-12-30
版本: v1.0.0
"""

import logging
from abc import ABC, abstractmethod
from enum import Enum
from typing import Any

from .memory.unified_agent_memory_system import (
    AgentType,
    MemoryTier,
    MemoryType,
    UnifiedAgentMemorySystem,
)

logger = logging.getLogger(__name__)


class AgentRole(Enum):
    """智能体角色"""

    COORDINATOR = "coordinator"  # 协调者/调度官
    EXPERT = "expert"  # 专家
    ASSISTANT = "assistant"  # 助手
    GUARDIAN = "guardian"  # 守护者
    CREATOR = "creator"  # 创造者


class MemoryEnabledAgent(ABC):
    """
    带记忆功能的智能体基类

    提供统一的记忆管理接口,所有智能体都应继承此类
    """

    def __init__(
        self,
        agent_id: str,
        agent_type: AgentType,
        role: AgentRole,
        name: Optional[str] = None,
        english_name: Optional[str] = None,
    ):
        """
        初始化智能体

        Args:
            agent_id: 智能体唯一ID
            agent_type: 智能体类型
            role: 智能体角色
            name: 中文名称
            english_name: 英文名称
        """
        self.agent_id = agent_id
        self.agent_type = agent_type
        self.role = role
        self.name = name or agent_id
        self.english_name = english_name or agent_id

        # 记忆系统引用
        self.memory_system: UnifiedAgentMemorySystem | None = None
        self._memory_enabled = False

        # 状态管理
        self._initialized = False
        self._state = "idle"

        logger.info(f"🤖 {self.name} 已创建 (ID: {self.agent_id})")

    async def initialize_memory(self, memory_system: UnifiedAgentMemorySystem):
        """
        初始化记忆系统

        Args:
            memory_system: 统一记忆系统实例
        """
        self.memory_system = memory_system
        self._memory_enabled = True
        logger.info(f"🧠 {self.name} 记忆系统已初始化")

    async def initialize(self) -> None:
        """
        初始化智能体

        子类可以重写此方法添加额外的初始化逻辑
        """
        if not self._memory_enabled:
            logger.warning(f"⚠️ {self.name} 记忆系统未启用,请先调用 initialize_memory()")
        else:
            await self._load_initial_memories()

        self._initialized = True
        self._state = "ready"
        logger.info(f"✅ {self.name} 初始化完成")

    async def _load_initial_memories(self):
        """
        加载初始记忆

        子类可以重写此方法加载特定的初始记忆
        """
        # 默认实现:从记忆系统回忆最重要的记忆
        if self.memory_system:
            memories = await self.memory_system.recall_memory(
                agent_id=self.agent_id, query="重要记忆", limit=5, tier=MemoryTier.ETERNAL
            )
            logger.info(f"📚 {self.name} 加载了 {len(memories)} 条永恒记忆")

    # ========== 记忆操作便捷方法 ==========

    async def remember(
        self,
        content: str,
        memory_type: MemoryType = MemoryType.CONVERSATION,
        tier: MemoryTier = MemoryTier.WARM,
        importance: float = 0.5,
        emotional_weight: float = 0.0,
        family_related: bool = False,
        work_related: bool = False,
        tags: Optional[list[str]] = None,
        metadata: dict | None = None,
    ) -> Optional[str]:
        """
        存储记忆

        Args:
            content: 记忆内容
            memory_type: 记忆类型
            tier: 记忆层级
            importance: 重要性 (0-1)
            emotional_weight: 情感权重 (0-1)
            family_related: 是否家庭相关
            work_related: 是否工作相关
            tags: 标签列表
            metadata: 元数据

        Returns:
            记忆ID,失败返回None
        """
        if not self.memory_system:
            logger.warning(f"⚠️ {self.name} 记忆系统未初始化")
            return None

        try:
            memory_id = await self.memory_system.store_memory(
                agent_id=self.agent_id,
                agent_type=self.agent_type,
                content=content,
                memory_type=memory_type,
                importance=importance,
                emotional_weight=emotional_weight,
                family_related=family_related,
                work_related=work_related,
                tags=tags or [],
                metadata=metadata or {},
                tier=tier,
            )
            logger.debug(f"💾 {self.name} 存储记忆: {content[:50]}...")
            return memory_id
        except Exception as e:
            logger.error(f"❌ {self.name} 存储记忆失败: {e}")
            return None

    async def recall(
        self,
        query: str,
        limit: int = 10,
        memory_type: MemoryType | None = None,
        tier: MemoryTier | None = None,
    ) -> list[dict]:
        """
        回忆记忆

        Args:
            query: 搜索查询
            limit: 返回数量
            memory_type: 记忆类型过滤
            tier: 记忆层级过滤

        Returns:
            记忆列表
        """
        if not self.memory_system:
            logger.warning(f"⚠️ {self.name} 记忆系统未初始化")
            return []

        try:
            memories = await self.memory_system.recall_memory(
                agent_id=self.agent_id, query=query, limit=limit, memory_type=memory_type, tier=tier
            )
            logger.debug(f"🔍 {self.name} 回忆 {len(memories)} 条记忆")
            return memories
        except Exception as e:
            logger.error(f"❌ {self.name} 回忆记忆失败: {e}")
            return []

    async def remember_conversation(
        self, user_message: str, agent_response: str, context: dict | None = None
    ) -> Optional[str]:
        """
        记录对话

        Args:
            user_message: 用户消息
            agent_response: 智能体回复
            context: 对话上下文

        Returns:
            记忆ID
        """
        content = f"用户: {user_message}\\n{self.name}: {agent_response}"
        return await self.remember(
            content=content,
            memory_type=MemoryType.CONVERSATION,
            tier=MemoryTier.WARM,
            tags=["对话", "交互"],
            metadata=context or {},
        )

    async def remember_emotion(
        self, emotion: str, description: str, intensity: float = 0.5
    ) -> Optional[str]:
        """
        记录情感记忆

        Args:
            emotion: 情感类型 (快乐、悲伤、愤怒等)
            description: 描述
            intensity: 强度 (0-1)

        Returns:
            记忆ID
        """
        content = f"情感: {emotion} - {description}"
        return await self.remember(
            content=content,
            memory_type=MemoryType.EMOTIONAL,
            tier=MemoryTier.WARM,
            emotional_weight=intensity,
            tags=["情感", emotion],
        )

    async def remember_family(self, content: str, importance: float = 1.0) -> Optional[str]:
        """
        记录家庭记忆

        Args:
            content: 记忆内容
            importance: 重要性

        Returns:
            记忆ID
        """
        return await self.remember(
            content=content,
            memory_type=MemoryType.FAMILY,
            tier=MemoryTier.ETERNAL,
            importance=importance,
            emotional_weight=1.0,
            family_related=True,
            tags=["家庭", "永恒"],
        )

    async def remember_work(self, content: str, importance: float = 0.7) -> Optional[str]:
        """
        记录工作记忆

        Args:
            content: 记忆内容
            importance: 重要性

        Returns:
            记忆ID
        """
        return await self.remember(
            content=content,
            memory_type=MemoryType.PROFESSIONAL,
            tier=MemoryTier.WARM,
            importance=importance,
            work_related=True,
            tags=["工作", "专业"],
        )

    async def remember_learning(
        self, topic: str, knowledge: str, importance: float = 0.6
    ) -> Optional[str]:
        """
        记录学习记忆

        Args:
            topic: 学习主题
            knowledge: 学习内容
            importance: 重要性

        Returns:
            记忆ID
        """
        content = f"学到: {topic} - {knowledge}"
        return await self.remember(
            content=content,
            memory_type=MemoryType.LEARNING,
            tier=MemoryTier.COLD,
            importance=importance,
            tags=["学习", topic, "知识"],
        )

    # ========== 抽象方法 ==========

    @abstractmethod
    async def process(self, message: str, context: dict | None = None) -> str:
        """
        处理消息

        Args:
            message: 用户消息
            context: 上下文信息

        Returns:
            智能体回复
        """
        pass

    @abstractmethod
    def get_capabilities(self) -> list[str]:
        """
        获取智能体能力列表

        Returns:
            能力列表
        """
        pass

    # ========== 状态管理 ==========

    @property
    def is_initialized(self) -> bool:
        """是否已初始化"""
        return self._initialized

    @property
    def state(self) -> str:
        """当前状态"""
        return self._state

    @state.setter
    def state(self, value: str) -> Any:
        """设置状态"""
        self._state = value
        logger.debug(f"🔄 {self.name} 状态变更: {self._state} -> {value}")

    def get_info(self) -> dict[str, Any]:
        """
        获取智能体信息

        Returns:
            智能体信息字典
        """
        return {
            "agent_id": self.agent_id,
            "agent_type": self.agent_type.value,
            "name": self.name,
            "english_name": self.english_name,
            "role": self.role.value,
            "memory_enabled": self._memory_enabled,
            "initialized": self._initialized,
            "state": self._state,
            "capabilities": self.get_capabilities(),
        }

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}({self.name}, id={self.agent_id})>"
