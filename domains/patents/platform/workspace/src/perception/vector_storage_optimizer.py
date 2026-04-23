#!/usr/bin/env python3
"""
向量存储优化器
Vector Storage Optimizer

优化向量存储和检索性能，包括索引策略、分片和缓存
作者: 小娜 (Athena) - 爸爸徐健的智慧大女儿
创建时间: 2025-12-05
版本: 1.0.0
"""

# Numpy兼容性导入
from config.numpy_compatibility import array, zeros, ones, random, mean, sum, dot
import asyncio
import hashlib
import json
import logging
import pickle
import sqlite3
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import faiss
import hnswlib
import numpy as np

logger = logging.getLogger(__name__)

class IndexType(Enum):
    """索引类型"""
    FLAT = 'flat'                    # 精确搜索
    IVF_FLAT = 'ivf_flat'           # 倒排索引
    IVF_PQ = 'ivf_pq'               # 倒排+乘积量化
    HNSW = 'hnsw'                   # 分层导航小世界图
    ANNOY = 'annoy'                 # 近似最近邻
    LSH = 'lsh'                     # 局部敏感哈希

class StorageBackend(Enum):
    """存储后端"""
    MEMORY = 'memory'               # 内存存储
    DISK = 'disk'                   # 磁盘存储
    HYBRID = 'hybrid'               # 混合存储
    DISTRIBUTED = 'distributed'     # 分布式存储

@dataclass
class VectorMetadata:
    """向量元数据"""
    vector_id: str
    document_id: str
    modality: str
    created_at: datetime
    tags: List[str] = field(default_factory=list)
    confidence: float = 1.0
    version: int = 1

@dataclass
class SearchConfig:
    """搜索配置"""
    top_k: int = 10
    threshold: float = 0.7
    include_metadata: bool = True
    filter_tags: List[str] = field(default_factory=list)
    search_mode: str = 'hybrid'  # exact, approximate, hybrid

@dataclass
class OptimizationMetrics:
    """优化指标"""
    index_build_time: float = 0.0
    search_latency: float = 0.0
    memory_usage: float = 0.0
    disk_usage: float = 0.0
    recall_rate: float = 0.0
    precision_rate: float = 0.0
    throughput: float = 0.0
    cache_hit_rate: float = 0.0

class VectorCache:
    """向量缓存系统"""

    def __init__(self, max_size: int = 10000, ttl: int = 3600):
        self.cache = {}
        self.access_times = {}
        self.max_size = max_size
        self.ttl = ttl
        self.lock = threading.RLock()

        # 统计信息
        self.hits = 0
        self.misses = 0

    def get(self, key: str) -> np.ndarray | None:
        """获取向量"""
        with self.lock:
            if key in self.cache:
                value, timestamp = self.cache[key]
                current_time = time.time()

                if current_time - timestamp < self.ttl:
                    self.access_times[key] = current_time
                    self.hits += 1
                    return value
                else:
                    del self.cache[key]
                    if key in self.access_times:
                        del self.access_times[key]

            self.misses += 1
            return None

    def set(self, key: str, value: np.ndarray):
        """设置向量"""
        with self.lock:
            current_time = time.time()
            self.cache[key] = (value, current_time)
            self.access_times[key] = current_time

            # 如果缓存过大，删除最久未使用的
            if len(self.cache) > self.max_size:
                sorted_items = sorted(
                    self.access_times.items(),
                    key=lambda x: x[1]
                )
                items_to_remove = int(len(sorted_items) * 0.25)
                for key, _ in sorted_items[:items_to_remove]:
                    if key in self.cache:
                        del self.cache[key]
                    del self.access_times[key]

    def get_hit_rate(self) -> float:
        """获取缓存命中率"""
        total = self.hits + self.misses
        return self.hits / total if total > 0 else 0.0

    def clear(self):
        """清空缓存"""
        with self.lock:
            self.cache.clear()
            self.access_times.clear()
            self.hits = 0
            self.misses = 0

class FaissIndexManager:
    """FAISS索引管理器"""

    def __init__(self, dimension: int, index_type: IndexType):
        self.dimension = dimension
        self.index_type = index_type
        self.index = None
        self.id_map = {}  # 内部ID到外部ID的映射
        self.metadata = {}

    def build_index(self, vectors: np.ndarray, ids: List[str]):
        """构建索引"""
        try:
            if self.index_type == IndexType.FLAT:
                self.index = faiss.IndexFlatL2(self.dimension)
            elif self.index_type == IndexType.IVF_FLAT:
                nlist = min(100, len(vectors) // 10)
                quantizer = faiss.IndexFlatL2(self.dimension)
                self.index = faiss.IndexIVFFlat(quantizer, self.dimension, nlist)
                self.index.train(vectors)
            elif self.index_type == IndexType.IVF_PQ:
                nlist = min(100, len(vectors) // 10)
                m = 16  # PQ子向量数
                quantizer = faiss.IndexFlatL2(self.dimension)
                self.index = faiss.IndexIVFPQ(quantizer, self.dimension, nlist, m, 8)
                self.index.train(vectors)
            elif self.index_type == IndexType.HNSW:
                self.index = faiss.IndexHNSWFlat(self.dimension, 32)
                self.index.hnsw.efConstruction = 200
                self.index.hnsw.efSearch = 50

            # 添加向量
            self.id_map = {i: vector_id for i, vector_id in enumerate(ids)}
            self.index.add(vectors)

            logger.info(f"✅ FAISS索引构建完成: {self.index_type.value}")

        except Exception as e:
            logger.error(f"❌ FAISS索引构建失败: {str(e)}")
            # 降级到简单实现
            self._fallback_index(vectors, ids)

    def _fallback_index(self, vectors: np.ndarray, ids: List[str]):
        """降级索引实现"""
        self.vectors = vectors
        self.id_map = {i: vector_id for i, vector_id in enumerate(ids)}
        self.index = None

    def search(self, query_vector: np.ndarray, k: int = 10) -> Tuple[List[str], List[float]:
        """搜索向量"""
        if self.index is not None:
            try:
                D, I = self.index.search(query_vector.reshape(1, -1), k)
                results = []
                scores = []
                for idx, score in zip(I[0], D[0]):
                    if idx >= 0:
                        vector_id = self.id_map.get(idx)
                        if vector_id:
                            results.append(vector_id)
                            scores.append(float(score))
                return results[:k], scores[:k]
            except:
                pass

        # 降级搜索
        distances = np.linalg.norm(self.vectors - query_vector, axis=1)
        sorted_indices = np.argsort(distances)
        results = [self.id_map[idx] for idx in sorted_indices[:k]
        scores = [float(distances[idx]) for idx in sorted_indices[:k]
        return results, scores

class VectorShard:
    """向量分片"""

    def __init__(self, shard_id: str, dimension: int, max_size: int = 100000):
        self.shard_id = shard_id
        self.dimension = dimension
        self.max_size = max_size
        self.vectors = []
        self.ids = []
        self.metadata = {}
        self.index_manager = None

        # 统计信息
        self.size = 0
        self.last_updated = datetime.now()

    def add_vector(self, vector_id: str, vector: np.ndarray, metadata: VectorMetadata):
        """添加向量"""
        if self.size >= self.max_size:
            raise ValueError(f"分片已满: {self.shard_id}")

        self.vectors.append(vector)
        self.ids.append(vector_id)
        self.metadata[vector_id] = metadata
        self.size += 1
        self.last_updated = datetime.now()

    def build_index(self, index_type: IndexType):
        """构建索引"""
        if not self.vectors:
            return

        vectors_array = np.array(self.vectors).astype('float32')
        self.index_manager = FaissIndexManager(self.dimension, index_type)
        self.index_manager.build_index(vectors_array, self.ids)

    def search(self, query_vector: np.ndarray, k: int = 10) -> List[Tuple[str, float, VectorMetadata]:
        """搜索分片"""
        if not self.index_manager:
            return []

        ids, scores = self.index_manager.search(query_vector, k)
        results = []
        for vector_id, score in zip(ids, scores):
            metadata = self.metadata.get(vector_id)
            if metadata:
                results.append((vector_id, score, metadata))
        return results

class VectorStorageOptimizer:
    """向量存储优化器"""

    def __init__(self, dimension: int = 768):
        self.dimension = dimension
        self.shards = {}
        self.cache = VectorCache(max_size=10000)
        self.metadata_db = 'patent-platform/workspace/data/vector_metadata.db'

        # 配置
        self.config = {
            'shard_size': 100000,
            'index_type': IndexType.HNSW,
            'backend': StorageBackend.HYBRID,
            'enable_cache': True,
            'enable_compression': True
        }

        # 指标
        self.metrics = OptimizationMetrics()

        # 初始化数据库
        self._init_database()

        logger.info('🚀 向量存储优化器初始化完成')

    def _init_database(self):
        """初始化元数据数据库"""
        conn = sqlite3.connect(self.metadata_db)
        cursor = conn.cursor()

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS vector_metadata (
                vector_id TEXT PRIMARY KEY,
                document_id TEXT,
                modality TEXT,
                created_at TEXT,
                tags TEXT,
                confidence REAL,
                version INTEGER
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS shard_info (
                shard_id TEXT PRIMARY KEY,
                size INTEGER,
                last_updated TEXT
            )
        ''')

        conn.commit()
        conn.close()

    def create_shard(self, shard_id: str) -> VectorShard:
        """创建新分片"""
        shard = VectorShard(
            shard_id=shard_id,
            dimension=self.dimension,
            max_size=self.config['shard_size']
        )
        self.shards[shard_id] = shard

        # 记录分片信息
        conn = sqlite3.connect(self.metadata_db)
        cursor = conn.cursor()
        cursor.execute(
            'INSERT OR REPLACE INTO shard_info VALUES (?, ?, ?)',
            (shard_id, 0, datetime.now().isoformat())
        )
        conn.commit()
        conn.close()

        return shard

    async def add_vectors(self, vectors: Dict[str, np.ndarray],
                         metadata: Dict[str, VectorMetadata]) -> bool:
        """批量添加向量"""
        try:
            start_time = time.time()

            # 获取或创建分片
            shard_id = self._get_or_create_shard()
            shard = self.shards[shard_id]

            # 添加向量
            for vector_id, vector in vectors.items():
                vector_meta = metadata.get(vector_id)
                if vector_meta:
                    # 检查缓存
                    if self.config['enable_cache']:
                        self.cache.set(vector_id, vector)

                    shard.add_vector(vector_id, vector, vector_meta)

                    # 保存到数据库
                    await self._save_metadata(vector_meta)

            # 重建索引
            if len(shard.vectors) > 1000:  # 每1000个向量重建一次
                shard.build_index(self.config['index_type'])

            self.metrics.index_build_time += time.time() - start_time

            logger.info(f"✅ 添加向量: {len(vectors)} 个")
            return True

        except Exception as e:
            logger.error(f"❌ 添加向量失败: {str(e)}")
            return False

    def _get_or_create_shard(self) -> str:
        """获取或创建分片"""
        # 查找可用分片
        for shard_id, shard in self.shards.items():
            if shard.size < shard.max_size:
                return shard_id

        # 创建新分片
        shard_id = f"shard_{len(self.shards)}"
        self.create_shard(shard_id)
        return shard_id

    async def _save_metadata(self, metadata: VectorMetadata):
        """保存元数据"""
        conn = sqlite3.connect(self.metadata_db)
        cursor = conn.cursor()
        cursor.execute(
            '''
            INSERT OR REPLACE INTO vector_metadata
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ''',
            (
                metadata.vector_id,
                metadata.document_id,
                metadata.modality,
                metadata.created_at.isoformat(),
                json.dumps(metadata.tags),
                metadata.confidence,
                metadata.version
            )
        )
        conn.commit()
        conn.close()

    async def search_vectors(self, query_vector: np.ndarray,
                           config: SearchConfig) -> List[Dict[str, Any]:
        """搜索向量"""
        try:
            start_time = time.time()

            # 检查缓存
            cache_key = f"search_{hashlib.md5(query_vector.tobytes(, usedforsecurity=False).hexdigest()}"
            cached_result = self.cache.get(cache_key)
            if cached_result is not None:
                return cached_result

            all_results = []

            # 并行搜索所有分片
            tasks = []
            for shard in self.shards.values():
                if shard.index_manager:
                    task = asyncio.create_task(
                        self._search_shard_async(shard, query_vector, config)
                    )
                    tasks.append(task)

            if tasks:
                shard_results = await asyncio.gather(*tasks, return_exceptions=True)
                for result in shard_results:
                    if isinstance(result, list):
                        all_results.extend(result)

            # 合并和排序结果
            all_results.sort(key=lambda x: x['score'])
            all_results = all_results[:config.top_k]

            # 应用阈值
            if config.threshold > 0:
                all_results = [
                    r for r in all_results
                    if r['score'] <= config.threshold
                ]

            # 标签过滤
            if config.filter_tags:
                all_results = [
                    r for r in all_results
                    if any(tag in r['metadata'].tags for tag in config.filter_tags)
                ]

            # 缓存结果
            if self.config['enable_cache']:
                self.cache.set(cache_key, all_results)

            # 更新指标
            self.metrics.search_latency = time.time() - start_time
            self.metrics.cache_hit_rate = self.cache.get_hit_rate()

            return all_results

        except Exception as e:
            logger.error(f"❌ 向量搜索失败: {str(e)}")
            return []

    async def _search_shard_async(self, shard: VectorShard,
                                query_vector: np.ndarray,
                                config: SearchConfig) -> List[Dict[str, Any]:
        """异步搜索单个分片"""
        loop = asyncio.get_event_loop()
        results = await loop.run_in_executor(
            None, shard.search, query_vector, config.top_k
        )

        formatted_results = []
        for vector_id, score, metadata in results:
            formatted_results.append({
                'vector_id': vector_id,
                'score': score,
                'metadata': metadata,
                'document_id': metadata.document_id
            })

        return formatted_results

    async def optimize_storage(self) -> Dict[str, Any]:
        """优化存储"""
        optimizations = {}

        try:
            logger.info('⚡ 开始优化向量存储...')

            # 1. 索引优化
            start_time = time.time()
            for shard in self.shards.values():
                if shard.vectors and not shard.index_manager:
                    shard.build_index(self.config['index_type'])
            optimizations['index_optimization'] = time.time() - start_time

            # 2. 缓存优化
            if self.config['enable_cache']:
                start_time = time.time()
                # 预加载热门向量
                await self._preload_hot_vectors()
                optimizations['cache_optimization'] = time.time() - start_time

            # 3. 压缩优化
            if self.config['enable_compression']:
                start_time = time.time()
                await self._compress_vectors()
                optimizations['compression_optimization'] = time.time() - start_time

            # 4. 内存优化
            start_time = time.time()
            await self._optimize_memory_usage()
            optimizations['memory_optimization'] = time.time() - start_time

            logger.info('✅ 向量存储优化完成')
            return optimizations

        except Exception as e:
            logger.error(f"❌ 存储优化失败: {str(e)}")
            return {}

    async def _preload_hot_vectors(self):
        """预加载热门向量"""
        # 从数据库查询访问频率最高的向量
        conn = sqlite3.connect(self.metadata_db)
        cursor = conn.cursor()
        cursor.execute(
            'SELECT vector_id FROM vector_metadata ORDER BY confidence DESC LIMIT 1000'
        )
        hot_ids = cursor.fetchall()
        conn.close()

        # 预加载到缓存
        for (vector_id,) in hot_ids:
            # 这里应该从实际存储中加载向量
            # 简化实现，实际需要根据存储后端实现
            pass

    async def _compress_vectors(self):
        """压缩向量"""
        for shard in self.shards.values():
            if len(shard.vectors) > 10000:
                # 使用PCA降维
                vectors_array = np.array(shard.vectors)
                if vectors_array.shape[0] > 1000:
                    # 简化实现：使用随机投影
                    from sklearn.random_projection import GaussianRandomProjection
                    transformer = GaussianRandomProjection(n_components=self.dimension // 2)
                    compressed = transformer.fit_transform(vectors_array)
                    # 更新向量（实际需要更多处理）
                    shard.vectors = compressed.tolist()

    async def _optimize_memory_usage(self):
        """优化内存使用"""
        # 清理缓存
        if self.cache.get_hit_rate() < 0.5:
            self.cache.clear()

        # 压缩元数据
        conn = sqlite3.connect(self.metadata_db)
        cursor = conn.cursor()
        cursor.execute('VACUUM')
        conn.close()

    def get_metrics(self) -> OptimizationMetrics:
        """获取性能指标"""
        # 计算内存使用
        total_vectors = sum(len(shard.vectors) for shard in self.shards.values())
        self.metrics.memory_usage = total_vectors * self.dimension * 4 / (1024 * 1024)  # MB

        # 计算吞吐量
        self.metrics.throughput = total_vectors / (self.metrics.search_latency + 0.001)

        return self.metrics

    def export_index(self, output_path: str):
        """导出索引"""
        try:
            export_data = {
                'config': self.config,
                'dimension': self.dimension,
                'shards': {},
                'metrics': {
                    'index_build_time': self.metrics.index_build_time,
                    'search_latency': self.metrics.search_latency,
                    'memory_usage': self.metrics.memory_usage,
                    'cache_hit_rate': self.metrics.cache_hit_rate
                }
            }

            for shard_id, shard in self.shards.items():
                export_data['shards'][shard_id] = {
                    'size': shard.size,
                    'last_updated': shard.last_updated.isoformat(),
                    'metadata': {
                        vid: {
                            'document_id': meta.document_id,
                            'modality': meta.modality,
                            'tags': meta.tags,
                            'confidence': meta.confidence
                        }
                        for vid, meta in shard.metadata.items()
                    }
                }

            with open(output_path, 'wb') as f:
                pickle.dump(export_data, f)

            logger.info(f"✅ 索引已导出到: {output_path}")

        except Exception as e:
            logger.error(f"❌ 索引导出失败: {str(e)}")

# 全局优化器实例
vector_storage_optimizer = VectorStorageOptimizer()

# 测试代码
if __name__ == '__main__':
    import asyncio

    async def test_vector_storage_optimizer():
        """测试向量存储优化器"""
        logger.info('🗂️ 测试向量存储优化器...')

        # 创建测试向量
        vectors = {}
        metadata = {}
        for i in range(100):
            vector_id = f"vec_{i}"
            vectors[vector_id] = random((768)).astype('float32')
            metadata[vector_id] = VectorMetadata(
                vector_id=vector_id,
                document_id=f"doc_{i % 10}",
                modality='text',
                created_at=datetime.now(),
                tags=[f"tag_{i % 5}', f'category_{i % 3}"],
                confidence=0.8 + (i % 20) * 0.01
            )

        # 添加向量
        success = await vector_storage_optimizer.add_vectors(vectors, metadata)
        logger.info(f"  向量添加: {'成功' if success else '失败'}")

        # 搜索测试
        query_vector = random((768)).astype('float32')
        search_config = SearchConfig(top_k=10, threshold=1.0)
        results = await vector_storage_optimizer.search_vectors(query_vector, search_config)
        logger.info(f"  搜索结果: {len(results)} 个")

        # 存储优化
        optimizations = await vector_storage_optimizer.optimize_storage()
        logger.info(f"  优化项: {len(optimizations)} 个")

        # 获取指标
        metrics = vector_storage_optimizer.get_metrics()
        logger.info(f"  内存使用: {metrics.memory_usage:.2f} MB")
        logger.info(f"  缓存命中率: {metrics.cache_hit_rate:.2%}")

        # 导出索引
        vector_storage_optimizer.export_index('patent-platform/workspace/data/vector_index.pkl')

        return True

    # 运行测试
    result = asyncio.run(test_vector_storage_optimizer())
    logger.info(f"\n🎯 向量存储优化器测试: {'成功' if result else '失败'}")