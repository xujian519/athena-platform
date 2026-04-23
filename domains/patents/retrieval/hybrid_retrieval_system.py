#!/usr/bin/env python3
"""
专利混合检索基线系统
Patent Hybrid Retrieval Baseline System

集成BM25稀疏检索、向量稠密检索和知识图谱增强的专利检索系统
"""

# Numpy兼容性导入
import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Any

import numpy as np

from config.numpy_compatibility import sum, zeros

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class PatentDocument:
    """专利文档数据结构"""
    id: str
    title: str
    abstract: str
    claims: str
    description: str
    ipc_codes: list[str]
    publication_date: str
    applicant: str
    inventors: list[str]
    citations: list[str]

@dataclass
class RetrievalResult:
    """检索结果数据结构"""
    patent_id: str
    score: float
    source: str  # 'bm25', 'vector', 'kg'
    evidence: str  # 匹配的文本片段
    metadata: dict[str, Any]

class HybridRetrievalSystem:
    """混合检索系统主类"""

    def __init__(self):
        """初始化检索系统组件"""
        self.bm25_index = None
        self.vector_index = None
        self.kg_index = None
        self.patent_corpus = {}
        self.embedding_model = None

        # 检索权重配置
        self.bm25_weight = 0.4
        self.vector_weight = 0.5
        self.kg_weight = 0.1

        logger.info('混合检索系统初始化完成')

    def load_patent_data(self, data_path: str) -> int:
        """
        加载专利数据

        Args:
            data_path: 专利数据文件路径

        Returns:
            加载的专利数量
        """
        logger.info(f"开始加载专利数据: {data_path}")

        # 创建示例数据（实际应用时从文件加载）
        sample_patents = self._create_sample_patents()

        for patent in sample_patents:
            self.patent_corpus[patent.id] = patent

        count = len(self.patent_corpus)
        logger.info(f"成功加载 {count} 条专利数据")

        # 初始化索引
        self._initialize_indexes()

        return count

    def _create_sample_patents(self) -> list[PatentDocument]:
        """创建示例专利数据（演示用）"""
        patents = [
            PatentDocument(
                id='CN123456789A',
                title='一种基于深度学习的图像识别方法',
                abstract='本发明公开了一种基于深度学习的图像识别方法，包括数据预处理、特征提取、分类识别等步骤...',
                claims='1. 一种基于深度学习的图像识别方法，其特征在于包括以下步骤：...',
                description='本发明涉及人工智能技术领域，具体涉及一种图像识别方法...',
                ipc_codes=['G06K9/00', 'G06N3/04'],
                publication_date='2023-05-15',
                applicant='某某科技有限公司',
                inventors=['张三', '李四'],
                citations=['CN987654321A', 'US2020012345A1']
            ),
            PatentDocument(
                id='CN987654321A',
                title='智能语音交互系统',
                abstract='一种智能语音交互系统，能够识别自然语言指令，提供智能对话服务...',
                claims='1. 一种智能语音交互系统，包括语音采集模块、语音识别模块...',
                description='本发明属于语音技术领域，提供了一种改进的语音交互方案...',
                ipc_codes=['G10L15/00', 'G06F3/048'],
                publication_date='2023-03-20',
                applicant='智能科技公司',
                inventors=['王五', '赵六'],
                citations=['US2020987654A1']
            ),
            PatentDocument(
                id='CN112233445A',
                title='区块链数据存储方法',
                abstract='一种基于区块链技术的数据存储方法，确保数据的不可篡改性和可追溯性...',
                claims='1. 一种区块链数据存储方法，包括数据加密、共识机制...',
                description='本发明涉及区块链技术，提供了一种安全的数据存储方案...',
                ipc_codes=['H04L9/32', 'G06F16/253'],
                publication_date='2023-07-08',
                applicant='链动科技',
                inventors=['陈七', '周八'],
                citations=['EP123456789B1']
            )
        ]
        return patents

    def _initialize_indexes(self):
        """初始化各类索引"""
        logger.info('开始初始化检索索引...')

        # 初始化BM25索引
        self._init_bm25_index()

        # 初始化向量索引
        self._init_vector_index()

        # 初始化知识图谱索引
        self._init_kg_index()

        logger.info('所有索引初始化完成')

    def _init_bm25_index(self):
        """初始化BM25稀疏检索索引"""
        logger.info('初始化BM25索引...')

        # 构建词汇表和文档-词频矩阵
        self.vocab = set()
        self.doc_freqs = {}

        for patent_id, patent in self.patent_corpus.items():
            # 合并所有文本字段
            full_text = f"{patent.title} {patent.abstract} {patent.claims}"
            words = self._tokenize_chinese(full_text)

            # 统计词频
            word_freq = {}
            for word in words:
                self.vocab.add(word)
                word_freq[word] = word_freq.get(word, 0) + 1

            self.doc_freqs[patent_id] = word_freq

        # 构建逆文档频率
        self.idf = {}
        total_docs = len(self.patent_corpus)
        for word in self.vocab:
            doc_count = sum(1 for freq in self.doc_freqs.values() if word in freq)
            self.idf[word] = np.log((total_docs - doc_count + 0.5) / (doc_count + 0.5))

        logger.info(f"BM25索引构建完成，词汇表大小: {len(self.vocab)}")

    def _init_vector_index(self):
        """初始化向量检索索引"""
        logger.info('初始化向量索引...')

        # 使用简单的TF-IDF作为向量（实际应用中应使用预训练模型）
        self.doc_vectors = {}

        for patent_id, patent in self.patent_corpus.items():
            full_text = f"{patent.title} {patent.abstract} {patent.claims}"
            vector = self._text_to_vector(full_text)
            self.doc_vectors[patent_id] = vector

        logger.info(f"向量索引构建完成，文档向量数: {len(self.doc_vectors)}")

    def _init_kg_index(self):
        """初始化知识图谱索引"""
        logger.info('初始化知识图谱索引...')

        # 构建简单的专利关系图
        self.patent_graph = {}

        for patent_id, patent in self.patent_corpus.items():
            self.patent_graph[patent_id] = {
                'ipc_codes': patent.ipc_codes,
                'citations': patent.citations,
                'cited_by': [],  # 反向引用
                'similar_ipc': []  # 相似IPC的专利
            }

        # 构建引用关系
        for patent_id in self.patent_graph:
            for cited in self.patent_graph[patent_id]['citations']:
                if cited in self.patent_graph:
                    self.patent_graph[cited]['cited_by'].append(patent_id)

        # 构建IPC相似关系
        for patent_id1 in self.patent_graph:
            for patent_id2 in self.patent_graph:
                if patent_id1 != patent_id2:
                    ipc1 = set(self.patent_graph[patent_id1]['ipc_codes'])
                    ipc2 = set(self.patent_graph[patent_id2]['ipc_codes'])
                    if ipc1 & ipc2:  # 有共同IPC
                        self.patent_graph[patent_id1]['similar_ipc'].append(patent_id2)

        logger.info('知识图谱索引构建完成')

    def _tokenize_chinese(self, text: str) -> list[str]:
        """中文分词（简化版）"""
        # 实际应用中应使用jieba或pkuseg等专业分词工具

        # 简单的单字切分
        return [char for char in text if char.strip()]

    def _text_to_vector(self, text: str) -> np.ndarray:
        """文本转向量（简化版TF-IDF）"""
        words = self._tokenize_chinese(text)
        vector = zeros(len(self.vocab))
        vocab_list = list(self.vocab, dtype=np.float64)

        word_count = {}
        for word in words:
            word_count[word] = word_count.get(word, 0) + 1

        for i, word in enumerate(vocab_list):
            if word in word_count:
                tf = word_count[word]
                idf = self.idf.get(word, 0)
                vector[i] = tf * idf

        # 归一化
        norm = np.linalg.norm(vector)
        if norm > 0:
            vector = vector / norm

        return vector

    def search(self, query: str, top_k: int = 20) -> list[RetrievalResult]:
        """
        混合检索主函数

        Args:
            query: 查询文本
            top_k: 返回结果数量

        Returns:
            检索结果列表
        """
        logger.info(f"开始混合检索，查询: {query}")

        # 第一阶段：BM25稀疏检索
        bm25_results = self._bm25_search(query, top_k * 2)

        # 第二阶段：向量稠密检索
        vector_results = self._vector_search(query, top_k * 2)

        # 第三阶段：知识图谱增强
        kg_results = self._kg_search(query, top_k)

        # 融合排序
        final_results = self._merge_and_rerank(
            bm25_results, vector_results, kg_results, top_k
        )

        logger.info(f"检索完成，返回 {len(final_results)} 条结果")

        return final_results

    def _bm25_search(self, query: str, top_k: int) -> list[RetrievalResult]:
        """BM25稀疏检索"""
        results = []
        query_words = self._tokenize_chinese(query)

        k1 = 1.5  # BM25参数
        b = 0.75  # BM25参数

        for patent_id, word_freq in self.doc_freqs.items():
            score = 0

            for word in query_words:
                if word in word_freq and word in self.idf:
                    tf = word_freq[word]
                    idf = self.idf[word]

                    # BM25评分公式
                    doc_len = sum(word_freq.values())
                    avg_doc_len = np.mean([sum(freq.values())
                                         for freq in self.doc_freqs.values()])

                    score += idf * (tf * (k1 + 1)) / (
                        tf + k1 * (1 - b + b * doc_len / avg_doc_len)
                    )

            if score > 0:
                patent = self.patent_corpus[patent_id]
                results.append(RetrievalResult(
                    patent_id=patent_id,
                    score=score,
                    source='bm25',
                    evidence=patent.abstract[:200] + '...',
                    metadata={'title': patent.title, 'ipc_codes': patent.ipc_codes}
                ))

        # 按分数排序
        results.sort(key=lambda x: x.score, reverse=True)
        return results[:top_k]

    def _vector_search(self, query: str, top_k: int) -> list[RetrievalResult]:
        """向量稠密检索"""
        query_vector = self._text_to_vector(query)
        results = []

        for patent_id, doc_vector in self.doc_vectors.items():
            # 计算余弦相似度
            similarity = np.dot(query_vector, doc_vector)

            if similarity > 0:
                patent = self.patent_corpus[patent_id]
                results.append(RetrievalResult(
                    patent_id=patent_id,
                    score=float(similarity),
                    source='vector',
                    evidence=patent.title + ' - ' + patent.abstract[:100] + '...',
                    metadata={'title': patent.title, 'ipc_codes': patent.ipc_codes}
                ))

        results.sort(key=lambda x: x.score, reverse=True)
        return results[:top_k]

    def _kg_search(self, query: str, top_k: int) -> list[RetrievalResult]:
        """知识图谱检索"""
        results = []

        # 提取查询中的IPC代码（简化版）
        query_ipcs = []
        for ipc in ['G06K', 'G10L', 'H04L']:  # 示例IPC
            if ipc in query:
                query_ipcs.append(ipc)

        # 查找相似IPC的专利
        for patent_id, graph_info in self.patent_graph.items():
            score = 0
            evidence_parts = []

            # IPC匹配分数
            for ipc in query_ipcs:
                for patent_ipc in graph_info['ipc_codes']:
                    if ipc in patent_ipc:
                        score += 0.5
                        evidence_parts.append(f"IPC匹配: {patent_ipc}")

            # 引用关系分数
            for citation in graph_info['citations']:
                if any(cip in citation for cip in query_ipcs):
                    score += 0.3
                    evidence_parts.append(f"引用相关专利: {citation}")

            if score > 0:
                patent = self.patent_corpus[patent_id]
                results.append(RetrievalResult(
                    patent_id=patent_id,
                    score=score,
                    source='kg',
                    evidence='; '.join(evidence_parts),
                    metadata={
                        'title': patent.title,
                        'ipc_codes': patent.ipc_codes,
                        'citations': patent.citations
                    }
                ))

        results.sort(key=lambda x: x.score, reverse=True)
        return results[:top_k]

    def _merge_and_rerank(
        self,
        bm25_results: list[RetrievalResult],
        vector_results: list[RetrievalResult],
        kg_results: list[RetrievalResult],
        top_k: int
    ) -> list[RetrievalResult]:
        """融合和重排序检索结果"""
        # 收集所有结果
        all_results = {}

        # 加权合并BM25结果
        for result in bm25_results:
            if result.patent_id not in all_results:
                all_results[result.patent_id] = {
                    'patent': result,
                    'total_score': 0,
                    'sources': []
                }
            all_results[result.patent_id]['total_score'] += result.score * self.bm25_weight
            all_results[result.patent_id]['sources'].append(f"BM25:{result.score:.3f}")

        # 加权合并向量结果
        for result in vector_results:
            if result.patent_id not in all_results:
                all_results[result.patent_id] = {
                    'patent': result,
                    'total_score': 0,
                    'sources': []
                }
            all_results[result.patent_id]['total_score'] += result.score * self.vector_weight
            all_results[result.patent_id]['sources'].append(f"VEC:{result.score:.3f}")

        # 加权合并知识图谱结果
        for result in kg_results:
            if result.patent_id not in all_results:
                all_results[result.patent_id] = {
                    'patent': result,
                    'total_score': 0,
                    'sources': []
                }
            all_results[result.patent_id]['total_score'] += result.score * self.kg_weight
            all_results[result.patent_id]['sources'].append(f"KG:{result.score:.3f}")

        # 排序并生成最终结果
        sorted_results = sorted(
            all_results.items(),
            key=lambda x: x[1]['total_score'],
            reverse=True
        )

        final_results = []
        for _patent_id, data in sorted_results[:top_k]:
            patent = data['patent']
            patent.score = data['total_score']
            patent.metadata['sources'] = data['sources']
            patent.metadata['score_breakdown'] = {
                'bm25': self.bm25_weight,
                'vector': self.vector_weight,
                'kg': self.kg_weight
            }
            final_results.append(patent)

        return final_results

    def get_statistics(self) -> dict[str, Any]:
        """获取系统统计信息"""
        return {
            'total_patents': len(self.patent_corpus),
            'vocab_size': len(self.vocab),
            'index_weights': {
                'bm25': self.bm25_weight,
                'vector': self.vector_weight,
                'kg': self.kg_weight
            },
            'last_updated': datetime.now().isoformat()
        }

# 测试函数
def test_hybrid_retrieval():
    """测试混合检索系统"""
    logger.info(str("\n" + '='*80))
    logger.info('🔍 专利混合检索系统测试')
    logger.info(str('='*80))

    # 初始化系统
    system = HybridRetrievalSystem()

    # 加载数据
    count = system.load_patent_data('')
    logger.info(f"\n📚 加载专利数量: {count}")

    # 测试查询
    test_queries = [
        '深度学习图像识别',
        '智能语音交互系统',
        '区块链数据存储',
        '人工智能专利'
    ]

    for query in test_queries:
        logger.info(f"\n🔎 查询: {query}")
        logger.info(str('-' * 60))

        results = system.search(query, top_k=3)

        for i, result in enumerate(results, 1):
            logger.info(f"\n{i}. 专利ID: {result.patent_id}")
            logger.info(f"   评分: {result.score:.4f}")
            logger.info(f"   来源: {result.metadata.get('sources', [])}")
            logger.info(f"   标题: {result.metadata['title']}")
            logger.info(f"   证据: {result.evidence[:150]}...")

    # 显示系统统计
    logger.info(str("\n" + '='*60))
    logger.info('📊 系统统计信息')
    logger.info(str('='*60))

    stats = system.get_statistics()
    for key, value in stats.items():
        logger.info(f"{key}: {value}")

    logger.info("\n✅ 测试完成！")

if __name__ == '__main__':
    test_hybrid_retrieval()
