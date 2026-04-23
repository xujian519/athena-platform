#!/usr/bin/env python3
"""
统一异步执行接口测试

测试BaseTool抽象类、同步/异步工具包装器。
"""

import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

import asyncio

import pytest

from core.tools.async_interface import (
    AsyncToolWrapper,
    BaseTool,
    SyncToolWrapper,
    ToolContext,
    ToolExecutor,
    call_tool,
    to_async_tool,
    tool_context,
)


class DummySyncTool:
    """同步工具示例"""

    def __init__(self):
        self.call_count = 0

    def process(self, parameters: dict) -> dict:
        """同步处理"""
        self.call_count += 1
        return {"result": f"sync_result_{self.call_count}", **parameters}


class DummyAsyncTool(BaseTool):
    """异步工具示例"""

    def __init__(self):
        super().__init__("dummy_async", "异步工具示例")
        self.call_count = 0

    async def call(self, parameters: dict, context: ToolContext | None = None) -> dict:
        """异步调用"""
        await asyncio.sleep(0.01)  # 模拟异步操作
        self.call_count += 1
        return {"result": f"async_result_{self.call_count}", **parameters}


class TestAsyncInterface:
    """异步接口测试"""

    @pytest.mark.asyncio
    async def test_async_tool_call(self):
        """测试异步工具调用"""
        tool = DummyAsyncTool()

        result = await tool.call({"arg1": "value1"})

        assert result["result"] == "async_result_1"
        assert result["arg1"] == "value1"
        assert tool.call_count == 1

    @pytest.mark.asyncio
    async def test_sync_tool_wrapper(self):
        """测试同步工具包装器"""
        sync_tool = DummySyncTool()
        wrapper = SyncToolWrapper(
            name="sync_tool",
            sync_handler=sync_tool.process,
            description="同步工具包装器测试",
        )

        result = await wrapper.call({"arg1": "value1"})

        assert result["result"] == "sync_result_1"
        assert result["arg1"] == "value1"
        assert sync_tool.call_count == 1

    @pytest.mark.asyncio
    async def test_async_tool_wrapper(self):
        """测试异步工具包装器"""
        async def async_handler(parameters: dict) -> dict:
            await asyncio.sleep(0.01)
            return {"result": "wrapped_async", **parameters}

        wrapper = AsyncToolWrapper(
            name="wrapped_async",
            async_handler=async_handler,
            description="异步工具包装器测试",
        )

        result = await wrapper.call({"arg1": "value1"})

        assert result["result"] == "wrapped_async"
        assert result["arg1"] == "value1"

    @pytest.mark.asyncio
    async def test_to_async_tool_decorator_sync(self):
        """测试装饰器 - 同步函数"""
        @to_async_tool("decorated_sync", "装饰器同步工具")
        def sync_handler(parameters: dict) -> dict:
            return {"result": "decorated_sync", **parameters}

        tool = sync_handler  # 装饰器返回工具
        result = await tool.call({"arg1": "value1"})

        assert result["result"] == "decorated_sync"
        assert isinstance(tool, SyncToolWrapper)

    @pytest.mark.asyncio
    async def test_to_async_tool_decorator_async(self):
        """测试装饰器 - 异步函数"""
        @to_async_tool("decorated_async", "装饰器异步工具")
        async def async_handler(parameters: dict) -> dict:
            await asyncio.sleep(0.01)
            return {"result": "decorated_async", **parameters}

        tool = async_handler  # 装饰器返回工具
        result = await tool.call({"arg1": "value1"})

        assert result["result"] == "decorated_async"
        assert isinstance(tool, AsyncToolWrapper)

    @pytest.mark.asyncio
    async def test_tool_context_manager(self):
        """测试工具上下文管理器"""
        async with tool_context(
            session_id="session_123",
            user_id="user_456",
            request_id="request_789",
        ) as context:
            assert context.session_id == "session_123"
            assert context.user_id == "user_456"
            assert context.request_id == "request_789"

            # 测试to_dict
            context_dict = context.to_dict()
            assert context_dict["session_id"] == "session_123"

    @pytest.mark.asyncio
    async def test_tool_executor(self):
        """测试工具执行器"""
        tool = DummyAsyncTool()
        executor = ToolExecutor(max_retries=3, timeout=5.0)

        result = await executor.execute(tool, {"arg1": "value1"})

        assert result["result"] == "async_result_1"
        assert tool.call_count == 1

    @pytest.mark.asyncio
    async def test_tool_executor_retry_on_failure(self):
        """测试工具执行器重试"""
        call_count = 0

        class FailingTool(BaseTool):
            def __init__(self):
                super().__init__("failing", "失败工具")

            async def call(self, parameters: dict, context=None) -> dict:
                nonlocal call_count
                call_count += 1
                if call_count < 3:
                    raise ValueError("模拟失败")
                return {"result": "success"}

        tool = FailingTool()
        executor = ToolExecutor(max_retries=3, retry_delay=0.01)

        result = await executor.execute(tool, {})

        assert result["result"] == "success"
        assert call_count == 3

    @pytest.mark.asyncio
    async def test_call_tool_convenience_function(self):
        """测试便捷函数"""
        tool = DummyAsyncTool()

        result = await call_tool(tool, {"arg1": "value1"})

        assert result["result"] == "async_result_1"
        assert tool.call_count == 1

    @pytest.mark.asyncio
    async def test_parameter_validation(self):
        """测试参数验证"""
        tool = DummyAsyncTool()

        # 默认验证通过
        is_valid, errors = tool.validate_parameters({"arg1": "value1"})
        assert is_valid
        assert len(errors) == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
