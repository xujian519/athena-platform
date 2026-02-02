#!/usr/bin/env python3
"""
专利新颖性分析模块
基于DeepSeek Matchv2策略的新颖性检索和分析系统
"""

import asyncio
import json
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class TechnicalFeature:
    """技术特征数据结构"""
    feature_id: str
    description: str
    category: str  # structural, functional, etc.
    importance: float  # 0-1
    keywords: List[str]

@dataclass
class PriorArt:
    """对比文件数据结构"""
    doc_id: str
    title: str
    abstract: str
    similarity_score: float
    matching_features: List[str]
    source: str  # patent, paper, standard
    publication_date: str

@dataclass
class NoveltyResult:
    """新颖性分析结果"""
    overall_novelty: bool
    novelty_score: float  # 0-1
    closest_prior_art: PriorArt
    distinguishing_features: List[TechnicalFeature]
    evidence_chain: List[Dict]
    recommendation: str

class NoveltyAnalyzer:
    """新颖性分析器"""

    def __init__(self):
        self.workspace = Path('patent-platform/workspace')
        self.data_dir = self.workspace / 'data'
        self.models_dir = self.data_dir / 'models'

    def extract_technical_features(self, disclosure_text: str) -> List[TechnicalFeature]:
        """
        从技术交底书中提取技术特征

        Args:
            disclosure_text: 技术交底书文本

        Returns:
            技术特征列表
        """
        features = []

        # 基于规则的特征提取
        feature_patterns = {
            'structural': [
                '包括.*模块', '由.*组成', '具有.*结构',
                '传感器模块', '控制器', '执行器'
            ],
            'functional': [
                '实现.*功能', '用于.*目的', '能够.*操作',
                '控制方法', '算法', '策略'
            ],
            'performance': [
                '精度.*%', '速度.*ms', '效率提升.*%',
                '响应时间', '功耗', '负载能力'
            ]
        }

        feature_id = 1
        for category, patterns in feature_patterns.items():
            for pattern in patterns:
                # 简化的匹配逻辑，实际应用中应使用更复杂的NLP
                if pattern in disclosure_text:
                    feature = TechnicalFeature(
                        feature_id=f"F{feature_id:03d}",
                        description=f"基于模式'{pattern}'提取的特征",
                        category=category,
                        importance=0.8 if category == 'structural' else 0.6,
                        keywords=[pattern]
                    )
                    features.append(feature)
                    feature_id += 1

        logger.info(f"提取到 {len(features)} 个技术特征")
        return features

    async def hybrid_search(self, features: List[TechnicalFeature]) -> List[PriorArt]:
        """
        混合检索：Dense + Sparse
        实现DeepSeek Matchv2的L1粗筛阶段

        Args:
            features: 技术特征列表

        Returns:
            对比文件列表
        """
        prior_arts = []

        # 模拟Dense检索结果
        dense_results = [
            PriorArt(
                doc_id='CN123456789A',
                title='基于人工智能的机器人控制方法',
                abstract='一种采用深度学习算法的机器人控制系统...',
                similarity_score=0.75,
                matching_features=['F001', 'F002'],
                source='patent',
                publication_date='2023-05-15'
            ),
            PriorArt(
                doc_id='US9876543B2',
                title='Multi-sensor fusion for robotic control',
                abstract='A robotic control system with sensor fusion...',
                similarity_score=0.68,
                matching_features=['F001', 'F003'],
                source='patent',
                publication_date='2022-11-20'
            )
        ]

        # 模拟Sparse检索结果
        sparse_results = [
            PriorArt(
                doc_id='CN109876543A',
                title='多机器人协作系统及方法',
                abstract='实现多机器人的智能协作与任务分配...',
                similarity_score=0.62,
                matching_features=['F004', 'F005'],
                source='patent',
                publication_date='2023-08-10'
            )
        ]

        # 合并和去重
        all_results = dense_results + sparse_results
        seen_ids = set()
        for result in all_results:
            if result.doc_id not in seen_ids:
                prior_arts.append(result)
                seen_ids.add(result.doc_id)

        # 按相似度排序
        prior_arts.sort(key=lambda x: x.similarity_score, reverse=True)

        logger.info(f"检索到 {len(prior_arts)} 篇对比文件")
        return prior_arts

    async def rerank(self, prior_arts: List[PriorArt], features: List[TechnicalFeature]) -> List[PriorArt]:
        """
        重排序：Cross-Encoder精排
        实现DeepSeek Matchv2的L2精排阶段

        Args:
            prior_arts: 原始对比文件列表
            features: 技术特征列表

        Returns:
            重排序后的对比文件列表
        """
        # 模拟重排序逻辑
        for prior_art in prior_arts:
            # 基于匹配特征数量和重要性重新计算分数
            feature_importance_sum = sum(
                next((f.importance for f in features if f.feature_id in prior_art.matching_features), 0)
                for feature_id in prior_art.matching_features
            )

            # 重排序分数 = 原始相似度 * 特征重要性权重
            prior_art.similarity_score = prior_art.similarity_score * (1 + feature_importance_sum)

        # 重新排序
        prior_arts.sort(key=lambda x: x.similarity_score, reverse=True)

        return prior_arts

    def legal_alignment(self, prior_arts: List[PriorArt], features: List[TechnicalFeature]) -> NoveltyResult:
        """
        法律逻辑对齐：新颖性判断
        实现DeepSeek Matchv2的L3法律对齐阶段

        Args:
            prior_arts: 对比文件列表
            features: 技术特征列表

        Returns:
            新颖性分析结果
        """
        if not prior_arts:
            return NoveltyResult(
                overall_novelty=True,
                novelty_score=1.0,
                closest_prior_art=None,
                distinguishing_features=features,
                evidence_chain=[],
                recommendation='建议提交专利申请，具备完全新颖性'
            )

        # 选择最接近的现有技术
        closest_prior_art = prior_arts[0]

        # 确定区别特征
        distinguishing_features = [
            f for f in features
            if f.feature_id not in closest_prior_art.matching_features
        ]

        # 计算新颖性分数
        total_features = len(features)
        distinguished_features = len(distinguishing_features)
        novelty_score = distinguished_features / total_features

        # 新颖性判断阈值
        novelty_threshold = 0.3  # 30%以上的特征区别认为具备新颖性
        overall_novelty = novelty_score >= novelty_threshold

        # 生成证据链
        evidence_chain = [
            {
                'step': '最接近现有技术识别',
                'content': f"选择对比文件：{closest_prior_art.title} ({closest_prior_art.doc_id})",
                'similarity': closest_prior_art.similarity_score
            },
            {
                'step': '技术特征对比',
                'content': f"共{total_features}个技术特征，其中{distinguished_features}个具有新颖性",
                'novelty_ratio': novelty_score
            },
            {
                'step': '法律判断',
                'content': f"新颖性分数{novelty_score:.2f}，阈值{novelty_threshold}",
                'conclusion': '具备新颖性' if overall_novelty else '不具备新颖性'
            }
        ]

        # 生成建议
        if overall_novelty:
            recommendation = f"建议提交专利申请，新颖性分数{novelty_score:.2f}，具备{distinguished_features}个区别技术特征"
        else:
            recommendation = f"建议修改权利要求，当前新颖性分数{novelty_score:.2f}，不足{distinguished_features}个区别特征"

        return NoveltyResult(
            overall_novelty=overall_novelty,
            novelty_score=novelty_score,
            closest_prior_art=closest_prior_art,
            distinguishing_features=distinguishing_features,
            evidence_chain=evidence_chain,
            recommendation=recommendation
        )

    async def analyze_novelty(self, task_id: str, disclosure_text: str, pre_extracted_features: Optional[List[TechnicalFeature] = None) -> NoveltyResult:
        """
        执行完整的新颖性分析流程

        Args:
            task_id: 任务ID
            disclosure_text: 技术交底书文本
            pre_extracted_features: 预先提取的技术特征（可选）

        Returns:
            新颖性分析结果
        """
        logger.info(f"开始执行任务 {task_id} 的新颖性分析")

        # Step 1: 提取技术特征
        if pre_extracted_features:
            features = pre_extracted_features
            logger.info(f"使用预先提取的 {len(features)} 个技术特征")
        else:
            features = self.extract_technical_features(disclosure_text)

        # Step 2: 混合检索
        prior_arts = await self.hybrid_search(features)

        # Step 3: 重排序
        reranked_prior_arts = await self.rerank(prior_arts, features)

        # Step 4: 法律逻辑对齐
        result = self.legal_alignment(reranked_prior_arts, features)

        logger.info(f"新颖性分析完成，结果：{'具备新颖性' if result.overall_novelty else '不具备新颖性'}")

        return result

    def save_result(self, task_id: str, result: NoveltyResult):
        """
        保存分析结果

        Args:
            task_id: 任务ID
            result: 新颖性分析结果
        """
        task_dir = Path('../tasks') / task_id  # 修正相对路径
        novelty_dir = task_dir / 'novelty'

        # 确保目录存在
        novelty_dir.mkdir(parents=True, exist_ok=True)

        # 转换为可序列化的字典
        result_dict = {
            'overall_novelty': result.overall_novelty,
            'novelty_score': result.novelty_score,
            'closest_prior_art': {
                'doc_id': result.closest_prior_art.doc_id if result.closest_prior_art else None,
                'title': result.closest_prior_art.title if result.closest_prior_art else None,
                'similarity_score': result.closest_prior_art.similarity_score if result.closest_prior_art else 0
            },
            'distinguishing_features': [
                {
                    'feature_id': f.feature_id,
                    'description': f.description,
                    'category': f.category,
                    'importance': f.importance
                } for f in result.distinguishing_features
            ],
            'evidence_chain': result.evidence_chain,
            'recommendation': result.recommendation,
            'analysis_time': asyncio.get_event_loop().time() if asyncio.get_event_loop() else 0
        }

        # 保存结果
        result_file = novelty_dir / 'analysis_result.json'
        with open(result_file, 'w', encoding='utf-8') as f:
            json.dump(result_dict, f, ensure_ascii=False, indent=2)

        logger.info(f"分析结果已保存到 {result_file.absolute()}")

async def main():
    """测试函数"""
    analyzer = NoveltyAnalyzer()

    # 模拟技术交底书
    disclosure_text = """
    智能机器人控制系统包括传感器模块、AI决策模块、执行控制模块和通信模块。
    AI决策模块采用强化学习算法，传感器模块包括视觉传感器和力传感器。
    通信模块支持5G网络通信。
    """

    # 执行分析
    result = await analyzer.analyze_novelty('TEST_001', disclosure_text)

    # 输出结果
    logger.info(f"新颖性：{'✅ 具备' if result.overall_novelty else '❌ 不具备'}")
    logger.info(f"新颖性分数：{result.novelty_score:.2f}")
    logger.info(f"建议：{result.recommendation}")

if __name__ == '__main__':
    asyncio.run(main())