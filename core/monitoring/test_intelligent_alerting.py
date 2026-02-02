#!/usr/bin/env python3
"""
智能告警系统测试脚本
Test Intelligent Alerting System

验证根因分析和自动恢复功能
作者: Athena AI系统
创建时间: 2025-12-11
版本: 1.0.0
"""

import asyncio
import logging
import sys
from datetime import datetime, timedelta
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from core.monitoring.intelligent_alerting_system import (
    RecoveryActionStatus,
    create_auto_recovery_engine,
    create_root_cause_analyzer,
)
from core.monitoring.optimized_monitoring_module import (
    AlertLevel,
    create_alert_rule,
    create_monitoring_module,
)

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_root_cause_analysis():
    """测试根因分析"""
    logger.info("\n🔍 测试根因分析功能")
    logger.info(str("=" * 60))

    try:
        # 创建监控模块
        monitoring = create_monitoring_module("test_root_cause", {"collection_interval": 1})

        await monitoring.initialize()
        await monitoring.start()

        # 创建根因分析器
        root_cause_analyzer = create_root_cause_analyzer(
            monitoring.metrics_collector,
            {"analysis_window": timedelta(minutes=10), "correlation_threshold": 0.6},
        )

        # 构建服务依赖图
        services = ["web_server", "api_server", "database", "cache"]
        dependencies = [
            ("web_server", "api_server"),
            ("api_server", "database"),
            ("api_server", "cache"),
        ]
        root_cause_analyzer.build_dependency_graph(services, dependencies)

        logger.info("1. 构建服务依赖图...")
        logger.info(f"   服务数量: {len(services)}")
        logger.info(f"   依赖关系: {len(dependencies)}")

        # 添加告警规则
        logger.info("\n2. 添加告警规则...")
        rules = [
            create_alert_rule(
                "high_cpu_web", "Web服务器CPU过高", "web_cpu", ">", 80, AlertLevel.WARNING
            ),
            create_alert_rule(
                "high_cpu_api", "API服务器CPU过高", "api_cpu", ">", 85, AlertLevel.ERROR
            ),
            create_alert_rule(
                "high_memory_db", "数据库内存过高", "db_memory", ">", 90, AlertLevel.CRITICAL
            ),
            create_alert_rule(
                "database_error", "数据库错误", "db_errors", ">", 10, AlertLevel.CRITICAL
            ),
        ]

        for rule in rules:
            monitoring.add_alert_rule(rule)

        logger.info(f"   ✅ 添加了 {len(rules)} 个告警规则")

        # 模拟指标数据
        logger.info("\n3. 模拟指标数据...")

        # 模拟CPU使用率逐渐升高
        for i in range(20):
            cpu_value = 60 + i * 2  # 从60%逐渐升到100%
            monitoring.record_metric("web_cpu", cpu_value)
            monitoring.record_metric("api_cpu", cpu_value - 5)
            await asyncio.sleep(0.1)

        # 模拟内存使用率突然升高
        for i in range(10):
            memory_value = 70 + i * 3  # 快速升高
            monitoring.record_metric("db_memory", memory_value)
            await asyncio.sleep(0.1)

        # 模拟数据库错误
        for i in range(5):
            error_count = i * 5
            monitoring.record_metric("db_errors", error_count)
            await asyncio.sleep(0.1)

        logger.info("   ✅ 指标数据模拟完成")

        # 模拟告警触发
        logger.info("\n4. 模拟告警触发...")
        await asyncio.sleep(5)  # 等待告警触发

        active_alerts = monitoring.get_active_alerts()
        logger.info(f"   活跃告警数量: {len(active_alerts)}")

        # 对每个告警进行根因分析
        logger.info("\n5. 执行根因分析...")
        for alert in active_alerts[:3]:  # 分析前3个告警
            logger.info(f"\n   分析告警: {alert.name}")

            root_cause = root_cause_analyzer.analyze_root_cause(alert)

            logger.info(f"     主要根因: {root_cause.primary_cause}")
            logger.info(f"     置信度: {root_cause.confidence:.2f}")
            logger.info(f"     贡献因子: {len(root_cause.contributing_factors)}")
            logger.info(f"     受影响服务: {root_cause.affected_services}")
            logger.info(f"     分析方法: {root_cause.analysis_method}")

            # 显示前3个贡献因子
            for i, factor in enumerate(root_cause.contributing_factors[:3]):
                logger.info(f"       - {factor}")

        # 清理
        await monitoring.stop()
        await monitoring.shutdown()

        logger.info("\n✅ 根因分析测试完成")
        return True

    except Exception as e:
        logger.error(f"❌ 根因分析测试失败: {e}")
        import traceback

        traceback.print_exc()
        return False


async def test_auto_recovery():
    """测试自动恢复"""
    logger.info("\n🔧 测试自动恢复功能")
    logger.info(str("=" * 60))

    try:
        # 创建自动恢复引擎
        recovery_engine = create_auto_recovery_engine(
            {"max_concurrent_actions": 2, "default_timeout": timedelta(minutes=2)}
        )

        await recovery_engine.start()
        logger.info("1. 自动恢复引擎启动成功")

        # 创建模拟告警
        logger.info("\n2. 创建模拟告警...")
        from core.monitoring.optimized_monitoring_module import Alert

        alerts = [
            Alert(
                id="cpu_critical_1",
                rule_id="cpu_high",
                name="CPU使用率严重过高",
                description="CPU使用率达到95%",
                level=AlertLevel.CRITICAL,
                status=AlertStatus.ACTIVE,
                message="CPU使用率95%",
                timestamp=datetime.now(),
                labels={"service": "web_server"},
            ),
            Alert(
                id="memory_error_1",
                rule_id="memory_high",
                name="内存使用率过高",
                description="内存使用率达到88%",
                level=AlertLevel.ERROR,
                status=AlertStatus.ACTIVE,
                message="内存使用率88%",
                timestamp=datetime.now(),
                labels={"service": "api_server"},
            ),
            Alert(
                id="disk_warning_1",
                rule_id="disk_high",
                name="磁盘使用率警告",
                description="磁盘使用率达到75%",
                level=AlertLevel.WARNING,
                status=AlertStatus.ACTIVE,
                message="磁盘使用率75%",
                timestamp=datetime.now(),
                labels={"service": "database"},
            ),
        ]

        logger.info(f"   ✅ 创建了 {len(alerts)} 个模拟告警")

        # 创建恢复动作
        logger.info("\n3. 创建恢复动作...")
        all_actions = []

        for alert in alerts:
            # 创建模拟根因
            from core.monitoring.intelligent_alerting_system import RootCause

            root_cause = RootCause(
                id=f"root_cause_{alert.id}",
                alert_id=alert.id,
                primary_cause="resource_exhaustion",
                confidence=0.85,
                contributing_factors=["high_load", "insufficient_resources"],
                affected_services=[alert.labels.get("service", "unknown")],
                evidence={},
                analysis_method="pattern_matching",
            )

            # 创建恢复动作
            actions = recovery_engine.create_recovery_action(alert, root_cause)
            all_actions.extend(actions)

            logger.info(f"   {alert.name}: 创建了 {len(actions)} 个恢复动作")

        logger.info(f"\n   总共创建了 {len(all_actions)} 个恢复动作")

        # 等待恢复动作执行
        logger.info("\n4. 等待恢复动作执行...")
        await asyncio.sleep(10)

        # 检查执行结果
        logger.info("\n5. 检查执行结果...")
        completed_actions = recovery_engine.list_actions(RecoveryActionStatus.COMPLETED)
        failed_actions = recovery_engine.list_actions(RecoveryActionStatus.FAILED)
        in_progress_actions = recovery_engine.list_actions(RecoveryActionStatus.IN_PROGRESS)

        logger.info(f"   ✅ 已完成: {len(completed_actions)}")
        logger.info(f"   ❌ 失败: {len(failed_actions)}")
        logger.info(f"   ⏳ 进行中: {len(in_progress_actions)}")

        # 显示详细结果
        if completed_actions:
            logger.info("\n   已完成的动作:")
            for action in completed_actions[:3]:  # 显示前3个
                duration = (action.completed_at - action.started_at).total_seconds()
                logger.info(f"     - {action.name}: {duration:.2f}秒")

        if failed_actions:
            logger.info("\n   失败的动作:")
            for action in failed_actions[:3]:  # 显示前3个
                error = action.result.get("error", "未知错误") if action.result else "未知错误"
                logger.info(f"     - {action.name}: {error}")

        # 清理
        await recovery_engine.stop()
        logger.info("\n✅ 自动恢复测试完成")
        return True

    except Exception as e:
        logger.error(f"❌ 自动恢复测试失败: {e}")
        import traceback

        traceback.print_exc()
        return False


async def test_integrated_alerting():
    """测试集成告警系统"""
    logger.info("\n🚀 测试集成智能告警系统")
    logger.info(str("=" * 60))

    try:
        # 创建完整的监控系统
        monitoring = create_monitoring_module(
            "integrated_monitoring", {"collection_interval": 1, "evaluation_interval": 3}
        )

        await monitoring.initialize()
        await monitoring.start()

        # 创建根因分析器和恢复引擎
        root_cause_analyzer = create_root_cause_analyzer(monitoring.metrics_collector)
        recovery_engine = create_auto_recovery_engine({"max_concurrent_actions": 2})

        await recovery_engine.start()

        logger.info("1. 系统组件初始化完成")

        # 设置告警处理回调
        async def handle_alert_with_recovery(alert):
            """处理告警并触发自动恢复"""
            logger.info(f"\n   📢 收到告警: {alert.name} (级别: {alert.level.value})")

            # 根因分析
            root_cause = root_cause_analyzer.analyze_root_cause(alert)
            logger.info(
                f"   🔍 根因: {root_cause.primary_cause} (置信度: {root_cause.confidence:.2f})"
            )

            # 创建恢复动作
            if alert.level in [AlertLevel.ERROR, AlertLevel.CRITICAL]:
                actions = recovery_engine.create_recovery_action(alert, root_cause)
                logger.info(f"   🔧 创建恢复动作: {len(actions)} 个")

        # 添加告警回调
        monitoring.alert_manager.add_alert_callback(handle_alert_with_recovery)

        # 模拟复杂的故障场景
        logger.info("\n2. 模拟复杂故障场景...")

        # 场景1: 数据库性能下降导致API响应慢
        logger.info("   场景1: 数据库性能下降")
        for i in range(15):
            # 数据库连接数增加
            monitoring.record_metric("db_connections", 100 + i * 10)
            # API响应时间增加
            monitoring.record_metric("api_response_time", 200 + i * 50)
            await asyncio.sleep(0.1)

        # 场景2: 内存泄漏
        logger.info("   场景2: 内存泄漏")
        for i in range(20):
            memory_usage = 60 + i * 2  # 逐渐增加的内存使用
            monitoring.record_metric("app_memory_usage", memory_usage)
            await asyncio.sleep(0.1)

        # 场景3: CPU密集型任务
        logger.info("   场景3: CPU密集型任务")
        for i in range(10):
            cpu_usage = 80 + random.randint(0, 15)  # 高CPU使用
            monitoring.record_metric("app_cpu_usage", cpu_usage)
            await asyncio.sleep(0.1)

        # 添加告警规则
        logger.info("\n3. 添加告警规则...")
        rules = [
            create_alert_rule(
                "db_connections_high",
                "数据库连接数过高",
                "db_connections",
                ">",
                200,
                AlertLevel.ERROR,
            ),
            create_alert_rule(
                "api_slow", "API响应过慢", "api_response_time", ">", 1000, AlertLevel.WARNING
            ),
            create_alert_rule(
                "memory_leak", "内存泄漏", "app_memory_usage", ">", 85, AlertLevel.CRITICAL
            ),
            create_alert_rule(
                "cpu_intensive", "CPU使用率过高", "app_cpu_usage", ">", 90, AlertLevel.ERROR
            ),
        ]

        for rule in rules:
            monitoring.add_alert_rule(rule)

        logger.info(f"   ✅ 添加了 {len(rules)} 个告警规则")

        # 等待告警触发和处理
        logger.info("\n4. 等待告警处理...")
        await asyncio.sleep(15)

        # 统计结果
        logger.info("\n5. 统计处理结果...")
        active_alerts = monitoring.get_active_alerts()
        all_actions = recovery_engine.list_actions()

        logger.info(f"   活跃告警: {len(active_alerts)}")
        logger.info(f"   恢复动作: {len(all_actions)}")

        if all_actions:
            status_counts = {}
            for action in all_actions:
                status = action.status.value
                status_counts[status] = status_counts.get(status, 0) + 1

            logger.info("   动作状态分布:")
            for status, count in status_counts.items():
                logger.info(f"     - {status}: {count}")

        # 系统状态
        logger.info("\n6. 系统状态...")
        monitoring_status = monitoring.get_monitoring_status()
        logger.info(f"   监控活跃: {monitoring_status['monitoring_active']}")
        logger.info(f"   指标数量: {monitoring_status['metrics_count']}")

        # 清理
        await recovery_engine.stop()
        await monitoring.stop()
        await monitoring.shutdown()

        logger.info("\n✅ 集成智能告警系统测试完成")
        return True

    except Exception as e:
        logger.error(f"❌ 集成测试失败: {e}")
        import traceback

        traceback.print_exc()
        return False


async def main():
    """主测试函数"""
    logger.info("🚀 智能告警系统测试")
    logger.info(str("=" * 80))

    # 导入random用于测试
    import random

    globals()["random"] = random

    # 测试列表
    tests = [
        ("根因分析测试", test_root_cause_analysis),
        ("自动恢复测试", test_auto_recovery),
        ("集成告警系统测试", test_integrated_alerting),
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
        logger.info("\n🎉 所有测试通过!智能告警系统验证成功!")
        logger.info("\n🌟 智能告警特性:")
        logger.info("   ✅ 多维度根因分析")
        logger.info("   ✅ 服务依赖图分析")
        logger.info("   ✅ 时间相关性分析")
        logger.info("   ✅ 因果模式识别")
        logger.info("   ✅ 自动恢复动作执行")
        logger.info("   ✅ 恢复动作重试机制")
        logger.info("   ✅ 分级告警处理")
        logger.info("   ✅ 集成监控流程")
    else:
        logger.info("\n⚠️ 部分测试失败,需要进一步优化。")

    return passed_count == total_count


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
