#!/usr/bin/env python3
"""
工具管理器单元测试

测试工具注册、分组、激活和选择功能。
"""
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

import pytest
from core.tools.tool_manager import ToolManager, ToolSelectionResult
from core.tools.base import ToolDefinition, ToolRegistry, ToolPriority
from core.tools.tool_group import ToolGroupDef


class TestToolManager:
    """测试工具管理器"""

    def test_initialization(self):
        """测试初始化"""
        manager = ToolManager()
        assert manager.registry is not None
        assert len(manager.groups) == 0
        assert manager.active_group is None
        assert manager._single_group_mode is True

    def test_register_group(self):
        """测试注册工具组"""
        manager = ToolManager()

        group_def = ToolGroupDef(
            name="test-group",
            display_name="测试组",
            description="测试工具组",
            tool_names=["test_tool1", "test_tool2"],
        )

        group = manager.register_group(group_def)

        assert group is not None
        assert group.name == "test-group"
        assert "test-group" in manager.groups
        assert len(manager.groups) == 1

    def test_register_duplicate_group(self):
        """测试注册重复工具组"""
        manager = ToolManager()

        group_def = ToolGroupDef(
            name="test-group",
            display_name="测试组",
            description="测试工具组",
            tool_names=["test_tool1"],
        )

        # 第一次注册
        manager.register_group(group_def)
        assert len(manager.groups) == 1

        # 第二次注册(应该产生警告但仍成功)
        manager.register_group(group_def)
        assert len(manager.groups) == 1  # 不会重复添加

    def test_get_group(self):
        """测试获取工具组"""
        manager = ToolManager()

        group_def = ToolGroupDef(
            name="test-group",
            display_name="测试组",
            description="测试工具组",
            tool_names=[],
        )

        manager.register_group(group_def)

        # 获取存在的组
        group = manager.get_group("test-group")
        assert group is not None
        assert group.name == "test-group"

        # 获取不存在的组
        group = manager.get_group("non-existent")
        assert group is None

    def test_activate_group(self):
        """测试激活工具组"""
        manager = ToolManager()

        group_def = ToolGroupDef(
            name="test-group",
            display_name="测试组",
            description="测试工具组",
            tool_names=[],
        )

        manager.register_group(group_def)

        # 激活组
        success = manager.activate_group("test-group")
        assert success is True
        assert manager.active_group == "test-group"

        # 激活不存在的组
        success = manager.activate_group("non-existent")
        assert success is False

    def test_activate_group_deactivate_others(self):
        """测试激活组时停用其他组"""
        manager = ToolManager()

        group1_def = ToolGroupDef(
            name="group1",
            display_name="组1",
            description="第一组",
            tool_names=[],
        )

        group2_def = ToolGroupDef(
            name="group2",
            display_name="组2",
            description="第二组",
            tool_names=[],
        )

        manager.register_group(group1_def)
        manager.register_group(group2_def)

        # 激活组1
        manager.activate_group("group1")
        assert manager.active_group == "group1"

        # 激活组2(停用组1)
        manager.activate_group("group2", deactivate_others=True)
        assert manager.active_group == "group2"

    def test_deactivate_group(self):
        """测试停用工具组"""
        manager = ToolManager()

        group_def = ToolGroupDef(
            name="test-group",
            display_name="测试组",
            description="测试工具组",
            tool_names=[],
        )

        manager.register_group(group_def)
        manager.activate_group("test-group")

        assert manager.active_group == "test-group"

        # 停用组
        manager.deactivate_group("test-group")
        assert manager.active_group is None

    def test_list_groups(self):
        """测试列出工具组"""
        manager = ToolManager()

        group1_def = ToolGroupDef(
            name="group1",
            display_name="组1",
            description="第一组",
            tool_names=[],
        )

        group2_def = ToolGroupDef(
            name="group2",
            display_name="组2",
            description="第二组",
            tool_names=[],
        )

        manager.register_group(group1_def)
        manager.register_group(group2_def)

        groups = manager.list_groups()
        assert len(groups) == 2
        assert "group1" in groups
        assert "group2" in groups

    def test_get_active_tools(self):
        """测试获取激活的工具"""
        manager = ToolManager()

        # 首先在注册表中注册一些工具
        registry = manager.registry

        tool1 = ToolDefinition(
            name="test_tool1",
            display_name="测试工具1",
            description="测试工具1描述",
            category="testing",
            priority=ToolPriority.MEDIUM,
            parameters=[],
        )

        tool2 = ToolDefinition(
            name="test_tool2",
            display_name="测试工具2",
            description="测试工具2描述",
            category="testing",
            priority=ToolPriority.HIGH,
            parameters=[],
        )

        registry.register(tool1)
        registry.register(tool2)

        # 创建工具组并激活
        group_def = ToolGroupDef(
            name="test-group",
            display_name="测试组",
            description="测试工具组",
            tool_names=["test_tool1", "test_tool2"],
        )

        manager.register_group(group_def)
        manager.activate_group("test-group")

        # 获取激活的工具
        active_tools = manager.get_active_tools()
        assert len(active_tools) == 2
        tool_names = [tool.name for tool in active_tools]
        assert "test_tool1" in tool_names
        assert "test_tool2" in tool_names

    def test_select_tool_for_task(self):
        """测试为任务选择工具"""
        manager = ToolManager()

        # 注册工具
        registry = manager.registry

        tool = ToolDefinition(
            name="search_tool",
            display_name="搜索工具",
            description="用于搜索信息",
            category="search",
            priority=ToolPriority.HIGH,
            parameters=[],
        )

        registry.register(tool)

        # 创建工具组并激活
        group_def = ToolGroupDef(
            name="search-group",
            display_name="搜索组",
            description="搜索工具组",
            tool_names=["search_tool"],
        )

        manager.register_group(group_def)
        manager.activate_group("search-group")

        # 选择工具
        result = manager.select_tool_for_task("搜索相关信息")
        assert result is not None
        assert result.tool.name == "search_tool"
        assert result.group_name == "search-group"
        assert result.confidence > 0

    def test_single_group_mode(self):
        """测试单组激活模式"""
        manager = ToolManager()

        group1_def = ToolGroupDef(
            name="group1",
            display_name="组1",
            description="第一组",
            tool_names=[],
        )

        group2_def = ToolGroupDef(
            name="group2",
            display_name="组2",
            description="第二组",
            tool_names=[],
        )

        manager.register_group(group1_def)
        manager.register_group(group2_def)

        # 单组模式(默认)
        assert manager.is_single_group_mode() is True

        # 激活组1
        manager.activate_group("group1")
        assert manager.active_group == "group1"

        # 激活组2(应该自动停用组1)
        manager.activate_group("group2")
        assert manager.active_group == "group2"

    def test_multi_group_mode(self):
        """测试多组激活模式"""
        manager = ToolManager()
        manager.set_single_group_mode(False)

        group1_def = ToolGroupDef(
            name="group1",
            display_name="组1",
            description="第一组",
            tool_names=[],
        )

        group2_def = ToolGroupDef(
            name="group2",
            display_name="组2",
            description="第二组",
            tool_names=[],
        )

        manager.register_group(group1_def)
        manager.register_group(group2_def)

        # 多组模式
        assert manager.is_single_group_mode() is False

        # 激活组1
        manager.activate_group("group1")
        # 激活组2(不停用组1)
        manager.activate_group("group2", deactivate_others=False)

        # 两个组都应该是激活的
        assert manager.get_group("group1").is_active() is True
        assert manager.get_group("group2").is_active() is True


class TestToolSelectionResult:
    """测试工具选择结果"""

    def test_creation(self):
        """测试创建选择结果"""
        tool = ToolDefinition(
            name="test",
            display_name="测试",
            description="测试工具",
            category="test",
            priority=ToolPriority.MEDIUM,
            parameters=[],
        )

        result = ToolSelectionResult(
            tool=tool,
            group_name="test-group",
            confidence=0.9,
            reason="匹配度高",
        )

        assert result.tool.name == "test"
        assert result.group_name == "test-group"
        assert result.confidence == 0.9
        assert result.reason == "匹配度高"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
