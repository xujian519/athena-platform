#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Athena统一智能体记忆系统 - 单元测试
Unit Tests for Unified Agent Memory System

测试内容：
1. 系统初始化测试
2. 记忆存储测试
3. 记忆回忆测试
4. 记忆搜索测试
5. 缓存命中率测试
6. 重试机制测试
7. 结构化日志测试

作者: Athena平台团队
创建时间: 2026-01-21
版本: v1.0.0
"""

import asyncio
import os
import sys
import pytest
import uuid
from datetime import datetime
from typing import Dict, Any
from unittest.mock import AsyncMock, MagicMock, patch

# 添加项目路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../../..'))

from core.memory.unified_memory import (
    UnifiedAgentMemorySystem,
    AgentType,
    MemoryType,
    MemoryTier,
    CacheStatistics,
)
from core.memory.unified_memory.utils import retry_with_backoff


class TestMemorySystemInitialization:
    """测试系统初始化"""

    @pytest.mark.asyncio
    async def test_initialization(self):
        """测试系统初始化"""
        # 使用环境变量设置测试数据库配置
        os.environ['MEMORY_DB_PASSWORD'] = 'test_password'
        os.environ['REDIS_HOST'] = 'localhost'

        system = UnifiedAgentMemorySystem()

        # 验证系统配置
        assert system.system_name == "Athena统一智能体记忆系统"
        assert system.version == "v1.0.0 永恒记忆"
        assert system.cache_stats is not None
        assert isinstance(system.cache_stats, CacheStatistics)

        # 验证数据库配置
        assert 'postgresql' in system.db_config
        assert 'redis' in system.db_config
        assert 'qdrant' in system.db_config

        # 验证Redis TTL配置
        redis_config = system.db_config['redis']
        assert 'ttl' in redis_config
        assert redis_config['ttl']['agent_stats'] == 300  # 5分钟
        assert redis_config['ttl']['search_results'] == 60  # 1分钟

        print("✅ 系统初始化测试通过")


class TestMemoryStorage:
    """测试记忆存储功能"""

    @pytest.mark.asyncio
    async def test_store_memory(self):
        """测试存储基本记忆"""
        system = UnifiedAgentMemorySystem()

        # Mock数据库连接
        with patch.object(system, '_check_initialized'):
            with patch.object(system, '_generate_embedding', return_value=[0.1] * 768):
                with patch.object(system, '_store_to_postgresql', return_value="test-memory-id"):
                    with patch.object(system, '_store_to_qdrant', return_value="test-memory-id"):
                        with patch.object(system, '_update_vector_id'):
                            with patch.object(system, '_invalidate_agent_caches'):
                                memory_id = await system.store_memory(
                                    agent_id="test_agent",
                                    agent_type=AgentType.ATHENA,
                                    content="这是一条测试记忆",
                                    memory_type=MemoryType.CONVERSATION,
                                    importance=0.8,
                                    emotional_weight=0.5
                                )

                                assert memory_id == "test-memory-id"

        print("✅ 记忆存储测试通过")

    @pytest.mark.asyncio
    async def test_store_hot_memory(self):
        """测试存储热记忆"""
        system = UnifiedAgentMemorySystem()
        system.HOT_CACHE_LIMIT = 50

        # Mock数据库连接
        with patch.object(system, '_check_initialized'):
            with patch.object(system, '_generate_embedding', return_value=[0.1] * 768):
                with patch.object(system, '_store_to_postgresql', return_value="hot-memory-id"):
                    with patch.object(system, '_store_to_qdrant', return_value="hot-memory-id"):
                        with patch.object(system, '_update_vector_id'):
                            with patch.object(system, '_cache_hot_memory') as mock_cache:
                                with patch.object(system, '_invalidate_agent_caches'):
                                    memory_id = await system.store_memory(
                                        agent_id="test_agent",
                                        agent_type=AgentType.XIAONUO,
                                        content="这是热记忆",
                                        memory_type=MemoryType.CONVERSATION,
                                        tier=MemoryTier.HOT
                                    )

                                    # 验证缓存方法被调用
                                    mock_cache.assert_called_once()
                                    assert memory_id == "hot-memory-id"

        print("✅ 热记忆存储测试通过")


class TestMemoryRecall:
    """测试记忆回忆功能"""

    @pytest.mark.asyncio
    async def test_recall_memory(self):
        """测试回忆记忆"""
        system = UnifiedAgentMemorySystem()

        # Mock返回结果 - 返回足够的结果避免调用数据库
        mock_results = [
            {
                'memory_id': f'mem{i}',
                'content': f'测试记忆{i}',
                'memory_type': 'conversation',
                'tier': 'hot',
                'similarity': 0.95 - i * 0.05,
                'importance': 0.8 - i * 0.05,
                'source': 'hot_cache'
            }
            for i in range(10)  # 返回10个结果以满足limit=10
        ]

        with patch.object(system, '_check_initialized'):
            with patch.object(system, '_search_hot_cache', return_value=mock_results):
                # 也mock _search_database以防万一
                with patch.object(system, '_search_database', return_value=[]):
                    results = await system.recall_memory(
                        agent_id="test_agent",
                        query="测试",
                        limit=10
                    )

                    assert len(results) > 0
                    assert results[0]['content'] == '测试记忆0'

        print("✅ 记忆回忆测试通过")


class TestMemorySearch:
    """测试记忆搜索功能"""

    @pytest.mark.asyncio
    async def test_search_memories(self):
        """测试搜索记忆"""
        system = UnifiedAgentMemorySystem()

        # Mock返回结果
        mock_search_results = [
            {
                'memory_id': 'mem1',
                'agent_id': 'athena_wisdom',
                'content': '智能体测试记忆',
                'memory_type': 'conversation',
                'tier': 'cold',
                'importance': 0.9,
                'created_at': datetime.now().isoformat()
            }
        ]

        with patch.object(system, '_check_initialized'):
            with patch.object(system, '_cache_get', return_value=None):  # 缓存未命中
                # 创建async context manager mock
                from contextlib import asynccontextmanager

                @asynccontextmanager
                async def mock_connection():
                    mock_conn = AsyncMock()
                    mock_conn.fetch = AsyncMock(return_value=mock_search_results)
                    yield mock_conn

                mock_pool = AsyncMock()
                mock_pool.acquire = mock_connection

                # 设置pg_pool属性
                system.pg_pool = mock_pool

                with patch.object(system, '_cache_set') as mock_cache_set:
                    results = await system.search_memories(
                        query="测试",
                        limit=20
                    )

                    # 验证结果
                    assert len(results) == 1
                    assert results[0]['content'] == '智能体测试记忆'

                    # 验证缓存被设置
                    mock_cache_set.assert_called_once()

        print("✅ 记忆搜索测试通过")

    @pytest.mark.asyncio
    async def test_search_with_cache_hit(self):
        """测试搜索命中缓存"""
        system = UnifiedAgentMemorySystem()

        # Mock缓存命中
        cached_results = [
            {
                'memory_id': 'mem1',
                'content': '缓存中的记忆',
                'memory_type': 'conversation'
            }
        ]

        with patch.object(system, '_check_initialized'):
            with patch.object(system, '_cache_get', return_value=cached_results):
                results = await system.search_memories(query="测试")

                # 验证返回缓存结果
                assert len(results) == 1
                assert results[0]['content'] == '缓存中的记忆'

        print("✅ 搜索缓存命中测试通过")


class TestCacheStatistics:
    """测试缓存统计功能"""

    def test_cache_hit_rate(self):
        """测试缓存命中率计算"""
        stats = CacheStatistics()

        # 初始状态
        assert stats.hit_rate == 0.0
        assert stats.total_requests == 0

        # 添加一些命中和未命中
        stats.record_hit()
        stats.record_hit()
        stats.record_miss()

        assert stats.hit_rate == 2/3
        assert stats.total_requests == 3
        assert stats.hits == 2
        assert stats.misses == 1

        # 获取统计信息
        stats_dict = stats.get_stats()
        assert stats_dict['hit_rate'] == 2/3
        assert 'hits' in stats_dict
        assert 'misses' in stats_dict

        print("✅ 缓存统计测试通过")

    def test_empty_cache_stats(self):
        """测试空缓存统计"""
        stats = CacheStatistics()

        # 空状态不应该有除零错误
        assert stats.hit_rate == 0.0

        stats_dict = stats.get_stats()
        assert stats_dict['total_requests'] == 0
        assert stats_dict['hit_rate'] == 0.0

        print("✅ 空缓存统计测试通过")


class TestRetryMechanism:
    """测试重试机制"""

    @pytest.mark.asyncio
    async def test_retry_with_backoff(self):
        """测试指数退避重试机制"""
        call_count = 0

        @retry_with_backoff(max_retries=3, base_delay=0.1, max_delay=1.0)
        async def failing_function():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise Exception("模拟失败")
            return "成功"

        result = await failing_function()

        # 验证重试了3次
        assert call_count == 3
        assert result == "成功"

        print("✅ 重试机制测试通过")

    @pytest.mark.asyncio
    async def test_retry_max_retries_exceeded(self):
        """测试超过最大重试次数"""
        call_count = 0

        @retry_with_backoff(max_retries=2, base_delay=0.1, max_delay=1.0)
        async def always_failing_function():
            nonlocal call_count
            call_count += 1
            raise Exception("总是失败")

        # 验证最终抛出异常
        with pytest.raises(Exception, match="总是失败"):
            await always_failing_function()

        # 验证尝试了最大次数
        assert call_count == 2

        print("✅ 最大重试次数测试通过")


class TestAgentStats:
    """测试智能体统计功能"""

    @pytest.mark.asyncio
    async def test_get_agent_stats_from_cache(self):
        """测试从缓存获取智能体统计"""
        system = UnifiedAgentMemorySystem()

        # Mock缓存命中
        cached_stats = {
            'agent_id': 'athena_wisdom',
            'total_memories': 100,
            'family_memories': 20,
            'agent_name': 'Athena.智慧女神'
        }

        with patch.object(system, '_check_initialized'):
            with patch.object(system, '_cache_get', return_value=cached_stats):
                stats = await system.get_agent_stats("athena_wisdom")

                assert stats['agent_id'] == 'athena_wisdom'
                assert stats['total_memories'] == 100
                assert stats['agent_name'] == 'Athena.智慧女神'

        print("✅ 缓存统计测试通过")

    @pytest.mark.asyncio
    async def test_get_agent_stats_from_db(self):
        """测试从数据库获取智能体统计"""
        system = UnifiedAgentMemorySystem()

        # Mock数据库查询结果
        mock_db_row = {
            'agent_id': 'xiaonuo_pisces',
            'agent_type': 'xiaonuo',
            'total_memories': 50,
            'family_memories': 30
        }

        with patch.object(system, '_check_initialized'):
            with patch.object(system, '_cache_get', return_value=None):  # 缓存未命中
                # 创建async context manager mock
                from contextlib import asynccontextmanager

                @asynccontextmanager
                async def mock_connection():
                    mock_conn = AsyncMock()
                    mock_conn.fetchrow = AsyncMock(return_value=mock_db_row)
                    yield mock_conn

                mock_pool = AsyncMock()
                mock_pool.acquire = mock_connection

                # 设置pg_pool属性
                system.pg_pool = mock_pool

                with patch.object(system, '_cache_set') as mock_cache_set:
                    stats = await system.get_agent_stats("xiaonuo_pisces")

                    # 验证结果
                    assert stats['agent_id'] == 'xiaonuo_pisces'
                    assert stats['total_memories'] == 50

                    # 验证缓存被设置
                    mock_cache_set.assert_called_once()

        print("✅ 数据库统计测试通过")


class TestCacheInvalidation:
    """测试缓存失效功能"""

    @pytest.mark.asyncio
    async def test_invalidate_agent_caches(self):
        """测试智能体缓存失效"""
        system = UnifiedAgentMemorySystem()

        with patch.object(system, '_cache_delete') as mock_delete:
            with patch.object(system, '_cache_delete_pattern') as mock_delete_pattern:
                await system._invalidate_agent_caches("athena_wisdom")

                # 验证删除了统计缓存
                mock_delete.assert_called_once()

                # 验证删除了搜索缓存
                mock_delete_pattern.assert_called_once_with("search:*")

        print("✅ 缓存失效测试通过")


class TestStructuredLogging:
    """测试结构化日志功能"""

    def test_log_format(self):
        """测试日志格式"""
        import logging

        # 创建logger并设置格式
        logger = logging.getLogger('test_logger')
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - [%(request_id)s] - %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)

        # 验证格式包含request_id
        assert formatter._fmt.startswith('%(asctime)s')
        assert '[%(request_id)s]' in formatter._fmt

        print("✅ 日志格式测试通过")


class TestCacheKeyGeneration:
    """测试缓存键生成功能"""

    def test_generate_cache_key(self):
        """测试缓存键生成"""
        system = UnifiedAgentMemorySystem()

        # 测试基本键生成
        key1 = system._generate_cache_key("test", agent_id="123")
        assert "test" in key1
        assert "agent_id:123" in key1

        # 测试多个参数
        key2 = system._generate_cache_key(
            "search",
            query="测试",
            agent_id="athena",
            limit=10
        )
        assert "search" in key2
        assert "agent_id:athena" in key2
        assert "limit:10" in key2

        # 测试None参数被忽略
        key3 = system._generate_cache_key(
            "stats",
            agent_id="123",
            memory_type=None  # 应该被忽略
        )
        assert "memory_type" not in key3

        print("✅ 缓存键生成测试通过")


# 运行所有测试
if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
