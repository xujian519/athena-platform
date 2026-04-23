#!/usr/bin/env python3
from __future__ import annotations
"""
Redis查询适配器
Redis Query Adapter

提供Redis缓存的查询能力

作者: Athena平台团队
版本: 1.0.0
"""

import json
import logging
import time
from datetime import datetime
from typing import Any

from core.query_engine.base import BaseAdapter
from core.query_engine.types import DataSourceType, QueryPlan, QueryResult, QueryStats, QueryStatus

logger = logging.getLogger(__name__)


class RedisAdapter(BaseAdapter):
    """
    Redis查询适配器

    支持String、Hash、List、Set、ZSet等数据结构操作
    """

    def __init__(self, connection_config: dict[str, Any]):
        """
        初始化Redis适配器

        Args:
            connection_config: 连接配置，包含:
                - host: 主机地址
                - port: 端口
                - password: 密码（可选）
                - db: 数据库编号（默认0）
                - decode_responses: 是否解码响应（默认True）
        """
        super().__init__(connection_config)
        self._client = None

    @property
    def data_source_type(self) -> DataSourceType:
        """返回数据源类型"""
        return DataSourceType.REDIS

    async def connect(self) -> None:
        """建立连接"""
        try:
            import redis.asyncio as aioredis

            self._client = await aioredis.Redis(
                host=self.connection_config.get("host", "localhost"),
                port=self.connection_config.get("port", 6379),
                password=self.connection_config.get("password"),
                db=self.connection_config.get("db", 0),
                decode_responses=self.connection_config.get("decode_responses", True),
            )

            # 测试连接
            await self._client.ping()
            self._is_connected = True
            logger.info("Redis连接已建立")
        except Exception as e:
            logger.error(f"Redis连接失败: {e}")
            raise

    async def disconnect(self) -> None:
        """断开连接"""
        if self._client:
            await self._client.close()
            self._is_connected = False
            logger.info("Redis连接已关闭")

    async def is_connected(self) -> bool:
        """检查连接状态"""
        if not self._is_connected or self._client is None:
            return False
        try:
            return await self._client.ping()
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
            query: Redis命令（如GET、SET、HGET等）
            parameters: 命令参数
            **kwargs: 额外参数

        Returns:
            QueryResult: 查询结果
        """
        if not await self.is_connected():
            await self.connect()

        start_time = time.time()
        params = parameters or {}

        try:
            command = query.upper().strip()
            result = None

            # String操作
            if command == "GET":
                result = await self._client.get(params.get("key"))
            elif command == "SET":
                ttl = params.get("ex", params.get("px"))
                if ttl:
                    result = await self._client.setex(
                        params["key"],
                        ttl,
                        params["value"],
                    )
                else:
                    result = await self._client.set(
                        params["key"],
                        params["value"],
                    )
            elif command == "MGET":
                result = await self._client.mget(params.get("keys", []))
            elif command == "MSET":
                result = await self._client.mset(params.get("mapping", {}))
            elif command == "INCR":
                result = await self._client.incr(params.get("key"))
            elif command == "DECR":
                result = await self._client.decr(params.get("key"))

            # Hash操作
            elif command == "HGET":
                result = await self._client.hget(params.get("name"), params.get("key"))
            elif command == "HSET":
                result = await self._client.hset(
                    params["name"],
                    key=params.get("key"),
                    value=params.get("value"),
                    mapping=params.get("mapping"),
                )
            elif command == "HGETALL":
                result = await self._client.hgetall(params.get("name"))
            elif command == "HKEYS":
                result = await self._client.hkeys(params.get("name"))
            elif command == "HVALS":
                result = await self._client.hvals(params.get("name"))
            elif command == "HDEL":
                result = await self._client.hdel(params.get("name"), *params.get("keys", []))

            # List操作
            elif command == "LPUSH":
                result = await self._client.lpush(params.get("name"), *params.get("values", []))
            elif command == "RPUSH":
                result = await self._client.rpush(params.get("name"), *params.get("values", []))
            elif command == "LPOP":
                result = await self._client.lpop(params.get("name"))
            elif command == "RPOP":
                result = await self._client.rpop(params.get("name"))
            elif command == "LRANGE":
                result = await self._client.lrange(
                    params.get("name"),
                    params.get("start", 0),
                    params.get("end", -1),
                )
            elif command == "LLEN":
                result = await self._client.llen(params.get("name"))

            # Set操作
            elif command == "SADD":
                result = await self._client.sadd(params.get("name"), *params.get("members", []))
            elif command == "SREM":
                result = await self._client.srem(params.get("name"), *params.get("members", []))
            elif command == "SMEMBERS":
                result = await self._client.smembers(params.get("name"))
            elif command == "SISMEMBER":
                result = await self._client.sismember(params.get("name"), params.get("value"))
            elif command == "SCARD":
                result = await self._client.scard(params.get("name"))

            # Sorted Set操作
            elif command == "ZADD":
                result = await self._client.zadd(
                    params.get("name"),
                    {params.get("member"): params.get("score")},
                )
            elif command == "ZREM":
                result = await self._client.zrem(params.get("name"), params.get("member"))
            elif command == "ZRANGE":
                result = await self._client.zrange(
                    params.get("name"),
                    params.get("start", 0),
                    params.get("end", -1),
                )
            elif command == "ZRANGEBYSCORE":
                result = await self._client.zrangebyscore(
                    params.get("name"),
                    params.get("min"),
                    params.get("max"),
                )
            elif command == "ZCARD":
                result = await self._client.zcard(params.get("name"))

            # 通用操作
            elif command == "DEL":
                result = await self._client.delete(*params.get("keys", []))
            elif command == "EXISTS":
                result = await self._client.exists(*params.get("keys", []))
            elif command == "EXPIRE":
                result = await self._client.expire(params.get("key"), params.get("seconds"))
            elif command == "TTL":
                result = await self._client.ttl(params.get("key"))
            elif command == "KEYS":
                result = await self._client.keys(params.get("pattern", "*"))
            else:
                raise ValueError(f"不支持的Redis命令: {query}")

            execution_time = time.time() - start_time

            # 格式化结果
            if result is None:
                data = []
            elif isinstance(result, (list, set, tuple)):
                data = [{"value": v} for v in result]
            elif isinstance(result, dict):
                data = [{"key": k, "value": v} for k, v in result.items()]
            elif isinstance(result, (int, float, str, bool)):
                data = [{"result": result}]
            else:
                data = [{"result": str(result)}]

            stats = QueryStats(
                execution_time=execution_time,
                rows_affected=len(data),
                rows_returned=len(data),
                data_source=DataSourceType.REDIS,
                timestamp=datetime.now(),
            )

            return QueryResult(
                data=data,
                status=QueryStatus.COMPLETED,
                stats=stats,
            )

        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"Redis命令执行失败: {e}")

            stats = QueryStats(
                execution_time=execution_time,
                data_source=DataSourceType.REDIS,
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
        批量执行命令（使用Pipeline）

        Args:
            queries: Redis命令列表
            parameters: 参数列表

        Returns:
            list[QueryResult]: 查询结果列表
        """
        if not await self.is_connected():
            await self.connect()

        if parameters is None:
            parameters = [{}] * len(queries)

        start_time = time.time()
        results = []

        try:
            async with self._client.pipeline(transaction=False) as pipe:
                # 构建管道命令
                for query, params in zip(queries, parameters):
                    command = query.upper().strip()
                    p = params or {}

                    if command == "GET":
                        pipe.get(p.get("key"))
                    elif command == "SET":
                        pipe.set(p.get("key"), p.get("value"))
                    elif command == "HGET":
                        pipe.hget(p.get("name"), p.get("key"))
                    elif command == "HGETALL":
                        pipe.hgetall(p.get("name"))
                    # 添加更多命令支持...

                # 执行管道
                raw_results = await pipe.execute()

            # 格式化结果
            for raw_result in raw_results:
                if isinstance(raw_result, Exception):
                    results.append(
                        QueryResult(
                            data=[],
                            status=QueryStatus.FAILED,
                            stats=QueryStats(data_source=DataSourceType.REDIS),
                            error=str(raw_result),
                        )
                    )
                else:
                    if isinstance(raw_result, (list, set)):
                        data = [{"value": v} for v in raw_result]
                    elif isinstance(raw_result, dict):
                        data = [{"key": k, "value": v} for k, v in raw_result.items()]
                    elif raw_result is None:
                        data = []
                    else:
                        data = [{"result": raw_result}]

                    results.append(
                        QueryResult(
                            data=data,
                            status=QueryStatus.COMPLETED,
                            stats=QueryStats(
                                execution_time=(time.time() - start_time) / len(queries),
                                rows_returned=len(data),
                                data_source=DataSourceType.REDIS,
                            ),
                        )
                    )

        except Exception as e:
            logger.error(f"Redis Pipeline执行失败: {e}")
            # 返回失败结果
            for _ in range(len(queries)):
                results.append(
                    QueryResult(
                        data=[],
                        status=QueryStatus.FAILED,
                        stats=QueryStats(data_source=DataSourceType.REDIS),
                        error=str(e),
                    )
                )

        return results

    def explain_query(self, query: str) -> QueryPlan:
        """
        解释查询计划

        Args:
            query: Redis命令

        Returns:
            QueryPlan: 执行计划
        """
        command = query.upper().strip()

        # Redis命令复杂度参考
        complexity_map = {
            # O(1)操作
            "GET": 1,
            "SET": 1,
            "HGET": 1,
            "HSET": 1,
            "INCR": 1,
            "DECR": 1,
            "SISMEMBER": 1,
            "ZADD": 1,
            "EXISTS": 1,
            "DEL": 1,
            # O(N)操作
            "KEYS": 100,
            "MGET": 10,
            "MSET": 10,
            "HGETALL": 50,
            "HKEYS": 50,
            "HVALS": 50,
            "LRANGE": 50,
            "SMEMBERS": 50,
            "ZRANGE": 50,
        }

        complexity = complexity_map.get(command, 10)

        steps = [
            f"1. 解析Redis命令: {command}",
            "2. 定位Key",
            "3. 执行操作",
            "4. 返回结果",
        ]

        return QueryPlan(
            steps=steps,
            estimated_cost=complexity,
            data_sources=[DataSourceType.REDIS],
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

            # 获取Redis信息
            info = await self._client.info()
            db_size = await self._client.dbsize()

            return {
                "status": "healthy",
                "version": info.get("redis_version"),
                "db_size": db_size,
                "used_memory": info.get("used_memory_human"),
                "connected_clients": info.get("connected_clients"),
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "message": str(e),
            }


__all__ = ["RedisAdapter"]
