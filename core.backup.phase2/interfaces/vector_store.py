"""
向量存储提供者接口

定义了向量数据库的抽象接口，支持多种向量数据库实现：
- Qdrant
- Neo4j
- Milvus
- Weaviate
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime


@dataclass
class VectorSearchResult:
    """向量搜索结果"""
    id: str
    score: float
    payload: Dict[str, Any]
    vector: Optional[List[float]] = None


class VectorStoreProvider(ABC):
    """
    向量存储提供者接口

    所有向量数据库实现都应继承此接口并实现其方法。
    """

    @abstractmethod
    async def insert_vectors(
        self,
        collection: str,
        vectors: List[List[float]],
        payloads: List[Dict[str, Any]],
        ids: Optional[List[str]] = None
    ) -> bool:
        """
        插入向量到指定集合

        Args:
            collection: 集合名称
            vectors: 向量列表
            payloads: 对应的元数据列表
            ids: 可选的ID列表

        Returns:
            是否成功
        """
        pass

    @abstractmethod
    async def search_vectors(
        self,
        collection: str,
        query_vector: List[float],
        limit: int = 10,
        score_threshold: Optional[float] = None,
        filter_dict: Optional[Dict[str, Any]] = None
    ) -> List[VectorSearchResult]:
        """
        搜索相似向量

        Args:
            collection: 集合名称
            query_vector: 查询向量
            limit: 返回结果数量
            score_threshold: 相似度阈值
            filter_dict: 过滤条件

        Returns:
            搜索结果列表
        """
        pass

    @abstractmethod
    async def delete_collection(self, collection: str) -> bool:
        """
        删除指定集合

        Args:
            collection: 集合名称

        Returns:
            是否成功
        """
        pass

    @abstractmethod
    async def get_collection_info(self, collection: str) -> Dict[str, Any]:
        """
        获取集合信息

        Args:
            collection: 集合名称

        Returns:
            集合信息字典
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
