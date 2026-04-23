#!/usr/bin/env python3
from __future__ import annotations
"""
Neo4j图查询适配器
Neo4j Graph Query Adapter

提供Neo4j图数据库的查询能力

作者: Athena平台团队
版本: 1.0.0
"""

import logging
import time
from datetime import datetime
from typing import Any

from core.query_engine.base import BaseAdapter
from core.query_engine.types import DataSourceType, QueryPlan, QueryResult, QueryStats, QueryStatus

logger = logging.getLogger(__name__)


class Neo4jAdapter(BaseAdapter):
    """
    Neo4j图查询适配器

    支持Cypher查询、节点关系操作、路径查询
    """

    def __init__(self, connection_config: dict[str, Any]):
        """
        初始化Neo4j适配器

        Args:
            connection_config: 连接配置，包含:
                - uri: 数据库URI（如bolt://localhost:7687）
                - user: 用户名
                - password: 密码
                - database: 数据库名（默认neo4j）
        """
        super().__init__(connection_config)
        self._driver = None

    @property
    def data_source_type(self) -> DataSourceType:
        """返回数据源类型"""
        return DataSourceType.NEO4J

    async def connect(self) -> None:
        """建立连接"""
        try:
            from neo4j import AsyncGraphDatabase

            self._driver = AsyncGraphDatabase.driver(
                self.connection_config["uri"],
                auth=(
                    self.connection_config["user"],
                    self.connection_config["password"],
                ),
            )

            # 测试连接
            async with self._driver.session(database=self.connection_config.get("database", "neo4j")) as session:
                await session.run("RETURN 1")

            self._is_connected = True
            logger.info("Neo4j连接已建立")
        except Exception as e:
            logger.error(f"Neo4j连接失败: {e}")
            raise

    async def disconnect(self) -> None:
        """断开连接"""
        if self._driver:
            await self._driver.close()
            self._is_connected = False
            logger.info("Neo4j连接已关闭")

    async def is_connected(self) -> bool:
        """检查连接状态"""
        if not self._is_connected or self._driver is None:
            return False
        try:
            async with self._driver.session() as session:
                await session.run("RETURN 1")
            return True
        except Exception:
            return False

    async def execute(
        self,
        query: str,
        parameters: Optional[dict[str, Any]] = None,
        **kwargs,
    ) -> QueryResult:
        """
        执行Cypher查询

        Args:
            query: Cypher查询语句
            parameters: 查询参数
            **kwargs: 额外参数
                - database: 数据库名
                - timeout: 超时时间

        Returns:
            QueryResult: 查询结果
        """
        if not await self.is_connected():
            await self.connect()

        start_time = time.time()
        params = parameters or {}
        database = kwargs.get("database", self.connection_config.get("database", "neo4j"))

        try:
            async with self._driver.session(database=database) as session:
                result = await session.run(query, params)

                # 获取所有记录
                records = []
                async for record in result:
                    # 将Record对象转换为字典
                    record_dict = dict(record)
                    records.append(record_dict)

                # 获取统计信息
                summary = await result.consume()

                execution_time = time.time() - start_time

                stats = QueryStats(
                    execution_time=execution_time,
                    rows_affected=summary.counters.nodes_created +
                                  summary.counters.nodes_deleted +
                                  summary.counters.relationships_created +
                                  summary.counters.relationships_deleted,
                    rows_returned=len(records),
                    data_source=DataSourceType.NEO4J,
                    timestamp=datetime.now(),
                )

                # 添加元数据
                metadata = {
                    "result_available_after": summary.result_available_after,
                    "result_consumed_after": summary.result_consumed_after,
                }

                return QueryResult(
                    data=records,
                    status=QueryStatus.COMPLETED,
                    stats=stats,
                    metadata=metadata,
                )

        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"Neo4j查询执行失败: {e}")

            stats = QueryStats(
                execution_time=execution_time,
                data_source=DataSourceType.NEO4J,
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
            queries: Cypher查询语句列表
            parameters: 参数列表

        Returns:
            list[QueryResult]: 查询结果列表
        """
        if parameters is None:
            parameters = [{}] * len(queries)

        results = []
        for query, params in zip(queries, parameters):
            result = await self.execute(query, params)
            results.append(result)

        return results

    async def execute_transaction(
        self,
        queries: list[str],
        parameters: list[dict[str, Any]] | None = None,
    ) -> list[QueryResult]:
        """
        执行事务

        Args:
            queries: Cypher查询语句列表
            parameters: 参数列表

        Returns:
            list[QueryResult]: 查询结果列表
        """
        if not await self.is_connected():
            await self.connect()

        if parameters is None:
            parameters = [{}] * len(queries)

        results = []
        database = self.connection_config.get("database", "neo4j")

        try:
            async with self._driver.session(database=database) as session:
                async with session.begin_transaction() as tx:
                    for query, params in zip(queries, parameters):
                        start_time = time.time()

                        result = await tx.run(query, params)

                        records = []
                        async for record in result:
                            records.append(dict(record))

                        execution_time = time.time() - start_time

                        stats = QueryStats(
                            execution_time=execution_time,
                            rows_returned=len(records),
                            data_source=DataSourceType.NEO4J,
                        )

                        results.append(
                            QueryResult(
                                data=records,
                                status=QueryStatus.COMPLETED,
                                stats=stats,
                            )
                        )

                    await tx.commit()

        except Exception as e:
            logger.error(f"Neo4j事务执行失败: {e}")
            # 返回失败状态
            for _ in range(len(results), len(queries)):
                results.append(
                    QueryResult(
                        data=[],
                        status=QueryStatus.FAILED,
                        stats=QueryStats(data_source=DataSourceType.NEO4J),
                        error=str(e),
                    )
                )

        return results

    def explain_query(self, query: str) -> QueryPlan:
        """
        解释查询计划

        Args:
            query: Cypher查询语句

        Returns:
            QueryPlan: 执行计划
        """
        query_upper = query.upper()

        # 估算复杂度
        complexity = 0
        weights = {
            "MATCH": 2,
            "OPTIONAL MATCH": 3,
            "CREATE": 5,
            "MERGE": 5,
            "DELETE": 5,
            "SET": 3,
            "RETURN": 1,
            "WHERE": 2,
            "ORDER BY": 2,
            "WITH": 2,
            "UNWIND": 3,
            "FOREACH": 4,
            "CALL": 10,
        }

        for keyword, weight in weights.items():
            complexity += query_upper.count(keyword) * weight

        # 检测路径查询
        complexity += query_upper.count("-[") * 3
        complexity += query_upper.count("]-[") * 5

        steps = [
            "1. 解析Cypher语句",
            "2. 生成执行计划",
            "3. 执行图遍历",
            "4. 返回结果",
        ]

        if "MATCH" in query_upper:
            steps.insert(2, "2.5. 执行模式匹配")

        if "CREATE" in query_upper or "MERGE" in query_upper:
            steps.insert(3, "3.5. 创建/更新节点和关系")

        return QueryPlan(
            steps=steps,
            estimated_cost=complexity,
            data_sources=[DataSourceType.NEO4J],
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

            async with self._driver.session() as session:
                # 获取数据库信息
                result = await session.run("CALL dbms.components() YIELD name, versions, edition")
                record = await result.single()

                # 获取节点和关系统计
                count_result = await session.run("MATCH (n) RETURN count(n) as node_count")
                node_record = await count_result.single()

                rel_result = await session.run("MATCH ()-[r]->() RETURN count(r) as rel_count")
                rel_record = await rel_result.single()

                return {
                    "status": "healthy",
                    "name": record["name"] if record else "neo4j",
                    "version": record["versions"][0] if record and record["versions"] else "unknown",
                    "edition": record["edition"] if record else "unknown",
                    "node_count": node_record["node_count"] if node_record else 0,
                    "relationship_count": rel_record["rel_count"] if rel_record else 0,
                }
        except Exception as e:
            return {
                "status": "unhealthy",
                "message": str(e),
            }


__all__ = ["Neo4jAdapter"]
