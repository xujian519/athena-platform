#!/usr/bin/env python3
"""
测试错误恢复监控功能
Test Error Recovery Monitoring

验证错误恢复系统的监控和统计功能

作者: Athena平台团队
创建时间: 2026-03-17
"""

import asyncio
import sys

sys.path.insert(0, '/Users/xujian/Athena工作平台')

from config.feature_flags import is_feature_enabled
from core.resilience.enhanced_fallback_recovery import (
    EnhancedFallbackRecovery,
    FailureContext,
    FailureSeverity,
)
from core.resilience.recovery_dashboard import RecoveryDashboard


async def test_recovery_monitoring():
    """测试错误恢复监控"""
    print("=" * 60)
    print("🧪 错误恢复监控功能测试")
    print("=" * 60)

    # 检查特性开关
    if not is_feature_enabled("enable_recovery_monitoring"):
        print("⚠️  错误恢复监控未启用，跳过测试")
        return

    # 创建恢复系统
    print("\n1️⃣ 初始化错误恢复系统...")
    recovery_system = EnhancedFallbackRecovery()
    print("   ✅ 恢复系统初始化完成")

    # 创建仪表板
    dashboard = RecoveryDashboard(recovery_system)

    # 模拟各种失败场景
    test_scenarios = [
        # (组件, 操作, 错误, 严重程度)
        ("intent_recognition", "classify", "Model loading failed", FailureSeverity.MEDIUM),
        ("tool_selection", "select", "No tools available", FailureSeverity.LOW),
        ("knowledge_base", "query", "Database connection timeout", FailureSeverity.HIGH),
        ("external_service", "api_call", "HTTP 500 error", FailureSeverity.MEDIUM),
        ("execution", "run", "Out of memory", FailureSeverity.CRITICAL),
    ]

    print(f"\n2️⃣ 模拟 {len(test_scenarios)} 个失败场景...")
    print("-" * 60)

    for i, (component, operation, error, severity) in enumerate(test_scenarios, 1):
        # 创建失败上下文
        failure = FailureContext(
            component=component,
            operation=operation,
            error=error,
            severity=severity,
        )

        # 处理失败
        result = await recovery_system.handle_failure(failure)

        print(f"  [{i}] {component}.{operation}")
        print(f"      严重程度: {severity.value}")
        print(f"      策略: {result.strategy.value}")
        print(f"      结果: {'✅ 成功' if result.success else '❌ 失败'}")
        print(f"      消息: {result.message}")
        print()

    # 获取实时统计
    print("\n3️⃣ 实时统计信息:")
    print("-" * 60)
    stats = dashboard.get_real_time_stats()

    print(f"  总失败数: {stats['total_failures']}")
    print(f"  成功恢复数: {stats['recoveries']}")
    print(f"  恢复成功率: {stats['recovery_rate']:.2%}")

    print("\n  组件健康状态:")
    for component, health in stats['component_health'].items():
        print(f"    - {component}: {health:.2%}")

    print("\n  策略使用分布:")
    for strategy, count in stats['strategy_usage'].items():
        if count > 0:
            print(f"    - {strategy}: {count}次")

    # 获取健康摘要
    print("\n4️⃣ 组件健康状态摘要:")
    print("-" * 60)
    health_summary = dashboard.get_component_health_summary()
    for component, status in health_summary.items():
        print(f"  {component}: {status}")

    # 导出指标
    print("\n5️⃣ 导出监控指标:")
    print("-" * 60)
    print("\n  JSON格式:")
    print(dashboard.export_metrics('json'))

    print("\n  Prometheus格式:")
    print(dashboard.export_metrics('prometheus'))

    # 生成报告
    print("\n6️⃣ 生成恢复报告:")
    print("-" * 60)
    report = dashboard.generate_report(period_hours=24)
    print(report)

    # 验证监控集成
    print("\n7️⃣ 验证监控集成:")
    print("-" * 60)

    # 检查监控指标是否已注册
    if hasattr(recovery_system, 'monitoring_system') and recovery_system.monitoring_system:
        print("  ✅ 监控系统已集成")

        # 检查指标
        metrics = recovery_system.monitoring_system.get_metric_value('recovery_rate')
        if metrics is not None:
            print(f"  ✅ 恢复率指标: {metrics:.2%}")
        else:
            print("  ⚠️  恢复率指标未记录")

        # 检查告警
        active_alerts = recovery_system.monitoring_system.get_active_alerts()
        if active_alerts:
            print(f"  ⚠️  活跃告警: {len(active_alerts)}个")
            for alert in active_alerts:
                print(f"     - {alert.rule_name}: {alert.message}")
        else:
            print("  ✅ 无活跃告警")
    else:
        print("  ⚠️  监控系统未集成")

    print("\n" + "=" * 60)
    print("✅ 测试完成")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(test_recovery_monitoring())
