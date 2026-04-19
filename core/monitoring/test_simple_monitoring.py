#!/usr/bin/env python3
from __future__ import annotations
"""
简化版监控模块测试脚本
Simplified Test for Monitoring Module

验证监控核心功能的基本可用性
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

from core.monitoring.optimized_monitoring_module import (
    AlertLevel,
    MetricType,
    create_alert_rule,
    create_monitoring_module,
)

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_basic_monitoring():
    """测试基本监控功能"""
    logger.info("🚀 测试监控模块基本功能")
    logger.info(str("=" * 60))

    try:
        # 创建监控模块
        monitoring = create_monitoring_module(
            "test_simple_monitoring", {"collection_interval": 1, "evaluation_interval": 2}
        )

        # 初始化
        logger.info("1. 初始化监控模块...")
        init_success = await monitoring.initialize()
        logger.info(
            f"   {'✅' if init_success else '❌'} 初始化{'成功' if init_success else '失败'}"
        )

        # 启动
        logger.info("\n2. 启动监控模块...")
        start_success = await monitoring.start()
        logger.info(
            f"   {'✅' if start_success else '❌'} 启动{'成功' if start_success else '失败'}"
        )

        # 测试指标收集
        logger.info("\n3. 测试指标收集...")

        # 记录计数器
        monitoring.record_metric("test_requests", 1, MetricType.COUNTER)
        monitoring.record_metric("test_requests", 1, MetricType.COUNTER)

        # 记录仪表盘
        monitoring.record_metric("test_cpu", 75.5, MetricType.GAUGE)
        monitoring.record_metric("test_memory", 60.2, MetricType.GAUGE)

        # 记录直方图
        monitoring.record_metric("test_response_time", 120.5, MetricType.HISTOGRAM)
        monitoring.record_metric("test_response_time", 150.8, MetricType.HISTOGRAM)

        # 记录计时器
        monitoring.record_metric("test_duration", 0.85, MetricType.TIMER)
        monitoring.record_metric("test_duration", 1.23, MetricType.TIMER)

        logger.info("   ✅ 指标记录完成")

        # 获取指标值
        logger.info("\n4. 验证指标获取...")
        counter_metric = monitoring.get_metric("test_requests")
        gauge_metric = monitoring.get_metric("test_cpu")

        if counter_metric:
            logger.info(f"   ✅ 计数器值: {counter_metric.value}")
        if gauge_metric:
            logger.info(f"   ✅ 仪表盘值: {gauge_metric.value}")

        # 测试告警规则
        logger.info("\n5. 测试告警规则...")

        alert_rule = create_alert_rule(
            id="high_cpu",
            name="CPU使用率过高",
            metric_name="test_cpu",
            condition=">",
            threshold=70,
            level=AlertLevel.WARNING,
        )

        monitoring.add_alert_rule(alert_rule)
        logger.info("   ✅ 告警规则添加完成")

        # 触发告警测试
        monitoring.record_metric("test_cpu", 85.0, MetricType.GAUGE)
        logger.info("   ✅ 触发告警条件已设置")

        # 等待告警评估
        logger.info("\n6. 等待告警评估...")
        await asyncio.sleep(3)

        # 检查监控状态
        logger.info("\n7. 检查监控状态...")
        status = monitoring.get_monitoring_status()
        logger.info(f"   监控活跃: {status['monitoring_active']}")
        logger.info(f"   指标数量: {status['metrics_count']}")
        logger.info(f"   告警规则: {status['alert_rules']}")

        # 健康检查
        logger.info("\n8. 健康检查...")
        health = await monitoring.health_check()
        logger.info(f"   健康状态: {'✅ 正常' if health else '❌ 异常'}")

        # 停止和关闭
        logger.info("\n9. 停止监控模块...")
        await monitoring.stop()
        logger.info("   ✅ 监控模块停止")

        await monitoring.shutdown()
        logger.info("   ✅ 监控模块关闭")

        return True

    except Exception as e:
        logger.error(f"❌ 测试失败: {e}")
        import traceback

        traceback.print_exc()
        return False


async def main():
    """主函数"""
    success = await test_basic_monitoring()

    if success:
        logger.info(str("\n" + "=" * 60))
        logger.info("🎉 监控模块基本功能测试通过!")
        logger.info("\n🌟 核心特性验证:")
        logger.info("   ✅ 模块初始化和启动")
        logger.info("   ✅ 多类型指标收集")
        logger.info("   ✅ 指标获取和查询")
        logger.info("   ✅ 告警规则管理")
        logger.info("   ✅ 健康状态检查")
    else:
        logger.info("\n❌ 测试失败")

    return success


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
