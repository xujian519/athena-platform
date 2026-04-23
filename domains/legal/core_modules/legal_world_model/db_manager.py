#!/usr/bin/env python3
from __future__ import annotations

"""
法律世界模型数据库管理器
Legal World Model Database Manager

管理Neo4j数据库连接，提供法律世界模型数据的CRUD操作

Author: Athena Team
Version: 1.0.0
Date: 2026-03-06
"""

import logging
import os
from typing import Any

from neo4j import AsyncDriver, AsyncGraphDatabase, AsyncSession

logger = logging.getLogger(__name__)


class LegalWorldDBManager:
    """
    法律世界模型数据库管理器

    管理Neo4j连接，提供法律世界模型的数据访问接口
    """

    def __init__(
        self,
        uri: str = "bolt://localhost:7687",
        username: str = "neo4j",
        password: str = os.getenv("DB_PASSWORD", "password"),
        database: str = "legal_world",
    ):
        """
        初始化数据库管理器

        Args:
            uri: Neo4j URI
            username: 用户名
            password: 密码
            database: 数据库名称
        """
        self.uri = uri
        self.username = username
        self.password = password
        self.database = database

        self.driver: AsyncDriver | None = None

    async def initialize(self) -> bool:
        """
        初始化数据库连接

        Returns:
            是否成功连接
        """
        try:
            self.driver = AsyncGraphDatabase.driver(
                self.uri,
                auth=(self.username, self.password),
            )

            # 测试连接
            async with self.driver.session(database=self.database) as session:
                result = await session.run("RETURN 1 as test")
                await result.single()

            logger.info(f"✅ 法律世界模型数据库连接成功: {self.uri}/{self.database}")
            return True

        except Exception as e:
            logger.error(f"❌ 法律世界模型数据库连接失败: {e}")
            return False

    async def close(self) -> None:
        """关闭数据库连接"""
        if self.driver:
            await self.driver.close()
            logger.info("✅ 法律世界模型数据库连接已关闭")

    @property
    def neo4j_session(self) -> AsyncSession:
        """
        获取Neo4j会话（上下文管理器）

        Returns:
            AsyncSession上下文管理器
        """
        if not self.driver:
            raise RuntimeError("数据库未初始化")

        return self.driver.session(database=self.database)

    async def execute_query(
        self,
        cypher: str,
        parameters: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]:
        """
        执行Cypher查询

        Args:
            cypher: Cypher查询语句
            parameters: 查询参数

        Returns:
            查询结果列表
        """
        async with self.neo4j_session as session:
            result = await session.run(cypher, parameters or {})
            records = await result.data()
            return records

    async def get_scenario_rules(
        self,
        domain: str | None = None,
        task_type: str | None = None,
        phase: str | None = None,
    ) -> list[dict[str, Any]:
        """
        获取场景规则

        Args:
            domain: 业务领域
            task_type: 任务类型
            phase: 业务阶段

        Returns:
            场景规则列表
        """
        cypher = """
            MATCH (sr:ScenarioRule)
            WHERE sr.is_active = true
        """

        params = {}
        conditions = []

        if domain:
            conditions.append("sr.domain = $domain")
            params["domain"] = domain

        if task_type:
            conditions.append("sr.task_type = $task_type")
            params["task_type"] = task_type

        if phase:
            conditions.append("sr.phase = $phase")
            params["phase"] = phase

        if conditions:
            cypher += " AND " + " AND ".join(conditions)

        cypher += """
            RETURN sr
            ORDER BY sr.version DESC
        """

        return await self.execute_query(cypher, params)

    async def get_legal_documents(
        self,
        domain: str | None = None,
        doc_type: str | None = None,
        limit: int = 100,
    ) -> list[dict[str, Any]:
        """
        获取法律文档

        Args:
            domain: 业务领域
            doc_type: 文档类型
            limit: 返回数量限制

        Returns:
            法律文档列表
        """
        cypher = """
            MATCH (d:LegalDocument)
            WHERE d.is_active = true
        """

        params = {"limit": limit}
        conditions = []

        if domain:
            conditions.append("d.domain = $domain")
            params["domain"] = domain

        if doc_type:
            conditions.append("d.doc_type = $doc_type")
            params["doc_type"] = doc_type

        if conditions:
            cypher += " AND " + " AND ".join(conditions)

        cypher += """
            RETURN d
            ORDER BY d.priority DESC, d.created_at DESC
            LIMIT $limit
        """

        return await self.execute_query(cypher, params)

    async def get_reference_cases(
        self,
        domain: str | None = None,
        case_type: str | None = None,
        limit: int = 50,
    ) -> list[dict[str, Any]:
        """
        获取参考案例

        Args:
            domain: 业务领域
            case_type: 案例类型
            limit: 返回数量限制

        Returns:
            参考案例列表
        """
        cypher = """
            MATCH (c:ReferenceCase)
            WHERE c.is_active = true
        """

        params = {"limit": limit}
        conditions = []

        if domain:
            conditions.append("c.domain = $domain")
            params["domain"] = domain

        if case_type:
            conditions.append("c.case_type = $case_type")
            params["case_type"] = case_type

        if conditions:
            cypher += " AND " + " AND ".join(conditions)

        cypher += """
            RETURN c
            ORDER BY c.relevance_score DESC, c.created_at DESC
            LIMIT $limit
        """

        return await self.execute_query(cypher, params)


# ========== 便捷函数 ==========

async def create_db_manager(
    uri: str = "bolt://localhost:7687",
    username: str = "neo4j",
    password: str = os.getenv("DB_PASSWORD", "password"),
    database: str = "legal_world",
) -> LegalWorldDBManager:
    """
    创建并初始化数据库管理器

    Args:
        uri: Neo4j URI
        username: 用户名
        password: 密码
        database: 数据库名称

    Returns:
        初始化完成的数据库管理器
    """
    manager = LegalWorldDBManager(
        uri=uri,
        username=username,
        password=password,
        database=database,
    )
    await manager.initialize()
    return manager


# ========== 导出 ==========

__all__ = [
    "LegalWorldDBManager",
    "create_db_manager",
]
