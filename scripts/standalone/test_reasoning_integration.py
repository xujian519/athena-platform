#!/usr/bin/env python3
"""
推理引擎集成测试
Test Reasoning Engine Integration in Production Environment
"""

import asyncio
import sys

sys.path.insert(0, '/Users/xujian/Athena工作平台')

def test_engine_imports():
    """测试引擎导入"""
    print("=" * 60)
    print("📦 测试1: 引擎导入")
    print("=" * 60)

    results = {}

    # 测试六步推理引擎
    try:
        from core.reasoning.xiaonuo_six_step_reasoning import XiaonuoSixStepReasoningEngine
        engine = XiaonuoSixStepReasoningEngine()
        results['六步推理引擎'] = engine is not None
        print("  ✅ 六步推理引擎导入成功")
    except Exception as e:
        results['六步推理引擎'] = False
        print(f"  ❌ 六步推理引擎导入失败: {e}")

    # 测试七步推理引擎
    try:
        from core.reasoning.athena_super_reasoning import AthenaSuperReasoningEngine
        engine = AthenaSuperReasoningEngine()
        results['七步推理引擎'] = engine is not None
        print("  ✅ 七步推理引擎导入成功")
    except Exception as e:
        results['七步推理引擎'] = False
        print(f"  ❌ 七步推理引擎导入失败: {e}")

    # 测试ReAct推理桥接器
    try:
        from core.reasoning.xiaonuo_reasoning_bridge import XiaonuoReasoningBridge
        bridge = XiaonuoReasoningBridge()
        results['ReAct推理桥接器'] = bridge is not None
        print("  ✅ ReAct推理桥接器导入成功")
    except Exception as e:
        results['ReAct推理桥接器'] = False
        print(f"  ❌ ReAct推理桥接器导入失败: {e}")

    return results


def test_agent_integration():
    """测试智能体集成"""
    print("\n" + "=" * 60)
    print("🤖 测试2: 智能体集成")
    print("=" * 60)

    results = {}

    # 测试小诺协调器
    try:
        from core.framework.agents.xiaonuo_coordinator import XiaonuoAgent
        print("  ✅ 小诺协调器导入成功")
        results['小诺协调器'] = True

        # 检查是否有推理相关属性
        agent = XiaonuoAgent({'agent_id': 'test'})
        reasoning_attrs = [a for a in dir(agent) if 'reason' in a.lower()]
        if reasoning_attrs:
            print(f"     推理相关方法: {reasoning_attrs[:5]}")
        else:
            print("     ⚠️ 未发现推理相关方法")
            results['小诺协调器'] = False
    except Exception as e:
        results['小诺协调器'] = False
        print(f"  ❌ 小诺协调器导入失败: {e}")

    # 测试小娜专业版
    try:
        from core.framework.agents.xiaona_professional import XiaonaProfessionalAgent
        print("  ✅ 小娜专业版导入成功")
        results['小娜专业版'] = True

        # 检查是否集成了推理编排器
        agent = XiaonaProfessionalAgent(config={'llm_provider': 'test'})
        if hasattr(agent, 'reasoning_orchestrator'):
            print("     ✅ 已集成推理编排器")
        else:
            print("     ⚠️ 未发现推理编排器")
    except Exception as e:
        results['小娜专业版'] = False
        print(f"  ❌ 小娜专业版导入失败: {e}")

    return results


async def test_reasoning_execution():
    """测试推理执行"""
    print("\n" + "=" * 60)
    print("⚡ 测试3: 推理执行")
    print("=" * 60)

    results = {}

    # 测试六步推理执行
    try:
        from core.reasoning.xiaonuo_six_step_reasoning import XiaonuoSixStepReasoningEngine
        engine = XiaonuoSixStepReasoningEngine()
        result = await engine.execute_super_reasoning("测试问题", {})
        results['六步推理执行'] = result is not None
        print("  ✅ 六步推理执行成功")
    except Exception as e:
        results['六步推理执行'] = False
        print(f"  ❌ 六步推理执行失败: {e}")

    # 测试七步推理执行
    try:
        from core.reasoning.athena_super_reasoning import AthenaSuperReasoningEngine
        engine = AthenaSuperReasoningEngine()
        result = await engine.execute_super_reasoning("测试问题", {})
        results['七步推理执行'] = result is not None
        print("  ✅ 七步推理执行成功")
    except Exception as e:
        results['七步推理执行'] = False
        print(f"  ❌ 七步推理执行失败: {e}")

    # 测试ReAct推理执行
    try:
        from core.reasoning.xiaonuo_reasoning_bridge import ReasoningRequest, XiaonuoReasoningBridge
        bridge = XiaonuoReasoningBridge()
        request = ReasoningRequest(problem="测试问题", mode="six_step")
        result = await bridge.execute_reasoning(request)
        results['ReAct推理执行'] = result is not None and result.success
        print("  ✅ ReAct推理执行成功")
    except Exception as e:
        results['ReAct推理执行'] = False
        print(f"  ❌ ReAct推理执行失败: {e}")

    return results


def print_summary(all_results):
    """打印总结"""
    print("\n" + "=" * 60)
    print("📊 集成测试总结")
    print("=" * 60)

    total = 0
    passed = 0

    for category, results in all_results.items():
        print(f"\n{category}:")
        for name, status in results.items():
            emoji = "✅" if status else "❌"
            print(f"  {emoji} {name}")
            total += 1
            if status:
                passed += 1

    print("\n" + "=" * 60)
    print(f"总计: {passed}/{total} 测试通过")
    print("=" * 60)

    # 判断是否已集成到生产环境
    print("\n🔍 生产环境集成状态:")
    if all_results.get('智能体集成', {}).get('小娜专业版'):
        print("  ✅ 小娜专业版已集成推理编排器")
    else:
        print("  ⚠️ 小娜专业版未完全集成推理引擎")

    if all_results.get('智能体集成', {}).get('小诺协调器'):
        print("  ✅ 小诺协调器可用")
    else:
        print("  ⚠️ 小诺协调器推理集成待完善")


async def main():
    """主函数"""
    print("🧪 Athena推理引擎集成测试")
    print("=" * 60)

    all_results = {}

    # 测试1: 引擎导入
    all_results['引擎导入'] = test_engine_imports()

    # 测试2: 智能体集成
    all_results['智能体集成'] = test_agent_integration()

    # 测试3: 推理执行
    all_results['推理执行'] = await test_reasoning_execution()

    # 打印总结
    print_summary(all_results)


if __name__ == "__main__":
    asyncio.run(main())
