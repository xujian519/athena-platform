#!/usr/bin/env python3
"""
统一工具注册表测试（简化版）
Tests for core.tools.unified_registry
"""



class TestUnifiedToolRegistry:
    """测试UnifiedToolRegistry类"""

    def test_import_registry(self):
        """测试导入注册表模块"""
        from core.tools.unified_registry import UnifiedToolRegistry
        assert UnifiedToolRegistry is not None

    def test_registry_singleton(self):
        """测试单例模式"""
        from core.tools.unified_registry import get_unified_registry
        registry1 = get_unified_registry()
        registry2 = get_unified_registry()
        assert registry1 is registry2

    def test_registry_has_methods(self):
        """测试注册表方法存在"""
        from core.tools.unified_registry import get_unified_registry
        registry = get_unified_registry()
        # 验证核心方法存在
        assert hasattr(registry, 'get')
        assert hasattr(registry, 'require')


class TestToolCategory:
    """测试工具分类"""

    def test_import_category(self):
        """测试导入工具分类"""
        from core.tools.base import ToolCategory
        assert ToolCategory is not None

    def test_tool_category_enum(self):
        """测试工具分类枚举"""
        from core.tools.base import ToolCategory
        # 验证分类值存在
        assert hasattr(ToolCategory, 'PATENT')
        assert hasattr(ToolCategory, 'LEGAL')
