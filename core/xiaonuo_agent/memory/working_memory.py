#!/usr/bin/env python3
"""
工作记忆 (Working Memory)
基于Redis的短期记忆系统

特点:
- 快速读写(毫秒级)
- 容量有限(默认100条)
- 自动过期(默认24小时)
- 适合存储对话上下文、临时信息

作者: Athena平台团队
创建时间: 2026-01-22
版本: v2.0.0
"""

import hashlib
import json
import logging
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

from redis.asyncio import Redis

from core.config.xiaona_config import get_config

logger = logging.getLogger(__name__)


@dataclass
class MemoryItem:
    """记忆项"""

    key: str
    value: Any
    importance: float = 0.5  # 重要性评分 0-1
    created_at: str = None
    accessed_at: str = None
    access_count: int = 0
    tags: list["key"] = None
    embedding: list["key"] = None  # 向量嵌入(可选)

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now().isoformat()
        if self.accessed_at is None:
            self.accessed_at = self.created_at
        if self.tags is None:
            self.tags = []

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        data = asdict(self)
        # 处理None值
        if self.embedding is None:
            data["key"] = None
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "MemoryItem":
        """从字典创建"""
        return cls(**data)


class WorkingMemory:
    """
    工作记忆 - 短期记忆系统

    基于 Redis 实现,特点:
    1. 快速访问(毫秒级延迟)
    2. 容量限制(默认100条)
    3. 自动过期(默认24小时)
    4. LRU淘汰策略
    """

    def __init__(
        self, max_size: int = 100, default_ttl: int = 86400, redis_client: Redis = None  # 24小时
    ):
        """
        初始化工作记忆

        Args:
            max_size: 最大记忆条数
            default_ttl: 默认过期时间(秒)
            redis_client: Redis客户端(可选,自动创建)
        """
        self.max_size = max_size
        self.default_ttl = default_ttl
        self._redis = redis_client

        # 性能统计
        self.stats = {
            "total_stores": 0,
            "total_retrievals": 0,
            "cache_hits": 0,
            "cache_misses": 0,
            "evictions": 0,
        }

    async def _get_redis(self) -> Redis:
        """获取Redis连接"""
        if self._redis is None:
            config = await get_config()
            self._redis = Redis(
                host=config.redis.host,
                port=config.redis.port,
                password=config.redis.password,
                db=config.redis.db,
                decode_responses=True,
            )
        return self._redis

    def _generate_key(self, content: Any) -> str:
        """生成记忆键"""
        # 使用内容哈希作为键
        content_str = json.dumps(content, sort_keys=True, ensure_ascii=False)
        hash_key = hashlib.md5(content_str.encode('utf-8'), usedforsecurity=False).hexdigest()
        return f"wm:{hash_key}"

    async def store(
        self, value: Any, importance: float = 0.5, tags: list["key"] = None, ttl: int | None = None
    ) -> str:
        """
        存储记忆

        Args:
            value: 记忆内容
            importance: 重要性评分(0-1)
            tags: 标签列表
            ttl: 过期时间(秒),默认使用default_ttl

        Returns:
            记忆键
        """
        redis = await self._get_redis()

        # 检查容量
        current_size = await redis.dbsize()
        if current_size >= self.max_size:
            await self._evict_low_importance()

        # 创建记忆项
        key = self._generate_key(value)
        memory_item = MemoryItem(
            key=key, value=value, importance=min(1.0, max(0.0, importance)), tags=tags or []
        )

        # 存储到Redis
        memory_key = f"working_memory:{key}"
        memory_data = json.dumps(memory_item.to_dict(), ensure_ascii=False)

        actual_ttl = ttl or self.default_ttl
        await redis.setex(memory_key, actual_ttl, memory_data)

        # 更新统计
        self.stats["total_stores"] += 1

        logger.debug(f"✅ 工作记忆存储: {key} (重要性: {importance})")
        return key

    async def retrieve(self, key: str) -> MemoryItem | None:
        """
        检索记忆

        Args:
            key: 记忆键

        Returns:
            记忆项,不存在返回None
        """
        redis = await self._get_redis()

        memory_key = f"working_memory:{key}"
        data = await redis.get(memory_key)

        if data is None:
            self.stats["cache_misses"] += 1
            return None

        # 更新访问统计
        memory_item = MemoryItem.from_dict(json.loads(data))
        memory_item.accessed_at = datetime.now().isoformat()
        memory_item.access_count += 1

        # 更新Redis中的数据
        await redis.setex(
            memory_key,
            await redis.ttl(memory_key),
            json.dumps(memory_item.to_dict(), ensure_ascii=False),
        )

        self.stats["total_retrievals"] += 1
        self.stats["cache_hits"] += 1

        return memory_item

    async def search(
        self, query: str, top_k: int = 10, tags: list["key"] = None
    ) -> list[MemoryItem]:
        """
        搜索记忆

        Args:
            query: 查询字符串
            top_k: 返回结果数量
            tags: 标签过滤(可选)

        Returns:
            匹配的记忆列表
        """
        redis = await self._get_redis()

        # 扫描所有工作记忆
        pattern = "working_memory:*"
        results = []

        async for key in redis.scan_iter(match=pattern):
            try:
                data = await redis.get(key)
                if data:
                    memory_item = MemoryItem.from_dict(json.loads(data))

                    # 文本匹配
                    if query.lower() in str(memory_item.value).lower():
                        # 标签过滤
                        if tags is None or any(tag in memory_item.tags for tag in tags):
                            results.append(memory_item)

                            if len(results) >= top_k:
                                break
            except Exception as e:
                logger.warning(f"⚠️  解析记忆项失败: {e}")
                continue

        # 按重要性和访问时间排序
        results.sort(key=lambda x: (x.importance, x.access_count), reverse=True)

        return results[:top_k]

    async def get_recent(self, n: int = 10) -> list[MemoryItem]:
        """
        获取最近的记忆

        Args:
            n: 返回数量

        Returns:
            最近的记忆列表
        """
        redis = await self._get_redis()

        # 获取所有键并按时间排序
        pattern = "working_memory:*"
        memories = []

        async for key in redis.scan_iter(match=pattern):
            try:
                data = await redis.get(key)
                if data:
                    memory_item = MemoryItem.from_dict(json.loads(data))
                    memories.append(memory_item)
            except Exception:
                continue

        # 按创建时间排序,取最近的n条
        memories.sort(key=lambda x: x.created_at, reverse=True)
        return memories[:n]

    async def update_importance(self, key: str, new_importance: float) -> bool:
        """
        更新记忆重要性

        Args:
            key: 记忆键
            new_importance: 新的重要性评分

        Returns:
            是否成功
        """
        memory_item = await self.retrieve(key)
        if memory_item is None:
            return False

        memory_item.importance = min(1.0, max(0.0, new_importance))

        redis = await self._get_redis()
        memory_key = f"working_memory:{key}"
        ttl = await redis.ttl(memory_key)

        await redis.setex(memory_key, ttl, json.dumps(memory_item.to_dict(), ensure_ascii=False))

        return True

    async def delete(self, key: str) -> bool:
        """
        删除记忆

        Args:
            key: 记忆键

        Returns:
            是否成功
        """
        redis = await self._get_redis()
        memory_key = f"working_memory:{key}"

        result = await redis.delete(memory_key)
        return result > 0

    async def clear(self) -> bool:
        """
        清空所有工作记忆

        Returns:
            是否成功
        """
        redis = await self._get_redis()
        pattern = "working_memory:*"

        count = 0
        async for key in redis.scan_iter(match=pattern):
            await redis.delete(key)
            count += 1

        logger.info(f"🗑️  清空工作记忆: {count}条")
        return count > 0

    async def _evict_low_importance(self) -> None:
        """淘汰重要性最低的记忆"""
        redis = await self._get_redis()

        # 获取所有记忆及其重要性
        memories = []
        pattern = "working_memory:*"

        async for key in redis.scan_iter(match=pattern):
            try:
                data = await redis.get(key)
                if data:
                    memory_item = MemoryItem.from_dict(json.loads(data))
                    memories.append((key, memory_item.importance))
            except Exception:
                continue

        # 按重要性排序
        memories.sort(key=lambda x: x[1])

        # 删除重要性最低的10%
        evict_count = max(1, len(memories) // 10)
        for key, _ in memories[:evict_count]:
            await redis.delete(key)

        self.stats["evictions"] += evict_count
        logger.debug(f"🔄 淘汰{evict_count}条低重要性记忆")

    async def get_stats(self) -> dict[str, Any]:
        """获取统计信息"""
        redis = await self._get_redis()

        current_size = await redis.dbsize()

        return {
            **self.stats,
            "current_size": current_size,
            "max_size": self.max_size,
            "hit_rate": (
                self.stats["cache_hits"] / self.stats["total_retrievals"]
                if self.stats["total_retrievals"] > 0
                else 0
            ),
        }

    async def health_check(self) -> bool:
        """健康检查"""
        try:
            redis = await self._get_redis()
            await redis.ping()
            return True
        except Exception as e:
            logger.error(f"❌ 工作记忆健康检查失败: {e}")
            return False

    async def close(self):
        """关闭Redis连接"""
        if self._redis:
            await self._redis.close()
            self._redis = None
            logger.info("🔌 工作记忆连接已关闭")


# 全局工作记忆实例
_working_memory = None


async def get_working_memory() -> WorkingMemory:
    """获取全局工作记忆实例"""
    global _working_memory
    if _working_memory is None:
        _working_memory = WorkingMemory()
    return _working_memory
