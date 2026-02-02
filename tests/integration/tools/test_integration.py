#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
工具系统集成测试

测试工具库各模块之间的集成功能

作者: Athena平台团队
创建时间: 2026-01-25
"""

import pytest
import asyncio
from pathlib import Path
import sys

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from core.tools.base import (
    ToolDefinition,
    ToolCategory,
    ToolRegistry,
    ToolPriority,
    ToolCapability
)
from core.tools.selector import (
    ToolSelector,
    SelectionStrategy
)
from core.tools.tool_call_manager import (
    ToolCallManager,
    CallStatus
)


@pytest.mark.integration
class TestToolIntegration:
    """工具系统集成测试"""

    @pytest.mark.asyncio
    async def test_full_tool_lifecycle(self):
        """测试完整的工具生命周期"""
        # 1. 创建工具定义
        async def sample_handler(params, context):
            return {"result": "success", "data": params.get("input", "")}

        tool = ToolDefinition(
            tool_id="test_tool",
            name="测试工具",
            category=ToolCategory.CODE_ANALYSIS,
            description="集成测试工具",
            capability=ToolCapability(
                input_types=["text"],
                output_types=["result"],
                domains=["all"],
                task_types=["analysis"]
            ),
            required_params=["input"],
            optional_params=["option"],
            handler=sample_handler,
            timeout=30.0
        )

        # 2. 注册到注册中心
        registry = ToolRegistry()
        registry.register(tool)

        # 3. 从注册中心检索
        retrieved = registry.get_tool("test_tool")
        assert retrieved is not None
        assert retrieved.tool_id == "test_tool"

        # 4. 通过选择器选择
        selector = ToolSelector(registry=registry)
        selected = await selector.select_tool(
            task_type="analysis",
            domain="all"
        )
        assert selected is not None

        # 5. 通过调用管理器执行
        manager = ToolCallManager(enable_rate_limit=False)
        manager.register_tool(selected)

        result = await manager.call_tool(
            tool_name="test_tool",
            parameters={"input": "test_data"}
        )

        assert result.status == CallStatus.SUCCESS
        assert result.result is not None

    @pytest.mark.asyncio
    async def test_multi_tool_workflow(self):
        """测试多工具协作工作流"""
        # 创建多个工具
        async def analyzer_handler(params, context):
            return {"analysis": f"分析了 {params.get('data', '')}"}

        async def transformer_handler(params, context):
            return {"transformed": f"转换了 {params.get('input', '')}"}

        tools = [
            ToolDefinition(
                tool_id="analyzer",
                name="分析器",
                category=ToolCategory.CODE_ANALYSIS,
                description="数据分析",
                capability=ToolCapability(
                    input_types=["raw"],
                    output_types=["analyzed"],
                    domains=["data"],
                    task_types=["analysis"]
                ),
                handler=analyzer_handler,
                timeout=10.0
            ),
            ToolDefinition(
                tool_id="transformer",
                name="转换器",
                category=ToolCategory.DATA_TRANSFORMATION,
                description="数据转换",
                capability=ToolCapability(
                    input_types=["analyzed"],
                    output_types=["transformed"],
                    domains=["data"],
                    task_types=["transformation"]
                ),
                handler=transformer_handler,
                timeout=10.0
            )
        ]

        # 注册所有工具
        registry = ToolRegistry()
        for tool in tools:
            registry.register(tool)

        # 创建选择器和调用管理器
        selector = ToolSelector(registry=registry)
        manager = ToolCallManager(enable_rate_limit=False)

        # 模拟工作流：分析 -> 转换
        analysis_tool = await selector.select_tool(task_type="analysis", domain="data")
        assert analysis_tool is not None
        manager.register_tool(analysis_tool)

        analysis_result = await manager.call_tool(
            tool_name="analyzer",
            parameters={"data": "test_data"}
        )
        assert analysis_result.status == CallStatus.SUCCESS

        transform_tool = await selector.select_tool(task_type="transformation", domain="data")
        assert transform_tool is not None
        manager.register_tool(transform_tool)

        transform_result = await manager.call_tool(
            tool_name="transformer",
            parameters={"input": "analyzed_data"}
        )
        assert transform_result.status == CallStatus.SUCCESS

    @pytest.mark.asyncio
    async def test_registry_selector_integration(self):
        """测试注册中心与选择器集成"""
        registry = ToolRegistry()

        # 注册不同优先级的工具
        for i in range(10):
            priority = ToolPriority.HIGH if i < 3 else ToolPriority.MEDIUM
            tool = ToolDefinition(
                tool_id=f"tool_{i}",
                name=f"工具{i}",
                category=ToolCategory.CODE_ANALYSIS,
                description=f"测试工具{i}",
                priority=priority,
                capability=ToolCapability(
                    input_types=["input"],
                    output_types=["output"],
                    domains=["test"],
                    task_types=["test"]
                )
            )
            registry.register(tool)

        # 使用选择器
        selector = ToolSelector(
            registry=registry,
            strategy=SelectionStrategy.PRIORITY
        )

        # 选择应该返回高优先级工具
        selected = await selector.select_tool(task_type="test", domain="test")

        assert selected is not None
        assert selected.priority == ToolPriority.HIGH


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
