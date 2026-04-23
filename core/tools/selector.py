#!/usr/bin/env python3
from __future__ import annotations
"""
工具选择器

基于任务需求智能选择最合适的工具。

Author: Athena平台团队
Created: 2026-01-20
Version: v1.0.0
"""

import logging
from dataclasses import dataclass
from enum import Enum
from typing import Any

from .base import ToolCategory, ToolDefinition, ToolPriority, ToolRegistry

logger = logging.getLogger(__name__)


class SelectionStrategy(Enum):
    """工具选择策略"""

    # 基于成功率选择
    SUCCESS_RATE = "success_rate"

    # 基于性能选择(执行时间)
    PERFORMANCE = "performance"

    # 基于优先级选择
    PRIORITY = "priority"

    # 平衡模式(综合评分)
    BALANCED = "balanced"

    # 随机选择(用于探索)
    RANDOM = "random"


@dataclass
class SelectionScore:
    """
    工具选择评分

    记录工具被选择的各项评分。
    """

    tool: ToolDefinition
    success_score: float = 0.0  # 成功率评分 (0-1)
    performance_score: float = 0.0  # 性能评分 (0-1)
    priority_score: float = 0.0  # 优先级评分 (0-1)
    relevance_score: float = 0.0  # 相关性评分 (0-1)
    total_score: float = 0.0  # 总评分 (0-1)

    def calculate_total(self, weights: dict[str, float] | None = None) -> Any:
        """
        计算总评分

        Args:
            weights: 各项评分的权重,默认平衡权重
        """
        if weights is None:
            weights = {"success": 0.3, "performance": 0.2, "priority": 0.2, "relevance": 0.3}

        self.total_score = (
            self.success_score * weights.get("success", 0.3)
            + self.performance_score * weights.get("performance", 0.2)
            + self.priority_score * weights.get("priority", 0.2)
            + self.relevance_score * weights.get("relevance", 0.3)
        )


class ToolSelector:
    """
    工具选择器(性能优化版)

    根据任务需求智能选择最合适的工具。

    优化内容:
    - 使用类级常量避免重复创建
    - 添加缓存减少重复计算
    - 预计算优先级映射
    """

    # ⚡ 性能优化:类级常量
    PRIORITY_ORDER = {
        ToolPriority.CRITICAL: 4,
        ToolPriority.HIGH: 3,
        ToolPriority.MEDIUM: 2,
        ToolPriority.LOW: 1,
    }

    PRIORITY_SCORES = {
        ToolPriority.CRITICAL: 1.0,
        ToolPriority.HIGH: 0.8,
        ToolPriority.MEDIUM: 0.5,
        ToolPriority.LOW: 0.2,
    }

    def __init__(
        self,
        registry: ToolRegistry,
        strategy: SelectionStrategy = SelectionStrategy.BALANCED,
        min_success_rate: float = 0.7,
    ):
        """
        初始化工具选择器

        Args:
            registry: 工具注册中心
            strategy: 选择策略
            min_success_rate: 最低成功率要求
        """
        self.registry = registry
        self.strategy = strategy
        self.min_success_rate = min_success_rate

        # ⚡ 性能优化:缓存
        self._priority_cache: dict[ToolPriority, int] = {}
        self._score_cache: dict[ToolPriority, float] = {}

        # 预填充缓存
        for priority in ToolPriority:
            self._priority_cache[priority] = self.PRIORITY_ORDER[priority]
            self._score_cache[priority] = self.PRIORITY_SCORES[priority]

        logger.info(
            f"🎯 ToolSelector初始化 (策略: {strategy.value}, " f"最低成功率: {min_success_rate})"
        )

    async def select_tool(
        self,
        task_type: str,
        domain: str,
        input_data: Optional[dict[str, Any]] = None,
        category: ToolCategory | None = None,
        exclude_tools: Optional[list[str]] = None,
    ) -> ToolDefinition | None:
        """
        为单个任务选择最佳工具

        Args:
            task_type: 任务类型
            domain: 任务领域
            input_data: 输入数据 (可选)
            category: 指定工具分类 (可选)
            exclude_tools: 排除的工具ID列表

        Returns:
            最佳工具,如果没有找到返回None
        """
        # 查找候选工具
        candidates = await self._find_candidates(
            task_type=task_type, domain=domain, category=category, exclude_tools=exclude_tools or []
        )

        if not candidates:
            logger.warning(f"⚠️ 没有找到合适的工具: task_type={task_type}, domain={domain}")
            return None

        # 过滤成功率
        qualified = [t for t in candidates if t.get_success_rate() >= self.min_success_rate]

        if not qualified:
            logger.warning(
                f"⚠️ 没有找到成功率达标(>{self.min_success_rate})的工具,"
                f"将选择成功率最高的候选工具"
            )
            qualified = candidates

        # 根据策略选择
        selected_tool = await self._select_by_strategy(qualified, self.strategy)

        if selected_tool:
            logger.info(
                f"✅ 工具已选择: {selected_tool.name} "
                f"(成功率: {selected_tool.get_success_rate():.2%}, "
                f"优先级: {selected_tool.priority.value})"
            )

        return selected_tool

    async def select_tools(
        self,
        task_type: str,
        domain: str,
        max_tools: int = 3,
        input_data: Optional[dict[str, Any]] = None,
        category: ToolCategory | None = None,
        exclude_tools: Optional[list[str]] = None,
    ) -> list[ToolDefinition]:
        """
        为任务选择多个工具(Top-K)

        Args:
            task_type: 任务类型
            domain: 任务领域
            max_tools: 最多返回工具数
            input_data: 输入数据
            category: 指定工具分类
            exclude_tools: 排除的工具ID列表

        Returns:
            工具列表,按评分排序
        """
        # 查找候选工具
        candidates = await self._find_candidates(
            task_type=task_type, domain=domain, category=category, exclude_tools=exclude_tools or []
        )

        if not candidates:
            return []

        # 计算评分
        scored_tools = await self._score_tools(candidates, task_type, domain)

        # 按评分排序
        scored_tools.sort(key=lambda s: s.total_score, reverse=True)

        # 返回Top-K
        selected = [s.tool for s in scored_tools[:max_tools]]

        logger.info(f"✅ 已选择{len(selected)}个工具: " f"{[t.name for t in selected]}")

        return selected

    async def _find_candidates(
        self,
        task_type: str,
        domain: str,
        category: ToolCategory | None = None,
        exclude_tools: Optional[list[str]] = None,
    ) -> list[ToolDefinition]:
        """
        查找候选工具

        Args:
            task_type: 任务类型
            domain: 任务领域
            category: 指定分类
            exclude_tools: 排除的工具ID

        Returns:
            候选工具列表
        """
        # 基础搜索:按领域
        candidates = self.registry.find_by_domain(domain)

        # 如果指定了分类,进一步过滤
        if category:
            category_tools = self.registry.find_by_category(category)
            candidate_ids = {t.tool_id for t in candidates}
            candidates = [t for t in category_tools if t.tool_id in candidate_ids]

        # 过滤匹配任务类型的工具
        candidates = [t for t in candidates if t.matches_task_type(task_type)]

        # 排除指定工具
        if exclude_tools:
            candidates = [t for t in candidates if t.tool_id not in exclude_tools]

        return candidates

    async def _select_by_strategy(
        self, candidates: list[ToolDefinition], strategy: SelectionStrategy
    ) -> ToolDefinition | None:
        """
        根据策略选择工具(性能优化版)

        Args:
            candidates: 候选工具列表
            strategy: 选择策略

        Returns:
            选中的工具
        """
        if not candidates:
            return None

        if strategy == SelectionStrategy.SUCCESS_RATE:
            # 按成功率排序
            return max(candidates, key=lambda t: t.get_success_rate())

        elif strategy == SelectionStrategy.PERFORMANCE:
            # 按执行时间排序(越短越好)
            valid_tools = [t for t in candidates if t.performance.avg_execution_time > 0]
            if valid_tools:
                return min(valid_tools, key=lambda t: t.performance.avg_execution_time)
            return candidates[0]

        elif strategy == SelectionStrategy.PRIORITY:
            # ⚡ 性能优化:使用缓存的优先级映射
            return max(candidates, key=lambda t: self._priority_cache.get(t.priority, 0))

        elif strategy == SelectionStrategy.BALANCED:
            # 综合评分
            scored = await self._score_tools(candidates, task_type="unknown", domain="unknown")
            return max(scored, key=lambda s: s.total_score).tool if scored else candidates[0]

        elif strategy == SelectionStrategy.RANDOM:
            # 随机选择
            import random

            return random.choice(candidates)

        return candidates[0]

    async def _score_tools(
        self, tools: list[ToolDefinition], task_type: str, domain: str
    ) -> list[SelectionScore]:
        """
        为工具列表评分(性能优化版)

        Args:
            tools: 工具列表
            task_type: 任务类型
            domain: 任务领域

        Returns:
            评分列表
        """
        scored = []

        for tool in tools:
            score = SelectionScore(tool=tool)

            # 成功率评分 (0-1)
            score.success_score = tool.get_success_rate()

            # 性能评分 (基于执行时间,转换为0-1)
            if tool.performance.avg_execution_time > 0:
                # 假设1秒是优秀,10秒是较差
                import math

                score.performance_score = max(
                    0, 1 - math.log10(tool.performance.avg_execution_time + 1) / 2
                )
            else:
                score.performance_score = 0.5  # 未知性能给中等分

            # ⚡ 性能优化:使用缓存的优先级评分
            score.priority_score = self._score_cache.get(tool.priority, 0.5)

            # 相关性评分
            relevance = 0.0
            if tool.capability:
                # 检查任务类型匹配
                if task_type in tool.capability.task_types:
                    relevance += 0.5
                # 检查领域匹配
                if domain in tool.capability.domains:
                    relevance += 0.5
                # 检查通配符
                if "all" in tool.capability.task_types or "all" in tool.capability.domains:
                    relevance += 0.3
            score.relevance_score = min(1.0, relevance)

            # 计算总评分
            score.calculate_total()

            scored.append(score)

        return scored

    def get_recommendations(
        self, tool_id: str, max_recommendations: int = 3
    ) -> list[ToolDefinition]:
        """
        获取工具推荐(相似工具)

        Args:
            tool_id: 工具ID
            max_recommendations: 最多推荐数量

        Returns:
            推荐工具列表
        """
        reference_tool = self.registry.get_tool(tool_id)
        if not reference_tool:
            return []

        # 查找同分类、同领域的工具
        candidates = self.registry.search_tools(category=reference_tool.category, enabled_only=True)

        # 排除自己
        candidates = [t for t in candidates if t.tool_id != tool_id]

        # 排序:优先级 + 成功率
        candidates.sort(
            key=lambda t: (t.priority.value != reference_tool.priority.value, -t.get_success_rate())
        )

        return candidates[:max_recommendations]


__all__ = ["SelectionScore", "SelectionStrategy", "ToolSelector"]
