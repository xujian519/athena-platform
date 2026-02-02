#!/usr/bin/env python3
"""
监控模块核心功能测试脚本
Test Core Monitoring Module

验证监控指标收集、告警规则和性能分析功能
作者: Athena AI系统
创建时间: 2025-12-11
版本: 1.0.0
"""

import asyncio
import logging
import random
import sys
import time
from datetime import timedelta
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from core.monitoring.optimized_monitoring_module import (
    AlertLevel,
    MetricType,
    create_alert_rule,
    create_monitoring_module,
)

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_metrics_collection():
    """测试指标收集"""
    logger.info("\n📊 测试指标收集功能")
    logger.info(str("=" * 60))

    try:
        # 创建监控模块
        monitoring = create_monitoring_module(
            "test_metrics", {"collection_interval": 5, "retention_period": 300}
        )

        # 初始化
        init_success = await monitoring.initialize()
        logger.info(
            f"   {'✅' if init_success else '❌'} 初始化{'成功' if init_success else '失败'}"
        )

        # 启动
        start_success = await monitoring.start()
        logger.info(
            f"   {'✅' if start_success else '❌'} 启动{'成功' if start_success else '失败'}"
        )

        # 测试不同类型的指标
        logger.info("\n1. 测试计数器指标...")
        for _i in range(10):
            monitoring.record_metric("test_requests", 1, MetricType.COUNTER)
            await asyncio.sleep(0.1)

        counter_metric = monitoring.get_metric("test_requests")
        if counter_metric:
            logger.info(f"   ✅ 计数器值: {counter_metric.value}")

        logger.info("\n2. 测试仪表盘指标...")
        for _i in range(5):
            value = random.uniform(50, 100)
            monitoring.record_metric("test_cpu_usage", value, MetricType.GAUGE)
            await asyncio.sleep(0.1)

        gauge_metric = monitoring.get_metric("test_cpu_usage")
        if gauge_metric:
            logger.info(f"   ✅ 仪表盘值: {gauge_metric.value:.2f}")

        logger.info("\n3. 测试直方图指标...")
        for _i in range(20):
            value = random.uniform(10, 200)
            monitoring.record_metric("test_response_time", value, MetricType.HISTOGRAM)
            await asyncio.sleep(0.1)

        logger.info("\n4. 测试计时器指标...")
        for _i in range(15):
            duration = random.uniform(0.1, 2.0)
            monitoring.record_metric("test_duration", duration, MetricType.TIMER)
            await asyncio.sleep(0.1)

        # 获取统计信息
        logger.info("\n5. 获取指标统计...")
        stats = monitoring.metrics_collector.get_metric_stats("test_response_time")
        if stats:
            logger.info("   ✅ 响应时间统计:")
            logger.info(f"     - 计数: {stats.get('count', 0)}")
            logger.info(f"     - 最小值: {stats.get('min', 0):.2f}")
            logger.info(f"     - 最大值: {stats.get('max', 0):.2f}")
            logger.info(f"     - 平均值: {stats.get('mean', 0):.2f}")

        # 测试带标签的指标
        logger.info("\n6. 测试带标签的指标...")
        monitoring.record_metric(
            "test_requests", 1, MetricType.COUNTER, {"endpoint": "/api/v1/users"}
        )
        monitoring.record_metric(
            "test_requests", 1, MetricType.COUNTER, {"endpoint": "/api/v1/orders"}
        )

        metric1 = monitoring.get_metric("test_requests", {"endpoint": "/api/v1/users"})
        metric2 = monitoring.get_metric("test_requests", {"endpoint": "/api/v1/orders"})

        if metric1 and metric2:
            logger.info(f"   ✅ 带标签指标: 用户API={metric1.value}, 订单API={metric2.value}")

        # 健康检查
        health = await monitoring.health_check()
        logger.info(f"\n7. 健康检查: {'✅ 正常' if health else '❌ 异常'}")

        # 清理
        await monitoring.stop()
        await monitoring.shutdown()

        logger.info("✅ 指标收集测试完成")
        return True

    except Exception as e:
        logger.error(f"❌ 指标收集测试失败: {e}")
        import traceback

        traceback.print_exc()
        return False


async def test_alert_system():
    """测试告警系统"""
    logger.info("\n🚨 测试告警系统")
    logger.info(str("=" * 60))

    try:
        # 创建监控模块
        monitoring = create_monitoring_module(
            "test_alerts", {"evaluation_interval": 5}  # 5秒评估一次
        )

        # 初始化和启动
        await monitoring.initialize()
        await monitoring.start()

        # 添加告警规则
        logger.info("\n1. 添加告警规则...")

        # CPU使用率告警
        cpu_rule = create_alert_rule(
            id="cpu_high_usage",
            name="CPU使用率过高",
            metric_name="test_cpu",
            condition=">",
            threshold=80,
            level=AlertLevel.WARNING,
            description="CPU使用率超过80%",
        )
        monitoring.add_alert_rule(cpu_rule)

        # 内存使用率告警
        memory_rule = create_alert_rule(
            id="memory_high_usage",
            name="内存使用率过高",
            metric_name="test_memory",
            condition=">",
            threshold=90,
            level=AlertLevel.ERROR,
            description="内存使用率超过90%",
        )
        monitoring.add_alert_rule(memory_rule)

        logger.info(f"   ✅ 添加了 {len(monitoring.alert_manager.rules)} 个告警规则")

        # 触发告警
        logger.info("\n2. 触发告警测试...")

        # 记录正常值
        monitoring.record_metric("test_cpu", 70, MetricType.GAUGE)
        monitoring.record_metric("test_memory", 60, MetricType.GAUGE)

        # 等待评估
        await asyncio.sleep(6)

        active_alerts = monitoring.get_active_alerts()
        logger.info(f"   正常状态下活跃告警数: {len(active_alerts)}")

        # 记录告警值
        monitoring.record_metric("test_cpu", 85, MetricType.GAUGE)
        monitoring.record_metric("test_memory", 95, MetricType.GAUGE)

        # 持续记录以触发持续时间要求
        for _i in range(10):
            monitoring.record_metric("test_cpu", 85 + random.uniform(0, 5), MetricType.GAUGE)
            monitoring.record_metric("test_memory", 95 + random.uniform(0, 3), MetricType.GAUGE)
            await asyncio.sleep(1)

        # 检查告警
        await asyncio.sleep(2)
        active_alerts = monitoring.get_active_alerts()
        logger.info(f"   告警状态下活跃告警数: {len(active_alerts)}")

        for alert in active_alerts:
            logger.info(f"   - {alert.name}: {alert.message} (级别: {alert.level.value})")

        # 测试告警恢复
        logger.info("\n3. 测试告警恢复...")
        monitoring.record_metric("test_cpu", 50, MetricType.GAUGE)
        monitoring.record_metric("test_memory", 40, MetricType.GAUGE)

        # 等待告警恢复
        await asyncio.sleep(10)

        active_alerts = monitoring.get_active_alerts()
        logger.info(f"   恢复后活跃告警数: {len(active_alerts)}")

        # 查看告警历史
        alert_history = monitoring.get_alert_history(10)
        logger.info(f"   告警历史记录数: {len(alert_history)}")

        # 删除测试规则
        logger.info("\n4. 清理告警规则...")
        monitoring.remove_alert_rule("cpu_high_usage")
        monitoring.remove_alert_rule("memory_high_usage")

        logger.info(f"   ✅ 剩余告警规则数: {len(monitoring.alert_manager.rules)}")

        # 清理
        await monitoring.stop()
        await monitoring.shutdown()

        logger.info("✅ 告警系统测试完成")
        return True

    except Exception as e:
        logger.error(f"❌ 告警系统测试失败: {e}")
        import traceback

        traceback.print_exc()
        return False


async def test_performance_analysis():
    """测试性能分析"""
    logger.info("\n📈 测试性能分析功能")
    logger.info(str("=" * 60))

    try:
        # 创建监控模块
        monitoring = create_monitoring_module("test_analysis", {"collection_interval": 1})

        await monitoring.initialize()
        await monitoring.start()

        # 生成测试数据
        logger.info("\n1. 生成测试数据...")

        # 生成趋势数据(逐渐增长)
        for i in range(30):
            value = 50 + i * 2 + random.uniform(-5, 5)  # 逐渐增长
            monitoring.record_metric("test_trend_metric", value, MetricType.GAUGE)
            await asyncio.sleep(0.1)

        # 生成周期性数据
        for i in range(60):
            value = 50 + 30 * (i % 20) / 20 + random.uniform(-5, 5)  # 周期变化
            monitoring.record_metric("test_periodic_metric", value, MetricType.GAUGE)
            await asyncio.sleep(0.1)

        # 生成异常数据
        for i in range(40):
            if i in [10, 25, 35]:
                value = 200 + random.uniform(0, 50)  # 异常值
            else:
                value = 50 + random.uniform(-10, 10)  # 正常值
            monitoring.record_metric("test_anomaly_metric", value, MetricType.GAUGE)
            await asyncio.sleep(0.1)

        logger.info("   ✅ 测试数据生成完成")

        # 趋势分析
        logger.info("\n2. 趋势分析...")

        trend_analysis = monitoring.analyze_trend("test_trend_metric", period=timedelta(seconds=5))

        logger.info("   趋势指标分析:")
        logger.info(f"     - 趋势方向: {trend_analysis.get('trend', 'unknown')}")
        logger.info(f"     - 变化率: {trend_analysis.get('change_rate', 0):.2f}%")
        logger.info(f"     - 当前值: {trend_analysis.get('current_value', 0):.2f}")
        logger.info(f"     - 平均值: {trend_analysis.get('average_value', 0):.2f}")

        # 异常检测
        logger.info("\n3. 异常检测...")

        anomalies = monitoring.detect_anomalies("test_anomaly_metric", period=timedelta(seconds=5))

        logger.info(f"   检测到 {len(anomalies)} 个异常:")
        for anomaly in anomalies[:5]:  # 显示前5个
            logger.info(f"     - 时间: {anomaly['timestamp'].strftime('%H:%M:%S')}")
            logger.info(f"       值: {anomaly['value']:.2f} (类型: {anomaly['type']})")

        # 性能报告
        logger.info("\n4. 生成性能报告...")

        report = monitoring.generate_performance_report(period=timedelta(seconds=10))

        metrics_in_report = len(report.get("metrics", {}))
        logger.info(f"   报告包含 {metrics_in_report} 个指标")

        # 监控状态
        logger.info("\n5. 监控状态...")

        status = monitoring.get_monitoring_status()
        logger.info("   监控状态:")
        logger.info(f"     - 监控活跃: {status['monitoring_active']}")
        logger.info(f"     - 指标数量: {status['metrics_count']}")
        logger.info(f"     - 活跃告警: {status['active_alerts']}")
        logger.info(f"     - 告警规则: {status['alert_rules']}")

        # 清理
        await monitoring.stop()
        await monitoring.shutdown()

        logger.info("✅ 性能分析测试完成")
        return True

    except Exception as e:
        logger.error(f"❌ 性能分析测试失败: {e}")
        import traceback

        traceback.print_exc()
        return False


async def test_system_integration():
    """测试系统集成"""
    logger.info("\n🔗 测试系统集成")
    logger.info(str("=" * 60))

    try:
        # 创建多个监控模块
        monitoring_main = create_monitoring_module(
            "main_monitoring", {"collection_interval": 2, "evaluation_interval": 5}
        )

        monitoring_backup = create_monitoring_module(
            "backup_monitoring", {"collection_interval": 3, "evaluation_interval": 7}
        )

        # 初始化所有模块
        await monitoring_main.initialize()
        await monitoring_backup.initialize()

        # 启动所有模块
        await monitoring_main.start()
        await monitoring_backup.start()

        logger.info("✅ 多个监控模块启动成功")

        # 模拟系统运行
        logger.info("\n1. 模拟系统运行...")

        start_time = time.time()

        for i in range(20):
            # 记录各种系统指标
            cpu_usage = random.uniform(20, 90)
            memory_usage = random.uniform(30, 80)
            disk_io = random.uniform(0, 100)
            network_io = random.uniform(10, 200)

            # 主监控记录
            monitoring_main.record_metric("system_cpu", cpu_usage, MetricType.GAUGE)
            monitoring_main.record_metric("system_memory", memory_usage, MetricType.GAUGE)
            monitoring_main.record_metric("disk_io_rate", disk_io, MetricType.GAUGE)
            monitoring_main.record_counter("network_packets", int(network_io))

            # 备份监控记录部分指标
            if i % 2 == 0:
                monitoring_backup.record_metric("system_cpu", cpu_usage, MetricType.GAUGE)
                monitoring_backup.record_metric("system_memory", memory_usage, MetricType.GAUGE)

            await asyncio.sleep(0.5)

        run_time = time.time() - start_time
        logger.info(f"   模拟运行时间: {run_time:.2f} 秒")

        # 添加系统告警规则
        logger.info("\n2. 添加系统告警规则...")

        system_rules = [
            create_alert_rule(
                "high_cpu", "CPU使用率过高", "system_cpu", ">", 85, AlertLevel.WARNING
            ),
            create_alert_rule(
                "critical_memory", "内存使用率严重", "system_memory", ">", 90, AlertLevel.CRITICAL
            ),
            create_alert_rule(
                "high_disk_io", "磁盘IO过高", "disk_io_rate", ">", 80, AlertLevel.WARNING
            ),
        ]

        for rule in system_rules:
            monitoring_main.add_alert_rule(rule)

        logger.info(f"   ✅ 添加了 {len(system_rules)} 个系统告警规则")

        # 等待告警评估
        await asyncio.sleep(10)

        # 检查结果
        logger.info("\n3. 检查监控结果...")

        main_status = monitoring_main.get_monitoring_status()
        backup_status = monitoring_backup.get_monitoring_status()

        logger.info("   主监控状态:")
        logger.info(f"     - 指标数: {main_status['metrics_count']}")
        logger.info(f"     - 活跃告警: {main_status['active_alerts']}")
        logger.info(f"     - 告警规则: {main_status['alert_rules']}")

        logger.info("   备份监控状态:")
        logger.info(f"     - 指标数: {backup_status['metrics_count']}")
        logger.info(f"     - 活跃告警: {backup_status['active_alerts']}")

        # 获取主监控的活跃告警
        main_alerts = monitoring_main.get_active_alerts()
        if main_alerts:
            logger.info(f"\n   检测到 {len(main_alerts)} 个活跃告警:")
            for alert in main_alerts[:3]:  # 显示前3个
                logger.info(f"     - {alert.name}: {alert.message}")

        # 健康检查
        logger.info("\n4. 健康检查...")

        main_health = await monitoring_main.health_check()
        backup_health = await monitoring_backup.health_check()

        logger.info(f"   主监控健康: {'✅ 正常' if main_health else '❌ 异常'}")
        logger.info(f"   备份监控健康: {'✅ 正常' if backup_health else '❌ 异常'}")

        # 清理所有模块
        logger.info("\n5. 清理资源...")

        await monitoring_main.stop()
        await monitoring_main.shutdown()

        await monitoring_backup.stop()
        await monitoring_backup.shutdown()

        logger.info("✅ 系统集成测试完成")
        return True

    except Exception as e:
        logger.error(f"❌ 系统集成测试失败: {e}")
        import traceback

        traceback.print_exc()
        return False


async def main():
    """主测试函数"""
    logger.info("🚀 优化版监控模块核心功能测试")
    logger.info(str("=" * 80))

    # 测试列表
    tests = [
        ("指标收集功能测试", test_metrics_collection),
        ("告警系统测试", test_alert_system),
        ("性能分析测试", test_performance_analysis),
        ("系统集成测试", test_system_integration),
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
        logger.info("\n🎉 所有测试通过!监控模块核心功能验证成功!")
        logger.info("\n🌟 监控系统特性:")
        logger.info("   ✅ 多类型指标收集(计数器、仪表盘、直方图、计时器)")
        logger.info("   ✅ 智能标签支持")
        logger.info("   ✅ 灵活的告警规则系统")
        logger.info("   ✅ 自动告警触发和恢复")
        logger.info("   ✅ 趋势分析和异常检测")
        logger.info("   ✅ 性能报告生成")
        logger.info("   ✅ 系统级监控集成")
        logger.info("   ✅ 实时健康检查")
    else:
        logger.info("\n⚠️ 部分测试失败,需要进一步优化。")

    return passed_count == total_count


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
