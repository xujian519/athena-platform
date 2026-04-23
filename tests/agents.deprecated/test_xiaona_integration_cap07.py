#!/usr/bin/env python3
"""
CAP07许可协议起草系统 - 小娜Agent集成测试

测试许可协议起草功能与小娜Agent的集成。
"""
import asyncio
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from core.agents.xiaona_legal import XiaonaLegalAgent, LegalTaskType
from core.agents.base import AgentRequest


async def test_licensing_full_processing():
    """测试完整许可协议起草流程"""
    print("\n" + "="*80)
    print("🚀 CAP07许可协议起草 - 完整处理模式测试")
    print("="*80)

    agent = XiaonaLegalAgent()

    try:
        # 初始化Agent
        await agent.initialize()
        print("✅ Agent初始化成功")

        # 创建AgentRequest
        request = AgentRequest(
            request_id="test_licensing_001",
            action=LegalTaskType.LICENSING_DRAFTING,
            parameters={
                "patent_id": "CN123456789A",
                "patent_info": {
                    "patent_type": "invention",
                    "technology_field": "人工智能",
                    "claims_count": 5,
                    "title": "一种智能控制系统"
                },
                "licensor_info": {
                    "name": "许可方科技公司",
                    "address": "北京市XXX区XXX路XXX号"
                },
                "licensee_info": {
                    "name": "被许可方制造公司",
                    "address": "上海市XXX区XXX路XXX号"
                },
                "license_requirements": {
                    "license_type": "non-exclusive",
                    "scope": "中国境内",
                    "duration": "5年"
                }
            }
        )

        print(f"✅ 请求创建成功: {request.action}")

        # 处理请求
        response = await agent.process(request)

        # 验证响应
        assert response is not None, "响应不应为空"
        assert response.success, f"处理应成功: {response.error}"

        # 输出结果
        result = response.data
        print(f"\n✅ 许可协议起草完成:")
        print(f"   任务类型: {result.get('task_type')}")
        print(f"   状态: {result.get('status')}")

        metadata = result.get('metadata', {})
        print(f"   专利号: {metadata.get('patent_id')}")
        print(f"   许可方: {metadata.get('licensor')}")
        print(f"   被许可方: {metadata.get('licensee')}")
        print(f"   许可类型: {metadata.get('license_type')}")
        print(f"   提成率: {metadata.get('royalty_rate', 0):.1%}")
        print(f"   预付费用: {metadata.get('upfront_fee', 0):.1f}万元")

        licensing_result = result.get('licensing_result', {})
        if 'agreement_text' in licensing_result:
            agreement_text = licensing_result['agreement_text']
            print(f"\n📄 协议文本（前500字）:")
            print(agreement_text[:500] + "...")

        print("\n" + "="*80)
        print("✅ 完整处理模式测试通过")
        print("="*80)

        return True

    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

    finally:
        await agent.shutdown()


async def test_licensing_simplified_advice():
    """测试简化建议模式（信息不完整时）"""
    print("\n" + "="*80)
    print("💡 CAP07许可协议起草 - 简化建议模式测试")
    print("="*80)

    agent = XiaonaLegalAgent()

    try:
        await agent.initialize()
        print("✅ Agent初始化成功")

        # 创建信息不完整的请求
        request = AgentRequest(
            request_id="test_licensing_002",
            action=LegalTaskType.LICENSING_DRAFTING,
            parameters={
                "patent_id": "CN987654321A",
                "licensor_info": {
                    "name": "许可方公司"
                },
                "licensee_info": {
                    "name": "被许可方公司"
                }
            }
        )

        print(f"✅ 请求创建成功（信息不完整）")

        # 处理请求
        response = await agent.process(request)

        # 验证响应
        assert response is not None, "响应不应为空"
        assert response.success, f"处理应成功: {response.error}"

        # 输出结果
        result = response.data
        print(f"\n💡 返回起草建议:")
        print(f"   任务类型: {result.get('task_type')}")
        print(f"   状态: {result.get('status')}")

        if 'drafting_requirements' in result:
            print(f"\n   📋 起草要求:")
            for req in result['drafting_requirements']:
                print(f"      - {req}")

        if 'recommended_steps' in result:
            print(f"\n   📝 推荐步骤:")
            for step in result['recommended_steps']:
                print(f"      {step}")

        print("\n" + "="*80)
        print("✅ 简化建议模式测试通过")
        print("="*80)

        return True

    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

    finally:
        await agent.shutdown()


async def main():
    """主测试函数"""
    print("\n" + "="*80)
    print("🧪 CAP07许可协议起草 - 小娜Agent集成测试套件")
    print("="*80)

    results = []

    # 测试1: 完整处理模式
    result1 = await test_licensing_full_processing()
    results.append(("完整处理模式", result1))

    # 等待一下
    await asyncio.sleep(1)

    # 测试2: 简化建议模式
    result2 = await test_licensing_simplified_advice()
    results.append(("简化建议模式", result2))

    # 汇总结果
    print("\n" + "="*80)
    print("📊 测试结果汇总")
    print("="*80)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for test_name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{status} - {test_name}")

    print(f"\n总计: {passed}/{total} 测试通过")

    if passed == total:
        print("\n🎉 所有测试通过！CAP07许可协议起草系统已成功集成到小娜Agent。")
        return 0
    else:
        print(f"\n⚠️ {total - passed} 个测试失败，请检查。")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
