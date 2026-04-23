#!/usr/bin/env python3

"""
感知模块权限控制系统
Perception Module Access Control System

提供基于角色的访问控制（RBAC）和权限管理功能

作者: Athena AI系统
创建时间: 2026-01-26
版本: 1.0.0
"""

import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional

logger = logging.getLogger(__name__)


class Permission(Enum):
    """权限枚举"""
    # 基础权限
    READ = "read"
    WRITE = "write"
    DELETE = "delete"

    # 处理权限
    PROCESS_TEXT = "process_text"
    PROCESS_IMAGE = "process_image"
    PROCESS_AUDIO = "process_audio"
    PROCESS_VIDEO = "process_video"

    # 高级权限
    BATCH_PROCESS = "batch_process"
    STREAM_PROCESS = "stream_process"
    ACCESS_CACHE = "access_cache"
    CLEAR_CACHE = "clear_cache"

    # 管理权限
    VIEW_METRICS = "view_metrics"
    MODIFY_CONFIG = "modify_config"
    RESTART_PROCESSOR = "restart_processor"


class Role(Enum):
    """角色枚举"""
    ADMIN = "admin"
    USER = "user"
    GUEST = "guest"
    SERVICE = "service"


@dataclass
class User:
    """用户信息"""
    user_id: str
    username: str
    role: Role
    permissions: set[Permission] = field(default_factory=set)
    metadata: dict[str, Any] = field(default_factory=dict)

    def has_permission(self, permission: Permission) -> bool:
        """检查用户是否有指定权限"""
        return permission in self.permissions

    def add_permission(self, permission: Permission) -> None:
        """添加权限"""
        self.permissions.add(permission)
        logger.info(f"用户 {self.username} 添加权限: {permission.value}")

    def remove_permission(self, permission: Permission) -> None:
        """移除权限"""
        self.permissions.discard(permission)
        logger.info(f"用户 {self.username} 移除权限: {permission.value}")


class AccessControl:
    """访问控制系统"""

    # 默认角色权限映射
    DEFAULT_ROLE_PERMISSIONS = {
        Role.ADMIN: {
            Permission.READ, Permission.WRITE, Permission.DELETE,
            Permission.PROCESS_TEXT, Permission.PROCESS_IMAGE,
            Permission.PROCESS_AUDIO, Permission.PROCESS_VIDEO,
            Permission.BATCH_PROCESS, Permission.STREAM_PROCESS,
            Permission.ACCESS_CACHE, Permission.CLEAR_CACHE,
            Permission.VIEW_METRICS, Permission.MODIFY_CONFIG,
            Permission.RESTART_PROCESSOR,
        },
        Role.USER: {
            Permission.READ, Permission.WRITE,
            Permission.PROCESS_TEXT, Permission.PROCESS_IMAGE,
            Permission.PROCESS_AUDIO, Permission.PROCESS_VIDEO,
            Permission.ACCESS_CACHE, Permission.VIEW_METRICS,
        },
        Role.GUEST: {
            Permission.READ,
            Permission.VIEW_METRICS,
        },
        Role.SERVICE: {
            Permission.READ, Permission.WRITE,
            Permission.PROCESS_TEXT, Permission.PROCESS_IMAGE,
            Permission.PROCESS_AUDIO, Permission.PROCESS_VIDEO,
            Permission.BATCH_PROCESS, Permission.ACCESS_CACHE,
        },
    }

    def __init__(self):
        self.users: dict[str, User] = {}
        self.role_permissions: dict[Role, set[Permission]] = {
            role: set(perms) for role, perms in self.DEFAULT_ROLE_PERMISSIONS.items()
        }
        logger.info("访问控制系统已初始化")

    def add_user(self, user: User) -> None:
        """添加用户"""
        # 如果用户没有明确指定权限，使用角色默认权限
        if not user.permissions:
            user.permissions = self.role_permissions.get(user.role, set()).copy()

        self.users[user.user_id] = user
        logger.info(f"添加用户: {user.username} (角色: {user.role.value})")

    def get_user(self, user_id: str) -> Optional[User]:
        """获取用户"""
        return self.users.get(user_id)

    def check_permission(self, user_id: str, permission: Permission) -> bool:
        """检查用户权限"""
        user = self.get_user(user_id)
        if not user:
            logger.warning(f"用户不存在: {user_id}")
            return False

        return user.has_permission(permission)

    def require_permission(self, user_id: str, permission: Permission) -> None:
        """
        要求用户具有指定权限，如果没有则抛出异常

        Raises:
            PermissionDenied: 当用户没有权限时
        """
        if not self.check_permission(user_id, permission):
            user = self.get_user(user_id)
            raise PermissionDenied(
                f"用户 {user.username if user else user_id} "
                f"没有权限: {permission.value}"
            )

    def grant_permission(self, user_id: str, permission: Permission) -> bool:
        """授予用户权限"""
        user = self.get_user(user_id)
        if not user:
            logger.warning(f"用户不存在: {user_id}")
            return False

        user.add_permission(permission)
        return True

    def revoke_permission(self, user_id: str, permission: Permission) -> bool:
        """撤销用户权限"""
        user = self.get_user(user_id)
        if not user:
            logger.warning(f"用户不存在: {user_id}")
            return False

        user.remove_permission(permission)
        return True

    def set_user_role(self, user_id: str, role: Role) -> bool:
        """设置用户角色"""
        user = self.get_user(user_id)
        if not user:
            logger.warning(f"用户不存在: {user_id}")
            return False

        old_role = user.role
        user.role = role
        user.permissions = self.role_permissions.get(role, set()).copy()

        logger.info(f"用户 {user.username} 角色从 {old_role.value} 更改为 {role.value}")
        return True

    def create_user(
        self,
        user_id: str,
        username: str,
        role: Role = Role.USER,
        permissions: Optional[set[Permission]] = None,
    ) -> User:
        """创建新用户"""
        user = User(
            user_id=user_id,
            username=username,
            role=role,
            permissions=permissions or self.role_permissions.get(role, set()).copy()
        )
        self.add_user(user)
        return user


class PermissionDenied(Exception):
    """权限拒绝异常"""

    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)


# 权限检查装饰器
def require_permission(permission: Permission, access_control: AccessControl):
    """权限检查装饰器"""

    def decorator(func):
        def wrapper(user_id: str, *args, **kwargs):
            # 检查权限
            access_control.require_permission(user_id, permission)
            # 执行函数
            return func(*args, **kwargs)

        return wrapper

    return decorator


# 全局访问控制实例
_global_access_control: Optional[AccessControl] = None


def get_global_access_control() -> AccessControl:
    """获取全局访问控制实例"""
    global _global_access_control
    if _global_access_control is None:
        _global_access_control = AccessControl()

        # 创建默认用户
        _global_access_control.create_user("admin", "Administrator", Role.ADMIN)
        _global_access_control.create_user("system", "System Service", Role.SERVICE)

        logger.info("全局访问控制系统已初始化")

    return _global_access_control


# 导出
__all__ = [
    "Permission",
    "Role",
    "User",
    "AccessControl",
    "PermissionDenied",
    "require_permission",
    "get_global_access_control",
]

