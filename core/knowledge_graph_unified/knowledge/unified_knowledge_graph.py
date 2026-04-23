#!/usr/bin/env python3

"""
统一知识图谱管理器
支持PostgreSQL和Neo4j双后端

v3.0.0: 统一使用Neo4j作为图数据库 (技术决策: TD-001)
"""

import asyncio
import logging
import os
from dataclasses import dataclass
from enum import Enum
from typing import Any, Optional

from neo4j import GraphDatabase

logger = logging.getLogger(__name__)


class GraphBackend(Enum):
    """图数据库后端类型"""

    NEO4J = "neo4j"  # Neo4j图数据库(推荐,统一选择)
    POSTGRESQL = "postgresql"  # PostgreSQL图存储(备用方案)
    HYBRID = "hybrid"  # 混合模式


@dataclass
class Neo4jConfig:
    """Neo4j配置"""

    uri: str = "bolt://localhost:7687"
    username: str = "neo4j"
    password: str = os.getenv("NEO4J_PASSWORD", "password")
    database: str = "neo4j"

    def __post_init__(self):
        """从环境变量读取配置"""
        self.uri = os.getenv("NEO4J_URI", self.uri)
        self.username = os.getenv("NEO4J_USERNAME", self.username)
        self.password = os.getenv("NEO4J_PASSWORD", self.password)
        self.database = os.getenv("NEO4J_DATABASE", self.database)


@dataclass
class GraphStatistics:
    """图统计信息"""

    backend: GraphBackend
    node_count: int = 0
    edge_count: int = 0
    tag_types: Optional[list[str]] = None
    edge_types: Optional[list[str]] = None
    is_available: bool = False


class UnifiedKnowledgeGraph:
    """统一知识图谱管理器"""

    def __init__(
        self,
        preferred_backend: GraphBackend = GraphBackend.NEO4J,
        neo4j_config: Optional[Neo4jConfig] = None,
    ):
        """初始化知识图谱管理器

        Args:
            preferred_backend: 首选后端(默认Neo4j)
            neo4j_config: Neo4j配置(可选,默认从环境变量读取)
        """
        self.preferred_backend = preferred_backend
        self.pg_graph_store = None
        self.neo4j_driver = None
        self.backends_available: dict[GraphBackend, bool]] = {}
        self.neo4j_config = neo4j_config or Neo4jConfig()

    async def initialize(self):
        """初始化知识图谱

        自动选择可用的后端:
        1. 优先使用Neo4j(推荐,统一图数据库)
        2. 如果Neo4j不可用,尝试PostgreSQL图存储
        3. 两者都不可用时抛出异常
        """
        logger.info("正在初始化统一知识图谱管理器...")

        # 尝试初始化Neo4j(优先)
        neo4j_available = await self._init_neo4j()
        self.backends_available[GraphBackend.NEO4J] = neo4j_available

        # 尝试初始化PostgreSQL图存储(备用)
        pg_available = await self._init_postgresql()
        self.backends_available[GraphBackend.POSTGRESQL] = pg_available

        # 选择可用后端
        if self.preferred_backend == GraphBackend.NEO4J and neo4j_available:
            logger.info("✅ 使用Neo4j作为主要后端")
        elif self.preferred_backend == GraphBackend.POSTGRESQL and pg_available:
            logger.info("✅ 使用PostgreSQL图存储作为主要后端")
        elif neo4j_available:
            logger.info("✅ 使用Neo4j作为主要后端(优先)")
            self.preferred_backend = GraphBackend.NEO4J
        elif pg_available:
            logger.info("✅ Neo4j不可用,使用PostgreSQL图存储")
            self.preferred_backend = GraphBackend.POSTGRESQL
        else:
            raise RuntimeError("❌ 所有图数据库后端都不可用")

        logger.info(f"📊 知识图谱后端: {self.preferred_backend.value}")

    async def _init_postgresql(self) -> bool:
        """初始化PostgreSQL图存储"""
        try:
            from core.knowledge.storage.pg_graph_store import PGGraphStore

            self.pg_graph_store = PGGraphStore()
            await self.pg_graph_store.initialize()

            logger.info("✅ PostgreSQL图存储初始化成功")
            return True

        except Exception as e:
            logger.warning(f"⚠️  PostgreSQL图存储初始化失败: {e}")
            return False

    async def _init_neo4j(self) -> bool:
        """初始化Neo4j"""
        try:
            # 创建Neo4j驱动
            self.neo4j_driver = GraphDatabase.driver(
                self.neo4j_config.uri,
                auth=(self.neo4j_config.username, self.neo4j_config.password),
            )

            # 测试连接
            with self.neo4j_driver.session(database=self.neo4j_config.database) as session:
                result = session.run("RETURN 'OK' as test")
                single_result = result.single()
                if single_result and single_result["test"] == "OK":
                    logger.info(f"✅ Neo4j连接成功 (uri: {self.neo4j_config.uri})")
                    return True

        except Exception as e:
            logger.warning(f"⚠️  Neo4j连接失败: {e}")
            logger.info("💡 提示: Neo4j为可选后端,PostgreSQL图存储可用")
            return False

    async def execute_query(self, query: str) -> Any:
        """执行图谱查询

        Args:
            query: 查询语句(Cypher)

        Returns:
            查询结果
        """
        if self.preferred_backend == GraphBackend.POSTGRESQL:
            return await self._execute_postgresql_query(query)
        elif self.preferred_backend == GraphBackend.NEO4J:
            return await self._execute_neo4j_query(query)
        else:
            raise ValueError(f"不支持的后端: {self.preferred_backend}")

    async def _execute_postgresql_query(self, query: str) -> Any:
        """在PostgreSQL上执行查询"""
        if not self.pg_graph_store:
            raise RuntimeError("PostgreSQL图存储未初始化")

        # 将类Cypher查询转换为SQL
        # 这里需要实现查询转换逻辑
        return await self.pg_graph_store.execute_query(query)

    async def _execute_neo4j_query(self, query: str) -> Any:
        """在Neo4j上执行查询"""
        if not self.neo4j_driver:
            raise RuntimeError("Neo4j未连接")

        with self.neo4j_driver.session(database=self.neo4j_config.database) as session:
            result = session.run(query)

            # 提取结果
            results = []
            for record in result:
                results.append(dict(record))

            return results

    async def get_statistics(self) -> GraphStatistics:
        """获取图统计信息"""
        if self.preferred_backend == GraphBackend.POSTGRESQL:
            return await self._get_postgresql_statistics()
        elif self.preferred_backend == GraphBackend.NEO4J:
            return await self._get_neo4j_statistics()
        else:
            return GraphStatistics(backend=self.preferred_backend, is_available=False)

    async def _get_postgresql_statistics(self) -> GraphStatistics:
        """获取PostgreSQL图统计"""
        # 实现PostgreSQL统计查询
        return GraphStatistics(
            backend=GraphBackend.POSTGRESQL, node_count=0, edge_count=0, is_available=True
        )

    async def _get_neo4j_statistics(self) -> GraphStatistics:
        """获取Neo4j统计"""
        try:
            with self.neo4j_driver.session(database=self.neo4j_config.database) as session:
                # 获取节点数量
                result = session.run("MATCH (n) RETURN COUNT(n) AS node_count")
                single_result = result.single()
                node_count = single_result["node_count"] if single_result else 0

                # 获取边数量
                result = session.run("MATCH ()-[r]->() RETURN COUNT(r) AS edge_count")
                single_result = result.single()
                edge_count = single_result["edge_count"] if single_result else 0

                # 获取标签类型
                result = session.run("CALL db.labels()")
                tag_types = [record["label"] for record in result]

                # 获取关系类型
                result = session.run("CALL db.relationshipTypes()")
                edge_types = [record["relationshipType"] for record in result]

                return GraphStatistics(
                    backend=GraphBackend.NEO4J,
                    node_count=node_count,
                    edge_count=edge_count,
                    tag_types=tag_types,
                    edge_types=edge_types,
                    is_available=True,
                )

        except Exception as e:
            logger.warning(f"获取Neo4j统计失败: {e}")
            return GraphStatistics(backend=GraphBackend.NEO4J, is_available=False)

    def get_available_backends(self) -> list[GraphBackend]:
        """获取可用的后端列表"""
        return [backend for backend, available in self.backends_available.items() if available]

    def is_backend_available(self, backend: GraphBackend) -> bool:
        """检查后端是否可用"""
        return self.backends_available.get(backend, False)

    async def close(self):
        """关闭所有连接"""
        if self.pg_graph_store:
            await self.pg_graph_store.close()

        if self.neo4j_driver:
            self.neo4j_driver.close()

        logger.info("✅ 知识图谱连接已关闭")


# 便捷函数
async def get_knowledge_graph(
    preferred_backend: GraphBackend = GraphBackend.NEO4J,
) -> UnifiedKnowledgeGraph:
    """获取知识图谱实例

    Args:
        preferred_backend: 首选后端(默认Neo4j)

    Returns:
        知识图谱实例
    """
    kg = UnifiedKnowledgeGraph(preferred_backend)
    await kg.initialize()
    return kg


if __name__ == "__main__":
    import asyncio

    async def main():
        print("=" * 80)
        print("统一知识图谱管理器测试")
        print("=" * 80)

        kg = await get_knowledge_graph()

        print(f"\n可用后端: {[b.value for b in kg.get_available_backends()]}")
        print(f"当前后端: {kg.preferred_backend.value}")

        stats = await kg.get_statistics()
        print("\n图统计信息:")
        print(f"  后端: {stats.backend.value}")
        print(f"  可用: {stats.is_available}")
        print(f"  节点数: {stats.node_count}")
        print(f"  边数: {stats.edge_count}")

        await kg.close()

    asyncio.run(main())

