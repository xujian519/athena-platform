#!/usr/bin/env python3
"""
Hook系统独立测试脚本

用于验证Hook系统的基本功能。
"""

import asyncio
import sys

# 添加路径
sys.path.insert(0, '/Users/xujian/Athena工作平台')

from core.tools.hooks import (
    BaseHook,
    HookContext,
    HookEvent,
    HookRegistry,
    HookResult,
    MetricsHook,
    RateLimitHook,
    ValidationHook,
    create_default_hooks,
    register_default_hooks,
)


class MockHook(BaseHook):
    """Mock Hook用于测试"""

    def __init__(self, hook_id: str, should_proceed: bool = True, priority: int = 10):
        super().__init__(hook_id=hook_id, priority=priority)
        self.should_proceed = should_proceed
        self.call_count = 0

    async def process(
        self, event: HookEvent, hook_context: HookContext
    ) -> HookResult:
        """Mock处理方法"""
        self.call_count += 1
        return HookResult(should_proceed=self.should_proceed)


async def test_hook_context():
    """测试HookContext"""
    print("\n📝 测试 HookContext...")

    ctx = HookContext(
        tool_name="test_tool",
        parameters={"key": "value"},
    )

    assert ctx.tool_name == "test_tool"
    assert ctx.parameters == {"key": "value"}
    print("✅ HookContext测试通过")


async def test_hook_result():
    """测试HookResult"""
    print("\n📝 测试 HookResult...")

    result = HookResult(
        should_proceed=False,
        error_message="权限不足",
    )

    assert result.should_proceed is False
    assert result.error_message == "权限不足"
    print("✅ HookResult测试通过")


async def test_hook_registry():
    """测试HookRegistry"""
    print("\n📝 测试 HookRegistry...")

    registry = HookRegistry()

    # 测试注册
    hook = MockHook(hook_id="test_hook", should_proceed=True)
    events = [HookEvent.PRE_TOOL_USE]
    registry.register(hook, events)

    stats = registry.get_stats()
    assert stats["total_hooks"] == 1
    print("✅ HookRegistry注册测试通过")

    # 测试执行
    context = HookContext(
        tool_name="test_tool",
        parameters={},
    )

    result = await registry.execute_hooks(HookEvent.PRE_TOOL_USE, context)
    assert result.should_proceed is True
    assert hook.call_count == 1
    print("✅ HookRegistry执行测试通过")


async def test_validation_hook():
    """测试ValidationHook"""
    print("\n📝 测试 ValidationHook...")

    hook = ValidationHook()

    # 有效输入
    context = HookContext(
        tool_name="test_tool",
        parameters={"key": "value"},
        request_id="req-001",
    )

    result = await hook.process(HookEvent.PRE_TOOL_USE, context)
    assert result.should_proceed is True
    print("✅ ValidationHook有效输入测试通过")

    # 无效输入（空参数）
    context = HookContext(
        tool_name="test_tool",
        parameters={},
        request_id="req-001",
    )

    result = await hook.process(HookEvent.PRE_TOOL_USE, context)
    assert result.should_proceed is False
    print("✅ ValidationHook无效输入测试通过")


async def test_rate_limit_hook():
    """测试RateLimitHook"""
    print("\n📝 测试 RateLimitHook...")

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
    print("✅ RateLimitHook测试通过")


async def test_metrics_hook():
    """测试MetricsHook"""
    print("\n📝 测试 MetricsHook...")

    hook = MetricsHook()
    context = HookContext(
        tool_name="test_tool",
        parameters={},
    )

    await hook.process(HookEvent.PRE_TOOL_USE, context)
    await hook.process(HookEvent.PRE_TOOL_USE, context)

    metrics = hook.get_metrics("test_tool")
    assert metrics["call_count"] == 2
    print("✅ MetricsHook测试通过")


async def test_default_hooks():
    """测试默认Hook"""
    print("\n📝 测试默认Hook...")

    hooks = create_default_hooks()
    assert len(hooks) == 4
    print("✅ 创建默认Hook测试通过")

    registry = HookRegistry()
    register_default_hooks(registry)

    stats = registry.get_stats()
    # 每个Hook注册到3个事件 (PRE, POST, FAILURE)
    assert stats["total_hooks"] == 12  # 4 hooks * 3 events
    print("✅ 注册默认Hook测试通过")


async def main():
    """运行所有测试"""
    print("=" * 60)
    print("🧪 Hook系统测试套件")
    print("=" * 60)

    try:
        await test_hook_context()
        await test_hook_result()
        await test_hook_registry()
        await test_validation_hook()
        await test_rate_limit_hook()
        await test_metrics_hook()
        await test_default_hooks()

        print("\n" + "=" * 60)
        print("✅ 所有测试通过！")
        print("=" * 60)
        return 0

    except AssertionError as e:
        print(f"\n❌ 测试失败: {e}")
        return 1
    except Exception as e:
        print(f"\n❌ 测试异常: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
