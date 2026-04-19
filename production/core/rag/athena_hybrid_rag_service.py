#!/usr/bin/env python3
from __future__ import annotations
"""
Athena平台混合架构RAG服务
Athena Platform Hybrid RAG Service

统一入口:Athena核心能力 + LlamaIndex工具
"""

import sys
import time
from dataclasses import dataclass
from typing import Any

from core.logging_config import setup_logging

# 添加Athena平台路径
sys.path.append("/Users/xujian/Athena工作平台")

# 导入组件
from qdrant_client import QdrantClient
from qdrant_client.models import Filter

from core.nlp.bge_embedding_service import get_bge_service
from core.rag.athena_llamaindex_evaluator import AthenaLlamaIndexEvaluator, EvaluationCase
from core.rag.athena_llamaindex_integration import AthenaLlamaIndexProcessor
from core.rag.athena_llamaindex_reranker import AthenaLlamaIndexReranker, SearchResult

# 配置日志
# setup_logging()  # 日志配置已移至模块导入
logger = setup_logging()


@dataclass
class RAGQuery:
    """RAG查询请求"""

    query: str
    top_k: int = 10
    filters: dict[str, Any] | None = None
    rerank_method: str = "hybrid"  # hybrid, athena_optimized, llamaindex_hybrid
    include_metadata: bool = True
    doc_types: list[str] | None = None


@dataclass
class RAGResponse:
    """RAG查询响应"""

    query: str
    results: list[SearchResult]
    total_results: int
    processing_time: float
    method_used: str
    metadata: dict[str, Any]
class AthenaHybridRAGService:
    """Athena混合架构RAG服务"""

    def __init__(self):
        """初始化RAG服务"""
        self.name = "Athena混合架构RAG服务"
        self.version = "1.1.0"  # 新增历史数据导入支持

        logger.info("🔄 初始化混合架构RAG服务...")

        # 初始化组件
        self.document_processor = AthenaLlamaIndexProcessor()
        self.reranker = AthenaLlamaIndexReranker()
        self.evaluator = AthenaLlamaIndexEvaluator()
        self.bge_service = None  # 将在异步初始化中设置
        self.qdrant_client = QdrantClient(host="localhost", port=6333)

        # 配置
        self.config = {
            "default_top_k": 10,
            "max_context_length": 4096,
            "default_collection": "patent_laws_simple",
            "enable_evaluation": True,
            "cache_enabled": True,
        }

        # 缓存(简单实现)
        self.query_cache = {}
        self.cache_ttl = 300  # 5分钟

        # 可用集合
        self.available_collections = self._get_available_collections()

        # 新增:历史数据集合映射
        self.historical_collections = {
            "invalidation_decisions": "patent_invalidation_decisions",
            "chinese_laws": "legal_docs_chinese_laws",
            "patent_laws": "legal_docs_patent_laws",
            "trademark_docs": "legal_docs_trademark_docs",
        }

        logger.info(f"✅ {self.name} 初始化完成")
        logger.info(f"   - 可用集合: {len(self.available_collections)}")
        logger.info(f"   - 默认集合: {self.config['default_collection']}")

    async def _ensure_bge_service(self):
        """确保BGE服务已初始化"""
        if self.bge_service is None:
            self.bge_service = await get_bge_service()

    def _get_available_collections(self) -> list[str]:
        """获取可用集合"""
        try:
            collections = self.qdrant_client.get_collections().collections
            return [c.name for c in collections]
        except Exception as e:
            logger.error(f"❌ 获取集合列表失败: {e}")
            return []

    async def search(self, query: RAGQuery) -> RAGResponse:
        """执行RAG搜索"""
        start_time = time.time()

        logger.info(f"🔍 执行RAG搜索: {query.query[:50]}...")
        logger.info(f"   - Top-K: {query.top_k}")
        logger.info(f"   - 重排序方法: {query.rerank_method}")
        logger.info(f"   - 文档类型: {query.doc_types or '全部'}")

        try:
            # 确保BGE服务已初始化
            await self._ensure_bge_service()

            # 检查缓存
            cache_key = self._get_cache_key(query)
            cached_result = self._get_from_cache(cache_key)
            if cached_result:
                logger.info("✅ 从缓存返回结果")
                return cached_result

            # 执行向量搜索
            search_results = await self._perform_vector_search(query)

            # 应用过滤器
            filtered_results = self._apply_filters(search_results, query)

            # 重排序
            reranked_results = await self.reranker.rerank_search_results(
                query.query, filtered_results, query.rerank_method
            )

            # 限制返回数量
            limited_results = reranked_results[: query.top_k]

            # 构建响应
            response = RAGResponse(
                query=query.query,
                results=limited_results,
                total_results=len(filtered_results),
                processing_time=time.time() - start_time,
                method_used=query.rerank_method,
                metadata={
                    "collection_used": self._get_best_collection(query),
                    "original_results": len(search_results),
                    "filtered_results": len(filtered_results),
                    "reranked_results": len(reranked_results),
                    "cache_hit": False,
                },
            )

            # 缓存结果
            self._put_to_cache(cache_key, response)

            logger.info(
                f"✅ 搜索完成: {len(limited_results)} 个结果,耗时 {response.processing_time:.2f}秒"
            )
            return response

        except Exception as e:
            logger.error(f"❌ RAG搜索失败: {e}")
            # 返回错误响应
            return RAGResponse(
                query=query.query,
                results=[],
                total_results=0,
                processing_time=time.time() - start_time,
                method_used="error",
                metadata={"error": str(e)},
            )

    async def query(self, query: RAGQuery) -> RAGResponse:
        """RAG查询接口 - search方法的别名"""
        return await self.search(query)

    async def _perform_vector_search(self, query: RAGQuery) -> list[SearchResult]:
        """执行向量搜索"""
        try:
            # 选择最佳集合
            collection_name = self._get_best_collection(query)

            # 生成查询向量
            query_embedding = await self.bge_service.encode([query.query])
            # 处理EmbeddingResult对象
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

            # 创建搜索过滤器
            search_filter = None
            if query.doc_types:
                search_filter = Filter(
                    must=[{"key": "doc_type", "match": {"any": query.doc_types}}]
                )

            # 执行搜索

            search_result = self.qdrant_client.search(
                collection_name=collection_name,
                query_vector=query_vector,
                limit=query.top_k * 2,  # 获取更多结果用于重排序
                query_filter=search_filter,
                with_payload=True,
                score_threshold=0.3,
            )

            # 转换结果
            results = []
            for hit in search_result:
                result = SearchResult(
                    id=str(hit.id),
                    content=hit.payload.get("content", ""),
                    score=hit.score,
                    metadata=hit.payload.get("metadata", {}),
                    source=hit.payload.get("source", ""),
                    doc_type=hit.payload.get("doc_type", ""),
                )
                results.append(result)

            logger.info(f"📊 向量搜索完成: {len(results)} 个结果")
            return results

        except Exception as e:
            logger.error(f"❌ 向量搜索失败: {e}")
            return []

    def _apply_filters(self, results: list[SearchResult], query: RAGQuery) -> list[SearchResult]:
        """应用过滤器"""
        if not results:
            return results

        filtered_results = results

        # 文档类型过滤
        if query.doc_types:
            filtered_results = [r for r in filtered_results if r.doc_type in query.doc_types]

        # 分数阈值过滤
        filtered_results = [r for r in filtered_results if r.score > 0.1]  # 最小分数阈值

        return filtered_results

    def _get_best_collection(self, query: RAGQuery) -> str:
        """获取最佳集合"""
        if query.doc_types:
            # 新增:优先检查历史数据集合
            for doc_type in query.doc_types:
                doc_type_lower = doc_type.lower()

                # 无效复审决定
                if (
                    "无效" in doc_type_lower
                    or "invalid" in doc_type_lower
                    or "复审" in doc_type_lower
                ):
                    collection = self.historical_collections.get("invalidation_decisions")
                    if collection and collection in self.available_collections:
                        return collection

                # 中国法律全集
                if (
                    "中国法律" in doc_type_lower
                    or "法律" in doc_type_lower
                    or "chinese_law" in doc_type_lower
                    or "statute" in doc_type_lower
                ):
                    collection = self.historical_collections.get("chinese_laws")
                    if collection and collection in self.available_collections:
                        return collection

                # 专利法
                if "专利法" in doc_type_lower or "patent_law" in doc_type_lower:
                    collection = self.historical_collections.get("patent_laws")
                    if collection and collection in self.available_collections:
                        return collection

                # 商标文档
                if "商标" in doc_type_lower or "trademark" in doc_type_lower:
                    collection = self.historical_collections.get("trademark_docs")
                    if collection and collection in self.available_collections:
                        return collection

                # 原有逻辑:专利相关集合
                if "patent" in doc_type_lower:
                    for collection in self.available_collections:
                        if "patent" in collection and "laws" in collection:
                            return collection

        # 默认集合
        return self.config["default_collection"]

    def _get_cache_key(self, query: RAGQuery) -> str:
        """生成缓存键"""
        key_data = {
            "query": query.query.lower().strip(),
            "top_k": query.top_k,
            "rerank_method": query.rerank_method,
            "doc_types": tuple(query.doc_types or []),
        }
        return hash(str(key_data))

    def _get_from_cache(self, cache_key: str) -> RAGResponse | None:
        """从缓存获取结果"""
        if not self.config["cache_enabled"]:
            return None

        cached_item = self.query_cache.get(cache_key)
        if cached_item:
            timestamp, response = cached_item
            if time.time() - timestamp < self.cache_ttl:
                return response
            else:
                del self.query_cache[cache_key]

        return None

    def _put_to_cache(self, cache_key: str, response: RAGResponse) -> Any:
        """将结果放入缓存"""
        if not self.config["cache_enabled"]:
            return

        self.query_cache[cache_key] = (time.time(), response)

    async def evaluate_performance(self, test_cases: list[dict[str, Any]]) -> dict[str, Any]:
        """评估RAG性能"""
        logger.info(f"📊 评估RAG性能,测试案例数: {len(test_cases)}")

        if not test_cases:
            return {"error": "没有测试案例"}

        # 创建评估案例
        evaluation_cases = []
        for case in test_cases:
            try:
                # 执行RAG搜索
                query = RAGQuery(
                    query=case["query"],
                    top_k=case.get("top_k", self.config["default_top_k"]),
                    doc_types=case.get("doc_types"),
                )

                response = await self.search(query)

                # 创建评估案例
                eval_case = EvaluationCase(
                    query=case["query"],
                    expected_context=case.get("expected_context", []),
                    expected_response=case.get("expected_response", ""),
                    actual_response=response.results[0].content if response.results else "",
                    actual_context=[r.content for r in response.results],
                    metadata={
                        "case_id": case.get("case_id"),
                        "processing_time": response.processing_time,
                        "method_used": response.method_used,
                    },
                )
                evaluation_cases.append(eval_case)

            except Exception as e:
                logger.error(f"❌ 处理测试案例失败: {e}")
                continue

        # 执行评估
        evaluation_report = await self.evaluator.evaluate_rag_performance(
            evaluation_cases, method="hybrid"
        )

        # 添加性能统计
        processing_times = [case.metadata.get("processing_time", 0) for case in evaluation_cases]
        if processing_times:
            evaluation_report["performance_stats"] = {
                "avg_processing_time": sum(processing_times) / len(processing_times),
                "max_processing_time": max(processing_times),
                "min_processing_time": min(processing_times),
                "total_cases": len(evaluation_cases),
            }

        return evaluation_report

    def get_service_status(self) -> dict[str, Any]:
        """获取服务状态"""
        return {
            "service_name": self.name,
            "version": self.version,
            "components": {
                "document_processor": "Athena + LlamaIndex",
                "reranker": "Athena + LlamaIndex",
                "evaluator": "Athena + LlamaIndex",
                "vector_search": "BGE + Qdrant",
            },
            "llamaindex_available": self.reranker.llamaindex_available,
            "available_collections": len(self.available_collections),
            "cache_enabled": self.config["cache_enabled"],
            "cache_size": len(self.query_cache),
            "config": self.config,
        }


async def main():
    """测试RAG服务"""
    print("🚀 Athena混合架构RAG服务测试")
    print("=" * 60)

    service = AthenaHybridRAGService()

    # 显示服务状态
    status = service.get_service_status()
    print("📊 服务状态:")
    print(f"   - 服务名称: {status['service_name']}")
    print(f"   - 版本: {status['version']}")
    print(f"   - LlamaIndex可用: {status['llamaindex_available']}")
    print(f"   - 可用集合: {status['available_collections']}")

    # 测试搜索
    print("\n🔍 测试搜索功能:")
    test_queries = [
        {
            "query": "发明专利的保护期是多长?",
            "top_k": 5,
            "rerank_method": "hybrid",
            "doc_types": ["专利法律"],
        },
        {
            "query": "专利权的无效宣告程序",
            "top_k": 3,
            "rerank_method": "athena_optimized",
            "doc_types": ["专利法律", "司法解释"],
        },
    ]

    for i, test_query in enumerate(test_queries):
        print(f"\n📝 测试查询 {i+1}: {test_query['query']}")

        query = RAGQuery(**test_query)
        response = await service.search(query)

        print("📊 搜索结果:")
        print(f"   - 找到结果: {response.total_results} 个")
        print(f"   - 返回结果: {len(response.results)} 个")
        print(f"   - 处理时间: {response.processing_time:.3f} 秒")
        print(f"   - 使用方法: {response.method_used}")

        for j, result in enumerate(response.results[:3]):
            print(
                f"   {j+1}. [{result.doc_type}] {result.content[:60]}... (分数: {result.score:.3f})"
            )

    # 测试性能评估
    print("\n📊 测试性能评估:")
    test_cases = [
        {
            "case_id": 1,
            "query": "发明专利的保护期是多长?",
            "expected_response": "发明专利的保护期为二十年,自申请日起计算。",
            "doc_types": ["专利法律"],
        },
        {
            "case_id": 2,
            "query": "专利权的无效宣告程序是什么?",
            "expected_response": "专利权的无效宣告程序是指任何单位或者个人认为专利权的授予不符合法律规定的,可以请求专利复审委员会宣告该专利权无效。",
            "doc_types": ["专利法律"],
        },
    ]

    performance_report = await service.evaluate_performance(test_cases)

    print("\n📈 性能评估结果:")
    print(f"   - 评估案例数: {performance_report['evaluated_cases']}")
    print(f"   - 平均相关性: {performance_report['overall_metrics']['avg_relevance']:.3f}")
    print(f"   - 平均忠实度: {performance_report['overall_metrics']['avg_faithfulness']:.3f}")
    print(f"   - 总体分数: {performance_report['overall_metrics']['overall_score']:.3f}")

    if "performance_stats" in performance_report:
        stats = performance_report["performance_stats"]
        print(f"   - 平均处理时间: {stats['avg_processing_time']:.3f} 秒")
        print(f"   - 最大处理时间: {stats['max_processing_time']:.3f} 秒")
        print(f"   - 最小处理时间: {stats['min_processing_time']:.3f} 秒")


# 入口点: @async_main装饰器已添加到main函数
