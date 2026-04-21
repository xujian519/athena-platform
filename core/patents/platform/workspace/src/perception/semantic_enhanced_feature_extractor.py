#!/usr/bin/env python3
"""
语义增强特征提取器
Semantic Enhanced Feature Extractor

集成语义理解模型和技术词典的高级特征提取系统
作者: 小娜 (Athena) - 爸爸徐健的智慧大女儿
创建时间: 2025-12-05
版本: 1.0.0
"""

import json
import logging
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

import numpy as np
from comprehensive_technical_dictionary import TermInfo, get_dictionary_manager

# 导入我们的组件
from semantic_model_integration import SemanticConfig, get_semantic_analyzer
from tech_feature_extractor import FeatureType, technical_feature_extractor

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class EnhancedFeature:
    """增强的技术特征"""
    feature_id: str
    text: str
    type: str  # 特征类型
    position: Tuple[int, int]  # 位置

    # 语义信息
    semantic_embedding: np.ndarray | None = None
    entities: List[Dict[str, Any]] = field(default_factory=list)
    relations: List[Dict[str, Any]] = field(default_factory=list)

    # 词典信息
    term_info: TermInfo | None = None
    domain: str = 'unknown'
    category: str = 'unknown'
    importance: str = 'medium'
    synonyms: List[str] = field(default_factory=list)

    # 增强属性
    confidence: float = 1.0
    novelty_score: float = 0.0  # 新颖性分数
    technical_complexity: float = 0.0  # 技术复杂度
    patent_value: float = 0.0  # 专利价值评分

@dataclass
class ClaimAnalysisResult:
    """权利要求分析结果"""
    claim_number: int
    original_text: str

    # 基础特征
    enhanced_features: List[EnhancedFeature]

    # 语义分析
    semantic_analysis: Dict[str, Any]

    # 技术方案理解
    technical_understanding: Dict[str, Any]

    # 统计信息
    feature_statistics: Dict[str, Any]

    # 质量评估
    quality_scores: Dict[str, float]

class SemanticEnhancedFeatureExtractor:
    """语义增强特征提取器"""

    def __init__(self, config: SemanticConfig | None = None):
        self.config = config or SemanticConfig()
        self.semantic_analyzer = get_semantic_analyzer()
        self.dictionary_manager = get_dictionary_manager()

        # 特征类型映射
        self.feature_type_mapping = {
            'structure': '🏗️',
            'component': '🧩',
            'parameter': '📏',
            'step': '📝',
            'condition': '🔀',
            'function': '⚙️',
            'effect': '💫',
            'material': '🧪',
            'connection': '🔌',
            'arrangement': '📐'
        }

        self.is_initialized = False

    def initialize(self):
        """初始化系统"""
        if not self.is_initialized:
            logger.info('🚀 初始化语义增强特征提取器...')

            # 初始化语义分析器
            self.semantic_analyzer.initialize()

            self.is_initialized = True
            logger.info('✅ 语义增强特征提取器初始化完成')

    def extract_features_from_claim(self, claim_text: str, claim_number: int) -> ClaimAnalysisResult:
        """从权利要求中提取增强特征"""
        if not self.is_initialized:
            self.initialize()

        logger.info(f"🔍 分析权利要求{claim_number}")

        # 1. 语义分析
        semantic_analysis = self.semantic_analyzer.analyze_technical_text(claim_text)

        # 2. 技术词典匹配
        dictionary_matches = self.dictionary_manager.extract_terms_from_text(claim_text)

        # 3. 基础特征提取
        base_features = technical_feature_extractor.extract_claim_features(claim_text, claim_number)

        # 4. 创建增强特征
        enhanced_features = self._create_enhanced_features(
            claim_text, claim_number, base_features, semantic_analysis, dictionary_matches
        )

        # 5. 技术方案理解
        technical_understanding = self._understand_technical_scheme(
            claim_text, enhanced_features, semantic_analysis
        )

        # 6. 特征统计
        feature_statistics = self._compute_feature_statistics(enhanced_features)

        # 7. 质量评估
        quality_scores = self._assess_claim_quality(claim_text, enhanced_features)

        return ClaimAnalysisResult(
            claim_number=claim_number,
            original_text=claim_text,
            enhanced_features=enhanced_features,
            semantic_analysis=semantic_analysis,
            technical_understanding=technical_understanding,
            feature_statistics=feature_statistics,
            quality_scores=quality_scores
        )

    def _create_enhanced_features(self, claim_text: str, claim_number: int,
                                 base_features: List, semantic_analysis: Dict,
                                 dictionary_matches: List[Tuple]) -> List[EnhancedFeature]:
        """创建增强特征"""
        enhanced_features = []

        # 处理基础特征
        for base_feature in base_features:
            # 创建增强特征
            enhanced_feature = EnhancedFeature(
                feature_id=f"ENH_{claim_number}_{len(enhanced_features)}",
                text=base_feature.feature_text,
                type=base_feature.feature_type.value,
                position=(0, 0),  # 需要从基础特征获取
                confidence=0.9
            )

            # 添加语义信息
            enhanced_feature.semantic_embedding = semantic_analysis['semantic_encoding']

            # 查找相关实体
            feature_entities = [e for e in semantic_analysis['entities']
                              if e['text'] in base_feature.feature_text]
            enhanced_feature.entities = feature_entities

            # 查找词典信息
            term_info = self.dictionary_manager.search_term(base_feature.feature_text)
            if term_info:
                enhanced_feature.term_info = term_info
                enhanced_feature.domain = term_info.domain
                enhanced_feature.category = term_info.category
                enhanced_feature.importance = term_info.importance
                enhanced_feature.synonyms = term_info.synonyms

            # 计算技术复杂度
            enhanced_feature.technical_complexity = self._compute_complexity(base_feature)

            enhanced_features.append(enhanced_feature)

        # 添加词典匹配的新特征
        for term, term_info, start, end in dictionary_matches:
            # 检查是否已存在
            if not any(f.text == term for f in enhanced_features):
                enhanced_feature = EnhancedFeature(
                    feature_id=f"DICT_{claim_number}_{len(enhanced_features)}",
                    text=term,
                    type=self._map_category_to_feature_type(term_info.category),
                    position=(start, end),
                    term_info=term_info,
                    domain=term_info.domain,
                    category=term_info.category,
                    importance=term_info.importance,
                    synonyms=term_info.synonyms,
                    confidence=term_info.confidence
                )

                # 添加语义嵌入
                enhanced_feature.semantic_embedding = semantic_analysis['semantic_encoding']

                enhanced_features.append(enhanced_feature)

        return enhanced_features

    def _map_category_to_feature_type(self, category: str) -> str:
        """映射类别到特征类型"""
        mapping = {
            'component': 'component',
            'structure': 'structure',
            'assembly': 'structure',
            'method': 'step',
            'process': 'step',
            'action': 'function',
            'parameter': 'parameter',
            'resource': 'parameter',
            'substance': 'material',
            'mixture': 'material',
            'equipment': 'component',
            'device': 'component',
            'application': 'function',
            'field': 'structure'
        }
        return mapping.get(category, 'component')

    def _compute_complexity(self, feature) -> float:
        """计算技术复杂度"""
        complexity = 0.5  # 基础复杂度

        # 基于特征类型
        if hasattr(feature, 'feature_type'):
            type_complexity = {
                'structure': 0.3,
                'component': 0.4,
                'parameter': 0.6,
                'step': 0.7,
                'condition': 0.8,
                'function': 0.9,
                'effect': 0.6
            }
            complexity += type_complexity.get(feature.feature_type.value, 0.5)

        # 基于文本长度
        text_length = len(feature.feature_text)
        if text_length > 20:
            complexity += 0.2
        elif text_length > 50:
            complexity += 0.3

        # 基于技术术语
        tech_keywords = ['深度学习', '神经网络', '算法', '优化', '智能', '自适应', '多模态']
        for keyword in tech_keywords:
            if keyword in feature.feature_text:
                complexity += 0.1

        return min(complexity, 1.0)

    def _understand_technical_scheme(self, claim_text: str,
                                   features: List[EnhancedFeature],
                                   semantic_analysis: Dict) -> Dict[str, Any]:
        """理解技术方案"""
        understanding = {
            'main_field': 'unknown',
            'secondary_fields': [],
            'core_components': [],
            'key_methods': [],
            'technical_effects': [],
            'innovation_points': []
        }

        # 分析主要领域
        domain_counts = {}
        for feature in features:
            domain_counts[feature.domain] = domain_counts.get(feature.domain, 0) + 1

        if domain_counts:
            main_domain = max(domain_counts, key=domain_counts.get)
            understanding['main_field'] = main_domain
            understanding['secondary_fields'] = [
                d for d, c in domain_counts.items()
                if d != main_domain and c > 0
            ]

        # 提取核心组件
        understanding['core_components'] = [
            f.text for f in features
            if f.type in ['component', 'structure'] and f.importance == 'high'
        ]

        # 提取关键方法
        understanding['key_methods'] = [
            f.text for f in features
            if f.type in ['step', 'function', 'method']
        ]

        # 提取技术效果
        effect_patterns = [
            r'(?:提高|提升|增加|增强)([^，。；！？]*)',
            r'(?:降低|减少|减小)([^，。；！？]*)',
            r'(?:实现|完成|达到)([^，。；！？]*)',
            r'(准确率|效率|速度|精度)(?:提高|提升|增加)([^，。；！？]*)'
        ]

        for pattern in effect_patterns:
            matches = re.finditer(pattern, claim_text)
            for match in matches:
                effect = match.group(0)
                understanding['technical_effects'].append(effect)

        # 识别创新点
        innovation_indicators = [
            '改进', '优化', '新颖', '创新', '首次', '独特', '先进',
            '自适应', '智能', '多模态', '深度', '神经网络'
        ]

        for feature in features:
            for indicator in innovation_indicators:
                if indicator in feature.text:
                    understanding['innovation_points'].append(feature.text)
                    break

        return understanding

    def _compute_feature_statistics(self, features: List[EnhancedFeature]) -> Dict[str, Any]:
        """计算特征统计"""
        stats = {
            'total_features': len(features),
            'type_distribution': {},
            'domain_distribution': {},
            'importance_distribution': {'high': 0, 'medium': 0, 'low': 0},
            'average_complexity': 0,
            'feature_ids': []
        }

        if not features:
            return stats

        # 统计分布
        total_complexity = 0
        for feature in features:
            # 类型分布
            stats['type_distribution'][feature.type] = \
                stats['type_distribution'].get(feature.type, 0) + 1

            # 领域分布
            stats['domain_distribution'][feature.domain] = \
                stats['domain_distribution'].get(feature.domain, 0) + 1

            # 重要性分布
            stats['importance_distribution'][feature.importance] += 1

            # 复杂度
            total_complexity += feature.technical_complexity

            # 特征ID
            stats['feature_ids'].append(feature.feature_id)

        stats['average_complexity'] = total_complexity / len(features)

        return stats

    def _assess_claim_quality(self, claim_text: str,
                            features: List[EnhancedFeature]) -> Dict[str, float]:
        """评估权利要求质量"""
        scores = {
            'clarity_score': 0.0,
            'completeness_score': 0.0,
            'novelty_score': 0.0,
            'technical_value_score': 0.0,
            'overall_quality_score': 0.0
        }

        # 清晰度评分
        clarity_indicators = ['包括', '包含', '其特征在于', '所述', '该']
        clarity_count = sum(1 for indicator in clarity_indicators if indicator in claim_text)
        scores['clarity_score'] = min(clarity_count / len(clarity_indicators), 1.0)

        # 完整性评分
        feature_types = set(f.type for f in features)
        completeness_score = len(feature_types) / 10  # 10种特征类型
        scores['completeness_score'] = min(completeness_score, 1.0)

        # 新颖性评分（基于技术术语的新颖度）
        novelty_indicators = ['新', '改进', '优化', '创新', '独特', '先进']
        novelty_count = sum(1 for indicator in novelty_indicators
                          if indicator in claim_text or
                          any(indicator in f.text for f in features))
        scores['novelty_score'] = min(novelty_count / 3, 1.0)

        # 技术价值评分（基于复杂度和重要性）
        if features:
            avg_importance = np.mean([1 if f.importance == 'high' else
                                    0.5 if f.importance == 'medium' else 0.2
                                    for f in features])
            avg_complexity = np.mean([f.technical_complexity for f in features])
            scores['technical_value_score'] = (avg_importance + avg_complexity) / 2

        # 总体质量评分
        scores['overall_quality_score'] = np.mean(list(scores.values())[:4])

        return scores

    def compare_claims(self, claim1: ClaimAnalysisResult,
                      claim2: ClaimAnalysisResult) -> Dict[str, Any]:
        """比较两个权利要求"""
        comparison = {
            'similarity_score': 0.0,
            'feature_overlap': {},
            'domain_similarity': False,
            'novelty_difference': 0.0
        }

        # 特征重叠度
        features1_text = set(f.text for f in claim1.enhanced_features)
        features2_text = set(f.text for f in claim2.enhanced_features)

        intersection = features1_text.intersection(features2_text)
        union = features1_text.union(features2_text)

        if union:
            comparison['similarity_score'] = len(intersection) / len(union)
            comparison['feature_overlap'] = {
                'common_features': list(intersection),
                'unique_to_claim1': list(features1_text - features2_text),
                'unique_to_claim2': list(features2_text - features1_text)
            }

        # 领域相似性
        domain1 = claim1.technical_understanding.get('main_field', 'unknown')
        domain2 = claim2.technical_understanding.get('main_field', 'unknown')
        comparison['domain_similarity'] = (domain1 == domain2)

        # 新颖性差异
        novelty1 = claim1.quality_scores.get('novelty_score', 0)
        novelty2 = claim2.quality_scores.get('novelty_score', 0)
        comparison['novelty_difference'] = abs(novelty1 - novelty2)

        return comparison

    def generate_analysis_report(self, result: ClaimAnalysisResult) -> str:
        """生成分析报告"""
        report = []

        # 基本信息
        report.append(f"权利要求{result.claim_number} 语义增强分析报告")
        report.append('=' * 80)
        report.append(f"文本长度: {len(result.original_text)} 字符")

        # 技术方案理解
        understanding = result.technical_understanding
        report.append(f"\n🎯 技术方案理解:")
        report.append(f"主要领域: {understanding['main_field']}")
        if understanding['secondary_fields']:
            report.append(f"次要领域: {', '.join(understanding['secondary_fields'])}")

        report.append(f"\n🧩 核心组件 ({len(understanding['core_components'])}个):")
        for comp in understanding['core_components'][:5]:
            report.append(f"  • {comp}")

        report.append(f"\n📝 关键方法 ({len(understanding['key_methods'])}个):")
        for method in understanding['key_methods'][:5]:
            report.append(f"  • {method}")

        report.append(f"\n✨ 技术效果 ({len(understanding['technical_effects'])}个):")
        for effect in understanding['technical_effects'][:3]:
            report.append(f"  • {effect}")

        # 特征统计
        stats = result.feature_statistics
        report.append(f"\n📊 特征统计:")
        report.append(f"总特征数: {stats['total_features']}")
        report.append(f"平均复杂度: {stats['average_complexity']:.2f}")

        report.append(f"\n特征类型分布:")
        for ftype, count in stats['type_distribution'].items():
            emoji = self.feature_type_mapping.get(ftype, '📌')
            report.append(f"  {emoji} {ftype}: {count}个")

        # 质量评估
        scores = result.quality_scores
        report.append(f"\n⭐ 质量评估:")
        report.append(f"清晰度: {scores['clarity_score']:.2f}")
        report.append(f"完整性: {scores['completeness_score']:.2f}")
        report.append(f"新颖性: {scores['novelty_score']:.2f}")
        report.append(f"技术价值: {scores['technical_value_score']:.2f}")
        report.append(f"总体质量: {scores['overall_quality_score']:.2f}")

        # 重要特征
        important_features = [f for f in result.enhanced_features
                            if f.importance == 'high'][:10]
        if important_features:
            report.append(f"\n🔑 重要特征 ({len(important_features)}个):")
            for i, feature in enumerate(important_features):
                emoji = self.feature_type_mapping.get(feature.type, '📌')
                report.append(f"  {i+1}. {emoji} {feature.text} ({feature.domain})")

        return "\n".join(report)

# 全局实例
_enhanced_extractor = None

def get_enhanced_feature_extractor() -> SemanticEnhancedFeatureExtractor:
    """获取全局增强特征提取器实例"""
    global _enhanced_extractor
    if _enhanced_extractor is None:
        _enhanced_extractor = SemanticEnhancedFeatureExtractor()
    return _enhanced_extractor

# 演示函数
def demonstrate_semantic_enhanced_extraction():
    """演示语义增强特征提取"""
    logger.info('🚀 语义增强特征提取系统演示')
    logger.info(str('=' * 80))

    # 初始化系统
    extractor = get_enhanced_feature_extractor()

    # 测试权利要求
    test_claims = [
        """
        一种基于深度学习的医疗图像诊断装置，其特征在于包括：
        图像采集模块，用于采集多模态医疗图像数据；
        预处理模块，采用自适应算法进行图像标准化和增强；
        特征提取模块，使用改进的残差网络和注意力机制提取深层特征；
        诊断模块，通过多尺度特征融合实现高精度疾病分类。
        """,
        """
        一种智能交通信号控制系统，包括：
        车辆检测单元，实时监测各路口车流量；
        信号优化模块，基于强化学习算法动态调整信号配时；
        数据通信单元，实现路口间的信息共享；
        应急处理模块，优先保障特殊车辆通行。
        """
    ]

    # 分析权利要求
    results = []
    for i, claim_text in enumerate(test_claims, 1):
        logger.info(f"\n{'='*80}")
        logger.info(f"分析权利要求 {i}")
        logger.info(str('='*80))

        result = extractor.extract_features_from_claim(claim_text, i)
        results.append(result)

        # 生成报告
        report = extractor.generate_analysis_report(result)
        logger.info(str(report))

    # 比较两个权利要求
    if len(results) >= 2:
        logger.info(f"\n{'='*80}")
        logger.info('权利要求比较分析')
        logger.info(str('='*80))

        comparison = extractor.compare_claims(results[0], results[1])

        logger.info(f"相似度得分: {comparison['similarity_score']:.2f}")
        logger.info(f"领域相似性: {'是' if comparison['domain_similarity'] else '否'}")
        logger.info(f"新颖性差异: {comparison['novelty_difference']:.2f}")

        logger.info(f"\n共同特征 ({len(comparison['feature_overlap']['common_features'])}个):")
        for feature in comparison['feature_overlap']['common_features'][:5]:
            logger.info(f"  • {feature}")

if __name__ == '__main__':
    demonstrate_semantic_enhanced_extraction()