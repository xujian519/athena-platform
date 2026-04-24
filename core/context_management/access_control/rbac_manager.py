"""
RBAC权限管理器

实现基于角色的访问控制（RBAC）系统，提供角色管理、
权限分配和权限检查功能。

Author: SecurityAgent
Date: 2026-04-24
"""

from __future__ import annotations

import asyncio
import sqlite3
import threading
from datetime import datetime
from pathlib import Path
from typing import Optional

from .models import Permission, Role, UserRole, SystemRoles


class RBACManager:
    """
    RBAC权限管理器

    管理系统中的角色、权限和用户角色关联。
    使用SQLite持久化存储，支持异步操作。

    Features:
    - 角色CRUD操作
    - 权限分配与撤销
    - 用户角色分配
    - 权限检查（支持通配符）
    - 线程安全
    """

    # 默认数据库路径
    DEFAULT_DB_PATH = Path.home() / ".athena" / "access_control.db"

    def __init__(
        self,
        db_path: Optional[Path | str] = None,
        auto_init: bool = True,
    ):
        """
        初始化RBAC管理器

        Args:
            db_path: 数据库路径，默认为 ~/.athena/access_control.db
            auto_init: 是否自动初始化数据库和系统角色
        """
        self._db_path = Path(db_path) if db_path else self.DEFAULT_DB_PATH
        self._lock = threading.Lock()
        self._local = threading.local()

        # 确保目录存在
        self._db_path.parent.mkdir(parents=True, exist_ok=True)

        if auto_init:
            self._init_database()
            self._init_system_roles()

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

            # 角色表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS roles (
                    name TEXT PRIMARY KEY,
                    description TEXT,
                    is_system_role BOOLEAN DEFAULT 0,
                    priority INTEGER DEFAULT 0,
                    created_at TEXT,
                    UNIQUE(name)
                )
            """)

            # 权限表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS permissions (
                    role_name TEXT,
                    permission TEXT,
                    FOREIGN KEY (role_name) REFERENCES roles(name) ON DELETE CASCADE,
                    PRIMARY KEY (role_name, permission)
                )
            """)

            # 用户角色关联表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS user_roles (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT,
                    role_name TEXT,
                    granted_by TEXT,
                    granted_at TEXT,
                    expires_at TEXT,
                    is_active BOOLEAN DEFAULT 1,
                    FOREIGN KEY (role_name) REFERENCES roles(name) ON DELETE CASCADE,
                    UNIQUE(user_id, role_name)
                )
            """)

            # 创建索引
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_user_roles_user
                ON user_roles(user_id)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_user_roles_active
                ON user_roles(user_id, is_active)
            """)

            conn.commit()

    def _init_system_roles(self) -> None:
        """初始化系统预定义角色"""
        for role in SystemRoles.all():
            existing = self.get_role(role.name)
            if existing is None:
                self.create_role(role)
            else:
                # 更新系统角色权限
                self._update_role_permissions(role.name, role.permissions)

    # ========== 角色管理 ==========

    def create_role(
        self,
        role: Role | str,
        description: str = "",
        permissions: Optional[set[str]] = None,
    ) -> Role:
        """
        创建角色

        Args:
            role: 角色对象或角色名称
            description: 角色描述
            permissions: 权限集合

        Returns:
            创建的角色

        Raises:
            ValueError: 角色已存在
        """
        if isinstance(role, str):
            role = Role(
                name=role,
                description=description,
                permissions=permissions or set(),
            )

        with self._lock:
            conn = self._conn
            cursor = conn.cursor()

            try:
                cursor.execute(
                    """
                    INSERT INTO roles (name, description, is_system_role, priority, created_at)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (
                        role.name,
                        role.description,
                        role.is_system_role,
                        role.priority,
                        role.created_at.isoformat(),
                    ),
                )

                # 添加权限
                for perm in role.permissions:
                    cursor.execute(
                        "INSERT INTO permissions (role_name, permission) VALUES (?, ?)",
                        (role.name, perm),
                    )

                conn.commit()
                return role

            except sqlite3.IntegrityError:
                raise ValueError(f"角色已存在: {role.name}")

    def get_role(self, name: str) -> Optional[Role]:
        """
        获取角色

        Args:
            name: 角色名称

        Returns:
            角色对象或None
        """
        conn = self._conn
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM roles WHERE name = ?", (name,))
        row = cursor.fetchone()

        if row is None:
            return None

        # 获取权限
        cursor.execute("SELECT permission FROM permissions WHERE role_name = ?", (name,))
        permissions = {row[0] for row in cursor.fetchall()}

        return Role(
            name=row["name"],
            description=row["description"],
            permissions=permissions,
            is_system_role=bool(row["is_system_role"]),
            priority=row["priority"],
            created_at=datetime.fromisoformat(row["created_at"]),
        )

    def list_roles(self) -> list[Role]:
        """
        列出所有角色

        Returns:
            角色列表
        """
        conn = self._conn
        cursor = conn.cursor()

        cursor.execute("SELECT name FROM roles ORDER BY priority DESC, name ASC")
        roles = []

        for row in cursor.fetchall():
            role = self.get_role(row["name"])
            if role:
                roles.append(role)

        return roles

    def delete_role(self, name: str) -> bool:
        """
        删除角色

        Args:
            name: 角色名称

        Returns:
            是否删除成功

        Note:
            系统角色不能删除
        """
        role = self.get_role(name)
        if role is None:
            return False

        if role.is_system_role:
            raise ValueError(f"不能删除系统角色: {name}")

        with self._lock:
            conn = self._conn
            cursor = conn.cursor()

            cursor.execute("DELETE FROM roles WHERE name = ?", (name,))
            conn.commit()

            return cursor.rowcount > 0

    def _update_role_permissions(self, role_name: str, permissions: set[str]) -> None:
        """更新角色权限"""
        with self._lock:
            conn = self._conn
            cursor = conn.cursor()

            # 删除旧权限
            cursor.execute("DELETE FROM permissions WHERE role_name = ?", (role_name,))

            # 添加新权限
            for perm in permissions:
                cursor.execute(
                    "INSERT INTO permissions (role_name, permission) VALUES (?, ?)",
                    (role_name, perm),
                )

            conn.commit()

    # ========== 权限管理 ==========

    def grant_permission(self, role_name: str, permission: str) -> bool:
        """
        为角色授予权限

        Args:
            role_name: 角色名称
            permission: 权限名称

        Returns:
            是否授予成功
        """
        if self.get_role(role_name) is None:
            return False

        with self._lock:
            conn = self._conn
            cursor = conn.cursor()

            try:
                cursor.execute(
                    "INSERT OR IGNORE INTO permissions (role_name, permission) VALUES (?, ?)",
                    (role_name, permission),
                )
                conn.commit()
                return True
            except sqlite3.Error:
                return False

    def revoke_permission(self, role_name: str, permission: str) -> bool:
        """
        撤销角色权限

        Args:
            role_name: 角色名称
            permission: 权限名称

        Returns:
            是否撤销成功
        """
        with self._lock:
            conn = self._conn
            cursor = conn.cursor()

            cursor.execute(
                "DELETE FROM permissions WHERE role_name = ? AND permission = ?",
                (role_name, permission),
            )
            conn.commit()

            return cursor.rowcount > 0

    def get_role_permissions(self, role_name: str) -> set[str]:
        """
        获取角色的所有权限

        Args:
            role_name: 角色名称

        Returns:
            权限集合
        """
        conn = self._conn
        cursor = conn.cursor()

        cursor.execute(
            "SELECT permission FROM permissions WHERE role_name = ?",
            (role_name,),
        )

        return {row[0] for row in cursor.fetchall()}

    # ========== 用户角色管理 ==========

    def assign_role(
        self,
        user_id: str,
        role_name: str,
        granted_by: str,
        expires_at: Optional[datetime] = None,
    ) -> UserRole:
        """
        为用户分配角色

        Args:
            user_id: 用户ID
            role_name: 角色名称
            granted_by: 授权人ID
            expires_at: 过期时间

        Returns:
            用户角色关联

        Raises:
            ValueError: 角色不存在
        """
        if self.get_role(role_name) is None:
            raise ValueError(f"角色不存在: {role_name}")

        with self._lock:
            conn = self._conn
            cursor = conn.cursor()

            now = datetime.utcnow()

            # 检查是否已存在
            cursor.execute(
                "SELECT id FROM user_roles WHERE user_id = ? AND role_name = ?",
                (user_id, role_name),
            )

            if cursor.fetchone():
                # 更新现有记录
                cursor.execute(
                    """
                    UPDATE user_roles
                    SET granted_by = ?, granted_at = ?, expires_at = ?, is_active = 1
                    WHERE user_id = ? AND role_name = ?
                    """,
                    (granted_by, now.isoformat(), expires_at.isoformat() if expires_at else None, user_id, role_name),
                )
            else:
                # 插入新记录
                cursor.execute(
                    """
                    INSERT INTO user_roles (user_id, role_name, granted_by, granted_at, expires_at)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (user_id, role_name, granted_by, now.isoformat(), expires_at.isoformat() if expires_at else None),
                )

            conn.commit()

            return UserRole(
                user_id=user_id,
                role_name=role_name,
                granted_by=granted_by,
                granted_at=now,
                expires_at=expires_at,
            )

    def revoke_role(self, user_id: str, role_name: str) -> bool:
        """
        撤销用户角色

        Args:
            user_id: 用户ID
            role_name: 角色名称

        Returns:
            是否撤销成功
        """
        with self._lock:
            conn = self._conn
            cursor = conn.cursor()

            cursor.execute(
                "UPDATE user_roles SET is_active = 0 WHERE user_id = ? AND role_name = ?",
                (user_id, role_name),
            )
            conn.commit()

            return cursor.rowcount > 0

    def get_user_roles(self, user_id: str, active_only: bool = True) -> list[UserRole]:
        """
        获取用户的所有角色

        Args:
            user_id: 用户ID
            active_only: 是否只返回激活的角色

        Returns:
            用户角色列表
        """
        conn = self._conn
        cursor = conn.cursor()

        query = "SELECT * FROM user_roles WHERE user_id = ?"
        params = [user_id]

        if active_only:
            query += " AND is_active = 1"
        else:
            query += " ORDER BY granted_at DESC"

        cursor.execute(query, params)

        roles = []
        for row in cursor.fetchall():
            ur = UserRole(
                user_id=row["user_id"],
                role_name=row["role_name"],
                granted_by=row["granted_by"],
                granted_at=datetime.fromisoformat(row["granted_at"]),
                expires_at=datetime.fromisoformat(row["expires_at"]) if row["expires_at"] else None,
                is_active=bool(row["is_active"]),
            )
            # 过滤过期角色
            if active_only and ur.is_expired():
                continue
            roles.append(ur)

        return roles

    def get_role_users(self, role_name: str) -> list[str]:
        """
        获取拥有指定角色的所有用户

        Args:
            role_name: 角色名称

        Returns:
            用户ID列表
        """
        conn = self._conn
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT DISTINCT user_id
            FROM user_roles
            WHERE role_name = ? AND is_active = 1
            ORDER BY user_id
            """,
            (role_name,),
        )

        return [row[0] for row in cursor.fetchall()]

    # ========== 权限检查 ==========

    def check_permission(
        self,
        user_id: str,
        permission: str,
    ) -> bool:
        """
        检查用户是否拥有指定权限

        Args:
            user_id: 用户ID
            permission: 权限名称

        Returns:
            是否拥有权限
        """
        user_roles = self.get_user_roles(user_id)

        for ur in user_roles:
            role = self.get_role(ur.role_name)
            if role and role.matches_permission(permission):
                return True

        return False

    def check_any_permission(
        self,
        user_id: str,
        permissions: list[str],
    ) -> bool:
        """
        检查用户是否拥有任一权限

        Args:
            user_id: 用户ID
            permissions: 权限列表

        Returns:
            是否拥有任一权限
        """
        return any(self.check_permission(user_id, perm) for perm in permissions)

    def check_all_permissions(
        self,
        user_id: str,
        permissions: list[str],
    ) -> bool:
        """
        检查用户是否拥有所有权限

        Args:
            user_id: 用户ID
            permissions: 权限列表

        Returns:
            是否拥有所有权限
        """
        return all(self.check_permission(user_id, perm) for perm in permissions)

    def get_user_permissions(self, user_id: str) -> set[str]:
        """
        获取用户的所有权限

        Args:
            user_id: 用户ID

        Returns:
            权限集合
        """
        permissions = set()

        for ur in self.get_user_roles(user_id):
            role = self.get_role(ur.role_name)
            if role:
                permissions.update(role.permissions)

        return permissions

    # ========== 批量操作 ==========

    def assign_roles(
        self,
        user_id: str,
        role_names: list[str],
        granted_by: str,
    ) -> list[UserRole]:
        """
        批量为用户分配角色

        Args:
            user_id: 用户ID
            role_names: 角色名称列表
            granted_by: 授权人ID

        Returns:
            用户角色关联列表
        """
        results = []
        for role_name in role_names:
            try:
                ur = self.assign_role(user_id, role_name, granted_by)
                results.append(ur)
            except ValueError:
                continue

        return results

    def revoke_all_roles(self, user_id: str, granted_by: str) -> int:
        """
        撤销用户的所有角色

        Args:
            user_id: 用户ID
            granted_by: 操作人ID

        Returns:
            撤销的角色数量
        """
        with self._lock:
            conn = self._conn
            cursor = conn.cursor()

            cursor.execute(
                "UPDATE user_roles SET is_active = 0 WHERE user_id = ?",
                (user_id,),
            )
            conn.commit()

            return cursor.rowcount

    # ========== 统计信息 ==========

    def get_statistics(self) -> dict[str, int]:
        """
        获取RBAC系统统计信息

        Returns:
            统计信息字典
        """
        conn = self._conn
        cursor = conn.cursor()

        stats = {}

        # 角色数量
        cursor.execute("SELECT COUNT(*) FROM roles")
        stats["total_roles"] = cursor.fetchone()[0]

        # 系统角色数量
        cursor.execute("SELECT COUNT(*) FROM roles WHERE is_system_role = 1")
        stats["system_roles"] = cursor.fetchone()[0]

        # 用户角色关联数量
        cursor.execute("SELECT COUNT(*) FROM user_roles WHERE is_active = 1")
        stats["active_user_roles"] = cursor.fetchone()[0]

        # 唯一用户数量
        cursor.execute("SELECT COUNT(DISTINCT user_id) FROM user_roles WHERE is_active = 1")
        stats["unique_users"] = cursor.fetchone()[0]

        return stats

    # ========== 清理 ==========

    def cleanup_expired_roles(self) -> int:
        """
        清理过期的用户角色关联

        Returns:
            清理的记录数
        """
        with self._lock:
            conn = self._conn
            cursor = conn.cursor()

            now = datetime.utcnow().isoformat()

            cursor.execute(
                """
                UPDATE user_roles
                SET is_active = 0
                WHERE expires_at IS NOT NULL AND expires_at < ?
                """,
                (now,),
            )
            conn.commit()

            return cursor.rowcount

    def close(self) -> None:
        """关闭数据库连接"""
        if hasattr(self._local, "conn"):
            self._local.conn.close()
            delattr(self._local, "conn")
