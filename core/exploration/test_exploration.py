#!/usr/bin/env python3
from __future__ import annotations
"""
Phase 3探索引擎测试脚本
Testing Phase 3 Exploration Engine

测试主动探索、知识空白分析、替代方案探索等功能

作者: 小诺·双鱼座
创建时间: 2025-01-05
"""

import asyncio
import os
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# 设置环境变量
os.chdir(project_root)

from core.exploration.active_exploration_engine import (
    get_active_exploration_engine,
)
from core.exploration.alternative_explorer import get_alternative_explorer
from core.exploration.knowledge_gap_analyzer import get_knowledge_gap_analyzer
from core.orchestration.xiaonuo_main_orchestrator import TaskPriority, XiaonuoMainOrchestrator


async def test_active_exploration_engine():
    """测试1: 主动探索引擎"""
    print("\n" + "=" * 70)
    print("🧪 测试1: 主动探索引擎")
    print("=" * 70)

    engine = get_active_exploration_engine()

    # 测试知识空白发现
    print("\n📊 测试知识空白发现...")
    gaps = await engine.discover_knowledge_gaps(domain="医疗AI", context={"focus": "诊断技术"})

    print(f"✅ 发现 {len(gaps)} 个知识空白:")
    for gap in gaps[:3]:
        print(f"   - {gap.topic} (重要性: {gap.importance:.1%})")

    # 测试新知识探索
    if gaps:
        print("\n🔎 测试新知识探索...")
        exploration_result = await engine.explore_new_knowledge(
            knowledge_gap=gaps[0], exploration_depth=3
        )

        print("✅ 探索完成:")
        print(f"   - 发现 {len(exploration_result.discovered_items)} 条新知识")
        print(f"   - 新颖性: {exploration_result.novelty_score:.1%}")
        print(f"   - 相关性: {exploration_result.relevance_score:.1%}")

    # 测试替代方案探索
    print("\n💡 测试替代方案探索...")
    task = {
        "id": "test_task_1",
        "title": "专利检索分析",
        "description": "检索并分析区块链技术专利",
        "domain": "区块链",
        "complexity": 0.7,
    }

    alternatives_result = await engine.explore_alternative_solutions(task=task, num_alternatives=3)

    print("✅ 替代方案探索完成:")
    print(f"   - 生成 {len(alternatives_result.discovered_items)} 个替代方案")
    print(f"   - 新颖性: {alternatives_result.novelty_score:.1%}")

    # 测试意外发现
    print("\n🎲 测试意外发现...")
    serendipitous_result = await engine.serendipitous_discovery(
        domains=["AI", "医疗"], exploration_scope="broad"
    )

    print("✅ 意外发现完成:")
    print(f"   - 发现 {len(serendipitous_result.discovered_items)} 个创新洞察")

    # 测试假设生成
    print("\n🧪 测试假设生成...")
    observation = {
        "description": "在某些情况下,专利检索结果不准确",
        "context": {"domain": "专利检索"},
    }

    hypotheses = await engine.generate_and_test_hypothesis(
        observation=observation, num_hypotheses=3
    )

    print(f"✅ 生成 {len(hypotheses)} 个假设:")
    for hyp in hypotheses:
        print(f"   - {hyp.statement} (状态: {hyp.status}, 置信度: {hyp.confidence:.1%})")

    print("\n✅ 主动探索引擎测试通过!")
    return engine


async def test_knowledge_gap_analyzer():
    """测试2: 知识图谱空白分析器"""
    print("\n" + "=" * 70)
    print("🧪 测试2: 知识图谱空白分析器")
    print("=" * 70)

    analyzer = get_knowledge_gap_analyzer()

    # 测试单领域分析
    print("\n📊 测试单领域分析...")
    result = await analyzer.analyze_domain_gaps(domain="人工智能")

    print("✅ 分析完成:")
    print(f"   - 实体覆盖: {result.covered_entities}/{result.total_entities}")
    print(f"   - 关系覆盖: {result.covered_relations}/{result.total_relations}")
    print(f"   - 覆盖率: {result.coverage_rate:.1%}")
    print(f"   - 发现空白: {len(result.gaps)} 个")

    if result.gaps:
        print("\n   前3个空白:")
        for i, gap in enumerate(result.gaps[:3], 1):
            print(
                f"      {i}. {gap.get('type', 'unknown')} - 重要性: {gap.get('importance', 0):.1%}"
            )

    if result.recommendations:
        print("\n   推荐:")
        for rec in result.recommendations[:3]:
            print(f"      - {rec}")

    # 测试批量分析
    print("\n📊 测试批量分析...")
    batch_results = await analyzer.batch_analyze_domains(domains=["AI", "医疗", "区块链"])

    print("✅ 批量分析完成:")
    for domain, result in batch_results.items():
        print(f"   - {domain}: 覆盖率 {result.coverage_rate:.1%}, 空白 {len(result.gaps)} 个")

    print("\n✅ 知识图谱空白分析器测试通过!")
    return analyzer


async def test_alternative_explorer():
    """测试3: 替代方案探索器"""
    print("\n" + "=" * 70)
    print("🧪 测试3: 替代方案探索器")
    print("=" * 70)

    explorer = get_alternative_explorer()

    # 测试替代方案生成
    task = {
        "id": "test_task_2",
        "title": "医疗AI系统开发",
        "description": "开发一个基于AI的医疗诊断系统",
        "domain": "医疗AI",
        "complexity": 0.8,
        "quality_requirement": 0.9,
        "urgency": 0.7,
    }

    print(f"\n💡 探索替代方案: {task['title']}")
    result = await explorer.explore_alternatives(
        task=task, num_alternatives=5, diversity_factor=0.8
    )

    print(f"\n✅ 生成 {len(result.alternatives)} 个替代方案:")
    for alt in result.alternatives:
        print(f"\n   方案: {alt.name}")
        print(f"   - 类型: {alt.approach_type.value}")
        print(f"   - 工作量: {alt.estimated_effort:.1f} 人日")
        print(f"   - 周期: {alt.estimated_duration:.1f} 天")
        print(f"   - 置信度: {alt.confidence:.1%}")
        print(f"   - 风险: {alt.risk_score:.1%}")
        print(f"   - 创新度: {alt.innovation_score:.1%}")

    # 显示推荐
    if result.recommendations:
        print("\n💡 推荐:")
        for rec in result.recommendations[:3]:
            print(f"   - {rec}")

    # 显示最优方案
    if result.best_overall:
        best = next((a for a in result.alternatives if a.solution_id == result.best_overall), None)
        if best:
            print(f"\n🏆 最优方案: {best.name}")
            print("   - 综合评分最高")
            print(f"   - 优点: {', '.join(best.pros[:2])}")

    print("\n✅ 替代方案探索器测试通过!")
    return explorer


async def test_orchestrator_integration():
    """测试4: 编排中枢集成"""
    print("\n" + "=" * 70)
    print("🧪 测试4: 编排中枢集成(探索模式)")
    print("=" * 70)

    # 创建带探索引擎的编排中枢
    orchestrator = XiaonuoMainOrchestrator(enable_planning=True, enable_exploration=True)

    print("\n✅ 编排中枢初始化成功:")
    print(f"   - 版本: {orchestrator.version}")
    print(f"   - 规划引擎: {'✅' if orchestrator.planner else '❌'}")
    print(f"   - 探索引擎: {'✅' if orchestrator.exploration_engine else '❌'}")

    # 测试探索模式编排
    print("\n🔍 测试探索模式编排...")
    report = await orchestrator.orchestrate_with_exploration(
        title="智能专利检索系统",
        description="开发一个智能的专利检索和分析系统",
        domain="专利AI",
        priority=TaskPriority.HIGH,
    )

    print("\n📊 编排报告:")
    print(f"   - 任务ID: {report.task_id}")
    print(f"   - 成功率: {report.success_rate:.1%}")
    print(f"   - 执行时间: {report.execution_time:.1f}秒")

    if report.optimization_suggestions:
        print("\n💡 优化建议:")
        for suggestion in report.optimization_suggestions[:5]:
            print(f"   - {suggestion}")

    print("\n✅ 编排中枢集成测试通过!")
    return orchestrator


async def test_comparison():
    """测试5: 模式对比"""
    print("\n" + "=" * 70)
    print("🧪 测试5: 三种编排模式对比")
    print("=" * 70)

    # 传统模式
    print("\n📊 传统编排模式:")
    orchestrator_traditional = XiaonuoMainOrchestrator(
        enable_planning=False, enable_exploration=False
    )
    print(f"   - 规划引擎: {'✅' if orchestrator_traditional.planner else '❌'}")
    print(f"   - 探索引擎: {'✅' if orchestrator_traditional.exploration_engine else '❌'}")

    # 规划模式
    print("\n🧠 规划编排模式:")
    orchestrator_planning = XiaonuoMainOrchestrator(enable_planning=True, enable_exploration=False)
    print(f"   - 规划引擎: {'✅' if orchestrator_planning.planner else '❌'}")
    print(f"   - 探索引擎: {'✅' if orchestrator_planning.exploration_engine else '❌'}")

    # 探索模式
    print("\n🔍 探索编排模式:")
    orchestrator_exploration = XiaonuoMainOrchestrator(
        enable_planning=True, enable_exploration=True
    )
    print(f"   - 规划引擎: {'✅' if orchestrator_exploration.planner else '❌'}")
    print(f"   - 探索引擎: {'✅' if orchestrator_exploration.exploration_engine else '❌'}")

    print("\n✅ 模式对比完成!")
    print("\n🎯 推荐使用探索编排模式以获得最佳效果!")


async def main():
    """主测试函数"""
    print("\n" + "=" * 70)
    print("🧪 Phase 3探索引擎测试套件")
    print("主动探索 + 知识空白分析 + 替代方案探索")
    print("=" * 70)

    try:
        # 测试1: 主动探索引擎
        await test_active_exploration_engine()

        # 测试2: 知识图谱空白分析器
        await test_knowledge_gap_analyzer()

        # 测试3: 替代方案探索器
        await test_alternative_explorer()

        # 测试4: 编排中枢集成
        await test_orchestrator_integration()

        # 测试5: 模式对比
        await test_comparison()

        print("\n" + "=" * 70)
        print("✅ Phase 3探索引擎测试全部通过!")
        print("=" * 70)
        print("\n📋 Phase 3功能总结:")
        print("   ✅ 主动探索引擎已实现")
        print("   ✅ 知识空白分析已实现")
        print("   ✅ 替代方案探索已实现")
        print("   ✅ 编排中枢集成完成")
        print("   ✅ 意外发现机制已实现")
        print("   ✅ 假设生成测试已实现")
        print("\n🚀 Phase 3探索与发现模式已成功集成到Athena平台!")

    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
