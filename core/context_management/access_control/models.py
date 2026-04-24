"""
访问控制数据模型

定义RBAC系统的核心数据结构，包括角色、权限、用户角色关联、
上下文权限和审计日志条目。

Author: SecurityAgent
Date: 2026-04-24
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Optional
from uuid import uuid4


class PermissionLevel(str, Enum):
    """上下文权限级别"""

    OWNER = "owner"  # 所有者 - 完全控制
    EDIT = "edit"    # 编辑 - 可修改内容
    READ = "read"    # 读取 - 仅查看
    NONE = "none"    # 无权限


class ActionType(str, Enum):
    """审计操作类型"""

    # 访问操作
    ACCESS = "access"
    VIEW = "view"

    # 上下文操作
    CREATE_CONTEXT = "create_context"
    READ_CONTEXT = "read_context"
    UPDATE_CONTEXT = "update_context"
    DELETE_CONTEXT = "delete_context"

    # 权限操作
    GRANT_PERMISSION = "grant_permission"
    REVOKE_PERMISSION = "revoke_permission"
    CHECK_PERMISSION = "check_permission"

    # 角色操作
    CREATE_ROLE = "create_role"
    DELETE_ROLE = "delete_role"
    ASSIGN_ROLE = "assign_role"
    REVOKE_ROLE = "revoke_role"

    # 用户操作
    CREATE_USER = "create_user"
    DELETE_USER = "delete_user"
    MODIFY_USER = "modify_user"

    # 系统操作
    LOGIN = "login"
    LOGOUT = "logout"
    SYSTEM = "system"


class OperationResult(str, Enum):
    """操作结果"""

    SUCCESS = "success"
    FAILURE = "failure"
    PARTIAL = "partial"
    DENIED = "denied"


@dataclass
class Permission:
    """
    权限模型

    表示系统中的一个权限点，格式为 "resource.action"
    例如: "context.read", "user.manage"
    """

    name: str
    """权限名称，格式: resource.action"""

    description: str = ""
    """权限描述"""

    category: str = "general"
    """权限分类"""

    def __post_init__(self):
        """验证权限名称格式"""
        if "." not in self.name:
            raise ValueError(f"无效的权限名称格式: {self.name}, 应为 'resource.action'")

    def __str__(self) -> str:
        return self.name

    def matches(self, pattern: str) -> bool:
        """
        检查权限是否匹配模式

        支持通配符:
        - "context.*" 匹配所有context相关权限
        - "*.read" 匹配所有read权限
        - "*" 匹配所有权限

        Args:
            pattern: 权限模式，可能包含通配符

        Returns:
            是否匹配
        """
        if pattern == "*":
            return True

        resource, action = self.name.split(".", 1)

        if "." in pattern:
            pattern_resource, pattern_action = pattern.split(".", 1)
            resource_match = pattern_resource == "*" or pattern_resource == resource
            action_match = pattern_action == "*" or pattern_action == action
            return resource_match and action_match
        else:
            return False

    @classmethod
    def from_string(cls, permission_str: str) -> Permission:
        """从字符串创建权限"""
        return cls(name=permission_str)


@dataclass
class Role:
    """
    角色模型

    表示系统中的一个角色，包含一组权限
    """

    name: str
    """角色名称，唯一标识符"""

    description: str = ""
    """角色描述"""

    permissions: set[str] = field(default_factory=set)
    """角色拥有的权限集合"""

    is_system_role: bool = False
    """是否为系统角色（不可删除）"""

    priority: int = 0
    """优先级，用于解决多角色冲突"""

    created_at: datetime = field(default_factory=datetime.utcnow)
    """创建时间"""

    def add_permission(self, permission: str | Permission) -> None:
        """添加权限"""
        if isinstance(permission, Permission):
            self.permissions.add(permission.name)
        else:
            self.permissions.add(permission)

    def remove_permission(self, permission: str | Permission) -> None:
        """移除权限"""
        if isinstance(permission, Permission):
            self.permissions.discard(permission.name)
        else:
            self.permissions.discard(permission)

    def has_permission(self, permission: str | Permission) -> bool:
        """检查是否拥有指定权限"""
        perm_name = permission.name if isinstance(permission, Permission) else permission
        return perm_name in self.permissions

    def get_wildcard_permissions(self) -> list[str]:
        """获取所有通配符权限"""
        return [p for p in self.permissions if "*" in p]

    def matches_permission(self, permission: str) -> bool:
        """
        检查是否匹配指定权限（支持通配符）

        Args:
            permission: 要检查的权限

        Returns:
            是否匹配
        """
        # 直接匹配
        if permission in self.permissions:
            return True

        # 通配符匹配
        for perm in self.permissions:
            if "*" in perm:
                parts = perm.split(".")
                if len(parts) == 2:
                    resource, action = parts
                    perm_resource, perm_action = permission.split(".", 1)

                    resource_match = resource == "*" or resource == perm_resource
                    action_match = action == "*" or action == perm_action

                    if resource_match and action_match:
                        return True

        return False


@dataclass
class UserRole:
    """
    用户角色关联模型

    表示用户与角色的关联关系
    """

    user_id: str
    """用户ID"""

    role_name: str
    """角色名称"""

    granted_by: str
    """授权人ID"""

    granted_at: datetime = field(default_factory=datetime.utcnow)
    """授权时间"""

    expires_at: Optional[datetime] = None
    """过期时间，None表示永久"""

    is_active: bool = True
    """是否激活"""

    def is_expired(self) -> bool:
        """检查是否已过期"""
        if self.expires_at is None:
            return False
        return datetime.utcnow() > self.expires_at


@dataclass
class ContextPermission:
    """
    上下文权限模型

    表示用户对特定上下文的访问权限
    """

    context_id: str
    """上下文ID"""

    user_id: str
    """用户ID"""

    level: PermissionLevel
    """权限级别"""

    granted_by: str
    """授权人ID"""

    granted_at: datetime = field(default_factory=datetime.utcnow)
    """授权时间"""

    expires_at: Optional[datetime] = None
    """过期时间"""

    is_active: bool = True
    """是否激活"""

    def is_expired(self) -> bool:
        """检查是否已过期"""
        if self.expires_at is None:
            return False
        return datetime.utcnow() > self.expires_at

    def can_read(self) -> bool:
        """检查是否可读"""
        return self.is_active and not self.is_expired() and self.level in (
            PermissionLevel.READ,
            PermissionLevel.EDIT,
            PermissionLevel.OWNER,
        )

    def can_edit(self) -> bool:
        """检查是否可编辑"""
        return self.is_active and not self.is_expired() and self.level in (
            PermissionLevel.EDIT,
            PermissionLevel.OWNER,
        )

    def can_delete(self) -> bool:
        """检查是否可删除"""
        return self.is_active and not self.is_expired() and self.level == PermissionLevel.OWNER


@dataclass
class AuditLogEntry:
    """
    审计日志条目

    记录系统中的所有敏感操作，用于安全审计和合规检查
    """

    id: str = field(default_factory=lambda: str(uuid4()))
    """唯一标识符"""

    timestamp: datetime = field(default_factory=datetime.utcnow)
    """时间戳"""

    user_id: str = ""
    """用户ID"""

    action: ActionType = ActionType.SYSTEM
    """操作类型"""

    resource_type: str = ""
    """资源类型"""

    resource_id: str = ""
    """资源ID"""

    result: OperationResult = OperationResult.SUCCESS
    """操作结果"""

    details: dict[str, Any] = field(default_factory=dict)
    """详细信息"""

    ip_address: Optional[str] = None
    """IP地址"""

    user_agent: Optional[str] = None
    """用户代理"""

    session_id: Optional[str] = None
    """会话ID"""

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "id": self.id,
            "timestamp": self.timestamp.isoformat(),
            "user_id": self.user_id,
            "action": self.action.value if isinstance(self.action, ActionType) else self.action,
            "resource_type": self.resource_type,
            "resource_id": self.resource_id,
            "result": self.result.value if isinstance(self.result, OperationResult) else self.result,
            "details": self.details,
            "ip_address": self.ip_address,
            "user_agent": self.user_agent,
            "session_id": self.session_id,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> AuditLogEntry:
        """从字典创建"""
        return cls(
            id=data.get("id", str(uuid4())),
            timestamp=datetime.fromisoformat(data["timestamp"]) if data.get("timestamp") else datetime.utcnow(),
            user_id=data.get("user_id", ""),
            action=ActionType(data["action"]) if data.get("action") in ActionType.__members__ else ActionType.SYSTEM,
            resource_type=data.get("resource_type", ""),
            resource_id=data.get("resource_id", ""),
            result=OperationResult(data["result"]) if data.get("result") in OperationResult.__members__ else OperationResult.SUCCESS,
            details=data.get("details", {}),
            ip_address=data.get("ip_address"),
            user_agent=data.get("user_agent"),
            session_id=data.get("session_id"),
        )


# 系统预定义角色
class SystemRoles:
    """系统预定义角色"""

    @staticmethod
    def admin() -> Role:
        """系统管理员 - 拥有所有权限"""
        return Role(
            name="admin",
            description="系统管理员，拥有所有权限",
            permissions={
                "context.create",
                "context.read",
                "context.update",
                "context.delete",
                "context.admin",
                "user.manage",
                "role.manage",
                "audit.read",
                "system.admin",
            },
            is_system_role=True,
            priority=1000,
        )

    @staticmethod
    def moderator() -> Role:
        """内容审核员"""
        return Role(
            name="moderator",
            description="内容审核员，可读取、更新和审核内容",
            permissions={
                "context.read",
                "context.update",
                "context.audit",
                "audit.read",
            },
            is_system_role=True,
            priority=500,
        )

    @staticmethod
    def editor() -> Role:
        """编辑者"""
        return Role(
            name="editor",
            description="编辑者，可创建和编辑自己的内容",
            permissions={
                "context.create",
                "context.read",
                "context.update",
            },
            is_system_role=True,
            priority=300,
        )

    @staticmethod
    def viewer() -> Role:
        """查看者"""
        return Role(
            name="viewer",
            description="查看者，仅能读取内容",
            permissions={"context.read"},
            is_system_role=True,
            priority=100,
        )

    @staticmethod
    def guest() -> Role:
        """访客"""
        return Role(
            name="guest",
            description="访客，受限的读取权限",
            permissions={"context.read"},
            is_system_role=True,
            priority=50,
        )

    @classmethod
    def all(cls) -> list[Role]:
        """获取所有系统角色"""
        return [cls.admin(), cls.moderator(), cls.editor(), cls.viewer(), cls.guest()]


# 系统预定义权限
class SystemPermissions:
    """系统预定义权限"""

    # 上下文权限
    CONTEXT_CREATE = Permission("context.create", "创建上下文")
    CONTEXT_READ = Permission("context.read", "读取上下文")
    CONTEXT_UPDATE = Permission("context.update", "更新上下文")
    CONTEXT_DELETE = Permission("context.delete", "删除上下文")
    CONTEXT_ADMIN = Permission("context.admin", "上下文管理")

    # 用户权限
    USER_MANAGE = Permission("user.manage", "用户管理")
    USER_CREATE = Permission("user.create", "创建用户")
    USER_DELETE = Permission("user.delete", "删除用户")
    USER_MODIFY = Permission("user.modify", "修改用户")

    # 角色权限
    ROLE_MANAGE = Permission("role.manage", "角色管理")
    ROLE_CREATE = Permission("role.create", "创建角色")
    ROLE_DELETE = Permission("role.delete", "删除角色")
    ROLE_ASSIGN = Permission("role.assign", "分配角色")

    # 审计权限
    AUDIT_READ = Permission("audit.read", "读取审计日志")
    AUDIT_EXPORT = Permission("audit.export", "导出审计日志")

    # 系统权限
    SYSTEM_ADMIN = Permission("system.admin", "系统管理")

    @classmethod
    def all(cls) -> list[Permission]:
        """获取所有系统权限"""
        return [
            cls.CONTEXT_CREATE,
            cls.CONTEXT_READ,
            cls.CONTEXT_UPDATE,
            cls.CONTEXT_DELETE,
            cls.CONTEXT_ADMIN,
            cls.USER_MANAGE,
            cls.USER_CREATE,
            cls.USER_DELETE,
            cls.USER_MODIFY,
            cls.ROLE_MANAGE,
            cls.ROLE_CREATE,
            cls.ROLE_DELETE,
            cls.ROLE_ASSIGN,
            cls.AUDIT_READ,
            cls.AUDIT_EXPORT,
            cls.SYSTEM_ADMIN,
        ]
