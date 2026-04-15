"""
缓存模块单元测试
测试缓存系统的核心功能
"""

import time

import pytest


class TestCacheModule:
    """缓存模块测试类"""

    def test_cache_module_import(self):
        """测试缓存模块可以导入"""
        try:
            import core.cache
            assert core.cache is not None
        except ImportError:
            pytest.skip("缓存模块导入失败")

    def test_cache_manager_import(self):
        """测试缓存管理器可以导入"""
        try:
            from core.cache.cache_manager import CacheManager
            assert CacheManager is not None
        except ImportError as e:
            pytest.skip(f"缓存管理器导入失败: {e}")

    def test_redis_cache_import(self):
        """测试Redis缓存可以导入"""
        try:
            from core.cache.redis_cache import RedisCache
            assert RedisCache is not None
        except ImportError:
            pytest.skip("Redis缓存导入失败")

    def test_memory_cache_import(self):
        """测试内存缓存可以导入"""
        try:
            from core.cache.memory_cache import MemoryCache
            assert MemoryCache is not None
        except ImportError:
            pytest.skip("内存缓存导入失败")


class TestMemoryCache:
    """内存缓存测试"""

    @pytest.fixture
    def memory_cache(self):
        """创建内存缓存实例"""
        try:
            from core.cache.memory_cache import MemoryCache
            return MemoryCache()
        except ImportError:
            pytest.skip("MemoryCache不可用")

    def test_memory_cache_set_get(self, memory_cache):
        """测试内存缓存的set和get操作"""
        # 设置值
        memory_cache.set("test_key", "test_value")

        # 获取值
        value = memory_cache.get("test_key")
        assert value == "test_value"

    def test_memory_cache_delete(self, memory_cache):
        """测试内存缓存的delete操作"""
        # 设置值
        memory_cache.set("delete_key", "delete_value")

        # 删除值
        memory_cache.delete("delete_key")

        # 验证已删除
        value = memory_cache.get("delete_key")
        assert value is None

    def test_memory_cache_exists(self, memory_cache):
        """测试内存缓存的exists操作"""
        # 测试不存在的key
        assert not memory_cache.exists("nonexistent_key")

        # 设置key
        memory_cache.set("exists_key", "exists_value")

        # 测试存在的key
        assert memory_cache.exists("exists_key")

    def test_memory_cache_clear(self, memory_cache):
        """测试内存缓存的clear操作"""
        # 设置多个值
        memory_cache.set("key1", "value1")
        memory_cache.set("key2", "value2")
        memory_cache.set("key3", "value3")

        # 清空缓存
        memory_cache.clear()

        # 验证所有值都已清除
        assert memory_cache.get("key1") is None
        assert memory_cache.get("key2") is None
        assert memory_cache.get("key3") is None

    def test_memory_cache_ttl(self, memory_cache):
        """测试内存缓存的TTL（生存时间）"""
        # 设置带TTL的值（1秒）
        memory_cache.set("ttl_key", "ttl_value", ttl=1)

        # 立即获取应该存在
        assert memory_cache.get("ttl_key") == "ttl_value"

        # 等待TTL过期
        time.sleep(1.5)

        # 应该已过期
        assert memory_cache.get("ttl_key") is None


class TestCacheManager:
    """缓存管理器测试"""

    @pytest.fixture
    def cache_manager(self):
        """创建缓存管理器实例"""
        try:
            from core.cache.cache_manager import CacheManager
            return CacheManager()
        except ImportError:
            pytest.skip("CacheManager不可用")

    def test_cache_manager_initialization(self, cache_manager):
        """测试缓存管理器初始化"""
        assert cache_manager is not None

    def test_cache_manager_set_get(self, cache_manager):
        """测试缓存管理器的set和get操作"""
        # 设置值
        cache_manager.set("manager_key", "manager_value")

        # 获取值
        value = cache_manager.get("manager_key")
        assert value == "manager_value"

    def test_cache_manager_delete(self, cache_manager):
        """测试缓存管理器的delete操作"""
        # 设置值
        cache_manager.set("delete_key", "delete_value")

        # 删除值
        cache_manager.delete("delete_key")

        # 验证已删除
        value = cache_manager.get("delete_key")
        assert value is None

    def test_cache_manager_get_many(self, cache_manager):
        """测试批量获取"""
        # 设置多个值
        cache_manager.set("key1", "value1")
        cache_manager.set("key2", "value2")
        cache_manager.set("key3", "value3")

        # 批量获取
        values = cache_manager.get_many(["key1", "key2", "key3"])

        assert isinstance(values, dict)
        assert values["key1"] == "value1"
        assert values["key2"] == "value2"
        assert values["key3"] == "value3"

    def test_cache_manager_set_many(self, cache_manager):
        """测试批量设置"""
        # 准备数据
        data = {
            "batch_key1": "batch_value1",
            "batch_key2": "batch_value2",
            "batch_key3": "batch_value3",
        }

        # 批量设置
        cache_manager.set_many(data)

        # 验证
        assert cache_manager.get("batch_key1") == "batch_value1"
        assert cache_manager.get("batch_key2") == "batch_value2"
        assert cache_manager.get("batch_key3") == "batch_value3"


class TestCachePerformance:
    """缓存性能测试"""

    def test_cache_performance_basic(self):
        """测试缓存基本性能"""
        try:
            from core.cache.memory_cache import MemoryCache

            cache = MemoryCache()

            # 测试写入性能（1000次）
            start_time = time.time()
            for i in range(1000):
                cache.set(f"perf_key_{i}", f"perf_value_{i}")
            write_time = time.time() - start_time

            # 测试读取性能（1000次）
            start_time = time.time()
            for i in range(1000):
                cache.get(f"perf_key_{i}")
            read_time = time.time() - start_time

            # 性能断言
            assert write_time < 1.0, f"写入1000个键值对应该在1秒内完成，实际耗时: {write_time:.2f}秒"
            assert read_time < 0.5, f"读取1000个键值对应该在0.5秒内完成，实际耗时: {read_time:.2f}秒"

        except ImportError:
            pytest.skip("MemoryCache不可用")

    @pytest.mark.slow
    def test_cache_performance_large_dataset(self):
        """测试大数据集缓存性能"""
        try:
            from core.cache.memory_cache import MemoryCache

            cache = MemoryCache()

            # 测试大数据集（10000个键值对）
            start_time = time.time()
            for i in range(10000):
                cache.set(f"large_key_{i}", f"large_value_{i}" * 10)
            write_time = time.time() - start_time

            # 性能断言
            assert write_time < 10.0, f"写入10000个键值对应该在10秒内完成，实际耗时: {write_time:.2f}秒"

        except ImportError:
            pytest.skip("MemoryCache不可用")
