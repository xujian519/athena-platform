"""
知识库服务接口

定义了知识库查询和更新的抽象接口。
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from dataclasses import dataclass


@dataclass
class KnowledgeQueryResult:
    """知识库查询结果"""
    content: str
    source: str
    relevance_score: float
    metadata: Dict[str, Any]


class KnowledgeBaseService(ABC):
    """
    知识库服务接口

    用于查询和更新领域知识库。
    """

    @abstractmethod
    async def query_knowledge(
        self,
        query: str,
        domain: str,
        limit: int = 5,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[KnowledgeQueryResult]:
        """
        查询知识库

        Args:
            query: 查询文本
            domain: 领域（如 legal, patent, medical）
            limit: 返回结果数量
            filters: 过滤条件

        Returns:
            查询结果列表
        """
        pass

    @abstractmethod
    async def update_knowledge(
        self,
        domain: str,
        knowledge_id: str,
        knowledge: Dict[str, Any]
    ) -> bool:
        """
        更新知识库

        Args:
            domain: 领域
            knowledge_id: 知识ID
            knowledge: 知识内容

        Returns:
            是否成功
        """
        pass

    @abstractmethod
    async def delete_knowledge(
        self,
        domain: str,
        knowledge_id: str
    ) -> bool:
        """
        删除知识

        Args:
            domain: 领域
            knowledge_id: 知识ID

        Returns:
            是否成功
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
