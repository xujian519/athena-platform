#!/usr/bin/env python3
from __future__ import annotations
"""
Athena知识图谱引擎
基于ArangoDB的多知识图谱管理系统
"""

import json
import logging
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any

# ArangoDB Python驱动
from arango import ArangoClient

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
    type: str  # 节点类型
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

class ArangoGraphEngine:
    """ArangoDB知识图谱引擎"""

    def __init__(self, host="http://localhost:8529", username="root", password=""):
        """初始化图引擎

        Args:
            host: ArangoDB连接地址
            username: 用户名
            password: 密码
        """
        self.client = ArangoClient(hosts=host)

        # 连接系统数据库
        sys_db = self.client.db("_system", username=username, password=password)

        # 创建主数据库
        if not sys_db.has_database("athena_kg"):
            sys_db.create_database("athena_kg")
            logger.info("✅ 创建Athena知识图谱数据库")

        # 连接知识图谱数据库
        self.db = self.client.db("athena_kg", username=username, password=password)

        # 初始化图集合
        self._init_collections()

        logger.info("✅ ArangoDB知识图谱引擎初始化完成")

    def _init_collections(self):
        """初始化所有图集合"""
        # 为每个知识图谱类型创建集合
        for graph_type in GraphType:
            # 节点集合
            node_collection = f"{graph_type.value}_nodes"
            if not self.db.has_collection(node_collection):
                self.db.create_collection(node_collection)
                logger.info(f"✅ 创建节点集合: {node_collection}")

            # 边集合
            edge_collection = f"{graph_type.value}_edges"
            if not self.db.has_collection(edge_collection):
                self.db.create_collection(edge_collection, edge=True)
                logger.info(f"✅ 创建边集合: {edge_collection}")

    def create_graph(self, graph_type: GraphType):
        """创建知识图谱

        Args:
            graph_type: 图类型
        """
        graph_name = graph_type.value
        node_collection = f"{graph_name}_nodes"
        edge_collection = f"{graph_name}_edges"

        # 创建图定义
        if not self.db.has_graph(graph_name):
            self.db.create_graph(
                graph_name,
                edge_definitions=[{
                    "edge_collection": edge_collection,
                    "from_vertex_collections": [node_collection],
                    "to_vertex_collections": [node_collection]
                }]
            )
            logger.info(f"✅ 创建知识图谱: {graph_name}")

    def add_node(self, graph_type: GraphType, node: GraphNode):
        """添加节点

        Args:
            graph_type: 图类型
            node: 节点数据
        """
        collection_name = f"{graph_type.value}_nodes"
        collection = self.db.collection(collection_name)

        # 添加时间戳
        node.metadata = node.metadata or {}
        node.metadata["created_at"] = datetime.now().isoformat()

        # 插入文档
        doc = {
            "_key": node.id,
            "type": node.type,
            "properties": node.properties,
            "content": node.content,
            "embedding": node.embedding,
            "metadata": node.metadata
        }

        try:
            result = collection.insert(doc)
            logger.debug(f"添加节点: {graph_type.value}/{node.id}")
            return result
        except Exception as e:
            logger.error(f"添加节点失败: {e}")
            return None

    def add_edge(self, graph_type: GraphType, edge: GraphEdge):
        """添加边

        Args:
            graph_type: 图类型
            edge: 边数据
        """
        collection_name = f"{graph_type.value}_edges"
        collection = self.db.collection(collection_name)

        doc = {
            "_from": f"{graph_type.value}_nodes/{edge.from_node}",
            "_to": f"{graph_type.value}_nodes/{edge.to_node}",
            "relation_type": edge.relation_type,
            "properties": edge.properties,
            "weight": edge.weight,
            "confidence": edge.confidence,
            "created_at": datetime.now().isoformat()
        }

        try:
            result = collection.insert(doc)
            logger.debug(f"添加边: {edge.from_node} -> {edge.to_node}")
            return result
        except Exception as e:
            logger.error(f"添加边失败: {e}")
            return None

    def query_nodes(self, graph_type: GraphType, query: dict[str, Any], limit: int = 10):
        """查询节点

        Args:
            graph_type: 图类型
            query: 查询条件
            limit: 返回数量限制
        """
        collection_name = f"{graph_type.value}_nodes"

        # 构建AQL查询
        aql = f"""
        FOR doc IN {collection_name}
            """

        # 添加过滤条件
        if query:
            filters = []
            for key, value in query.items():
                if key == "content":
                    filters.append(f"LIKE(doc.content, '%{value}%')")
                elif key == "type":
                    filters.append(f"doc.type == '{value}'")
                else:
                    filters.append(f"doc.properties.{key} == '{value}'")

            if filters:
                aql += " FILTER " + " AND ".join(filters)

        aql += f" LIMIT {limit} RETURN doc"

        try:
            cursor = self.db.aql.execute(aql)
            results = list(cursor)
            return results
        except Exception as e:
            logger.error(f"查询节点失败: {e}")
            return []

    def traverse_graph(self, graph_type: GraphType, start_node: str,
                      direction: str = "any", max_depth: int = 3):
        """图遍历

        Args:
            graph_type: 图类型
            start_node: 起始节点ID
            direction: 方向 (inbound/outbound/any)
            max_depth: 最大深度
        """
        graph_name = graph_type.value

        # 构建遍历AQL
        if direction == "any":
            filter_dir = "ANY"
        elif direction == "inbound":
            filter_dir = "INBOUND"
        else:
            filter_dir = "OUTBOUND"

        aql = f"""
        FOR v, e, p IN 1..{max_depth} {filter_dir} '{graph_name}_nodes/{start_node}'
        GRAPH '{graph_name}'
        OPTIONS {{ uniqueVertices: 'global' }}
        RETURN {{
            vertex: v,
            edge: e,
            path: p,
            depth: LENGTH(p.vertices) - 1
        }}
        """

        try:
            cursor = self.db.aql.execute(aql)
            results = list(cursor)
            return results
        except Exception as e:
            logger.error(f"图遍历失败: {e}")
            return []

    def get_graph_statistics(self, graph_type: GraphType):
        """获取图统计信息

        Args:
            graph_type: 图类型
        """
        graph_name = graph_type.value
        node_collection = f"{graph_name}_nodes"
        edge_collection = f"{graph_name}_edges"

        try:
            # 节点数量
            node_count = self.db.collection(node_collection).count()
            # 边数量
            edge_count = self.db.collection(edge_collection).count()

            # 节点类型分布
            node_type_aql = f"""
            FOR doc IN {node_collection}
            COLLECT type = doc.type WITH COUNT INTO count
            RETURN {{ type, count }}
            """

            cursor = self.db.aql.execute(node_type_aql)
            type_distribution = list(cursor)

            # 边类型分布
            edge_type_aql = f"""
            FOR doc IN {edge_collection}
            COLLECT type = doc.relation_type WITH COUNT INTO count
            RETURN {{ type, count }}
            """

            cursor = self.db.aql.execute(edge_type_aql)
            relation_distribution = list(cursor)

            return {
                "graph_type": graph_name,
                "nodes": node_count,
                "edges": edge_count,
                "node_types": type_distribution,
                "relation_types": relation_distribution
            }
        except Exception as e:
            logger.error(f"获取统计信息失败: {e}")
            return None

    def export_graph(self, graph_type: GraphType, output_path: str):
        """导出图数据

        Args:
            graph_type: 图类型
            output_path: 输出文件路径
        """
        try:
            # 导出节点
            nodes = self.query_nodes(graph_type, {}, limit=10000)

            # 导出边
            edge_collection = f"{graph_type.value}_edges"
            edges = self.db.collection(edge_collection).all()

            graph_data = {
                "graph_type": graph_type.value,
                "nodes": nodes,
                "edges": edges,
                "exported_at": datetime.now().isoformat()
            }

            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(graph_data, f, ensure_ascii=False, indent=2)

            logger.info(f"✅ 导出图数据到: {output_path}")
            return True
        except Exception as e:
            logger.error(f"导出失败: {e}")
            return False

# 全局实例
graph_engine = ArangoGraphEngine()
