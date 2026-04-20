#!/usr/bin/env python3
from __future__ import annotations
"""
Query Engine基类和接口定义
Query Engine Base Classes and Interface Definitions

定义查询引擎的核心基类和接口

作者: Athena平台团队
版本: 1.0.0
"""

from abc import ABC, abstractmethod
from typing import Any

from core.query_engine.types import DataSourceType, QueryPlan, QueryResult, QueryStats


class BaseAdapter(ABC):
    """
    数据源适配器基类

    所有数据源适配器必须继承此类并实现相应方法
    """

    def __init__(self, connection_config: dict[str, Any]):
        """
        初始化适配器

        Args:
            connection_config: 连接配置字典
        """
        self.connection_config = connection_config
        self._connection = None
        self._is_connected = False

    @property
    @abstractmethod
    def data_source_type(self) -> DataSourceType:
        """返回数据源类型"""
        pass

    @abstractmethod
    async def connect(self) -> None:
        """建立连接"""
        pass

    @abstractmethod
    async def disconnect(self) -> None:
        """断开连接"""
        pass

    @abstractmethod
    async def is_connected(self) -> bool:
        """检查连接状态"""
        pass

    @abstractmethod
    async def execute(
        self,
        query: str,
        parameters: dict[str, Any] | None = None,
        **kwargs,
    ) -> QueryResult:
        """
        执行查询

        Args:
            query: 查询语句或命令
            parameters: 查询参数
            **kwargs: 额外参数

        Returns:
            QueryResult: 查询结果
        """
        pass

    @abstractmethod
    async def execute_batch(
        self,
        queries: list[str],
        parameters: list[dict[str, Any]] | None = None,
    ) -> list[QueryResult]:
        """
        批量执行查询

        Args:
            queries: 查询语句列表
            parameters: 参数列表

        Returns:
            list[QueryResult]: 查询结果列表
        """
        pass

    @abstractmethod
    def explain_query(self, query: str) -> QueryPlan:
        """
        解释查询计划

        Args:
            query: 查询语句

        Returns:
            QueryPlan: 查询执行计划
        """
        pass

    @abstractmethod
    async def health_check(self) -> dict[str, Any]:
        """
        健康检查

        Returns:
            dict: 健康状态信息
        """
        pass

    async def __aenter__(self):
        """异步上下文管理器入口"""
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器出口"""
        await self.disconnect()


class QueryOptimizer(ABC):
    """
    查询优化器基类

    负责查询优化和执行计划生成
    """

    @abstractmethod
    def optimize(self, query: str, data_source: DataSourceType) -> str:
        """
        优化查询

        Args:
            query: 原始查询
            data_source: 数据源类型

        Returns:
            str: 优化后的查询
        """
        pass

    @abstractmethod
    def generate_plan(
        self,
        query: str,
        data_source: DataSourceType,
    ) -> QueryPlan:
        """
        生成执行计划

        Args:
            query: 查询语句
            data_source: 数据源类型

        Returns:
            QueryPlan: 执行计划
        """
        pass


class CacheStrategy(ABC):
    """
    缓存策略基类

    定义缓存接口
    """

    @abstractmethod
    async def get(self, key: str) -> QueryResult | None:
        """
        获取缓存

        Args:
            key: 缓存键

        Returns:
            QueryResult | None: 缓存的结果
        """
        pass

    @abstractmethod
    async def set(
        self,
        key: str,
        value: QueryResult,
        ttl: int | None = None,
    ) -> None:
        """
        设置缓存

        Args:
            key: 缓存键
            value: 缓存值
            ttl: 过期时间（秒）
        """
        pass

    @abstractmethod
    async def delete(self, key: str) -> bool:
        """
        删除缓存

        Args:
            key: 缓存键

        Returns:
            bool: 是否成功删除
        """
        pass

    @abstractmethod
    async def clear(self) -> None:
        """清空缓存"""
        pass

    @abstractmethod
    async def get_stats(self) -> dict[str, Any]:
        """
        获取缓存统计

        Returns:
            dict: 缓存统计信息
        """
        pass


# 导出类型
__all__ = [
    "BaseAdapter",
    "QueryOptimizer",
    "CacheStrategy",
    "DataSourceType",
    "QueryPlan",
    "QueryResult",
    "QueryStats",
]
