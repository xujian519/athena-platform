#!/usr/bin/env python3
from __future__ import annotations
"""
Neo4j智能检索路由系统
Neo4j Intelligent Retrieval Router System

版本: v3.0.0
技术决策: TD-001 - 统一图数据库选择为Neo4j

实现向量库+知识图谱的智能路由和混合检索

核心功能:
1. 意图识别 - 自动判断查询类型
2. 智能路由 - 根据意图路由到最优数据源
3. 并行检索 - 同时查询多个数据源
4. 结果融合 - 智能合并多源结果
5. 性能优化 - 缓存和批处理

作者: 小诺AI团队
创建时间: 2025-01-09
更新时间: 2026-01-25 (TD-001: 迁移到Neo4j)
"""

import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

import numpy as np

# Neo4j 驱动 (TD-001: 替换NebulaGraph)
from neo4j import GraphDatabase

# 向量库客户端
from qdrant_client import QdrantClient

# 重试和超时控制
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from core.config.unified_config import get_database_config
from core.logging_config import setup_logging

# 熔断器
from core.resilience.circuit_breaker import (
    CircuitBreakerConfig,
    CircuitBreakerOpenError,
    get_circuit_breaker,
)

# 配置日志
logger = setup_logging()


class QueryIntent(Enum):
    """查询意图类型"""

    PATENT_SEARCH = "patent_search"  # 专利技术检索
    LEGAL_SEARCH = "legal_search"  # 法律条款查询
    INVALID_DECISION_SEARCH = "invalid_decision_search"  # 无效复审决定检索
    HYBRID_SEARCH = "hybrid_search"  # 混合检索
    CASE_ANALYSIS = "case_analysis"  # 案例分析
    CONCEPT_QUERY = "concept_query"  # 概念查询
    UNKNOWN = "unknown"  # 未知意图


class DataSource(Enum):
    """数据源类型"""

    PATENT_VECTORS = "patent_vectors"  # 专利向量库
    LEGAL_VECTORS = "legal_vectors"  # 法律向量库
    PATENT_KG = "patent_kg"  # 专利知识图谱
    LEGAL_KG = "legal_kg"  # 法律知识图谱
    INVALID_DECISIONS = "invalidation_decisions"  # 无效复审决定
    CHINESE_LAWS = "chinese_laws"  # 中国法律全集
    PATENT_LAWS = "patent_laws"  # 专利法律文档
    TRADEMARK_DOCS = "trademark_docs"  # 商标文档
    MIXED = "mixed"  # 混合数据源


@dataclass
class QueryContext:
    """查询上下文"""

    query: str  # 原始查询
    intent: QueryIntent  # 查询意图
    confidence: float  # 意图置信度
    data_sources: list[DataSource]  # 推荐数据源
    weights: dict[str, float] = field(default_factory=dict)  # 数据源权重
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class SearchResult:
    """搜索结果"""

    content: str  # 内容
    source: DataSource  # 数据源
    score: float  # 相关性分数
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class RouterResult:
    """路由结果"""

    query_context: QueryContext  # 查询上下文
    results: list[SearchResult]  # 搜索结果
    total_time: float  # 总耗时
    source_stats: dict[str, dict] = field(default_factory=dict)


class IntentClassifier:
    """意图分类器 - 使用关键词+规则"""

    def __init__(self):
        # 专利相关关键词
        self.patent_keywords = [
            "专利",
            "发明",
            "实用新型",
            "外观设计",
            "技术方案",
            "技术特征",
            "权利要求",
            "说明书",
            "专利申请",
            "专利权",
            "专利侵权",
            "新颖性",
            "创造性",
            "实用性",
            "现有技术",
            "对比文件",
        ]

        # 法律相关关键词
        self.legal_keywords = [
            "法",
            "法律",
            "条款",
            "条例",
            "规定",
            "办法",
            "第.*条",
            "民法典",
            "专利法",
            "商标法",
            "著作权法",
            "司法解释",
            "最高法院",
            "法律责任",
            "法律依据",
        ]

        # 无效复审决定相关关键词 (新增)
        self.invalid_decision_keywords = [
            "无效",
            "复审",
            "无效宣告",
            "复审决定",
            "无效决定",
            "专利无效",
            "无效请求",
            "复审请求",
            "专利复审委员会",
        ]

        # 混合检索关键词
        self.hybrid_keywords = [
            "专利.*法",
            "法律.*专利",
            "侵权.*责任",
            "专利.*保护",
            "案例.*分析",
            "判例.*适用",
            "法律.*适用",
        ]

    def classify(self, query: str) -> tuple[QueryIntent, float]:
        """
        分类查询意图

        Args:
            query: 查询文本

        Returns:
            (意图类型, 置信度)
        """
        query.lower()

        # 计算各类关键词匹配分数
        patent_score = sum(1 for kw in self.patent_keywords if kw in query)
        legal_score = sum(1 for kw in self.legal_keywords if kw in query)
        invalid_score = sum(1 for kw in self.invalid_decision_keywords if kw in query)
        hybrid_score = sum(1 for kw in self.hybrid_keywords if kw in query)

        # 判断意图 (优先匹配无效复审决定)
        if invalid_score > 0:
            return QueryIntent.INVALID_DECISION_SEARCH, min(0.95, 0.7 + invalid_score * 0.1)
        elif hybrid_score > 0:
            return QueryIntent.HYBRID_SEARCH, min(0.9, 0.5 + hybrid_score * 0.1)
        elif patent_score > legal_score and patent_score > 0:
            return QueryIntent.PATENT_SEARCH, min(0.95, 0.6 + patent_score * 0.1)
        elif legal_score > 0:
            return QueryIntent.LEGAL_SEARCH, min(0.95, 0.6 + legal_score * 0.1)
        elif "案例" in query or "判例" in query:
            return QueryIntent.CASE_ANALYSIS, 0.7
        else:
            return QueryIntent.PATENT_SEARCH, 0.5  # 默认专利搜索


class VectorSearchEngine:
    """向量搜索引擎(带重试机制和熔断器)"""

    def __init__(self, qdrant_url: str | None = None, timeout: int = 30):
        """初始化向量搜索引擎

        Args:
            qdrant_url: Qdrant服务器URL,默认从环境变量读取
            timeout: 超时时间(秒)
        """
        import os

        if qdrant_url is None:
            qdrant_host = os.getenv("QDRANT_HOST", "localhost")
            qdrant_port = os.getenv("QDRANT_PORT", "6333")
            qdrant_url = f"http://{qdrant_host}:{qdrant_port}"

        self.client = QdrantClient(url=qdrant_url, timeout=timeout)
        self.cache = {}  # 简单缓存

        # Collection映射 (更新后的集合列表)
        self.patent_collections = [
            "patent_decisions",
            "patent_guidelines",
            "patent_rules_complete",
            "patent_invalidation_decisions",  # 新增: 无效复审决定
        ]

        self.legal_collections = [
            "laws_articles",
            "legal_knowledge",
            "patent_legal_rules_enhanced",
            "legal_docs_chinese_laws",  # 新增: 中国法律全集
            "legal_docs_patent_laws",  # 新增: 专利法律文档
            "legal_docs_trademark_docs",  # 新增: 商标文档
        ]

        # 初始化熔断器
        self.qdrant_breaker = get_circuit_breaker(
            "qdrant_search", CircuitBreakerConfig(failure_threshold=5, recovery_timeout=60)
        )
        logger.info("✅ Qdrant熔断器已初始化")

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((ConnectionError, TimeoutError)),
        reraise=True,
    )
    def _search_patent_internal(
        self, query_vector: list[float], limit: int = 10
    ) -> list[SearchResult]:
        """搜索专利向量库(带重试)- 内部方法"""
        results = []

        for collection in self.patent_collections:
            try:
                search_result = self.client.query_points(
                    collection_name=collection,
                    query=query_vector,
                    limit=limit,
                    with_payload=True,
                    timeout=5,  # 5秒超时
                )

                for point in search_result.points:
                    results.append(
                        SearchResult(
                            content=point.payload.get("title", point.payload.get("content", "")),
                            source=DataSource.PATENT_VECTORS,
                            score=point.score,
                            metadata={"collection": collection, "payload": point.payload},
                        )
                    )
            except Exception as e:
                logger.warning(f"Patent search failed in {collection}: {e}")

        return results

    def search_patent(self, query_vector: list[float], limit: int = 10) -> list[SearchResult]:
        """搜索专利向量库(带熔断器保护)"""
        try:
            return self.qdrant_breaker.call(self._search_patent_internal, query_vector, limit)
        except CircuitBreakerOpenError as e:
            logger.error(f"❌ Qdrant熔断器打开: {e}")
            # 返回空结果或缓存结果
            return []

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((ConnectionError, TimeoutError)),
        reraise=True,
    )
    def _search_legal_internal(
        self, query_vector: list[float], limit: int = 10
    ) -> list[SearchResult]:
        """搜索法律向量库(带重试)- 内部方法"""
        results = []

        for collection in self.legal_collections:
            try:
                search_result = self.client.query_points(
                    collection_name=collection,
                    query=query_vector,
                    limit=limit,
                    with_payload=True,
                    timeout=5,  # 5秒超时
                )

                for point in search_result.points:
                    results.append(
                        SearchResult(
                            content=point.payload.get("title", point.payload.get("content", "")),
                            source=DataSource.LEGAL_VECTORS,
                            score=point.score,
                            metadata={"collection": collection, "payload": point.payload},
                        )
                    )
            except Exception as e:
                logger.warning(f"Legal search failed in {collection}: {e}")

        return results

    def search_legal(self, query_vector: list[float], limit: int = 10) -> list[SearchResult]:
        """搜索法律向量库(带熔断器保护)"""
        try:
            return self.qdrant_breaker.call(self._search_legal_internal, query_vector, limit)
        except CircuitBreakerOpenError as e:
            logger.error(f"❌ Qdrant熔断器打开: {e}")
            return []


class Neo4jKGRetriever:
    """Neo4j知识图谱检索器 (TD-001: 替换NebulaGraph)"""

    def __init__(self, neo4j_uri: str | None = None):
        """初始化知识图谱检索器

        Args:
            neo4j_uri: Neo4j连接URI,默认从统一配置读取
        """
        # 从统一配置获取Neo4j配置 (TD-001)
        db_config = get_database_config()
        neo4j_config = db_config.get("neo4j", {})

        if neo4j_uri is None:
            neo4j_uri = neo4j_config.get("uri", "bolt://localhost:7687")

        self.neo4j_uri = neo4j_uri
        self.neo4j_username = neo4j_config.get("username", "neo4j")
        self.neo4j_password = neo4j_config.get("password", "password")
        self.neo4j_database = neo4j_config.get("database", "neo4j")

        self.driver = None

        try:
            self.driver = GraphDatabase.driver(
                self.neo4j_uri,
                auth=(self.neo4j_username, self.neo4j_password),
            )
            # 测试连接
            with self.driver.session(database=self.neo4j_database) as session:
                result = session.run("RETURN 'Connection OK' as message")
                record = result.single()
                if record and record["message"] == "Connection OK":
                    logger.info("✅ Neo4j连接成功")
        except Exception as e:
            logger.error(f"❌ Neo4j连接失败: {e}")
            self.driver = None

    def query_patent_kg(self, query: str, limit: int = 10) -> list[SearchResult]:
        """查询专利知识图谱"""
        if not self.driver:
            return []

        results = []

        try:
            with self.driver.session(database=self.neo4j_database) as session:
                # Cypher查询专利节点
                cypher = """
                    MATCH (p:Patent)
                    RETURN p.number AS number, p.title AS title, p.status AS status
                    LIMIT $limit
                """
                result = session.run(cypher, {"limit": limit})

                for row in result:
                    results.append(
                        SearchResult(
                            content=f"{row['title']} ({row['number']})",
                            source=DataSource.PATENT_KG,
                            score=0.8,
                            metadata={"number": row["number"], "status": row["status"]},
                        )
                    )
        except Exception as e:
            logger.warning(f"Patent KG query failed: {e}")

        return results

    def query_legal_kg(self, query: str, limit: int = 10) -> list[SearchResult]:
        """查询法律知识图谱"""
        if not self.driver:
            return []

        results = []

        try:
            with self.driver.session(database=self.neo4j_database) as session:
                # Cypher查询法律规则节点
                cypher = """
                    MATCH (n)
                    RETURN n
                    LIMIT $limit
                """
                result = session.run(cypher, {"limit": limit})

                for row in result:
                    node = row["n"]
                    results.append(
                        SearchResult(
                            content=str(node),
                            source=DataSource.LEGAL_KG,
                            score=0.8,
                            metadata={},
                        )
                    )
        except Exception as e:
            logger.warning(f"Legal KG query failed: {e}")

        return results

    def close(self):
        """关闭连接"""
        if self.driver:
            self.driver.close()


class ResultFusionEngine:
    """结果融合引擎"""

    def __init__(self):
        pass

    def fuse_results(
        self, results: list[SearchResult], weights: dict[str, float]
    ) -> list[SearchResult]:
        """
        融合多源结果

        Args:
            results: 所有搜索结果
            weights: 数据源权重

        Returns:
            融合后的结果列表
        """
        # 按source分组
        grouped = {}
        for result in results:
            source_name = result.source.value
            if source_name not in grouped:
                grouped[source_name] = []
            grouped[source_name].append(result)

        # 应用权重并排序
        weighted_results = []
        for source_name, source_results in grouped.items():
            weight = weights.get(source_name, 1.0)
            for result in source_results:
                result.score *= weight
                weighted_results.append(result)

        # 按分数排序
        weighted_results.sort(key=lambda x: x.score, reverse=True)

        # 去重(基于内容)
        seen = set()
        unique_results = []
        for result in weighted_results:
            content_hash = hash(result.content[:100])
            if content_hash not in seen:
                seen.add(content_hash)
                unique_results.append(result)

        return unique_results[:20]  # 返回前20条


class IntelligentRetrievalRouter:
    """智能检索路由器 - 主控制器"""

    def __init__(self):
        self.intent_classifier = IntentClassifier()
        self.vector_engine = VectorSearchEngine()
        self.kg_retriever = Neo4jKGRetriever()  # TD-001: 使用Neo4j
        self.fusion_engine = ResultFusionEngine()

        # 权重配置
        self.default_weights = {
            "patent_vectors": 0.6,
            "legal_vectors": 0.3,
            "patent_kg": 0.05,
            "legal_kg": 0.05,
        }

    def generate_query_vector(self, query: str) -> list[float]:
        """
        生成查询向量(使用平台BGE-large模型,1024维)

        注意:Qdrant中所有collections都是1024维,使用BAAI/bge-m3编码
        """
        try:
            # 导入平台的BGE嵌入服务
            import os
            import sys

            sys.path.append(os.path.dirname(os.path.dirname(__file__)))

            from core.embedding.bge_embedding_service import get_bge_service

            # 获取BGE服务(使用BAAI/bge-m3,1024维,匹配Qdrant collections)
            bge_service = get_bge_service("BAAI/bge-m3", device="mps")

            # 编码查询文本
            query_vector = bge_service.encode_single(query, normalize=True)

            logger.info(f"✅ BGE-large编码成功,向量维度: {len(query_vector)}")
            return query_vector

        except Exception as e:
            logger.error(f"❌ BGE编码失败: {e},使用随机向量")
            # 降级到随机向量(1024维匹配bge-large)
            return np.random.rand(1024).tolist()

    def route_and_search(self, query: str, limit: int = 10) -> RouterResult:
        """
        智能路由并执行检索

        Args:
            query: 查询文本
            limit: 返回结果数量

        Returns:
            路由结果
        """
        start_time = time.time()

        # 1. 意图识别
        intent, confidence = self.intent_classifier.classify(query)

        query_context = QueryContext(
            query=query,
            intent=intent,
            confidence=confidence,
            data_sources=self._get_data_sources(intent),
            weights=self._get_weights(intent),
        )

        logger.info(f"🎯 意图: {intent.value}, 置信度: {confidence:.2f}")

        # 2. 生成查询向量
        query_vector = self.generate_query_vector(query)

        # 3. 并行检索
        all_results = []
        source_stats = {}

        with ThreadPoolExecutor(max_workers=4) as executor:
            futures = {}

            # 根据意图选择检索策略
            if intent in [QueryIntent.PATENT_SEARCH, QueryIntent.HYBRID_SEARCH]:
                futures["patent_vectors"] = executor.submit(
                    self.vector_engine.search_patent, query_vector, limit
                )

            if intent in [QueryIntent.LEGAL_SEARCH, QueryIntent.HYBRID_SEARCH]:
                futures["legal_vectors"] = executor.submit(
                    self.vector_engine.search_legal, query_vector, limit
                )

            # 无效复审决定检索 (新增)
            if intent == QueryIntent.INVALID_DECISION_SEARCH:
                futures["invalid_decisions"] = executor.submit(
                    self.vector_engine.search_patent, query_vector, limit
                )

            # 知识图谱检索(可选)
            if intent == QueryIntent.CASE_ANALYSIS:
                futures["patent_kg"] = executor.submit(
                    self.kg_retriever.query_patent_kg, query, limit
                )

            # 收集结果
            for source_name, future in futures.items():
                try:
                    source_results = future.result(timeout=10)
                    all_results.extend(source_results)
                    source_stats[source_name] = {
                        "count": len(source_results),
                        "time": time.time() - start_time,
                    }
                except Exception as e:
                    logger.warning(f"{source_name} search failed: {e}")
                    source_stats[source_name] = {"count": 0, "error": str(e)}

        # 4. 结果融合
        fused_results = self.fusion_engine.fuse_results(all_results, query_context.weights)

        total_time = time.time() - start_time

        return RouterResult(
            query_context=query_context,
            results=fused_results,
            total_time=total_time,
            source_stats=source_stats,
        )

    def _get_data_sources(self, intent: QueryIntent) -> list[DataSource]:
        """根据意图获取数据源"""
        if intent == QueryIntent.PATENT_SEARCH:
            return [DataSource.PATENT_VECTORS]
        elif intent == QueryIntent.LEGAL_SEARCH:
            return [DataSource.LEGAL_VECTORS]
        elif intent == QueryIntent.INVALID_DECISION_SEARCH:
            return [DataSource.INVALID_DECISIONS]
        elif intent == QueryIntent.HYBRID_SEARCH:
            return [DataSource.PATENT_VECTORS, DataSource.LEGAL_VECTORS]
        else:
            return [DataSource.PATENT_VECTORS]

    def _get_weights(self, intent: QueryIntent) -> dict[str, float]:
        """根据意图获取权重"""
        if intent == QueryIntent.PATENT_SEARCH:
            return {"patent_vectors": 1.0}
        elif intent == QueryIntent.LEGAL_SEARCH:
            return {"legal_vectors": 1.0}
        elif intent == QueryIntent.INVALID_DECISION_SEARCH:
            return {"invalid_decisions": 1.0}
        elif intent == QueryIntent.HYBRID_SEARCH:
            return {"patent_vectors": 0.6, "legal_vectors": 0.4}
        else:
            return self.default_weights

    def close(self):
        """关闭资源"""
        self.kg_retriever.close()


# 全局实例
_global_router: IntelligentRetrievalRouter | None = None


def get_router() -> IntelligentRetrievalRouter:
    """获取全局路由器实例"""
    global _global_router
    if _global_router is None:
        _global_router = IntelligentRetrievalRouter()
    return _global_router


# ========== 兼容层: 保持与旧API的兼容性 ==========

# 导入旧名称以保持向后兼容
KGRetriever = Neo4jKGRetriever


if __name__ == "__main__":
    # 测试智能路由
    router = get_router()

    print("=" * 70)
    print("🧪 测试Neo4j智能检索路由")
    print("=" * 70)

    # 测试查询
    test_queries = ["智能农业设备的专利申请", "专利法第22条关于新颖性的规定", "专利侵权如何认定"]

    for query in test_queries:
        print(f"\n🔍 查询: {query}")
        print("-" * 70)

        result = router.route_and_search(query, limit=5)

        print(f"意图: {result.query_context.intent.value}")
        print(f"置信度: {result.query_context.confidence:.2f}")
        print(f"数据源: {[ds.value for ds in result.query_context.data_sources]}")
        print(f"耗时: {result.total_time:.3f}秒")
        print(f"结果数: {len(result.results)}")

        print("\n📊 结果来源统计:")
        for source, stats in result.source_stats.items():
            print(f"  {source}: {stats.get('count', 0)}条")

        print("\n📝 Top 3 结果:")
        for i, r in enumerate(result.results[:3], 1):
            print(f"  {i}. [{r.source.value}] {r.content[:80]}...")

    router.close()

    print("\n" + "=" * 70)
    print("🎉 测试完成!")
    print("=" * 70)
