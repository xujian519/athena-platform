#!/usr/bin/env python3
from __future__ import annotations
"""
法律世界模型问答系统测试脚本
Legal World Model Q&A System Test Script

版本: 1.0.0
创建时间: 2026-01-23
"""

import asyncio
import logging

from core.legal_qa.legal_world_qa_system import LegalWorldQAEngine

# 配置日志
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


async def test_qa_system():
    """测试问答系统"""
    print("""
╔═══════════════════════════════════════════════════════════╗
║     法律世界模型 - 智能问答系统测试                         ║
╚═══════════════════════════════════════════════════════════╝
    """)

    # 创建问答引擎
    print("🔄 初始化问答引擎...")
    qa_engine = LegalWorldQAEngine(device="auto")

    # 初始化组件
    await qa_engine.initialize()
    print("✅ 问答引擎初始化成功\n")

    # 测试问题集
    test_questions = [
        "什么是专利的创造性?",
        "专利法对新颖性的规定是什么?",
        "查找机械结构类创造性判断案例",
        "专利侵权的判定标准是什么?",
        "如何判断技术方案是否具有创造性?",
    ]

    print(f"📝 开始测试 {len(test_questions)} 个问题...\n")

    # 逐个测试
    for i, question in enumerate(test_questions, 1):
        print("=" * 70)
        print(f"❓ 问题 {i}: {question}")
        print("=" * 70)

        try:
            # 执行查询
            answer = await qa_engine.query(question=question, top_k=3)

            # 显示结果
            print(f"\n🎯 查询意图: {answer.query_intent.question_type.value}")
            print(f"📊 置信度: {answer.confidence:.2f}")
            print("\n💡 答案:")
            print(answer.answer[:500] + "..." if len(answer.answer) > 500 else answer.answer)

            if answer.reasoning_chain:
                print("\n🔗 推理链:")
                for step in answer.reasoning_chain:
                    print(f"  {step.step_number}. {step.description}")

            if answer.references:
                print("\n📚 参考文献:")
                for ref in answer.references[:3]:
                    print(f"  - {ref.source} (相关度: {ref.relevance_score:.2%})")

            if answer.suggestions:
                print("\n💭 建议:")
                for suggestion in answer.suggestions[:2]:
                    print(f"  - {suggestion}")

            print("\n✅ 查询成功\n")

        except Exception as e:
            print(f"\n❌ 查询失败: {e}\n")
            import traceback

            traceback.print_exc()

    # 显示统计信息
    stats = qa_engine.get_statistics()
    print("\n" + "=" * 70)
    print("📊 测试统计")
    print("=" * 70)
    print(f"总查询数: {stats['total_queries']}")
    print(f"成功查询: {stats['successful_queries']}")
    print(f"失败查询: {stats['failed_queries']}")
    print(f"成功率: {stats['success_rate']:.2%}")
    print(f"平均响应时间: {stats['avg_response_time']:.3f}秒")

    if stats["by_question_type"]:
        print("\n按问题类型分布:")
        for qtype, count in sorted(stats["by_question_type"].items()):
            print(f"  {qtype}: {count}")

    if stats["by_layer"]:
        print("\n按层级分布:")
        for layer, count in sorted(stats["by_layer"].items()):
            print(f"  {layer}: {count}")

    print("\n" + "=" * 70)
    print("✅ 测试完成")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(test_qa_system())
