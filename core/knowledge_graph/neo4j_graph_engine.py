#!/usr/bin/env python3
from __future__ import annotations
"""
Neo4j知识图谱引擎
使用Neo4j实现多知识图谱管理
"""

import logging
import sys
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any

from neo4j import GraphDatabase
from neo4j.exceptions import ServiceUnavailable

# 导入安全配置
sys.path.append(str(Path(__file__).parent.parent / "core"))
from security.env_config import get_neo4j_config

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class GraphType(Enum):
    """知识图谱类型"""
    LEGAL_RULES = "legal_rules"          # 法律规则
    PATENT_GUIDELINE = "patent_guideline"  # 审查指南
    PATENT_INVALIDATION = "patent_invalidation"  # 专利无效
    PATENT_REVIEW = "patent_review"      # 复审
    PATENT_JUDGMENT = "patent_judgment"  # 专利判决
    TRADEMARK = "trademark"              # 商标
    TECH_TERMS = "tech_terms"            # 技术术语

@dataclass
class GraphNode:
    """知识图谱节点"""
    id: str
    type: str
    properties: dict[str, Any]
    content: str | None = None
    embedding: list[float] | None = None
    metadata: dict[str, Any] | None = None

@dataclass
class GraphEdge:
    """知识图谱边"""
    from_node: str
    to_node: str
    relation_type: str
    properties: dict[str, Any]
    weight: float | None = 1.0
    confidence: float | None = 1.0

class Neo4jGraphEngine:
    """Neo4j知识图谱引擎"""

    def __init__(self, uri=None, username=None, password=None):
        """初始化图引擎

        Args:
            uri: Neo4j连接URI（可选，默认从环境变量读取）
            username: 用户名（可选，默认从环境变量读取）
            password: 密码（可选，默认从环境变量读取）
        """
        # 从环境变量读取配置（如果未提供参数）
        if uri is None or username is None or password is None:
            config = get_neo4j_config()
            uri = uri or config["uri"]
            username = username or config["username"]
            password = password or config["password"]

        self.driver = GraphDatabase.driver(uri, auth=(username, password))

        # 测试连接
        try:
            with self.driver.session() as session:
                session.run("RETURN 1")
            logger.info("✅ Neo4j连接成功")
        except ServiceUnavailable:
            logger.error("❌ Neo4j连接失败，请确保Neo4j已启动")
            raise

    def init_graph(self, graph_type: GraphType):
        """初始化图

        Args:
            graph_type: 图类型
        """
        with self.driver.session() as session:
            # 创建约束（如果不存在）
            constraints = [
                f"CREATE CONSTRAINT ON (n:{graph_type.value}) ASSERT n.id IS UNIQUE",
            ]

            for constraint in constraints:
                try:
                    session.run(constraint)
                    logger.debug(f"创建约束: {constraint}")
                except Exception as e:
                    logger.debug(f"约束可能已存在: {e}")

    def add_node(self, graph_type: GraphType, node: GraphNode):
        """添加节点

        Args:
            graph_type: 图类型
            node: 节点数据
        """
        self.init_graph(graph_type)

        # 构建Cypher查询
        label = graph_type.value
        properties = {
            "id": node.id,
            "type": node.type,
            "properties": node.properties,
            "content": node.content,
            "embedding": node.embedding,
            "metadata": node.metadata or {},
            "created_at": datetime.now().isoformat()
        }

        # 构建动态Cypher
        props_str = ", ".join([f"{k}: ${k}" for k in properties.keys()])
        cypher = f"""
        MERGE (n:{label} {{id: $id}})
        SET n += {{{props_str}}}
        """

        with self.driver.session() as session:
            session.run(cypher, properties)
            logger.debug(f"添加节点: {graph_type.value}/{node.id}")

    def add_edge(self, graph_type: GraphType, edge: GraphEdge):
        """添加边

        Args:
            graph_type: 图类型
            edge: 边数据
        """
        # 确保节点存在
        cypher = f"""
        MATCH (a:{graph_type.value} {{id: $from_id}})
        MATCH (b:{graph_type.value} {{id: $to_id}})
        MERGE (a)-[r:{edge.relation_type}]->(b)
        SET r += $properties
        SET r.weight = $weight
        SET r.confidence = $confidence
        SET r.created_at = $created_at
        """

        properties = {
            "from_id": edge.from_node,
            "to_id": edge.to_node,
            "relation_type": edge.relation_type,
            "properties": edge.properties,
            "weight": edge.weight,
            "confidence": edge.confidence,
            "created_at": datetime.now().isoformat()
        }

        with self.driver.session() as session:
            session.run(cypher, properties)
            logger.debug(f"添加边: {edge.from_node} -> {edge.to_node}")

    def query_nodes(self, graph_type: GraphType, filters: dict[str, Any], limit: int = 10):
        """查询节点

        Args:
            graph_type: 图类型
            filters: 过滤条件
            limit: 返回数量限制

        Returns:
            节点列表
        """
        label = graph_type.value

        # 构建WHERE条件
        where_clauses = []
        params = {"limit": limit}

        if filters.get("type"):
            where_clauses.append("n.type = $type")
            params["type"] = filters["type"]

        if filters.get("content"):
            where_clauses.append("toLower(n.content) CONTAINS toLower($content)")
            params["content"] = filters["content"]

        if filters.get("properties"):
            for key, value in filters["properties"].items():
                where_clauses.append(f"n.properties.{key} = $prop_{key}")
                params[f"prop_{key}"] = value

        where_str = " WHERE " + " AND ".join(where_clauses) if where_clauses else ""

        cypher = f"""
        MATCH (n:{label}){where_str}
        RETURN n
        LIMIT $limit
        """

        with self.driver.session() as session:
            result = session.run(cypher, params)
            nodes = [record["n"] for record in result]
            return nodes

    def traverse_graph(self, graph_type: GraphType, start_node: str,
                      direction: str = "any", max_depth: int = 3):
        """图遍历

        Args:
            graph_type: 图类型
            start_node: 起始节点ID
            direction: 方向 (inbound/outbound/any)
            max_depth: 最大深度

        Returns:
            遍历结果
        """
        label = graph_type.value

        if direction == "inbound":
            pattern = "<-[r]-"
        elif direction == "outbound":
            pattern = "-[r]->"
        else:  # any
            pattern = "-[r]-"

        cypher = f"""
        MATCH path = (start:{label} {{id: $start_id}}){pattern}*1..{max_depth}(end:{label})
        RETURN [node IN nodes(path) | node] as nodes,
               [rel IN relationships(path) | rel] as relationships,
               length(path) as depth
        LIMIT 100
        """

        with self.driver.session() as session:
            result = session.run(cypher, {"start_id": start_node})
            return list(result)

    def get_statistics(self, graph_type: GraphType):
        """获取图统计信息

        Args:
            graph_type: 图类型
        """
        label = graph_type.value

        with self.driver.session() as session:
            # 节点数
            node_result = session.run(f"MATCH (n:{label}) RETURN count(n) as count")
            node_count = node_result.single()["count"]

            # 边数
            edge_result = session.run(f"MATCH ()-[r]->() WHERE type(startNode(r)) = '{label}' RETURN count(r) as count")
            edge_count = edge_result.single()["count"]

            # 节点类型分布
            type_result = session.run(f"""
            MATCH (n:{label})
            RETURN n.type as type, count(n) as count
            ORDER BY count DESC
            """)
            type_distribution = [{"type": record["type"], "count": record["count"]}
                               for record in type_result]

            # 关系类型分布
            rel_result = session.run(f"""
            MATCH ()-[r]->()
            WHERE type(startNode(r)) = '{label}'
            RETURN type(r) as type, count(r) as count
            ORDER BY count DESC
            """)
            relation_distribution = [{"type": record["type"], "count": record["count"]}
                                   for record in rel_result]

            return {
                "graph_type": graph_type.value,
                "nodes": node_count,
                "edges": edge_count,
                "node_types": type_distribution,
                "relation_types": relation_distribution
            }

    def create_fulltext_index(self, graph_type: GraphType, properties: list[str]):
        """创建全文索引

        Args:
            graph_type: 图类型
            properties: 要索引的属性
        """
        label = graph_type.value

        with self.driver.session() as session:
            for prop in properties:
                try:
                    # Neo4j 5.x 全文索引
                    session.run(f"""
                    CREATE FULLTEXT INDEX {label}_{prop}_index
                    FOR (n:{label})
                    ON EACH [n.{prop}]
                    """)
                    logger.info(f"创建全文索引: {label}.{prop}")
                except Exception as e:
                    logger.warning(f"索引可能已存在: {e}")

# 全局实例
graph_engine = Neo4jGraphEngine()
