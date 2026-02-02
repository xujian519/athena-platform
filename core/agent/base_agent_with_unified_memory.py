#!/usr/bin/env python3
"""
带统一记忆系统的智能体基类
Base Agent with Unified Memory System
"""

import json
import os
from datetime import datetime
from typing import Any

from unified_agent_memory_system import MemoryType, UnifiedAgentMemorySystem


class BaseAgentWithUnifiedMemory:
    """带统一记忆系统的智能体基类"""

    def __init__(self, agent_id: str, agent_type: str):
        self.agent_id = agent_id
        self.agent_type = agent_type
        self.memory_system: UnifiedAgentMemorySystem | None = None
        self.conversation_context: list[dict[str, Any]] = []
        self.memory_config = {"auto_save": True, "save_threshold": 5, "importance_threshold": 0.5}

    async def initialize(self):
        """初始化智能体和记忆系统"""
        # 加载记忆系统配置
        config_path = os.environ.get(
            "MEMORY_SYSTEM_CONFIG", "/Users/xujian/Athena工作平台/config/memory_system_config.json"
        )

        if os.path.exists(config_path):
            with open(config_path, encoding="utf-8") as f:
                config = json.load(f)

            # 获取当前智能体的配置
            agent_config = config.get("agents", {}).get(self.agent_type, {})
            if agent_config:
                config["current_agent"] = agent_config

        # 初始化记忆系统
        self.memory_system = UnifiedAgentMemorySystem(config=config.get("memory", {}))
        await self.memory_system.initialize()

        # 加载最近的重要记忆
        await self._load_recent_memories()

    async def _load_recent_memories(self):
        """加载最近的重要记忆"""
        try:
            # 获取最近的永恒记忆和热记忆
            recent_memories = await self.memory_system.recall_memory(
                agent_id=self.agent_id,
                query="recent important memories",
                limit=5,
                importance_threshold=0.7,
            )

            for memory in recent_memories:
                self.conversation_context.append(
                    {
                        "type": "memory",
                        "content": memory.get("content"),
                        "timestamp": memory.get("created_at"),
                        "importance": memory.get("importance"),
                    }
                )

        except Exception as e:
            print(f"加载历史记忆失败: {e}")

    async def process_message(self, user_input: str, **kwargs) -> str:
        """处理用户消息"""
        # 保存用户输入到记忆
        if self.memory_config["auto_save"]:
            await self._save_interaction_to_memory(user_input, is_user=True)

        # 添加到对话上下文
        self.conversation_context.append(
            {"type": "user", "content": user_input, "timestamp": datetime.now().isoformat()}
        )

        # 生成响应
        response = await self._generate_response(user_input, **kwargs)

        # 保存响应到记忆
        if self.memory_config["auto_save"]:
            await self._save_interaction_to_memory(response, is_user=False)

        # 添加到对话上下文
        self.conversation_context.append(
            {"type": "agent", "content": response, "timestamp": datetime.now().isoformat()}
        )

        # 自动保存上下文
        await self._auto_save_context()

        return response

    async def _save_interaction_to_memory(self, content: str, is_user: bool):
        """保存交互到记忆系统"""
        try:
            # 根据内容判断重要性
            importance = self._calculate_importance(content)

            # 根据智能体类型确定记忆类型
            memory_type = self._determine_memory_type(content)

            # 保存到记忆系统
            await self.memory_system.store_memory(
                content=content,
                memory_type=memory_type,
                importance=importance,
                emotional_weight=self._calculate_emotional_weight(content),
                family_related=self._is_family_related(content),
                work_related=self._is_work_related(content),
                tags=self._extract_tags(content),
                metadata={
                    "is_user_input": is_user,
                    "agent_type": self.agent_type,
                    "session_id": getattr(self, "session_id", None),
                },
                agent_id=self.agent_id,
            )

        except Exception as e:
            print(f"保存记忆失败: {e}")

    async def _auto_save_context(self):
        """自动保存对话上下文"""
        if len(self.conversation_context) >= self.memory_config["save_threshold"]:
            # 将对话上下文保存为一个整体记忆
            conversation_text = "\n".join(
                [
                    f"{'用户' if ctx['type'] == 'user' else '智能体'}: {ctx['content']}"
                    for ctx in self.conversation_context[-self.memory_config["save_threshold"] :]
                ]
            )

            await self.memory_system.store_memory(
                content=conversation_text,
                memory_type=MemoryType.CONVERSATION,
                importance=0.6,
                metadata={
                    "conversation_context": True,
                    "agent_type": self.agent_type,
                    "turn_count": len(self.conversation_context),
                },
                agent_id=self.agent_id,
            )

    async def search_memories(self, query: str, limit: int = 10):
        """搜索相关记忆"""
        if not self.memory_system:
            return []

        return await self.memory_system.recall_memory(
            agent_id=self.agent_id, query=query, limit=limit
        )

    # 以下方法需要子类实现
    async def _generate_response(self, user_input: str, **kwargs) -> str:
        raise NotImplementedError

    def _calculate_importance(self, content: str) -> float:
        """计算内容重要性"""
        # 默认实现,子类可以重写
        if len(content) > 100:
            return 0.7
        return 0.5

    def _determine_memory_type(self, content: str) -> MemoryType:
        """确定记忆类型"""
        # 默认实现,子类可以重写
        return MemoryType.CONVERSATION

    def _calculate_emotional_weight(self, content: str) -> float:
        """计算情感权重"""
        # 默认实现,子类可以重写
        return 0.5

    def _is_family_related(self, content: str) -> bool:
        """判断是否与家庭相关"""
        # 默认实现,子类可以重写
        family_keywords = ["爸爸", "妈妈", "女儿", "家庭", "家人"]
        return any(keyword in content for keyword in family_keywords)

    def _is_work_related(self, content: str) -> bool:
        """判断是否与工作相关"""
        # 默认实现,子类可以重写
        work_keywords = ["工作", "项目", "专利", "业务", "任务"]
        return any(keyword in content for keyword in work_keywords)

    def _extract_tags(self, content: str) -> list[str]:
        """提取标签"""
        # 默认实现,子类可以重写
        tags = []
        if "?" in content:
            tags.append("问题")
        if "!" in content or "!" in content:
            tags.append("感叹")
        if len(content) > 200:
            tags.append("长文本")
        return tags
