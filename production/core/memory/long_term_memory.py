from __future__ import annotations
"""
长记忆系统

实现跨会话的用户偏好和历史记忆功能
"""

import json
import logging
import sqlite3
import time
from dataclasses import asdict, dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class MemoryType(Enum):
    """记忆类型"""

    PREFERENCE = "preference"
    FREQUENT_QUERY = "frequent_query"
    EXPERTISE = "expertise"
    INTERACTION = "interaction"
    ENTITY = "entity"


@dataclass
class MemoryItem:
    """记忆项"""

    memory_id: str
    user_id: str
    memory_type: MemoryType
    content: dict[str, Any]
    importance: float = 0.5
    access_count: int = 0
    last_accessed: float = field(default_factory=time.time)
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)
    expires_at: float | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "memory_id": self.memory_id,
            "user_id": self.user_id,
            "memory_type": self.memory_type.value,
            "content": self.content,
            "importance": self.importance,
            "access_count": self.access_count,
            "last_accessed": self.last_accessed,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "expires_at": self.expires_at,
        }


@dataclass
class UserPreference:
    """用户偏好"""

    user_id: str
    response_detail: str = "medium"
    technical_depth: str = "medium"
    language_style: str = "professional"
    output_format: str = "text"
    preferred_capabilities: list[str] = field(default_factory=list)
    avoided_topics: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class LongTermMemoryManager:
    """长记忆管理器"""

    def __init__(
        self,
        db_path: str | None = None,
        memory_ttl: int = 2592000,
        max_memories_per_user: int = 1000,
    ):
        if db_path is None:
            project_root = Path(__file__).parent.parent.parent
            db_path = project_root / "data" / "memory" / "long_term_memory.db"

        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        self.memory_ttl = memory_ttl
        self.max_memories_per_user = max_memories_per_user

        self._init_database()

        logger.info("✅ 长记忆管理器初始化完成")

    def _init_database(self) -> Any:
        """初始化数据库表"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS long_term_memories (
                    memory_id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    memory_type TEXT NOT NULL,
                    content TEXT NOT NULL,
                    importance REAL DEFAULT 0.5,
                    access_count INTEGER DEFAULT 0,
                    last_accessed REAL,
                    created_at REAL,
                    updated_at REAL,
                    expires_at REAL
                )
            """)

            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_user_id
                ON long_term_memories(user_id)
            """)

            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_memory_type
                ON long_term_memories(memory_type)
            """)

            conn.commit()

    def store_preference(self, user_id: str, preference: UserPreference) -> str:
        """存储用户偏好"""
        memory_id = f"pref_{user_id}_{int(time.time())}"

        memory = MemoryItem(
            memory_id=memory_id,
            user_id=user_id,
            memory_type=MemoryType.PREFERENCE,
            content=preference.to_dict(),
            importance=1.0,
            expires_at=None,
        )

        self._store_memory(memory)
        logger.info(f"💾 存储用户偏好: {user_id}")

        return memory_id

    def get_preference(self, user_id: str) -> UserPreference | None:
        """获取用户偏好"""
        memories = self._retrieve_memories(
            user_id=user_id, memory_type=MemoryType.PREFERENCE, limit=1
        )

        if memories:
            self._increment_access(memories[0].memory_id)
            return UserPreference(**memories[0].content)

        return None

    def record_query(
        self, user_id: str, query: str, intent: str, response: str, entities: dict[str, Any]
    ) -> str:
        """记录查询历史"""
        # 使用纳秒级时间戳+随机数确保唯一性
        import random

        memory_id = f"query_{user_id}_{time.time_ns()}_{random.randint(1000, 9999)}"

        memory = MemoryItem(
            memory_id=memory_id,
            user_id=user_id,
            memory_type=MemoryType.FREQUENT_QUERY,
            content={
                "query": query,
                "intent": intent,
                "response": response[:500],
                "entities": entities,
            },
            importance=0.3,
            expires_at=time.time() + self.memory_ttl,
        )

        self._store_memory(memory)
        return memory_id

    def get_frequent_queries(self, user_id: str, limit: int = 10) -> list[dict[str, Any]]:
        """获取常用查询"""
        memories = self._retrieve_memories(
            user_id=user_id, memory_type=MemoryType.FREQUENT_QUERY, limit=limit * 2
        )

        memories.sort(key=lambda m: m.access_count, reverse=True)

        return [
            {
                "query": m.content.get("query", ""),
                "intent": m.content.get("intent", ""),
                "count": m.access_count,
                "last_used": m.last_accessed,
            }
            for m in memories[:limit]
        ]

    def identify_expertise(self, user_id: str) -> list[str]:
        """识别用户的专业领域"""
        memories = self._retrieve_memories(
            user_id=user_id, memory_type=MemoryType.FREQUENT_QUERY, limit=500
        )

        intent_counts = {}
        for memory in memories:
            intent = memory.content.get("intent", "")
            if intent:
                intent_counts[intent] = intent_counts.get(intent, 0) + 1

        expertise_domains = [intent for intent, count in intent_counts.items() if count >= 5]

        return expertise_domains

    def retrieve_relevant_memories(
        self, user_id: str, current_query: str, current_intent: str, limit: int = 5
    ) -> list[MemoryItem]:
        """检索相关记忆"""
        all_memories = self._retrieve_memories(
            user_id=user_id, memory_type=None, limit=self.max_memories_per_user
        )

        scored_memories = []
        for memory in all_memories:
            score = self._calculate_relevance(memory, current_query, current_intent)
            scored_memories.append((memory, score))

        scored_memories.sort(key=lambda x: x[1], reverse=True)

        relevant_memories = [m for m, s in scored_memories[:limit]]

        for memory in relevant_memories:
            self._increment_access(memory.memory_id)

        return relevant_memories

    def cleanup_expired_memories(self) -> int:
        """清理过期记忆"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                current_time = time.time()

                cursor.execute(
                    """
                    DELETE FROM long_term_memories
                    WHERE expires_at IS NOT NULL AND expires_at < ?
                """,
                    (current_time,),
                )

                deleted_count = cursor.rowcount
                conn.commit()

                if deleted_count > 0:
                    logger.info(f"🧹 清理过期记忆: {deleted_count}条")

                return deleted_count

        except Exception as e:
            logger.error(f"操作失败: {e}", exc_info=True)
            raise

    def get_memory_summary(self, user_id: str) -> dict[str, Any]:
        """获取用户记忆摘要"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            cursor.execute(
                """
                SELECT memory_type, COUNT(*) as count
                FROM long_term_memories
                WHERE user_id = ? AND (expires_at IS NULL OR expires_at > ?)
                GROUP BY memory_type
            """,
                (user_id, time.time()),
            )

            type_counts = {row[0]: row[1] for row in cursor.fetchall()}

        preference = self.get_preference(user_id)
        expertise = self.identify_expertise(user_id)
        frequent_queries = self.get_frequent_queries(user_id, limit=5)

        return {
            "user_id": user_id,
            "memory_counts": type_counts,
            "preference": preference.to_dict() if preference else None,
            "expertise_domains": expertise,
            "frequent_queries": frequent_queries,
            "total_memories": sum(type_counts.values()),
        }

    def _store_memory(self, memory: MemoryItem) -> Any:
        """存储记忆"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            cursor.execute(
                """
                INSERT OR REPLACE INTO long_term_memories
                (memory_id, user_id, memory_type, content, importance,
                 access_count, last_accessed, created_at, updated_at, expires_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    memory.memory_id,
                    memory.user_id,
                    memory.memory_type.value,
                    json.dumps(memory.content, ensure_ascii=False),
                    memory.importance,
                    memory.access_count,
                    memory.last_accessed,
                    memory.created_at,
                    memory.updated_at,
                    memory.expires_at,
                ),
            )

            conn.commit()

    def _retrieve_memories(
        self, user_id: str, memory_type: MemoryType | None = None, limit: int = 100
    ) -> list[MemoryItem]:
        """检索记忆"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            current_time = time.time()

            if memory_type:
                cursor.execute(
                    """
                    SELECT * FROM long_term_memories
                    WHERE user_id = ? AND memory_type = ?
                    AND (expires_at IS NULL OR expires_at > ?)
                    ORDER BY updated_at DESC
                    LIMIT ?
                """,
                    (user_id, memory_type.value, current_time, limit),
                )
            else:
                cursor.execute(
                    """
                    SELECT * FROM long_term_memories
                    WHERE user_id = ?
                    AND (expires_at IS NULL OR expires_at > ?)
                    ORDER BY updated_at DESC
                    LIMIT ?
                """,
                    (user_id, current_time, limit),
                )

            rows = cursor.fetchall()

            memories = []
            for row in rows:
                memories.append(
                    MemoryItem(
                        memory_id=row[0],
                        user_id=row[1],
                        memory_type=MemoryType(row[2]),
                        content=json.loads(row[3]),
                        importance=row[4],
                        access_count=row[5],
                        last_accessed=row[6],
                        created_at=row[7],
                        updated_at=row[8],
                        expires_at=row[9],
                    )
                )

            return memories

    def _increment_access(self, memory_id: str) -> Any:
        """增加访问计数"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            cursor.execute(
                """
                UPDATE long_term_memories
                SET access_count = access_count + 1, last_accessed = ?
                WHERE memory_id = ?
            """,
                (time.time(), memory_id),
            )

            conn.commit()

    def _calculate_relevance(
        self, memory: MemoryItem, current_query: str, current_intent: str
    ) -> float:
        """计算记忆相关性"""
        score = 0.0

        if memory.content.get("intent") == current_intent:
            score += 0.4

        score += memory.importance * 0.3

        time_diff = time.time() - memory.updated_at
        time_score = max(0, 1 - time_diff / (30 * 24 * 3600))
        score += time_score * 0.3

        return score


# 单例
_long_term_memory_manager: LongTermMemoryManager | None = None


def get_long_term_memory_manager() -> LongTermMemoryManager:
    """获取长记忆管理器单例"""
    global _long_term_memory_manager
    if _long_term_memory_manager is None:
        _long_term_memory_manager = LongTermMemoryManager()
    return _long_term_memory_manager
