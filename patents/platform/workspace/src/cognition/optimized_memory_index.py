#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
优化记忆索引系统
Optimized Memory Index System

提供高性能的记忆索引、检索和相似度计算功能

作者: Athena AI系统
创建时间: 2025-12-11
版本: 1.0.0
"""

# Numpy兼容性导入
from config.numpy_compatibility import array, zeros, ones, random, mean, sum, dot
import asyncio
import bisect
import hashlib
import heapq
import json
import logging
import pickle
import sqlite3
import threading
import time
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple, Union

# 尝试导入向量计算库
try:
    import faiss  # Facebook AI Similarity Search
    import numpy as np
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity
    FAISS_AVAILABLE = True
except ImportError:
    FAISS_AVAILABLE = False
    import numpy as np
    logging.warning('Faiss或Scikit-learn不可用，使用基础索引功能')

logger = logging.getLogger(__name__)

class IndexType(Enum):
    """索引类型"""
    INVERTED = 'inverted'               # 倒排索引
    TF_IDF = 'tf_idf'                  # TF-IDF索引
    VECTOR = 'vector'                  # 向量索引
    LSH = 'lsh'                        # 局部敏感哈希
    HIERARCHICAL = 'hierarchical'       # 层次索引
    COMPOSITE = 'composite'            # 复合索引

@dataclass
class IndexEntry:
    """索引条目"""
    id: str
    content: str
    vector: np.ndarray | None = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)
    access_count: int = 0
    last_accessed: datetime = field(default_factory=datetime.now)

class OptimizedMemoryIndex:
    """优化的记忆索引系统"""

    def __init__(self,
                 index_type = IndexType.COMPOSITE,
                 use_faiss: bool = True,
                 dimension: int = 1024):  # 默认1024维
        # 验证和标准化索引类型
        self.index_type = self._validate_index_type(index_type)
        self.use_faiss = use_faiss and FAISS_AVAILABLE
        self.dimension = dimension

        # 存储索引数据
        self.entries: Dict[str, IndexEntry] = {}
        self.index_lock = threading.RLock()

        # 不同类型的索引
        self.inverted_index: Dict[str, Set[str]] = defaultdict(set)
        self.tfidf_vectorizer = None
        self.tfidf_matrix = None
        self.vector_index = None
        self.lsh_hashes: Dict[int, Set[str]] = defaultdict(set)
        self.hierarchical_index: Dict[str, List[IndexEntry]] = defaultdict(list)

        # 性能统计
        self.stats = {
            'total_entries': 0,
            'index_size': 0,
            'query_count': 0,
            'average_query_time': 0.0,
            'cache_hits': 0,
            'cache_misses': 0
        }

        # 查询缓存
        self.query_cache: Dict[str, Tuple[float, List[str]]] = {}
        self.cache_max_size = 1000

        # 初始化索引
        self._initialize_indexes()

    def _validate_index_type(self, index_type):
        """验证索引类型"""
        if isinstance(index_type, str):
            try:
                return IndexType(index_type)
            except ValueError:
                logger.warning(f"无效的索引类型: {index_type}，使用默认值")
                return IndexType.COMPOSITE
        elif isinstance(index_type, IndexType):
            return index_type
        else:
            logger.warning(f"索引类型参数错误: {type(index_type)}，使用默认值")
            return IndexType.COMPOSITE

    def _initialize_indexes(self):
        """初始化各种索引"""
        if self.index_type in [IndexType.TF_IDF, IndexType.COMPOSITE]:
            self.tfidf_vectorizer = TfidfVectorizer(
                max_features=10000,
                stop_words=None,  # 中文停用词需要特殊处理
                ngram_range=(1, 2)
            )

        if self.index_type in [IndexType.VECTOR, IndexType.COMPOSITE] and self.use_faiss:
            # 初始化Faiss索引
            self.vector_index = faiss.IndexFlatIP(self.dimension)  # 内积索引
            logger.info(f"🔍 初始化Faiss向量索引，维度: {self.dimension}")

        logger.info(f"✅ 优化记忆索引系统初始化完成，类型: {self.index_type.value if hasattr(self.index_type, 'value') else str(self.index_type)}")

    def add_entry(self, entry: IndexEntry):
        """添加索引条目"""
        with self.index_lock:
            self.entries[entry.id] = entry
            self.stats['total_entries'] += 1

            # 更新各种索引
            self._update_inverted_index(entry)
            self._update_tfidf_index(entry)
            self._update_vector_index(entry)
            self._update_lsh_index(entry)
            self._update_hierarchical_index(entry)

            # 清理缓存
            if len(self.query_cache) > self.cache_max_size:
                self._cleanup_cache()

    def _update_inverted_index(self, entry: IndexEntry):
        """更新倒排索引"""
        if self.index_type not in [IndexType.INVERTED, IndexType.COMPOSITE]:
            return

        # 提取关键词
        keywords = self._extract_keywords(entry.content)
        for keyword in keywords:
            self.inverted_index[keyword].add(entry.id)

    def _update_tfidf_index(self, entry: IndexEntry):
        """更新TF-IDF索引"""
        if self.index_type not in [IndexType.TF_IDF, IndexType.COMPOSITE]:
            return

        if not self.tfidf_vectorizer:
            return

        # 重建TF-IDF矩阵（简化实现，实际应用中应增量更新）
        all_contents = [e.content for e in self.entries.values()]
        if all_contents:
            self.tfidf_matrix = self.tfidf_vectorizer.fit_transform(all_contents)

    def _update_vector_index(self, entry: IndexEntry):
        """更新向量索引"""
        if self.index_type not in [IndexType.VECTOR, IndexType.COMPOSITE]:
            return

        if entry.vector is None:
            return

        if self.use_faiss and self.vector_index:
            # 添加到Faiss索引
            vector = entry.vector.reshape(1, -1).astype('float32')
            # 归一化向量（用于余弦相似度）
            faiss.normalize_L2(vector)
            self.vector_index.add(vector)

    def _update_lsh_index(self, entry: IndexEntry):
        """更新局部敏感哈希索引"""
        if self.index_type != IndexType.LSH:
            return

        if entry.vector is None:
            return

        # 简化的LSH实现（随机投影）
        num_hash_tables = 10
        hash_size = 8

        for table_id in range(num_hash_tables):
            # 生成随机投影矩阵（实际应用中应预计算）
            random_vector = random((self.dimension))
            hash_value = int(np.dot(entry.vector, random_vector) % (2 ** hash_size))
            self.lsh_hashes[(table_id, hash_value)].add(entry.id)

    def _update_hierarchical_index(self, entry: IndexEntry):
        """更新层次索引"""
        if self.index_type != IndexType.HIERARCHICAL:
            return

        # 基于时间戳的层次索引
        date_key = entry.timestamp.strftime('%Y-%m')
        self.hierarchical_index[date_key].append(entry)

        # 按访问频率分类
        if entry.access_count > 10:
            self.hierarchical_index['hot'].append(entry)
        elif entry.access_count > 5:
            self.hierarchical_index['warm'].append(entry)
        else:
            self.hierarchical_index['cold'].append(entry)

    def _extract_keywords(self, text: str) -> List[str]:
        """提取关键词"""
        import re

        # 简单的中英文分词
        words = re.findall(r'[\u4e00-\u9fff]+|[a-zA-Z]+', text.lower())

        # 过滤停用词和短词
        stop_words = {
            '的', '是', '在', '有', '和', '与', '或', '但', '如果', '因为', '所以',
            'the', 'is', 'at', 'which', 'on', 'and', 'or', 'but', 'if', 'because'
        }

        keywords = [word for word in words if len(word) > 1 and word not in stop_words]

        # 返回前20个关键词
        return keywords[:20]

    async def search(self,
                    query: str,
                    top_k: int = 10,
                    similarity_threshold: float = 0.01,  # 降低阈值，提高召回率
                    search_type: str = 'hybrid') -> List[Tuple[str, float]]:
        """搜索索引"""
        start_time = time.time()

        # 检查缓存
        cache_key = f"{query}_{top_k}_{similarity_threshold}_{search_type}"
        if cache_key in self.query_cache:
            cached_time, cached_result = self.query_cache[cache_key]
            if time.time() - cached_time < 300:  # 5分钟缓存
                self.stats['cache_hits'] += 1
                return cached_result

        self.stats['cache_misses'] += 1
        self.stats['query_count'] += 1

        # 执行搜索
        if search_type == 'keyword':
            results = await self._keyword_search(query, top_k)
        elif search_type == 'semantic':
            results = await self._semantic_search(query, top_k)
        elif search_type == 'tfidf':
            results = await self._tfidf_search(query, top_k)
        elif search_type == 'vector':
            results = await self._vector_search(query, top_k)
        else:  # hybrid
            results = await self._hybrid_search(query, top_k)

        # 过滤低相似度结果
        filtered_results = [(eid, score) for eid, score in results if score >= similarity_threshold]
        filtered_results = filtered_results[:top_k]

        # 更新缓存
        self.query_cache[cache_key] = (time.time(), filtered_results)

        # 更新统计
        query_time = time.time() - start_time
        total_queries = self.stats['query_count']
        if total_queries > 0:
            self.stats['average_query_time'] = (
                (self.stats['average_query_time'] * (total_queries - 1) + query_time) / total_queries
            )

        return filtered_results

    async def _keyword_search(self, query: str, top_k: int) -> List[Tuple[str, float]]:
        """关键词搜索"""
        query_keywords = self._extract_keywords(query)
        candidate_ids = set()

        # 从倒排索引获取候选
        for keyword in query_keywords:
            if keyword in self.inverted_index:
                candidate_ids.update(self.inverted_index[keyword])

        # 如果没有找到候选，进行全文搜索
        if not candidate_ids:
            for entry_id, entry in self.entries.items():
                if any(keyword.lower() in entry.content.lower() for keyword in query_keywords):
                    candidate_ids.add(entry_id)

        # 计算相关性分数
        results = []
        for entry_id in candidate_ids:
            if entry_id in self.entries:
                entry = self.entries[entry_id]
                entry_keywords = self._extract_keywords(entry.content)

                # 改进的相关性计算
                query_set = set(query_keywords)
                entry_set = set(entry_keywords)

                # Jaccard相似度
                intersection = len(query_set & entry_set)
                union = len(query_set | entry_set)
                jaccard_score = intersection / union if union > 0 else 0

                # 频次加权
                freq_score = sum(query_keywords.count(k) for k in entry_keywords) / len(query_keywords)

                # 位置加权（开头出现的词更重要）
                content_lower = entry.content.lower()
                position_score = 0
                for i, keyword in enumerate(query_keywords):
                    pos = content_lower.find(keyword.lower())
                    if pos != -1:
                        position_score += 1.0 / (1 + pos / 100)  # 位置越靠前，分数越高

                # 综合评分
                final_score = 0.5 * jaccard_score + 0.3 * freq_score + 0.2 * position_score

                # 如果直接包含查询词，给予额外加分
                if any(keyword.lower() in content_lower for keyword in query_keywords):
                    final_score += 0.2

                results.append((entry_id, min(final_score, 1.0)))  # 限制在[0,1]范围内

        # 排序并返回
        results.sort(key=lambda x: x[1], reverse=True)
        return results[:top_k]

    async def _semantic_search(self, query: str, top_k: int) -> List[Tuple[str, float]]:
        """语义搜索（使用预训练模型）"""
        # 这里应该使用预训练的语义模型
        # 简化实现：基于关键词重叠的语义相似度

        query_keywords = set(self._extract_keywords(query))
        results = []

        for entry_id, entry in self.entries.items():
            entry_keywords = set(self._extract_keywords(entry.content))

            # 计算语义相似度
            common_keywords = query_keywords & entry_keywords
            total_keywords = query_keywords | entry_keywords

            if total_keywords:
                semantic_score = len(common_keywords) / len(total_keywords)
                # 考虑访问频率
                access_boost = min(entry.access_count / 100, 0.2)
                final_score = semantic_score + access_boost
            else:
                final_score = 0

            if final_score > 0:
                results.append((entry_id, final_score))

        results.sort(key=lambda x: x[1], reverse=True)
        return results[:top_k]

    async def _tfidf_search(self, query: str, top_k: int) -> List[Tuple[str, float]]:
        """TF-IDF搜索"""
        if not self.tfidf_vectorizer or self.tfidf_matrix is None:
            return []

        try:
            # 计算查询的TF-IDF向量
            query_vector = self.tfidf_vectorizer.transform([query])

            # 计算余弦相似度
            similarities = cosine_similarity(query_vector, self.tfidf_matrix)[0]

            # 获取最相似的条目
            entry_ids = list(self.entries.keys())
            results = [(entry_ids[i], similarities[i]) for i in range(len(similarities))]

            # 过滤和排序
            results = [(eid, score) for eid, score in results if score > 0]
            results.sort(key=lambda x: x[1], reverse=True)

            return results[:top_k]

        except Exception as e:
            logger.error(f"TF-IDF搜索失败: {e}")
            return []

    async def _vector_search(self, query: str, top_k: int) -> List[Tuple[str, float]]:
        """向量搜索"""
        if not self.use_faiss or not self.vector_index:
            return []

        try:
            # 生成查询向量
            query_vector = self._generate_query_vector(query)

            # 使用向量索引搜索
            if query_vector is not None:
                # 使用numpy数组进行向量搜索（简化实现）
                results = []
                entry_list = list(self.entries.items())

                for entry_id, entry in entry_list:
                    if entry.vector is not None:
                        # 计算余弦相似度
                        similarity = self._cosine_similarity(query_vector, entry.vector)
                        if similarity > 0.1:  # 最低相似度阈值
                            results.append((entry_id, similarity))

                # 排序并返回top_k
                results.sort(key=lambda x: x[1], reverse=True)
                return results[:top_k]

        except Exception as e:
            logger.error(f"向量搜索失败: {e}")

        return []

    def _generate_query_vector(self, query: str) -> np.ndarray | None:
        """生成查询向量"""
        try:
            # 基于查询文本生成向量（简化实现）
            import hashlib
            import re

            # 预处理查询文本
            words = re.findall(r'[\\u4e00-\\u9fff]+|[a-zA-Z]+', query.lower())

            # 创建固定大小的向量
            vector = zeros(self.dimension, dtype=np.float32)

            # 使用哈希函数生成确定性的向量
            query_hash = hashlib.md5(query.encode('utf-8'), usedforsecurity=False).hexdigest()

            # 将哈希值映射到向量
            for i, char in enumerate(query_hash):
                if i < self.dimension:
                    vector[i] = int(char, 16) / 15.0  # 归一化到[0,1]

            # 添加一些基于词语的特征
            for i, word in enumerate(words[:self.dimension]):
                word_hash = sum(ord(c) for c in word)
                idx = word_hash % self.dimension
                vector[idx] += 0.1

            # 归一化向量
            norm = np.linalg.norm(vector)
            if norm > 0:
                vector = vector / norm

            return vector

        except Exception as e:
            logger.error(f"生成查询向量失败: {e}")
            return None

    def _cosine_similarity(self, vec1: np.ndarray, vec2: np.ndarray) -> float:
        """计算余弦相似度"""
        try:
            dot_product = np.dot(vec1, vec2)
            norm1 = np.linalg.norm(vec1)
            norm2 = np.linalg.norm(vec2)

            if norm1 == 0 or norm2 == 0:
                return 0.0

            return dot_product / (norm1 * norm2)

        except Exception:
            return 0.0

    async def _hybrid_search(self, query: str, top_k: int) -> List[Tuple[str, float]]:
        """混合搜索（结合多种搜索方法）"""
        # 获取各种搜索结果
        keyword_results = await self._keyword_search(query, top_k * 2)
        semantic_results = await self._semantic_search(query, top_k * 2)

        # 合并结果
        combined_scores = defaultdict(float)

        # 关键词搜索权重：0.4
        for entry_id, score in keyword_results:
            combined_scores[entry_id] += score * 0.4

        # 语义搜索权重：0.6
        for entry_id, score in semantic_results:
            combined_scores[entry_id] += score * 0.6

        # 排序并返回
        results = [(eid, score) for eid, score in combined_scores.items()]
        results.sort(key=lambda x: x[1], reverse=True)

        return results[:top_k]

    def update_access(self, entry_id: str):
        """更新访问记录"""
        with self.index_lock:
            if entry_id in self.entries:
                entry = self.entries[entry_id]
                entry.access_count += 1
                entry.last_accessed = datetime.now()

    def _cleanup_cache(self):
        """清理查询缓存"""
        # 删除最旧的缓存项
        sorted_cache = sorted(
            self.query_cache.items(),
            key=lambda x: x[1][0]  # 按时间排序
        )

        # 保留最近的缓存项
        keep_count = int(self.cache_max_size * 0.8)
        self.query_cache = dict(sorted_cache[-keep_count:])

    def get_stats(self) -> Dict[str, Any]:
        """获取索引统计信息"""
        with self.index_lock:
            stats = self.stats.copy()
            stats['cache_hit_rate'] = (
                stats['cache_hits'] / max(stats['cache_hits'] + stats['cache_misses'], 1)
            )
            stats['index_types_used'] = [self.index_type.value if hasattr(self.index_type, 'value') else str(self.index_type)]
            if self.use_faiss:
                stats['index_types_used'].append('faiss')

            # 计算索引大小
            stats['index_size'] = (
                len(self.inverted_index) +
                (self.tfidf_matrix.nnz if self.tfidf_matrix is not None else 0) +
                len(self.lsh_hashes)
            )

            return stats

    def export_index(self, file_path: str):
        """导出索引数据"""
        export_data = {
            'entries': {},
            'inverted_index': dict(self.inverted_index),
            'lsh_hashes': {str(k): list(v) for k, v in self.lsh_hashes.items()},
            'hierarchical_index': {
                k: [{'id': e.id, 'content': e.content[:100]} for e in v]
                for k, v in self.hierarchical_index.items()
            },
            'stats': self.get_stats(),
            'export_time': datetime.now().isoformat()
        }

        # 导出条目数据（不包含向量以节省空间）
        for entry_id, entry in self.entries.items():
            export_data['entries'][entry_id] = {
                'id': entry.id,
                'content': entry.content,
                'metadata': entry.metadata,
                'timestamp': entry.timestamp.isoformat(),
                'access_count': entry.access_count,
                'last_accessed': entry.last_accessed.isoformat(),
                'has_vector': entry.vector is not None
            }

        with open(file_path, 'wb') as f:
            pickle.dump(export_data, f)

        logger.info(f"📄 索引数据已导出到: {file_path}")

    def optimize_index(self):
        """优化索引"""
        logger.info('🔧 开始优化索引...')

        with self.index_lock:
            # 清理未使用的条目
            unused_entries = []
            for entry_id, entry in self.entries.items():
                if entry.access_count == 0 and (datetime.now() - entry.timestamp).days > 30:
                    unused_entries.append(entry_id)

            for entry_id in unused_entries:
                del self.entries[entry_id]
                logger.info(f"🗑️ 删除未使用的条目: {entry_id}")

            # 重建倒排索引
            if self.index_type in [IndexType.INVERTED, IndexType.COMPOSITE]:
                self.inverted_index.clear()
                for entry in self.entries.values():
                    self._update_inverted_index(entry)

            # 重建TF-IDF索引
            if self.index_type in [IndexType.TF_IDF, IndexType.COMPOSITE]:
                self._update_tfidf_index(IndexEntry('', ''))  # 触发重建

            # 优化层次索引
            if self.index_type == IndexType.HIERARCHICAL:
                for date_key in self.hierarchical_index:
                    self.hierarchical_index[date_key].sort(
                        key=lambda x: x.last_accessed,
                        reverse=True
                    )

        logger.info('✅ 索引优化完成')

# 测试用例
async def main():
    """主函数"""
    logger.info('🧠 优化记忆索引系统测试')
    logger.info(str('='*50))

    # 创建测试数据
    test_entries = [
        IndexEntry(
            id='entry1',
            content='专利权利要求包括技术方案的实施方式',
            vector=random((768)),
            metadata={'type': 'patent', 'category': 'legal'}
        ),
        IndexEntry(
            id='entry2',
            content='本发明涉及人工智能在专利审查中的应用',
            vector=random((768)),
            metadata={'type': 'patent', 'category': 'technical'}
        ),
        IndexEntry(
            id='entry3',
            content='深度学习模型用于自动评估专利新颖性',
            vector=random((768)),
            metadata={'type': 'patent', 'category': 'ai'}
        ),
        IndexEntry(
            id='entry4',
            content='机器学习算法可以识别现有技术文献',
            vector=random((768)),
            metadata={'type': 'patent', 'category': 'algorithm'}
        )
    ]

    # 创建索引系统
    index = OptimizedMemoryIndex(index_type=IndexType.COMPOSITE)

    # 添加条目
    logger.info("\n📝 添加索引条目...")
    for entry in test_entries:
        index.add_entry(entry)
        logger.info(f"  已添加: {entry.id}")

    # 执行搜索测试
    logger.info("\n🔍 执行搜索测试:")

    queries = [
        '专利权利要求',
        '人工智能应用',
        '深度学习模型',
        '机器学习算法'
    ]

    for query in queries:
        logger.info(f"\n查询: {query}")
        results = await index.search(query, top_k=3)

        if results:
            logger.info(f"找到 {len(results)} 个结果:")
            for entry_id, score in results:
                entry = index.entries[entry_id]
                logger.info(f"  - {entry_id}: {score:.3f} | {entry.content[:50]}...")
        else:
            logger.info('  未找到匹配结果')

    # 获取统计信息
    logger.info("\n📊 索引统计:")
    stats = index.get_stats()
    for key, value in stats.items():
        logger.info(f"  {key}: {value}")

    # 优化索引
    logger.info("\n🔧 优化索引...")
    index.optimize_index()

    # 导出索引
    logger.info("\n💾 导出索引数据...")
    index.export_index('optimized_memory_index.pkl')

    logger.info("\n✅ 测试完成！")

if __name__ == '__main__':
    asyncio.run(main())