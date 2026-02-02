#!/usr/bin/env python3
"""
Athena Memory模块 - Phase 2核心测试
Core Tests for Memory Module - Phase 2

测试内容：
1. UnifiedAgentMemorySystem初始化
2. 异步存储操作
3. 异步检索操作
4. 缓存机制

作者: Athena AI系统
创建时间: 2026-01-27
版本: v2.0.0 (Phase 2)
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

from core.memory.unified_memory import (
    UnifiedAgentMemorySystem,
    AgentType,
    MemoryType,
    MemoryTier,
    CacheStatistics
)
import json


@pytest.mark.asyncio
class TestUnifiedAgentMemorySystemInit:
    """测试UnifiedAgentMemorySystem初始化"""

    async def test_system_creation(self):
        """测试系统创建"""
        system = UnifiedAgentMemorySystem()
        assert system.system_name == "Athena统一智能体记忆系统"
        assert system.version == "v1.0.0 永恒记忆"
        assert system.db_config is not None

    async def test_db_config_structure(self):
        """测试数据库配置结构"""
        system = UnifiedAgentMemorySystem()

        # 检查PostgreSQL配置
        assert "postgresql" in system.db_config
        pg_config = system.db_config["postgresql"]
        assert "host" in pg_config
        assert "port" in pg_config
        assert pg_config["port"] == 5432

        # 检查Redis配置
        assert "redis" in system.db_config
        redis_config = system.db_config["redis"]
        assert "host" in redis_config
        assert "port" in redis_config

        # 检查TTL配置
        assert "ttl" in redis_config
        ttl_config = redis_config["ttl"]
        assert "agent_stats" in ttl_config
        assert "search_results" in ttl_config

    @pytest.mark.skip(reason="需要外部数据库连接")
    async def test_full_initialization(self):
        """测试完整初始化（需要数据库）"""
        system = UnifiedAgentMemorySystem()
        await system.initialize()
        # 验证初始化成功
        assert system.postgresql_pool is not None
        assert system.redis_client is not None


@pytest.mark.asyncio
class TestMemoryValidation:
    """测试记忆验证功能"""

    async def test_validate_normal_content(self):
        """测试验证正常内容"""
        system = UnifiedAgentMemorySystem()
        content = "这是一条正常的记忆内容"

        # 不应该抛出异常
        system._validate_memory_content(content)

    async def test_validate_empty_content(self):
        """测试验证空内容"""
        system = UnifiedAgentMemorySystem()

        with pytest.raises(ValueError, match="记忆内容必须是非空字符串"):
            system._validate_memory_content("")

    async def test_validate_too_long_content(self):
        """测试验证超长内容"""
        system = UnifiedAgentMemorySystem()
        long_content = "x" * 10001

        with pytest.raises(ValueError, match="记忆内容过长"):
            system._validate_memory_content(long_content)

    async def test_validate_custom_max_length(self):
        """测试自定义最大长度"""
        system = UnifiedAgentMemorySystem()
        content = "x" * 101

        with pytest.raises(ValueError, match="记忆内容过长"):
            system._validate_memory_content(content, max_length=100)


@pytest.mark.asyncio
class TestMemoryStorage:
    """测试记忆存储功能"""

    async def test_store_memory_basic(self, initialized_system):
        """测试基本存储功能"""
        # Mock _cache_hot_memory (不需要实际调用)
        with patch.object(initialized_system, '_cache_hot_memory'):
            memory_id = await initialized_system.store_memory(
                agent_id="xiaonuo_pisces",
                agent_type=AgentType.XIAONUO,
                content="用户询问了专利检索问题",
                memory_type=MemoryType.CONVERSATION,
                tier=MemoryTier.WARM
            )

        assert memory_id is not None

    async def test_store_memory_with_metadata(self, initialized_system):
        """测试带元数据的存储"""
        metadata = {"source": "user_query", "topic": "patent_search"}

        with patch.object(initialized_system, '_cache_hot_memory'):
            memory_id = await initialized_system.store_memory(
                agent_id="xiaonuo_pisces",
                agent_type=AgentType.XIAONUO,
                content="专利检索咨询",
                memory_type=MemoryType.CONVERSATION,
                tier=MemoryTier.WARM,
                metadata=metadata
            )

        assert memory_id is not None

    async def test_store_memory_validation_error(self):
        """测试存储时验证错误"""
        from tests.core.memory.conftest import MockConnectionPool, MockQdrantClient

        system = UnifiedAgentMemorySystem()
        # 设置初始化标志以通过初始化检查
        system._initialized = True
        # 设置pg_pool以通过PostgreSQL检查
        system.pg_pool = MockConnectionPool()
        # 设置qdrant_client以通过Qdrant检查
        system.qdrant_client = MockQdrantClient()

        with pytest.raises(ValueError, match="记忆内容必须是非空字符串"):
            await system.store_memory(
                agent_id="xiaonuo_pisces",
                agent_type=AgentType.XIAONUO,
                content="",  # 空内容
                memory_type=MemoryType.CONVERSATION,
                tier=MemoryTier.WARM
            )


@pytest.mark.asyncio
class TestMemoryRetrieval:
    """测试记忆检索功能"""

    async def test_recall_memory_by_id(self, initialized_system):
        """测试通过agent_id和query回忆记忆"""
        # Mock数据库返回 - 注意recall_memory现在返回的是list
        async def mock_fetch(*args, **kwargs):
            return [
                {
                    "id": "test_memory_1",
                    "agent_id": "xiaonuo_pisces",
                    "agent_type": "xiaonuo",
                    "content": "用户询问了专利检索问题",
                    "memory_type": "conversation",
                    "memory_tier": "warm",
                    "importance": 0.7,
                    "created_at": datetime.now(),
                    "last_accessed": datetime.now(),
                    "access_count": 1
                }
            ]

        initialized_system.postgresql_pool.fetch = mock_fetch

        memories = await initialized_system.recall_memory(
            agent_id="xiaonuo_pisces",
            query="专利检索"
        )

        assert memories is not None
        assert len(memories) >= 1
        assert memories[0]["id"] == "test_memory_1"
        assert memories[0]["content"] == "用户询问了专利检索问题"

    async def test_recall_memory_not_found(self, initialized_system):
        """测试回忆不存在的记忆"""
        # Mock数据库返回空列表
        async def mock_fetch(*args, **kwargs):
            return []

        initialized_system.postgresql_pool.fetch = mock_fetch

        memories = await initialized_system.recall_memory(
            agent_id="xiaonuo_pisces",
            query="不存在的查询"
        )
        assert memories == []


@pytest.mark.asyncio
class TestMemorySearch:
    """测试记忆搜索功能"""

    async def test_search_memories_basic(self, initialized_system):
        """测试基本搜索功能"""
        # Mock搜索结果
        async def mock_fetch(*args, **kwargs):
            return [
                {
                    "id": "mem_1",
                    "content": "专利检索相关问题",
                    "memory_type": "conversation",
                    "similarity": 0.9
                },
                {
                    "id": "mem_2",
                    "content": "专利分析结果",
                    "memory_type": "knowledge",
                    "similarity": 0.8
                }
            ]

        initialized_system.postgresql_pool.fetch = mock_fetch

        results = await initialized_system.search_memories(
            agent_id="xiaonuo_pisces",
            query="专利检索",
            limit=5
        )

        assert len(results) == 2
        assert results[0]["similarity"] > results[1]["similarity"]

    async def test_search_with_memory_type_filter(self, initialized_system):
        """测试带记忆类型过滤的搜索"""
        async def mock_fetch(*args, **kwargs):
            return [
                {
                    "id": "mem_1",
                    "content": "专业知识记忆",
                    "memory_type": "knowledge"
                }
            ]

        initialized_system.postgresql_pool.fetch = mock_fetch

        results = await initialized_system.search_memories(
            agent_id="xiaonuo_pisces",
            query="专利",
            memory_type=MemoryType.KNOWLEDGE,
            limit=10
        )

        assert len(results) >= 0
        for result in results:
            assert result["memory_type"] == "knowledge"


@pytest.mark.asyncio
class TestCacheMechanism:
    """测试缓存机制"""

    async def test_hot_memory_cache(self, initialized_system):
        """测试热记忆缓存"""
        # _cache_hot_memory需要独立参数，不是MemoryItem对象
        initialized_system._cache_hot_memory(
            agent_id="xiaonuo_pisces",
            memory_id="test_hot_1",
            content="当前会话的重要记忆",
            memory_type=MemoryType.CONVERSATION
        )

        # 验证缓存已存储 - 使用字符串key
        assert "xiaonuo_pisces" in initialized_system.hot_caches

    async def test_search_hot_cache(self):
        """测试搜索热缓存"""
        system = UnifiedAgentMemorySystem()
        # 使用字符串作为key
        system.hot_caches = {
            "xiaonuo_pisces": {
                "test_mem_1": {
                    "id": "test_mem_1",
                    "content": "专利相关问题",
                    "type": "conversation"  # 使用"type"而不是"memory_type"
                }
            }
        }

        results = system._search_hot_cache(
            agent_id="xiaonuo_pisces",
            query="专利",
            memory_type=None,  # 不过滤类型
            limit=10
        )

        assert len(results) == 1
        assert results[0]["memory_id"] == "test_mem_1"

    async def test_cache_invalidation(self, initialized_system):
        """测试缓存失效"""
        # 应该不抛出异常
        await initialized_system._invalidate_agent_caches("xiaonuo_pisces")


@pytest.mark.asyncio
class TestAgentStats:
    """测试智能体统计功能"""

    async def test_get_agent_stats(self, initialized_system):
        """测试获取智能体统计"""
        # 不要覆盖cache_stats，它应该是一个CacheStatistics对象
        # initialized_system.cache_stats已经在fixture中设置为CacheStatistics()

        # Mock数据库返回
        async def mock_fetchrow(*args, **kwargs):
            return {
                "agent_id": "xiaonuo_pisces",
                "agent_type": "xiaonuo",
                "total_memories": 100,
                "hot_memories": 20,
                "warm_memories": 50,
                "cold_memories": 30,
                "eternal_memories": 0
            }

        initialized_system.postgresql_pool.fetchrow = mock_fetchrow

        # Mock Redis缓存
        async def mock_get(*args, **kwargs):
            return None  # 返回None以测试数据库查询路径

        initialized_system.redis_client.get = mock_get

        stats = await initialized_system.get_agent_stats("xiaonuo_pisces")

        assert stats is not None
        assert "total_memories" in stats
        assert stats["total_memories"] == 100

    async def test_get_agent_stats_empty_cache(self, initialized_system):
        """测试获取智能体统计（空缓存）"""
        # Mock数据库返回
        async def mock_fetchrow(*args, **kwargs):
            return {
                "agent_id": "xiaonuo_pisces",
                "agent_type": "xiaonuo",
                "total_memories": 50,
                "hot_memories": 10,
                "warm_memories": 20,
                "cold_memories": 20,
                "eternal_memories": 0
            }

        initialized_system.postgresql_pool.fetchrow = mock_fetchrow

        # Mock Redis返回None
        async def mock_get(*args, **kwargs):
            return None

        initialized_system.redis_client.get = mock_get

        stats = await initialized_system.get_agent_stats("xiaonuo_pisces")

        assert stats is not None
        assert stats["total_memories"] == 50


@pytest.mark.asyncio
class TestMemorySharing:
    """测试记忆共享功能"""

    async def test_share_memory(self, initialized_system):
        """测试记忆共享"""
        # Mock验证记忆存在
        async def mock_fetchval(*args, **kwargs):
            return "xiaonuo_pisces"  # 记忆属于该agent

        initialized_system.postgresql_pool.fetchval = mock_fetchval

        result = await initialized_system.share_memory(
            memory_id="test_mem_1",
            target_agents=["xiaona_libra", "yunxi_vega"]
        )

        assert result is True

    async def test_share_memory_not_owner(self, initialized_system):
        """测试分享不拥有的记忆"""
        # Mock验证记忆不存在或不属于该agent
        async def mock_fetchval(*args, **kwargs):
            return None

        initialized_system.postgresql_pool.fetchval = mock_fetchval

        result = await initialized_system.share_memory(
            memory_id="test_mem_1",
            target_agents=["xiaona_libra"]
        )

        assert result is False


@pytest.mark.asyncio
class TestEmbeddingGeneration:
    """测试嵌入生成功能"""

    async def test_generate_embedding_with_model(self):
        """测试使用模型生成嵌入（需要模型）"""
        system = UnifiedAgentMemorySystem()

        # 当没有模型时，应该使用MD5 fallback
        embedding = await system._generate_embedding("测试文本")

        assert isinstance(embedding, list)
        assert len(embedding) == 1024  # MD5 fallback产生1024维向量
        assert all(isinstance(x, float) for x in embedding)

    async def test_generate_md5_embedding(self):
        """测试MD5 fallback嵌入"""
        system = UnifiedAgentMemorySystem()

        embedding = await system._generate_md5_embedding("测试文本")

        assert len(embedding) == 1024
        assert all(0 <= x <= 1 for x in embedding)

    async def test_embedding_consistency(self):
        """测试嵌入一致性"""
        system = UnifiedAgentMemorySystem()

        text = "一致性测试文本"
        embedding1 = await system._generate_md5_embedding(text)
        embedding2 = await system._generate_md5_embedding(text)

        # 相同文本应该产生相同的嵌入
        assert embedding1 == embedding2

    async def test_embedding_uniqueness(self):
        """测试嵌入唯一性"""
        system = UnifiedAgentMemorySystem()

        embedding1 = await system._generate_md5_embedding("文本1")
        embedding2 = await system._generate_md5_embedding("文本2")

        # 不同文本应该产生不同的嵌入
        assert embedding1 != embedding2
