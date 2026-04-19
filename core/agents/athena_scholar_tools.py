#!/usr/bin/env python3
from __future__ import annotations
"""
小娜 Google Scholar 集成工具
Athena Google Scholar Integration Tools

为小娜智能体提供学术搜索能力

作者: 小诺·双鱼公主 (Xiaonuo Pisces Princess)
版本: v1.0.0
创建: 2025-12-31
"""

import asyncio
import logging
from typing import Any

logger = logging.getLogger(__name__)

# ==========================================
# 工具1: 学术论文搜索
# ==========================================


async def scholar_paper_search(
    query: str,
    max_results: int = 10,
    year_from: int | None = None,
    year_to: int | None = None,
) -> dict[str, Any]:
    """
    搜索学术论文

    Args:
        query: 搜索关键词
        max_results: 最大结果数
        year_from: 起始年份
        year_to: 结束年份

    Returns:
        搜索结果
    """
    try:
        from core.search.standards.base_search_tool import SearchQuery
        from core.search.tools.google_scholar_tool import create_scholar_search

        # 构建查询
        search_query = query
        if year_from:
            search_query += f" after:{year_from}"
        if year_to:
            search_query += f" before:{year_to}"

        logger.info(f"📚 小娜执行学术搜索: {search_query}")

        # 创建搜索工具
        tool = await create_scholar_search()

        # 执行搜索
        search_query_obj = SearchQuery(text=search_query, max_results=max_results)

        response = await tool.search(search_query_obj)

        # 格式化结果
        results = []
        for doc in response.documents:
            result = {
                "title": doc.title,
                "authors": doc.metadata.get("authors", []),
                "year": doc.metadata.get("year"),
                "publication": doc.metadata.get("publication"),
                "citation": doc.metadata.get("citation"),
                "url": doc.url,
                "snippet": doc.snippet,
            }
            results.append(result)

        return {
            "success": True,
            "query": query,
            "total_found": response.total_found,
            "results": results,
            "search_time": response.search_time,
        }

    except Exception as e:
        logger.error(f"❌ 学术搜索失败: {e}")
        return {"success": False, "error": str(e), "query": query}


# ==========================================
# 工具2: 现有技术检索
# ==========================================


async def prior_art_search(
    patent_claims: str, technology_field: str, max_results: int = 20
) -> dict[str, Any]:
    """
    专利现有技术检索

    Args:
        patent_claims: 专利权利要求
        technology_field: 技术领域
        max_results: 最大结果数

    Returns:
        现有技术检索结果
    """
    try:
        logger.info(f"🔍 小娜执行现有技术检索: {technology_field}")

        # 提取关键技术词
        keywords = await _extract_keywords(patent_claims)

        # 构建学术搜索查询
        academic_query = f"{technology_field} {' '.join(keywords[:5])}"

        # 执行搜索
        results = await scholar_paper_search(query=academic_query, max_results=max_results)

        if not results.get("success"):
            return results

        # 分析与权利要求的对比
        analysis = await _analyze_claim_relevance(patent_claims, results.get("results", []))

        return {
            "success": True,
            "patent_claims": patent_claims[:200] + "...",
            "technology_field": technology_field,
            "academic_literature": results,
            "claim_analysis": analysis,
            "summary": f"找到 {results.get('total_found', 0)} 篇相关学术论文",
        }

    except Exception as e:
        logger.error(f"❌ 现有技术检索失败: {e}")
        return {"success": False, "error": str(e)}


# ==========================================
# 工具3: 技术趋势分析
# ==========================================


async def technology_trend_analysis(technology: str, years: int = 5) -> dict[str, Any]:
    """
    技术趋势分析

    Args:
        technology: 技术名称
        years: 分析年数

    Returns:
        技术趋势分析结果
    """
    try:
        from datetime import datetime

        logger.info(f"📈 小娜执行技术趋势分析: {technology}")

        current_year = datetime.now().year

        # 按年份搜索
        yearly_results = {}
        for year in range(current_year - years, current_year + 1):
            results = await scholar_paper_search(
                query=technology, year_from=year, year_to=year, max_results=100
            )
            yearly_results[year] = results.get("total_found", 0)

        # 趋势分析
        trend = _calculate_trend(yearly_results)
        growth_rate = _calculate_growth_rate(yearly_results)

        return {
            "success": True,
            "technology": technology,
            "years_analyzed": years,
            "yearly_counts": yearly_results,
            "trend": trend,
            "growth_rate": f"{growth_rate:.2f}%",
            "summary": f"过去{years}年{technology}领域呈现{trend}趋势",
        }

    except Exception as e:
        logger.error(f"❌ 技术趋势分析失败: {e}")
        return {"success": False, "error": str(e)}


# ==========================================
# 工具4: 作者论文检索
# ==========================================


async def author_publication_search(author_name: str, max_results: int = 20) -> dict[str, Any]:
    """
    检索特定作者的论文

    Args:
        author_name: 作者姓名
        max_results: 最大结果数

    Returns:
        作者论文列表
    """
    try:
        logger.info(f"👤 小娜执行作者论文检索: {author_name}")

        # 构建作者搜索查询
        query = f"author:{author_name}"

        results = await scholar_paper_search(query=query, max_results=max_results)

        return {
            "success": True,
            "author": author_name,
            "total_publications": results.get("total_found", 0),
            "publications": results.get("results", []),
        }

    except Exception as e:
        logger.error(f"❌ 作者论文检索失败: {e}")
        return {"success": False, "error": str(e)}


# ==========================================
# 工具5: 引用文献发现
# ==========================================


async def related_papers_search(paper_title: str, max_results: int = 10) -> dict[str, Any]:
    """
    发现相关论文(引用、被引用、相关)

    Args:
        paper_title: 论文标题
        max_results: 最大结果数

    Returns:
        相关论文列表
    """
    try:
        logger.info(f"🔗 小娜执行相关论文发现: {paper_title}")

        # 构建相关论文搜索
        query = f"related:{paper_title}"

        results = await scholar_paper_search(query=query, max_results=max_results)

        return {
            "success": True,
            "source_paper": paper_title,
            "related_papers": results.get("results", []),
            "total_found": results.get("total_found", 0),
        }

    except Exception as e:
        logger.error(f"❌ 相关论文发现失败: {e}")
        return {"success": False, "error": str(e)}


# === 辅助函数 ===


async def _extract_keywords(text: str) -> list[str]:
    """提取关键词"""
    # 简化实现,提取长度>4的单词
    words = text.lower().split()
    stopwords = {
        "a",
        "an",
        "the",
        "and",
        "or",
        "but",
        "in",
        "on",
        "at",
        "to",
        "for",
        "of",
        "with",
        "by",
        "from",
        "as",
        "is",
        "was",
        "are",
        "been",
        "be",
        "have",
        "has",
        "had",
        "do",
        "does",
        "did",
        "will",
        "would",
        "could",
        "should",
        "may",
        "might",
        "can",
    }

    keywords = [w for w in words if len(w) > 4 and w not in stopwords and w.isalpha()]

    # 返回前10个关键词
    return list(set(keywords))[:10]


async def _analyze_claim_relevance(claims: str, papers: list[dict]) -> dict[str, Any]:
    """
    分析论文与权利要求的相关性

    简化实现:基于关键词匹配
    """
    claim_words = set(claims.lower().split())

    highly_relevant = []
    moderately_relevant = []
    background = []

    for paper in papers:
        title = paper.get("title", "").lower()
        snippet = paper.get("snippet", "").lower()
        paper_text = f"{title} {snippet}"
        paper_words = set(paper_text.split())

        # 计算交集
        intersection = claim_words & paper_words
        overlap_rate = len(intersection) / len(claim_words) if claim_words else 0

        if overlap_rate > 0.3:
            highly_relevant.append(paper)
        elif overlap_rate > 0.1:
            moderately_relevant.append(paper)
        else:
            background.append(paper)

    return {
        "highly_relevant": len(highly_relevant),
        "moderately_relevant": len(moderately_relevant),
        "background": len(background),
        "total": len(papers),
    }


def _calculate_trend(yearly_data: dict[int, int]) -> str:
    """计算趋势"""
    values = list(yearly_data.values())
    if len(values) < 2:
        return "未知"

    first_avg = (
        sum(values[: len(values) // 2]) / (len(values) // 2) if len(values) > 1 else values[0]
    )
    second_avg = sum(values[len(values) // 2 :]) / (len(values) - len(values) // 2)

    if second_avg > first_avg * 1.3:
        return "快速上升"
    elif second_avg > first_avg * 1.1:
        return "稳步上升"
    elif second_avg < first_avg * 0.7:
        return "下降"
    else:
        return "平稳"


def _calculate_growth_rate(yearly_data: dict[int, int]) -> float:
    """计算增长率"""
    values = list(yearly_data.values())
    if len(values) < 2:
        return 0.0

    first_value = values[0]
    last_value = values[-1]

    if first_value == 0:
        return 100.0 if last_value > 0 else 0.0

    return ((last_value - first_value) / first_value) * 100


# === 工具定义字典 ===

ATHENA_SCHOLAR_TOOLS = {
    "scholar_paper_search": {
        "name": "学术论文搜索",
        "description": "搜索Google Scholar学术数据库,查找相关论文、期刊文章和会议论文",
        "function": scholar_paper_search,
        "parameters": {
            "query": {"type": "string", "description": "搜索关键词"},
            "max_results": {"type": "integer", "description": "最大结果数", "default": 10},
            "year_from": {"type": "integer", "description": "起始年份", "required": False},
            "year_to": {"type": "integer", "description": "结束年份", "required": False},
        },
        "examples": [
            {"query": "deep learning", "max_results": 10},
            {"query": "quantum computing", "max_results": 20, "year_from": 2020},
        ],
    },
    "prior_art_search": {
        "name": "现有技术检索",
        "description": "基于专利权利要求检索非专利现有技术(学术论文)",
        "function": prior_art_search,
        "parameters": {
            "patent_claims": {"type": "string", "description": "专利权利要求内容"},
            "technology_field": {"type": "string", "description": "技术领域"},
            "max_results": {"type": "integer", "description": "最大结果数", "default": 20},
        },
    },
    "technology_trend_analysis": {
        "name": "技术趋势分析",
        "description": "分析特定技术领域的学术研究趋势",
        "function": technology_trend_analysis,
        "parameters": {
            "technology": {"type": "string", "description": "技术名称"},
            "years": {"type": "integer", "description": "分析年数", "default": 5},
        },
    },
    "author_publication_search": {
        "name": "作者论文检索",
        "description": "检索特定作者的学术论文",
        "function": author_publication_search,
        "parameters": {
            "author_name": {"type": "string", "description": "作者姓名"},
            "max_results": {"type": "integer", "description": "最大结果数", "default": 20},
        },
    },
    "related_papers_search": {
        "name": "相关论文发现",
        "description": "发现与给定论文相关的其他论文(引用、被引用)",
        "function": related_papers_search,
        "parameters": {
            "paper_title": {"type": "string", "description": "论文标题"},
            "max_results": {"type": "integer", "description": "最大结果数", "default": 10},
        },
    },
}

if __name__ == "__main__":
    # 测试代码
    async def test_athena_scholar_tools():
        """测试小娜学术工具"""
        print("🧪 测试小娜学术搜索工具")
        print()

        # 测试1: 学术论文搜索
        print("=" * 60)
        print("测试 1: 学术论文搜索")
        print("=" * 60)

        result = await scholar_paper_search(query="artificial intelligence", max_results=5)

        print(f"成功: {result.get('success')}")
        print(f"查询: {result.get('query')}")
        print(f"找到: {result.get('total_found')} 篇论文")

        if result.get("results"):
            print("\n前3篇论文:")
            for i, paper in enumerate(result["results"][:3], 1):
                print(f"\n{i}. {paper['title']}")
                print(f"   作者: {', '.join(paper['authors'][:3])}")
                print(f"   年份: {paper.get('year', 'N/A')}")

        # 测试2: 技术趋势分析
        print("\n" + "=" * 60)
        print("测试 2: 技术趋势分析")
        print("=" * 60)

        trend = await technology_trend_analysis(technology="machine learning", years=3)

        print(f"技术: {trend.get('technology')}")
        print(f"趋势: {trend.get('trend')}")
        print(f"增长率: {trend.get('growth_rate')}")
        print(f"年度统计: {trend.get('yearly_counts')}")

    asyncio.run(test_athena_scholar_tools())
