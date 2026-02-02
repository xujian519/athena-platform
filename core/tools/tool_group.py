#!/usr/bin/env python3
"""
工具分组管理模块
Tool Group Management

提供工具组抽象,用于将相关工具组织在一起,
支持按任务类型自动激活相应的工具组。

作者: Athena平台团队
创建时间: 2026-01-20
版本: v1.0.0 "Phase 1"
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

from .base import ToolCategory, ToolDefinition, ToolRegistry

logger = logging.getLogger(__name__)


class GroupActivationRule(str, Enum):
    """工具组激活规则类型"""

    KEYWORD = "keyword"  # 基于关键词匹配
    TASK_TYPE = "task_type"  # 基于任务类型
    DOMAIN = "domain"  # 基于领域
    MANUAL = "manual"  # 手动激活
    ADAPTIVE = "adaptive"  # 自适应激活


@dataclass
class ActivationRule:
    """
    激活规则定义

    定义何时应该激活此工具组。
    """

    rule_type: GroupActivationRule
    keywords: list[str] = field(default_factory=list)
    task_types: list[str] = field(default_factory=list)
    domains: list[str] = field(default_factory=list)
    priority: int = 0  # 规则优先级 (数字越大优先级越高)

    # 自适应参数
    min_confidence: float = 0.7
    max_tools: int = 20

    def matches(
        self, task_description: str, task_type: str | None = None, domain: str | None = None
    ) -> bool:
        """
        检查任务是否匹配激活规则

        Args:
            task_description: 任务描述
            task_type: 任务类型
            domain: 领域

        Returns:
            是否匹配
        """
        if self.rule_type == GroupActivationRule.KEYWORD:
            desc_lower = task_description.lower()
            return any(kw.lower() in desc_lower for kw in self.keywords)

        elif self.rule_type == GroupActivationRule.TASK_TYPE:
            return task_type in self.task_types if task_type else False

        elif self.rule_type == GroupActivationRule.DOMAIN:
            return domain in self.domains if domain else False

        elif self.rule_type == GroupActivationRule.MANUAL:
            return False

        elif self.rule_type == GroupActivationRule.ADAPTIVE:
            # 自适应规则由ToolManager处理
            return True

        return False


@dataclass
class ToolGroupDef:
    """
    工具组定义

    描述一个工具组的元数据。
    """

    name: str  # 工具组唯一标识
    display_name: str  # 显示名称
    description: str  # 描述
    categories: list[ToolCategory]  # 包含的工具分类

    # 激活规则
    activation_rules: list[ActivationRule] = field(default_factory=list)

    # 工具列表 (可选,如果为空则从categories推断)
    tools: list[str] = field(default_factory=list)

    # 配置
    config: dict[str, Any] = field(default_factory=dict)

    # 元数据
    created_at: datetime = field(default_factory=datetime.now)
    version: str = "1.0.0"


class ToolGroup:
    """
    工具组

    管理一组相关的工具,支持激活/停用,并提供工具查询接口。
    """

    def __init__(self, definition: ToolGroupDef, registry: ToolRegistry):
        """
        初始化工具组

        Args:
            definition: 工具组定义
            registry: 工具注册中心
        """
        self.definition = definition
        self.registry = registry
        self._active = False
        self._active_tools: dict[str, ToolDefinition] = {}

        logger.info(f"🔧 工具组已创建: {definition.display_name} ({definition.name})")

    def activate(self) -> None:
        """激活工具组"""
        self._active = True
        self._reload_tools()
        logger.info(f"✅ 工具组已激活: {self.definition.display_name}")

    def deactivate(self) -> None:
        """停用工具组"""
        self._active = False
        self._active_tools.clear()
        logger.info(f"⏹️ 工具组已停用: {self.definition.display_name}")

    def is_active(self) -> bool:
        """检查工具组是否激活"""
        return self._active

    def get_tools(self) -> list[ToolDefinition]:
        """
        获取工具组中的所有工具

        Returns:
            工具定义列表
        """
        if not self._active:
            return []

        return list(self._active_tools.values())

    def get_tool(self, tool_id: str) -> ToolDefinition | None:
        """
        获取指定工具

        Args:
            tool_id: 工具ID

        Returns:
            工具定义,如果不存在返回None
        """
        return self._active_tools.get(tool_id)

    def has_tool(self, tool_id: str) -> bool:
        """检查是否包含指定工具"""
        return tool_id in self._active_tools

    def get_tool_count(self) -> int:
        """获取工具数量"""
        return len(self._active_tools)

    def _reload_tools(self) -> None:
        """从注册中心重新加载工具"""
        self._active_tools.clear()

        # 如果定义中指定了工具列表
        if self.definition.tools:
            for tool_id in self.definition.tools:
                tool = self.registry.get_tool(tool_id)
                if tool and tool.enabled:
                    self._active_tools[tool_id] = tool
        else:
            # 否则从分类中推断
            for category in self.definition.categories:
                tools = self.registry.find_by_category(category, enabled_only=True)
                for tool in tools:
                    self._active_tools[tool.tool_id] = tool

        logger.debug(f"   加载了 {len(self._active_tools)} 个工具 " f"(组: {self.definition.name})")

    def should_activate_for_task(
        self, task_description: str, task_type: str | None = None, domain: str | None = None
    ) -> bool:
        """
        判断是否应该为指定任务激活此工具组

        Args:
            task_description: 任务描述
            task_type: 任务类型
            domain: 领域

        Returns:
            是否应该激活
        """
        for rule in self.definition.activation_rules:
            if rule.matches(task_description, task_type, domain):
                logger.debug(
                    f"   规则匹配: {rule.rule_type.value} " f"(组: {self.definition.name})"
                )
                return True
        return False

    def get_statistics(self) -> dict[str, Any]:
        """
        获取工具组统计信息

        Returns:
            统计信息字典
        """
        tools = list(self._active_tools.values())

        total_calls = sum(t.performance.total_calls for t in tools)
        successful_calls = sum(t.performance.successful_calls for t in tools)
        success_rate = successful_calls / total_calls if total_calls > 0 else 0.0

        return {
            "group_name": self.definition.name,
            "display_name": self.definition.display_name,
            "active": self._active,
            "tool_count": len(tools),
            "total_calls": total_calls,
            "successful_calls": successful_calls,
            "success_rate": success_rate,
        }


__all__ = ["ActivationRule", "GroupActivationRule", "ToolGroup", "ToolGroupDef"]
