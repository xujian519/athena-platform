#!/usr/bin/env python3
"""
学术搜索Handler
Academic Search Handler

提供统一的学术论文和文献搜索接口，支持多数据源：
- Google Scholar (通过Serper API)
- Semantic Scholar API
- 未来可扩展更多数据源

作者: Athena平台团队
版本: v1.0.0
创建: 2026-04-19
"""

import asyncio
import logging
from datetime import datetime
from typing import Any, Dict

import aiohttp

from core.tools.decorators import tool

logger = logging.getLogger(__name__)


@tool(
    name="academic_search",
    category="academic_search",
    description="学术论文和文献搜索（支持Google Scholar和Semantic Scholar）",
    tags=["academic", "search", "research", "papers", "scholar"]
)
async def academic_search_handler(
    query: str,
    source: str = "auto",
    limit: int = 10,
    year: str = "",
    field: str = ""
) -> dict[str, Any]:
    """
    学术论文搜索Handler

    支持多数据源的学术论文搜索，自动降级和结果合并。

    参数:
        query: 搜索关键词
        source: 数据源选择
            - "auto": 自动选择（优先Semantic Scholar）
            - "google_scholar": Google Scholar（需要Serper API密钥）
            - "semantic_scholar": Semantic Scholar API
            - "both": 同时查询两个数据源并合并结果
        limit: 返回结果数量（默认: 10，最大: 100）
        year: 限定年份（如: "2024"）
        field: 研究领域（如: "computer_science", "medicine"）

    返回:
        {
            "success": true,
            "query": "...",
            "source": "semantic_scholar",
            "total_results": 10,
            "results": [
                {
                    "index": 1,
                    "title": "论文标题",
                    "authors": ["作者1", "作者2"],
                    "year": 2024,
                    "venue": "期刊/会议名称",
                    "url": "论文链接",
                    "abstract": "摘要",
                    "citations": 100,
                    "paper_id": "Semantic Scholar ID"
                },
                ...
            ],
            "timestamp": "2026-04-19T22:45:00Z"
        }

    错误返回:
        {
            "success": false,
            "error": "错误信息",
            "query": "...",
            "timestamp": "..."
        }
    """
    try:
        # 参数验证
        if not query or not query.strip():
            return {
                "success": False,
                "error": "缺少必需参数: query",
                "query": query,
                "timestamp": datetime.now().isoformat()
            }

        query = query.strip()
        limit = min(max(1, limit), 100)  # 限制在1-100之间

        logger.info(f"🔍 学术搜索: query='{query}', source={source}, limit={limit}")

        # 根据source选择搜索方式
        if source == "google_scholar":
            # 仅使用Google Scholar
            result = await _search_google_scholar(query, limit, year, field)
        elif source == "semantic_scholar":
            # 仅使用Semantic Scholar
            result = await _search_semantic_scholar(query, limit, year, field)
        elif source == "both":
            # 同时查询两个数据源并合并
            result = await _search_both_sources(query, limit, year, field)
        else:
            # 自动选择（默认Semantic Scholar）
            result = await _search_semantic_scholar(query, limit, year, field)

            # 如果Semantic Scholar失败，尝试Google Scholar
            if not result["success"]:
                logger.warning("⚠️ Semantic Scholar搜索失败，尝试Google Scholar")
                result = await _search_google_scholar(query, limit, year, field)

        return result

    except Exception as e:
        logger.error(f"❌ 学术搜索失败: {e}", exc_info=True)
        return {
            "success": False,
            "error": str(e),
            "query": query,
            "timestamp": datetime.now().isoformat()
        }


async def _search_semantic_scholar(
    query: str,
    limit: int,
    year: str = "",
    field: str = ""
) -> dict[str, Any]:
    """
    使用Semantic Scholar API搜索论文

    优点:
    - 无需API密钥（免费层）
    - 返回结构化数据
    - 包含引用信息

    限制:
    - 免费层: 5000次/5分钟
    """
    try:
        api_url = "https://api.semanticscholar.org/graph/v1/paper/search"
        params = {
            "query": query,
            "limit": limit,
            "fields": "title,authors,year,venue,url,abstract,citationCount,paperId"
        }

        if year:
            params["year"] = year

        if field:
            params["fieldsOfStudy"] = field

        async with aiohttp.ClientSession() as session:
            async with session.get(
                api_url,
                params=params,
                timeout=aiohttp.ClientTimeout(total=30)
            ) as response:
                if response.status != 200:
                    error_text = await response.text()
                    return {
                        "success": False,
                        "error": f"Semantic Scholar API错误: {response.status} - {error_text}",
                        "query": query,
                        "timestamp": datetime.now().isoformat()
                    }

                data = await response.json()

                # 转换结果格式
                results = []
                for i, paper in enumerate(data.get("data", []), 1):
                    result = {
                        "index": i,
                        "title": paper.get("title", ""),
                        "authors": [a.get("name", "") for a in paper.get("authors", [])],
                        "year": paper.get("year"),
                        "venue": paper.get("venue", ""),
                        "url": paper.get("url", ""),
                        "abstract": paper.get("abstract", ""),
                        "citations": paper.get("citationCount", 0),
                        "paper_id": paper.get("paperId", "")
                    }
                    results.append(result)

                return {
                    "success": True,
                    "query": query,
                    "source": "semantic_scholar",
                    "total_results": len(results),
                    "results": results,
                    "timestamp": datetime.now().isoformat()
                }

    except Exception as e:
        logger.error(f"❌ Semantic Scholar搜索失败: {e}")
        return {
            "success": False,
            "error": f"Semantic Scholar搜索失败: {str(e)}",
            "query": query,
            "timestamp": datetime.now().isoformat()
        }


async def _search_google_scholar(
    query: str,
    limit: int,
    year: str = "",
    field: str = ""
) -> dict[str, Any]:
    """
    使用Google Scholar搜索论文（通过Serper API）

    优点:
    - 覆盖面广
    - 包含多种语言文献

    限制:
    - 需要Serper API密钥
    - 免费层: 100次/天
    """
    try:
        import os

        api_key = os.getenv("SERPER_API_KEY", "")

        if not api_key:
            return {
                "success": False,
                "error": "未配置SERPER_API_KEY环境变量",
                "hint": "请设置环境变量: export SERPER_API_KEY=your_key_here",
                "query": query,
                "timestamp": datetime.now().isoformat()
            }

        # 使用Serper API进行Google Scholar搜索
        api_url = "https://google.serper.dev/scholar"
        headers = {
            "X-API-KEY": api_key,
            "Content-Type": "application/json"
        }
        payload = {
            "q": query,
            "num": limit
        }

        if year:
            payload["q"] += f" year:{year}"

        async with aiohttp.ClientSession() as session:
            async with session.post(
                api_url,
                headers=headers,
                json=payload,
                timeout=aiohttp.ClientTimeout(total=30)
            ) as response:
                if response.status != 200:
                    error_text = await response.text()
                    return {
                        "success": False,
                        "error": f"Serper API错误: {response.status} - {error_text}",
                        "query": query,
                        "timestamp": datetime.now().isoformat()
                    }

                data = await response.json()

                # 转换结果格式
                results = []
                for i, paper in enumerate(data.get("organic", []), 1):
                    result = {
                        "index": i,
                        "title": paper.get("title", ""),
                        "authors": paper.get("authors", "").split(", "),
                        "year": _extract_year(paper.get("publicationInfo", "")),
                        "venue": paper.get("publicationInfo", ""),
                        "url": paper.get("link", ""),
                        "abstract": paper.get("snippet", ""),
                        "citations": paper.get("citationCount", 0),
                        "paper_id": ""  # Google Scholar没有固定ID
                    }
                    results.append(result)

                return {
                    "success": True,
                    "query": query,
                    "source": "google_scholar",
                    "total_results": len(results),
                    "results": results,
                    "timestamp": datetime.now().isoformat()
                }

    except Exception as e:
        logger.error(f"❌ Google Scholar搜索失败: {e}")
        return {
            "success": False,
            "error": f"Google Scholar搜索失败: {str(e)}",
            "query": query,
            "timestamp": datetime.now().isoformat()
        }


async def _search_both_sources(
    query: str,
    limit: int,
    year: str = "",
    field: str = ""
) -> dict[str, Any]:
    """
    同时查询两个数据源并合并结果

    策略:
    1. 并发查询两个数据源
    2. 合并结果并去重（基于标题相似度）
    3. 按相关性排序
    """
    try:
        # 并发查询
        tasks = [
            _search_semantic_scholar(query, limit, year, field),
            _search_google_scholar(query, limit, year, field)
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        semantic_result = results[0] if not isinstance(results[0], Exception) else {"success": False, "results": []}
        google_result = results[1] if not isinstance(results[1], Exception) else {"success": False, "results": []}

        # 合并结果
        merged_results = []

        # 添加Semantic Scholar结果
        if semantic_result.get("success"):
            merged_results.extend(semantic_result.get("results", []))

        # 添加Google Scholar结果（去重）
        if google_result.get("success"):
            for google_paper in google_result.get("results", []):
                # 检查是否已存在（简单去重：标题相似）
                is_duplicate = False
                for existing_paper in merged_results:
                    if _title_similarity(google_paper["title"], existing_paper["title"]) > 0.85:
                        is_duplicate = True
                        # 合并信息（如Google Scholar有PDF链接）
                        if google_paper.get("url") and not existing_paper.get("url"):
                            existing_paper["url"] = google_paper["url"]
                        break

                if not is_duplicate:
                    merged_results.append(google_paper)

        # 重新编号
        for i, paper in enumerate(merged_results, 1):
            paper["index"] = i

        # 截取指定数量
        merged_results = merged_results[:limit]

        return {
            "success": True,
            "query": query,
            "source": "both",
            "total_results": len(merged_results),
            "results": merged_results,
            "breakdown": {
                "semantic_scholar": len(semantic_result.get("results", [])),
                "google_scholar": len(google_result.get("results", []))
            },
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"❌ 双数据源搜索失败: {e}")
        return {
            "success": False,
            "error": f"双数据源搜索失败: {str(e)}",
            "query": query,
            "timestamp": datetime.now().isoformat()
        }


def _extract_year(publication_info: str) -> int:
    """从出版信息中提取年份"""
    import re

    # 匹配4位数字年份
    match = re.search(r'\b(19|20)\d{2}\b', publication_info)
    if match:
        return int(match.group())
    return None


def _title_similarity(title1: str, title2: str) -> float:
    """计算两个标题的相似度（简单实现）"""
    # 转小写
    t1 = title1.lower()
    t2 = title2.lower()

    # 完全相同
    if t1 == t2:
        return 1.0

    # 简单包含关系
    if t1 in t2 or t2 in t1:
        return 0.9

    # 词级相似度
    words1 = set(t1.split())
    words2 = set(t2.split())

    if not words1 or not words2:
        return 0.0

    intersection = words1 & words2
    union = words1 | words2

    return len(intersection) / len(union)


# 便捷函数
async def search_papers(
    query: str,
    limit: int = 10,
    source: str = "auto"
) -> dict[str, Any]:
    """
    便捷的学术论文搜索函数

    Args:
        query: 搜索关键词
        limit: 返回结果数量
        source: 数据源（auto/google_scholar/semantic_scholar/both）

    Returns:
        搜索结果字典

    Example:
        >>> result = await search_papers("deep learning", limit=5)
        >>> if result["success"]:
        ...     for paper in result["results"]:
        ...         print(f"{paper['title']} ({paper['year']})")
    """
    return await academic_search_handler(
        query=query,
        source=source,
        limit=limit
    )


__all__ = [
    "academic_search_handler",
    "search_papers"
]
