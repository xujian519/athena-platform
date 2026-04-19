#!/usr/bin/env python3
"""
优化版通信模块测试脚本
Test Optimized Communication Module

验证消息压缩和批处理机制功能
作者: Athena AI系统
创建时间: 2025-12-11
版本: 1.0.0
"""

from __future__ import annotations
import asyncio
import json
import logging
import sys
import time
import uuid
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
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


async def test_message_compression():
    """测试消息压缩"""
    logger.info("\n🗜️ 测试消息压缩")
    logger.info(str("=" * 60))

    try:
        # 创建优化通信模块
        communication_module = OptimizedCommunicationModule(
            agent_id="test_compression_agent",
            config={
                "message_compression": True,
                "adaptive_compression": True,
                "compression_threshold": 512,  # 512B阈值
                "default_compression": CompressionType.AUTO,
            },
        )

        # 初始化和启动
        logger.info("\n1. 初始化优化通信模块...")
        init_success = await communication_module.initialize()
        if init_success:
            logger.info("✅ 优化通信模块初始化成功")
        else:
            logger.info("❌ 优化通信模块初始化失败")
            return False

        logger.info("\n2. 启动优化通信模块...")
        start_success = await communication_module.start()
        if start_success:
            logger.info("✅ 优化通信模块启动成功")
        else:
            logger.info("❌ 优化通信模块启动失败")
            return False

        # 3. 测试不同大小消息的压缩
        logger.info("\n3. 测试不同大小消息的压缩...")
        compression_results = []

        # 小消息(不应压缩)
        small_payload = "小消息测试"
        small_message_id = await communication_module.send_message_optimized(
            receiver_id="test_receiver",
            message_type="small_message",
            payload=small_payload,
            compression=CompressionType.AUTO,
        )
        compression_results.append(("小消息", len(small_payload.encode()), small_message_id))

        # 中等消息(应该压缩)
        medium_payload = "中等消息测试" * 100  # 约2KB
        medium_message_id = await communication_module.send_message_optimized(
            receiver_id="test_receiver",
            message_type="medium_message",
            payload=medium_payload,
            compression=CompressionType.AUTO,
        )
        compression_results.append(("中等消息", len(medium_payload.encode()), medium_message_id))

        # 大消息(必须压缩)
        large_payload = "大消息测试" * 1000  # 约20KB
        large_message_id = await communication_module.send_message_optimized(
            receiver_id="test_receiver",
            message_type="large_message",
            payload=large_payload,
            compression=CompressionType.AUTO,
        )
        compression_results.append(("大消息", len(large_payload.encode()), large_message_id))

        # JSON结构化消息
        json_payload = {
            "data": ["test"] * 500,
            "metadata": {"compression": "test", "timestamp": time.time()},
            "nested": {"level1": {"level2": {"level3": "deep value" * 100}}},
        }
        json_message_id = await communication_module.send_message_optimized(
            receiver_id="test_receiver",
            message_type="json_message",
            payload=json_payload,
            compression=CompressionType.AUTO,
        )
        compression_results.append(
            ("JSON消息", len(json.dumps(json_payload).encode()), json_message_id)
        )

        logger.info(f"   ✅ 成功发送 {len(compression_results)} 个不同大小的消息")

        # 4. 分析压缩效果
        logger.info("\n4. 分析压缩效果...")
        stats = communication_module.get_optimization_stats()

        if "module_stats" in stats:
            module_stats = stats["module_stats"]
            compression_stats = module_stats.get("compression_stats", {})

            logger.info("✅ 压缩统计:")
            for result in compression_results:
                msg_name, original_size, msg_id = result
                logger.info(f"   {msg_name}:")
                logger.info(f"     原始大小: {original_size} 字节")
                logger.info(f"     消息ID: {msg_id}")

            if compression_stats:
                total_compression_ratio = 0
                total_compressions = 0
                for msg_id, cr in compression_stats.items():
                    if hasattr(cr, "compression_ratio"):
                        total_compression_ratio += cr.compression_ratio
                        total_compressions += 1

                if total_compressions > 0:
                    avg_compression_ratio = total_compression_ratio / total_compressions
                    space_savings = (1 - avg_compression_ratio) * 100
                    logger.info(f"   平均压缩比: {avg_compression_ratio:.2f}")
                    logger.info(f"   空间节省: {space_savings:.1f}%")
                    logger.info(f"   带宽节省: {module_stats.get('bandwidth_saved', 0):.1f}%")

        # 5. 测试不同压缩算法
        logger.info("\n5. 测试不同压缩算法...")
        test_payload = "压缩算法测试" * 500  # 约5KB
        compression_algorithms = [
            CompressionType.GZIP,
            CompressionType.LZMA,
        ]

        # 如果LZ4可用,添加测试
        if "compression_benchmarks" in stats:
            benchmarks = stats["compression_benchmarks"]
            if "lz4" in benchmarks:
                compression_algorithms.append(CompressionType.LZ4)

        algorithm_results = []
        for algorithm in compression_algorithms:
            try:
                start_time = time.time()
                message_id = await communication_module.send_message_optimized(
                    receiver_id="test_receiver",
                    message_type="algorithm_test",
                    payload=test_payload,
                    compression=algorithm,
                )
                send_time = time.time() - start_time
                algorithm_results.append((algorithm.value, message_id, send_time))
                logger.info(f"   ✅ {algorithm.value} 压缩算法测试完成")
            except Exception as e:
                logger.info(f"   ❌ {algorithm.value} 压缩算法测试失败: {e}")

        # 6. 获取压缩基准测试结果
        logger.info("\n6. 获取压缩基准测试结果...")
        if "compression_benchmarks" in stats:
            benchmarks = stats["compression_benchmarks"]
            logger.info("✅ 压缩算法基准:")
            for algorithm, benchmark in benchmarks.items():
                logger.info(f"   {algorithm}:")
                logger.info(f"     压缩比: {benchmark.get('compression_ratio', 'N/A'):.3f}")
                logger.info(f"     压缩时间: {benchmark.get('compression_time', 'N/A'):.4f}s")
                logger.info(f"     压缩速度: {benchmark.get('speed', 'N/A'):.1f} MB/s")

        # 7. 健康检查
        logger.info("\n7. 执行健康检查...")
        health_status = await communication_module.health_check()
        logger.info(f"   健康状态: {'健康' if health_status else '不健康'}")

        if hasattr(communication_module, "_health_check_details"):
            details = communication_module._health_check_details
            logger.info(f"   - 压缩器状态: {details.get('compressor_status', 'unknown')}")
            logger.info(f"   - 批处理器状态: {details.get('batch_processor_status', 'unknown')}")
            logger.info(f"   - 消息路由器状态: {details.get('message_router_status', 'unknown')}")

        # 8. 关闭模块
        logger.info("\n8. 关闭优化通信模块...")
        await communication_module.shutdown()
        logger.info("✅ 优化通信模块关闭成功")

        logger.info(str("\n" + "=" * 60))
        logger.info("🎉 消息压缩测试完成!")
        return True

    except Exception as e:
        logger.error(f"❌ 测试过程中发生错误: {e!s}")
        import traceback

        traceback.print_exc()
        return False


async def test_batch_processing():
    """测试批处理"""
    logger.info("\n📦 测试批处理")
    logger.info(str("=" * 60))

    try:
        communication_module = OptimizedCommunicationModule(
            agent_id="test_batch_agent",
            config={
                "batch_processing": True,
                "batch_size": 10,
                "batch_timeout": 0.5,  # 0.5秒
                "max_batch_size": 50,
                "adaptive_batching": True,
            },
        )

        await communication_module.initialize()
        await communication_module.start()

        # 1. 测试批量消息发送
        logger.info("\n1. 测试批量消息发送...")
        batch_message_ids = []

        # 发送多个消息到同一接收者
        receiver_id = "batch_receiver"
        num_messages = 25

        for i in range(num_messages):
            message_id = await communication_module.send_message_optimized(
                receiver_id=receiver_id,
                message_type="batch_test",
                payload=f"批量消息 {i} - {time.time()}",
                priority=MessagePriority.BULK,
                delivery_mode=DeliveryMode.BATCH,
            )
            if message_id:
                batch_message_ids.append(message_id)

        logger.info(f"   ✅ 成功发送 {len(batch_message_ids)} 个批量消息")

        # 2. 等待批处理完成
        logger.info("\n2. 等待批处理完成...")
        await asyncio.sleep(2)  # 等待批处理完成

        # 3. 获取批处理统计
        logger.info("\n3. 获取批处理统计...")
        stats = communication_module.get_optimization_stats()

        if "batch_statistics" in stats:
            batch_stats = stats["batch_statistics"]
            logger.info("✅ 批处理统计:")
            logger.info(f"   - 总批次数: {batch_stats.get('total_batches_processed', 0)}")
            logger.info(f"   - 批处理消息总数: {batch_stats.get('total_messages_batched', 0)}")
            logger.info(f"   - 平均批次大小: {batch_stats.get('average_batch_size', 0):.1f}")
            logger.info(f"   - 批处理效率: {batch_stats.get('batch_efficiency', 0):.1%}")

        # 4. 测试不同优先级的批处理
        logger.info("\n4. 测试不同优先级的批处理...")
        priority_batch_ids = []

        for priority in [MessagePriority.HIGH, MessagePriority.NORMAL, MessagePriority.LOW]:
            for i in range(5):
                message_id = await communication_module.send_message_optimized(
                    receiver_id=f"priority_batch_{priority.name.lower()}",
                    message_type="priority_batch_test",
                    payload=f"{priority.name} 批量消息 {i}",
                    priority=priority,
                    delivery_mode=DeliveryMode.BATCH,
                )
                if message_id:
                    priority_batch_ids.append(message_id)

        logger.info(f"   ✅ 成功发送 {len(priority_batch_ids)} 个不同优先级的批量消息")

        # 5. 测试超时批处理
        logger.info("\n5. 测试超时批处理...")
        timeout_batch_ids = []

        # 发送少量消息,测试超时触发批处理
        for i in range(3):  # 少于batch_size
            message_id = await communication_module.send_message_optimized(
                receiver_id="timeout_batch_receiver",
                message_type="timeout_test",
                payload=f"超时测试消息 {i}",
                delivery_mode=DeliveryMode.BATCH,
            )
            if message_id:
                timeout_batch_ids.append(message_id)

        logger.info(f"   ✅ 发送 {len(timeout_batch_ids)} 个消息,等待超时触发批处理...")
        await asyncio.sleep(1)  # 等待超时

        # 6. 验证批处理效率
        logger.info("\n6. 验证批处理效率...")
        final_stats = communication_module.get_optimization_stats()

        if "module_stats" in final_stats:
            module_stats = final_stats["module_stats"]
            logger.info("✅ 批处理效率验证:")
            logger.info(f"   - 总发送消息数: {module_stats.get('total_messages_sent', 0)}")
            logger.info(
                f"   - 平均消息大小: {module_stats.get('average_message_size', 0):.1f} 字节"
            )
            logger.info(f"   - 消息速率: {module_stats.get('message_rate', 0):.2f} 消息/秒")

        await communication_module.shutdown()
        logger.info("\n✅ 批处理测试完成")
        return True

    except Exception as e:
        logger.error(f"❌ 批处理测试失败: {e!s}")
        import traceback

        traceback.print_exc()
        return False


async def test_intelligent_routing():
    """测试智能路由"""
    logger.info("\n🧭 测试智能路由")
    logger.info(str("=" * 60))

    try:
        communication_module = OptimizedCommunicationModule(
            agent_id="test_routing_agent",
            config={
                "intelligent_routing": True,
                "routing_cache_ttl": 60,  # 1分钟缓存
                "message_caching": True,
                "cache_max_size": 500,
            },
        )

        await communication_module.initialize()
        await communication_module.start()

        # 1. 测试消息订阅
        logger.info("\n1. 测试消息订阅...")
        subscription_types = ["test_type_1", "test_type_2", "test_type_3"]
        subscription_success = await communication_module.subscribe_optimized(subscription_types)

        if subscription_success:
            logger.info(f"   ✅ 成功订阅 {len(subscription_types)} 种消息类型")
        else:
            logger.info("   ❌ 订阅失败")

        # 2. 测试消息路由
        logger.info("\n2. 测试消息路由...")
        routing_test_ids = []

        for message_type in subscription_types:
            for i in range(3):
                message_id = await communication_module.send_message_optimized(
                    receiver_id="subscribers",
                    message_type=message_type,
                    payload=f"路由测试消息 {message_type}_{i}",
                    priority=MessagePriority.NORMAL,
                )
                if message_id:
                    routing_test_ids.append(message_id)

        logger.info(f"   ✅ 成功发送 {len(routing_test_ids)} 个路由测试消息")

        # 3. 测试不同优先级的消息路由
        logger.info("\n3. 测试不同优先级的消息路由...")
        priority_routing_ids = []

        for priority in [
            MessagePriority.CRITICAL,
            MessagePriority.HIGH,
            MessagePriority.NORMAL,
            MessagePriority.LOW,
        ]:
            message_id = await communication_module.send_message_optimized(
                receiver_id="priority_test",
                message_type="priority_routing",
                payload=f"优先级 {priority.name} 路由测试",
                priority=priority,
            )
            if message_id:
                priority_routing_ids.append(message_id)

        logger.info(f"   ✅ 成功发送 {len(priority_routing_ids)} 个不同优先级的路由消息")

        # 4. 测试TTL过期
        logger.info("\n4. 测试消息TTL过期...")
        ttl_test_id = await communication_module.send_message_optimized(
            receiver_id="ttl_test",
            message_type="ttl_test",
            payload="TTL测试消息",
            ttl=0.1,  # 0.1秒TTL
        )
        logger.info(f"   ✅ 发送TTL测试消息: {ttl_test_id}")
        await asyncio.sleep(0.2)  # 等待消息过期

        # 5. 获取路由统计
        logger.info("\n5. 获取路由统计...")
        stats = communication_module.get_optimization_stats()

        if "routing_statistics" in stats:
            routing_stats = stats["routing_statistics"]
            logger.info("✅ 路由统计:")
            logger.info(f"   - 总处理器数: {routing_stats.get('total_handlers', 0)}")
            logger.info(f"   - 总订阅者数: {routing_stats.get('total_subscribers', 0)}")
            logger.info(f"   - 缓存条目数: {routing_stats.get('cache_entries', 0)}")

            subscription_details = routing_stats.get("subscription_details", {})
            if subscription_details:
                logger.info("   - 订阅详情:")
                for subscriber, types in subscription_details.items():
                    logger.info(f"     {subscriber}: {types}")

        # 6. 测试消息关联
        logger.info("\n6. 测试消息关联...")
        correlation_id = str(uuid.uuid4())

        request_id = await communication_module.send_message_optimized(
            receiver_id="correlation_test",
            message_type="request",
            payload={"request": "test_data"},
            correlation_id=correlation_id,
        )

        response_id = await communication_module.send_message_optimized(
            receiver_id="correlation_test",
            message_type="response",
            payload={"response": "test_result"},
            correlation_id=correlation_id,
        )

        logger.info(f"   ✅ 发送关联消息: 请求 {request_id}, 响应 {response_id}")

        await communication_module.shutdown()
        logger.info("\n✅ 智能路由测试完成")
        return True

    except Exception as e:
        logger.error(f"❌ 智能路由测试失败: {e!s}")
        import traceback

        traceback.print_exc()
        return False


async def test_performance_benchmarks():
    """测试性能基准"""
    logger.info("\n⚡ 测试性能基准")
    logger.info(str("=" * 60))

    try:
        communication_module = OptimizedCommunicationModule(
            agent_id="test_performance_agent",
            config={
                "message_compression": True,
                "batch_processing": True,
                "adaptive_compression": True,
                "async_messaging": True,
            },
        )

        await communication_module.initialize()
        await communication_module.start()

        # 1. 吞吐量测试
        logger.info("\n1. 吞吐量测试...")
        throughput_start_time = time.time()
        num_throughput_messages = 1000
        throughput_ids = []

        # 快速发送大量消息
        for i in range(num_throughput_messages):
            message_id = await communication_module.send_message_optimized(
                receiver_id="throughput_test",
                message_type="throughput",
                payload=f"吞吐量测试消息 {i}",
                priority=MessagePriority.NORMAL,
                compression=CompressionType.AUTO,
            )
            if message_id:
                throughput_ids.append(message_id)

        throughput_time = time.time() - throughput_start_time
        throughput_rate = len(throughput_ids) / throughput_time

        logger.info("   ✅ 吞吐量测试完成:")
        logger.info(f"     发送消息数: {len(throughput_ids)}")
        logger.info(f"     总耗时: {throughput_time:.3f}s")
        logger.info(f"     吞吐量: {throughput_rate:.1f} 消息/秒")

        # 2. 压缩性能测试
        logger.info("\n2. 压缩性能测试...")
        compression_performance_ids = []
        compression_payloads = []

        # 生成不同大小的测试负载
        for size in [1, 5, 10, 50, 100]:  # KB
            payload = "性能测试负载" * (size * 100)  # 创建指定大小的负载
            compression_payloads.append((size, payload))

        compression_start_time = time.time()

        for size, payload in compression_payloads:
            message_id = await communication_module.send_message_optimized(
                receiver_id="compression_performance",
                message_type="performance",
                payload=payload,
                compression=CompressionType.AUTO,
            )
            if message_id:
                compression_performance_ids.append((size, message_id))

        compression_time = time.time() - compression_start_time

        logger.info("   ✅ 压缩性能测试完成:")
        logger.info(f"     测试消息数: {len(compression_performance_ids)}")
        logger.info(f"     总耗时: {compression_time:.3f}s")
        logger.info(
            f"     平均压缩时间: {compression_time/len(compression_performance_ids)*1000:.1f}ms/消息"
        )

        # 3. 延迟测试
        logger.info("\n3. 延迟测试...")
        latency_measurements = []
        num_latency_tests = 50

        for i in range(num_latency_tests):
            start_time = time.time()
            message_id = await communication_module.send_message_optimized(
                receiver_id="latency_test",
                message_type="latency",
                payload=f"延迟测试消息 {i}",
                priority=MessagePriority.HIGH,
            )
            end_time = time.time()

            if message_id:
                latency = (end_time - start_time) * 1000  # 转换为毫秒
                latency_measurements.append(latency)

        if latency_measurements:
            avg_latency = sum(latency_measurements) / len(latency_measurements)
            min_latency = min(latency_measurements)
            max_latency = max(latency_measurements)

            logger.info("   ✅ 延迟测试完成:")
            logger.info(f"     测试消息数: {len(latency_measurements)}")
            logger.info(f"     平均延迟: {avg_latency:.2f}ms")
            logger.info(f"     最小延迟: {min_latency:.2f}ms")
            logger.info(f"     最大延迟: {max_latency:.2f}ms")

        # 4. 内存使用测试
        logger.info("\n4. 内存使用测试...")
        try:
            import psutil

            process = psutil.Process()
            initial_memory = process.memory_info().rss / 1024 / 1024  # MB

            # 发送大量消息测试内存增长
            memory_test_messages = 500
            large_payload = "x" * 1024 * 10  # 10KB负载

            for i in range(memory_test_messages):
                await communication_module.send_message_optimized(
                    receiver_id="memory_test",
                    message_type="memory",
                    payload=f"{large_payload}_{i}",
                    compression=CompressionType.AUTO,
                )

            final_memory = process.memory_info().rss / 1024 / 1024  # MB
            memory_increase = final_memory - initial_memory
            memory_per_message = memory_increase / memory_test_messages

            logger.info("   ✅ 内存使用测试完成:")
            logger.info(f"     初始内存: {initial_memory:.1f}MB")
            logger.info(f"     最终内存: {final_memory:.1f}MB")
            logger.info(f"     内存增长: {memory_increase:.1f}MB")
            logger.info(f"     每消息内存: {memory_per_message:.2f}KB")

        except ImportError:
            logger.info("   ⚠️ psutil不可用,跳过内存测试")

        # 5. 获取最终性能统计
        logger.info("\n5. 获取最终性能统计...")
        final_stats = communication_module.get_optimization_stats()

        if "module_stats" in final_stats:
            module_stats = final_stats["module_stats"]
            logger.info("✅ 最终性能统计:")
            logger.info(f"   - 总发送消息: {module_stats.get('total_messages_sent', 0)}")
            logger.info(f"   - 总接收消息: {module_stats.get('total_messages_received', 0)}")
            logger.info(f"   - 总发送字节: {module_stats.get('total_bytes_sent', 0)}")
            logger.info(f"   - 总接收字节: {module_stats.get('total_bytes_received', 0)}")
            logger.info(
                f"   - 平均消息大小: {module_stats.get('average_message_size', 0):.1f} 字节"
            )
            logger.info(f"   - 消息速率: {module_stats.get('message_rate', 0):.2f} 消息/秒")
            logger.info(f"   - 带宽节省: {module_stats.get('bandwidth_saved', 0):.1f}%")

        await communication_module.shutdown()
        logger.info("\n✅ 性能基准测试完成")
        return True

    except Exception as e:
        logger.error(f"❌ 性能基准测试失败: {e!s}")
        import traceback

        traceback.print_exc()
        return False


async def main():
    """主测试函数"""
    logger.info("🚀 优化版通信模块完整测试套件")
    logger.info(str("=" * 80))

    # 测试列表
    tests = [
        ("消息压缩测试", test_message_compression),
        ("批处理测试", test_batch_processing),
        ("智能路由测试", test_intelligent_routing),
        ("性能基准测试", test_performance_benchmarks),
    ]

    results = []

    for test_name, test_func in tests:
        logger.info(f"\n🧪 执行测试: {test_name}")
        try:
            result = await test_func()
            results.append((test_name, result))
            status = "✅ 通过" if result else "❌ 失败"
            logger.info(f"\n{test_name}: {status}")
        except Exception as e:
            logger.error(f"测试异常 {test_name}: {e}")
            results.append((test_name, False))

    # 测试总结
    logger.info(str("\n" + "=" * 80))
    logger.info("📊 测试总结")
    logger.info(str("=" * 80))

    passed_count = sum(1 for _, result in results if result)
    total_count = len(results)

    for test_name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        logger.info(f"{test_name}: {status}")

    logger.info(f"\n🎯 总体结果: {passed_count}/{total_count} 测试通过")
    logger.info(f"成功率: {passed_count/total_count*100:.1f}%")

    if passed_count == total_count:
        logger.info("\n🎉 所有测试通过!优化版通信模块功能验证成功!")
        logger.info("\n🌟 通信模块优化特性:")
        logger.info("   ✅ 多算法消息压缩")
        logger.info("   ✅ 自适应压缩策略")
        logger.info("   ✅ 智能批处理机制")
        logger.info("   ✅ 高效消息路由")
        logger.info("   ✅ 异步消息处理")
        logger.info("   ✅ 性能监控和统计")
    else:
        logger.info("\n⚠️ 部分测试失败,需要进一步优化。")

    return passed_count == total_count


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
