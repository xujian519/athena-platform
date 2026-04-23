#!/usr/bin/env python3
"""
集成专利分析系统
Integrated Patent Analysis System

整合语义理解、技术词典、IPC分类和特征提取的完整系统
作者: 小娜 (Athena) - 爸爸徐健的智慧大女儿
创建时间: 2025-12-05
版本: 1.0.0
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from comprehensive_technical_dictionary import get_dictionary_manager
from ipc_classification_system import get_ipc_system

# 导入各个子系统
from semantic_model_integration import get_semantic_analyzer
from test_enhanced_system_demo import MockEnhancedAnalyzer

from core.logging_config import setup_logging

# 配置日志
# setup_logging()  # 日志配置已移至模块导入
logger = setup_logging()

@dataclass
class PatentAnalysisResult:
    """完整的专利分析结果"""
    # 基本信息
    patent_id: str
    title: str
    abstract: str
    claims: list[str]

    # 分析时间
    analysis_time: datetime = field(default_factory=datetime.now)

    # IPC分类结果
    ipc_classifications: list[dict[str, Any] = field(default_factory=list)
    primary_ipc: str | None = None

    # 技术特征分析
    technical_features: list[dict[str, Any] = field(default_factory=list)
    feature_statistics: dict[str, Any] = field(default_factory=dict)

    # 语义分析
    semantic_analysis: dict[str, Any] = field(default_factory=dict)

    # 技术方案理解
    technical_understanding: dict[str, Any] = field(default_factory=dict)

    # 新颖性评估
    novelty_assessment: dict[str, Any] = field(default_factory=dict)

    # 检索策略
    search_strategy: dict[str, Any] = field(default_factory=dict)

    # 质量评分
    quality_scores: dict[str, float] = field(default_factory=dict)

@dataclass
class ComparisonResult:
    """专利对比结果"""
    patent1_id: str
    patent2_id: str

    # IPC分类对比
    ipc_similarity: float
    ipc_relationship: str

    # 技术特征对比
    feature_overlap: float
    unique_features_1: list[str]
    unique_features_2: list[str]

    # 语义相似度
    semantic_similarity: float

    # 新颖性判断
    novelty_judgment: str
    reasoning: list[str]

class IntegratedPatentAnalysisSystem:
    """集成专利分析系统"""

    def __init__(self, config: dict[str, Any] | None = None):
        self.config = config or {}

        # 初始化各个子系统
        self.semantic_analyzer = get_semantic_analyzer()
        self.dictionary_manager = get_dictionary_manager()
        self.enhanced_analyzer = MockEnhancedAnalyzer()
        self.ipc_system = get_ipc_system()

        self.is_initialized = False

        logger.info('🚀 初始化集成专利分析系统...')

    def initialize(self) -> Any:
        """初始化所有子系统"""
        if self.is_initialized:
            return

        # 初始化语义分析器
        try:
            self.semantic_analyzer.initialize()
            logger.info('✅ 语义分析器初始化成功')
        except Exception as e:
            logger.warning(f"⚠️ 语义分析器初始化失败，使用模拟模式: {e}")

        self.is_initialized = True
        logger.info('✅ 集成专利分析系统初始化完成')

    def analyze_patent(self, patent_id: str, title: str, abstract: str,
                      claims: list[str]) -> PatentAnalysisResult:
        """完整分析专利"""
        if not self.is_initialized:
            self.initialize()

        logger.info(f"🔍 开始分析专利: {patent_id}")

        result = PatentAnalysisResult(
            patent_id=patent_id,
            title=title,
            abstract=abstract,
            claims=claims
        )

        # 1. IPC分类分析
        f"{title} {abstract} {' '.join(claims)}"
        ipc_match = self.ipc_system.match_patent_to_ipc(
            claims[0] if claims else '', title, abstract
        )

        result.ipc_classifications = [
            {
                'code': ipc.code,
                'name': ipc.name,
                'section': ipc.section,
                'domain': ipc.domain,
                'confidence': float(score),
                'keywords': keywords
            }
            for ipc, score, keywords in zip(
                ipc_match.matched_codes,
                ipc_match.confidence_scores,
                ipc_match.matching_keywords, strict=False
            )
        ]

        if result.ipc_classifications:
            result.primary_ipc = result.ipc_classifications[0]['code']

        # 2. 技术特征分析（分析每个权利要求）
        all_features = []
        for i, claim in enumerate(claims, 1):
            claim_analysis = self.enhanced_analyzer.extract_enhanced_features(claim, i)

            # 转换特征格式
            for feature in claim_analysis['semantic_features']:
                all_features.append({
                    'claim_number': i,
                    'text': feature['text'],
                    'type': feature['type'],
                    'importance': feature.get('importance', 'medium'),
                    'confidence': feature.get('confidence', 1.0)
                })

            # 保存第一个权利要求的详细分析
            if i == 1:
                result.technical_understanding = claim_analysis['technical_understanding']
                result.quality_scores = claim_analysis['quality_assessment']

        result.technical_features = all_features

        # 3. 特征统计
        result.feature_statistics = self._compute_feature_statistics(all_features)

        # 4. 语义分析（对第一个权利要求）
        if claims:
            try:
                result.semantic_analysis = self.semantic_analyzer.analyze_technical_text(claims[0])
            except Exception as e:
                logger.warning(f"语义分析失败: {e}")
                result.semantic_analysis = {'entities': [], 'relations': [], 'technical_score': 0}

        # 5. 新颖性评估
        result.novelty_assessment = self._assess_novelty(result)

        # 6. 检索策略生成
        result.search_strategy = self._generate_search_strategy(result)

        logger.info(f"✅ 专利分析完成: {patent_id}")
        return result

    def _compute_feature_statistics(self, features: list[dict[str, Any]) -> dict[str, Any]:
        """计算特征统计"""
        stats = {
            'total_features': len(features),
            'type_distribution': {},
            'importance_distribution': {'high': 0, 'medium': 0, 'low': 0},
            'claim_distribution': {}
        }

        for feature in features:
            # 类型分布
            ftype = feature['type']
            stats['type_distribution'][ftype] = stats['type_distribution'].get(ftype, 0) + 1

            # 重要性分布
            importance = feature['importance']
            stats['importance_distribution'][importance] += 1

            # 权利要求分布
            claim_num = feature['claim_number']
            stats['claim_distribution'][claim_num] = stats['claim_distribution'].get(claim_num, 0) + 1

        return stats

    def _assess_novelty(self, result: PatentAnalysisResult) -> dict[str, Any]:
        """评估新颖性"""
        assessment = {
            'overall_score': 0.0,
            'technical_field_score': 0.0,
            'feature_novelty_score': 0.0,
            'cross_domain_potential': False,
            'key_innovations': [],
            'recommendations': []
        }

        # 技术领域评分
        if len(result.ipc_classifications) > 1:
            sections = {ipc['section'] for ipc in result.ipc_classifications[:2]}
            if len(sections) > 1:
                assessment['technical_field_score'] = 0.7
                assessment['cross_domain_potential'] = True
                assessment['recommendations'].append('跨领域技术，具有潜在新颖性')

        # 特征新颖性评分
        innovation_keywords = ['新', '改进', '优化', '创新', '独特', '先进', '智能', '自适应']
        innovation_count = 0

        for feature in result.technical_features:
            for keyword in innovation_keywords:
                if keyword in feature['text']:
                    innovation_count += 1
                    if feature['text'] not in assessment['key_innovations']:
                        assessment['key_innovations'].append(feature['text'])
                    break

        if result.technical_features:
            assessment['feature_novelty_score'] = min(innovation_count / len(result.technical_features), 1.0)

        # 综合评分
        assessment['overall_score'] = (
            assessment['technical_field_score'] * 0.4 +
            assessment['feature_novelty_score'] * 0.6
        )

        # 生成建议
        if assessment['overall_score'] > 0.7:
            assessment['recommendations'].append('建议进行深入的现有技术检索')
        elif assessment['overall_score'] > 0.4:
            assessment['recommendations'].append('重点关注技术特征的组合创新')
        else:
            assessment['recommendations'].append('需要进一步挖掘创新点')

        return assessment

    def _generate_search_strategy(self, result: PatentAnalysisResult) -> dict[str, Any]:
        """生成检索策略"""
        strategy = {
            'primary_keywords': [],
            'secondary_keywords': [],
            'ipc_classes': [],
            'search_combinations': [],
            'exclusion_terms': []
        }

        # 从IPC分类获取关键词
        for ipc in result.ipc_classifications[:3]:
            if ipc.get('keywords'):
                strategy['primary_keywords'].extend(ipc['keywords'])
            strategy['ipc_classes'].append(ipc['code'])

        # 从技术特征获取关键词
        for feature in result.technical_features:
            if feature['importance'] == 'high' and len(feature['text']) > 2:
                strategy['primary_keywords'].append(feature['text'])
            elif feature['importance'] == 'medium':
                strategy['secondary_keywords'].append(feature['text'])

        # 去重
        strategy['primary_keywords'] = list(set(strategy['primary_keywords']))
        strategy['secondary_keywords'] = list(set(strategy['secondary_keywords']))

        # 生成检索组合
        if len(strategy['ipc_classes']) >= 2:
            for ipc in strategy['ipc_classes'][:2]:
                for keyword in strategy['primary_keywords'][:3]:
                    strategy['search_combinations'].append(f"{ipc} AND {keyword}")

        # 排除词
        strategy['exclusion_terms'] = ['审查指南', '专利法', '现有技术']

        return strategy

    def compare_patents(self, result1: PatentAnalysisResult,
                        result2: PatentAnalysisResult) -> ComparisonResult:
        """对比两个专利"""
        logger.info(f"🔄 对比专利: {result1.patent_id} vs {result2.patent_id}")

        # IPC分类对比
        ipc1 = result1.primary_ipc
        ipc2 = result2.primary_ipc
        ipc_comparison = self.ipc_system.compare_ipc_classes(ipc1 or '', ipc2 or '')

        # 技术特征对比
        features1_text = {f['text'] for f in result1.technical_features}
        features2_text = {f['text'] for f in result2.technical_features}

        common_features = features1_text & features2_text
        unique1 = features1_text - features2_text
        unique2 = features2_text - features1_text

        feature_overlap = len(common_features) / len(features1_text | features2_text) if features1_text | features2_text else 0

        # 语义相似度（简化版）
        semantic_similarity = 0.0
        if result1.semantic_analysis.get('technical_score', 0) > 0 and result2.semantic_analysis.get('technical_score', 0) > 0:
            # 这里可以使用真实的语义相似度计算
            semantic_similarity = feature_overlap  # 简化处理

        # 新颖性判断
        if ipc_comparison['similarity'] > 0.7 and feature_overlap > 0.7:
            novelty_judgment = '可能不具备新颖性'
            reasoning = ['技术领域高度相关', '技术特征重合度高']
        elif ipc_comparison['similarity'] > 0.5 or feature_overlap > 0.5:
            novelty_judgment = '需要仔细分析区别特征'
            reasoning = ['技术领域或特征有部分重合', '需要识别关键差异点']
        else:
            novelty_judgment = '可能具有新颖性'
            reasoning = ['技术领域差异明显', '技术特征重合度低']

        if len({ipc[:2] for ipc in [ipc1, ipc2] if ipc}) > 1:
            reasoning.append('涉及不同技术领域，可能具有组合创新')

        return ComparisonResult(
            patent1_id=result1.patent_id,
            patent2_id=result2.patent_id,
            ipc_similarity=ipc_comparison['similarity'],
            ipc_relationship=ipc_comparison['relationship'],
            feature_overlap=feature_overlap,
            unique_features_1=list(unique1),
            unique_features_2=list(unique2),
            semantic_similarity=semantic_similarity,
            novelty_judgment=novelty_judgment,
            reasoning=reasoning
        )

    def generate_analysis_report(self, result: PatentAnalysisResult) -> str:
        """生成分析报告"""
        report = []

        # 标题
        report.append("专利分析报告")
        report.append('=' * 80)
        report.append(f"专利ID: {result.patent_id}")
        report.append(f"标题: {result.title}")
        report.append(f"分析时间: {result.analysis_time.strftime('%Y-%m-%d %H:%M:%S')}")

        # IPC分类
        report.append("\n📚 IPC分类分析:")
        report.append(f"主要分类: {result.primary_ipc}")
        for ipc in result.ipc_classifications[:3]:
            report.append(f"  • {ipc['code']} {ipc['name']} (置信度: {ipc['confidence']:.2f})")

        # 技术特征
        report.append("\n🔧 技术特征分析:")
        report.append(f"总特征数: {result.feature_statistics['total_features']}")

        type_dist = result.feature_statistics['type_distribution']
        if type_dist:
            report.append(f"特征类型分布: {dict(list(type_dist.items())[:5])}")

        # 技术方案理解
        understanding = result.technical_understanding
        if understanding:
            report.append("\n💡 技术方案理解:")
            report.append(f"主要领域: {understanding.get('main_field', 'unknown')}")

            if understanding.get('core_components'):
                report.append(f"核心组件: {understanding['core_components'][:3]}")

            if understanding.get('innovation_points'):
                report.append(f"创新点: {understanding['innovation_points'][:3]}")

        # 新颖性评估
        novelty = result.novelty_assessment
        report.append("\n🎯 新颖性评估:")
        report.append(f"综合评分: {novelty['overall_score']:.2f}")
        report.append(f"技术领域评分: {novelty['technical_field_score']:.2f}")
        report.append(f"特征新颖性评分: {novelty['feature_novelty_score']:.2f}")

        if novelty['key_innovations']:
            report.append(f"关键创新: {novelty['key_innovations'][:3]}")

        if novelty['recommendations']:
            report.append(f"建议: {'; '.join(novelty['recommendations'][:2])}")

        # 检索策略
        strategy = result.search_strategy
        report.append("\n🔍 检索策略:")
        if strategy['ipc_classes']:
            report.append(f"IPC分类: {', '.join(strategy['ipc_classes'][:3])}")
        if strategy['primary_keywords']:
            report.append(f"主要关键词: {', '.join(strategy['primary_keywords'][:5])}")
        if strategy['search_combinations']:
            report.append(f"检索组合示例: {strategy['search_combinations'][0] if strategy['search_combinations'] else '无'}")

        # 质量评分
        quality = result.quality_scores
        if quality:
            report.append("\n⭐ 质量评分:")
            report.append(f"清晰度: {quality.get('clarity_score', 0):.2f}")
            report.append(f"完整性: {quality.get('completeness_score', 0):.2f}")
            report.append(f"新颖性: {quality.get('novelty_score', 0):.2f}")
            report.append(f"总体质量: {quality.get('overall_quality_score', 0):.2f}")

        return "\n".join(report)

# 全局实例
_integrated_system = None

def get_integrated_system() -> IntegratedPatentAnalysisSystem:
    """获取全局集成系统实例"""
    global _integrated_system
    if _integrated_system is None:
        _integrated_system = IntegratedPatentAnalysisSystem()
    return _integrated_system

# 演示函数
def demonstrate_integrated_system() -> Any:
    """演示集成系统"""
    logger.info('🚀 集成专利分析系统演示')
    logger.info(str('=' * 80))

    # 初始化系统
    system = get_integrated_system()

    # 测试专利数据
    test_patents = [
        {
            'id': 'PATENT001',
            'title': '基于深度学习的医疗图像诊断系统',
            'abstract': '本发明涉及一种使用深度学习算法进行医疗图像自动分析的系统，包括图像采集、预处理、特征提取和诊断模块。',
            'claims': [
                '一种基于深度学习的医疗图像诊断装置，其特征在于包括：图像采集模块，用于采集多模态医疗图像数据；预处理模块，采用自适应算法进行图像标准化和增强；特征提取模块，使用改进的残差网络和注意力机制提取深层特征；诊断模块，通过多尺度特征融合实现高精度疾病分类。',
                '根据权利要求1所述的装置，其特征在于，所述特征提取模块包括：输入层，接收预处理后的图像数据；卷积层组，由多个卷积层组成；池化层组，用于降低特征图的空间维度；全连接层，输出最终的图像特征向量。'
            ]
        },
        {
            'id': 'PATENT002',
            'title': '智能交通信号优化控制系统',
            'abstract': '一种基于强化学习的智能交通信号控制系统，通过实时车流检测和动态信号调整，提高交通效率。',
            'claims': [
                '一种智能交通信号控制系统，包括：车辆检测单元，实时监测各路口车流量；信号优化模块，基于强化学习算法动态调整信号配时；数据通信单元，实现路口间的信息共享；应急处理模块，优先保障特殊车辆通行。',
                '根据权利要求1所述的系统，其特征在于，所述信号优化模块采用深度Q网络算法，根据历史交通数据预测最优信号配时方案。'
            ]
        }
    ]

    # 分析专利
    results = []
    for patent in test_patents:
        result = system.analyze_patent(
            patent['id'],
            patent['title'],
            patent['abstract'],
            patent['claims']
        )
        results.append(result)

        # 生成报告
        report = system.generate_analysis_report(result)
        logger.info(str(report))

        if len(results) < 2:
            logger.info(str("\n" + '='*80 + "\n"))

    # 对比分析
    if len(results) >= 2:
        logger.info(str("\n" + '='*80))
        logger.info('专利对比分析')
        logger.info(str('='*80))

        comparison = system.compare_patents(results[0], results[1])

        logger.info("\n📊 对比结果:")
        logger.info(f"专利1: {comparison.patent1_id}")
        logger.info(f"专利2: {comparison.patent2_id}")
        logger.info(f"IPC相似度: {comparison.ipc_similarity:.2f}")
        logger.info(f"特征重合度: {comparison.feature_overlap:.2f}")
        logger.info(f"语义相似度: {comparison.semantic_similarity:.2f}")

        logger.info("\n🎯 新颖性判断:")
        logger.info(f"结论: {comparison.novelty_judgment}")
        logger.info("理由:")
        for reason in comparison.reasoning:
            logger.info(f"  • {reason}")

if __name__ == '__main__':
    demonstrate_integrated_system()
