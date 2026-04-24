#!/usr/bin/env python3
"""
L3 SQLite持久化实现 - Phase 2.2架构优化

L3 SQLite Backend - 持久化存储层

特性:
- ACID事务保证
- 无限容量
- 自动压缩（VACUUM）
- 全文搜索支持

配置:
- 位置: ~/.athena/cache/context.db
- WAL模式: 启用（更好的并发性能）
- 同步模式: NORMAL（性能与安全平衡）

作者: Athena平台团队
创建时间: 2026-04-24
"""

import aiosqlite
import asyncio
import json
import logging
import os
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class SQLiteCacheEntry:
    """SQLite缓存条目"""

    key: str
    value: Any
    content_type: str
    created_at: float
    updated_at: float
    expires_at: Optional[float] = None
    access_count: int = 0
    size_bytes: int = 0


class L3SQLiteBackend:
    """
    L3 SQLite持久化存储

    提供可靠的持久化存储层，作为多级缓存的最后一道防线。
    """

    def __init__(
        self,
        db_path: Optional[str] = None,
        table_name: str = "context_cache",
    ):
        """
        初始化L3 SQLite存储

        Args:
            db_path: 数据库文件路径（默认: ~/.athena/cache/context.db）
            table_name: 表名
        """
        if db_path is None:
            cache_dir = Path.home() / ".athena" / "cache"
            cache_dir.mkdir(parents=True, exist_ok=True)
            db_path = str(cache_dir / "context.db")

        self.db_path = db_path
        self.table_name = table_name
        self._lock = asyncio.Lock()
        self._initialized = False

        # 统计信息
        self._reads = 0
        self._writes = 0
        self._deletes = 0
        self._errors = 0

        logger.info(f"✅ L3 SQLite存储初始化: {db_path}")

    async def _initialize(self) -> None:
        """初始化数据库表"""
        if self._initialized:
            return

        async with self._lock:
            if self._initialized:
                return

            try:
                async with aiosqlite.connect(self.db_path) as db:
                    # 启用WAL模式
                    await db.execute("PRAGMA journal_mode=WAL")
                    await db.execute("PRAGMA synchronous=NORMAL")
                    await db.execute("PRAGMA cache_size=-64000")  # 64MB缓存

                    # 创建表
                    await db.execute(f"""
                        CREATE TABLE IF NOT EXISTS {self.table_name} (
                            key TEXT PRIMARY KEY,
                            value TEXT NOT NULL,
                            content_type TEXT DEFAULT 'json',
                            created_at REAL NOT NULL,
                            updated_at REAL NOT NULL,
                            expires_at REAL,
                            access_count INTEGER DEFAULT 0,
                            size_bytes INTEGER DEFAULT 0
                        )
                    """)

                    # 创建索引
                    await db.execute(f"""
                        CREATE INDEX IF NOT EXISTS idx_{self.table_name}_expires
                        ON {self.table_name}(expires_at)
                        WHERE expires_at IS NOT NULL
                    """)

                    await db.execute(f"""
                        CREATE INDEX IF NOT EXISTS idx_{self.table_name}_created
                        ON {self.table_name}(created_at)
                    """)

                    await db.commit()

                self._initialized = True
                logger.info(f"✅ L3 SQLite表初始化完成: {self.table_name}")

            except Exception as e:
                logger.error(f"❌ L3 SQLite初始化失败: {e}")
                self._errors += 1
                raise

    async def get(self, key: str) -> Optional[Any]:
        """
        获取缓存值

        Args:
            key: 缓存键

        Returns:
            Any: 缓存值，不存在或过期返回None
        """
        await self._initialize()

        try:
            async with aiosqlite.connect(self.db_path) as db:
                db.row_factory = aiosqlite.Row

                async with db.execute(
                    f"""
                    SELECT value, content_type, expires_at
                    FROM {self.table_name}
                    WHERE key = ?
                    """,
                    (key,),
                ) as cursor:
                    row = await cursor.fetchone()

                    if row is None:
                        self._reads += 1
                        logger.debug(f"L3未命中: {key}")
                        return None

                    # 检查过期
                    if row["expires_at"] and time.time() > row["expires_at"]:
                        await self.delete(key)
                        self._reads += 1
                        logger.debug(f"L3过期: {key}")
                        return None

                    # 更新访问计数
                    await db.execute(
                        f"""
                        UPDATE {self.table_name}
                        SET access_count = access_count + 1
                        WHERE key = ?
                        """,
                        (key,),
                    )
                    await db.commit()

                    # 反序列化
                    value = json.loads(row["value"]) if row["content_type"] == "json" else row["value"]

                    self._reads += 1
                    logger.debug(f"L3命中: {key}")
                    return value

        except Exception as e:
            logger.error(f"L3获取失败: {key}, 错误: {e}")
            self._errors += 1
            return None

    async def set(
        self,
        key: str,
        value: Any,
        ttl_seconds: Optional[int] = None,
    ) -> bool:
        """
        设置缓存值

        Args:
            key: 缓存键
            value: 缓存值
            ttl_seconds: TTL（秒），None表示永不过期

        Returns:
            bool: 设置成功返回True
        """
        await self._initialize()

        try:
            # 序列化
            json_value = json.dumps(value, ensure_ascii=False)
            size_bytes = len(json_value.encode("utf-8"))

            now = time.time()
            expires_at = now + ttl_seconds if ttl_seconds else None

            async with aiosqlite.connect(self.db_path) as db:
                await db.execute(
                    f"""
                    INSERT OR REPLACE INTO {self.table_name}
                    (key, value, content_type, created_at, updated_at, expires_at, size_bytes)
                    VALUES (?, ?, ?, COALESCE((SELECT created_at FROM {self.table_name} WHERE key = ?), ?), ?, ?, ?)
                    """,
                    (
                        key,
                        json_value,
                        "json",
                        key,
                        now,
                        now,
                        expires_at,
                        size_bytes,
                    ),
                )
                await db.commit()

            self._writes += 1
            logger.debug(f"L3设置: {key} (大小: {size_bytes} bytes)")
            return True

        except Exception as e:
            logger.error(f"L3设置失败: {key}, 错误: {e}")
            self._errors += 1
            return False

    async def delete(self, key: str) -> bool:
        """
        删除缓存值

        Args:
            key: 缓存键

        Returns:
            bool: 删除成功返回True
        """
        await self._initialize()

        try:
            async with aiosqlite.connect(self.db_path) as db:
                cursor = await db.execute(
                    f"DELETE FROM {self.table_name} WHERE key = ?",
                    (key,),
                )
                await db.commit()

                deleted = cursor.rowcount > 0
                if deleted:
                    self._deletes += 1
                    logger.debug(f"L3删除: {key}")

                return deleted

        except Exception as e:
            logger.error(f"L3删除失败: {key}, 错误: {e}")
            self._errors += 1
            return False

    async def clear(self) -> bool:
        """
        清空所有缓存

        Returns:
            bool: 清空成功返回True
        """
        await self._initialize()

        try:
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute(f"DELETE FROM {self.table_name}")
                await db.commit()

                logger.info("L3缓存已清空")
                return True

        except Exception as e:
            logger.error(f"L3清空失败: {e}")
            self._errors += 1
            return False

    async def exists(self, key: str) -> bool:
        """
        检查键是否存在

        Args:
            key: 缓存键

        Returns:
            bool: 存在且未过期返回True
        """
        await self._initialize()

        try:
            async with aiosqlite.connect(self.db_path) as db:
                async with db.execute(
                    f"""
                    SELECT 1 FROM {self.table_name}
                    WHERE key = ? AND (expires_at IS NULL OR expires_at > ?)
                    LIMIT 1
                    """,
                    (key, time.time()),
                ) as cursor:
                    row = await cursor.fetchone()
                    return row is not None

        except Exception as e:
            logger.error(f"L3存在检查失败: {key}, 错误: {e}")
            return False

    async def cleanup_expired(self) -> int:
        """
        清理过期条目

        Returns:
            int: 清理的条目数
        """
        await self._initialize()

        try:
            async with aiosqlite.connect(self.db_path) as db:
                cursor = await db.execute(
                    f"""
                    DELETE FROM {self.table_name}
                    WHERE expires_at IS NOT NULL AND expires_at < ?
                    """,
                    (time.time(),),
                )
                await db.commit()

                count = cursor.rowcount
                if count > 0:
                    logger.info(f"L3清理过期条目: {count}个")

                return count

        except Exception as e:
            logger.error(f"L3清理过期失败: {e}")
            self._errors += 1
            return 0

    async def get_many(self, keys: list[str]) -> Dict[str, Any]:
        """
        批量获取缓存值

        Args:
            keys: 缓存键列表

        Returns:
            Dict[str, Any]: 键到值的映射
        """
        if not keys:
            return {}

        await self._initialize()

        try:
            async with aiosqlite.connect(self.db_path) as db:
                db.row_factory = aiosqlite.Row

                placeholders = ",".join("?" * len(keys))
                now = time.time()

                async with db.execute(
                    f"""
                    SELECT key, value, content_type, expires_at
                    FROM {self.table_name}
                    WHERE key IN ({placeholders})
                      AND (expires_at IS NULL OR expires_at > ?)
                    """,
                    keys + [now],
                ) as cursor:
                    rows = await cursor.fetchall()

                result = {}
                for row in rows:
                    key = row["key"]
                    value = (
                        json.loads(row["value"])
                        if row["content_type"] == "json"
                        else row["value"]
                    )
                    result[key] = value
                    self._reads += 1

                return result

        except Exception as e:
            logger.error(f"L3批量获取失败: {e}")
            self._errors += 1
            return {}

    async def set_many(
        self, mapping: dict[str, Any], ttl_seconds: Optional[int] = None
    ) -> int:
        """
        批量设置缓存值

        Args:
            mapping: 键到值的映射
            ttl_seconds: TTL（秒）

        Returns:
            int: 成功设置的数量
        """
        if not mapping:
            return 0

        await self._initialize()

        count = 0
        now = time.time()
        expires_at = now + ttl_seconds if ttl_seconds else None

        try:
            async with aiosqlite.connect(self.db_path) as db:
                for key, value in mapping.items():
                    try:
                        json_value = json.dumps(value, ensure_ascii=False)
                        size_bytes = len(json_value.encode("utf-8"))

                        await db.execute(
                            f"""
                            INSERT OR REPLACE INTO {self.table_name}
                            (key, value, content_type, created_at, updated_at, expires_at, size_bytes)
                            VALUES (?, ?, ?, COALESCE((SELECT created_at FROM {self.table_name} WHERE key = ?), ?), ?, ?, ?)
                            """,
                            (
                                key,
                                json_value,
                                "json",
                                key,
                                now,
                                now,
                                expires_at,
                                size_bytes,
                            ),
                        )
                        count += 1
                    except Exception as e:
                        logger.warning(f"批量设置失败: {key}, {e}")

                await db.commit()
                self._writes += count

            return count

        except Exception as e:
            logger.error(f"L3批量设置失败: {e}")
            self._errors += 1
            return count

    async def vacuum(self) -> bool:
        """
        优化数据库（VACUUM）

        Returns:
            bool: 成功返回True
        """
        await self._initialize()

        try:
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute("VACUUM")
                await db.commit()
                logger.info("L3数据库优化完成")
                return True

        except Exception as e:
            logger.error(f"L3数据库优化失败: {e}")
            return False

    async def get_statistics(self) -> Dict[str, Any]:
        """
        获取存储统计信息

        Returns:
            Dict[str, Any]: 统计信息
        """
        await self._initialize()

        try:
            async with aiosqlite.connect(self.db_path) as db:
                # 获取条目数
                async with db.execute(
                    f"SELECT COUNT(*) FROM {self.table_name}"
                ) as cursor:
                    count = (await cursor.fetchone())[0]

                # 获取总大小
                async with db.execute(
                    f"SELECT SUM(size_bytes) FROM {self.table_name}"
                ) as cursor:
                    size = (await cursor.fetchone())[0] or 0

                # 获取过期条目数
                async with db.execute(
                    f"""
                    SELECT COUNT(*) FROM {self.table_name}
                    WHERE expires_at IS NOT NULL AND expires_at < ?
                    """,
                    (time.time(),),
                ) as cursor:
                    expired = (await cursor.fetchone())[0]

        except Exception as e:
            logger.error(f"L3统计获取失败: {e}")
            count = size = expired = 0

        # 文件大小
        file_size = os.path.getsize(self.db_path) if os.path.exists(self.db_path) else 0

        return {
            "level": "L3",
            "type": "sqlite",
            "db_path": self.db_path,
            "table_name": self.table_name,
            "entries": count,
            "expired_entries": expired,
            "total_bytes": size,
            "total_mb": size / (1024 * 1024),
            "file_size_bytes": file_size,
            "file_size_mb": file_size / (1024 * 1024),
            "reads": self._reads,
            "writes": self._writes,
            "deletes": self._deletes,
            "errors": self._errors,
        }

    async def list_keys(
        self, pattern: Optional[str] = None, limit: int = 1000
    ) -> List[str]:
        """
        列出缓存键

        Args:
            pattern: 键模式（LIKE语法）
            limit: 最大返回数量

        Returns:
            List[str]: 键列表
        """
        await self._initialize()

        try:
            async with aiosqlite.connect(self.db_path) as db:
                if pattern:
                    async with db.execute(
                        f"SELECT key FROM {self.table_name} WHERE key LIKE ? LIMIT ?",
                        (f"%{pattern}%", limit),
                    ) as cursor:
                        rows = await cursor.fetchall()
                        return [row[0] for row in rows]
                else:
                    async with db.execute(
                        f"SELECT key FROM {self.table_name} LIMIT ?",
                        (limit,),
                    ) as cursor:
                        rows = await cursor.fetchall()
                        return [row[0] for row in rows]

        except Exception as e:
            logger.error(f"L3列出键失败: {e}")
            return []


__all__ = ["L3SQLiteBackend", "SQLiteCacheEntry"]
