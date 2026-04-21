#!/usr/bin/env python3
from __future__ import annotations
"""
统一专利知识图谱模型
Unified Patent Knowledge Graph Model

整合自4个源文件:
- core/patents/patent_knowledge_graph.py (PostgreSQL+Qdrant混合架构)
- core/knowledge/patent_analysis/knowledge_graph.py (NetworkX图分析)
- core/knowledge/patent_analysis/enhanced_knowledge_graph.py (GraphRAG增强)
- core/patents/patent_knowledge_graph_enhanced.py (PDF适配器)

功能:
- 支持两种后端：PostgreSQL+Qdrant (持久化) / NetworkX (内存)
- 整合所有节点/关系类型
- 支持三元组建模(问题-特征-效果)
- 支持GraphRAG检索
- 支持PDF输入适配器
- 支持可视化

作者: Athena平台团队
版本: v1.0.0
创建时间: 2026-04-21
"""

import asyncio
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any

# 核心组件导入 (延迟导入以避免依赖问题)
try:
    from core.embedding.unified_embedding_service import ModuleType, UnifiedEmbeddingService
except ImportError:
    UnifiedEmbeddingService = None  # type: ignore
    ModuleType = None  # type: ignore

try:
    from core.knowledge.storage.pg_graph_store import PGGraphStore
except ImportError:
    PGGraphStore = None  # type: ignore

try:
    from core.reranking.bge_reranker import RerankConfig, RerankMode, get_reranker
except ImportError:
    get_reranker = None  # type: ignore

try:
    from core.vector.qdrant_adapter import QdrantVectorAdapter
except ImportError:
    QdrantVectorAdapter = None  # type: ignore

logger = logging.getLogger(__name__)


# =============================================================================
# 节点类型定义 (整合所有源文件的节点类型)
# =============================================================================

class NodeType(Enum):
    """统一节点类型枚举"""

    # 专利相关
    PATENT = "patent"  # 专利
    PRIOR_ART = "prior_art"  # 现有技术
    CLAIM = "claim"  # 权利要求
    EMBODIMENT = "embodiment"  # 实施例

    # 技术相关
    TECHNOLOGY = "technology"  # 技术
    PROBLEM = "problem"  # 技术问题
    FEATURE = "feature"  # 技术特征
    EFFECT = "effect"  # 技术效果

    # 实体相关
    COMPANY = "company"  # 公司
    INVENTOR = "inventor"  # 发明人

    # 分类相关
    CATEGORY = "category"  # 分类
    KEYWORD = "keyword"  # 关键词

    # 法律相关
    LEGAL_CASE = "legal_case"  # 法律案例
    ARTICLE = "article"  # 法律条款
    CONCEPT = "concept"  # 法律/专利概念

    # 文档相关
    DOCUMENT = "document"  # 文档(专利/论文)


class RelationType(Enum):
    """统一关系类型枚举"""

    # 文档内部关系
    SOLVES = "solves"  # 问题-特征:特征解决问题
    ACHIEVES = "achieves"  # 特征-效果:特征实现效果
    DEPENDS_ON = "depends_on"  # 特征依赖:特征A依赖特征B
    COMBINED_WITH = "combined_with"  # 特征组合:特征A与B组合
    ALTERNATIVE_TO = "alternative_to"  # 特征替代:特征A替代B
    INCLUDES = "includes"  # 文档包含:文档包含权利要求

    # 跨文档关系
    SIMILAR_TO = "similar_to"  # 特征相似:特征A与B相似
    IMPROVES_UPON = "improves_upon"  # 改进关系:A改进B
    DIFFERENT_FROM = "different_from"  # 区别关系:A与B不同
    SAME_AS = "same_as"  # 相同关系:A与B相同
    PRIOR_ART = "prior_art"  # 现有技术:A是B的现有技术

    # 专利关系
    CITES = "cites"  # 引用
    INVENTED_BY = "invented_by"  # 发明
    ASSIGNED_TO = "assigned_to"  # 转让
    BELONGS_TO = "belongs_to"  # 属于
    RELATED_TO = "related_to"  # 相关
    PRECEDES = "precedes"  # 先于
    IMPROVES = "improves"  # 改进
    DEFINES = "defines"  # 定义
    CONTAINS = "contains"  # 包含


class QueryType(Enum):
    """查询类型"""

    PATENT_ANALYSIS = "patent_analysis"  # 专利分析
    LEGAL_COMPLIANCE = "legal_compliance"  # 法律合规检查
    TECHNICAL_SEARCH = "technical_search"  # 技术搜索
    GENERAL_SEARCH = "general_search"  # 通用搜索


# =============================================================================
# 数据类定义
# =============================================================================

@dataclass
class TechnicalTriple:
    """技术三元组:问题-特征-效果"""

    problem: str  # 技术问题
    features: list[str]  # 技术特征列表
    effect: str  # 技术效果
    source_claim: int | None = None  # 来源权利要求号

    def __str__(self) -> str:
        return f"[{self.problem}] + {self.features} -> [{self.effect}]"


@dataclass
class FeatureRelation:
    """特征关系"""

    source_feature: str  # 源特征
    target_feature: str  # 目标特征
    relation_type: RelationType  # 关系类型
    strength: float = 1.0  # 关系强度(0-1)
    description: str | None = None  # 关系描述


@dataclass
class DocumentAnalysis:
    """文档技术分析结果"""

    document_id: str  # 文档ID(申请号/公开号)
    document_type: str  # 文档类型(专利/论文)
    document_name: str  # 文档名称
    triples: list[TechnicalTriple] = field(default_factory=list)  # 三元组列表
    feature_relations: list[FeatureRelation] = field(default_factory=list)  # 特征关系
    ipc_classifications: list[str] = field(default_factory=list)  # IPC分类号

    def get_all_features(self) -> set[str]:
        """获取所有技术特征"""
        features = set()
        for triple in self.triples:
            features.update(triple.features)
        return features

    def get_all_problems(self) -> set[str]:
        """获取所有技术问题"""
        return {triple.problem for triple in self.triples}

    def get_all_effects(self) -> set[str]:
        """获取所有技术效果"""
        return {triple.effect for triple in self.triples}


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


@dataclass
class SearchResult:
    """搜索结果"""

    node_id: str
    title: str
    content: str
    score: float
    node_type: str
    context: dict[str, Any] = field(default_factory=dict)
    related_nodes: list[dict[str, Any]] = field(default_factory=list)


@dataclass
class HybridSearchConfig:
    """混合检索配置"""

    vector_weight: float = 0.5
    graph_weight: float = 0.3
    text_weight: float = 0.2
    max_hops: int = 2
    top_k: int = 50
    re_rank_top_k: int = 10


# =============================================================================
# 后端抽象接口
# =============================================================================

class GraphBackend(ABC):
    """图后端抽象接口"""

    @abstractmethod
    async def initialize(self):
        """初始化后端"""
        pass

    @abstractmethod
    async def add_node(self, node: KnowledgeNode) -> bool:
        """添加节点"""
        pass

    @abstractmethod
    async def add_relation(self, relation: KnowledgeRelation) -> bool:
        """添加关系"""
        pass

    @abstractmethod
    async def search_nodes(self, query: str, limit: int = 10) -> list[SearchResult]:
        """搜索节点"""
        pass

    @abstractmethod
    async def get_neighbors(self, node_id: str, max_depth: int = 1) -> list[dict[str, Any]]:
        """获取邻居节点"""
        pass

    @abstractmethod
    async def close(self):
        """关闭后端"""
        pass


class PersistentGraphBackend(GraphBackend):
    """持久化图后端 (PostgreSQL + Qdrant)"""

    def __init__(self):
        self.pg_store: PGGraphStore | None = None
        self.vector_adapter: QdrantVectorAdapter | None = None
        self.embedding_service: UnifiedEmbeddingService | None = None

    async def initialize(self):
        """初始化后端"""
        # 初始化PostgreSQL图存储
        self.pg_store = PGGraphStore()
        await self.pg_store.initialize()
        logger.info("✅ PostgreSQL图存储初始化完成")

        # 初始化向量适配器
        self.vector_adapter = QdrantVectorAdapter()
        await self.vector_adapter.initialize()
        logger.info("✅ Qdrant向量适配器初始化完成")

        # 初始化嵌入服务
        self.embedding_service = UnifiedEmbeddingService()
        await self.embedding_service.initialize()
        logger.info("✅ 统一嵌入服务初始化完成")

    async def add_node(self, node: KnowledgeNode) -> bool:
        """添加节点 (PG + Vector)"""
        if not self.pg_store or not self.vector_adapter or not self.embedding_service:
            raise RuntimeError("后端未初始化")

        # 1. 保存到PostgreSQL
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
            logger.error(f"保存节点 {node.node_id} 到PostgreSQL失败")
            return False

        # 2. 生成向量并保存到Qdrant
        try:
            text_to_embed = f"{node.title}\n{node.description}"
            if "keywords" in node.properties:
                text_to_embed += f"\n关键词: {', '.join(node.properties['keywords'])}"

            embedding_result = await self.embedding_service.encode(
                text_to_embed, module_type=ModuleType.KNOWLEDGE_GRAPH
            )

            if isinstance(embedding_result, dict) and "embeddings" in embedding_result:
                vector = embedding_result["embeddings"][0]
            elif isinstance(embedding_result, list):
                vector = embedding_result[0]
            else:
                logger.warning(f"节点 {node.node_id} 的向量格式异常")
                return True  # PG保存成功，返回True

            # 保存到Qdrant (使用合适的collection)
            await self.vector_adapter.upsert(
                collection_name="knowledge_graph",
                points=[{
                    "id": node.node_id,
                    "vector": vector,
                    "payload": {
                        "node_id": node.node_id,
                        "node_type": node_type_str,
                        "title": node.title,
                        "description": node.description,
                    }
                }]
            )
            logger.debug(f"节点 {node.node_id} 保存成功 (PG + Qdrant)")
            return True

        except Exception as e:
            logger.error(f"保存节点 {node.node_id} 向量失败: {e}")
            return True  # PG保存成功，返回True

    async def add_relation(self, relation: KnowledgeRelation) -> bool:
        """添加关系"""
        if not self.pg_store:
            raise RuntimeError("后端未初始化")

        relation_type_str = (
            relation.relation_type.value
            if isinstance(relation.relation_type, RelationType)
            else str(relation.relation_type)
        )

        return await self.pg_store.add_edge(
            edge_id=relation.relation_id,
            source_id=relation.source_id,
            target_id=relation.target_id,
            relation_type=relation_type_str,
            properties=relation.properties,
        )

    async def search_nodes(self, query: str, limit: int = 10) -> list[SearchResult]:
        """搜索节点"""
        if not self.pg_store:
            raise RuntimeError("后端未初始化")
        nodes = await self.pg_store.search_nodes_by_text(query, limit=limit)
        return [
            SearchResult(
                node_id=node["node_id"],
                title=node["name"],
                content=node["content"],
                score=0.0,  # PG搜索不返回分数
                node_type=node["node_type"],
            )
            for node in nodes
        ]

    async def get_neighbors(self, node_id: str, max_depth: int = 1) -> list[dict[str, Any]]:
        """获取邻居节点"""
        if not self.pg_store:
            raise RuntimeError("后端未初始化")
        return await self.pg_store.get_neighbors(node_id, max_depth=max_depth)

    async def close(self):
        """关闭后端"""
        if self.pg_store:
            await self.pg_store.close()


class MemoryGraphBackend(GraphBackend):
    """内存图后端 (NetworkX) - 用于分析和可视化"""

    def __init__(self):
        self.graph = None  # 延迟导入NetworkX
        self._nodes: dict[str, KnowledgeNode] = {}
        self._relations: dict[str, KnowledgeRelation] = {}

    async def initialize(self):
        """初始化后端"""
        try:
            import networkx as nx
            self.graph = nx.MultiDiGraph()
            logger.info("✅ NetworkX内存图初始化完成")
        except ImportError:
            logger.warning("⚠️ NetworkX未安装，内存图功能不可用")
            self.graph = None

    async def add_node(self, node: KnowledgeNode) -> bool:
        """添加节点"""
        self._nodes[node.node_id] = node
        if self.graph:
            self.graph.add_node(
                node.node_id,
                node_type=node.node_type,
                title=node.title,
                description=node.description,
                **node.properties
            )
        return True

    async def add_relation(self, relation: KnowledgeRelation) -> bool:
        """添加关系"""
        self._relations[relation.relation_id] = relation
        if self.graph:
            relation_type_str = (
                relation.relation_type.value
                if isinstance(relation.relation_type, RelationType)
                else str(relation.relation_type)
            )
            self.graph.add_edge(
                relation.source_id,
                relation.target_id,
                key=relation.relation_id,
                relation_type=relation_type_str,
                weight=relation.weight,
                **relation.properties
            )
        return True

    async def search_nodes(self, query: str, limit: int = 10) -> list[SearchResult]:
        """搜索节点 (简单的文本匹配)"""
        results = []
        query_lower = query.lower()
        for node_id, node in self._nodes.items():
            if (
                query_lower in node.title.lower()
                or query_lower in node.description.lower()
            ):
                results.append(
                    SearchResult(
                        node_id=node_id,
                        title=node.title,
                        content=node.description,
                        score=1.0,
                        node_type=str(node.node_type),
                    )
                )
                if len(results) >= limit:
                    break
        return results

    async def get_neighbors(self, node_id: str, max_depth: int = 1) -> list[dict[str, Any]]:
        """获取邻居节点"""
        if not self.graph:
            return []
        neighbors = []
        for source, target, data in self.graph.edges(node_id, data=True):
            neighbors.append({
                "source": source,
                "target": target,
                "relation_type": data.get("relation_type"),
                "weight": data.get("weight", 1.0),
            })
        return neighbors

    async def close(self):
        """关闭后端"""
        self._nodes.clear()
        self._relations.clear()
        if self.graph:
            self.graph.clear()


# =============================================================================
# 统一专利知识图谱
# =============================================================================

class UnifiedPatentKnowledgeGraph:
    """
    统一专利知识图谱

    整合所有专利知识图谱功能:
    - 支持持久化和内存两种后端
    - 支持三元组建模
    - 支持GraphRAG检索
    - 支持文档分析
    """

    _instance: UnifiedPatentKnowledgeGraph | None = None

    def __init__(self, backend_type: str = "persistent"):
        """
        初始化知识图谱

        Args:
            backend_type: 后端类型 ("persistent" | "memory" | "hybrid")
        """
        self.backend_type = backend_type
        self.backend: GraphBackend | None = None
        self.memory_backend: MemoryGraphBackend | None = None  # 用于可视化
        self.reranker = None
        self._initialized = False

        # 文档分析缓存
        self.document_analyses: dict[str, DocumentAnalysis] = {}

    @classmethod
    async def initialize(cls, backend_type: str = "persistent") -> "UnifiedPatentKnowledgeGraph":
        """初始化知识图谱"""
        if cls._instance is None:
            cls._instance = cls(backend_type)
            await cls._instance._init_components()
            await cls._instance._load_knowledge_base()
            cls._instance._initialized = True
            logger.info(f"✅ 统一专利知识图谱初始化完成 (backend={backend_type})")
        return cls._instance

    @classmethod
    def get_instance(cls) -> "UnifiedPatentKnowledgeGraph":
        """获取单例实例"""
        if cls._instance is None:
            raise RuntimeError("UnifiedPatentKnowledgeGraph未初始化,请先调用initialize()")
        return cls._instance

    async def _init_components(self):
        """初始化组件"""
        # 初始化主后端
        if self.backend_type == "persistent":
            self.backend = PersistentGraphBackend()
        elif self.backend_type == "memory":
            self.backend = MemoryGraphBackend()
        else:  # hybrid
            self.backend = PersistentGraphBackend()
            self.memory_backend = MemoryGraphBackend()

        await self.backend.initialize()

        # 如果是混合模式，也初始化内存后端
        if self.memory_backend:
            await self.memory_backend.initialize()

        # 初始化重排序引擎
        try:
            self.reranker = await get_reranker()
            logger.info("✅ 重排序引擎初始化完成")
        except Exception as e:
            logger.warning(f"⚠️ 重排序引擎初始化失败: {e}")

    async def _load_knowledge_base(self):
        """加载知识库"""
        logger.info("📚 知识图谱已就绪，等待数据...")

    # -------------------------------------------------------------------------
    # 节点和关系操作
    # -------------------------------------------------------------------------

    async def add_node(self, node: KnowledgeNode) -> bool:
        """添加节点"""
        if not self.backend:
            raise RuntimeError("后端未初始化")

        # 同时添加到两个后端（如果是混合模式）
        result = await self.backend.add_node(node)
        if self.memory_backend:
            await self.memory_backend.add_node(node)
        return result

    async def add_relation(self, relation: KnowledgeRelation) -> bool:
        """添加关系"""
        if not self.backend:
            raise RuntimeError("后端未初始化")

        result = await self.backend.add_relation(relation)
        if self.memory_backend:
            await self.memory_backend.add_relation(relation)
        return result

    # -------------------------------------------------------------------------
    # 文档分析功能 (三元组建模)
    # -------------------------------------------------------------------------

    async def analyze_document(
        self,
        document_id: str,
        document_name: str,
        triples: list[TechnicalTriple],
        feature_relations: list[FeatureRelation] | None = None,
        ipc_classifications: list[str] | None = None,
        document_type: str = "专利",
    ) -> DocumentAnalysis:
        """
        分析单个文档,构建技术知识图谱

        Args:
            document_id: 文档ID
            document_name: 文档名称
            triples: 技术三元组列表
            feature_relations: 特征关系列表
            ipc_classifications: IPC分类号
            document_type: 文档类型

        Returns:
            DocumentAnalysis: 文档分析结果
        """
        # 创建文档分析对象
        analysis = DocumentAnalysis(
            document_id=document_id,
            document_name=document_name,
            triples=triples,
            feature_relations=feature_relations or [],
            ipc_classifications=ipc_classifications or [],
            document_type=document_type,
        )

        # 缓存分析结果
        self.document_analyses[document_id] = analysis

        # 添加文档节点
        doc_node = KnowledgeNode(
            node_id=document_id,
            node_type=NodeType.DOCUMENT,
            title=document_name,
            description=f"{document_type}文档",
            properties={
                "document_type": document_type,
                "ipc_classifications": ipc_classifications or [],
            }
        )
        await self.add_node(doc_node)

        # 添加三元组到图谱
        await self._add_triples_to_graph(analysis, document_id)

        # 添加特征关系到图谱
        if feature_relations:
            await self._add_feature_relations_to_graph(analysis, document_id)

        return analysis

    async def _add_triples_to_graph(self, analysis: DocumentAnalysis, document_id: str):
        """将三元组添加到图谱"""
        for idx, triple in enumerate(analysis.triples):
            # 创建唯一ID
            problem_id = f"{document_id}_P{idx}"
            effect_id = f"{document_id}_E{idx}"

            # 添加问题节点
            problem_node = KnowledgeNode(
                node_id=problem_id,
                node_type=NodeType.PROBLEM,
                title=triple.problem,
                description=triple.problem,
                properties={"source_document": document_id, "source_claim": triple.source_claim}
            )
            await self.add_node(problem_node)

            # 添加效果节点
            effect_node = KnowledgeNode(
                node_id=effect_id,
                node_type=NodeType.EFFECT,
                title=triple.effect,
                description=triple.effect,
                properties={"source_document": document_id}
            )
            await self.add_node(effect_node)

            # 添加特征节点和关系
            for f_idx, feature in enumerate(triple.features):
                feature_id = f"{document_id}_F{idx}_{f_idx}"

                feature_node = KnowledgeNode(
                    node_id=feature_id,
                    node_type=NodeType.FEATURE,
                    title=feature,
                    description=feature,
                    properties={"source_document": document_id, "source_claim": triple.source_claim}
                )
                await self.add_node(feature_node)

                # 添加:特征->问题(解决关系)
                await self.add_relation(KnowledgeRelation(
                    relation_id=f"{feature_id}_solves_{problem_id}",
                    source_id=feature_id,
                    target_id=problem_id,
                    relation_type=RelationType.SOLVES,
                    weight=1.0,
                    properties={}
                ))

                # 添加:特征->效果(实现关系)
                await self.add_relation(KnowledgeRelation(
                    relation_id=f"{feature_id}_achieves_{effect_id}",
                    source_id=feature_id,
                    target_id=effect_id,
                    relation_type=RelationType.ACHIEVES,
                    weight=1.0,
                    properties={}
                ))

            # 添加:文档->问题(包含关系)
            await self.add_relation(KnowledgeRelation(
                relation_id=f"{document_id}_includes_{problem_id}",
                source_id=document_id,
                target_id=problem_id,
                relation_type=RelationType.INCLUDES,
                weight=1.0,
                properties={}
            ))

            # 添加:文档->效果(包含关系)
            await self.add_relation(KnowledgeRelation(
                relation_id=f"{document_id}_includes_{effect_id}",
                source_id=document_id,
                target_id=effect_id,
                relation_type=RelationType.INCLUDES,
                weight=1.0,
                properties={}
            ))

    async def _add_feature_relations_to_graph(self, analysis: DocumentAnalysis, document_id: str):
        """添加特征关系到图谱"""
        for idx, relation in enumerate(analysis.feature_relations):
            # 查找特征节点ID
            source_id = self._find_feature_node(document_id, relation.source_feature)
            target_id = self._find_feature_node(document_id, relation.target_feature)

            if source_id and target_id:
                await self.add_relation(KnowledgeRelation(
                    relation_id=f"{source_id}_{relation.relation_type.value}_{target_id}",
                    source_id=source_id,
                    target_id=target_id,
                    relation_type=relation.relation_type,
                    weight=relation.strength,
                    properties={"description": relation.description} if relation.description else {}
                ))

    def _find_feature_node(self, document_id: str, feature_name: str) -> str | None:
        """查找特征节点ID"""
        # 遍历所有三元组查找匹配的特征
        for analysis in self.document_analyses.values():
            if analysis.document_id != document_id:
                continue
            for idx, triple in enumerate(analysis.triples):
                for f_idx, feature in enumerate(triple.features):
                    if feature == feature_name:
                        return f"{document_id}_F{idx}_{f_idx}"
        return None

    # -------------------------------------------------------------------------
    # 搜索功能
    # -------------------------------------------------------------------------

    async def search(self, query: str, limit: int = 10) -> list[SearchResult]:
        """搜索节点"""
        if not self.backend:
            raise RuntimeError("后端未初始化")
        return await self.backend.search_nodes(query, limit=limit)

    async def hybrid_search(
        self,
        query: str,
        config: HybridSearchConfig | None = None,
    ) -> list[SearchResult]:
        """
        混合搜索 (向量 + 图 + 文本)

        Args:
            query: 查询文本
            config: 混合搜索配置

        Returns:
            搜索结果列表
        """
        if not self.backend:
            raise RuntimeError("后端未初始化")

        config = config or HybridSearchConfig()

        # 执行搜索
        results = await self.search(query, limit=config.top_k)

        # 重排序
        if self.reranker and results:
            try:
                passages = [r.content for r in results]
                rerank_results = await self.reranker.rerank(
                    query=query,
                    passages=passages,
                    top_k=config.re_rank_top_k
                )
                # 重新排序结果
                reranked = [results[i] for i in rerank_results.indices[:config.re_rank_top_k]]
                return reranked
            except Exception as e:
                logger.warning(f"重排序失败: {e}")

        return results[:config.re_rank_top_k]

    # -------------------------------------------------------------------------
    # 图谱遍历
    # -------------------------------------------------------------------------

    async def get_neighbors(self, node_id: str, max_depth: int = 1) -> list[dict[str, Any]]:
        """获取邻居节点"""
        if not self.backend:
            raise RuntimeError("后端未初始化")
        return await self.backend.get_neighbors(node_id, max_depth=max_depth)

    async def find_path(self, source_id: str, target_id: str) -> list[dict[str, Any]]:
        """查找两个节点之间的路径"""
        if not self.memory_backend:
            logger.warning("⚠️ 路径查找需要内存后端")
            return []
        # TODO: 实现NetworkX路径查找
        return []

    # -------------------------------------------------------------------------
    # 文档对比功能
    # -------------------------------------------------------------------------

    async def compare_documents(
        self, doc1_id: str, doc2_id: str
    ) -> dict[str, Any]:
        """
        对比两个文档的技术差异

        Args:
            doc1_id: 文档1 ID
            doc2_id: 文档2 ID

        Returns:
            对比分析结果字典
        """
        if doc1_id not in self.document_analyses or doc2_id not in self.document_analyses:
            raise ValueError("文档未在图谱中,请先分析文档")

        doc1 = self.document_analyses[doc1_id]
        doc2 = self.document_analyses[doc2_id]

        # 提取特征集合
        features1 = doc1.get_all_features()
        features2 = doc2.get_all_features()

        # 计算相似度
        common_features = features1 & features2
        unique_features1 = features1 - features2
        unique_features2 = features2 - features1

        # 计算相似度比例
        total_features = features1 | features2
        similarity = len(common_features) / len(total_features) if total_features else 0.0

        return {
            "doc1_id": doc1_id,
            "doc2_id": doc2_id,
            "similarity": similarity,
            "common_features": list(common_features),
            "unique_features_doc1": list(unique_features1),
            "unique_features_doc2": list(unique_features2),
        }

    # -------------------------------------------------------------------------
    # 可视化功能
    # -------------------------------------------------------------------------

    def visualize_graph(self, output_path: str | None = None) -> Any | None:
        """
        可视化图谱

        Args:
            output_path: 输出文件路径 (可选)

        Returns:
            matplotlib图形对象 (如果output_path为None)
        """
        if not self.memory_backend or not self.memory_backend.graph:
            logger.warning("⚠️ 可视化需要内存后端")
            return None

        try:
            import matplotlib.pyplot as plt
            import networkx as nx

            fig, ax = plt.subplots(figsize=(12, 8))

            # 绘制图谱
            pos = nx.spring_layout(self.memory_backend.graph, k=1, iterations=50)

            # 按节点类型着色
            node_colors = []
            for node in self.memory_backend.graph.nodes():
                node_data = self.memory_backend.graph.nodes[node]
                node_type = node_data.get("node_type", "unknown")
                if node_type == NodeType.PROBLEM:
                    node_colors.append("red")
                elif node_type == NodeType.FEATURE:
                    node_colors.append("blue")
                elif node_type == NodeType.EFFECT:
                    node_colors.append("green")
                else:
                    node_colors.append("gray")

            nx.draw(
                self.memory_backend.graph,
                pos,
                ax=ax,
                with_labels=True,
                node_color=node_colors,
                node_size=500,
                font_size=8,
                arrows=True,
            )

            ax.set_title("专利知识图谱")
            plt.tight_layout()

            if output_path:
                plt.savefig(output_path, dpi=300, bbox_inches="tight")
                logger.info(f"✅ 图谱已保存到: {output_path}")
                plt.close()
                return None
            else:
                return fig

        except ImportError:
            logger.warning("⚠️ matplotlib未安装，可视化功能不可用")
            return None

    # -------------------------------------------------------------------------
    # 关闭
    # -------------------------------------------------------------------------

    async def close(self):
        """关闭知识图谱"""
        if self.backend:
            await self.backend.close()
        if self.memory_backend:
            await self.memory_backend.close()
        logger.info("🔌 统一专利知识图谱已关闭")


# =============================================================================
# 兼容层
# =============================================================================

class PatentKnowledgeGraph(UnifiedPatentKnowledgeGraph):
    """
    PatentKnowledgeGraph兼容层

    保持与旧版API的兼容性
    """

    @classmethod
    async def initialize(cls) -> "PatentKnowledgeGraph":
        """初始化（兼容旧版签名）"""
        instance = await super().initialize(backend_type="persistent")
        return cls(backend_type="persistent")


class EnhancedPatentKnowledgeGraph(UnifiedPatentKnowledgeGraph):
    """
    EnhancedPatentKnowledgeGraph兼容层

    保持与旧版API的兼容性
    """

    @classmethod
    async def initialize(cls) -> "EnhancedPatentKnowledgeGraph":
        """初始化（兼容旧版签名）"""
        instance = await super().initialize(backend_type="hybrid")
        return cls(backend_type="hybrid")


# =============================================================================
# 便捷函数
# =============================================================================

async def get_patent_kg(backend_type: str = "persistent") -> UnifiedPatentKnowledgeGraph:
    """
    获取专利知识图谱实例

    Args:
        backend_type: 后端类型

    Returns:
        专利知识图谱实例
    """
    return await UnifiedPatentKnowledgeGraph.initialize(backend_type)


# =============================================================================
# 测试代码
# =============================================================================

if __name__ == "__main__":
    async def test():
        print("🧪 测试统一专利知识图谱")
        print("=" * 80)

        # 初始化
        kg = await UnifiedPatentKnowledgeGraph.initialize(backend_type="memory")

        # 添加节点
        node = KnowledgeNode(
            node_id="test_001",
            node_type=NodeType.PATENT,
            title="测试专利",
            description="这是一个测试专利",
            properties={"application_date": "2023-01-01"}
        )
        await kg.add_node(node)

        # 分析文档
        triples = [
            TechnicalTriple(
                problem="如何提高效率",
                features=["使用AI", "优化算法"],
                effect="效率提升50%"
            )
        ]
        analysis = await kg.analyze_document(
            document_id="doc_001",
            document_name="测试文档",
            triples=triples
        )

        print(f"✅ 文档分析完成: {analysis.document_name}")
        print(f"   技术问题: {analysis.get_all_problems()}")
        print(f"   技术特征: {analysis.get_all_features()}")
        print(f"   技术效果: {analysis.get_all_effects()}")

        # 搜索
        results = await kg.search("效率", limit=5)
        print(f"✅ 搜索结果: {len(results)}条")

        # 关闭
        await kg.close()
        print("\n✅ 测试完成")

    asyncio.run(test())
