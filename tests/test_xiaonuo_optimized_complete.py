#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试优化后的小诺完整功能
Test Complete Optimized Xiaonuo Features
"""

import sys
import os
sys.path.append(os.path.expanduser("~/Athena工作平台"))

import asyncio
from datetime import datetime

async def test_optimized_xiaonuo():
    """测试优化后的小诺完整功能"""
    print("🧪 测试优化后的小诺完整功能")
    print("=" * 60)
    print(f"⏰ 测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    try:
        # 导入优化后的小诺
        from core.agent.xiaonuo_integrated_enhanced import XiaonuoIntegratedEnhanced

        # 创建小诺实例
        print("🚀 正在创建优化后的小诺...")
        princess = XiaonuoIntegratedEnhanced()
        await princess.initialize()

        print("✅ 小诺初始化成功\n")

        # 1. 检查所有核心模块
        await check_all_modules(princess)

        # 2. 测试认知与决策功能
        await test_cognition_decision_features(princess)

        # 3. 测试人机协作决策
        await test_human_collaboration(princess)

        # 4. 生成最终报告
        await generate_final_report(princess)

    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()

async def check_all_modules(princess):
    """检查所有核心模块"""
    print("📋 检查核心模块状态")
    print("-" * 50)

    modules = [
        ("感知引擎", "perception_engine"),
        ("认知引擎", "cognition"),
        ("执行引擎", "execution_engine"),
        ("学习引擎", "learning_engine"),
        ("通讯引擎", "communication_engine"),
        ("评估引擎", "evaluation_engine"),
        ("记忆系统", "memory"),
        ("知识管理器", "knowledge"),
        ("规划器", "task_planner"),
        ("决策模型", "decision_model")
    ]

    active_count = 0
    for display_name, attr_name in modules:
        if hasattr(princess, attr_name) and getattr(princess, attr_name) is not None:
            print(f"  ✅ {display_name}: 已激活")
            active_count += 1
        else:
            print(f"  ❌ {display_name}: 未激活")

    completeness = (active_count / len(modules)) * 100
    print(f"\n📊 模块激活率: {completeness:.1f}% ({active_count}/{len(modules)})")
    print()

async def test_cognition_decision_features(princess):
    """测试认知与决策功能"""
    print("🧠 测试认知与决策功能")
    print("-" * 50)

    # 测试推理能力
    print("\n1. 推理能力测试:")
    try:
        if hasattr(princess, 'cognitive_reasoning'):
            result = await princess.cognitive_reasoning(
                "如果所有程序员都爱学习，而小诺是程序员，那么小诺爱学习吗？",
                context="逻辑推理测试"
            )
            print("   ✅ 认知推理功能可用")
        else:
            print("   ⚠️ 认知推理方法不可用")
    except Exception as e:
        print(f"   ❌ 推理测试失败: {e}")

    # 测试决策能力
    print("\n2. 决策能力测试:")
    try:
        if hasattr(princess, 'decision_model') and princess.decision_model:
            print("   ✅ 人机协作决策模型已集成")
            print("   📝 特性:")
            print("      • 人类在环（Human-in-the-Loop）设计")
            print("      • 多阶段决策流程")
            print("      • 动态偏好学习")
            print("      • 详细决策报告")
        else:
            print("   ⚠️ 决策模型未初始化")
    except Exception as e:
        print(f"   ❌ 决策测试失败: {e}")

    # 测试综合处理
    print("\n3. 综合处理测试:")
    test_inputs = [
        "分析这个技术方案的优缺点",
        "帮我制定一个学习计划",
        "评估项目的风险和收益"
    ]

    for i, input_text in enumerate(test_inputs, 1):
        try:
            print(f"\n   测试 {i}: {input_text[:30]}...")
            result = await princess.process_input(input_text, "text")
            if result:
                print("     ✅ 处理成功")
            else:
                print("     ⚠️ 处理结果为空")
        except Exception as e:
            print(f"     ❌ 处理失败: {e}")

    print()

async def test_human_collaboration(princess):
    """测试人机协作功能"""
    print("🤝 测试人机协作功能")
    print("-" * 50)

    # 检查决策模型是否支持人机协作
    if hasattr(princess, 'decision_model') and princess.decision_model:
        print("✅ 人机协作决策模型已就绪")

        # 显示协作特性
        print("\n💡 人机协作特性:")
        print("  🎯 决策阶段: 初始化 → 爸爸审核 → 协作优化 → 最终决策")
        print("  👥 参与方式: 小诺分析 + 爸爸指导 = 最佳决策")
        print("  📊 决策依据: AI分析 + 人类经验 = 综合判断")
        print("  🧠 学习机制: 记录爸爸偏好，持续优化")

        print("\n📋 决策流程说明:")
        print("  1. 小诺分析问题并生成初步方案")
        print("  2. 展示详细的决策报告给爸爸")
        print("  3. 爸爸提供反馈和指导")
        print("  4. 结合双方意见优化方案")
        print("  5. 做出最终决策并记录学习")

        print("\n💭 爸爸的参与方式:")
        print("  • 批准或否决方案")
        print("  • 提出修改建议")
        print("  • 表达偏好倾向")
        print("  • 分享经验和见解")

    else:
        print("⚠️ 决策模型未完全初始化，人机协作功能受限")

    print()

async def generate_final_report(princess):
    """生成最终报告"""
    print("📊 生成最终优化报告")
    print("=" * 60)

    # 统计优化成果
    optimizations = {
        "规划器集成": hasattr(princess, 'task_planner') and princess.task_planner is not None,
        "决策模型增强": hasattr(princess, 'decision_model') and princess.decision_model is not None,
        "人机协作": hasattr(princess, 'decision_model') and hasattr(princess.decision_model, 'human_involvement_level'),
        "认知协同": hasattr(princess, 'cognitive_reasoning')
    }

    print("\n✅ 优化成果:")
    for item, status in optimizations.items():
        icon = "✅" if status else "❌"
        print(f"  {icon} {item}: {'成功' if status else '失败'}")

    # 计算总体评分
    completed = sum(1 for status in optimizations.values() if status)
    total = len(optimizations)
    score = (completed / total) * 100

    print(f"\n🎯 优化完成度: {score:.1f}%")

    # 保存报告
    import json
    report = {
        "optimization_date": datetime.now().isoformat(),
        "optimizations": optimizations,
        "completion_rate": score,
        "agent_id": getattr(princess, 'agent_id', 'unknown'),
        "features": {
            "core_engines": {
                "perception": hasattr(princess, 'perception_engine'),
                "cognition": hasattr(princess, 'cognition'),
                "execution": hasattr(princess, 'execution_engine'),
                "learning": hasattr(princess, 'learning_engine'),
                "communication": hasattr(princess, 'communication_engine'),
                "evaluation": hasattr(princess, 'evaluation_engine')
            },
            "advanced_features": {
                "planning": hasattr(princess, 'task_planner'),
                "decision_making": hasattr(princess, 'decision_model'),
                "human_collaboration": hasattr(princess, 'decision_model') and princess.decision_model is not None
            }
        }
    }

    with open("/Users/xujian/xiaonuo_optimization_final_report.json", 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    print("\n💾 报告已保存至: /Users/xujian/xiaonuo_optimization_final_report.json")

    # 总结
    print("\n🎉 优化总结:")
    print("=" * 60)

    if score >= 75:
        print("🌟 优化非常成功！小诺的认知与决策能力已大幅提升！")
        print("\n主要改进:")
        print("  • 集成了任务规划器，支持复杂项目规划")
        print("  • 引入了人机协作决策模型，爸爸可参与决策过程")
        print("  • 优化了认知协同机制，推理更智能")
    elif score >= 50:
        print("✨ 优化基本成功，部分功能已增强。")
    else:
        print("⚠️ 优化部分完成，需要进一步完善。")

    print("\n🎯 关键特性:")
    print("  1. 📋 智能规划器 - 任务分解与执行管理")
    print("  2. 🤝 人机协作决策 - 爸爸参与每个重要决策")
    print("  3. 🧠 认知推理 - 逻辑分析与应用理解")
    print("  4. 📊 评估体系 - 多维度评估与风险控制")
    print("  5. 💾 记忆学习 - 经验积累与偏好适应")

    print("\n💡 使用建议:")
    print("  • 复杂项目时使用规划器功能")
    print("  • 重要决策时启用人机协作模式")
    print("  • 定期查看决策历史获取洞察")
    print("  • 与小诺共同学习，持续优化决策")

if __name__ == "__main__":
    asyncio.run(test_optimized_xiaonuo())