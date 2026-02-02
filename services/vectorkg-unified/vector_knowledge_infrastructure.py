#!/usr/bin/env python3
"""
向量+知识图谱统一基础设施
Vector + Knowledge Graph Unified Infrastructure

作为项目的核心智能后端，为专利等专业应用提供统一的向量检索和知识推理能力

作者: 小诺·双鱼公主
创建时间: 2024年12月15日
"""

import asyncio
from core.async_main import async_main
import logging
from core.logging_config import setup_logging
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
import json

# 向量数据库
try:
    from qdrant_client import QdrantClient
    from qdrant_client.models import Distance, VectorParams, PointStruct
    HAS_QDRANT = True
except ImportError:
    HAS_QDRANT = False

# 知识图谱
import sqlite3
import networkx as nx
import numpy as np

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = setup_logging()

@dataclass
class VectorCollection:
    """向量集合配置"""
    name: str
    vector_size: int
    distance: str
    description: str

@dataclass
class KnowledgeGraph:
    """知识图谱配置"""
    name: str
    type: str  # sqlite, networkx, neo4j
    path: str
    description: str

class VectorKnowledgeInfrastructure:
    """向量+知识图谱统一基础设施"""

    def __init__(self):
        """初始化基础设施"""
        # 向量库配置
        self.vector_collections = [
            VectorCollection(
                name="patent_legal_vectors_1024",
                vector_size=1024,
                distance=Distance.COSINE,
                description="专利法律法规1024维向量"
            ),
            VectorCollection(
                name="patent_guideline",
                vector_size=768,
                distance=Distance.COSINE,
                description="专利审查指南768维向量"
            ),
            VectorCollection(
                name="technical_patents_1024",
                vector_size=1024,
                distance=Distance.COSINE,
                description="技术专利1024维向量"
            ),
            VectorCollection(
                name="innovation_vectors_1024",
                vector_size=1024,
                distance=Distance.COSINE,
                description="创新概念1024维向量"
            )
        ]

        # 知识图谱配置
        self.knowledge_graphs = [
            KnowledgeGraph(
                name="patent_sqlite_kg",
                type="sqlite",
                path="/Users/xujian/Athena工作平台/data/knowledge_graph_sqlite/databases/patent_knowledge_graph.db",
                description="SQLite专利知识图谱(125万+实体)"
            ),
            KnowledgeGraph(
                name="patent_legal_kg",
                type="networkx",
                path="/Users/xujian/Athena工作平台/data/patent_legal_kg_simple",
                description="专利法律法规知识图谱(45个实体)"
            ),
            KnowledgeGraph(
                name="technical_kg",
                type="networkx",
                path="/Users/xujian/Athena工作平台/data/technical_kg",
                description="技术知识图谱"
            )
        ]

        # 初始化连接
        self.vector_client = None
        self.graph_connections = {}
        self.cache = {}

        logger.info("向量+知识图谱统一基础设施初始化完成")

    async def initialize(self):
        """初始化所有连接"""
        logger.info("初始化基础设施连接...")

        # 连接向量库
        if HAS_QDRANT:
            self.vector_client = QdrantClient(host="localhost", port=6333)
            logger.info("✅ Qdrant向量库已连接")
        else:
            logger.warning("Qdrant未安装，向量功能受限")

        # 连接知识图谱
        await self._connect_knowledge_graphs()
        logger.info("✅ 知识图谱已连接")

    async def _connect_knowledge_graphs(self):
        """连接所有知识图谱"""
        for kg in self.knowledge_graphs:
            if kg.type == "sqlite":
                conn = sqlite3.connect(kg.path)
                self.graph_connections[kg.name] = conn
                logger.info(f"✅ SQLite知识图谱已连接: {kg.name}")

            elif kg.type == "networkx":
                try:
                    graph_path = Path(kg.path) / "knowledge_graph.graphml"
                    if graph_path.exists():
                        graph = nx.read_graphml(str(graph_path))
                    else:
                        graph = self._load_networkx_from_json(kg.path)
                    self.graph_connections[kg.name] = graph
                    logger.info(f"✅ NetworkX知识图谱已加载: {kg.name}")
                except Exception as e:
                    logger.warning(f"NetworkX知识图谱加载失败: {kg.name} - {e}")

    def _load_networkx_from_json(self, path: str) -> Any:
        """从JSON加载NetworkX图"""
        graph = nx.DiGraph()

        entities_path = Path(path) / "entities.json"
        relations_path = Path(path) / "relationships.json"

        if entities_path.exists() and relations_path.exists():
            with open(entities_path, 'r', encoding='utf-8') as f:
                entities = json.load(f)
            with open(relations_path, 'r', encoding='utf-8') as f:
                relations = json.load(f)

            # 添加节点
            for entity in entities.values():
                graph.add_node(
                    entity['id'],
                    name=entity.get('name', ''),
                    type=entity.get('type', ''),
                    **entity.get('properties', {})
                )

            # 添加边
            for rel in relations:
                graph.add_edge(
                    rel['source'],
                    rel['target'],
                    type=rel.get('type', ''),
                    **rel.get('properties', {})
                )

        return graph

    async def hybrid_search(
        self,
        query_text: str,
        vector_threshold: float = 0.7,
        max_vector_results: int = 10,
        max_graph_paths: int = 5,
        collections: List[str] = None
    ) -> Dict[str, Any]:
        """
        混合搜索：向量检索 + 知识图谱推理
        """
        results = {
            "vector_results": [],
            "graph_results": [],
            "hybrid_insights": [],
            "timestamp": datetime.now().isoformat()
        }

        # 1. 向量检索
        if self.vector_client and collections:
            results["vector_results"] = await self._vector_search(
                query_text=query_text,
                collections=collections,
                threshold=vector_threshold,
                max_results=max_vector_results
            )

        # 2. 知识图谱搜索
        results["graph_results"] = await self._graph_search(
            query_text=query_text,
            max_paths=max_graph_paths
        )

        # 3. 混合分析
        results["hybrid_insights"] = self._analyze_hybrid_results(
            query_text=query_text,
            vector_results=results["vector_results"],
            graph_results=results["graph_results"]
        )

        return results

    async def _vector_search(
        self,
        query_text: str,
        collections: List[str],
        threshold: float = 0.7,
        max_results: int = 10
    ) -> List[Dict]:
        """向量检索"""
        results = []

        # 将查询文本转换为向量（简化版）
        query_vector = self._text_to_vector(query_text)

        for collection_name in (collections or self._get_default_collections()):
            try:
                search_result = self.vector_client.search(
                    collection_name=collection_name,
                    query_vector=query_vector,
                    limit=max_results,
                    score_threshold=threshold
                )

                for hit in search_result:
                    results.append({
                        "collection": collection_name,
                        "id": hit.id,
                        "score": hit.score,
                        "content": hit.payload.get('content', ''),
                        "metadata": hit.payload
                    })
            except Exception as e:
                logger.warning(f"向量搜索失败 {collection_name}: {e}")

        # 按相似度排序
        results.sort(key=lambda x: x['score'], reverse=True)
        return results[:max_results]

    async def _graph_search(self, query_text: str, max_paths: int = 5) -> List[Dict]:
        """知识图谱搜索"""
        results = []

        # 提取查询关键词
        keywords = self._extract_keywords(query_text)

        # 在所有知识图谱中搜索
        for kg_name, graph in self.graph_connections.items():
            if isinstance(graph, nx.DiGraph):
                graph_results = self._search_in_graph(graph, keywords, kg_name, max_paths)
                results.extend(graph_results)

        return results

    def _search_in_graph(self, graph: nx.DiGraph, keywords: List[str], graph_name: str, max_paths: int) -> List[Dict]:
        """在单个图中搜索"""
        results = []

        # 查找匹配的节点
        matched_nodes = []
        for node_id, data in graph.nodes(data=True):
            node_text = f"{data.get('name', '')} {data.get('description', '')}".lower()
            if any(keyword.lower() in node_text for keyword in keywords):
                matched_nodes.append((node_id, data))

        # 为每个匹配节点查找相关路径
        for node_id, data in matched_nodes[:max_paths]:
            # 获取入边和出边
            in_edges = list(graph.in_edges(node_id, data=True))
            out_edges = list(graph.out_edges(node_id, data=True))

            result = {
                "graph": graph_name,
                "node": {
                    "id": node_id,
                    "name": data.get('name', ''),
                    "type": data.get('type', ''),
                    "description": data.get('description', '')
                },
                "relations": {
                    "incoming": in_edges[:5],  # 限制数量
                    "outgoing": out_edges[:5]
                },
                "centrality": {
                    "in_degree": graph.in_degree(node_id),
                    "out_degree": graph.out_degree(node_id),
                    "betweenness": nx.betweenness_centrality(graph, node_id)
                }
            }
            results.append(result)

        return results

    def _analyze_hybrid_results(
        self,
        query_text: str,
        vector_results: List[Dict],
        graph_results: List[Dict]
    ) -> List[Dict]:
        """分析混合搜索结果"""
        insights = []

        # 1. 向量-图谱关联分析
        vector_graph_links = self._find_vector_graph_links(vector_results, graph_results)
        if vector_graph_links:
            insights.extend(vector_graph_links)

        # 2. 综合评分
        combined_score = self._calculate_combined_score(vector_results, graph_results)
        insights.append({
            "type": "combined_score",
            "score": combined_score,
            "vector_count": len(vector_results),
            "graph_count": len(graph_results)
        })

        # 3. 推荐洞察
        recommendations = self._generate_recommendations(query_text, vector_results, graph_results)
        if recommendations:
            insights.extend(recommendations)

        return insights

    def _find_vector_graph_links(self, vector_results: List[Dict], graph_results: List[Dict]) -> List[Dict]:
        """找到向量结果和图谱结果的关联"""
        links = []
        vector_content = " ".join([r.get('content', '') for r in vector_results[:5]])
        graph_entities = [r['node']['name'] for r in graph_results]

        # 简化的关联检测
        for entity in graph_entities:
            if entity.lower() in vector_content.lower():
                links.append({
                    "type": "entity_mention",
                    "entity": entity,
                    "vector_content_snippet": vector_content[:100] + "..."
                })

        return links

    def _calculate_combined_score(self, vector_results: List[Dict], graph_results: List[Dict]) -> float:
        """计算综合评分"""
        vector_score = sum(r['score'] for r in vector_results) / len(vector_results) if vector_results else 0
        graph_score = sum(1 for r in graph_results if r['centrality']['betweenness'] > 0) / len(graph_results) if graph_results else 0

        return (vector_score * 0.6 + graph_score * 0.4)

    def _generate_recommendations(self, query_text: str, vector_results: List[Dict], graph_results: List[Dict]) -> List[Dict]:
        """生成推荐"""
        recommendations = []

        # 基于查询意图推荐
        if "审查" in query_text or "判断" in query_text:
            if vector_results:
                recommendations.append({
                    "type": "review_guidance",
                    "message": "根据相似案例，建议关注新颖性和创造性判断"
                })

        if "侵权" in query_text or "风险" in query_text:
            if graph_results:
                recommendations.append({
                    "type": "legal_risk",
                    "message": "建议参考相关法条和判例进行风险评估"
                })

        return recommendations

    def _text_to_vector(self, text: str) -> List[float]:
        """文本转向量（简化版，实际应使用embedding模型）"""
        import hashlib

        hash_obj = hashlib.md5(text.encode('utf-8', usedforsecurity=False)
        vector = []
        for i in range(1024):  # 假设1024维
            byte_idx = i % 16
            vector.append(ord(hash_obj.digest()[byte_idx]) / 255.0)

        # 归一化
        import numpy as np
        vector = np.array(vector)
        norm = np.linalg.norm(vector)
        if norm > 0:
            vector = vector / norm

        return vector.tolist()

    def _extract_keywords(self, text: str) -> List[str]:
        """提取关键词"""
        # 使用简单的分词（实际应使用jieba）
        words = text.lower().split()
        # 过滤停用词
        stop_words = {'的', '是', '在', '有', '和', '与', '了', '等'}
        keywords = [w for w in words if w not in stop_words and len(w) > 1]

        # 去重并限制数量
        return list(set(keywords))[:20]

    def _get_default_collections(self) -> List[str]:
        """获取默认向量集合"""
        return [c.name for c in self.vector_collections if c.vector_size == 1024]

    async def get_infrastructure_stats(self) -> Dict[str, Any]:
        """获取基础设施统计"""
        stats = {
            "vector_collections": {
                "total": len(self.vector_collections),
                "details": []
            },
            "knowledge_graphs": {
                "total": len(self.knowledge_graphs),
                "details": []
            },
            "capabilities": {
                "vector_search": HAS_QDRANT,
                "graph_traversal": True,
                "hybrid_search": True,
                "real_time_query": True
            }
        }

        # 收集向量库统计
        if self.vector_client:
            for collection in self.vector_collections:
                try:
                    collection_info = self.vector_client.get_collection(collection.name)
                    stats["vector_collections"]["details"].append({
                        "name": collection.name,
                        "vector_size": collection.vector_size,
                        "points_count": collection_info.points_count,
                        "distance": collection.distance
                    })
                except Exception as e:
                    logger.warning(f"获取集合信息失败 {collection.name}: {e}")

        # 收集知识图谱统计
        for kg in self.knowledge_graphs:
            if kg.type == "sqlite" and kg.name in self.graph_connections:
                conn = self.graph_connections[kg.name]
                cursor = conn.cursor()
                try:
                    cursor.execute("SELECT COUNT(*) FROM patent_entities")
                    entity_count = cursor.fetchone()[0]
                    cursor.execute("SELECT COUNT(*) FROM patent_relations")
                    relation_count = cursor.fetchone()[0]

                    stats["knowledge_graphs"]["details"].append({
                        "name": kg.name,
                        "type": kg.type,
                        "entity_count": entity_count,
                        "relation_count": relation_count
                    })
                except Exception as e:
                    logger.warning(f"获取SQLite统计失败 {kg.name}: {e}")

            elif kg.type == "networkx" and kg.name in self.graph_connections:
                graph = self.graph_connections[kg.name]
                if isinstance(graph, nx.DiGraph):
                    stats["knowledge_graphs"]["details"].append({
                        "name": kg.name,
                        "type": kg.type,
                        "node_count": graph.number_of_nodes(),
                        "edge_count": graph.number_of_edges(),
                        "density": nx.density(graph)
                    })

        return stats

    def close(self) -> Any:
        """关闭连接"""
        # 关闭SQLite连接
        for conn in self.graph_connections.values():
            if hasattr(conn, 'close'):
                conn.close()

        logger.info("向量+知识图谱基础设施连接已关闭")

# 全局实例
_infrastructure = None

async def get_vector_knowledge_infrastructure():
    """获取基础设施实例"""
    global _infrastructure
    if _infrastructure is None:
        _infrastructure = VectorKnowledgeInfrastructure()
        await _infrastructure.initialize()
    return _infrastructure

# 使用示例
async def main():
    """使用示例"""
    # 获取基础设施
    infra = await get_vector_knowledge_infrastructure()

    # 混合搜索
    results = await infra.hybrid_search(
        query_text="基于深度学习的图像识别方法",
        vector_threshold=0.7,
        max_vector_results=5,
        max_graph_paths=3
    )

    print("=== 混合搜索结果 ===")
    print(f"向量结果数: {len(results['vector_results'])}")
    print(f"图谱结果数: {len(results['graph_results'])}")
    print(f"混合洞察: {len(results['hybrid_insights'])}")

    # 获取统计
    stats = await infra.get_infrastructure_stats()
    print("\n=== 基础设施统计 ===")
    print(f"向量集合: {stats['vector_collections']['total']}")
    print(f"知识图谱: {stats['knowledge_graphs']['total']}")

    # 关闭连接
    infra.close()

# 入口点: @async_main装饰器已添加到main函数