#!/usr/bin/env python3
"""
直接测试权利要求检索功能
"""
import asyncio
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from enhanced_patent_search import EnhancedPatentRetriever


async def main():
    """测试权利要求检索"""
    print("\n" + "=" * 80)
    print("🔍 专利权利要求（Claims）检索功能测试")
    print("=" * 80)

    retriever = EnhancedPatentRetriever()

    # 测试用例：检索权利要求中的技术特征
    test_cases = [
        {
            "name": "权利要求中的算法名称",
            "query": "A*算法",
            "description": "应能在权利要求中找到A*算法的描述"
        },
        {
            "name": "权利要求中的网络结构",
            "query": "卷积层",
            "description": "应能在权利要求中找到卷积层的描述"
        },
        {
            "name": "权利要求中的功能模块",
            "query": "环境感知单元",
            "description": "应能在权利要求中找到环境感知单元的描述"
        },
        {
            "name": "权利要求中的技术特征",
            "query": "注意力机制",
            "description": "应能在权利要求中找到注意力机制的描述"
        },
        {
            "name": "权利要求中的方法步骤",
            "query": "知识蒸馏",
            "description": "应能在权利要求中找到知识蒸馏的描述"
        },
    ]

    passed = 0
    failed = 0

    for i, test_case in enumerate(test_cases, 1):
        print("\n" + "=" * 80)
        print(f"测试 {i}: {test_case['name']}")
        print(f"查询: '{test_case['query']}'")
        print(f"说明: {test_case['description']}")
        print("=" * 80)

        results = await retriever.search(
            query=test_case['query'],
            top_k=5,
            search_fields=['title', 'abstract', 'claims']
        )

        if results:
            print(f"\n✅ 找到 {len(results)} 条结果:\n")

            # 检查是否有结果匹配了权利要求
            found_in_claims = False

            for j, result in enumerate(results[:3], 1):
                print(f"{j}. [{result.patent_id}] {result.title}")
                print(f"   申请人: {result.applicant}")
                print(f"   匹配字段: {', '.join(result.matched_fields)}")

                # 如果在权利要求中找到匹配
                if 'claims' in result.matched_fields:
                    found_in_claims = True

                    # 显示权利要求匹配片段
                    query_lower = test_case['query'].lower()
                    claims = result.claims.replace('\n', ' ')
                    start = claims.lower().find(query_lower)

                    if start != -1:
                        # 获取上下文
                        context_start = max(0, start - 50)
                        context_end = min(start + 80, len(claims))
                        context = claims[context_start:context_end]

                        print("   ⚖️  权利要求匹配:")
                        print(f"      ...{context}...")

                print()

            if found_in_claims:
                print("✅ 通过：成功在权利要求中找到匹配")
                passed += 1
            else:
                print("⚠️  警告：仅在标题或摘要中找到，未在权利要求中找到")
                failed += 1
        else:
            print("❌ 未找到结果")
            failed += 1

    retriever.close()

    # 总结
    print("\n" + "=" * 80)
    print("📋 测试总结")
    print("=" * 80)
    print(f"  通过: {passed}/{len(test_cases)}")
    print(f"  失败: {failed}/{len(test_cases)}")

    if failed == 0:
        print("\n✅ 所有测试通过！权利要求检索功能完全正常")
        return True
    else:
        print(f"\n⚠️  {failed}/{len(test_cases)} 测试未在权利要求中找到匹配")
        return False


if __name__ == "__main__":
    result = asyncio.run(main())
    sys.exit(0 if result else 1)
