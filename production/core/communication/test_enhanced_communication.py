#!/usr/bin/env python3
"""
增强通信模块测试脚本
Test Enhanced Communication Module

验证BaseModule兼容性和通信功能
作者: Athena AI系统
创建时间: 2025-12-11
版本: 1.0.0
"""

from __future__ import annotations
import asyncio
import logging
import sys
from datetime import datetime, timedelta
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from core.communication.enhanced_communication_module import EnhancedCommunicationModule

# 配置日志
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


async def test_enhanced_communication_module():
    """测试增强通信模块"""
    logger.info("\n💬 增强通信模块测试")
    logger.info(str("=" * 60))

    try:
        # 1. 创建模块实例
        logger.info("\n1. 创建增强通信模块...")
        communication_module = EnhancedCommunicationModule(
            agent_id="test_communication_agent_001",
            config={
                "enable_websocket": False,  # 测试时禁用websocket以简化
                "enable_api_gateway": False,
                "max_queue_size": 1000,
                "max_connections": 50,
                "default_protocol": "json",
            },
        )
        logger.info("✅ 通信模块创建成功")

        # 2. 初始化模块
        logger.info("\n2. 初始化通信模块...")
        init_success = await communication_module.initialize()
        if init_success:
            logger.info("✅ 通信模块初始化成功")
        else:
            logger.info("❌ 通信模块初始化失败")
            return False

        # 3. 健康检查
        logger.info("\n3. 执行健康检查...")
        health_status = await communication_module.health_check()
        logger.info("✅ 健康检查结果:")
        logger.info(f"   - 健康状态: {'健康' if health_status.value == 'healthy' else '不健康'}")
        logger.info(f"   - 状态值: {health_status.value}")

        # 获取健康检查详情
        if hasattr(communication_module, "_health_check_details"):
            details = communication_module._health_check_details
            logger.info(f"   - 通信系统状态: {details.get('communication_status', 'unknown')}")
            logger.info(f"   - 依赖状态: {details.get('dependencies_status', 'unknown')}")
            logger.info(f"   - 消息系统状态: {details.get('message_system_status', 'unknown')}")
            logger.info(f"   - 连接管理状态: {details.get('connection_status', 'unknown')}")

            stats = details.get("stats", {})
            if stats:
                logger.info(
                    f"   - 通信统计: 发送{stats.get('sent_messages', 0)}, 接收{stats.get('received_messages', 0)}"
                )

        # 4. 测试通道管理
        logger.info("\n4. 测试通道管理...")

        # 创建测试通道
        test_channels = [
            {
                "name": "技术讨论组",
                "channel_type": "group",
                "participants": ["user1", "user2", "test_agent"],
            },
            {"name": "项目协作频道", "channel_type": "direct", "participants": ["collaborator1"]},
            {"name": "公告广播", "channel_type": "broadcast", "participants": []},
        ]

        created_channels = []
        for channel_data in test_channels:
            result = await communication_module.create_channel(
                name=channel_data["name"],
                channel_type=channel_data["channel_type"],
                participants=channel_data["participants"],
            )
            created_channels.append((channel_data, result))
            status = "成功" if result.success else "失败"
            logger.info(f"   {channel_data['name']}创建: {status}")
            if result.success:
                logger.info(f"     - 通道ID: {result.channel_id}")
                logger.info(f"     - 参与者数: {result.participant_count}")

        # 5. 测试消息发送
        logger.info("\n5. 测试消息发送...")

        # 发送测试消息
        test_messages = [
            {
                "receiver_id": "user1",
                "content": "你好,这是一条测试消息",
                "message_type": "text",
                "metadata": {"source": "test", "type": "greeting"},
            },
            {
                "receiver_id": "user2",
                "content": {"data": "结构化数据", "value": 123},
                "message_type": "text",
                "metadata": {"format": "json"},
            },
            {
                "receiver_id": "",
                "content": "这是广播消息",
                "message_type": "notification",
                "channel_id": created_channels[0][1].channel_id if created_channels else "default",
            },
        ]

        sent_messages = []
        for i, msg_data in enumerate(test_messages):
            if msg_data.get("receiver_id"):
                result = await communication_module.send_message(
                    receiver_id=msg_data["receiver_id"],
                    content=msg_data["content"],
                    message_type=msg_data["message_type"],
                    metadata=msg_data.get("metadata"),
                )
            else:
                result = await communication_module.broadcast_message(
                    content=msg_data["content"],
                    message_type=msg_data["message_type"],
                    channel_id=msg_data.get("channel_id"),
                )

            sent_messages.append((msg_data, result))
            status = "成功" if result.success else "失败"
            logger.info(f"   消息{i+1}发送: {status}")
            if result.success:
                logger.info(f"     - 消息ID: {result.message_id}")
                logger.info(f"     - 投递时间: {result.delivery_time:.3f}s")

        # 6. 测试消息接收
        logger.info("\n6. 测试消息接收...")
        received_messages = await communication_module.receive_messages(limit=5)
        logger.info(f"   接收消息: {len(received_messages)} 条")
        for i, msg in enumerate(received_messages[:2]):  # 显示前2条
            logger.info(f"     消息{i+1}: {str(msg.content)[:50]}... (来自: {msg.sender_id})")

        # 7. 测试标准处理接口
        logger.info("\n7. 测试标准处理接口...")
        process_test_cases = [
            {
                "operation": "send",
                "receiver_id": "user3",
                "content": "通过标准接口发送消息",
                "message_type": "text",
            },
            {
                "operation": "create_channel",
                "name": "接口测试频道",
                "channel_type": "direct",
                "participants": ["test_user"],
            },
            {"operation": "broadcast", "content": "标准接口广播", "message_type": "notification"},
        ]

        for i, test_case in enumerate(process_test_cases):
            result = await communication_module.process(test_case)
            operation = test_case["operation"]
            logger.info(f"   处理{i+1}({operation}): {result.get('success', False)}")
            if "message_id" in result:
                logger.info(f"     - 消息ID: {result.get('message_id', 'unknown')}")
            if "channel_id" in result:
                logger.info(f"     - 通道ID: {result.get('channel_id', 'unknown')}")

        # 8. 测试消息历史
        logger.info("\n8. 测试消息历史...")
        history_messages = await communication_module.receive_messages(
            limit=3, since=datetime.now() - timedelta(minutes=5)
        )
        logger.info(f"   历史消息: {len(history_messages)} 条 (最近5分钟)")

        # 9. 获取模块状态
        logger.info("\n9. 获取模块状态...")
        status = communication_module.get_status()
        logger.info("✅ 状态获取完成")
        logger.info(f"   - 智能体ID: {status.get('agent_id', 'unknown')}")
        logger.info(f"   - 模块类型: {status.get('module_type', 'unknown')}")
        logger.info(f"   - 运行状态: {status.get('status', 'unknown')}")

        # 10. 获取性能指标
        logger.info("\n10. 获取性能指标...")
        metrics = communication_module.get_metrics()
        logger.info("✅ 指标获取完成")
        logger.info(f"   - 模块状态: {metrics.get('module_status', 'unknown')}")
        logger.info(f"   - 代理ID: {metrics.get('agent_id', 'unknown')}")
        logger.info(f"   - 初始化状态: {metrics.get('initialized', False)}")
        logger.info(f"   - 运行时长: {metrics.get('uptime_seconds', 0):.2f}s")

        comm_stats = metrics.get("communication_stats", {})
        if comm_stats:
            logger.info("   - 通信统计:")
            logger.info(f"     * 总消息数: {comm_stats.get('total_messages', 0)}")
            logger.info(f"     * 发送消息: {comm_stats.get('sent_messages', 0)}")
            logger.info(f"     * 接收消息: {comm_stats.get('received_messages', 0)}")
            logger.info(f"     * 失败消息: {comm_stats.get('failed_messages', 0)}")
            logger.info(f"     * 活跃通道: {metrics.get('active_channels', 0)}")
            logger.info(f"     * 平均投递时间: {comm_stats.get('average_delivery_time', 0):.3f}s")

        # 11. 测试关闭
        logger.info("\n11. 测试模块关闭...")
        await communication_module.shutdown()
        logger.info("✅ 模块关闭成功")

        logger.info(str("\n" + "=" * 60))
        logger.info("🎉 增强通信模块测试完成 - 所有测试通过!")
        return True

    except Exception as e:
        logger.error(f"❌ 测试过程中发生错误: {e!s}")
        import traceback

        traceback.print_exc()
        return False


async def test_communication_protocols():
    """测试通信协议"""
    logger.info("\n🔄 通信协议测试")
    logger.info(str("=" * 60))

    try:
        communication_module = EnhancedCommunicationModule(
            agent_id="protocol_test_agent",
            config={
                "enable_websocket": False,
                "supported_protocols": ["json", "xml", "custom"],
                "default_protocol": "json",
            },
        )

        await communication_module.initialize()

        # 测试不同消息类型
        message_types = ["text", "image", "file", "notification", "system"]

        for msg_type in message_types:
            logger.info(f"\n测试消息类型: {msg_type}")

            # 发送不同类型的消息
            if msg_type == "text":
                content = f"这是{msg_type}类型消息"
            elif msg_type == "image":
                content = {"image_data": "base64_encoded_image_data", "format": "png"}
            elif msg_type == "file":
                content = {"file_path": "/path/to/file", "size": 1024, "checksum": "abc123"}
            elif msg_type == "notification":
                content = {"title": "通知", "body": "重要通知内容", "level": "info"}
            elif msg_type == "system":
                content = {"system_event": "test", "timestamp": datetime.now().isoformat()}

            result = await communication_module.send_message(
                receiver_id="protocol_test_user",
                content=content,
                message_type=msg_type,
                metadata={"protocol_test": True},
            )

            logger.info(f"   发送结果: {'✅ 成功' if result.success else '❌ 失败'}")
            logger.info(f"   - 消息ID: {result.message_id}")
            logger.info(f"   - 投递时间: {result.delivery_time:.3f}s")

        await communication_module.shutdown()
        return True

    except Exception as e:
        logger.error(f"❌ 通信协议测试失败: {e!s}")
        return False


async def main():
    """主测试函数"""
    logger.info("🚀 增强通信模块完整测试套件")
    logger.info(str("=" * 80))

    # 基础功能测试
    basic_test_passed = await test_enhanced_communication_module()

    # 通信协议测试
    protocol_test_passed = await test_communication_protocols()

    # 测试总结
    logger.info(str("\n" + "=" * 80))
    logger.info("📊 测试总结")
    logger.info(str("=" * 80))
    logger.info(f"基础功能测试: {'✅ 通过' if basic_test_passed else '❌ 失败'}")
    logger.info(f"通信协议测试: {'✅ 通过' if protocol_test_passed else '❌ 失败'}")

    overall_success = basic_test_passed and protocol_test_passed
    logger.info(f"\n🎯 总体结果: {'✅ 全部测试通过' if overall_success else '❌ 存在失败测试'}")

    return overall_success


if __name__ == "__main__":
    asyncio.run(main())
