#!/usr/bin/env python3
from __future__ import annotations
"""
优化记忆系统 - 分层管理器
Optimized Memory System - Tier Managers

实现热层、温层、冷层的数据管理

作者: Athena AI系统
创建时间: 2025-12-11
重构时间: 2026-01-26
版本: 2.1.0
"""

import json
import pickle
import sqlite3
import threading
from datetime import datetime
from pathlib import Path
from typing import Any

from core.logging_config import setup_logging
from core.memory.optimized_memory.types import (
    DataAccessPattern,
    MemoryData,
    MemoryTier,
)

logger = setup_logging()


class HotTierManager:
    """热层管理器 - 内存存储 (LRU缓存)"""

    def __init__(self, config: dict[str, Any]):
        self.config = config
        self.max_size_bytes = config.get("hot_limit_mb", 100) * 1024 * 1024
        from collections import OrderedDict

        self.data: OrderedDict[str, MemoryData] = OrderedDict()
        self.current_size = 0
        self.lock = threading.RLock()

    async def store(self, data: MemoryData) -> bool:
        """存储到热层"""
        with self.lock:
            # 检查空间限制
            if self.current_size + data.size_bytes > self.max_size_bytes:
                await self._evict_lru()

            # 如果数据已存在，先移除旧数据
            if data.data_id in self.data:
                old_data = self.data[data.data_id]
                self.current_size -= old_data.size_bytes

            # 添加新数据
            self.data[data.data_id] = data
            self.current_size += data.size_bytes

            # 移动到最前面
            self.data.move_to_end(data.data_id, last=False)

        return True

    async def retrieve(self, data_id: str) -> MemoryData | None:
        """从热层检索"""
        with self.lock:
            if data_id in self.data:
                data = self.data[data_id]
                # 更新访问信息
                data.access_count += 1
                data.last_accessed = datetime.now()
                # 移动到最前面
                self.data.move_to_end(data_id, last=False)
                return data
            return None

    async def _evict_lru(self):
        """LRU淘汰"""
        while self.current_size > self.max_size_bytes * 0.9 and self.data:
            lru_data_id = next(iter(self.data))
            lru_data = self.data.pop(lru_data_id)
            self.current_size -= lru_data.size_bytes
            logger.debug(f"热层LRU淘汰: {lru_data_id}")


class WarmTierManager:
    """温层管理器 - Redis缓存"""

    def __init__(self, config: dict[str, Any]):
        self.config = config
        self.redis_available = self._init_redis()
        self.ttl = config.get("warm_ttl", 3600)  # 1小时
        self.redis_client = None  # type: ignore

    def _init_redis(self) -> bool:
        """初始化Redis连接"""
        try:
            import redis

            self.redis_client = redis.Redis(
                host=self.config.get("redis_host", "localhost"),
                port=self.config.get("redis_port", 6379),
                db=self.config.get("redis_db", 0),
                decode_responses=False,
            )
            # 测试连接
            self.redis_client.ping()
            return True
        except Exception as e:
            logger.warning(f"Redis连接失败: {e}")
            return False

    async def store(self, data: MemoryData) -> bool:
        """存储到温层"""
        if not self.redis_available:
            return False

        try:
            key = f"warm:{data.data_id}"
            value = pickle.dumps(data)

            # 使用Pipeline提高性能
            pipe = self.redis_client.pipeline()
            pipe.set(key, value, ex=self.ttl)
            pipe.execute()

            return True
        except Exception as e:
            logger.error(f"❌ 温层存储失败: {e}")
            return False

    async def retrieve(self, data_id: str) -> MemoryData | None:
        """从温层检索"""
        if not self.redis_available:
            return None

        try:
            key = f"warm:{data_id}"
            value = self.redis_client.get(key)

            if value:
                data = pickle.loads(value)
                # 更新访问信息
                data.access_count += 1
                data.last_accessed = datetime.now()
                # 延长TTL
                self.redis_client.expire(key, self.ttl)
                return data
            return None
        except Exception as e:
            logger.error(f"❌ 温层检索失败: {e}")
            return None


class ColdTierManager:
    """冷层管理器 - 持久化存储 (SQLite)"""

    def __init__(self, config: dict[str, Any]):
        self.config = config
        self.db_path = config.get("cold_db_path", "data/memory/cold_tier.db")
        self.conn = None  # type: ignore
        self._init_database()

    def _init_database(self):
        """初始化数据库"""
        try:
            # 确保目录存在
            Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)

            self.conn = sqlite3.connect(self.db_path)
            self.conn.execute(
                """
                CREATE TABLE IF NOT EXISTS memory_data (
                    data_id TEXT PRIMARY KEY,
                    content BLOB,
                    metadata TEXT,
                    access_pattern TEXT,
                    access_count INTEGER,
                    last_accessed TIMESTAMP,
                    created_at TIMESTAMP,
                    size_bytes INTEGER,
                    tier TEXT,
                    vector_embedding BLOB,
                    related_entities TEXT,
                    access_frequency REAL,
                    decay_factor REAL
                )
            """
            )
            self.conn.execute("CREATE INDEX IF NOT EXISTS idx_tier ON memory_data(tier)")
            self.conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_last_accessed ON memory_data(last_accessed)"
            )
            self.conn.commit()
            logger.info("✅ 冷层数据库初始化完成")
        except Exception as e:
            logger.error(f"❌ 冷层数据库初始化失败: {e}")

    async def store(self, data: MemoryData) -> bool:
        """存储到冷层"""
        try:
            vector_blob = (
                pickle.dumps(data.vector_embedding) if data.vector_embedding is not None else None
            )
            entities_json = (
                json.dumps(data.related_entities) if data.related_entities else None
            )

            self.conn.execute(
                """
                INSERT OR REPLACE INTO memory_data
                (data_id, content, metadata, access_pattern, access_count,
                 last_accessed, created_at, size_bytes, tier, vector_embedding,
                 related_entities, access_frequency, decay_factor)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    data.data_id,
                    pickle.dumps(data.content),
                    json.dumps(data.metadata),
                    data.access_pattern.value,
                    data.access_count,
                    data.last_accessed,
                    data.created_at,
                    data.size_bytes,
                    data.tier.value,
                    vector_blob,
                    entities_json,
                    data.access_frequency,
                    data.decay_factor,
                ),
            )
            self.conn.commit()
            return True
        except Exception as e:
            logger.error(f"❌ 冷层存储失败: {e}")
            return False

    async def retrieve(self, data_id: str) -> MemoryData | None:
        """从冷层检索"""
        try:
            cursor = self.conn.execute(
                """
                SELECT * FROM memory_data WHERE data_id = ?
            """,
                (data_id,),
            )

            row = cursor.fetchone()
            if row:
                vector_blob = row[9]  # vector_embedding
                entities_json = row[10]  # related_entities

                return MemoryData(
                    data_id=row[0],
                    content=pickle.loads(row[1]),
                    metadata=json.loads(row[2]),
                    access_pattern=DataAccessPattern(row[3]),
                    access_count=row[4],
                    last_accessed=datetime.fromisoformat(row[5]),
                    created_at=datetime.fromisoformat(row[6]),
                    size_bytes=row[7],
                    tier=MemoryTier(row[8]),
                    vector_embedding=pickle.loads(vector_blob) if vector_blob else None,
                    related_entities=json.loads(entities_json) if entities_json else [],
                    access_frequency=row[11],
                    decay_factor=row[12],
                )
            return None
        except Exception as e:
            logger.error(f"❌ 冷层检索失败: {e}")
            return None
