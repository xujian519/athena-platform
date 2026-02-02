#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
法律向量库查询服务
基于BGE模型和FAISS索引的法律文档检索服务

作者: 小娜 AI系统
时间: 2025-12-05
"""

import json
import logging
import os
import pickle
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

# 添加项目路径
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

try:
    import faiss
    import torch
    from sentence_transformers import SentenceTransformer
except ImportError as e:
    logger.info(f"❌ 缺少依赖库: {e}")
    logger.info('请运行: pip install sentence-transformers faiss-cpu torch')
    sys.exit(1)


# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@dataclass
class SearchResult:
    """搜索结果"""
    doc_id: str
    title: str
    content: str
    category: str
    subcategory: str
    doc_type: str
    score: float
    file_path: str
    effective_date: str | None = None
    keywords: Optional[List[str] = None
    metadata: Dict[str, Any] = None


class LegalVectorSearch:
    """法律向量库搜索服务"""

    def __init__(self):
        self.bge_model_path = '/Users/xujian/Athena工作平台/models/pretrained/bge-large-zh-v1.5'
        self.vector_db_path = '/Users/xujian/Athena工作平台/data/legal_vector_db'
        self.vector_dim = 1024

        # 检查向量库是否存在
        if not self._check_vector_db():
            logger.error('❌ 法律向量库不存在，请先运行构建程序')
            raise FileNotFoundError('法律向量库不存在')

        # 加载模型
        logger.info('📦 加载BGE-large-zh-v1.5模型...')
        self.embedding_model = SentenceTransformer(self.bge_model_path)
        logger.info('✅ BGE模型加载成功')

        # 加载向量索引
        self.index = None
        self.doc_store = None
        self.metadata = None
        self._load_vector_db()

    def _check_vector_db(self) -> bool:
        """检查向量库是否存在"""
        required_files = [
            'legal_vectors.index',
            'doc_store.json',
            'metadata.json'
        ]
        return all((Path(self.vector_db_path) / f).exists() for f in required_files)

    def _load_vector_db(self) -> Any:
        """加载向量数据库"""
        logger.info('📂 加载向量数据库...')

        # 加载FAISS索引
        index_path = Path(self.vector_db_path) / 'legal_vectors.index'
        self.index = faiss.read_index(str(index_path))
        logger.info(f"✅ FAISS索引加载成功，包含 {self.index.ntotal} 个向量")

        # 加载文档存储
        doc_store_path = Path(self.vector_db_path) / 'doc_store.json'
        with open(doc_store_path, 'r', encoding='utf-8') as f:
            self.doc_store = json.load(f)
        logger.info(f"✅ 文档存储加载成功，包含 {len(self.doc_store)} 个文档")

        # 加载元数据
        metadata_path = Path(self.vector_db_path) / 'metadata.json'
        with open(metadata_path, 'r', encoding='utf-8') as f:
            self.metadata = json.load(f)
        logger.info('✅ 元数据加载成功')

    def search(self, query: str, top_k: int = 10, category_filter: str | None = None) -> List[SearchResult]:
        """搜索法律文档"""
        logger.info(f"🔍 搜索查询: {query[:50]}...")
        logger.info(f"🎯 返回数量: {top_k}")

        # 向量化查询
        query_embedding = self.embedding_model.encode([query], normalize_embeddings=True)
        query_embedding = query_embedding.astype('float32')

        # 搜索
        scores, indices = self.index.search(query_embedding, min(top_k, self.index.ntotal))

        # 处理结果
        results = []
        for score, idx in zip(scores[0], indices[0]):
            if idx < 0:  # FAISS可能返回无效索引
                continue

            doc_data = self.doc_store.get(str(idx))
            if not doc_data:
                continue

            # 应用分类过滤
            if category_filter and doc_data.get('category') != category_filter:
                continue

            result = SearchResult(
                doc_id=doc_data['doc_id'],
                title=doc_data['title'],
                content=doc_data['content'][:500] + '...' if len(doc_data['content']) > 500 else doc_data['content'],
                category=doc_data['category'],
                subcategory=doc_data['subcategory'],
                doc_type=doc_data['doc_type'],
                score=float(score),
                file_path=doc_data['file_path'],
                effective_date=doc_data.get('effective_date'),
                keywords=doc_data.get('keywords', []),
                metadata=doc_data.get('metadata', {})
            )
            results.append(result)

        logger.info(f"✅ 搜索完成，返回 {len(results)} 个结果")
        return results

    def search_by_category(self, query: str, category: str, top_k: int = 10) -> List[SearchResult]:
        """按分类搜索"""
        return self.search(query, top_k=top_k, category_filter=category)

    def get_categories(self) -> Dict[str, int]:
        """获取所有分类和文档数量"""
        categories = {}
        for doc_id, doc_data in self.doc_store.items():
            category = doc_data.get('category', '其他')
            categories[category] = categories.get(category, 0) + 1
        return categories

    def get_statistics(self) -> Dict[str, Any]:
        """获取向量库统计信息"""
        return {
            'total_docs': self.metadata.get('total_docs', 0),
            'vector_dim': self.metadata.get('vector_dim', 0),
            'model_path': self.metadata.get('model_path', ''),
            'created_time': self.metadata.get('created_time', ''),
            'categories': self.get_categories(),
            'faiss_index_size': self.index.ntotal if self.index else 0
        }


def demo_search() -> Any:
    """演示搜索功能"""
    search = LegalVectorSearch()

    # 显示统计信息
    stats = search.get_statistics()
    logger.info("\n📊 法律向量库统计信息:")
    logger.info(f"   总文档数: {stats['total_docs']}")
    logger.info(f"   向量维度: {stats['vector_dim']}")
    logger.info(f"   创建时间: {stats['created_time']}")
    logger.info("\n📂 分类统计:")
    for category, count in stats['categories'].items():
        logger.info(f"   {category}: {count} 个文档")

    # 测试查询
    test_queries = [
        '什么是知识产权法？',
        '劳动合同法的规定有哪些？',
        '刑法中关于盗窃罪的规定',
        '行政诉讼的程序是什么？',
        '民法典总则的基本原则'
    ]

    logger.info("\n🔍 搜索演示:")
    logger.info(str('=' * 60))

    for i, query in enumerate(test_queries, 1):
        logger.info(f"\n📝 查询 {i}: {query}")
        logger.info(str('-' * 40))

        results = search.search(query, top_k=3)

        if results:
            for j, result in enumerate(results, 1):
                logger.info(f"\n{j}. 【{result.category}】{result.title}")
                logger.info(f"   相似度: {result.score:.4f}")
                logger.info(f"   文件: {Path(result.file_path).name}")
                if result.effective_date:
                    logger.info(f"   生效日期: {result.effective_date}")
                logger.info(f"   内容摘要: {result.content[:100]}...")
                if result.keywords:
                    logger.info(f"   关键词: {', '.join(result.keywords[:5])}")
        else:
            logger.info('   ❌ 未找到相关文档')

    # 按分类搜索演示
    logger.info(f"\n📂 按分类搜索演示:")
    logger.info(str('=' * 60))

    category_query = '合同'
    category = '民法商法'
    logger.info(f"\n📝 在'{category}'分类中搜索: {category_query}")
    logger.info(str('-' * 40))

    category_results = search.search_by_category(category_query, category, top_k=3)

    if category_results:
        for j, result in enumerate(category_results, 1):
            logger.info(f"\n{j}. {result.title}")
            logger.info(f"   相似度: {result.score:.4f}")
            logger.info(f"   内容摘要: {result.content[:80]}...")
    else:
        logger.info('   ❌ 该分类中未找到相关文档')


if __name__ == '__main__':
    demo_search()