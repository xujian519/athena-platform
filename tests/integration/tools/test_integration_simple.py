#!/usr/bin/env python3
"""工具库集成测试 - 简化版"""

import pytest
import asyncio

from core.tools import (
    ToolManager, ToolSelector, ToolRegistry,
    ToolDefinition, ToolCategory, ToolPriority, ToolCapability,
)
from core.tools.tool_group import ToolGroupDef, ActivationRule, GroupActivationRule


@pytest.fixture
def sample_tools():
    """创建示例工具"""
    return [
        ToolDefinition(
            tool_id="patent_search_cn",
            name="中国专利检索",
            description="检索中国专利数据库",
            category=ToolCategory.PATENT_SEARCH,
            priority=ToolPriority.HIGH,
            capability=ToolCapability(
                input_types=["text", "keywords"],
                output_types=["json", "patent_list"],
                domains=["patent", "cn"],
                task_types=["search", "retrieval"],
            ),
            tags={"patent", "search", "cn"},
        ),
        ToolDefinition(
            tool_id="patent_analysis",
            name="专利分析",
            description="分析专利内容",
            category=ToolCategory.PATENT_ANALYSIS,
            priority=ToolPriority.MEDIUM,
            capability=ToolCapability(
                input_types=["patent_id", "patent_data"],
                output_types=["json", "analysis_report"],
                domains=["patent", "all"],
                task_types=["analysis", "evaluation"],
            ),
            tags={"patent", "analysis"},
        ),
    ]


class TestToolManagerIntegration:
    """工具管理器集成测试"""

    def test_full_workflow(self, sample_tools):
        """测试完整工作流程"""
        manager = ToolManager()
        
        # 注册工具
        for tool in sample_tools:
            manager.registry.register(tool)
        
        # 创建工具组 (使用正确的参数)
        patent_group = ToolGroupDef(
            name="patent_tools",
            display_name="专利工具组",
            description="专利检索和分析工具",
            categories=[ToolCategory.PATENT_SEARCH, ToolCategory.PATENT_ANALYSIS],
            tools=[t.tool_id for t in sample_tools],
            activation_rules=[
                ActivationRule(
                    rule_type=GroupActivationRule.DOMAIN,
                    domains=["patent"],
                    priority=10,
                )
            ],
        )
        
        manager.register_group(patent_group)
        result = manager.activate_group("patent_tools")
        
        assert result is True
        assert manager.active_group == "patent_tools"
        
        active_tools = manager.get_all_active_tools()
        assert len(active_tools) == 2


class TestToolSelectorIntegration:
    """工具选择器集成测试"""

    def test_selector_with_registry(self, sample_tools):
        """测试选择器与注册中心的集成"""
        registry = ToolRegistry()
        for tool in sample_tools:
            registry.register(tool)
        
        selector = ToolSelector(registry)
        
        async def test_select():
            tool = await selector.select_tool(
                task_type="search",
                domain="patent",
            )
            assert tool is not None
            assert tool.category == ToolCategory.PATENT_SEARCH
        
        asyncio.run(test_select())


class TestEndToEndIntegration:
    """端到端集成测试"""

    def test_complete_tool_lifecycle(self, sample_tools):
        """测试完整的工具生命周期"""
        manager = ToolManager()
        selector = ToolSelector(manager.registry)
        
        # 注册工具
        for tool in sample_tools:
            manager.registry.register(tool)
        
        # 创建工具组
        group = ToolGroupDef(
            name="test_group",
            display_name="测试组",
            description="测试工具组",
            categories=[ToolCategory.PATENT_SEARCH],
            tools=["patent_search_cn"],
            activation_rules=[
                ActivationRule(
                    rule_type=GroupActivationRule.KEYWORD,
                    keywords=["test"],
                    priority=1,
                )
            ],
        )
        
        manager.register_group(group)
        manager.activate_group("test_group")
        
        # 选择工具并更新性能
        async def test_workflow():
            tool = await selector.select_tool(
                task_type="search",
                domain="patent",
            )
            
            assert tool is not None
            manager.registry.update_tool_performance(tool.tool_id, 0.5, True)
            
            tool_updated = manager.registry.get_tool(tool.tool_id)
            assert tool_updated.performance.total_calls == 1
        
        asyncio.run(test_workflow())
