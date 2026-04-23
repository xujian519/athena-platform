#!/usr/bin/env python3
from __future__ import annotations
"""
Agent上下文管理

Agent间共享上下文,支持数据传递和调用链跟踪。

Author: Athena平台团队
创建时间: 2026-04-21
"""

import json
import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class AgentContext:
    """
    Agent间共享上下文

    功能:
    1. 存储Agent间共享数据
    2. 跟踪Agent调用链
    3. 记忆系统引用
    4. 上下文序列化和反序列化
    """

    session_id: str
    task_id: str
    shared_data: dict[str, Any] = field(default_factory=dict)
    agent_call_chain: list[str] = field(default_factory=list)
    memory_references: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """初始化后处理"""
        if not self.session_id:
            self.session_id = f"session_{int(datetime.now().timestamp())}"
        if not self.task_id:
            self.task_id = f"task_{int(datetime.now().timestamp())}"

    def update(self, key: str, value: Any):
        """
        更新上下文数据

        Args:
            key: 键名
            value: 值
        """
        self.shared_data[key] = value
        logger.debug(f"📝 上下文更新: {key} = {value}")

    def get(self, key: str, default: Any = None) -> Any:
        """
        获取上下文数据

        Args:
            key: 键名
            default: 默认值

        Returns:
            值或默认值
        """
        return self.shared_data.get(key, default)

    def has(self, key: str) -> bool:
        """
        检查上下文是否有某个键

        Args:
            key: 键名

        Returns:
            是否存在
        """
        return key in self.shared_data

    def add_to_call_chain(self, agent_name: str):
        """
        添加Agent到调用链

        Args:
            agent_name: Agent名称
        """
        if agent_name not in self.agent_call_chain:
            self.agent_call_chain.append(agent_name)
            logger.debug(f"🔗 调用链: {' -> '.join(self.agent_call_chain)}")

    def get_call_chain(self) -> list[str]:
        """
        获取调用链

        Returns:
            Agent名称列表
        """
        return self.agent_call_chain.copy()

    def get_last_agent(self) -> Optional[str]:
        """
        获取调用的最后一个Agent

        Returns:
            Agent名称或None
        """
        return self.agent_call_chain[-1] if self.agent_call_chain else None

    def add_memory_reference(self, memory_id: str):
        """
        添加记忆引用

        Args:
            memory_id: 记忆ID
        """
        if memory_id not in self.memory_references:
            self.memory_references.append(memory_id)

    def merge(self, other: AgentContext):
        """
        合并另一个上下文

        Args:
            other: 另一个AgentContext
        """
        try:
            if not isinstance(other, AgentContext):
                logger.warning(f"尝试合并非AgentContext对象: {type(other)}")
                return
    
            # 合并共享数据
            self.shared_data.update(other.shared_data)
    
            # 合并调用链
            for agent in other.agent_call_chain:
                self.add_to_call_chain(agent)
    
            # 合并记忆引用
            for mem_ref in other.memory_references:
                self.add_memory_reference(mem_ref)
    
            # 合并元数据
            self.metadata.update(other.metadata)
    
            logger.debug(f"🔄 上下文合并: 合并了 {len(other.shared_data)} 个数据项")
        except Exception as e:
            logger.error(f"上下文合并失败: {e}", exc_info=True)

    def to_dict(self) -> dict[str, Any]:
        """
        转换为字典

        Returns:
            字典表示
        """
        return {
            "session_id": self.session_id,
            "task_id": self.task_id,
            "shared_data": self.shared_data,
            "agent_call_chain": self.agent_call_chain,
            "memory_references": self.memory_references,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> AgentContext:
        """
        从字典创建

        Args:
            data: 字典数据

        Returns:
            AgentContext实例
        """
        return cls(
            session_id=data.get("session_id", ""),
            task_id=data.get("task_id", ""),
            shared_data=data.get("shared_data", {}),
            agent_call_chain=data.get("agent_call_chain", []),
            memory_references=data.get("memory_references", []),
            metadata=data.get("metadata", {}),
        )

    def to_json(self) -> str:
        """
        转换为JSON字符串

        Returns:
            JSON字符串
        """
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)

    @classmethod
    def from_json(cls, json_str: str) -> AgentContext:
        """
        从JSON字符串创建

        Args:
            json_str: JSON字符串

        Returns:
            AgentContext实例
        """
        try:
            data = json.loads(json_str)
            return cls.from_dict(data)
        except json.JSONDecodeError as e:
            logger.error(f"解析上下文JSON失败: {e}")
            return cls(session_id="", task_id="")
        except Exception as e:
            logger.error(f"从JSON创建上下文失败: {e}", exc_info=True)
            return cls(session_id="", task_id="")

    def create_child_context(self, task_id: Optional[str] = None) -> AgentContext:
        """
        创建子上下文

        子上下文继承父上下文的数据,但可以独立修改。

        Args:
            task_id: 子任务ID

        Returns:
            新的AgentContext实例
        """
        child = AgentContext(
            session_id=self.session_id,
            task_id=task_id or f"{self.task_id}_child",
            shared_data=self.shared_data.copy(),
            agent_call_chain=self.agent_call_chain.copy(),
            memory_references=self.memory_references.copy(),
            metadata=self.metadata.copy(),
        )

        # 标记父子关系
        child.metadata["parent_task_id"] = self.task_id

        return child

    def summary(self) -> str:
        """
        生成上下文摘要

        Returns:
            摘要字符串
        """
        parts = [
            f"Session: {self.session_id}",
            f"Task: {self.task_id}",
            f"Shared Data: {len(self.shared_data)} items",
            f"Call Chain: {' -> '.join(self.agent_call_chain) or 'None'}",
            f"Memory References: {len(self.memory_references)}",
        ]

        return "\n".join(parts)

    def __repr__(self) -> str:
        return f"<AgentContext(session={self.session_id}, task={self.task_id}, data={len(self.shared_data)} items)>"


class AgentContextManager:
    """
    Agent上下文管理器

    管理多个AgentContext实例,提供查询和清理功能。
    """

    def __init__(self):
        """初始化管理器"""
        self._contexts: dict[str, AgentContext] = {}
        self._session_index: dict[str, list[str]] = {}

        logger.info("🗂️  Agent上下文管理器初始化")

    def create_context(
        self,
        session_id: Optional[str] = None,
        task_id: Optional[str] = None,
    ) -> AgentContext:
        """
        创建新的上下文

        Args:
            session_id: 会话ID
            task_id: 任务ID

        Returns:
            AgentContext实例
        """
        context = AgentContext(
            session_id=session_id,
            task_id=task_id,
        )

        # 存储上下文
        self._contexts[context.task_id] = context

        # 更新会话索引
        if context.session_id not in self._session_index:
            self._session_index[context.session_id] = []
        self._session_index[context.session_id].append(context.task_id)

        logger.info(f"✅ 创建上下文: {context.task_id}")

        return context

    def get_context(self, task_id: str) -> AgentContext | None:
        """
        获取上下文

        Args:
            task_id: 任务ID

        Returns:
            AgentContext实例或None
        """
        return self._contexts.get(task_id)

    def get_session_contexts(self, session_id: str) -> list[AgentContext]:
        """
        获取会话的所有上下文

        Args:
            session_id: 会话ID

        Returns:
            AgentContext列表
        """
        task_ids = self._session_index.get(session_id, [])
        return [self._contexts[tid] for tid in task_ids if tid in self._contexts]

    def remove_context(self, task_id: str):
        """
        移除上下文

        Args:
            task_id: 任务ID
        """
        if task_id in self._contexts:
            context = self._contexts[task_id]

            # 从会话索引中移除
            if context.session_id in self._session_index:
                self._session_index[context.session_id].remove(task_id)

            # 删除上下文
            del self._contexts[task_id]

            logger.info(f"🗑️  移除上下文: {task_id}")

    def clear_session(self, session_id: str):
        """
        清除会话的所有上下文

        Args:
            session_id: 会话ID
        """
        task_ids = self._session_index.get(session_id, [])

        for task_id in task_ids:
            if task_id in self._contexts:
                del self._contexts[task_id]

        # 清除会话索引
        if session_id in self._session_index:
            del self._session_index[session_id]

        logger.info(f"🧹 清除会话: {session_id} ({len(task_ids)} 个上下文)")

    def get_stats(self) -> dict[str, Any]:
        """
        获取统计信息

        Returns:
            统计信息字典
        """
        return {
            "total_contexts": len(self._contexts),
            "total_sessions": len(self._session_index),
            "contexts": list(self._contexts.keys()),
            "sessions": list(self._session_index.keys()),
        }


# 全局上下文管理器实例
_context_manager: AgentContextManager | None = None


def get_context_manager() -> AgentContextManager:
    """
    获取全局上下文管理器实例

    Returns:
        Agent上下文管理器
    """
    global _context_manager

    if _context_manager is None:
        _context_manager = AgentContextManager()

    return _context_manager
