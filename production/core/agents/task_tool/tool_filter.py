from __future__ import annotations
"""
ToolFilter - 工具过滤器
实现工具过滤和权限控制，支持通配符。
"""

import fnmatch
import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)


class ToolFilter:
    """工具过滤器类

    负责根据代理配置过滤工具列表，支持通配符匹配。
    """

    def __init__(self, registry):
        """初始化ToolFilter

        Args:
            registry: SubagentRegistry实例
        """
        self._registry = registry
        logger.info("✅ ToolFilter初始化完成")

    def filter_tools(self, available_tools, agent_config):
        """过滤工具列表

        Args:
            available_tools: 可用工具列表
            agent_config: 代理配置

        Returns:
            过滤后的工具列表
        """
        # 如果允许列表为空，返回所有工具
        if not agent_config.allowed_tools:
            return list(available_tools)

        # 过滤工具
        filtered = []
        for tool in available_tools:
            if self.is_tool_allowed(tool, agent_config):
                filtered.append(tool)

        logger.debug(
            f"🔧 工具过滤: {len(available_tools)} -> {len(filtered)} "
            f"(代理: {agent_config.agent_type})"
        )

        return filtered

    def is_tool_allowed(self, tool_name, agent_config):
        """检查工具是否被允许

        Args:
            tool_name: 工具名称
            agent_config: 代理配置

        Returns:
            如果工具被允许返回True，否则返回False
        """
        # 如果允许列表为空，所有工具都被允许
        if not agent_config.allowed_tools:
            return True

        # 检查是否匹配任何允许的模式
        for pattern in agent_config.allowed_tools:
            if self._match_pattern(pattern, tool_name):
                return True

        return False

    def _match_pattern(self, pattern, tool_name):
        """匹配工具名称和模式（支持通配符）

        Args:
            pattern: 模式字符串（可以包含通配符*）
            tool_name: 工具名称

        Returns:
            如果匹配返回True，否则返回False
        """
        # 使用fnmatch进行通配符匹配
        return fnmatch.fnmatch(tool_name, pattern)

    def get_allowed_tools_for_agent(self, agent_config):
        """获取代理的允许工具列表

        Args:
            agent_config: 代理配置

        Returns:
            允许的工具列表
        """
        return list(agent_config.allowed_tools)


__all__ = ["ToolFilter"]
