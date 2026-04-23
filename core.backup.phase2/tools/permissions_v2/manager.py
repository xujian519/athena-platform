"""
全局权限管理器

整合新旧权限系统，提供统一的权限管理接口。

作者: Athena平台团队
创建时间: 2026-04-20
"""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from .modes import PermissionMode
from .path_rules import PathRule, PathRuleManager, DEFAULT_PATH_RULES
from .command_blacklist import CommandBlacklist
from .checker import EnhancedPermissionChecker, PermissionConfig

logger = logging.getLogger(__name__)


class GlobalPermissionManager:
    """全局权限管理器

    单例模式，提供全局统一的权限管理。

    Features:
    - 单例模式，全局唯一实例
    - 支持运行时权限模式切换
    - 整合路径规则、命令黑名单、工具级规则
    - 支持从配置文件加载
    - 线程安全
    """

    _instance: "GlobalPermissionManager | None" = None
    _initialized: bool = False

    def __new__(cls) -> "GlobalPermissionManager":
        """实现单例模式"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        """初始化全局权限管理器"""
        if GlobalPermissionManager._initialized:
            return

        self._checker: EnhancedPermissionChecker | None = None
        self._config_path: Path | None = None
        GlobalPermissionManager._initialized = True

        logger.info("🌐 全局权限管理器已创建")

    def initialize(
        self,
        mode: PermissionMode = PermissionMode.DEFAULT,
        config_path: str | None = None,
        path_rules: list[PathRule] | None = None,
        denied_commands: list[str] | None = None,
    ) -> None:
        """初始化权限检查器

        Args:
            mode: 权限模式
            config_path: 配置文件路径（可选）
            path_rules: 路径规则列表（可选）
            denied_commands: 命令黑名单（可选）
        """
        self._config_path = Path(config_path) if config_path else None

        # 如果提供了配置文件，从配置文件加载
        if self._config_path and self._config_path.exists():
            self._load_from_config(self._config_path)
        else:
            # 使用默认配置
            self._checker = EnhancedPermissionChecker(
                mode=mode,
                path_rules=path_rules,
                denied_commands=denied_commands,
            )

        logger.info(f"✅ 全局权限管理器已初始化 (模式: {mode.value})")

    def check_permission(
        self,
        tool_name: str,
        parameters: dict[str, Any] | None = None,
    ) -> tuple[bool, str | None]:
        """检查工具调用权限

        Args:
            tool_name: 工具名称
            parameters: 工具参数

        Returns:
            tuple[bool, str | None]: (是否允许, 原因)
        """
        if self._checker is None:
            # 未初始化，使用默认配置
            self.initialize()

        decision = self._checker.check_permission(tool_name, parameters)
        return decision.allowed, decision.reason

    def set_mode(self, mode: PermissionMode) -> None:
        """设置权限模式

        Args:
            mode: 新的权限模式
        """
        if self._checker is None:
            self.initialize()

        self._checker.set_mode(mode)
        logger.info(f"🔄 全局权限模式已切换: {mode.value}")

    def get_mode(self) -> PermissionMode:
        """获取当前权限模式

        Returns:
            PermissionMode: 当前权限模式
        """
        if self._checker is None:
            self.initialize()
        return self._checker._enhanced_mode

    def add_path_rule(self, rule: PathRule) -> None:
        """添加路径规则

        Args:
            rule: 路径规则
        """
        if self._checker is None:
            self.initialize()
        self._checker.add_path_rule(rule)

    def remove_path_rule(self, rule_id: str) -> bool:
        """移除路径规则

        Args:
            rule_id: 规则ID

        Returns:
            bool: 是否成功移除
        """
        if self._checker is None:
            self.initialize()
        return self._checker.remove_path_rule(rule_id)

    def add_denied_command(self, pattern: str) -> None:
        """添加命令黑名单模式

        Args:
            pattern: 命令模式
        """
        if self._checker is None:
            self.initialize()
        self._checker.add_denied_command(pattern)

    def remove_denied_command(self, pattern: str) -> bool:
        """移除命令黑名单模式

        Args:
            pattern: 命令模式

        Returns:
            bool: 是否成功移除
        """
        if self._checker is None:
            self.initialize()
        return self._checker.remove_denied_command(pattern)

    def get_config(self) -> PermissionConfig:
        """获取当前配置

        Returns:
            PermissionConfig: 权限配置对象
        """
        if self._checker is None:
            self.initialize()
        return self._checker.get_config()

    def save_config(self, path: str | None = None) -> None:
        """保存当前配置到文件

        Args:
            path: 保存路径（可选，默认使用初始化时的路径）
        """
        import yaml

        config = self.get_config()
        save_path = Path(path) if path else self._config_path

        if not save_path:
            raise ValueError("未指定配置文件路径")

        # 转换为可序列化的字典
        config_dict = {
            "mode": config.mode.value,
            "path_rules": [
                {
                    "rule_id": rule.rule_id,
                    "pattern": rule.pattern,
                    "allow": rule.allow,
                    "priority": rule.priority,
                    "reason": rule.reason,
                    "enabled": rule.enabled,
                }
                for rule in config.path_rules
            ],
            "denied_commands": config.denied_commands,
        }

        save_path.parent.mkdir(parents=True, exist_ok=True)
        with open(save_path, "w", encoding="utf-8") as f:
            yaml.dump(config_dict, f, allow_unicode=True, default_flow_style=False)

        logger.info(f"💾 配置已保存: {save_path}")

    def _load_from_config(self, path: Path) -> None:
        """从配置文件加载

        Args:
            path: 配置文件路径
        """
        import yaml

        with open(path, "r", encoding="utf-8") as f:
            config_dict = yaml.safe_load(f)

        # 解析权限模式
        mode_str = config_dict.get("mode", "default")
        mode = PermissionMode(mode_str)

        # 解析路径规则
        path_rules = []
        for rule_dict in config_dict.get("path_rules", []):
            path_rules.append(
                PathRule(
                    rule_id=rule_dict["rule_id"],
                    pattern=rule_dict["pattern"],
                    allow=rule_dict["allow"],
                    priority=rule_dict.get("priority", 0),
                    reason=rule_dict.get("reason", ""),
                    enabled=rule_dict.get("enabled", True),
                )
            )

        # 解析命令黑名单
        denied_commands = config_dict.get("denied_commands")

        # 创建检查器
        self._checker = EnhancedPermissionChecker(
            mode=mode,
            path_rules=path_rules,
            denied_commands=denied_commands,
        )

        logger.info(f"📥 配置已加载: {path}")


# ========================================
# 全局实例
# ========================================

_global_manager: GlobalPermissionManager | None = None


def get_global_permission_manager() -> GlobalPermissionManager:
    """获取全局权限管理器实例

    Returns:
        GlobalPermissionManager: 全局权限管理器单例
    """
    global _global_manager
    if _global_manager is None:
        _global_manager = GlobalPermissionManager()
    return _global_manager


__all__ = [
    "GlobalPermissionManager",
    "get_global_permission_manager",
]
