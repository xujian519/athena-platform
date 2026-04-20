#!/usr/bin/env python3
from __future__ import annotations

"""
Swarm通信协议实现
Swarm Communication Protocol Implementation

作者: Athena平台团队
创建时间: 2026-04-20
版本: 1.0.0

实现Swarm群体的通信协议。
"""

import asyncio
import logging
import random
import uuid
from datetime import datetime
from typing import Any, Callable

from .swarm_models import (
    SwarmKnowledgeItem,
    SwarmMessageType,
    SwarmRole,
)

logger = logging.getLogger(__name__)


class SwarmMessage:
    """Swarm消息"""

    def __init__(
        self,
        message_type: SwarmMessageType,
        sender_id: str,
        content: dict[str, Any],
        receiver_id: str | None = None,
        target_role: SwarmRole | None = None,
        message_id: str | None = None,
    ):
        """
        初始化消息

        Args:
            message_type: 消息类型
            sender_id: 发送者ID
            content: 消息内容
            receiver_id: 接收者ID（None表示广播）
            target_role: 目标角色（None表示无特定角色）
            message_id: 消息ID（可选）
        """
        self.message_id = message_id or str(uuid.uuid4())
        self.message_type = message_type
        self.sender_id = sender_id
        self.receiver_id = receiver_id
        self.target_role = target_role
        self.content = content
        self.timestamp = datetime.now()
        self.ttl = 60  # 默认60秒生存时间

    def is_expired(self) -> bool:
        """检查消息是否已过期"""
        age = (datetime.now() - self.timestamp).total_seconds()
        return age > self.ttl

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "message_id": self.message_id,
            "message_type": self.message_type.value,
            "sender_id": self.sender_id,
            "receiver_id": self.receiver_id,
            "target_role": self.target_role.value if self.target_role else None,
            "content": self.content,
            "timestamp": self.timestamp.isoformat(),
            "ttl": self.ttl,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "SwarmMessage":
        """从字典创建消息"""
        return cls(
            message_type=SwarmMessageType(data["message_type"]),
            sender_id=data["sender_id"],
            content=data["content"],
            receiver_id=data.get("receiver_id"),
            target_role=SwarmRole(data["target_role"]) if data.get("target_role") else None,
            message_id=data.get("message_id"),
        )


class SwarmCommunicationProtocol:
    """
    Swarm通信协议

    实现群体内的各种通信模式：广播、组播、单播。
    """

    def __init__(self, session_id: str):
        """
        初始化通信协议

        Args:
            session_id: 会话ID
        """
        self.session_id = session_id

        # 消息处理器
        self.message_handlers: dict[SwarmMessageType, list[Callable]] = {}

        # 消息历史（用于去重）
        self.message_history: dict[str, float] = {}
        self._history_max_size = 10000

        # 统计信息
        self.stats = {
            "messages_sent": 0,
            "messages_received": 0,
            "messages_broadcast": 0,
            "messages_multicast": 0,
            "messages_unicast": 0,
        }

        logger.debug(f"创建Swarm通信协议: session={session_id}")

    def register_handler(
        self,
        message_type: SwarmMessageType,
        handler: Callable,
    ) -> None:
        """
        注册消息处理器

        Args:
            message_type: 消息类型
            handler: 处理函数
        """
        if message_type not in self.message_handlers:
            self.message_handlers[message_type] = []
        self.message_handlers[message_type].append(handler)
        logger.debug(f"注册消息处理器: {message_type.value}")

    async def broadcast(
        self,
        sender_id: str,
        message_type: SwarmMessageType,
        content: dict[str, Any],
    ) -> SwarmMessage:
        """
        广播消息（发送给所有成员）

        Args:
            sender_id: 发送者ID
            message_type: 消息类型
            content: 消息内容

        Returns:
            创建的消息
        """
        message = SwarmMessage(
            message_type=message_type,
            sender_id=sender_id,
            content=content,
        )

        self.stats["messages_sent"] += 1
        self.stats["messages_broadcast"] += 1

        logger.debug(
            f"广播消息: type={message_type.value}, sender={sender_id}, "
            f"id={message.message_id}"
        )

        return message

    async def multicast(
        self,
        sender_id: str,
        message_type: SwarmMessageType,
        content: dict[str, Any],
        target_role: SwarmRole,
    ) -> SwarmMessage:
        """
        组播消息（发送给特定角色的成员）

        Args:
            sender_id: 发送者ID
            message_type: 消息类型
            content: 消息内容
            target_role: 目标角色

        Returns:
            创建的消息
        """
        message = SwarmMessage(
            message_type=message_type,
            sender_id=sender_id,
            content=content,
            target_role=target_role,
        )

        self.stats["messages_sent"] += 1
        self.stats["messages_multicast"] += 1

        logger.debug(
            f"组播消息: type={message_type.value}, sender={sender_id}, "
            f"target_role={target_role.value}, id={message.message_id}"
        )

        return message

    async def unicast(
        self,
        sender_id: str,
        receiver_id: str,
        message_type: SwarmMessageType,
        content: dict[str, Any],
    ) -> SwarmMessage:
        """
        单播消息（点对点）

        Args:
            sender_id: 发送者ID
            receiver_id: 接收者ID
            message_type: 消息类型
            content: 消息内容

        Returns:
            创建的消息
        """
        message = SwarmMessage(
            message_type=message_type,
            sender_id=sender_id,
            content=content,
            receiver_id=receiver_id,
        )

        self.stats["messages_sent"] += 1
        self.stats["messages_unicast"] += 1

        logger.debug(
            f"单播消息: type={message_type.value}, sender={sender_id}, "
            f"receiver={receiver_id}, id={message.message_id}"
        )

        return message

    async def handle_message(self, message: SwarmMessage) -> bool:
        """
        处理接收到的消息

        Args:
            message: 消息对象

        Returns:
            是否成功处理
        """
        # 检查去重
        if self._is_duplicate(message.message_id):
            logger.debug(f"忽略重复消息: {message.message_id}")
            return False

        # 记录消息
        self._record_message(message.message_id)
        self.stats["messages_received"] += 1

        # 检查过期
        if message.is_expired():
            logger.debug(f"忽略过期消息: {message.message_id}")
            return False

        # 调用处理器
        handlers = self.message_handlers.get(message.message_type, [])

        if not handlers:
            logger.warning(f"没有找到消息处理器: {message.message_type.value}")
            return False

        # 调用所有处理器
        for handler in handlers:
            try:
                if asyncio.iscoroutinefunction(handler):
                    await handler(message)
                else:
                    handler(message)
            except Exception as e:
                logger.error(
                    f"消息处理器错误: {message.message_type.value}, "
                    f"error={e}"
                )

        return True

    def _is_duplicate(self, message_id: str) -> bool:
        """检查是否为重复消息"""
        return message_id in self.message_history

    def _record_message(self, message_id: str) -> None:
        """记录消息"""
        self.message_history[message_id] = datetime.now().timestamp()

        # 限制历史大小
        if len(self.message_history) > self._history_max_size:
            # 移除最旧的1000条
            oldest = sorted(self.message_history.items(), key=lambda x: x[1])[:1000]
            for msg_id, _ in oldest:
                del self.message_history[msg_id]

    def cleanup_expired_history(self, max_age: float = 3600) -> int:
        """
        清理过期的消息历史

        Args:
            max_age: 最大年龄（秒）

        Returns:
            清理的数量
        """
        now = datetime.now().timestamp()
        expired_ids = [
            msg_id
            for msg_id, timestamp in self.message_history.items()
            if now - timestamp > max_age
        ]

        for msg_id in expired_ids:
            del self.message_history[msg_id]

        return len(expired_ids)

    def get_statistics(self) -> dict[str, Any]:
        """获取统计信息"""
        return {
            **self.stats,
            "handlers_registered": sum(
                len(handlers) for handlers in self.message_handlers.values()
            ),
            "message_history_size": len(self.message_history),
        }


class SwarmGossipProtocol:
    """
    Swarm Gossip协议

    实现基于随机选择的Gossip状态同步协议。
    """

    def __init__(
        self,
        session_id: str,
        gossip_interval: float = 10.0,
        gossip_fanout: int = 3,
    ):
        """
        初始化Gossip协议

        Args:
            session_id: 会话ID
            gossip_interval: Gossip间隔（秒）
            gossip_fanout: 每轮Gossip的邻居数量
        """
        self.session_id = session_id
        self.gossip_interval = gossip_interval
        self.gossip_fanout = gossip_fanout

        # 版本向量
        self.version_vector: dict[str, int] = {}

        # 统计信息
        self.stats = {
            "gossip_rounds": 0,
            "states_exchanged": 0,
            "conflicts_resolved": 0,
        }

        logger.debug(
            f"创建Gossip协议: interval={gossip_interval}s, fanout={gossip_fanout}"
        )

    def select_gossip_partners(
        self,
        members: list[str],
        exclude: list[str] | None = None,
    ) -> list[str]:
        """
        选择Gossip伙伴

        Args:
            members: 成员列表
            exclude: 排除的成员列表

        Returns:
            选择的伙伴列表
        """
        exclude = exclude or []
        available = [m for m in members if m not in exclude]

        # 随机选择N个邻居
        fanout = min(self.gossip_fanout, len(available))
        selected = random.sample(available, fanout) if available else []

        logger.debug(
            f"选择Gossip伙伴: {len(available)}个可用, 选择{len(selected)}个"
        )

        return selected

    def update_version(self, key: str, version: int) -> bool:
        """
        更新版本号

        Args:
            key: 键
            version: 版本号

        Returns:
            是否更新（版本更新）
        """
        current_version = self.version_vector.get(key, 0)

        if version > current_version:
            self.version_vector[key] = version
            return True

        return False

    def get_version(self, key: str) -> int:
        """
        获取版本号

        Args:
            key: 键

        Returns:
            版本号
        """
        return self.version_vector.get(key, 0)

    def compare_version_vectors(
        self,
        other_vector: dict[str, int],
    ) -> dict[str, Any]:
        """
        比较版本向量

        Args:
            other_vector: 另一个版本向量

        Returns:
            比较结果
        """
        my_keys = set(self.version_vector.keys())
        other_keys = set(other_vector.keys())

        # 我有但对方没有的
        only_my_keys = my_keys - other_keys

        # 对方有但我没有的
        only_other_keys = other_keys - my_keys

        # 共有的键
        common_keys = my_keys & other_keys

        # 我更新的
        my_newer = [
            k
            for k in common_keys
            if self.version_vector[k] > other_vector[k]
        ]

        # 对方更新的
        other_newer = [
            k
            for k in common_keys
            if self.version_vector[k] < other_vector[k]
        ]

        # 冲突（不可能，因为版本向量单调递增）
        conflicts = []  # 在向量时钟中不应该有冲突

        return {
            "only_my_keys": list(only_my_keys),
            "only_other_keys": list(only_other_keys),
            "my_newer": my_newer,
            "other_newer": other_newer,
            "conflicts": conflicts,
        }

    def merge_version_vector(self, other_vector: dict[str, int]) -> list[str]:
        """
        合并版本向量

        Args:
            other_vector: 另一个版本向量

        Returns:
            更新的键列表
        """
        updated_keys = []

        for key, version in other_vector.items():
            if self.update_version(key, version):
                updated_keys.append(key)

        return updated_keys

    def get_statistics(self) -> dict[str, Any]:
        """获取统计信息"""
        return {
            **self.stats,
            "version_vector_size": len(self.version_vector),
        }


class SwarmKnowledgeSharing:
    """
    Swarm知识共享

    管理群体内的知识共享和传播。
    """

    def __init__(self, session_id: str):
        """
        初始化知识共享

        Args:
            session_id: 会话ID
        """
        self.session_id = session_id

        # 本地知识缓存
        self.local_knowledge: dict[str, SwarmKnowledgeItem] = {}

        # 知识传播记录
        self.propagation_history: dict[str, list[str]] = {}

        # 统计信息
        self.stats = {
            "knowledge_shared": 0,
            "knowledge_received": 0,
            "knowledge_merged": 0,
        }

        logger.debug(f"创建知识共享: session={session_id}")

    def share_knowledge(
        self,
        knowledge: SwarmKnowledgeItem,
        propagate_to: list[str] | None = None,
    ) -> None:
        """
        共享知识

        Args:
            knowledge: 知识项
            propagate_to: 传播目标列表（None表示广播）
        """
        # 存储到本地
        self.local_knowledge[knowledge.key] = knowledge

        # 记录传播
        if propagate_to:
            self.propagation_history[knowledge.key] = propagate_to

        self.stats["knowledge_shared"] += 1

        logger.debug(
            f"共享知识: key={knowledge.key}, 源={knowledge.source}, "
            f"传播给={len(propagate_to) if propagate_to else 'all'}"
        )

    def receive_knowledge(
        self,
        knowledge: SwarmKnowledgeItem,
        source: str,
    ) -> bool:
        """
        接收知识

        Args:
            knowledge: 知识项
            source: 来源

        Returns:
            是否接受（版本更新或新知识）
        """
        existing = self.local_knowledge.get(knowledge.key)

        if existing is None:
            # 新知识
            self.local_knowledge[knowledge.key] = knowledge
            self.stats["knowledge_received"] += 1
            logger.debug(f"接收新知识: key={knowledge.key}, 来源={source}")
            return True

        elif knowledge.version > existing.version:
            # 版本更新
            self.local_knowledge[knowledge.key] = knowledge
            self.stats["knowledge_merged"] += 1
            logger.debug(
                f"更新知识: key={knowledge.key}, "
                f"版本={existing.version}->{knowledge.version}"
            )
            return True

        return False

    def get_knowledge(self, key: str) -> SwarmKnowledgeItem | None:
        """
        获取知识

        Args:
            key: 知识键

        Returns:
            知识项或None
        """
        knowledge = self.local_knowledge.get(key)

        if knowledge and knowledge.is_expired():
            del self.local_knowledge[key]
            return None

        return knowledge

    def query_knowledge(
        self,
        pattern: str,
        max_results: int = 10,
    ) -> list[SwarmKnowledgeItem]:
        """
        查询知识

        Args:
            pattern: 匹配模式
            max_results: 最大结果数

        Returns:
            匹配的知识列表
        """
        results = []

        for knowledge in self.local_knowledge.values():
            if knowledge.is_expired():
                continue

            if pattern.lower() in knowledge.key.lower():
                results.append(knowledge)
                if len(results) >= max_results:
                    break

        return results

    def cleanup_expired_knowledge(self) -> int:
        """
        清理过期知识

        Returns:
            清理的数量
        """
        expired_keys = [
            k
            for k, v in self.local_knowledge.items()
            if v.is_expired()
        ]

        for key in expired_keys:
            del self.local_knowledge[key]

        return len(expired_keys)

    def get_statistics(self) -> dict[str, Any]:
        """获取统计信息"""
        return {
            **self.stats,
            "local_knowledge_size": len(self.local_knowledge),
        }
