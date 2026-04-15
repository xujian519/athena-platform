#!/usr/bin/env python3
from __future__ import annotations
"""
增强版工具管理器
Enhanced Tool Manager

支持工具分组管理、动态激活和智能工具选择。

作者: Athena平台团队
创建时间: 2026-01-20
版本: v1.0.0 "Phase 1"
"""

import logging
from dataclasses import dataclass
from typing import Any

from .base import ToolDefinition, ToolRegistry, get_global_registry
from .tool_group import GroupActivationRule, ToolGroup, ToolGroupDef

logger = logging.getLogger(__name__)


@dataclass
class ToolSelectionResult:
    """工具选择结果"""

    tool: ToolDefinition
    group_name: str
    confidence: float
    reason: str


class ToolManager:
    """
    增强版工具管理器

    提供工具分组管理、动态激活和智能选择功能。
    """

    def __init__(self, registry: ToolRegistry | None = None):
        """
        初始化工具管理器

        Args:
            registry: 工具注册中心 (默认使用全局注册中心)
        """
        self.registry = registry or get_global_registry()
        self.groups: dict[str, ToolGroup] = {}
        self.active_group: str | None = None

        # 单组激活模式 (默认True)
        self._single_group_mode = True

        logger.info("🔧 ToolManager初始化完成")

    def register_group(self, definition: ToolGroupDef) -> ToolGroup:
        """
        注册工具组

        Args:
            definition: 工具组定义

        Returns:
            ToolGroup实例
        """
        if definition.name in self.groups:
            logger.warning(f"⚠️ 工具组已存在: {definition.name}")

        group = ToolGroup(definition, self.registry)
        self.groups[definition.name] = group

        logger.info(f"✅ 工具组已注册: {definition.display_name}")
        return group

    def get_group(self, group_name: str) -> ToolGroup | None:
        """
        获取工具组

        Args:
            group_name: 工具组名称

        Returns:
            ToolGroup实例,如果不存在返回None
        """
        return self.groups.get(group_name)

    def activate_group(self, group_name: str, deactivate_others: bool | None = None) -> bool:
        """
        激活工具组

        Args:
            group_name: 工具组名称
            deactivate_others: 是否停用其他组 (默认使用单组模式设置)

        Returns:
            是否成功激活
        """
        group = self.get_group(group_name)
        if not group:
            logger.error(f"❌ 工具组不存在: {group_name}")
            return False

        # 单组激活模式
        if deactivate_others is None:
            deactivate_others = self._single_group_mode

        if deactivate_others and group_name != self.active_group:
            # 停用所有其他组
            for name, g in self.groups.items():
                if name != group_name and g.is_active():
                    g.deactivate()

        # 激活目标组
        group.activate()
        self.active_group = group_name

        logger.info(
            f"✅ 工具组已激活: {group.definition.display_name} "
            f"(工具数: {group.get_tool_count()})"
        )
        return True

    def deactivate_group(self, group_name: str) -> bool:
        """
        停用工具组

        Args:
            group_name: 工具组名称

        Returns:
            是否成功停用
        """
        group = self.get_group(group_name)
        if not group:
            logger.error(f"❌ 工具组不存在: {group_name}")
            return False

        group.deactivate()

        if self.active_group == group_name:
            self.active_group = None

        logger.info(f"⏹️ 工具组已停用: {group.definition.display_name}")
        return True

    def deactivate_all_groups(self) -> None:
        """停用所有工具组"""
        for group in self.groups.values():
            if group.is_active():
                group.deactivate()
        self.active_group = None
        logger.info("⏹️ 所有工具组已停用")

    async def auto_activate_group_for_task(
        self, task_description: str, task_type: str | None = None, domain: str | None = None
    ) -> str | None:
        """
        为任务自动激活最合适的工具组

        Args:
            task_description: 任务描述
            task_type: 任务类型
            domain: 领域

        Returns:
            激活的工具组名称,如果没有合适的返回None
        """
        logger.info("🔍 为任务自动选择工具组...")
        logger.debug(f"   任务描述: {task_description[:100]}...")
        if task_type:
            logger.debug(f"   任务类型: {task_type}")
        if domain:
            logger.debug(f"   领域: {domain}")

        # 收集所有匹配的工具组
        matched_groups = []
        for group_name, group in self.groups.items():
            if group.should_activate_for_task(task_description, task_type, domain):
                # 计算匹配分数
                score = self._calculate_group_match_score(
                    group, task_description, task_type, domain
                )
                matched_groups.append((score, group_name, group))

        # 按分数排序
        matched_groups.sort(key=lambda x: x[0], reverse=True)

        if not matched_groups:
            logger.warning("⚠️ 没有找到匹配的工具组,使用默认组")
            # 尝试激活通用组
            general_group = self.get_group("general")
            if general_group:
                self.activate_group("general")
                return "general"
            return None

        # 选择分数最高的工具组
        best_score, best_name, best_group = matched_groups[0]

        # 检查置信度
        if best_score < 0.5:
            logger.warning(f"⚠️ 最佳工具组匹配度较低: {best_score:.2f}")
            # 仍然激活,但记录警告

        # 激活最佳工具组
        if self.activate_group(best_name):
            logger.info(
                f"✅ 自动激活工具组: {best_group.definition.display_name} "
                f"(匹配度: {best_score:.2%})"
            )
            return best_name

        return None

    def _calculate_group_match_score(
        self,
        group: ToolGroup,
        task_description: str,
        task_type: str | None = None,
        domain: str | None = None,
    ) -> float:
        """
        计算工具组与任务的匹配分数

        Args:
            group: 工具组
            task_description: 任务描述
            task_type: 任务类型
            domain: 领域

        Returns:
            匹配分数 (0-1)
        """
        score = 0.0
        total_weight = 0.0

        # 检查每个激活规则
        for rule in group.definition.activation_rules:
            weight = 1.0  # 默认权重
            rule_score = 0.0

            if rule.rule_type == GroupActivationRule.KEYWORD:
                # 关键词匹配
                desc_lower = task_description.lower()
                matched = sum(1 for kw in rule.keywords if kw.lower() in desc_lower)
                if matched > 0:
                    rule_score = min(matched / len(rule.keywords), 1.0)
                    weight = rule.priority / 10.0  # 优先级作为权重

            elif rule.rule_type == GroupActivationRule.TASK_TYPE:
                # 任务类型匹配
                if task_type and task_type in rule.task_types:
                    rule_score = 1.0
                    weight = rule.priority / 10.0

            elif rule.rule_type == GroupActivationRule.DOMAIN:
                # 领域匹配
                if domain and domain in rule.domains:
                    rule_score = 1.0
                    weight = rule.priority / 10.0

            score += rule_score * weight
            total_weight += weight

        return score / total_weight if total_weight > 0 else 0.0

    def get_all_active_tools(self) -> list[ToolDefinition]:
        """
        获取所有激活的工具

        Returns:
            工具定义列表
        """
        if self._single_group_mode and self.active_group:
            group = self.get_group(self.active_group)
            return group.get_tools() if group else []

        # 多组激活模式
        tools = []
        for group in self.groups.values():
            if group.is_active():
                tools.extend(group.get_tools())

        # 去重
        seen = set()
        unique_tools = []
        for tool in tools:
            if tool.tool_id not in seen:
                seen.add(tool.tool_id)
                unique_tools.append(tool)

        return unique_tools

    async def select_best_tool(
        self, task_description: str, task_type: str | None = None, domain: str | None = None
    ) -> ToolSelectionResult:
        """
        为任务选择最佳工具

        Args:
            task_description: 任务描述
            task_type: 任务类型
            domain: 领域

        Returns:
            工具选择结果
        """
        # 先确保有激活的工具组
        if not self.active_group:
            await self.auto_activate_group_for_task(task_description, task_type, domain)

        # 获取所有可用工具
        available_tools = self.get_all_active_tools()

        if not available_tools:
            return ToolSelectionResult(
                tool=None, group_name=None, confidence=0.0, reason="没有可用的工具"
            )

        # 简单实现:选择优先级最高、成功率最高的工具
        # 后续可以集成更复杂的选择算法
        best_tool = max(
            available_tools, key=lambda t: (t.priority.value, t.performance.success_rate)
        )

        group_name = self.active_group or "unknown"
        confidence = best_tool.performance.success_rate

        return ToolSelectionResult(
            tool=best_tool,
            group_name=group_name,
            confidence=confidence,
            reason=f"从工具组 {group_name} 中选择最佳工具",
        )

    def get_statistics(self) -> dict[str, Any]:
        """
        获取工具管理器统计信息

        Returns:
            统计信息字典
        """
        total_groups = len(self.groups)
        active_groups = sum(1 for g in self.groups.values() if g.is_active())

        group_stats = []
        for group in self.groups.values():
            group_stats.append(group.get_statistics())

        total_tools = len(self.get_all_active_tools())

        return {
            "total_groups": total_groups,
            "active_groups": active_groups,
            "active_group": self.active_group,
            "total_active_tools": total_tools,
            "groups": group_stats,
        }

    def set_single_group_mode(self, enabled: bool) -> None:
        """
        设置单组激活模式

        Args:
            enabled: 是否启用单组模式
        """
        self._single_group_mode = enabled
        logger.info(f"🔧 单组激活模式: {'启用' if enabled else '禁用'}")


# 便捷函数
def get_tool_manager() -> ToolManager:
    """获取全局工具管理器"""
    return ToolManager()


__all__ = ["ToolManager", "ToolSelectionResult", "get_tool_manager"]
