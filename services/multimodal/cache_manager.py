#!/usr/bin/env python3
"""
缓存管理器 - 支持Redis和本地缓存
Cache Manager - Redis and Local Cache Support
"""

import json
import logging
import time
from typing import Any

logger = logging.getLogger(__name__)

class CacheManager:
    """统一缓存管理器"""

    def __init__(self, use_redis: bool = False):
        self.use_redis = use_redis
        self.redis_client = None

        # 本地内存缓存
        self.local_cache = {}
        self.cache_timeout = {}

        # 尝试连接Redis
        if use_redis:
            try:
                import redis
                self.redis_client = redis.Redis(
                    host='localhost',
                    port=6379,
                    db=2,  # 使用专用数据库
                    decode_responses=True
                )
                # 测试连接
                self.redis_client.ping()
                logger.info("✅ Redis缓存连接成功")
            except Exception as e:
                logger.warning(f"⚠️ Redis连接失败，使用本地缓存: {e}")
                self.use_redis = False

    def get(self, key: str) -> Any | None:
        """获取缓存值"""
        try:
            if self.use_redis and self.redis_client:
                # 尝试从Redis获取
                value = self.redis_client.get(key)
                if value:
                    # 同时更新本地缓存（L1缓存）
                    self.local_cache[key] = json.loads(value) if isinstance(value, str) else value
                    return self.local_cache[key]
            else:
                # 仅使用本地缓存
                if key in self.cache_timeout:
                    if time.time() < self.cache_timeout[key]:
                        return self.local_cache.get(key)
                    else:
                        # 过期，清理
                        self.delete(key)
                return self.local_cache.get(key)
        except Exception as e:
            logger.error(f"缓存获取失败 {key}: {e}")
        return None

    def set(self, key: str, value: Any, timeout: int = 3600) -> Any:
        """设置缓存值"""
        try:
            # 设置本地缓存
            self.local_cache[key] = value
            self.cache_timeout[key] = time.time() + timeout

            # 设置Redis缓存
            if self.use_redis and self.redis_client:
                if isinstance(value, (dict, list)):
                    value = json.dumps(value, ensure_ascii=False)
                self.redis_client.setex(key, timeout, value)

        except Exception as e:
            logger.error(f"缓存设置失败 {key}: {e}")

    def delete(self, key: str) -> Any:
        """删除缓存"""
        try:
            self.local_cache.pop(key, None)
            self.cache_timeout.pop(key, None)

            if self.use_redis and self.redis_client:
                self.redis_client.delete(key)

        except Exception as e:
            logger.error(f"缓存删除失败 {key}: {e}")

    def delete_pattern(self, pattern: str) -> None:
        """批量删除缓存（模式匹配）"""
        try:
            # 删除本地缓存
            keys_to_delete = [k for k in self.local_cache.keys() if pattern in k]
            for key in keys_to_delete:
                self.delete(key)

            # 删除Redis缓存
            if self.use_redis and self.redis_client:
                keys = self.redis_client.keys(f"*{pattern}*")
                if keys:
                    self.redis_client.delete(*keys)

        except Exception as e:
            logger.error(f"批量删除缓存失败 {pattern}: {e}")

    def exists(self, key: str) -> bool:
        """检查缓存是否存在"""
        return self.get(key) is not None

    def clear_all(self) -> None:
        """清空所有缓存"""
        try:
            self.local_cache.clear()
            self.cache_timeout.clear()

            if self.use_redis and self.redis_client:
                self.redis_client.flushdb()

            logger.info("缓存已清空")

        except Exception as e:
            logger.error(f"清空缓存失败: {e}")

    def get_stats(self) -> dict[str, Any]:
        """获取缓存统计信息"""
        try:
            stats = {
                "local_cache_size": len(self.local_cache),
                "local_cache_items": len(self.cache_timeout),
                "redis_enabled": self.use_redis
            }

            if self.use_redis and self.redis_client:
                redis_info = self.redis_client.info()
                stats.update({
                    "redis_connected_clients": redis_info.get("connected_clients", 0),
                    "redis_used_memory": redis_info.get("used_memory_human", "N/A"),
                    "redis_keyspace_hits": redis_info.get("keyspace_hits", 0),
                    "redis_keyspace_misses": redis_info.get("keyspace_misses", 0),
                })

            return stats

        except Exception as e:
            logger.error(f"获取缓存统计失败: {e}")
            return {"error": str(e)}

# 全局缓存实例
cache_manager = CacheManager(use_redis=True)  # 自动检测Redis可用性

# 缓存装饰器
def cache_result(timeout: int = 3600, key_prefix: str = "default") -> Any:
    """缓存结果装饰器"""
    def decorator(func) -> None:
        def wrapper(*args, **kwargs) -> Any:
            # 生成缓存键
            cache_key = f"{key_prefix}:{func.__name__}:{hash(str(args) + str(kwargs))}"

            # 尝试从缓存获取
            result = cache_manager.get(cache_key)
            if result is not None:
                logger.debug(f"缓存命中: {cache_key}")
                return result

            # 执行函数
            result = func(*args, **kwargs)

            # 存入缓存
            cache_manager.set(cache_key, result, timeout)
            logger.debug(f"缓存设置: {cache_key}")

            return result
        return wrapper
    return decorator

# 文件缓存专用函数
class FileCacheManager:
    """文件专用缓存管理"""

    @staticmethod
    def cache_file_info(file_id: str, file_info: dict[str, Any], timeout: int = 3600) -> Any:
        """缓存文件信息"""
        cache_manager.set(f"file_info:{file_id}", file_info, timeout)

    @staticmethod
    def get_cached_file_info(file_id: str) -> dict[str, Any | None]:
        """获取缓存的文件信息"""
        return cache_manager.get(f"file_info:{file_id}")

    @staticmethod
    def cache_search_results(query: str, file_type: str, results: list[dict[str, Any]], timeout: int = 300) -> Any:
        """缓存搜索结果"""
        cache_key = f"search:{query}:{file_type}"
        cache_manager.set(cache_key, results, timeout)

    @staticmethod
    def get_cached_search_results(query: str, file_type: str) -> list[dict[str, Any | None]]:
        """获取缓存的搜索结果"""
        cache_key = f"search:{query}:{file_type}"
        return cache_manager.get(cache_key)

    @staticmethod
    def cache_thumbnail_path(file_hash: str, thumbnail_path: str, timeout: int = 7200) -> Any:
        """缓存缩略图路径"""
        cache_manager.set(f"thumbnail:{file_hash}", thumbnail_path, timeout)

    @staticmethod
    def get_cached_thumbnail_path(file_hash: str) -> str | None:
        """获取缓存的缩略图路径"""
        return cache_manager.get(f"thumbnail:{file_hash}")

    @staticmethod
    def invalidate_file_cache(file_id: str) -> Any:
        """失效文件相关缓存"""
        # 删除文件信息缓存
        cache_manager.delete(f"file_info:{file_id}")

        # 删除相关搜索缓存（通过模式匹配）
        cache_manager.delete_pattern("search:")

# 测试函数
def test_cache_performance() -> Any:
    """测试缓存性能"""
    print("=== 缓存性能测试 ===")

    # 测试缓存读写
    start_time = time.time()

    # 写入1000个缓存项
    for i in range(1000):
        cache_manager.set(f"test_key_{i}", f"test_value_{i}", 3600)

    write_time = time.time() - start_time
    print(f"写入1000个缓存项耗时: {write_time:.4f}s")

    # 读取1000个缓存项
    start_time = time.time()

    hit_count = 0
    for i in range(1000):
        if cache_manager.get(f"test_key_{i}") == f"test_value_{i}":
            hit_count += 1

    read_time = time.time() - start_time
    print(f"读取1000个缓存项耗时: {read_time:.4f}s")
    print(f"缓存命中率: {hit_count/1000*100:.2f}%")

    # 获取缓存统计
    stats = cache_manager.get_stats()
    print(f"缓存统计: {stats}")

if __name__ == "__main__":
    test_cache_performance()
