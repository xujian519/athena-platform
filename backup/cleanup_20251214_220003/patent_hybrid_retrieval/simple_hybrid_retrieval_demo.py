#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
专利混合检索系统简化演示
Patent Hybrid Retrieval System Simple Demo

独立运行的演示版本，展示混合检索的核心功能
"""

import json
import logging
import math
import re
from collections import defaultdict
from datetime import datetime
from typing import Any, Dict, List

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class SimpleHybridRetrieval:
    """简化的混合检索系统"""

    def __init__(self):
        """初始化检索系统"""
        logger.info('初始化简化混合检索系统...')

        # 示例专利数据
        self.patents = [
            {
                'id': 'CN202310123456.7',
                'title': '基于深度学习的图像识别方法及系统',
                'abstract': '本发明公开了一种基于深度学习的图像识别方法，包括：获取待识别图像；通过卷积神经网络提取图像特征；利用注意力机制增强关键特征；通过全连接层进行分类识别。该方法有效提高了图像识别的准确率和鲁棒性。',
                'claims': '一种基于深度学习的图像识别方法，其特征在于，包括以下步骤：获取待识别图像；通过预训练的卷积神经网络提取所述图像的深度特征；采用自注意力机制对所述深度特征进行加权，获得增强特征；将所述增强特征输入全连接层，得到图像识别结果。',
                'ipc': ['G06K9/00', 'G06N3/04'],
                'keywords': ['深度学习', '图像识别', '卷积神经网络', '注意力机制'],
                'date': '2023-05-15',
                'applicant': '智能科技研究院'
            },
            {
                'id': 'CN202310234567.8',
                'title': '基于区块链的分布式数据存储系统',
                'abstract': '本发明提供了一种基于区块链技术的分布式数据存储系统，通过智能合约管理数据访问权限，确保数据的不可篡改性和可追溯性。系统采用分片存储技术，提高了数据存储和检索的效率。',
                'claims': '一种基于区块链的分布式数据存储系统，包括：多个存储节点，用于存储数据分片；区块链网络，用于记录数据操作的元数据；智能合约模块，用于管理数据访问权限；共识模块，用于确保数据一致性。',
                'ipc': ['H04L9/32', 'G06F16/253'],
                'keywords': ['区块链', '分布式存储', '智能合约', '数据安全'],
                'date': '2023-06-20',
                'applicant': '链动科技公司'
            },
            {
                'id': 'CN202310345678.9',
                'title': '自然语言处理的语义理解方法',
                'abstract': '本发明涉及一种自然语言处理领域的语义理解方法，通过结合BERT预训练模型和领域知识图谱，提高了文本语义理解的准确性。特别适用于专业领域的文本分析和知识抽取。',
                'claims': '一种自然语言处理的语义理解方法，包括：对输入文本进行分词和词性标注；利用BERT模型获取词向量；将词向量输入知识图谱增强的语义理解模型；输出文本的语义表示。',
                'ipc': ['G06F16/35', 'G06N3/08'],
                'keywords': ['自然语言处理', 'BERT', '知识图谱', '语义理解'],
                'date': '2023-04-10',
                'applicant': '语义智能公司'
            },
            {
                'id': 'CN202310456789.0',
                'title': '智能语音交互系统及其实现方法',
                'abstract': '本发明公开了一种智能语音交互系统，能够准确识别用户的语音指令，并生成自然流畅的语音回应。系统采用了声学模型和语言模型的联合优化，显著提升了语音识别的准确率。',
                'claims': '一种智能语音交互系统，包括：语音采集模块，用于采集用户语音；语音识别模块，用于将语音转换为文本；自然语言理解模块，用于理解用户意图；语音合成模块，用于生成语音回应。',
                'ipc': ['G10L15/00', 'G06F3/048'],
                'keywords': ['语音识别', '自然语言理解', '语音合成', '人机交互'],
                'date': '2023-07-08',
                'applicant': '语音科技股份'
            },
            {
                'id': 'CN202310567890.1',
                'title': '基于强化学习的推荐算法优化方法',
                'abstract': '本发明提供了一种基于强化学习的推荐算法优化方法，通过动态调整推荐策略，提高了推荐的准确性和多样性。系统能够根据用户反馈实时优化推荐模型。',
                'claims': '一种基于强化学习的推荐算法优化方法，其特征在于，包括：构建用户-物品交互图；设计强化学习奖励函数；训练深度Q网络模型；根据模型输出推荐结果。',
                'ipc': ['G06F16/9535', 'G06N20/00'],
                'keywords': ['强化学习', '推荐系统', '深度Q网络', '个性化推荐'],
                'date': '2023-08-12',
                'applicant': '推荐引擎科技'
            }
        ]

        # 构建索引
        self._build_indexes()

        # 检索权重
        self.weights = {
            'bm25': 0.4,
            'vector': 0.5,
            'keyword': 0.1
        }

        logger.info(f"系统初始化完成，加载 {len(self.patents)} 条专利")

    def _build_indexes(self):
        """构建检索索引"""
        # 构建词汇表
        self.vocab = set()
        self.doc_freqs = defaultdict(int)
        self.doc_lengths = []

        for patent in self.patents:
            # 合并所有文本
            full_text = f"{patent['title']} {patent['abstract']} {patent['claims']}"
            words = self._tokenize(full_text)
            unique_words = set(words)

            # 统计词频和文档频率
            doc_freq = defaultdict(int)
            for word in words:
                doc_freq[word] += 1
                self.vocab.add(word)

            self.doc_freqs[patent['id']] = dict(doc_freq)
            self.doc_lengths.append(len(words))

            # 更新文档频率
            for word in unique_words:
                self.doc_freqs[word] += 1

        # 计算IDF
        total_docs = len(self.patents)
        self.idf = {}
        for word in self.vocab:
            df = self.doc_freqs[word]
            self.idf[word] = math.log((total_docs - df + 0.5) / (df + 0.5))

        # 计算平均文档长度
        self.avg_doc_length = sum(self.doc_lengths) / len(self.doc_lengths)

        # 构建向量空间（简化版TF-IDF）
        self.doc_vectors = {}
        for patent in self.patents:
            self.doc_vectors[patent['id']] = self._text_to_vector(patent)

        logger.info('索引构建完成')

    def _tokenize(self, text: str) -> List[str]:
        """中文分词（简化版）"""
        # 实际应用应使用jieba等专业分词工具
        text = re.sub(r'[^\w\u4e00-\u9fff]', ' ', text)
        tokens = [t for t in text.split() if len(t) > 1]
        return tokens

    def _text_to_vector(self, patent: dict) -> List[float]:
        """将专利文本转换为向量（TF-IDF）"""
        full_text = f"{patent['title']} {patent['abstract']} {patent['claims']}"
        words = self._tokenize(full_text)

        # 计算词频
        word_count = defaultdict(int)
        for word in words:
            word_count[word] += 1

        # 构建TF-IDF向量
        vector = []
        vocab_list = sorted(self.vocab)
        for word in vocab_list:
            if word in word_count and word in self.idf:
                tf = word_count[word]
                idf = self.idf[word]
                vector.append(tf * idf)
            else:
                vector.append(0)

        # 归一化
        norm = math.sqrt(sum(x*x for x in vector))
        if norm > 0:
            vector = [x/norm for x in vector]

        return vector

    def search(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """执行混合检索"""
        logger.info(f"执行混合检索: {query}")

        # 1. BM25检索
        bm25_results = self._bm25_search(query, top_k * 2)

        # 2. 向量检索
        vector_results = self._vector_search(query, top_k * 2)

        # 3. 关键词检索
        keyword_results = self._keyword_search(query, top_k)

        # 4. 融合结果
        final_results = self._merge_results(
            bm25_results, vector_results, keyword_results, top_k
        )

        return final_results

    def _bm25_search(self, query: str, top_k: int) -> List[Dict[str, Any]]:
        """BM25检索"""
        results = []
        query_words = self._tokenize(query)

        k1 = 1.5
        b = 0.75

        for i, patent in enumerate(self.patents):
            score = 0
            doc_freq = self.doc_freqs[patent['id']]
            doc_length = self.doc_lengths[i]

            for word in query_words:
                if word in doc_freq and word in self.idf:
                    tf = doc_freq[word]
                    idf = self.idf[word]

                    # BM25评分
                    score += idf * (tf * (k1 + 1)) / (
                        tf + k1 * (1 - b + b * doc_length / self.avg_doc_length)
                    )

            if score > 0:
                results.append({
                    'patent': patent,
                    'score': score,
                    'source': 'bm25'
                })

        results.sort(key=lambda x: x['score'], reverse=True)
        return results[:top_k]

    def _vector_search(self, query: str, top_k: int) -> List[Dict[str, Any]]:
        """向量检索（余弦相似度）"""
        query_vector = self._text_to_vector({
            'title': query,
            'abstract': query,
            'claims': query
        })

        results = []
        for patent in self.patents:
            doc_vector = self.doc_vectors[patent['id']]

            # 计算余弦相似度
            similarity = sum(a*b for a, b in zip(query_vector, doc_vector))

            if similarity > 0:
                results.append({
                    'patent': patent,
                    'score': similarity,
                    'source': 'vector'
                })

        results.sort(key=lambda x: x['score'], reverse=True)
        return results[:top_k]

    def _keyword_search(self, query: str, top_k: int) -> List[Dict[str, Any]]:
        """关键词检索"""
        query_words = set(self._tokenize(query))
        results = []

        for patent in self.patents:
            patent_keywords = set(patent['keywords'])
            patent_words = set(self._tokenize(
                f"{patent['title']} {patent['abstract']}"
            ))

            # 计算匹配分数
            keyword_matches = query_words & patent_keywords
            text_matches = query_words & patent_words
            total_matches = keyword_matches.union(text_matches)

            if total_matches:
                # 综合评分：关键词匹配权重更高
                score = (len(keyword_matches) * 0.7 + len(text_matches) * 0.3) / len(query_words)
                results.append({
                    'patent': patent,
                    'score': score,
                    'source': 'keyword',
                    'matched_keywords': list(total_matches)
                })

        results.sort(key=lambda x: x['score'], reverse=True)
        return results[:top_k]

    def _merge_results(
        self,
        bm25_results: List[Dict[str, Any]],
        vector_results: List[Dict[str, Any]],
        keyword_results: List[Dict[str, Any]],
        top_k: int
    ) -> List[Dict[str, Any]]:
        """融合检索结果"""
        # 收集所有专利
        all_patents = {}

        # 合并BM25结果
        for result in bm25_results:
            patent_id = result['patent']['id']
            if patent_id not in all_patents:
                all_patents[patent_id] = {
                    'patent': result['patent'],
                    'scores': {'bm25': 0, 'vector': 0, 'keyword': 0},
                    'sources': []
                }
            all_patents[patent_id]['scores']['bm25'] = result['score']
            all_patents[patent_id]['sources'].append(f"BM25:{result['score']:.3f}")

        # 合并向量结果
        for result in vector_results:
            patent_id = result['patent']['id']
            if patent_id not in all_patents:
                all_patents[patent_id] = {
                    'patent': result['patent'],
                    'scores': {'bm25': 0, 'vector': 0, 'keyword': 0},
                    'sources': []
                }
            all_patents[patent_id]['scores']['vector'] = result['score']
            all_patents[patent_id]['sources'].append(f"VEC:{result['score']:.3f}")

        # 合并关键词结果
        for result in keyword_results:
            patent_id = result['patent']['id']
            if patent_id not in all_patents:
                all_patents[patent_id] = {
                    'patent': result['patent'],
                    'scores': {'bm25': 0, 'vector': 0, 'keyword': 0},
                    'sources': []
                }
            all_patents[patent_id]['scores']['keyword'] = result['score']
            all_patents[patent_id]['sources'].append(f"KW:{result['score']:.3f}")

        # 计算加权总分
        final_results = []
        for patent_id, data in all_patents.items():
            scores = data['scores']
            total_score = (
                scores['bm25'] * self.weights['bm25'] +
                scores['vector'] * self.weights['vector'] +
                scores['keyword'] * self.weights['keyword']
            )

            final_results.append({
                'patent_id': patent_id,
                'title': data['patent']['title'],
                'abstract': data['patent']['abstract'],
                'ipc': data['patent']['ipc'],
                'date': data['patent']['date'],
                'applicant': data['patent']['applicant'],
                'total_score': total_score,
                'score_breakdown': scores,
                'sources': data['sources']
            })

        # 排序并返回Top-K
        final_results.sort(key=lambda x: x['total_score'], reverse=True)
        return final_results[:top_k]

    def demonstrate(self):
        """演示检索功能"""
        logger.info(str("\n" + '='*80))
        logger.info('🔍 专利混合检索系统演示')
        logger.info(str('='*80))

        # 测试查询
        test_queries = [
            '深度学习 图像识别',
            '区块链 数据存储',
            '自然语言处理',
            '智能语音',
            '强化学习 推荐'
        ]

        for query in test_queries:
            logger.info(f"\n{'='*80}")
            logger.info(f"🎯 查询: {query}")
            logger.info(str('='*80))

            # 执行检索
            results = self.search(query, top_k=3)

            if results:
                for i, result in enumerate(results, 1):
                    logger.info(f"\n{i}. 【专利号】{result['patent_id']}")
                    logger.info(f"   【标题】{result['title']}")
                    logger.info(f"   【申请人】{result['applicant']}")
                    logger.info(f"   【IPC分类】{', '.join(result['ipc'])}")
                    logger.info(f"   【综合评分】{result['total_score']:.4f}")
                    logger.info(f"   【评分明细】")
                    logger.info(f"     - BM25: {result['score_breakdown']['bm25']:.3f}")
                    logger.info(f"     - 向量: {result['score_breakdown']['vector']:.3f}")
                    logger.info(f"     - 关键词: {result['score_breakdown']['keyword']:.3f}")
                    logger.info(f"   【数据来源】{', '.join(result['sources'])}")
                    logger.info(f"   【摘要】{result['abstract'][:150]}...")
            else:
                logger.info('未找到相关专利')

        # 性能对比
        logger.info(f"\n{'='*80}")
        logger.info("📈 检索策略对比 (查询: '深度学习')")
        logger.info(str('='*80))

        query = '深度学习'

        # 分别测试各策略
        bm25_only = self._bm25_search(query, 3)
        vector_only = self._vector_search(query, 3)
        keyword_only = self._keyword_search(query, 3)
        hybrid = self.search(query, 3)

        def show_results(name, results):
            logger.info(f"\n{name}:")
            for i, r in enumerate(results, 1):
                if 'patent' in r:
                    logger.info(f"   {i}. {r['patent']['id'][:20]}... - {r['patent']['title'][:30]}... (分数: {r['score']:.3f})")
                else:
                    logger.info(f"   {i}. {r['patent_id']} - {r['title'][:30]}... (分数: {r['total_score']:.3f})")

        show_results('1️⃣ 仅BM25检索', bm25_only)
        show_results('2️⃣ 仅向量检索', vector_only)
        show_results('3️⃣ 仅关键词检索', keyword_only)
        show_results('4️⃣ 混合检索 (推荐)', hybrid)

        logger.info(f"\n{'='*80}")
        logger.info('✅ 演示完成！')
        logger.info(str('='*80))

        # 显示系统信息
        logger.info(f"\n📊 系统统计:")
        logger.info(f"  - 专利数量: {len(self.patents)}")
        logger.info(f"  - 词汇表大小: {len(self.vocab)}")
        logger.info(f"  - 平均文档长度: {self.avg_doc_length:.1f} 词")
        logger.info(f"  - 检索权重: {self.weights}")

# 主函数
def main():
    """运行演示"""
    system = SimpleHybridRetrieval()
    system.demonstrate()

if __name__ == '__main__':
    main()