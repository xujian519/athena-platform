#!/usr/bin/env python3
from __future__ import annotations
"""
服务抽象层
Service Abstraction Layer

提供统一的服务接口,实现解耦和可替换性
"""

import logging
from abc import ABC, abstractmethod
from typing import Any

logger = logging.getLogger(__name__)


# =============================================================================
# 向量存储服务抽象
# =============================================================================


class VectorStoreService(ABC):
    """向量存储服务抽象接口"""

    @abstractmethod
    def search(
        self,
        vector: list[float],
        collection_name: str,
        limit: int = 10,
        score_threshold: float = 0.0,
    ) -> list[dict[str, Any]]:
        """
        向量搜索

        Args:
            vector: 查询向量
            collection_name: 集合名称
            limit: 返回结果数量
            score_threshold: 相似度阈值

        Returns:
            搜索结果列表
        """
        pass

    @abstractmethod
    def insert(self, collection_name: str, points: list[dict[str, Any]]) -> bool:
        """
        插入向量

        Args:
            collection_name: 集合名称
            points: 向量点列表

        Returns:
            是否成功
        """
        pass


# =============================================================================
# 知识图谱服务抽象
# =============================================================================


class KnowledgeGraphService(ABC):
    """知识图谱服务抽象接口"""

    @abstractmethod
    def search_entities(self, query: str, limit: int = 10) -> list[dict[str, Any]]:
        """
        搜索实体

        Args:
            query: 查询字符串
            limit: 返回结果数量

        Returns:
            实体列表
        """
        pass

    @abstractmethod
    def find_path(self, start_entity: str, end_entity: str, max_depth: int = 3) -> list[str]:
        """
        查找实体间路径

        Args:
            start_entity: 起始实体
            end_entity: 结束实体
            max_depth: 最大深度

        Returns:
            路径节点列表
        """
        pass


# =============================================================================
# 文档存储服务抽象
# =============================================================================


class DocumentStoreService(ABC):
    """文档存储服务抽象接口"""

    @abstractmethod
    def search(
        self, query: str, filters: dict[str, Any] | None = None, limit: int = 10
    ) -> list[dict[str, Any]]:
        """
        文档搜索

        Args:
            query: 查询字符串
            filters: 过滤条件
            limit: 返回结果数量

        Returns:
            文档列表
        """
        pass

    @abstractmethod
    def get_document(self, doc_id: str) -> dict[str, Any] | None:
        """
        获取文档

        Args:
            doc_id: 文档ID

        Returns:
            文档内容
        """
        pass


# =============================================================================
# 统一搜索引擎接口
# =============================================================================


class UnifiedSearchEngine(ABC):
    """统一搜索引擎抽象接口"""

    @abstractmethod
    def search(
        self, query: str, filters: dict[str, Any] | None = None, limit: int = 10
    ) -> dict[str, Any]:
        """
        执行混合搜索

        Args:
            query: 查询字符串
            filters: 过滤条件
            limit: 返回结果数量

        Returns:
            搜索结果
        """
        pass

    @abstractmethod
    def get_status(self) -> dict[str, Any]:
        """
        获取搜索引擎状态

        Returns:
            状态信息
        """
        pass


# =============================================================================
# 导出
# =============================================================================

__all__ = [
    "DocumentStoreService",
    "KnowledgeGraphService",
    "UnifiedSearchEngine",
    "VectorStoreService",
]
