"""
命令黑名单检查

检查危险命令，防止系统破坏操作。

作者: Athena平台团队
创建时间: 2026-04-20
"""
from __future__ import annotations

import logging
import re
from typing import Any

from .modes import DENIED_COMMANDS

logger = logging.getLogger(__name__)


class CommandBlacklist:
    """命令黑名单检查器

    检查命令是否包含危险操作，防止系统破坏。
    """

    def __init__(self, denied_patterns: list[str] | None = None):
        """初始化命令黑名单检查器

        Args:
            denied_patterns: 拒绝的命令模式列表（可选，默认使用 DENIED_COMMANDS）
        """
        self._patterns: list[str] = denied_patterns or DENIED_COMMANDS.copy()
        self._compiled_patterns: list[re.Pattern[str]] = []

        # 预编译正则表达式
        for pattern in self._patterns:
            try:
                # 转换为不区分大小写的正则表达式
                # 转义特殊字符，但保留关键字匹配
                escaped = re.escape(pattern)
                # 使用不区分大小写的匹配
                regex = re.compile(escaped, re.IGNORECASE)
                self._compiled_patterns.append(regex)
            except re.error as e:
                logger.warning(f"⚠️ 无法编译黑名单模式: {pattern} - {e}")

        logger.info(f"🚫 命令黑名单初始化 (模式数: {len(self._patterns)})")

    def check(self, command: str) -> tuple[bool, str | None]:
        """检查命令是否在黑名单中

        Args:
            command: 要检查的命令

        Returns:
            tuple[bool, str | None]: (是否被拒绝, 拒绝原因)
            - True: 命令被拒绝
            - False: 命令未被拒绝
            - 原因: 拒绝原因描述
        """
        if not command:
            return False, None

        command_stripped = command.strip()

        # 遍历所有黑名单模式
        for i, pattern in enumerate(self._patterns):
            pattern_lower = pattern.lower()

            # 检查命令是否包含黑名单关键词
            if pattern_lower in command_stripped.lower():
                reason = f"命令包含黑名单关键词: {pattern}"
                logger.warning(f"🚫 命令被拒绝: {command_stripped[:100]} - {reason}")
                return True, reason

            # 使用编译的正则表达式进行更精确的匹配
            if i < len(self._compiled_patterns):
                regex = self._compiled_patterns[i]
                if regex.search(command_stripped):
                    reason = f"命令匹配黑名单模式: {pattern}"
                    logger.warning(f"🚫 命令被拒绝: {command_stripped[:100]} - {reason}")
                    return True, reason

        # 未匹配到黑名单
        return False, None

    def add_pattern(self, pattern: str) -> None:
        """添加黑名单模式

        Args:
            pattern: 要添加的模式
        """
        self._patterns.append(pattern)

        # 编译正则表达式
        try:
            escaped = re.escape(pattern)
            regex = re.compile(escaped, re.IGNORECASE)
            self._compiled_patterns.append(regex)
            logger.info(f"✅ 黑名单模式已添加: {pattern}")
        except re.error as e:
            logger.warning(f"⚠️ 无法编译黑名单模式: {pattern} - {e}")

    def remove_pattern(self, pattern: str) -> bool:
        """移除黑名单模式

        Args:
            pattern: 要移除的模式

        Returns:
            bool: 是否成功移除
        """
        try:
            index = self._patterns.index(pattern)
            self._patterns.pop(index)
            # 移除对应的编译模式
            if index < len(self._compiled_patterns):
                self._compiled_patterns.pop(index)
            logger.info(f"✅ 黑名单模式已移除: {pattern}")
            return True
        except ValueError:
            logger.warning(f"⚠️ 黑名单模式不存在: {pattern}")
            return False

    def get_patterns(self) -> list[str]:
        """获取所有黑名单模式

        Returns:
            list[str]: 模式列表
        """
        return self._patterns.copy()

    def clear_patterns(self) -> None:
        """清除所有黑名单模式"""
        count = len(self._patterns)
        self._patterns.clear()
        self._compiled_patterns.clear()
        logger.info(f"🗑️ 已清除所有黑名单模式 (共 {count} 条)")


# ========================================
# 辅助函数
# ========================================

def check_denied_command(command: str) -> tuple[bool, str | None]:
    """检查命令是否被拒绝（便捷函数）

    Args:
        command: 要检查的命令

    Returns:
        tuple[bool, str | None]: (是否被拒绝, 拒绝原因)
    """
    blacklist = CommandBlacklist()
    return blacklist.check(command)


__all__ = [
    "CommandBlacklist",
    "check_denied_command",
]
