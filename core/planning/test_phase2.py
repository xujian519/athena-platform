#!/usr/bin/env python3
from __future__ import annotations
"""
Phase 2功能测试脚本
测试GLM-4.7集成、并行任务识别、动态调整等新功能

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

from core.integration.planning_gateway_integration import get_planning_gateway_integration
from core.planning.explicit_planner import PlanningRequest, Priority, get_explicit_planner


async def test_glm47_integration():
    """测试1: GLM-4.7集成"""
    print("\n" + "=" * 60)
    print("🧪 测试1: GLM-4.7集成")
    print("=" * 60)

    planner = get_explicit_planner()

    # 显示LLM信息
    llm_info = planner.llm_client.get_model_info()
    print("\n🤖 LLM信息:")
    print(f"   模型: {llm_info['model']}")
    print(f"   提供商: {llm_info['provider']}")
    print(f"   模拟模式: {llm_info['mock_mode']}")
    print(f"   API密钥已配置: {llm_info['api_key_configured']}")
    print(f"   能力: {', '.join(llm_info['capabilities'])}")

    # 创建计划
    request = PlanningRequest(
        title="GLM-4.7测试计划",
        description="检索关于人工智能在医疗领域应用的专利,并分析技术趋势",
        context={"domain": "医疗AI", "language": "zh"},
        requirements=["检索准确", "分析深入"],
        priority=Priority.HIGH,
    )

    result = await planner.create_plan(request)

    if result.success:
        print("\n✅ GLM-4.7计划生成成功!")
        print(f"   计划ID: {result.plan_id}")
        print(f"   步骤数: {len(result.steps)}")
        print(f"   置信度: {result.confidence_score:.1%}")
        return result.plan_id
    else:
        print(f"\n❌ 计划生成失败: {result.feedback}")
        return None


async def test_parallel_task_identification(plan_id: str):
    """测试2: 并行任务识别"""
    print("\n" + "=" * 60)
    print("🧪 测试2: 并行任务识别")
    print("=" * 60)

    planner = get_explicit_planner()

    # 识别并行任务
    parallel_groups = await planner.identify_parallel_tasks(plan_id)

    if parallel_groups:
        print(f"\n✅ 识别到 {len(parallel_groups)} 组并行任务:")
        for i, group in enumerate(parallel_groups, 1):
            print(f"\n   并行组 {i}: 步骤 {group}")
    else:
        print("\nℹ️  未发现可并行的任务")

    return parallel_groups


async def test_dynamic_adjustment():
    """测试3: 动态调整"""
    print("\n" + "=" * 60)
    print("🧪 测试3: 动态调整(GLM-4.7建议)")
    print("=" * 60)

    planner = get_explicit_planner()

    # 创建一个简单的计划
    request = PlanningRequest(
        title="动态调整测试", description="测试专利检索", context={}, priority=Priority.MEDIUM
    )

    result = await planner.create_plan(request)

    if not result.success:
        print("❌ 计划创建失败")
        return

    plan_id = result.plan_id
    plan = await planner.get_plan(plan_id)

    # 模拟某个步骤失败
    if plan and len(plan.steps) > 0:
        failed_step = plan.steps[1]  # 假设第二步失败
        error = "数据库连接超时"

        print("\n🔧 模拟步骤失败:")
        print(f"   步骤: {failed_step.name}")
        print(f"   错误: {error}")

        # 尝试动态调整
        adjustment_success = await planner._adjust_plan(plan_id, failed_step, error)

        if adjustment_success:
            print("\n✅ 动态调整成功!")
            # 查看调整后的计划
            updated_plan = await planner.get_plan(plan_id)
            print("   原步骤数: 6")
            print(f"   新步骤数: {len(updated_plan.steps)}")
            print(f"   新增步骤: {[s.name for s in updated_plan.steps if '替代' in s.name]}")
        else:
            print("\n❌ 动态调整失败")


async def test_gateway_integration():
    """测试4: 网关集成"""
    print("\n" + "=" * 60)
    print("🧪 测试4: 网关集成")
    print("=" * 60)

    integration = get_planning_gateway_integration()

    # 测试规划判断
    test_messages = [
        ("检索深度学习专利", True),
        ("你好", False),
        ("分析人工智能在医疗领域的应用趋势,生成详细报告", True),
        ("今天天气怎么样", False),
    ]

    print("\n📊 规划判断测试:")
    for message, expected in test_messages:
        should_plan, reason = integration.should_use_planning(message, 0.8)
        status = "✅" if should_plan == expected else "❌"
        print(f'   {status} "{message[:30]}..."')
        print(f"      结果: {'使用规划' if should_plan else '直接执行'}")
        print(f"      原因: {reason}")

    # 测试完整处理流程
    print("\n🔄 完整处理流程测试:")
    result = await integration.process_with_planning(
        user_message="检索关于区块链技术的专利,分析技术发展趋势",
        context={"user_id": "test_user"},
        session_id="test_session",
    )

    if result["success"]:
        print("✅ 处理成功!")
        print(f"   模式: {result['mode']}")
        print(f"   计划ID: {result.get('plan_id')}")
        print(f"   并行组: {len(result.get('parallel_groups', []))}")
    else:
        print(f"❌ 处理失败: {result.get('error')}")


async def test_parallel_execution_suggestion(plan_id: str):
    """测试5: 并行执行建议"""
    print("\n" + "=" * 60)
    print("🧪 测试5: 并行执行建议")
    print("=" * 60)

    integration = get_planning_gateway_integration()

    suggestion = await integration.suggest_parallel_execution(plan_id)

    if "error" not in suggestion:
        print("\n✅ 并行执行分析完成:")
        print(f"   有并行任务: {suggestion['has_parallel_tasks']}")
        print(f"   并行组数: {suggestion.get('total_groups', 0)}")
        print(f"   预计节省时间: {suggestion.get('estimated_time_saved_minutes', 0)} 分钟")
        print(f"   优化建议: {suggestion.get('optimization_suggestion', '')}")

        if "execution_plan" in suggestion:
            exec_plan = suggestion["execution_plan"]
            print(f"\n   执行阶段: {exec_plan['total_stages']}")
            for stage in exec_plan["stages"]:
                print(f"      阶段 {stage['stage']}: {stage['type']} - 步骤 {stage['steps']}")
    else:
        print(f"\n❌ 分析失败: {suggestion['error']}")


async def main():
    """主测试函数"""
    print("\n" + "=" * 60)
    print("🧪 Phase 2功能测试套件")
    print("GLM-4.7集成 + 并行任务识别 + 动态调整")
    print("=" * 60)

    try:
        # 测试1: GLM-4.7集成
        plan_id = await test_glm47_integration()

        if plan_id:
            # 测试2: 并行任务识别
            await test_parallel_task_identification(plan_id)

            # 测试5: 并行执行建议
            await test_parallel_execution_suggestion(plan_id)

        # 测试3: 动态调整
        await test_dynamic_adjustment()

        # 测试4: 网关集成
        await test_gateway_integration()

        print("\n" + "=" * 60)
        print("✅ Phase 2功能测试完成!")
        print("=" * 60)

    except Exception:
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
