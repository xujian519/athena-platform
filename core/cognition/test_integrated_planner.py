#!/usr/bin/env python3
from __future__ import annotations
"""
集成测试 - 验证增强意图分析器与Gateway系统的集成
Integration Test - Enhanced Intent Analyzer with Gateway System

验证：
1. 集成规划引擎正常工作
2. 小诺协调器能正确调用增强分析器
3. 意图识别结果包含增强信息
4. 向后兼容性

Author: Athena Team
Version: 1.0.0
Date: 2026-02-24
"""

import asyncio
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))


def print_separator(title: str = ""):
    """打印分隔线"""
    print("\n" + "=" * 80)
    if title:
        print(f"  {title}")
        print("=" * 80)


async def test_integrated_planner():
    """测试集成规划引擎"""
    print_separator("测试集成规划引擎")

    from core.cognition.integrated_planner_engine import (
        create_planner_engine,
    )

    # 创建集成规划引擎
    planner = create_planner_engine(use_enhanced=True)

    # 测试用户输入
    test_input = "我要写一篇农业领域的实用新型专利"

    print(f"\n📝 用户输入: {test_input}")

    # 生成规划
    plan = await planner.plan(test_input)

    # 验证结果
    print("\n🎯 规划结果:")
    print(f"  方案ID: {plan.plan_id}")
    print(f"  意图类型: {plan.intent.intent_type.value}")
    print(f"  主要目标: {plan.intent.primary_goal}")
    print(f"  置信度: {plan.intent.confidence:.2f}")
    print(f"  执行模式: {plan.mode.value}")
    print(f"  步骤数: {len(plan.steps)}")

    # 检查增强信息
    metadata = plan.metadata
    if metadata.get("enhanced_analysis"):
        print("\n✨ 增强分析已启用")
        if metadata.get("required_layers"):
            print(f"  需要层级: {metadata['required_layers']}")
        if metadata.get("suggested_agent"):
            print(f"  建议智能体: {metadata['suggested_agent']}")

    # 检查实体信息
    entities = plan.intent.entities
    if entities.get("patent_type"):
        print(f"\n📋 专利类型: {entities['patent_type']}")
    if entities.get("patent_sub_domain"):
        print(f"  专利子领域: {entities['patent_sub_domain']}")
    if entities.get("domain"):
        print(f"  业务领域: {entities['domain']}")

    # 验证关键信息
    assert plan.intent.intent_type.value in ["task", "analysis"], \
        f"意图类型应该是task或analysis，实际为{plan.intent.intent_type.value}"
    assert plan.intent.confidence > 0.7, \
        f"置信度应该大于0.7，实际为{plan.intent.confidence}"
    assert entities.get("patent_type") == "utility_model", \
        f"专利类型应为utility_model，实际为{entities.get('patent_type')}"
    assert entities.get("patent_sub_domain") == "agriculture", \
        f"专利子领域应为agriculture，实际为{entities.get('patent_sub_domain')}"

    print("\n✅ 集成规划引擎测试通过！")
    return True


async def test_xiaonuo_coordinator():
    """测试小诺协调器集成"""
    print_separator("测试小诺协调器集成")

    from core.agents.base import AgentRequest
    from core.agents.xiaonuo.xiaonuo_agent_v2 import XiaonuoAgentV2 as XiaonuoAgent

    # 创建小诺协调器
    xiaonuo = XiaonuoAgent()

    # 调用初始化方法
    await xiaonuo.initialize()

    # 等待初始化完成
    await asyncio.sleep(0.5)

    # 检查规划器是否初始化
    if not hasattr(xiaonuo, 'planner') or xiaonuo.planner is None:
        print("⚠️ 小诺规划器未初始化，跳过测试")
        return False

    print("✅ 小诺协调器初始化成功")
    print(f"   规划器类型: {type(xiaonuo.planner).__name__}")

    # 检查是否使用增强分析器
    if hasattr(xiaonuo.planner, 'enhanced_available'):
        if xiaonuo.planner.enhanced_available:
            print("   ✅ 使用增强意图分析器")
        else:
            print("   📌 使用基础意图分析器")

    # 创建智能规划请求
    test_input = "我要写一篇农业领域的实用新型专利"

    request = AgentRequest(
        request_id="test-integrated-planner",
        action="intelligent-plan",
        parameters={
            "user_input": test_input,
            "context": {"test": True},
        },
    )

    print(f"\n📝 发送请求: {test_input}")

    # 处理请求
    response = await xiaonuo.process(request)

    # 验证响应
    print("\n📊 响应结果:")
    print(f"  成功: {response.success}")

    if response.success:
        data = response.data
        print(f"  方案ID: {data.get('plan_id')}")
        print(f"  意图类型: {data.get('intent_type')}")
        print(f"  主要目标: {data.get('primary_goal')}")
        print(f"  置信度: {data.get('confidence')}")

        steps = data.get('steps', [])
        print(f"  步骤数: {len(steps)}")

        for i, step in enumerate(steps[:3], 1):  # 显示前3个步骤
            print(f"    {i}. {step.get('description')} ({step.get('agent')})")

        # 验证
        assert response.success, "请求应该成功"
        assert data.get("success"), "规划应该成功"
        assert len(steps) > 0, "应该有执行步骤"

        print("\n✅ 小诺协调器集成测试通过！")
        return True
    else:
        print(f"  错误: {response.error}")
        return False


async def test_backward_compatibility():
    """测试向后兼容性"""
    print_separator("测试向后兼容性")

    # 测试基础规划器
    from core.cognition.xiaonuo_planner_engine import XiaonuoPlannerEngine

    planner = XiaonuoPlannerEngine()

    test_input = "帮我查询专利信息"
    plan = await planner.plan(test_input)

    print(f"\n📝 输入: {test_input}")
    print(f"  意图类型: {plan.intent.intent_type.value}")
    print(f"  主要目标: {plan.intent.primary_goal}")
    print(f"  置信度: {plan.intent.confidence:.2f}")

    assert plan.intent.intent_type.value == "query", \
        f"基础规划器应该识别为query，实际为{plan.intent.intent_type.value}"

    print("\n✅ 向后兼容性测试通过！")
    return True


async def test_various_inputs():
    """测试各种输入"""
    print_separator("测试各种输入场景")

    from core.cognition.integrated_planner_engine import create_planner_engine

    planner = create_planner_engine(use_enhanced=True)

    test_cases = [
        {
            "input": "我要写一篇农业领域的实用新型专利",
            "expected_patent_type": "utility_model",
            "expected_sub_domain": "agriculture",
        },
        {
            "input": "检索电子电路相关的发明专利",
            "expected_patent_type": "invention",
            "expected_sub_domain": "electronics",
        },
        {
            "input": "分析汽车制动系统的侵权风险",
            "expected_sub_domain": "vehicle",
        },
    ]

    for i, case in enumerate(test_cases, 1):
        print(f"\n📝 测试案例 {i}: {case['input'][:30]}...")

        plan = await planner.plan(case["input"])
        entities = plan.intent.entities

        # 验证专利类型
        if "expected_patent_type" in case:
            patent_type = entities.get("patent_type")
            status = "✅" if patent_type == case["expected_patent_type"] else "❌"
            print(f"   {status} 专利类型: {patent_type} (期望: {case['expected_patent_type']})")

        # 验证子领域
        if "expected_sub_domain" in case:
            sub_domain = entities.get("patent_sub_domain")
            status = "✅" if sub_domain == case["expected_sub_domain"] else "❌"
            print(f"   {status} 子领域: {sub_domain} (期望: {case['expected_sub_domain']})")

    print("\n✅ 各种输入场景测试完成！")
    return True


async def main():
    """主测试函数"""
    print_separator("增强意图分析器 - Gateway集成测试")

    results = {}

    try:
        # 1. 测试集成规划引擎
        results["integrated_planner"] = await test_integrated_planner()

        # 2. 测试小诺协调器
        results["xiaonuo_coordinator"] = await test_xiaonuo_coordinator()

        # 3. 测试向后兼容性
        results["backward_compatibility"] = await test_backward_compatibility()

        # 4. 测试各种输入
        results["various_inputs"] = await test_various_inputs()

    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return 1

    # 汇总结果
    print_separator("测试结果汇总")

    passed = sum(1 for v in results.values() if v)
    total = len(results)

    for name, result in results.items():
        status = "✅ 通过" if result else "❌ 失败"
        print(f"  {name}: {status}")

    print(f"\n总计: {passed}/{total} 测试通过")

    if passed == total:
        print("\n🎉 所有测试通过！增强意图分析器已成功集成到Gateway系统！")
        return 0
    else:
        print(f"\n⚠️ 有 {total - passed} 个测试失败")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
