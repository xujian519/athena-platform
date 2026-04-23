#!/usr/bin/env python3
from __future__ import annotations
"""
文件缓存管理器 - Athena平台缓存系统
File Cache Manager - Athena Platform Cache System

提供高性能异步文件缓存功能,支持TTL过期策略和LRU淘汰算法

作者: Athena平台团队
创建时间: 2026-01-16
版本: 1.0.0
"""

import asyncio
import hashlib
import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

import aiofiles

# 从配置导入缓存设置
try:
    from core.config.settings import get_multimodal_config

    config = get_multimodal_config()
    DEFAULT_CACHE_DIR = config.cache_dir
    DEFAULT_CACHE_TTL = config.cache_ttl
    CACHE_ENABLED = config.cache_enabled
except ImportError:
    DEFAULT_CACHE_DIR = "/tmp/athena_cache"
    DEFAULT_CACHE_TTL = 3600
    CACHE_ENABLED = True

logger = logging.getLogger(__name__)


class FileCacheEntry:
    """文件缓存条目"""

    def __init__(
        self, cache_key: str, file_path: str, content: bytes, ttl: int = DEFAULT_CACHE_TTL
    ):
        self.cache_key = cache_key
        self.file_path = file_path
        self.content = content
        self.created_at = datetime.now()
        self.expires_at = self.created_at + timedelta(seconds=ttl)
        self.size = len(content)
        self.hits = 0
        self.last_accessed = self.created_at

    def is_expired(self) -> bool:
        """检查缓存是否过期"""
        return datetime.now() >= self.expires_at

    def touch(self) -> Any:
        """更新访问时间"""
        self.last_accessed = datetime.now()
        self.hits += 1

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "cache_key": self.cache_key,
            "file_path": self.file_path,
            "size": self.size,
            "created_at": self.created_at.isoformat(),
            "expires_at": self.expires_at.isoformat(),
            "hits": self.hits,
            "last_accessed": self.last_accessed.isoformat(),
            "is_expired": self.is_expired(),
        }


class FileCache:
    """
    异步文件缓存管理器

    特性:
    - 异步IO操作,不阻塞事件循环
    - TTL过期自动清理
    - LRU淘汰策略
    - 缓存统计
    - 持久化存储
    """

    def __init__(
        self,
        cache_dir: str = DEFAULT_CACHE_DIR,
        ttl: int = DEFAULT_CACHE_TTL,
        max_size: Optional[int] = None,
        enabled: bool = CACHE_ENABLED,
    ):
        """
        初始化文件缓存

        Args:
            cache_dir: 缓存目录
            ttl: 默认缓存生存时间(秒)
            max_size: 最大缓存大小(字节),None表示不限制
            enabled: 是否启用缓存
        """
        self.cache_dir = Path(cache_dir)
        self.ttl = ttl
        self.max_size = max_size
        self.enabled = enabled

        # 内存中的缓存索引
        self._index: dict[str, FileCacheEntry] = {}
        self._lock = asyncio.Lock()

        # 统计信息
        self._stats = {"hits": 0, "misses": 0, "evictions": 0, "size_bytes": 0, "entry_count": 0}

        # 创建缓存目录
        if self.enabled:
            self._ensure_cache_dir()

    def _ensure_cache_dir(self) -> Any:
        """确保缓存目录存在"""
        try:
            self.cache_dir.mkdir(parents=True, exist_ok=True)
            logger.info(f"缓存目录已创建: {self.cache_dir}")
        except OSError as e:
            logger.error(f"创建缓存目录失败: {e}")
            self.enabled = False

    def _get_cache_key(self, file_path: str) -> str:
        """
        生成缓存键

        使用MD5哈希确保文件路径唯一性
        """
        return hashlib.md5(file_path.encode("utf-8", usedforsecurity=False), usedforsecurity=False).hexdigest()

    def _get_cache_path(self, cache_key: str) -> Path:
        """获取缓存文件路径"""
        return self.cache_dir / f"{cache_key}.cache"

    def _get_meta_path(self, cache_key: str) -> Path:
        """获取元数据文件路径"""
        return self.cache_dir / f"{cache_key}.meta"

    async def get(self, file_path: str) -> bytes | None:
        """
        获取缓存内容

        Args:
            file_path: 原始文件路径

        Returns:
            缓存的内容,如果不存在或已过期则返回None
        """
        if not self.enabled:
            return None

        cache_key = self._get_cache_key(file_path)

        async with self._lock:
            # 检查内存索引
            entry = self._index.get(cache_key)

            if entry is None:
                # 尝试从磁盘加载
                entry = await self._load_entry_from_disk(cache_key)

            if entry is None:
                self._stats["misses"] += 1
                return None

            # 检查是否过期
            if entry.is_expired():
                await self._remove_entry(cache_key)
                self._stats["misses"] += 1
                return None

            # 更新访问统计
            entry.touch()
            self._stats["hits"] += 1

            logger.debug(f"缓存命中: {file_path}")
            return entry.content

    async def set(self, file_path: str, content: bytes, ttl: Optional[int] = None) -> bool:
        """
        设置缓存

        Args:
            file_path: 原始文件路径
            content: 要缓存的内容
            ttl: 缓存生存时间(秒),None使用默认值

        Returns:
            是否成功设置缓存
        """
        if not self.enabled:
            return False

        cache_key = self._get_cache_key(file_path)
        ttl = ttl or self.ttl

        async with self._lock:
            # 检查是否需要淘汰旧缓存
            await self._ensure_space(len(content))

            # 创建缓存条目
            entry = FileCacheEntry(cache_key, file_path, content, ttl)

            # 写入磁盘
            try:
                await self._save_entry_to_disk(entry)
                self._index[cache_key] = entry
                self._stats["size_bytes"] += entry.size
                self._stats["entry_count"] = len(self._index)

                logger.debug(f"缓存已设置: {file_path} ({entry.size} bytes)")
                return True

            except OSError as e:
                logger.error(f"保存缓存失败: {e}")
                return False

    async def invalidate(self, file_path: str) -> bool:
        """
        使缓存失效

        Args:
            file_path: 原始文件路径

        Returns:
            是否成功使缓存失效
        """
        if not self.enabled:
            return False

        cache_key = self._get_cache_key(file_path)

        async with self._lock:
            return await self._remove_entry(cache_key)

    async def clear(self) -> bool:
        """
        清空所有缓存

        Returns:
            是否成功清空
        """
        if not self.enabled:
            return False

        async with self._lock:
            try:
                # 删除所有缓存文件
                for cache_file in self.cache_dir.glob("*.cache"):
                    cache_file.unlink(missing_ok=True)

                for meta_file in self.cache_dir.glob("*.meta"):
                    meta_file.unlink(missing_ok=True)

                # 清空索引
                self._index.clear()

                # 重置统计
                self._stats = {
                    "hits": 0,
                    "misses": 0,
                    "evictions": 0,
                    "size_bytes": 0,
                    "entry_count": 0,
                }

                logger.info("缓存已清空")
                return True

            except OSError as e:
                logger.error(f"清空缓存失败: {e}")
                return False

    async def cleanup_expired(self) -> int:
        """
        清理过期缓存

        Returns:
            清理的缓存条目数量
        """
        if not self.enabled:
            return 0

        async with self._lock:
            expired_keys = [key for key, entry in self._index.items() if entry.is_expired()]

            for key in expired_keys:
                await self._remove_entry(key)

            if expired_keys:
                logger.info(f"清理了 {len(expired_keys)} 个过期缓存")

            return len(expired_keys)

    async def _load_entry_from_disk(self, cache_key: str) -> FileCacheEntry | None:
        """从磁盘加载缓存条目"""
        cache_path = self._get_cache_path(cache_key)
        meta_path = self._get_meta_path(cache_key)

        if not cache_path.exists() or not meta_path.exists():
            return None

        try:
            # 读取元数据
            async with aiofiles.open(meta_path, encoding="utf-8") as f:
                meta = json.loads(await f.read())

            # 读取内容
            async with aiofiles.open(cache_path, "rb") as f:
                content = await f.read()

            # 创建条目
            entry = FileCacheEntry(
                cache_key,
                meta["file_path"],
                content,
                ttl=int(
                    (datetime.fromisoformat(meta["expires_at"]) - datetime.now()).total_seconds()
                ),
            )
            entry.hits = meta.get("hits", 0)
            entry.created_at = datetime.fromisoformat(meta["created_at"])

            return entry

        except (OSError, json.JSONDecodeError) as e:
            logger.warning(f"加载缓存条目失败: {e}")
            # 删除损坏的缓存文件
            cache_path.unlink(missing_ok=True)
            meta_path.unlink(missing_ok=True)
            return None

    async def _save_entry_to_disk(self, entry: FileCacheEntry) -> None:
        """保存缓存条目到磁盘"""
        cache_path = self._get_cache_path(entry.cache_key)
        meta_path = self._get_meta_path(entry.cache_key)

        # 保存内容
        async with aiofiles.open(cache_path, "wb") as f:
            await f.write(entry.content)

        # 保存元数据
        meta = {
            "cache_key": entry.cache_key,
            "file_path": entry.file_path,
            "created_at": entry.created_at.isoformat(),
            "expires_at": entry.expires_at.isoformat(),
            "hits": entry.hits,
            "size": entry.size,
        }

        async with aiofiles.open(meta_path, "w", encoding="utf-8") as f:
            await f.write(json.dumps(meta, ensure_ascii=False, indent=2))

    async def _remove_entry(self, cache_key: str) -> bool:
        """移除缓存条目"""
        entry = self._index.pop(cache_key, None)
        if entry:
            self._stats["size_bytes"] -= entry.size
            self._stats["entry_count"] = len(self._index)

        # 删除磁盘文件
        cache_path = self._get_cache_path(cache_key)
        meta_path = self._get_meta_path(cache_key)

        cache_path.unlink(missing_ok=True)
        meta_path.unlink(missing_ok=True)

        return True

    async def _ensure_space(self, required_size: int) -> None:
        """
        确保有足够的空间,必要时淘汰旧缓存

        使用LRU策略淘汰最少使用的缓存
        """
        if self.max_size is None:
            return

        # 计算当前使用量
        current_size = self._stats["size_bytes"]
        available_space = self.max_size - current_size

        # 如果空间不足,进行淘汰
        if available_space < required_size:
            # 按最后访问时间排序(LRU)
            entries_by_lru = sorted(self._index.values(), key=lambda e: e.last_accessed)

            # 淘汰缓存直到有足够空间
            freed_space = 0
            for entry in entries_by_lru:
                await self._remove_entry(entry.cache_key)
                self._stats["evictions"] += 1
                freed_space += entry.size

                if (self.max_size - (current_size - freed_space)) >= required_size:
                    break

            logger.info(f"淘汰了 {self._stats['evictions']} 个缓存条目")

    def get_stats(self) -> dict[str, Any]:
        """获取缓存统计信息"""
        hit_rate = 0.0
        total_requests = self._stats["hits"] + self._stats["misses"]
        if total_requests > 0:
            hit_rate = self._stats["hits"] / total_requests

        return {
            **self._stats,
            "hit_rate": hit_rate,
            "enabled": self.enabled,
            "cache_dir": str(self.cache_dir),
            "ttl": self.ttl,
            "max_size": self.max_size,
        }

    def get_cache_info(self, file_path: str) -> Optional[dict[str, Any]]:
        """获取特定文件的缓存信息"""
        cache_key = self._get_cache_key(file_path)
        entry = self._index.get(cache_key)

        if entry:
            return entry.to_dict()

        return None


# 全局缓存实例
_global_cache: FileCache | None = None
_cache_lock = asyncio.Lock()


def get_file_cache() -> FileCache:
    """获取全局文件缓存实例"""
    global _global_cache

    if _global_cache is None:
        _global_cache = FileCache()

    return _global_cache


# 导出缓存统计(用于监控)
def CACHE_STATS():
    return get_file_cache().get_stats()


# 便捷函数
async def cached_file_operation(
    file_path: Optional[str] = None, operation: callable | None = None, ttl: Optional[int] = None
) -> bytes:
    """
    执行缓存文件操作

    Args:
        file_path: 文件路径
        operation: 异步操作函数,接收文件路径,返回bytes
        ttl: 缓存时间

    Returns:
        操作结果(bytes)
    """
    cache = get_file_cache()

    # 尝试从缓存获取
    content = await cache.get(file_path)
    if content is not None:
        return content

    # 执行操作
    content = await operation(file_path)

    # 存入缓存
    await cache.set(file_path, content, ttl)

    return content
