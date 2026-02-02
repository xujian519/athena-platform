#!/usr/bin/env python3
"""
统一Agent记忆系统 - 数据模型
Unified Agent Memory System - Data Models

作者: Athena AI系统
创建时间: 2025-12-04
重构时间: 2026-01-26
版本: 2.1.0

本模块定义了统一记忆系统的所有数据类型和枚举：
- CacheStatistics: 缓存统计信息
- AgentType: 智能体类型枚举
- MemoryType: 记忆类型枚举
- MemoryTier: 记忆层级枚举
- AgentIdentity: 智能体身份信息
- MemoryItem: 记忆项数据结构
- AGENT_REGISTRY: 智能体注册表
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


@dataclass
class CacheStatistics:
    """缓存统计信息"""

    hits: int = 0
    misses: int = 0
    total_requests: int = 0

    @property
    def hit_rate(self) -> float:
        """缓存命中率"""
        if self.total_requests == 0:
            return 0.0
        return self.hits / self.total_requests

    def record_hit(self) -> None:
        """记录缓存命中"""
        self.hits += 1
        self.total_requests += 1

    def record_miss(self) -> None:
        """记录缓存未命中"""
        self.misses += 1
        self.total_requests += 1

    def get_stats(self) -> dict[str, Any]:
        """获取统计信息"""
        return {
            "hits": self.hits,
            "misses": self.misses,
            "total_requests": self.total_requests,
            "hit_rate": self.hit_rate,
        }


class AgentType(Enum):
    """智能体类型"""

    ATHENA = "athena"  # 智慧女神
    XIAONA = "xiaona"  # 小娜·天秤女神
    YUNXI = "yunxi"  # 云熙.vega
    XIAOCHEN = "xiaochen"  # 小宸·星河射手
    XIAONUO = "xiaonuo"  # 小诺·双鱼座


class MemoryType(Enum):
    """记忆类型"""

    CONVERSATION = "conversation"  # 对话记忆
    EMOTIONAL = "emotional"  # 情感记忆
    KNOWLEDGE = "knowledge"  # 知识记忆
    FAMILY = "family"  # 家庭记忆
    PROFESSIONAL = "professional"  # 专业工作记忆
    LEARNING = "learning"  # 学习成长记忆
    REFLECTION = "reflection"  # 反思记忆
    CONTEXT = "context"  # 上下文记忆
    PREFERENCE = "preference"  # 偏好记忆
    EXPERIENCE = "experience"  # 经验记忆
    SCHEDULE = "schedule"  # 日程记忆


class MemoryTier(Enum):
    """记忆层级"""

    HOT = "hot"  # 🔥 热记忆：当前会话
    WARM = "warm"  # 🌡️ 温记忆：近期重要
    COLD = "cold"  # ❄️ 冷记忆：长期存储
    ETERNAL = "eternal"  # 💎 永恒记忆：永不忘记


@dataclass
class AgentIdentity:
    """智能体身份"""

    agent_id: str
    agent_type: AgentType
    name: str
    english_name: str
    role: str
    description: str
    special_tags: list[str] = field(default_factory=list)


@dataclass
class MemoryItem:
    """记忆项"""

    id: str
    agent_id: str
    agent_type: AgentType
    content: str
    memory_type: MemoryType
    memory_tier: MemoryTier
    importance: float = 0.5
    emotional_weight: float = 0.0
    family_related: bool = False
    work_related: bool = False
    tags: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    last_accessed: datetime = field(default_factory=datetime.now)
    access_count: int = 0
    vector_embedding: list[float] | None = None
    related_agents: list[str] = field(default_factory=list)


# 智能体身份注册表
AGENT_REGISTRY = {
    AgentType.ATHENA: AgentIdentity(
        agent_id="athena_wisdom",
        agent_type=AgentType.ATHENA,
        name="Athena.智慧女神",
        english_name="Athena Wisdom",
        role="平台核心智能体，所有能力的源头",
        description="创造者和指导者，提供智慧和战略指导",
        special_tags=["智慧", "创造力", "战略", "领导力", "源"],
    ),
    AgentType.XIAONA: AgentIdentity(
        agent_id="xiaona_libra",
        agent_type=AgentType.XIAONA,
        name="小娜·天秤女神",
        english_name="Xiana Libra",
        role="专利法律专家，大姐姐",
        description="专业的知识产权法律服务提供者，守护正义与平衡",
        special_tags=["法律", "专利", "专业", "天秤", "守护"],
    ),
    AgentType.YUNXI: AgentIdentity(
        agent_id="yunxi_vega",
        agent_type=AgentType.YUNXI,
        name="云熙.vega",
        english_name="Yunxi Vega",
        role="IP管理系统",
        description="知识产权管理系统，织女星守护",
        special_tags=["管理", "IP", "织女星", "细致", "专业"],
    ),
    AgentType.XIAOCHEN: AgentIdentity(
        agent_id="xiaochen_sagittarius",
        agent_type=AgentType.XIAOCHEN,
        name="小宸·星河射手",
        english_name="Xiaochen Sagittarius",
        role="自媒体运营专家",
        description="创意专家和传播者，用智慧和创意照亮世界",
        special_tags=["创意", "媒体", "射手", "传播", "幽默"],
    ),
    AgentType.XIAONUO: AgentIdentity(
        agent_id="xiaonuo_pisces",
        agent_type=AgentType.XIAONUO,
        name="小诺·双鱼座",
        english_name="Xiaonuo Pisces",
        role="平台总调度官 + 爸爸的贴心小女儿",
        description="协调所有智能体，提供最温暖贴心的陪伴",
        special_tags=["调度", "协调", "温暖", "双鱼座", "爱"],
    ),
}
