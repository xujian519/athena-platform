
# pyright: ignore
# !/usr/bin/env python3
"""
缓存管理器
Cache Manager

提供智能缓存功能,优化LLM调用性能

作者: 小娜·天秤女神
创建时间: 2025-12-16
版本: v1.0 Cache Manager
"""

import asyncio
import contextlib
import hashlib
import json
import logging
import pickle
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Optional

from core.logging_config import setup_logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = setup_logging()


@dataclass
class CacheEntry:
    """缓存条目"""

    key: str
    value: Any
    created_at: datetime
    expires_at: datetime
    access_count: int = 0
    last_accessed: datetime = field(default_factory=datetime.now)
    size_bytes: int = 0
    tags: list[str] = field(default_factory=list)


@dataclass
class CacheStats:
    """缓存统计"""

    total_entries: int = 0
    total_size_mb: float = 0.0
    hit_count: int = 0
    miss_count: int = 0
    eviction_count: int = 0
    hit_rate: float = 0.0


class CacheManager:
    """智能缓存管理器"""

    def __init__(self, max_size_mb: float = 100.0, default_ttl: int = 3600):
        self.max_size_mb = max_size_mb
        self.default_ttl = default_ttl

        # 缓存存储
        self.cache: dict[str, CacheEntry] = {}
        self.tag_index: dict[str, list[str] = {}

        # 统计信息
        self.stats = CacheStats()

        # 缓存目录
        self.cache_dir = Path("/Users/xujian/Athena工作平台/cache")
        self.cache_dir.mkdir(exist_ok=True)

        # 启动时加载持久化缓存
        self._load_persistent_cache()

        # 内存泄露修复: 后台清理任务引用 - 使用下划线前缀避免与方法名冲突
        self._cleanup_task: asyncio.Optional[Task] = None
        self._cleanup_running = False

    def _generate_key(
        self,
        prompt: str,
        model: str,
        system_message: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 4000,
    ) -> str:
        """生成缓存键"""
        key_data = {
            "prompt": prompt,
            "model": model,
            "system_message": system_message,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        # 使用MD5生成唯一键
        key_str = json.dumps(key_data, sort_keys=True)
        return hashlib.md5(key_str.encode(), usedforsecurity=False).hexdigest()

    async def get(self, key: str) -> Optional[Any]:
        """获取缓存值"""
        entry = self.cache.get(key)

        if entry is None:
            self.stats.miss_count += 1
            self._update_hit_rate()
            return None

        # 检查是否过期
        if entry.expires_at and datetime.now() > entry.expires_at:
            await self.delete(key)
            self.stats.miss_count += 1
            self._update_hit_rate()
            return None

        # 更新访问信息
        entry.access_count += 1
        entry.last_accessed = datetime.now()

        self.stats.hit_count += 1
        self._update_hit_rate()

        logger.debug(f"缓存命中: {key[:16]}...")
        return entry.value

    async def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None,
        tags: Optional[list[str]] = None,
        persist: bool = False,
    ) -> bool:
        """设置缓存值"""
        try:
            # 计算值的大小
            value_bytes = pickle.dumps(value)
            size_bytes = len(value_bytes)

            # 检查是否超过最大大小限制
            if size_bytes > self.max_size_mb * 1024 * 1024:
                logger.warning(f"缓存项过大,跳过缓存: {size_bytes / 1024 / 1024:.2f}MB")
                return False

            # 计算过期时间
            expires_at = None
            if ttl or self.default_ttl:
                seconds = ttl or self.default_ttl
                expires_at = datetime.now() + timedelta(seconds=seconds)

            # 如果需要,清理空间
            await self._ensure_space(size_bytes)

            # 创建缓存条目
            entry = CacheEntry(
                key=key,
                value=value,
                created_at=datetime.now(),
                expires_at=expires_at,
                size_bytes=size_bytes,
                tags=tags or [],
            )

            # 存储缓存
            self.cache[key] = entry

            # 更新标签索引
            for tag in entry.tags:
                if tag not in self.tag_index:
                    self.tag_index[tag]] = []
                if key not in self.tag_index[tag]:
                    self.tag_index[tag].append(key)

            # 持久化到磁盘(如果需要)
            if persist:
                await self._persist_entry(key, entry)

            # 更新统计
            self._update_stats()

            logger.debug(f"缓存设置: {key[:16]}... (大小: {size_bytes / 1024:.2f}KB)")
            return True

        except Exception:
            return False

    async def delete(self, key: str) -> bool:
        """删除缓存条目"""
        entry = self.cache.pop(key, None)
        if entry:
            # 删除标签索引
            for tag in entry.tags:
                if tag in self.tag_index and key in self.tag_index[tag]:
                    self.tag_index[tag].remove(key)

            # 删除持久化文件
            await self._delete_persistent_entry(key)

            self._update_stats()
            return True
        return False

    async def clear_by_tag(self, tag: str) -> int:
        """按标签清除缓存"""
        if tag not in self.tag_index:
            return 0

        keys_to_delete = self.tag_index[tag].copy()
        count = 0

        for key in keys_to_delete:
            if await self.delete(key):
                count += 1

        del self.tag_index[tag]
        return count

    async def clear_expired(self) -> int:
        """清除过期缓存"""
        now = datetime.now()
        expired_keys = []

        for key, entry in self.cache.items():
            if entry.expires_at and now > entry.expires_at:
                expired_keys.append(key)

        count = 0
        for key in expired_keys:
            if await self.delete(key):
                count += 1

        if count > 0:
            logger.info(f"清除过期缓存: {count} 项")
            self.stats.eviction_count += count

        return count

    async def _ensure_space(self, required_bytes: int):
        """确保有足够的空间"""
        current_size = sum(entry.size_bytes for entry in self.cache.values())
        max_bytes = self.max_size_mb * 1024 * 1024

        # 如果当前大小加上新项超过限制,执行LRU清理
        if current_size + required_bytes > max_bytes:
            await self._lru_evict(int((current_size + required_bytes) * 0.8))  # 保留80%空间

    async def _lru_evict(self, target_size: int):
        """LRU淘汰策略"""
        # 按最后访问时间排序
        sorted_entries = sorted(self.cache.items(), key=lambda x: x[1].last_accessed)

        bytes_removed = 0
        for key, entry in sorted_entries:
            if sum(e.size_bytes for e in self.cache.values()) <= target_size:
                break

            bytes_removed += entry.size_bytes
            await self.delete(key)
            self.stats.eviction_count += 1

        if bytes_removed > 0:
            logger.info(f"LRU淘汰: {bytes_removed / 1024:.2f}KB")

    def _update_stats(self) -> Any:
        """更新统计信息"""
        self.stats.total_entries = len(self.cache)
        self.stats.total_size_mb = sum(entry.size_bytes for entry in self.cache.values()) / (
            1024 * 1024
        )

    def _update_hit_rate(self) -> Any:
        """更新命中率"""
        total = self.stats.hit_count + self.stats.miss_count
        if total > 0:
            self.stats.hit_rate = self.stats.hit_count / total

    async def _persist_entry(self, key: str, entry: CacheEntry):
        """持久化缓存条目到磁盘"""
        try:
            cache_file = self.cache_dir / f"{key}.cache"
            cache_data = {"entry": entry, "value": entry.value}

            with open(cache_file, "wb") as f:
                pickle.dump(cache_data, f)

        except Exception as e:
            # 持久化缓存保存失败，记录警告但不影响主流程
            logger.warning(f"保存持久化缓存失败 {key}: {e}")

    def _load_persistent_cache(self) -> Any:
        """加载持久化缓存"""
        try:
            loaded_count = 0
            for cache_file in self.cache_dir.glob("*.cache"):
                try:
                    with open(cache_file, "rb") as f:
                        cache_data = pickle.load(f)

                    entry = cache_data.get("entry")
                    # 检查是否过期
                    if not entry.expires_at or datetime.now() <= entry.expires_at:
                        self.cache[entry.key] = entry
                        loaded_count += 1

                    # 删除过期文件
                    else:
                        cache_file.unlink()

                except Exception as e:
                    # 单个缓存文件加载失败，跳过该文件
                    logger.debug(f"跳过损坏的缓存文件 {cache_file}: {e}")

            if loaded_count > 0:
                logger.info(f"加载持久化缓存: {loaded_count} 项")

        except Exception as e:
            # 加载持久化缓存整体失败，记录错误但不影响系统启动
            logger.error(f"加载持久化缓存失败: {e}", exc_info=True)

    async def _delete_persistent_entry(self, key: str):
        """删除持久化缓存文件"""
        try:
            cache_file = self.cache_dir / f"{key}.cache"
            if cache_file.exists():
                cache_file.unlink()
        except Exception as e:
            # 删除缓存文件失败，记录警告
            logger.debug(f"删除缓存文件失败 {key}: {e}")

    def get_stats(self) -> CacheStats:
        """获取缓存统计"""
        self._update_stats()
        return self.stats

    def get_top_entries(self, limit: int = 10) -> list[dict[str, Any]]:
        """获取访问最多的缓存条目"""
        sorted_entries = sorted(self.cache.items(), key=lambda x: x[1].access_count, reverse=True)

        return [
            {
                "key": key[:16] + "...",
                "access_count": entry.access_count,
                "created_at": entry.created_at.isoformat(),
                "last_accessed": entry.last_accessed.isoformat(),
                "size_kb": entry.size_bytes / 1024,
                "tags": entry.tags,
            }
            for key, entry in sorted_entries[:limit]
        ]

    async def _cleanup_loop(self):
        """内存泄露修复: 后台清理循环 - 重命名方法避免与实例变量冲突"""
        try:
            while True:
                try:
                    await asyncio.sleep(300)  # 每5分钟清理一次
                    await self.clear_expired()
                except asyncio.CancelledError:
                    # 任务被取消，正常退出
                    logger.info("🧹 清理任务已取消")
                    break
                except Exception as e:
                    # 清理任务执行失败，记录错误并继续
                    logger.error(f"缓存清理任务失败: {e}", exc_info=True)
        except asyncio.CancelledError as e:
            logger.info("🧹 清理任务收到取消信号")
            logger.error(f"操作失败: {e}", exc_info=True)
            raise

    async def start_cleanup_task(self):
        """启动后台清理任务"""
        if not self._cleanup_task or self._cleanup_task.done():
            self._cleanup_task = asyncio.create_task(self._cleanup_loop())
            self._cleanup_running = True
            logger.info("✅ 缓存清理任务已启动")

    async def stop_cleanup_task(self):
        """内存泄露修复: 停止后台清理任务"""
        if self._cleanup_task and not self._cleanup_task.done():
            self._cleanup_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._cleanup_task
            self._cleanup_running = False
            logger.info("✅ 缓存清理任务已停止")

    async def __aenter__(self):
        """异步上下文管理器入口"""
        await self.start_cleanup_task()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器出口"""
        await self.stop_cleanup_task()

    def __del__(self):
        """析构函数 - 确保资源被清理"""
        try:
            if hasattr(self, '_cleanup_task'):
                if self._cleanup_task and not self._cleanup_task.done():
                    self._cleanup_task.cancel()
        except Exception as e:
            logger.error(f"捕获异常: {e}", exc_info=True)


# 全局缓存管理器实例
cache_manager = CacheManager(max_size_mb=50.0, default_ttl=3600)  # 50MB缓存  # 1小时过期


# 便捷函数
async def get_cached_response(
    prompt: str,
    model: str,
    system_message: Optional[str] = None,
    temperature: float = 0.7,
    max_tokens: int = 4000,
) -> Optional[str]:
    """获取缓存的响应"""
    key = cache_manager._generate_key(prompt, model, system_message, temperature, max_tokens)  # type: ignore
    return await cache_manager.get(key)


async def cache_response(
    prompt: str,
    model: str,
    response: str,
    system_message: Optional[str] = None,
    temperature: float = 0.7,
    max_tokens: int = 4000,
    ttl: Optional[int] = None,
    tags: Optional[list[str]] = None,
):
    """缓存响应"""
    key = cache_manager._generate_key(prompt, model, system_message, temperature, max_tokens)  # type: ignore
    return await cache_manager.set(key, response, ttl=ttl, tags=tags)


def get_cache_stats() -> CacheStats:
    """获取缓存统计"""
    return cache_manager.get_stats()

