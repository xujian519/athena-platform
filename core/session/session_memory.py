"""
会话记忆管理器

为小诺网关提供轻量级的会话记忆持久化功能。

特点:
- 基于SQLite的本地存储
- 支持会话历史记录
- 支持会话上下文保持
- 自动过期清理
"""

import json
import logging
import sqlite3
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class SessionMessage:
    """会话消息"""

    role: str  # user/assistant/system
    content: str  # 消息内容
    timestamp: float  # 时间戳
    intent: str | None = None  # 意图
    capability: str | None = None  # 使用的能力
    confidence: float | None = None  # 置信度
    metadata: dict[str, Any] = field(default_factory=dict)  # 其他元数据


@dataclass
class SessionContext:
    """会话上下文"""

    session_id: str  # 会话ID
    user_id: str | None = None  # 用户ID
    created_at: float = field(default_factory=time.time)
    last_active: float = field(default_factory=time.time)
    message_count: int = 0
    total_tokens: int = 0
    preferences: dict[str, Any] = field(default_factory=dict)
    context_data: dict[str, Any] = field(default_factory=dict)


class SessionMemoryManager:
    """
    会话记忆管理器

    提供轻量级的会话记忆持久化功能。
    """

    def __init__(
        self,
        db_path: str | None = None,
        session_timeout: int = 3600,  # 会话超时时间(秒)
        max_messages_per_session: int = 100,  # 每个会话最大消息数
    ):
        """
        初始化会话记忆管理器

        Args:
            db_path: 数据库文件路径
            session_timeout: 会话超时时间(秒)
            max_messages_per_session: 每个会话最大消息数
        """
        if db_path is None:
            # 默认路径
            project_root = Path(__file__).parent.parent.parent
            db_path = project_root / "data" / "sessions" / "session_memory.db"

        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        self.session_timeout = session_timeout
        self.max_messages_per_session = max_messages_per_session

        # 初始化数据库
        self._init_database()

        logger.info("✅ 会话记忆管理器初始化完成")
        logger.info(f"   数据库: {self.db_path}")
        logger.info(f"   会话超时: {session_timeout}秒")
        logger.info(f"   最大消息数: {max_messages_per_session}")

    def _init_database(self) -> Any:
        """初始化数据库表"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # 创建会话上下文表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS session_contexts (
                    session_id TEXT PRIMARY KEY,
                    user_id TEXT,
                    created_at REAL,
                    last_active REAL,
                    message_count INTEGER DEFAULT 0,
                    total_tokens INTEGER DEFAULT 0,
                    preferences TEXT,
                    context_data TEXT
                )
            """)

            # 创建会话消息表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS session_messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    timestamp REAL NOT NULL,
                    intent TEXT,
                    capability TEXT,
                    confidence REAL,
                    metadata TEXT,
                    FOREIGN KEY (session_id) REFERENCES session_contexts(session_id)
                )
            """)

            # 创建索引
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_session_messages_session_id
                ON session_messages(session_id)
            """)

            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_session_messages_timestamp
                ON session_messages(timestamp DESC)
            """)

            conn.commit()

        logger.info("✅ 数据库表初始化完成")

    def create_session(self, session_id: str, user_id: str | None = None) -> SessionContext:
        """
        创建新会话

        Args:
            session_id: 会话ID
            user_id: 用户ID

        Returns:
            SessionContext: 会话上下文
        """
        context = SessionContext(session_id=session_id, user_id=user_id)

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            cursor.execute(
                """
                INSERT INTO session_contexts
                (session_id, user_id, created_at, last_active, preferences, context_data)
                VALUES (?, ?, ?, ?, ?, ?)
            """,
                (
                    session_id,
                    user_id,
                    context.created_at,
                    context.last_active,
                    json.dumps(context.preferences),
                    json.dumps(context.context_data),
                ),
            )

            conn.commit()

        logger.info(f"📝 创建会话: {session_id}")
        return context

    def get_session(self, session_id: str) -> SessionContext | None:
        """
        获取会话上下文

        Args:
            session_id: 会话ID

        Returns:
            SessionContext or None
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            cursor.execute(
                """
                SELECT session_id, user_id, created_at, last_active,
                       message_count, total_tokens, preferences, context_data
                FROM session_contexts
                WHERE session_id = ?
            """,
                (session_id,),
            )

            row = cursor.fetchone()

            if row is None:
                return None

            return SessionContext(
                session_id=row[0],
                user_id=row[1],
                created_at=row[2],
                last_active=row[3],
                message_count=row[4],
                total_tokens=row[5],
                preferences=json.loads(row[6]) if row[6] else {},
                context_data=json.loads(row[7]) if row[7] else {},
            )

    def add_message(
        self,
        session_id: str,
        role: str,
        content: str,
        intent: str | None = None,
        capability: str | None = None,
        confidence: float | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> SessionMessage:
        """
        添加消息到会话

        Args:
            session_id: 会话ID
            role: 角色 (user/assistant/system)
            content: 消息内容
            intent: 意图
            capability: 使用的能力
            confidence: 置信度
            metadata: 元数据

        Returns:
            SessionMessage: 消息对象
        """
        message = SessionMessage(
            role=role,
            content=content,
            timestamp=time.time(),
            intent=intent,
            capability=capability,
            confidence=confidence,
            metadata=metadata or {},
        )

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # 插入消息
            cursor.execute(
                """
                INSERT INTO session_messages
                (session_id, role, content, timestamp, intent, capability, confidence, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    session_id,
                    role,
                    content,
                    message.timestamp,
                    intent,
                    capability,
                    confidence,
                    json.dumps(metadata or {}),
                ),
            )

            # 更新会话活跃时间
            cursor.execute(
                """
                UPDATE session_contexts
                SET last_active = ?, message_count = message_count + 1
                WHERE session_id = ?
            """,
                (message.timestamp, session_id),
            )

            conn.commit()

        return message

    def get_session_messages(
        self, session_id: str, limit: int | None = None
    ) -> list[SessionMessage]:
        """
        获取会话消息

        Args:
            session_id: 会话ID
            limit: 最大消息数量

        Returns:
            list[SessionMessage]: 消息列表
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            query = """
                SELECT role, content, timestamp, intent, capability, confidence, metadata
                FROM session_messages
                WHERE session_id = ?
                ORDER BY timestamp ASC
            """

            if limit:
                query += f" LIMIT {limit}"

            cursor.execute(query, (session_id,))

            messages = []
            for row in cursor.fetchall():
                messages.append(
                    SessionMessage(
                        role=row[0],
                        content=row[1],
                        timestamp=row[2],
                        intent=row[3],
                        capability=row[4],
                        confidence=row[5],
                        metadata=json.loads(row[6]) if row[6] else {},
                    )
                )

            return messages

    def get_recent_messages(self, session_id: str, count: int = 10) -> list[SessionMessage]:
        """
        获取最近的几条消息

        Args:
            session_id: 会话ID
            count: 消息数量

        Returns:
            list[SessionMessage]: 消息列表
        """
        messages = self.get_session_messages(session_id)
        return messages[-count:] if messages else []

    def update_session_context(
        self,
        session_id: str,
        preferences: dict[str, Any] | None = None,
        context_data: dict[str, Any] | None = None,
    ) -> bool:
        """
        更新会话上下文

        Args:
            session_id: 会话ID
            preferences: 偏好设置
            context_data: 上下文数据

        Returns:
            是否成功
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            updates = []
            params = []

            if preferences:
                updates.append("preferences = ?")
                params.append(json.dumps(preferences))

            if context_data:
                updates.append("context_data = ?")
                params.append(json.dumps(context_data))

            if not updates:
                return False

            params.append(session_id)

            # 安全说明:updates列表只包含硬编码的列名(preferences, context_data)
            # 不包含任何用户输入,因此字符串拼接是安全的
            cursor.execute(
                f"""
                UPDATE session_contexts
                SET {', '.join(updates)}
                WHERE session_id = ?
            """,
                params,
            )

            conn.commit()

            return cursor.rowcount > 0

    def cleanup_expired_sessions(self) -> int:
        """
        清理过期的会话

        Returns:
            清理的会话数量
        """
        expiration_time = time.time() - self.session_timeout

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # 获取过期会话ID
            cursor.execute(
                """
                SELECT session_id FROM session_contexts
                WHERE last_active < ?
            """,
                (expiration_time,),
            )

            expired_sessions = [row[0] for row in cursor.fetchall()]

            if not expired_sessions:
                return 0

            # 删除过期会话的消息
            # 安全说明:使用占位符生成动态IN子句,参数化查询防止SQL注入
            placeholders = ",".join(["?" for _ in expired_sessions])
            cursor.execute(
                f"""
                DELETE FROM session_messages
                WHERE session_id IN ({placeholders})
            """,
                expired_sessions,
            )

            # 删除过期会话
            cursor.execute(
                """
                DELETE FROM session_contexts
                WHERE session_id IN ({})
            """.format(",".join(["?" for _ in expired_sessions])),
                expired_sessions,
            )

            conn.commit()

            logger.info(f"🧹 清理了 {len(expired_sessions)} 个过期会话")

            return len(expired_sessions)

    def get_session_stats(self, session_id: str) -> dict[str, Any]:
        """
        获取会话统计信息

        Args:
            session_id: 会话ID

        Returns:
            统计信息字典
        """
        context = self.get_session(session_id)
        if not context:
            return {}

        messages = self.get_session_messages(session_id)

        # 统计意图分布
        intent_counts = {}
        capability_counts = {}

        for msg in messages:
            if msg.intent:
                intent_counts[msg.intent] = intent_counts.get(msg.intent, 0) + 1
            if msg.capability:
                capability_counts[msg.capability] = capability_counts.get(msg.capability, 0) + 1

        return {
            "session_id": session_id,
            "created_at": context.created_at,
            "last_active": context.last_active,
            "message_count": context.message_count,
            "duration": context.last_active - context.created_at,
            "intent_distribution": intent_counts,
            "capability_distribution": capability_counts,
            "is_expired": (time.time() - context.last_active) > self.session_timeout,
        }


# 单例模式
_session_memory_manager = None


def get_session_memory_manager() -> SessionMemoryManager:
    """获取会话记忆管理器单例"""
    global _session_memory_manager
    if _session_memory_manager is None:
        _session_memory_manager = SessionMemoryManager()
    return _session_memory_manager
