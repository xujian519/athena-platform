#!/usr/bin/env python3
"""
Athena自动进化系统测试脚本
Athena Auto-Evolution System Test

测试所有三个阶段的进化功能

作者: Athena平台团队
创建时间: 2026-02-06
"""

import asyncio
import sys
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.evolution import (
    EvolutionCoordinator,
    EvolutionConfig,
    EvolutionPhase,
    get_evolution_coordinator
)
from core.evolution.mutation_engine import (
    MutationEngine,
    MutationType,
    MutationIntensity,
    get_mutation_engine
)
from core.evolution.auto_deployment import (
    AutoDeployment,
    DeploymentConfig,
    DeploymentStrategy,
    get_auto_deployment
)


async def test_phase1_basic_evolution():
    """测试Phase 1: 基础进化"""
    print("\n" + "=" * 70)
    print("📍 Phase 1: 基础进化测试")
    print("=" * 70)

    coordinator = get_evolution_coordinator()
    await coordinator.initialize()

    print("\n🔧 执行基础进化（参数自动调优）...")
    result = await coordinator.evolve()

    print(f"\n✅ 进化结果:")
    print(f"   成功: {result.success}")
    print(f"   阶段: {result.phase.value}")
    print(f"   改进: {result.improvement:.1%}")
    print(f"   突变数: {result.mutations_count}")

    if result.mutations:
        print(f"\n📋 应用的突变:")
        for i, mutation in enumerate(result.mutations[:3], 1):
            print(f"   {i}. {mutation.get('mutation_type', 'N/A')}: {mutation.get('target', 'N/A')}")

    stats = coordinator.get_stats()
    print(f"\n📊 统计信息:")
    print(f"   总进化次数: {stats['total_evolutions']}")
    print(f"   成功率: {stats['successful_evolutions']}/{stats['total_evolutions']}")

    return result.success


async def test_phase2_intelligent_evolution():
    """测试Phase 2: 智能进化"""
    print("\n" + "=" * 70)
    print("🧬 Phase 2: 智能进化测试（突变引擎）")
    print("=" * 70)

    mutation_engine = get_mutation_engine()
    await mutation_engine.initialize()

    print("\n🧬 生成和应用突变...")

    # 生成参数突变
    param_mutation = await mutation_engine.generate_mutation(
        MutationType.PARAMETER_TUNING,
        intensity=MutationIntensity.MODERATE
    )
    print(f"\n   参数突变: {param_mutation.target}")
    print(f"   变更: {param_mutation.before_value} → {param_mutation.after_value}")

    # 批量突变
    results = await mutation_engine.batch_mutate(count=3)

    stats = mutation_engine.get_mutation_stats()
    print(f"\n📊 突变统计:")
    print(f"   总突变数: {stats['total_mutations']}")
    print(f"   成功率: {stats['success_rate']:.1%}")
    print(f"   总改进: {stats['total_improvement']:.2%}")

    return stats['success_rate'] > 0


async def test_phase3_autonomous_evolution():
    """测试Phase 3: 自主进化（自动部署）"""
    print("\n" + "=" * 70)
    print("🤖 Phase 3: 自主进化测试（自动部署）")
    print("=" * 70)

    deployment = get_auto_deployment()

    # 创建模拟进化结果
    from core.evolution.types import EvolutionResult, EvolutionPhase, EvolutionStrategy

    mock_result = EvolutionResult(
        success=True,
        phase=EvolutionPhase.BASIC,
        strategy=EvolutionStrategy.GRADIENT,
        before_score=0.70,
        after_score=0.78,
        improvement=0.08,
        mutations=[
            {
                "mutation_type": "parameter_tuning",
                "target": "temperature",
                "after_value": 0.5
            },
            {
                "mutation_type": "config_update",
                "target": "config.cache_ttl",
                "after_value": 7200
            }
        ]
    )

    print("\n🚀 执行自动部署...")
    result = await deployment.deploy_evolution(mock_result)

    print(f"\n✅ 部署结果:")
    print(f"   成功: {result.success}")
    print(f"   策略: {result.strategy.value}")
    print(f"   状态: {result.status.value}")
    print(f"   性能变化: {result.performance_delta:+.1%}")
    print(f"   是否回滚: {'是' if result.rollback_performed else '否'}")

    stats = deployment.get_deployment_stats()
    print(f"\n📊 部署统计:")
    print(f"   总部署数: {stats['total_deployments']}")
    print(f"   成功率: {stats['success_rate']:.1%}")

    return result.success


async def main():
    """主测试函数"""
    print("=" * 70)
    print("🧪 Athena自动进化系统 - 完整测试")
    print("=" * 70)
    print(f"测试时间: {__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    results = {}

    try:
        # Phase 1: 基础进化
        results["phase1"] = await test_phase1_basic_evolution()

        # Phase 2: 智能进化
        results["phase2"] = await test_phase2_intelligent_evolution()

        # Phase 3: 自主进化
        results["phase3"] = await test_phase3_autonomous_evolution()

        # 总结
        print("\n" + "=" * 70)
        print("📊 测试总结")
        print("=" * 70)

        for phase, success in results.items():
            status = "✅ 通过" if success else "❌ 失败"
            print(f"  {phase.upper()}: {status}")

        all_passed = all(results.values())
        if all_passed:
            print("\n🎉 所有测试通过！Athena自动进化系统运行正常！")
        else:
            print("\n⚠️ 部分测试失败，请检查日志")

    except Exception as e:
        print(f"\n❌ 测试异常: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
