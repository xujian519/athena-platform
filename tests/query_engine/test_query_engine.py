#!/usr/bin/env python3
from __future__ import annotations
"""
Query Engine单元测试
Query Engine Unit Tests

使用pytest进行TDD测试

作者: Athena平台团队
版本: 1.0.0
"""

import asyncio
import time
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from core.query_engine import (
    InvalidQueryError,
    QueryEngine,
    QueryOptimizer,
    QueryResult,
    QueryStats,
    QueryStatus,
)
from core.query_engine.adapters import (
    Neo4jAdapter,
    PostgreSQLAdapter,
    QdrantAdapter,
    RedisAdapter,
)
from core.query_engine.cache import MemoryCache, MultiLevelCache
from core.query_engine.types import CacheKey, DataSourceType


# ==================== 测试配置 ====================

@pytest.fixture
def postgres_config():
    """PostgreSQL测试配置"""
    return {
        "host": "localhost",
        "port": 5432,
        "database": "test_db",
        "user": "test_user",
        "password": "test_pass",
    }


@pytest.fixture
def redis_config():
    """Redis测试配置"""
    return {
        "host": "localhost",
        "port": 6379,
        "password": None,
        "db": 0,
    }


@pytest.fixture
def qdrant_config():
    """Qdrant测试配置"""
    return {
        "host": "localhost",
        "port": 6333,
    }


@pytest.fixture
def neo4j_config():
    """Neo4j测试配置"""
    return {
        "uri": "bolt://localhost:7687",
        "user": "neo4j",
        "password": "test_pass",
    }


@pytest.fixture
def mock_cache():
    """模拟缓存"""
    cache = MemoryCache(max_size=100)
    return cache


# ==================== CacheKey测试 ====================

class TestCacheKey:
    """测试CacheKey"""

    def test_cache_key_creation(self):
        """测试缓存键创建"""
        key = CacheKey(
            data_source=DataSourceType.POSTGRESQL,
            query="SELECT * FROM users",
            parameters=("limit", 10),
        )
        assert key.hash_value is not None
        assert len(key.hash_value) == 64  # SHA256哈希长度

    def test_cache_key_string_representation(self):
        """测试缓存键字符串表示"""
        key = CacheKey(
            data_source=DataSourceType.REDIS,
            query="GET mykey",
        )
        assert str(key) == key.hash_value


# ==================== QueryResult测试 ====================

class TestQueryResult:
    """测试QueryResult"""

    def test_query_result_creation(self):
        """测试查询结果创建"""
        stats = QueryStats(
            execution_time=0.1,
            rows_returned=5,
            data_source=DataSourceType.POSTGRESQL,
        )

        result = QueryResult(
            data=[{"id": 1, "name": "test"}],
            status=QueryStatus.COMPLETED,
            stats=stats,
        )

        assert result.is_success is True
        assert result.row_count == 1

    def test_query_result_to_dict(self):
        """测试查询结果转字典"""
        stats = QueryStats(
            execution_time=0.1,
            rows_returned=5,
            data_source=DataSourceType.POSTGRESQL,
        )

        result = QueryResult(
            data=[{"id": 1}],
            status=QueryStatus.COMPLETED,
            stats=stats,
        )

        result_dict = result.to_dict()
        assert result_dict["status"] == "completed"
        assert result_dict["data"] == [{"id": 1}]


# ==================== MemoryCache测试 ====================

class TestMemoryCache:
    """测试MemoryCache"""

    @pytest.mark.asyncio
    async def test_cache_set_and_get(self):
        """测试缓存设置和获取"""
        cache = MemoryCache(max_size=10)

        stats = QueryStats(
            execution_time=0.1,
            rows_returned=1,
            data_source=DataSourceType.POSTGRESQL,
        )

        result = QueryResult(
            data=[{"id": 1}],
            status=QueryStatus.COMPLETED,
            stats=stats,
        )

        await cache.set("test_key", result, ttl=60)
        cached_result = await cache.get("test_key")

        assert cached_result is not None
        assert cached_result.row_count == 1
        assert cached_result.status == QueryStatus.CACHED

    @pytest.mark.asyncio
    async def test_cache_miss(self):
        """测试缓存未命中"""
        cache = MemoryCache()
        result = await cache.get("non_existent_key")
        assert result is None

    @pytest.mark.asyncio
    async def test_cache_delete(self):
        """测试缓存删除"""
        cache = MemoryCache()

        stats = QueryStats()
        result = QueryResult(
            data=[],
            status=QueryStatus.COMPLETED,
            stats=stats,
        )

        await cache.set("test_key", result)
        assert await cache.delete("test_key") is True
        assert await cache.get("test_key") is None

    @pytest.mark.asyncio
    async def test_cache_clear(self):
        """测试缓存清空"""
        cache = MemoryCache()

        stats = QueryStats()
        result = QueryResult(
            data=[],
            status=QueryStatus.COMPLETED,
            stats=stats,
        )

        await cache.set("key1", result)
        await cache.set("key2", result)
        await cache.clear()

        stats_result = await cache.get_stats()
        assert stats_result["size"] == 0

    @pytest.mark.asyncio
    async def test_cache_stats(self):
        """测试缓存统计"""
        cache = MemoryCache()

        stats = QueryStats()
        result = QueryResult(
            data=[],
            status=QueryStatus.COMPLETED,
            stats=stats,
        )

        await cache.set("test_key", result)
        await cache.get("test_key")  # 命中
        await cache.get("miss_key")  # 未命中

        cache_stats = await cache.get_stats()
        assert cache_stats["hits"] == 1
        assert cache_stats["misses"] == 1
        assert "hit_rate" in cache_stats


# ==================== PostgreSQLAdapter测试 ====================

class TestPostgreSQLAdapter:
    """测试PostgreSQLAdapter"""

    def test_adapter_creation(self, postgres_config):
        """测试适配器创建"""
        adapter = PostgreSQLAdapter(postgres_config)
        assert adapter.data_source_type == DataSourceType.POSTGRESQL
        assert adapter._is_connected is False

    def test_data_source_type(self, postgres_config):
        """测试数据源类型"""
        adapter = PostgreSQLAdapter(postgres_config)
        assert adapter.data_source_type == DataSourceType.POSTGRESQL

    def test_explain_query(self, postgres_config):
        """测试查询解释"""
        adapter = PostgreSQLAdapter(postgres_config)
        plan = adapter.explain_query("SELECT * FROM users WHERE id = $1")

        assert plan.estimated_cost > 0
        assert len(plan.steps) > 0
        assert DataSourceType.POSTGRESQL in plan.data_sources


# ==================== RedisAdapter测试 ====================

class TestRedisAdapter:
    """测试RedisAdapter"""

    def test_adapter_creation(self, redis_config):
        """测试适配器创建"""
        adapter = RedisAdapter(redis_config)
        assert adapter.data_source_type == DataSourceType.REDIS
        assert adapter._is_connected is False

    def test_explain_query(self, redis_config):
        """测试查询解释"""
        adapter = RedisAdapter(redis_config)
        plan = adapter.explain_query("GET mykey")

        assert plan.estimated_cost > 0
        assert DataSourceType.REDIS in plan.data_sources


# ==================== QdrantAdapter测试 ====================

class TestQdrantAdapter:
    """测试QdrantAdapter"""

    def test_adapter_creation(self, qdrant_config):
        """测试适配器创建"""
        adapter = QdrantAdapter(qdrant_config)
        assert adapter.data_source_type == DataSourceType.QDRANT
        assert adapter._is_connected is False

    def test_explain_query(self, qdrant_config):
        """测试查询解释"""
        adapter = QdrantAdapter(qdrant_config)
        plan = adapter.explain_query("search")

        assert plan.estimated_cost > 0
        assert DataSourceType.QDRANT in plan.data_sources


# ==================== Neo4jAdapter测试 ====================

class TestNeo4jAdapter:
    """测试Neo4jAdapter"""

    def test_adapter_creation(self, neo4j_config):
        """测试适配器创建"""
        adapter = Neo4jAdapter(neo4j_config)
        assert adapter.data_source_type == DataSourceType.NEO4J
        assert adapter._is_connected is False

    def test_explain_query(self, neo4j_config):
        """测试查询解释"""
        adapter = Neo4jAdapter(neo4j_config)
        plan = adapter.explain_query("MATCH (n:User) RETURN n")

        assert plan.estimated_cost > 0
        assert DataSourceType.NEO4J in plan.data_sources


# ==================== QueryEngine测试 ====================

class TestQueryEngine:
    """测试QueryEngine"""

    def test_engine_creation(self):
        """测试引擎创建"""
        engine = QueryEngine(enable_cache=True)
        assert engine._enable_cache is True
        assert engine._query_count == 0

    def test_register_adapter(self, postgres_config):
        """测试注册适配器"""
        engine = QueryEngine()
        adapter = PostgreSQLAdapter(postgres_config)

        engine.register_adapter(DataSourceType.POSTGRESQL, adapter)

        assert DataSourceType.POSTGRESQL in engine._adapters

    def test_explain(self, postgres_config):
        """测试查询解释"""
        engine = QueryEngine()
        adapter = PostgreSQLAdapter(postgres_config)
        engine.register_adapter(DataSourceType.POSTGRESQL, adapter)

        plan = engine.explain("SELECT * FROM users", DataSourceType.POSTGRESQL)

        assert plan.estimated_cost > 0
        assert len(plan.steps) > 0

    def test_get_stats(self):
        """测试获取统计信息"""
        engine = QueryEngine()
        stats = engine.get_stats()

        assert "query_count" in stats
        assert "registered_adapters" in stats
        assert stats["query_count"] == 0


# ==================== QueryOptimizer测试 ====================

class TestQueryOptimizer:
    """测试QueryOptimizer"""

    def test_optimize_sql(self):
        """测试SQL优化"""
        query = "select  *  from  users  where  id  =  1"
        optimized = QueryOptimizer.optimize_sql(query)

        assert "SELECT" in optimized
        assert "FROM" in optimized
        assert optimized.count("  ") == 0  # 无多余空格

    def test_estimate_complexity_postgres(self):
        """测试PostgreSQL复杂度估算"""
        query = "SELECT * FROM users JOIN orders ON users.id = orders.user_id"
        complexity = QueryOptimizer.estimate_complexity(query, DataSourceType.POSTGRESQL)

        assert complexity > 0
        assert complexity <= 100

    def test_estimate_complexity_redis(self):
        """测试Redis复杂度估算"""
        query = "KEYS *"
        complexity = QueryOptimizer.estimate_complexity(query, DataSourceType.REDIS)

        assert complexity == 80  # KEYS命令复杂度高

    def test_estimate_complexity_qdrant(self):
        """测试Qdrant复杂度估算"""
        query = "search"
        complexity = QueryOptimizer.estimate_complexity(query, DataSourceType.QDRANT)

        assert complexity == 50

    def test_estimate_complexity_neo4j(self):
        """测试Neo4j复杂度估算"""
        query = "MATCH (n:User)-[:KNOWS]->(m:User) RETURN n, m"
        complexity = QueryOptimizer.estimate_complexity(query, DataSourceType.NEO4J)

        assert complexity > 0


# ==================== MultiLevelCache测试 ====================

class TestMultiLevelCache:
    """测试多级缓存"""

    @pytest.mark.asyncio
    async def test_l1_l2_cache(self):
        """测试L1和L2缓存"""
        l1 = MemoryCache(max_size=10)
        l2 = MemoryCache(max_size=20)
        cache = MultiLevelCache(l1, l2)

        stats = QueryStats()
        result = QueryResult(
            data=[{"id": 1}],
            status=QueryStatus.COMPLETED,
            stats=stats,
        )

        # 写入缓存
        await cache.set("test_key", result)

        # 从L1读取
        l1_result = await l1.get("test_key")
        assert l1_result is not None

        # 从多级缓存读取
        cache_result = await cache.get("test_key")
        assert cache_result is not None

    @pytest.mark.asyncio
    async def test_cache_stats(self):
        """测试多级缓存统计"""
        l1 = MemoryCache()
        l2 = MemoryCache()
        cache = MultiLevelCache(l1, l2)

        stats_result = await cache.get_stats()
        assert "l1" in stats_result
        assert "l2" in stats_result


# ==================== 集成测试 ====================

class TestQueryEngineIntegration:
    """查询引擎集成测试"""

    @pytest.mark.asyncio
    async def test_cross_source_query_sequential(self):
        """测试顺序跨数据源查询"""
        engine = QueryEngine(enable_cache=False)

        # 模拟适配器
        mock_adapter1 = AsyncMock()
        mock_adapter1.data_source_type = DataSourceType.POSTGRESQL
        mock_adapter1.is_connected = AsyncMock(return_value=True)
        mock_adapter1.execute = AsyncMock(
            return_value=QueryResult(
                data=[{"id": 1}],
                status=QueryStatus.COMPLETED,
                stats=QueryStats(),
            )
        )

        mock_adapter2 = AsyncMock()
        mock_adapter2.data_source_type = DataSourceType.REDIS
        mock_adapter2.is_connected = AsyncMock(return_value=True)
        mock_adapter2.execute = AsyncMock(
            return_value=QueryResult(
                data=[{"key": "value"}],
                status=QueryStatus.COMPLETED,
                stats=QueryStats(),
            )
        )

        engine.register_adapter(DataSourceType.POSTGRESQL, mock_adapter1)
        engine.register_adapter(DataSourceType.REDIS, mock_adapter2)

        # 执行跨数据源查询
        queries = {
            DataSourceType.POSTGRESQL: "SELECT * FROM users",
            DataSourceType.REDIS: "GET user:1",
        }

        result = await engine.execute_cross_source(
            queries,
            join_strategy="sequential",
        )

        assert result.status == QueryStatus.COMPLETED
        assert result.row_count == 2

    @pytest.mark.asyncio
    async def test_cross_source_query_merge(self):
        """测试合并跨数据源查询"""
        engine = QueryEngine(enable_cache=False)

        # 模拟适配器
        mock_adapter = AsyncMock()
        mock_adapter.data_source_type = DataSourceType.POSTGRESQL
        mock_adapter.is_connected = AsyncMock(return_value=True)
        mock_adapter.execute = AsyncMock(
            return_value=QueryResult(
                data=[{"user_id": 1, "name": "Alice"}],
                status=QueryStatus.COMPLETED,
                stats=QueryStats(),
            )
        )

        engine.register_adapter(DataSourceType.POSTGRESQL, mock_adapter)

        # 执行合并查询
        queries = {
            DataSourceType.POSTGRESQL: "SELECT * FROM users",
        }

        result = await engine.execute_cross_source(
            queries,
            join_strategy="merge",
            join_key="user_id",
        )

        assert result.status == QueryStatus.COMPLETED
        assert "join_key" in result.metadata


# ==================== 性能测试 ====================

class TestQueryEnginePerformance:
    """查询引擎性能测试"""

    @pytest.mark.asyncio
    @pytest.mark.performance
    async def test_cache_performance(self):
        """测试缓存性能"""
        import time

        cache = MemoryCache(max_size=1000)

        stats = QueryStats()
        result = QueryResult(
            data=[{"id": i} for i in range(100)],
            status=QueryStatus.COMPLETED,
            stats=stats,
        )

        # 写入性能
        start = time.time()
        for i in range(100):
            await cache.set(f"key_{i}", result)
        write_time = time.time() - start

        # 读取性能
        start = time.time()
        for i in range(100):
            await cache.get(f"key_{i}")
        read_time = time.time() - start

        # 性能断言
        assert write_time < 1.0  # 写入应在1秒内完成
        assert read_time < 0.1  # 读取应在0.1秒内完成

    @pytest.mark.asyncio
    @pytest.mark.performance
    async def test_query_optimization(self):
        """测试查询优化性能"""
        query = "select  *  from  users  where  id  =  1  and  name  =  'test'"

        start = time.time()
        for _ in range(1000):
            QueryOptimizer.optimize_sql(query)
        optimize_time = time.time() - start

        # 优化1000次应在0.1秒内完成
        assert optimize_time < 0.1


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
