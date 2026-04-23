#!/usr/bin/env python3
from __future__ import annotations
"""
PostgreSQL查询适配器
PostgreSQL Query Adapter

提供PostgreSQL数据库的查询能力

作者: Athena平台团队
版本: 1.0.0
"""

import logging
import time
from datetime import datetime
from typing import Any

from core.query_engine.base import BaseAdapter
from core.query_engine.exceptions import QueryExecutionError
from core.query_engine.types import DataSourceType, QueryPlan, QueryResult, QueryStats, QueryStatus

logger = logging.getLogger(__name__)


class PostgreSQLAdapter(BaseAdapter):
    """
    PostgreSQL查询适配器

    支持标准SQL查询、参数化查询、批量操作
    """

    def __init__(self, connection_config: dict[str, Any]):
        """
        初始化PostgreSQL适配器

        Args:
            connection_config: 连接配置，包含:
                - host: 主机地址
                - port: 端口
                - database: 数据库名
                - user: 用户名
                - password: 密码
                - pool_size: 连接池大小（可选）
        """
        super().__init__(connection_config)
        self._pool = None

    @property
    def data_source_type(self) -> DataSourceType:
        """返回数据源类型"""
        return DataSourceType.POSTGRESQL

    async def connect(self) -> None:
        """建立连接"""
        try:
            import asyncpg

            dsn = (
                f"postgresql://{self.connection_config['user']}:"
                f"{self.connection_config['password']}@"
                f"{self.connection_config['host']}:"
                f"{self.connection_config.get('port', 5432)}/"
                f"{self.connection_config['database']}"
            )

            pool_size = self.connection_config.get("pool_size", 10)
            self._pool = await asyncpg.create_pool(dsn, min_size=5, max_size=pool_size)

            self._is_connected = True
            logger.info(f"PostgreSQL连接已建立: {self.connection_config['database']}")
        except Exception as e:
            logger.error(f"PostgreSQL连接失败: {e}")
            raise

    async def disconnect(self) -> None:
        """断开连接"""
        if self._pool:
            await self._pool.close()
            self._is_connected = False
            logger.info("PostgreSQL连接已关闭")

    async def is_connected(self) -> bool:
        """检查连接状态"""
        return self._is_connected and self._pool is not None

    async def execute(
        self,
        query: str,
        parameters: Optional[dict[str, Any]] = None,
        **kwargs,
    ) -> QueryResult:
        """
        执行查询

        Args:
            query: SQL查询语句
            parameters: 查询参数（字典形式，支持$1命名参数）
            **kwargs: 额外参数
                - timeout: 超时时间（秒）
                - fetch_all: 是否获取所有结果（默认True）

        Returns:
            QueryResult: 查询结果
        """
        if not await self.is_connected():
            await self.connect()

        start_time = time.time()
        timeout = kwargs.get("timeout", 30)
        fetch_all = kwargs.get("fetch_all", True)

        try:
            async with self._pool.acquire() as conn:
                # 判断是否为SELECT查询
                is_select = query.strip().upper().startswith("SELECT")

                if is_select:
                    # SELECT查询 - 获取数据
                    if parameters:
                        # 使用参数化查询
                        rows = await conn.fetch(query, *parameters.values(), timeout=timeout)
                    else:
                        rows = await conn.fetch(query, timeout=timeout)

                    data = [dict(row) for row in rows]
                else:
                    # 非SELECT查询 - 执行并返回状态
                    result = await conn.execute(query, timeout=timeout)
                    data = [{"result": result}]

                execution_time = time.time() - start_time

                stats = QueryStats(
                    execution_time=execution_time,
                    rows_affected=len(data),
                    rows_returned=len(data),
                    data_source=DataSourceType.POSTGRESQL,
                    timestamp=datetime.now(),
                )

                return QueryResult(
                    data=data,
                    status=QueryStatus.COMPLETED,
                    stats=stats,
                )

        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"PostgreSQL查询执行失败: {e}")

            stats = QueryStats(
                execution_time=execution_time,
                data_source=DataSourceType.POSTGRESQL,
                timestamp=datetime.now(),
            )

            return QueryResult(
                data=[],
                status=QueryStatus.FAILED,
                stats=stats,
                error=str(e),
            )

    async def execute_batch(
        self,
        queries: list[str],
        parameters: list[dict[str, Any]] | None = None,
    ) -> list[QueryResult]:
        """
        批量执行查询

        Args:
            queries: SQL查询语句列表
            parameters: 参数列表

        Returns:
            list[QueryResult]: 查询结果列表
        """
        if parameters is None:
            parameters = [None] * len(queries)

        results = []
        for query, params in zip(queries, parameters):
            result = await self.execute(query, params)
            results.append(result)

        return results

    def explain_query(self, query: str) -> QueryPlan:
        """
        解释查询计划

        Args:
            query: SQL查询语句

        Returns:
            QueryPlan: 执行计划
        """
        # 简单的查询复杂度估算
        complexity = 0
        query_upper = query.upper()

        # 关键词权重
        weights = {
            "SELECT": 1,
            "JOIN": 3,
            "LEFT JOIN": 3,
            "RIGHT JOIN": 3,
            "INNER JOIN": 3,
            "OUTER JOIN": 4,
            "SUBQUERY": 5,
            "UNION": 4,
            "GROUP BY": 2,
            "ORDER BY": 1,
            "HAVING": 2,
            "WINDOW": 5,
        }

        for keyword, weight in weights.items():
            complexity += query_upper.count(keyword) * weight

        # 检测子查询
        complexity += query_upper.count("(SELECT") * 5

        steps = [
            "1. 解析SQL语句",
            "2. 生成执行计划",
            "3. 执行查询",
            "4. 返回结果",
        ]

        if "JOIN" in query_upper:
            steps.insert(2, "2.5. 执行表连接")

        if "GROUP BY" in query_upper or "ORDER BY" in query_upper:
            steps.append("5. 执行排序/聚合")

        return QueryPlan(
            steps=steps,
            estimated_cost=complexity,
            data_sources=[DataSourceType.POSTGRESQL],
            parallelizable=False,
        )

    async def health_check(self) -> dict[str, Any]:
        """
        健康检查

        Returns:
            dict: 健康状态信息
        """
        try:
            if not await self.is_connected():
                return {
                    "status": "unhealthy",
                    "message": "未连接",
                }

            async with self._pool.acquire() as conn:
                version = await conn.fetchval("SELECT version()")
                pool_stats = {
                    "min_size": self._pool.get_min_size(),
                    "max_size": self._pool.get_max_size(),
                    "current_size": self._pool.get_size(),
                }

                return {
                    "status": "healthy",
                    "version": version,
                    "pool_stats": pool_stats,
                }
        except Exception as e:
            return {
                "status": "unhealthy",
                "message": str(e),
            }

    async def execute_transaction(
        self,
        queries: list[str],
        parameters: list[dict[str, Any]] | None = None,
    ) -> list[QueryResult]:
        """
        执行事务

        Args:
            queries: SQL查询语句列表
            parameters: 参数列表

        Returns:
            list[QueryResult]: 查询结果列表
        """
        if not await self.is_connected():
            await self.connect()

        if parameters is None:
            parameters = [None] * len(queries)

        results = []

        try:
            async with self._pool.acquire() as conn:
                async with conn.transaction():
                    for query, params in zip(queries, parameters):
                        start_time = time.time()

                        if params:
                            rows = await conn.fetch(query, *params.values())
                        else:
                            rows = await conn.fetch(query)

                        execution_time = time.time() - start_time

                        stats = QueryStats(
                            execution_time=execution_time,
                            rows_affected=len(rows),
                            rows_returned=len(rows),
                            data_source=DataSourceType.POSTGRESQL,
                        )

                        results.append(
                            QueryResult(
                                data=[dict(row) for row in rows],
                                status=QueryStatus.COMPLETED,
                                stats=stats,
                            )
                        )
        except Exception as e:
            logger.error(f"事务执行失败: {e}")
            # 返回失败状态
            for _ in range(len(results), len(queries)):
                results.append(
                    QueryResult(
                        data=[],
                        status=QueryStatus.FAILED,
                        stats=QueryStats(data_source=DataSourceType.POSTGRESQL),
                        error=str(e),
                    )
                )

        return results


__all__ = ["PostgreSQLAdapter"]
