#!/usr/bin/env python3
"""
Athena平台LlamaIndex重排序器集成
Athena Platform LlamaIndex Reranker Integration

结合Athena检索结果 + LlamaIndex重排序算法
"""

import logging
import sys
from dataclasses import dataclass
from typing import Any


from core.logging_config import setup_logging

# 添加Athena平台路径
sys.path.append("/Users/xujian/Athena工作平台")

# LlamaIndex组件
try:
    from llama_index.core import NodeWithScore, QueryBundle
    from llama_index.core.postprocessor import (
        KeywordRelevancyPostprocessor,
        LongContextReorder,
        SimilarityPostprocessor,
        SimilarityScorer,
    )
    from llama_index.core.schema import Node

    LLAMAINDEX_AVAILABLE = True
except ImportError as e:
    LLAMAINDEX_AVAILABLE = False
    logging.warning(f"LlamaIndex重排序器不可用: {e}")

# Athena核心组件
from core.nlp.bge_embedding_service import get_bge_service

# 配置日志
# setup_logging()  # 日志配置已移至模块导入
logger = setup_logging()


@dataclass
class SearchResult:
    """搜索结果"""

    id: str
    content: str
    score: float
    metadata: dict[str, Any]
    source: str
    doc_type: str


class AthenaLlamaIndexReranker:
    """Athena平台LlamaIndex重排序器"""

    def __init__(self):
        """初始化重排序器"""
        self.name = "Athena-LlamaIndex重排序器"
        self.version = "1.0.0"

        # 初始化BGE服务
        self.bge_service = None  # 将在异步初始化中设置

        # LlamaIndex可用性
        self.llamaindex_available = LLAMAINDEX_AVAILABLE

        # 配置
        self.config = {
            "top_k": 10,
            "similarity_threshold": 0.5,
            "keyword_weight": 0.3,
            "semantic_weight": 0.7,
            "diversity_factor": 0.1,
        }

        # 初始化LlamaIndex组件
        self._init_llamaindex_components()

        logger.info(f"✅ {self.name} 初始化完成")

    async def _ensure_bge_service(self):
        """确保BGE服务已初始化"""
        if self.bge_service is None:
            self.bge_service = await get_bge_service()

    def _init_llamaindex_components(self) -> Any:
        """初始化LlamaIndex组件"""
        if not self.llamaindex_available:
            logger.warning("⚠️ LlamaIndex不可用,将使用内置重排序算法")
            self.similarity_postprocessor = None
            self.keyword_postprocessor = None
            self.similarity_scorer = None
            self.long_context_reorder = None
        else:
            try:
                self.similarity_postprocessor = SimilarityPostprocessor(
                    similarity_cutoff=self.config["similarity_threshold"]
                )
                self.keyword_postprocessor = KeywordRelevancyPostprocessor(
                    similarity_cutoff=self.config["similarity_threshold"]
                )
                self.similarity_scorer = SimilarityScorer()
                self.long_context_reorder = LongContextReorder()
                logger.info("✅ LlamaIndex重排序组件初始化成功")
            except Exception as e:
                logger.error(f"❌ LlamaIndex组件初始化失败: {e}")
                self.llamaindex_available = False

    async def rerank_search_results(
        self, query: str, search_results: list[SearchResult], method: str = "hybrid"
    ) -> list[SearchResult]:
        """重排序搜索结果"""
        logger.info(f"🔄 重排序 {len(search_results)} 个搜索结果,方法: {method}")

        if not search_results:
            return []

        # 确保BGE服务已初始化
        await self._ensure_bge_service()

        if method == "llamaindex_similarity" and self.llamaindex_available:
            return await self._rerank_with_llamaindex_similarity(query, search_results)
        elif method == "llamaindex_keyword" and self.llamaindex_available:
            return await self._rerank_with_llamaindex_keyword(query, search_results)
        elif method == "llamaindex_hybrid" and self.llamaindex_available:
            return await self._rerank_with_llamaindex_hybrid(query, search_results)
        elif method == "athena_optimized":
            return await self._rerank_with_athena_optimized(query, search_results)
        else:
            # 默认混合重排序
            return await self._rerank_with_hybrid(query, search_results)

    async def _rerank_with_llamaindex_similarity(
        self, query: str, results: list[SearchResult]
    ) -> list[SearchResult]:
        """使用LlamaIndex相似度重排序"""
        logger.info("🔍 使用LlamaIndex相似度重排序...")

        try:
            # 转换为LlamaIndex格式
            nodes_with_scores = []
            for result in results:
                node = Node(text=result.content, metadata=result.metadata)
                node_with_score = NodeWithScore(node=node, score=result.score)
                nodes_with_scores.append(node_with_score)

            # 创建查询bundle
            query_bundle = QueryBundle(query_str=query)

            # 使用相似度后处理器
            reranked_nodes = self.similarity_postprocessor.postprocess_nodes(
                nodes_with_scores, query_bundle=query_bundle
            )

            # 转换回Athena格式
            reranked_results = []
            for node_with_score in reranked_nodes[: self.config["top_k"]]:
                # 找到原始结果中的metadata
                original_result = next(
                    (r for r in results if r.content == node_with_score.node.text), None
                )
                if original_result:
                    reranked_result = SearchResult(
                        id=original_result.id,
                        content=node_with_score.node.text,
                        score=node_with_score.score,
                        metadata=node_with_score.node.metadata,
                        source=original_result.source,
                        doc_type=original_result.doc_type,
                    )
                    reranked_results.append(reranked_result)

            logger.info(f"✅ 相似度重排序完成,返回 {len(reranked_results)} 个结果")
            return reranked_results

        except Exception as e:
            logger.error(f"❌ LlamaIndex相似度重排序失败: {e}")
            return await self._rerank_with_athena_optimized(query, results)

    async def _rerank_with_llamaindex_keyword(
        self, query: str, results: list[SearchResult]
    ) -> list[SearchResult]:
        """使用LlamaIndex关键词相关性重排序"""
        logger.info("🔍 使用LlamaIndex关键词重排序...")

        try:
            # 转换为LlamaIndex格式
            nodes_with_scores = []
            for result in results:
                node = Node(text=result.content, metadata=result.metadata)
                node_with_score = NodeWithScore(node=node, score=result.score)
                nodes_with_scores.append(node_with_score)

            # 创建查询bundle
            query_bundle = QueryBundle(query_str=query)

            # 使用关键词相关性后处理器
            reranked_nodes = self.keyword_postprocessor.postprocess_nodes(
                nodes_with_scores, query_bundle=query_bundle
            )

            # 转换回Athena格式
            reranked_results = []
            for node_with_score in reranked_nodes[: self.config["top_k"]]:
                original_result = next(
                    (r for r in results if r.content == node_with_score.node.text), None
                )
                if original_result:
                    reranked_result = SearchResult(
                        id=original_result.id,
                        content=node_with_score.node.text,
                        score=node_with_score.score,
                        metadata=node_with_score.node.metadata,
                        source=original_result.source,
                        doc_type=original_result.doc_type,
                    )
                    reranked_results.append(reranked_result)

            logger.info(f"✅ 关键词重排序完成,返回 {len(reranked_results)} 个结果")
            return reranked_results

        except Exception as e:
            logger.error(f"❌ LlamaIndex关键词重排序失败: {e}")
            return await self._rerank_with_athena_optimized(query, results)

    async def _rerank_with_llamaindex_hybrid(
        self, query: str, results: list[SearchResult]
    ) -> list[SearchResult]:
        """使用LlamaIndex混合重排序"""
        logger.info("🔍 使用LlamaIndex混合重排序...")

        try:
            # 先进行相似度重排序
            similarity_reranked = await self._rerank_with_llamaindex_similarity(query, results)

            # 再进行关键词重排序
            keyword_reranked = await self._rerank_with_llamaindex_keyword(query, results)

            # 合并结果(加权平均)
            combined_scores = {}
            for result in similarity_reranked:
                combined_scores[result.id] = {
                    "result": result,
                    "similarity_score": result.score,
                    "keyword_score": 0.0,
                }

            for result in keyword_reranked:
                if result.id in combined_scores:
                    combined_scores[result.id]["keyword_score"] = result.score
                else:
                    combined_scores[result.id] = {
                        "result": result,
                        "similarity_score": 0.0,
                        "keyword_score": result.score,
                    }

            # 计算混合分数
            reranked_results = []
            for data in combined_scores.values():
                hybrid_score = (
                    self.config["semantic_weight"] * data["similarity_score"]
                    + self.config["keyword_weight"] * data["keyword_score"]
                )

                result = data["result"]
                result.score = hybrid_score
                reranked_results.append(result)

            # 按分数排序
            reranked_results.sort(key=lambda x: x.score, reverse=True)
            reranked_results = reranked_results[: self.config["top_k"]]

            logger.info(f"✅ 混合重排序完成,返回 {len(reranked_results)} 个结果")
            return reranked_results

        except Exception as e:
            logger.error(f"❌ LlamaIndex混合重排序失败: {e}")
            return await self._rerank_with_athena_optimized(query, results)

    async def _rerank_with_athena_optimized(
        self, query: str, results: list[SearchResult]
    ) -> list[SearchResult]:
        """使用Athena优化重排序算法"""
        logger.info("🔍 使用Athena优化重排序算法...")

        try:
            # 生成查询向量
            query_embedding = await self._get_query_embedding(query)

            # 计算语义相似度分数
            for result in results:
                if not hasattr(result, "_semantic_score"):
                    result_embedding = await self._get_embedding(result.content)
                    semantic_score = self._cosine_similarity(query_embedding, result_embedding)
                    result._semantic_score = semantic_score

            # 多维度评分
            for result in results:
                semantic_score = getattr(result, "_semantic_score", 0)
                original_score = result.score

                # 加权综合分数
                hybrid_score = (
                    self.config["semantic_weight"] * semantic_score
                    + self.config["keyword_weight"] * original_score
                )
                result.score = hybrid_score

            # 按分数排序
            reranked_results = sorted(results, key=lambda x: x.score, reverse=True)
            reranked_results = reranked_results[: self.config["top_k"]]

            logger.info(f"✅ Athena优化重排序完成,返回 {len(reranked_results)} 个结果")
            return reranked_results

        except Exception as e:
            logger.error(f"❌ Athena优化重排序失败: {e}")
            # 返回原始结果
            return sorted(results, key=lambda x: x.score, reverse=True)[: self.config["top_k"]]

    async def _rerank_with_hybrid(
        self, query: str, results: list[SearchResult]
    ) -> list[SearchResult]:
        """混合重排序(自适应选择)"""
        if self.llamaindex_available:
            # 优先使用LlamaIndex
            return await self._rerank_with_llamaindex_hybrid(query, results)
        else:
            # 回退到Athena优化
            return await self._rerank_with_athena_optimized(query, results)

    async def _get_query_embedding(self, query: str) -> list[float]:
        """获取查询向量"""
        try:
            result = await self.bge_service.encode([query])
            # 处理EmbeddingResult对象
            if isinstance(result.embeddings, list) and len(result.embeddings) > 0:
                return (
                    result.embeddings[0]
                    if isinstance(result.embeddings[0], list)
                    else result.embeddings[0].tolist()
                )
            else:
                return (
                    result.embeddings.tolist()
                    if hasattr(result.embeddings, "tolist")
                    else result.embeddings
                )
        except Exception as e:
            logger.error(f"❌ 获取查询向量失败: {e}")
            return [0.0] * 1024  # 返回零向量

    async def _get_embedding(self, text: str) -> list[float]:
        """获取文本向量"""
        try:
            result = await self.bge_service.encode([text])
            # 处理EmbeddingResult对象
            if isinstance(result.embeddings, list) and len(result.embeddings) > 0:
                return (
                    result.embeddings[0]
                    if isinstance(result.embeddings[0], list)
                    else result.embeddings[0].tolist()
                )
            else:
                return (
                    result.embeddings.tolist()
                    if hasattr(result.embeddings, "tolist")
                    else result.embeddings
                )
        except Exception as e:
            logger.error(f"❌ 获取文本向量失败: {e}")
            return [0.0] * 1024  # 返回零向量

    def _cosine_similarity(self, vec1: list[float], vec2: list[float]) -> float:
        """计算余弦相似度"""
        try:
            vec1_np = np.array(vec1)
            vec2_np = np.array(vec2)

            if np.all(vec1_np == 0) or np.all(vec2_np == 0):
                return 0.0

            dot_product = np.dot(vec1_np, vec2_np)
            norm1 = np.linalg.norm(vec1_np)
            norm2 = np.linalg.norm(vec2_np)

            if norm1 == 0 or norm2 == 0:
                return 0.0

            return dot_product / (norm1 * norm2)
        except Exception as e:
            logger.error(f"❌ 计算余弦相似度失败: {e}")
            return 0.0


async def main():
    """测试重排序器"""
    print("🚀 Athena-LlamaIndex重排序器测试")
    print("=" * 60)

    reranker = AthenaLlamaIndexReranker()

    # 模拟搜索结果
    test_results = [
        SearchResult(
            id="1",
            content="专利法是保护发明创造的重要法律制度",
            score=0.8,
            metadata={"source": "专利法", "category": "法律条文"},
            source="patent_law.md",
            doc_type="专利法律",
        ),
        SearchResult(
            id="2",
            content="发明专利的保护期为二十年",
            score=0.6,
            metadata={"source": "专利法", "category": "法律条文"},
            source="patent_law.md",
            doc_type="专利法律",
        ),
        SearchResult(
            id="3",
            content="实用新型专利的保护期为十年",
            score=0.5,
            metadata={"source": "专利法", "category": "法律条文"},
            source="patent_law.md",
            doc_type="专利法律",
        ),
    ]

    query = "发明专利的保护期是多长"

    # 测试不同重排序方法
    methods = ["hybrid", "athena_optimized"]
    if reranker.llamaindex_available:
        methods.extend(["llamaindex_similarity", "llamaindex_hybrid"])

    for method in methods:
        print(f"\n🔄 测试重排序方法: {method}")
        reranked = await reranker.rerank_search_results(query, test_results, method)

        print("📊 重排序结果:")
        for i, result in enumerate(reranked):
            print(
                f"   {i+1}. [{result.doc_type}] {result.content[:50]}... (分数: {result.score:.3f})"
            )


# 入口点: @async_main装饰器已添加到main函数
