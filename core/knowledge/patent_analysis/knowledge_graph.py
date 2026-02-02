#!/usr/bin/env python3
"""
专利知识图谱
Patent Knowledge Graph

专利领域知识图谱构建和查询功能
基于 PostgreSQL (结构化存储) + Qdrant (向量检索) 的混合架构

作者: Athena AI系统
创建时间: 2025-12-04
更新时间: 2025-12-21
版本: 3.1.0 (PostgreSQL + Vector Enhanced)
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

from core.embedding.unified_embedding_service import ModuleType, UnifiedEmbeddingService
from core.knowledge.storage.pg_graph_store import PGGraphStore
from core.vector.qdrant_adapter import QdrantVectorAdapter

logger = logging.getLogger(__name__)


class NodeType(Enum):
    """节点类型"""

    PATENT = "patent"  # 专利
    TECHNOLOGY = "technology"  # 技术
    COMPANY = "company"  # 公司
    INVENTOR = "inventor"  # 发明人
    CATEGORY = "category"  # 分类
    KEYWORD = "keyword"  # 关键词
    LEGAL_CASE = "legal_case"  # 法律案例
    PRIOR_ART = "prior_art"  # 现有技术
    ARTICLE = "article"  # 法律条款 (新增)
    CONCEPT = "concept"  # 法律/专利概念 (新增)


class RelationType(Enum):
    """关系类型"""

    CITES = "cites"  # 引用
    SIMILAR_TO = "similar_to"  # 相似
    INVENTED_BY = "invented_by"  # 发明
    ASSIGNED_TO = "assigned_to"  # 转让
    BELONGS_TO = "belongs_to"  # 属于
    RELATED_TO = "related_to"  # 相关
    PRECEDES = "precedes"  # 先于
    IMPROVES = "improves"  # 改进
    DEFINES = "defines"  # 定义 (新增)
    CONTAINS = "contains"  # 包含 (新增)


@dataclass
class KnowledgeNode:
    """知识节点"""

    node_id: str
    node_type: NodeType | str
    title: str
    description: str
    properties: dict[str, Any]
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> dict[str, Any]:
        return {
            "node_id": self.node_id,
            "node_type": (
                self.node_type.value if isinstance(self.node_type, NodeType) else self.node_type
            ),
            "title": self.title,
            "description": self.description,
            "properties": self.properties,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }


@dataclass
class KnowledgeRelation:
    """知识关系"""

    relation_id: str
    source_id: str
    target_id: str
    relation_type: RelationType | str
    weight: float
    properties: dict[str, Any]
    created_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> dict[str, Any]:
        return {
            "relation_id": self.relation_id,
            "source_id": self.source_id,
            "target_id": self.target_id,
            "relation_type": (
                self.relation_type.value
                if isinstance(self.relation_type, RelationType)
                else self.relation_type
            ),
            "weight": self.weight,
            "properties": self.properties,
            "created_at": self.created_at.isoformat(),
        }


class PatentKnowledgeGraph:
    """专利知识图谱 (Enhanced)"""

    _instance: PatentKnowledgeGraph | None = None

    def __init__(self):
        self.nodes: dict[str, KnowledgeNode] = (
            {}
        )  # Keep memory cache for frequently accessed nodes? Or just rely on PG.
        # We will use PG as the source of truth, but maybe cache some.
        # For compatibility with existing code, we might maintain self.nodes but it's dangerous if it gets too big.
        # Let's transition to async fetching from PG primarily.

        self.pg_store: PGGraphStore | None = None
        self.vector_adapter: QdrantVectorAdapter | None = None
        self.embedding_service: UnifiedEmbeddingService | None = None
        self._initialized = False

    @classmethod
    async def initialize(cls):
        """初始化知识图谱"""
        if cls._instance is None:
            cls._instance = cls()
            await cls._instance._init_components()
            await cls._instance._load_knowledge_base()
            cls._instance._initialized = True
            logger.info("✅ 专利知识图谱初始化完成 (PostgreSQL + Qdrant)")
        return cls._instance

    @classmethod
    def get_instance(cls) -> PatentKnowledgeGraph:
        """获取单例实例"""
        if cls._instance is None:
            raise RuntimeError("PatentKnowledgeGraph未初始化,请先调用initialize()")
        return cls._instance

    async def _init_components(self):
        """初始化组件"""
        self.pg_store = PGGraphStore()
        self.vector_adapter = QdrantVectorAdapter()
        self.embedding_service = UnifiedEmbeddingService()
        await self.embedding_service.initialize()

    async def _load_knowledge_base(self):
        """加载知识库 (如果为空则加载初始数据)"""
        # Check if DB has data
        existing_nodes = await self.pg_store.search_nodes_by_text("", limit=1)
        if not existing_nodes:
            logger.info("Empty Knowledge Graph detected. Seeding initial data...")
            await self._load_patent_knowledge()
            await self._load_technology_knowledge()
            await self._load_legal_knowledge()
            await self._load_company_knowledge()
        else:
            logger.info("Knowledge Graph data already exists in PostgreSQL.")

    async def _load_patent_knowledge(self):
        """加载专利知识 (Seed Data)"""
        patents = [
            {
                "node_id": "patent_001",
                "title": "一种基于AI的专利分析方法",
                "description": "利用人工智能技术进行专利分析的方法",
                "properties": {
                    "application_date": "2023-01-15",
                    "publication_number": "CN202310010000.1",
                    "inventors": ["张三", "李四"],
                    "assignee": "Athena科技公司",
                },
            },
            {
                "node_id": "patent_002",
                "title": "智能专利重写系统",
                "description": "自动优化专利文档的系统",
                "properties": {
                    "application_date": "2023-03-20",
                    "publication_number": "CN202310020000.5",
                    "inventors": ["王五"],
                    "assignee": "智能科技股份",
                },
            },
        ]

        for patent_data in patents:
            node = KnowledgeNode(
                node_id=patent_data["node_id"],
                node_type=NodeType.PATENT,
                title=patent_data["title"],
                description=patent_data["description"],
                properties=patent_data["properties"],
            )
            await self.add_node(node)

    async def _load_technology_knowledge(self):
        """加载技术知识 (Seed Data)"""
        technologies = [
            {
                "node_id": "tech_001",
                "title": "人工智能",
                "description": "模拟人类智能的技术",
                "properties": {
                    "category": "计算机科学",
                    "keywords": ["AI", "机器学习", "深度学习"],
                    "maturity_level": "成熟",
                },
            },
            {
                "node_id": "tech_002",
                "title": "自然语言处理",
                "description": "处理和理解自然语言的技术",
                "properties": {
                    "category": "计算机科学",
                    "keywords": ["NLP", "文本分析", "语言模型"],
                    "maturity_level": "发展期",
                },
            },
            {
                "node_id": "tech_003",
                "title": "知识图谱",
                "description": "结构化知识表示技术",
                "properties": {
                    "category": "数据科学",
                    "keywords": ["图谱", "知识表示", "语义网络"],
                    "maturity_level": "成熟",
                },
            },
        ]

        for tech_data in technologies:
            node = KnowledgeNode(
                node_id=tech_data["node_id"],
                node_type=NodeType.TECHNOLOGY,
                title=tech_data["title"],
                description=tech_data["description"],
                properties=tech_data["properties"],
            )
            await self.add_node(node)

    async def _load_legal_knowledge(self):
        """加载法律知识 (Seed Data)"""
        legal_cases = [
            {
                "node_id": "legal_001",
                "title": "专利侵权纠纷案例",
                "description": "典型的专利侵权判决案例",
                "properties": {
                    "case_number": "(2023)最高法知民终123号",
                    "court": "最高人民法院",
                    "decision_date": "2023-06-15",
                    "outcome": "维持原判",
                },
            }
        ]

        for case_data in legal_cases:
            node = KnowledgeNode(
                node_id=case_data["node_id"],
                node_type=NodeType.LEGAL_CASE,
                title=case_data["title"],
                description=case_data["description"],
                properties=case_data["properties"],
            )
            await self.add_node(node)

    async def _load_company_knowledge(self):
        """加载公司知识 (Seed Data)"""
        companies = [
            {
                "node_id": "company_001",
                "title": "Athena科技公司",
                "description": "专注于AI专利技术的创新企业",
                "properties": {
                    "industry": "人工智能",
                    "founded": "2020-01-01",
                    "location": "北京",
                    "patent_count": 150,
                },
            }
        ]

        for company_data in companies:
            node = KnowledgeNode(
                node_id=company_data["node_id"],
                node_type=NodeType.COMPANY,
                title=company_data["title"],
                description=company_data["description"],
                properties=company_data["properties"],
            )
            await self.add_node(node)

    async def add_node(self, node: KnowledgeNode):
        """添加节点 (PG + Vector)"""
        # 1. Save to PostgreSQL
        node_type_str = (
            node.node_type.value if isinstance(node.node_type, NodeType) else str(node.node_type)
        )
        success = await self.pg_store.add_node(
            node_id=node.node_id,
            node_type=node_type_str,
            name=node.title,
            content=node.description,
            properties=node.properties,
        )

        if not success:
            logger.error(f"Failed to save node {node.node_id} to PG")
            return

        # 2. Generate Embedding
        try:
            # Combine title and description for embedding
            text_to_embed = f"{node.title}\n{node.description}"
            # Extract keywords from properties if any
            if "keywords" in node.properties:
                text_to_embed += f"\n_keywords: {', '.join(node.properties['keywords'])}"

            # Using KNOWLEDGE_GRAPH module config
            embedding_result = await self.embedding_service.encode(
                text_to_embed, module_type=ModuleType.KNOWLEDGE_GRAPH
            )

            # Assuming result is a dict with 'embeddings' key or similar,
            # based on typical BGE service wrapper.
            # If UnifiedEmbeddingService returns the raw list from BGE service:
            if isinstance(embedding_result, dict) and "embeddings" in embedding_result:
                vector = embedding_result["embeddings"][0]
            elif isinstance(embedding_result, list):
                vector = embedding_result[0]
            else:
                # Fallback or error
                logger.warning(f"Unexpected embedding format for node {node.node_id}")
                return

            # 3. Save to Qdrant
            # Use 'patent_rules_1024' as the collection for now, or 'knowledge_graph' if available.
            # The QdrantAdapter has 'patent_rules_1024'. Let's use that for rules, but maybe 'technical' for others?
            # For simplicity, let's assume we use 'patent_rules_1024' for all KG nodes for now,
            # or map based on type.
            collection_name = "patent_rules_1024"
            if node.node_type == NodeType.LEGAL_CASE:
                collection_name = "legal_clauses_1024"  # Or 'legal'
            elif node.node_type == NodeType.TECHNOLOGY:
                collection_name = "technical_terms_1024"  # Or 'technical'

            # Payload matches Qdrant expectations
            payload = {
                "node_id": node.node_id,
                "type": node_type_str,
                "title": node.title,
                "description": node.description[:200],  # Truncate for payload
            }

            await self.vector_adapter.add_vectors(
                collection_name,  # Pass key name from adapter's collection map?
                # Adapter takes 'collection_type' key.
                # keys in adapter: 'patent_rules_1024', 'legal_clauses_1024', 'technical_terms_1024'
                [
                    {
                        "id": node.node_id,  # Qdrant expects UUID or int. Our IDs are strings.
                        # Qdrant client handles UUID strings usually.
                        # If it fails, we might need to hash it to UUID.
                        "vector": vector,
                        "payload": payload,
                    }
                ],
            )

        except Exception as e:
            logger.error(f"Failed to vectorize node {node.node_id}: {e}")

    async def add_relation(self, relation: KnowledgeRelation):
        """添加关系"""
        relation_type_str = (
            relation.relation_type.value
            if isinstance(relation.relation_type, RelationType)
            else str(relation.relation_type)
        )
        await self.pg_store.add_relation(
            source_id=relation.source_id,
            target_id=relation.target_id,
            relation_type=relation_type_str,
            weight=relation.weight,
            properties=relation.properties,
        )

    async def get_node(self, node_id: str) -> KnowledgeNode | None:
        """获取节点"""
        data = await self.pg_store.get_node(node_id)
        if data:
            return KnowledgeNode(
                node_id=data["id"],
                node_type=data["type"],
                title=data["name"],
                description=data["content"] or "",
                properties=data["properties"],
            )
        return None

    async def get_related_nodes(
        self, node_id: str, relation_types: list[RelationType] | None = None, max_depth: int = 1
    ) -> list[KnowledgeNode]:
        """获取相关节点 (From PG)"""
        # Convert enums to strings
        rel_types_str = [rt.value for rt in relation_types] if relation_types else None

        # Currently PG adapter implements direct neighbors (depth 1).
        # For max_depth > 1, we could implement recursive query in PG adapter.
        # Adapter has get_related_nodes (depth 1).

        results = await self.pg_store.get_related_nodes(node_id, rel_types_str)
        nodes = []
        for res in results:
            node_data = res["node"]
            nodes.append(
                KnowledgeNode(
                    node_id=node_data["id"],
                    node_type=node_data["type"],
                    title=node_data["name"],
                    description=node_data["content"] or "",
                    properties=node_data["properties"],
                )
            )
        return nodes

    async def search_nodes(
        self, query: str, node_types: list[NodeType] | None = None, limit: int = 10
    ) -> list[KnowledgeNode]:
        """搜索节点 (Vector + Hybrid)"""

        # 1. Embed Query
        embedding_result = await self.embedding_service.encode(
            query, module_type=ModuleType.KNOWLEDGE_GRAPH
        )

        if isinstance(embedding_result, dict) and "embeddings" in embedding_result:
            query_vector = embedding_result["embeddings"][0]
        elif isinstance(embedding_result, list):
            query_vector = embedding_result[0]
        else:
            return []

        # 2. Vector Search in Qdrant
        # We need to search across multiple collections if node_types is mixed or None.
        # For simplicity, search 'patent_rules_1024' as primary, or iterate.
        # Let's search 'patent_rules_1024' (Concepts), 'legal_clauses_1024', 'technical_terms_1024'.

        collections_to_search = ["patent_rules_1024", "legal_clauses_1024", "technical_terms_1024"]
        all_results = []

        for col_type in collections_to_search:
            results = await self.vector_adapter.search_vectors(
                collection_type=col_type,
                query_vector=query_vector,
                limit=limit,
                threshold=0.6,  # High threshold for quality
            )
            all_results.extend(results)

        # 3. Sort by score
        all_results.sort(key=lambda x: x["score"], reverse=True)
        top_results = all_results[:limit]

        # 4. Fetch full nodes from PG
        node_ids = [res["id"] for res in top_results]

        # Also filter by node_type if requested (post-filter since Qdrant payload filter might be complex to pass via adapter)
        # Actually fetching from PG allows us to check types.

        pg_nodes = await self.pg_store.get_nodes_by_ids(node_ids)

        # Convert to KnowledgeNode objects
        final_nodes = []
        for data in pg_nodes:
            # Filter type if needed
            if node_types:
                type_values = [nt.value for nt in node_types]
                if data["type"] not in type_values:
                    continue

            final_nodes.append(
                KnowledgeNode(
                    node_id=data["id"],
                    node_type=data["type"],
                    title=data["name"],
                    description=data["content"] or "",
                    properties=data["properties"],
                )
            )

        return final_nodes

    async def search_entities(self, query: str, limit: int = 10) -> list[dict]:
        """搜索实体 - 兼容性接口"""
        nodes = await self.search_nodes(query, limit=limit)

        entities = []
        for node in nodes:
            entities.append(
                {
                    "id": node.node_id,
                    "type": node.node_type.value,
                    "title": node.title,
                    "description": node.description,
                    "properties": node.properties,
                    "relevance": 0.8,  # 默认相关性评分
                }
            )

        return entities

    async def get_path(
        self, source_id: str, target_id: str, max_length: int = 5
    ) -> list[str | None]:
        """获取节点间路径 (Use PG recursive query)"""
        # Implement using PG recursive query if available in adapter,
        # or keep BFS logic but fetch neighbors from PG.
        # For now, let's skip deep implementation to focus on core structure.
        return None

    async def analyze_patent_context(self, patent_data: dict[str, Any]) -> dict[str, Any]:
        """分析专利上下文"""
        # Logic remains similar but uses async search
        keywords = self._extract_keywords(patent_data)

        related_technologies = await self.search_nodes(
            " ".join(keywords[:3]), [NodeType.TECHNOLOGY], limit=5
        )

        related_patents = await self.search_nodes(
            patent_data.get("title", ""), [NodeType.PATENT], limit=5
        )

        related_cases = await self.search_nodes(
            " ".join(keywords[:2]), [NodeType.LEGAL_CASE], limit=3
        )

        return {
            "keywords": keywords,
            "related_technologies": [t.title for t in related_technologies],
            "related_patents": [p.title for p in related_patents],
            "related_cases": [c.title for c in related_cases],
            "innovation_level": "High",  # Placeholder
        }

    def _extract_keywords(self, patent_data: dict[str, Any]) -> list[str]:
        """提取关键词"""
        # Same as before
        title = patent_data.get("title", "")
        return title.split()[:5]

    async def get_statistics(self) -> dict[str, Any]:
        """获取图谱统计信息"""
        # Could fetch count from PG
        return {"total_nodes": "Unknown (in DB)", "status": "Active"}

    @classmethod
    async def shutdown(cls):
        """关闭知识图谱"""
        if cls._instance:
            cls._instance = None
            logger.info("✅ 专利知识图谱已关闭")
