#!/usr/bin/env python3
"""
测试 Athena 搜索引擎与 STORM 的集成

测试外部搜索引擎在 STORM 信息策展器中的工作情况

作者: Athena 平台团队
创建时间: 2026-01-03
"""

from __future__ import annotations
import asyncio
import logging
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from core.storm_integration.patent_curator import (
    PatentInformationCurator,
    RetrievalSource,
)


async def test_web_search_integration():
    """测试 WebSearchRetriever 集成"""
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    logger = logging.getLogger(__name__)

    logger.info("=" * 70)
    logger.info("Athena 搜索引擎与 STORM 集成测试")
    logger.info("=" * 70)

    # 创建信息策展器
    curator = PatentInformationCurator()

    # 打印统计信息
    stats = curator.get_statistics()
    logger.info("\n📊 策展器配置:")
    logger.info(f"  总检索器: {stats['total_retrievers']}")
    logger.info(f"  可用检索器: {stats['available_retrievers']}")
    logger.info(f"  检索器类型: {', '.join(stats['retriever_types'])}")

    # 测试查询
    test_queries = [
        "深度学习在专利检索中的应用",
        "专利创造性判断标准",
        "人工智能专利分析技术",
    ]

    for i, query in enumerate(test_queries, 1):
        logger.info(f"\n{'='*70}")
        logger.info(f"测试查询 {i}/{len(test_queries)}: {query}")
        logger.info(f"{'='*70}")

        # 多源策展(包括 Web Search)
        results = await curator.curate(query=query, context=f"测试查询 {i}", top_k=15)

        logger.info(f"\n✅ 策展完成: 找到 {len(results)} 条结果")

        # 按来源统计
        source_counts = {}
        for result in results:
            source = result.source.value
            source_counts[source] = source_counts.get(source, 0) + 1

        logger.info("\n📊 来源分布:")
        for source, count in source_counts.items():
            logger.info(f"  - {source}: {count} 条")

        # 显示前 5 条结果
        logger.info("\n🔍 Top 5 结果:")
        for j, result in enumerate(results[:5], 1):
            logger.info(f"\n{j}. [{result.source.value}] {result.title}")
            logger.info(f"   URL: {result.url}")
            logger.info(f"   相关性: {result.relevance_score:.3f}")
            logger.info(f"   内容: {result.content[:150]}...")

            # 显示元数据
            if result.metadata:
                meta_str = ", ".join(
                    f"{k}={v}" for k, v in result.metadata.items() if k != "api_key_used"
                )
                if meta_str:
                    logger.info(f"   元数据: {meta_str}")

    # 专门测试 WebSearchRetriever
    logger.info(f"\n{'='*70}")
    logger.info("🌐 专门测试 WebSearchRetriever")
    logger.info(f"{'='*70}")

    web_retriever = None
    for retriever in curator.available_retrievers:
        if retriever.source_type == RetrievalSource.WEB_SEARCH:
            web_retriever = retriever
            break

    if web_retriever:
        logger.info("✅ WebSearchRetriever 可用")
        logger.info(f"   引擎: {web_retriever.engine}")
        logger.info(f"   备用引擎: {'启用' if web_retriever.enable_fallback else '禁用'}")

        # 直接测试 WebSearchRetriever
        test_query = "专利审查指南 最新版本"
        logger.info(f"\n测试查询: {test_query}")

        web_results = await web_retriever.search(query=test_query, context="直接测试", top_k=5)

        logger.info(f"\n找到 {len(web_results)} 条网络搜索结果:")
        for j, result in enumerate(web_results, 1):
            logger.info(f"\n{j}. {result.title}")
            logger.info(f"   URL: {result.url}")
            logger.info(f"   相关性: {result.relevance_score:.3f}")
            logger.info(f"   内容: {result.content[:150]}...")

            if result.metadata.get("engine") == "mock":
                logger.info("   ⚠️ 这是模拟结果,请配置 Athena 搜索引擎 API Key")
    else:
        logger.warning("⚠️ WebSearchRetriever 不可用")

    logger.info(f"\n{'='*70}")
    logger.info("✅ 测试完成!")
    logger.info(f"{'='*70}")


if __name__ == "__main__":
    asyncio.run(test_web_search_integration())
