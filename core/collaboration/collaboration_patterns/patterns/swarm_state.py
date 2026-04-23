#!/usr/bin/env python3
from __future__ import annotations

"""
Swarm状态管理实现
Swarm State Management Implementation

作者: Athena平台团队
创建时间: 2026-04-20
版本: 1.0.0

实现Swarm群体的共享状态管理。
"""

import logging
from collections import OrderedDict
from datetime import datetime, timedelta
from typing import Any

from .swarm_models import (
    AgentState,
    SwarmEmergencyType,
    SwarmKnowledgeItem,
    SwarmRole,
    SwarmStatistics,
)

logger = logging.getLogger(__name__)


class SwarmSharedState:
    """
    Swarm共享状态

    管理群体的共享状态，包括成员状态、知识库、任务队列等。
    """

    def __init__(self, max_knowledge_items: int = 10000):
        """
        初始化共享状态

        Args:
            max_knowledge_items: 最大知识条目数
        """
        # 成员状态
        self.member_states: dict[str, AgentState] = {}

        # 知识库（使用OrderedDict实现LRU）
        self._knowledge_base: OrderedDict[str, SwarmKnowledgeItem] = OrderedDict()
        self._max_knowledge_items = max_knowledge_items

        # 统计信息
        self.statistics = SwarmStatistics()

        # 紧急标志
        self.emergency_flags: list[str] = []

        # 任务队列
        self.pending_tasks: list[dict[str, Any]] = []
        self.active_tasks: dict[str, dict[str, Any]] = {}
        self.completed_tasks: list[dict[str, Any]] = []

        # 版本向量（用于冲突检测）
        self.version_vector: dict[str, int] = {}

        # 最后更新时间
        self.last_updated: datetime = datetime.now()

        logger.debug("创建Swarm共享状态")

    def update_member_state(self, agent_id: str, state: dict[str, Any]) -> None:
        """
        更新成员状态

        Args:
            agent_id: Agent ID
            state: 状态字典
        """
        if agent_id in self.member_states:
            # 更新现有状态
            existing = self.member_states[agent_id]
            for key, value in state.items():
                if hasattr(existing, key):
                    setattr(existing, key, value)
            existing.update_heartbeat()
        else:
            # 创建新状态
            self.member_states[agent_id] = AgentState(
                agent_id=agent_id,
                role=SwarmRole(state.get("role", SwarmRole.WORKER)),
                status=state.get("status", "active"),
                current_load=state.get("current_load", 0.0),
                capabilities=state.get("capabilities", []),
                neighbors=state.get("neighbors", []),
                last_heartbeat=datetime.now(),
            )
            self.statistics.total_members += 1

        self._update_version(agent_id)
        self.last_updated = datetime.now()

    def get_member_state(self, agent_id: str) -> AgentState | None:
        """
        获取成员状态

        Args:
            agent_id: Agent ID

        Returns:
            AgentState或None
        """
        return self.member_states.get(agent_id)

    def remove_member_state(self, agent_id: str) -> None:
        """
        移除成员状态

        Args:
            agent_id: Agent ID
        """
        if agent_id in self.member_states:
            del self.member_states[agent_id]
            self.statistics.active_members -= 1
            self.last_updated = datetime.now()

    def add_knowledge(self, knowledge: SwarmKnowledgeItem) -> None:
        """
        添加知识

        Args:
            knowledge: 知识项
        """
        # 如果已存在，更新版本
        if knowledge.key in self._knowledge_base:
            existing = self._knowledge_base[knowledge.key]
            knowledge.version = existing.version + 1

        # 添加到知识库
        self._knowledge_base[knowledge.key] = knowledge
        self._knowledge_base.move_to_end(knowledge.key)

        # LRU: 如果超过最大容量，移除最旧的
        if len(self._knowledge_base) > self._max_knowledge_items:
            self._knowledge_base.popitem(last=False)

        self.statistics.total_knowledge_items = len(self._knowledge_base)
        self.last_updated = datetime.now()

        logger.debug(f"添加知识: {knowledge.key}, 版本: {knowledge.version}")

    def get_knowledge(self, key: str) -> SwarmKnowledgeItem | None:
        """
        获取知识

        Args:
            key: 知识键

        Returns:
            知识项或None
        """
        knowledge = self._knowledge_base.get(key)

        if knowledge:
            # 检查是否过期
            if knowledge.is_expired():
                self.remove_knowledge(key)
                return None

            # LRU: 移到末尾
            self._knowledge_base.move_to_end(key)
            return knowledge

        return None

    def remove_knowledge(self, key: str) -> None:
        """
        移除知识

        Args:
            key: 知识键
        """
        if key in self._knowledge_base:
            del self._knowledge_base[key]
            self.statistics.total_knowledge_items = len(self._knowledge_base)
            self.last_updated = datetime.now()

    def query_knowledge_by_pattern(self, pattern: str) -> list[SwarmKnowledgeItem]:
        """
        按模式查询知识

        Args:
            pattern: 匹配模式（简单包含匹配）

        Returns:
            匹配的知识列表
        """
        results = []
        now = datetime.now()

        for knowledge in self._knowledge_base.values():
            # 检查是否过期
            if knowledge.ttl and (now - knowledge.timestamp).total_seconds() > knowledge.ttl:
                continue

            # 检查是否匹配
            if pattern.lower() in knowledge.key.lower():
                results.append(knowledge)

        return results

    def cleanup_expired_knowledge(self) -> int:
        """
        清理过期知识

        Returns:
            清理的数量
        """
        expired_keys = []

        for key, knowledge in self._knowledge_base.items():
            if knowledge.is_expired():
                expired_keys.append(key)

        for key in expired_keys:
            self.remove_knowledge(key)

        if expired_keys:
            logger.info(f"清理了 {len(expired_keys)} 条过期知识")

        return len(expired_keys)

    def add_emergency_flag(self, flag: str) -> None:
        """
        添加紧急标志

        Args:
            flag: 紧急标志
        """
        if flag not in self.emergency_flags:
            self.emergency_flags.append(flag)
            self.statistics.emergency_count += 1
            logger.warning(f"添加紧急标志: {flag}")

    def clear_emergency_flags(self) -> None:
        """清除所有紧急标志"""
        if self.emergency_flags:
            logger.info(f"清除紧急标志: {self.emergency_flags}")
            self.emergency_flags.clear()

    def is_emergency(self) -> bool:
        """
        检查是否处于紧急状态

        Returns:
            是否紧急
        """
        return len(self.emergency_flags) > 0

    def add_pending_task(self, task: dict[str, Any]) -> None:
        """
        添加待处理任务

        Args:
            task: 任务字典
        """
        self.pending_tasks.append(task)
        self.statistics.total_tasks += 1

    def get_next_pending_task(self) -> Optional[dict[str, Any]]:
        """
        获取下一个待处理任务

        Returns:
            任务字典或None
        """
        if self.pending_tasks:
            return self.pending_tasks.pop(0)
        return None

    def activate_task(self, task_id: str, task: dict[str, Any]) -> None:
        """
        激活任务

        Args:
            task_id: 任务ID
            task: 任务字典
        """
        self.active_tasks[task_id] = task

    def complete_task(self, task_id: str, result: dict[str, Any]) -> None:
        """
        完成任务

        Args:
            task_id: 任务ID
            result: 结果字典
        """
        if task_id in self.active_tasks:
            task = self.active_tasks.pop(task_id)
            task["result"] = result
            task["completed_at"] = datetime.now().isoformat()
            self.completed_tasks.append(task)

            # 更新统计
            if result.get("success", False):
                self.statistics.completed_tasks += 1
            else:
                self.statistics.failed_tasks += 1

            # 限制已完成任务列表大小
            if len(self.completed_tasks) > 1000:
                self.completed_tasks = self.completed_tasks[-1000:]

    def get_role_distribution(self) -> dict[SwarmRole, int]:
        """
        获取角色分布

        Returns:
            角色到数量的映射
        """
        distribution = {role: 0 for role in SwarmRole}

        for state in self.member_states.values():
            distribution[state.role] += 1

        return distribution

    def get_available_members(self, required_capability: Optional[str] = None) -> list[str]:
        """
        获取可用成员列表

        Args:
            required_capability: 需要的能力（可选）

        Returns:
            可用成员ID列表
        """
        available = []

        for agent_id, state in self.member_states.items():
            if state.is_available():
                if required_capability is None or state.can_handle_capability(
                    required_capability
                ):
                    available.append(agent_id)

        return available

    def _update_version(self, agent_id: str) -> None:
        """
        更新版本向量

        Args:
            agent_id: Agent ID
        """
        self.version_vector[agent_id] = self.version_vector.get(agent_id, 0) + 1

    def get_version(self, agent_id: str) -> int:
        """
        获取版本号

        Args:
            agent_id: Agent ID

        Returns:
            版本号
        """
        return self.version_vector.get(agent_id, 0)

    def merge_state(self, other_state: SwarmSharedState) -> list[str]:
        """
        合并另一个状态（用于Gossip同步）

        Args:
            other_state: 另一个共享状态

        Returns:
            发生变更的键列表
        """
        changes = []

        # 合并成员状态
        for agent_id, state in other_state.member_states.items():
            if agent_id not in self.member_states:
                self.member_states[agent_id] = state
                changes.append(f"member:{agent_id}")
            else:
                # 比较版本，使用更新的
                other_version = other_state.get_version(agent_id)
                my_version = self.get_version(agent_id)
                if other_version > my_version:
                    self.member_states[agent_id] = state
                    changes.append(f"member:{agent_id}")

        # 合并知识
        for key, knowledge in other_state._knowledge_base.items():
            if key not in self._knowledge_base:
                self.add_knowledge(knowledge)
                changes.append(f"knowledge:{key}")
            else:
                # 比较版本，使用更新的
                existing = self._knowledge_base[key]
                if knowledge.version > existing.version:
                    self.add_knowledge(knowledge)
                    changes.append(f"knowledge:{key}")

        self.last_updated = datetime.now()
        return changes

    def to_dict(self) -> dict[str, Any]:
        """
        转换为字典

        Returns:
            状态字典
        """
        return {
            "member_states": {
                k: v.to_dict() for k, v in self.member_states.items()
            },
            "knowledge_count": len(self._knowledge_base),
            "statistics": self.statistics.to_dict(),
            "emergency_flags": self.emergency_flags.copy(),
            "pending_tasks_count": len(self.pending_tasks),
            "active_tasks_count": len(self.active_tasks),
            "completed_tasks_count": len(self.completed_tasks),
            "version_vector": self.version_vector.copy(),
            "last_updated": self.last_updated.isoformat(),
        }

    def cleanup(self) -> None:
        """清理过期数据"""
        # 清理过期知识
        self.cleanup_expired_knowledge()

        # 清理不活跃的成员状态
        now = datetime.now()
        inactive_members = []

        for agent_id, state in self.member_states.items():
            if (now - state.last_heartbeat).total_seconds() > 300:  # 5分钟无心跳
                inactive_members.append(agent_id)

        for agent_id in inactive_members:
            self.remove_member_state(agent_id)
            logger.info(f"清理不活跃成员: {agent_id}")
