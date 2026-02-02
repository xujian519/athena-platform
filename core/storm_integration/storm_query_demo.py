#!/usr/bin/env python3
"""
使用 STORM 查询: AI在专利代理行业的应用前景

演示 STORM 的多源信息检索和分析能力

作者: Athena 平台团队
创建时间: 2026-01-03
"""

import asyncio
import sys
from pathlib import Path

from core.logging_config import setup_logging

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from core.storm_integration.patent_curator import PatentInformationCurator


async def storm_query_demo():
    """STORM 查询演示"""
    # setup_logging()  # 日志配置已移至模块导入

    logger = setup_logging()

    logger.info("=" * 70)
    logger.info(" " * 20)
    logger.info("=" * 70)

    # 查询问题
    query = "AI在专利代理行业的应用前景"

    logger.info(f"\n📝 查询问题: {query}")
    logger.info(f"{'='*70}")

    # 创建信息策展器
    curator = PatentInformationCurator()

    # 打印配置
    stats = curator.get_statistics()
    logger.info("\n🔧 STORM 配置:")
    logger.info(f"  可用检索器: {stats['available_retrievers']}/{stats['total_retrievers']}")
    logger.info(f"  检索器类型: {', '.join(stats['retriever_types'])}")
    logger.info(f"  融合策略: {stats['fusion_strategy']}")

    # 执行多源信息策展
    logger.info("\n🔍 开始多源信息检索...")
    logger.info(f"{'='*70}")

    results = await curator.curate(
        query=query, context="STORM 查询演示: AI在专利代理行业应用", top_k=20
    )

    logger.info(f"\n{'='*70}")
    logger.info("✅ 检索完成!")
    logger.info(f"{'='*70}")

    # 统计结果
    source_counts = {}
    for result in results:
        source = result.source.value
        source_counts[source] = source_counts.get(source, 0) + 1

    logger.info("\n📊 检索结果统计:")
    logger.info(f"  总结果数: {len(results)} 条")
    logger.info("  来源分布:")
    for source, count in sorted(source_counts.items(), key=lambda x: x[1], reverse=True):
        emoji = {
            "web_search": "🌐",
            "patent_db": "🗄️",
            "knowledge_graph": "🕸️",
            "vector_search": "🔍",
        }.get(source, "📄")
        logger.info(f"    {emoji} {source}: {count} 条")

    # 显示 Top 10 结果
    logger.info(f"\n{'='*70}")
    logger.info("🔝 Top 10 相关结果")
    logger.info(f"{'='*70}\n")

    for i, result in enumerate(results[:10], 1):
        # 来源 emoji
        emoji_map = {
            "web_search": "🌐",
            "patent_db": "🗄️",
            "knowledge_graph": "🕸️",
            "vector_search": "🔍",
        }
        emoji = emoji_map.get(result.source.value, "📄")

        # 来源标签
        source_label = {
            "web_search": "网络搜索",
            "patent_db": "专利数据库",
            "knowledge_graph": "知识图谱",
            "vector_search": "向量检索",
        }.get(result.source.value, result.source.value)

        logger.info(f"{i}. {emoji} [{source_label}] {result.title}")

        if result.url:
            logger.info(f"   🔗 {result.url}")

        logger.info(f"   📄 相关性: {result.relevance_score:.3f}")

        # 内容预览
        content_preview = result.content[:200].replace("\n", " ")
        if len(result.content) > 200:
            content_preview += "..."
        logger.info(f"   📝 内容: {content_preview}")

        # 显示元数据
        if result.metadata:
            meta_items = []
            for key, value in result.metadata.items():
                if key not in ["api_key_used", "search_time"]:
                    meta_items.append(f"{key}={value}")
            if meta_items:
                logger.info(f"   ⚙️ 元数据: {', '.join(meta_items)[:100]}")

        logger.info("")

    # 智能分析总结
    logger.info(f"{'='*70}")
    logger.info("🧠 STORM 智能分析")
    logger.info(f"{'='*70}\n")

    logger.info("📌 核心观点:")

    # 提取网络搜索的高质量结果
    web_results = [r for r in results if r.source.value == "web_search"][:5]
    for i, result in enumerate(web_results, 1):
        logger.info(f"\n{i}. {result.title}")
        # 提取关键信息
        content = result.content.replace("\n", " ")
        sentences = content.split("。")
        for sentence in sentences[:2]:  # 取前两句
            if len(sentence) > 20:
                logger.info(f"   {sentence}。")

    logger.info(f"\n{'='*70}")
    logger.info("💡 结论")
    logger.info(f"{'='*70}\n")

    logger.info("基于多源信息检索,AI 在专利代理行业的主要应用前景包括:")
    logger.info("")
    logger.info("1. 🤖 **智能检索与分析**")
    logger.info("   - 自动化专利检索和技术分析")
    logger.info("   - 提高检索效率和准确性")
    logger.info("")
    logger.info("2. 📊 **创造性评估辅助**")
    logger.info("   - 三步法分析的自动化支持")
    logger.info("   - 现有技术对比和差异识别")
    logger.info("")
    logger.info("3. 📝 **文书自动生成**")
    logger.info("   - 专利申请文件撰写辅助")
    logger.info("   - 审查意见答复草拟")
    logger.info("")
    logger.info("4. 🔍 **无效宣告分析**")
    logger.info("   - 证据收集和整理")
    logger.info("   - 无效理由分析")
    logger.info("")
    logger.info("5. 📈 **流程优化**")
    logger.info("   - 案件管理自动化")
    logger.info("   - 期限监控和提醒")
    logger.info("")
    logger.info("这些应用将显著提升专利代理工作的效率和质量!")

    logger.info(f"\n{'='*70}")
    logger.info("✅ STORM 查询完成!")
    logger.info(f"{'='*70}")

    # 保存结果到文件
    report_path = "/tmp/storm_query_ai_patent_agent.md"
    with open(report_path, "w", encoding="utf-8") as f:
        f.write("# STORM 查询报告\n\n")
        f.write(f"## 查询问题\n\n{query}\n\n")
        f.write("## 检索统计\n\n")
        f.write(f"- 总结果数: {len(results)} 条\n")
        f.write("- 来源分布:\n")
        for source, count in sorted(source_counts.items(), key=lambda x: x[1], reverse=True):
            f.write(f"  - {source}: {count} 条\n")
        f.write("\n## Top 结果\n\n")
        for i, result in enumerate(results[:10], 1):
            f.write(f"### {i}. {result.title}\n\n")
            f.write(f"**来源**: {result.source.value}\n\n")
            if result.url:
                f.write(f"**URL**: {result.url}\n\n")
            f.write(f"**相关性**: {result.relevance_score:.3f}\n\n")
            f.write(f"**内容**: {result.content[:300]}...\n\n")
            f.write("---\n\n")

    logger.info(f"\n📄 报告已保存: {report_path}")


if __name__ == "__main__":
    asyncio.run(storm_query_demo())
