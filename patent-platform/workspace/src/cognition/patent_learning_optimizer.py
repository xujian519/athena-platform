#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
专利专用学习优化系统
Patent-Specific Learning Optimization System

基于Athena工作平台现有的学习与适应模块，
为专利应用领域提供专门的智能学习优化能力。

Created by Athena + 小诺 (AI助手)
Date: 2025-12-05
"""

import asyncio
import hashlib
import json
import logging
import sqlite3
import time
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import numpy as np

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@dataclass
class PatentLearningExperience:
    """专利学习经验"""
    experience_id: str
    patent_id: str
    learning_type: str  # case_analysis, rule_application, strategy_optimization, quality_assessment
    input_context: Dict[str, Any]
    action_taken: Dict[str, Any]
    result_outcome: Dict[str, Any]
    success_score: float  # 0.0-1.0
    learning_insights: List[str]
    timestamp: datetime = field(default_factory=datetime.now)
    confidence_level: float = 0.0
    ai_family_member: str = 'unknown'  # athena, xiaona, xiaonuo

@dataclass
class PatentLearningPattern:
    """专利学习模式"""
    pattern_id: str
    pattern_type: str  # successful_strategy, common_failure, optimization_opportunity, quality_indicator
    description: str
    conditions: List[Dict[str, Any]]
    actions: List[Dict[str, Any]]
    success_rate: float
    confidence_score: float
    last_updated: datetime = field(default_factory=datetime.now)
    usage_count: int = 0
    effectiveness_score: float = 0.0

@dataclass
class PatentLearningRequest:
    """专利学习请求"""
    request_id: str
    learning_type: str
    patent_context: Dict[str, Any]
    current_performance: Dict[str, Any]
    learning_goals: List[str]
    ai_family_member: str
    priority: int = 1
    timestamp: datetime = field(default_factory=datetime.now)

class PatentLearningOptimizer:
    """专利学习优化器"""

    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.PatentLearningOptimizer")

        # 数据存储
        self.experiences: Dict[str, PatentLearningExperience] = {}
        self.patterns: Dict[str, PatentLearningPattern] = {}

        # 学习模型参数
        self.learning_weights = {
            'case_analysis': 0.3,
            'rule_application': 0.25,
            'strategy_optimization': 0.25,
            'quality_assessment': 0.2
        }

        # AI家庭成员专利特化权重
        self.ai_family_specialization = {
            'athena': {
                'strategic_analysis': 0.9,
                'technical_evaluation': 0.8,
                'patent_portfolio': 0.85,
                'innovation_assessment': 0.9
            },
            'xiaona': {
                'novelty_analysis': 0.9,
                'inventiveness_assessment': 0.85,
                'legal_interpretation': 0.9,
                'prior_art_search': 0.8
            },
            'xiaonuo': {
                'patent_filing': 0.9,
                'examination_response': 0.85,
                'workflow_optimization': 0.8,
                'quality_control': 0.85
            }
        }

        # 学习效果统计
        self.learning_stats = {
            'total_experiences': 0,
            'successful_learnings': 0,
            'patterns_identified': 0,
            'improvement_rate': 0.0,
            'ai_family_performance': defaultdict(dict)
        }

        # 专利知识集成路径
        self.knowledge_integration_path = '/Users/xujian/Athena工作平台/patent-platform/workspace/src/cognition/patent_knowledge_memory_integration.py'

        # 数据库路径
        self.db_path = '/Users/xujian/Athena工作平台/data/databases/patent_learning.db'

        # 初始化数据库
        self._init_database()

        self.logger.info('专利学习优化器初始化完成')

    def _init_database(self):
        """初始化数据库"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # 创建经验表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS patent_learning_experiences (
                    experience_id TEXT PRIMARY KEY,
                    patent_id TEXT,
                    learning_type TEXT,
                    input_context TEXT,
                    action_taken TEXT,
                    result_outcome TEXT,
                    success_score REAL,
                    learning_insights TEXT,
                    timestamp TEXT,
                    confidence_level REAL,
                    ai_family_member TEXT
                )
            ''')

            # 创建模式表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS patent_learning_patterns (
                    pattern_id TEXT PRIMARY KEY,
                    pattern_type TEXT,
                    description TEXT,
                    conditions TEXT,
                    actions TEXT,
                    success_rate REAL,
                    confidence_score REAL,
                    last_updated TEXT,
                    usage_count INTEGER,
                    effectiveness_score REAL
                )
            ''')

            conn.commit()
            conn.close()

            self.logger.info('专利学习数据库初始化完成')

        except Exception as e:
            self.logger.error(f"数据库初始化失败: {str(e)}")

    async def learn_from_patent_analysis(self,
                                       patent_id: str,
                                       analysis_input: Dict[str, Any],
                                       analysis_result: Dict[str, Any],
                                       ai_member: str) -> Dict[str, Any]:
        """从专利分析中学习"""
        self.logger.info(f"从专利分析中学习: {patent_id} by {ai_member}")

        try:
            # 生成经验ID
            experience_id = f"exp_{patent_id}_{ai_member}_{int(time.time())}"

            # 计算学习成功分数
            success_score = self._calculate_analysis_success_score(analysis_result)

            # 提取学习洞察
            learning_insights = self._extract_learning_insights(analysis_input, analysis_result)

            # 创建学习经验
            experience = PatentLearningExperience(
                experience_id=experience_id,
                patent_id=patent_id,
                learning_type='case_analysis',
                input_context=analysis_input,
                action_taken=analysis_result.get('actions', {}),
                result_outcome=analysis_result,
                success_score=success_score,
                learning_insights=learning_insights,
                confidence_level=analysis_result.get('confidence', 0.0),
                ai_family_member=ai_member
            )

            # 存储经验
            await self._store_experience(experience)

            # 更新学习模式
            await self._update_learning_patterns(experience)

            # 更新AI家庭成员性能统计
            self._update_ai_family_performance(ai_member, success_score, 'case_analysis')

            return {
                'success': True,
                'experience_id': experience_id,
                'success_score': success_score,
                'learning_insights_count': len(learning_insights),
                'improvement_suggestions': await self._generate_improvement_suggestions(experience)
            }

        except Exception as e:
            self.logger.error(f"专利分析学习失败: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }

    def _calculate_analysis_success_score(self, analysis_result: Dict[str, Any]) -> float:
        """计算分析成功分数"""
        try:
            score = 0.0

            # 基础分数
            base_score = analysis_result.get('confidence', 0.0) * 0.3

            # 完整性分数
            completeness_keys = ['novelty_assessment', 'inventiveness_assessment', 'industrial_applicability', 'conclusion']
            completeness = sum(1 for key in completeness_keys if key in analysis_result) / len(completeness_keys)
            completeness_score = completeness * 0.3

            # 质量分数
            quality_indicators = [
                analysis_result.get('detailed_analysis', False),
                analysis_result.get('evidence_support', False),
                analysis_result.get('clear_reasoning', False)
            ]
            quality_score = sum(quality_indicators) / len(quality_indicators) * 0.2

            # 一致性分数
            consistency_score = min(1.0, analysis_result.get('logic_consistency', 0.0)) * 0.2

            score = base_score + completeness_score + quality_score + consistency_score

            return min(1.0, max(0.0, score))

        except Exception as e:
            self.logger.error(f"计算成功分数失败: {str(e)}")
            return 0.5  # 默认中等分数

    def _extract_learning_insights(self, input_context: Dict[str, Any],
                                 result_outcome: Dict[str, Any]) -> List[str]:
        """提取学习洞察"""
        insights = []

        try:
            # 分析质量洞察
            confidence = result_outcome.get('confidence', 0.0)
            if confidence > 0.8:
                insights.append('高置信度分析模式：技术特征识别准确')
            elif confidence < 0.6:
                insights.append('低置信度警告：需要更多技术细节支持')

            # 创新性评估洞察
            novelty_score = result_outcome.get('novelty_score', 0.0)
            if novelty_score > 0.8:
                insights.append('高创新性特征：具有突破性技术要素')
            elif novelty_score < 0.4:
                insights.append('创新性不足：建议加强技术差异化')

            # 审查策略洞察
            if 'examination_strategy' in result_outcome:
                strategy = result_outcome['examination_strategy']
                if strategy.get('proactive_claims_adjustment', False):
                    insights.append('主动权利要求调整策略有效')
                if strategy.get('technical_emphasis', False):
                    insights.append('技术优势强调策略提升授权概率')

            # 常见问题洞察
            if 'common_issues' in result_outcome:
                issues = result_outcome['common_issues']
                if issues.get('broad_claims', False):
                    insights.append('权利要求范围过宽：建议进一步限定')
                if issues.get('insufficient_disclosure', False):
                    insights.append('技术公开不充分：需要补充实施例')

            # 最佳实践洞察
            if 'best_practices' in result_outcome:
                practices = result_outcome['best_practices']
                if practices.get('clear_hierarchy', False):
                    insights.append('权利要求层次清晰：有利于审查通过')
                if practices.get('adequate_support', False):
                    insights.append('说明书支持充分：权利要求稳定性高')

        except Exception as e:
            self.logger.error(f"提取学习洞察失败: {str(e)}")
            insights.append('学习洞察提取异常：需要人工审核')

        return insights

    async def _store_experience(self, experience: PatentLearningExperience):
        """存储学习经验"""
        try:
            # 内存存储
            self.experiences[experience.experience_id] = experience
            self.learning_stats['total_experiences'] += 1

            if experience.success_score > 0.7:
                self.learning_stats['successful_learnings'] += 1

            # 数据库存储
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute('''
                INSERT INTO patent_learning_experiences
                (experience_id, patent_id, learning_type, input_context, action_taken,
                 result_outcome, success_score, learning_insights, timestamp,
                 confidence_level, ai_family_member)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                experience.experience_id,
                experience.patent_id,
                experience.learning_type,
                json.dumps(experience.input_context, ensure_ascii=False),
                json.dumps(experience.action_taken, ensure_ascii=False),
                json.dumps(experience.result_outcome, ensure_ascii=False),
                experience.success_score,
                json.dumps(experience.learning_insights, ensure_ascii=False),
                experience.timestamp.isoformat(),
                experience.confidence_level,
                experience.ai_family_member
            ))

            conn.commit()
            conn.close()

            self.logger.debug(f"学习经验已存储: {experience.experience_id}")

        except Exception as e:
            self.logger.error(f"存储学习经验失败: {str(e)}")

    async def _update_learning_patterns(self, experience: PatentLearningExperience):
        """更新学习模式"""
        try:
            # 分析成功模式
            if experience.success_score > 0.8:
                await self._identify_success_pattern(experience)

            # 分析失败模式
            elif experience.success_score < 0.5:
                await self._identify_failure_pattern(experience)

            # 分析优化机会
            await self._identify_optimization_opportunities(experience)

        except Exception as e:
            self.logger.error(f"更新学习模式失败: {str(e)}")

    async def _identify_success_pattern(self, experience: PatentLearningExperience):
        """识别成功模式"""
        pattern_id = f"success_{experience.learning_type}_{hash(experience.patent_id) % 10000}"

        if pattern_id not in self.patterns:
            # 创建新的成功模式
            pattern = PatentLearningPattern(
                pattern_id=pattern_id,
                pattern_type='successful_strategy',
                description=f"成功的{experience.learning_type}模式",
                conditions=[{
                    'patent_type': experience.input_context.get('patent_type', 'unknown'),
                    'technology_field': experience.input_context.get('technology_field', 'unknown'),
                    'ai_member': experience.ai_family_member
                }],
                actions=[{
                    'strategy': experience.action_taken.get('strategy', 'standard'),
                    'key_decisions': experience.result_outcome.get('key_decisions', [])
                }],
                success_rate=1.0,
                confidence_score=experience.confidence_level,
                effectiveness_score=experience.success_score
            )

            self.patterns[pattern_id] = pattern
            self.learning_stats['patterns_identified'] += 1

            # 存储到数据库
            await self._store_pattern(pattern)

            self.logger.info(f"识别成功模式: {pattern_id}")

    async def _identify_failure_pattern(self, experience: PatentLearningExperience):
        """识别失败模式"""
        pattern_id = f"failure_{experience.learning_type}_{hash(experience.patent_id) % 10000}"

        if pattern_id not in self.patterns:
            # 创建新的失败模式
            pattern = PatentLearningPattern(
                pattern_id=pattern_id,
                pattern_type='common_failure',
                description=f"常见的{experience.learning_type}失败模式",
                conditions=[{
                    'patent_type': experience.input_context.get('patent_type', 'unknown'),
                    'technology_field': experience.input_context.get('technology_field', 'unknown'),
                    'ai_member': experience.ai_family_member
                }],
                actions=[{
                    'problematic_strategy': experience.action_taken.get('strategy', 'unknown'),
                    'missing_elements': experience.result_outcome.get('missing_elements', [])
                }],
                success_rate=0.0,
                confidence_score=experience.confidence_level,
                effectiveness_score=experience.success_score
            )

            self.patterns[pattern_id] = pattern
            self.learning_stats['patterns_identified'] += 1

            # 存储到数据库
            await self._store_pattern(pattern)

            self.logger.info(f"识别失败模式: {pattern_id}")

    async def _identify_optimization_opportunities(self, experience: PatentLearningExperience):
        """识别优化机会"""
        # 检查是否可以优化现有模式
        for pattern_id, pattern in self.patterns.items():
            if pattern.pattern_type == 'successful_strategy':
                # 检查是否可以优化成功策略
                if self._is_pattern_applicable(pattern, experience):
                    await self._optimize_existing_pattern(pattern, experience)

    def _is_pattern_applicable(self, pattern: PatentLearningPattern,
                              experience: PatentLearningExperience) -> bool:
        """检查模式是否适用"""
        try:
            # 简化的适用性检查
            if experience.ai_family_member != 'unknown':
                return True
            return False
        except:
            return False

    async def _optimize_existing_pattern(self, pattern: PatentLearningPattern,
                                        experience: PatentLearningExperience):
        """优化现有模式"""
        # 更新模式使用统计
        pattern.usage_count += 1

        # 根据新经验更新模式效果
        if experience.success_score > pattern.effectiveness_score:
            pattern.effectiveness_score = experience.success_score
            pattern.last_updated = datetime.now()

            self.logger.info(f"优化模式: {pattern.pattern_id}")

    async def _store_pattern(self, pattern: PatentLearningPattern):
        """存储学习模式"""
        try:
            # 数据库存储
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute('''
                INSERT OR REPLACE INTO patent_learning_patterns
                (pattern_id, pattern_type, description, conditions, actions,
                 success_rate, confidence_score, last_updated, usage_count, effectiveness_score)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                pattern.pattern_id,
                pattern.pattern_type,
                pattern.description,
                json.dumps(pattern.conditions, ensure_ascii=False),
                json.dumps(pattern.actions, ensure_ascii=False),
                pattern.success_rate,
                pattern.confidence_score,
                pattern.last_updated.isoformat(),
                pattern.usage_count,
                pattern.effectiveness_score
            ))

            conn.commit()
            conn.close()

        except Exception as e:
            self.logger.error(f"存储学习模式失败: {str(e)}")

    def _update_ai_family_performance(self, ai_member: str, success_score: float, learning_type: str):
        """更新AI家庭成员性能统计"""
        if learning_type not in self.learning_stats['ai_family_performance'][ai_member]:
            self.learning_stats['ai_family_performance'][ai_member][learning_type] = []

        self.learning_stats['ai_family_performance'][ai_member][learning_type].append(success_score)

        # 保持最近50次记录
        if len(self.learning_stats['ai_family_performance'][ai_member][learning_type]) > 50:
            self.learning_stats['ai_family_performance'][ai_member][learning_type] = \
                self.learning_stats['ai_family_performance'][ai_member][learning_type][-50:]

    async def _generate_improvement_suggestions(self, experience: PatentLearningExperience) -> List[str]:
        """生成改进建议"""
        suggestions = []

        try:
            # 基于成功分数生成建议
            if experience.success_score < 0.6:
                suggestions.append('建议加强技术细节分析，提高分析完整性')

            # 基于AI家庭成员特化生成建议
            ai_specialization = self.ai_family_specialization.get(experience.ai_family_member, {})

            if experience.ai_family_member == 'athena':
                if experience.success_score < 0.7:
                    suggestions.append('建议雅典娜加强专利战略规划和技术评估能力')
            elif experience.ai_family_member == 'xiaona':
                if experience.success_score < 0.7:
                    suggestions.append('建议小娜加强新颖性分析和法律解释能力')
            elif experience.ai_family_member == 'xiaonuo':
                if experience.success_score < 0.7:
                    suggestions.append('建议小诺加强专利申请流程和质量控制能力')

            # 基于学习类型生成建议
            if experience.learning_type == 'case_analysis':
                if len(experience.learning_insights) < 3:
                    suggestions.append('建议增加案例分析的深度和广度')
            elif experience.learning_type == 'rule_application':
                suggestions.append('建议加强专利规则的具体应用训练')

        except Exception as e:
            self.logger.error(f"生成改进建议失败: {str(e)}")
            suggestions.append('建议人工审核分析结果，提取更多学习价值')

        return suggestions

    async def get_patent_learning_insights(self, patent_context: Dict[str, Any]) -> Dict[str, Any]:
        """获取专利学习洞察"""
        try:
            insights = []

            # 基于历史模式提供洞察
            successful_patterns = [p for p in self.patterns.values() if p.pattern_type == 'successful_strategy']
            if successful_patterns:
                insights.append({
                    'type': 'successful_strategies',
                    'message': f"已识别 {len(successful_patterns)} 种成功策略模式",
                    'suggestion': '建议优先应用历史成功率高的策略'
                })

            # 基于失败模式提供预警
            failure_patterns = [p for p in self.patterns.values() if p.pattern_type == 'common_failure']
            if failure_patterns:
                insights.append({
                    'type': 'failure_warnings',
                    'message': f"已识别 {len(failure_patterns)} 种常见失败模式",
                    'suggestion': '建议避免已知的失败策略'
                })

            # 基于AI家庭成员表现推荐
            best_performer = self._get_best_performer_for_context(patent_context)
            if best_performer:
                insights.append({
                    'type': 'ai_recommendation',
                    'message': f"推荐由 {best_performer} 处理此专利",
                    'suggestion': f"{best_performer} 在此类专利中表现最佳"
                })

            return {
                'total_insights': len(insights),
                'insights': insights,
                'learning_stats': self.get_learning_statistics(),
                'recommendation_confidence': min(1.0, len(insights) / 3.0)
            }

        except Exception as e:
            self.logger.error(f"获取专利学习洞察失败: {str(e)}")
            return {
                'total_insights': 0,
                'insights': [],
                'error': str(e)
            }

    def _get_best_performer_for_context(self, patent_context: Dict[str, Any]) -> str | None:
        """根据上下文获取最佳执行者"""
        try:
            patent_type = patent_context.get('patent_type', 'invention')

            # 基于专利类型推荐AI家庭成员
            if patent_type == 'invention':
                return 'athena'  # 雅典娜擅长发明专利
            elif patent_type == 'utility_model':
                return 'xiaonuo'  # 小诺擅长实用新型
            elif patent_type == 'design':
                return 'xiaona'   # 小娜擅长外观设计

            return None

        except Exception as e:
            self.logger.error(f"获取最佳执行者失败: {str(e)}")
            return None

    def get_learning_statistics(self) -> Dict[str, Any]:
        """获取学习统计信息"""
        stats = self.learning_stats.copy()

        # 计算改进率
        if stats['total_experiences'] > 0:
            stats['improvement_rate'] = stats['successful_learnings'] / stats['total_experiences']

        # 添加模式统计
        stats['total_patterns'] = len(self.patterns)
        stats['success_patterns'] = len([p for p in self.patterns.values() if p.pattern_type == 'successful_strategy'])
        stats['failure_patterns'] = len([p for p in self.patterns.values() if p.pattern_type == 'common_failure'])

        # 添加AI家庭成员平均性能
        for member in ['athena', 'xiaona', 'xiaonuo']:
            if member in stats['ai_family_performance']:
                member_scores = []
                for scores in stats['ai_family_performance'][member].values():
                    member_scores.extend(scores)

                if member_scores:
                    stats[f"{member}_avg_performance"] = sum(member_scores) / len(member_scores)
                else:
                    stats[f"{member}_avg_performance"] = 0.0

        return stats

    async def optimize_patent_learning_strategy(self, learning_request: PatentLearningRequest) -> Dict[str, Any]:
        """优化专利学习策略"""
        try:
            self.logger.info(f"优化专利学习策略: {learning_request.request_id}")

            # 分析当前学习需求
            learning_needs = await self._analyze_learning_needs(learning_request)

            # 推荐最佳学习策略
            recommended_strategy = await self._recommend_learning_strategy(learning_needs, learning_request)

            # 生成学习计划
            learning_plan = await self._generate_learning_plan(recommended_strategy, learning_request)

            return {
                'success': True,
                'learning_needs': learning_needs,
                'recommended_strategy': recommended_strategy,
                'learning_plan': learning_plan,
                'expected_improvement': self._estimate_improvement_potential(recommended_strategy)
            }

        except Exception as e:
            self.logger.error(f"优化专利学习策略失败: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }

    async def _analyze_learning_needs(self, request: PatentLearningRequest) -> Dict[str, Any]:
        """分析学习需求"""
        needs = {
            'priority_areas': [],
            'improvement_opportunities': [],
            'knowledge_gaps': []
        }

        # 分析专利类型特定需求
        patent_type = request.patent_context.get('patent_type', 'invention')
        if patent_type == 'invention':
            needs['priority_areas'].append('inventiveness_assessment')
            needs['priority_areas'].append('technical_evaluation')
        elif patent_type == 'utility_model':
            needs['priority_areas'].append('practicality_assessment')
            needs['priority_areas'].append('simplification_strategy')

        # 分析性能改进需求
        current_performance = request.current_performance
        if current_performance.get('accuracy', 1.0) < 0.8:
            needs['improvement_opportunities'].append('accuracy_enhancement')
        if current_performance.get('efficiency', 1.0) < 0.7:
            needs['improvement_opportunities'].append('efficiency_optimization')

        # 分析知识缺口
        if len(self.experiences) < 100:
            needs['knowledge_gaps'].append('insufficient_experience')

        return needs

    async def _recommend_learning_strategy(self, needs: Dict[str, Any],
                                         request: PatentLearningRequest) -> Dict[str, Any]:
        """推荐学习策略"""
        strategy = {
            'primary_approach': 'incremental_learning',
            'learning_methods': [],
            'focus_areas': [],
            'timeline_days': 30
        }

        # 根据需求调整策略
        if needs['priority_areas']:
            strategy['learning_methods'].append('focused_training')
            strategy['focus_areas'].extend(needs['priority_areas'])

        if needs['improvement_opportunities']:
            strategy['learning_methods'].append('performance_optimization')

        if needs['knowledge_gaps']:
            strategy['learning_methods'].append('knowledge_base_expansion')
            strategy['primary_approach'] = 'intensive_learning'
            strategy['timeline_days'] = 60

        # 基于AI家庭成员特化调整
        ai_specialization = self.ai_family_specialization.get(request.ai_family_member, {})
        if ai_specialization:
            # 优先强化特化领域
            top_specializations = sorted(ai_specialization.items(), key=lambda x: x[1], reverse=True)[:2]
            strategy['focus_areas'].extend([spec[0] for spec in top_specializations])

        return strategy

    async def _generate_learning_plan(self, strategy: Dict[str, Any],
                                    request: PatentLearningRequest) -> List[Dict[str, Any]]:
        """生成学习计划"""
        plan = []

        # 基础学习阶段
        plan.append({
            'phase': 'foundation',
            'duration_days': 7,
            'activities': [
                '复习专利基础知识',
                '学习相关案例经验',
                '强化专业术语理解'
            ],
            'expected_outcome': '基础知识巩固'
        })

        # 专项训练阶段
        if 'focused_training' in strategy['learning_methods']:
            plan.append({
                'phase': 'specialized_training',
                'duration_days': 14,
                'activities': [
                    f"重点训练: {', '.join(strategy.get('focus_areas', []))}",
                    '参与专项案例分析',
                    '接受专家指导'
                ],
                'expected_outcome': '专项能力提升'
            })

        # 实践应用阶段
        if 'performance_optimization' in strategy['learning_methods']:
            plan.append({
                'phase': 'practical_application',
                'duration_days': 9,
                'activities': [
                    '实际案例处理',
                    '性能反馈收集',
                    '策略调整优化'
                ],
                'expected_outcome': '实践能力强化'
            })

        return plan

    def _estimate_improvement_potential(self, strategy: Dict[str, Any]) -> Dict[str, float]:
        """估计改进潜力"""
        potential = {
            'accuracy_improvement': 0.1,
            'efficiency_improvement': 0.15,
            'overall_performance': 0.12
        }

        # 根据策略强度调整预期
        if strategy.get('primary_approach') == 'intensive_learning':
            for key in potential:
                potential[key] *= 1.5

        # 根据时间线调整
        timeline = strategy.get('timeline_days', 30)
        if timeline > 45:
            for key in potential:
                potential[key] *= 1.2

        return potential


# 测试代码
async def test_patent_learning_optimizer():
    """测试专利学习优化器"""
    optimizer = PatentLearningOptimizer()

    # 模拟专利分析学习
    test_patent_id = 'CN202410001234.5'
    test_input = {
        'patent_id': test_patent_id,
        'patent_type': 'invention',
        'technology_field': 'artificial_intelligence',
        'title': '基于深度学习的图像识别方法'
    }

    test_result = {
        'confidence': 0.85,
        'novelty_score': 0.8,
        'inventiveness_assessment': '具有显著创造性',
        'detailed_analysis': True,
        'evidence_support': True,
        'clear_reasoning': True,
        'examination_strategy': {
            'proactive_claims_adjustment': True,
            'technical_emphasis': True
        },
        'best_practices': {
            'clear_hierarchy': True,
            'adequate_support': True
        }
    }

    # 测试Athena学习
    athena_result = await optimizer.learn_from_patent_analysis(
        test_patent_id, test_input, test_result, 'athena'
    )

    logger.info('Athena专利分析学习测试结果:')
    logger.info(f"  学习成功: {athena_result['success']}")
    logger.info(f"  成功分数: {athena_result.get('success_score', 0):.3f}")
    logger.info(f"  学习洞察数量: {athena_result.get('learning_insights_count', 0)}")
    logger.info(f"  改进建议数量: {len(athena_result.get('improvement_suggestions', []))}")

    # 测试学习洞察
    insights = await optimizer.get_patent_learning_insights({
        'patent_type': 'invention',
        'technology_field': 'artificial_intelligence'
    })

    logger.info(f"\n学习洞察测试结果:")
    logger.info(f"  洞察总数: {insights['total_insights']}")
    logger.info(f"  推荐置信度: {insights.get('recommendation_confidence', 0):.3f}")

    # 测试学习统计
    stats = optimizer.get_learning_statistics()
    logger.info(f"\n学习统计信息:")
    logger.info(f"  总经验数: {stats['total_experiences']}")
    logger.info(f"  成功学习数: {stats['successful_learnings']}")
    logger.info(f"  改进率: {stats['improvement_rate']:.3f}")
    logger.info(f"  总模式数: {stats['total_patterns']}")

    return {
        'athena_learning': athena_result['success'],
        'insights_generated': insights['total_insights'],
        'learning_stats': stats
    }


if __name__ == '__main__':
    asyncio.run(test_patent_learning_optimizer())