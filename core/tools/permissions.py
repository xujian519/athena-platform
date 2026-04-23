#!/usr/bin/env python3
"""
工具权限系统

实现Claude Code风格的工具权限控制，支持三种权限模式：
- DEFAULT: 默认模式，需要用户确认
- AUTO: 自动模式，根据规则自动决策
- BYPASS: 绕过模式，允许所有调用

核心特性:
1. 基于规则的权限控制 (允许/拒绝规则)
2. 支持通配符模式匹配
3. 运行时权限检查
4. 与ToolCallManager无缝集成

作者: Athena平台团队
创建时间: 2026-04-19
版本: v1.0.0
"""
from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class PermissionMode(Enum):
    """权限模式枚举"""

    DEFAULT = "default"  # 默认模式: 未匹配规则时需要用户确认
    AUTO = "auto"  # 自动模式: 未匹配规则时自动拒绝
    BYPASS = "bypass"  # 绕过模式: 允许所有调用


@dataclass
class PermissionRule:
    """
    权限规则

    定义工具调用的允许或拒绝规则。

    Attributes:
        rule_id: 规则唯一标识
        pattern: 工具名称模式 (支持通配符*, 如 "bash:*" 或 "web_*")
        description: 规则描述
        enabled: 是否启用该规则
        priority: 优先级 (数值越大优先级越高，用于冲突解决)
        metadata: 额外元数据
    """

    rule_id: str
    pattern: str
    description: str
    enabled: bool = True
    priority: int = 0
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class PermissionDecision:
    """
    权限决策结果

    记录权限检查的结果和原因。
    """

    allowed: bool  # 是否允许调用
    reason: str  # 决策原因
    mode: PermissionMode  # 决策时使用的权限模式
    matched_rule: Optional[str] = None  # 匹配的规则ID (如果有)


class ToolPermissionContext:
    """
    工具权限上下文

    管理工具调用的权限规则和决策逻辑。

    权限检查流程:
    1. 检查是否为BYPASS模式 → 直接允许
    2. 检查拒绝规则 (按优先级排序) → 匹配则拒绝
    3. 检查允许规则 (按优先级排序) → 匹配则允许
    4. 无匹配规则 → 根据mode决定 (AUTO:拒绝, DEFAULT:需要确认)

    Example:
        >>> ctx = ToolPermissionContext(mode=PermissionMode.AUTO)
        >>> ctx.add_rule("deny", PermissionRule(
        ...     rule_id="no-danger",
        ...     pattern="bash:*rm*",
        ...     description="拒绝危险命令"
        ... ))
        >>> decision = ctx.check_permission("bash:rm -rf /")
        >>> print(decision.allowed)  # False
    """

    def __init__(
        self,
        mode: PermissionMode = PermissionMode.DEFAULT,
        always_allow: list[PermissionRule] | None = None,
        always_deny: list[PermissionRule] | None = None,
    ):
        """
        初始化权限上下文

        Args:
            mode: 权限模式
            always_allow: 总是允许的规则列表
            always_deny: 总是拒绝的规则列表
        """
        self.mode = mode
        self._always_allow: dict[str, PermissionRule] = {}
        self._always_deny: dict[str, PermissionRule] = {}

        # 初始化规则
        for rule in always_allow or []:
            self._always_allow[rule.rule_id] = rule
        for rule in always_deny or []:
            self._always_deny[rule.rule_id] = rule

        logger.info(f"🔒 工具权限上下文初始化 (模式: {mode.value})")
        logger.info(f"   允许规则: {len(self._always_allow)}, 拒绝规则: {len(self._always_deny)}")

    def check_permission(
        self, tool_name: str, parameters: Optional[dict[str, Any]] = None
    ) -> PermissionDecision:
        """
        检查工具调用权限

        Args:
            tool_name: 工具名称
            parameters: 工具参数 (可选, 未来可用于高级规则)

        Returns:
            PermissionDecision: 权限决策结果
        """
        # 1. 绕过模式: 直接允许
        if self.mode == PermissionMode.BYPASS:
            return PermissionDecision(
                allowed=True,
                reason="绕过权限模式: 允许所有调用",
                mode=self.mode,
            )

        # 2. 检查拒绝规则 (优先级最高)
        sorted_deny = sorted(
            self._always_deny.values(),
            key=lambda r: r.priority,
            reverse=True,
        )
        for rule in sorted_deny:
            if not rule.enabled:
                continue
            if self._match_pattern(tool_name, rule.pattern):
                return PermissionDecision(
                    allowed=False,
                    reason=f"匹配拒绝规则: {rule.description}",
                    mode=self.mode,
                    matched_rule=rule.rule_id,
                )

        # 3. 检查允许规则
        sorted_allow = sorted(
            self._always_allow.values(),
            key=lambda r: r.priority,
            reverse=True,
        )
        for rule in sorted_allow:
            if not rule.enabled:
                continue
            if self._match_pattern(tool_name, rule.pattern):
                return PermissionDecision(
                    allowed=True,
                    reason=f"匹配允许规则: {rule.description}",
                    mode=self.mode,
                    matched_rule=rule.rule_id,
                )

        # 4. 无匹配规则: 根据模式决定
        if self.mode == PermissionMode.AUTO:
            return PermissionDecision(
                allowed=False,
                reason="自动模式: 无匹配允许规则，默认拒绝",
                mode=self.mode,
            )
        else:  # DEFAULT模式
            return PermissionDecision(
                allowed=False,
                reason="默认模式: 无匹配规则，需要用户确认",
                mode=self.mode,
            )

    def _match_pattern(self, tool_name: str, pattern: str) -> bool:
        """
        匹配工具名称模式

        支持通配符:
        - *: 匹配任意字符 (包括空字符)
        - 可以出现在模式的任意位置

        Examples:
            - "bash:*" 匹配 "bash:command", "bash:ls"
            - "*_search" 匹配 "web_search", "patent_search"
            - "file_*" 匹配 "file_read", "file_write"

        Args:
            tool_name: 工具名称
            pattern: 模式字符串

        Returns:
            bool: 是否匹配
        """
        # 转换为正则表达式
        # 转义特殊字符，但保留 * 作为通配符
        regex_pattern = re.escape(pattern).replace(r"\*", ".*")
        # 添加行首行尾锚点，确保完全匹配
        regex_pattern = f"^{regex_pattern}$"
        return re.match(regex_pattern, tool_name) is not None

    def add_rule(
        self, rule_type: str, rule: PermissionRule
    ) -> None:
        """
        添加权限规则

        Args:
            rule_type: 规则类型 ("allow" 或 "deny")
            rule: 权限规则

        Raises:
            ValueError: 如果规则类型无效
        """
        if rule_type == "allow":
            self._always_allow[rule.rule_id] = rule
            logger.info(f"✅ 允许规则已添加: {rule.rule_id} - {rule.pattern}")
        elif rule_type == "deny":
            self._always_deny[rule.rule_id] = rule
            logger.info(f"🚫 拒绝规则已添加: {rule.rule_id} - {rule.pattern}")
        else:
            raise ValueError(f"无效的规则类型: {rule_type} (必须是 'allow' 或 'deny')")

    def remove_rule(self, rule_id: str) -> bool:
        """
        移除权限规则

        Args:
            rule_id: 规则ID

        Returns:
            bool: 是否成功移除
        """
        removed = False
        if rule_id in self._always_allow:
            del self._always_allow[rule_id]
            removed = True
            logger.info(f"✅ 允许规则已移除: {rule_id}")
        if rule_id in self._always_deny:
            del self._always_deny[rule_id]
            removed = True
            logger.info(f"✅ 拒绝规则已移除: {rule_id}")
        return removed

    def set_mode(self, mode: PermissionMode) -> None:
        """
        设置权限模式

        Args:
            mode: 新的权限模式
        """
        old_mode = self.mode
        self.mode = mode
        logger.info(f"🔄 权限模式已更改: {old_mode.value} → {mode.value}")

    def get_rules(self) -> dict[str, Any]:
        """
        获取所有规则

        Returns:
            dict: 包含allow和deny规则的字典
        """
        return {
            "allow": [
                {
                    "id": rule.rule_id,
                    "pattern": rule.pattern,
                    "description": rule.description,
                    "enabled": rule.enabled,
                    "priority": rule.priority,
                }
                for rule in sorted(
                    self._always_allow.values(),
                    key=lambda r: r.priority,
                    reverse=True,
                )
            ],
            "deny": [
                {
                    "id": rule.rule_id,
                    "pattern": rule.pattern,
                    "description": rule.description,
                    "enabled": rule.enabled,
                    "priority": rule.priority,
                }
                for rule in sorted(
                    self._always_deny.values(),
                    key=lambda r: r.priority,
                    reverse=True,
                )
            ],
        }


# ========================================
# 预定义权限规则
# ========================================

DEFAULT_ALLOW_RULES = [
    PermissionRule(
        rule_id="read-operations",
        pattern="*:read",
        description="允许所有读操作",
        priority=10,
    ),
    PermissionRule(
        rule_id="safe-tools",
        pattern="web_search",
        description="允许网络搜索工具",
        priority=10,
    ),
    PermissionRule(
        rule_id="patent-tools",
        pattern="patent_*",
        description="允许专利相关工具",
        priority=10,
    ),
    PermissionRule(
        rule_id="analysis-tools",
        pattern="*analysis*",
        description="允许分析类工具",
        priority=5,
    ),
]

DEFAULT_DENY_RULES = [
    PermissionRule(
        rule_id="dangerous-rm",
        pattern="bash:*rm*",
        description="拒绝包含rm的bash命令",
        priority=100,
    ),
    PermissionRule(
        rule_id="dangerous-format",
        pattern="bash:*format*",
        description="拒绝格式化磁盘命令",
        priority=100,
    ),
    PermissionRule(
        rule_id="system-critical",
        pattern="*:shutdown",
        description="拒绝系统关机命令",
        priority=100,
    ),
]


# ========================================
# 全局权限上下文
# ========================================

_global_permission_context: ToolPermissionContext | None = None


def get_global_permission_context() -> ToolPermissionContext:
    """获取全局权限上下文"""
    global _global_permission_context
    if _global_permission_context is None:
        _global_permission_context = ToolPermissionContext(
            mode=PermissionMode.DEFAULT,
            always_allow=DEFAULT_ALLOW_RULES,
            always_deny=DEFAULT_DENY_RULES,
        )
    return _global_permission_context


__all__ = [
    "PermissionMode",
    "PermissionRule",
    "PermissionDecision",
    "ToolPermissionContext",
    "DEFAULT_ALLOW_RULES",
    "DEFAULT_DENY_RULES",
    "get_global_permission_context",
]
