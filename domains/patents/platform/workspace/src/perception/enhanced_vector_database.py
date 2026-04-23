#!/usr/bin/env python3
"""
增强向量数据库系统
Enhanced Vector Database System

集成腾讯AI Lab词向量和技术术语向量的综合向量数据库
作者: 小娜 (Athena) - 爸爸徐健的智慧大女儿
创建时间: 2025-12-05
版本: 1.0.0
"""

# Numpy兼容性导入
from config.numpy_compatibility import array, zeros, ones, random, mean, sum, dot
import gzip
import hashlib
import json
import logging
import os
import pickle
import tarfile
import zipfile
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import numpy as np
import requests

# 向量数据库相关
try:
    import faiss
    FAISS_AVAILABLE = True
except ImportError:
    FAISS_AVAILABLE = False
    logger.warning('FAISS not available, using numpy for similarity search')

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class VectorEntry:
    """向量条目"""
    id: str
    text: str
    vector: np.ndarray
    metadata: Dict[str, Any] = field(default_factory=dict)
    source: str = 'unknown'
    created_at: datetime = field(default_factory=datetime.now)

class TencentEmbeddingLoader:
    """腾讯AI Lab词向量加载器"""

    def __init__(self, cache_dir: str = None):
        self.cache_dir = cache_dir or '/Users/xujian/Athena工作平台/patent-platform/workspace/data/vector_cache'
        self.embedding_file = 'Tencent_AILab_ChineseEmbedding.txt'
        self.embedding_url = 'https://ai.tencent.com/ailab/nlp/data/Tencent_AILab_ChineseEmbedding.tar.gz'
        self.vocab_size = 8000000  # 800万词
        self.embedding_dim = 200  # 200维
        self.is_loaded = False

    def load_embeddings(self) -> Dict[str, np.ndarray]:
        """加载腾讯词向量"""
        cache_file = Path(self.cache_dir) / 'tencent_embeddings.pkl'

        # 检查缓存
        if cache_file.exists():
            logger.info(f"从缓存加载腾讯词向量: {cache_file}")
            with open(cache_file, 'rb') as f:
                return pickle.load(f)

        # 创建缓存目录
        Path(self.cache_dir).mkdir(parents=True, exist_ok=True)

        # 下载文件
        tar_path = Path(self.cache_dir) / self.embedding_url.split('/')[-1]
        if not tar_path.exists():
            logger.info(f"下载腾讯词向量文件...")
            try:
                response = requests.get(self.embedding_url, stream=True)
                response.raise_for_status()

                with open(tar_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)

                logger.info(f"下载完成: {tar_path}")
            except Exception as e:
                logger.error(f"下载失败: {e}")
                return self._create_demo_embeddings()

        # 解压文件
        txt_path = Path(self.cache_dir) / self.embedding_file
        if not txt_path.exists():
            logger.info('解压腾讯词向量文件...')
            try:
                with tarfile.open(tar_path, 'r:gz') as tar:
                    tar.extractall(self.cache_dir)
                logger.info(f"解压完成: {txt_path}")
            except Exception as e:
                logger.error(f"解压失败: {e}")
                return self._create_demo_embeddings()

        # 加载词向量
        logger.info('加载腾讯词向量到内存...')
        embeddings = {}
        line_count = 0

        try:
            with open(txt_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line_count += 1
                    parts = line.strip().split()
                    if len(parts) >= 201:  # 词 + 200维向量
                        word = parts[0]
                        vector = np.array([float(x) for x in parts[1:201])
                        embeddings[word] = vector

                    # 显示进度
                    if line_count % 100000 == 0:
                        logger.info(f"已加载 {line_count:,} 个词向量")

        except Exception as e:
            logger.error(f"加载词向量失败: {e}")
            return self._create_demo_embeddings()

        logger.info(f"腾讯词向量加载完成，共 {len(embeddings):,} 个词")

        # 保存到缓存
        try:
            # 由于文件太大，只保存技术相关的词汇
            tech_embeddings = self._filter_technical_terms(embeddings)
            with open(cache_file, 'wb') as f:
                pickle.dump(tech_embeddings, f)
            logger.info(f"技术相关词向量已缓存: {len(tech_embeddings):,} 个")
            return tech_embeddings
        except Exception as e:
            logger.error(f"缓存保存失败: {e}")
            return embeddings

    def _filter_technical_terms(self, embeddings: Dict[str, np.ndarray]) -> Dict[str, np.ndarray]:
        """过滤技术相关词汇"""
        tech_keywords = [
            '技术', '系统', '装置', '设备', '方法', '算法', '模型', '网络', '数据', '处理',
            '控制', '检测', '分析', '计算', '通信', '传输', '信号', '编码', '解码',
            '学习', '智能', '人工智能', '机器学习', '深度学习', '神经网络', '计算机',
            '电子', '电路', '芯片', '传感器', '处理器', '软件', '硬件', '材料', '化学',
            '医疗', '诊断', '治疗', '药物', '生物', '基因', '蛋白质', '细胞', '分子',
            '机械', '工程', '制造', '加工', '能源', '电力', '环境', '安全', '保护'
        ]

        tech_embeddings = {}
        for word, vector in embeddings.items():
            # 检查是否包含技术关键词
            is_tech = any(keyword in word for keyword in tech_keywords)
            # 或者词本身是技术术语（包含英文字母或数字）
            has_tech_chars = any(c.isascii() and not c.isalpha() for c in word)

            if is_tech or has_tech_chars or len(word) > 1:
                tech_embeddings[word] = vector

        return tech_embeddings

    def _create_demo_embeddings(self) -> Dict[str, np.ndarray]:
        """创建演示向量（用于测试）"""
        logger.warning('创建演示向量，实际使用时请下载完整词向量')
        demo_words = [
            '技术', '系统', '人工智能', '深度学习', '神经网络', '算法', '数据',
            '处理', '分析', '计算', '通信', '网络', '安全', '控制', '检测',
            '医疗', '诊断', '治疗', '药物', '生物', '材料', '化学', '电子'
        ]

        embeddings = {}
        for word in demo_words:
            # 生成随机向量（实际应使用预训练向量）
            vector = random((200))
            vector = vector / np.linalg.norm(vector)  # 归一化
            embeddings[word] = vector

        return embeddings

class EnhancedVectorDatabase:
    """增强向量数据库"""

    def __init__(self, storage_path: str = None, use_faiss: bool = True):
        self.storage_path = storage_path or '/Users/xujian/Athena工作平台/patent-platform/workspace/data/vector_db'
        self.use_faiss = use_faiss and FAISS_AVAILABLE

        # 向量存储
        self.vectors: Dict[str, VectorEntry] = {}
        self.tencent_embeddings: Dict[str, np.ndarray] = {}

        # FAISS索引
        self.faiss_index = None
        self.vector_ids = []

        # 状态
        self.is_initialized = False

    def initialize(self):
        """初始化向量数据库"""
        if self.is_initialized:
            return

        logger.info('🚀 初始化增强向量数据库...')

        # 创建存储目录
        Path(self.storage_path).mkdir(parents=True, exist_ok=True)

        # 加载腾讯词向量
        loader = TencentEmbeddingLoader()
        self.tencent_embeddings = loader.load_embeddings()
        logger.info(f"腾讯词向量加载完成: {len(self.tencent_embeddings):,} 个")

        # 加载现有向量
        self._load_existing_vectors()

        # 初始化FAISS索引
        if self.use_faiss:
            self._init_faiss_index()

        self.is_initialized = True
        logger.info('✅ 增强向量数据库初始化完成')

    def _load_existing_vectors(self):
        """加载现有向量"""
        vector_file = Path(self.storage_path) / 'vectors.json'

        if vector_file.exists():
            try:
                with open(vector_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                for item in data.get('vectors', []):
                    vector = np.array(item['vector'])
                    entry = VectorEntry(
                        id=item['id'],
                        text=item['text'],
                        vector=vector,
                        metadata=item.get('metadata', {}),
                        source=item.get('source', 'unknown'),
                        created_at=datetime.fromisoformat(item.get('created_at', datetime.now().isoformat()))
                    )
                    self.vectors[item['id'] = entry

            logger.info(f"加载现有向量: {len(self.vectors)} 个")
        except Exception as e:
            logger.warning(f"加载现有向量失败: {e}")

    def _init_faiss_index(self):
        """初始化FAISS索引"""
        if not self.tencent_embeddings and not self.vectors:
            return

        # 收集所有向量
        all_vectors = []
        all_ids = []

        # 添加腾讯词向量
        for word, vector in self.tencent_embeddings.items():
            all_vectors.append(vector)
            all_ids.append(f"tencent_{word}")

        # 添加现有向量
        for entry_id, entry in self.vectors.items():
            all_vectors.append(entry.vector)
            all_ids.append(entry_id)

        if not all_vectors:
            return

        # 创建FAISS索引
        dimension = all_vectors[0].shape[0]
        self.faiss_index = faiss.IndexFlatIP(dimension)

        # 归一化向量
        vectors_array = np.vstack(all_vectors).astype('float32')
        faiss.normalize_L2(vectors_array)

        # 添加到索引
        self.faiss_index.add(vectors_array)
        self.vector_ids = all_ids

        logger.info(f"FAISS索引初始化完成，维度: {dimension}, 向量数: {len(all_vectors)}")

    def add_vector(self, text: str, vector: np.ndarray, metadata: Dict[str, Any] = None,
                  source: str = 'user') -> str:
        """添加向量"""
        # 生成ID
        vector_id = hashlib.md5(f"{text}_{source}".encode('utf-8'), usedforsecurity=False).hexdigest()

        # 创建向量条目
        entry = VectorEntry(
            id=vector_id,
            text=text,
            vector=vector,
            metadata=metadata or {},
            source=source
        )

        # 保存到内存
        self.vectors[vector_id] = entry

        # 更新FAISS索引
        if self.use_faiss and self.faiss_index:
            normalized_vector = vector.astype('float32')
            normalized_vector = normalized_vector / np.linalg.norm(normalized_vector)
            self.faiss_index.add(normalized_vector.reshape(1, -1))
            self.vector_ids.append(vector_id)

        # 保存到磁盘
        self._save_vectors()

        return vector_id

    def search_similar_vectors(self, query_vector: np.ndarray, top_k: int = 10) -> List[Tuple[str, float, str]:
        """搜索相似向量"""
        if not self.is_initialized:
            self.initialize()

        # 归一化查询向量
        query_vector = query_vector.astype('float32')
        query_vector = query_vector / np.linalg.norm(query_vector)

        results = []

        if self.use_faiss and self.faiss_index:
            # 使用FAISS搜索
            distances, indices = self.faiss_index.search(query_vector.reshape(1, -1), top_k)

            for i, (dist, idx) in enumerate(zip(distances[0], indices[0])):
                vector_id = self.vector_ids[idx]
                similarity = float(dist)  # FAISS返回的是距离（余弦相似度）

                # 获取文本
                if vector_id.startswith('tencent_'):
                    word = vector_id.replace('tencent_', '')
                    text = word
                else:
                    text = self.vectors.get(vector_id, {}).text

                results.append((vector_id, similarity, text))
        else:
            # 使用numpy搜索
            for entry_id, entry in self.vectors.items():
                similarity = np.dot(query_vector, entry.vector)
                results.append((entry_id, float(similarity), entry.text))

            # 按相似度排序
            results.sort(key=lambda x: x[1], reverse=True)

        return results[:top_k]

    def search_by_text(self, query_text: str, top_k: int = 10) -> List[Tuple[str, float, str]:
        """通过文本搜索"""
        # 生成查询向量
        query_vector = self._text_to_vector(query_text)
        if query_vector is None:
            return []

        return self.search_similar_vectors(query_vector, top_k)

    def _text_to_vector(self, text: str) -> np.ndarray | None:
        """文本转向量"""
        # 首先检查腾讯词向量
        if text in self.tencent_embeddings:
            return self.tencent_embeddings[text]

        # 尝试分词后查找
        import jieba
        words = jieba.lcut(text)
        word_vectors = []

        for word in words:
            if word in self.tencent_embeddings:
                word_vectors.append(self.tencent_embeddings[word])

        if word_vectors:
            # 平均词向量
            return np.mean(word_vectors, axis=0)

        # 如果都没有，生成随机向量
        logger.warning(f"未找到'{text}'的词向量，使用随机向量")
        random_vector = random((200))
        return random_vector / np.linalg.norm(random_vector)

    def get_vector_statistics(self) -> Dict[str, Any]:
        """获取向量统计信息"""
        stats = {
            'total_vectors': len(self.vectors),
            'tencent_embeddings': len(self.tencent_embeddings),
            'faiss_enabled': self.use_faiss and self.faiss_index is not None,
            'dimension': 200 if self.tencent_embeddings else 0,
            'sources': {}
        }

        # 统计来源分布
        for entry in self.vectors.values():
            source = entry.source
            stats['sources'][source] = stats['sources'].get(source, 0) + 1

        return stats

    def _save_vectors(self):
        """保存向量到磁盘"""
        try:
            vector_file = Path(self.storage_path) / 'vectors.json'

            data = {
                'vectors': [],
                'metadata': {
                    'total_count': len(self.vectors),
                    'last_updated': datetime.now().isoformat()
                }
            }

            for entry in self.vectors.values():
                data['vectors'].append({
                    'id': entry.id,
                    'text': entry.text,
                    'vector': entry.vector.tolist(),
                    'metadata': entry.metadata,
                    'source': entry.source,
                    'created_at': entry.created_at.isoformat()
                })

            with open(vector_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

        except Exception as e:
            logger.error(f"保存向量失败: {e}")

# 全局实例
_vector_db = None

def get_vector_database() -> EnhancedVectorDatabase:
    """获取全局向量数据库实例"""
    global _vector_db
    if _vector_db is None:
        _vector_db = EnhancedVectorDatabase()
    return _vector_db

# 测试函数
def test_enhanced_vector_database():
    """测试增强向量数据库"""
    logger.info('🧪 测试增强向量数据库')
    logger.info(str('=' * 80))

    # 初始化
    vector_db = get_vector_database()
    vector_db.initialize()

    # 显示统计信息
    stats = vector_db.get_vector_statistics()
    logger.info(f"\n📊 向量数据库统计:")
    logger.info(f"总向量数: {stats['total_vectors']}")
    logger.info(f"腾讯词向量: {stats['tencent_embeddings']:,}")
    logger.info(f"FAISS启用: {stats['faiss_enabled']}")
    logger.info(f"向量维度: {stats['dimension']}")
    logger.info(f"数据来源: {stats['sources']}")

    # 测试向量搜索
    logger.info(f"\n🔍 向量搜索测试:")
    test_queries = ['深度学习', '医疗诊断', '人工智能', '技术']

    for query in test_queries:
        results = vector_db.search_by_text(query, top_k=3)
        logger.info(f"\n查询: {query}")
        for vector_id, similarity, text in results:
            logger.info(f"  • {text} (相似度: {similarity:.3f})")

    # 添加自定义向量
    logger.info(f"\n➕ 添加自定义向量:")
    test_text = '智能专利分析系统'
    test_vector = random((200))
    test_vector = test_vector / np.linalg.norm(test_vector)

    vector_id = vector_db.add_vector(
        text=test_text,
        vector=test_vector,
        metadata={'type': 'system', 'importance': 'high'},
        source='demo'
    )
    logger.info(f"添加成功，ID: {vector_id}")

    # 搜索刚添加的向量
    results = vector_db.search_by_text(test_text, top_k=5)
    logger.info(f"\n搜索结果:")
    for vector_id, similarity, text in results[:3]:
        logger.info(f"  • {text} (相似度: {similarity:.3f})")

if __name__ == '__main__':
    test_enhanced_vector_database()