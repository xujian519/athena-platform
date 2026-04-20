#!/usr/bin/env python3
"""
Hook生命周期管理器测试

测试Hook生命周期管理的所有功能。

作者: Athena平台团队
创建时间: 2026-04-20
"""
from __future__ import annotations

import asyncio
import pytest

from core.hooks.base import HookContext, HookFunction, HookRegistry, HookType


# 由于增强模块还未创建，我们先测试现有功能
# 然后逐步添加增强功能的测试


class TestHookRegistryBasics:
    """测试HookRegistry基础功能"""

    @pytest.fixture
    def registry(self):
        """创建Hook注册表实例"""
        return HookRegistry()

    @pytest.fixture
    def sample_hook(self):
        """创建示例Hook函数"""

        async def my_hook(context: HookContext):
            return "hook_executed"

        return my_hook

    def test_register_hook(self, registry, sample_hook):
        """测试注册Hook"""
        hook_func = HookFunction(
            name="test_hook",
            hook_type=HookType.POST_TASK_COMPLETE,
            func=sample_hook,
            priority=10,
        )

        result = registry.register(hook_func)

        assert result is registry  # 支持链式调用
        hooks = registry.get_hooks(HookType.POST_TASK_COMPLETE)
        assert len(hooks) == 1
        assert hooks[0].name == "test_hook"

    def test_register_function(self, registry, sample_hook):
        """测试便捷注册方法"""
        hook = registry.register_function(
            name="test_hook",
            hook_type=HookType.POST_TASK_COMPLETE,
            func=sample_hook,
            priority=10,
        )

        assert hook.name == "test_hook"
        assert hook.priority == 10
        assert hook.async_mode is True

    def test_priority_ordering(self, registry):
        """测试优先级排序"""

        async def hook1(ctx):
            return "1"

        async def hook2(ctx):
            return "2"

        async def hook3(ctx):
            return "3"

        # 按不同优先级注册
        registry.register_function("hook1", HookType.POST_TASK_COMPLETE, hook1, priority=5)
        registry.register_function("hook2", HookType.POST_TASK_COMPLETE, hook2, priority=10)
        registry.register_function("hook3", HookType.POST_TASK_COMPLETE, hook3, priority=1)

        hooks = registry.get_hooks(HookType.POST_TASK_COMPLETE)

        # 应该按优先级降序排列
        assert hooks[0].name == "hook2"  # priority 10
        assert hooks[1].name == "hook1"  # priority 5
        assert hooks[2].name == "hook3"  # priority 1

    @pytest.mark.asyncio
    async def test_trigger_hook(self, registry):
        """测试触发Hook"""

        executed = []

        async def test_hook(context: HookContext):
            executed.append(context.hook_type)
            return "result"

        registry.register_function(
            name="test_hook",
            hook_type=HookType.POST_TASK_COMPLETE,
            func=test_hook,
        )

        context = HookContext(hook_type=HookType.POST_TASK_COMPLETE)
        results = await registry.trigger(HookType.POST_TASK_COMPLETE, context)

        assert len(results) == 1
        assert results[0] == "result"
        assert len(executed) == 1

    @pytest.mark.asyncio
    async def test_trigger_multiple_hooks(self, registry):
        """测试触发多个Hook"""

        executed = []

        async def hook1(ctx):
            executed.append("hook1")
            return "1"

        async def hook2(ctx):
            executed.append("hook2")
            return "2"

        async def hook3(ctx):
            executed.append("hook3")
            return "3"

        registry.register_function("hook1", HookType.POST_TASK_COMPLETE, hook1, priority=1)
        registry.register_function("hook2", HookType.POST_TASK_COMPLETE, hook2, priority=3)
        registry.register_function("hook3", HookType.POST_TASK_COMPLETE, hook3, priority=2)

        context = HookContext(hook_type=HookType.POST_TASK_COMPLETE)
        results = await registry.trigger(HookType.POST_TASK_COMPLETE, context)

        # 按优先级执行
        assert executed == ["hook2", "hook3", "hook1"]
        assert len(results) == 3

    @pytest.mark.asyncio
    async def test_trigger_parallel(self, registry):
        """测试并行触发Hook"""

        execution_order = []

        async def hook1(ctx):
            execution_order.append("1")
            await asyncio.sleep(0.01)
            return "1"

        async def hook2(ctx):
            execution_order.append("2")
            await asyncio.sleep(0.01)
            return "2"

        async def hook3(ctx):
            execution_order.append("3")
            await asyncio.sleep(0.01)
            return "3"

        registry.register_function("hook1", HookType.POST_TASK_COMPLETE, hook1)
        registry.register_function("hook2", HookType.POST_TASK_COMPLETE, hook2)
        registry.register_function("hook3", HookType.POST_TASK_COMPLETE, hook3)

        context = HookContext(hook_type=HookType.POST_TASK_COMPLETE)
        results = await registry.trigger_parallel(HookType.POST_TASK_COMPLETE, context)

        assert len(results) == 3
        # 并行执行，顺序可能不同
        assert set(results) == {"1", "2", "3"}

    def test_remove_hook(self, registry):
        """测试移除Hook"""

        async def test_hook(ctx):
            return "result"

        registry.register_function("test_hook", HookType.POST_TASK_COMPLETE, test_hook)
        assert len(registry.get_hooks(HookType.POST_TASK_COMPLETE)) == 1

        removed = registry.remove_hook("test_hook")
        assert removed is True
        assert len(registry.get_hooks(HookType.POST_TASK_COMPLETE)) == 0

    def test_enable_disable_hook(self, registry):
        """测试启用/禁用Hook"""

        async def test_hook(ctx):
            return "result"

        hook = registry.register_function("test_hook", HookType.POST_TASK_COMPLETE, test_hook)

        assert hook.enabled is True

        registry.disable_hook("test_hook")
        assert hook.enabled is False

        registry.enable_hook("test_hook")
        assert hook.enabled is True

    def test_clear_hooks(self, registry):
        """测试清空所有Hook"""

        async def test_hook(ctx):
            return "result"

        registry.register_function("hook1", HookType.POST_TASK_COMPLETE, test_hook)
        registry.register_function("hook2", HookType.PRE_TASK_START, test_hook)

        registry.clear()

        assert len(registry.get_hooks(HookType.POST_TASK_COMPLETE)) == 0
        assert len(registry.get_hooks(HookType.PRE_TASK_START)) == 0


class TestHookContext:
    """测试HookContext"""

    def test_context_data_operations(self):
        """测试上下文数据操作"""
        context = HookContext(hook_type=HookType.POST_TASK_COMPLETE)

        # 设置和获取数据
        context.set("key1", "value1")
        context.set("key2", 123)

        assert context.get("key1") == "value1"
        assert context.get("key2") == 123
        assert context.get("nonexistent", "default") == "default"

    def test_context_to_dict(self):
        """测试转换为字典"""
        context = HookContext(
            hook_type=HookType.POST_TASK_COMPLETE,
            data={"key": "value"},
        )

        result = context.to_dict()

        assert result["hook_type"] == "post_task_complete"
        assert result["data"] == {"key": "value"}
        assert "timestamp" in result


class TestHookFunction:
    """测试HookFunction"""

    @pytest.mark.asyncio
    async def test_async_hook_execution(self):
        """测试异步Hook执行"""

        async def test_hook(context: HookContext):
            return "async_result"

        hook = HookFunction(
            name="test_async",
            hook_type=HookType.POST_TASK_COMPLETE,
            func=test_hook,
            async_mode=True,
        )

        context = HookContext(hook_type=HookType.POST_TASK_COMPLETE)
        result = await hook.execute(context)

        assert result == "async_result"

    @pytest.mark.asyncio
    async def test_sync_hook_execution(self):
        """测试同步Hook执行"""

        def test_hook(context: HookContext):
            return "sync_result"

        hook = HookFunction(
            name="test_sync",
            hook_type=HookType.POST_TASK_COMPLETE,
            func=test_hook,
            async_mode=False,
        )

        context = HookContext(hook_type=HookType.POST_TASK_COMPLETE)
        result = await hook.execute(context)

        assert result == "sync_result"

    @pytest.mark.asyncio
    async def test_hook_error_handling(self):
        """测试Hook错误处理"""

        async def failing_hook(context: HookContext):
            raise ValueError("Hook error")

        hook = HookFunction(
            name="failing_hook",
            hook_type=HookType.POST_TASK_COMPLETE,
            func=failing_hook,
        )

        context = HookContext(hook_type=HookType.POST_TASK_COMPLETE)
        result = await hook.execute(context)

        # 错误不应该抛出，应该返回None
        assert result is None

    @pytest.mark.asyncio
    async def test_disabled_hook_not_executed(self):
        """测试禁用的Hook不执行"""

        executed = []

        async def test_hook(context: HookContext):
            executed.append(True)
            return "result"

        hook = HookFunction(
            name="disabled_hook",
            hook_type=HookType.POST_TASK_COMPLETE,
            func=test_hook,
            enabled=False,
        )

        context = HookContext(hook_type=HookType.POST_TASK_COMPLETE)
        await hook.execute(context)

        assert len(executed) == 0


class TestHookType:
    """测试HookType枚举"""

    def test_hook_type_values(self):
        """测试HookType枚举值"""
        assert HookType.PRE_TASK_START.value == "pre_task_start"
        assert HookType.POST_TASK_COMPLETE.value == "post_task_complete"
        assert HookType.PRE_TOOL_USE.value == "pre_tool_use"
        assert HookType.POST_TOOL_USE.value == "post_tool_use"
        assert HookType.ON_ERROR.value == "on_error"
        assert HookType.ON_CHECKPOINT.value == "on_checkpoint"
        assert HookType.ON_STATE_CHANGE.value == "on_state_change"
        assert HookType.PRE_REASONING.value == "pre_reasoning"
        assert HookType.POST_REASONING.value == "post_reasoning"

    def test_hook_type_comparisons(self):
        """测试HookType比较"""
        assert HookType.PRE_TASK_START == HookType.PRE_TASK_START
        assert HookType.PRE_TASK_START != HookType.POST_TASK_COMPLETE


__all__ = [
    "TestHookRegistryBasics",
    "TestHookContext",
    "TestHookFunction",
    "TestHookType",
]
