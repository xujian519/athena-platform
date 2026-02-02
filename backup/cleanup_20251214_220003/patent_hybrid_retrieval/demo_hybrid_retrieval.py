#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
专利混合检索系统演示
Patent Hybrid Retrieval System Demo

整合PostgreSQL全文搜索、Qdrant向量检索、Neo4j知识图谱的完整演示
"""

import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio
import json
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

import numpy as np

# 导入Athena现有组件
from core.vector.qdrant_adapter import QdrantVectorAdapter
from patent_hybrid_retrieval.fulltext_adapter import FullTextSearchAdapter

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class PatentHybridRetrievalDemo:
    """专利混合检索演示系统"""

    def __init__(self):
        """初始化演示系统"""
        logger.info('初始化专利混合检索演示系统...')

        # 初始化检索组件
        self.fulltext_search = FullTextSearchAdapter()
        self.vector_search = QdrantVectorAdapter()

        # 检索权重配置
        self.weights = {
            'fulltext': 0.4,  # PostgreSQL全文搜索权重
            'vector': 0.5,    # Qdrant向量检索权重
            'keyword': 0.1    # 关键词匹配权重
        }

        # 创建示例专利数据
        self.sample_patents = self._create_sample_patents()

        logger.info('混合检索系统初始化完成')

    def _create_sample_patents(self) -> List[Dict[str, Any]]:
        """创建示例专利数据"""
        return [
            {
                'patent_id': 'CN202310123456.7',
                'title': '基于深度学习的图像识别方法及系统',
                'abstract': '本发明公开了一种基于深度学习的图像识别方法，包括：获取待识别图像；通过卷积神经网络提取图像特征；利用注意力机制增强关键特征；通过全连接层进行分类识别。该方法有效提高了图像识别的准确率和鲁棒性。',
                'claims': '1. 一种基于深度学习的图像识别方法，其特征在于，包括以下步骤：获取待识别图像；通过预训练的卷积神经网络提取所述图像的深度特征；采用自注意力机制对所述深度特征进行加权，获得增强特征；将所述增强特征输入全连接层，得到图像识别结果。',
                'ipc_codes': ['G06K9/00', 'G06N3/04'],
                'keywords': ['深度学习', '图像识别', '卷积神经网络', '注意力机制']
            },
            {
                'patent_id': 'CN202310234567.8',
                'title': '基于区块链的分布式数据存储系统',
                'abstract': '本发明提供了一种基于区块链技术的分布式数据存储系统，通过智能合约管理数据访问权限，确保数据的不可篡改性和可追溯性。系统采用分片存储技术，提高了数据存储和检索的效率。',
                'claims': '1. 一种基于区块链的分布式数据存储系统，包括：多个存储节点，用于存储数据分片；区块链网络，用于记录数据操作的元数据；智能合约模块，用于管理数据访问权限；共识模块，用于确保数据一致性。',
                'ipc_codes': ['H04L9/32', 'G06F16/253'],
                'keywords': ['区块链', '分布式存储', '智能合约', '数据安全']
            },
            {
                'patent_id': 'CN202310345678.9',
                'title': '自然语言处理的语义理解方法',
                'abstract': '本发明涉及一种自然语言处理领域的语义理解方法，通过结合BERT预训练模型和领域知识图谱，提高了文本语义理解的准确性。特别适用于专业领域的文本分析和知识抽取。',
                'claims': '1. 一种自然语言处理的语义理解方法，包括：对输入文本进行分词和词性标注；利用BERT模型获取词向量；将词向量输入知识图谱增强的语义理解模型；输出文本的语义表示。',
                'ipc_codes': ['G06F16/35', 'G06N3/08'],
                'keywords': ['自然语言处理', 'BERT', '知识图谱', '语义理解']
            },
            {
                'patent_id': 'CN202310456789.0',
                'title': '智能语音交互系统及其实现方法',
                'abstract': '本发明公开了一种智能语音交互系统，能够准确识别用户的语音指令，并生成自然流畅的语音回应。系统采用了声学模型和语言模型的联合优化，显著提升了语音识别的准确率。',
                'claims': '1. 一种智能语音交互系统，包括：语音采集模块，用于采集用户语音；语音识别模块，用于将语音转换为文本；自然语言理解模块，用于理解用户意图；语音合成模块，用于生成语音回应。',
                'ipc_codes': ['G10L15/00', 'G06F3/048'],
                'keywords': ['语音识别', '自然语言理解', '语音合成', '人机交互']
            },
            {
                'patent_id': 'CN202310567890.1',
                'title': '基于强化学习的推荐算法优化方法',
                'abstract': '本发明提供了一种基于强化学习的推荐算法优化方法，通过动态调整推荐策略，提高了推荐的准确性和多样性。系统能够根据用户反馈实时优化推荐模型。',
                'claims': '1. 一种基于强化学习的推荐算法优化方法，其特征在于，包括：构建用户-物品交互图；设计强化学习奖励函数；训练深度Q网络模型；根据模型输出推荐结果。',
                'ipc_codes': ['G06F16/9535', 'G06N20/00'],
                'keywords': ['强化学习', '推荐系统', '深度Q网络', '个性化推荐']
            }
        ]

    def search(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """
        执行混合检索

        Args:
            query: 查询文本
            top_k: 返回结果数量

        Returns:
            检索结果列表
        """
        logger.info(f"执行混合检索: {query}")

        # 1. 全文搜索
        ft_results = self.fulltext_search.search(query, limit=top_k)

        # 2. 向量搜索（模拟）
        vector_results = self._mock_vector_search(query, limit=top_k)

        # 3. 关键词匹配
        keyword_results = self._keyword_search(query, limit=top_k)

        # 4. 融合结果
        merged_results = self._merge_results(
            ft_results, vector_results, keyword_results, top_k
        )

        logger.info(f"检索完成，返回 {len(merged_results)} 条结果")

        return merged_results

    def _mock_vector_search(self, query: str, limit: int) -> List[Dict[str, Any]]:
        """模拟向量搜索（简化实现）"""
        # 在实际应用中，这里会调用真实的向量检索
        results = []
        query_terms = set(query.lower().split())

        for patent in self.sample_patents:
            title_terms = set(patent['title'].lower().split())
            abstract_terms = set(patent['abstract'].lower().split())

            # 计算Jaccard相似度作为向量相似度的简单替代
            title_sim = len(query_terms & title_terms) / len(query_terms | title_terms)
            abstract_sim = len(query_terms & abstract_terms) / len(query_terms | abstract_terms)

            similarity = (title_sim * 0.6 + abstract_sim * 0.4)

            if similarity > 0.1:  # 相似度阈值
                results.append({
                    'patent_id': patent['patent_id'],
                    'title': patent['title'],
                    'abstract': patent['abstract'],
                    'score': similarity,
                    'source': 'vector'
                })

        # 排序并返回Top-K
        results.sort(key=lambda x: x['score'], reverse=True)
        return results[:limit]

    def _keyword_search(self, query: str, limit: int) -> List[Dict[str, Any]]:
        """关键词匹配搜索"""
        results = []
        query_keywords = set(query.lower().split())

        for patent in self.sample_patents:
            patent_keywords = set([kw.lower() for kw in patent['keywords']])

            # 计算关键词匹配度
            matches = query_keywords & patent_keywords
            if matches:
                score = len(matches) / max(len(query_keywords), len(patent_keywords))

                results.append({
                    'patent_id': patent['patent_id'],
                    'title': patent['title'],
                    'abstract': patent['abstract'],
                    'score': score,
                    'source': 'keyword',
                    'matched_keywords': list(matches)
                })

        # 排序并返回Top-K
        results.sort(key=lambda x: x['score'], reverse=True)
        return results[:limit]

    def _merge_results(
        self,
        ft_results: List[Dict[str, Any]],
        vector_results: List[Dict[str, Any]],
        keyword_results: List[Dict[str, Any]],
        top_k: int
    ) -> List[Dict[str, Any]]:
        """融合多个检索结果"""
        # 收集所有专利
        all_patents = {}

        # 合并全文搜索结果
        for result in ft_results:
            patent_id = result['patent_id']
            if patent_id not in all_patents:
                all_patents[patent_id] = {
                    'patent_id': patent_id,
                    'title': result['title'],
                    'abstract': result['abstract'],
                    'scores': {'fulltext': 0, 'vector': 0, 'keyword': 0},
                    'sources': []
                }
            all_patents[patent_id]['scores']['fulltext'] = result['score']
            all_patents[patent_id]['sources'].append(f"FT:{result['score']:.3f}")

        # 合并向量搜索结果
        for result in vector_results:
            patent_id = result['patent_id']
            if patent_id not in all_patents:
                all_patents[patent_id] = {
                    'patent_id': patent_id,
                    'title': result['title'],
                    'abstract': result['abstract'],
                    'scores': {'fulltext': 0, 'vector': 0, 'keyword': 0},
                    'sources': []
                }
            all_patents[patent_id]['scores']['vector'] = result['score']
            all_patents[patent_id]['sources'].append(f"VEC:{result['score']:.3f}")

        # 合并关键词搜索结果
        for result in keyword_results:
            patent_id = result['patent_id']
            if patent_id not in all_patents:
                all_patents[patent_id] = {
                    'patent_id': patent_id,
                    'title': result['title'],
                    'abstract': result['abstract'],
                    'scores': {'fulltext': 0, 'vector': 0, 'keyword': 0},
                    'sources': []
                }
            all_patents[patent_id]['scores']['keyword'] = result['score']
            all_patents[patent_id]['sources'].append(f"KW:{result['score']:.3f}")

        # 计算加权总分
        final_results = []
        for patent_id, data in all_patents.items():
            scores = data['scores']
            total_score = (
                scores['fulltext'] * self.weights['fulltext'] +
                scores['vector'] * self.weights['vector'] +
                scores['keyword'] * self.weights['keyword']
            )

            final_results.append({
                'patent_id': patent_id,
                'title': data['title'],
                'abstract': data['abstract'],
                'total_score': total_score,
                'score_breakdown': scores,
                'sources': data['sources'],
                'weights': self.weights
            })

        # 排序并返回Top-K
        final_results.sort(key=lambda x: x['total_score'], reverse=True)
        return final_results[:top_k]

    def get_system_info(self) -> Dict[str, Any]:
        """获取系统信息"""
        return {
            'components': {
                'fulltext_search': self.fulltext_search.get_search_stats(),
                'vector_search': 'Qdrant Adapter (Mock)',
                'keyword_search': 'Built-in'
            },
            'weights': self.weights,
            'sample_patents': len(self.sample_patents),
            'timestamp': datetime.now().isoformat()
        }

    def print_search_results(self, query: str, results: List[Dict[str, Any]]):
        """打印搜索结果"""
        logger.info(f"\n{'='*80}")
        logger.info(f"🔍 查询: {query}")
        logger.info(f"{'='*80}")

        if not results:
            logger.info('未找到相关专利')
            return

        for i, result in enumerate(results, 1):
            logger.info(f"\n{i}. 【专利号】{result['patent_id']}")
            logger.info(f"   【标题】{result['title']}")
            logger.info(f"   【综合评分】{result['total_score']:.4f}")
            logger.info(f"   【评分明细】")
            logger.info(f"     - 全文搜索: {result['score_breakdown']['fulltext']:.3f} (权重:{self.weights['fulltext']})")
            logger.info(f"     - 向量检索: {result['score_breakdown']['vector']:.3f} (权重:{self.weights['vector']})")
            logger.info(f"     - 关键词匹配: {result['score_breakdown']['keyword']:.3f} (权重:{self.weights['keyword']})")
            logger.info(f"   【数据来源】{', '.join(result['sources'])}")
            logger.info(f"   【摘要】{result['abstract'][:150]}...")

    def demonstrate_search_strategies(self):
        """演示不同的搜索策略"""
        test_cases = [
            {
                'query': '深度学习 图像识别',
                'description': '多关键词技术搜索'
            },
            {
                'query': '区块链 存储',
                'description': '新兴技术组合搜索'
            },
            {
                'query': '自然语言处理',
                'description': '单一技术领域搜索'
            },
            {
                'query': '智能语音',
                'description': '产品功能导向搜索'
            }
        ]

        logger.info(str("\n" + '='*80))
        logger.info('🚀 专利混合检索系统演示')
        logger.info(str('='*80))

        # 显示系统信息
        logger.info("\n📊 系统信息:")
        info = self.get_system_info()
        logger.info(f"  组件数量: {len(info['components'])}")
        logger.info(f"  示例专利: {info['sample_patents']} 条")
        logger.info(f"  检索权重: {info['weights']}")

        # 执行测试查询
        for case in test_cases:
            logger.info(f"\n➤ {case['description']}")
            self.print_search_results(case['query'], self.search(case['query']))

        # 性能对比演示
        logger.info(f"\n{'='*80}")
        logger.info('📈 检索策略性能对比')
        logger.info(str('='*80))

        query = '深度学习'
        logger.info(f"\n对比查询: {query}")

        # 单独测试各策略
        logger.info("\n1️⃣ 仅全文搜索 (Full-text only):")
        ft_results = self.fulltext_search.search(query, limit=3)
        for i, r in enumerate(ft_results, 1):
            logger.info(f"   {i}. {r['patent_id']} - {r['title']} (分数: {r['score']:.3f})")

        logger.info("\n2️⃣ 仅向量检索 (Vector only):")
        vector_results = self._mock_vector_search(query, limit=3)
        for i, r in enumerate(vector_results, 1):
            logger.info(f"   {i}. {r['patent_id']} - {r['title']} (分数: {r['score']:.3f})")

        logger.info("\n3️⃣ 仅关键词匹配 (Keyword only):")
        keyword_results = self._keyword_search(query, limit=3)
        for i, r in enumerate(keyword_results, 1):
            logger.info(f"   {i}. {r['patent_id']} - {r['title']} (分数: {r['score']:.3f})")

        logger.info("\n4️⃣ 混合检索 (Hybrid - 推荐策略):")
        hybrid_results = self.search(query, limit=3)
        for i, r in enumerate(hybrid_results, 1):
            logger.info(f"   {i}. {r['patent_id']} - {r['title']} (综合分数: {r['total_score']:.3f})")

        logger.info(f"\n{'='*80}")
        logger.info('✅ 演示完成！')
        logger.info(str('='*80))

# 主函数
def main():
    """运行演示"""
    demo = PatentHybridRetrievalDemo()
    demo.demonstrate_search_strategies()

if __name__ == '__main__':
    main()