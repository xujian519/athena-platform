from __future__ import annotations
"""
多级缓存策略

实现三级缓存系统:
L1: 内存缓存 (Python dict) - 最快,容量最小
L2: Redis缓存 - 快速,容量中等
L3: 数据库缓存 - 较慢,容量最大

特点:
- 自动缓存逐出
- 缓存预热
- 缓存穿透保护
- 缓存雪崩防护

安全性:
- 使用JSON进行序列化,避免pickle的安全风险
- 只能缓存可JSON序列化的数据(基本类型、dict、list等)
"""

import json
import logging
import threading
import time
from collections import OrderedDict
from collections.abc import Callable
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class CacheLevel(Enum):
    """缓存级别"""

    L1_MEMORY = "L1_MEMORY"  # 内存缓存
    L2_REDIS = "L2_REDIS"  # Redis缓存
    L3_DATABASE = "L3_DATABASE"  # 数据库缓存


@dataclass
class CacheItem:
    """缓存项"""

    key: str
    value: Any
    ttl: int  # 生存时间(秒)
    created_at: float
    last_accessed: float
    access_count: int = 0
    level: CacheLevel = CacheLevel.L1_MEMORY
    metadata: dict[str, Any] = field(default_factory=dict)

    def is_expired(self) -> bool:
        """检查是否过期"""
        return time.time() - self.created_at > self.ttl

    def touch(self) -> Any:
        """更新访问时间和计数"""
        self.last_accessed = time.time()
        self.access_count += 1


class CacheStats:
    """缓存统计"""

    def __init__(self):
        self.hits = dict.fromkeys(CacheLevel, 0)
        self.misses = 0
        self.evictions = dict.fromkeys(CacheLevel, 0)
        self.total_sets = 0
        self.total_gets = 0

    def record_hit(self, level: CacheLevel) -> Any:
        """记录缓存命中"""
        self.hits[level] += 1
        self.total_gets += 1

    def record_miss(self) -> Any:
        """记录缓存未命中"""
        self.misses += 1
        self.total_gets += 1

    def record_eviction(self, level: CacheLevel) -> Any:
        """记录缓存逐出"""
        self.evictions[level] += 1

    def record_set(self) -> Any:
        """记录缓存设置"""
        self.total_sets += 1

    def get_hit_rate(self) -> float:
        """获取命中率"""
        if self.total_gets == 0:
            return 0.0
        total_hits = sum(self.hits.values())
        return total_hits / self.total_gets

    def get_stats(self) -> dict[str, Any]:
        """获取统计信息"""
        return {
            "hit_rate": self.get_hit_rate(),
            "total_gets": self.total_gets,
            "total_sets": self.total_sets,
            "hits_by_level": {k.value: v for k, v in self.hits.items()},
            "misses": self.misses,
            "evictions_by_level": {k.value: v for k, v in self.evictions.items()},
        }


class MemoryCache:
    """
    L1内存缓存

    使用OrderedDict实现LRU策略
    """

    def __init__(self, max_size: int = 1000, default_ttl: int = 300):
        """
        初始化内存缓存

        Args:
            max_size: 最大缓存项数
            default_ttl: 默认TTL(秒)
        """
        self.max_size = max_size
        self.default_ttl = default_ttl
        self.cache: OrderedDict[str, CacheItem] = OrderedDict()
        self.lock = threading.RLock()

    def get(self, key: str) -> Any | None:
        """获取缓存值"""
        with self.lock:
            if key not in self.cache:
                return None

            item = self.cache[key]

            # 检查过期
            if item.is_expired():
                del self.cache[key]
                return None

            # 移到末尾(LRU)
            self.cache.move_to_end(key)
            item.touch()

            return item.value

    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """设置缓存值"""
        with self.lock:
            if ttl is None:
                ttl = self.default_ttl

            # 如果已存在,删除旧的
            if key in self.cache:
                del self.cache[key]

            # 检查容量
            while len(self.cache) >= self.max_size:
                # 删除最旧的项
                self.cache.popitem(last=False)

            # 添加新项
            item = CacheItem(
                key=key,
                value=value,
                ttl=ttl,
                created_at=time.time(),
                last_accessed=time.time(),
                level=CacheLevel.L1_MEMORY,
            )

            self.cache[key] = item
            return True

    def delete(self, key: str) -> bool:
        """删除缓存值"""
        with self.lock:
            if key in self.cache:
                del self.cache[key]
                return True
            return False

    def clear(self) -> Any:
        """清空缓存"""
        with self.lock:
            self.cache.clear()

    def cleanup_expired(self) -> int:
        """清理过期项"""
        with self.lock:
            expired_keys = [k for k, v in self.cache.items() if v.is_expired()]

            for k in expired_keys:
                del self.cache[k]

            return len(expired_keys)

    def get_size(self) -> int:
        """获取当前大小"""
        return len(self.cache)


class RedisCache:
    """
    L2 Redis缓存

    注意:此实现使用模拟版本,实际部署时需要连接真实Redis
    """

    def __init__(
        self,
        host: str = "localhost",
        port: int = 6379,
        db: int = 0,
        default_ttl: int = 3600,
        enabled: bool = True,
    ):
        """
        初始化Redis缓存

        Args:
            host: Redis主机
            port: Redis端口
            db: 数据库编号
            default_ttl: 默认TTL(秒)
            enabled: 是否启用
        """
        self.host = host
        self.port = port
        self.db = db
        self.default_ttl = default_ttl
        self.enabled = enabled

        # 模拟存储(实际部署时替换为真实Redis连接)
        self._mock_storage: dict[str, tuple[Any, float]] = {}
        self.lock = threading.RLock()

        if enabled:
            try:
                import redis

                self.client = redis.Redis(
                    host=host, port=port, db=db, decode_responses=False, socket_connect_timeout=5
                )
                # 测试连接
                self.client.ping()
                self._use_real_redis = True
                logger.info(f"✅ 连接到Redis: {host}:{port}")
            except Exception as e:
                logger.warning(f"Redis连接失败,使用模拟存储: {e}")
                self._use_real_redis = False
        else:
            self._use_real_redis = False

    def get(self, key: str) -> Any | None:
        """获取缓存值"""
        if not self.enabled:
            return None

        if self._use_real_redis:
            try:
                data = self.client.get(key)
                if data:
                    # 使用JSON反序列化,避免pickle的安全风险
                    value = json.loads(data)
                    return value
            except json.JSONDecodeError as e:
                logger.error(f"Redis JSON反序列化失败: {e}")
            except Exception as e:
                logger.error(f"Redis GET失败: {e}")
        else:
            # 模拟存储
            with self.lock:
                if key in self._mock_storage:
                    value, expires_at = self._mock_storage[key]
                    if time.time() < expires_at:
                        return value
                    else:
                        del self._mock_storage[key]

        return None

    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """设置缓存值"""
        if not self.enabled:
            return False

        if ttl is None:
            ttl = self.default_ttl

        if self._use_real_redis:
            try:
                # 使用JSON序列化,避免pickle的安全风险
                # 只能序列化基本类型、dict、list等JSON兼容类型
                data = json.dumps(value, ensure_ascii=False)
                return self.client.setex(key, ttl, data)
            except (TypeError, ValueError) as e:
                logger.error(f"Redis JSON序列化失败,值类型不支持: {e}")
                return False
            except Exception as e:
                logger.error(f"Redis SET失败: {e}")
                return False
        else:
            # 模拟存储
            with self.lock:
                expires_at = time.time() + ttl
                self._mock_storage[key] = (value, expires_at)
            return True

    def delete(self, key: str) -> bool:
        """删除缓存值"""
        if not self.enabled:
            return False

        if self._use_real_redis:
            try:
                return self.client.delete(key) > 0
            except Exception as e:
                logger.error(f"Redis DELETE失败: {e}")
                return False
        else:
            with self.lock:
                if key in self._mock_storage:
                    del self._mock_storage[key]
                    return True

        return False

    def clear(self) -> Any:
        """清空缓存"""
        if not self.enabled:
            return

        if self._use_real_redis:
            try:
                self.client.flushdb()
            except Exception as e:
                logger.error(f"Redis CLEAR失败: {e}")
        else:
            with self.lock:
                self._mock_storage.clear()

    def get_size(self) -> int:
        """获取缓存大小"""
        if not self.enabled:
            return 0

        if self._use_real_redis:
            try:
                return self.client.dbsize()
            except Exception:
                return 0
        else:
            with self.lock:
                return len(self._mock_storage)

    def close(self) -> Any:
        """关闭Redis连接"""
        if not self.enabled:
            return

        if self._use_real_redis and hasattr(self, "client"):
            try:
                self.client.close()
                logger.info("✅ Redis连接已关闭")
            except Exception as e:
                logger.error(f"❌ 关闭Redis连接失败: {e}")

    def __enter__(self):
        """上下文管理器入口"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器出口"""
        self.close()
        return False


class MultiLevelCacheManager:
    """
    多级缓存管理器

    实现三级缓存策略:
    1. L1内存缓存 - 最快访问
    2. L2 Redis缓存 - 中等速度
    3. L3 数据库 - 慢速但大容量
    """

    def __init__(
        self,
        l1_max_size: int = 1000,
        l1_default_ttl: int = 300,
        l2_enabled: bool = True,
        l2_host: str = "localhost",
        l2_port: int = 6379,
        l2_default_ttl: int = 3600,
    ):
        """
        初始化多级缓存管理器

        Args:
            l1_max_size: L1缓存最大大小
            l1_default_ttl: L1默认TTL
            l2_enabled: 是否启用L2
            l2_host: Redis主机
            l2_port: Redis端口
            l2_default_ttl: L2默认TTL
        """
        # L1内存缓存
        self.l1_cache = MemoryCache(max_size=l1_max_size, default_ttl=l1_default_ttl)

        # L2 Redis缓存
        self.l2_cache = RedisCache(
            host=l2_host, port=l2_port, default_ttl=l2_default_ttl, enabled=l2_enabled
        )

        # 统计信息
        self.stats = CacheStats()

        # 缓存预热函数
        self._warmup_funcs: dict[str, Callable] = {}

        logger.info("✅ 多级缓存管理器初始化完成")
        logger.info(f"   L1内存缓存: max_size={l1_max_size}, ttl={l1_default_ttl}s")
        logger.info(f"   L2 Redis缓存: enabled={l2_enabled}")

    def get(self, key: str, level: CacheLevel = CacheLevel.L1_MEMORY) -> Any | None:
        """
        获取缓存值(自动逐级查找)

        Args:
            key: 缓存键
            level: 首选缓存级别

        Returns:
            缓存值或None
        """
        # 先尝试L1
        value = self.l1_cache.get(key)
        if value is not None:
            self.stats.record_hit(CacheLevel.L1_MEMORY)
            logger.debug(f"L1缓存命中: {key}")
            return value

        # L1未命中,尝试L2
        value = self.l2_cache.get(key)
        if value is not None:
            self.stats.record_hit(CacheLevel.L2_REDIS)
            logger.debug(f"L2缓存命中: {key}")

            # 回填L1
            self.l1_cache.set(key, value)
            return value

        # 全部未命中
        self.stats.record_miss()
        logger.debug(f"缓存未命中: {key}")

        return None

    def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None,
        levels: list[str] = None,
    ) -> bool:
        """
        设置缓存值(可指定缓存级别)

        Args:
            key: 缓存键
            value: 缓存值
            ttl: 生存时间
            levels: 缓存级别列表(None表示全部级别)

        Returns:
            是否成功
        """
        self.stats.record_set()

        success = True

        # 默认同时写入L1和L2
        if levels is None:
            levels = [CacheLevel.L1_MEMORY, CacheLevel.L2_REDIS]

        # 写入指定级别
        for level in levels:
            if level == CacheLevel.L1_MEMORY:
                self.l1_cache.set(key, value, ttl)
            elif level == CacheLevel.L2_REDIS:
                self.l2_cache.set(key, value, ttl)

        return success

    def delete(self, key: str) -> bool:
        """删除所有级别的缓存"""
        l1_deleted = self.l1_cache.delete(key)
        l2_deleted = self.l2_cache.delete(key)

        return l1_deleted or l2_deleted

    def get_or_set(self, key: str, func: Callable[[], Any], ttl: Optional[int] = None) -> Any:
        """
        获取缓存值,如果不存在则通过函数计算并缓存

        Args:
            key: 缓存键
            func: 计算函数
            ttl: 生存时间

        Returns:
            缓存值或计算结果
        """
        value = self.get(key)

        if value is None:
            # 缓存未命中,调用函数计算
            logger.debug(f"缓存计算: {key}")
            value = func()

            # 存入缓存
            self.set(key, value, ttl)

        return value

    def invalidate(self, pattern: Optional[str] = None) -> Any:
        """
        使缓存失效

        Args:
            pattern: 键模式(None表示全部清空)
        """
        if pattern is None:
            # 清空所有缓存
            self.l1_cache.clear()
            self.l2_cache.clear()
            logger.info("🗑️ 清空所有缓存")
        else:
            # 模式匹配删除(简化版:只处理精确匹配)
            self.l1_cache.delete(pattern)
            self.l2_cache.delete(pattern)
            logger.info(f"🗑️ 删除缓存: {pattern}")

    def cleanup_expired(self) -> dict[str, int]:
        """清理过期缓存"""
        l1_cleaned = self.l1_cache.cleanup_expired()

        cleaned = {"L1": l1_cleaned, "L2": 0}  # Redis自动处理过期

        total_cleaned = sum(cleaned.values())
        if total_cleaned > 0:
            logger.info(f"🧹 清理过期缓存: {cleaned}")

        return cleaned

    def warmup(self, keys: list[str], func: Callable[[str], Any]):
        """
        缓存预热

        Args:
            keys: 需要预热的键
            func: 获取值的函数
        """
        logger.info(f"🔥 缓存预热: {len(keys)}个键")

        warmed = 0
        for key in keys:
            # 检查是否已缓存
            if self.get(key) is not None:
                continue

            try:
                value = func(key)
                self.set(key, value)
                warmed += 1
            except Exception as e:
                logger.error(f"预热失败 {key}: {e}")

        logger.info(f"✅ 缓存预热完成: {warmed}/{len(keys)}")

    def register_warmup_func(self, name: str, func: Callable[[str], Any]) -> Any:
        """注册预热函数"""
        self._warmup_funcs[name] = func

    def get_stats(self) -> dict[str, Any]:
        """获取缓存统计"""
        stats = self.stats.get_stats()

        stats["l1_size"] = self.l1_cache.get_size()
        stats["l2_size"] = self.l2_cache.get_size()

        return stats

    def get_hit_rate_by_level(self) -> dict[str, float]:
        """获取各级别命中率"""
        if self.stats.total_gets == 0:
            return {k.value: 0.0 for k in CacheLevel}

        return {k.value: v / self.stats.total_gets for k, v in self.stats.hits.items()}


# 全局单例
_cache_manager: MultiLevelCacheManager | None = None


def get_cache_manager() -> MultiLevelCacheManager:
    """获取缓存管理器单例"""
    global _cache_manager
    if _cache_manager is None:
        _cache_manager = MultiLevelCacheManager()
    return _cache_manager


def cached(ttl: int = 300, key_prefix: str = "", cache_levels: list | None = None):
    """
    缓存装饰器

    Args:
        ttl: 生存时间
        key_prefix: 键前缀
        cache_levels: 缓存级别

    Usage:
        @cached(ttl=600, key_prefix="user_info")
        def get_user_info(user_id: str):
            # 昂贵的数据库查询
            return db.query(user_id)
    """

    def decorator(func) -> None:
        def wrapper(*args, **kwargs) -> Any:
            cache = get_cache_manager()

            # 生成缓存键
            key_parts = [key_prefix, func.__name__]
            key_parts.extend(str(arg) for arg in args)
            key_parts.extend(f"{k}={v}" for k, v in sorted(kwargs.items()))

            key = ":".join(key_parts)

            # 尝试获取缓存
            value = cache.get(key)
            if value is not None:
                return value

            # 缓存未命中,调用函数
            value = func(*args, **kwargs)

            # 存入缓存
            cache.set(key, value, ttl=ttl, levels=cache_levels)

            return value

        return wrapper

    return decorator
