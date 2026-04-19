#!/usr/bin/env python3
"""
统一专利检索工具

整合两个有效的检索渠道：
1. 本地PostgreSQL patent_db数据库
2. Google Patents在线检索

Author: Athena平台团队
Created: 2026-04-19
"""

from enum import Enum
from typing import List, Dict, Any, Optional, Union
import logging
import asyncio

logger = logging.getLogger(__name__)


class PatentRetrievalChannel(Enum):
    """专利检索渠道"""
    LOCAL_POSTGRES = "local_postgres"  # 本地PostgreSQL patent_db
    GOOGLE_PATENTS = "google_patents"  # Google Patents在线检索
    BOTH = "both"  # 同时使用两个渠道


class PatentSearchResult:
    """专利检索结果"""

    def __init__(
        self,
        patent_id: str,
        title: str,
        abstract: str,
        source: str,  # "local_postgres" 或 "google_patents"
        url: Optional[str] = None,
        publication_date: Optional[str] = None,
        applicant: Optional[str] = None,
        inventor: Optional[str] = None,
        score: Optional[float] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        self.patent_id = patent_id
        self.title = title
        self.abstract = abstract
        self.source = source
        self.url = url
        self.publication_date = publication_date
        self.applicant = applicant
        self.inventor = inventor
        self.score = score
        self.metadata = metadata or {}

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "patent_id": self.patent_id,
            "title": self.title,
            "abstract": self.abstract,
            "source": self.source,
            "url": self.url,
            "publication_date": self.publication_date,
            "applicant": self.applicant,
            "inventor": self.inventor,
            "score": self.score,
            "metadata": self.metadata
        }


class UnifiedPatentRetriever:
    """统一专利检索器 - 整合本地和Google两个渠道"""

    def __init__(self):
        self._local_retriever = None
        self._google_retriever = None

    def _get_local_retriever(self):
        """获取本地PostgreSQL检索器（延迟加载）"""
        if self._local_retriever is None:
            try:
                import sys
                from pathlib import Path
                # 添加patent_hybrid_retrieval到Python路径
                project_root = Path(__file__).parent.parent.parent
                patent_retrieval_path = project_root / "patent_hybrid_retrieval"
                sys.path.insert(0, str(patent_retrieval_path))

                from real_patent_hybrid_retrieval import RealPatentHybridRetrieval
                self._local_retriever = RealPatentHybridRetrieval()
                logger.info("✅ 本地PostgreSQL检索器已初始化")
            except Exception as e:
                logger.error(f"❌ 本地PostgreSQL检索器初始化失败: {e}")
                raise
        return self._local_retriever

    def _get_google_retriever(self):
        """获取Google Patents检索器（延迟加载）"""
        if self._google_retriever is None:
            try:
                import sys
                from pathlib import Path
                self._google_retriever = GooglePatentsRetriever()
                logger.info("✅ Google Patents检索器已初始化")
            except Exception as e:
                logger.error(f"❌ Google Patents检索器初始化失败: {e}")
                raise
        return self._google_retriever

    async def search(
        self,
        query: str,
        channel: PatentRetrievalChannel = PatentRetrievalChannel.LOCAL_POSTGRES,
        max_results: int = 10,
        **kwargs
    ) -> List[PatentSearchResult]:
        """
        统一检索接口

        Args:
            query: 检索查询词
            channel: 检索渠道（本地/Google/两者）
            max_results: 最大结果数
            **kwargs: 其他参数

        Returns:
            检索结果列表
        """
        logger.info(f"🔍 开始检索: query='{query}', channel={channel.value}, max_results={max_results}")

        if channel == PatentRetrievalChannel.LOCAL_POSTGRES:
            # 本地PostgreSQL检索
            results = await self._search_local(query, max_results, **kwargs)
        elif channel == PatentRetrievalChannel.GOOGLE_PATENTS:
            # Google Patents检索
            results = await self._search_google(query, max_results, **kwargs)
        elif channel == PatentRetrievalChannel.BOTH:
            # 同时检索两个渠道
            results_dict = await self._search_both(query, max_results, **kwargs)
            # 合并结果
            results = results_dict["local"] + results_dict["google"]
        else:
            raise ValueError(f"不支持的检索渠道: {channel}")

        logger.info(f"✅ 检索完成: 找到 {len(results)} 个结果")
        return results

    async def _search_local(
        self,
        query: str,
        max_results: int,
        **kwargs
    ) -> List[PatentSearchResult]:
        """本地PostgreSQL检索"""
        logger.info(f"  🔍 使用本地PostgreSQL检索...")

        try:
            retriever = self._get_local_retriever()

            # 调用本地检索器
            # 注意：这里需要根据实际的API调整
            raw_results = retriever.search(
                query=query,
                limit=max_results,
                **kwargs
            )

            # 转换为统一格式
            results = []
            for item in raw_results:
                result = PatentSearchResult(
                    patent_id=item.get("patent_id", ""),
                    title=item.get("title", ""),
                    abstract=item.get("abstract", ""),
                    source="local_postgres",
                    url=item.get("url"),
                    publication_date=item.get("publication_date"),
                    applicant=item.get("applicant"),
                    inventor=item.get("inventor"),
                    score=item.get("score"),
                    metadata=item
                )
                results.append(result)

            logger.info(f"  ✅ 本地检索完成: {len(results)} 个结果")
            return results

        except Exception as e:
            logger.error(f"  ❌ 本地检索失败: {e}")
            return []

    async def _search_google(
        self,
        query: str,
        max_results: int,
        **kwargs
    ) -> List[PatentSearchResult]:
        """Google Patents检索"""
        logger.info(f"  🔍 使用Google Patents检索...")

        try:
            retriever = self._get_google_retriever()

            # 调用Google检索器
            # 注意：这里需要根据实际的API调整
            raw_results = await retriever.search(
                query=query,
                max_results=max_results,
                **kwargs
            )

            # 转换为统一格式
            results = []
            for item in raw_results:
                result = PatentSearchResult(
                    patent_id=item.get("patent_id", ""),
                    title=item.get("title", ""),
                    abstract=item.get("abstract", ""),
                    source="google_patents",
                    url=item.get("url"),
                    publication_date=item.get("publication_date"),
                    applicant=item.get("assignee"),
                    inventor=item.get("inventor"),
                    score=item.get("relevance_score"),
                    metadata=item
                )
                results.append(result)

            logger.info(f"  ✅ Google检索完成: {len(results)} 个结果")
            return results

        except Exception as e:
            logger.error(f"  ❌ Google检索失败: {e}")
            return []

    async def _search_both(
        self,
        query: str,
        max_results: int,
        **kwargs
    ) -> Dict[str, List[PatentSearchResult]]:
        """同时使用两个渠道检索"""
        logger.info(f"  🔍 同时使用两个渠道检索...")

        # 并发检索
        local_results_future = self._search_local(query, max_results, **kwargs)
        google_results_future = self._search_google(query, max_results, **kwargs)

        local_results, google_results = await asyncio.gather(
            local_results_future,
            google_results_future,
            return_exceptions=True
        )

        # 处理异常
        if isinstance(local_results, Exception):
            logger.error(f"  ❌ 本地检索异常: {local_results}")
            local_results = []

        if isinstance(google_results, Exception):
            logger.error(f"  ❌ Google检索异常: {google_results}")
            google_results = []

        return {
            "local": local_results,
            "google": google_results
        }


# ============================================================================
# Tool Handler - 用于工具系统注册
# ============================================================================

async def patent_search_handler(params: Dict[str, Any], context: Dict) -> Dict[str, Any]:
    """
    专利检索工具Handler

    参数:
        query: 检索查询词（必需）
        channel: 检索渠道
            - "local_postgres": 本地PostgreSQL
            - "google_patents": Google Patents
            - "both": 同时使用两个渠道（默认）
        max_results: 最大结果数（默认10）

    返回:
        {
            "success": true,
            "query": "...",
            "channel": "...",
            "total_results": 10,
            "results": [...]
        }
    """
    try:
        # 提取参数
        query = params.get("query")
        if not query:
            return {
                "success": False,
                "error": "缺少必需参数: query"
            }

        channel_str = params.get("channel", "both")
        max_results = params.get("max_results", 10)

        # 转换渠道
        channel_map = {
            "local_postgres": PatentRetrievalChannel.LOCAL_POSTGRES,
            "google_patents": PatentRetrievalChannel.GOOGLE_PATENTS,
            "both": PatentRetrievalChannel.BOTH
        }

        channel = channel_map.get(channel_str)
        if not channel:
            return {
                "success": False,
                "error": f"不支持的检索渠道: {channel_str}"
            }

        # 创建检索器并执行检索
        retriever = UnifiedPatentRetriever()
        results = await retriever.search(
            query=query,
            channel=channel,
            max_results=max_results
        )

        # 转换结果为字典格式
        results_dict = [result.to_dict() for result in results]

        # 如果是双渠道，统计各渠道结果数
        channel_stats = {}
        if channel == PatentRetrievalChannel.BOTH:
            local_count = sum(1 for r in results if r.source == "local_postgres")
            google_count = sum(1 for r in results if r.source == "google_patents")
            channel_stats = {
                "local_postgres": local_count,
                "google_patents": google_count
            }

        return {
            "success": True,
            "query": query,
            "channel": channel_str,
            "total_results": len(results_dict),
            "channel_stats": channel_stats,
            "results": results_dict
        }

    except Exception as e:
        logger.error(f"专利检索失败: {e}")
        return {
            "success": False,
            "error": str(e)
        }


# ============================================================================
# 便捷函数
# ============================================================================

async def search_patents(
    query: str,
    channel: str = "local_postgres",
    max_results: int = 10
) -> List[Dict[str, Any]]:
    """
    便捷的专利检索函数

    Args:
        query: 检索查询词
        channel: 检索渠道（"local_postgres" / "google_patents" / "both"）
        max_results: 最大结果数

    Returns:
        检索结果列表（字典格式）
    """
    retriever = UnifiedPatentRetriever()

    channel_map = {
        "local_postgres": PatentRetrievalChannel.LOCAL_POSTGRES,
        "google_patents": PatentRetrievalChannel.GOOGLE_PATENTS,
        "both": PatentRetrievalChannel.BOTH
    }

    results = await retriever.search(
        query=query,
        channel=channel_map[channel],
        max_results=max_results
    )

    return [result.to_dict() for result in results]


async def search_local_patents(
    query: str,
    max_results: int = 10
) -> List[Dict[str, Any]]:
    """便捷的本地检索函数"""
    return await search_patents(query, "local_postgres", max_results)


async def search_google_patents(
    query: str,
    max_results: int = 10
) -> List[Dict[str, Any]]:
    """便捷的Google检索函数"""
    return await search_patents(query, "google_patents", max_results)


# 导出
__all__ = [
    "PatentRetrievalChannel",
    "PatentSearchResult",
    "UnifiedPatentRetriever",
    "patent_search_handler",
    "search_patents",
    "search_local_patents",
    "search_google_patents",
]
