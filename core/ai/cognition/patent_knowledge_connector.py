from nebula3.gclient.net import GraphDatabase
from nebula3.gclient.net import GraphDatabase as session
from qdrant_client import QdrantClient

# pyright: ignore
# !/usr/bin/env python3
"""
专利知识库连接器
Patent Knowledge Base Connector

连接向量数据库(Qdrant)和知识图谱(Neo4j),为专利专家系统提供知识支持

作者: 小娜·天秤女神
创建时间: 2025-12-16
版本: v1.0 Knowledge Connector
"""

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from core.logging_config import setup_logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = setup_logging()


@dataclass
class KnowledgeQuery:
    """知识查询"""

    query_text: str
    query_type: str  # similarity, relationship, hybrid
    technology_field: str
    filters: dict[str, Any] = field(default_factory=dict)
    limit: int = 10


@dataclass
class KnowledgeResult:
    """知识检索结果"""

    query_id: str
    results: list[dict[str, Any]
    confidence_scores: list[float]
    query_time: float
    source_type: str
    metadata: dict[str, Any] = field(default_factory=dict)


class PatentKnowledgeConnector:
    """专利知识库连接器"""

    def __init__(self):
        self.name = "专利知识库连接器"
        self.version = "v1.0"

        # 数据库配置
        self.qdrant_config = {
            "host": "localhost",
            "port": 6333,
            "collection_name": "patent_vectors",
        }

        self.neo4j_config = {
            "uri": "bolt://localhost:7687",
            "user": "neo4j",
            "password": "xiaonuo_neo4j_2025",
        }

        # 缓存
        self.query_cache = {}
        self.embedding_cache = {}

        # 连接状态
        self.qdrant_client = None
        self.neo4j_driver = None

        self.is_initialized = False

    async def initialize(self):
        """初始化知识库连接"""
        logger.info("🔗 初始化专利知识库连接器...")

        try:
            await self._connect_qdrant()

            # 2. 连接Neo4j知识图谱
            await self._connect_neo4j()

            # 3. 初始化知识索引
            await self._initialize_knowledge_indexes()

            # 4. 加载专利知识映射
            await self._load_knowledge_mappings()

            self.is_initialized = True
            logger.info("✅ 专利知识库连接器初始化完成")

        except Exception as e:
            logger.error(f"❌ 知识库连接器初始化失败: {e!s}")
            # 允许在连接失败时继续运行,使用模拟数据
            self.is_initialized = True
            logger.warning("⚠️ 使用模拟知识库数据")

    async def search_similar_patents(self, query: KnowledgeQuery) -> KnowledgeResult:
        """搜索相似专利(向量检索)"""
        if not self.is_initialized:
            return await self._mock_similar_patents(query)

        logger.info(f"🔍 搜索相似专利: {query.query_text[:50]}...")
        datetime.now()

    async def search_patent_relationships(self, query: KnowledgeQuery) -> KnowledgeResult:
        """搜索专利关系(知识图谱)"""
        if not self.is_initialized:
            return await self._mock_patent_relationships(query)

        logger.info(f"🕸️ 搜索专利关系: {query.query_text[:50]}...")
        start_time = datetime.now()

        try:
            cypher_query = await self._build_cypher_query(query)

            # Neo4j图检索
            if self.neo4j_driver:
                graph_result = await self._neo4j_search(cypher_query, query)
            else:
                graph_result = await self._mock_neo4j_search(query)

            # 处理图数据
            processed_results = await self._process_graph_results(graph_result, query)

            query_time = (datetime.now() - start_time).total_seconds()

            result = KnowledgeResult(
                query_id=f"rel_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                results=processed_results,
                confidence_scores=[r.get("relevance", 0.0) for r in processed_results],
                query_time=query_time,
                source_type="knowledge_graph",
                metadata={"cypher_query": cypher_query, "graph_traversal": "relationship_search"},
            )

            logger.info(f"✅ 图检索完成,找到 {len(processed_results)} 个关系")
            return result

        except Exception:
            return await self._mock_patent_relationships(query)

    async def hybrid_search(self, query: KnowledgeQuery) -> KnowledgeResult:
        """混合检索(向量+图)"""
        logger.info(f"🔄 混合检索: {query.query_text[:50]}...")
        start_time = datetime.now()

        # 并行执行向量检索和图检索
        vector_task = self.search_similar_patents(query)
        graph_task = self.search_patent_relationships(query)

        vector_result, graph_result = await asyncio.gather(vector_task, graph_task)

        # 融合结果
        hybrid_results = await self._merge_results(vector_result, graph_result, query)

        query_time = (datetime.now() - start_time).total_seconds()

        result = KnowledgeResult(
            query_id=f"hybrid_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            results=hybrid_results,
            confidence_scores=[r.get("combined_score", 0.0) for r in hybrid_results],
            query_time=query_time,
            source_type="hybrid_search",
            metadata={
                "vector_results": len(vector_result.results),
                "graph_results": len(graph_result.results),
                "fusion_method": "weighted_average",
            },
        )

        logger.info(f"✅ 混合检索完成,融合得到 {len(hybrid_results)} 个结果")
        return result

    async def get_domain_knowledge(self, technology_field: str) -> dict[str, Any]:
        """获取领域专业知识"""
        logger.info(f"📚 获取领域知识: {technology_field}")

        # 构建领域查询
        domain_query = KnowledgeQuery(
            query_text=f"{technology_field} 专利专业知识",
            query_type="domain",
            technology_field=technology_field,
            limit=20,
        )

        # 执行混合检索
        domain_results = await self.hybrid_search(domain_query)

        # 提取和分类知识
        domain_knowledge = await self._extract_domain_knowledge(domain_results, technology_field)

        return domain_knowledge

    async def get_legal_precedents(
        self, legal_issue: str, technology_field: str = ""
    ) -> KnowledgeResult:
        """获取法律判例"""
        logger.info(f"⚖️ 获取法律判例: {legal_issue}")

        precedent_query = KnowledgeQuery(
            query_text=f"{legal_issue} {technology_field} 专利判例",
            query_type="precedent",
            technology_field=technology_field,
            limit=15,
        )

        return await self.hybrid_search(precedent_query)

    async def _connect_qdrant(self):
        """连接Qdrant向量数据库"""
        try:
            from qdrant_client.http.models import Distance, VectorParams

            self.qdrant_client = QdrantClient(
                host=self.qdrant_config.get("host"), port=self.qdrant_config.get("port")
            )

            # 检查集合是否存在
            collections = self.qdrant_client.get_collections().collections
            collection_names = [c.name for c in collections]

            if self.qdrant_config.get("collection_name") not in collection_names:
                # 创建集合
                self.qdrant_client.create_collection(
                    collection_name=self.qdrant_config.get("collection_name"),
                    vectors_config=VectorParams(size=768, distance=Distance.COSINE),
                )
                logger.info(f"✅ 创建Qdrant集合: {self.qdrant_config.get('collection_name')}")

            logger.info("✅ Qdrant连接成功")

        except ImportError:
            logger.warning(f"可选模块导入失败，使用降级方案: {e}")
        except Exception:
            self.qdrant_client = None

    async def _connect_neo4j(self):
        """连接Neo4j知识图谱"""
        try:

            self.neo4j_driver = GraphDatabase.driver(
                self.neo4j_config.get("uri"),
                auth=(self.neo4j_config.get("user"), self.neo4j_config.get("password")),
            )

            # 测试连接
            with self.neo4j_driver.session() as session:
                result = session.run("RETURN 1 as test")
                record = result.single()
                if record["test"] == 1:  # type: ignore
                    logger.info("✅ Neo4j连接成功")
                else:
                    raise Exception("Neo4j连接测试失败")

        except ImportError:
            logger.warning(f"可选模块导入失败，使用降级方案: {e}")
        except Exception:
            self.neo4j_driver = None

    async def _generate_embedding(self, text: str) -> list[float]:
        """生成文本嵌入向量"""
        # 简化实现:使用hash生成伪向量
        # 实际应用中应该使用真正的嵌入模型
        import hashlib

        text_hash = hashlib.md5(text.encode(), usedforsecurity=False).hexdigest()
        # 将hash转换为768维向量
        vector = []
        for i in range(0, len(text_hash), 2):
            hex_val = int(text_hash[i : i + 2], 16) / 255.0
            # 重复值以填充到768维
            for _ in range(24):  # 768 / 32 (hash长度)
                vector.append(hex_val)
            if len(vector) >= 768:
                break

        return vector[:768]

    async def _qdrant_search(self, query_vector: list[float], query: KnowledgeQuery) -> list[dict]:  # type: ignore
        """Qdrant向量检索"""

    async def _neo4j_search(self, cypher_query: str, query: KnowledgeQuery) -> list[dict]:  # type: ignore
        """Neo4j图检索"""
        try:
                result = session.run(cypher_query)
                records = result.data()

                return records

        except Exception:
            return []

    async def _build_cypher_query(self, query: KnowledgeQuery) -> str:
        """构建Cypher查询"""
        # 简化的Cypher查询构建
        base_query = f"""
        MATCH (p:Patent)-[r]->(related)
        WHERE p.technology_field CONTAINS '{query.technology_field}'
        AND (p.title CONTAINS '{query.query_text}' OR p.abstract CONTAINS '{query.query_text}')
        RETURN p, r, related
        LIMIT {query.limit}
        """
        return base_query

    async def _process_vector_results(
        self, results: list[dict], query: KnowledgeQuery  # type: ignore
    ) -> list[dict]:  # type: ignore
        """处理向量检索结果"""
        processed = []
        for result in results:
            payload = result.get("payload", {})
            processed.append(
                {
                    "id": result.get("id"),
                    "title": payload.get("title", ""),
                    "abstract": payload.get("abstract", ""),
                    "score": result.get("score", 0.0),
                    "publication_date": payload.get("publication_date", ""),
                    "applicant": payload.get("applicant", ""),
                    "ipc": payload.get("ipc", []),
                    "relevance_type": "similarity",
                }
            )
        return processed

    async def _process_graph_results(
        self, results: list[dict], query: KnowledgeQuery  # type: ignore
    ) -> list[dict]:  # type: ignore
        """处理图检索结果"""
        processed = []
        for result in results:
            patent_node = result.get("p", {})
            relationship = result.get("r", {})
            related_node = result.get("related", {})

            processed.append(
                {
                    "patent": patent_node,
                    "relationship": relationship,
                    "related": related_node,
                    "relevance": 0.8,  # 固定相关性,实际应该计算
                    "relationship_type": relationship.get("type", ""),
                    "relevance_type": "relationship",
                }
            )
        return processed

    async def _merge_results(
        self, vector_result: KnowledgeResult, graph_result: KnowledgeResult, query: KnowledgeQuery
    ) -> list[dict]:  # type: ignore
        """融合向量检索和图检索结果"""
        # 简化的融合策略:加权平均
        merged = []
        vector_weight = 0.7
        graph_weight = 0.3

        # 合并向量结果
        for v_result in vector_result.results:
            v_result["combined_score"] = v_result.get("score", 0.0) * vector_weight
            merged.append(v_result)

        # 合并图结果
        for g_result in graph_result.results:
            g_result["combined_score"] = g_result.get("relevance", 0.0) * graph_weight
            merged.append(g_result)

        # 去重并排序
        seen_ids = set()
        unique_results = []
        for result in merged:
            result_id = result.get("id", id(result))
            if result_id not in seen_ids:
                seen_ids.add(result_id)
                unique_results.append(result)

        unique_results.sort(key=lambda x: x.get("combined_score", 0.0), reverse=True)  # type: ignore
        return unique_results[: query.limit]

    async def _extract_domain_knowledge(
        self, results: KnowledgeResult, technology_field: str
    ) -> dict[str, Any]:
        """提取领域专业知识"""
        domain_knowledge = {
            "key_concepts": [],
            "common_issues": [],
            "success_patterns": [],
            "relevant_cases": [],
        }

        for result in results.results:
            if result.get("relevance_type") == "similarity":
                domain_knowledge["key_concepts"].append(
                    {
                        "concept": result.get("title", ""),
                        "description": result.get("abstract", "")[:200],
                        "relevance": result.get("combined_score", 0.0),
                    }
                )

            elif result.get("relevance_type") == "relationship":
                domain_knowledge["common_issues"].append(
                    {
                        "issue": result.get("relationship", {}).get("type", ""),
                        "context": str(result.get("patent", {}))[:100],
                        "relevance": result.get("relevance", 0.0),
                    }
                )

        return domain_knowledge

    # 模拟方法(当连接失败时使用)
    async def _mock_similar_patents(self, query: KnowledgeQuery) -> KnowledgeResult:
        """模拟相似专利检索"""
        mock_results = []
        for i in range(min(5, query.limit)):
            mock_results.append(
                {
                    "id": f"mock_patent_{i}",
                    "title": f"模拟专利 - {query.technology_field} - {i + 1}",
                    "abstract": f"这是关于{query.technology_field}的模拟专利描述,涉及{query.query_text}相关技术...",
                    "score": 0.8 - i * 0.1,
                    "publication_date": "2023-01-01",
                    "applicant": f"模拟公司{i + 1}",
                    "ipc": [f"G06F {i + 1}/00"],
                    "relevance_type": "similarity",
                }
            )

        return KnowledgeResult(
            query_id=f"mock_sim_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            results=mock_results,
            confidence_scores=[r.get("score", 0.0) for r in mock_results],
            query_time=0.1,
            source_type="mock_vector_database",
        )

    async def _mock_patent_relationships(self, query: KnowledgeQuery) -> KnowledgeResult:
        """模拟专利关系检索"""
        mock_results = []
        for i in range(min(3, query.limit)):
            mock_results.append(
                {
                    "patent": {"title": f"专利A{i + 1}", "id": f"patent_a_{i + 1}"},
                    "relationship": {"type": "引用", "strength": 0.7 - i * 0.1},
                    "related": {"title": f"专利B{i + 1}", "id": f"patent_b_{i + 1}"},
                    "relevance": 0.8 - i * 0.15,
                    "relationship_type": "引用",
                    "relevance_type": "relationship",
                }
            )

        return KnowledgeResult(
            query_id=f"mock_rel_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            results=mock_results,
            confidence_scores=[r.get("relevance", 0.0) for r in mock_results],
            query_time=0.1,
            source_type="mock_knowledge_graph",
        )

    async def _mock_qdrant_search(self, query: KnowledgeQuery) -> list[dict]:  # type: ignore
        """模拟Qdrant检索"""
        return await self._mock_similar_patents(query)

    async def _mock_neo4j_search(self, query: KnowledgeQuery) -> list[dict]:  # type: ignore
        """模拟Neo4j检索"""
        return await self._mock_patent_relationships(query)

    async def _initialize_knowledge_indexes(self):
        """初始化知识索引"""
        logger.info("📋 初始化知识索引...")
        # 这里可以初始化各种索引

    async def _load_knowledge_mappings(self):
        """加载知识映射"""
        logger.info("🗺️ 加载知识映射...")
        # 这里可以加载领域特定的知识映射

    async def cleanup(self):
        """清理连接资源"""
        if self.neo4j_driver:
            self.neo4j_driver.close()
        if self.qdrant_client:
            self.qdrant_client = None
        logger.info("🧹 知识库连接器资源清理完成")


# 导出主类
__all__ = ["KnowledgeQuery", "KnowledgeResult", "PatentKnowledgeConnector"]
