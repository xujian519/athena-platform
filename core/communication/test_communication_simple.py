#!/usr/bin/env python3
from __future__ import annotations
"""
简化的通信模块测试脚本
Simple Communication Module Test Script

验证修复版的增强通信模块功能
作者: Athena AI系统
创建时间: 2025-12-11
版本: 1.0.0
"""

import asyncio
import logging
import sys
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from core.communication.enhanced_communication_module import EnhancedCommunicationModule

# 配置日志
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


async def test_communication_module_basic():
    """基础通信模块测试"""
    logger.info("\n💬 基础通信模块测试")
    logger.info(str("=" * 50))

    try:
        # 1. 创建模块
        logger.info("\n1. 创建通信模块...")
        comm_module = EnhancedCommunicationModule(
            agent_id="test_comm_agent",
            config={
                "enable_websocket": False,  # 简化测试
                "enable_api_gateway": False,
                "max_queue_size": 100,
            },
        )
        logger.info("✅ 通信模块创建成功")

        # 2. 初始化模块
        logger.info("\n2. 初始化通信模块...")
        init_success = await comm_module.initialize()
        logger.info(f"✅ 初始化结果: {init_success}")

        # 3. 健康检查
        logger.info("\n3. 执行健康检查...")
        health_status = await comm_module.health_check()
        logger.info(f"✅ 健康状态: {health_status.value}")

        # 4. 创建通道
        logger.info("\n4. 测试创建通道...")
        channel_result = await comm_module.create_channel(
            name="测试通道", channel_type="direct", participants=["user1", "user2"]
        )
        logger.info(f"✅ 通道创建: {channel_result.success}")
        logger.info(f"   - 通道ID: {channel_result.channel_id}")
        logger.info(f"   - 参与者数: {channel_result.participant_count}")

        # 5. 发送消息
        logger.info("\n5. 测试发送消息...")
        message_result = await comm_module.send_message(
            receiver_id="user1", content="Hello, this is a test message", message_type="text"
        )
        logger.info(f"✅ 消息发送: {message_result.success}")
        logger.info(f"   - 消息ID: {message_result.message_id}")
        logger.info(f"   - 投递时间: {message_result.delivery_time:.3f}s")

        # 6. 广播消息
        logger.info("\n6. 测试广播消息...")
        broadcast_result = await comm_module.broadcast_message(
            content="This is a broadcast message",
            message_type="notification",
            channel_id=channel_result.channel_id,
        )
        logger.info(f"✅ 广播发送: {broadcast_result.success}")
        logger.info(f"   - 消息ID: {broadcast_result.message_id}")

        # 7. 接收消息
        logger.info("\n7. 测试接收消息...")
        messages = await comm_module.receive_messages(limit=5)
        logger.info(f"✅ 接收消息: {len(messages)} 条")
        for i, msg in enumerate(messages[:2]):
            logger.info(f"   - 消息{i+1}: {str(msg.content)[:30]}...")

        # 8. 标准接口测试
        logger.info("\n8. 测试标准处理接口...")
        process_result = await comm_module.process(
            {
                "operation": "send",
                "receiver_id": "user2",
                "content": "Process interface test",
                "message_type": "text",
            }
        )
        logger.info(f"✅ 标准处理: {process_result.get('success', False)}")

        # 9. 获取状态
        logger.info("\n9. 获取模块状态...")
        status = comm_module.get_status()
        logger.info(f"✅ 模块状态: {status.get('status', 'unknown')}")
        logger.info(f"   - 通道数量: {status.get('channels_count', 0)}")
        logger.info(f"   - 运行时间: {status.get('uptime_seconds', 0):.2f}s")

        # 10. 获取指标
        logger.info("\n10. 获取性能指标...")
        metrics = comm_module.get_metrics()
        comm_stats = metrics.get("communication_stats", {})
        logger.info("✅ 性能指标:")
        logger.info(f"   - 总消息数: {comm_stats.get('total_messages', 0)}")
        logger.info(f"   - 发送消息: {comm_stats.get('sent_messages', 0)}")
        logger.info(f"   - 接收消息: {comm_stats.get('received_messages', 0)}")
        logger.info(f"   - 活跃通道: {metrics.get('active_channels', 0)}")

        # 11. 关闭模块
        logger.info("\n11. 关闭通信模块...")
        await comm_module.shutdown()
        logger.info("✅ 模块关闭成功")

        logger.info(str("\n" + "=" * 50))
        logger.info("🎉 基础通信模块测试完成!")
        return True

    except Exception as e:
        logger.error(f"❌ 测试失败: {e!s}")
        import traceback

        traceback.print_exc()
        return False


async def test_communication_advanced():
    """高级通信功能测试"""
    logger.info("\n🔄 高级通信功能测试")
    logger.info(str("=" * 50))

    try:
        comm_module = EnhancedCommunicationModule(
            agent_id="advanced_test_agent",
            config={"enable_websocket": False, "max_queue_size": 200},
        )

        await comm_module.initialize()

        # 测试不同消息类型
        message_types = ["text", "notification", "system"]

        for msg_type in message_types:
            logger.info(f"\n测试消息类型: {msg_type}")

            result = await comm_module.send_message(
                receiver_id=f"test_user_{msg_type}",
                content=f"Test {msg_type} message",
                message_type=msg_type,
            )

            logger.info(f"   发送结果: {'✅' if result.success else '❌'}")
            logger.info(f"   消息ID: {result.message_id}")

        # 测试不同通道类型
        channel_types = ["direct", "group", "broadcast"]

        for ch_type in channel_types:
            logger.info(f"\n测试通道类型: {ch_type}")

            result = await comm_module.create_channel(
                name=f"Test {ch_type} channel",
                channel_type=ch_type,
                participants=[f"user{i}" for i in range(2)],
            )

            logger.info(f"   创建结果: {'✅' if result.success else '❌'}")
            logger.info(f"   通道ID: {result.channel_id}")

        await comm_module.shutdown()
        return True

    except Exception as e:
        logger.error(f"❌ 高级测试失败: {e!s}")
        return False


async def main():
    """主测试函数"""
    logger.info("🚀 通信模块测试套件")
    logger.info(str("=" * 70))

    # 基础功能测试
    basic_test_passed = await test_communication_module_basic()

    # 高级功能测试
    advanced_test_passed = await test_communication_advanced()

    # 测试总结
    logger.info(str("\n" + "=" * 70))
    logger.info("📊 测试总结")
    logger.info(str("=" * 70))
    logger.info(f"基础功能测试: {'✅ 通过' if basic_test_passed else '❌ 失败'}")
    logger.info(f"高级功能测试: {'✅ 通过' if advanced_test_passed else '❌ 失败'}")

    overall_success = basic_test_passed and advanced_test_passed
    logger.info(f"\n🎯 总体结果: {'✅ 全部测试通过' if overall_success else '❌ 存在失败测试'}")

    return overall_success


if __name__ == "__main__":
    asyncio.run(main())
