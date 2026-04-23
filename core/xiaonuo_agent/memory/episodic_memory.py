#!/usr/bin/env python3
from __future__ import annotations
"""
情景记忆 (Episodic Memory)
基于PostgreSQL的长期经历记忆系统

特点:
- 存储"何时、何地、何事、为何"的经历
- 时间序列索引
- 情感标记
- 永久存储

作者: Athena平台团队
创建时间: 2026-01-22
版本: v2.0.0
"""

import json
import logging
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Any

import asyncpg

from core.config.xiaona_config import get_config
from core.database.unified_connection import get_postgres_pool

logger = logging.getLogger(__name__)


class ExperienceType(Enum):
    """经历类型"""
    INTERACTION = "interaction"  # 用户交互
    TASK_COMPLETION = "task_completion"  # 任务完成
    LEARNING = "learning"  # 学习经历
    ERROR = "error"  # 错误经历
    SUCCESS = "success"  # 成功经历
    FAILURE = "failure"  # 失败经历


@dataclass
class EpisodicMemoryItem:
    """情景记忆项"""
    episode_id: str
    experience_type: ExperienceType
    timestamp: str
    content: str
    context: dict[str, Any]  # 何地、为何等上下文
    participants: Optional[list[str]] = None  # 参与者
    emotional_tag: Optional[str] = None  # 情感标记
    importance: float = 0.5  # 重要性
    embedding: list[float] | None = None
    related_episodes: Optional[list[str]] = None  # 相关经历
    metadata: Optional[dict[str, Any]] = None

    def __post_init__(self):
        if self.participants is None:
            self.participants = []
        if self.related_episodes is None:
            self.related_episodes = []
        if self.metadata is None:
            self.metadata = {}

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        data = asdict(self)
        data['experience_type'] = self.experience_type.value
        return data


class EpisodicMemory:
    """
    情景记忆 - 长期经历记忆系统

    基于 PostgreSQL 存储:
    1. 记录具体的"事件"
    2. 包含完整上下文信息
    3. 时间序列组织
    4. 支持复杂查询

    特点:
    - 永久存储
    - 时间索引
    - 上下文丰富
    - 情感标记
    """

    def __init__(self, postgres_url: Optional[str] = None):
        """
        初始化情景记忆

        Args:
            postgres_url: PostgreSQL连接URL
        """
        self.postgres_url = postgres_url
        self._pool: asyncpg.Pool | None = None

        # 性能统计
        self.stats = {
            "total_episodes": 0,
            "total_retrievals": 0,
            "searches_by_time": 0,
            "searches_by_context": 0
        }

    async def _get_pool(self) -> asyncpg.Pool:
        """获取连接池"""
        if self._pool is None:
            if self.postgres_url is None:
                config = await get_config()
                self.postgres_url = config.get_memory_database_url(async_mode=True, driver="asyncpg")

            self._db = await get_postgres_pool(
                self.postgres_url,
                min_size=5,
                max_size=20
            )
            await self._init_schema()
        return self._pool

    async def _init_schema(self):
        """初始化数据库表"""
        pool = await self._get_pool()

        async with pool.acquire() as conn:
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS episodic_memory (
                    episode_id VARCHAR(64) PRIMARY KEY,
                    experience_type VARCHAR(32) NOT NULL,
                    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                    content TEXT NOT NULL,
                    context JSONB,
                    participants TEXT[],
                    emotional_tag VARCHAR(32),
                    importance FLOAT DEFAULT 0.5,
                    embedding VECTOR(768),
                    related_episodes TEXT[],
                    metadata JSONB,
                    created_at TIMESTAMPTZ DEFAULT NOW()
                );

                CREATE INDEX IF NOT EXISTS idx_episodic_timestamp
                    ON episodic_memory(timestamp DESC);

                CREATE INDEX IF NOT EXISTS idx_episodic_type
                    ON episodic_memory(experience_type);

                CREATE INDEX IF NOT EXISTS idx_episodic_importance
                    ON episodic_memory(importance DESC);

                CREATE INDEX IF NOT EXISTS idx_episodic_emotional
                    ON episodic_memory(emotional_tag);
            """)

            logger.info("✅ 情景记忆表初始化完成")

    async def store(
        self,
        content: str,
        experience_type: ExperienceType,
        context: Optional[dict[str, Any]] = None,
        participants: Optional[list[str]] = None,
        emotional_tag: Optional[str] = None,
        importance: float = 0.5,
        embedding: list[float] | None = None,
        related_episodes: Optional[list[str]] = None,
        metadata: Optional[dict[str, Any]] = None
    ) -> str:
        """
        存储情景记忆

        Args:
            content: 经历内容
            experience_type: 经历类型
            context: 上下文信息(何时、何地、为何)
            participants: 参与者列表
            emotional_tag: 情感标记
            importance: 重要性
            embedding: 向量嵌入(可选)
            related_episodes: 相关经历ID
            metadata: 元数据

        Returns:
            经历ID
        """
        # 生成经历ID
        import hashlib
        import time
        episode_id = f"ep_{int(time.time() * 1000)}_{hashlib.md5(content.encode('utf-8'), usedforsecurity=False).hexdigest()[:8]}"

        # 解析时间戳
        timestamp_str = context.get("timestamp") if context else None
        if timestamp_str:
            try:
                timestamp = datetime.fromisoformat(timestamp_str)
            except Exception:  # TODO: 根据上下文指定具体异常类型
                timestamp = datetime.now()
        else:
            timestamp = datetime.now()

        pool = await self._get_pool()

        async with pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO episodic_memory (
                    episode_id, experience_type, timestamp, content,
                    context, participants, emotional_tag, importance,
                    embedding, related_episodes, metadata
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
            """, episode_id, experience_type.value, timestamp, content,
                json.dumps(context or {}), participants or [],
                emotional_tag, importance, embedding, related_episodes or [],
                json.dumps(metadata or {}))

        self.stats["total_episodes"] += 1
        logger.info(f"✅ 情景记忆存储: {episode_id} ({experience_type.value})")

        return episode_id

    async def recall(
        self,
        episode_id: str
    ) -> EpisodicMemoryItem | None:
        """
        回忆特定经历

        Args:
            episode_id: 经历ID

        Returns:
            经历项,不存在返回None
        """
        pool = await self._get_pool()

        async with pool.acquire() as conn:
            row = await conn.fetchrow("""
                SELECT * FROM episodic_memory WHERE episode_id = $1
            """, episode_id)

        if row is None:
            return None

        return self._row_to_memory(row)

    async def search_by_time(
        self,
        start_time: datetime,
        end_time: datetime,
        top_k: int = 50
    ) -> list[EpisodicMemoryItem]:
        """
        按时间范围搜索经历

        Args:
            start_time: 开始时间
            end_time: 结束时间
            top_k: 返回数量

        Returns:
            经历列表
        """
        pool = await self._get_pool()

        async with pool.acquire() as conn:
            rows = await conn.fetch("""
                SELECT * FROM episodic_memory
                WHERE timestamp >= $1 AND timestamp <= $2
                ORDER BY importance DESC, timestamp DESC
                LIMIT $3
            """, start_time, end_time, top_k)

        self.stats["searches_by_time"] += 1
        return [self._row_to_memory(row) for row in rows]

    async def search_by_context(
        self,
        context_key: str,
        context_value: Any,
        top_k: int = 50
    ) -> list[EpisodicMemoryItem]:
        """
        按上下文搜索经历

        Args:
            context_key: 上下文键
            context_value: 上下文值
            top_k: 返回数量

        Returns:
            经历列表
        """
        pool = await self._get_pool()

        async with pool.acquire() as conn:
            rows = await conn.fetch("""
                SELECT * FROM episodic_memory
                WHERE context->>$1 = $2
                ORDER BY importance DESC, timestamp DESC
                LIMIT $3
            """, context_key, json.dumps(context_value), top_k)

        self.stats["searches_by_context"] += 1
        return [self._row_to_memory(row) for row in rows]

    async def search_by_emotion(
        self,
        emotional_tag: str,
        top_k: int = 50
    ) -> list[EpisodicMemoryItem]:
        """
        按情感标记搜索经历

        Args:
            emotional_tag: 情感标签
            top_k: 返回数量

        Returns:
            经历列表
        """
        pool = await self._get_pool()

        async with pool.acquire() as conn:
            rows = await conn.fetch("""
                SELECT * FROM episodic_memory
                WHERE emotional_tag = $1
                ORDER BY timestamp DESC
                LIMIT $2
            """, emotional_tag, top_k)

        return [self._row_to_memory(row) for row in rows]

    async def search_by_participant(
        self,
        participant: str,
        top_k: int = 50
    ) -> list[EpisodicMemoryItem]:
        """
        按参与者搜索经历

        Args:
            participant: 参与者名称
            top_k: 返回数量

        Returns:
            经历列表
        """
        pool = await self._get_pool()

        async with pool.acquire() as conn:
            rows = await conn.fetch("""
                SELECT * FROM episodic_memory
                WHERE $1 = ANY(participants)
                ORDER BY timestamp DESC
                LIMIT $2
            """, participant, top_k)

        return [self._row_to_memory(row) for row in rows]

    async def search_by_content(
        self,
        keyword: str,
        top_k: int = 50
    ) -> list[EpisodicMemoryItem]:
        """
        按内容关键词搜索经历

        Args:
            keyword: 关键词
            top_k: 返回数量

        Returns:
            经历列表
        """
        pool = await self._get_pool()

        async with pool.acquire() as conn:
            rows = await conn.fetch("""
                SELECT * FROM episodic_memory
                WHERE content ILIKE '%' || $1 || '%'
                ORDER BY importance DESC, timestamp DESC
                LIMIT $2
            """, keyword, top_k)

        return [self._row_to_memory(row) for row in rows]

    async def get_recent_experiences(
        self,
        days: int = 7,
        top_k: int = 50
    ) -> list[EpisodicMemoryItem]:
        """
        获取最近N天的经历

        Args:
            days: 天数
            top_k: 返回数量

        Returns:
            经历列表
        """
        start_time = datetime.now() - timedelta(days=days)
        return await self.search_by_time(start_time, datetime.now(), top_k)

    async def get_timeline(
        self,
        participant: Optional[str] = None,
        days: int = 30
    ) -> dict[str, list[EpisodicMemoryItem]]:
        """
        获取时间线(按天分组)

        Args:
            participant: 参与者过滤(可选)
            days: 天数

        Returns:
            时间线字典 {日期: [经历列表]}
        """
        start_time = datetime.now() - timedelta(days=days)

        if participant:
            experiences = await self.search_by_participant(participant, top_k=1000)
            experiences = [e for e in experiences if datetime.fromisoformat(e.timestamp) >= start_time]
        else:
            experiences = await self.search_by_time(start_time, datetime.now(), top_k=1000)

        # 按日期分组
        timeline = {}
        for exp in experiences:
            date_str = datetime.fromisoformat(exp.timestamp).strftime("%Y-%m-%d")
            if date_str not in timeline:
                timeline[date_str] = []
            timeline[date_str].append(exp)

        return timeline

    def _row_to_memory(self, row) -> EpisodicMemoryItem:
        """数据库行转换为记忆项"""
        return EpisodicMemoryItem(
            episode_id=row["episode_id"],
            experience_type=ExperienceType(row["experience_type"]),
            timestamp=row["timestamp"].isoformat(),
            content=row["content"],
            context=json.loads(row["context"]) if row["context"] else {},
            participants=list(row["participants"]) if row["participants"] else [],
            emotional_tag=row["emotional_tag"],
            importance=row["importance"],
            embedding=list(row["embedding"]) if row["embedding"] else None,
            related_episodes=list(row["related_episodes"]) if row["related_episodes"] else [],
            metadata=json.loads(row["metadata"]) if row["metadata"] else {}
        )

    async def delete(self, episode_id: str) -> bool:
        """
        删除经历

        Args:
            episode_id: 经历ID

        Returns:
            是否成功
        """
        pool = await self._get_pool()

        async with pool.acquire() as conn:
            result = await conn.execute("""
                DELETE FROM episodic_memory WHERE episode_id = $1
            """, episode_id)

            logger.info(f"🗑️  情景记忆删除: {episode_id}")
            return result > 0

    async def get_stats(self) -> dict[str, Any]:
        """获取统计信息"""
        pool = await self._get_pool()

        async with pool.acquire() as conn:
            total = await conn.fetchval("SELECT COUNT(*) FROM episodic_memory")

            # 按类型统计
            type_stats = await conn.fetch("""
                SELECT experience_type, COUNT(*) as count
                FROM episodic_memory
                GROUP BY experience_type
            """)

            # 按情感统计
            emotion_stats = await conn.fetch("""
                SELECT emotional_tag, COUNT(*) as count
                FROM episodic_memory
                WHERE emotional_tag IS NOT NULL
                GROUP BY emotional_tag
            """)

        return {
            **self.stats,
            "total_episodes": total,
            "type_distribution": {row["experience_type"]: row["count"] for row in type_stats},
            "emotion_distribution": {row["emotional_tag"]: row["count"] for row in emotion_stats}
        }

    async def health_check(self) -> bool:
        """健康检查"""
        try:
            pool = await self._get_pool()
            async with pool.acquire() as conn:
                await conn.fetchval("SELECT 1")
            return True
        except Exception as e:
            logger.error(f"❌ 情景记忆健康检查失败: {e}")
            return False


# 全局情景记忆实例
_episodic_memory = None


async def get_episodic_memory() -> EpisodicMemory:
    """获取全局情景记忆实例"""
    global _episodic_memory
    if _episodic_memory is None:
        _episodic_memory = EpisodicMemory()
    return _episodic_memory
