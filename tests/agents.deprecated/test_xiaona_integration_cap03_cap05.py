#!/usr/bin/env python3
"""
小娜Agent集成测试 - CAP03/CAP04/CAP05

展示如何通过小娜Agent调用新实现的专利撰写、审查答复和无效宣告系统。
"""
import asyncio
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from core.framework.agents.xiaona_legal import XiaonaLegalAgent

from core.framework.agents.base import AgentRequest


async def test_patent_drafting_integration():
    """测试专利撰写集成（CAP03）"""
    print("\n" + "="*80)
    print("✍️ 测试CAP03专利撰写集成")
    print("="*80)

    # 创建小娜Agent
    agent = XiaonaLegalAgent()
    await agent.initialize()  # 重要：初始化agent

    # 方式1: 使用技术交底书文件（推荐）
    print("\n【方式1: 使用技术交底书文件】")
    request1 = AgentRequest(
        request_id="test_drafting_001",
        action="patent-drafting",
        parameters={
            "disclosure_file": "/path/to/disclosure.docx",
            "claim_count": 3,
            "include_background": True,
            "include_detailed_description": True
        }
    )

    response1 = await agent.process(request1)
    print(f"成功: {response1.success}")
    if response1.success:
        print(f"专利标题: {response1.data['patent_application']['title']}")
        print(f"权利要求数: {len(response1.data['patent_application']['claims'])}")
    else:
        print(f"错误: {response1.error}")

    # 方式2: 使用参数直接构建（简化版）
    print("\n【方式2: 使用参数直接构建】")
    request2 = AgentRequest(
        request_id="test_drafting_002",
        action="patent-drafting",
        parameters={
            "invention_title": "一种智能控制系统",
            "technical_field": "自动化控制领域",
            "technical_problem": "现有控制方式响应慢",
            "technical_solution": "采用深度学习算法优化控制决策",
            "beneficial_effects": "提高响应速度30%"
        }
    )

    response2 = await agent.process(request2)
    print(f"成功: {response2.success}")
    if response2.success:
        print(f"专利标题: {response2.data['patent_application']['title']}")
        print(f"摘要: {response2.data['patent_application']['abstract'][:100]}...")
    else:
        print(f"错误: {response2.error}")

    print("\n" + "="*80)


async def test_oa_response_integration():
    """测试审查意见答复集成（CAP04）"""
    print("\n" + "="*80)
    print("📝 测试CAP04审查答复集成")
    print("="*80)

    # 创建小娜Agent
    agent = XiaonaLegalAgent()
    await agent.initialize()  # 重要：初始化agent

    # 方式1: 完整审查意见处理
    print("\n【方式1: 完整审查意见处理】")
    request1 = AgentRequest(
        request_id="test_oa_001",
        action="office-action-response",
        parameters={
            "oa_number": "OA202312001",
            "patent_id": "CN123456789A",
            "oa_date": "2023-12-01",
            "rejection_type": "novelty",
            "cited_claims": [1, 2],
            "examiner_arguments": [
                "对比文件D1公开了相同的图像识别方法",
                "权利要求1不具备新颖性"
            ],
            "prior_art_references": ["CN112233445A", "US9876543B2"],
            "current_claims": [
                "1. 一种图像识别方法，包括输入层和卷积层。",
                "2. 根据权利要求1所述的方法，其特征在于，所述卷积层采用多尺度卷积核。"
            ],
            "include_amendments": True,
            "auto_generate_amendments": True
        }
    )

    response1 = await agent.process(request1)
    print(f"成功: {response1.success}")
    if response1.success:
        strategy_type = response1.data.get('oa_response', {}).get('strategy', {}).get('strategy_type', 'N/A')
        success_prob = response1.data.get('metadata', {}).get('success_probability', 0.0)
        claims_amended = response1.data.get('metadata', {}).get('claims_amended', False)
        print(f"策略类型: {strategy_type}")
        print(f"成功概率: {success_prob:.2%}")
        print(f"修改权利要求: {claims_amended}")
    else:
        print(f"错误: {response1.error}")

    # 方式2: 简化版策略建议
    print("\n【方式2: 简化版策略建议】")
    request2 = AgentRequest(
        request_id="test_oa_002",
        action="office-action-response",
        parameters={
            "oa_number": "OA202312002",
            "patent_id": "CN987654321A",
            "rejection_type": "inventiveness",
            "examiner_arguments": ["权利要求1显而易见"]
        }
    )

    response2 = await agent.process(request2)
    print(f"成功: {response2.success}")
    if response2.success:
        print(f"推荐策略: {response2.data['recommended_strategy']}")
        print(f"成功概率: {response2.data['estimated_success_rate']:.2%}")
        print(f"建议论点: {response2.data['suggested_arguments']}")

    print("\n" + "="*80)


async def test_invalidity_request_integration():
    """测试无效宣告集成（CAP05）"""
    print("\n" + "="*80)
    print("🔍 测试CAP05无效宣告集成")
    print("="*80)

    # 创建小娜Agent
    agent = XiaonaLegalAgent()
    await agent.initialize()  # 重要：初始化agent

    # 方式1: 完整无效宣告请求
    print("\n【方式1: 完整无效宣告请求】")
    request1 = AgentRequest(
        request_id="test_invalidity_001",
        action="invalidity-request",
        parameters={
            "patent_id": "CN123456789A",
            "target_claims": [
                "1. 一种图像识别方法，包括输入层和卷积层。",
                "2. 根据权利要求1所述的方法，其特征在于，所述卷积层采用多尺度卷积核。",
                "3. 根据权利要求1所述的方法，其特征在于，还包括池化层。"
            ],
            "petitioner_info": {
                "name": "XXX科技公司",
                "address": "北京市XXX区XXX路XXX号"
            },
            "max_evidence": 10,
            "auto_collect_evidence": True
        }
    )

    response1 = await agent.process(request1)
    print(f"成功: {response1.success}")
    if response1.success:
        evidence_count = response1.data.get('metadata', {}).get('evidence_count', 0)
        grounds_count = response1.data.get('metadata', {}).get('grounds_count', 0)
        petition_text = response1.data.get('invalidity_result', {}).get('petition_text', '')
        print(f"证据数量: {evidence_count}")
        print(f"无效理由数: {grounds_count}")
        print(f"请求书长度: {len(petition_text)} 字符")
    else:
        print(f"错误: {response1.error}")

    # 方式2: 简化版理由分析
    print("\n【方式2: 简化版理由分析】")
    request2 = AgentRequest(
        request_id="test_invalidity_002",
        action="invalidity-request",
        parameters={
            "patent_id": "CN987654321A",
            "ground_type": "inventiveness"
        }
    )

    response2 = await agent.process(request2)
    print(f"成功: {response2.success}")
    if response2.success:
        print(f"推荐策略: {response2.data['invalidity_analysis']['recommended_strategy']}")
        print(f"建议现有技术: {response2.data['suggested_prior_art']}")

    print("\n" + "="*80)


async def main():
    """运行所有集成测试"""
    print("\n" + "="*80)
    print("🚀 小娜Agent集成测试 - CAP03/CAP04/CAP05")
    print("="*80)

    try:
        # 测试专利撰写
        await test_patent_drafting_integration()

        # 测试审查答复
        await test_oa_response_integration()

        # 测试无效宣告
        await test_invalidity_request_integration()

        print("\n" + "="*80)
        print("✅ 所有集成测试完成")
        print("="*80)

    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
