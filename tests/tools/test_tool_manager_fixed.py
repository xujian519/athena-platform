#!/usr/bin/env python3
"""
工具管理器单元测试 (修正版)

使用正确的API字段名。
"""
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

import pytest

from core.tools.base import ToolCategory
from core.tools.tool_group import ToolGroupDef
from core.tools.tool_manager import ToolManager


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
            categories=[ToolCategory.WEB_SEARCH],
        )

        group = manager.register_group(group_def)

        assert group is not None
        assert group.name == "test-group"
        assert "test-group" in manager.groups
        assert len(manager.groups) == 1

    def test_get_group(self):
        """测试获取工具组"""
        manager = ToolManager()

        group_def = ToolGroupDef(
            name="test-group",
            display_name="测试组",
            description="测试工具组",
            categories=[ToolCategory.WEB_SEARCH],
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
            categories=[ToolCategory.WEB_SEARCH],
        )

        manager.register_group(group_def)

        # 激活组
        success = manager.activate_group("test-group")
        assert success is True
        assert manager.active_group == "test-group"

        # 激活不存在的组
        success = manager.activate_group("non-existent")
        assert success is False

    def test_deactivate_group(self):
        """测试停用工具组"""
        manager = ToolManager()

        group_def = ToolGroupDef(
            name="test-group",
            display_name="测试组",
            description="测试工具组",
            categories=[ToolCategory.WEB_SEARCH],
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
            categories=[ToolCategory.WEB_SEARCH],
        )

        group2_def = ToolGroupDef(
            name="group2",
            display_name="组2",
            description="第二组",
            categories=[ToolCategory.PATENT_SEARCH],
        )

        manager.register_group(group1_def)
        manager.register_group(group2_def)

        groups = manager.list_groups()
        assert len(groups) == 2
        assert "group1" in groups
        assert "group2" in groups


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
