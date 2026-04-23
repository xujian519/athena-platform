#!/usr/bin/env python3
from __future__ import annotations
"""
优化记忆系统 - 向量索引
Optimized Memory System - Vector Index

实现HNSW、IVF和暴力搜索的向量索引

作者: Athena AI系统
创建时间: 2025-12-11
重构时间: 2026-01-26
版本: 2.1.0
"""

import time
import uuid
from typing import Any

import numpy as np

from core.logging_config import setup_logging
from core.memory.optimized_memory.types import VectorIndexConfig

logger = setup_logging()


class OptimizedVectorIndex:
    """优化版向量索引 - 支持HNSW、IVF和暴力搜索"""

    def __init__(self, config: VectorIndexConfig):
        self.config = config
        self.index_type = config.index_type
        self.dimension = config.dimension

        # 初始化索引结构
        self.vectors: list[np.ndarray] = []
        self.index_metadata: dict[str, dict[str, Any]] = {}
        self.build_time: Optional[float] = None
        self.query_count = 0

        # 性能统计
        self.stats: dict[str, Any] = {
            "index_size": 0,
            "build_time": 0.0,
            "query_count": 0,
            "average_query_time": 0.0,
            "index_type": self.index_type,
            "precision": 0.0,
            "recall": 0.0,
        }

        # 可选索引对象
        self.hnsw_index = None  # type: ignore
        self.ivf_centers = None  # type: ignore
        self.ivf_labels = None  # type: ignore
        self.kmeans_model = None  # type: ignore

    def add_vector(
        self, vector: np.ndarray, metadata: Optional[dict[str, Any]] = None
    ) -> str:
        """添加向量"""
        vector_id = str(uuid.uuid4())

        self.vectors.append(vector)
        self.index_metadata[vector_id] = metadata or {}

        self.stats["index_size"] = len(self.vectors)
        return vector_id

    def build_index(self):
        """构建索引"""
        start_time = time.time()

        try:
            if self.index_type == "hnsw":
                self._build_hnsw_index()
            elif self.index_type == "ivf":
                self._build_ivf_index()
            elif self.index_type == "brute_force":
                # 暴力搜索不需要预构建
                pass

            self.build_time = time.time() - start_time
            self.stats["build_time"] = self.build_time

            logger.info(f"✅ {self.index_type} 索引构建完成 - 耗时: {self.build_time:.2f}s")

        except Exception as e:
            logger.error(f"❌ 索引构建失败: {e}")

    def _build_hnsw_index(self):
        """构建HNSW索引"""
        try:
            import hnswlib

            # 创建HNSW索引
            index = hnswlib.Index(
                space=self.config.space,
                dim=self.dimension,
                ef_construction=self.config.ef_construction,
                M=self.config.max_connections,
            )

            # 添加向量
            if self.vectors:
                for vector in self.vectors:
                    index.add_item(vector.astype(np.float32))

            # 设置搜索参数
            index.set_ef(self.config.ef_search)

            self.hnsw_index = index

        except ImportError:
            logger.warning("HNSW库不可用，使用暴力搜索")
            self.index_type = "brute_force"

    def _build_ivf_index(self):
        """构建IVF索引"""
        try:
            from sklearn.cluster import KMeans

            # 使用KMeans进行聚类
            n_clusters = min(100, len(self.vectors) // 10)
            kmeans = KMeans(n_clusters=n_clusters, random_state=42)

            if self.vectors:
                kmeans.fit(self.vectors)
                self.ivf_centers = kmeans.cluster_centers_
                self.ivf_labels = kmeans.labels_
                self.kmeans_model = kmeans

        except ImportError:
            logger.warning("scikit-learn不可用，使用暴力搜索")
            self.index_type = "brute_force"

    async def search(
        self, query_vector: np.ndarray, k: int = 10
    ) -> list[tuple[str, float]]:
        """搜索相似向量"""
        start_time = time.time()
        self.query_count += 1

        try:
            results: list[tuple[str, float]] = []

            if self.index_type == "hnsw" and self.hnsw_index is not None:
                # HNSW搜索
                labels, distances = self.hnsw_index.knn_query(
                    query_vector.astype(np.float32), k=k
                )

                for label, distance in zip(labels, distances, strict=False):
                    vector_id = list(self.index_metadata.keys())[label]
                    results.append((vector_id, float(distance)))

            elif self.index_type == "ivf" and self.kmeans_model is not None:
                # IVF搜索
                # 先找到最近的聚类中心
                center_distances = np.linalg.norm(
                    self.ivf_centers - query_vector, axis=1
                )
                nearest_cluster = int(np.argmin(center_distances))

                # 在聚类内搜索
                cluster_indices = np.where(self.ivf_labels == nearest_cluster)[0]
                cluster_vectors = [self.vectors[i] for i in cluster_indices]

                if cluster_vectors:
                    distances = np.linalg.norm(
                        np.array(cluster_vectors) - query_vector, axis=1
                    )
                    sorted_indices = np.argsort(distances)[:k]

                    results = []
                    for idx in sorted_indices:
                        actual_idx = cluster_indices[idx]
                        vector_id = list(self.index_metadata.keys())[actual_idx]
                        results.append((vector_id, float(distances[idx])))

            else:
                # 暴力搜索
                if not self.vectors:
                    return []

                distances = np.linalg.norm(np.array(self.vectors) - query_vector, axis=1)

                sorted_indices = np.argsort(distances)[:k]
                for idx in sorted_indices:
                    vector_id = list(self.index_metadata.keys())[idx]
                    results.append((vector_id, float(distances[idx])))

            # 更新统计信息
            query_time = time.time() - start_time
            self.stats["query_count"] += 1
            self.stats["average_query_time"] = (
                (
                    self.stats["average_query_time"] * (self.stats["query_count"] - 1)
                    + query_time
                )
                / self.stats["query_count"]
            )

            return results

        except Exception as e:
            logger.error(f"❌ 向量搜索失败: {e}")
            return []

    def get_stats(self) -> dict[str, Any]:
        """获取索引统计信息"""
        return self.stats.copy()
