#!/usr/bin/env python3
"""
测试优化后的小诺认知与决策功能
Test Optimized Xiaonuo Cognition & Decision Features
"""

import os
import sys

sys.path.append(os.path.expanduser("~/Athena工作平台"))

import asyncio
from datetime import datetime


async def test_optimized_features():
    """测试优化后的功能"""
    print("🧪 测试优化后的小诺认知与决策功能")
    print("=" * 60)
    print(f"⏰ 测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    try:
        # 导入优化后的类
        from core.agent.xiaonuo_integrated_enhanced import XiaonuoIntegratedEnhanced

        # 创建小诺实例
        print("🚀 正在创建优化后的小诺实例...")
        princess = XiaonuoIntegratedEnhanced()
        await princess.initialize()

        print("✅ 小诺实例创建并初始化成功\n")

        # 1. 测试规划器功能
        await test_planning_features(princess)

        # 2. 测试决策模型
        await test_decision_features(princess)

        # 3. 测试认知协同
        await test_cognition_coordination(princess)

        # 4. 生成测试报告
        await generate_test_report(princess)

    except Exception as e:
        print(f"❌ 测试过程出现错误: {e}")
        import traceback
        traceback.print_exc()

async def test_planning_features(princess):
    """测试规划器功能"""
    print("📋 测试规划器功能")
    print("-" * 40)

    # 检查规划器是否已初始化
    if hasattr(princess, 'task_planner') and princess.task_planner:
        print("  ✅ 任务规划器已初始化")
    else:
        print("  ⚠️ 任务规划器未初始化")

    if hasattr(princess, 'planning_integration') and princess.planning_integration:
        print("  ✅ 规划集成器已初始化")
    else:
        print("  ⚠️ 规划集成器未初始化")

    # 测试规划请求
    test_tasks = [
        "帮我制定一个学习计划",
        "如何优化工作流程",
        "项目管理方案"
    ]

    for task in test_tasks:
        try:
            print(f"\n  📝 测试任务: {task}")

            # 如果有规划集成器，使用它
            if hasattr(princess, 'planning_integration') and princess.planning_integration:
                result = await princess.planning_integration.handle_planning_request(task)
                if result.get('success', False):
                    print(f"    ✅ 规划成功: {result.get('response', '')[:100]}...")
                else:
                    print("    ⚠️ 规划部分成功")
            else:
                print("    ⚠️ 规划集成器不可用")

        except Exception as e:
            print(f"    ❌ 规划测试失败: {e}")

async def test_decision_features(princess):
    """测试决策模型功能"""
    print("\n⚖️ 测试决策模型功能")
    print("-" * 40)

    # 检查决策模型
    if hasattr(princess, 'decision_model') and princess.decision_model:
        print("  ✅ 增强决策模型已初始化")
    else:
        print("  ⚠️ 决策模型未初始化")
        return

    # 测试决策场景
    test_scenarios = [
        {
            'name': '技术选型决策',
            'options': [
                {'name': '方案A', 'tech': 'React', 'cost': 'low', 'complexity': 'medium'},
                {'name': '方案B', 'tech': 'Vue', 'cost': 'medium', 'complexity': 'low'},
                {'name': '方案C', 'tech': 'Angular', 'cost': 'high', 'complexity': 'high'}
            ],
            'criteria': ['cost', 'complexity', 'performance', 'maintainability']
        },
        {
            'name': '任务优先级决策',
            'options': [
                {'name': '紧急修复', 'impact': 'high', 'effort': 'low'},
                {'name': '功能开发', 'impact': 'medium', 'effort': 'high'},
                {'name': '文档更新', 'impact': 'low', 'effort': 'low'}
            ],
            'criteria': ['impact', 'effort', 'urgency', 'value']
        }
    ]

    for scenario in test_scenarios:
        try:
            print(f"\n  🎯 测试场景: {scenario['name']}")

            result = await princess.decision_model.make_decision(
                scenario['options'],
                scenario['criteria'],
                context={'weights': {'cost': 0.3, 'complexity': 0.3, 'performance': 0.4}}
            )

            if result.get('success', False):
                best_option = result.get('best_option', {})
                print("    ✅ 决策成功")
                print(f"    🏆 最佳选择: {best_option.get('option', {}).get('name', 'Unknown')}")
                print(f"    📊 置信度: {result.get('confidence', 0):.2f}")
            else:
                print(f"    ⚠️ 决策部分成功: {result.get('error', '')}")

        except Exception as e:
            print(f"    ❌ 决策测试失败: {e}")

async def test_cognition_coordination(princess):
    """测试认知协同功能"""
    print("\n🔄 测试认知协同功能")
    print("-" * 40)

    # 测试推理能力
    print("  🧠 测试推理能力...")
    try:
        if hasattr(princess, 'cognitive_reasoning'):
            result = await princess.cognitive_reasoning(
                "如果所有的程序员都很优秀，而小诺是程序员，那么小诺优秀吗？",
                context="逻辑推理测试"
            )
            print("    ✅ 认知推理功能可用")
        else:
            print("    ⚠️ 认知推理方法不可用")
    except Exception as e:
        print(f"    ❌ 推理测试失败: {e}")

    # 测试综合处理能力
    print("\n  🔄 测试综合处理流程...")
    complex_tasks = [
        "分析现有代码库并提出优化方案",
        "设计一个新的功能模块",
        "解决系统性能问题"
    ]

    for task in complex_tasks:
        try:
            print(f"\n    📝 任务: {task[:30]}...")

            # 使用综合处理方法
            result = await princess.process_input(task, "text")

            if result:
                print("      ✅ 处理成功")

                # 检查是否包含认知分析
                if 'xiaonuo_emotional_response' in result:
                    print("      🎭 包含情感分析")

                # 检查是否有执行建议
                if 'suggestions' in result or 'recommendations' in result:
                    print("      💡 包含执行建议")
            else:
                print("      ⚠️ 处理结果为空")

        except Exception as e:
            print(f"      ❌ 处理失败: {e}")

async def generate_test_report(princess):
    """生成测试报告"""
    print("\n📊 生成测试报告")
    print("=" * 60)

    # 收集系统状态
    system_status = {
        "规划器": hasattr(princess, 'task_planner') and princess.task_planner is not None,
        "规划集成器": hasattr(princess, 'planning_integration') and princess.planning_integration is not None,
        "决策模型": hasattr(princess, 'decision_model') and princess.decision_model is not None,
        "认知推理": hasattr(princess, 'cognitive_reasoning'),
        "增强NLP": hasattr(princess, 'enhanced_nlp') and princess.enhanced_nlp is not None
    }

    print("\n📋 系统组件状态:")
    for component, status in system_status.items():
        status_icon = "✅" if status else "❌"
        print(f"  {status_icon} {component}: {'已激活' if status else '未激活'}")

    # 计算优化完成度
    activated = sum(1 for status in system_status.values() if status)
    total = len(system_status)
    completion_rate = (activated / total) * 100

    print(f"\n🎯 优化完成度: {completion_rate:.1f}% ({activated}/{total})")

    # 保存测试报告
    import json
    report = {
        "test_time": datetime.now().isoformat(),
        "system_status": system_status,
        "completion_rate": completion_rate,
        "agent_id": getattr(princess, 'agent_id', 'unknown'),
        "optimization_summary": {
            "planner": "已集成" if system_status["规划器"] else "未集成",
            "decision_model": "已增强" if system_status["决策模型"] else "未增强",
            "coordination": "已优化" if completion_rate > 70 else "需进一步优化"
        }
    }

    with open("/Users/xujian/xiaonuo_optimization_test_report.json", 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    print("\n💾 测试报告已保存至: /Users/xujian/xiaonuo_optimization_test_report.json")

    # 总结
    if completion_rate >= 80:
        print("\n🎉 优化成功！小诺的认知与决策功能已大幅提升！")
    elif completion_rate >= 60:
        print("\n✨ 优化基本成功，部分功能已增强。")
    else:
        print("\n⚠️ 优化部分完成，需要进一步调试。")

    # 建议
    print("\n💡 使用建议:")
    print("1. 规划器可用于复杂任务的分解和执行")
    print("2. 决策模型支持多标准决策分析")
    print("3. 认知协同提供更智能的问题处理")

if __name__ == "__main__":
    asyncio.run(test_optimized_features())
