#!/usr/bin/env python3
"""
Hook系统单元测试

测试Hook系统的注册、执行和错误处理功能。
"""

import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from datetime import datetime

import pytest

from core.tools.hooks import (
    BaseHook,
    HookContext,
    HookEvent,
    HookRegistry,
    HookResult,
    LoggingHook,
    MetricsHook,
    RateLimitHook,
    ValidationHook,
    create_default_hooks,
    register_default_hooks,
)


class TestHookContext:
    """测试HookContext数据类"""

    def test_initialization_with_defaults(self):
        """测试使用默认值初始化"""
        ctx = HookContext(
            tool_name="test_tool",
            parameters={"key": "value"},
        )

        assert ctx.tool_name == "test_tool"
        assert ctx.parameters == {"key": "value"}
        assert ctx.context == {}
        assert ctx.request_id == ""
        assert isinstance(ctx.timestamp, datetime)
        assert ctx.metadata == {}

    def test_initialization_with_all_params(self):
        """测试完整参数初始化"""
        timestamp = datetime.now()
        ctx = HookContext(
            tool_name="test_tool",
            parameters={"key": "value"},
            context={"session_id": "123"},
            request_id="req-001",
            timestamp=timestamp,
            metadata={"custom": "data"},
        )

        assert ctx.tool_name == "test_tool"
        assert ctx.parameters == {"key": "value"}
        assert ctx.context == {"session_id": "123"}
        assert ctx.request_id == "req-001"
        assert ctx.timestamp == timestamp
        assert ctx.metadata == {"custom": "data"}


class TestHookResult:
    """测试HookResult数据类"""

    def test_default_result(self):
        """测试默认结果"""
        result = HookResult()

        assert result.should_proceed is True
        assert result.modified_parameters is None
        assert result.metadata == {}
        assert result.error_message is None

    def test_blocking_result(self):
        """测试阻止结果"""
        result = HookResult(
            should_proceed=False,
            error_message="权限不足",
        )

        assert result.should_proceed is False
        assert result.error_message == "权限不足"

    def test_modifying_result(self):
        """测试修改参数的结果"""
        result = HookResult(
            modified_parameters={"new_key": "new_value"},
            metadata={"hook_id": "test"},
        )

        assert result.should_proceed is True
        assert result.modified_parameters == {"new_key": "new_value"}
        assert result.metadata == {"hook_id": "test"}


class MockHook(BaseHook):
    """Mock Hook用于测试"""

    def __init__(
        self, hook_id: str, should_proceed: bool = True, priority: int = 10, enabled: bool = True
    ):
        super().__init__(hook_id=hook_id, priority=priority, enabled=enabled)
        self.should_proceed = should_proceed
        self.call_count = 0

    async def process(
        self, event: HookEvent, hook_context: HookContext
    ) -> HookResult:
        """Mock处理方法"""
        self.call_count += 1
        return HookResult(should_proceed=self.should_proceed)


class TestBaseHook:
    """测试BaseHook抽象类"""

    def test_hook_properties(self):
        """测试Hook属性"""
        hook = MockHook(hook_id="test_hook", priority=5)

        assert hook.hook_id == "test_hook"
        assert hook.priority == 5
        assert hook.enabled is True

    def test_hook_disabled(self):
        """测试禁用Hook"""
        hook = MockHook(hook_id="test_hook", enabled=False)

        assert hook.enabled is False

    def test_hook_repr(self):
        """测试Hook字符串表示"""
        hook = MockHook(hook_id="test_hook", priority=5)
        repr_str = repr(hook)

        assert "test_hook" in repr_str
        assert "5" in repr_str
        assert "True" in repr_str


class TestHookRegistry:
    """测试HookRegistry注册表"""

    @pytest.fixture
    def registry(self):
        """创建Hook注册表"""
        return HookRegistry()

    def test_initialization(self, registry):
        """测试初始化"""
        stats = registry.get_stats()

        assert stats["total_hooks"] == 0
        assert stats["executed_hooks"] == 0
        assert stats["blocked_calls"] == 0
        assert stats["hook_errors"] == 0

    def test_register_single_hook(self, registry):
        """测试注册单个Hook"""
        hook = MockHook(hook_id="test_hook")
        events = [HookEvent.PRE_TOOL_USE]

        registry.register(hook, events)

        stats = registry.get_stats()
        assert stats["total_hooks"] == 1

        hooks = registry.get_hooks(HookEvent.PRE_TOOL_USE)
        assert len(hooks) == 1
        assert hooks[0].hook_id == "test_hook"

    def test_register_multiple_events(self, registry):
        """测试注册到多个事件"""
        hook = MockHook(hook_id="test_hook")
        events = [
            HookEvent.PRE_TOOL_USE,
            HookEvent.POST_TOOL_USE,
            HookEvent.TOOL_FAILURE,
        ]

        registry.register(hook, events)

        stats = registry.get_stats()
        assert stats["total_hooks"] == 3

        assert len(registry.get_hooks(HookEvent.PRE_TOOL_USE)) == 1
        assert len(registry.get_hooks(HookEvent.POST_TOOL_USE)) == 1
        assert len(registry.get_hooks(HookEvent.TOOL_FAILURE)) == 1

    def test_hook_priority_ordering(self, registry):
        """测试Hook按优先级排序"""
        hook1 = MockHook(hook_id="hook1", priority=30)
        hook2 = MockHook(hook_id="hook2", priority=10)
        hook3 = MockHook(hook_id="hook3", priority=20)

        events = [HookEvent.PRE_TOOL_USE]
        registry.register(hook1, events)
        registry.register(hook2, events)
        registry.register(hook3, events)

        hooks = registry.get_hooks(HookEvent.PRE_TOOL_USE)
        assert hooks[0].hook_id == "hook2"  # priority 10
        assert hooks[1].hook_id == "hook3"  # priority 20
        assert hooks[2].hook_id == "hook1"  # priority 30

    def test_unregister_hook(self, registry):
        """测试注销Hook"""
        hook = MockHook(hook_id="test_hook")
        events = [HookEvent.PRE_TOOL_USE]

        registry.register(hook, events)
        assert len(registry.get_hooks(HookEvent.PRE_TOOL_USE)) == 1

        removed = registry.unregister("test_hook")
        assert removed is True
        assert len(registry.get_hooks(HookEvent.PRE_TOOL_USE)) == 0

    def test_unregister_nonexistent_hook(self, registry):
        """测试注销不存在的Hook"""
        removed = registry.unregister("nonexistent_hook")
        assert removed is False

    @pytest.mark.asyncio
    async def test_execute_hooks_success(self, registry):
        """测试成功执行Hook"""
        hook = MockHook(hook_id="test_hook", should_proceed=True)
        events = [HookEvent.PRE_TOOL_USE]

        registry.register(hook, events)

        context = HookContext(
            tool_name="test_tool",
            parameters={},
        )

        result = await registry.execute_hooks(HookEvent.PRE_TOOL_USE, context)

        assert result.should_proceed is True
        assert hook.call_count == 1

        stats = registry.get_stats()
        assert stats["executed_hooks"] == 1

    @pytest.mark.asyncio
    async def test_execute_hooks_blocking(self, registry):
        """测试Hook阻止调用"""
        hook = MockHook(hook_id="blocking_hook", should_proceed=False)
        events = [HookEvent.PRE_TOOL_USE]

        registry.register(hook, events)

        context = HookContext(
            tool_name="test_tool",
            parameters={},
        )

        result = await registry.execute_hooks(HookEvent.PRE_TOOL_USE, context)

        assert result.should_proceed is False

        stats = registry.get_stats()
        assert stats["blocked_calls"] == 1

    @pytest.mark.asyncio
    async def test_execute_hooks_no_hooks(self, registry):
        """测试没有Hook时直接返回"""
        context = HookContext(
            tool_name="test_tool",
            parameters={},
        )

        result = await registry.execute_hooks(HookEvent.PRE_TOOL_USE, context)

        assert result.should_proceed is True

    @pytest.mark.asyncio
    async def test_execute_hooks_error_isolation(self, registry):
        """测试Hook错误隔离"""
        class FailingHook(BaseHook):
            def __init__(self):
                super().__init__(hook_id="failing_hook")

            async def process(
                self, event: HookEvent, hook_context: HookContext
            ) -> HookResult:
                raise ValueError("Hook执行失败")

        failing_hook = FailingHook()
        mock_hook = MockHook(hook_id="mock_hook")

        events = [HookEvent.PRE_TOOL_USE]
        registry.register(failing_hook, events)
        registry.register(mock_hook, events)

        context = HookContext(
            tool_name="test_tool",
            parameters={},
        )

        result = await registry.execute_hooks(HookEvent.PRE_TOOL_USE, context)

        # Hook错误不应阻止主流程
        assert result.should_proceed is True
        assert mock_hook.call_count == 1

        stats = registry.get_stats()
        assert stats["hook_errors"] == 1

    def test_clear_hooks(self, registry):
        """测试清除所有Hook"""
        hook1 = MockHook(hook_id="hook1")
        hook2 = MockHook(hook_id="hook2")

        events = [HookEvent.PRE_TOOL_USE]
        registry.register(hook1, events)
        registry.register(hook2, events)

        assert len(registry.get_hooks(HookEvent.PRE_TOOL_USE)) == 2

        registry.clear()

        assert len(registry.get_hooks(HookEvent.PRE_TOOL_USE)) == 0
        stats = registry.get_stats()
        assert stats["total_hooks"] == 0


class TestLoggingHook:
    """测试LoggingHook"""

    @pytest.mark.asyncio
    async def test_pre_tool_use_logging(self, caplog):
        """测试工具调用前日志"""
        hook = LoggingHook()
        context = HookContext(
            tool_name="test_tool",
            parameters={"key": "value"},
            request_id="req-001",
        )

        result = await hook.process(HookEvent.PRE_TOOL_USE, context)

        assert result.should_proceed is True

    @pytest.mark.asyncio
    async def test_post_tool_use_logging(self, caplog):
        """测试工具调用后日志"""
        hook = LoggingHook()
        context = HookContext(
            tool_name="test_tool",
            parameters={},
            request_id="req-001",
        )

        result = await hook.process(HookEvent.POST_TOOL_USE, context)

        assert result.should_proceed is True

    @pytest.mark.asyncio
    async def test_failure_logging(self, caplog):
        """测试失败日志"""
        hook = LoggingHook()
        context = HookContext(
            tool_name="test_tool",
            parameters={},
            request_id="req-001",
        )

        result = await hook.process(HookEvent.TOOL_FAILURE, context)

        assert result.should_proceed is True


class TestValidationHook:
    """测试ValidationHook"""

    @pytest.mark.asyncio
    async def test_valid_input(self):
        """测试有效输入"""
        hook = ValidationHook()
        context = HookContext(
            tool_name="test_tool",
            parameters={"key": "value"},
            request_id="req-001",
        )

        result = await hook.process(HookEvent.PRE_TOOL_USE, context)

        assert result.should_proceed is True

    @pytest.mark.asyncio
    async def test_empty_parameters(self):
        """测试空参数"""
        hook = ValidationHook()
        context = HookContext(
            tool_name="test_tool",
            parameters={},
            request_id="req-001",
        )

        result = await hook.process(HookEvent.PRE_TOOL_USE, context)

        assert result.should_proceed is False
        assert "参数不能为空" in result.error_message

    @pytest.mark.asyncio
    async def test_invalid_tool_name(self):
        """测试无效工具名称"""
        hook = ValidationHook()
        context = HookContext(
            tool_name="",
            parameters={"key": "value"},
            request_id="req-001",
        )

        result = await hook.process(HookEvent.PRE_TOOL_USE, context)

        assert result.should_proceed is False
        assert "工具名称无效" in result.error_message

    @pytest.mark.asyncio
    async def test_empty_request_id(self):
        """测试空请求ID"""
        hook = ValidationHook()
        context = HookContext(
            tool_name="test_tool",
            parameters={"key": "value"},
            request_id="",
        )

        result = await hook.process(HookEvent.PRE_TOOL_USE, context)

        assert result.should_proceed is False
        assert "请求ID不能为空" in result.error_message


class TestRateLimitHook:
    """测试RateLimitHook"""

    @pytest.mark.asyncio
    async def test_within_limit(self):
        """测试在限制内"""
        hook = RateLimitHook(max_calls=5, window_seconds=60)

        context = HookContext(
            tool_name="test_tool",
            parameters={},
        )

        for _i in range(5):
            result = await hook.process(HookEvent.PRE_TOOL_USE, context)
            assert result.should_proceed is True

    @pytest.mark.asyncio
    async def test_exceeds_limit(self):
        """测试超过限制"""
        hook = RateLimitHook(max_calls=3, window_seconds=60)

        context = HookContext(
            tool_name="test_tool",
            parameters={},
        )

        # 前3次成功
        for _i in range(3):
            result = await hook.process(HookEvent.PRE_TOOL_USE, context)
            assert result.should_proceed is True

        # 第4次被阻止
        result = await hook.process(HookEvent.PRE_TOOL_USE, context)
        assert result.should_proceed is False
        assert "速率限制" in result.error_message

    @pytest.mark.asyncio
    async def test_reset(self):
        """测试重置计数"""
        hook = RateLimitHook(max_calls=2, window_seconds=60)

        context = HookContext(
            tool_name="test_tool",
            parameters={},
        )

        # 达到限制
        for _i in range(2):
            await hook.process(HookEvent.PRE_TOOL_USE, context)

        result = await hook.process(HookEvent.PRE_TOOL_USE, context)
        assert result.should_proceed is False

        # 重置
        hook.reset("test_tool")

        # 再次调用应该成功
        result = await hook.process(HookEvent.PRE_TOOL_USE, context)
        assert result.should_proceed is True


class TestMetricsHook:
    """测试MetricsHook"""

    @pytest.mark.asyncio
    async def test_track_call_count(self):
        """测试调用次数统计"""
        hook = MetricsHook()

        context = HookContext(
            tool_name="test_tool",
            parameters={},
        )

        await hook.process(HookEvent.PRE_TOOL_USE, context)
        await hook.process(HookEvent.PRE_TOOL_USE, context)

        metrics = hook.get_metrics("test_tool")
        assert metrics["call_count"] == 2

    @pytest.mark.asyncio
    async def test_track_execution_time(self):
        """测试执行时间统计"""
        import time

        hook = MetricsHook()

        context = HookContext(
            tool_name="test_tool",
            parameters={},
        )

        # 开始调用
        await hook.process(HookEvent.PRE_TOOL_USE, context)
        time.sleep(0.01)  # 模拟执行
        await hook.process(HookEvent.POST_TOOL_USE, context)

        metrics = hook.get_metrics("test_tool")
        assert metrics["avg_execution_time"] > 0

    @pytest.mark.asyncio
    async def test_get_all_metrics(self):
        """测试获取所有工具指标"""
        hook = MetricsHook()

        ctx1 = HookContext(tool_name="tool1", parameters={})
        ctx2 = HookContext(tool_name="tool2", parameters={})

        await hook.process(HookEvent.PRE_TOOL_USE, ctx1)
        await hook.process(HookEvent.PRE_TOOL_USE, ctx2)

        all_metrics = hook.get_metrics()
        assert "tool1" in all_metrics
        assert "tool2" in all_metrics


class TestUtilityFunctions:
    """测试便捷函数"""

    def test_create_default_hooks(self):
        """测试创建默认Hook"""
        hooks = create_default_hooks()

        assert len(hooks) == 4

        hook_types = [type(h).__name__ for h in hooks]
        assert "ValidationHook" in hook_types
        assert "RateLimitHook" in hook_types
        assert "MetricsHook" in hook_types
        assert "LoggingHook" in hook_types

    def test_register_default_hooks(self):
        """测试注册默认Hook"""
        registry = HookRegistry()
        register_default_hooks(registry)

        stats = registry.get_stats()
        # 每个Hook注册到3个事件 (PRE, POST, FAILURE)
        assert stats["total_hooks"] == 12  # 4 hooks * 3 events
