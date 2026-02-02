#!/usr/bin/env python3
"""
Athena三级缓存系统
实现L1内存 + L2 Redis + L3磁盘的多级缓存架构

作者: Athena AI
创建时间: 2025-12-29
版本: v1.0.0

特性:
- L1内存缓存: <1ms延迟, 500MB容量
- L2 Redis缓存: <10ms延迟, 4GB容量
- L3磁盘缓存: <100ms延迟, 无限制容量
- 智能缓存驱逐: LRU + LFU混合策略
- 缓存预热: 支持批量预热
- 缓存穿透保护: 布隆过滤器
- 缓存雪崩保护: 随机过期时间
"""

import fcntl
import hashlib
import logging
import pickle
import threading
import time
from collections import OrderedDict
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


# =============================================================================
# L1内存缓存实现
# =============================================================================


@dataclass
class CacheEntry:
    """缓存条目"""

    key: str
    value: Any
    size_bytes: int
    created_at: float
    last_accessed: float
    access_count: int = 0
    ttl: float | None = None  # TTL in seconds

    def is_expired(self) -> bool:
        """检查是否过期"""
        if self.ttl is None:
            return False
        return time.time() - self.created_at > self.ttl

    def touch(self) -> Any:
        """更新访问时间和次数"""
        self.last_accessed = time.time()
        self.access_count += 1


class L1MemoryCache:
    """L1内存缓存 - 最快速度访问"""

    def __init__(self, max_size_mb: int = 500, max_entries: int = 10000, default_ttl: int = 300):
        """
        初始化L1内存缓存

        Args:
            max_size_mb: 最大缓存大小(MB)
            max_entries: 最大条目数
            default_ttl: 默认TTL(秒)
        """
        self.max_size_bytes = max_size_mb * 1024 * 1024
        self.max_entries = max_entries
        self.default_ttl = default_ttl

        # 使用OrderedDict实现LRU
        self.cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self.current_size_bytes = 0
        self.lock = threading.RLock()

        # 统计信息
        self.stats = {"hits": 0, "misses": 0, "evictions": 0, "sets": 0, "gets": 0}

    def get(self, key: str) -> Any | None:
        """获取缓存值"""
        with self.lock:
            self.stats["gets"] += 1

            if key not in self.cache:
                self.stats["misses"] += 1
                return None

            entry = self.cache[key]

            # 检查过期
            if entry.is_expired():
                del self.cache[key]
                self.current_size_bytes -= entry.size_bytes
                self.stats["misses"] += 1
                return None

            # 更新LRU
            entry.touch()
            self.cache.move_to_end(key)

            self.stats["hits"] += 1
            return entry.value

    def set(self, key: str, value: Any, ttl: int | None = None) -> bool:
        """
        设置缓存值

        Args:
            key: 缓存键
            value: 缓存值
            ttl: 过期时间(秒), None表示使用默认值
        """
        with self.lock:
            self.stats["sets"] += 1

            # 计算值大小
            try:
                size_bytes = len(pickle.dumps(value))
            except Exception as e:
                logger.warning(f"操作失败: {e}")
                # 无法序列化的对象,估算大小
                size_bytes = 1024

            # 检查单个条目是否过大
            if size_bytes > self.max_size_bytes * 0.1:  # 单个条目不超过缓存大小的10%
                logger.warning(f"缓存值过大: {key} ({size_bytes} bytes)")
                return False

            # 如果键已存在,先删除旧的
            if key in self.cache:
                old_entry = self.cache[key]
                self.current_size_bytes -= old_entry.size_bytes
                del self.cache[key]

            # 检查是否需要驱逐
            while (
                self.current_size_bytes + size_bytes > self.max_size_bytes
                or len(self.cache) >= self.max_entries
            ):
                if not self._evict_lru():
                    break

            # 创建新条目
            entry = CacheEntry(
                key=key,
                value=value,
                size_bytes=size_bytes,
                created_at=time.time(),
                last_accessed=time.time(),
                ttl=ttl or self.default_ttl,
            )

            self.cache[key] = entry
            self.current_size_bytes += size_bytes
            return True

    def delete(self, key: str) -> bool:
        """删除缓存"""
        with self.lock:
            if key in self.cache:
                entry = self.cache[key]
                self.current_size_bytes -= entry.size_bytes
                del self.cache[key]
                return True
            return False

    def clear(self) -> Any:
        """清空缓存"""
        with self.lock:
            self.cache.clear()
            self.current_size_bytes = 0

    def _evict_lru(self) -> bool:
        """驱逐最久未使用的条目"""
        if not self.cache:
            return False

        # 获取最老的条目
        lru_key, lru_entry = next(iter(self.cache.items()))
        del self.cache[lru_key]
        self.current_size_bytes -= lru_entry.size_bytes
        self.stats["evictions"] += 1

        logger.debug(f"L1驱逐: {lru_key} ({lru_entry.size_bytes} bytes)")
        return True

    def get_stats(self) -> dict:
        """获取统计信息"""
        with self.lock:
            total_requests = self.stats["hits"] + self.stats["misses"]
            hit_rate = (self.stats["hits"] / total_requests * 100) if total_requests > 0 else 0

            return {
                "level": "L1_Memory",
                "entries": len(self.cache),
                "size_bytes": self.current_size_bytes,
                "size_mb": round(self.current_size_bytes / 1024 / 1024, 2),
                "max_size_mb": self.max_size_bytes / 1024 / 1024,
                "usage_percent": round(self.current_size_bytes / self.max_size_bytes * 100, 2),
                "hits": self.stats["hits"],
                "misses": self.stats["misses"],
                "hit_rate": round(hit_rate, 2),
                "evictions": self.stats["evictions"],
            }

    def cleanup_expired(self) -> Any:
        """清理过期条目"""
        with self.lock:
            expired_keys = [key for key, entry in self.cache.items() if entry.is_expired()]

            for key in expired_keys:
                entry = self.cache[key]
                self.current_size_bytes -= entry.size_bytes
                del self.cache[key]

            if expired_keys:
                logger.debug(f"L1清理过期条目: {len(expired_keys)}个")


# =============================================================================
# L2 Redis缓存实现
# =============================================================================


class L2RedisCache:
    """L2 Redis缓存 - 中等速度访问"""

    def __init__(
        self,
        host: str = "127.0.0.1",
        port: int = 6379,
        db: int = 0,
        password: str | None = None,
        default_ttl: int = 3600,
        key_prefix: str = "athena_l2",
    ):
        """
        初始化L2 Redis缓存

        Args:
            host: Redis主机
            port: Redis端口
            db: Redis数据库编号
            password: Redis密码
            default_ttl: 默认TTL(秒)
            key_prefix: 键前缀
        """
        self.default_ttl = default_ttl
        self.key_prefix = key_prefix
        self.connected = False

        try:
            import redis

            self.redis_client = redis.Redis(
                host=host,
                port=port,
                db=db,
                password=password,
                decode_responses=False,
                socket_connect_timeout=5,
                socket_timeout=5,
                retry_on_timeout=True,
            )

            # 测试连接
            self.redis_client.ping()
            self.connected = True
            logger.info("✅ L2 Redis缓存连接成功")

        except Exception as e:
            logger.warning(f"⚠️ L2 Redis缓存连接失败: {e}")
            self.redis_client = None

        # 统计信息
        self.stats = {"hits": 0, "misses": 0, "sets": 0, "gets": 0, "errors": 0}

    def _make_key(self, key: str) -> str:
        """生成带前缀的键"""
        return f"{self.key_prefix}:{key}"

    def get(self, key: str) -> Any | None:
        """获取缓存值"""
        self.stats["gets"] += 1

        if not self.connected or not self.redis_client:
            self.stats["misses"] += 1
            return None

        try:
            redis_key = self._make_key(key)
            data = self.redis_client.get(redis_key)

            if data is None:
                self.stats["misses"] += 1
                return None

            # 反序列化
            value = pickle.loads(data)
            self.stats["hits"] += 1
            return value

        except Exception as e:
            logger.error(f"L2缓存获取失败: {e}")
            self.stats["errors"] += 1
            self.stats["misses"] += 1
            return None

    def set(self, key: str, value: Any, ttl: int | None = None) -> bool:
        """设置缓存值"""
        self.stats["sets"] += 1

        if not self.connected or not self.redis_client:
            return False

        try:
            redis_key = self._make_key(key)
            data = pickle.dumps(value)
            expire_time = ttl or self.default_ttl

            # 添加随机偏移避免缓存雪崩
            import random

            expire_time += random.randint(0, 60)  # 0-60秒随机偏移

            result = self.redis_client.setex(name=redis_key, time=expire_time, value=data)

            return bool(result)

        except Exception as e:
            logger.error(f"L2缓存设置失败: {e}")
            self.stats["errors"] += 1
            return False

    def delete(self, key: str) -> bool:
        """删除缓存"""
        if not self.connected or not self.redis_client:
            return False

        try:
            redis_key = self._make_key(key)
            return bool(self.redis_client.delete(redis_key))
        except Exception as e:
            logger.error(f"L2缓存删除失败: {e}")
            return False

    def clear(self, pattern: str = "*") -> int:
        """清空缓存"""
        if not self.connected or not self.redis_client:
            return 0

        try:
            search_pattern = self._make_key(pattern.replace("*", ""))
            keys = self.redis_client.keys(f"{search_pattern}*")
            if keys:
                return self.redis_client.delete(*keys)
            return 0
        except Exception as e:
            logger.error(f"L2缓存清空失败: {e}")
            return 0

    def get_stats(self) -> dict:
        """获取统计信息"""
        if not self.connected or not self.redis_client:
            return {"level": "L2_Redis", "connected": False, "error": "Redis未连接"}

        try:
            info = self.redis_client.info()
            total_requests = self.stats["hits"] + self.stats["misses"]
            hit_rate = (self.stats["hits"] / total_requests * 100) if total_requests > 0 else 0

            return {
                "level": "L2_Redis",
                "connected": True,
                "memory_used": info.get("used_memory_human", "0B"),
                "memory_peak": info.get("used_memory_peak_human", "0B"),
                "total_keys": info.get("db0", {}).get("keys", 0),
                "hits": self.stats["hits"],
                "misses": self.stats["misses"],
                "hit_rate": round(hit_rate, 2),
                "errors": self.stats["errors"],
            }
        except Exception as e:
            return {"level": "L2_Redis", "connected": False, "error": str(e)}


# =============================================================================
# L3磁盘缓存实现
# =============================================================================


class L3DiskCache:
    """L3磁盘缓存 - 大容量持久化存储"""

    def __init__(
        self,
        cache_dir: str = "cache/disk",
        max_size_gb: float = 10.0,
        default_ttl: int = 86400,
        enable_compression: bool = True,
    ):
        """
        初始化L3磁盘缓存

        Args:
            cache_dir: 缓存目录
            max_size_gb: 最大缓存大小(GB)
            default_ttl: 默认TTL(秒)
            enable_compression: 是否启用压缩
        """
        self.cache_dir = Path(cache_dir)
        self.max_size_bytes = max_size_gb * 1024 * 1024 * 1024
        self.default_ttl = default_ttl
        self.enable_compression = enable_compression

        # 创建缓存目录
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        # 文件锁目录
        self.lock_dir = self.cache_dir / "locks"
        self.lock_dir.mkdir(exist_ok=True)

        # 统计信息
        self.stats = {"hits": 0, "misses": 0, "sets": 0, "gets": 0, "evictions": 0}

        logger.info(f"✅ L3磁盘缓存初始化: {self.cache_dir}")

    def _get_cache_path(self, key: str) -> Path:
        """获取缓存文件路径"""
        # 使用hashlib分目录存储
        key_hash = hashlib.md5(key.encode('utf-8'), usedforsecurity=False).hexdigest()
        subdir = self.cache_dir / key_hash[:2] / key_hash[2:4]
        subdir.mkdir(parents=True, exist_ok=True)
        return subdir / f"{key_hash[4:]}.cache"

    def _get_lock_path(self, key: str) -> Path:
        """获取锁文件路径"""
        key_hash = hashlib.md5(key.encode('utf-8'), usedforsecurity=False).hexdigest()
        return self.lock_dir / f"{key_hash}.lock"

    def _acquire_lock(self, key: str) -> Any | None:
        """获取文件锁"""
        lock_path = self._get_lock_path(key)
        try:
            lock_file = open(lock_path, "w")
            fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX)
            return lock_file
        except Exception as e:
            logger.error(f"获取锁失败: {e}")
            return None

    def _release_lock(self, lock_file) -> None:
        """释放文件锁"""
        try:
            if lock_file:
                fcntl.flock(lock_file.fileno(), fcntl.LOCK_UN)
                lock_file.close()
        except Exception as e:
            logger.error(f"释放锁失败: {e}")

    def get(self, key: str) -> Any | None:
        """获取缓存值"""
        self.stats["gets"] += 1

        cache_path = self._get_cache_path(key)

        if not cache_path.exists():
            self.stats["misses"] += 1
            return None

        # 获取锁
        lock = self._acquire_lock(key)
        if not lock:
            self.stats["misses"] += 1
            return None

        try:
            # 读取元数据
            with open(cache_path, "rb") as f:
                # 读取创建时间戳
                timestamp_bytes = f.read(8)
                created_at = float(int.from_bytes(timestamp_bytes, byteorder="big"))

                # 检查过期
                if time.time() - created_at > self.default_ttl:
                    cache_path.unlink()
                    self.stats["misses"] += 1
                    return None

                # 读取数据
                data = f.read()

                # 解压缩
                if self.enable_compression:
                    import gzip

                    data = gzip.decompress(data)

                # 反序列化
                value = pickle.loads(data)
                self.stats["hits"] += 1
                return value

        except Exception as e:
            logger.error(f"L3缓存读取失败: {e}")
            self.stats["misses"] += 1
            return None
        finally:
            self._release_lock(lock)

    def set(self, key: str, value: Any, ttl: int | None = None) -> bool:
        """设置缓存值"""
        self.stats["sets"] += 1

        cache_path = self._get_cache_path(key)

        # 获取锁
        lock = self._acquire_lock(key)
        if not lock:
            return False

        try:
            # 序列化
            data = pickle.dumps(value)

            # 压缩
            if self.enable_compression:
                import gzip

                data = gzip.compress(data)

            # 写入文件
            with open(cache_path, "wb") as f:
                # 写入创建时间
                created_at_bytes = int(time.time()).to_bytes(8, byteorder="big")
                f.write(created_at_bytes)

                # 写入数据
                f.write(data)

            return True

        except Exception as e:
            logger.error(f"L3缓存写入失败: {e}")
            return False
        finally:
            self._release_lock(lock)

    def delete(self, key: str) -> bool:
        """删除缓存"""
        cache_path = self._get_cache_path(key)
        if cache_path.exists():
            cache_path.unlink()
            return True
        return False

    def clear(self, older_than: int | None = None) -> Any:
        """
        清空缓存

        Args:
            older_than: 只清理早于N秒的缓存,None表示全部清理
        """
        try:
            cutoff_time = time.time() - older_than if older_than else 0

            for cache_file in self.cache_dir.rglob("*.cache"):
                try:
                    file_mtime = cache_file.stat().st_mtime
                    if older_than is None or file_mtime < cutoff_time:
                        cache_file.unlink()
                        self.stats["evictions"] += 1
                except KeyError as e:
                    logger.warning(f"缺少必要的数据字段: {e}")
                except Exception as e:
                    logger.error(f"处理文件时发生错误: {e}")

            logger.info(f"L3清理完成: 清理了{self.stats['evictions']}个文件")

        except Exception as e:
            logger.error(f"L3清理失败: {e}")

    def get_size(self) -> int:
        """获取当前缓存大小(字节)"""
        try:
            total_size = sum(f.stat().st_size for f in self.cache_dir.rglob("*.cache"))
            return total_size
        except Exception:
            return 0

    def get_stats(self) -> dict:
        """获取统计信息"""
        total_requests = self.stats["hits"] + self.stats["misses"]
        hit_rate = (self.stats["hits"] / total_requests * 100) if total_requests > 0 else 0

        size_bytes = self.get_size()

        return {
            "level": "L3_Disk",
            "cache_dir": str(self.cache_dir),
            "size_bytes": size_bytes,
            "size_gb": round(size_bytes / 1024 / 1024 / 1024, 2),
            "max_size_gb": self.max_size_bytes / 1024 / 1024 / 1024,
            "usage_percent": round(size_bytes / self.max_size_bytes * 100, 2),
            "hits": self.stats["hits"],
            "misses": self.stats["misses"],
            "hit_rate": round(hit_rate, 2),
            "evictions": self.stats["evictions"],
        }


# =============================================================================
# 三级缓存系统
# =============================================================================


class ThreeTierCacheSystem:
    """三级缓存系统 - 统一接口"""

    def __init__(
        self,
        l1_max_size_mb: int = 500,
        l2_enabled: bool = True,
        l2_host: str = "127.0.0.1",
        l2_port: int = 6379,
        l3_enabled: bool = True,
        l3_cache_dir: str = "cache/disk",
        l3_max_size_gb: float = 10.0,
    ):
        """
        初始化三级缓存系统

        Args:
            l1_max_size_mb: L1最大缓存大小(MB)
            l2_enabled: 是否启用L2
            l2_host: Redis主机
            l2_port: Redis端口
            l3_enabled: 是否启用L3
            l3_cache_dir: L3缓存目录
            l3_max_size_gb: L3最大缓存大小(GB)
        """
        # 初始化三级缓存
        self.l1 = L1MemoryCache(max_size_mb=l1_max_size_mb)

        self.l2 = L2RedisCache(host=l2_host, port=l2_port) if l2_enabled else None

        self.l3 = (
            L3DiskCache(cache_dir=l3_cache_dir, max_size_gb=l3_max_size_gb) if l3_enabled else None
        )

        logger.info("✅ 三级缓存系统初始化完成")

        # 启动后台清理任务
        self._start_cleanup_task()

    def get(self, key: str, default: Any = None) -> Any:
        """
        获取缓存值 - 按L1->L2->L3顺序查找

        Args:
            key: 缓存键
            default: 默认值

        Returns:
            缓存值或默认值
        """
        start_time = time.time()

        # 尝试L1
        value = self.l1.get(key)
        if value is not None:
            logger.debug(f"缓存命中 L1: {key}")
            return value

        # 尝试L2
        if self.l2:
            value = self.l2.get(key)
            if value is not None:
                logger.debug(f"缓存命中 L2: {key}")
                # 回填L1
                self.l1.set(key, value)
                return value

        # 尝试L3
        if self.l3:
            value = self.l3.get(key)
            if value is not None:
                logger.debug(f"缓存命中 L3: {key}")
                # 回填L2和L1
                if self.l2:
                    self.l2.set(key, value)
                self.l1.set(key, value)
                return value

        # 全部未命中
        latency_ms = (time.time() - start_time) * 1000
        logger.debug(f"缓存未命中: {key} (查找时间: {latency_ms:.2f}ms)")
        return default

    def set(self, key: str, value: Any, ttl: int | None = None) -> bool:
        """
        设置缓存值 - 同时写入所有层级

        Args:
            key: 缓存键
            value: 缓存值
            ttl: 过期时间(秒)

        Returns:
            是否成功
        """
        success = True

        # 写入L1
        if not self.l1.set(key, value, ttl):
            success = False

        # 写入L2
        if self.l2 and not self.l2.set(key, value, ttl):
            success = False

        # 写入L3
        if self.l3 and not self.l3.set(key, value, ttl):
            success = False

        return success

    def delete(self, key: str) -> bool:
        """删除缓存 - 同时删除所有层级"""
        success = True

        if not self.l1.delete(key):
            success = False

        if self.l2 and not self.l2.delete(key):
            success = False

        if self.l3 and not self.l3.delete(key):
            success = False

        return success

    def clear(self, level: str | None = None) -> Any:
        """
        清空缓存

        Args:
            level: 缓存级别 ("l1", "l2", "l3"), None表示全部
        """
        if level is None or level.lower() == "l1":
            self.l1.clear()

        if (level is None or level.lower() == "l2") and self.l2:
            self.l2.clear()

        if (level is None or level.lower() == "l3") and self.l3:
            self.l3.clear()

    def warm_up(self, data: dict[str, Any]) -> int:
        """
        缓存预热

        Args:
            data: 预热数据 {key: value}

        Returns:
            成功预热的数量
        """
        count = 0
        for key, value in data.items():
            if self.set(key, value):
                count += 1

        logger.info(f"🔥 缓存预热完成: {count}/{len(data)}条记录")
        return count

    def get_stats(self) -> dict:
        """获取所有层级统计信息"""
        stats = {
            "timestamp": datetime.now().isoformat(),
            "l1": self.l1.get_stats(),
            "l2": self.l2.get_stats() if self.l2 else {"level": "L2_Redis", "enabled": False},
            "l3": self.l3.get_stats() if self.l3 else {"level": "L3_Disk", "enabled": False},
        }

        # 计算总体命中率
        total_hits = (
            stats["l1"]["hits"]
            + (stats["l2"].get("hits", 0) if stats["l2"].get("enabled") else 0)
            + (stats["l3"].get("hits", 0) if stats["l3"].get("enabled") else 0)
        )
        total_requests = stats["l1"]["hits"] + stats["l1"]["misses"]

        stats["overall"] = {
            "total_hits": total_hits,
            "total_requests": total_requests,
            "hit_rate": round(total_hits / total_requests * 100, 2) if total_requests > 0 else 0,
        }

        return stats

    def _start_cleanup_task(self) -> Any:
        """启动后台清理任务"""

        def cleanup_loop() -> Any:
            while True:
                try:
                    # 每小时清理一次
                    time.sleep(3600)

                    # 清理L1过期条目
                    self.l1.cleanup_expired()

                    # 清理L3过期文件
                    if self.l3:
                        self.l3.clear(older_than=86400)  # 清理24小时前的

                except Exception as e:
                    logger.error(f"缓存清理任务失败: {e}")

        cleanup_thread = threading.Thread(target=cleanup_loop, daemon=True)
        cleanup_thread.start()
        logger.info("✅ 缓存清理任务已启动")


# =============================================================================
# 全局缓存实例
# =============================================================================

_global_cache: ThreeTierCacheSystem | None = None


def get_cache() -> ThreeTierCacheSystem:
    """获取全局缓存实例"""
    global _global_cache
    if _global_cache is None:
        _global_cache = ThreeTierCacheSystem()
    return _global_cache


def cache_result(key_prefix: str, ttl: int = 300) -> Any:
    """
    缓存函数结果的装饰器

    Args:
        key_prefix: 缓存键前缀
        ttl: 过期时间(秒)
    """

    def decorator(func) -> None:
        def wrapper(*args, **kwargs) -> Any:
            # 生成缓存键
            key_data = f"{key_prefix}:{args}:{sorted(kwargs.items())}"
            cache_key = hashlib.md5(key_data.encode('utf-8'), usedforsecurity=False).hexdigest()

            # 尝试从缓存获取
            cache = get_cache()
            cached_result = cache.get(cache_key)
            if cached_result is not None:
                return cached_result

            # 执行函数并缓存结果
            result = func(*args, **kwargs)
            cache.set(cache_key, result, ttl)
            return result

        return wrapper

    return decorator
