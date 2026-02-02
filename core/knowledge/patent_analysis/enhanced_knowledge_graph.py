#!/usr/bin/env python3
"""
增强版专利知识图谱
Enhanced Patent Knowledge Graph

基于优化计划重构的知识图谱,实现数据分离、智能路由和GraphRAG能力
作者: 小诺·双鱼座 + Athena AI系统
创建时间: 2025-12-21
版本: v4.0.0 "GraphRAG增强"
"""

import asyncio
import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional

from core.embedding.unified_embedding_service import ModuleType, UnifiedEmbeddingService
from core.knowledge.collection_config import CollectionType, get_collection_mapper
from core.knowledge.storage.pg_graph_store import PGGraphStore
from core.reranking.bge_reranker import RerankConfig, RerankMode, get_reranker
from core.vector.qdrant_adapter import QdrantVectorAdapter

logger = logging.getLogger(__name__)


class QueryType(Enum):
    """查询类型"""

    PATENT_ANALYSIS = "patent_analysis"  # 专利分析
    LEGAL_COMPLIANCE = "legal_compliance"  # 法律合规检查
    TECHNICAL_SEARCH = "technical_search"  # 技术搜索
    GENERAL_SEARCH = "general_search"  # 通用搜索


@dataclass
class SearchResult:
    """搜索结果"""

    node_id: str
    title: str
    content: str
    score: float
    collection_type: CollectionType
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


class EnhancedPatentKnowledgeGraph:
    """增强版专利知识图谱"""

    _instance: EnhancedPatentKnowledgeGraph | None = None

    def __init__(self):
        self.nodes: dict[str, Any] = {}
        self.pg_store: PGGraphStore | None = None
        self.vector_adapter: QdrantVectorAdapter | None = None
        self.embedding_service: UnifiedEmbeddingService | None = None
        self.collection_mapper = get_collection_mapper()
        self._initialized = False

    @classmethod
    async def initialize(cls):
        """初始化增强版知识图谱"""
        if cls._instance is None:
            cls._instance = cls()
            await cls._instance._init_components()
            await cls._instance._load_knowledge_base()
            cls._instance._initialized = True
            logger.info("✅ 增强版专利知识图谱初始化完成 (GraphRAG Ready)")
        return cls._instance

    @classmethod
    def get_instance(cls) -> EnhancedPatentKnowledgeGraph:
        """获取单例实例"""
        if cls._instance is None:
            raise RuntimeError("EnhancedPatentKnowledgeGraph未初始化,请先调用initialize()")
        return cls._instance

    async def _init_components(self):
        """初始化组件"""
        try:
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

            # 初始化重排序引擎
            self.reranker = await get_reranker()
            logger.info("✅ 重排序引擎初始化完成")

        except Exception as e:
            logger.error(f"❌ 组件初始化失败: {e}")
            raise

    async def _load_knowledge_base(self):
        """加载知识库(保持向后兼容)"""
        try:
            # 这里可以加载种子数据
            logger.info("📚 开始加载知识库...")
            # await self._load_patent_rules()
            # await self._load_technology_knowledge()
            # await self._load_legal_knowledge()
            logger.info("✅ 知识库加载完成")
        except Exception as e:
            logger.warning(f"⚠️ 知识库加载警告: {e}")

    async def add_node(self, node_data: dict[str, Any]) -> bool:
        """
        添加节点(使用优化的集合映射)

        Args:
            node_data: 节点数据,包含node_id, node_type, title, description, properties

        Returns:
            bool: 是否添加成功
        """
        try:
            node_id = node_data["node_id"]
            node_type = node_data["node_type"]
            title = node_data["title"]
            description = node_data["description"]
            properties = node_data.get("properties", {})

            # 1. 确定目标集合
            collection_type = self.collection_mapper.map_node_to_collection(
                node_type=node_type, content=description, title=title
            )

            # 2. 保存到PostgreSQL
            success = await self.pg_store.add_node(
                node_id=node_id,
                node_type=node_type,
                name=title,
                content=description,
                properties={**properties, "collection_type": collection_type.value},
            )

            if not success:
                logger.error(f"❌ 节点保存到PostgreSQL失败: {node_id}")
                return False

            # 3. 生成向量
            text_to_embed = f"{title} {description}"
            embedding_result = await self.embedding_service.embed_text(
                text=text_to_embed, module_type=ModuleType.KNOWLEDGE
            )

            if not embedding_result or "vector" not in embedding_result:
                logger.error(f"❌ 节点向量化失败: {node_id}")
                # 即使向量化失败,PG中已经有数据,所以返回True
                return True

            vector = embedding_result["vector"]

            # 4. 保存到Qdrant(使用新的集合映射)
            payload = {
                "node_id": node_id,
                "type": node_type,
                "title": title,
                "description": description,
                "properties": properties,
            }

            await self.vector_adapter.add_vectors(
                collection_type.value,  # 使用集合枚举值
                [{"id": node_id, "vector": vector, "payload": payload}],
            )

            logger.info(f"✅ 节点添加成功: {node_id} -> {collection_type.value}")
            return True

        except Exception as e:
            logger.error(f"❌ 添加节点失败: {e}")
            return False

    async def search_hybrid(
        self,
        query: str,
        query_type: QueryType = QueryType.GENERAL_SEARCH,
        config: HybridSearchConfig | None = None,
        node_types: list[str] | None = None,
    ) -> list[SearchResult]:
        """
        混合检索(Vector + Graph + Text)

        Args:
            query: 查询文本
            query_type: 查询类型
            config: 检索配置
            node_types: 节点类型过滤

        Returns:
            list[SearchResult]: 检索结果列表
        """
        if config is None:
            config = HybridSearchConfig()

        try:
            # 1. 获取检索策略
            search_strategy = self.collection_mapper.get_search_strategy(query_type.value)
            logger.info(f"🔍 检索策略: {[col.value for col in search_strategy]}")

            # 2. 生成查询向量
            embedding_result = await self.embedding_service.embed_text(
                text=query, module_type=ModuleType.QUERY
            )

            if not embedding_result or "vector" not in embedding_result:
                logger.error("❌ 查询向量化失败")
                return []

            query_vector = embedding_result["vector"]

            # 3. 并行执行多路检索
            vector_results, graph_results, text_results = await asyncio.gather(
                self._vector_search(query_vector, search_strategy, config),
                self._graph_traversal_search(query, node_types, config),
                self._full_text_search(query, node_types, config),
                return_exceptions=True,
            )

            # 4. 处理异常结果
            if isinstance(vector_results, Exception):
                logger.error(f"❌ 向量检索失败: {vector_results}")
                vector_results = []
            if isinstance(graph_results, Exception):
                logger.error(f"❌ 图检索失败: {graph_results}")
                graph_results = []
            if isinstance(text_results, Exception):
                logger.error(f"❌ 文本检索失败: {text_results}")
                text_results = []

            # 5. 融合结果(RRF算法)
            merged_results = self._reciprocal_rank_fusion(
                vector_results, graph_results, text_results, config
            )

            # 6. 重排序(使用BGE重排序引擎)
            reranked_results = await self._rerank_results(query, merged_results, config)

            # 7. 图增强(获取相关节点)
            enhanced_results = await self._enhance_with_graph_context(reranked_results, config)

            logger.info(f"✅ 混合检索完成: 返回{len(enhanced_results)}个结果(已重排序)")
            return enhanced_results

        except Exception as e:
            logger.error(f"❌ 混合检索失败: {e}")
            return []

    async def _vector_search(
        self,
        query_vector: list[float],
        search_strategy: list[CollectionType],
        config: HybridSearchConfig,
    ) -> list[SearchResult]:
        """向量检索"""
        results = []

        for collection_type in search_strategy:
            try:
                search_results = await self.vector_adapter.search_vectors(
                    collection_type=collection_type.value,
                    query_vector=query_vector,
                    limit=config.top_k,
                    threshold=0.6,
                )

                for result in search_results:
                    search_result = SearchResult(
                        node_id=result["id"],
                        title=result["payload"].get("title", ""),
                        content=result["payload"].get("description", ""),
                        score=result["score"],
                        collection_type=collection_type,
                        node_type=result["payload"].get("type", ""),
                        context=result.get("context", {}),
                    )
                    results.append(search_result)

            except Exception as e:
                logger.warning(f"⚠️ 向量检索失败 {collection_type.value}: {e}")

        return results

    async def _graph_traversal_search(
        self, query: str, node_types: list[str], config: HybridSearchConfig
    ) -> list[SearchResult]:
        """图遍历检索"""
        results = []

        try:
            # 基于关键词查询图节点
            graph_nodes = await self.pg_store.search_nodes(
                keyword=query, node_types=node_types, limit=config.top_k
            )

            for node in graph_nodes:
                # 获取相连节点
                connected_nodes = await self.pg_store.get_connected_nodes(
                    node["node_id"], max_depth=config.max_hops
                )

                search_result = SearchResult(
                    node_id=node["node_id"],
                    title=node["name"],
                    content=node["content"],
                    score=0.7,  # 图检索基础分数
                    collection_type=self.collection_mapper.map_node_to_collection(
                        node["node_type"]
                    ),
                    node_type=node["node_type"],
                    related_nodes=connected_nodes,
                )
                results.append(search_result)

        except Exception as e:
            logger.warning(f"⚠️ 图检索失败: {e}")

        return results

    async def _full_text_search(
        self, query: str, node_types: list[str], config: HybridSearchConfig
    ) -> list[SearchResult]:
        """全文检索"""
        results = []

        try:
            # 使用PostgreSQL的全文检索功能
            text_results = await self.pg_store.full_text_search(
                query=query, node_types=node_types, limit=config.top_k
            )

            for node in text_results:
                search_result = SearchResult(
                    node_id=node["node_id"],
                    title=node["name"],
                    content=node["content"],
                    score=node.get("rank", 0.5),
                    collection_type=self.collection_mapper.map_node_to_collection(
                        node["node_type"]
                    ),
                    node_type=node["node_type"],
                )
                results.append(search_result)

        except Exception as e:
            logger.warning(f"⚠️ 全文检索失败: {e}")

        return results

    async def _rerank_results(
        self, query: str, results: list[SearchResult], config: HybridSearchConfig
    ) -> list[SearchResult]:
        """
        使用重排序引擎重新排序结果

        Args:
            query: 查询文本
            results: 待重排序的搜索结果
            config: 检索配置

        Returns:
            list[SearchResult]: 重排序后的结果
        """
        if not results or not hasattr(self, "reranker"):
            logger.info("⚠️ 跳过重排序:无结果或重排序引擎未初始化")
            return results

        try:
            # 准备重排序数据
            rerank_items = []
            for result in results:
                rerank_item = {
                    "id": result.node_id,
                    "content": f"{result.title} {result.content}",
                    "original_score": result.score,
                }
                rerank_items.append(rerank_item)

            # 配置重排序参数
            rerank_config = RerankConfig(
                mode=RerankMode.TOP_K_RERANK,
                top_k=len(rerank_items),
                final_top_k=config.re_rank_top_k,
                use_cache=True,
            )

            # 执行重排序
            rerank_result = await self.reranker.rerank(query, rerank_items, rerank_config)

            if rerank_result and rerank_result.reranked_items:
                # 创建新的搜索结果列表
                reranked_search_results = []

                for i, rerank_item in enumerate(rerank_result.reranked_items):
                    # 找到原始的搜索结果
                    original_result = next(
                        (r for r in results if r.node_id == rerank_item["id"]), None
                    )

                    if original_result:
                        # 更新分数
                        updated_result = SearchResult(
                            node_id=original_result.node_id,
                            title=original_result.title,
                            content=original_result.content,
                            score=rerank_result.reranked_scores[i],  # 使用重排序后的分数
                            collection_type=original_result.collection_type,
                            node_type=original_result.node_type,
                            context=original_result.context,
                            related_nodes=original_result.related_nodes,
                        )
                        reranked_search_results.append(updated_result)

                logger.info(f"✅ 重排序完成: {len(results)} -> {len(reranked_search_results)} 项")
                return reranked_search_results
            else:
                logger.warning("⚠️ 重排序失败,返回原始结果")
                return results

        except Exception as e:
            logger.error(f"❌ 重排序异常: {e}")
            return results

    def _reciprocal_rank_fusion(
        self,
        vector_results: list[SearchResult],
        graph_results: list[SearchResult],
        text_results: list[SearchResult],
        config: HybridSearchConfig,
    ) -> list[SearchResult]:
        """
        倒数排名融合算法

        Args:
            vector_results: 向量检索结果
            graph_results: 图检索结果
            text_results: 文本检索结果
            config: 检索配置

        Returns:
            list[SearchResult]: 融合后的结果
        """
        k = 60  # RRF常数,通常设为60
        fused_scores = {}

        # 合并所有结果的ID
        vector_results + graph_results + text_results

        # 处理向量检索结果
        for i, result in enumerate(vector_results):
            score = 1.0 / (k + i + 1)
            if result.node_id not in fused_scores:
                fused_scores[result.node_id] = {"result": result, "score": 0}
            fused_scores[result.node_id]["score"] += config.vector_weight * score

        # 处理图检索结果
        for i, result in enumerate(graph_results):
            score = 1.0 / (k + i + 1)
            if result.node_id not in fused_scores:
                fused_scores[result.node_id] = {"result": result, "score": 0}
            fused_scores[result.node_id]["score"] += config.graph_weight * score

        # 处理文本检索结果
        for i, result in enumerate(text_results):
            score = 1.0 / (k + i + 1)
            if result.node_id not in fused_scores:
                fused_scores[result.node_id] = {"result": result, "score": 0}
            fused_scores[result.node_id]["score"] += config.text_weight * score

        # 排序并返回Top结果
        sorted_results = sorted(fused_scores.values(), key=lambda x: x["score"], reverse=True)

        final_results = []
        for item in sorted_results[: config.re_rank_top_k]:
            result = item["result"]
            result.score = item["score"]
            final_results.append(result)

        return final_results

    async def _enhance_with_graph_context(
        self, results: list[SearchResult], config: HybridSearchConfig
    ) -> list[SearchResult]:
        """
        使用图上下文增强结果

        Args:
            results: 检索结果
            config: 检索配置

        Returns:
            list[SearchResult]: 增强后的结果
        """
        for result in results:
            try:
                # 获取节点的1-hop邻居
                connected_nodes = await self.pg_store.get_connected_nodes(
                    result.node_id, max_depth=1
                )

                # 添加到相关节点中
                result.related_nodes = connected_nodes[:5]  # 限制最多5个相关节点

            except Exception as e:
                logger.warning(f"⚠️ 图上下文增强失败 {result.node_id}: {e}")

        return results

    async def get_node_with_context(self, node_id: str, max_hops: int = 2) -> dict[str, Any] | None:
        """
        获取节点及其图上下文

        Args:
            node_id: 节点ID
            max_hops: 最大跳数

        Returns:
            Optional[Dict]: 节点信息及上下文
        """
        try:
            # 获取基础节点信息
            node = await self.pg_store.get_node(node_id)
            if not node:
                return None

            # 获取图上下文
            connected_nodes = await self.pg_store.get_connected_nodes(node_id, max_depth=max_hops)

            return {
                "node": node,
                "context": {
                    "connected_nodes": connected_nodes,
                    "hop_count": max_hops,
                    "total_connections": len(connected_nodes),
                },
            }

        except Exception as e:
            logger.error(f"❌ 获取节点上下文失败 {node_id}: {e}")
            return None

    async def cleanup(self):
        """清理资源"""
        try:
            if self.pg_store:
                await self.pg_store.close()
            if self.vector_adapter:
                await self.vector_adapter.close()
            if self.embedding_service:
                await self.embedding_service.close()
            logger.info("✅ 增强版知识图谱资源清理完成")
        except Exception as e:
            logger.error(f"❌ 资源清理失败: {e}")
