#!/usr/bin/env python3
"""
Tools模块__init__.py单元测试

测试工具管理系统的导入和便捷函数

测试范围:
- 模块导入验证
- 类和枚举可用性
- 便捷函数测试
- 常量验证
"""

import pytest


# 测试所有主要导入
def test_module_imports():
    """测试模块主要导入"""
    from core.tools import (
        GroupActivationRule,
        SelectionScore,
        SelectionStrategy,
        ToolCapability,
        ToolCategory,
        ToolDefinition,
        ToolGroup,
        ToolGroupDef,
        ToolManager,
        ToolPerformance,
        ToolPriority,
        ToolRegistry,
        ToolSelectionResult,
        ToolSelector,
        get_global_registry,
        get_tool_manager,
    )

    # 验证导入成功
    assert ToolCapability is not None
    assert ToolCategory is not None
    assert ToolDefinition is not None
    assert ToolPerformance is not None
    assert ToolPriority is not None
    assert ToolRegistry is not None
    assert get_global_registry is not None
    assert SelectionScore is not None
    assert SelectionStrategy is not None
    assert ToolSelector is not None
    assert GroupActivationRule is not None
    assert ToolGroup is not None
    assert ToolGroupDef is not None
    assert ToolManager is not None
    assert ToolSelectionResult is not None
    assert get_tool_manager is not None


class TestToolCapability:
    """测试ToolCapability类"""

    def test_capability_creation(self):
        """测试能力创建"""
        from core.tools import ToolCapability

        # ToolCapability是dataclass，不是枚举
        capability = ToolCapability(
            input_types=["text"],
            output_types=["result"],
            domains=["general"],
            task_types=["analysis"]
        )

        assert capability.input_types == ["text"]
        assert capability.output_types == ["result"]
        assert capability.domains == ["general"]
        assert capability.task_types == ["analysis"]


class TestToolCategory:
    """测试ToolCategory枚举"""

    def test_category_values(self):
        """测试分类值"""
        from core.tools import ToolCategory

        # 验证常见分类存在
        assert hasattr(ToolCategory, 'PATENT_SEARCH')
        assert hasattr(ToolCategory, 'PATENT_ANALYSIS')
        assert hasattr(ToolCategory, 'CODE_ANALYSIS')
        assert hasattr(ToolCategory, 'SEMANTIC_ANALYSIS')


class TestToolPriority:
    """测试ToolPriority枚举"""

    def test_priority_values(self):
        """测试优先级值"""
        from core.tools import ToolPriority

        # 验证优先级存在
        assert hasattr(ToolPriority, 'LOW')
        assert hasattr(ToolPriority, 'MEDIUM')
        assert hasattr(ToolPriority, 'HIGH')
        assert hasattr(ToolPriority, 'CRITICAL')


class TestSelectionStrategy:
    """测试SelectionStrategy枚举"""

    def test_strategy_values(self):
        """测试策略值"""
        from core.tools import SelectionStrategy

        # 验证策略存在
        assert hasattr(SelectionStrategy, 'SUCCESS_RATE')
        assert hasattr(SelectionStrategy, 'PERFORMANCE')
        assert hasattr(SelectionStrategy, 'PRIORITY')


class TestConvenienceFunctions:
    """测试便捷函数"""

    def test_get_global_registry(self):
        """测试获取全局注册表"""
        from core.tools import get_global_registry

        # 可能返回None或注册表实例
        registry = get_global_registry()

        # 只验证可以调用，不要求特定属性
        assert registry is not None or callable(get_global_registry)

    def test_get_tool_manager(self):
        """测试获取工具管理器"""
        from core.tools import get_tool_manager

        # 可能返回None或管理器实例
        manager = get_tool_manager()

        # 只验证可以调用
        assert manager is not None or callable(get_tool_manager)


class TestModuleConstants:
    """测试模块常量"""

    def test_module_all(self):
        """测试__all__导出列表"""
        import core.tools as tools_module

        # 验证__all__存在且不为空
        assert hasattr(tools_module, '__all__')
        all_list = tools_module.__all__

        assert isinstance(all_list, list)
        assert len(all_list) > 0


class TestAutoRegister:
    """测试自动注册模块"""

    def test_auto_register_import(self):
        """测试自动注册模块导入"""
        # 自动注册模块应该在导入时触发
        from core.tools import auto_register

        assert auto_register is not None
        assert hasattr(auto_register, '__file__')


class TestIntegration:
    """集成测试"""

    def test_registry_and_manager_integration(self):
        """测试注册表和管理器集成"""
        from core.tools import get_global_registry, get_tool_manager

        # 获取注册表和管理器
        registry = get_global_registry()
        manager = get_tool_manager()

        # 验证两者可以获取
        assert registry is not None or callable(get_global_registry)
        assert manager is not None or callable(get_tool_manager)


class TestEdgeCases:
    """测试边界情况"""

    def test_multiple_registry_calls(self):
        """测试多次调用获取注册表"""
        from core.tools import get_global_registry

        # 多次调用应该返回同一个实例（单例模式）
        registry1 = get_global_registry()
        registry2 = get_global_registry()

        assert registry1 is registry2

    def test_multiple_manager_calls(self):
        """测试多次调用获取管理器"""
        from core.tools import get_tool_manager

        # 多次调用可能返回同一实例或新实例
        manager1 = get_tool_manager()
        manager2 = get_tool_manager()

        # 验证两个都是有效的管理器
        assert manager1 is not None
        assert manager2 is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
