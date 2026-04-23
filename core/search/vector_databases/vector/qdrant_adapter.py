#!/usr/bin/env python3

"""
Qdrant向量搜索适配器
Qdrant Vector Search Adapter

替换原有的NumPy向量搜索实现
集成HNSW索引优化向量检索性能

作者: Athena平台团队
创建时间: 2026-03-17
版本: v2.0.0 "HNSW优化版"
"""

import logging
import sys
import time
from typing import Any

from qdrant_client import QdrantClient
from qdrant_client.models import Distance, HnswConfigDiff, SearchParams, VectorParams

sys.path.insert(0, '/Users/xujian/Athena工作平台')
from config.feature_flags import is_feature_enabled

logger = logging.getLogger(__name__)


class QdrantVectorAdapter:
    """Qdrant向量搜索适配器（带HNSW优化）"""

    def __init__(self, host: str = "localhost", port: int = 6333):
        self.client = QdrantClient(host=host, port=port)
        self.collections = {
            "athena_memory": "athena_memory",
            "xiaonuo_memory": "xiaonuo_memory",
            "patent_vectors": "patent_vectors",
            "legal_clauses": "legal_clauses",
            "technical_terms": "technical_terms",
        }

        # HNSW配置
        self.enable_hnsw = is_feature_enabled("enable_hnsw_search")
        self.hnsw_config = HnswConfigDiff(
            m=16,  # 每个节点的连接数，影响召回率和构建时间
            ef_construct=100,  # 构建时的搜索宽度，影响索引质量
            full_scan_threshold=10000,  # 小于这个数量的向量使用精确搜索
        )

        # 搜索配置
        self.search_params = SearchParams(
            hnsw_ef=128,  # 搜索时的动态宽度
            exact=False  # 是否使用精确搜索
        )

        # 性能统计
        self.search_stats = {
            "total_searches": 0,
            "total_time": 0.0,
            "avg_time": 0.0,
            "min_time": float('inf'),
            "max_time": 0.0,
        }

        logger.info(f"✅ Qdrant向量搜索适配器初始化完成 (HNSW: {self.enable_hnsw})")

        logger.info(f"   - 主机: {host}:{port}")
        logger.info(f"   - 集合数: {len(self.collections)}")
        logger.info(f"   - HNSW配置: m={self.hnsw_config.m}, ef_construct={self.hnsw_config.ef_construct}")

    def ensure_collection_with_hnsw(self, collection_name: str, vector_size: int = 768):
        """
        确保集合使用HNSW索引

        Args:
            collection_name: 集合名称
            vector_size: 向量维度
        """
        try:
            # 检查集合是否存在
            collections = self.client.get_collections()
            exists = any(c.name == collection_name for c in collections.collections)

            if not exists:
                # 创建新集合（带HNSW配置）
                self.client.create_collection(
                    collection_name=collection_name,
                    vectors_config=VectorParams(
                        size=vector_size,
                        distance=Distance.COSINE,
                        hnsw_config=self.hnsw_config
                    )
                )
                logger.info(f"✅ 创建HNSW集合: {collection_name}")
            else:
                # 更新现有集合的HNSW配置
                try:
                    self.client.update_collection(
                        collection_name=collection_name,
                        hnsw_config=self.hnsw_config
                    )
                    logger.info(f"✅ 更新HNSW配置: {collection_name}")
                except Exception as e:
                    logger.warning(f"⚠️ 更新HNSW配置失败（可能已是最优）: {e}")

            return True

        except Exception as e:
            logger.error(f"❌ 确保HNSW集合失败: {e}")
            return False

    def search(self, query_vector: list[float], collection_name: str,
              limit: int = 10, threshold: float = 0.0) -> list[dict[str, Any]]:
        """
        优化的向量搜索（使用HNSW）

        Args:
            query_vector: 查询向量
            collection_name: 集合名称
            limit: 返回结果数量
            threshold: 相似度阈值

        Returns:
            搜索结果列表
        """
        collection_name = self.collections.get(collection_name)
        if not collection_name:
            logger.warning(f"未知的集合类型: {collection_name}")
            return []

        start_time = time.time()

        try:
            # 使用优化的搜索参数
            params = self.search_params if self.enable_hnsw else None

            results = self.client.search(
                collection_name=collection_name,
                query_vector=query_vector,
                limit=limit,
                score_threshold=threshold,
                search_params=params,
                with_payload=True
            )

            # 更新统计
            elapsed = (time.time() - start_time) * 1000
            self._update_search_stats(elapsed)

            logger.debug(f"✅ 向量搜索完成: {len(results)}条结果, 耗时: {elapsed:.2f}ms")
            return results

        except Exception as e:
            logger.error(f"❌ 向量搜索失败: {e}")
            return []

    def search_optimized(self, query_vector: list[float], collection_type: str,
                        limit: int = 10, ef: int = 128) -> list[dict[str, Any]]:
        """
        优化的向量搜索（可调整ef参数）

        Args:
            query_vector: 查询向量
            collection_type: 集合类型
            limit: 返回结果数量
            ef: 搜索宽度（越大越准确但越慢）

        Returns:
            搜索结果列表
        """
        collection_name = self.collections.get(collection_type)
        if not collection_name:
            return []

        try:
            # 动态调整ef参数
            search_params = SearchParams(hnsw_ef=ef, exact=False)

            results = self.client.search(
                collection_name=collection_name,
                query_vector=query_vector,
                limit=limit,
                search_params=search_params,
                with_payload=True
            )

            return results
        except Exception as e:
            logger.error(f"❌ 优化搜索失败: {e}")
            return []

    def add_vectors(self, vectors: list[dict[str, Any], collection_type: str) -> bool]:
        """
        添加向量（确保集合使用HNSW）

        Args:
            vectors: 向量列表 [{"id": str, "vector": list, "payload": dict}]
            collection_type: 集合类型

        Returns:
            是否成功
        """
        collection_name = self.collections.get(collection_type)
        if not collection_name:
            logger.warning(f"未知的集合类型: {collection_type}")
            return False

        try:
            # 确保集合使用HNSW
            if self.enable_hnsw:
                self.ensure_collection_with_hnsw(collection_name)

            points = [
                {"id": item["id"], "vector": item["vector"], "payload": item["payload"]}
                for item in vectors
            ]

            self.client.upsert(collection_name=collection_name, points=points)

            logger.info(f"✅ 添加 {len(points)} 个向量到 {collection_name}")
            return True
        except Exception as e:
            logger.error(f"❌ 添加向量失败: {e}")
            return False

    def batch_search(self, query_vectors: list[list[float], collection_type: str,
                    limit: int = 10) -> list[list[dict[str, Any]]]:
        """
        批量向量搜索

        Args:
            query_vectors: 查询向量列表
            collection_type: 集合类型
            limit: 每个查询返回的结果数量

        Returns:
            搜索结果列表的列表
        """
        collection_name = self.collections.get(collection_type)
        if not collection_name:
            return [[] for _ in query_vectors]

        results_list = []
        for query_vector in query_vectors:
            results = self.search(query_vector, collection_type, limit)
            results_list.append(results)

        return results_list

    def get_collection_info(self, collection_type: str) -> dict[str, Any]:
        """
        获取集合信息

        Args:
            collection_type: 集合类型

        Returns:
            集合信息
        """
        collection_name = self.collections.get(collection_type)
        if not collection_name:
            return {}

        try:
            info = self.client.get_collection(collection_name)
            return {
                "name": info.config.name,
                "vector_size": info.config.params.vectors.size,
                "distance": info.config.params.vectors.distance.value,
                "points_count": info.points_count,
                "status": info.status.value,
                "hnsw_config": {
                    "m": info.config.params.vectors.hnsw_config.m,
                    "ef_construct": info.config.params.vectors.hnsw_config.ef_construct,
                }
            }
        except Exception as e:
            logger.error(f"❌ 获取集合信息失败: {e}")
            return {}

    def _update_search_stats(self, elapsed_time: float):
        """更新搜索统计"""
        stats = self.search_stats
        stats["total_searches"] += 1
        stats["total_time"] += elapsed_time
        stats["avg_time"] = stats["total_time"] / stats["total_searches"]
        stats["min_time"] = min(stats["min_time"], elapsed_time)
        stats["max_time"] = max(stats["max_time"], elapsed_time)

    def get_search_stats(self) -> dict[str, Any]:
        """获取搜索统计"""
        return self.search_stats.copy()

    def optimize_collection(self, collection_type: str) -> bool:
        """
        优化集合（更新HNSW配置）

        Args:
            collection_type: 集合类型

        Returns:
            是否成功
        """
        collection_name = self.collections.get(collection_type)
        if not collection_name:
            return False

        try:
            self.client.update_collection(
                collection_name=collection_name,
                hnsw_config=self.hnsw_config
            )
            logger.info(f"✅ 优化集合: {collection_name}")
            return True
        except Exception as e:
            logger.error(f"❌ 优化集合失败: {e}")
            return False


# 导出
__all__ = [
    'QdrantVectorAdapter',
]

