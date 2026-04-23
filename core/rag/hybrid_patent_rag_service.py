#!/usr/bin/env python3
from __future__ import annotations
"""
混合专利RAG服务 - 法规与决定书融合检索
Hybrid Patent RAG Service - Regulations & Decisions Integration

统一处理专利法律法规和决定书案例的检索需求
"""

import asyncio
import sys
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from core.logging_config import setup_logging

# 添加Athena平台路径
sys.path.append("/Users/xujian/Athena工作平台")

# 导入组件
from qdrant_client import QdrantClient
from qdrant_client.models import Filter

from core.nlp.bge_embedding_service import get_bge_service
from core.rag.athena_hybrid_rag_service import AthenaHybridRAGService, RAGQuery, SearchResult

# 配置日志
# setup_logging()  # 日志配置已移至模块导入
logger = setup_logging()


class DocumentType(Enum):
    """文档类型枚举"""

    REGULATION = "regulation"  # 法律法规
    DECISION_REVIEW = "decision_review"  # 复审决定
    DECISION_INVALID = "decision_invalid"  # 无效决定
    MIXED = "mixed"  # 混合类型


class QueryIntent(Enum):
    """查询意图枚举"""

    LEGAL_RESEARCH = "legal_research"  # 法律研究
    CASE_REFERENCE = "case_reference"  # 案例参考
    PRACTICAL_GUIDANCE = "practical_guidance"  # 实务指导
    MIXED_QUERY = "mixed_query"  # 混合查询


@dataclass
class PatentRAGQuery:
    """专利RAG查询请求"""

    query: str
    document_types: list[DocumentType] = field(default_factory=lambda: [DocumentType.MIXED])
    intent: QueryIntent = QueryIntent.MIXED_QUERY
    top_k: int = 10
    rerank_method: str = "hybrid"
    include_metadata: bool = True
    filters: Optional[dict[str, Any]] = None
    # 决定书特有参数
    decision_date_range: Optional[tuple[str, str]] | None = None  # 开始日期,结束日期
    patent_numbers: Optional[list[str]] = None  # 特定专利号
    case_types: Optional[list[str]] = None  # 案件类型


@dataclass
class PatentRAGResponse:
    """专利RAG查询响应"""

    query: str
    intent: QueryIntent
    results_by_type: dict[str, list[SearchResult]]
    combined_results: list[SearchResult]
    statistics: dict[str, Any]
    processing_time: float
    metadata: dict[str, Any]
class HybridPatentRAGService:
    """混合专利RAG服务"""

    def __init__(self):
        """初始化混合专利RAG服务"""
        self.name = "混合专利RAG服务"
        self.version = "1.0.0"

        logger.info("🔄 初始化混合专利RAG服务...")

        # 初始化核心服务
        self.athena_rag_service = AthenaHybridRAGService()
        self.bge_service = None  # 将在异步初始化中设置
        self.qdrant_client = QdrantClient(host="localhost", port=6333)

        # 集合配置
        self.collections = {
            DocumentType.REGULATION: "patent_laws_simple",
            DocumentType.DECISION_REVIEW: "patent_decisions_review",
            DocumentType.DECISION_INVALID: "patent_decisions_invalid",
        }

        # 查询意图识别关键词
        self.intent_keywords = {
            QueryIntent.LEGAL_RESEARCH: [
                "法律规定",
                "法条",
                "法规",
                "条款",
                "依据",
                "如何规定",
                "什么是",
                "定义",
                "适用",
                "条件",
                "程序",
            ],
            QueryIntent.CASE_REFERENCE: [
                "案例",
                "决定",
                "判例",
                "先例",
                "类似案例",
                "参考",
                "如何处理",
                "实际案例",
                "实务",
                "操作",
            ],
            QueryIntent.PRACTICAL_GUIDANCE: [
                "如何申请",
                "怎么办理",
                "流程",
                "步骤",
                "注意事项",
                "建议",
                "经验",
                "技巧",
                "最佳实践",
            ],
        }

        # 智能路由权重
        self.routing_weights = {
            QueryIntent.LEGAL_RESEARCH: {
                DocumentType.REGULATION: 0.7,
                DocumentType.DECISION_REVIEW: 0.2,
                DocumentType.DECISION_INVALID: 0.1,
            },
            QueryIntent.CASE_REFERENCE: {
                DocumentType.REGULATION: 0.2,
                DocumentType.DECISION_REVIEW: 0.4,
                DocumentType.DECISION_INVALID: 0.4,
            },
            QueryIntent.PRACTICAL_GUIDANCE: {
                DocumentType.REGULATION: 0.4,
                DocumentType.DECISION_REVIEW: 0.3,
                DocumentType.DECISION_INVALID: 0.3,
            },
            QueryIntent.MIXED_QUERY: {
                DocumentType.REGULATION: 0.4,
                DocumentType.DECISION_REVIEW: 0.3,
                DocumentType.DECISION_INVALID: 0.3,
            },
        }

        logger.info(f"✅ {self.name} 初始化完成")

    async def _ensure_bge_service(self):
        """确保BGE服务已初始化"""
        if self.bge_service is None:
            self.bge_service = await get_bge_service()

    def _detect_query_intent(self, query: str) -> QueryIntent:
        """检测查询意图"""
        query_lower = query.lower()
        intent_scores = {}

        for intent, keywords in self.intent_keywords.items():
            score = sum(1 for keyword in keywords if keyword in query_lower)
            intent_scores[intent] = score

        # 返回得分最高的意图
        if max(intent_scores.values()) == 0:
            return QueryIntent.MIXED_QUERY

        return max(intent_scores, key=intent_scores.get)

    def _calculate_search_weights(self, query: PatentRAGQuery) -> dict[DocumentType, float]:
        """计算各类型文档的搜索权重"""
        # 基于意图的权重
        base_weights = self.routing_weights.get(
            query.intent, self.routing_weights[QueryIntent.MIXED_QUERY]
        )

        # 如果用户指定了文档类型,调整权重
        if query.document_types and DocumentType.MIXED not in query.document_types:
            for doc_type in DocumentType:
                if doc_type not in query.document_types:
                    base_weights[doc_type] = 0.0
                else:
                    base_weights[doc_type] = 1.0 / len(query.document_types)

        return base_weights

    async def search(self, query: PatentRAGQuery) -> PatentRAGResponse:
        """执行混合专利检索"""
        start_time = time.time()

        logger.info(f"🔍 执行混合专利检索: {query.query[:50]}...")
        logger.info(f"   - 查询意图: {query.intent.value}")
        logger.info(f"   - 文档类型: {[dt.value for dt in query.document_types]}")

        try:
            # 确保BGE服务已初始化
            await self._ensure_bge_service()

            # 检测查询意图
            if query.intent == QueryIntent.MIXED_QUERY:
                query.intent = self._detect_query_intent(query.query)
                logger.info(f"   - 检测到的意图: {query.intent.value}")

            # 计算搜索权重
            search_weights = self._calculate_search_weights(query)
            logger.info(f"   - 搜索权重: {search_weights}")

            # 并行搜索各类型文档
            results_by_type = {}
            search_tasks = []

            for doc_type, weight in search_weights.items():
                if weight > 0:
                    task = self._search_document_type(query, doc_type, weight)
                    search_tasks.append((doc_type, task))

            # 执行并行搜索
            if search_tasks:
                completed_tasks = await asyncio.gather(
                    *[task for _, task in search_tasks], return_exceptions=True
                )

                for (doc_type, _), result in zip(search_tasks, completed_tasks, strict=False):
                    if isinstance(result, Exception):
                        logger.error(f"❌ 搜索{doc_type.value}失败: {result}")
                        results_by_type[doc_type.value] = []
                    else:
                        results_by_type[doc_type.value] = result

            # 智能合并结果
            combined_results = await self._combine_search_results(
                query, results_by_type, search_weights
            )

            # 生成统计信息
            statistics = self._generate_statistics(results_by_type, search_weights)

            # 构建响应
            response = PatentRAGResponse(
                query=query.query,
                intent=query.intent,
                results_by_type=results_by_type,
                combined_results=combined_results,
                statistics=statistics,
                processing_time=time.time() - start_time,
                metadata={
                    "search_weights": search_weights,
                    "collections_used": list(search_weights.keys()),
                    "intent_confidence": self._calculate_intent_confidence(query.query),
                },
            )

            logger.info(
                f"✅ 混合检索完成: {len(combined_results)} 个结果,耗时 {response.processing_time:.3f}秒"
            )
            return response

        except Exception as e:
            logger.error(f"❌ 混合检索失败: {e}")
            # 返回错误响应
            return PatentRAGResponse(
                query=query.query,
                intent=query.intent,
                results_by_type={},
                combined_results=[],
                statistics={},
                processing_time=time.time() - start_time,
                metadata={"error": str(e)},
            )

    async def _search_document_type(
        self, query: PatentRAGQuery, doc_type: DocumentType, weight: float
    ) -> list[SearchResult]:
        """搜索特定类型的文档"""
        collection_name = self.collections.get(doc_type)
        if not collection_name:
            logger.warning(f"⚠️ 未配置{doc_type.value}的集合")
            return []

        try:
            # 构建传统RAG查询
            rag_query = RAGQuery(
                query=query.query,
                top_k=max(10, int(query.top_k * 1.5)),  # 获取更多结果用于合并
                rerank_method=query.rerank_method,
                include_metadata=query.include_metadata,
                filters=self._build_collection_filters(query, doc_type),
            )

            # 如果是法规类型,使用现有服务
            if doc_type == DocumentType.REGULATION:
                response = await self.athena_rag_service.search(rag_query)
                # 应用权重调整分数
                for result in response.results:
                    result.score *= weight
                return response.results

            # 决定书类型使用专门的处理
            else:
                return await self._search_decisions(rag_query, collection_name, weight)

        except Exception as e:
            logger.error(f"❌ 搜索{doc_type.value}失败: {e}")
            return []

    async def _search_decisions(
        self, query: RAGQuery, collection_name: str, weight: float
    ) -> list[SearchResult]:
        """搜索决定书文档"""
        try:
            # 生成查询向量
            query_embedding = await self.bge_service.encode([query.query])
            if isinstance(query_embedding.embeddings, list) and len(query_embedding.embeddings) > 0:
                query_vector = (
                    query_embedding.embeddings[0]
                    if isinstance(query_embedding.embeddings[0], list)
                    else query_embedding.embeddings[0].tolist()
                )
            else:
                query_vector = (
                    query_embedding.embeddings.tolist()
                    if hasattr(query_embedding.embeddings, "tolist")
                    else query_embedding.embeddings
                )

            # 执行搜索
            search_result = self.qdrant_client.search(
                collection_name=collection_name,
                query_vector=query_vector,
                limit=query.top_k,
                query_filter=query.filters,
                with_payload=True,
                score_threshold=0.3,
            )

            # 转换结果并应用权重
            results = []
            for hit in search_result:
                result = SearchResult(
                    id=str(hit.id),
                    content=hit.payload.get("content", ""),
                    score=hit.score * weight,  # 应用权重
                    metadata=hit.payload.get("metadata", {}),
                    source=hit.payload.get("source", ""),
                    doc_type="专利决定书",
                )
                results.append(result)

            return results

        except Exception as e:
            logger.error(f"❌ 决定书搜索失败: {e}")
            return []

    def _build_collection_filters(
        self, query: PatentRAGQuery, doc_type: DocumentType
    ) -> Filter | None:
        """构建集合过滤器"""
        filters = []

        # 决定书特有过滤条件
        if doc_type in [DocumentType.DECISION_REVIEW, DocumentType.DECISION_INVALID]:
            if query.decision_date_range:
                start_date, end_date = query.decision_date_range
                filters.append(
                    {"key": "decision_date", "range": {"gte": start_date, "lte": end_date}}
                )

            if query.patent_numbers:
                filters.append({"key": "patent_number", "match": {"any": query.patent_numbers}})

            if query.case_types:
                filters.append({"key": "case_type", "match": {"any": query.case_types}})

        # 用户自定义过滤条件
        if query.filters:
            filters.extend(query.filters)

        return Filter(must=filters) if filters else None

    async def _combine_search_results(
        self,
        query: PatentRAGQuery,
        results_by_type: dict[str, list[SearchResult]],
        weights: dict[DocumentType, float],
    ) -> list[SearchResult]:
        """智能合并搜索结果"""
        all_results = []

        # 收集所有结果
        for doc_type, results in results_by_type.items():
            for result in results:
                # 添加类型标记
                result.metadata["source_type"] = doc_type
                all_results.append(result)

        if not all_results:
            return []

        # 去重(基于内容相似度)
        deduplicated_results = await self._deduplicate_results(all_results)

        # 重新排序
        if query.rerank_method == "hybrid":
            # 使用混合重排序
            reranker = self.athena_rag_service.reranker
            reranked = await reranker.rerank_search_results(
                query.query, deduplicated_results, "hybrid"
            )
            return reranked[: query.top_k]
        else:
            # 按分数排序
            deduplicated_results.sort(key=lambda x: x.score, reverse=True)
            return deduplicated_results[: query.top_k]

    async def _deduplicate_results(
        self, results: list[SearchResult], similarity_threshold: float = 0.9
    ) -> list[SearchResult]:
        """基于相似度去重"""
        if len(results) <= 1:
            return results

        deduplicated = []
        content_hashes = {}

        for result in results:
            # 简单的内容哈希去重
            content_hash = hash(result.content[:200])  # 使用前200字符的哈希

            if content_hash not in content_hashes:
                deduplicated.append(result)
                content_hashes[content_hash] = result
            else:
                # 如果分数更高,替换现有结果
                if result.score > content_hashes[content_hash].score:
                    deduplicated.remove(content_hashes[content_hash])
                    deduplicated.append(result)
                    content_hashes[content_hash] = result

        return deduplicated

    def _generate_statistics(
        self, results_by_type: dict[str, list[SearchResult]], weights: dict[DocumentType, float]
    ) -> dict[str, Any]:
        """生成统计信息"""
        total_results = sum(len(results) for results in results_by_type.values())

        stats = {
            "total_results": total_results,
            "results_by_type": {
                doc_type: len(results) for doc_type, results in results_by_type.items()
            },
            "search_weights": {doc_type.value: weight for doc_type, weight in weights.items()},
            "type_distribution": {},
        }

        # 计算类型分布
        if total_results > 0:
            for doc_type, results in results_by_type.items():
                stats["type_distribution"][doc_type] = len(results) / total_results

        return stats

    def _calculate_intent_confidence(self, query: str) -> float:
        """计算意图识别置信度"""
        query_lower = query.lower()
        max_matches = 0
        total_matches = 0

        for _intent, keywords in self.intent_keywords.items():
            matches = sum(1 for keyword in keywords if keyword in query_lower)
            total_matches += matches
            max_matches = max(max_matches, matches)

        if total_matches == 0:
            return 0.0

        return max_matches / total_matches

    async def get_service_status(self) -> dict[str, Any]:
        """获取服务状态"""
        # 检查集合状态
        available_collections = set()
        try:
            collections = self.qdrant_client.get_collections().collections
            available_collections = {c.name for c in collections}
        except Exception as e:
            logger.error(f"❌ 获取集合列表失败: {e}")

        collection_status = {}
        for doc_type, collection_name in self.collections.items():
            collection_status[doc_type.value] = {
                "collection_name": collection_name,
                "available": collection_name in available_collections,
                "configured": True,
            }

        return {
            "service_name": self.name,
            "version": self.version,
            "collections": collection_status,
            "routing_weights": {
                intent.value: {dt.value: weight for dt, weight in weights.items()}
                for intent, weights in self.routing_weights.items()
            },
            "supported_intents": [intent.value for intent in QueryIntent],
            "supported_document_types": [dt.value for dt in DocumentType],
        }


async def main():
    """测试混合专利RAG服务"""
    print("🚀 混合专利RAG服务测试")
    print("=" * 60)

    service = HybridPatentRAGService()

    # 显示服务状态
    status = await service.get_service_status()
    print("📊 服务状态:")
    print(f"   - 服务名称: {status['service_name']}")
    print(f"   - 版本: {status['version']}")

    print("\n📚 集合状态:")
    for doc_type, info in status["collections"].items():
        status_icon = "✅" if info["available"] else "❌"
        print(f"   {status_icon} {doc_type}: {info['collection_name']}")

    # 测试查询
    print("\n🔍 测试混合检索:")

    test_queries = [
        {
            "query": "发明专利的保护期是多久?",
            "document_types": [DocumentType.REGULATION],
            "intent": QueryIntent.LEGAL_RESEARCH,
        },
        {
            "query": "专利复审的成功案例有哪些?",
            "document_types": [DocumentType.DECISION_REVIEW],
            "intent": QueryIntent.CASE_REFERENCE,
        },
        {
            "query": "专利无效宣告的条件是什么?",
            "document_types": [DocumentType.MIXED],
            "intent": QueryIntent.MIXED_QUERY,
        },
    ]

    for i, test_data in enumerate(test_queries):
        print(f"\n📝 测试查询 {i+1}: {test_data['query']}")

        query = PatentRAGQuery(
            query=test_data["query"],
            document_types=test_data["document_types"],
            intent=test_data["intent"],
            top_k=5,
        )

        response = await service.search(query)

        print("📊 检索结果:")
        print(f"   - 检测意图: {response.intent.value}")
        print(f"   - 总结果数: {len(response.combined_results)}")
        print(f"   - 按类型分布: {response.statistics.get('results_by_type', {})}")
        print(f"   - 处理时间: {response.processing_time:.3f} 秒")

        for j, result in enumerate(response.combined_results[:3]):
            source_type = result.metadata.get("source_type", "unknown")
            print(f"   {j+1}. [{source_type}] {result.content[:60]}... (分数: {result.score:.3f})")


# 入口点: @async_main装饰器已添加到main函数
