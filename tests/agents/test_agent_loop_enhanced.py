#!/usr/bin/env python3
"""
Agent Loop 增强版单元测试

测试流式响应、LLM 适配器和事件发布集成。

作者: Athena平台团队
创建时间: 2026-04-20
"""
from __future__ import annotations

import asyncio
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_streaming_handler():
    """测试流式处理器"""
    from core.agents.streaming_handler import (
        LoggingStreamingHandler,
        StreamingHandler,
    )
    from core.agents.stream_events import (
        AssistantTextDelta,
        StatusEvent,
        stream_event_to_json,
    )

    print("\n=== 测试流式处理器 ===")

    # 创建流式处理器
    handler = LoggingStreamingHandler()
    await handler.start()

    # 发送测试事件
    await handler.emit(AssistantTextDelta(text="Hello, "))
    await handler.emit(AssistantTextDelta(text="world!"))
    await handler.emit(StatusEvent(message="测试完成", level="info"))

    # 等待处理
    await asyncio.sleep(0.2)

    # 检查统计
    stats = handler.get_stats()
    print(f"✅ 流式处理器统计: {stats}")

    # 停止处理器
    await handler.stop()

    # 测试事件序列化
    event = AssistantTextDelta(text="测试")
    event_json = stream_event_to_json(event)
    print(f"✅ 事件序列化: {event_json}")

    print("✅ 流式处理器测试完成")


async def test_llm_adapter():
    """测试 LLM 适配器"""
    from core.agents.llm_adapter import LLMAdapter, LLMRequest

    print("\n=== 测试 LLM 适配器 ===")

    # 创建 LLM 适配器
    adapter = LLMAdapter()

    # 创建请求
    request = LLMRequest(
        messages=[
            {"role": "system", "content": "你是一个测试助手。"},
            {"role": "user", "content": "说 'Hello'"},
        ],
        tools=[],
        stream=False,
    )

    # 调用 LLM（非流式）
    print("📞 调用 LLM（非流式）...")
    response = await adapter.call_llm(request)
    print(f"✅ LLM 响应: {response.content[:100]}...")
    print(f"   停止原因: {response.stop_reason}")

    # 测试流式调用
    print("\n📞 调用 LLM（流式）...")
    async for event in adapter.call_llm_stream(request):
        if event.__class__.__name__ == "AssistantTextDelta":
            print(f"   增量: {event.text}")
        elif event.__class__.__name__ == "AssistantTurnComplete":
            print(f"✅ 流式调用完成")
            break

    # 检查统计
    stats = adapter.get_stats()
    print(f"✅ LLM 适配器统计: {stats}")

    print("✅ LLM 适配器测试完成")


async def test_event_publisher():
    """测试事件发布器"""
    from core.agents.event_publisher import AgentEventPublisher
    from core.events.event_bus import get_global_event_bus, CallbackSubscriber
    from core.events.event_types import AgentStarted, ToolExecutionStarted

    print("\n=== 测试事件发布器 ===")

    # 创建事件总线
    event_bus = get_global_event_bus()

    # 创建事件发布器
    publisher = AgentEventPublisher(
        agent_id="test_agent",
        agent_type="test",
        agent_name="测试代理",
    )

    # 订阅事件
    received_events = []

    async def on_event(event):
        received_events.append(event)
        print(f"✅ 收到事件: {event.__class__.__name__}")

    subscriber = CallbackSubscriber(callback=on_event, event_type=AgentStarted)
    await event_bus.subscribe(AgentStarted, subscriber)

    # 发布代理启动事件
    await publisher.publish_agent_started(capabilities=["test", "demo"])

    # 等待事件处理
    await asyncio.sleep(0.1)

    # 验证
    assert len(received_events) >= 1
    print(f"✅ 收到事件数量: {len(received_events)}")

    # 发布工具执行事件
    await publisher.publish_tool_execution_started(
        tool_id="test_tool",
        tool_name="test_tool",
        tool_use_id="test_123",
        parameters={"query": "test"},
    )

    # 检查统计
    stats = publisher.get_stats()
    print(f"✅ 事件发布器统计: {stats}")

    print("✅ 事件发布器测试完成")


async def test_enhanced_agent_loop():
    """测试增强版 Agent Loop"""
    from core.agents.agent_loop_enhanced import (
        AgentLoopConfig,
        EnhancedAgentLoop,
        create_enhanced_agent_loop,
    )

    print("\n=== 测试增强版 Agent Loop ===")

    # 创建配置
    config = AgentLoopConfig(
        agent_name="xiaona",
        agent_type="legal",
        system_prompt="你是一个专利法律专家助手。请简洁回答。",
        max_iterations=3,
        enable_streaming=True,
        enable_events=True,
    )

    # 创建增强版 Agent Loop
    agent_loop = EnhancedAgentLoop(config)

    # 初始化
    await agent_loop.initialize()

    # 测试简单运行
    print("\n📞 测试简单运行...")
    result = await agent_loop.run("请用一句话介绍你自己。")
    print(f"✅ 运行结果: {result.content[:100]}...")
    print(f"   迭代次数: {result.iterations}")
    print(f"   工具执行: {result.tool_executions}")
    print(f"   总耗时: {result.total_time:.2f}秒")

    # 检查统计
    stats = agent_loop.get_stats()
    print(f"✅ Agent Loop 统计: {stats}")

    # 关闭
    await agent_loop.shutdown()

    print("✅ 增强版 Agent Loop 测试完成")


async def test_enhanced_agent_loop_stream():
    """测试增强版 Agent Loop 流式执行"""
    from core.agents.agent_loop_enhanced import create_enhanced_agent_loop

    print("\n=== 测试增强版 Agent Loop 流式执行 ===")

    # 创建增强版 Agent Loop
    agent_loop = create_enhanced_agent_loop(
        agent_name="xiaonuo",
        agent_type="coordinator",
        system_prompt="你是一个任务协调助手。请简洁回答。",
        enable_streaming=True,
        enable_events=False,  # 流式测试时禁用事件以减少噪音
    )

    # 初始化
    await agent_loop.initialize()

    # 测试流式运行
    print("\n📞 测试流式运行...")
    event_count = 0

    async for event in agent_loop.run_stream("数到3"):
        event_count += 1
        event_type = event.__class__.__name__
        print(f"   [{event_count}] {event_type}")

        if event_type == "AssistantTextDelta":
            print(f"      文本: {event.text}")
        elif event_type == "StatusEvent":
            print(f"      状态: {event.message}")
        elif event_type == "ErrorEvent":
            print(f"      错误: {event.message}")

    print(f"✅ 流式执行完成，共收到 {event_count} 个事件")

    # 关闭
    await agent_loop.shutdown()

    print("✅ 增强版 Agent Loop 流式执行测试完成")


async def main():
    """主函数"""
    print("🧪 开始 Agent Loop 增强版测试...")
    print("=" * 60)

    try:
        await test_streaming_handler()
        await test_llm_adapter()
        await test_event_publisher()
        await test_enhanced_agent_loop()
        await test_enhanced_agent_loop_stream()

        print("\n" + "=" * 60)
        print("🎉 所有测试完成！")

    except Exception as e:
        logger.error(f"❌ 测试失败: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
