#!/usr/bin/env python3
"""
测试Google Patents检索功能
"""
import asyncio
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from google_patents_retriever_v2 import GooglePatentsRetrieverV2


async def test_google_patents():
    """测试Google Patents检索"""
    print("\n" + "=" * 80)
    print("🔍 Google Patents检索功能测试")
    print("=" * 80)

    retriever = GooglePatentsRetrieverV2(headless=True)

    test_queries = [
        "deep learning neural network",
        "autonomous vehicle",
        "blockchain technology"
    ]

    for i, query in enumerate(test_queries, 1):
        print(f"\n{'='*80}")
        print(f"测试 {i}: '{query}'")
        print('='*80)

        try:
            results = await retriever.search(query, max_results=3)

            if results:
                print(f"\n✅ 找到 {len(results)} 条结果:\n")

                for j, result in enumerate(results, 1):
                    print(f"{j}. [{result.patent_id}] {result.title}")
                    print(f"   申请人: {result.assignee}")
                    print(f"   公开日: {result.publication_date}")
                    print(f"   相关度: {result.relevance_score:.2f}")

                    if result.inventors:
                        print(f"   发明人: {', '.join(result.inventors[:3])}")

                    if result.abstract:
                        abstract_preview = result.abstract[:120] + "..." if len(result.abstract) > 120 else result.abstract
                        print(f"   摘要: {abstract_preview}")

                    print(f"   URL: {result.url}")
                    print()
            else:
                print("❌ 未找到结果（可能原因：网络连接问题、Playwright未安装、或Google Patents服务不可用）")

        except Exception as e:
            print(f"❌ 检索异常: {e}")
            import traceback
            traceback.print_exc()

        # 礼貌延迟
        if i < len(test_queries):
            print("⏳ 等待3秒后进行下一个查询...")
            await asyncio.sleep(3)

    await retriever.close()

    print("\n" + "=" * 80)
    print("✅ 测试完成")
    print("=" * 80)
    print("\n💡 提示：")
    print("  - 如果所有测试都返回0条结果，可能需要安装Playwright:")
    print("    pip install playwright")
    print("    playwright install chromium")
    print("  - 或者检查网络连接是否正常")
    print("  - Google Patents可能需要代理访问")
    print()


if __name__ == "__main__":
    result = asyncio.run(test_google_patents())
    sys.exit(0 if result else 1)
