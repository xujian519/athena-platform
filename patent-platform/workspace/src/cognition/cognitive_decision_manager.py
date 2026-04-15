#!/usr/bin/env python3
"""
认知决策管理器
Cognitive Decision Manager

整合特征提取、推理引擎和决策生成的认知决策系统

作者: Athena + 小诺
创建时间: 2025-12-05
版本: 2.0.0
"""

import asyncio
import json
import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

import numpy as np
from enhanced_patent_feature_extractor import BERTEnhancedExtractor, EnhancedFeature

# 导入相关模块
from enhanced_reasoning_engine import EnhancedReasoningEngine, ReasoningResult

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class DecisionLevel(Enum):
    """决策级别"""
    STRONG_APPROVE = 5    # 强推荐授权
    APPROVE = 4           # 推荐授权
    WEAK_APPROVE = 3      # 弱推荐授权
    REJECT = 2            # 拒绝授权
    STRONG_REJECT = 1     # 强拒绝授权

class PatentDomain(Enum):
    """专利领域"""
    MECHANICAL = 'mechanical'
    ELECTRICAL = 'electrical'
    SOFTWARE = 'software'
    CHEMICAL = 'chemical'
    BIOMEDICAL = 'biomedical'
    TELECOMM = 'telecommunication'
    MATERIAL = 'material'
    OTHER = 'other'

@dataclass
class CognitiveDecision:
    """认知决策结果"""
    patent_id: str
    decision_level: DecisionLevel
    decision_summary: str
    detailed_analysis: dict[str, Any]
    confidence_score: float
    risk_assessment: dict[str, float]
    recommendations: list[str]
    supporting_evidence: list[str]
    opposing_evidence: list[str]
    processing_time: float
    timestamp: datetime = field(default_factory=datetime.now)

@dataclass
class DecisionMetrics:
    """决策指标"""
    novelty_score: float           # 新颖性分数
    inventive_score: float         # 创造性分数
    practical_score: float         # 实用性分数
    technical_merit: float         # 技术价值
    commercial_value: float        # 商业价值
    legal_compliance: float        # 合规性
    prior_art_risk: float          # 现有技术风险
    infringement_risk: float       # 侵权风险

class CognitiveDecisionManager:
    """认知决策管理器"""

    def __init__(self):
        self.feature_extractor = BERTEnhancedExtractor()
        self.reasoning_engine = EnhancedReasoningEngine()
        self.decision_history = []
        self.domain_expertise = self._initialize_domain_expertise()
        self.performance_metrics = {
            'total_decisions': 0,
            'average_confidence': 0.0,
            'processing_time_avg': 0.0,
            'decision_distribution': {level.name: 0 for level in DecisionLevel}
        }

    def _initialize_domain_expertise(self) -> dict[PatentDomain, dict[str, float]]:
        """初始化领域专业知识"""
        return {
            PatentDomain.MECHANICAL: {
                'novelty_threshold': 0.7,
                'inventive_threshold': 0.6,
                'technical_weight': 0.4,
                'practical_weight': 0.6
            },
            PatentDomain.ELECTRICAL: {
                'novelty_threshold': 0.8,
                'inventive_threshold': 0.7,
                'technical_weight': 0.5,
                'practical_weight': 0.5
            },
            PatentDomain.SOFTWARE: {
                'novelty_threshold': 0.9,
                'inventive_threshold': 0.8,
                'technical_weight': 0.7,
                'practical_weight': 0.3
            },
            PatentDomain.CHEMICAL: {
                'novelty_threshold': 0.75,
                'inventive_threshold': 0.65,
                'technical_weight': 0.4,
                'practical_weight': 0.6
            },
            PatentDomain.BIOMEDICAL: {
                'novelty_threshold': 0.85,
                'inventive_threshold': 0.75,
                'technical_weight': 0.6,
                'practical_weight': 0.4
            },
            PatentDomain.TELECOMM: {
                'novelty_threshold': 0.8,
                'inventive_threshold': 0.75,
                'technical_weight': 0.6,
                'practical_weight': 0.4
            },
            PatentDomain.MATERIAL: {
                'novelty_threshold': 0.75,
                'inventive_threshold': 0.65,
                'technical_weight': 0.5,
                'practical_weight': 0.5
            },
            PatentDomain.OTHER: {
                'novelty_threshold': 0.7,
                'inventive_threshold': 0.6,
                'technical_weight': 0.5,
                'practical_weight': 0.5
            }
        }

    async def make_decision(self,
                           patent_data: dict[str, Any],
                           context: dict[str, Any] | None = None) -> CognitiveDecision:
        """做出认知决策"""
        start_time = datetime.now()
        logger.info(f"🧠 开始对专利 {patent_data.get('patent_id', 'unknown')} 进行认知决策...")

        context = context or {}

        try:
            # 1. 特征提取
            features = await self._extract_features(patent_data)

            # 2. 计算决策指标
            metrics = self._calculate_decision_metrics(features, patent_data)

            # 3. 执行法律推理
            reasoning_result = await self.reasoning_engine.reason(patent_data, context)

            # 4. 领域特异性分析
            domain_analysis = self._analyze_domain_specificity(patent_data, metrics)

            # 5. 风险评估
            risk_assessment = self._assess_risks(patent_data, metrics, reasoning_result)

            # 6. 生成决策
            decision_level, confidence = self._generate_decision_level(metrics, reasoning_result, domain_analysis)

            # 7. 生成建议
            recommendations = self._generate_recommendations(decision_level, metrics, reasoning_result)

            # 8. 收集证据
            supporting_evidence, opposing_evidence = self._collect_evidence(patent_data, reasoning_result, metrics)

            # 9. 计算处理时间
            processing_time = (datetime.now() - start_time).total_seconds()

            # 10. 创建决策对象
            decision = CognitiveDecision(
                patent_id=patent_data.get('patent_id', 'unknown'),
                decision_level=decision_level,
                decision_summary=self._generate_decision_summary(decision_level, confidence),
                detailed_analysis={
                    'metrics': metrics.__dict__,
                    'reasoning': {
                        'conclusion': reasoning_result.conclusion,
                        'confidence': reasoning_result.confidence,
                        'applied_rules': reasoning_result.applied_rules,
                        'conflicts': reasoning_result.conflicts_detected
                    },
                    'domain_analysis': domain_analysis,
                    'features': [f.__dict__ for f in features]
                },
                confidence_score=confidence,
                risk_assessment=risk_assessment,
                recommendations=recommendations,
                supporting_evidence=supporting_evidence,
                opposing_evidence=opposing_evidence,
                processing_time=processing_time
            )

            # 11. 更新性能指标
            self._update_performance_metrics(decision)

            # 12. 记录决策历史
            self.decision_history.append(decision)

            logger.info(f"✅ 认知决策完成，决策级别: {decision_level.name}，置信度: {confidence:.2f}")
            return decision

        except Exception as e:
            logger.error(f"❌ 认知决策失败: {e}")
            raise

    async def _extract_features(self, patent_data: dict[str, Any]) -> list[EnhancedFeature]:
        """提取专利特征"""
        # 获取专利文本
        title = patent_data.get('title', '')
        abstract = patent_data.get('abstract', '')
        claims = patent_data.get('claims', '')
        description = patent_data.get('description', '')

        # 合并文本
        full_text = f"{title} {abstract} {claims} {description}"

        # 提取特征
        features = await self.feature_extractor.extract_features(
            full_text,
            patent_context=patent_data
        )

        return features

    def _calculate_decision_metrics(self,
                                   features: list[EnhancedFeature],
                                   patent_data: dict[str, Any]) -> DecisionMetrics:
        """计算决策指标"""
        # 从特征中提取分数
        novelty_score = 0.0
        inventive_score = 0.0
        technical_merit = 0.0

        for feature in features:
            if 'novelty' in feature.feature_name.lower():
                novelty_score = max(novelty_score, feature.confidence)
            elif 'inventive' in feature.feature_name.lower():
                inventive_score = max(inventive_score, feature.confidence)
            elif 'technical' in feature.feature_name.lower():
                technical_merit = max(technical_merit, feature.confidence)

        # 使用专利数据中的分数
        novelty_score = patent_data.get('novelty_score', novelty_score)
        inventive_score = patent_data.get('inventive_score', inventive_score)
        practical_score = patent_data.get('practical_score', 0.8)

        # 计算综合技术价值
        technical_value = (novelty_score + inventive_score + technical_merit) / 3

        # 评估商业价值（简化模型）
        commercial_value = self._evaluate_commercial_value(patent_data, technical_value)

        # 评估合规性
        legal_compliance = self._evaluate_legal_compliance(patent_data)

        # 评估风险
        prior_art_risk = 1 - novelty_score
        infringement_risk = patent_data.get('infringement_risk', 0.1)

        return DecisionMetrics(
            novelty_score=novelty_score,
            inventive_score=inventive_score,
            practical_score=practical_score,
            technical_merit=technical_merit,
            commercial_value=commercial_value,
            legal_compliance=legal_compliance,
            prior_art_risk=prior_art_risk,
            infringement_risk=infringement_risk
        )

    def _evaluate_commercial_value(self, patent_data: dict[str, Any], technical_value: float) -> float:
        """评估商业价值"""
        factors = {
            'market_size': patent_data.get('market_size', 0.5),
            'competition_level': patent_data.get('competition_level', 0.5),
            'industry_growth': patent_data.get('industry_growth', 0.5),
            'innovation_impact': patent_data.get('innovation_impact', technical_value)
        }

        # 加权计算
        weights = {
            'market_size': 0.3,
            'competition_level': 0.2,
            'industry_growth': 0.2,
            'innovation_impact': 0.3
        }

        commercial_value = sum(factors[key] * weights[key] for key in factors)
        return min(commercial_value, 1.0)

    def _evaluate_legal_compliance(self, patent_data: dict[str, Any]) -> float:
        """评估合规性"""
        # 检查是否符合法律要求
        compliance_factors = {
            'complete_disclosure': patent_data.get('complete_disclosure', True),
            'proper_claims': patent_data.get('proper_claims', True),
            'eligibility': patent_data.get('eligibility', True),
            'formal_requirements': patent_data.get('formal_requirements', True)
        }

        compliance_score = sum(int(compliance_factors[key]) for key in compliance_factors) / len(compliance_factors)
        return compliance_score

    def _analyze_domain_specificity(self,
                                   patent_data: dict[str, Any],
                                   metrics: DecisionMetrics) -> dict[str, Any]:
        """领域特异性分析"""
        # 识别专利领域
        domain = self._identify_patent_domain(patent_data)
        expertise = self.domain_expertise.get(domain, self.domain_expertise[PatentDomain.OTHER])

        # 根据领域特点调整评估
        adjusted_novelty = metrics.novelty_score * expertise['novelty_threshold']
        adjusted_inventive = metrics.inventive_score * expertise['inventive_threshold']

        # 加权计算综合分数
        overall_score = (
            adjusted_novelty * expertise['technical_weight'] +
            adjusted_inventive * expertise['practical_weight'] +
            metrics.practical_score * expertise['practical_weight']
        )

        return {
            'domain': domain.value,
            'expertise_weights': expertise,
            'adjusted_scores': {
                'novelty': adjusted_novelty,
                'inventive': adjusted_inventive,
                'overall': overall_score
            },
            'domain_specific_factors': self._get_domain_factors(domain, patent_data)
        }

    def _identify_patent_domain(self, patent_data: dict[str, Any]) -> PatentDomain:
        """识别专利领域"""
        technical_field = patent_data.get('technical_field', '').lower()
        title = patent_data.get('title', '').lower()
        abstract = patent_data.get('abstract', '').lower()

        # 关键词映射
        domain_keywords = {
            PatentDomain.MECHANICAL: ['mechanical', 'machine', 'device', 'apparatus', 'structure'],
            PatentDomain.ELECTRICAL: ['electrical', 'circuit', 'electronic', 'voltage', 'current'],
            PatentDomain.SOFTWARE: ['software', 'algorithm', 'program', 'computer', 'digital'],
            PatentDomain.CHEMICAL: ['chemical', 'compound', 'composition', 'reaction', 'molecule'],
            PatentDomain.BIOMEDICAL: ['medical', 'biological', 'pharmaceutical', 'gene', 'protein'],
            PatentDomain.TELECOMM: ['communication', 'network', 'wireless', 'signal', 'transmission'],
            PatentDomain.MATERIAL: ['material', 'polymer', 'metal', 'ceramic', 'composite']
        }

        # 计算每个领域的匹配分数
        domain_scores = {}
        for domain, keywords in domain_keywords.items():
            score = 0
            for keyword in keywords:
                if keyword in technical_field or keyword in title or keyword in abstract:
                    score += 1
            domain_scores[domain] = score

        # 返回得分最高的领域
        if max(domain_scores.values()) == 0:
            return PatentDomain.OTHER

        return max(domain_scores, key=domain_scores.get)

    def _get_domain_factors(self, domain: PatentDomain, patent_data: dict[str, Any]) -> dict[str, float]:
        """获取领域特定因素"""
        # 根据不同领域返回特定的评估因素
        if domain == PatentDomain.SOFTWARE:
            return {
                'algorithm_complexity': patent_data.get('algorithm_complexity', 0.5),
                'innovation_level': patent_data.get('innovation_level', 0.5),
                'implementation_difficulty': patent_data.get('implementation_difficulty', 0.5)
            }
        elif domain == PatentDomain.BIOMEDICAL:
            return {
                'clinical_significance': patent_data.get('clinical_significance', 0.5),
                'safety_profile': patent_data.get('safety_profile', 0.5),
                'regulatory_pathway': patent_data.get('regulatory_pathway', 0.5)
            }
        else:
            return {
                'manufacturing_feasibility': patent_data.get('manufacturing_feasibility', 0.5),
                'cost_effectiveness': patent_data.get('cost_effectiveness', 0.5),
                'market_acceptance': patent_data.get('market_acceptance', 0.5)
            }

    def _assess_risks(self,
                     patent_data: dict[str, Any],
                     metrics: DecisionMetrics,
                     reasoning_result: ReasoningResult) -> dict[str, float]:
        """评估风险"""
        risks = {
            'novelty_risk': metrics.prior_art_risk,
            'inventive_risk': 1 - metrics.inventive_score,
            'legal_risk': 1 - metrics.legal_compliance,
            'technical_risk': 1 - metrics.technical_merit,
            'commercial_risk': 1 - metrics.commercial_value,
            'infringement_risk': metrics.infringement_risk
        }

        # 基于推理结果调整风险
        if reasoning_result.conflicts_detected:
            risks['conflict_risk'] = len(reasoning_result.conflicts_detected) * 0.1

        # 计算综合风险分数
        risks['overall_risk'] = np.mean(list(risks.values()))

        return risks

    def _generate_decision_level(self,
                                metrics: DecisionMetrics,
                                reasoning_result: ReasoningResult,
                                domain_analysis: dict[str, Any]) -> tuple[DecisionLevel, float]:
        """生成决策级别"""
        # 计算综合分数
        scores = {
            'novelty': metrics.novelty_score,
            'inventive': metrics.inventive_score,
            'practical': metrics.practical_score,
            'technical': metrics.technical_merit,
            'legal': metrics.legal_compliance,
            'domain_overall': domain_analysis['adjusted_scores']['overall']
        }

        # 加权计算总分数
        weights = {
            'novelty': 0.25,
            'inventive': 0.25,
            'practical': 0.15,
            'technical': 0.15,
            'legal': 0.1,
            'domain_overall': 0.1
        }

        total_score = sum(scores[key] * weights[key] for key in scores)

        # 结合推理结果的置信度
        combined_confidence = (total_score + reasoning_result.confidence) / 2

        # 确定决策级别
        if combined_confidence >= 0.9:
            decision = DecisionLevel.STRONG_APPROVE
        elif combined_confidence >= 0.8:
            decision = DecisionLevel.APPROVE
        elif combined_confidence >= 0.6:
            decision = DecisionLevel.WEAK_APPROVE
        elif combined_confidence >= 0.4:
            decision = DecisionLevel.REJECT
        else:
            decision = DecisionLevel.STRONG_REJECT

        return decision, combined_confidence

    def _generate_recommendations(self,
                                 decision_level: DecisionLevel,
                                 metrics: DecisionMetrics,
                                 reasoning_result: ReasoningResult) -> list[str]:
        """生成建议"""
        recommendations = []

        # 基于决策级别的建议
        if decision_level in [DecisionLevel.STRONG_APPROVE, DecisionLevel.APPROVE]:
            recommendations.extend([
                '建议授予专利权',
                '技术方案具有显著创新性',
                '符合专利授权条件'
            ])
        elif decision_level == DecisionLevel.WEAK_APPROVE:
            recommendations.extend([
                '可以考虑授权，需要进一步审查',
                '建议补充技术细节',
                '关注现有技术对比'
            ])
        else:
            recommendations.extend([
                '建议驳回专利申请',
                '技术方案不满足授权条件',
                '需要改进技术方案'
            ])

        # 基于具体指标的建议
        if metrics.novelty_score < 0.6:
            recommendations.append('新颖性不足，建议进行更全面的现有技术检索')

        if metrics.inventive_score < 0.6:
            recommendations.append('创造性不足，建议突出技术方案的进步性')

        if metrics.practical_score < 0.6:
            recommendations.append('实用性存疑，建议提供可实施的具体方案')

        # 基于推理结果的建议
        if reasoning_result.conflicts_detected:
            recommendations.append(f"存在{len(reasoning_result.conflicts_detected)}个规则冲突，需要进一步分析")

        return recommendations

    def _collect_evidence(self,
                         patent_data: dict[str, Any],
                         reasoning_result: ReasoningResult,
                         metrics: DecisionMetrics) -> tuple[list[str], list[str]]:
        """收集支持性和反对性证据"""
        supporting = []
        opposing = []

        # 支持性证据
        if metrics.novelty_score > 0.7:
            supporting.append(f"新颖性分数高({metrics.novelty_score:.2f})")

        if metrics.inventive_score > 0.7:
            supporting.append(f"创造性分数高({metrics.inventive_score:.2f})")

        if metrics.practical_score > 0.8:
            supporting.append(f"实用性分数高({metrics.practical_score:.2f})")

        if reasoning_result.confidence > 0.8:
            supporting.append(f"推理置信度高({reasoning_result.confidence:.2f})")

        # 反对性证据
        if metrics.novelty_score < 0.5:
            opposing.append(f"新颖性分数低({metrics.novelty_score:.2f})")

        if metrics.inventive_score < 0.5:
            opposing.append(f"创造性分数低({metrics.inventive_score:.2f})")

        if metrics.legal_compliance < 0.6:
            opposing.append(f"法律合规性不足({metrics.legal_compliance:.2f})")

        if reasoning_result.conflicts_detected:
            opposing.append(f"存在{len(reasoning_result.conflicts_detected)}个规则冲突")

        return supporting, opposing

    def _generate_decision_summary(self, decision_level: DecisionLevel, confidence: float) -> str:
        """生成决策摘要"""
        level_descriptions = {
            DecisionLevel.STRONG_APPROVE: '强烈推荐授权',
            DecisionLevel.APPROVE: '推荐授权',
            DecisionLevel.WEAK_APPROVE: '谨慎推荐授权',
            DecisionLevel.REJECT: '建议驳回',
            DecisionLevel.STRONG_REJECT: '强烈建议驳回'
        }

        return f"{level_descriptions[decision_level]}，置信度: {confidence:.2f}"

    def _update_performance_metrics(self, decision: CognitiveDecision):
        """更新性能指标"""
        self.performance_metrics['total_decisions'] += 1

        # 更新平均置信度
        current_avg = self.performance_metrics['average_confidence']
        total = self.performance_metrics['total_decisions']
        self.performance_metrics['average_confidence'] = (
            (current_avg * (total - 1) + decision.confidence_score) / total
        )

        # 更新平均处理时间
        current_time_avg = self.performance_metrics['processing_time_avg']
        self.performance_metrics['processing_time_avg'] = (
            (current_time_avg * (total - 1) + decision.processing_time) / total
        )

        # 更新决策分布
        level_name = decision.decision_level.name
        self.performance_metrics['decision_distribution'][level_name] += 1

    def get_decision_statistics(self) -> dict[str, Any]:
        """获取决策统计信息"""
        total = self.performance_metrics['total_decisions']
        if total == 0:
            return {}

        # 计算决策分布百分比
        distribution_pct = {}
        for level, count in self.performance_metrics['decision_distribution'].items():
            distribution_pct[level] = (count / total) * 100 if total > 0 else 0

        return {
            'total_decisions': total,
            'average_confidence': self.performance_metrics['average_confidence'],
            'average_processing_time': self.performance_metrics['processing_time_avg'],
            'decision_distribution': self.performance_metrics['decision_distribution'],
            'decision_distribution_pct': distribution_pct,
            'most_common_decision': max(distribution_pct, key=distribution_pct.get) if distribution_pct else None
        }

    def export_decision_history(self, file_path: str, limit: int | None = None):
        """导出决策历史"""
        history_to_export = self.decision_history[-limit:] if limit else self.decision_history

        exported_data = []
        for decision in history_to_export:
            exported_data.append({
                'patent_id': decision.patent_id,
                'decision_level': decision.decision_level.name,
                'confidence': decision.confidence_score,
                'processing_time': decision.processing_time,
                'timestamp': decision.timestamp.isoformat(),
                'summary': decision.decision_summary,
                'recommendations': decision.recommendations
            })

        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(exported_data, f, ensure_ascii=False, indent=2)

        logger.info(f"📄 决策历史已导出到: {file_path}，共 {len(exported_data)} 条记录")

async def main():
    """主函数"""
    logger.info('🧠 认知决策管理器测试')
    logger.info('Athena + 小诺 为您服务~ 💖')
    logger.info(str('='*50))

    manager = CognitiveDecisionManager()

    # 测试用例
    test_patents = [
        {
            'patent_id': 'CN202512050001',
            'title': '基于人工智能的专利分析系统',
            'abstract': '本发明提供一种基于深度学习的智能专利分析系统',
            'technical_field': '人工智能',
            'patent_type': 'invention',
            'novelty_score': 0.85,
            'inventive_score': 0.78,
            'practical_score': 0.92,
            'market_size': 0.8,
            'industry_growth': 0.7,
            'eligibility': True,
            'complete_disclosure': True
        },
        {
            'patent_id': 'CN202512050002',
            'title': '一种传统的机械装置',
            'abstract': '本发明涉及一种常见的机械设备改进',
            'technical_field': '机械工程',
            'patent_type': 'invention',
            'novelty_score': 0.45,
            'inventive_score': 0.38,
            'practical_score': 0.85,
            'market_size': 0.4,
            'eligibility': True,
            'complete_disclosure': True
        }
    ]

    # 处理测试专利
    for i, patent in enumerate(test_patents, 1):
        logger.info(f"\n📋 测试专利 {i}: {patent['title']}")
        logger.info(str('-' * 50))

        try:
            decision = await manager.make_decision(patent)

            logger.info(f"决策级别: {decision.decision_level.name}")
            logger.info(f"决策摘要: {decision.decision_summary}")
            logger.info(f"置信度: {decision.confidence_score:.2f}")
            logger.info(f"处理时间: {decision.processing_time:.2f}秒")

            logger.info("\n风险评估:")
            for risk, value in decision.risk_assessment.items():
                logger.info(f"  {risk}: {value:.2f}")

            logger.info("\n主要建议:")
            for rec in decision.recommendations[:3]:
                logger.info(f"  - {rec}")

        except Exception as e:
            logger.info(f"❌ 处理失败: {e}")

    # 统计信息
    stats = manager.get_decision_statistics()
    if stats:
        logger.info("\n📊 决策统计:")
        logger.info(f"总决策数: {stats['total_decisions']}")
        logger.info(f"平均置信度: {stats['average_confidence']:.2f}")
        logger.info(f"平均处理时间: {stats['average_processing_time']:.2f}秒")
        logger.info(f"最常见决策: {stats['most_common_decision']}")

    # 导出结果
    manager.export_decision_history('cognitive_decisions_history.json')
    logger.info("\n✅ 测试完成！决策历史已导出")

if __name__ == '__main__':
    asyncio.run(main())
