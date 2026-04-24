"""
访问控制模块

提供完整的RBAC权限系统和审计日志功能，保护上下文系统的安全访问。

Components:
- RBACManager: RBAC权限管理器
- ContextPermissionManager: 上下文权限管理器
- AuditLogger: 审计日志管理器
- Models: 数据模型（Role、Permission、ContextPermission等）

Author: SecurityAgent
Date: 2026-04-24
"""

from .audit_logger import AuditLogger
from .context_permission_manager import ContextPermissionManager
from .models import (
    ActionType,
    AuditLogEntry,
    ContextPermission,
    OperationResult,
    Permission,
    PermissionLevel,
    Role,
    SystemPermissions,
    SystemRoles,
    UserRole,
)
from .rbac_manager import RBACManager

__all__ = [
    # 管理器
    "RBACManager",
    "ContextPermissionManager",
    "AuditLogger",
    # 数据模型
    "Role",
    "Permission",
    "UserRole",
    "ContextPermission",
    "AuditLogEntry",
    "PermissionLevel",
    "ActionType",
    "OperationResult",
    # 系统预定义
    "SystemRoles",
    "SystemPermissions",
    # 工厂函数
    "create_access_control_system",
]


def create_access_control_system(
    db_dir: str = "~/.athena",
    auto_init: bool = True,
) -> tuple[RBACManager, ContextPermissionManager, AuditLogger]:
    """
    创建完整的访问控制系统

    Args:
        db_dir: 数据库目录
        auto_init: 是否自动初始化

    Returns:
        (RBAC管理器, 上下文权限管理器, 审计日志管理器) 元组
    """
    from pathlib import Path

    db_path = Path(db_dir).expanduser()

    rbac = RBACManager(
        db_path=db_path / "access_control.db",
        auto_init=auto_init,
    )

    context_perm = ContextPermissionManager(
        db_path=db_path / "context_permissions.db",
        auto_init=auto_init,
    )

    audit = AuditLogger(
        db_path=db_path / "audit_logs.db",
        auto_init=auto_init,
    )

    return rbac, context_perm, audit


# 版本信息
__version__ = "1.0.0"
__author__ = "SecurityAgent"
__license__ = "MIT"
