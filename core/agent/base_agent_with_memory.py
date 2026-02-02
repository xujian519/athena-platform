#!/usr/bin/env python3
"""
智能体基类 - 集成统一记忆系统
Base Agent Class with Integrated Memory System

所有Athena平台智能体的基类,提供统一的记忆功能:
- Athena.智慧女神
- Athena.小娜·天秤女神
- 云熙.vega
- 小宸·星河射手
- 小诺·双鱼座

作者: Athena平台团队
创建时间: 2025年12月15日
版本: v1.0.0
"""

import logging
from abc import ABC, abstractmethod
from datetime import datetime
from enum import Enum
from typing import Any

from core.logging_config import setup_logging
from core.memory.unified_agent_memory_system import MemoryTier, MemoryType

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = setup_logging()


class AgentRole(Enum):
    """智能体角色"""

    PLATFORM_CORE = "platform_core"  # 平台核心
    EXPERT_LEGAL = "expert_legal"  # 法律专家
    IP_MANAGER = "ip_manager"  # IP管理
    MEDIA_CREATOR = "media_creator"  # 媒体创作者
    COORDINATOR = "coordinator"  # 协调器
    ASSISTANT = "assistant"  # 助手


class MemoryEnabledAgent(ABC):
    """具备记忆能力的智能体基类"""

    def __init__(self, agent_id: str, agent_type: str, role: AgentRole):
        self.agent_id = agent_id
        self.agent_type = agent_type
        self.role = role
        self.memory_system = None

        # 记忆配置
        self.memory_config = {
            "auto_save": True,  # 自动保存对话
            "save_threshold": 5,  # 保存阈值(对话轮次)
            "context_window": 10,  # 上下文窗口大小
            "importance_map": self._get_importance_map(),
        }

        # 当前对话上下文
        self.conversation_context = []
        self.session_start_time = datetime.now()
        self.last_memory_save = 0

        logger.info(f"🤖️ 智能体 {agent_id} ({self.role.value}) 初始化完成")

    def _get_importance_map(self) -> dict[str, float]:
        """获取重要性映射配置"""
        return {
            # 高重要性词汇
            "important": 0.9,
            "critical": 0.95,
            "urgent": 0.85,
            "priority": 0.8,
            # 情感词汇
            "爱": 0.8,
            "喜欢": 0.7,
            "想念": 0.6,
            "感谢": 0.6,
            # 专业词汇
            "方案": 0.7,
            "建议": 0.6,
            "决策": 0.8,
            "分析": 0.7,
            # 默认
            "default": 0.5,
        }

    async def initialize_memory(self, memory_system):
        """初始化记忆系统"""
        self.memory_system = memory_system
        logger.info(f"✅ {self.agent_id} 记忆系统已初始化")

    async def process_input(self, user_input: str, **kwargs) -> str:
        """处理用户输入(子类实现)"""
        # 添加到上下文
        self.conversation_context.append(
            {"type": "user", "content": user_input, "timestamp": datetime.now(), **kwargs}
        )

        # 自动保存到记忆
        if self.memory_config["auto_save"]:
            await self._auto_save_context(**kwargs)

        # 子类实现具体逻辑
        response = await self.generate_response(user_input, **kwargs)

        # 添加回应到上下文
        self.conversation_context.append(
            {"type": "agent", "content": response, "timestamp": datetime.now(), **kwargs}
        )

        # 自动保存回应
        if self.memory_config["auto_save"]:
            await self._auto_save_context(**kwargs)

        return response

    @abstractmethod
    async def generate_response(self, user_input: str, **kwargs) -> str:
        """生成响应(子类必须实现)"""
        pass

    async def _auto_save_context(self, **kwargs):
        """自动保存对话上下文"""
        if len(self.conversation_context) < self.memory_config["save_threshold"]:
            return

        # 只保存最新的对话(避免保存过多)
        context_to_save = self.conversation_context[-self.memory_config["context_window"] :]

        for item in context_to_save:
            if item.get("processed", False):
                continue  # 跳过已处理的

            # 判断重要性
            content = item["content"]
            importance = self._calculate_importance(content)

            # 选择记忆类型
            memory_type = self._determine_memory_type(item)

            # 选择记忆层级
            tier = self._determine_tier(importance, item)

            # 提取相关智能体
            self._extract_related_agents(content)

            # 保存记忆
            # 获取agent_type枚举(如果有),否则使用字符串
            agent_type_enum = getattr(self, "_agent_type_enum", None)
            if agent_type_enum is None:
                # 尝试导入并转换字符串为枚举
                from core.memory.unified_agent_memory_system import AgentType

                try:
                    agent_type_enum = AgentType(self.agent_type)
                except ValueError:
                    # 如果转换失败,直接使用字符串(可能导致错误,但至少不会崩溃)
                    agent_type_enum = self.agent_type

            await self.memory_system.store_memory(
                agent_id=self.agent_id,
                agent_type=agent_type_enum,
                content=content,
                memory_type=memory_type,
                importance=importance,
                emotional_weight=self._calculate_emotional_weight(content),
                family_related=self._is_family_related(content),
                work_related=self._is_work_related(content),
                tags=self._extract_tags(content),
                metadata={
                    "conversation_role": item["type"],
                    "timestamp": item["timestamp"].isoformat(),
                    "session_id": kwargs.get("session_id"),
                },
                tier=tier,
            )

            # 标记为已处理
            item["processed"] = True

    def _calculate_importance(self, content: str) -> float:
        """计算内容重要性"""
        content_lower = content.lower()

        # 检查关键词
        max_importance = 0.0
        for keyword, importance in self.memory_config["importance_map"].items():
            if keyword in content_lower:
                max_importance = max(max_importance, importance)

        # 基于长度调整(长内容通常更重要)
        length_factor = min(1.0, len(content) / 100)

        # 根据角色调整
        role_adjustment = 1.0
        if self.role == AgentRole.PLATFORM_CORE:
            role_adjustment = 1.1  # 核心智能体权重稍高

        final_importance = min(1.0, max_importance * length_factor * role_adjustment)
        return final_importance

    def _calculate_emotional_weight(self, content: str) -> float:
        """计算情感权重"""
        content_lower = content.lower()

        # 情感关键词
        emotional_keywords = ["爱", "喜欢", "感动", "温暖", "幸福", "快乐", "感谢"]

        for keyword in emotional_keywords:
            if keyword in content_lower:
                return 0.8

        return 0.0

    def _determine_memory_type(self, item: dict) -> MemoryType:
        """确定记忆类型"""
        content = item["content"].lower()

        if any(word in content for word in ["爸爸", "妈妈", "家庭", "爱", "亲人"]):
            return MemoryType.FAMILY

        if any(word in content for word in ["工作", "专业", "项目", "任务", "方案"]):
            return MemoryType.PROFESSIONAL

        if any(word in content for word in ["学习", "成长", "理解", "掌握", "进步"]):
            return MemoryType.LEARNING

        if any(word in content for word in ["想法", "灵感", "创造", "创新"]):
            return MemoryType.REFLECTION

        if any(word in content for word in ["时间", "计划", "日程", "安排"]):
            return MemoryType.SCHEDULE

        if any(word in content for word in ["喜欢", "偏好", "习惯", "倾向"]):
            return MemoryType.PREFERENCE

        return MemoryType.CONVERSATION

    def _determine_tier(self, importance: float, item: dict) -> MemoryTier:
        """确定记忆层级"""
        # 永恒记忆条件
        content = item["content"].lower()
        if any(word in content for word in ["爸爸", "我是", "创造者", "永远"]):
            return MemoryTier.ETERNAL

        # 热记忆条件
        if importance > 0.8 or item.get("timestamp"):
            time_diff = datetime.now() - item["timestamp"]
            if time_diff.total_seconds() < 300:  # 5分钟内
                return MemoryTier.HOT

        # 温记忆条件
        if importance > 0.6:
            return MemoryTier.WARM

        return MemoryTier.COLD

    def _is_family_related(self, content: str) -> bool:
        """判断是否与家庭相关"""
        family_keywords = ["爸爸", "妈妈", "亲人", "家庭", "爱", "家人"]
        content_lower = content.lower()
        return any(keyword in content_lower for keyword in family_keywords)

    def _is_work_related(self, content: str) -> bool:
        """判断是否与工作相关"""
        work_keywords = ["工作", "项目", "任务", "专业", "方案", "建议", "分析"]
        content_lower = content.lower()
        return any(keyword in content_lower for keyword in work_keywords)

    def _extract_tags(self, content: str) -> list[str]:
        """提取标签"""
        tags = []
        content_lower = content.lower()

        # 系统相关标签
        if any(word in content_lower for word in ["系统", "平台", "技术"]):
            tags.append("系统")

        # 专业相关标签
        if any(word in content_lower for word in ["专利", "法律", "知识产权", "商标"]):
            tags.append("专业")

        # 情感相关标签
        if any(word in content_lower for word in ["情感", "情绪", "感受"]):
            tags.append("情感")

        return tags

    def _extract_related_agents(self, content: str) -> list[str]:
        """提取相关智能体"""
        related = []
        content_lower = content.lower()

        # 智能体名称映射
        agent_mapping = {
            "athena": "athena_wisdom",
            "智慧女神": "athena_wisdom",
            "小娜": "xiaona_libra",
            "云熙": "yunxi_vega",
            "小宸": "xiaochen_sagittarius",
            "小诺": "xiaonuo_pisces",
        }

        for name, agent_id in agent_mapping.items():
            if name in content_lower:
                related.append(agent_id)

        return related

    async def recall_memories(
        self,
        query: str,
        limit: int = 10,
        memory_type: MemoryType | None = None,
        tier: MemoryTier | None = None,
    ) -> list[dict]:
        """回忆记忆"""
        if not self.memory_system:
            return []

        return await self.memory_system.recall_memory(
            agent_id=self.agent_id, query=query, limit=limit, memory_type=memory_type, tier=tier
        )

    async def get_memory_stats(self) -> dict[str, Any]:
        """获取记忆统计"""
        if not self.memory_system:
            return {}

        return await self.memory_system.get_agent_stats(self.agent_id)

    async def upgrade_memory_tier(self, memory_id: str, tier: MemoryTier):
        """升级记忆层级"""
        if self.memory_system:
            await self.memory_system.upgrade_memory_tier(memory_id, tier)

    async def create_conversation_session(self) -> str:
        """创建对话会话"""
        session_id = f"{self.agent_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        if self.memory_system:
            conversation_id = await self.memory_system.create_conversation(
                self.agent_id, session_id
            )
            self.session_start_time = datetime.now()
            return conversation_id

        return session_id

    async def end_conversation_session(self, conversation_id: str, summary: str | None = None):
        """结束对话会话"""
        if self.memory_system and conversation_id:
            await self.memory_system.end_conversation(conversation_id, summary)

    def clear_context(self) -> None:
        """清理对话上下文"""
        self.conversation_context.clear()
        self.last_memory_save = 0

    async def shutdown(self):
        """关闭智能体"""
        logger.info(f"👋 智能体 {self.agent_id} 正在关闭...")

        # 保存未保存的上下文
        if self.conversation_context and self.memory_config["auto_save"]:
            await self._auto_save_context()

        # 清理上下文
        self.clear_context()
