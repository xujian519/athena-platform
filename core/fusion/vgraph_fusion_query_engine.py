#!/usr/bin/env python3
"""
融合查询引擎
Fusion Query Engine for pgvector + NebulaGraph Deep Integration

作者: 小诺·双鱼公主
创建时间: 2025-12-28
"""

import asyncio
import hashlib
import json
import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple


from core.async_main import async_main
from core.config.secure_config import get_config
from core.database.unified_connection import get_postgres_pool
from core.logging_config import setup_logging

from .vgraph_joint_index import VectorGraphJointIndex

logger = setup_logging()


class QueryType(Enum):
    """查询类型"""

    PURE_VECTOR = "pure_vector"
    PURE_GRAPH = "pure_graph"
    VECTOR_GUIDED = "vector_guided"
    GRAPH_PRUNED = "graph_pruned"
    FUSION_BOTH = "fusion_both"


class QueryStrategy(Enum):
    """查询策略"""

    RECALL_FIRST = "recall_first"
    PRECISION_FIRST = "precision_first"
    BALANCED = "balanced"
    FAST_PATH = "fast_path"


@dataclass
class QueryResult:
    """查询结果"""

    entity_id: str
    entity_type: str
    business_key: str
    content: str

    # 分数信息
    vector_score: float = 0.0
    graph_score: float = 0.0
    fusion_score: float = 0.0

    # 元数据
    vector_metadata: dict[str, Any] = field(default_factory=dict)
    graph_metadata: dict[str, Any] = field(default_factory=dict)

    # 路径信息
    graph_path: list[str] = field(default_factory=list)
    related_entities: list[str] = field(default_factory=list)

    # 置信度
    confidence: float = 0.0

    def __post_init__(self):
        """计算融合分数和置信度"""
        self.fusion_score = self.vector_score * 0.5 + self.graph_score * 0.5
        self.confidence = min(1.0, self.fusion_score)

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "entity_id": self.entity_id,
            "entity_type": self.entity_type,
            "business_key": self.business_key,
            "content": self.content,
            "vector_score": self.vector_score,
            "graph_score": self.graph_score,
            "fusion_score": self.fusion_score,
            "confidence": self.confidence,
            "vector_metadata": self.vector_metadata,
            "graph_metadata": self.graph_metadata,
            "graph_path": self.graph_path,
            "related_entities": self.related_entities,
        }


@dataclass
class QueryPlan:
    """查询计划"""

    query_type: QueryType
    strategy: QueryStrategy
    estimated_cost: float
    execution_steps: list[str]

    # 向量检索参数
    vector_threshold: float = 0.7
    vector_limit: int = 100

    # 图遍历参数
    graph_depth: int = 3
    graph_limit: int = 50

    # 融合参数
    fusion_weight_vector: float = 0.5
    fusion_weight_graph: float = 0.5


class FusionQueryEngine:
    """融合查询引擎"""

    def __init__(
        self, pg_pool: asyncpg.Pool, nebula_pool: SessionPool, joint_index: VectorGraphJointIndex
    ):
        """初始化融合查询引擎"""
        self.pg_pool = pg_pool
        self.nebula_pool = nebula_pool
        self.joint_index = joint_index

        # 查询缓存
        self.query_cache: dict[str, tuple[list[QueryResult], datetime]] = {}
        self.cache_ttl = 300  # 5分钟

        # 统计信息
        self.query_stats = {
            "total_queries": 0,
            "cache_hits": 0,
            "avg_latency_ms": 0.0,
            "query_type_distribution": {},
        }

    async def execute_fusion_query(
        self,
        query_text: str,
        query_vector: list[float],
        entity_types: Optional[list[str]] = None,
        limit: int = 10,
        filters: Optional[dict[str, Any]] = None,
        strategy: str = "balanced",
    ) -> tuple[list[QueryResult], dict[str, Any]]:
        """
        执行融合查询

        Args:
            query_text: 查询文本
            query_vector: 查询向量
            entity_types: 实体类型过滤
            limit: 返回结果数量
            filters: 额外过滤条件
            strategy: 查询策略

        Returns:
            (查询结果列表, 查询报告)
        """
        start_time = datetime.now()
        self.query_stats["total_queries"] += 1

        logger.info(f"🔍 执行融合查询: {query_text[:50]}...")

        # 1. 检查缓存
        cache_key = self._generate_cache_key(query_text, entity_types, limit)
        if cache_key in self.query_cache:
            cached_results, cached_time = self.query_cache[cache_key]
            if (datetime.now() - cached_time).total_seconds() < self.cache_ttl:
                self.query_stats["cache_hits"] += 1
                logger.info("✅ 返回缓存结果")
                return cached_results, self._generate_query_report(
                    query_text, cached_results, 0, True
                )

        # 2. 分析查询并优化
        query_features = await self._analyze_query(query_text, query_vector)
        plan = await self._optimize_query(query_features, entity_types, limit, strategy)

        logger.info(f"📋 查询计划: {plan.query_type.value}, 预估成本: {plan.estimated_cost:.2f}")

        # 3. 执行查询计划
        if plan.query_type == QueryType.PURE_VECTOR:
            results = await self._execute_vector_query(query_vector, plan, filters)
        elif plan.query_type == QueryType.PURE_GRAPH:
            results = await self._execute_graph_query(query_text, plan, filters)
        elif plan.query_type == QueryType.VECTOR_GUIDED:
            results = await self._execute_vector_guided_query(
                query_vector, query_text, plan, filters
            )
        elif plan.query_type == QueryType.GRAPH_PRUNED:
            results = await self._execute_graph_pruned_query(
                query_vector, query_text, plan, filters
            )
        else:  # FUSION_BOTH
            results = await self._execute_fusion_both_query(query_vector, query_text, plan, filters)

        # 4. 重排序和去重
        results = await self._rerank_and_deduplicate(results, limit)

        # 5. 缓存结果
        self.query_cache[cache_key] = (results, datetime.now())

        # 清理过期缓存
        await self._cleanup_expired_cache()

        # 6. 生成报告
        latency_ms = (datetime.now() - start_time).total_seconds() * 1000
        self._update_avg_latency(latency_ms)
        report = self._generate_query_report(query_text, results, latency_ms, False)

        logger.info(f"✅ 查询完成,返回 {len(results)} 条结果 ({latency_ms:.2f}ms)")
        return results, report

    async def _analyze_query(self, query_text: str, query_vector: list[float]) -> dict[str, Any]:
        """分析查询特征"""
        features = {
            "text_length": len(query_text),
            "vector_dimension": len(query_vector),
            "vector_norm": np.linalg.norm(query_vector),
            "has_special_terms": False,
            "entity_mentions": [],
            "query_complexity": "simple",
        }

        # 简单的实体提及检测
        # 实际应该使用 NER 模型
        keywords = query_text.split()
        features["entity_mentions"] = [w for w in keywords if len(w) > 2][:5]

        # 评估查询复杂度
        if len(query_text) > 100 or len(features["entity_mentions"]) > 2:
            features["query_complexity"] = "complex"

        return features

    async def _optimize_query(
        self, query_features: dict[str, Any], entity_types: list[str], limit: int, strategy: str
    ) -> QueryPlan:
        """优化查询计划"""
        query_strategy = QueryStrategy(strategy)

        # 简化版:根据特征选择查询类型
        if query_features["entity_mentions"] and query_features["query_complexity"] == "complex":
            query_type = QueryType.GRAPH_PRUNED
        elif query_features["entity_mentions"]:
            query_type = QueryType.VECTOR_GUIDED
        else:
            query_type = QueryType.FUSION_BOTH

        # 估算成本
        estimated_cost = self._estimate_query_cost(query_type, query_features)

        return QueryPlan(
            query_type=query_type,
            strategy=query_strategy,
            estimated_cost=estimated_cost,
            execution_steps=self._get_execution_steps(query_type),
            vector_threshold=0.7,
            vector_limit=limit * 10,
            graph_depth=2,
            graph_limit=limit * 5,
        )

    def _estimate_query_cost(self, query_type: QueryType, features: dict[str, Any]) -> float:
        """估算查询成本"""
        base_costs = {
            QueryType.PURE_VECTOR: 10.0,
            QueryType.PURE_GRAPH: 50.0,
            QueryType.VECTOR_GUIDED: 25.0,
            QueryType.GRAPH_PRUNED: 30.0,
            QueryType.FUSION_BOTH: 40.0,
        }
        return base_costs.get(query_type, 30.0)

    def _get_execution_steps(self, query_type: QueryType) -> list[str]:
        """获取执行步骤"""
        steps = {
            QueryType.PURE_VECTOR: [
                "1. 执行向量相似度搜索",
                "2. 应用过滤条件",
                "3. 排序并返回top-K",
            ],
            QueryType.PURE_GRAPH: ["1. 定位起始实体", "2. 执行图遍历", "3. 排序并返回top-K"],
            QueryType.VECTOR_GUIDED: [
                "1. 执行向量检索获取候选集",
                "2. 在候选集中执行图遍历",
                "3. 融合分数并排序",
            ],
            QueryType.GRAPH_PRUNED: [
                "1. 通过实体定位相关子图",
                "2. 在子图范围内执行向量检索",
                "3. 融合分数并排序",
            ],
            QueryType.FUSION_BOTH: [
                "1. 并行执行向量检索和图遍历",
                "2. 结果去重和融合",
                "3. 重排序并返回top-K",
            ],
        }
        return steps.get(query_type, [])

    async def _execute_vector_query(
        self, query_vector: list[float], plan: QueryPlan, filters: Optional[dict[str, Any]] = None
    ) -> list[QueryResult]:
        """执行纯向量查询"""
        results = []

        async with self.pg_pool.acquire() as conn:
            # 查询所有相关表
            tables = [
                ("agent_memory", 768),
                ("legal_documents", 1024),
                ("patent_rules", 1024),
                ("patent_fulltext", 1024),
            ]

            for table_name, _dim in tables:
                try:
                    query = f"""
                        SELECT
                            m.entity_id,
                            m.entity_type,
                            m.business_key,
                            v.content,
                            1 - (v.embedding <=> $1::vector) AS similarity,
                            v.metadata
                        FROM vgraph_unified_mapping m
                        JOIN {table_name}_vectors v ON v.id = m.pgvector_id
                        WHERE 1 - (v.embedding <=> $1::vector) >= $2
                        ORDER BY v.embedding <=> $1::vector
                        LIMIT $3
                    """

                    rows = await conn.fetch(
                        query, query_vector, plan.vector_threshold, plan.vector_limit
                    )

                    for row in rows:
                        result = QueryResult(
                            entity_id=str(row["entity_id"]),
                            entity_type=row["entity_type"],
                            business_key=row["business_key"],
                            content=row["content"],
                            vector_score=row["similarity"],
                            vector_metadata=row["metadata"] or {},
                        )
                        results.append(result)

                except Exception as e:
                    logger.warning(f"向量查询失败 {table_name}: {e}")

        return results

    async def _execute_graph_query(
        self, query_text: str, plan: QueryPlan, filters: Optional[dict[str, Any]] = None
    ) -> list[QueryResult]:
        """执行纯图查询"""
        results = []

        # 提取实体
        entities = self._extract_entities(query_text)
        if not entities:
            return results

        session = self.nebula_pool.get_session()
        try:
            for entity in entities[:5]:
                # 执行图遍历
                nebula_query = f"""
                    MATCH (v)-[r*1..{plan.graph_depth}]-(related)
                    WHERE v.标题 CONTAINS "{entity}" OR v.关键词 CONTAINS "{entity}"
                    RETURN
                        id(v) AS vertex_id,
                        v.entity_type AS entity_type,
                        v.business_key AS business_key,
                        v.content AS content,
                        v.中心性分数 AS centrality,
                        v.重要性分数 AS importance
                    LIMIT {plan.graph_limit}
                """

                result = session.execute(nebula_query)
                if result.is_succeeded():
                    for row in result.row_values():
                        result_obj = QueryResult(
                            entity_id=row[0].as_string(),
                            entity_type=row[1].as_string(),
                            business_key=row[2].as_string(),
                            content=row[3].as_string(),
                            graph_score=(
                                row[4].as_float()
                                if row[4]
                                else row[5].as_float() if row[5] else 0.5
                            ),
                            graph_metadata={"centrality": row[4].as_float() if row[4] else 0.0},
                        )
                        results.append(result_obj)

        finally:
            session.release()

        return results

    async def _execute_vector_guided_query(
        self,
        query_vector: list[float],
        query_text: str,
        plan: QueryPlan,
        filters: Optional[dict[str, Any]] = None,
    ) -> list[QueryResult]:
        """执行向量引导图遍历"""
        # 使用联合索引的优化方法
        entity_type = filters.get("entity_type", "patent_rule") if filters else "patent_rule"

        joint_results = await self.joint_index.joint_search_vector_guided(
            query_vector=query_vector,
            entity_type=entity_type,
            vector_threshold=plan.vector_threshold,
            graph_depth=plan.graph_depth,
            limit=plan.vector_limit,
        )

        results = []
        for jr in joint_results:
            # 获取完整内容
            async with self.pg_pool.acquire() as conn:
                content = await conn.fetchval(
                    """
                    SELECT content FROM patent_rules_vectors
                    WHERE id = (SELECT pgvector_id FROM vgraph_unified_mapping WHERE entity_id = $1)
                """,
                    jr["entity_id"],
                )

            result = QueryResult(
                entity_id=jr["entity_id"],
                entity_type=entity_type,
                business_key="",
                content=content or "",
                vector_score=jr["vector_score"],
                graph_score=jr["graph_score"],
                fusion_score=jr["fusion_score"],
            )
            results.append(result)

        return results

    async def _execute_graph_pruned_query(
        self,
        query_vector: list[float],
        query_text: str,
        plan: QueryPlan,
        filters: Optional[dict[str, Any]] = None,
    ) -> list[QueryResult]:
        """执行图剪枝向量检索"""
        entities = self._extract_entities(query_text)
        if not entities:
            return await self._execute_vector_query(query_vector, plan, filters)

        # 获取起始实体ID
        async with self.pg_pool.acquire() as conn:
            start_entities = await conn.fetch(
                """
                SELECT entity_id, nebula_vertex_id
                FROM vgraph_unified_mapping
                WHERE business_key = ANY($1)
                LIMIT 5
            """,
                entities,
            )

            if not start_entities:
                return await self._execute_vector_query(query_vector, plan, filters)

            results = []
            for start_entity in start_entities:
                joint_results = await self.joint_index.joint_search_graph_pruned(
                    start_entity_id=str(start_entity["entity_id"]),
                    query_vector=query_vector,
                    entity_type=(
                        filters.get("entity_type", "patent_rule") if filters else "patent_rule"
                    ),
                    graph_depth=plan.graph_depth,
                    limit=plan.vector_limit,
                )

                for jr in joint_results:
                    result = QueryResult(
                        entity_id=jr["entity_id"],
                        entity_type="",
                        business_key="",
                        content="",
                        vector_score=jr["vector_score"],
                        graph_score=jr["graph_score"],
                        fusion_score=jr["fusion_score"],
                    )
                    results.append(result)

            return results

    async def _execute_fusion_both_query(
        self,
        query_vector: list[float],
        query_text: str,
        plan: QueryPlan,
        filters: Optional[dict[str, Any]] = None,
    ) -> list[QueryResult]:
        """执行完全融合查询"""
        # 并行执行向量检索和图遍历
        vector_task = asyncio.create_task(self._execute_vector_query(query_vector, plan, filters))
        graph_task = asyncio.create_task(self._execute_graph_query(query_text, plan, filters))

        vector_results, graph_results = await asyncio.gather(
            vector_task, graph_task, return_exceptions=True
        )

        # 处理异常
        if isinstance(vector_results, Exception):
            logger.warning(f"向量检索异常: {vector_results}")
            vector_results = []
        if isinstance(graph_results, Exception):
            logger.warning(f"图遍历异常: {graph_results}")
            graph_results = []

        # 合并结果
        merged = {}

        for result in vector_results:
            merged[result.entity_id] = result

        for result in graph_results:
            if result.entity_id in merged:
                # 融合
                existing = merged[result.entity_id]
                existing.graph_score = result.graph_score
                existing.graph_metadata = result.graph_metadata
                existing.fusion_score = (
                    existing.vector_score * plan.fusion_weight_vector
                    + existing.graph_score * plan.fusion_weight_graph
                )
            else:
                merged[result.entity_id] = result

        return list(merged.values())

    async def _rerank_and_deduplicate(
        self, results: list[QueryResult], limit: int
    ) -> list[QueryResult]:
        """重排序和去重"""
        # 按融合分数排序
        results.sort(key=lambda r: r.fusion_score, reverse=True)

        # 去重
        deduplicated = []
        seen_contents = set()

        for result in results:
            content_hash = hashlib.md5(
                result.content[:100].encode('utf-8', usedforsecurity=False), usedforsecurity=False
            ).hexdigest()
            if content_hash not in seen_contents:
                deduplicated.append(result)
                seen_contents.add(content_hash)

                if len(deduplicated) >= limit:
                    break

        return deduplicated

    def _extract_entities(self, text: str) -> list[str]:
        """提取文本中的实体"""
        words = text.split()
        stop_words = {"的", "是", "在", "有", "和", "与", "了", "等", "或", "但", "这", "那"}
        entities = [w for w in words if len(w) > 2 and w not in stop_words]
        return entities[:5]

    def _generate_cache_key(self, query_text: str, entity_types: list[str], limit: int) -> str:
        """生成缓存键"""
        key_str = f"{query_text}:{','.join(entity_types or []):{limit}}"
        return hashlib.md5(key_str.encode('utf-8'), usedforsecurity=False).hexdigest()

    async def _cleanup_expired_cache(self):
        """清理过期缓存"""
        now = datetime.now()
        expired_keys = [
            key
            for key, (_, cached_time) in self.query_cache.items()
            if (now - cached_time).total_seconds() > self.cache_ttl
        ]

        for key in expired_keys:
            del self.query_cache[key]

        if expired_keys:
            logger.debug(f"清理了 {len(expired_keys)} 个过期缓存")

    def _update_avg_latency(self, latency_ms: float) -> Any:
        """更新平均延迟"""
        current_avg = self.query_stats["avg_latency_ms"]
        total_queries = self.query_stats["total_queries"]

        if total_queries > 0:
            alpha = 0.1
            self.query_stats["avg_latency_ms"] = alpha * latency_ms + (1 - alpha) * current_avg

    def _generate_query_report(
        self, query_text: str, results: list[QueryResult], latency_ms: float, from_cache: bool
    ) -> dict[str, Any]:
        """生成查询报告"""
        return {
            "query_text": query_text,
            "result_count": len(results),
            "latency_ms": latency_ms,
            "from_cache": from_cache,
            "avg_fusion_score": np.mean([r.fusion_score for r in results]) if results else 0.0,
            "avg_vector_score": np.mean([r.vector_score for r in results]) if results else 0.0,
            "avg_graph_score": np.mean([r.graph_score for r in results]) if results else 0.0,
            "top_result": results[0].to_dict() if results else None,
        }

    async def get_query_statistics(self) -> dict[str, Any]:
        """获取查询统计"""
        return {
            **self.query_stats,
            "cache_size": len(self.query_cache),
            "cache_hit_rate": (
                self.query_stats["cache_hits"] / self.query_stats["total_queries"]
                if self.query_stats["total_queries"] > 0
                else 0.0
            ),
        }

    async def clear_cache(self):
        """清空查询缓存"""
        self.query_cache.clear()
        logger.info("🗑️  查询缓存已清空")

    async def close(self):
        """关闭连接池"""
        if self.nebula_pool:
            try:
                self.nebula_pool.close()
                logger.info("✅ NebulaGraph连接池已关闭")
            except Exception as e:
                logger.error(f"❌ 关闭NebulaGraph连接池失败: {e}")

    async def __aenter__(self):
        """异步上下文管理器入口"""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器出口"""
        await self.close()
        return False


# 使用示例
@async_main
async def main():
    """使用示例"""
    # 使用安全配置
    config = get_config()
    pg_config = config.get_postgres_config()
    nebula_config = config.get_nebula_config()

    # 创建连接池
    await get_postgres_pool(
        host=pg_config.get("host", "localhost"),
        port=pg_config.get("port", 5438),
        user=pg_config.get("user", "postgres"),
        password=pg_config.get("password", required=True),
        database=pg_config.get("dbname", "agent_memory_db"),
    )

    nebula_pool = SessionPool()
    await nebula_pool.init(
        username=nebula_config.get("user", "root"),
        password=nebula_config.get("password", required=True),
        space_name=nebula_config.get("space", "vgraph_unified_space"),
        addresses=[(nebula_config.get("host", "localhost"), nebula_config.get("port", 9669))],
    )

    # 创建联合索引
    from .vgraph_joint_index import VectorGraphJointIndex

    joint_index = VectorGraphJointIndex(pg_pool)

    # 创建融合查询引擎
    engine = FusionQueryEngine(pg_pool, nebula_pool, joint_index)

    # 执行融合查询
    results, report = await engine.execute_fusion_query(
        query_text="专利新颖性判断标准",
        query_vector=np.random.rand(1024).tolist(),
        entity_types=["patent_rule"],
        limit=10,
        strategy="balanced",
    )

    # 输出结果
    print(f"查询报告: {json.dumps(report, indent=2, ensure_ascii=False)}")
    for i, result in enumerate(results[:5], 1):
        print(f"\n{i}. [融合分数: {result.fusion_score:.4f}]")
        print(f"   向量分数: {result.vector_score:.4f}")
        print(f"   图分数: {result.graph_score:.4f}")
        print(f"   内容: {result.content[:100]}...")

    # 获取统计
    stats = await engine.get_query_statistics()
    print(f"\n查询统计: {json.dumps(stats, indent=2, ensure_ascii=False)}")

    # 清理
    await pg_pool.close()
    await engine.close()  # 使用close()方法


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
