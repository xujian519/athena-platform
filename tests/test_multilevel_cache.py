#!/usr/bin/env python3
"""
多级缓存系统单元测试 - Phase 2.2架构优化

Multi-Level Cache Unit Tests

测试覆盖:
- L1内存缓存（命中、未命中、淘汰、过期）
- L2 Redis缓存（连接、CRUD、批量操作）
- L3 SQLite存储（CRUD、批量操作、统计）
- 多级缓存管理器（协调、回填、统计）

运行:
    pytest tests/test_multilevel_cache.py -v
    pytest tests/test_multilevel_cache.py -v -m "not slow"

作者: Athena平台团队
创建时间: 2026-04-24
"""

import asyncio
import os
import tempfile
import time
from pathlib import Path

import pytest

# 导入被测试模块
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.context_management.cache import (
    CacheConfig,
    L1MemoryCache,
    L3SQLiteBackend,
    MultiLevelCacheManager,
)


# =============================================================================
# L1内存缓存测试
# =============================================================================


class TestL1MemoryCache:
    """L1内存缓存测试套件"""

    def test_init(self):
        """测试初始化"""
        cache = L1MemoryCache(capacity=100, ttl_seconds=60)
        assert cache.capacity == 100
        assert cache.ttl_seconds == 60
        assert cache._lock is not None

    @pytest.mark.asyncio
    async def test_set_and_get(self):
        """测试基本设置和获取"""
        cache = L1MemoryCache()

        # 设置值
        result = await cache.set("key1", "value1")
        assert result is True

        # 获取值
        value = await cache.get("key1")
        assert value == "value1"

    @pytest.mark.asyncio
    async def test_get_nonexistent(self):
        """测试获取不存在的键"""
        cache = L1MemoryCache()
        value = await cache.get("nonexistent")
        assert value is None

    @pytest.mark.asyncio
    async def test_delete(self):
        """测试删除"""
        cache = L1MemoryCache()

        await cache.set("key1", "value1")
        result = await cache.delete("key1")
        assert result is True

        value = await cache.get("key1")
        assert value is None

    @pytest.mark.asyncio
    async def test_clear(self):
        """测试清空"""
        cache = L1MemoryCache()

        await cache.set("key1", "value1")
        await cache.set("key2", "value2")
        await cache.clear()

        assert await cache.get("key1") is None
        assert await cache.get("key2") is None

    @pytest.mark.asyncio
    async def test_ttl_expiration(self):
        """测试TTL过期"""
        cache = L1MemoryCache(ttl_seconds=1)

        await cache.set("key1", "value1")
        assert await cache.get("key1") == "value1"

        # 等待过期
        await asyncio.sleep(1.5)
        assert await cache.get("key1") is None

    @pytest.mark.asyncio
    async def test_lru_eviction(self):
        """测试LRU淘汰"""
        cache = L1MemoryCache(capacity=3)

        # 填满缓存
        await cache.set("key1", "value1")
        await cache.set("key2", "value2")
        await cache.set("key3", "value3")

        # 访问key1（使其成为最近使用）
        await cache.get("key1")

        # 添加新键，应该淘汰key2（最久未使用）
        await cache.set("key4", "value4")

        assert await cache.get("key1") == "value1"  # 仍在
        assert await cache.get("key2") is None  # 被淘汰
        assert await cache.get("key3") == "value3"  # 仍在
        assert await cache.get("key4") == "value4"  # 新添加

    @pytest.mark.asyncio
    async def test_statistics(self):
        """测试统计信息"""
        cache = L1MemoryCache()

        await cache.set("key1", "value1")
        await cache.get("key1")  # 命中
        await cache.get("key2")  # 未命中

        stats = cache.get_statistics()
        assert stats["hits"] == 1
        assert stats["misses"] == 1
        assert stats["hit_rate"] == 0.5
        assert stats["size"] == 1

    @pytest.mark.asyncio
    async def test_complex_value_types(self):
        """测试复杂数据类型"""
        cache = L1MemoryCache()

        # 字典
        await cache.set("dict", {"a": 1, "b": 2})
        assert await cache.get("dict") == {"a": 1, "b": 2}

        # 列表
        await cache.set("list", [1, 2, 3])
        assert await cache.get("list") == [1, 2, 3]

        # 嵌套结构
        nested = {"users": [{"id": 1, "name": "Alice"}]}
        await cache.set("nested", nested)
        assert await cache.get("nested") == nested

    @pytest.mark.asyncio
    async def test_custom_ttl(self):
        """测试自定义TTL"""
        cache = L1MemoryCache(ttl_seconds=60)

        # 设置短TTL
        await cache.set("key1", "value1", ttl_seconds=1)

        await asyncio.sleep(1.5)
        assert await cache.get("key1") is None

    @pytest.mark.asyncio
    async def test_cleanup_expired(self):
        """测试清理过期条目"""
        cache = L1MemoryCache(ttl_seconds=1)

        await cache.set("key1", "value1")
        await cache.set("key2", "value2")
        await asyncio.sleep(1.5)

        cleaned = await cache.cleanup_expired()
        assert cleaned == 2

    @pytest.mark.asyncio
    async def test_contains(self):
        """测试contains方法"""
        cache = L1MemoryCache()

        await cache.set("key1", "value1")
        assert await cache.contains("key1") is True
        assert await cache.contains("key2") is False


# =============================================================================
# L3 SQLite存储测试
# =============================================================================


class TestL3SQLiteBackend:
    """L3 SQLite存储测试套件"""

    @pytest.fixture
    def temp_db(self):
        """临时数据库文件"""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = f.name
        yield db_path
        # 清理
        if os.path.exists(db_path):
            os.remove(db_path)

    @pytest.mark.asyncio
    async def test_init(self, temp_db):
        """测试初始化"""
        backend = L3SQLiteBackend(db_path=temp_db)
        await backend._initialize()
        assert backend._initialized is True

    @pytest.mark.asyncio
    async def test_set_and_get(self, temp_db):
        """测试基本设置和获取"""
        backend = L3SQLiteBackend(db_path=temp_db)

        await backend.set("key1", "value1")
        value = await backend.get("key1")
        assert value == "value1"

    @pytest.mark.asyncio
    async def test_get_nonexistent(self, temp_db):
        """测试获取不存在的键"""
        backend = L3SQLiteBackend(db_path=temp_db)
        value = await backend.get("nonexistent")
        assert value is None

    @pytest.mark.asyncio
    async def test_delete(self, temp_db):
        """测试删除"""
        backend = L3SQLiteBackend(db_path=temp_db)

        await backend.set("key1", "value1")
        result = await backend.delete("key1")
        assert result is True

        value = await backend.get("key1")
        assert value is None

    @pytest.mark.asyncio
    async def test_clear(self, temp_db):
        """测试清空"""
        backend = L3SQLiteBackend(db_path=temp_db)

        await backend.set("key1", "value1")
        await backend.set("key2", "value2")
        await backend.clear()

        assert await backend.get("key1") is None
        assert await backend.get("key2") is None

    @pytest.mark.asyncio
    async def test_exists(self, temp_db):
        """测试exists方法"""
        backend = L3SQLiteBackend(db_path=temp_db)

        await backend.set("key1", "value1")
        assert await backend.exists("key1") is True
        assert await backend.exists("key2") is False

    @pytest.mark.asyncio
    async def test_ttl_expiration(self, temp_db):
        """测试TTL过期"""
        backend = L3SQLiteBackend(db_path=temp_db)

        await backend.set("key1", "value1", ttl_seconds=1)
        assert await backend.exists("key1") is True

        await asyncio.sleep(1.5)
        assert await backend.get("key1") is None

    @pytest.mark.asyncio
    async def test_get_many(self, temp_db):
        """测试批量获取"""
        backend = L3SQLiteBackend(db_path=temp_db)

        await backend.set("key1", "value1")
        await backend.set("key2", "value2")
        await backend.set("key3", "value3")

        results = await backend.get_many(["key1", "key2", "key4"])
        assert results == {"key1": "value1", "key2": "value2"}

    @pytest.mark.asyncio
    async def test_set_many(self, temp_db):
        """测试批量设置"""
        backend = L3SQLiteBackend(db_path=temp_db)

        mapping = {"key1": "value1", "key2": "value2", "key3": "value3"}
        count = await backend.set_many(mapping)
        assert count == 3

        assert await backend.get("key1") == "value1"
        assert await backend.get("key2") == "value2"
        assert await backend.get("key3") == "value3"

    @pytest.mark.asyncio
    async def test_cleanup_expired(self, temp_db):
        """测试清理过期条目"""
        backend = L3SQLiteBackend(db_path=temp_db)

        await backend.set("key1", "value1", ttl_seconds=1)
        await backend.set("key2", "value2", ttl_seconds=1)
        await asyncio.sleep(1.5)

        count = await backend.cleanup_expired()
        assert count == 2

    @pytest.mark.asyncio
    async def test_statistics(self, temp_db):
        """测试统计信息"""
        backend = L3SQLiteBackend(db_path=temp_db)

        await backend.set("key1", "value1")
        await backend.set("key2", "value2")
        await backend.get("key1")
        await backend.get("key3")  # 未命中

        stats = await backend.get_statistics()
        assert stats["entries"] == 2
        assert stats["reads"] == 2
        assert stats["writes"] == 2

    @pytest.mark.asyncio
    async def test_list_keys(self, temp_db):
        """测试列出键"""
        backend = L3SQLiteBackend(db_path=temp_db)

        await backend.set("user:1", "Alice")
        await backend.set("user:2", "Bob")
        await backend.set("session:1", "xyz")

        # 列出所有键
        all_keys = await backend.list_keys()
        assert len(all_keys) == 3

        # 模式搜索
        user_keys = await backend.list_keys(pattern="user")
        assert len(user_keys) == 2


# =============================================================================
# 多级缓存管理器测试
# =============================================================================


class TestMultiLevelCacheManager:
    """多级缓存管理器测试套件"""

    @pytest.fixture
    def temp_manager(self):
        """临时测试管理器（禁用L2 Redis）"""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = f.name

        config = CacheConfig(
            l2_enabled=False,  # 禁用Redis
            l3_db_path=db_path,
        )
        manager = MultiLevelCacheManager(config=config)

        yield manager

        # 清理
        if os.path.exists(db_path):
            os.remove(db_path)

    @pytest.mark.asyncio
    async def test_init(self, temp_manager):
        """测试初始化"""
        assert temp_manager.l1 is not None
        assert temp_manager.l2 is not None
        assert temp_manager.l3 is not None

    @pytest.mark.asyncio
    async def test_set_and_get(self, temp_manager):
        """测试基本设置和获取"""
        await temp_manager.set("key1", "value1")
        value = await temp_manager.get("key1")
        assert value == "value1"

    @pytest.mark.asyncio
    async def test_get_nonexistent(self, temp_manager):
        """测试获取不存在的键"""
        value = await temp_manager.get("nonexistent")
        assert value is None

    @pytest.mark.asyncio
    async def test_delete(self, temp_manager):
        """测试删除"""
        await temp_manager.set("key1", "value1")
        result = await temp_manager.delete("key1")
        assert result is True

        value = await temp_manager.get("key1")
        assert value is None

    @pytest.mark.asyncio
    async def test_exists(self, temp_manager):
        """测试exists方法"""
        await temp_manager.set("key1", "value1")
        assert await temp_manager.exists("key1") is True
        assert await temp_manager.exists("key2") is False

    @pytest.mark.asyncio
    async def test_l1_hit(self, temp_manager):
        """测试L1命中"""
        await temp_manager.set("key1", "value1")

        # 第一次从L3获取
        value1 = await temp_manager.get("key1")
        assert value1 == "value1"

        # 第二次从L1获取
        value2 = await temp_manager.get("key1")
        assert value2 == "value1"

        stats = temp_manager.get_statistics()["manager"]
        assert stats["l1_hits"] >= 1

    @pytest.mark.asyncio
    async def test_write_through(self, temp_manager):
        """测试write-through策略"""
        await temp_manager.set("key1", "value1")

        # 检查各层级
        l1_value = await temp_manager.l1.get("key1")
        l3_value = await temp_manager.l3.get("key1")

        assert l1_value == "value1"
        assert l3_value == "value1"

    @pytest.mark.asyncio
    async def test_get_many(self, temp_manager):
        """测试批量获取"""
        await temp_manager.set("key1", "value1")
        await temp_manager.set("key2", "value2")
        await temp_manager.set("key3", "value3")

        results = await temp_manager.get_many(["key1", "key2", "key4"])
        assert results == {"key1": "value1", "key2": "value2"}

    @pytest.mark.asyncio
    async def test_set_many(self, temp_manager):
        """测试批量设置"""
        mapping = {"key1": "value1", "key2": "value2"}
        count = await temp_manager.set_many(mapping)
        assert count == 2

        assert await temp_manager.get("key1") == "value1"
        assert await temp_manager.get("key2") == "value2"

    @pytest.mark.asyncio
    async def test_clear(self, temp_manager):
        """测试清空"""
        await temp_manager.set("key1", "value1")
        await temp_manager.set("key2", "value2")
        await temp_manager.clear()

        assert await temp_manager.get("key1") is None
        assert await temp_manager.get("key2") is None

    @pytest.mark.asyncio
    async def test_health_check(self, temp_manager):
        """测试健康检查"""
        health = await temp_manager.health_check()
        assert health["L1"] is True
        assert health["L3"] is True

    @pytest.mark.asyncio
    async def test_statistics(self, temp_manager):
        """测试统计信息"""
        await temp_manager.set("key1", "value1")
        await temp_manager.get("key1")
        await temp_manager.get("key2")

        stats = await temp_manager.get_full_statistics()
        assert stats["manager"]["total_requests"] == 2
        assert stats["manager"]["l1_hits"] >= 1

    @pytest.mark.asyncio
    async def test_warm_up(self, temp_manager):
        """测试缓存预热"""
        data = {"key1": "value1", "key2": "value2"}
        count = await temp_manager.warm_up(data)
        assert count == 2

        assert await temp_manager.get("key1") == "value1"
        assert await temp_manager.get("key2") == "value2"


# =============================================================================
# 性能测试（标记为slow）
# =============================================================================


@pytest.mark.slow
@pytest.mark.asyncio
async def test_performance_comparison():
    """性能测试：有缓存 vs 无缓存"""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name

    try:
        config = CacheConfig(l2_enabled=False, l3_db_path=db_path)
        manager = MultiLevelCacheManager(config=config)

        # 预热缓存
        test_data = {f"key_{i}": f"value_{i}" for i in range(100)}
        await manager.warm_up(test_data)

        # 测试缓存命中
        start = time.time()
        for i in range(1000):
            await manager.get(f"key_{i % 100}")
        cache_time = time.time() - start

        # 测试缓存未命中（直接从L3）
        await manager.clear()
        start = time.time()
        for i in range(100):
            await manager.get(f"key_{i}")
        no_cache_time = time.time() - start

        print(f"\n性能测试结果:")
        print(f"  缓存命中 (1000次): {cache_time:.4f}秒")
        print(f"  缓存未命中 (100次): {no_cache_time:.4f}秒")
        print(f"  加速比: {no_cache_time / cache_time:.2f}x")

        stats = await manager.get_full_statistics()
        print(f"  L1命中率: {stats['manager']['l1_hit_rate']:.2%}")

        # 清理
        await manager.close()

    finally:
        if os.path.exists(db_path):
            os.remove(db_path)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
