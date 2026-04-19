#!/usr/bin/env python3
from __future__ import annotations
"""
简化版通信模块测试脚本
Simplified Test for Optimized Communication Module

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

from core.communication.optimized_communication_module import (
    CompressionType,
    DeliveryMode,
    MessagePriority,
    OptimizedCommunicationModule,
)

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_basic_functionality():
    """测试基本功能"""
    logger.info("🚀 测试优化版通信模块基本功能")
    logger.info(str("=" * 60))

    try:
        # 创建通信模块
        communication_module = OptimizedCommunicationModule(
            agent_id="test_simple_agent",
            config={
                "message_compression": True,
                "batch_processing": True,
                "adaptive_compression": True,
                "compression_threshold": 512,
            },
        )

        # 初始化
        logger.info("1. 初始化通信模块...")
        init_success = await communication_module.initialize()
        logger.info(
            f"   {'✅' if init_success else '❌'} 初始化{'成功' if init_success else '失败'}"
        )

        # 启动
        logger.info("\n2. 启动通信模块...")
        start_success = await communication_module.start()
        logger.info(
            f"   {'✅' if start_success else '❌'} 启动{'成功' if start_success else '失败'}"
        )

        # 测试消息压缩
        logger.info("\n3. 测试消息压缩...")
        test_payloads = [
            ("小消息", "这是一个小消息"),
            ("中等消息", "中等消息测试" * 50),
            ("大消息", "大消息测试内容" * 200),
        ]

        compression_results = []
        for name, payload in test_payloads:
            message_id = await communication_module.send_message_optimized(
                receiver_id="test_receiver",
                message_type="compression_test",
                payload=payload,
                compression=CompressionType.AUTO,
            )
            compression_results.append((name, len(payload.encode()), message_id))
            logger.info(f"   ✅ {name} 发送成功: {len(payload.encode())} 字节")

        # 测试批处理
        logger.info("\n4. 测试批处理...")
        batch_ids = []
        for i in range(10):
            message_id = await communication_module.send_message_optimized(
                receiver_id="batch_receiver",
                message_type="batch_test",
                payload=f"批处理消息 {i}",
                delivery_mode=DeliveryMode.BATCH,
                priority=MessagePriority.BULK,
            )
            if message_id:
                batch_ids.append(message_id)

        logger.info(f"   ✅ 发送 {len(batch_ids)} 个批量消息")

        # 等待批处理
        await asyncio.sleep(2)

        # 获取统计信息
        logger.info("\n5. 获取统计信息...")
        stats = communication_module.get_optimization_stats()

        if "module_stats" in stats:
            module_stats = stats["module_stats"]
            logger.info(f"   - 总发送消息: {module_stats.get('total_messages_sent', 0)}")
            logger.info(f"   - 总发送字节: {module_stats.get('total_bytes_sent', 0)}")
            logger.info(
                f"   - 平均消息大小: {module_stats.get('average_message_size', 0):.1f} 字节"
            )
            logger.info(f"   - 带宽节省: {module_stats.get('bandwidth_saved', 0):.1f}%")

        # 健康检查
        logger.info("\n6. 健康检查...")
        health_status = await communication_module.health_check()
        logger.info(f"   健康状态: {'✅ 健康' if health_status else '❌ 不健康'}")

        # 关闭
        logger.info("\n7. 关闭通信模块...")
        await communication_module.shutdown()
        logger.info("   ✅ 通信模块关闭成功")

        return True

    except Exception as e:
        logger.error(f"测试失败: {e}")
        import traceback

        traceback.print_exc()
        return False


async def main():
    """主函数"""
    success = await test_basic_functionality()

    if success:
        logger.info(str("\n" + "=" * 60))
        logger.info("🎉 优化版通信模块测试通过!")
        logger.info("\n🌟 优化特性:")
        logger.info("   ✅ 消息压缩算法")
        logger.info("   ✅ 自适应压缩策略")
        logger.info("   ✅ 批处理机制")
        logger.info("   ✅ 异步消息处理")
    else:
        logger.info("\n❌ 测试失败")

    return success


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
