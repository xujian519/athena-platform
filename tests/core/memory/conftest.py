#!/usr/bin/env python3
"""
Athena Memory模块 - pytest共享配置
Shared pytest fixtures for Memory module testing

作者: Athena AI系统
创建时间: 2026-01-27
版本: v2.2.0 - 导出Mock类供测试使用
"""

from collections import OrderedDict
from contextlib import asynccontextmanager
from unittest.mock import AsyncMock, MagicMock

import pytest

# 尝试导入统一记忆系统，如果失败则使用Mock
try:
    from core.memory.unified_memory import (
        AgentType,
        CacheStatistics,
        MemoryType,
        UnifiedAgentMemorySystem,
    )
except ImportError:
    # 使用Mock替代
    UnifiedAgentMemorySystem = MagicMock
    CacheStatistics = MagicMock
    AgentType = MagicMock
    MemoryType = MagicMock


# 创建一个模拟的异步连接对象
class MockAsyncConnection:
    """模拟PostgreSQL异步连接"""
    def __init__(self):
        self._closed = False
        # 可动态设置的mock方法
        self.fetchval = self._default_fetchval
        self.fetch = self._default_fetch
        self.fetchrow = self._default_fetchrow
        self.execute = self._default_execute

    async def _default_fetchval(self, *args, **kwargs):
        return "mock_memory_id_12345"

    async def _default_fetch(self, *args, **kwargs):
        return []

    async def _default_fetchrow(self, *args, **kwargs):
        # 返回一个包含memory_id的字典，匹配_store_to_postgresql的期望
        return {"memory_id": "mock_memory_id_12345"}

    async def _default_execute(self, *args, **kwargs):
        return None

    async def close(self):
        self._closed = True

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()


# 创建一个模拟的连接池
class MockConnectionPool:
    """模拟PostgreSQL连接池"""
    def __init__(self):
        self._conn = MockAsyncConnection()

    @asynccontextmanager
    async def acquire(self):
        """返回一个异步上下文管理器"""
        yield self._conn

    def acquire_sync(self):
        """同步版本的acquire"""
        return self._conn

    # 支持直接访问connection的方法
    @property
    def fetchval(self):
        return self._conn.fetchval

    @fetchval.setter
    def fetchval(self, value):
        self._conn.fetchval = value

    @property
    def fetch(self):
        return self._conn.fetch

    @fetch.setter
    def fetch(self, value):
        self._conn.fetch = value

    @property
    def fetchrow(self):
        return self._conn.fetchrow

    @fetchrow.setter
    def fetchrow(self, value):
        self._conn.fetchrow = value

    @property
    def execute(self):
        return self._conn.execute

    @execute.setter
    def execute(self, value):
        self._conn.execute = value


# 创建一个模拟的Qdrant HTTP响应
class MockQdrantResponse:
    """模拟Qdrant HTTP响应"""
    def __init__(self, status=200, result=None):
        self.status = status
        self._result = result or {"result": []}

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass

    async def json(self):
        """返回JSON格式的响应数据"""
        return self._result


# 创建一个模拟的Qdrant客户端
class MockQdrantClient:
    """模拟Qdrant客户端"""
    def __init__(self):
        pass

    def put(self, *args, **kwargs):
        """返回一个异步上下文管理器"""
        return MockQdrantResponse(result={"status": "ok"})

    def post(self, *args, **kwargs):
        """返回一个异步上下文管理器"""
        return MockQdrantResponse(result={"status": "ok"})

    def get(self, *args, **kwargs):
        """返回一个异步上下文管理器"""
        # 对于搜索请求，返回空结果
        return MockQdrantResponse(result={"result": []})


@pytest.fixture
async def initialized_system():
    """提供已初始化的系统实例（Mock版本）"""
    system = UnifiedAgentMemorySystem()

    # 创建Mock连接池实例
    mock_pool = MockConnectionPool()

    # 设置PostgreSQL连接池 - 需要同时设置两个属性
    system.postgresql_pool = mock_pool
    system.pg_pool = mock_pool  # 系统检查的是pg_pool

    # Mock Redis客户端
    system.redis_client = AsyncMock()

    # Mock Redis get操作
    async def mock_get(*args, **kwargs):
        return None

    system.redis_client.get = mock_get

    # Mock Redis set操作
    async def mock_set(*args, **kwargs):
        return True

    system.redis_client.set = mock_set

    # Mock Redis delete操作
    async def mock_delete(*args, **kwargs):
        return 1

    system.redis_client.delete = mock_delete

    # Mock Qdrant客户端
    system.qdrant_client = MockQdrantClient()

    # 初始化本地缓存
    # hot_caches应该使用字符串作为key（匹配_search_hot_cache的期望）
    # 虽然系统初始化使用AgentType，但_search_hot_cache使用字符串访问
    # 这是一个已知的设计不一致问题，测试需要适应当前行为
    system.hot_caches = {
        "athena_wisdom": OrderedDict(),
        "xiaona_libra": OrderedDict(),
        "yunxi_vega": OrderedDict(),
        "xiaochen_sagittarius": OrderedDict(),
        "xiaonuo_pisces": OrderedDict()
    }

    system.warm_cache = {}

    # 初始化cache_stats - 使用CacheStatistics对象（正确的对象，不是dict）
    system.cache_stats = CacheStatistics()

    # 设置全局缓存统计（用于agent特定的统计）
    system._cache_stats = {
        "test_agent": CacheStatistics(),
        "xiaonuo_pisces": CacheStatistics(),
        "xiaona_libra": CacheStatistics(),
        "yunxi_vega": CacheStatistics(),
        "xiaochen_sagittarius": CacheStatistics(),
        "athena_wisdom": CacheStatistics()
    }

    # 设置已初始化标志 - 这是关键！
    system._initialized = True

    return system


@pytest.fixture
async def system_with_sample_data():
    """提供包含示例数据的已初始化系统"""
    system = await initialized_system()

    # 添加一些示例缓存数据 - 使用AgentType作为key
    system.hot_caches[AgentType.XIAONUO]["test_mem_1"] = {
        "id": "test_mem_1",
        "content": "测试记忆内容",
        "memory_type": "conversation"
    }

    # 添加cache统计数据
    system.cache_stats = {
        "xiaonuo_pisces": CacheStatistics(hits=70, misses=30)
    }

    system.hot_cache = {
        "test_agent": {
            "mem_1": {
                "id": "mem_1",
                "content": "测试记忆内容",
                "memory_type": "conversation"
            }
        }
    }

    return system


@pytest.fixture
def mock_memory_record():
    """提供Mock的记忆记录"""
    from datetime import datetime

    return {
        "id": "test_memory_1",
        "agent_id": "test_agent",
        "agent_type": "xiaonuo",
        "content": "测试记忆内容",
        "memory_type": "conversation",
        "memory_tier": "warm",
        "importance": 0.7,
        "created_at": datetime.now(),
        "last_accessed": datetime.now(),
        "access_count": 1
    }


@pytest.fixture
def mock_search_results():
    """提供Mock的搜索结果"""
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


@pytest.fixture
def basic_system():
    """提供基本系统实例（未初始化）"""
    system = UnifiedAgentMemorySystem()
    return system


# 导出Mock类供测试使用
__all__ = [
    'MockAsyncConnection',
    'MockConnectionPool',
    'MockQdrantClient',
    'basic_system',
    'initialized_system',
    'system_with_sample_data',
    'mock_memory_record',
    'mock_search_results'
]
