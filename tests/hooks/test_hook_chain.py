#!/usr/bin/env python3
"""
Hook链和中间件测试

测试Hook链式处理和中间件模式。

作者: Athena平台团队
创建时间: 2026-04-20
"""
from __future__ import annotations

import asyncio
import pytest
from dataclasses import dataclass
from typing import Any

from core.hooks.base import HookContext, HookRegistry, HookType


# 定义增强功能的类型（待实现）


@dataclass
class HookResult:
    """Hook执行结果"""
    success: bool
    data: Any = None
    error: str | None = None
    execution_time: float = 0.0
    stopped: bool = False
    modified_context: bool = False


class HookMiddleware:
    """Hook中间件基类"""

    async def before_hook(self, context: HookContext) -> HookContext:
        """Hook执行前处理"""
        return context

    async def after_hook(self, context: HookContext, result: HookResult) -> HookResult:
        """Hook执行后处理"""
        return result


class LoggingMiddleware(HookMiddleware):
    """日志中间件"""

    def __init__(self):
        self.before_calls = []
        self.after_calls = []

    async def before_hook(self, context: HookContext) -> HookContext:
        self.before_calls.append(context.hook_type)
        return context

    async def after_hook(self, context: HookContext, result: HookResult) -> HookResult:
        self.after_calls.append(context.hook_type)
        return result


class TimingMiddleware(HookMiddleware):
    """计时中间件"""

    def __init__(self):
        self.times = []

    async def before_hook(self, context: HookContext) -> HookContext:
        context.set("_start_time", asyncio.get_event_loop().time())
        return context

    async def after_hook(self, context: HookContext, result: HookResult) -> HookResult:
        start_time = context.get("_start_time")
        if start_time:
            elapsed = asyncio.get_event_loop().time() - start_time
            self.times.append(elapsed)
            result.execution_time = elapsed
        return result


class StopPropagationMiddleware(HookMiddleware):
    """停止传播中间件"""

    def __init__(self, stop_on: HookType | None = None):
        self.stop_on = stop_on
        self.stopped = False

    async def after_hook(self, context: HookContext, result: HookResult) -> HookResult:
        if self.stop_on and context.hook_type == self.stop_on:
            result.stopped = True
            self.stopped = True
        return result


class TestHookMiddleware:
    """测试Hook中间件"""

    @pytest.mark.asyncio
    async def test_logging_middleware(self):
        """测试日志中间件"""
        middleware = LoggingMiddleware()
        context = HookContext(hook_type=HookType.POST_TASK_COMPLETE)
        result = HookResult(success=True, data="test")

        context = await middleware.before_hook(context)
        result = await middleware.after_hook(context, result)

        assert len(middleware.before_calls) == 1
        assert len(middleware.after_calls) == 1
        assert middleware.before_calls[0] == HookType.POST_TASK_COMPLETE

    @pytest.mark.asyncio
    async def test_timing_middleware(self):
        """测试计时中间件"""
        middleware = TimingMiddleware()
        context = HookContext(hook_type=HookType.POST_TASK_COMPLETE)
        result = HookResult(success=True)

        context = await middleware.before_hook(context)
        await asyncio.sleep(0.01)  # 模拟处理
        result = await middleware.after_hook(context, result)

        assert len(middleware.times) == 1
        assert result.execution_time > 0
        assert result.execution_time >= 0.01  # 至少睡了10ms

    @pytest.mark.asyncio
    async def test_stop_propagation(self):
        """测试停止传播"""
        middleware = StopPropagationMiddleware(stop_on=HookType.POST_TASK_COMPLETE)
        context = HookContext(hook_type=HookType.POST_TASK_COMPLETE)
        result = HookResult(success=True)

        result = await middleware.after_hook(context, result)

        assert result.stopped is True
        assert middleware.stopped is True

    @pytest.mark.asyncio
    async def test_middleware_chain(self):
        """测试中间件链"""
        logging_mw = LoggingMiddleware()
        timing_mw = TimingMiddleware()

        context = HookContext(hook_type=HookType.POST_TASK_COMPLETE)
        result = HookResult(success=True)

        # 模拟中间件链执行
        context = await logging_mw.before_hook(context)
        context = await timing_mw.before_hook(context)

        await asyncio.sleep(0.01)

        result = await timing_mw.after_hook(context, result)
        result = await logging_mw.after_hook(context, result)

        # 验证所有中间件都执行了
        assert len(logging_mw.before_calls) == 1
        assert len(logging_mw.after_calls) == 1
        assert len(timing_mw.times) == 1


class TestHookChain:
    """测试Hook链"""

    @pytest.fixture
    def registry(self):
        """创建Hook注册表"""
        return HookRegistry()

    @pytest.mark.asyncio
    async def test_sequential_execution(self, registry):
        """测试顺序执行"""
        execution_order = []

        async def hook1(ctx):
            execution_order.append("hook1")
            return "1"

        async def hook2(ctx):
            execution_order.append("hook2")
            return "2"

        async def hook3(ctx):
            execution_order.append("hook3")
            return "3"

        # 按优先级注册
        registry.register_function("hook1", HookType.POST_TASK_COMPLETE, hook1, priority=1)
        registry.register_function("hook2", HookType.POST_TASK_COMPLETE, hook2, priority=3)
        registry.register_function("hook3", HookType.POST_TASK_COMPLETE, hook3, priority=2)

        context = HookContext(hook_type=HookType.POST_TASK_COMPLETE)
        await registry.trigger(HookType.POST_TASK_COMPLETE, context)

        # 按优先级执行
        assert execution_order == ["hook2", "hook3", "hook1"]

    @pytest.mark.asyncio
    async def test_parallel_execution(self, registry):
        """测试并行执行"""
        execution_times = {}

        async def hook1(ctx):
            execution_times["hook1"] = asyncio.get_event_loop().time()
            await asyncio.sleep(0.01)
            return "1"

        async def hook2(ctx):
            execution_times["hook2"] = asyncio.get_event_loop().time()
            await asyncio.sleep(0.01)
            return "2"

        async def hook3(ctx):
            execution_times["hook3"] = asyncio.get_event_loop().time()
            await asyncio.sleep(0.01)
            return "3"

        registry.register_function("hook1", HookType.POST_TASK_COMPLETE, hook1)
        registry.register_function("hook2", HookType.POST_TASK_COMPLETE, hook2)
        registry.register_function("hook3", HookType.POST_TASK_COMPLETE, hook3)

        context = HookContext(hook_type=HookType.POST_TASK_COMPLETE)
        await registry.trigger_parallel(HookType.POST_TASK_COMPLETE, context)

        # 并行执行，时间应该很接近
        times = list(execution_times.values())
        time_diff = max(times) - min(times)
        assert time_diff < 0.05  # 应该在50ms内完成

    @pytest.mark.asyncio
    async def test_error_handling_in_chain(self, registry):
        """测试链中的错误处理"""
        results = []

        async def hook1(ctx):
            results.append("hook1")
            return "1"

        async def hook2(ctx):
            results.append("hook2")
            raise ValueError("Hook2 error")

        async def hook3(ctx):
            results.append("hook3")
            return "3"

        registry.register_function("hook1", HookType.POST_TASK_COMPLETE, hook1)
        registry.register_function("hook2", HookType.POST_TASK_COMPLETE, hook2)
        registry.register_function("hook3", HookType.POST_TASK_COMPLETE, hook3)

        context = HookContext(hook_type=HookType.POST_TASK_COMPLETE)
        await registry.trigger(HookType.POST_TASK_COMPLETE, context)

        # 即使有错误，所有Hook都应该执行
        assert "hook1" in results
        assert "hook2" in results
        assert "hook3" in results


class TestHookResult:
    """测试HookResult"""

    def test_hook_result_creation(self):
        """测试创建HookResult"""
        result = HookResult(
            success=True,
            data="test_data",
            execution_time=0.123,
        )

        assert result.success is True
        assert result.data == "test_data"
        assert result.execution_time == 0.123
        assert result.error is None
        assert result.stopped is False
        assert result.modified_context is False

    def test_hook_result_with_error(self):
        """测试带错误的HookResult"""
        result = HookResult(
            success=False,
            error="Something went wrong",
        )

        assert result.success is False
        assert result.error == "Something went wrong"

    def test_hook_result_stopped(self):
        """测试停止传播的HookResult"""
        result = HookResult(
            success=True,
            stopped=True,
        )

        assert result.stopped is True


class TestContextModification:
    """测试上下文修改"""

    @pytest.mark.asyncio
    async def test_hook_modifies_context(self):
        """测试Hook修改上下文"""

        async def modifying_hook(context: HookContext):
            context.set("modified", True)
            context.set("value", 42)
            return "modified"

        registry = HookRegistry()
        registry.register_function(
            "modifying_hook",
            HookType.POST_TASK_COMPLETE,
            modifying_hook,
        )

        context = HookContext(hook_type=HookType.POST_TASK_COMPLETE)
        await registry.trigger(HookType.POST_TASK_COMPLETE, context)

        assert context.get("modified") is True
        assert context.get("value") == 42

    @pytest.mark.asyncio
    async def test_multiple_hooks_modify_context(self):
        """测试多个Hook修改上下文"""

        async def hook1(ctx):
            ctx.set("counter", 1)
            return "1"

        async def hook2(ctx):
            counter = ctx.get("counter", 0)
            ctx.set("counter", counter + 1)
            return "2"

        async def hook3(ctx):
            counter = ctx.get("counter", 0)
            ctx.set("counter", counter + 10)
            return "3"

        registry = HookRegistry()
        # 按优先级顺序注册：hook3(priority=3) -> hook2(priority=2) -> hook1(priority=1)
        registry.register_function("hook1", HookType.POST_TASK_COMPLETE, hook1, priority=1)
        registry.register_function("hook2", HookType.POST_TASK_COMPLETE, hook2, priority=2)
        registry.register_function("hook3", HookType.POST_TASK_COMPLETE, hook3, priority=3)

        context = HookContext(hook_type=HookType.POST_TASK_COMPLETE)
        await registry.trigger(HookType.POST_TASK_COMPLETE, context)

        # 按优先级执行：hook3先执行，此时counter=0，设置为0+10=10
        # 然后hook2执行，counter=10，设置为10+1=11
        # 最后hook1执行，直接设置为1
        # 所以最终值应该是1
        assert context.get("counter") == 1  # hook1最后执行，覆盖了之前的值


__all__ = [
    "TestHookMiddleware",
    "TestHookChain",
    "TestHookResult",
    "TestContextModification",
]
