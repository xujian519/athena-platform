#!/usr/bin/env python3
"""
小娜Agent集成测试 - CAP06侵权分析

展示如何通过小娜Agent调用侵权分析系统。
"""
import asyncio
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from core.agents.xiaona_legal import XiaonaLegalAgent
from core.agents.base import AgentRequest


async def test_infringement_analysis_integration():
    """测试侵权分析集成（CAP06）"""
    print("\n" + "="*80)
    print("⚖️ 测试CAP06侵权分析集成")
    print("="*80)

    # 创建小娜Agent
    agent = XiaonaLegalAgent()
    await agent.initialize()

    # 方式1: 完整侵权分析（推荐）
    print("\n【方式1: 完整侵权分析】")
    request1 = AgentRequest(
        request_id="test_infringement_001",
        action="infringement-analysis",
        parameters={
            "patent_id": "CN123456789A",
            "claims": [
                "1. 一种图像识别方法，包括输入层和卷积层，其特征在于，所述卷积层采用多尺度卷积核。",
                "2. 根据权利要求1所述的方法，其特征在于，还包括池化层。"
            ],
            "product_description": """
            本产品是一种智能图像识别系统，用于人脸识别应用。
            系统包括数据输入模块，用于接收图像数据。
            系统还包括卷积神经网络模块，该模块使用3x3和5x5两种尺寸的卷积核进行特征提取。
            系统还包括池化层，用于降低特征维度。
            系统输出识别结果到显示模块。
            """,
            "product_name": "智能图像识别系统",
            "include_comparison_table": True
        }
    )

    response1 = await agent.process(request1)
    print(f"成功: {response1.success}")
    if response1.success:
        metadata = response1.data.get('infringement_result', {}).get('metadata', {})
        print(f"总体侵权: {metadata.get('overall_infringement', False)}")
        print(f"风险等级: {metadata.get('overall_risk', 'unknown')}")
        print(f"分析权利要求: {metadata.get('claims_analyzed', 0)} 条")
    else:
        print(f"错误: {response1.error}")

    # 方式2: 简化版分析建议
    print("\n【方式2: 简化版分析建议】")
    request2 = AgentRequest(
        request_id="test_infringement_002",
        action="infringement-analysis",
        parameters={
            "patent_id": "CN987654321A",
            "product_name": "竞争对手产品"
        }
    )

    response2 = await agent.process(request2)
    print(f"成功: {response2.success}")
    if response2.success:
        print(f"分析需求: {response2.data['analysis_requirements']}")
        print(f"推荐步骤: {response2.data['recommended_steps']}")

    print("\n" + "="*80)


async def main():
    """运行集成测试"""
    print("\n" + "="*80)
    print("🚀 小娜Agent集成测试 - CAP06侵权分析")
    print("="*80)

    try:
        # 测试侵权分析
        await test_infringement_analysis_integration()

        print("\n" + "="*80)
        print("✅ 集成测试完成")
        print("="*80)

    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
