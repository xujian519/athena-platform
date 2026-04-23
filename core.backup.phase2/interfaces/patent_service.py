"""
专利检索服务接口

定义了专利检索和详情获取的抽象接口。
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime


@dataclass
class PatentDetail:
    """专利详情"""
    patent_id: str
    title: str
    abstract: str
    claims: List[str]
    description: str
    applicants: List[str]
    inventors: List[str]
    filing_date: Optional[datetime] = None
    publication_date: Optional[datetime] = None
    status: Optional[str] = None
    metadata: Dict[str, Any] = None


@dataclass
class PatentSearchResult:
    """专利搜索结果"""
    patent_id: str
    title: str
    abstract: str
    relevance_score: float
    metadata: Dict[str, Any] = None


class PatentRetrievalService(ABC):
    """
    专利检索服务接口

    用于搜索和获取专利信息。
    """

    @abstractmethod
    async def search_patents(
        self,
        query: str,
        filters: Optional[Dict[str, Any]] = None,
        limit: int = 10,
        offset: int = 0
    ) -> List[PatentSearchResult]:
        """
        搜索专利

        Args:
            query: 搜索查询
            filters: 过滤条件（如日期范围、申请人等）
            limit: 返回结果数量
            offset: 偏移量

        Returns:
            搜索结果列表
        """
        pass

    @abstractmethod
    async def get_patent_detail(
        self,
        patent_id: str,
        include_full_text: bool = False
    ) -> Optional[PatentDetail]:
        """
        获取专利详情

        Args:
            patent_id: 专利ID
            include_full_text: 是否包含全文

        Returns:
            专利详情，如果不存在返回None
        """
        pass

    @abstractmethod
    async def batch_get_patent_details(
        self,
        patent_ids: List[str],
        include_full_text: bool = False
    ) -> List[Optional[PatentDetail]]:
        """
        批量获取专利详情

        Args:
            patent_ids: 专利ID列表
            include_full_text: 是否包含全文

        Returns:
            专利详情列表（不存在的专利对应位置为None）
        """
        pass

    @abstractmethod
    async def health_check(self) -> bool:
        """
        健康检查

        Returns:
            是否健康
        """
        pass
