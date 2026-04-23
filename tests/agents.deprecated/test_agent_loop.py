#!/usr/bin/env python3
"""
Agent Loop 单元测试

测试 Agent Loop 的核心功能。

作者: Athena平台团队
创建时间: 2026-04-20
"""

import asyncio
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_agent_loop_creation():
    """测试 Agent Loop 创建"""
    from core.framework.agents.agent_loop import create_agent_loop

    print("\n=== 测试 Agent Loop 创建 ===")

    # 创建 Agent Loop
    agent_loop = create_agent_loop(
        agent_name="xiaona",
        agent_type="legal",
        system_prompt="你是一个专利法律专家。",
    )

    assert agent_loop.agent_name == "xiaona"
    assert agent_loop.agent_type == "legal"
    print(f"✅ Agent Loop 创建成功: {agent_loop.agent_name}")

    # 测试统计
    stats = agent_loop.get_stats()
    assert stats["total_calls"] == 0
    print(f"✅ 初始统计: {stats}")

    print("✅ Agent Loop 创建测试完成")


async def test_agent_loop_execution():
    """测试 Agent Loop 执行"""
    from core.framework.agents.agent_loop import create_agent_loop

    print("\n=== 测试 Agent Loop 执行 ===")

    # 创建 Agent Loop
    agent_loop = create_agent_loop(
        agent_name="xiaonuo",
        agent_type="coordinator",
        system_prompt="你是一个任务协调专家。",
    )

    # 测试统计信息获取
    stats = agent_loop.get_stats()
    print(f"✅ 统计信息: {stats}")

    # 测试工具执行（模拟简单工具）
    tool_use = {"name": "test_tool", "id": "test_123", "input": {"query": "test"}}
    result = await agent_loop._execute_tool(tool_use)
    print(f"✅ 工具执行结果: success={result.success}, execution_time={result.execution_time:.4f}s")

    # 由于test_tool不存在，预期会失败，但这是正常的
    print(f"   错误信息: {result.error}")

    print("✅ Agent Loop 执行测试完成")


async def test_integration():
    """测试事件系统和 Agent Loop 集成"""
    from core.events.event_bus import CallbackSubscriber, get_global_event_bus
    from core.events.event_types import AgentStarted, AgentStopped

    from core.framework.agents.agent_loop import create_agent_loop

    print("\n=== 测试事件系统和 Agent Loop 集成 ===")

    # 创建事件总线
    event_bus = get_global_event_bus()

    # 创建 Agent Loop
    create_agent_loop(
        agent_name="xiaona",
        agent_type="legal",
        system_prompt="你是一个专利法律专家。",
    )

    # 订阅代理生命周期事件
    lifecycle_events = []

    async def on_lifecycle_event(event):
        lifecycle_events.append(event)
        print(f"✅ 收到事件: {event.__class__.__name__} - {event.agent_id}")

    subscriber = CallbackSubscriber(
        callback=on_lifecycle_event,
        event_type=AgentStarted,  # 将在测试中处理两种事件
    )

    await event_bus.subscribe(AgentStarted, subscriber)
    await event_bus.subscribe(AgentStopped, subscriber)

    # 模拟代理启动事件
    event = AgentStarted(
        agent_id="xiaona",
        agent_type="legal",
        agent_name="小娜",
    )
    await event_bus.publish(event)

    # 等待事件处理
    await asyncio.sleep(0.1)

    # 验证
    assert len(lifecycle_events) >= 1
    print(f"✅ 收到事件数量: {len(lifecycle_events)}")

    print("✅ 集成测试完成")


async def main():
    """主函数"""
    print("🧪 开始 Agent Loop 测试...")

    await test_agent_loop_creation()
    await test_agent_loop_execution()
    await test_integration()

    print("\n🎉 所有测试完成！")


if __name__ == "__main__":
    asyncio.run(main())

