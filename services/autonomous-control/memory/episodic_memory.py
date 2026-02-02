#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
情景记忆数据库
Episodic Memory Database

存储和管理具体的交互情景和案例记忆

作者: 小娜·天秤女神
创建时间: 2024年12月15日
"""

import asyncio
from core.async_main import async_main
from core.database.unified_connection import get_postgres_pool
from typing import Dict, List, Any, Optional
from datetime import datetime
import json
import logging

logger = logging.getLogger(__name__)

class EpisodicMemory:
    """情景记忆系统"""

    def __init__(self):
        """初始化情景记忆"""
        self.db_config = {
            "host": "localhost",
            "port": 5432,
            "user": "postgres",
            "password": "xj78102",
            "database": "athena_memory",
            "min_size": 5,
            "max_size": 20
        }
        self.pool = None

    async def initialize(self):
        """初始化数据库连接池"""
        try:
            self.db = await get_postgres_pool(**self.db_config)
            await self._create_tables()
            logger.info("✅ 情景记忆数据库初始化完成")
        except Exception as e:
            logger.error(f"情景记忆初始化失败: {str(e)}")
            raise

    async def _create_tables(self):
        """创建数据表"""
        async with self.pool.acquire() as conn:
            # 创建情景记忆表
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS episodic_memories (
                    id SERIAL PRIMARY KEY,
                    episode_id VARCHAR(50) UNIQUE NOT NULL,
                    user_id VARCHAR(50) NOT NULL,
                    business_type VARCHAR(20) NOT NULL,
                    title TEXT,
                    content TEXT NOT NULL,
                    entities JSONB,
                    emotions JSONB,
                    outcomes JSONB,
                    importance FLOAT DEFAULT 1.0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    tags TEXT[]
                )
            """)

            # 创建索引
            await conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_episodic_user_id
                ON episodic_memories(user_id)
            """)

            await conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_episodic_business_type
                ON episodic_memories(business_type)
            """)

            await conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_episodic_created_at
                ON episodic_memories(created_at DESC)
            """)

            await conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_episodic_embedding
                ON episodic_memories USING hnsw (embedding vector_cosine_ops)
            """)

            logger.info("✅ 情景记忆表创建完成")

    async def store(self, episode: Dict[str, Any]) -> str:
        """
        存储情景记忆

        Args:
            episode: 情景数据
                {
                    "episode_id": "EP_20241215_001",
                    "user_id": "user123",
                    "business_type": "patent",
                    "title": "发明专利申请",
                    "content": "详细内容...",
                    "entities": {...},
                    "emotions": {...},
                    "outcomes": {...},
                    "importance": 1.0,
                    "tags": ["AI", "专利"],
                    "embedding": [0.1, 0.2, ...]
                }

        Returns:
            episode_id
        """
        try:
            async with self.pool.acquire() as conn:
                # 检查是否已存在
                existing = await conn.fetchval(
                    "SELECT id FROM episodic_memories WHERE episode_id = $1",
                    episode["episode_id"]
                )

                if existing:
                    # 更新现有记录
                    await conn.execute("""
                        UPDATE episodic_memories
                        SET content = $2, entities = $3, emotions = $4,
                            outcomes = $5, importance = $6,
                            tags = $7, updated_at = CURRENT_TIMESTAMP
                        WHERE episode_id = $1
                    """,
                        episode["episode_id"],
                        episode["content"],
                        json.dumps(episode.get("entities", {})),
                        json.dumps(episode.get("emotions", {})),
                        json.dumps(episode.get("outcomes", {})),
                        episode.get("importance", 1.0),
                        episode.get("tags", [])
                    )
                else:
                    # 插入新记录
                    await conn.execute("""
                        INSERT INTO episodic_memories
                        (episode_id, user_id, business_type, title, content,
                         entities, emotions, outcomes, importance, tags)
                        VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
                    """,
                        episode["episode_id"],
                        episode["user_id"],
                        episode["business_type"],
                        episode.get("title", ""),
                        episode["content"],
                        json.dumps(episode.get("entities", {})),
                        json.dumps(episode.get("emotions", {})),
                        json.dumps(episode.get("outcomes", {})),
                        episode.get("importance", 1.0),
                        episode.get("tags", [])
                    )

                logger.info(f"✅ 情景记忆已存储: {episode['episode_id']}")
                return episode["episode_id"]

        except Exception as e:
            logger.error(f"存储情景记忆失败: {str(e)}")
            raise

    async def retrieve(self, query: Dict[str, Any], limit: int = 10) -> List[Dict[str, Any]]:
        """
        检索情景记忆

        Args:
            query: 查询条件
            {
                "user_id": "user123",        # 可选
                "business_type": "patent",    # 可选
                "tags": ["AI", "专利"],       # 可选
                "embedding": [0.1, 0.2,...],  # 可选
                "date_range": {"start": "2024-01-01", "end": "2024-12-31"}, # 可选
                "min_importance": 0.8         # 可选
            }
            limit: 返回数量

        Returns:
            检索结果
        """
        try:
            async with self.pool.acquire() as conn:
                # 构建查询条件
                conditions = []
                params = []
                param_index = 1

                # 用户ID条件
                if "user_id" in query:
                    conditions.append(f"user_id = ${param_index}")
                    params.append(query["user_id"])
                    param_index += 1

                # 业务类型条件
                if "business_type" in query:
                    conditions.append(f"business_type = ${param_index}")
                    params.append(query["business_type"])
                    param_index += 1

                # 标签条件
                if "tags" in query:
                    for tag in query["tags"]:
                        conditions.append(f"${param_index} = ANY(tags)")
                        params.append(tag)
                        param_index += 1

                # 重要性条件
                if "min_importance" in query:
                    conditions.append(f"importance >= ${param_index}")
                    params.append(query["min_importance"])
                    param_index += 1

                # 日期范围条件
                if "date_range" in query:
                    date_range = query["date_range"]
                    if "start" in date_range:
                        conditions.append(f"created_at >= ${param_index}")
                        params.append(date_range["start"])
                        param_index += 1
                    if "end" in date_range:
                        conditions.append(f"created_at <= ${param_index}")
                        params.append(date_range["end"])
                        param_index += 1

                # 构建WHERE子句
                where_clause = " AND ".join(conditions) if conditions else "1=1"

                # 向量相似度查询（如果有embedding）
                if "embedding" in query and len(query["embedding"]) == 768:
                    similarity_query = f"""
                        SELECT *,
                            (embedding <=> $1)::real as similarity
                        FROM episodic_memories
                        WHERE {where_clause}
                        ORDER BY embedding <=> $1
                        LIMIT ${param_index}
                    """
                    params = [query["embedding"]] + params + [limit]
                else:
                    similarity_query = f"""
                        SELECT *, 1.0 as similarity
                        FROM episodic_memories
                        WHERE {where_clause}
                        ORDER BY created_at DESC
                        LIMIT ${param_index}
                    """
                    params.append(limit)

                rows = await conn.fetch(similarity_query, *params)

                # 转换为字典格式
                results = []
                for row in rows:
                    result = {
                        "episode_id": row["episode_id"],
                        "user_id": row["user_id"],
                        "business_type": row["business_type"],
                        "title": row["title"],
                        "content": row["content"],
                        "entities": json.loads(row["entities"]) if row["entities"] else {},
                        "emotions": json.loads(row["emotions"]) if row["emotions"] else {},
                        "outcomes": json.loads(row["outcomes"]) if row["outcomes"] else {},
                        "importance": row["importance"],
                        "created_at": row["created_at"].isoformat(),
                        "updated_at": row["updated_at"].isoformat(),
                        "tags": row["tags"] or [],
                        "similarity": float(row["similarity"])
                    }
                    results.append(result)

                return results

        except Exception as e:
            logger.error(f"检索情景记忆失败: {str(e)}")
            return []

    async def get_episode_by_id(self, episode_id: str) -> Dict[str, Any | None]:
        """根据ID获取情景记忆"""
        try:
            async with self.pool.acquire() as conn:
                row = await conn.fetchrow(
                    "SELECT * FROM episodic_memories WHERE episode_id = $1",
                    episode_id
                )

                if row:
                    return {
                        "episode_id": row["episode_id"],
                        "user_id": row["user_id"],
                        "business_type": row["business_type"],
                        "title": row["title"],
                        "content": row["content"],
                        "entities": json.loads(row["entities"]) if row["entities"] else {},
                        "emotions": json.loads(row["emotions"]) if row["emotions"] else {},
                        "outcomes": json.loads(row["outcomes"]) if row["outcomes"] else {},
                        "importance": row["importance"],
                        "created_at": row["created_at"].isoformat(),
                        "updated_at": row["updated_at"].isoformat(),
                        "tags": row["tags"] or []
                    }
                return None

        except Exception as e:
            logger.error(f"获取情景记忆失败: {str(e)}")
            return None

    async def update_episode(self, episode_id: str, updates: Dict[str, Any]) -> bool:
        """更新情景记忆"""
        try:
            async with self.pool.acquire() as conn:
                # 构建更新语句
                update_fields = []
                params = []
                param_index = 1

                for field, value in updates.items():
                    if field in ["content", "title", "importance", "tags"]:
                        update_fields.append(f"{field} = ${param_index}")
                        params.append(value)
                        param_index += 1

                if not update_fields:
                    return False

                update_fields.append("updated_at = CURRENT_TIMESTAMP")

                params.append(episode_id)

                query = f"""
                    UPDATE episodic_memories
                    SET {', '.join(update_fields)}
                    WHERE episode_id = ${param_index}
                """

                result = await conn.execute(query, *params)
                return result == "UPDATE 1"

        except Exception as e:
            logger.error(f"更新情景记忆失败: {str(e)}")
            return False

    async def delete_episode(self, episode_id: str) -> bool:
        """删除情景记忆"""
        try:
            async with self.pool.acquire() as conn:
                result = await conn.execute(
                    "DELETE FROM episodic_memories WHERE episode_id = $1",
                    episode_id
                )
                return result == "DELETE 1"

        except Exception as e:
            logger.error(f"删除情景记忆失败: {str(e)}")
            return False

    async def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息"""
        try:
            async with self.pool.acquire() as conn:
                stats = {}

                # 总数统计
                total = await conn.fetchval("SELECT COUNT(*) FROM episodic_memories")
                stats["total_episodes"] = total

                # 按业务类型统计
                type_stats = await conn.fetch("""
                    SELECT business_type, COUNT(*) as count
                    FROM episodic_memories
                    GROUP BY business_type
                """)
                stats["by_business_type"] = {
                    row["business_type"]: row["count"] for row in type_stats
                }

                # 按用户统计（Top 10）
                user_stats = await conn.fetch("""
                    SELECT user_id, COUNT(*) as count
                    FROM episodic_memories
                    GROUP BY user_id
                    ORDER BY count DESC
                    LIMIT 10
                """)
                stats["top_users"] = [
                    {"user_id": row["user_id"], "count": row["count"]}
                    for row in user_stats
                ]

                # 最近7天统计
                recent_stats = await conn.fetchval("""
                    SELECT COUNT(*)
                    FROM episodic_memories
                    WHERE created_at >= NOW() - INTERVAL '7 days'
                """)
                stats["recent_7_days"] = recent_stats

                return stats

        except Exception as e:
            logger.error(f"获取统计信息失败: {str(e)}")
            return {}

    async def close(self):
        """关闭连接池"""
        if self.pool:
            await self.pool.close()
            logger.info("✅ 情景记忆连接池已关闭")

# 使用示例
async def main():
    """测试情景记忆"""
    memory = EpisodicMemory()
    await memory.initialize()

    # 存储示例
    episode = {
        "episode_id": "EP_20241215_001",
        "user_id": "user123",
        "business_type": "patent",
        "title": "AI图像识别专利申请",
        "content": "用户想申请基于深度学习的图像识别技术专利...",
        "entities": {"技术": "深度学习", "领域": "图像识别"},
        "emotions": {"anxiety": 0.3, "confidence": 0.7},
        "outcomes": {"success": True, "patent_id": "CN202410001234.5"},
        "importance": 0.9,
        "tags": ["AI", "专利", "图像识别"],
        "embedding": [0.1] * 768  # 示例向量
    }

    episode_id = await memory.store(episode)
    print(f"存储成功: {episode_id}")

    # 检索示例
    results = await memory.retrieve({
        "user_id": "user123",
        "business_type": "patent"
    })
    print(f"检索到 {len(results)} 条记录")

    # 获取统计
    stats = await memory.get_statistics()
    print(f"统计信息: {stats}")

    await memory.close()

# 入口点: @async_main装饰器已添加到main函数