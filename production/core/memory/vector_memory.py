#!/usr/bin/env python3
"""
向量记忆系统
Vector Memory System

从备份的优化版本迁移并集成到新核心架构
提供高性能的向量存储和语义搜索能力

作者: 小娜 AI系统
创建时间: 2025-12-04
版本: 3.0.0
"""

# Numpy兼容性导入
from __future__ import annotations
import logging
import time
from datetime import datetime
from typing import Any

import numpy as np

from config.numpy_compatibility import zeros

logger = logging.getLogger(__name__)

class VectorSearchEngine:
    """优化的向量搜索引擎"""

    def __init__(self, dimension: int = 1024, use_optimized: bool = True):
        self.dimension = dimension
        self.use_optimized = use_optimized
        self.vectors = []
        self.metadata = []
        self.index_built = False
        self.last_build_time = 0

        # 简化的KD树实现（避免外部依赖）
        self.vector_tree = None

    def add_vector(self, vector: np.ndarray, metadata: dict[str, Any]) -> int:
        """添加单个向量"""
        if len(vector) != self.dimension:
            raise ValueError(f"向量维度不匹配: 期望{self.dimension}, 实际{len(vector)}")

        self.vectors.append(vector.astype(np.float32))
        self.metadata.append(metadata)
        self.index_built = False

        return len(self.vectors) - 1

    def add_vectors(self, vectors: list[list[float]], metadata_list: list[dict[str, Any]]) -> list[int]:
        """批量添加向量"""
        indices = []
        for vector, metadata in zip(vectors, metadata_list, strict=False):
            indices.append(self.add_vector(vector, metadata))
        return indices

    def build_index(self) -> None:
        """构建搜索索引"""
        if not self.vectors:
            return

        if self.use_optimized:
            # 构建简化的索引结构
            self.vector_tree = {
                'vectors': np.array(self.vectors, dtype=np.float32),
                'built_at': time.time()
            }

        self.index_built = True
        self.last_build_time = time.time()
        logger.debug(f"构建向量索引完成: {len(self.vectors)} 个向量")

    def search(self, query_vector: np.ndarray, k: int = 10, threshold: float = 0.0) -> list[tuple[int, float, dict[str, Any]]]:
        """搜索最相似的向量"""
        if not self.vectors:
            return []

        if len(query_vector) != self.dimension:
            raise ValueError(f"查询向量维度不匹配: 期望{self.dimension}, 实际{len(query_vector)}")

        if not self.index_built:
            self.build_index()

        query_vector = query_vector.astype(np.float32)

        if self.use_optimized and self.vector_tree:
            # 优化的搜索实现
            vectors_array = self.vector_tree['vectors']

            # 计算余弦相似度
            dot_products = np.dot(vectors_array, query_vector)
            norm_query = np.linalg.norm(query_vector)
            norm_vectors = np.linalg.norm(vectors_array, axis=1)

            # 避免除零
            valid_indices = norm_vectors > 0
            if not np.any(valid_indices):
                return []

            similarities = zeros(len(vectors_array))
            similarities[valid_indices] = dot_products[valid_indices] / (norm_query * norm_vectors[valid_indices])

            # 获取top-k结果
            if threshold > 0:
                valid_mask = similarities >= threshold
                valid_indices = np.where(valid_mask)[0]
                if len(valid_indices) == 0:
                    return []

                sorted_indices = valid_indices[np.argsort(-similarities[valid_indices])[:k]]
            else:
                sorted_indices = np.argsort(-similarities)[:k]

            results = []
            for idx in sorted_indices:
                if idx < len(self.metadata):
                    similarity = float(similarities[idx])
                    distance = 1.0 - similarity  # 转换为距离
                    results.append((int(idx, dtype=np.float64), distance, self.metadata[idx]))

            return results
        else:
            # 暴力搜索
            vectors_array = np.array(self.vectors, dtype=np.float32)

            # 计算欧氏距离
            distances = np.linalg.norm(vectors_array - query_vector, axis=1)

            # 获取top-k
            k = min(k, len(distances))
            sorted_indices = np.argsort(distances)[:k]

            results = []
            for idx in sorted_indices:
                if distances[idx] <= (1.0 - threshold):  # 距离阈值
                    results.append((int(idx), float(distances[idx]), self.metadata[idx]))

            return results

    def delete_vector(self, index: int) -> bool:
        """删除指定索引的向量"""
        if 0 <= index < len(self.vectors):
            del self.vectors[index]
            del self.metadata[index]
            self.index_built = False
            return True
        return False

    def clear(self) -> None:
        """清空所有向量"""
        self.vectors.clear()
        self.metadata.clear()
        self.vector_tree = None
        self.index_built = False

    def get_stats(self) -> dict[str, Any]:
        """获取统计信息"""
        return {
            'vector_count': len(self.vectors),
            'dimension': self.dimension,
            'index_built': self.index_built,
            'last_build_time': self.last_build_time,
            'memory_usage_mb': self._estimate_memory_usage()
        }

    def _estimate_memory_usage(self) -> float:
        """估算内存使用量（MB）"""
        vector_memory = len(self.vectors) * self.dimension * 4  # float32
        metadata_memory = len(str(self.metadata).encode('utf-8'))
        return (vector_memory + metadata_memory) / (1024 * 1024)

class VectorMemorySystem:
    """向量记忆系统 - 适配新核心架构"""

    def __init__(self, agent_id: str, config: dict | None = None):
        self.agent_id = agent_id
        self.config = config or {}
        self.initialized = False

        # 向量搜索引擎配置
        self.dimension = self.config.get('dimension', 1024)
        self.use_optimized = self.config.get('use_optimized', True)
        self.max_vectors = self.config.get('max_vectors', 10000)

        # 创建搜索引擎
        self.search_engine = VectorSearchEngine(
            dimension=self.dimension,
            use_optimized=self.use_optimized
        )

        # 记忆分类
        self.memory_categories = {
            'episodic': [],    # 情景记忆
            'semantic': [],     # 语义记忆
            'procedural': [],   # 程序记忆
            'working': []       # 工作记忆
        }

        logger.info(f"🧠 向量记忆系统创建: {self.agent_id} (维度: {self.dimension})")

    async def initialize(self):
        """初始化向量记忆系统"""
        if self.initialized:
            return

        logger.info(f"🚀 启动向量记忆系统: {self.agent_id}")

        # 尝试加载持久化数据
        await self._load_persisted_data()

        self.initialized = True
        logger.info(f"✅ 向量记忆系统启动完成: {self.agent_id}")

    async def store_memory(
        self,
        content: Any,
        category: str = 'episodic',
        embedding: np.ndarray | None = None,
        metadata: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """存储向量记忆"""
        if not self.initialized:
            raise RuntimeError('向量记忆系统未初始化')

        if category not in self.memory_categories:
            category = 'episodic'

        # 如果没有提供嵌入向量，生成模拟向量
        if embedding is None:
            embedding = self._generate_mock_embedding(str(content))

        # 构建元数据
        memory_metadata = {
            'agent_id': self.agent_id,
            'category': category,
            'content': str(content)[:500],  # 限制内容长度
            'timestamp': datetime.now().isoformat(),
            'embedding_source': 'generated' if embedding is None else 'provided',
            **(metadata or {})
        }

        try:
            # 添加到向量搜索引擎
            vector_id = self.search_engine.add_vector(embedding, memory_metadata)

            # 添加到分类记录
            self.memory_categories[category].append({
                'vector_id': vector_id,
                'content_summary': memory_metadata['content'][:100],
                'timestamp': memory_metadata['timestamp']
            })

            # 检查向量数量限制
            await self._enforce_vector_limit()

            logger.debug(f"✅ 向量记忆存储成功: category={category}, vector_id={vector_id}")

            return {
                'success': True,
                'vector_id': vector_id,
                'category': category,
                'timestamp': memory_metadata['timestamp'],
                'agent_id': self.agent_id
            }

        except Exception as e:
            logger.error(f"❌ 向量记忆存储失败: {e}")
            return {
                'success': False,
                'error': str(e),
                'agent_id': self.agent_id
            }

    async def search_memories(
        self,
        query: str,
        category: str | None = None,
        k: int = 10,
        threshold: float = 0.3,
        embedding: np.ndarray | None = None
    ) -> dict[str, Any]:
        """搜索相关记忆"""
        if not self.initialized:
            raise RuntimeError('向量记忆系统未初始化')

        try:
            # 生成查询向量
            if embedding is None:
                query_embedding = self._generate_mock_embedding(query)
            else:
                query_embedding = embedding

            # 执行向量搜索
            search_results = self.search_engine.search(
                query_embedding,
                k=k,
                threshold=threshold
            )

            # 过滤分类
            if category and category in self.memory_categories:
                category_ids = {item['vector_id'] for item in self.memory_categories[category]}
                search_results = [
                    (idx, dist, meta) for idx, dist, meta in search_results
                    if idx in category_ids
                ]

            # 格式化结果
            memories = []
            for vector_id, distance, metadata in search_results:
                similarity = 1.0 - distance
                memories.append({
                    'vector_id': vector_id,
                    'content': metadata['content'],
                    'category': metadata['category'],
                    'timestamp': metadata['timestamp'],
                    'similarity': similarity,
                    'distance': distance,
                    'metadata': metadata
                })

            return {
                'success': True,
                'query': query[:100] + '...' if len(query) > 100 else query,
                'category': category,
                'total_found': len(memories),
                'memories': memories,
                'search_stats': self.search_engine.get_stats(),
                'agent_id': self.agent_id
            }

        except Exception as e:
            logger.error(f"❌ 记忆搜索失败: {e}")
            return {
                'success': False,
                'error': str(e),
                'agent_id': self.agent_id
            }

    async def delete_memory(self, vector_id: int) -> dict[str, Any]:
        """删除指定记忆"""
        if not self.initialized:
            raise RuntimeError('向量记忆系统未初始化')

        try:
            success = self.search_engine.delete_vector(vector_id)

            if success:
                # 从分类记录中移除
                for category_key, category_items in self.memory_categories.items():
                    self.memory_categories[category_key] = [
                        item for item in category_items
                        if item['vector_id'] != vector_id
                    ]

            return {
                'success': success,
                'vector_id': vector_id,
                'agent_id': self.agent_id
            }

        except Exception as e:
            logger.error(f"❌ 记忆删除失败: {e}")
            return {
                'success': False,
                'error': str(e),
                'agent_id': self.agent_id
            }

    async def get_memory_stats(self) -> dict[str, Any]:
        """获取记忆统计信息"""
        if not self.initialized:
            raise RuntimeError('向量记忆系统未初始化')

        category_counts = {
            category: len(items)
            for category, items in self.memory_categories.items()
        }

        return {
            'agent_id': self.agent_id,
            'total_memories': len(self.search_engine.vectors),
            'category_counts': category_counts,
            'search_engine_stats': self.search_engine.get_stats(),
            'config': {
                'dimension': self.dimension,
                'max_vectors': self.max_vectors,
                'use_optimized': self.use_optimized
            },
            'timestamp': datetime.now().isoformat()
        }

    async def clear_memories(self, category: str | None = None) -> dict[str, Any]:
        """清空记忆"""
        if not self.initialized:
            raise RuntimeError('向量记忆系统未初始化')

        try:
            if category and category in self.memory_categories:
                # 只清空指定分类
                vector_ids = [item['vector_id'] for item in self.memory_categories[category]]
                for vector_id in sorted(vector_ids, reverse=True):  # 倒序删除避免索引变化
                    self.search_engine.delete_vector(vector_id)
                self.memory_categories[category] = []

                cleared_count = len(vector_ids)
            else:
                # 清空所有记忆
                cleared_count = len(self.search_engine.vectors)
                self.search_engine.clear()
                for cat in self.memory_categories:
                    self.memory_categories[cat] = []

            return {
                'success': True,
                'cleared_count': cleared_count,
                'category': category,
                'agent_id': self.agent_id
            }

        except Exception as e:
            logger.error(f"❌ 记忆清空失败: {e}")
            return {
                'success': False,
                'error': str(e),
                'agent_id': self.agent_id
            }

    def _generate_mock_embedding(self, text: str) -> np.ndarray:
        """生成模拟嵌入向量（在没有实际NLP模型时使用）"""
        # 基于文本内容生成确定性向量
        text_bytes = text.encode('utf-8')

        # 生成固定长度的向量
        vector = zeros(self.dimension, dtype=np.float32)

        # 简单的哈希映射
        for i, byte in enumerate(text_bytes[:self.dimension]):
            vector[i % self.dimension] = float(byte) / 255.0

        # 添加一些变化使向量更真实
        for i in range(self.dimension):
            vector[i] += np.sin(i + len(text)) * 0.1
            vector[i] = np.clip(vector[i], -1.0, 1.0)

        # 归一化
        norm = np.linalg.norm(vector)
        if norm > 0:
            vector = vector / norm

        return vector

    async def _enforce_vector_limit(self):
        """强制执行向量数量限制"""
        current_count = len(self.search_engine.vectors)
        if current_count > self.max_vectors:
            # 删除最旧的向量（简单实现）
            excess_count = current_count - self.max_vectors
            for _ in range(excess_count):
                if self.search_engine.vectors:
                    # 删除第一个向量（最旧的）
                    self.search_engine.delete_vector(0)

                    # 更新分类记录中的vector_id
                    for category in self.memory_categories:
                        self.memory_categories[category] = [
                            {**item, 'vector_id': item['vector_id'] - 1}
                            for item in self.memory_categories[category]
                            if item['vector_id'] > 0
                        ]

    async def _load_persisted_data(self):
        """加载持久化数据（简化实现）"""
        # 这里可以实现从文件或数据库加载历史记忆
        # 目前跳过，使用空记忆开始
        pass

    async def _persist_data(self):
        """持久化数据（简化实现）"""
        # 这里可以实现将记忆保存到文件或数据库
        # 目前跳过
        pass

    async def shutdown(self):
        """关闭向量记忆系统"""
        logger.info(f"🔄 关闭向量记忆系统: {self.agent_id}")

        try:
            # 持久化数据
            await self._persist_data()

            # 清理资源
            self.search_engine.clear()

        except Exception as e:
            logger.error(f"❌ 向量记忆系统关闭失败: {e}")

        self.initialized = False

    # 注册回调支持
    def register_callback(self, event_type: str, callback):
        """注册回调函数"""
        if not hasattr(self, '_callbacks'):
            self._callbacks = {}
        if event_type not in self._callbacks:
            self._callbacks[event_type] = []
        self._callbacks[event_type].append(callback)

# 全局实例管理
_global_instances: dict[str, VectorMemorySystem] = {}

async def get_vector_memory_instance(agent_id: str | None = None, config: dict | None = None) -> VectorMemorySystem:
    """获取向量记忆实例"""
    if agent_id not in _global_instances:
        _global_instances[agent_id] = VectorMemorySystem(agent_id, config)
        await _global_instances[agent_id].initialize()
    return _global_instances[agent_id]

async def shutdown_vector_memory(agent_id: str | None = None):
    """关闭向量记忆实例"""
    if agent_id:
        if agent_id in _global_instances:
            await _global_instances[agent_id].shutdown()
            del _global_instances[agent_id]
    else:
        # 关闭所有实例
        for _instance_id, instance in list(_global_instances.items()):
            await instance.shutdown()
        _global_instances.clear()

__all__ = [
    'VectorMemorySystem',
    'VectorSearchEngine',
    'get_vector_memory_instance',
    'shutdown_vector_memory'
]
