#!/usr/bin/env python3
"""
知识图谱增强的专利分析器
Knowledge Graph Enhanced Patent Analyzer

集成高级技术知识图谱的专利分析系统
作者: 小娜 (Athena) - 爸爸徐健的智慧大女儿
创建时间: 2025-12-05
版本: 1.0.0
"""

import logging
from dataclasses import dataclass
from typing import Any

import numpy as np

# 导入知识图谱和其他系统
from advanced_technical_knowledge_graph import TechEntity, get_knowledge_graph
from integrated_patent_analysis_system import (
    IntegratedPatentAnalysisSystem,
    PatentAnalysisResult,
)
from semantic_model_integration import get_semantic_analyzer

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class KGEnhancedAnalysisResult:
    """知识图谱增强的分析结果"""
    # 基础分析结果
    base_result: PatentAnalysisResult

    # 知识图谱增强
    matched_entities: list[tuple[TechEntity, float]] = None
    related_entities: list[TechEntity] | None = None
    knowledge_context: dict[str, Any] = None
    technology_trends: dict[str, Any] = None

    # 增强分析
    innovation_insights: list[str] | None = None
    cross_domain_potential: bool = False
    similar_patents_suggestions: list[str] | None = None
    expert_considerations: list[str] | None = None

    # 量化评分
    kg_confidence_score: float = 0.0
    novelty_enhancement: float = 0.0
    technical_strength_score: float = 0.0

class KnowledgeEnhancedPatentAnalyzer:
    """知识图谱增强的专利分析器"""

    def __init__(self):
        self.kg = get_knowledge_graph()
        self.base_analyzer = IntegratedPatentAnalysisSystem()
        self.semantic_analyzer = get_semantic_analyzer()
        self.is_initialized = False

        logger.info('🚀 初始化知识图谱增强专利分析器...')

    def initialize(self):
        """初始化系统"""
        if self.is_initialized:
            return

        # 初始化基础系统
        self.base_analyzer.initialize()

        # 尝试初始化语义分析器
        try:
            self.semantic_analyzer.initialize()
        except Exception as e:
            logger.warning(f"语义分析器初始化失败: {e}")

        # 检查知识图谱是否已有嵌入
        if self.kg.embedding_index is None:
            logger.info('🔄 构建知识图谱嵌入向量...')
            try:
                self.kg.build_embeddings()
            except Exception as e:
                logger.warning(f"构建嵌入失败: {e}")

        self.is_initialized = True
        logger.info('✅ 知识图谱增强专利分析器初始化完成')

    def analyze_patent_with_kg(self, patent_id: str, title: str, abstract: str,
                               claims: list[str]) -> KGEnhancedAnalysisResult:
        """使用知识图谱分析专利"""
        if not self.is_initialized:
            self.initialize()

        logger.info(f"🔍 知识图谱增强分析专利: {patent_id}")

        # 1. 基础分析
        base_result = self.base_analyzer.analyze_patent(patent_id, title, abstract, claims)

        # 2. 知识图谱增强
        full_text = f"{title} {abstract} {' '.join(claims)}"

        # 匹配知识图谱实体
        matched_entities = self.kg.generate_patent_keywords(full_text, top_k=50)

        # 转换为实体对象
        kg_entities = []
        for keyword, weight in matched_entities:
            search_results = self.kg.search_entities(keyword, limit=1)
            if search_results:
                kg_entities.append((search_results[0][0], weight))

        # 获取相关实体
        related_entities = []
        if kg_entities:
            main_entity = kg_entities[0][0]
            related_entities = self.kg.find_related_entities(main_entity.entity_id, limit=10)

        # 3. 知识上下文分析
        knowledge_context = self._analyze_knowledge_context(kg_entities, related_entities)

        # 4. 技术趋势分析
        technology_trends = self._analyze_technology_trends(kg_entities, base_result.ipc_classifications)

        # 5. 创新洞察
        innovation_insights = self._generate_innovation_insights(kg_entities, base_result)

        # 6. 跨领域潜力评估
        cross_domain_potential = self._assess_cross_domain_potential(kg_entities, knowledge_context)

        # 7. 相似专利建议
        similar_patents_suggestions = self._suggest_similar_patents(kg_entities, base_result.ipc_classifications)

        # 8. 专家审查考虑事项
        expert_considerations = self._generate_expert_considerations(kg_entities, base_result)

        # 9. 量化评分
        kg_confidence_score = self._calculate_kg_confidence(kg_entities, base_result)
        novelty_enhancement = self._calculate_novelty_enhancement(kg_entities, base_result)
        technical_strength_score = self._calculate_technical_strength(kg_entities, base_result)

        # 创建增强结果
        enhanced_result = KGEnhancedAnalysisResult(
            base_result=base_result,
            matched_entities=kg_entities[:20],  # 保留前20个
            related_entities=related_entities[:10],  # 保留前10个
            knowledge_context=knowledge_context,
            technology_trends=technology_trends,
            innovation_insights=innovation_insights,
            cross_domain_potential=cross_domain_potential,
            similar_patents_suggestions=similar_patents_suggestions,
            expert_considerations=expert_considerations,
            kg_confidence_score=kg_confidence_score,
            novelty_enhancement=novelty_enhancement,
            technical_strength_score=technical_strength_score
        )

        logger.info(f"✅ 知识图谱增强分析完成: {patent_id}")
        return enhanced_result

    def _analyze_knowledge_context(self, matched_entities: list[tuple[TechEntity, float]],
                                   related_entities: list[TechEntity]) -> dict[str, Any]:
        """分析知识上下文"""
        context = {
            'primary_domains': set(),
            'related_fields': set(),
            'technical_maturity': 'emerging',
            'industry_applications': [],
            'key_technologies': []
        }

        # 分析主要领域
        for entity, score in matched_entities[:10]:
            if entity.domain != 'unknown':
                context['primary_domains'].add(entity.domain)
            if entity.category == 'technical_term' and score > 1.0:
                context['key_technologies'].append(entity.name)

        # 分析相关领域
        for entity in related_entities:
            if entity.domain != 'unknown':
                context['related_fields'].add(entity.domain)

        # 评估技术成熟度
        high_confidence_terms = [e for e, s in matched_entities if s > 2.0]
        if len(high_confidence_terms) > 5:
            context['technical_maturity'] = 'mature'
        elif len(high_confidence_terms) > 2:
            context['technical_maturity'] = 'developing'

        # 转换set为list
        context['primary_domains'] = list(context['primary_domains'])
        context['related_fields'] = list(context['related_fields'])

        return context

    def _analyze_technology_trends(self, matched_entities: list[tuple[TechEntity, float]],
                                   ipc_classifications: list[dict]) -> dict[str, Any]:
        """分析技术趋势"""
        trends = {
            'emerging_technologies': [],
            'hot_domains': [],
            'industry_focus': [],
            'future_directions': []
        }

        # 识别新兴技术
        emerging_keywords = ['智能', 'AI', '人工智能', '深度学习', '机器学习', '量子', '纳米', '生物']
        for entity, _score in matched_entities:
            for keyword in emerging_keywords:
                if keyword in entity.name:
                    trends['emerging_technologies'].append(entity.name)
                    break

        # 热门领域
        domain_counts = {}
        for entity, _score in matched_entities:
            domain_counts[entity.domain] = domain_counts.get(entity.domain, 0) + 1

        trends['hot_domains'] = sorted(domain_counts.items(), key=lambda x: x[1], reverse=True)[:5]

        # 基于IPC的行业焦点
        if ipc_classifications:
            for ipc in ipc_classifications[:3]:
                if 'A61' in ipc['code']:
                    trends['industry_focus'].append('医疗健康')
                elif 'G06F' in ipc['code']:
                    trends['industry_focus'].append('信息技术')
                elif 'H04L' in ipc['code']:
                    trends['industry_focus'].append('通信技术')
                elif 'B60' in ipc['code']:
                    trends['industry_focus'].append('汽车工业')

        return trends

    def _generate_innovation_insights(self, matched_entities: list[tuple[TechEntity, float]],
                                     base_result: PatentAnalysisResult) -> list[str]:
        """生成创新洞察"""
        insights = []

        # 检查技术组合创新
        domains = set()
        for entity, _score in matched_entities[:10]:
            if entity.domain != 'unknown':
                domains.add(entity.domain)

        if len(domains) > 1:
            insights.append(f"涉及{len(domains)}个技术领域的组合，具有交叉创新潜力")

        # 检查关键技术
        high_tech_terms = [e.name for e, s in matched_entities
                          if e.category == 'technical_term' and s > 2.0]
        if high_tech_terms:
            insights.append(f"核心技术包括：{', '.join(high_tech_terms[:3])}")

        # 检查新兴技术应用
        emerging_applications = []
        for entity, _score in matched_entities:
            if '智能' in entity.name or 'AI' in entity.name:
                if '应用' in entity.description or '系统' in entity.description:
                    emerging_applications.append(entity.name)

        if emerging_applications:
            insights.append(f"新兴技术应用：{', '.join(emerging_applications[:2])}")

        # 基于IPC的创新分析
        if len(base_result.ipc_classifications) > 1:
            sections = {ipc['section'] for ipc in base_result.ipc_classifications}
            if len(sections) > 1:
                insights.append(f"跨{len(sections)}个技术部的创新，具有潜在突破性")

        return insights[:5]  # 返回前5个洞察

    def _assess_cross_domain_potential(self, matched_entities: list[tuple[TechEntity, float]],
                                      knowledge_context: dict[str, Any]) -> bool:
        """评估跨领域潜力"""
        # 检查是否涉及多个领域
        if len(knowledge_context['primary_domains']) > 1:
            return True

        # 检查是否有跨领域技术
        cross_domain_terms = ['系统', '平台', '集成', '融合', '综合', '多功能']
        for entity, _score in matched_entities:
            for term in cross_domain_terms:
                if term in entity.name:
                    return True

        # 检查相关领域
        if len(knowledge_context['related_fields']) > 2:
            return True

        return False

    def _suggest_similar_patents(self, matched_entities: list[tuple[TechEntity, float]],
                               ipc_classifications: list[dict]) -> list[str]:
        """建议相似专利"""
        suggestions = []

        # 基于技术术语的检索建议
        top_entities = [e.name for e, s in matched_entities if s > 1.5][:5]
        if top_entities:
            suggestions.append(f"技术术语检索：{', '.join(top_entities)}")

        # 基于IPC的检索建议
        if ipc_classifications:
            top_ipc = [ipc['code'] for ipc in ipc_classifications[:3]]
            suggestions.append(f"IPC分类检索：{', '.join(top_ipc)}")

        # 组合检索建议
        if top_entities and top_ipc:
            suggestions.append(f"组合检索：{top_ipc[0]} + {top_entities[0]}")

        return suggestions

    def _generate_expert_considerations(self, matched_entities: list[tuple[TechEntity, float]],
                                        base_result: PatentAnalysisResult) -> list[str]:
        """生成专家审查考虑事项"""
        considerations = []

        # 技术复杂性
        high_tech_count = len([e for e, s in matched_entities
                             if e.category == 'technical_term' and s > 2.0])
        if high_tech_count > 5:
            considerations.append('技术方案较为复杂，建议详细审查技术实现细节')

        # 领域特殊性
        domains = {e.domain for e, s in matched_entities if e.domain != 'unknown'}
        if 'medical' in domains:
            considerations.append('涉及医疗领域，需要特别关注临床应用效果和安全')
        if 'communication' in domains:
            considerations.append('涉及通信技术，需要评估标准化和兼容性问题')

        # 创新程度
        innovation_score = base_result.novelty_assessment.get('overall_score', 0)
        if innovation_score > 0.7:
            considerations.append('创新程度较高，建议进行全面的现有技术检索')
        elif innovation_score < 0.3:
            considerations.append('创新程度可能不足，需要仔细分析区别特征')

        # 实施难度
        implementation_keywords = ['设备', '系统', '装置', '工艺', '方法']
        implementation_count = sum(1 for e, s in matched_entities
                                 if any(kw in e.name for kw in implementation_keywords))
        if implementation_count > 10:
            considerations.append('涉及较多实施细节，需要评估可实施性')

        return considerations

    def _calculate_kg_confidence(self, matched_entities: list[tuple[TechEntity, float]],
                                 base_result: PatentAnalysisResult) -> float:
        """计算知识图谱置信度"""
        if not matched_entities:
            return 0.0

        # 基于匹配分数
        avg_match_score = np.mean([score for entity, score in matched_entities])

        # 基于覆盖度
        total_possible = 50  # 期望匹配的实体数
        coverage = min(len(matched_entities) / total_possible, 1.0)

        # 综合评分
        confidence = (avg_match_score * 0.6 + coverage * 0.4)
        return min(confidence, 1.0)

    def _calculate_novelty_enhancement(self, matched_entities: list[tuple[TechEntity, float]],
                                       base_result: PatentAnalysisResult) -> float:
        """计算新颖性增强度"""
        base_novelty = base_result.novelty_assessment.get('overall_score', 0)

        # 检查知识图谱中的新兴技术
        emerging_boost = 0
        for entity, _score in matched_entities:
            if '智能' in entity.name or 'AI' in entity.name or '深度学习' in entity.name:
                emerging_boost += 0.1

        # 检查跨领域技术
        domains = {entity.domain for entity, score in matched_entities if entity.domain != 'unknown'}
        domain_boost = min(len(domains) / 3, 0.3)  # 跨领域增强

        # 计算增强后的新颖性
        enhanced_novelty = base_novelty + emerging_boost + domain_boost
        return min(enhanced_novelty, 1.0)

    def _calculate_technical_strength(self, matched_entities: list[tuple[TechEntity, float]],
                                     base_result: PatentAnalysisResult) -> float:
        """计算技术实力评分"""
        # 技术术语数量和权重
        tech_terms = [score for entity, score in matched_entities
                     if entity.category == 'technical_term']
        tech_strength = np.mean(tech_terms) if tech_terms else 0

        # 技术完整性
        feature_count = base_result.feature_statistics.get('total_features', 0)
        completeness = min(feature_count / 20, 1.0)  # 假设20个特征为完整

        # 综合评分
        technical_score = (tech_strength * 0.6 + completeness * 0.4)
        return min(technical_score, 1.0)

    def generate_comprehensive_report(self, result: KGEnhancedAnalysisResult) -> str:
        """生成综合分析报告"""
        report = []

        # 基础信息
        base = result.base_result
        report.append('📊 知识图谱增强专利分析报告')
        report.append('=' * 80)
        report.append(f"专利ID: {base.patent_id}")
        report.append(f"标题: {base.title}")
        report.append(f"分析时间: {base.analysis_time.strftime('%Y-%m-%d %H:%M:%S')}")
        report.append(f"知识图谱置信度: {result.kg_confidence_score:.2f}")

        # 知识图谱匹配
        report.append("\n🔗 知识图谱分析:")
        report.append(f"匹配实体数: {len(result.matched_entities) if result.matched_entities else 0}")
        report.append(f"相关实体数: {len(result.related_entities) if result.related_entities else 0}")

        if result.matched_entities:
            report.append("\n匹配的关键技术实体:")
            for entity, score in result.matched_entities[:5]:
                report.append(f"  • {entity.name} (置信度: {score:.2f}, 领域: {entity.domain})")

        # 知识上下文
        if result.knowledge_context:
            ctx = result.knowledge_context
            report.append("\n🧠 知识上下文:")
            report.append(f"主要技术领域: {', '.join(ctx.get('primary_domains', []))}")
            report.append(f"相关技术领域: {', '.join(ctx.get('related_fields', []))}")
            report.append(f"技术成熟度: {ctx.get('technical_maturity', 'unknown')}")

        # 创新洞察
        if result.innovation_insights:
            report.append("\n💡 创新洞察:")
            for insight in result.innovation_insights:
                report.append(f"  • {insight}")

        # 技术趋势
        if result.technology_trends:
            trends = result.technology_trends
            report.append("\n📈 技术趋势:")
            if trends.get('emerging_technologies'):
                report.append(f"新兴技术: {', '.join(trends['emerging_technologies'][:3])}")
            if trends.get('hot_domains'):
                report.append(f"热门领域: {', '.join([f'{d}({c})' for d, c in trends['hot_domains'][:3]])}")

        # 量化评分
        report.append("\n⭐ 综合评分:")
        report.append(f"知识图谱置信度: {result.kg_confidence_score:.2f}")
        report.append(f"新颖性增强度: {result.novelty_enhancement:.2f}")
        report.append(f"技术实力评分: {result.technical_strength_score:.2f}")

        if result.cross_domain_potential:
            report.append('✅ 具有跨领域创新潜力')

        # 专家建议
        if result.expert_considerations:
            report.append("\n👨‍💼 专家审查建议:")
            for consideration in result.expert_considerations:
                report.append(f"  • {consideration}")

        # 检索建议
        if result.similar_patents_suggestions:
            report.append("\n🔍 相似专利检索建议:")
            for suggestion in result.similar_patents_suggestions:
                report.append(f"  • {suggestion}")

        return "\n".join(report)

# 演示函数
def demonstrate_kg_enhanced_analyzer():
    """演示知识图谱增强分析器"""
    logger.info('🚀 知识图谱增强专利分析器演示')
    logger.info(str('=' * 80))

    # 初始化分析器
    analyzer = KnowledgeEnhancedPatentAnalyzer()

    # 测试专利
    test_patents = [
        {
            'id': 'TECH_PATENT_001',
            'title': '基于深度学习的智能医疗影像诊断系统',
            'abstract': '本发明提供一种结合人工智能和深度学习技术的医疗影像自动诊断系统，能够准确识别各种疾病特征。',
            'claims': [
                '一种基于深度学习的医疗影像诊断系统，包括：影像采集模块，用于获取多模态医学影像数据；预处理模块，采用自适应算法对影像进行标准化处理；深度学习模块，使用改进的卷积神经网络和注意力机制提取关键特征；诊断模块，基于提取的特征进行疾病分类和风险评估。',
                '根据权利要求1所述的系统，其特征在于，所述深度学习模块采用残差网络结构和多尺度特征融合技术。'
            ]
        }
    ]

    # 分析专利
    for patent in test_patents:
        result = analyzer.analyze_patent_with_kg(
            patent['id'],
            patent['title'],
            patent['abstract'],
            patent['claims']
        )

        # 生成报告
        report = analyzer.generate_comprehensive_report(result)
        logger.info(str(report))

if __name__ == '__main__':
    demonstrate_kg_enhanced_analyzer()
