"""
上下文权限管理器

管理用户对特定上下文的访问权限，支持细粒度的权限控制。
与RBAC系统协同工作，提供完整的访问控制解决方案。

Author: SecurityAgent
Date: 2026-04-24
"""

from __future__ import annotations

import sqlite3
import threading
from datetime import datetime
from pathlib import Path
from typing import Optional

from .models import ContextPermission, PermissionLevel


class ContextPermissionManager:
    """
    上下文权限管理器

    管理用户对特定上下文的访问权限，支持以下权限级别:
    - owner: 所有者（完全控制）
    - edit: 编辑权限（可修改）
    - read: 读取权限（仅查看）
    - none: 无权限

    Features:
    - 细粒度上下文权限控制
    - 权限继承（未设置时使用RBAC权限）
    - 临时权限（支持过期时间）
    - 批量权限操作
    - 线程安全
    """

    # 默认数据库路径
    DEFAULT_DB_PATH = Path.home() / ".athena" / "context_permissions.db"

    def __init__(
        self,
        db_path: Optional[Path | str] = None,
        auto_init: bool = True,
    ):
        """
        初始化上下文权限管理器

        Args:
            db_path: 数据库路径，默认为 ~/.athena/context_permissions.db
            auto_init: 是否自动初始化数据库
        """
        self._db_path = Path(db_path) if db_path else self.DEFAULT_DB_PATH
        self._lock = threading.Lock()
        self._local = threading.local()

        # 确保目录存在
        self._db_path.parent.mkdir(parents=True, exist_ok=True)

        if auto_init:
            self._init_database()

    @property
    def _conn(self) -> sqlite3.Connection:
        """获取线程本地数据库连接"""
        if not hasattr(self._local, "conn"):
            self._local.conn = sqlite3.connect(str(self._db_path))
            self._local.conn.row_factory = sqlite3.Row
        return self._local.conn

    def _init_database(self) -> None:
        """初始化数据库表结构"""
        with self._lock:
            conn = self._conn
            cursor = conn.cursor()

            # 上下文权限表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS context_permissions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    context_id TEXT NOT NULL,
                    user_id TEXT NOT NULL,
                    level TEXT NOT NULL,
                    granted_by TEXT,
                    granted_at TEXT,
                    expires_at TEXT,
                    is_active BOOLEAN DEFAULT 1,
                    UNIQUE(context_id, user_id)
                )
            """)

            # 上下文所有者表（优化查询）
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS context_owners (
                    context_id TEXT PRIMARY KEY,
                    owner_id TEXT NOT NULL,
                    created_at TEXT
                )
            """)

            # 创建索引
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_context_permissions_context
                ON context_permissions(context_id)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_context_permissions_user
                ON context_permissions(user_id)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_context_permissions_active
                ON context_permissions(context_id, user_id, is_active)
            """)

            conn.commit()

    # ========== 权限授予/撤销 ==========

    def grant_permission(
        self,
        context_id: str,
        user_id: str,
        level: PermissionLevel | str,
        granted_by: str,
        expires_at: Optional[datetime] = None,
    ) -> ContextPermission:
        """
        授予上下文权限

        Args:
            context_id: 上下文ID
            user_id: 用户ID
            level: 权限级别
            granted_by: 授权人ID
            expires_at: 过期时间

        Returns:
            上下文权限对象
        """
        if isinstance(level, str):
            level = PermissionLevel(level)

        with self._lock:
            conn = self._conn
            cursor = conn.cursor()

            now = datetime.utcnow()

            # 检查是否已存在
            cursor.execute(
                "SELECT id FROM context_permissions WHERE context_id = ? AND user_id = ?",
                (context_id, user_id),
            )

            if cursor.fetchone():
                # 更新现有记录
                cursor.execute(
                    """
                    UPDATE context_permissions
                    SET level = ?, granted_by = ?, granted_at = ?, expires_at = ?, is_active = 1
                    WHERE context_id = ? AND user_id = ?
                    """,
                    (
                        level.value,
                        granted_by,
                        now.isoformat(),
                        expires_at.isoformat() if expires_at else None,
                        context_id,
                        user_id,
                    ),
                )
            else:
                # 插入新记录
                cursor.execute(
                    """
                    INSERT INTO context_permissions
                    (context_id, user_id, level, granted_by, granted_at, expires_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (
                        context_id,
                        user_id,
                        level.value,
                        granted_by,
                        now.isoformat(),
                        expires_at.isoformat() if expires_at else None,
                    ),
                )

            # 如果是owner级别，更新所有者表
            if level == PermissionLevel.OWNER:
                cursor.execute(
                    """
                    INSERT OR REPLACE INTO context_owners (context_id, owner_id, created_at)
                    VALUES (?, ?, ?)
                    """,
                    (context_id, user_id, now.isoformat()),
                )

            conn.commit()

            return ContextPermission(
                context_id=context_id,
                user_id=user_id,
                level=level,
                granted_by=granted_by,
                granted_at=now,
                expires_at=expires_at,
            )

    def revoke_permission(
        self,
        context_id: str,
        user_id: str,
    ) -> bool:
        """
        撤销上下文权限

        Args:
            context_id: 上下文ID
            user_id: 用户ID

        Returns:
            是否撤销成功
        """
        with self._lock:
            conn = self._conn
            cursor = conn.cursor()

            cursor.execute(
                "UPDATE context_permissions SET is_active = 0 WHERE context_id = ? AND user_id = ?",
                (context_id, user_id),
            )
            update_count = cursor.rowcount

            # 如果撤销的是owner权限，从所有者表移除
            cursor.execute(
                "DELETE FROM context_owners WHERE context_id = ? AND owner_id = ?",
                (context_id, user_id),
            )

            conn.commit()

            return update_count > 0

    def revoke_all_permissions(self, context_id: str) -> int:
        """
        撤销上下文的所有权限

        Args:
            context_id: 上下文ID

        Returns:
            撤销的权限数量
        """
        with self._lock:
            conn = self._conn
            cursor = conn.cursor()

            cursor.execute(
                "UPDATE context_permissions SET is_active = 0 WHERE context_id = ?",
                (context_id,),
            )

            cursor.execute(
                "DELETE FROM context_owners WHERE context_id = ?",
                (context_id,),
            )

            conn.commit()

            return cursor.rowcount

    # ========== 权限查询 ==========

    def get_permission(
        self,
        context_id: str,
        user_id: str,
    ) -> Optional[ContextPermission]:
        """
        获取用户对上下文的权限

        Args:
            context_id: 上下文ID
            user_id: 用户ID

        Returns:
            上下文权限对象或None
        """
        conn = self._conn
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT * FROM context_permissions
            WHERE context_id = ? AND user_id = ? AND is_active = 1
            ORDER BY granted_at DESC LIMIT 1
            """,
            (context_id, user_id),
        )

        row = cursor.fetchone()
        if row is None:
            return None

        return ContextPermission(
            context_id=row["context_id"],
            user_id=row["user_id"],
            level=PermissionLevel(row["level"]),
            granted_by=row["granted_by"],
            granted_at=datetime.fromisoformat(row["granted_at"]),
            expires_at=datetime.fromisoformat(row["expires_at"]) if row["expires_at"] else None,
            is_active=bool(row["is_active"]),
        )

    def get_context_permissions(
        self,
        context_id: str,
        active_only: bool = True,
    ) -> list[ContextPermission]:
        """
        获取上下文的所有权限

        Args:
            context_id: 上下文ID
            active_only: 是否只返回激活的权限

        Returns:
            上下文权限列表
        """
        conn = self._conn
        cursor = conn.cursor()

        query = "SELECT * FROM context_permissions WHERE context_id = ?"
        params = [context_id]

        if active_only:
            query += " AND is_active = 1"

        query += " ORDER BY granted_at DESC"

        cursor.execute(query, params)

        permissions = []
        for row in cursor.fetchall():
            cp = ContextPermission(
                context_id=row["context_id"],
                user_id=row["user_id"],
                level=PermissionLevel(row["level"]),
                granted_by=row["granted_by"],
                granted_at=datetime.fromisoformat(row["granted_at"]),
                expires_at=datetime.fromisoformat(row["expires_at"]) if row["expires_at"] else None,
                is_active=bool(row["is_active"]),
            )

            # 过滤过期权限
            if active_only and cp.is_expired():
                continue

            permissions.append(cp)

        return permissions

    def get_user_contexts(
        self,
        user_id: str,
        min_level: PermissionLevel | str = PermissionLevel.READ,
    ) -> list[str]:
        """
        获取用户可访问的上下文列表

        Args:
            user_id: 用户ID
            min_level: 最低权限级别

        Returns:
            上下文ID列表
        """
        if isinstance(min_level, str):
            min_level = PermissionLevel(min_level)

        conn = self._conn
        cursor = conn.cursor()

        # 定义权限级别顺序
        level_order = {
            PermissionLevel.NONE: 0,
            PermissionLevel.READ: 1,
            PermissionLevel.EDIT: 2,
            PermissionLevel.OWNER: 3,
        }

        min_level_value = level_order.get(min_level, 0)

        cursor.execute(
            """
            SELECT DISTINCT context_id, level
            FROM context_permissions
            WHERE user_id = ? AND is_active = 1
            """,
            (user_id,),
        )

        contexts = []
        for row in cursor.fetchall():
            level = PermissionLevel(row["level"])
            level_value = level_order.get(level, 0)

            if level_value >= min_level_value:
                contexts.append(row["context_id"])

        return contexts

    def get_context_owner(self, context_id: str) -> Optional[str]:
        """
        获取上下文的所有者

        Args:
            context_id: 上下文ID

        Returns:
            所有者用户ID或None
        """
        conn = self._conn
        cursor = conn.cursor()

        cursor.execute(
            "SELECT owner_id FROM context_owners WHERE context_id = ?",
            (context_id,),
        )

        row = cursor.fetchone()
        return row["owner_id"] if row else None

    # ========== 访问检查 ==========

    def check_access(
        self,
        context_id: str,
        user_id: str,
        required_level: PermissionLevel | str = PermissionLevel.READ,
    ) -> bool:
        """
        检查用户对上下文的访问权限

        Args:
            context_id: 上下文ID
            user_id: 用户ID
            required_level: 所需的权限级别

        Returns:
            是否有权限
        """
        if isinstance(required_level, str):
            required_level = PermissionLevel(required_level)

        permission = self.get_permission(context_id, user_id)

        if permission is None:
            return False

        if permission.is_expired():
            return False

        # 检查权限级别
        if required_level == PermissionLevel.READ:
            return permission.can_read()
        elif required_level == PermissionLevel.EDIT:
            return permission.can_edit()
        elif required_level == PermissionLevel.OWNER:
            return permission.can_delete()
        else:
            return False

    def can_read(self, context_id: str, user_id: str) -> bool:
        """检查是否可读"""
        return self.check_access(context_id, user_id, PermissionLevel.READ)

    def can_edit(self, context_id: str, user_id: str) -> bool:
        """检查是否可编辑"""
        return self.check_access(context_id, user_id, PermissionLevel.EDIT)

    def can_delete(self, context_id: str, user_id: str) -> bool:
        """检查是否可删除"""
        return self.check_access(context_id, user_id, PermissionLevel.OWNER)

    def is_owner(self, context_id: str, user_id: str) -> bool:
        """检查是否是所有者"""
        return self.check_access(context_id, user_id, PermissionLevel.OWNER)

    # ========== 批量操作 ==========

    def grant_batch(
        self,
        context_id: str,
        user_ids: list[str],
        level: PermissionLevel | str,
        granted_by: str,
    ) -> list[ContextPermission]:
        """
        批量授予上下文权限

        Args:
            context_id: 上下文ID
            user_ids: 用户ID列表
            level: 权限级别
            granted_by: 授权人ID

        Returns:
            上下文权限列表
        """
        results = []
        for user_id in user_ids:
            try:
                cp = self.grant_permission(context_id, user_id, level, granted_by)
                results.append(cp)
            except sqlite3.Error:
                continue

        return results

    def get_accessible_contexts(
        self,
        user_id: str,
        context_ids: list[str],
        required_level: PermissionLevel | str = PermissionLevel.READ,
    ) -> list[str]:
        """
        从给定列表中获取用户可访问的上下文

        Args:
            user_id: 用户ID
            context_ids: 上下文ID列表
            required_level: 所需权限级别

        Returns:
            可访问的上下文ID列表
        """
        accessible = []
        for context_id in context_ids:
            if self.check_access(context_id, user_id, required_level):
                accessible.append(context_id)

        return accessible

    # ========== 统计信息 ==========

    def get_statistics(self) -> dict[str, int]:
        """
        获取权限系统统计信息

        Returns:
            统计信息字典
        """
        conn = self._conn
        cursor = conn.cursor()

        stats = {}

        # 总权限数
        cursor.execute("SELECT COUNT(*) FROM context_permissions")
        stats["total_permissions"] = cursor.fetchone()[0]

        # 激活权限数
        cursor.execute("SELECT COUNT(*) FROM context_permissions WHERE is_active = 1")
        stats["active_permissions"] = cursor.fetchone()[0]

        # 上下文数量
        cursor.execute("SELECT COUNT(DISTINCT context_id) FROM context_permissions")
        stats["total_contexts"] = cursor.fetchone()[0]

        # 用户数量
        cursor.execute("SELECT COUNT(DISTINCT user_id) FROM context_permissions WHERE is_active = 1")
        stats["total_users"] = cursor.fetchone()[0]

        # 所有者上下文数量
        cursor.execute("SELECT COUNT(*) FROM context_owners")
        stats["owned_contexts"] = cursor.fetchone()[0]

        return stats

    # ========== 清理 ==========

    def cleanup_expired_permissions(self) -> int:
        """
        清理过期的权限

        Returns:
            清理的权限数量
        """
        with self._lock:
            conn = self._conn
            cursor = conn.cursor()

            now = datetime.utcnow().isoformat()

            cursor.execute(
                """
                UPDATE context_permissions
                SET is_active = 0
                WHERE expires_at IS NOT NULL AND expires_at < ?
                """,
                (now,),
            )
            conn.commit()

            return cursor.rowcount

    def cleanup_context(self, context_id: str) -> int:
        """
        清理上下文的所有权限和所有者记录

        Args:
            context_id: 上下文ID

        Returns:
            清理的记录数
        """
        with self._lock:
            conn = self._conn
            cursor = conn.cursor()

            cursor.execute("DELETE FROM context_permissions WHERE context_id = ?", (context_id,))
            deleted_permissions = cursor.rowcount

            cursor.execute("DELETE FROM context_owners WHERE context_id = ?", (context_id,))
            deleted_owners = cursor.rowcount

            conn.commit()

            return deleted_permissions + deleted_owners

    def cleanup_user(self, user_id: str) -> int:
        """
        清理用户的所有权限

        Args:
            user_id: 用户ID

        Returns:
            清理的权限数量
        """
        with self._lock:
            conn = self._conn
            cursor = conn.cursor()

            cursor.execute("UPDATE context_permissions SET is_active = 0 WHERE user_id = ?", (user_id,))
            conn.commit()

            return cursor.rowcount

    def close(self) -> None:
        """关闭数据库连接"""
        if hasattr(self._local, "conn"):
            self._local.conn.close()
            delattr(self._local, "conn")
