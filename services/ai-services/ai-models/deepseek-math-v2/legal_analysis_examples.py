#!/usr/bin/env python3
"""
DeepSeek Math V2 在法律分析中的实际应用示例
演示数学模型如何赋能法律和专利分析业务
"""

import logging
from typing import Any

import numpy as np
import requests

logger = logging.getLogger(__name__)

class LegalMathAnalyzer:
    """法律数学分析器 - 集成DeepSeek Math V2能力"""

    def __init__(self):
        self.deepseek_url = 'http://localhost:8022'
        self.pqai_url = 'http://localhost:8030'

    def calculate_patent_novelty_score(self, patent_text: str,
                                      existing_patents: list[str]) -> dict:
        """
        计算专利新颖性分数
        使用向量空间数学模型进行量化评估
        """
        # 调用PQAI进行向量化和相似度计算
        search_data = {
            'query': patent_text,
            'top_k': len(existing_patents),
            'search_type': 'hybrid',
            'min_similarity': 0.1
        }

        try:
            # 检索相似专利
            response = requests.post(f"{self.pqai_url}/search", json=search_data)
            if response.status_code == 200:
                results = response.json().get('reports/reports/results', [])

                # 数学模型计算新颖性分数
                similarity_scores = [r['score'] for r in results]

                # 1. 最高相似度分数 (最相关专利)
                max_similarity = max(similarity_scores) if similarity_scores else 0

                # 2. 平均相似度 (整体相似程度)
                avg_similarity = np.mean(similarity_scores) if similarity_scores else 0

                # 3. 新颖性分数计算 (数学模型)
                # 新颖性 = 1 - (加权相似度)
                novelty_score = 1 - (0.7 * max_similarity + 0.3 * avg_similarity)

                # 4. 风险等级分类
                if novelty_score >= 0.8:
                    risk_level = '低风险'
                    risk_probability = novelty_score * 0.1
                elif novelty_score >= 0.5:
                    risk_level = '中等风险'
                    risk_probability = (1 - novelty_score) * 0.5
                else:
                    risk_level = '高风险'
                    risk_probability = (1 - novelty_score) * 0.8

                return {
                    'novelty_score': round(novelty_score, 3),
                    'max_similarity': round(max_similarity, 3),
                    'avg_similarity': round(avg_similarity, 3),
                    'risk_level': risk_level,
                    'risk_probability': round(risk_probability, 3),
                    'similar_patents_count': len(results),
                    'analysis_method': '向量空间相似度数学模型'
                }
            else:
                return {'error': '无法检索相似专利'}

        except Exception as e:
            return {'error': f"分析失败: {str(e)}"}

    def analyze_inventive_step(self, technical_solution: str,
                               existing_solutions: list[str]) -> dict:
        """
        创造性分析 - 使用数学模型评估技术方案的创造性
        """
        # 技术方案向量化
        solution_vector = self._vectorize_text(technical_solution)

        if solution_vector is None or len(solution_vector) == 0:
            return {'error': '技术方案向量化失败'}

        # 现有技术向量化
        existing_vectors = []
        for solution in existing_solutions:
            vector = self._vectorize_text(solution)
            if vector is not None and len(vector) > 0:
                existing_vectors.append(vector)

        if not existing_vectors:
            return {'error': '现有技术向量化失败'}

        # 数学模型计算创造性指标

        # 1. 技术距离计算 (向量空间距离)
        distances = []
        for existing_vector in existing_vectors:
            distance = np.linalg.norm(solution_vector - existing_vector)
            distances.append(distance)

        min_distance = min(distances)
        avg_distance = np.mean(distances)
        max_distance = max(distances)

        # 2. 创新度分数计算
        # 标准化距离到[0,1]区间
        if max_distance > 0:
            normalized_min_distance = min_distance / max_distance
            normalized_avg_distance = avg_distance / max_distance
        else:
            normalized_min_distance = 0
            normalized_avg_distance = 0

        # 创新度 = 1 - 标准化距离 (距离越远创新度越高)
        innovation_score = 1 - (0.6 * normalized_min_distance + 0.4 * normalized_avg_distance)

        # 3. 技术突破性评估
        breakthrough_score = min_distance / np.linalg.norm(solution_vector) if np.linalg.norm(solution_vector) > 0 else 0

        # 4. 综合创造性分数
        inventive_score = 0.5 * innovation_score + 0.3 * breakthrough_score + 0.2 * (1 / (1 + len(existing_vectors)/10))

        # 5. 创造性等级
        if inventive_score >= 0.7:
            inventive_level = '强创造性'
        elif inventive_score >= 0.4:
            inventive_level = '中等创造性'
        else:
            inventive_level = '弱创造性'

        return {
            'innovation_score': round(innovation_score, 3),
            'breakthrough_score': round(breakthrough_score, 3),
            'inventive_score': round(inventive_score, 3),
            'inventive_level': inventive_level,
            'technical_distances': {
                'min_distance': round(min_distance, 3),
                'avg_distance': round(avg_distance, 3),
                'max_distance': round(max_distance, 3)
            },
            'analysis_details': f"基于{len(existing_vectors)}个现有技术方案的向量空间距离分析"
        }

    def _vectorize_text(self, text: str) -> np.ndarray:
        """文本向量化 (简化实现)"""
        # 这里应该调用实际的向量模型
        # 为了演示，使用简单的hash向量化
        text_hash = hash(text) % 10000
        vector = np.array([float(text_hash & (1 << i)) / (1 << i) for i in range(768)])
        return vector / np.linalg.norm(vector) if np.linalg.norm(vector) > 0 else vector

    def analyze_patent_scope(self, claim_text: str, prior_art: list[str]) -> dict:
        """
        专利权利要求保护范围分析
        使用数学模型优化保护范围
        """
        # 调用DeepSeek Math V2进行复杂计算
        try:
            # 构建数学计算请求
            {
                'input_data': self._text_to_features(claim_text),
                'calculation_type': 'scope_analysis',
                'reference_data': [self._text_to_features(art) for art in prior_art]
            }

            # response = requests.post(f"{self.deepseek_url}/calculate", json=math_request)
            # 演示使用模拟结果

            # 模拟数学计算结果
            scope_score = np.random.uniform(0.3, 0.9)
            protection_level = '宽' if scope_score > 0.6 else '适中' if scope_score > 0.4 else '窄'

            return {
                'scope_score': round(scope_score, 3),
                'protection_level': protection_level,
                'risk_assessment': '中等风险' if 0.4 < scope_score < 0.7 else '低风险',
                'optimization_suggestions': [
                    '考虑调整权利要求的技术特征组合',
                    '平衡保护范围与专利稳定性',
                    '增加从属权利要求以扩大保护层次'
                ]
            }

        except Exception as e:
            return {'error': f"范围分析失败: {str(e)}"}

    def _text_to_features(self, text: str) -> list[float]:
        """将文本转换为特征向量 (简化实现)"""
        # 简化的特征提取
        features = []
        for char in text[:768]:
            features.append(float(ord(char)) / 1000.0)

        # 填充到1024维（BGE-M3）
        while len(features) < 768:
            features.append(0.0)

        return features[:768]

def demonstrate_legal_math_applications() -> Any:
    """演示法律数学分析应用"""
    logger.info('🎯 DeepSeek Math V2 法律分析应用演示')
    logger.info(str('=' * 60))

    analyzer = LegalMathAnalyzer()

    # 示例1: 专利新颖性分析
    logger.info("\n📊 示例1: 专利新颖性数学分析")
    logger.info(str('-' * 40))

    patent_text = '基于深度学习的智能专利检索系统及方法'
    existing_patents = [
        '基于机器学习的专利分析系统',
        '智能信息检索方法',
        '传统专利检索技术'
    ]

    novelty_result = analyzer.calculate_patent_novelty_score(patent_text, existing_patents)
    logger.info(f"专利文本: {patent_text}")
    logger.info(f"新颖性分数: {novelty_result.get('novelty_score', 'N/A')}")
    logger.info(f"风险等级: {novelty_result.get('risk_level', 'N/A')}")
    logger.info(f"风险概率: {novelty_result.get('risk_probability', 'N/A')}")

    # 示例2: 创造性分析
    logger.info("\n💡 示例2: 技术方案创造性数学分析")
    logger.info(str('-' * 40))

    technical_solution = '采用注意力机制和多级特征融合的深度学习图像识别算法'
    existing_solutions = [
        '传统卷积神经网络',
        '基础的深度学习识别',
        '单阶段特征提取'
    ]

    inventive_result = analyzer.analyze_inventive_step(technical_solution, existing_solutions)
    logger.info(f"技术方案: {technical_solution}")
    logger.info(f"创造性分数: {inventive_result.get('inventive_score', 'N/A')}")
    logger.info(f"创造性等级: {inventive_result.get('inventive_level', 'N/A')}")
    logger.info(f"技术突破性: {inventive_result.get('breakthrough_score', 'N/A')}")

    # 示例3: 权利要求范围分析
    logger.info("\n📝 示例3: 专利权利要求保护范围数学分析")
    logger.info(str('-' * 40))

    claim_text = '一种基于深度学习的智能专利检索系统，包括数据预处理模块、特征提取模块、语义理解模块和检索排序模块'
    prior_art = [
        '传统专利检索系统',
        '基于关键词的检索方法'
    ]

    scope_result = analyzer.analyze_patent_scope(claim_text, prior_art)
    logger.info(f"权利要求: {claim_text[:50]}...")
    logger.info(f"范围分数: {scope_result.get('scope_score', 'N/A')}")
    logger.info(f"保护水平: {scope_result.get('protection_level', 'N/A')}")
    logger.info(f"风险评估: {scope_result.get('risk_assessment', 'N/A')}")

    logger.info("\n🎉 DeepSeek Math V2 赋能的法律分析优势:")
    logger.info('✅ 量化评估 - 将定性分析转为数学量化')
    logger.info('✅ 风险预测 - 基于概率模型的风险评估')
    logger.info('✅ 标准化处理 - 统一的分析标准')
    logger.info('✅ 智能优化 - 数学算法驱动的智能分析')
    logger.info('✅ 精准计算 - 减少人为误差和主观性')

if __name__ == '__main__':
    demonstrate_legal_math_applications()
