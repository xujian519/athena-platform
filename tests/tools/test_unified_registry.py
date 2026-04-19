#!/usr/bin/env python3
"""
统一工具注册表测试
Unified Tool Registry Tests

测试统一工具注册表的核心功能。

Author: Athena平台团队
Created: 2026-04-19
Version: v2.0.0
"""

import pytest
from core.tools.unified_registry import (
    UnifiedToolRegistry,
    get_unified_registry,
    ToolHealthStatus,
    LazyToolLoader,
)
from core.tools.base import ToolDefinition, ToolCategory, ToolPriority


class TestUnifiedToolRegistry:
    """统一工具注册表测试"""

    def test_singleton(self):
        """测试单例模式"""
        registry1 = get_unified_registry()
        registry2 = get_unified_registry()

        assert registry1 is registry2
        assert isinstance(registry1, UnifiedToolRegistry)

    def test_register_tool(self):
        """测试工具注册"""
        registry = get_unified_registry()

        # 创建工具定义
        tool = ToolDefinition(
            tool_id="test_tool",
            name="测试工具",
            description="这是一个测试工具",
            category=ToolCategory.PATENT_SEARCH,
            priority=ToolPriority.HIGH,
        )

        # 注册工具
        registry.register(tool)

        # 验证注册
        retrieved = registry.get("test_tool")
        assert retrieved is not None
        assert retrieved.tool_id == "test_tool"

    def test_register_lazy_tool(self):
        """测试懒加载工具注册"""
        registry = get_unified_registry()

        # 注册懒加载工具
        success = registry.register_lazy(
            tool_id="lazy_tool",
            import_path="os.path",
            function_name="join",
            metadata={"description": "路径连接工具"},
        )

        assert success is True

    def test_health_status(self):
        """测试健康状态管理"""
        registry = get_unified_registry()

        # 创建工具定义
        tool = ToolDefinition(
            tool_id="health_test_tool",
            name="健康测试工具",
            description="测试健康状态",
            category=ToolCategory.PATENT_SEARCH,
        )

        registry.register(tool)

        # 初始状态
        status = registry.get_health_status("health_test_tool")
        assert status == ToolHealthStatus.UNKNOWN

        # 标记为不健康
        registry.mark_unhealthy("health_test_tool", "测试原因")
        status = registry.get_health_status("health_test_tool")
        assert status == ToolHealthStatus.UNHEALTHY

        # 标记为健康
        registry.mark_healthy("health_test_tool")
        status = registry.get_health_status("health_test_tool")
        assert status == ToolHealthStatus.HEALTHY

    def test_find_by_category(self):
        """测试按分类查找"""
        registry = get_unified_registry()

        # 注册多个工具
        for i in range(3):
            tool = ToolDefinition(
                tool_id=f"search_tool_{i}",
                name=f"搜索工具{i}",
                description=f"搜索工具{i}",
                category=ToolCategory.PATENT_SEARCH,
            )
            registry.register(tool)

        # 查找工具
        tools = registry.find_by_category(ToolCategory.PATENT_SEARCH)

        # 验证结果
        assert len(tools) >= 3

    def test_get_statistics(self):
        """测试统计信息"""
        registry = get_unified_registry()

        stats = registry.get_statistics()

        assert "total_tools" in stats
        assert "base_tools" in stats
        assert "lazy_tools" in stats
        assert "health_distribution" in stats

    def test_require_tool(self):
        """测试require方法"""
        registry = get_unified_registry()

        # 创建工具定义
        tool = ToolDefinition(
            tool_id="require_test_tool",
            name="Require测试工具",
            description="测试require方法",
            category=ToolCategory.PATENT_SEARCH,
        )

        registry.register(tool)

        # 测试存在的工具
        retrieved = registry.require("require_test_tool")
        assert retrieved is not None

        # 测试不存在的工具
        with pytest.raises(ValueError):
            registry.require("non_existent_tool")


class TestLazyToolLoader:
    """懒加载工具测试"""

    def test_load_tool(self):
        """测试工具加载"""
        loader = LazyToolLoader(
            tool_id="test_lazy",
            import_path="os.path",
            function_name="join",
            metadata={},
        )

        # 加载工具
        func = loader.load()

        assert func is not None
        assert callable(func)

    def test_load_cache(self):
        """测试加载缓存"""
        loader = LazyToolLoader(
            tool_id="test_cache",
            import_path="os.path",
            function_name="join",
            metadata={},
        )

        # 第一次加载
        func1 = loader.load()
        assert loader._loaded is True

        # 第二次加载（应该使用缓存）
        func2 = loader.load()
        assert func1 is func2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
