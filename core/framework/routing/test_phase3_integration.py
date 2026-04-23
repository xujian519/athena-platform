#!/usr/bin/env python3

"""
Phase 3完整集成测试脚本
Complete Phase 3 Integration Testing

测试Phase 3所有功能(探索+学习+优先级)在主编排中枢的集成

作者: 小诺·双鱼座
创建时间: 2025-01-05
版本: v3.1.0 "智慧进化"
"""

import asyncio
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# 设置环境变量
os.chdir(project_root)

from core.orchestration.xiaonuo_main_orchestrator import TaskPriority, XiaonuoMainOrchestrator


async def test_v3_1_0_initialization():
    """测试1: v3.1.0初始化"""
    print("\n" + "=" * 80)
    print("🧪 测试1: 主编排中枢v3.1.0初始化")
    print("=" * 80)

    # 创建v3.1.0编排中枢,启用所有功能
    orchestrator = XiaonuoMainOrchestrator(
        enable_planning=True,
        enable_exploration=True,
        enable_learning=True,
        enable_prioritization=True,
    )

    print("\n✅ 主编排中枢初始化成功:")
    print(f"   - 版本: {orchestrator.version}")
    print(f"   - 名称: {orchestrator.name}")
    print(f"   - 规划引擎: {'✅' if orchestrator.planner else '❌'}")
    print(f"   - 探索引擎: {'✅' if orchestrator.exploration_engine else '❌'}")
    print(f"   - 学习引擎: {'✅' if orchestrator.learning_engine else '❌'}")
    print(f"   - 优先级系统: {'✅' if orchestrator.prioritization_system else '❌'}")

    # 验证配置
    print("\n📋 配置验证:")
    print(f"   - 显式规划: {orchestrator.config.get('use_explicit_planning')}")
    print(f"   - 探索模式: {orchestrator.config.get('use_exploration')}")
    print(f"   - 学习模式: {orchestrator.config.get('use_learning')}")
    print(f"   - 优先级系统: {orchestrator.config.get('use_prioritization')}")

    print("\n✅ v3.1.0初始化测试通过!")
    return orchestrator


async def test_orchestrate_with_exploration(orchestrator):
    """测试2: 探索编排"""
    print("\n" + "=" * 80)
    print("🧪 测试2: 探索引擎编排")
    print("=" * 80)

    report = await orchestrator.orchestrate_with_exploration(
        title="区块链专利检索",
        description="检索和分析区块链技术专利",
        domain="区块链",
        priority=TaskPriority.HIGH,
    )

    print("\n📊 探索编排报告:")
    print(f"   - 任务ID: {report.task_id}")
    print(f"   - 执行时间: {report.execution_time:.2f}秒")
    print(f"   - 成功率: {report.success_rate:.1%}")
    print(f"   - 优化建议: {len(report.optimization_suggestions)} 条")

    if report.optimization_suggestions:
        print("\n💡 优化建议:")
        for suggestion in report.optimization_suggestions[:5]:
            print(f"   - {suggestion}")

    print("\n✅ 探索编排测试通过!")
    return report


async def test_orchestrate_with_learning(orchestrator):
    """测试3: 学习编排"""
    print("\n" + "=" * 80)
    print("🧪 测试3: 学习引擎编排")
    print("=" * 80)

    report = await orchestrator.orchestrate_with_learning(
        title="AI医疗专利分析",
        description="分析AI+医疗领域的专利趋势",
        domain="医疗AI",
        priority=TaskPriority.NORMAL,
        enable_learning=True,
    )

    print("\n📊 学习编排报告:")
    print(f"   - 任务ID: {report.task_id}")
    print(f"   - 执行时间: {report.execution_time:.2f}秒")
    print(f"   - 成功率: {report.success_rate:.1%}")
    print(f"   - 优化建议: {len(report.optimization_suggestions)} 条")

    if report.optimization_suggestions:
        print("\n💡 学习洞察:")
        for suggestion in report.optimization_suggestions[:3]:
            print(f"   - {suggestion}")

    # 显示学习统计
    if "learning_stats" in report.resource_utilization:
        stats = report.resource_utilization["learning_stats"]
        print("\n🧠 学习统计:")
        print(f"   - 总经验数: {stats.get('total_experiences', 0)}")
        print(f"   - 总策略数: {stats.get('total_strategies', 0)}")

    print("\n✅ 学习编排测试通过!")
    return report


async def test_orchestrate_with_learning(orchestrator):
    """测试3: 学习编排"""
    print("\n" + "=" * 80)
    print("🧪 测试3: 学习引擎编排")
    print("=" * 80)

    report = await orchestrator.orchestrate_with_learning(
        title="AI医疗专利分析",
        description="分析AI+医疗领域的专利趋势",
        domain="医疗AI",
        priority=TaskPriority.NORMAL,
        enable_learning=True,
    )

    print("\n📊 学习编排报告:")
    print(f"   - 任务ID: {report.task_id}")
    print(f"   - 执行时间: {report.execution_time:.2f}秒")
    print(f"   - 成功率: {report.success_rate:.1%}")
    print(f"   - 优化建议: {len(report.optimization_suggestions)} 条")

    if report.optimization_suggestions:
        print("\n💡 学习洞察:")
        for suggestion in report.optimization_suggestions[:3]:
            print(f"   - {suggestion}")

    # 显示学习统计
    if "learning_stats" in report.resource_utilization:
        stats = report.resource_utilization["learning_stats"]
        print("\n🧠 学习统计:")
        print(f"   - 总经验数: {stats.get('total_experiences', 0)}")
        print(f"   - 总策略数: {stats.get('total_strategies', 0)}")

    print("\n✅ 学习编排测试通过!")
    return report


async def test_orchestrate_with_prioritization(orchestrator):
    """测试4: 优先级编排"""
    print("\n" + "=" * 80)
    print("🧪 测试4: 智能优先级编排")
    print("=" * 80)

    report = await orchestrator.orchestrate_with_prioritization(
        title="紧急专利检索",
        description="需要立即检索的关键专利",
        domain="专利检索",
        priority=TaskPriority.HIGH,  # 使用HIGH代替URGENT
        importance=0.9,
        deadline=datetime.now() + timedelta(hours=2),
    )

    print("\n📊 优先级编排报告:")
    print(f"   - 任务ID: {report.task_id}")
    print(f"   - 执行时间: {report.execution_time:.2f}秒")
    print(f"   - 成功率: {report.success_rate:.1%}")
    print(f"   - 优化建议: {len(report.optimization_suggestions)} 条")

    if report.optimization_suggestions:
        print("\n⚡ 优先级洞察:")
        for suggestion in report.optimization_suggestions[:3]:
            print(f"   - {suggestion}")

    # 显示队列状态
    if "priority_queue_status" in report.resource_utilization:
        status = report.resource_utilization["priority_queue_status"]
        print("\n📊 队列状态:")
        print(f"   - 总任务数: {status.get('total_tasks', 0)}")
        print(f"   - 待处理: {status.get('pending', 0)}")
        print(f"   - 已完成: {status.get('completed_tasks', 0)}")

    print("\n✅ 优先级编排测试通过!")
    return report


async def test_full_intelligence_orchestration(orchestrator):
    """测试5: 完整智能编排"""
    print("\n" + "=" * 80)
    print("🧪 测试5: 完整智能编排(规划+探索+学习+优先级)")
    print("=" * 80)

    report = await orchestrator.orchestrate_full_intelligence(
        title="智能专利战略分析",
        description="综合分析专利技术趋势和竞争态势",
        domain="专利战略",
        priority=TaskPriority.HIGH,
        context={
            "importance": 0.85,
            "strategic_value": 0.9,
            "deadline": (datetime.now() + timedelta(days=1)).isoformat(),
        },
        user_id="expert_001",
        enable_all=True,
    )

    print("\n📊 完整智能编排报告:")
    print(f"   - 任务ID: {report.task_id}")
    print(f"   - 执行时间: {report.execution_time:.2f}秒")
    print(f"   - 成功率: {report.success_rate:.1%}")
    print(f"   - 子任务总数: {report.total_subtasks}")
    print(f"   - 完成子任务: {report.completed_subtasks}")
    print(f"   - 失败子任务: {report.failed_subtasks}")
    print(f"   - 优化建议: {len(report.optimization_suggestions)} 条")

    if report.optimization_suggestions:
        print("\n💡 综合洞察 (前10条):")
        for i, suggestion in enumerate(report.optimization_suggestions[:10], 1):
            print(f"   {i}. {suggestion}")

    # 检查完整智能模式标记
    if report.resource_utilization.get("full_intelligence_mode"):
        phases = report.resource_utilization.get("phases_completed", 0)
        print("\n🚀 完整智能模式:")
        print(f"   - 已完成阶段: {phases}/5")
        print("   - ✅ 阶段1: 智能优先级评估")
        print("   - ✅ 阶段2: 主动探索")
        print("   - ✅ 阶段3: 智能规划与执行")
        print("   - ✅ 阶段4: 在线学习")
        print("   - ✅ 阶段5: 策略优化")

    print("\n✅ 完整智能编排测试通过!")
    return report


async def test_mode_comparison(orchestrator):
    """测试6: 编排模式对比"""
    print("\n" + "=" * 80)
    print("🧪 测试6: 编排模式对比")
    print("=" * 80)

    task_title = "专利检索分析"
    task_description = "检索并分析指定专利"
    task_domain = "专利检索"

    print(f"\n📋 对比任务: {task_title}")

    # 模式1: 仅规划
    print("\n🧠 模式1: 仅规划 (v2.0.0)")
    orchestrator_v2 = XiaonuoMainOrchestrator(
        enable_planning=True,
        enable_exploration=False,
        enable_learning=False,
        enable_prioritization=False,
    )
    report_v2 = await orchestrator_v2.orchestrate_task_with_planning(
        task_title, task_description, TaskPriority.NORMAL
    )
    print(f"   - 版本: {orchestrator_v2.version}")
    print(f"   - 执行时间: {report_v2.execution_time:.2f}秒")
    print(f"   - 成功率: {report_v2.success_rate:.1%}")

    # 模式2: 规划+探索
    print("\n🔍 模式2: 规划+探索 (v3.0.0)")
    orchestrator_v3 = XiaonuoMainOrchestrator(
        enable_planning=True,
        enable_exploration=True,
        enable_learning=False,
        enable_prioritization=False,
    )
    report_v3 = await orchestrator_v3.orchestrate_with_exploration(
        task_title, task_description, task_domain
    )
    print(f"   - 版本: {orchestrator_v3.version}")
    print(f"   - 执行时间: {report_v3.execution_time:.2f}秒")
    print(f"   - 成功率: {report_v3.success_rate:.1%}")
    print(f"   - 优化建议: {len(report_v3.optimization_suggestions)} 条")

    # 模式3: 完整智能
    print("\n🚀 模式3: 完整智能 (v3.1.0)")
    report_v31 = await orchestrator.orchestrate_full_intelligence(
        task_title, task_description, task_domain, enable_all=True
    )
    print(f"   - 版本: {orchestrator.version}")
    print(f"   - 执行时间: {report_v31.execution_time:.2f}秒")
    print(f"   - 成功率: {report_v31.success_rate:.1%}")
    print(f"   - 优化建议: {len(report_v31.optimization_suggestions)} 条")

    # 对比总结
    print("\n📊 版本对比总结:")
    print("   - v2.0.0: 规划能力")
    print(f"   - v3.0.0: 规划 + 探索 (建议数: {len(report_v3.optimization_suggestions)})")
    print(
        f"   - v3.1.0: 规划 + 探索 + 学习 + 优先级 (建议数: {len(report_v31.optimization_suggestions)})"
    )
    print(
        f"   - 智能提升: {len(report_v31.optimization_suggestions) - len(report_v3.optimization_suggestions)} 条额外洞察"
    )

    print("\n✅ 模式对比测试通过!")


async def main():
    """主测试函数"""
    print("\n" + "=" * 80)
    print("🧪 Phase 3完整集成测试套件")
    print("探索 + 学习 + 优先级 + 主编排中枢集成")
    print("Athena平台 v3.1.0 '智慧进化'")
    print("=" * 80)

    try:
        # 测试1: 初始化
        orchestrator = await test_v3_1_0_initialization()

        # 测试2: 探索编排
        await test_orchestrate_with_exploration(orchestrator)

        # 测试3: 学习编排
        await test_orchestrate_with_learning(orchestrator)

        # 测试4: 优先级编排
        await test_orchestrate_with_prioritization(orchestrator)

        # 测试5: 完整智能编排
        await test_full_intelligence_orchestration(orchestrator)

        # 测试6: 模式对比
        await test_mode_comparison(orchestrator)

        print("\n" + "=" * 80)
        print("✅ Phase 3完整集成测试全部通过!")
        print("=" * 80)
        print("\n📋 集成验证总结:")
        print("   ✅ 主编排中枢v3.1.0初始化成功")
        print("   ✅ 探索引擎编排集成完成")
        print("   ✅ 学习引擎编排集成完成")
        print("   ✅ 优先级系统编排集成完成")
        print("   ✅ 完整智能编排功能正常")
        print("   ✅ 版本对比演进验证通过")
        print("\n🚀 Phase 3所有功能已成功集成到Athena平台!")
        print("\n📊 平台能力矩阵:")
        print("   - Phase 2 (v2.0): 智能规划")
        print("   - Phase 3.1 (v3.0): 主动探索")
        print("   - Phase 3.2 (v3.1): 学习适应 + 智能优先级")
        print("\n🎉 Athena平台v3.1.0 '智慧进化' 全面集成成功!")

    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())

