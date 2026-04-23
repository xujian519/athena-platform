"""
多级权限系统

提供基于规则的工具权限控制，支持三种权限模式：
- DEFAULT: 默认模式，需要用户确认
- AUTO: 自动模式，根据规则自动决策
- BYPASS: 绕过模式，允许所有调用
- PLAN: 计划模式，阻止所有写入操作（新增）

核心特性:
1. 基于规则的权限控制 (允许/拒绝规则)
2. 支持通配符模式匹配
3. 路径级权限控制（新增）
4. 命令黑名单检查（新增）
5. PLAN 模式写入阻止（新增）
6. 运行时权限检查
7. 与 ToolCallManager 无缝集成

作者: Athena平台团队
创建时间: 2026-04-20
版本: v2.0.0
"""
from __future__ import annotations

from .modes import (
    DENIED_COMMANDS,
    PLAN_MODE_WRITES,
    PermissionMode,
)
from .path_rules import (
    PathRule,
    PathRuleManager,
)
from .command_blacklist import (
    CommandBlacklist,
)
from .checker import (
    EnhancedPermissionChecker,
)

# 向后兼容：从原 permissions.py 导出
from core.tools.permissions import (
    PermissionRule,
    PermissionDecision,
    ToolPermissionContext,
    DEFAULT_ALLOW_RULES,
    DEFAULT_DENY_RULES,
    get_global_permission_context,
)

__all__ = [
    # 新增 v2.0
    "PermissionMode",
    "PLAN_MODE_WRITES",
    "DENIED_COMMANDS",
    "PathRule",
    "PathRuleManager",
    "CommandBlacklist",
    "EnhancedPermissionChecker",

    # 向后兼容 v1.0
    "PermissionRule",
    "PermissionDecision",
    "ToolPermissionContext",
    "DEFAULT_ALLOW_RULES",
    "DEFAULT_DENY_RULES",
    "get_global_permission_context",
]

__version__ = "2.0.0"
