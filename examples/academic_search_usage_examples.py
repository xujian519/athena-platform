#!/usr/bin/env python3
"""
学术搜索工具使用示例
Academic Search Tool Usage Examples

展示如何在Athena平台中使用学术搜索工具

作者: Athena平台团队
版本: v1.0.0
创建: 2026-04-19
"""

import asyncio
import json
from pathlib import Path

from core.tools.handlers.academic_search_handler import academic_search_handler, search_papers


async def example_1_basic_search():
    """示例1: 基本搜索"""
    print("=" * 60)
    print("示例1: 基本学术论文搜索")
    print("=" * 60)

    result = await academic_search_handler(
        query="artificial intelligence patent law",
        limit=5
    )

    if result["success"]:
        print(f"✅ 找到 {result['total_results']} 篇论文")
        print(f"数据源: {result['source']}")
        print()

        for paper in result["results"]:
            print(f"{paper['index']}. {paper['title']}")
            print(f"   作者: {', '.join(paper['authors'])}")
            print(f"   年份: {paper['year'] or 'N/A'}")
            print(f"   引用数: {paper['citations']}")
            print(f"   链接: {paper['url']}")
            print()
    else:
        print(f"❌ 搜索失败: {result['error']}")


async def example_2_search_with_filters():
    """示例2: 带过滤条件的搜索"""
    print("=" * 60)
    print("示例2: 带年份过滤的搜索")
    print("=" * 60)

    result = await academic_search_handler(
        query="machine learning",
        source="semantic_scholar",
        limit=10,
        year="2024"
    )

    if result["success"]:
        print(f"✅ 找到 {result['total_results']} 篇2024年的论文")
        print()

        for paper in result["results"][:3]:
            print(f"• {paper['title']} ({paper['year']})")
            print(f"  {paper['venue']}")
            print()


async def example_3_convenience_function():
    """示例3: 使用便捷函数"""
    print("=" * 60)
    print("示例3: 使用便捷函数 search_papers()")
    print("=" * 60)

    result = await search_papers(
        query="quantum computing patents",
        limit=5
    )

    if result["success"]:
        print(f"✅ 搜索成功: {result['total_results']} 篇论文")
        print()

        # 显示前3篇
        for paper in result["results"][:3]:
            print(f"📄 {paper['title']}")
            if paper["abstract"]:
                print(f"   摘要: {paper['abstract'][:200]}...")
            print()


async def example_4_save_results():
    """示例4: 保存搜索结果到文件"""
    print("=" * 60)
    print("示例4: 保存搜索结果到JSON文件")
    print("=" * 60)

    result = await academic_search_handler(
        query="blockchain intellectual property",
        limit=10
    )

    if result["success"]:
        # 保存到文件
        output_file = Path("/tmp/academic_search_results.json")
        output_file.write_text(
            json.dumps(result, indent=2, ensure_ascii=False),
            encoding='utf-8'
        )

        print(f"✅ 结果已保存到: {output_file}")
        print(f"   共 {result['total_results']} 篇论文")


async def example_5_patent_prior_art_search():
    """示例5: 专利现有技术检索（实际应用场景）"""
    print("=" * 60)
    print("示例5: 专利现有技术检索")
    print("=" * 60)

    # 模拟一个专利技术交底书的关键词
    patent_keywords = [
        "deep learning image recognition",
        "convolutional neural networks",
        "computer vision patents"
    ]

    all_papers = []

    for keyword in patent_keywords:
        print(f"🔍 搜索: {keyword}")
        result = await academic_search_handler(
            query=keyword,
            limit=5,
            year="2023"
        )

        if result["success"]:
            all_papers.extend(result["results"])
            print(f"   找到 {len(result['results'])} 篇相关论文")

    # 去重（基于标题）
    seen_titles = set()
    unique_papers = []
    for paper in all_papers:
        title_lower = paper["title"].lower()
        if title_lower not in seen_titles:
            seen_titles.add(title_lower)
            unique_papers.append(paper)

    print()
    print(f"✅ 共找到 {len(unique_papers)} 篇不重复的相关论文")
    print()

    # 显示最相关的5篇
    print("📚 最相关的5篇论文:")
    for i, paper in enumerate(unique_papers[:5], 1):
        print(f"{i}. {paper['title']}")
        print(f"   引用数: {paper['citations']}")
        print()


async def example_6_multi_source_search():
    """示例6: 多数据源搜索（需要配置API密钥）"""
    print("=" * 60)
    print("示例6: 多数据源搜索（需要SERPER_API_KEY）")
    print("=" * 60)

    # 尝试使用双数据源
    result = await academic_search_handler(
        query="patent analytics",
        source="both",
        limit=10
    )

    if result["success"]:
        print("✅ 搜索成功")
        print(f"   数据源: {result['source']}")

        if "breakdown" in result:
            print(f"   Semantic Scholar: {result['breakdown']['semantic_scholar']} 篇")
            print(f"   Google Scholar: {result['breakdown']['google_scholar']} 篇")

        print(f"   合并后总数: {result['total_results']} 篇")
        print()
    else:
        print("⚠️ 双数据源搜索失败（可能未配置API密钥）")
        print(f"   错误: {result.get('error', 'Unknown')}")


async def main():
    """运行所有示例"""
    print("\n")
    print("🎓 Athena平台 - 学术搜索工具使用示例")
    print("=" * 60)
    print("\n")

    # 运行示例
    await example_1_basic_search()
    await asyncio.sleep(1)

    await example_2_search_with_filters()
    await asyncio.sleep(1)

    await example_3_convenience_function()
    await asyncio.sleep(1)

    await example_4_save_results()
    await asyncio.sleep(1)

    await example_5_patent_prior_art_search()
    await asyncio.sleep(1)

    await example_6_multi_source_search()

    print("\n")
    print("=" * 60)
    print("✅ 所有示例运行完成")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
