#!/usr/bin/env python3
"""
测试统一知识图谱服务
Test Unified Knowledge Graph Service

作者: 小诺·双鱼公主
创建时间: 2024年12月15日
"""

import asyncio
import sys
import os
from pathlib import Path

# 添加服务路径
sys.path.append(str(Path(__file__).parent.parent.parent))
sys.path.append(str(Path(__file__).parent))

from services.knowledge_unified.integrated_patent_service import get_integrated_patent_service

async def test_patent_review():
    """测试专利审查场景"""
    print("\n" + "="*60)
    print("测试场景1: 专利审查")
    print("="*60)

    service = await get_integrated_patent_service()

    query = "这个专利是否符合新颖性要求？"
    patent_text = """
    本发明涉及一种基于人工智能的图像识别方法，包括：
    1. 收集训练图像数据集；
    2. 构建深度神经网络模型；
    3. 使用训练数据对模型进行训练；
    4. 通过训练后的模型识别图像。

    本发明的创新点在于使用了新的网络结构，能够提高识别准确率10%以上。
    """

    response = await service.process_patent_query(
        query=query,
        patent_text=patent_text,
        context_type="patent_review"
    )

    print(f"\n查询ID: {response['query_id']}")
    print(f"识别意图: {response['intent']}")
    print(f"\n系统角色提示词:\n{response['prompts']['system_role'][:200]}...")
    print(f"\n知识指导:\n{response['prompts']['knowledge_guidance'][:300]}...")
    print(f"\n建议操作: {[action['label'] for action in response['suggested_actions']]}")

async def test_legal_advice():
    """测试法律咨询场景"""
    print("\n" + "="*60)
    print("测试场景2: 法律咨询")
    print("="*60)

    service = await get_integrated_patent_service()

    query = "我们的产品是否可能侵犯这个专利？"
    patent_text = """
    专利权利要求1：
    一种数据处理方法，其特征在于，包括：
    - 接收数据输入；
    - 使用算法处理数据；
    - 输出处理结果。
    """

    response = await service.process_patent_query(
        query=query,
        patent_text=patent_text,
        context_type="legal_advice",
        context={"user_type": "企业", "industry": "软件"}
    )

    print(f"\n查询ID: {response['query_id']}")
    print(f"识别意图: {response['intent']}")
    print(f"\n法律依据:\n{response['prompts']['legal_basis'][:300]}...")
    print(f"\n风险评估要点:\n{response['prompts']['risk_assessment'][:200]}...")

async def test_technical_analysis():
    """测试技术分析场景"""
    print("\n" + "="*60)
    print("测试场景3: 技术分析")
    print("="*60)

    service = await get_integrated_patent_service()

    query = "分析这个专利的创新点和技术效果"
    patent_text = """
    本发明公开了一种高效的能量存储装置，包括：
    - 新型正极材料，比容量提升50%；
    - 优化的电解液配方，循环寿命提升3倍；
    - 改进的封装工艺，安全性显著提高。
    """

    response = await service.process_patent_query(
        query=query,
        patent_text=patent_text,
        context_type="technical_analysis"
    )

    print(f"\n查询ID: {response['query_id']}")
    print(f"识别意图: {response['intent']}")
    print(f"\n技术分析框架:\n{response['prompts']['analysis_dimensions']}")

async def test_batch_processing():
    """测试批量处理"""
    print("\n" + "="*60)
    print("测试场景4: 批量处理")
    print("="*60)

    service = await get_integrated_patent_service()

    queries = [
        {
            "query": "什么是专利的三性？",
            "user_id": "user001"
        },
        {
            "query": "如何撰写权利要求？",
            "user_id": "user002",
            "context": {"patent_type": "发明"}
        },
        {
            "query": "PCT申请的流程是什么？",
            "user_id": "user003",
            "context": {"application_type": "PCT"}
        }
    ]

    results = await service.batch_process_queries(queries)

    print(f"\n批量处理完成，处理了 {len(results)} 个查询")
    for result in results:
        print(f"  - 查询ID: {result['query_id'][:8]}..., 意图: {result['intent']}")

async def test_knowledge_insights():
    """测试知识洞察"""
    print("\n" + "="*60)
    print("测试场景5: 知识洞察")
    print("="*60)

    service = await get_integrated_patent_service()

    insights = await service.export_knowledge_insights()
    stats = await service.get_service_statistics()

    print("\n知识图谱统计:")
    kg_summary = insights['knowledge_graph_summary']
    print(f"  SQLite实体数: {kg_summary['sqlite_entities']:,}")
    print(f"  SQLite关系数: {kg_summary['sqlite_relations']:,}")
    print(f"  法律实体数: {kg_summary['legal_entities']}")
    print(f"  审查指南向量: {kg_summary['guideline_vectors']}")

    print("\n服务统计:")
    print(f"  总查询数: {stats['statistics']['total_queries']}")
    print(f"  提示词生成数: {stats['statistics']['prompt_generated']}")
    print(f"  知识库命中数: {stats['statistics']['knowledge_hits']}")

async def main():
    """主测试函数"""
    print("🚀 开始测试统一知识图谱服务")

    # 运行各种测试
    await test_patent_review()
    await test_legal_advice()
    await test_technical_analysis()
    await test_batch_processing()
    await test_knowledge_insights()

    print("\n" + "="*60)
    print("✅ 所有测试完成！")
    print("="*60)

    # 输出使用建议
    print("\n💡 使用建议:")
    print("1. 在专利审查系统中集成此服务，提供智能审查辅助")
    print("2. 在法律咨询系统中使用，提供专业法律建议")
    print("3. 在专利分析平台中应用，辅助技术评估")
    print("4. 可作为任何专利应用的智能后端服务")

if __name__ == "__main__":
    asyncio.run(main())