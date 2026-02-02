#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
向量验证引擎
Vector Verification Engine

对关键词检索结果进行向量化验证，提升检索精度
作者: 小诺
创建时间: 2025-12-10
"""

import asyncio
import logging
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Optional, Tuple

import numpy as np
import ollama

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class VerificationResult:
    """验证结果"""
    original_results: List[Dict]
    verified_results: List[Dict]
    verification_time: float
    improvement_metrics: Dict[str, float]

class VectorVerificationEngine:
    """向量验证引擎"""

    def __init__(self):
        # 使用本地Ollama模型
        self.model_name = 'qwen3-embedding:4b'
        self.embedding_dim = 768

        # 验证参数
        self.similarity_threshold = 0.3  # 相似度阈值
        self.max_results = 20  # 最终输出数量
        self.diversity_factor = 0.2  # 多样性因子

    def get_embedding(self, text: str) -> np.ndarray | None:
        """获取文本向量"""
        try:
            # 使用Ollama本地嵌入模型
            response = ollama.embeddings(
                model=self.model_name,
                prompt=text
            )
            return np.array(response['embedding'])
        except Exception as e:
            logger.error(f"❌ 获取向量失败: {e}")
            return None

    def calculate_similarity(self, text1: str, text2: str) -> float:
        """计算两个文本的余弦相似度"""
        emb1 = self.get_embedding(text1)
        emb2 = self.get_embedding(text2)

        if emb1 is None or emb2 is None:
            return 0.0

        # 余弦相似度
        dot_product = np.dot(emb1, emb2)
        norm1 = np.linalg.norm(emb1)
        norm2 = np.linalg.norm(emb2)

        if norm1 == 0 or norm2 == 0:
            return 0.0

        return dot_product / (norm1 * norm2)

    def verify_relevance(self, query: str, patent: Dict) -> Tuple[float, float]:
        """验证专利与查询的相关性"""
        # 构建专利文本（标题+摘要）
        patent_text = f"{patent.get('patent_name', '')} {patent.get('abstract', '')}"

        # 计算与查询的相似度
        relevance_score = self.calculate_similarity(query, patent_text)

        # 计算与原始相关性分数的一致性
        original_score = patent.get('relevance_score', 0)
        consistency = abs(relevance_score - original_score) if original_score else relevance_score

        return relevance_score, consistency

    def diversify_results(self, results: List[Dict], query: str) -> List[Dict]:
        """确保结果多样性"""
        if len(results) <= 5:
            return results

        diversified = []
        selected_patents = set()

        # 首先选择最相关的
        top_relevant = sorted(results, key=lambda x: x.get('vector_relevance', 0), reverse=True)

        for patent in top_relevant:
            if len(diversified) >= self.max_results:
                break

            # 检查多样性（避免重复申请人）
            applicant = patent.get('applicant', '')
            if applicant not in selected_patents:
                diversified.append(patent)
                selected_patents.add(applicant)

        return diversified

    def verify_batch(self, query: str, patents: List[Dict]) -> List[Dict]:
        """批量验证专利相关性"""
        if not patents:
            return []

        logger.info(f"🔍 开始向量验证，共{len(patents)}条专利")

        # 并行计算相关性
        with ThreadPoolExecutor(max_workers=4) as executor:
            futures = []
            for patent in patents:
                future = executor.submit(self.verify_relevance, query, patent)
                futures.append((future, patent))

            # 收集结果
            for future, patent in futures:
                try:
                    relevance_score, consistency = future.result(timeout=30)
                    patent['vector_relevance'] = relevance_score
                    patent['consistency_score'] = consistency

                    # 综合评分：向量相关性 + 一致性
                    patent['combined_score'] = (
                        0.7 * relevance_score +
                        0.3 * (1 - consistency)
                    )

                except Exception as e:
                    logger.warning(f"⚠️ 专利验证失败 {patent.get('patent_name', '')[:30]}: {e}")
                    patent['vector_relevance'] = 0.0
                    patent['consistency_score'] = 0.0
                    patent['combined_score'] = patent.get('relevance_score', 0)

        # 过滤低相关性结果
        filtered_results = [
            p for p in patents
            if p.get('vector_relevance', 0) >= self.similarity_threshold
        ]

        # 按综合评分排序
        sorted_results = sorted(filtered_results, key=lambda x: x.get('combined_score', 0), reverse=True)

        # 确保多样性
        final_results = self.diversify_results(sorted_results, query)

        logger.info(f"✅ 向量验证完成，最终输出{len(final_results)}条专利")

        return final_results

    def analyze_improvement(self, original: List[Dict], verified: List[Dict]) -> Dict[str, float]:
        """分析检索改进效果"""
        if not original or not verified:
            return {}

        # 计算平均相关性分数
        orig_avg = np.mean([p.get('relevance_score', 0) for p in original])
        verified_avg = np.mean([p.get('combined_score', 0) for p in verified])

        # 计算向量相关性
        vector_avg = np.mean([p.get('vector_relevance', 0) for p in verified])

        # 计算多样性（不同申请人数量）
        orig_diversity = len(set(p.get('applicant', '') for p in original[:20]))
        verified_diversity = len(set(p.get('applicant', '') for p in verified))

        return {
            'original_avg_score': float(orig_avg),
            'verified_avg_score': float(verified_avg),
            'vector_avg_score': float(vector_avg),
            'score_improvement': float(verified_avg - orig_avg),
            'diversity_improvement': float(verified_diversity - orig_diversity),
            'original_diversity': float(orig_diversity),
            'verified_diversity': float(verified_diversity)
        }

# 测试用例
def test_vector_verification():
    """测试向量验证"""
    verification_engine = VectorVerificationEngine()

    # 模拟关键词检索结果
    mock_results = [
        {
            'id': 1,
            'patent_name': '基于人工智能的语义识别方法',
            'abstract': '本发明涉及一种基于人工智能的语义识别方法...',
            'applicant': '平安科技(深圳)有限公司',
            'relevance_score': 0.85
        },
        {
            'id': 2,
            'patent_name': '机器学习模型优化方法',
            'abstract': '本发明提供一种机器学习模型优化方法...',
            'applicant': '腾讯科技(深圳)有限公司',
            'relevance_score': 0.75
        },
        {
            'id': 3,
            'patent_name': '通信网络优化系统',
            'abstract': '本发明涉及通信网络优化系统...',
            'applicant': '华为技术有限公司',
            'relevance_score': 0.65
        }
    ]

    try:
        # 测试验证
        query = '人工智能 机器学习'
        verified_results = verification_engine.verify_batch(query, mock_results)

        logger.info(f"✅ 向量验证测试完成")
        logger.info(f"原始结果: {len(mock_results)}条")
        logger.info(f"验证结果: {len(verified_results)}条")

        for i, result in enumerate(verified_results):
            logger.info(f"  {i+1}. {result['patent_name'][:50]}...")
            logger.info(f"     向量相关性: {result.get('vector_relevance', 0):.3f}")
            logger.info(f"     综合评分: {result.get('combined_score', 0):.3f}")

        # 分析改进效果
        improvements = verification_engine.analyze_improvement(mock_results, verified_results)
        logger.info(f"\n📊 改进效果分析:")
        for metric, value in improvements.items():
            logger.info(f"  {metric}: {value:.3f}")

    except Exception as e:
        logger.info(f"❌ 测试失败: {e}")

if __name__ == '__main__':
    test_vector_verification()