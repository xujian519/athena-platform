#!/usr/bin/env python3
from __future__ import annotations
"""
统一知识图谱模型
Unified Knowledge Graph Model

整合自:
- core/legal_world_model/legal_knowledge_graph_builder.py (法律知识图谱构建器)
- core/legal_kg/legal_kg_builder.py (法律知识图谱构建工具)
- core/knowledge/unified_knowledge_graph.py (统一知识图谱管理器)

功能:
- 支持PostgreSQL和Neo4j双后端
- 法律知识图谱构建
- 统一知识图谱管理
- 后端自动选择

作者: Athena平台团队
版本: v1.0.0
创建时间: 2026-04-21
"""

import asyncio
import logging
import os
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


# =============================================================================
# 后端类型定义
# =============================================================================

class GraphBackend(Enum):
    """图数据库后端类型"""

    NEO4J = "neo4j"  # Neo4j图数据库(推荐,统一选择)
    POSTGRESQL = "postgresql"  # PostgreSQL图存储(备用方案)
    HYBRID = "hybrid"  # 混合模式


# =============================================================================
# 配置数据类
# =============================================================================

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


# =============================================================================
# 法律知识图谱数据类
# =============================================================================

@dataclass
class PatentLaw:
    """专利法法条"""

    article: str
    title: str
    content: str
    keywords: list[str]
    category: str
    effective_date: str
    metadata: dict[str, Any] = None


@dataclass
class CasePrecedent:
    """案例先例"""

    case_id: str
    title: str
    issue: str  # 争议焦点
    outcome: str  # 裁判结果
    reasoning: str  # 裁判理由
    cited_articles: list[str]  # 引用法条
    date: str
    metadata: dict[str, Any] = None


@dataclass
class InferenceRule:
    """推理规则"""

    rule_id: str
    name: str
    conditions: list[str]  # 条件
    conclusion: str  # 结论
    confidence: float
    category: str  # 规则类别
    metadata: dict[str, Any] = None


@dataclass
class LegalEntity:
    """法律实体"""

    id: str
    type: str  # Law, Article, Concept, Organization, etc.
    name: str
    properties: dict


@dataclass
class LegalRelation:
    """法律关系"""

    source_id: str
    target_id: str
    relation_type: str
    properties: dict


# =============================================================================
# 统一知识图谱
# =============================================================================

class UnifiedKnowledgeGraph:
    """
    统一知识图谱管理器

    整合所有知识图谱功能:
    - 支持PostgreSQL和Neo4j双后端
    - 后端自动选择
    - 法律知识图谱构建
    - 统一API接口
    """

    def __init__(
        self,
        preferred_backend: GraphBackend = GraphBackend.NEO4J,
        neo4j_config: Neo4jConfig | None = None,
    ):
        """
        初始化知识图谱管理器

        Args:
            preferred_backend: 首选后端(默认Neo4j)
            neo4j_config: Neo4j配置(可选,默认从环境变量读取)
        """
        self.preferred_backend = preferred_backend
        self.pg_graph_store = None
        self.neo4j_driver = None
        self.backends_available: dict[GraphBackend, bool] = {}
        self.neo4j_config = neo4j_config or Neo4jConfig()
        self._initialized = False

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
            logger.info("✅ 使用PostgreSQL作为主要后端")
        elif neo4j_available:
            logger.info("✅ 使用Neo4j作为主要后端(自动选择)")
        elif pg_available:
            logger.info("✅ 使用PostgreSQL作为主要后端(自动选择)")
        else:
            raise RuntimeError("没有可用的图数据库后端")

        self._initialized = True
        logger.info("✅ 统一知识图谱管理器初始化完成")

    async def _init_neo4j(self) -> bool:
        """初始化Neo4j后端"""
        try:
            from neo4j import GraphDatabase

            self.neo4j_driver = GraphDatabase.driver(
                self.neo4j_config.uri,
                auth=(self.neo4j_config.username, self.neo4j_config.password)
            )

            # 测试连接
            with self.neo4j_driver.session(database=self.neo4j_config.database) as session:
                session.run("RETURN 1")

            logger.info("✅ Neo4j后端初始化成功")
            return True

        except Exception as e:
            logger.warning(f"⚠️ Neo4j后端初始化失败: {e}")
            return False

    async def _init_postgresql(self) -> bool:
        """初始化PostgreSQL图存储后端"""
        try:
            # 延迟导入以避免依赖问题
            try:
                from core.knowledge.storage.pg_graph_store import PGGraphStore
            except ImportError:
                return False

            self.pg_graph_store = PGGraphStore()
            await self.pg_graph_store.initialize()
            logger.info("✅ PostgreSQL图存储后端初始化成功")
            return True

        except Exception as e:
            logger.warning(f"⚠️ PostgreSQL图存储后端初始化失败: {e}")
            return False

    def get_active_backend(self) -> GraphBackend:
        """获取当前活跃的后端"""
        if self.preferred_backend == GraphBackend.NEO4J and self.backends_available.get(GraphBackend.NEO4J):
            return GraphBackend.NEO4J
        elif self.preferred_backend == GraphBackend.POSTGRESQL and self.backends_available.get(GraphBackend.POSTGRESQL):
            return GraphBackend.POSTGRESQL
        elif self.backends_available.get(GraphBackend.NEO4J):
            return GraphBackend.NEO4J
        elif self.backends_available.get(GraphBackend.POSTGRESQL):
            return GraphBackend.POSTGRESQL
        else:
            raise RuntimeError("没有可用的后端")

    async def get_statistics(self) -> GraphStatistics:
        """获取图统计信息"""
        backend = self.get_active_backend()

        if backend == GraphBackend.NEO4J and self.neo4j_driver:
            return await self._get_neo4j_statistics()
        elif backend == GraphBackend.POSTGRESQL and self.pg_graph_store:
            return await self._get_postgresql_statistics()
        else:
            return GraphStatistics(backend=backend, is_available=False)

    async def _get_neo4j_statistics(self) -> GraphStatistics:
        """获取Neo4j统计信息"""
        with self.neo4j_driver.session(database=self.neo4j_config.database) as session:
            # 节点数
            node_result = session.run("MATCH (n) RETURN count(n) as count")
            node_count = node_result.single()["count"]

            # 边数
            edge_result = session.run("MATCH ()-[r]->() RETURN count(r) as count")
            edge_count = edge_result.single()["count"]

            # 节点类型
            type_result = session.run("CALL db.labels() YIELD label RETURN label")
            tag_types = [record["label"] for record in type_result]

            # 关系类型
            rel_result = session.run("CALL db.relationshipTypes() YIELD relationshipType RETURN relationshipType")
            edge_types = [record["relationshipType"] for record in rel_result]

            return GraphStatistics(
                backend=GraphBackend.NEO4J,
                node_count=node_count,
                edge_count=edge_count,
                tag_types=tag_types,
                edge_types=edge_types,
                is_available=True
            )

    async def _get_postgresql_statistics(self) -> GraphStatistics:
        """获取PostgreSQL统计信息"""
        # TODO: 实现PostgreSQL统计信息获取
        return GraphStatistics(
            backend=GraphBackend.POSTGRESQL,
            is_available=True
        )

    async def add_node(self, node_id: str, node_type: str, properties: dict[str, Any]) -> bool:
        """添加节点"""
        backend = self.get_active_backend()

        if backend == GraphBackend.NEO4J and self.neo4j_driver:
            return await self._add_neo4j_node(node_id, node_type, properties)
        elif backend == GraphBackend.POSTGRESQL and self.pg_graph_store:
            return await self._add_postgresql_node(node_id, node_type, properties)
        else:
            raise RuntimeError("没有可用的后端")

    async def _add_neo4j_node(self, node_id: str, node_type: str, properties: dict[str, Any]) -> bool:
        """添加Neo4j节点"""
        with self.neo4j_driver.session(database=self.neo4j_config.database) as session:
            cypher = f"""
            MERGE (n:{node_type} {{id: $id}})
            SET n += $properties
            """
            session.run(cypher, {"id": node_id, "properties": properties})
            return True

    async def _add_postgresql_node(self, node_id: str, node_type: str, properties: dict[str, Any]) -> bool:
        """添加PostgreSQL节点"""
        return await self.pg_graph_store.add_node(
            node_id=node_id,
            node_type=node_type,
            name=properties.get("name", ""),
            content=properties.get("content", ""),
            properties=properties
        )

    async def add_relation(
        self,
        source_id: str,
        target_id: str,
        relation_type: str,
        properties: Optional[dict[str, Any]] = None
    ) -> bool:
        """添加关系"""
        backend = self.get_active_backend()

        if backend == GraphBackend.NEO4J and self.neo4j_driver:
            return await self._add_neo4j_relation(source_id, target_id, relation_type, properties or {})
        elif backend == GraphBackend.POSTGRESQL and self.pg_graph_store:
            return await self._add_postgresql_relation(source_id, target_id, relation_type, properties or {})
        else:
            raise RuntimeError("没有可用的后端")

    async def _add_neo4j_relation(
        self,
        source_id: str,
        target_id: str,
        relation_type: str,
        properties: dict[str, Any]
    ) -> bool:
        """添加Neo4j关系"""
        with self.neo4j_driver.session(database=self.neo4j_config.database) as session:
            cypher = f"""
            MATCH (source {{id: $source_id}})
            MATCH (target {{id: $target_id}})
            MERGE (source)-[r:{relation_type}]->(target)
            SET r += $properties
            """
            session.run(cypher, {
                "source_id": source_id,
                "target_id": target_id,
                "properties": properties
            })
            return True

    async def _add_postgresql_relation(
        self,
        source_id: str,
        target_id: str,
        relation_type: str,
        properties: dict[str, Any]
    ) -> bool:
        """添加PostgreSQL关系"""
        import uuid
        return await self.pg_graph_store.add_edge(
            edge_id=str(uuid.uuid4()),
            source_id=source_id,
            target_id=target_id,
            relation_type=relation_type,
            properties=properties
        )

    async def close(self):
        """关闭知识图谱"""
        if self.neo4j_driver:
            self.neo4j_driver.close()
        if self.pg_graph_store:
            await self.pg_graph_store.close()
        logger.info("🔌 统一知识图谱已关闭")


# =============================================================================
# 法律知识图谱构建器
# =============================================================================

class LegalKnowledgeGraphBuilder:
    """
    法律知识图谱构建器

    整合法律知识图谱构建功能
    """

    def __init__(
        self,
        neo4j_uri: str = "bolt://localhost:7687",
        neo4j_user: str = "neo4j",
        neo4j_password: str = os.getenv("NEO4J_PASSWORD", "athena_neo4j_2024"),
    ):
        """
        初始化知识图谱构建器

        Args:
            neo4j_uri: Neo4j连接URI
            neo4j_user: Neo4j用户名
            neo4j_password: Neo4j密码
        """
        # Neo4j连接
        try:
            from neo4j import GraphDatabase
            self.driver = GraphDatabase.driver(neo4j_uri, auth=(neo4j_user, neo4j_password))
            logger.info("✅ 法律知识图谱构建器初始化完成")
        except ImportError:
            self.driver = None
            logger.warning("⚠️ Neo4j未安装，法律知识图谱构建器功能不可用")

    async def add_patent_law(self, law: PatentLaw) -> bool:
        """
        添加专利法法条

        Args:
            law: 专利法法条

        Returns:
            是否成功
        """
        if not self.driver:
            return False

        with self.driver.session() as session:
            cypher = """
            MERGE (l:PatentLaw {article: $article})
            SET l.title = $title,
                l.content = $content,
                l.keywords = $keywords,
                l.category = $category,
                l.effective_date = $effective_date
            """
            session.run(cypher, {
                "article": law.article,
                "title": law.title,
                "content": law.content,
                "keywords": law.keywords,
                "category": law.category,
                "effective_date": law.effective_date
            })
            return True

    async def add_case_precedent(self, case: CasePrecedent) -> bool:
        """
        添加案例先例

        Args:
            case: 案例先例

        Returns:
            是否成功
        """
        if not self.driver:
            return False

        with self.driver.session() as session:
            cypher = """
            MERGE (c:CasePrecedent {case_id: $case_id})
            SET c.title = $title,
                c.issue = $issue,
                c.outcome = $outcome,
                c.reasoning = $reasoning,
                c.cited_articles = $cited_articles,
                c.date = $date
            """
            session.run(cypher, {
                "case_id": case.case_id,
                "title": case.title,
                "issue": case.issue,
                "outcome": case.outcome,
                "reasoning": case.reasoning,
                "cited_articles": case.cited_articles,
                "date": case.date
            })
            return True

    async def add_inference_rule(self, rule: InferenceRule) -> bool:
        """
        添加推理规则

        Args:
            rule: 推理规则

        Returns:
            是否成功
        """
        if not self.driver:
            return False

        with self.driver.session() as session:
            cypher = """
            MERGE (r:InferenceRule {rule_id: $rule_id})
            SET r.name = $name,
                r.conditions = $conditions,
                r.conclusion = $conclusion,
                r.confidence = $confidence,
                r.category = $category
            """
            session.run(cypher, {
                "rule_id": rule.rule_id,
                "name": rule.name,
                "conditions": rule.conditions,
                "conclusion": rule.conclusion,
                "confidence": rule.confidence,
                "category": rule.category
            })
            return True

    async def close(self):
        """关闭构建器"""
        if self.driver:
            self.driver.close()
            logger.info("🔌 法律知识图谱构建器已关闭")


# =============================================================================
# 兼容层
# =============================================================================

# 保持与旧版API的兼容性
async def get_unified_knowledge_graph(
    preferred_backend: GraphBackend = GraphBackend.NEO4J,
    neo4j_config: Neo4jConfig | None = None,
) -> UnifiedKnowledgeGraph:
    """
    获取统一知识图谱实例

    Args:
        preferred_backend: 首选后端
        neo4j_config: Neo4j配置

    Returns:
        统一知识图谱实例
    """
    kg = UnifiedKnowledgeGraph(
        preferred_backend=preferred_backend,
        neo4j_config=neo4j_config
    )
    await kg.initialize()
    return kg


# =============================================================================
# 测试代码
# =============================================================================

if __name__ == "__main__":
    async def test():
        print("🧪 测试统一知识图谱")
        print("=" * 80)

        # 初始化
        kg = await get_unified_knowledge_graph()

        # 获取统计信息
        stats = await kg.get_statistics()
        print(f"后端: {stats.backend.value}")
        print(f"节点数: {stats.node_count}")
        print(f"边数: {stats.edge_count}")

        # 关闭
        await kg.close()
        print("\n✅ 测试完成")

    asyncio.run(test())
