#!/usr/bin/env python3
from __future__ import annotations
"""
共享记忆空间
Shared Memory Space

为智能体提供共享记忆能力:
1. 跨智能体记忆共享
2. 记忆访问控制
3. 记忆版本管理
4. 记忆同步机制
5. 记忆冲突解决
6. 记忆订阅通知

作者: Athena平台团队
创建时间: 2025-12-26
版本: v1.0.0 "共享记忆"
"""

import logging
import uuid
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class MemoryAccessLevel(Enum):
    """记忆访问级别"""

    PRIVATE = "private"  # 私有 - 仅创建者
    RESTRICTED = "restricted"  # 受限 - 指定智能体
    TEAM = "team"  # 团队 - 同团队智能体
    PUBLIC = "public"  # 公开 - 所有智能体


class MemoryType(Enum):
    """记忆类型"""

    EPISODIC = "episodic"  # 情景记忆
    SEMANTIC = "semantic"  # 语义记忆
    PROCEDURAL = "procedural"  # 程序记忆
    WORKING = "working"  # 工作记忆
    COLLECTIVE = "collective"  # 集体记忆


@dataclass
class SharedMemory:
    """共享记忆"""

    memory_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    type: MemoryType = MemoryType.EPISODIC
    access_level: MemoryAccessLevel = MemoryAccessLevel.RESTRICTED

    # 创建者和权限
    creator_id: str = ""
    allowed_agents: list[str] = field(default_factory=list)

    # 内容
    content: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)
    embeddings: list[float] | None = None

    # 时间戳
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    expires_at: datetime | None = None

    # 版本控制
    version: int = 1
    parent_memory_id: str | None = None

    # 访问统计
    access_count: int = 0
    last_accessed: datetime | None = None

    # 标签和分类
    tags: list[str] = field(default_factory=list)
    category: str = ""

    # 重要性
    importance: float = 0.5  # 0-1


@dataclass
class MemorySubscription:
    """记忆订阅"""

    subscription_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    subscriber_id: str = ""
    memory_type_filters: list[MemoryType] = field(default_factory=list)
    tag_filters: list[str] = field(default_factory=list)
    min_importance: float = 0.0
    callback: callable | None = None
    created_at: datetime = field(default_factory=datetime.now)
    active: bool = True


class SharedMemorySpace:
    """
    共享记忆空间

    核心功能:
    1. 跨智能体记忆存储和检索
    2. 访问控制管理
    3. 记忆版本追踪
    4. 记忆订阅通知
    5. 智能记忆合并
    6. 记忆冲突解决
    """

    def __init__(self):
        # 记忆存储
        self.memories: dict[str, SharedMemory] = {}

        # 智能体团队映射
        self.agent_teams: dict[str, str] = defaultdict(str)  # agent_id -> team_id

        # 记忆订阅
        self.subscriptions: list[MemorySubscription] = []

        # 索引
        self.by_type: dict[MemoryType, list[str]] = defaultdict(list)
        self.by_tag: dict[str, list[str]] = defaultdict(list)
        self.by_creator: dict[str, list[str]] = defaultdict(list)

        # 统计
        self.metrics = {
            "total_memories": 0,
            "access_count": 0,
            "shared_count": 0,
            "merge_count": 0,
            "conflict_count": 0,
        }

        logger.info("🧠 共享记忆空间初始化完成")

    async def store_memory(
        self,
        creator_id: str,
        content: str,
        memory_type: MemoryType = MemoryType.EPISODIC,
        access_level: MemoryAccessLevel = MemoryAccessLevel.RESTRICTED,
        allowed_agents: list[str] | None = None,
        tags: list[str] | None = None,
        metadata: dict[str, Any] | None = None,
        importance: float = 0.5,
        ttl_seconds: int | None = None,
    ) -> str:
        """存储共享记忆"""
        memory = SharedMemory(
            creator_id=creator_id,
            content=content,
            type=memory_type,
            access_level=access_level,
            allowed_agents=allowed_agents or [],
            tags=tags or [],
            metadata=metadata or {},
            importance=importance,
        )

        # 设置过期时间
        if ttl_seconds:
            memory.expires_at = datetime.now() + timedelta(seconds=ttl_seconds)

        # 存储记忆
        self.memories[memory.memory_id] = memory

        # 更新索引
        self.by_type[memory_type].append(memory.memory_id)
        for tag in memory.tags:
            self.by_tag[tag].append(memory.memory_id)
        self.by_creator[creator_id].append(memory.memory_id)

        # 更新统计
        self.metrics["total_memories"] += 1

        # 如果是共享级别,通知订阅者
        if access_level in [MemoryAccessLevel.TEAM, MemoryAccessLevel.PUBLIC]:
            await self._notify_subscribers(memory)

        logger.info(
            f"💾 共享记忆已存储: {memory.memory_id[:8]}... "
            f"({memory_type.value}, {access_level.value})"
        )

        return memory.memory_id

    async def retrieve_memory(self, memory_id: str, requester_id: str) -> SharedMemory | None:
        """检索记忆"""
        memory = self.memories.get(memory_id)

        if not memory:
            return None

        # 检查访问权限
        if not await self._check_access(memory, requester_id):
            logger.warning(f"未授权的记忆访问: {requester_id} -> {memory_id}")
            return None

        # 检查是否过期
        if memory.expires_at and datetime.now() > memory.expires_at:
            logger.info(f"记忆已过期: {memory_id}")
            del self.memories[memory_id]
            return None

        # 更新访问统计
        memory.access_count += 1
        memory.last_accessed = datetime.now()
        self.metrics["access_count"] += 1

        return memory

    async def search_memories(
        self,
        requester_id: str,
        query: str,
        memory_type: MemoryType | None = None,
        tags: list[str] | None = None,
        min_importance: float = 0.0,
        limit: int = 10,
    ) -> list[SharedMemory]:
        """搜索记忆"""
        results = []

        # 收集候选记忆
        candidates = list(self.memories.values())

        # 过滤
        for memory in candidates:
            # 检查访问权限
            if not await self._check_access(memory, requester_id):
                continue

            # 检查类型
            if memory_type and memory.type != memory_type:
                continue

            # 检查标签
            if tags and not any(tag in memory.tags for tag in tags):
                continue

            # 检查重要性
            if memory.importance < min_importance:
                continue

            # 简单文本匹配
            if query.lower() in memory.content.lower():
                results.append(memory)

        # 排序(按重要性和最近访问)
        results.sort(key=lambda m: (m.importance, m.last_accessed or datetime.min), reverse=True)

        return results[:limit]

    async def update_memory(
        self,
        memory_id: str,
        updater_id: str,
        updates: dict[str, Any],        create_new_version: bool = True,
    ) -> str | None:
        """更新记忆"""
        memory = self.memories.get(memory_id)

        if not memory:
            return None

        # 检查权限(只有创建者可以更新)
        if memory.creator_id != updater_id:
            logger.warning(f"未授权的记忆更新: {updater_id} -> {memory_id}")
            return None

        if create_new_version:
            # 创建新版本
            new_memory = SharedMemory(
                content=updates.get("content", memory.content),
                type=memory.type,
                access_level=updates.get("access_level", memory.access_level),
                creator_id=memory.creator_id,
                allowed_agents=memory.allowed_agents,
                metadata=updates.get("metadata", memory.metadata),
                tags=updates.get("tags", memory.tags),
                importance=updates.get("importance", memory.importance),
                version=memory.version + 1,
                parent_memory_id=memory_id,
            )

            # 存储新版本
            self.memories[new_memory.memory_id] = new_memory

            # 更新索引
            self.by_type[new_memory.type].append(new_memory.memory_id)
            for tag in new_memory.tags:
                self.by_tag[tag].append(new_memory.memory_id)
            self.by_creator[new_memory.creator_id].append(new_memory.memory_id)

            logger.info(f"📝 记忆新版本: {new_memory.memory_id[:8]}... (v{new_memory.version})")

            return new_memory.memory_id
        else:
            # 直接更新
            for key, value in updates.items():
                if hasattr(memory, key):
                    setattr(memory, key, value)
            memory.updated_at = datetime.now()

            logger.info(f"📝 记忆已更新: {memory_id[:8]}...")

            return memory_id

    async def merge_memories(
        self, memory_ids: list[str], merger_id: str, merge_strategy: str = "concatenate"
    ) -> str | None:
        """合并多个记忆"""
        memories = []
        for mid in memory_ids:
            memory = self.memories.get(mid)
            if memory and await self._check_access(memory, merger_id):
                memories.append(memory)

        if len(memories) < 2:
            logger.warning("需要至少2个记忆进行合并")
            return None

        # 合并策略
        if merge_strategy == "concatenate":
            merged_content = "\n\n---\n\n".join([m.content for m in memories])
        elif merge_strategy == "interleave":
            # 交错合并段落
            paragraphs = []
            for memory in memories:
                paragraphs.extend(memory.content.split("\n\n"))
            merged_content = "\n\n".join(paragraphs)
        else:  # smart
            # 智能合并(去重、排序)
            merged_content = await self._smart_merge(memories)

        # 创建合并后的记忆
        merged_memory = await self.store_memory(
            creator_id=merger_id,
            content=merged_content,
            memory_type=memories[0].type,
            access_level=memories[0].access_level,
            tags=list({tag for m in memories for tag in m.tags}),
            metadata={"merged_from": memory_ids, "merge_strategy": merge_strategy},
            importance=max(m.importance for m in memories),
        )

        self.metrics["merge_count"] += 1

        logger.info(f"🔀 记忆已合并: {len(memory_ids)} -> {merged_memory[:8]}...")

        return merged_memory

    async def subscribe_memories(
        self,
        subscriber_id: str,
        memory_types: list[MemoryType] | None = None,
        tags: list[str] | None = None,
        min_importance: float = 0.0,
        callback: callable | None = None,
    ) -> str:
        """订阅记忆更新"""
        subscription = MemorySubscription(
            subscriber_id=subscriber_id,
            memory_type_filters=memory_types or [],
            tag_filters=tags or [],
            min_importance=min_importance,
            callback=callback,
        )

        self.subscriptions.append(subscription)

        logger.info(f"📬 记忆订阅: {subscriber_id}")

        return subscription.subscription_id

    async def set_agent_team(self, agent_id: str, team_id: str):
        """设置智能体所属团队"""
        self.agent_teams[agent_id] = team_id
        logger.debug(f"👥 智能体团队: {agent_id} -> {team_id}")

    async def _check_access(self, memory: SharedMemory, requester_id: str) -> bool:
        """检查访问权限"""
        # 创建者总是有权限
        if memory.creator_id == requester_id:
            return True

        # 私有记忆
        if memory.access_level == MemoryAccessLevel.PRIVATE:
            return False

        # 受限记忆
        if memory.access_level == MemoryAccessLevel.RESTRICTED:
            return requester_id in memory.allowed_agents

        # 团队记忆
        if memory.access_level == MemoryAccessLevel.TEAM:
            requester_team = self.agent_teams.get(requester_id)
            creator_team = self.agent_teams.get(memory.creator_id)
            return requester_team and requester_team == creator_team

        # 公开记忆
        return memory.access_level == MemoryAccessLevel.PUBLIC

    async def _notify_subscribers(self, memory: SharedMemory):
        """通知订阅者"""
        for subscription in self.subscriptions:
            if not subscription.active:
                continue

            # 检查过滤条件
            if (
                subscription.memory_type_filters
                and memory.type not in subscription.memory_type_filters
            ):
                continue

            if subscription.tag_filters and not any(
                tag in memory.tags for tag in subscription.tag_filters
            ):
                continue

            if memory.importance < subscription.min_importance:
                continue

            # 执行回调
            if subscription.callback:
                try:
                    pass
                except Exception:
                    logger.error("操作失败: e", exc_info=True)
                    raise
    async def _smart_merge(self, memories: list[SharedMemory]) -> str:
        """智能合并记忆"""
        # 简化实现:去除重复内容
        seen_contents = set()
        unique_paragraphs = []

        for memory in memories:
            for paragraph in memory.content.split("\n\n"):
                paragraph = paragraph.strip()
                if paragraph and paragraph not in seen_contents:
                    seen_contents.add(paragraph)
                    unique_paragraphs.append(paragraph)

        return "\n\n".join(unique_paragraphs)

    async def get_space_metrics(self) -> dict[str, Any]:
        """获取空间指标"""
        return {
            "total_memories": len(self.memories),
            "by_type": {
                mem_type.value: len(memory_ids) for mem_type, memory_ids in self.by_type.items()
            },
            "by_access": {
                access_level.value: sum(
                    1 for m in self.memories.values() if m.access_level == access_level
                )
                for access_level in MemoryAccessLevel
            },
            "subscriptions": len(self.subscriptions),
            "active_subscriptions": sum(1 for s in self.subscriptions if s.active),
            "metrics": self.metrics,
        }


# 导出便捷函数
_shared_memory_space: SharedMemorySpace | None = None


def get_shared_memory_space() -> SharedMemorySpace:
    """获取共享记忆空间单例"""
    global _shared_memory_space
    if _shared_memory_space is None:
        _shared_memory_space = SharedMemorySpace()
    return _shared_memory_space
