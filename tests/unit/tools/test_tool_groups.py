#!/usr/bin/env python3
"""
工具分组管理测试
Tests for Tool Group Management

测试用例：
1. 工具组注册和激活
2. 关键词匹配激活
3. 任务类型匹配激活
4. 领域匹配激活
5. 自动工具组选择
6. 工具组统计

作者: Athena平台团队
创建时间: 2026-01-20
版本: v1.0.0 "Phase 1"
"""

import pytest
from core.tools.tool_group import (
    ToolGroup,
    ToolGroupDef,
    ActivationRule,
    GroupActivationRule
)
from core.tools.tool_manager import ToolManager, get_tool_manager, ToolSelectionResult
from core.tools.base import ToolCategory, ToolDefinition, ToolCapability, ToolPriority
from core.tools import groups


@pytest.fixture
def sample_tools():
    """创建示例工具"""
    return [
        ToolDefinition(
            tool_id="patent_search_01",
            name="专利搜索工具",
            description="搜索专利文献",
            category=ToolCategory.PATENT_SEARCH,
            priority=ToolPriority.HIGH,
            capability=ToolCapability(
                input_types=["text"],
                output_types=["json"],
                domains=["patent"],
                task_types=["patent_search", "patent_analysis"]
            ),
            tags={"search", "patent"}
        ),
        ToolDefinition(
            tool_id="novelty_analysis_01",
            name="新颖性分析工具",
            description="分析专利新颖性",
            category=ToolCategory.PATENT_ANALYSIS,
            priority=ToolPriority.HIGH,
            capability=ToolCapability(
                input_types=["text"],
                output_types=["report"],
                domains=["patent"],
                task_types=["novelty_assessment"]
            ),
            tags={"analysis", "patent"}
        ),
        ToolDefinition(
            tool_id="web_crawler_01",
            name="网页爬虫工具",
            description="爬取网页数据",
            category=ToolCategory.WEB_AUTOMATION,
            priority=ToolPriority.MEDIUM,
            capability=ToolCapability(
                input_types=["url"],
                output_types=["html", "json"],
                domains=["web", "general"],
                task_types=["web_scraping", "data_collection"]
            ),
            tags={"crawler", "web"}
        ),
        ToolDefinition(
            tool_id="legal_search_01",
            name="法律搜索工具",
            description="搜索法律案例",
            category=ToolCategory.LEGAL_ANALYSIS,
            priority=ToolPriority.HIGH,
            capability=ToolCapability(
                input_types=["text"],
                output_types=["json"],
                domains=["legal"],
                task_types=["legal_research", "case_analysis"]
            ),
            tags={"search", "legal"}
        )
    ]


@pytest.fixture
def tool_manager(sample_tools):
    """创建带有示例工具的工具管理器"""
    manager = ToolManager()
    registry = manager.registry

    # 注册示例工具
    for tool in sample_tools:
        registry.register(tool)

    # 注册所有工具组
    for group_def in groups.ALL_TOOL_GROUPS:
        manager.register_group(group_def)

    return manager


class TestToolGroup:
    """工具组测试"""

    def test_group_creation(self):
        """测试工具组创建"""
        definition = ToolGroupDef(
            name="test_group",
            display_name="测试工具组",
            description="用于测试的工具组",
            categories=[ToolCategory.PATENT_SEARCH],
            activation_rules=[
                ActivationRule(
                    rule_type=GroupActivationRule.KEYWORD,
                    keywords=["测试", "test"]
                )
            ]
        )

        group = ToolGroup(definition, None)
        assert group.definition.name == "test_group"
        assert not group.is_active()
        assert group.get_tool_count() == 0

    def test_group_activation(self, tool_manager):
        """测试工具组激活"""
        group = tool_manager.get_group("patent_analysis")
        assert group is not None

        # 激活工具组
        tool_manager.activate_group("patent_analysis")
        assert group.is_active()
        assert tool_manager.active_group == "patent_analysis"

    def test_group_deactivation(self, tool_manager):
        """测试工具组停用"""
        group = tool_manager.get_group("patent_analysis")
        tool_manager.activate_group("patent_analysis")

        # 停用工具组
        tool_manager.deactivate_group("patent_analysis")
        assert not group.is_active()
        assert tool_manager.active_group is None

    def test_keyword_matching(self, tool_manager):
        """测试关键词匹配"""
        # 专利分析组应该匹配专利相关任务
        group = tool_manager.get_group("patent_analysis")

        assert group.should_activate_for_task("帮我搜索专利文献")
        assert group.should_activate_for_task("分析专利的新颖性")
        assert not group.should_activate_for_task("写一首诗")

    def test_task_type_matching(self, tool_manager):
        """测试任务类型匹配"""
        group = tool_manager.get_group("patent_analysis")

        assert group.should_activate_for_task(
            "任意任务",
            task_type="patent_analysis"
        )

    def test_domain_matching(self, tool_manager):
        """测试领域匹配"""
        group = tool_manager.get_group("patent_analysis")

        assert group.should_activate_for_task(
            "任意任务",
            domain="patent"
        )

    def test_group_statistics(self, tool_manager):
        """测试工具组统计"""
        group = tool_manager.get_group("patent_analysis")
        tool_manager.activate_group("patent_analysis")

        stats = group.get_statistics()
        assert stats["group_name"] == "patent_analysis"
        assert stats["active"] is True
        assert "tool_count" in stats


class TestToolManager:
    """工具管理器测试"""

    def test_manager_initialization(self):
        """测试管理器初始化"""
        manager = ToolManager()
        assert manager.registry is not None
        assert len(manager.groups) == 0
        assert manager.active_group is None

    def test_register_all_groups(self, tool_manager):
        """测试注册所有工具组"""
        # 在fixture中已经注册了所有组
        assert len(tool_manager.groups) == len(groups.ALL_TOOL_GROUPS)

        # 检查关键组存在
        assert "patent_analysis" in tool_manager.groups
        assert "legal_research" in tool_manager.groups
        assert "browser_automation" in tool_manager.groups
        assert "general" in tool_manager.groups

    @pytest.mark.asyncio
    async def test_auto_activate_patent_task(self, tool_manager):
        """测试自动激活专利任务"""
        group_name = await tool_manager.auto_activate_group_for_task(
            "帮我分析专利的新颖性",
            task_type="patent_analysis"
        )

        assert group_name == "patent_analysis"
        assert tool_manager.active_group == "patent_analysis"

    @pytest.mark.asyncio
    async def test_auto_activate_legal_task(self, tool_manager):
        """测试自动激活法律任务"""
        group_name = await tool_manager.auto_activate_group_for_task(
            "帮我搜索相关法律案例",
            task_type="legal_research"
        )

        assert group_name == "legal_research"
        assert tool_manager.active_group == "legal_research"

    @pytest.mark.asyncio
    async def test_auto_activate_fallback_to_general(self, tool_manager):
        """测试回退到通用组"""
        group_name = await tool_manager.auto_activate_group_for_task(
            "写一首关于春天的诗"
        )

        # 应该激活通用组或返回None
        assert group_name in ["general", None]

    def test_get_all_active_tools(self, tool_manager):
        """测试获取所有激活工具"""
        tool_manager.activate_group("patent_analysis")
        tools = tool_manager.get_all_active_tools()

        # 应该包含专利相关的工具
        tool_ids = [t.tool_id for t in tools]
        assert "patent_search_01" in tool_ids
        assert "novelty_analysis_01" in tool_ids

    @pytest.mark.asyncio
    async def test_select_best_tool(self, tool_manager):
        """测试选择最佳工具"""
        result = await tool_manager.select_best_tool(
            "搜索专利文献",
            task_type="patent_analysis"
        )

        assert result.tool is not None
        assert result.confidence > 0
        assert result.group_name is not None

    def test_manager_statistics(self, tool_manager):
        """测试管理器统计"""
        stats = tool_manager.get_statistics()

        assert stats["total_groups"] == len(groups.ALL_TOOL_GROUPS)
        assert "groups" in stats
        assert isinstance(stats["groups"], list)

    def test_single_group_mode(self, tool_manager):
        """测试单组激活模式"""
        # 默认是单组模式
        tool_manager.activate_group("patent_analysis")
        tool_manager.activate_group("legal_research")

        # 应该只有最后一个激活
        assert tool_manager.active_group == "legal_research"
        assert not tool_manager.get_group("patent_analysis").is_active()

        # 切换到多组模式
        tool_manager.set_single_group_mode(False)
        tool_manager.activate_group("patent_analysis")

        # 现在应该有多个激活的组
        assert tool_manager.get_group("legal_research").is_active()
        assert tool_manager.get_group("patent_analysis").is_active()

    def test_deactivate_all_groups(self, tool_manager):
        """测试停用所有组"""
        tool_manager.activate_group("patent_analysis")
        tool_manager.activate_group("legal_research")
        tool_manager.set_single_group_mode(False)

        tool_manager.deactivate_all_groups()

        assert tool_manager.active_group is None
        assert not tool_manager.get_group("patent_analysis").is_active()
        assert not tool_manager.get_group("legal_research").is_active()


class TestActivationRule:
    """激活规则测试"""

    def test_keyword_rule(self):
        """测试关键词规则"""
        rule = ActivationRule(
            rule_type=GroupActivationRule.KEYWORD,
            keywords=["专利", "patent"]
        )

        assert rule.matches("搜索专利文献")
        assert rule.matches("Search for patents")
        assert not rule.matches("写一首诗")

    def test_task_type_rule(self):
        """测试任务类型规则"""
        rule = ActivationRule(
            rule_type=GroupActivationRule.TASK_TYPE,
            task_types=["patent_analysis", "patent_search"]
        )

        assert rule.matches("任意任务", task_type="patent_analysis")
        assert not rule.matches("任意任务", task_type="legal_research")

    def test_domain_rule(self):
        """测试领域规则"""
        rule = ActivationRule(
            rule_type=GroupActivationRule.DOMAIN,
            domains=["patent", "知识产权"]
        )

        assert rule.matches("任意任务", domain="patent")
        assert not rule.matches("任意任务", domain="legal")

    def test_manual_rule(self):
        """测试手动规则"""
        rule = ActivationRule(
            rule_type=GroupActivationRule.MANUAL
        )

        # 手动规则不自动匹配
        assert not rule.matches("任何任务")

    def test_adaptive_rule(self):
        """测试自适应规则"""
        rule = ActivationRule(
            rule_type=GroupActivationRule.ADAPTIVE
        )

        # 自适应规则总是返回True，由ToolManager处理
        assert rule.matches("任何任务")


class TestConvenienceFunctions:
    """便捷函数测试"""

    def test_get_tool_manager(self):
        """测试获取全局工具管理器"""
        manager = get_tool_manager()
        assert manager is not None
        assert isinstance(manager, ToolManager)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
