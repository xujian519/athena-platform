"""
路径级权限规则管理

支持基于文件路径的权限控制，使用 glob 模式匹配。

作者: Athena平台团队
创建时间: 2026-04-20
"""
from __future__ import annotations

import fnmatch
import logging
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class PathRule:
    """路径级权限规则

    定义基于文件路径的允许或拒绝规则。

    Attributes:
        rule_id: 规则唯一标识
        pattern: 路径模式 (支持 glob 通配符: **, *, ?)
        allow: True=允许, False=拒绝
        priority: 优先级 (数值越大优先级越高)
        reason: 规则原因说明
        enabled: 是否启用该规则
    """

    rule_id: str
    pattern: str
    allow: bool
    priority: int = 0
    reason: str = ""
    enabled: bool = True

    def __post_init__(self):
        """初始化后处理"""
        # 规范化路径模式
        self.pattern = str(Path(self.pattern).expanduser().resolve())

        # 编译正则表达式（如果使用 ** 通配符）
        self._regex_pattern: str | None = None
        if "**" in self.pattern:
            # ** 表示递归匹配，转换为前缀匹配
            self._regex_pattern = self.pattern.replace("**", "")


class PathRuleManager:
    """路径规则管理器

    管理路径级权限规则，提供路径匹配检查功能。
    """

    def __init__(self, rules: list[PathRule] | None = None):
        """初始化路径规则管理器

        Args:
            rules: 初始规则列表
        """
        self._rules: dict[str, PathRule] = {}

        for rule in rules or []:
            self._rules[rule.rule_id] = rule

        logger.info(f"🛣️ 路径规则管理器初始化 (规则数: {len(self._rules)})")

    def add_rule(self, rule: PathRule) -> None:
        """添加路径规则

        Args:
            rule: 路径规则
        """
        self._rules[rule.rule_id] = rule
        logger.info(
            f"✅ 路径规则已添加: {rule.rule_id} - {rule.pattern} "
            f"({'允许' if rule.allow else '拒绝'}, 优先级: {rule.priority})"
        )

    def remove_rule(self, rule_id: str) -> bool:
        """移除路径规则

        Args:
            rule_id: 规则ID

        Returns:
            bool: 是否成功移除
        """
        if rule_id in self._rules:
            del self._rules[rule_id]
            logger.info(f"✅ 路径规则已移除: {rule_id}")
            return True
        return False

    def get_rule(self, rule_id: str) -> PathRule | None:
        """获取路径规则

        Args:
            rule_id: 规则ID

        Returns:
            PathRule | None: 规则对象，不存在返回 None
        """
        return self._rules.get(rule_id)

    def get_rules(self, enabled_only: bool = False) -> list[PathRule]:
        """获取所有规则

        Args:
            enabled_only: 是否只返回启用的规则

        Returns:
            list[PathRule]: 规则列表（按优先级降序）
        """
        rules = list(self._rules.values())

        if enabled_only:
            rules = [r for r in rules if r.enabled]

        # 按优先级降序排序
        return sorted(rules, key=lambda r: r.priority, reverse=True)

    def check_path(self, file_path: str) -> tuple[bool, str | None]:
        """检查文件路径权限

        按优先级顺序检查规则，返回第一个匹配规则的结果。

        Args:
            file_path: 文件路径

        Returns:
            tuple[bool, str | None]: (是否允许, 原因)
            - True: 允许访问
            - False: 拒绝访问
            - 原因: None 表示无匹配规则，需要继续检查
        """
        # 规范化文件路径
        try:
            normalized_path = str(Path(file_path).expanduser().resolve())
        except (OSError, ValueError) as e:
            logger.warning(f"⚠️ 无法规范化路径: {file_path} - {e}")
            return False, f"无效的文件路径: {file_path}"

        # 按优先级排序规则
        sorted_rules = self.get_rules(enabled_only=True)

        # 遍历规则
        for rule in sorted_rules:
            if self._match_path(normalized_path, rule.pattern):
                # 匹配到规则
                if rule.allow:
                    logger.debug(
                        f"✅ 路径匹配允许规则: {normalized_path} → {rule.rule_id}"
                    )
                    return True, rule.reason or f"匹配允许规则: {rule.rule_id}"
                else:
                    logger.debug(
                        f"🚫 路径匹配拒绝规则: {normalized_path} → {rule.rule_id}"
                    )
                    return False, rule.reason or f"匹配拒绝规则: {rule.rule_id}"

        # 无匹配规则
        logger.debug(f"⏭️ 路径无匹配规则: {normalized_path}")
        return True, None  # 允许继续检查（不拒绝）

    def _match_path(self, file_path: str, pattern: str) -> bool:
        """匹配文件路径模式

        支持的通配符:
        - **: 递归匹配任意子目录
        - *: 匹配单层任意字符（不包括 /）
        - ?: 匹配单个字符

        Examples:
            - /Users/xujian/Athena工作平台/** → 匹配项目下所有文件
            - /etc/* → 匹配 /etc 下的直接文件和目录
            - /tmp/**/*.tmp → 匹配 /tmp 下所有 .tmp 文件
            - /Users/*/Documents → 匹配任意用户下的 Documents

        Args:
            file_path: 规范化的文件路径
            pattern: 路径模式（已规范化）

        Returns:
            bool: 是否匹配
        """
        # 处理 ** 递归通配符
        if "**" in pattern:
            # 移除 **，进行前缀匹配
            prefix = pattern.replace("**", "")
            if file_path.startswith(prefix):
                return True

        # 处理单层 * 通配符（不包括 /）
        # 将模式按 / 分割，检查每一层
        pattern_parts = pattern.split("/")
        path_parts = file_path.split("/")

        # 如果层数不同，肯定不匹配
        if len(pattern_parts) != len(path_parts):
            return False

        # 逐层匹配
        for pattern_part, path_part in zip(pattern_parts, path_parts):
            # 如果是 *，匹配任意非空字符串
            if pattern_part == "*":
                if not path_part:  # * 不匹配空字符串
                    return False
            # 如果包含 * 但不是纯粹的 *，使用 fnmatch
            elif "*" in pattern_part or "?" in pattern_part:
                if not fnmatch.fnmatch(path_part, pattern_part):
                    return False
            # 普通字符串，必须完全匹配
            elif pattern_part != path_part:
                return False

        return True

    def set_rule_enabled(self, rule_id: str, enabled: bool) -> bool:
        """设置规则启用状态

        Args:
            rule_id: 规则ID
            enabled: 是否启用

        Returns:
            bool: 是否成功设置
        """
        rule = self._rules.get(rule_id)
        if rule:
            rule.enabled = enabled
            logger.info(
                f"🔄 规则状态已更新: {rule_id} → {'启用' if enabled else '禁用'}"
            )
            return True
        return False

    def clear_rules(self) -> None:
        """清除所有规则"""
        count = len(self._rules)
        self._rules.clear()
        logger.info(f"🗑️ 已清除所有路径规则 (共 {count} 条)")


# ========================================
# 预定义路径规则
# ========================================

DEFAULT_PATH_RULES = [
    PathRule(
        rule_id="project-dir",
        pattern="/Users/xujian/Athena工作平台/**",
        allow=True,
        priority=50,
        reason="项目目录允许访问",
    ),
    PathRule(
        rule_id="system-dir",
        pattern="/etc/*",
        allow=False,
        priority=100,
        reason="系统目录禁止访问",
    ),
    PathRule(
        rule_id="usr-dir",
        pattern="/usr/*",
        allow=False,
        priority=100,
        reason="系统目录禁止访问",
    ),
    PathRule(
        rule_id="temp-dir",
        pattern="/tmp/**",
        allow=True,
        priority=10,
        reason="临时目录允许访问",
    ),
    PathRule(
        rule_id="home-dir",
        pattern="/Users/xujian/**",
        allow=True,
        priority=50,
        reason="用户主目录允许访问",
    ),
]


__all__ = [
    "PathRule",
    "PathRuleManager",
    "DEFAULT_PATH_RULES",
]
