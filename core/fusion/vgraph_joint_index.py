#!/usr/bin/env python3
"""
向量-图联合索引策略
Joint Index Strategy for Vector + Graph Fusion

作者: 小诺·双鱼公主
创建时间: 2025-12-28
"""

import asyncio
import logging
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple


from core.async_main import async_main
from core.config.secure_config import get_config
from core.database.unified_connection import get_postgres_pool
from core.logging_config import setup_logging

logger = setup_logging()


class IndexStrategy(Enum):
    """索引策略"""

    SEMANTIC_SIMILARITY = "semantic_similarity"  # 语义相似度索引
    GRAPH_CENTRALITY = "graph_centrality"  # 图中心性索引
    HYBRID_FUSION = "hybrid_fusion"  # 混合融合索引
    PATH_BASED = "path_based"  # 路径索引


@dataclass
class SimilarityCacheEntry:
    """相似度缓存条目"""

    source_entity_id: str
    target_entity_id: str
    similarity_score: float
    distance_score: float
    has_graph_relation: bool = False
    graph_distance: int | None = None
    graph_path: list[str] | None = None


@dataclass
class GraphPathEntry:
    """图路径缓存条目"""

    source_entity_id: str
    target_entity_id: str
    path_length: int
    path_vertices: list[str]
    path_edges: list[str]
    path_strength: float = 1.0
    path_type: str = "default"


class VectorGraphJointIndex:
    """向量-图联合索引管理器"""

    def __init__(self, pg_pool: asyncpg.Pool):
        """初始化联合索引管理器"""
        self.pg_pool = pg_pool
        self.cache_enabled = True
        self.cache_ttl_days = 30

    # ============================================
    # 相似度预计算和缓存
    # ============================================

    async def precompute_similarity_index(
        self, entity_type: str, batch_size: int = 1000, threshold: float = 0.7
    ) -> int:
        """
        预计算实体间的向量相似度并缓存

        Args:
            entity_type: 实体类型
            batch_size: 批处理大小
            threshold: 相似度阈值

        Returns:
            预计算的相似度对数量
        """
        logger.info(f"🔄 开始预计算 {entity_type} 的相似度索引...")

        count = 0
        offset = 0

        while True:
            # 获取一批实体
            async with self.pg_pool.acquire() as conn:
                entities = await conn.fetch(
                    f"""
                    SELECT
                        m.entity_id,
                        m.entity_type,
                        m.pgvector_table,
                        m.pgvector_id,
                        v.embedding
                    FROM vgraph_unified_mapping m
                    JOIN {entity_type}_vectors v ON v.id = m.pgvector_id
                    WHERE m.entity_type = $1
                    ORDER BY m.entity_id
                    LIMIT $2 OFFSET $3
                """,
                    entity_type,
                    batch_size,
                    offset,
                )

                if not entities:
                    break

                # 计算两两相似度
                for i, entity_a in enumerate(entities):
                    for entity_b in entities[i + 1 :]:
                        similarity = self._cosine_similarity(
                            entity_a["embedding"], entity_b["embedding"]
                        )

                        if similarity >= threshold:
                            await self._cache_similarity(
                                entity_a["entity_id"],
                                entity_b["entity_id"],
                                similarity,
                                1 - similarity,  # 距离 = 1 - 余弦相似度
                            )
                            count += 1

                offset += batch_size
                logger.info(f"  已处理 {offset} 个实体,预计算 {count} 个相似度对")

        logger.info(f"✅ 相似度预计算完成,共 {count} 对")
        return count

    async def _cache_similarity(
        self, source_id: str, target_id: str, similarity: float, distance: float
    ):
        """缓存相似度结果"""
        if not self.cache_enabled:
            return

        try:
            async with self.pg_pool.acquire() as conn:
                await conn.execute(
                    """
                    INSERT INTO vector_similarity_cache (
                        source_entity_id, target_entity_id,
                        similarity_score, distance_score,
                        ttl
                    )
                    VALUES ($1, $2, $3, $4, $5)
                    ON CONFLICT (source_entity_id, target_entity_id, calculation_method)
                    DO UPDATE SET
                        similarity_score = EXCLUDED.similarity_score,
                        distance_score = EXCLUDED.distance_score,
                        last_accessed = CURRENT_TIMESTAMP
                """,
                    source_id,
                    target_id,
                    similarity,
                    distance,
                    datetime.now() + timedelta(days=self.cache_ttl_days),
                )
        except Exception as e:
            logger.warning(f"缓存相似度失败: {e}")

    async def get_similar_entities(
        self,
        entity_id: str,
        threshold: float = 0.7,
        limit: int = 100,
        require_graph_relation: bool = False,
    ) -> list[SimilarityCacheEntry]:
        """
        从缓存中获取相似实体

        Args:
            entity_id: 源实体ID
            threshold: 相似度阈值
            limit: 返回数量限制
            require_graph_relation: 是否要求有图关系

        Returns:
            相似实体列表
        """
        async with self.pg_pool.acquire() as conn:
            query = """
                SELECT
                    source_entity_id,
                    target_entity_id,
                    similarity_score,
                    distance_score,
                    has_graph_relation,
                    graph_distance,
                    graph_path
                FROM vector_similarity_cache
                WHERE source_entity_id = $1
                  AND similarity_score >= $2
            """

            if require_graph_relation:
                query += " AND has_graph_relation = TRUE"

            query += f" ORDER BY similarity_score DESC LIMIT {limit}"

            rows = await conn.fetch(query, entity_id, threshold)

            return [
                SimilarityCacheEntry(
                    source_entity_id=row["source_entity_id"],
                    target_entity_id=row["target_entity_id"],
                    similarity_score=row["similarity_score"],
                    distance_score=row["distance_score"],
                    has_graph_relation=row["has_graph_relation"],
                    graph_distance=row["graph_distance"],
                    graph_path=row["graph_path"],
                )
                for row in rows
            ]

    # ============================================
    # 图路径预计算和缓存
    # ============================================

    async def precompute_graph_paths(
        self, max_depth: int = 3, max_paths_per_entity: int = 100, centrality_threshold: float = 0.5
    ) -> int:
        """
        预计算高频实体间的图路径

        Args:
            max_depth: 最大路径深度
            max_paths_per_entity: 每个实体的最大路径数
            centrality_threshold: 中心性阈值,只处理重要实体

        Returns:
            预计算的路径数量
        """
        logger.info("🔄 开始预计算图路径...")

        count = 0

        # 获取高中心性实体
        async with self.pg_pool.acquire() as conn:
            important_entities = await conn.fetch(
                """
                SELECT entity_id, nebula_vertex_id, graph_centrality_score
                FROM vgraph_unified_mapping
                WHERE graph_centrality_score >= $1
                ORDER BY graph_centrality_score DESC
                LIMIT 1000
            """,
                centrality_threshold,
            )

            logger.info(f"  找到 {len(important_entities)} 个重要实体")

            # 为每个实体计算到其他实体的路径
            for i, entity_a in enumerate(important_entities):
                paths = await self._find_shortest_paths(
                    entity_a["nebula_vertex_id"], max_depth, max_paths_per_entity
                )

                for path in paths:
                    await self._cache_graph_path(
                        entity_a["entity_id"], path["target_id"], path["vertices"], path["edges"]
                    )
                    count += 1

                if (i + 1) % 100 == 0:
                    logger.info(f"  已处理 {i + 1}/{len(important_entities)} 个实体")

        logger.info(f"✅ 图路径预计算完成,共 {count} 条路径")
        return count

    async def _find_shortest_paths(
        self, start_vertex_id: str, max_depth: int, limit: int
    ) -> list[dict[str, Any]]:
        """
        查找从起始顶点出发的最短路径

        注意:这里需要通过 NebulaGraph 客户端执行图遍历
        简化实现,返回模拟数据
        """
        # TODO: 集成 NebulaGraph 客户端执行实际的图遍历
        # 这里返回空列表,实际使用时需要实现
        return []

    async def _cache_graph_path(
        self, source_id: str, target_id: str, vertices: list[str], edges: list[str]
    ):
        """缓存图路径"""
        if not self.cache_enabled:
            return

        try:
            async with self.pg_pool.acquire() as conn:
                await conn.execute(
                    """
                    INSERT INTO graph_path_cache (
                        source_entity_id, target_entity_id,
                        path_length, path_vertices, path_edges
                    )
                    VALUES ($1, $2, $3, $4, $5)
                    ON CONFLICT (source_entity_id, target_entity_id, path_vertices)
                    DO NOTHING
                """,
                    source_id,
                    target_id,
                    len(vertices),
                    vertices,
                    edges,
                )
        except Exception as e:
            logger.warning(f"缓存图路径失败: {e}")

    async def get_cached_paths(self, source_id: str, max_length: int = 3) -> list[GraphPathEntry]:
        """获取缓存的图路径"""
        async with self.pg_pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT
                    source_entity_id,
                    target_entity_id,
                    path_length,
                    path_vertices,
                    path_edges,
                    path_strength,
                    path_type
                FROM graph_path_cache
                WHERE source_entity_id = $1
                  AND path_length <= $2
                ORDER BY path_length, path_strength DESC
                LIMIT 100
            """,
                source_id,
                max_length,
            )

            return [
                GraphPathEntry(
                    source_entity_id=row["source_entity_id"],
                    target_entity_id=row["target_entity_id"],
                    path_length=row["path_length"],
                    path_vertices=row["path_vertices"],
                    path_edges=row["path_edges"],
                    path_strength=row["path_strength"],
                    path_type=row["path_type"],
                )
                for row in rows
            ]

    # ============================================
    # 联合查询优化
    # ============================================

    async def joint_search_vector_guided(
        self,
        query_vector: list[float],
        entity_type: str,
        vector_threshold: float = 0.7,
        graph_depth: int = 2,
        limit: int = 50,
    ) -> list[dict[str, Any]]:
        """
        向量引导的图搜索

        先用向量检索获取候选集,然后在候选集中进行图遍历
        """
        results = []

        # 映射实体类型到表名
        table_mapping = {
            "agent_memory": "agent_memory_vectors",
            "agent_memory_vectors": "agent_memory_vectors",
            "legal_document": "legal_documents_vectors",
            "legal_document_vectors": "legal_documents_vectors",
            "patent_rule": "patent_rules_vectors",
            "patent_rule_vectors": "patent_rules_vectors",
            "patent_fulltext": "patent_fulltext_vectors",
            "patent_fulltext_vectors": "patent_fulltext_vectors",
            "patent_judgment": "patent_judgments_vectors",
            "patent_judgments_vectors": "patent_judgments_vectors",
            "trademark": "trademark_vectors",
            "trademark_vectors": "trademark_vectors",
        }

        table_name = table_mapping.get(entity_type, f"{entity_type}_vectors")

        async with self.pg_pool.acquire() as conn:
            # 1. 向量检索获取候选集
            try:
                # 将向量转换为字符串格式
                vector_str = "[" + ",".join(map(str, query_vector)) + "]"

                candidates = await conn.fetch(
                    f"""
                    SELECT
                        m.entity_id,
                        m.nebula_vertex_id,
                        m.graph_centrality_score,
                        1 - (v.embedding <=> $1::vector) AS similarity
                    FROM vgraph_unified_mapping m
                    JOIN {table_name} v ON v.id = m.pgvector_id
                    WHERE m.entity_type = $2
                      AND 1 - (v.embedding <=> $1::vector) >= $3
                    ORDER BY v.embedding <=> $1::vector
                    LIMIT 100
                """,
                    vector_str,
                    entity_type,
                    vector_threshold,
                )
            except Exception as e:
                logger.warning(f"向量引导搜索失败: {e}")
                return results

            if not candidates:
                return results

            # 2. 在候选集中查找图关系
            candidate_ids = [c["entity_id"] for c in candidates[:50]]

            # 查询候选实体之间的图关系
            graph_relations = await conn.fetch(
                """
                SELECT
                    source_entity_id,
                    target_entity_id,
                    has_graph_relation,
                    graph_distance
                FROM vector_similarity_cache
                WHERE source_entity_id = ANY($1)
                  AND has_graph_relation = TRUE
            """,
                candidate_ids,
            )

            # 3. 融合分数
            relation_map = {}
            for rel in graph_relations:
                key = rel["source_entity_id"]
                if key not in relation_map:
                    relation_map[key] = []
                relation_map[key].append(rel)

            for candidate in candidates:
                entity_id = candidate["entity_id"]
                vector_score = candidate["similarity"]
                graph_score = candidate["graph_centrality_score"] or 0.5

                # 如果有图关系,增强图分数
                if entity_id in relation_map:
                    related_count = len(relation_map[entity_id])
                    graph_score = min(1.0, graph_score + related_count * 0.1)

                fusion_score = vector_score * 0.6 + graph_score * 0.4

                results.append(
                    {
                        "entity_id": entity_id,
                        "nebula_vertex_id": candidate["nebula_vertex_id"],
                        "vector_score": vector_score,
                        "graph_score": graph_score,
                        "fusion_score": fusion_score,
                    }
                )

        # 按融合分数排序
        results.sort(key=lambda x: x["fusion_score"], reverse=True)
        return results[:limit]

    async def joint_search_graph_pruned(
        self,
        start_entity_id: str,
        query_vector: list[float],
        entity_type: str,
        graph_depth: int = 2,
        limit: int = 50,
    ) -> list[dict[str, Any]]:
        """
        图剪枝的向量搜索

        先通过图遍历限定搜索范围,然后在范围内进行向量检索
        """
        results = []

        async with self.pg_pool.acquire() as conn:
            # 1. 通过图遍历获取相关实体(使用缓存的路径)
            cached_paths = await self.get_cached_paths(start_entity_id, max_length=graph_depth)

            if not cached_paths:
                # 如果没有缓存路径,回退到纯向量搜索
                return await self.joint_search_vector_guided(query_vector, entity_type, limit=limit)

            # 2. 获取路径上的所有实体
            related_entity_ids = set()
            for path in cached_paths:
                related_entity_ids.update(path.path_vertices)
                related_entity_ids.add(path.target_entity_id)

            # 3. 在相关实体中进行向量检索
            placeholders = ",".join([f"${i+1}" for i in range(len(related_entity_ids))])

            rows = await conn.fetch(
                f"""
                SELECT
                    m.entity_id,
                    m.nebula_vertex_id,
                    1 - (v.embedding <=> ${len(related_entity_ids)+1}::vector) AS similarity
                FROM vgraph_unified_mapping m
                JOIN {entity_type}_vectors v ON v.id = m.pgvector_id
                WHERE m.entity_id IN ({placeholders})
                ORDER BY v.embedding <=> ${len(related_entity_ids)+1}::vector
                LIMIT $ {len(related_entity_ids)+2}
            """,
                *list(related_entity_ids),
                query_vector,
                limit,
            )

            for row in rows:
                results.append(
                    {
                        "entity_id": row["entity_id"],
                        "nebula_vertex_id": row["nebula_vertex_id"],
                        "vector_score": row["similarity"],
                        "graph_score": 0.8,  # 子图内默认高分
                        "fusion_score": row["similarity"] * 0.5 + 0.8 * 0.5,
                    }
                )

        return results

    # ============================================
    # 索引维护
    # ============================================

    async def cleanup_expired_cache(self) -> dict[str, int]:
        """清理过期缓存"""
        stats = {"similarity_cache": 0, "path_cache": 0}

        async with self.pg_pool.acquire() as conn:
            # 清理相似度缓存
            similarity_count = await conn.fetchval("""
                SELECT COUNT(*) FROM vector_similarity_cache
                WHERE ttl < CURRENT_TIMESTAMP
            """)

            await conn.execute("""
                DELETE FROM vector_similarity_cache
                WHERE ttl < CURRENT_TIMESTAMP
            """)

            stats["similarity_cache"] = similarity_count

            # 清理长期未访问的路径缓存
            path_count = await conn.fetchval("""
                DELETE FROM graph_path_cache
                WHERE created_at < CURRENT_TIMESTAMP - INTERVAL '60 days'
                  AND access_count < 5
                RETURNING COUNT(*)
            """)

            stats["path_cache"] = path_count or 0

        logger.info(f"🗑️  清理缓存完成: {stats}")
        return stats

    async def get_index_statistics(self) -> dict[str, Any]:
        """获取索引统计信息"""
        async with self.pg_pool.acquire() as conn:
            # 相似度缓存统计
            sim_stats = await conn.row("""
                SELECT
                    COUNT(*) as total_entries,
                    COUNT(*) FILTER (WHERE has_graph_relation = TRUE) as with_graph_relation,
                    AVG(similarity_score) as avg_similarity,
                    MAX(last_accessed) as last_accessed
                FROM vector_similarity_cache
            """)

            # 路径缓存统计
            path_stats = await conn.row("""
                SELECT
                    COUNT(*) as total_paths,
                    AVG(path_length) as avg_path_length,
                    SUM(access_count) as total_accesses,
                    MAX(created_at) as last_created
                FROM graph_path_cache
            """)

            return {
                "similarity_cache": {
                    "total_entries": sim_stats["total_entries"],
                    "with_graph_relation": sim_stats["with_graph_relation"],
                    "avg_similarity": (
                        float(sim_stats["avg_similarity"]) if sim_stats["avg_similarity"] else 0.0
                    ),
                    "last_accessed": (
                        sim_stats["last_accessed"].isoformat()
                        if sim_stats["last_accessed"]
                        else None
                    ),
                },
                "graph_path_cache": {
                    "total_paths": path_stats["total_paths"],
                    "avg_path_length": (
                        float(path_stats["avg_path_length"])
                        if path_stats["avg_path_length"]
                        else 0.0
                    ),
                    "total_accesses": path_stats["total_accesses"],
                    "last_created": (
                        path_stats["last_created"].isoformat()
                        if path_stats["last_created"]
                        else None
                    ),
                },
            }

    # ============================================
    # 工具方法
    # ============================================

    @staticmethod
    def _cosine_similarity(vec1: list[float], vec2: list[float]) -> float:
        """计算余弦相似度"""
        try:
            a = np.array(vec1)
            b = np.array(vec2)
            return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))
        except Exception:
            return 0.0

    async def close(self):
        """关闭连接池"""
        if self.pg_pool:
            try:
                await self.pg_pool.close()
                logger.info("✅ PostgreSQL连接池已关闭")
            except Exception as e:
                logger.error(f"❌ 关闭PostgreSQL连接池失败: {e}")

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

    # 创建连接池
    await get_postgres_pool(
        host=pg_config.get("host", "localhost"),
        port=pg_config.get("port", 5438),
        user=pg_config.get("user", "postgres"),
        password=pg_config.get("password", required=True),
        database=pg_config.get("dbname", "agent_memory_db"),
    )

    # 创建联合索引管理器
    joint_index = VectorGraphJointIndex(pg_pool)

    # 预计算相似度索引
    count = await joint_index.precompute_similarity_index(entity_type="patent_rule", threshold=0.75)
    print(f"预计算了 {count} 个相似度对")

    # 获取索引统计
    stats = await joint_index.get_index_statistics()
    print(f"索引统计: {stats}")

    # 清理过期缓存
    cleanup_stats = await joint_index.cleanup_expired_cache()
    print(f"清理统计: {cleanup_stats}")

    # 关闭连接
    await pg_pool.close()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
