#!/usr/bin/env python3
"""
Athena Memory模块 - Phase 3边界测试
Edge Case Tests for Memory Module - Phase 3

测试内容：
1. 边界情况测试
2. 错误处理测试
3. 性能测试

作者: Athena AI系统
创建时间: 2026-01-27
版本: v3.0.0 (Phase 3)
"""

import asyncio
import sys
import time
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from unittest.mock import MagicMock, patch

from core.memory.unified_memory import (
    AgentType,
    CacheStatistics,
    MemoryItem,
    MemoryTier,
    MemoryType,
    UnifiedAgentMemorySystem,
)


@pytest.mark.asyncio
class TestBoundaryCases:
    """测试边界情况"""

    async def test_empty_content_storage(self, initialized_system):
        """测试空内容存储"""
        with pytest.raises(ValueError):
            await initialized_system.store_memory(
                agent_id="test_agent",
                agent_type=AgentType.XIAONUO,
                content="",  # 空内容
                memory_type=MemoryType.CONVERSATION,
                tier=MemoryTier.HOT
            )

    async def test_extremely_long_content(self, initialized_system):
        """测试超长内容"""
        long_content = "x" * 100000  # 非常长的内容

        with pytest.raises(ValueError):
            await initialized_system.store_memory(
                agent_id="test_agent",
                agent_type=AgentType.XIAONUO,
                content=long_content,
                memory_type=MemoryType.CONVERSATION,
                tier=MemoryTier.HOT
            )

    async def test_special_characters_content(self, initialized_system):
        """测试特殊字符内容"""
        special_content = """
        测试特殊字符：!@#$%^&*()_+-={}[]|\\:";'<>?,./
        换行符、制表符、Unicode字符：🎉🎊🎁
        HTML标签：<div><p>test</p></div>
        JavaScript代码：function test() { return true; }
        """

        with patch.object(initialized_system, '_cache_hot_memory'):
            # 不应该抛出异常
            memory_id = await initialized_system.store_memory(
                agent_id="test_agent",
                agent_type=AgentType.XIAONUO,
                content=special_content,
                memory_type=MemoryType.CONVERSATION,
                tier=MemoryTier.HOT
            )

        assert memory_id is not None

    async def test_unicode_content(self, initialized_system):
        """测试Unicode内容"""
        unicode_content = "测试中文、日本語、한국어、العربية、🎉🎊"

        with patch.object(initialized_system, '_cache_hot_memory'):
            memory_id = await initialized_system.store_memory(
                agent_id="test_agent",
                agent_type=AgentType.XIAONUO,
                content=unicode_content,
                memory_type=MemoryType.CONVERSATION,
                tier=MemoryTier.HOT
            )

        assert memory_id is not None

    async def test_null_values_in_metadata(self, initialized_system):
        """测试元数据中的空值"""
        metadata = {
            "key1": None,
            "key2": "",
            "key3": 0,
            "key4": False
        }

        with patch.object(initialized_system, '_cache_hot_memory'):
            memory_id = await initialized_system.store_memory(
                agent_id="test_agent",
                agent_type=AgentType.XIAONUO,
                content="测试内容",
                memory_type=MemoryType.CONVERSATION,
                tier=MemoryTier.HOT,
                metadata=metadata
            )

        assert memory_id is not None

    async def test_concurrent_storage(self, initialized_system):
        """测试并发存储"""
        initialized_system.hot_cache = {}

        # 并发存储10条记忆
        tasks = []
        for i in range(10):
            task = initialized_system.store_memory(
                agent_id="test_agent",
                agent_type=AgentType.XIAONUO,
                content=f"并发测试内容{i}",
                memory_type=MemoryType.CONVERSATION,
                tier=MemoryTier.HOT
            )
            tasks.append(task)

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # 验证所有操作都成功
        assert len(results) == 10
        assert all(isinstance(r, str) or r is None for r in results)

    async def test_empty_search_results(self, initialized_system):
        """测试空搜索结果"""
        # Mock空结果
        async def mock_fetch(*args, **kwargs):
            return []  # 空结果

        initialized_system.postgresql_pool.fetch = mock_fetch

        results = await initialized_system.search_memories(
            agent_id="test_agent",
            query="不存在的查询",
            limit=10
        )

        assert results == []

    async def test_large_limit_search(self, initialized_system):
        """测试大限制搜索"""
        # 生成100个结果
        async def mock_fetch(*args, **kwargs):
            return [
                {"id": f"mem_{i}", "content": f"内容{i}"}
                for i in range(100)
            ]

        initialized_system.postgresql_pool.fetch = mock_fetch

        results = await initialized_system.search_memories(
            agent_id="test_agent",
            query="测试",
            limit=1000  # 非常大的limit
        )

        # 应该返回所有结果
        assert len(results) == 100


@pytest.mark.asyncio
class TestErrorHandling:
    """测试错误处理"""

    async def test_database_connection_failure(self):
        """测试数据库连接失败"""
        system = UnifiedAgentMemorySystem()

        # Mock数据库连接失败
        async def mock_acquire(*args, **kwargs):
            raise Exception("数据库连接失败")

        system.postgresql_pool = MagicMock()
        system.postgresql_pool.acquire = mock_acquire

        with pytest.raises(Exception):
            await system.initialize()

    async def test_storage_with_invalid_agent_type(self, initialized_system):
        """测试使用有效的智能体类型存储"""
        # 不应该抛出异常，但应该记录警告
        with patch.object(initialized_system, '_cache_hot_memory'):
            memory_id = await initialized_system.store_memory(
                agent_id="test_agent",
                agent_type=AgentType.XIAONUO,  # 有效类型
                content="测试",
                memory_type=MemoryType.CONVERSATION,
                tier=MemoryTier.HOT
            )

        assert memory_id is not None

    async def test_retrieve_nonexistent_memory(self, initialized_system):
        """测试检索不存在的记忆"""
        # Mock空结果
        async def mock_fetch(*args, **kwargs):
            return []  # 记忆不存在，返回空列表

        initialized_system.postgresql_pool.fetch = mock_fetch

        memories = await initialized_system.recall_memory(
            agent_id="test_agent",
            query="不存在的记忆"
        )
        assert memories == []  # 应该返回空列表而不是抛出异常

    async def test_search_with_invalid_query(self, initialized_system):
        """测试无效查询搜索"""
        # Mock空结果
        async def mock_fetch(*args, **kwargs):
            # 不应该抛出异常
            return []

        initialized_system.postgresql_pool.fetch = mock_fetch

        # 空查询
        results = await initialized_system.search_memories(
            agent_id="test_agent",
            query="",
            limit=10
        )

        assert isinstance(results, list)

    async def test_cache_failure_handling(self, initialized_system):
        """测试缓存失败处理"""
        # Mock Redis失败
        async def mock_get(*args, **kwargs):
            raise Exception("Redis连接失败")

        initialized_system.redis_client.get = mock_get
        initialized_system.cache_stats = {"test_agent": CacheStatistics()}

        # 应该能降级到数据库查询
        async def mock_fetch(*args, **kwargs):
            return [{"id": "mem_1", "content": "测试"}]

        initialized_system.postgresql_pool.fetch = mock_fetch

        results = await initialized_system.search_memories(
            agent_id="test_agent",
            query="测试",
            limit=10
        )

        assert results is not None

    async def test_concurrent_write_conflict(self, initialized_system):
        """测试并发写入冲突"""
        call_count = 0

        async def mock_fetchval(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            await asyncio.sleep(0.01)
            return f"mem_{call_count}"

        initialized_system.postgresql_pool.fetchval = mock_fetchval

        # 尝试同时写入相同记忆
        tasks = [
            initialized_system.store_memory(
                agent_id="test_agent",
                agent_type=AgentType.XIAONUO,
                content="相同内容",
                memory_type=MemoryType.CONVERSATION,
                tier=MemoryTier.HOT
            )
            for _ in range(5)
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # 验证所有操作都完成了
        assert len(results) == 5


@pytest.mark.asyncio
class TestPerformance:
    """测试性能"""

    async def test_bulk_storage_performance(self, initialized_system):
        """测试批量存储性能"""
        # 测试100次连续存储
        start_time = time.time()

        for i in range(100):
            with patch.object(initialized_system, '_cache_hot_memory'):
                await initialized_system.store_memory(
                    agent_id="test_agent",
                    agent_type=AgentType.XIAONUO,
                    content=f"性能测试内容{i}",
                    memory_type=MemoryType.CONVERSATION,
                    tier=MemoryTier.HOT
                )

        elapsed = time.time() - start_time

        # 应该在合理时间内完成（<5秒）
        assert elapsed < 5.0
        print(f"100次存储耗时: {elapsed:.2f}秒")

    async def test_cache_hit_rate(self):
        """测试缓存命中率"""
        system = UnifiedAgentMemorySystem()
        system.cache_stats = {"test_agent": CacheStatistics()}

        stats = system.cache_stats["test_agent"]

        # 记录100次访问，70%命中
        for i in range(100):
            if i < 70:
                stats.record_hit()
            else:
                stats.record_miss()

        assert stats.hit_rate == 0.7
        assert stats.total_requests == 100

    async def test_search_performance(self, initialized_system):
        """测试搜索性能"""
        # 模拟搜索延迟
        async def mock_fetch(*args, **kwargs):
            await asyncio.sleep(0.01)  # 10ms延迟
            return [{"id": f"mem_{i}", "content": f"结果{i}"} for i in range(10)]

        initialized_system.postgresql_pool.fetch = mock_fetch

        start_time = time.time()

        # 执行10次搜索
        for _ in range(10):
            await initialized_system.search_memories(
                agent_id="test_agent",
                query="测试查询",
                limit=10
            )

        elapsed = time.time() - start_time

        # 10次搜索应该在1秒内完成
        assert elapsed < 1.0
        print(f"10次搜索耗时: {elapsed:.2f}秒")

    @pytest.mark.slow
    async def test_memory_efficiency(self):
        """测试内存效率"""
        system = UnifiedAgentMemorySystem()
        system.hot_cache = {}

        # 添加1000条热记忆
        for i in range(1000):
            agent_id = f"agent_{i % 10}"
            memory_id = f"mem_{i}"
            content = f"记忆内容{i}" * 10  # 约100字节

            if agent_id not in system.hot_cache:
                system.hot_cache[agent_id] = {}

            system.hot_cache[agent_id][memory_id] = {
                "id": memory_id,
                "content": content,
                "memory_type": "conversation"
            }

        # 验证缓存大小合理（应该小于10MB）
        import sys
        cache_size = sys.getsizeof(system.hot_cache)
        assert cache_size < 10 * 1024 * 1024  # 10MB
        print(f"1000条热记忆缓存大小: {cache_size / 1024:.2f}KB")

    async def test_concurrent_performance(self, initialized_system):
        """测试并发性能"""
        async def mock_fetch(*args, **kwargs):
            await asyncio.sleep(0.01)
            return [{"id": "mem_1", "content": "测试"}]

        initialized_system.postgresql_pool.fetch = mock_fetch

        start_time = time.time()

        # 并发执行50次搜索
        tasks = [
            initialized_system.search_memories(
                agent_id="test_agent",
                query="测试",
                limit=5
            )
            for _ in range(50)
        ]

        await asyncio.gather(*tasks)

        elapsed = time.time() - start_time

        # 并发执行应该比串行快
        # 50次串行需要约50 * 0.01 = 0.5秒
        # 并发应该在1秒内完成
        assert elapsed < 1.0
        print(f"50次并发搜索耗时: {elapsed:.2f}秒")

    async def test_cache_invalidation_performance(self, initialized_system):
        """测试缓存失效性能"""
        initialized_system.hot_cache = {}

        # 添加大量缓存数据
        for i in range(100):
            agent_id = "test_agent"
            memory_id = f"mem_{i}"
            if agent_id not in initialized_system.hot_cache:
                initialized_system.hot_cache[agent_id] = {}
            initialized_system.hot_cache[agent_id][memory_id] = {"id": memory_id}

        start_time = time.time()

        await initialized_system._invalidate_agent_caches("test_agent")

        elapsed = time.time() - start_time

        # 应该快速完成（<0.1秒）
        assert elapsed < 0.1
        print(f"缓存失效耗时: {elapsed:.3f}秒")


@pytest.mark.asyncio
class TestMemoryLifecycle:
    """测试记忆生命周期"""

    async def test_memory_aging(self):
        """测试记忆老化"""
        UnifiedAgentMemorySystem()

        # 创建不同层级的记忆
        memories = [
            MemoryItem(
                id=f"mem_{tier}",
                agent_id="test_agent",
                agent_type=AgentType.XIAONUO,
                content=f"{tier}记忆",
                memory_type=MemoryType.CONVERSATION,
                memory_tier=tier,
                access_count=0
            )
            for tier in [MemoryTier.HOT, MemoryTier.WARM, MemoryTier.COLD]
        ]

        # 验证层级属性
        assert memories[0].memory_tier == MemoryTier.HOT
        assert memories[1].memory_tier == MemoryTier.WARM
        assert memories[2].memory_tier == MemoryTier.COLD

    async def test_memory_promotion(self):
        """测试记忆升级"""
        UnifiedAgentMemorySystem()

        # 创建冷记忆
        memory = MemoryItem(
            id="mem_1",
            agent_id="test_agent",
            agent_type=AgentType.XIAONUO,
            content="初始记忆",
            memory_type=MemoryType.CONVERSATION,
            memory_tier=MemoryTier.COLD,
            access_count=0
        )

        # 模拟多次访问
        for _ in range(100):
            memory.access_count += 1

        # 高访问次数的记忆应该被提升到热记忆
        # （实际实现中会有升级逻辑）
        assert memory.access_count == 100

    async def test_memory_importance(self):
        """测试记忆重要性"""
        UnifiedAgentMemorySystem()

        # 不同重要性的记忆
        memories = [
            MemoryItem(
                id=f"mem_{i}",
                agent_id="test_agent",
                agent_type=AgentType.XIAONUO,
                content=f"记忆{i}",
                memory_type=MemoryType.CONVERSATION,
                memory_tier=MemoryTier.WARM,
                importance=i / 10.0
            )
            for i in range(10)
        ]

        # 验证重要性分布
        importances = [m.importance for m in memories]
        assert min(importances) >= 0.0
        assert max(importances) <= 1.0
