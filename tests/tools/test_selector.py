#!/usr/bin/env python3
"""
工具选择器单元测试

测试工具选择策略和评分功能。
"""
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

import pytest

from core.tools.base import (
    ToolDefinition,
    ToolPriority,
    ToolRegistry,
)
from core.tools.selector import (
    SelectionScore,
    SelectionStrategy,
    ToolSelector,
)


class TestSelectionStrategy:
    """测试选择策略枚举"""

    def test_strategy_values(self):
        """测试策略值"""
        assert SelectionStrategy.SUCCESS_RATE.value == "success_rate"
        assert SelectionStrategy.PERFORMANCE.value == "performance"
        assert SelectionStrategy.PRIORITY.value == "priority"
        assert SelectionStrategy.BALANCED.value == "balanced"
        assert SelectionStrategy.RANDOM.value == "random"


class TestSelectionScore:
    """测试选择评分"""

    def test_creation(self):
        """测试创建评分"""
        tool = ToolDefinition(
            name="test",
            display_name="测试",
            description="测试工具",
            category="test",
            priority=ToolPriority.MEDIUM,
            parameters=[],
        )

        score = SelectionScore(
            tool=tool,
            success_score=0.8,
            performance_score=0.7,
            priority_score=0.6,
            relevance_score=0.9,
        )

        assert score.tool.name == "test"
        assert score.success_score == 0.8
        assert score.performance_score == 0.7
        assert score.priority_score == 0.6
        assert score.relevance_score == 0.9

    def test_calculate_total_default_weights(self):
        """测试计算总评分(默认权重)"""
        tool = ToolDefinition(
            name="test",
            display_name="测试",
            description="测试工具",
            category="test",
            priority=ToolPriority.MEDIUM,
            parameters=[],
        )

        score = SelectionScore(
            tool=tool,
            success_score=0.8,
            performance_score=0.7,
            priority_score=0.6,
            relevance_score=0.9,
        )

        score.calculate_total()

        # 默认权重: success=0.3, performance=0.2, priority=0.2, relevance=0.3
        expected = 0.8 * 0.3 + 0.7 * 0.2 + 0.6 * 0.2 + 0.9 * 0.3
        assert abs(score.total_score - expected) < 0.001

    def test_calculate_total_custom_weights(self):
        """测试计算总评分(自定义权重)"""
        tool = ToolDefinition(
            name="test",
            display_name="测试",
            description="测试工具",
            category="test",
            priority=ToolPriority.MEDIUM,
            parameters=[],
        )

        score = SelectionScore(
            tool=tool,
            success_score=0.8,
            performance_score=0.7,
            priority_score=0.6,
            relevance_score=0.9,
        )

        # 自定义权重
        custom_weights = {
            "success": 0.5,
            "performance": 0.3,
            "priority": 0.1,
            "relevance": 0.1,
        }

        score.calculate_total(weights=custom_weights)

        expected = 0.8 * 0.5 + 0.7 * 0.3 + 0.6 * 0.1 + 0.9 * 0.1
        assert abs(score.total_score - expected) < 0.001


class TestToolSelector:
    """测试工具选择器"""

    def test_initialization(self):
        """测试初始化"""
        registry = ToolRegistry()
        selector = ToolSelector(registry)

        assert selector.registry is not None
        assert selector.strategy == SelectionStrategy.BALANCED

    def test_set_strategy(self):
        """测试设置策略"""
        registry = ToolRegistry()
        selector = ToolSelector(registry)

        selector.set_strategy(SelectionStrategy.SUCCESS_RATE)
        assert selector.strategy == SelectionStrategy.SUCCESS_RATE

        selector.set_strategy(SelectionStrategy.PERFORMANCE)
        assert selector.strategy == SelectionStrategy.PERFORMANCE

    def test_score_tool_by_priority(self):
        """测试按优先级评分"""
        registry = ToolRegistry()
        selector = ToolSelector(registry)

        # 创建不同优先级的工具
        high_tool = ToolDefinition(
            name="high_tool",
            display_name="高优先级",
            description="高优先级工具",
            category="test",
            priority=ToolPriority.HIGH,
            parameters=[],
        )

        low_tool = ToolDefinition(
            name="low_tool",
            display_name="低优先级",
            description="低优先级工具",
            category="test",
            priority=ToolPriority.LOW,
            parameters=[],
        )

        high_score = selector.score_tool(high_tool, "测试任务")
        low_score = selector.score_tool(low_tool, "测试任务")

        # 高优先级工具应该得分更高
        assert high_score.priority_score > low_score.priority_score

    def test_score_tool_by_relevance(self):
        """测试按相关性评分"""
        registry = ToolRegistry()
        selector = ToolSelector(registry)

        # 创建工具
        search_tool = ToolDefinition(
            name="search_tool",
            display_name="搜索工具",
            description="用于搜索信息",
            category="search",
            priority=ToolPriority.MEDIUM,
            parameters=[],
        )

        # 相关任务
        relevant_score = selector.score_tool(search_tool, "搜索相关信息")

        # 不相关任务
        irrelevant_score = selector.score_tool(search_tool, "播放音乐")

        # 相关任务应该得分更高
        assert relevant_score.relevance_score > irrelevant_score.relevance_score

    def test_select_best_tool_priority(self):
        """测试按优先级选择最佳工具"""
        registry = ToolRegistry()
        selector = ToolSelector(registry)
        selector.set_strategy(SelectionStrategy.PRIORITY)

        # 注册工具
        high_tool = ToolDefinition(
            name="high_tool",
            display_name="高优先级",
            description="高优先级工具",
            category="test",
            priority=ToolPriority.HIGH,
            parameters=[],
        )

        low_tool = ToolDefinition(
            name="low_tool",
            display_name="低优先级",
            description="低优先级工具",
            category="test",
            priority=ToolPriority.LOW,
            parameters=[],
        )

        registry.register(high_tool)
        registry.register(low_tool)

        # 选择最佳工具
        tools = registry.list_tools()
        best = selector.select_best_tool(tools, "测试任务")

        # 应该选择高优先级工具
        assert best.name == "high_tool"

    def test_select_best_tool_balanced(self):
        """测试平衡模式选择最佳工具"""
        registry = ToolRegistry()
        selector = ToolSelector(registry)
        selector.set_strategy(SelectionStrategy.BALANCED)

        # 注册工具
        tool1 = ToolDefinition(
            name="tool1",
            display_name="工具1",
            description="搜索工具",
            category="search",
            priority=ToolPriority.HIGH,
            parameters=[],
        )

        tool2 = ToolDefinition(
            name="tool2",
            display_name="工具2",
            description="计算工具",
            category="compute",
            priority=ToolPriority.MEDIUM,
            parameters=[],
        )

        registry.register(tool1)
        registry.register(tool2)

        # 选择最佳工具
        tools = registry.list_tools()
        best = selector.select_best_tool(tools, "搜索相关信息")

        # 应该选择相关的工具
        assert best.name == "tool1"

    def test_select_best_tool_empty_list(self):
        """测试空工具列表"""
        registry = ToolRegistry()
        selector = ToolSelector(registry)

        # 空列表
        best = selector.select_best_tool([], "测试任务")
        assert best is None

    def test_score_and_rank_tools(self):
        """测试评分和排序工具"""
        registry = ToolRegistry()
        selector = ToolSelector(registry)

        # 注册工具
        tool1 = ToolDefinition(
            name="tool1",
            display_name="工具1",
            description="高优先级搜索工具",
            category="search",
            priority=ToolPriority.HIGH,
            parameters=[],
        )

        tool2 = ToolDefinition(
            name="tool2",
            display_name="工具2",
            description="低优先级工具",
            category="other",
            priority=ToolPriority.LOW,
            parameters=[],
        )

        registry.register(tool1)
        registry.register(tool2)

        # 评分和排序
        tools = registry.list_tools()
        ranked = selector.score_and_rank_tools(tools, "搜索任务")

        # 应该返回两个评分
        assert len(ranked) == 2

        # 第一个应该得分更高
        assert ranked[0].total_score >= ranked[1].total_score

    def test_priority_scores(self):
        """测试优先级评分映射"""
        registry = ToolRegistry()
        selector = ToolSelector(registry)

        # 测试所有优先级
        priorities = [
            ToolPriority.CRITICAL,
            ToolPriority.HIGH,
            ToolPriority.MEDIUM,
            ToolPriority.LOW,
        ]

        scores = []
        for priority in priorities:
            tool = ToolDefinition(
                name=f"tool_{priority.value}",
                display_name=f"工具{priority.value}",
                description="测试",
                category="test",
                priority=priority,
                parameters=[],
            )

            score_obj = selector.score_tool(tool, "测试")
            scores.append(score_obj.priority_score)

        # CRITICAL应该得分最高
        assert scores[0] >= scores[1] >= scores[2] >= scores[3]
        assert scores[0] == 1.0  # CRITICAL


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
