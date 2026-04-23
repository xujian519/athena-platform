#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
专利评估与反思系统
Patent Evaluation and Reflection System

基于Athena工作平台现有的评估与反思基础设施，
为专利应用提供专门的多维度评估和智能反思能力。

Created by Athena + 小诺 (AI助手)
Date: 2025-12-05
"""

import asyncio
import json
import logging
import sqlite3
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class EvaluationType(Enum):
    """评估类型"""
    PATENTABILITY = 'patentability'
    COMMERCIAL_VALUE = 'commercial_value'
    TECHNICAL_ASSESSMENT = 'technical_assessment'
    LEGAL_STABILITY = 'legal_stability'
    MARKET_POTENTIAL = 'market_potential'
    RISK_ANALYSIS = 'risk_analysis'
    COMPETITIVE_POSITION = 'competitive_position'
    INVESTMENT_RETURN = 'investment_return'

class EvaluationLevel(Enum):
    """评估等级"""
    EXCELLENT = 'excellent'
    GOOD = 'good'
    AVERAGE = 'average'
    POOR = 'poor'
    VERY_POOR = 'very_poor'

class ReflectionType(Enum):
    """反思类型"""
    PROCESS_IMPROVEMENT = 'process_improvement'
    DECISION_REVIEW = 'decision_review'
    LESSON_LEARNED = 'lesson_learned'
    STRATEGY_ADJUSTMENT = 'strategy_adjustment'
    PERFORMANCE_ANALYSIS = 'performance_analysis'
    ERROR_ANALYSIS = 'error_analysis'

@dataclass
class PatentEvaluationCriteria:
    """专利评估标准"""
    criterion_id: str
    name: str
    description: str
    weight: float  # 权重 0.0-1.0
    evaluation_method: str  # 评估方法
    target_value: float  # 目标值
    current_value: float = 0.0
    score: float = 0.0  # 得分 0-100
    comments: str = ''
    evidence: List[Dict[str, Any]] = field(default_factory=list)

@dataclass
class PatentEvaluationResult:
    """专利评估结果"""
    evaluation_id: str
    patent_id: str
    evaluation_type: EvaluationType
    criteria_scores: Dict[str, float] = field(default_factory=dict)
    overall_score: float = 0.0
    evaluation_level: EvaluationLevel = EvaluationLevel.AVERAGE
    strengths: List[str] = field(default_factory=list)
    weaknesses: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    confidence_level: float = 0.0
    evaluator: str = ''
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class PatentReflection:
    """专利反思记录"""
    reflection_id: str
    patent_id: str
    evaluation_id: str
    reflection_type: ReflectionType
    what_happened: str  # 发生了什么
    why_it_happened: str  # 为什么发生
    what_we_learned: str  # 学到了什么
    what_to_do_next: str  # 下一步做什么
    action_items: List[Dict[str, Any]] = field(default_factory=list)
    impact_assessment: str = ''
    success_factors: List[str] = field(default_factory=list)
    improvement_opportunities: List[str] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.now)
    follow_up_required: bool = False
    follow_up_deadline: datetime | None = None

class PatentEvaluationReflectionSystem:
    """专利评估与反思系统"""

    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.PatentEvaluationReflectionSystem")

        # 评估配置
        self.evaluation_frameworks = self._init_evaluation_frameworks()

        # 评估结果存储
        self.evaluation_results: Dict[str, PatentEvaluationResult] = {}
        self.reflection_records: Dict[str, PatentReflection] = {}

        # AI家庭成员评估专长
        self.ai_family_expertise = {
            'athena': {
                'technical_assessment': 0.9,
                'commercial_value': 0.85,
                'investment_return': 0.9,
                'competitive_position': 0.8
            },
            'xiaona': {
                'patentability': 0.9,
                'legal_stability': 0.95,
                'risk_analysis': 0.85,
                'technical_assessment': 0.8
            },
            'xiaonuo': {
                'market_potential': 0.8,
                'process_improvement': 0.9,
                'performance_analysis': 0.85,
                'strategy_adjustment': 0.8
            }
        }

        # 统计信息
        self.stats = {
            'total_evaluations': 0,
            'evaluations_by_type': {},
            'evaluations_by_level': {},
            'total_reflections': 0,
            'reflections_by_type': {},
            'average_scores': {},
            'improvement_trends': []
        }

        # 数据库路径
        self.db_path = '/Users/xujian/Athena工作平台/data/databases/patent_evaluation.db'

        # 初始化数据库
        self._init_database()

        self.logger.info('专利评估与反思系统初始化完成')

    def _init_database(self):
        """初始化数据库"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # 创建评估结果表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS patent_evaluation_results (
                    evaluation_id TEXT PRIMARY KEY,
                    patent_id TEXT,
                    evaluation_type TEXT,
                    criteria_scores TEXT,
                    overall_score REAL,
                    evaluation_level TEXT,
                    strengths TEXT,
                    weaknesses TEXT,
                    recommendations TEXT,
                    confidence_level REAL,
                    evaluator TEXT,
                    timestamp TEXT,
                    metadata TEXT
                )
            ''')

            # 创建反思记录表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS patent_reflections (
                    reflection_id TEXT PRIMARY KEY,
                    patent_id TEXT,
                    evaluation_id TEXT,
                    reflection_type TEXT,
                    what_happened TEXT,
                    why_it_happened TEXT,
                    what_we_learned TEXT,
                    what_to_do_next TEXT,
                    action_items TEXT,
                    impact_assessment TEXT,
                    success_factors TEXT,
                    improvement_opportunities TEXT,
                    timestamp TEXT,
                    follow_up_required INTEGER,
                    follow_up_deadline TEXT
                )
            ''')

            conn.commit()
            conn.close()

            self.logger.info('专利评估数据库初始化完成')

        except Exception as e:
            self.logger.error(f"数据库初始化失败: {str(e)}")

    def _init_evaluation_frameworks(self) -> Dict[EvaluationType, List[PatentEvaluationCriteria]]:
        """初始化评估框架"""
        frameworks = {}

        # 专利性评估框架
        frameworks[EvaluationType.PATENTABILITY] = [
            PatentEvaluationCriteria(
                criterion_id='novelty',
                name='新颖性',
                description='申请日以前没有同样的发明在国内外出版物上公开发表过',
                weight=0.35,
                evaluation_method='prior_art_analysis',
                target_value=0.8
            ),
            PatentEvaluationCriteria(
                criterion_id='inventiveness',
                name='创造性',
                description='同现有技术相比，具有突出的实质性特点和显著进步',
                weight=0.40,
                evaluation_method='technical_advancement_analysis',
                target_value=0.7
            ),
            PatentEvaluationCriteria(
                criterion_id='industrial_applicability',
                name='实用性',
                description='能够制造或使用，并产生积极效果',
                weight=0.25,
                evaluation_method='practicality_assessment',
                target_value=0.9
            )
        ]

        # 商业价值评估框架
        frameworks[EvaluationType.COMMERCIAL_VALUE] = [
            PatentEvaluationCriteria(
                criterion_id='market_size',
                name='市场规模',
                description='目标市场的规模和增长潜力',
                weight=0.25,
                evaluation_method='market_analysis',
                target_value=0.8
            ),
            PatentEvaluationCriteria(
                criterion_id='competitive_advantage',
                name='竞争优势',
                description='相对于现有技术的优势程度',
                weight=0.30,
                evaluation_method='competitive_analysis',
                target_value=0.7
            ),
            PatentEvaluationCriteria(
                criterion_id='commercialization_feasibility',
                name='商业化可行性',
                description='技术实现和商业化的可行性',
                weight=0.25,
                evaluation_method='feasibility_analysis',
                target_value=0.8
            ),
            PatentEvaluationCriteria(
                criterion_id='intellectual_property_strength',
                name='知识产权强度',
                description='专利的保护范围和稳定性',
                weight=0.20,
                evaluation_method='ip_analysis',
                target_value=0.8
            )
        ]

        # 技术评估框架
        frameworks[EvaluationType.TECHNICAL_ASSESSMENT] = [
            PatentEvaluationCriteria(
                criterion_id='technical_innovation',
                name='技术创新性',
                description='技术方案的创新程度和突破性',
                weight=0.35,
                evaluation_method='innovation_analysis',
                target_value=0.8
            ),
            PatentEvaluationCriteria(
                criterion_id='technical_maturity',
                name='技术成熟度',
                description='技术方案的成熟程度和实现难度',
                weight=0.25,
                evaluation_method='maturity_assessment',
                target_value=0.7
            ),
            PatentEvaluationCriteria(
                criterion_id='scalability',
                name='可扩展性',
                description='技术方案的扩展能力和适应性',
                weight=0.20,
                evaluation_method='scalability_analysis',
                target_value=0.8
            ),
            PatentEvaluationCriteria(
                criterion_id='technical_risk',
                name='技术风险',
                description='技术实现过程中的风险因素',
                weight=0.20,
                evaluation_method='risk_assessment',
                target_value=0.3  # 风险越低越好
            )
        ]

        # 法律稳定性评估框架
        frameworks[EvaluationType.LEGAL_STABILITY] = [
            PatentEvaluationCriteria(
                criterion_id='claim_scope',
                name='权利要求范围',
                description='权利要求的合理性和稳定性',
                weight=0.30,
                evaluation_method='claim_analysis',
                target_value=0.8
            ),
            PatentEvaluationCriteria(
                criterion_id='disclosure_completeness',
                name='公开充分性',
                description='说明书对技术方案的完整公开',
                weight=0.25,
                evaluation_method='disclosure_analysis',
                target_value=0.9
            ),
            PatentEvaluationCriteria(
                criterion_id='prior_art_handling',
                name='现有技术处理',
                description='对现有技术的引用和区分',
                weight=0.25,
                evaluation_method='prior_art_review',
                target_value=0.8
            ),
            PatentEvaluationCriteria(
                criterion_id='support_relationship',
                name='支持关系',
                description='权利要求与说明书的支持关系',
                weight=0.20,
                evaluation_method='support_analysis',
                target_value=0.9
            )
        ]

        # 市场潜力评估框架
        frameworks[EvaluationType.MARKET_POTENTIAL] = [
            PatentEvaluationCriteria(
                criterion_id='market_demand',
                name='市场需求',
                description='市场对该技术的需求程度',
                weight=0.30,
                evaluation_method='demand_analysis',
                target_value=0.8
            ),
            PatentEvaluationCriteria(
                criterion_id='growth_potential',
                name='增长潜力',
                description='市场的发展潜力和增长速度',
                weight=0.25,
                evaluation_method='growth_analysis',
                target_value=0.8
            ),
            PatentEvaluationCriteria(
                criterion_id='market_timing',
                name='市场时机',
                description='进入市场的时间点是否合适',
                weight=0.25,
                evaluation_method='timing_analysis',
                target_value=0.8
            ),
            PatentEvaluationCriteria(
                criterion_id='competition_level',
                name='竞争程度',
                description='市场竞争的激烈程度',
                weight=0.20,
                evaluation_method='competition_analysis',
                target_value=0.5  # 竞争适中为佳
            )
        ]

        # 风险分析评估框架
        frameworks[EvaluationType.RISK_ANALYSIS] = [
            PatentEvaluationCriteria(
                criterion_id='infringement_risk',
                name='侵权风险',
                description='侵犯他人专利权的风险',
                weight=0.30,
                evaluation_method='infringement_analysis',
                target_value=0.2  # 风险越低越好
            ),
            PatentEvaluationCriteria(
                criterion_id='invalidation_risk',
                name='无效风险',
                description='专利被无效的风险',
                weight=0.25,
                evaluation_method='invalidation_analysis',
                target_value=0.2
            ),
            PatentEvaluationCriteria(
                criterion_id='enforceability_risk',
                name='执行风险',
                description='专利执行和维权的风险',
                weight=0.25,
                evaluation_method='enforceability_analysis',
                target_value=0.3
            ),
            PatentEvaluationCriteria(
                criterion_id='technology_obsolescence',
                name='技术过时风险',
                description='技术被淘汰的风险',
                weight=0.20,
                evaluation_method='obsolescence_analysis',
                target_value=0.3
            )
        ]

        # 竞争地位评估框架
        frameworks[EvaluationType.COMPETITIVE_POSITION] = [
            PatentEvaluationCriteria(
                criterion_id='technology_leadership',
                name='技术领导地位',
                description='在技术领域中的领先程度',
                weight=0.30,
                evaluation_method='leadership_analysis',
                target_value=0.7
            ),
            PatentEvaluationCriteria(
                criterion_id='patent_portfolio_strength',
                name='专利组合强度',
                description='相关专利组合的整体实力',
                weight=0.25,
                evaluation_method='portfolio_analysis',
                target_value=0.8
            ),
            PatentEvaluationCriteria(
                criterion_id='market_position',
                name='市场地位',
                description='在目标市场中的地位',
                weight=0.25,
                evaluation_method='position_analysis',
                target_value=0.7
            ),
            PatentEvaluationCriteria(
                criterion_id='entry_barriers',
                name='进入壁垒',
                description='为竞争对手设置的壁垒',
                weight=0.20,
                evaluation_method='barrier_analysis',
                target_value=0.8
            )
        ]

        # 投资回报评估框架
        frameworks[EvaluationType.INVESTMENT_RETURN] = [
            PatentEvaluationCriteria(
                criterion_id='roi_potential',
                name='投资回报潜力',
                description='预期的投资回报率',
                weight=0.35,
                evaluation_method='roi_analysis',
                target_value=0.8
            ),
            PatentEvaluationCriteria(
                criterion_id='time_to_profit',
                name='盈利时间',
                description='从投资到盈利的时间',
                weight=0.25,
                evaluation_method='profit_timeline_analysis',
                target_value=0.7
            ),
            PatentEvaluationCriteria(
                criterion_id='cost_benefit_ratio',
                name='成本效益比',
                description='研发成本与预期收益的比例',
                weight=0.25,
                evaluation_method='cost_benefit_analysis',
                target_value=0.8
            ),
            PatentEvaluationCriteria(
                criterion_id='risk_adjusted_return',
                name='风险调整后回报',
                description='考虑风险后的预期回报',
                weight=0.15,
                evaluation_method='risk_adjusted_analysis',
                target_value=0.7
            )
        ]

        return frameworks

    async def evaluate_patent(self,
                             patent_id: str,
                             evaluation_type: EvaluationType,
                             criteria_data: Dict[str, float],
                             evaluator: str,
                             **kwargs) -> PatentEvaluationResult:
        """评估专利"""
        try:
            self.logger.info(f"开始评估专利: {patent_id} - {evaluation_type.value}")

            # 生成评估ID
            evaluation_id = f"eval_{patent_id}_{evaluation_type.value}_{int(time.time())}"

            # 获取评估框架
            framework = self.evaluation_frameworks.get(evaluation_type, [])

            if not framework:
                raise ValueError(f"未找到评估类型 {evaluation_type.value} 的框架")

            # 更新标准数据
            for criterion in framework:
                if criterion.criterion_id in criteria_data:
                    criterion.current_value = criteria_data[criterion.criterion_id]
                    # 计算得分 (基于与目标值的对比)
                    if criterion.evaluation_method == 'risk_assessment':
                        # 风险类指标：越低越好
                        criterion.score = max(0, 100 * (1 - criterion.current_value / criterion.target_value))
                    else:
                        # 收益类指标：越高越好
                        criterion.score = min(100, 100 * criterion.current_value / criterion.target_value)
                else:
                    # 使用默认分数
                    criterion.score = 50

            # 计算总体得分
            overall_score = 0.0
            criteria_scores = {}

            for criterion in framework:
                weighted_score = criterion.score * criterion.weight
                overall_score += weighted_score
                criteria_scores[criterion.criterion_id] = criterion.score

            # 确定评估等级
            evaluation_level = self._determine_evaluation_level(overall_score)

            # 生成优劣势分析
            strengths, weaknesses, recommendations = self._generate_evaluation_analysis(
                framework, criteria_scores
            )

            # 计算置信度
            confidence_level = self._calculate_confidence_level(framework, criteria_scores, evaluator)

            # 创建评估结果
            result = PatentEvaluationResult(
                evaluation_id=evaluation_id,
                patent_id=patent_id,
                evaluation_type=evaluation_type,
                criteria_scores=criteria_scores,
                overall_score=overall_score,
                evaluation_level=evaluation_level,
                strengths=strengths,
                weaknesses=weaknesses,
                recommendations=recommendations,
                confidence_level=confidence_level,
                evaluator=evaluator,
                metadata={
                    'framework_version': '1.0',
                    'evaluation_method': 'weighted_criteria',
                    'data_completeness': len(criteria_data) / len(framework)
                }
            )

            # 存储评估结果
            self.evaluation_results[evaluation_id] = result
            await self._store_evaluation_result(result)

            # 更新统计
            self._update_evaluation_stats(result)

            self.logger.info(f"专利评估完成: {patent_id} - 总分: {overall_score:.2f}")
            return result

        except Exception as e:
            self.logger.error(f"专利评估失败: {str(e)}")
            raise

    def _determine_evaluation_level(self, overall_score: float) -> EvaluationLevel:
        """确定评估等级"""
        if overall_score >= 90:
            return EvaluationLevel.EXCELLENT
        elif overall_score >= 80:
            return EvaluationLevel.GOOD
        elif overall_score >= 70:
            return EvaluationLevel.AVERAGE
        elif overall_score >= 60:
            return EvaluationLevel.POOR
        else:
            return EvaluationLevel.VERY_POOR

    def _generate_evaluation_analysis(self,
                                    framework: List[PatentEvaluationCriteria],
                                    criteria_scores: Dict[str, float]) -> Tuple[List[str], List[str], List[str]]:
        """生成评估分析"""
        strengths = []
        weaknesses = []
        recommendations = []

        for criterion in framework:
            score = criteria_scores.get(criterion.criterion_id, 0)

            if score >= 80:
                strengths.append(f"{criterion.name}表现优秀 ({score:.1f}分)")
            elif score >= 60:
                strengths.append(f"{criterion.name}表现良好 ({score:.1f}分)")
            else:
                weaknesses.append(f"{criterion.name}需要改进 ({score:.1f}分)")

        # 生成建议
        for criterion in framework:
            score = criteria_scores.get(criterion.criterion_id, 0)
            if score < 70:
                recommendations.append(f"建议重点提升{criterion.name}，当前得分为{score:.1f}分")

        if not recommendations:
            recommendations.append('各项指标表现良好，继续保持')

        return strengths, weaknesses, recommendations

    def _calculate_confidence_level(self,
                                  framework: List[PatentEvaluationCriteria],
                                  criteria_scores: Dict[str, float],
                                  evaluator: str) -> float:
        """计算评估置信度"""
        try:
            # 基于评估员专长
            expertise_bonus = self.ai_family_expertise.get(evaluator, {}).get('technical_assessment', 0.5)

            # 基于数据完整性
            completeness = len(criteria_scores) / len(framework)

            # 基于得分一致性
            scores = list(criteria_scores.values())
            if scores:
                score_std = np.std(scores)
                consistency = max(0, 1 - score_std / 50)  # 标准差越小，一致性越高
            else:
                consistency = 0

            # 综合计算置信度
            confidence_level = (expertise_bonus * 0.4 + completeness * 0.3 + consistency * 0.3)

            return min(1.0, confidence_level)

        except Exception as e:
            self.logger.error(f"计算置信度失败: {str(e)}")
            return 0.5

    async def _store_evaluation_result(self, result: PatentEvaluationResult):
        """存储评估结果"""
        try:
            # 数据库存储
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute('''
                INSERT INTO patent_evaluation_results
                (evaluation_id, patent_id, evaluation_type, criteria_scores,
                 overall_score, evaluation_level, strengths, weaknesses,
                 recommendations, confidence_level, evaluator, timestamp, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                result.evaluation_id,
                result.patent_id,
                result.evaluation_type.value,
                json.dumps(result.criteria_scores, ensure_ascii=False),
                result.overall_score,
                result.evaluation_level.value,
                json.dumps(result.strengths, ensure_ascii=False),
                json.dumps(result.weaknesses, ensure_ascii=False),
                json.dumps(result.recommendations, ensure_ascii=False),
                result.confidence_level,
                result.evaluator,
                result.timestamp.isoformat(),
                json.dumps(result.metadata, ensure_ascii=False)
            ))

            conn.commit()
            conn.close()

        except Exception as e:
            self.logger.error(f"存储评估结果失败: {str(e)}")

    def _update_evaluation_stats(self, result: PatentEvaluationResult):
        """更新评估统计"""
        self.stats['total_evaluations'] += 1

        # 按类型统计
        eval_type = result.evaluation_type.value
        self.stats['evaluations_by_type'][eval_type] = \
            self.stats['evaluations_by_type'].get(eval_type, 0) + 1

        # 按等级统计
        eval_level = result.evaluation_level.value
        self.stats['evaluations_by_level'][eval_level] = \
            self.stats['evaluations_by_level'].get(eval_level, 0) + 1

        # 更新平均分
        if eval_type not in self.stats['average_scores']:
            self.stats['average_scores'][eval_type] = []
        self.stats['average_scores'][eval_type].append(result.overall_score)

    async def create_patent_reflection(self,
                                     patent_id: str,
                                     evaluation_id: str,
                                     reflection_type: ReflectionType,
                                     what_happened: str,
                                     why_it_happened: str,
                                     what_we_learned: str,
                                     what_to_do_next: str,
                                     **kwargs) -> PatentReflection:
        """创建专利反思记录"""
        try:
            self.logger.info(f"创建专利反思: {patent_id} - {reflection_type.value}")

            # 生成反思ID
            reflection_id = f"refl_{patent_id}_{reflection_type.value}_{int(time.time())}"

            # 创建反思记录
            reflection = PatentReflection(
                reflection_id=reflection_id,
                patent_id=patent_id,
                evaluation_id=evaluation_id,
                reflection_type=reflection_type,
                what_happened=what_happened,
                why_it_happened=why_it_happened,
                what_we_learned=what_we_learned,
                what_to_do_next=what_to_do_next,
                action_items=kwargs.get('action_items', []),
                impact_assessment=kwargs.get('impact_assessment', ''),
                success_factors=kwargs.get('success_factors', []),
                improvement_opportunities=kwargs.get('improvement_opportunities', []),
                follow_up_required=kwargs.get('follow_up_required', False),
                follow_up_deadline=kwargs.get('follow_up_deadline')
            )

            # 存储反思记录
            self.reflection_records[reflection_id] = reflection
            await self._store_reflection(reflection)

            # 更新统计
            self._update_reflection_stats(reflection)

            self.logger.info(f"专利反思创建成功: {reflection_id}")
            return reflection

        except Exception as e:
            self.logger.error(f"创建专利反思失败: {str(e)}")
            raise

    async def _store_reflection(self, reflection: PatentReflection):
        """存储反思记录"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute('''
                INSERT INTO patent_reflections
                (reflection_id, patent_id, evaluation_id, reflection_type,
                 what_happened, why_it_happened, what_we_learned, what_to_do_next,
                 action_items, impact_assessment, success_factors, improvement_opportunities,
                 timestamp, follow_up_required, follow_up_deadline)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                reflection.reflection_id,
                reflection.patent_id,
                reflection.evaluation_id,
                reflection.reflection_type.value,
                reflection.what_happened,
                reflection.why_it_happened,
                reflection.what_we_learned,
                reflection.what_to_do_next,
                json.dumps(reflection.action_items, ensure_ascii=False),
                reflection.impact_assessment,
                json.dumps(reflection.success_factors, ensure_ascii=False),
                json.dumps(reflection.improvement_opportunities, ensure_ascii=False),
                reflection.timestamp.isoformat(),
                int(reflection.follow_up_required),
                reflection.follow_up_deadline.isoformat() if reflection.follow_up_deadline else None
            ))

            conn.commit()
            conn.close()

        except Exception as e:
            self.logger.error(f"存储反思记录失败: {str(e)}")

    def _update_reflection_stats(self, reflection: PatentReflection):
        """更新反思统计"""
        self.stats['total_reflections'] += 1

        # 按类型统计
        refl_type = reflection.reflection_type.value
        self.stats['reflections_by_type'][refl_type] = \
            self.stats['reflections_by_type'].get(refl_type, 0) + 1

    async def get_comprehensive_patent_assessment(self,
                                                 patent_id: str,
                                                 evaluation_types: Optional[List[EvaluationType]] = None) -> Dict[str, Any]]:
        """获取专利综合评估"""
        try:
            if evaluation_types is None:
                evaluation_types = list(EvaluationType)

            self.logger.info(f"生成专利综合评估: {patent_id}")

            # 查找相关评估结果
            patent_evaluations = []
            for eval_result in self.evaluation_results.values():
                if eval_result.patent_id == patent_id and eval_result.evaluation_type in evaluation_types:
                    patent_evaluations.append(eval_result)

            # 按类型分组
            evaluations_by_type = {}
            for eval_result in patent_evaluations:
                eval_type = eval_result.evaluation_type.value
                evaluations_by_type[eval_type] = eval_result

            # 计算综合得分
            overall_scores = [eval.overall_score for eval in patent_evaluations]
            if overall_scores:
                comprehensive_score = sum(overall_scores) / len(overall_scores)
            else:
                comprehensive_score = 0.0

            # 汇总优劣势
            all_strengths = []
            all_weaknesses = []
            all_recommendations = []

            for eval_result in patent_evaluations:
                all_strengths.extend(eval_result.strengths)
                all_weaknesses.extend(eval_result.weaknesses)
                all_recommendations.extend(eval_result.recommendations)

            # 去重和排序
            unique_strengths = list(set(all_strengths))
            unique_weaknesses = list(set(all_weaknesses))
            unique_recommendations = list(set(all_recommendations))

            # 生成综合建议
            comprehensive_recommendations = self._generate_comprehensive_recommendations(
                evaluations_by_type, comprehensive_score
            )

            return {
                'patent_id': patent_id,
                'comprehensive_score': comprehensive_score,
                'evaluations_count': len(patent_evaluations),
                'evaluations_by_type': evaluations_by_type,
                'overall_strengths': unique_strengths,
                'overall_weaknesses': unique_weaknesses,
                'overall_recommendations': unique_recommendations,
                'comprehensive_recommendations': comprehensive_recommendations,
                'assessment_date': datetime.now().isoformat(),
                'confidence_level': self._calculate_overall_confidence(patent_evaluations)
            }

        except Exception as e:
            self.logger.error(f"生成专利综合评估失败: {str(e)}")
            return {
                'patent_id': patent_id,
                'error': str(e)
            }

    def _generate_comprehensive_recommendations(self,
                                                evaluations_by_type: Dict[str, PatentEvaluationResult],
                                                comprehensive_score: float) -> List[str]:
        """生成综合建议"""
        recommendations = []

        # 基于综合得分的建议
        if comprehensive_score >= 85:
            recommendations.append('专利整体表现优秀，建议积极推进申请和商业化')
        elif comprehensive_score >= 75:
            recommendations.append('专利表现良好，建议优化后继续推进')
        elif comprehensive_score >= 65:
            recommendations.append('专利表现一般，建议重点改进弱点后考虑申请')
        else:
            recommendations.append('专利表现较差，建议重新评估或放弃申请')

        # 基于具体评估类型的建议
        if 'patentability' in evaluations_by_type:
            patentability_score = evaluations_by_type['patentability'].overall_score
            if patentability_score < 70:
                recommendations.append('专利性得分较低，建议加强技术创新性或修改权利要求')

        if 'commercial_value' in evaluations_by_type:
            commercial_score = evaluations_by_type['commercial_value'].overall_score
            if commercial_score < 60:
                recommendations.append('商业价值得分较低，建议重新评估市场定位')

        if 'risk_analysis' in evaluations_by_type:
            risk_score = evaluations_by_type['risk_analysis'].overall_score
            if risk_score < 70:
                recommendations.append('风险分析得分较低，建议进行风险规避措施')

        return recommendations

    def _calculate_overall_confidence(self, evaluations: List[PatentEvaluationResult]) -> float:
        """计算整体置信度"""
        if not evaluations:
            return 0.0

        confidences = [eval.confidence_level for eval in evaluations]
        return sum(confidences) / len(confidences)

    def get_evaluation_statistics(self) -> Dict[str, Any]:
        """获取评估统计信息"""
        stats = self.stats.copy()

        # 计算平均分
        for eval_type, scores in stats['average_scores'].items():
            if scores:
                stats[f"avg_{eval_type}_score"] = sum(scores) / len(scores)

        # 计算改进趋势
        if len(stats['improvement_trends']) > 1:
            recent_trend = stats['improvement_trends'][-1] - stats['improvement_trends'][-2]
            stats['recent_trend'] = 'improving' if recent_trend > 0 else 'declining'
        else:
            stats['recent_trend'] = 'insufficient_data'

        return stats


# 测试代码
async def test_patent_evaluation_reflection_system():
    """测试专利评估与反思系统"""
    system = PatentEvaluationReflectionSystem()

    logger.info(str('=' * 60))
    logger.info('专利评估与反思系统测试')
    logger.info(str('=' * 60))

    # 测试专利性评估
    logger.info("\n1. 专利性评估测试:")
    patentability_data = {
        'novelty': 0.85,
        'inventiveness': 0.78,
        'industrial_applicability': 0.92
    }

    patentability_result = await system.evaluate_patent(
        patent_id='CN202410001234.5',
        evaluation_type=EvaluationType.PATENTABILITY,
        criteria_data=patentability_data,
        evaluator='xiaona'
    )

    logger.info(f"   评估ID: {patentability_result.evaluation_id}")
    logger.info(f"   总体得分: {patentability_result.overall_score:.2f}")
    logger.info(f"   评估等级: {patentability_result.evaluation_level.value}")
    logger.info(f"   优势数量: {len(patentability_result.strengths)}")
    logger.info(f"   劣势数量: {len(patentability_result.weaknesses)}")
    logger.info(f"   置信度: {patentability_result.confidence_level:.3f}")

    # 测试商业价值评估
    logger.info("\n2. 商业价值评估测试:")
    commercial_data = {
        'market_size': 0.75,
        'competitive_advantage': 0.68,
        'commercialization_feasibility': 0.82,
        'intellectual_property_strength': 0.70
    }

    commercial_result = await system.evaluate_patent(
        patent_id='CN202410001234.5',
        evaluation_type=EvaluationType.COMMERCIAL_VALUE,
        criteria_data=commercial_data,
        evaluator='athena'
    )

    logger.info(f"   总体得分: {commercial_result.overall_score:.2f}")
    logger.info(f"   评估等级: {commercial_result.evaluation_level.value}")

    # 测试反思记录
    logger.info("\n3. 反思记录测试:")
    reflection = await system.create_patent_reflection(
        patent_id='CN202410001234.5',
        evaluation_id=patentability_result.evaluation_id,
        reflection_type=ReflectionType.LESSON_LEARNED,
        what_happened='专利性评估显示创造性得分较低',
        why_it_happened='技术创新性不够突出，与现有技术差异较小',
        what_we_learned='需要加强技术创新点的描述和差异化',
        what_to_do_next='重新撰写权利要求，突出创新特征',
        action_items=[
            {'action': '修改权利要求', 'deadline': '2025-12-10', 'responsible': 'xiaona'},
            {'action': '补充技术对比', 'deadline': '2025-12-08', 'responsible': 'athena'}
        ],
        follow_up_required=True
    )

    logger.info(f"   反思ID: {reflection.reflection_id}")
    logger.info(f"   反思类型: {reflection.reflection_type.value}")
    logger.info(f"   行动项数量: {len(reflection.action_items)}")
    logger.info(f"   需要跟进: {reflection.follow_up_required}")

    # 测试综合评估
    logger.info("\n4. 综合评估测试:")
    comprehensive_assessment = await system.get_comprehensive_patent_assessment(
        patent_id='CN202410001234.5',
        evaluation_types=[EvaluationType.PATENTABILITY, EvaluationType.COMMERCIAL_VALUE]
    )

    logger.info(f"   综合得分: {comprehensive_assessment['comprehensive_score']:.2f}")
    logger.info(f"   评估数量: {comprehensive_assessment['evaluations_count']}")
    logger.info(f"   整体优势: {len(comprehensive_assessment['overall_strengths'])}")
    logger.info(f"   整体劣势: {len(comprehensive_assessment['overall_weaknesses'])}")
    logger.info(f"   综合建议: {len(comprehensive_assessment['comprehensive_recommendations'])}")

    # 测试统计信息
    logger.info("\n5. 评估统计测试:")
    stats = system.get_evaluation_statistics()
    logger.info(f"   总评估数: {stats['total_evaluations']}")
    logger.info(f"   总反思数: {stats['total_reflections']}")
    logger.info(f"   按类型评估: {stats['evaluations_by_type']}")
    logger.info(f"   按等级评估: {stats['evaluations_by_level']}")

    return {
        'patentability_evaluated': True,
        'commercial_evaluated': True,
        'reflection_created': True,
        'comprehensive_generated': True,
        'statistics_collected': True
    }


if __name__ == '__main__':
    asyncio.run(test_patent_evaluation_reflection_system())