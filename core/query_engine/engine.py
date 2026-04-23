#!/usr/bin/env python3
from __future__ import annotations
"""
Query Engine核心引擎
Query Engine Core Engine

提供统一的跨数据源查询能力

作者: Athena平台团队
版本: 1.0.0
"""

import logging
import re
import time
from datetime import datetime
from typing import Any

from core.query_engine.adapters import (
    Neo4jAdapter,
    PostgreSQLAdapter,
    QdrantAdapter,
    RedisAdapter,
)
from core.query_engine.base import BaseAdapter, CacheStrategy
from core.query_engine.cache import MemoryCache, MultiLevelCache
from core.query_engine.exceptions import AdapterNotFoundError, InvalidQueryError
from core.query_engine.types import (
    CacheKey,
    DataSourceType,
    QueryPlan,
    QueryResult,
    QueryStats,
    QueryStatus,
)

logger = logging.getLogger(__name__)


class QueryEngine:
    """
    查询引擎核心类

    提供统一的查询接口，支持跨数据源查询和缓存
    """

    def __init__(
        self,
        cache: CacheStrategy | None = None,
        enable_cache: bool = True,
    ):
        """
        初始化查询引擎

        Args:
            cache: 缓存策略
            enable_cache: 是否启用缓存
        """
        self._adapters: dict[DataSourceType, BaseAdapter] = {}
        self._cache = cache or MemoryCache()
        self._enable_cache = enable_cache
        self._query_count = 0
        self._total_time = 0.0

    def register_adapter(
        self,
        data_source: DataSourceType,
        adapter: BaseAdapter,
    ) -> None:
        """
        注册数据源适配器

        Args:
            data_source: 数据源类型
            adapter: 适配器实例
        """
        self._adapters[data_source] = adapter
        logger.info(f"已注册适配器: {data_source.value}")

    async def connect_all(self) -> None:
        """连接所有已注册的适配器"""
        for data_source, adapter in self._adapters.items():
            if not await adapter.is_connected():
                await adapter.connect()
                logger.info(f"已连接数据源: {data_source.value}")

    async def disconnect_all(self) -> None:
        """断开所有适配器连接"""
        for data_source, adapter in self._adapters.items():
            if await adapter.is_connected():
                await adapter.disconnect()
                logger.info(f"已断开数据源: {data_source.value}")

    async def execute(
        self,
        query: str,
        data_source: DataSourceType,
        parameters: Optional[dict[str, Any]] = None,
        use_cache: Optional[bool] = None,
        **kwargs,
    ) -> QueryResult:
        """
        执行查询

        Args:
            query: 查询语句
            data_source: 数据源类型
            parameters: 查询参数
            use_cache: 是否使用缓存（默认使用引擎配置）
            **kwargs: 额外参数

        Returns:
            QueryResult: 查询结果
        """
        self._query_count += 1

        # 检查是否使用缓存
        should_use_cache = use_cache if use_cache is not None else self._enable_cache

        if should_use_cache:
            cache_key = str(CacheKey(data_source, query, tuple(sorted((parameters or {}).items()))))
            cached_result = await self._cache.get(cache_key)
            if cached_result:
                logger.debug(f"缓存命中: {cache_key[:16]}...")
                return cached_result

        # 获取适配器
        adapter = self._adapters.get(data_source)
        if not adapter:
            raise AdapterNotFoundError(data_source.value)

        # 执行查询
        start_time = time.time()
        result = await adapter.execute(query, parameters, **kwargs)
        execution_time = time.time() - start_time

        self._total_time += execution_time

        # 缓存结果
        if should_use_cache and result.is_success:
            await self._cache.set(
                cache_key,
                result,
                ttl=kwargs.get("cache_ttl"),
            )

        return result

    async def execute_cross_source(
        self,
        queries: dict[DataSourceType, str],
        join_strategy: str = "sequential",
        join_key: Optional[str] = None,
    ) -> QueryResult:
        """
        执行跨数据源查询

        Args:
            queries: 各数据源的查询字典
            join_strategy: 连接策略（sequential, parallel, merge）
            join_key: 连接键

        Returns:
            QueryResult: 合并后的查询结果
        """
        start_time = time.time()
        results = []

        if join_strategy == "parallel":
            # 并行执行
            import asyncio

            tasks = []
            for data_source, query in queries.items():
                task = self.execute(query, data_source)
                tasks.append(task)

            raw_results = await asyncio.gather(*tasks, return_exceptions=True)

            for raw_result in raw_results:
                if isinstance(raw_result, Exception):
                    results.append(
                        QueryResult(
                            data=[],
                            status=QueryStatus.FAILED,
                            stats=QueryStats(),
                            error=str(raw_result),
                        )
                    )
                elif isinstance(raw_result, QueryResult):
                    results.append(raw_result)

        elif join_strategy == "sequential":
            # 顺序执行
            for data_source, query in queries.items():
                result = await self.execute(query, data_source)
                results.append(result)

        elif join_strategy == "merge":
            # 合并执行（需要join_key）
            if not join_key:
                raise InvalidQueryError("", "合并策略需要指定join_key")

            all_data = {}
            for data_source, query in queries.items():
                result = await self.execute(query, data_source)
                for row in result.data:
                    key = row.get(join_key)
                    if key is not None:
                        if key not in all_data:
                            all_data[key] = {}
                        all_data[key][data_source.value] = row

            # 转换为列表
            merged_data = [
                {"_key": k, **v} for k, v in all_data.items()
            ]

            execution_time = time.time() - start_time

            stats = QueryStats(
                execution_time=execution_time,
                rows_returned=len(merged_data),
                timestamp=datetime.now(),
            )

            return QueryResult(
                data=merged_data,
                status=QueryStatus.COMPLETED,
                stats=stats,
                metadata={"join_strategy": "merge", "join_key": join_key},
            )

        else:
            raise InvalidQueryError("", f"不支持的连接策略: {join_strategy}")

        # 合并结果
        execution_time = time.time() - start_time

        total_rows = sum(r.row_count for r in results)
        all_data = []
        for result in results:
            all_data.extend(result.data)

        stats = QueryStats(
            execution_time=execution_time,
            rows_returned=total_rows,
            timestamp=datetime.now(),
        )

        return QueryResult(
            data=all_data,
            status=QueryStatus.COMPLETED,
            stats=stats,
            metadata={"join_strategy": join_strategy, "result_count": len(results)},
        )

    def explain(
        self,
        query: str,
        data_source: DataSourceType,
    ) -> QueryPlan:
        """
        解释查询计划

        Args:
            query: 查询语句
            data_source: 数据源类型

        Returns:
            QueryPlan: 执行计划
        """
        adapter = self._adapters.get(data_source)
        if not adapter:
            raise AdapterNotFoundError(data_source.value)

        return adapter.explain_query(query)

    async def health_check(self) -> dict[str, Any]:
        """
        健康检查

        Returns:
            dict: 所有数据源的健康状态
        """
        health_status = {}

        for data_source, adapter in self._adapters.items():
            try:
                status = await adapter.health_check()
                health_status[data_source.value] = status
            except Exception as e:
                health_status[data_source.value] = {
                    "status": "error",
                    "message": str(e),
                }

        return health_status

    async def get_cache_stats(self) -> dict[str, Any]:
        """
        获取缓存统计

        Returns:
            dict: 缓存统计信息
        """
        return await self._cache.get_stats()

    def get_stats(self) -> dict[str, Any]:
        """
        获取引擎统计

        Returns:
            dict: 统计信息
        """
        avg_time = self._total_time / self._query_count if self._query_count > 0 else 0

        return {
            "query_count": self._query_count,
            "total_time": self._total_time,
            "avg_time": avg_time,
            "registered_adapters": list(self._adapters.keys()),
        }


class QueryOptimizer:
    """
    查询优化器

    提供查询优化和执行计划分析
    """

    @staticmethod
    def optimize_sql(query: str) -> str:
        """
        优化SQL查询

        Args:
            query: 原始SQL查询

        Returns:
            str: 优化后的SQL查询
        """
        # 去除多余空格
        query = re.sub(r"\s+", " ", query).strip()

        # 转换为 uppercase 关键字
        keywords = [
            "SELECT", "FROM", "WHERE", "JOIN", "LEFT JOIN", "RIGHT JOIN",
            "INNER JOIN", "ON", "AND", "OR", "ORDER BY", "GROUP BY",
            "HAVING", "LIMIT", "OFFSET", "INSERT INTO", "VALUES",
            "UPDATE", "SET", "DELETE FROM",
        ]

        for keyword in keywords:
            pattern = r"\b" + keyword.lower() + r"\b"
            query = re.sub(pattern, keyword, query, flags=re.IGNORECASE)

        return query

    @staticmethod
    def estimate_complexity(query: str, data_source: DataSourceType) -> int:
        """
        估算查询复杂度

        Args:
            query: 查询语句
            data_source: 数据源类型

        Returns:
            int: 复杂度评分（0-100）
        """
        query_upper = query.upper()

        if data_source == DataSourceType.POSTGRESQL:
            # SQL复杂度估算
            complexity = 0
            complexity += query_upper.count("JOIN") * 10
            complexity += query_upper.count("SUBQUERY") * 15
            complexity += query_upper.count("UNION") * 10
            complexity += query_upper.count("GROUP BY") * 5
            complexity += query_upper.count("ORDER BY") * 3
            complexity += query_upper.count("HAVING") * 5
            return min(complexity, 100)

        elif data_source == DataSourceType.REDIS:
            # Redis命令复杂度
            if "KEYS" in query_upper:
                return 80
            return 10

        elif data_source == DataSourceType.QDRANT:
            # Qdrant查询复杂度
            if "SEARCH" in query_upper:
                return 50
            return 20

        elif data_source == DataSourceType.NEO4J:
            # Cypher复杂度估算
            complexity = 0
            complexity += query_upper.count("MATCH") * 5
            complexity += query_upper.count("OPTIONAL MATCH") * 8
            complexity += query_upper.count("-[") * 10
            complexity += query_upper.count("CREATE") * 10
            return min(complexity, 100)

        return 50


# 工厂函数
async def create_query_engine(
    postgres_config: Optional[dict[str, Any]] = None,
    redis_config: Optional[dict[str, Any]] = None,
    qdrant_config: Optional[dict[str, Any]] = None,
    neo4j_config: Optional[dict[str, Any]] = None,
    enable_cache: bool = True,
) -> QueryEngine:
    """
    创建查询引擎实例

    Args:
        postgres_config: PostgreSQL配置
        redis_config: Redis配置
        qdrant_config: Qdrant配置
        neo4j_config: Neo4j配置
        enable_cache: 是否启用缓存

    Returns:
        QueryEngine: 查询引擎实例
    """
    engine = QueryEngine(enable_cache=enable_cache)

    if postgres_config:
        engine.register_adapter(
            DataSourceType.POSTGRESQL,
            PostgreSQLAdapter(postgres_config),
        )

    if redis_config:
        engine.register_adapter(
            DataSourceType.REDIS,
            RedisAdapter(redis_config),
        )

    if qdrant_config:
        engine.register_adapter(
            DataSourceType.QDRANT,
            QdrantAdapter(qdrant_config),
        )

    if neo4j_config:
        engine.register_adapter(
            DataSourceType.NEO4J,
            Neo4jAdapter(neo4j_config),
        )

    # 连接所有数据源
    await engine.connect_all()

    return engine


__all__ = [
    "QueryEngine",
    "QueryOptimizer",
    "create_query_engine",
]
