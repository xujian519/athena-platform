from __future__ import annotations
"""
工具权限过滤器

为声明式 Agent 提供工具调用权限控制。
支持白名单（tools）和黑名单（disallowed_tools）两种过滤模式。

Author: Athena Team
"""

import logging
from dataclasses import dataclass, field
from typing import Any

from .models import AgentDefinition

logger = logging.getLogger("agent.declarative.permissions")

# 只读模式下默认禁止的工具类别
READONLY_BLOCKED_PATTERNS = [
    "file_write",
    "file_edit",
    "file_delete",
    "file_create",
    "bash",
    "shell",
    "execute",
    "database_write",
    "database_delete",
    "database_update",
]


@dataclass
class ToolPermissionFilter:
    """
    工具权限过滤器

    根据工具 ID 判断是否允许执行。
    支持精确匹配和前缀匹配两种模式。

    优先级：
    1. 如果 disallowed_tools 包含该工具 → 拒绝
    2. 如果 tools 非空且不包含该工具 → 拒绝
    3. 否则 → 允许
    """

    # 允许的工具白名单（空=允许全部，仅受黑名单限制）
    allowed_tools: list[str] = field(default_factory=list)

    # 禁止的工具黑名单
    disallowed_tools: list[str] = field(default_factory=list)

    # 是否为只读模式
    is_readonly: bool = False

    def is_tool_permitted(self, tool_id: str) -> bool:
        """
        检查工具是否被允许

        Args:
            tool_id: 工具标识符，如 "builtin.file_read"

        Returns:
            是否允许执行
        """
        # 1. 检查黑名单（精确匹配和前缀匹配）
        for blocked in self.disallowed_tools:
            if tool_id == blocked or tool_id.startswith(f"{blocked}."):
                return False

        # 2. 只读模式下额外检查（精确匹配或前缀匹配，避免子串误杀）
        if self.is_readonly:
            tool_lower = tool_id.lower()
            for pattern in READONLY_BLOCKED_PATTERNS:
                if tool_lower == pattern or tool_lower.startswith(f"{pattern}.") or tool_lower.startswith(f"{pattern}_"):
                    return False

        # 3. 如果有白名单，检查是否在其中
        if self.allowed_tools:
            for allowed in self.allowed_tools:
                if tool_id == allowed or tool_id.startswith(f"{allowed}."):
                    return True
            return False

        # 4. 无白名单限制，允许
        return True

    def filter_tools(self, tools: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """
        过滤工具列表，移除不允许的工具

        Args:
            tools: 工具信息列表，每个字典应包含 "id" 或 "tool_id" 字段

        Returns:
            过滤后的工具列表
        """
        filtered = []
        for tool in tools:
            tool_id = tool.get("id") or tool.get("tool_id", "")
            if not isinstance(tool_id, str):
                tool_id = str(tool_id) if tool_id is not None else ""
            if self.is_tool_permitted(tool_id):
                filtered.append(tool)
            else:
                logger.debug(f"工具被权限过滤: {tool_id}")
        return filtered

    @classmethod
    def from_definition(cls, definition: AgentDefinition) -> ToolPermissionFilter:
        """
        从 AgentDefinition 创建权限过滤器

        Args:
            definition: Agent 定义

        Returns:
            配置好的 ToolPermissionFilter
        """
        return cls(
            allowed_tools=definition.tools,
            disallowed_tools=definition.disallowed_tools,
            is_readonly=definition.is_readonly,
        )

    @classmethod
    def get_readonly_filter(cls) -> ToolPermissionFilter:
        """
        创建只读过滤器工厂方法

        Returns:
            只读模式的权限过滤器
        """
        return cls(is_readonly=True)
