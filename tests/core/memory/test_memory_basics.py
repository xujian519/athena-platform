#!/usr/bin/env python3
"""
Athena Memory模块基础测试
Basic Tests for Memory Module

测试内容：
1. 数据模型测试
2. 缓存统计测试
3. 枚举类型测试

作者: Athena AI系统
创建时间: 2026-01-27
版本: v1.0.0
"""

import pytest
from datetime import datetime
from core.memory.unified_memory.types import (
    CacheStatistics,
    AgentType,
    MemoryType,
    MemoryTier,
    AgentIdentity,
    MemoryItem
)


class TestCacheStatistics:
    """测试缓存统计信息"""

    def test_initialization(self):
        """测试初始化"""
        stats = CacheStatistics()
        assert stats.hits == 0
        assert stats.misses == 0
        assert stats.total_requests == 0
        assert stats.hit_rate == 0.0

    def test_record_hit(self):
        """测试记录命中"""
        stats = CacheStatistics()
        stats.record_hit()
        assert stats.hits == 1
        assert stats.total_requests == 1
        assert stats.hit_rate == 1.0

    def test_record_miss(self):
        """测试记录未命中"""
        stats = CacheStatistics()
        stats.record_miss()
        assert stats.misses == 1
        assert stats.total_requests == 1
        assert stats.hit_rate == 0.0

    def test_multiple_records(self):
        """测试多次记录"""
        stats = CacheStatistics()
        for _ in range(7):
            stats.record_hit()
        for _ in range(3):
            stats.record_miss()
        assert stats.hits == 7
        assert stats.misses == 3
        assert stats.total_requests == 10
        assert stats.hit_rate == 0.7

    def test_get_stats(self):
        """测试获取统计信息"""
        stats = CacheStatistics()
        stats.record_hit()
        stats.record_miss()
        stats_dict = stats.get_stats()
        assert stats_dict["hits"] == 1
        assert stats_dict["misses"] == 1
        assert stats_dict["total_requests"] == 2
        assert stats_dict["hit_rate"] == 0.5


class TestAgentType:
    """测试智能体类型枚举"""

    def test_agent_types(self):
        """测试所有智能体类型"""
        assert AgentType.ATHENA.value == "athena"
        assert AgentType.XIAONA.value == "xiaona"
        assert AgentType.YUNXI.value == "yunxi"
        assert AgentType.XIAOCHEN.value == "xiaochen"
        assert AgentType.XIAONUO.value == "xiaonuo"

    def test_agent_type_string_representation(self):
        """测试字符串表示"""
        assert str(AgentType.ATHENA) == "AgentType.ATHENA"
        assert AgentType.ATHENA.name == "ATHENA"


class TestMemoryType:
    """测试记忆类型枚举"""

    def test_memory_types(self):
        """测试所有记忆类型"""
        assert MemoryType.CONVERSATION.value == "conversation"
        assert MemoryType.EMOTIONAL.value == "emotional"
        assert MemoryType.KNOWLEDGE.value == "knowledge"
        assert MemoryType.FAMILY.value == "family"
        assert MemoryType.PROFESSIONAL.value == "professional"
        assert MemoryType.LEARNING.value == "learning"


class TestMemoryTier:
    """测试记忆层级枚举"""

    def test_memory_tiers(self):
        """测试所有记忆层级"""
        assert MemoryTier.HOT.value == "hot"
        assert MemoryTier.WARM.value == "warm"
        assert MemoryTier.COLD.value == "cold"
        assert MemoryTier.ETERNAL.value == "eternal"


class TestAgentIdentity:
    """测试智能体身份信息"""

    def test_creation(self):
        """测试创建智能体身份"""
        identity = AgentIdentity(
            agent_id="test_agent",
            agent_type=AgentType.XIAONUO,
            name="测试智能体",
            english_name="Test Agent",
            role="测试角色",
            description="这是一个测试智能体"
        )
        assert identity.agent_id == "test_agent"
        assert identity.agent_type == AgentType.XIAONUO
        assert identity.name == "测试智能体"

    def test_default_values(self):
        """测试默认值"""
        identity = AgentIdentity(
            agent_id="test_agent",
            agent_type=AgentType.ATHENA,
            name="Athena",
            english_name="Athena",
            role="智慧女神",
            description="智慧女神"
        )
        assert identity.special_tags == []
        identity.special_tags.append("test")
        assert len(identity.special_tags) == 1


class TestMemoryItem:
    """测试记忆项"""

    def test_creation(self):
        """测试创建记忆项"""
        item = MemoryItem(
            id="test_memory_1",
            agent_id="test_agent",
            agent_type=AgentType.XIAONUO,
            content="这是一条测试记忆",
            memory_type=MemoryType.CONVERSATION,
            memory_tier=MemoryTier.WARM
        )
        assert item.id == "test_memory_1"
        assert item.agent_id == "test_agent"
        assert item.content == "这是一条测试记忆"
        assert item.memory_type == MemoryType.CONVERSATION
        assert item.memory_tier == MemoryTier.WARM
        assert isinstance(item.created_at, datetime)

    def test_metadata(self):
        """测试元数据"""
        item = MemoryItem(
            id="test_memory_2",
            agent_id="test_agent",
            agent_type=AgentType.ATHENA,
            content="测试内容",
            memory_type=MemoryType.KNOWLEDGE,
            memory_tier=MemoryTier.COLD,
            metadata={"key": "value"}
        )
        assert item.metadata == {"key": "value"}

    def test_vector_embedding(self):
        """测试嵌入向量"""
        item = MemoryItem(
            id="test_memory_3",
            agent_id="test_agent",
            agent_type=AgentType.XIAONA,
            content="测试内容",
            memory_type=MemoryType.CONVERSATION,
            memory_tier=MemoryTier.HOT,
            vector_embedding=[0.1, 0.2, 0.3]
        )
        assert item.vector_embedding == [0.1, 0.2, 0.3]

    def test_access_count(self):
        """测试访问计数"""
        item = MemoryItem(
            id="test_memory_4",
            agent_id="test_agent",
            agent_type=AgentType.YUNXI,
            content="测试内容",
            memory_type=MemoryType.CONVERSATION,
            memory_tier=MemoryTier.HOT
        )
        assert item.access_count == 0
        item.access_count += 1
        assert item.access_count == 1


class TestMemoryIntegration:
    """集成测试：测试多个组件的协同工作"""

    def test_agent_with_memory(self):
        """测试智能体与记忆的关联"""
        agent = AgentIdentity(
            agent_id="xiaonuo_pisces",
            agent_type=AgentType.XIAONUO,
            name="小诺·双鱼座",
            english_name="Xiaonuo Pisces",
            role="专利专家",
            description="专利分析专家"
        )

        memory = MemoryItem(
            id="memory_1",
            agent_id=agent.agent_id,
            agent_type=agent.agent_type,
            content="用户询问了专利检索的问题",
            memory_type=MemoryType.CONVERSATION,
            memory_tier=MemoryTier.WARM
        )

        assert memory.agent_id == agent.agent_id
        assert memory.memory_type == MemoryType.CONVERSATION

    def test_statistics_tracking(self):
        """测试统计追踪"""
        stats = CacheStatistics()
        items = [
            MemoryItem(
                id=f"memory_{i}",
                agent_id=f"agent_{i}",
                agent_type=AgentType.XIAONUO,
                content=f"记忆内容{i}",
                memory_type=MemoryType.CONVERSATION,
                memory_tier=MemoryTier.HOT
            )
            for i in range(10)
        ]

        # 模拟缓存命中和未命中
        for _ in items[:7]:
            stats.record_hit()  # 7次命中
        for _ in items[7:]:
            stats.record_miss()  # 3次未命中

        assert stats.total_requests == 10
        assert stats.hit_rate == 0.7
        assert stats.get_stats()["hits"] == 7
        assert stats.get_stats()["misses"] == 3
