#!/usr/bin/env python3
"""
事件系统单元测试

测试事件总线的发布/订阅功能。

作者: Athena平台团队
创建时间: 2026-04-20
"""
from __future__ import annotations

import asyncio
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_event_bus():
    """测试事件总线"""
    from core.events.event_bus import EventBus, CallbackSubscriber, QueueSubscriber
    from core.events.event_types import AgentStarted, AgentStopped

    print("\n=== 测试事件总线 ===")

    # 创建事件总线
    bus = EventBus()

    # 创建回调订阅者
    received_events = []

    async def on_agent_started(event: AgentStarted):
        received_events.append(("started", event.agent_id))
        print(f"✅ 收到 AgentStarted 事件: {event.agent_id}")

    subscriber = CallbackSubscriber(
        callback=on_agent_started,
        event_type=AgentStarted,
    )

    # 订阅事件
    subscription_id = await bus.subscribe(AgentStarted, subscriber)
    print(f"✅ 订阅成功: {subscription_id}")

    # 发布事件
    event1 = AgentStarted(
        agent_id="xiaona",
        agent_type="legal",
        agent_name="小娜",
    )
    await bus.publish(event1)

    # 发布另一个事件
    event2 = AgentStarted(
        agent_id="xiaonuo",
        agent_type="coordinator",
        agent_name="小诺",
    )
    await bus.publish(event2)

    # 等待事件处理完成
    await asyncio.sleep(0.1)

    # 验证
    assert len(received_events) == 2, f"应该收到 2 个事件，实际收到 {len(received_events)} 个"
    print(f"✅ 收到事件数量: {len(received_events)}")

    # 测试事件历史
    history = bus.get_history(AgentStarted)
    print(f"✅ 事件历史数量: {len(history)}")

    # 测试统计
    stats = bus.get_stats()
    print(f"✅ 订阅统计: {stats}")

    # 取消订阅
    await bus.unsubscribe(subscription_id)
    print("✅ 订阅已取消")

    print("✅ 事件总线测试完成")


async def test_event_types():
    """测试事件类型序列化"""
    from core.events.event_types import AgentStarted, AgentStopped, ToolExecutionStarted

    print("\n=== 测试事件类型 ===")

    # 创建事件
    event = AgentStarted(
        agent_id="xiaona",
        agent_type="legal",
        agent_name="小娜",
        capabilities=["patent_search", "patent_analysis"],
    )

    # 测试序列化
    event_dict = event.to_dict()
    print(f"✅ 事件序列化: {len(event_dict)} 个字段")

    # 测试 JSON
    event_json = event.to_json()
    print(f"✅ 事件 JSON: {len(event_json)} 字符")

    # 测试反序列化
    restored_event = AgentStarted.from_dict(event_dict)
    assert restored_event.agent_id == event.agent_id
    print(f"✅ 事件反序列化成功: {restored_event.agent_id}")

    print("✅ 事件类型测试完成")


async def main():
    """主函数"""
    print("🧪 开始事件系统测试...")

    await test_event_types()
    await test_event_bus()

    print("\n🎉 所有测试完成！")


if __name__ == "__main__":
    asyncio.run(main())
