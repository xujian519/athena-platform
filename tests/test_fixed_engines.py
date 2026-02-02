#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试修复后的引擎
Test Fixed Engines
"""

import sys
import os
sys.path.append(os.path.expanduser("~/Athena工作平台"))

import asyncio
from datetime import datetime

async def test_fixed_engines():
    """测试修复后的引擎"""
    print("🧪 测试修复后的引擎功能")
    print("=" * 60)
    print(f"⏰ 测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    try:
        from core.agent.xiaonuo_integrated_enhanced import XiaonuoIntegratedEnhanced

        # 创建小诺实例
        print("🚀 创建小诺实例...")
        princess = XiaonuoIntegratedEnhanced()
        await princess.initialize()

        print("✅ 小诺初始化成功\n")

        # 检查修复后的功能
        await check_engine_methods(princess)

        # 测试规划器功能
        await test_planner_functionality(princess)

        print("\n📊 测试结果总结:")
        print("=" * 60)

    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()

async def check_engine_methods(princess):
    """检查引擎方法"""
    print("🔍 检查引擎方法是否存在:")
    print("-" * 40)

    # 检查学习引擎
    print("\n📚 学习引擎方法:")
    learning_engine = getattr(princess, 'learning_engine', None)
    if learning_engine:
        methods_to_check = [
            'process_experience',
            'learn_from_feedback',
            'adapt_behavior',
            'get_learning_insights'
        ]
        for method in methods_to_check:
            has_method = hasattr(learning_engine, method)
            status = "✅" if has_method else "❌"
            print(f"  {status} {method}")
    else:
        print("  ❌ 学习引擎未初始化")

    # 检查评估引擎
    print("\n🔍 评估引擎方法:")
    evaluation_engine = getattr(princess, 'evaluation_engine', None)
    if evaluation_engine:
        methods_to_check = [
            'evaluate_interaction',
            'evaluate_option',
            'comprehensive_evaluation'
        ]
        for method in methods_to_check:
            has_method = hasattr(evaluation_engine, method)
            status = "✅" if has_method else "❌"
            print(f"  {status} {method}")
    else:
        print("  ❌ 评估引擎未初始化")

    # 检查规划器
    print("\n📋 规划器状态:")
    has_planner = hasattr(princess, 'task_planner') and princess.task_planner is not None
    has_integration = hasattr(princess, 'planning_integration') and princess.planning_integration is not None
    has_simple_planner = hasattr(princess, '_simple_planner_enabled')

    print(f"  {'✅' if has_planner else '❌'} 任务规划器")
    print(f"  {'✅' if has_integration else '❌'} 规划集成器")
    print(f"  {'✅' if has_simple_planner else '❌'} 简化规划器")

    if has_simple_planner and not has_planner:
        print("  💡 使用简化规划模式")

    print()

async def test_planner_functionality(princess):
    """测试规划器功能"""
    print("📋 测试规划器功能")
    print("-" * 40)

    # 测试简化规划
    if hasattr(princess, '_simple_planner_enabled'):
        print("\n🤖️ 测试简化规划器:")
        test_tasks = [
            "开发一个新功能模块",
            "制定学习计划",
            "组织团队活动"
        ]

        for task in test_tasks:
            print(f"\n  📝 任务: {task}")
            try:
                result = await princess.simple_planner_handler(task, {'priority': 'medium'})
                if result.get('success'):
                    plan = result.get('plan', {})
                    print(f"    ✅ 规划成功")
                    print(f"    📋 类型: {plan.get('type', 'unknown')}")
                    print(f"    ⏱️ 估算时间: {plan.get('estimated_time', 'unknown')}")
                else:
                    print(f"    ⚠️ 规划部分成功: {result.get('error', '')}")
            except Exception as e:
                print(f"    ❌ 规划失败: {e}")

    # 测试完整的规划集成
    if hasattr(princess, 'planning_integration') and princess.planning_integration:
        print("\n🤖️ 测试规划集成器:")
        try:
            result = await princess.planning_integration.handle_planning_request(
                "优化系统性能",
                {'context': 'performance_optimization'}
            )
            if result.get('success', False):
                print("    ✅ 规划集成成功")
            else:
                print("    ⚠️ 规划集成需要更多配置")
        except Exception as e:
            print(f"    ⚠️ 规划集成测试: {e}")

    print()

if __name__ == "__main__":
    asyncio.run(test_fixed_engines())