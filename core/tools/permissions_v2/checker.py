"""
增强的权限检查器

整合路径规则、命令黑名单和 PLAN 模式的权限检查。

作者: Athena平台团队
创建时间: 2026-04-20
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

# 导入原有权限系统
from core.tools.permissions import (
    ToolPermissionContext,
    PermissionDecision,
    PermissionRule,
    PermissionMode as OldPermissionMode,
)

# 导入新增的权限模块
from .modes import (
    PermissionMode,
    is_plan_mode_write,
    is_read_only_tool,
)
from .path_rules import PathRule, PathRuleManager, DEFAULT_PATH_RULES
from .command_blacklist import CommandBlacklist

logger = logging.getLogger(__name__)


@dataclass
class PermissionConfig:
    """权限配置

    整合所有权限相关的配置参数。
    """

    mode: PermissionMode = PermissionMode.DEFAULT
    path_rules: list[PathRule] = field(default_factory=lambda: DEFAULT_PATH_RULES.copy())
    denied_commands: Optional[list[str]] = None
    always_allow: list[PermissionRule] = field(default_factory=list)
    always_deny: list[PermissionRule] = field(default_factory=list)


class EnhancedPermissionChecker(ToolPermissionContext):
    """增强的权限检查器

    在原有权限系统基础上增加：
    1. PLAN 模式支持
    2. 路径级规则检查
    3. 命令黑名单检查
    4. 只读工具自动批准

    权限检查流程：
    1. 检查 BYPASS 模式 → 直接允许
    2. 检查只读工具 → 自动允许
    3. 检查 PLAN 模式写入 → 拒绝
    4. 检查命令黑名单 → 拒绝
    5. 检查路径级规则 → 允许/拒绝/继续
    6. 检查工具级规则 → 允许/拒绝/继续
    7. 无匹配规则 → 根据模式决定

    Example:
        >>> checker = EnhancedPermissionChecker(mode=PermissionMode.PLAN)
        >>> decision = checker.check_permission(
        ...     "file:write",
        ...     {"file_path": "/tmp/test.txt"}
        ... )
        >>> print(decision.allowed)  # False (PLAN 模式阻止写入)
    """

    def __init__(
        self,
        mode: PermissionMode = PermissionMode.DEFAULT,
        path_rules: list[PathRule] | None = None,
        denied_commands: Optional[list[str]] = None,
        always_allow: list[PermissionRule] | None = None,
        always_deny: list[PermissionRule] | None = None,
    ):
        """初始化增强权限检查器

        Args:
            mode: 权限模式
            path_rules: 路径级规则列表
            denied_commands: 命令黑名单
            always_allow: 总是允许的工具规则
            always_deny: 总是拒绝的工具规则
        """
        # 转换 PermissionMode 为旧版 PermissionMode
        old_mode = self._convert_mode(mode)

        # 调用父类初始化
        super().__init__(
            mode=old_mode,
            always_allow=always_allow,
            always_deny=always_deny,
        )

        # 保存新权限模式
        self._enhanced_mode = mode

        # 初始化路径规则管理器
        self.path_manager = PathRuleManager(path_rules or DEFAULT_PATH_RULES)

        # 初始化命令黑名单检查器
        self.blacklist = CommandBlacklist(denied_commands)

        logger.info(
            f"🔒 增强权限检查器初始化 "
            f"(模式: {mode.value}, "
            f"路径规则: {len(self.path_manager.get_rules())}, "
            f"黑名单模式: {len(self.blacklist.get_patterns())})"
        )

    def check_permission(
        self,
        tool_name: str,
        parameters: Optional[dict[str, Any]] = None,
    ) -> PermissionDecision:
        """增强的权限检查

        Args:
            tool_name: 工具名称
            parameters: 工具参数

        Returns:
            PermissionDecision: 权限决策结果
        """
        parameters = parameters or {}

        # 1. 检查 BYPASS 模式 → 直接允许
        if self._enhanced_mode == PermissionMode.BYPASS:
            return PermissionDecision(
                allowed=True,
                reason="绕过权限模式: 允许所有调用",
                mode=self._convert_mode(self._enhanced_mode),
            )

        # 2. 检查只读工具 → 自动允许
        if is_read_only_tool(tool_name):
            return PermissionDecision(
                allowed=True,
                reason="只读工具: 自动允许",
                mode=self._convert_mode(self._enhanced_mode),
            )

        # 3. 检查命令黑名单 → 拒绝（优先级高于 PLAN 模式）
        if "command" in parameters:
            command = str(parameters["command"])
            is_denied, reason = self.blacklist.check(command)
            if is_denied:
                return PermissionDecision(
                    allowed=False,
                    reason=reason,
                    mode=self._convert_mode(self._enhanced_mode),
                )

        # 4. 检查 PLAN 模式写入操作 → 拒绝
        if self._enhanced_mode == PermissionMode.PLAN and is_plan_mode_write(tool_name):
            return PermissionDecision(
                allowed=False,
                reason=f"计划模式: 阻止写入操作 ({tool_name})",
                mode=self._convert_mode(self._enhanced_mode),
            )

        # 4. 检查命令黑名单 → 拒绝
        if "command" in parameters:
            command = str(parameters["command"])
            is_denied, reason = self.blacklist.check(command)
            if is_denied:
                return PermissionDecision(
                    allowed=False,
                    reason=reason,
                    mode=self._convert_mode(self._enhanced_mode),
                )

        # 5. 检查路径级规则
        file_path = parameters.get("file_path") or parameters.get("path")
        if file_path:
            allowed, reason = self.path_manager.check_path(str(file_path))
            if not allowed:
                # 明确拒绝
                return PermissionDecision(
                    allowed=False,
                    reason=reason,
                    mode=self._convert_mode(self._enhanced_mode),
                )
            elif reason is not None:
                # 明确允许（reason 不为 None 表示匹配到允许规则）
                return PermissionDecision(
                    allowed=True,
                    reason=reason,
                    mode=self._convert_mode(self._enhanced_mode),
                )
            # reason 为 None，继续检查

        # 6. 调用父类工具级检查
        return super().check_permission(tool_name, parameters)

    def set_mode(self, mode: PermissionMode) -> None:
        """设置权限模式

        Args:
            mode: 新的权限模式
        """
        old_mode = self._enhanced_mode
        self._enhanced_mode = mode

        # 同步更新父类模式
        super().set_mode(self._convert_mode(mode))

        logger.info(f"🔄 权限模式已更改: {old_mode.value} → {mode.value}")

    def add_path_rule(self, rule: PathRule) -> None:
        """添加路径规则

        Args:
            rule: 路径规则
        """
        self.path_manager.add_rule(rule)

    def remove_path_rule(self, rule_id: str) -> bool:
        """移除路径规则

        Args:
            rule_id: 规则ID

        Returns:
            bool: 是否成功移除
        """
        return self.path_manager.remove_rule(rule_id)

    def get_path_rules(self, enabled_only: bool = False) -> list[PathRule]:
        """获取所有路径规则

        Args:
            enabled_only: 是否只返回启用的规则

        Returns:
            list[PathRule]: 规则列表
        """
        return self.path_manager.get_rules(enabled_only)

    def add_denied_command(self, pattern: str) -> None:
        """添加命令黑名单模式

        Args:
            pattern: 命令模式
        """
        self.blacklist.add_pattern(pattern)

    def remove_denied_command(self, pattern: str) -> bool:
        """移除命令黑名单模式

        Args:
            pattern: 命令模式

        Returns:
            bool: 是否成功移除
        """
        return self.blacklist.remove_pattern(pattern)

    def get_denied_commands(self) -> list[str]:
        """获取所有命令黑名单模式

        Returns:
            list[str]: 模式列表
        """
        return self.blacklist.get_patterns()

    def _convert_mode(self, mode: PermissionMode) -> OldPermissionMode:
        """转换新权限模式为旧权限模式

        Args:
            mode: 新权限模式

        Returns:
            OldPermissionMode: 旧权限模式
        """
        mode_mapping = {
            PermissionMode.DEFAULT: OldPermissionMode.DEFAULT,
            PermissionMode.AUTO: OldPermissionMode.AUTO,
            PermissionMode.BYPASS: OldPermissionMode.BYPASS,
            PermissionMode.PLAN: OldPermissionMode.DEFAULT,  # PLAN 映射为 DEFAULT
        }
        return mode_mapping.get(mode, OldPermissionMode.DEFAULT)

    def get_config(self) -> PermissionConfig:
        """获取当前配置

        Returns:
            PermissionConfig: 权限配置对象
        """
        return PermissionConfig(
            mode=self._enhanced_mode,
            path_rules=self.path_manager.get_rules(),
            denied_commands=self.blacklist.get_patterns(),
            always_allow=list(self._always_allow.values()),
            always_deny=list(self._always_deny.values()),
        )


__all__ = [
    "PermissionConfig",
    "EnhancedPermissionChecker",
]
