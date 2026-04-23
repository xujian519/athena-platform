#!/usr/bin/env python3
from __future__ import annotations
"""
Qdrant向量查询适配器
Qdrant Vector Query Adapter

提供Qdrant向量数据库的查询能力

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


class QdrantAdapter(BaseAdapter):
    """
    Qdrant向量查询适配器

    支持向量相似度搜索、过滤查询、批量操作
    """

    def __init__(self, connection_config: dict[str, Any]):
        """
        初始化Qdrant适配器

        Args:
            connection_config: 连接配置，包含:
                - host: 主机地址
                - port: 端口（默认6333）
                - api_key: API密钥（可选）
                - timeout: 超时时间（默认60秒）
        """
        super().__init__(connection_config)
        self._client = None

    @property
    def data_source_type(self) -> DataSourceType:
        """返回数据源类型"""
        return DataSourceType.QDRANT

    async def connect(self) -> None:
        """建立连接"""
        try:
            from qdrant_client import AsyncQdrantClient
            from qdrant_client.http.exceptions import UnexpectedResponse

            self._client = AsyncQdrantClient(
                host=self.connection_config.get("host", "localhost"),
                port=self.connection_config.get("port", 6333),
                api_key=self.connection_config.get("api_key"),
                timeout=self.connection_config.get("timeout", 60),
            )

            # 测试连接
            collections = await self._client.get_collections()
            self._is_connected = True
            logger.info("Qdrant连接已建立")
        except Exception as e:
            logger.error(f"Qdrant连接失败: {e}")
            raise

    async def disconnect(self) -> None:
        """断开连接"""
        if self._client:
            await self._client.close()
            self._is_connected = False
            logger.info("Qdrant连接已关闭")

    async def is_connected(self) -> bool:
        """检查连接状态"""
        if not self._is_connected or self._client is None:
            return False
        try:
            await self._client.get_collections()
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
        执行查询

        Args:
            query: 查询类型（search、recommend、scroll等）
            parameters: 查询参数
            **kwargs: 额外参数

        Returns:
            QueryResult: 查询结果
        """
        if not await self.is_connected():
            await self.connect()

        start_time = time.time()
        params = parameters or {}

        try:
            query_type = query.lower().strip()
            result_data = []

            if query_type == "search":
                # 向量相似度搜索
                results = await self._client.search(
                    collection_name=params.get("collection_name"),
                    query_vector=params.get("vector"),
                    query_filter=params.get("filter"),
                    limit=params.get("limit", 10),
                    offset=params.get("offset", 0),
                    score_threshold=params.get("score_threshold"),
                    with_payload=params.get("with_payload", True),
                    with_vectors=params.get("with_vectors", False),
                )

                result_data = [
                    {
                        "id": str(r.id),
                        "score": r.score,
                        "payload": r.payload if r.payload else {},
                    }
                    for r in results
                ]

            elif query_type == "recommend":
                # 推荐查询
                results = await self._client.recommend(
                    collection_name=params.get("collection_name"),
                    positive=params.get("positive", []),
                    negative=params.get("negative", []),
                    limit=params.get("limit", 10),
                    query_filter=params.get("filter"),
                    with_payload=params.get("with_payload", True),
                )

                result_data = [
                    {
                        "id": str(r.id),
                        "score": r.score,
                        "payload": r.payload if r.payload else {},
                    }
                    for r in results
                ]

            elif query_type == "scroll":
                # 滚动查询
                results, next_page_offset = await self._client.scroll(
                    collection_name=params.get("collection_name"),
                    scroll_filter=params.get("filter"),
                    limit=params.get("limit", 10),
                    offset=params.get("offset"),
                    with_payload=params.get("with_payload", True),
                    with_vectors=params.get("with_vectors", False),
                )

                result_data = [
                    {
                        "id": str(r.id),
                        "payload": r.payload if r.payload else {},
                    }
                    for r in results
                ]

            elif query_type == "count":
                # 计数查询
                count_result = await self._client.count(
                    collection_name=params.get("collection_name"),
                    count_filter=params.get("filter"),
                )

                result_data = [{"count": count_result.count}]

            elif query_type == "get":
                # 通过ID获取
                points = await self._client.retrieve(
                    collection_name=params.get("collection_name"),
                    ids=params.get("ids", []),
                    with_payload=params.get("with_payload", True),
                    with_vectors=params.get("with_vectors", False),
                )

                result_data = [
                    {
                        "id": str(p.id),
                        "payload": p.payload if p.payload else {},
                    }
                    for p in points
                ]

            elif query_type == "delete":
                # 删除操作
                await self._client.delete(
                    collection_name=params.get("collection_name"),
                    points_selector=params.get("points_selector"),
                )

                result_data = [{"deleted": True}]

            elif query_type == "create_collection":
                # 创建集合
                from qdrant_client.models import Distance, VectorParams

                await self._client.create_collection(
                    collection_name=params.get("collection_name"),
                    vectors_config=VectorParams(
                        size=params.get("vector_size", 768),
                        distance=Distance.COSINE,
                    ),
                )

                result_data = [{"created": True}]

            elif query_type == "list_collections":
                # 列出所有集合
                collections = await self._client.get_collections()
                result_data = [
                    {"name": c.name} for c in collections.collections
                ]

            else:
                raise ValueError(f"不支持的查询类型: {query_type}")

            execution_time = time.time() - start_time

            stats = QueryStats(
                execution_time=execution_time,
                rows_affected=len(result_data),
                rows_returned=len(result_data),
                data_source=DataSourceType.QDRANT,
                timestamp=datetime.now(),
            )

            return QueryResult(
                data=result_data,
                status=QueryStatus.COMPLETED,
                stats=stats,
            )

        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"Qdrant查询执行失败: {e}")

            stats = QueryStats(
                execution_time=execution_time,
                data_source=DataSourceType.QDRANT,
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
            queries: 查询类型列表
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

    def explain_query(self, query: str) -> QueryPlan:
        """
        解释查询计划

        Args:
            query: 查询类型

        Returns:
            QueryPlan: 执行计划
        """
        query_type = query.lower().strip()

        complexity_map = {
            "search": 50,
            "recommend": 60,
            "scroll": 30,
            "count": 10,
            "get": 10,
            "delete": 20,
            "create_collection": 5,
            "list_collections": 5,
        }

        complexity = complexity_map.get(query_type, 20)

        steps = [
            f"1. 解析查询类型: {query_type}",
            "2. 定位集合",
            "3. 执行向量搜索/操作",
            "4. 返回结果",
        ]

        if query_type == "search":
            steps.insert(2, "2.5. 计算向量相似度")

        return QueryPlan(
            steps=steps,
            estimated_cost=complexity,
            data_sources=[DataSourceType.QDRANT],
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

            collections = await self._client.get_collections()

            return {
                "status": "healthy",
                "collection_count": len(collections.collections),
                "collections": [c.name for c in collections.collections],
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "message": str(e),
            }


__all__ = ["QdrantAdapter"]
