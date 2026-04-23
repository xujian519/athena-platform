#!/usr/bin/env python3
"""
AI家庭成员专利学习特化配置
AI Family Patent Learning Specialization Configuration

为爸爸(Athena)、小娜(Xiaona)、小诺(Xiaonuo)配置专利领域的专门学习特化，
实现专利业务的个性化学习和能力提升。

Created by Athena + 小诺 (AI助手)
Date: 2025-12-05
"""

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@dataclass
class PatentLearningProfile:
    """专利学习配置档案"""
    ai_member: str
    specialization_areas: list[str]
    learning_priorities: dict[str, float]
    expertise_level: dict[str, float]
    target_capabilities: list[str]
    learning_methods: list[str]
    performance_metrics: dict[str, float] = field(default_factory=dict)

class AIFamilyPatentLearningConfig:
    """AI家庭成员专利学习配置管理器"""

    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.AIFamilyPatentLearningConfig")

        # AI家庭成员专利学习档案
        self.learning_profiles: dict[str, PatentLearningProfile] = {}

        # 初始化学习配置
        self._init_learning_profiles()

        self.logger.info('AI家庭成员专利学习配置初始化完成')

    def _init_learning_profiles(self):
        """初始化学习配置档案"""

        # 爸爸 (Athena) - 专利战略分析专家
        self.learning_profiles['athena'] = PatentLearningProfile(
            ai_member='athena',
            specialization_areas=[
                'patent_portfolio_strategy',
                'technology_trend_analysis',
                'innovation_assessment',
                'market_competitive_analysis',
                'strategic_patent_planning',
                'technical_evaluation'
            ],
            learning_priorities={
                'strategic_analysis': 0.9,
                'technical_evaluation': 0.8,
                'patent_portfolio': 0.85,
                'innovation_assessment': 0.9,
                'market_analysis': 0.75,
                'competitive_intelligence': 0.8
            },
            expertise_level={
                'invention_patent_analysis': 0.9,
                'technology_domain_assessment': 0.85,
                'patent_valuation': 0.8,
                'freedom_to_operate': 0.75,
                'invalidity_analysis': 0.8
            },
            target_capabilities=[
                '高价值专利识别',
                '技术路线图规划',
                '专利组合优化',
                '竞争对手分析',
                '技术创新评估',
                '专利商业化潜力评估'
            ],
            learning_methods=[
                '战略案例研究',
                '行业趋势跟踪',
                '技术发展预测',
                '市场分析建模',
                '竞争情报收集',
                '专家知识访谈'
            ]
        )

        # 小娜 (Xiaona) - 专利法律分析专家
        self.learning_profiles['xiaona'] = PatentLearningProfile(
            ai_member='xiaona',
            specialization_areas=[
                'patentability_analysis',
                'legal_interpretation',
                'prior_art_search',
                'claim_drafting',
                'examination_strategy',
                'infringement_analysis'
            ],
            learning_priorities={
                'novelty_analysis': 0.9,
                'inventiveness_assessment': 0.85,
                'legal_interpretation': 0.9,
                'prior_art_search': 0.8,
                'claim_analysis': 0.85,
                'examination_response': 0.8
            },
            expertise_level={
                'novelty_assessment': 0.9,
                'inventiveness_evaluation': 0.85,
                'industrial_applicability': 0.8,
                'claim_interpretation': 0.9,
                'legal_basis_analysis': 0.85,
                'examination_guidelines': 0.9
            },
            target_capabilities=[
                '专利性精准判断',
                '权利要求优化设计',
                '审查意见专业答复',
                '现有技术深度检索',
                '侵权风险评估',
                '专利稳定性分析'
            ],
            learning_methods=[
                '判例分析法',
                '法规条款解读',
                '审查指南研究',
                '案例对比学习',
                '法律推理训练',
                '实务模拟练习'
            ]
        )

        # 小诺 (Xiaonuo) - 专利实务执行专家
        self.learning_profiles['xiaonuo'] = PatentLearningProfile(
            ai_member='xiaonuo',
            specialization_areas=[
                'patent_filing_process',
                'workflow_optimization',
                'quality_control',
                'case_management',
                'client_communication',
                'project_coordination'
            ],
            learning_priorities={
                'patent_filing': 0.9,
                'examination_response': 0.85,
                'workflow_optimization': 0.8,
                'quality_control': 0.85,
                'case_management': 0.9,
                'process_improvement': 0.8
            },
            expertise_level={
                'application_preparation': 0.9,
                'filing_procedure': 0.85,
                'examination_monitoring': 0.8,
                'deadline_management': 0.9,
                'document_preparation': 0.85,
                'client_service': 0.8
            },
            target_capabilities=[
                '专利申请高效办理',
                '流程优化管理',
                '质量风险控制',
                '项目进度跟踪',
                '客户需求响应',
                '团队协作协调'
            ],
            learning_methods=[
                '流程标准化学习',
                '实务操作训练',
                '案例实践积累',
                '效率工具掌握',
                '质量标准内化',
                '沟通技巧提升'
            ]
        )

    def get_ai_member_profile(self, ai_member: str) -> PatentLearningProfile | None:
        """获取AI家庭成员学习配置档案"""
        return self.learning_profiles.get(ai_member.lower())

    def get_patent_task_assignment(self, patent_type: str,
                                 task_complexity: str,
                                 urgency_level: str) -> dict[str, Any]:
        """获取专利任务分配建议"""

        # 基于专利类型的初始推荐
        if patent_type == 'invention':
            primary_recommendation = 'athena'
            secondary_recommendation = 'xiaona'
        elif patent_type == 'utility_model':
            primary_recommendation = 'xiaonuo'
            secondary_recommendation = 'athena'
        elif patent_type == 'design':
            primary_recommendation = 'xiaona'
            secondary_recommendation = 'xiaonuo'
        else:
            primary_recommendation = 'athena'
            secondary_recommendation = 'xiaona'

        # 基于复杂度调整
        if task_complexity == 'high':
            # 复杂任务优先推荐爸爸
            primary_recommendation = 'athena'
            secondary_recommendation = 'xiaona'
        elif task_complexity == 'medium':
            # 中等任务根据专利类型推荐
            pass
        elif task_complexity == 'low':
            # 简单任务优先推荐小诺
            primary_recommendation = 'xiaonuo'
            secondary_recommendation = 'xiaona'

        # 基于紧急程度调整
        if urgency_level == 'high':
            # 紧急任务优先推荐小诺（实务执行能力）
            if task_complexity != 'high':  # 除非是高复杂度任务
                primary_recommendation = 'xiaonuo'

        return {
            'primary_recommendation': primary_recommendation,
            'secondary_recommendation': secondary_recommendation,
            'reasoning': self._generate_assignment_reasoning(
                patent_type, task_complexity, urgency_level,
                primary_recommendation, secondary_recommendation
            ),
            'confidence_score': self._calculate_assignment_confidence(
                patent_type, task_complexity, urgency_level
            )
        }

    def _generate_assignment_reasoning(self, patent_type: str, task_complexity: str,
                                     urgency_level: str, primary: str, secondary: str) -> str:
        """生成任务分配推理说明"""

        primary_profile = self.get_ai_member_profile(primary)
        self.get_ai_member_profile(secondary)

        reasoning_parts = []

        # 专利类型理由
        if patent_type == 'invention':
            reasoning_parts.append('发明专利需要深度技术分析和战略规划')
        elif patent_type == 'utility_model':
            reasoning_parts.append('实用新型注重实用性和申请效率')
        elif patent_type == 'design':
            reasoning_parts.append('外观设计重视独特性和法律保护')

        # 复杂度理由
        if task_complexity == 'high':
            reasoning_parts.append('高复杂度任务需要丰富的经验和分析能力')
        elif task_complexity == 'medium':
            reasoning_parts.append('中等复杂度任务平衡专业知识和执行效率')
        elif task_complexity == 'low':
            reasoning_parts.append('低复杂度任务重点关注执行质量和效率')

        # 推荐理由
        if primary_profile:
            primary_strengths = primary_profile.specialization_areas[:2]
            reasoning_parts.append(f"{primary} 在 {', '.join(primary_strengths)} 方面具有专长")

        return '; '.join(reasoning_parts)

    def _calculate_assignment_confidence(self, patent_type: str,
                                        task_complexity: str,
                                        urgency_level: str) -> float:
        """计算任务分配置信度"""

        base_confidence = 0.8

        # 根据专利类型调整
        if patent_type in ['invention', 'utility_model', 'design']:
            base_confidence += 0.1
        else:
            base_confidence -= 0.1

        # 根据复杂度调整
        if task_complexity == 'high':
            base_confidence += 0.05
        elif task_complexity == 'medium':
            base_confidence += 0.1
        elif task_complexity == 'low':
            base_confidence += 0.05

        # 根据紧急程度调整
        if urgency_level == 'high':
            base_confidence += 0.05

        return min(1.0, base_confidence)

    def generate_learning_plan(self, ai_member: str,
                             focus_areas: list[str],
                             duration_days: int = 30) -> dict[str, Any]:
        """为AI家庭成员生成个性化学习计划"""

        profile = self.get_ai_member_profile(ai_member)
        if not profile:
            return {'error': f"未找到 {ai_member} 的学习配置档案"}

        # 生成学习计划
        plan = {
            'ai_member': ai_member,
            'duration_days': duration_days,
            'focus_areas': focus_areas,
            'learning_phases': []
        }

        # 基础巩固阶段
        if duration_days >= 7:
            plan['learning_phases'].append({
                'phase': 'foundation',
                'duration_days': min(7, duration_days // 4),
                'objectives': [
                    '巩固专利基础知识',
                    '强化专业术语理解',
                    '熟悉相关法规指南'
                ],
                'learning_methods': profile.learning_methods[:2],
                'expected_outcome': '基础知识牢固掌握'
            })

        # 专项提升阶段
        if duration_days >= 14:
            remaining_days = duration_days - plan['learning_phases'][0]['duration_days']
            phase_days = min(14, remaining_days // 2)

            # 基于关注领域定制学习内容
            phase_objectives = []
            for area in focus_areas:
                if area in profile.specialization_areas:
                    phase_objectives.append(f"提升{area}专业能力")

            plan['learning_phases'].append({
                'phase': 'specialization',
                'duration_days': phase_days,
                'objectives': phase_objectives,
                'learning_methods': profile.learning_methods[2:4],
                'expected_outcome': '专项能力显著提升'
            })

        # 实践应用阶段
        if duration_days >= 21:
            remaining_days = duration_days - sum(p['duration_days'] for p in plan['learning_phases'])

            plan['learning_phases'].append({
                'phase': 'practice',
                'duration_days': remaining_days,
                'objectives': [
                    '实际案例处理',
                    '综合能力应用',
                    '性能优化调整'
                ],
                'learning_methods': profile.learning_methods[-2:],
                'expected_outcome': '实践能力熟练掌握'
            })

        # 添加学习资源建议
        plan['learning_resources'] = self._recommend_learning_resources(ai_member, focus_areas)

        # 添加成功评估标准
        plan['success_criteria'] = self._define_success_criteria(ai_member, focus_areas)

        return plan

    def _recommend_learning_resources(self, ai_member: str,
                                    focus_areas: list[str]) -> list[dict[str, str]:
        """推荐学习资源"""

        resources = []

        # 基础资源
        base_resources = [
            {'type': 'document', 'name': '专利法及实施细则', 'priority': 'high'},
            {'type': 'guide', 'name': '专利审查指南', 'priority': 'high'},
            {'type': 'database', 'name': '专利案例数据库', 'priority': 'medium'}
        ]
        resources.extend(base_resources)

        # 专项资源
        if ai_member == 'athena':
            resources.extend([
                {'type': 'report', 'name': '技术发展趋势报告', 'priority': 'high'},
                {'type': 'analysis', 'name': '专利竞争分析案例', 'priority': 'medium'},
                {'type': 'tool', 'name': '专利估值模型工具', 'priority': 'medium'}
            ])
        elif ai_member == 'xiaona':
            resources.extend([
                {'type': 'casebook', 'name': '专利复审无效案例集', 'priority': 'high'},
                {'type': 'regulation', 'name': '审查指南详解', 'priority': 'high'},
                {'type': 'database', 'name': '判例检索系统', 'priority': 'medium'}
            ])
        elif ai_member == 'xiaonuo':
            resources.extend([
                {'type': 'handbook', 'name': '专利申请实务手册', 'priority': 'high'},
                {'type': 'template', 'name': '申请文件模板库', 'priority': 'medium'},
                {'type': 'workflow', 'name': '流程优化案例', 'priority': 'medium'}
            ])

        return resources

    def _define_success_criteria(self, ai_member: str,
                               focus_areas: list[str]) -> list[dict[str, Any]:
        """定义成功评估标准"""

        profile = self.get_ai_member_profile(ai_member)
        if not profile:
            return []

        criteria = []

        # 基础能力标准
        criteria.append({
            'category': '基础能力',
            'metrics': [
                {'name': '专利知识掌握度', 'target': '>= 90%'},
                {'name': '专业术语准确率', 'target': '>= 95%'},
                {'name': '法规理解深度', 'target': '>= 85%'}
            ]
        })

        # 专项能力标准
        for area in focus_areas:
            if area in profile.target_capabilities:
                criteria.append({
                    'category': f"专项能力-{area}",
                    'metrics': [
                        {'name': f"{area}准确率', 'target': '>= 85%"},
                        {'name': f"{area}效率', 'target': '>= 80%"},
                        {'name': f"{area}质量评分', 'target': '>= 4.0/5.0"}
                    ]
                })

        # 综合能力标准
        criteria.append({
            'category': '综合能力',
            'metrics': [
                {'name': '任务完成质量', 'target': '>= 90%'},
                {'name': '处理效率', 'target': '>= 85%'},
                {'name': '创新能力', 'target': '>= 80%'}
            ]
        })

        return criteria

    def evaluate_learning_progress(self, ai_member: str,
                                  performance_data: dict[str, float]) -> dict[str, Any]:
        """评估学习进度"""

        profile = self.get_ai_member_profile(ai_member)
        if not profile:
            return {'error': f"未找到 {ai_member} 的学习配置档案"}

        evaluation = {
            'ai_member': ai_member,
            'evaluation_time': datetime.now().isoformat(),
            'overall_score': 0.0,
            'area_scores': {},
            'improvement_suggestions': [],
            'next_focus_areas': []
        }

        # 计算各领域得分
        total_score = 0.0
        weight_sum = 0.0

        for area, weight in profile.learning_priorities.items():
            area_score = performance_data.get(area, 0.0) * 100
            weighted_score = area_score * weight

            evaluation['area_scores'][area] = {
                'score': area_score,
                'weight': weight,
                'weighted_score': weighted_score
            }

            total_score += weighted_score
            weight_sum += weight

        # 计算总体得分
        if weight_sum > 0:
            evaluation['overall_score'] = total_score / weight_sum

        # 生成改进建议
        for area, score_data in evaluation['area_scores'].items():
            if score_data['score'] < 70:
                evaluation['improvement_suggestions'].append(
                    f"{area}: 基础能力需要加强，建议重点学习"
                )
            elif score_data['score'] < 85:
                evaluation['improvement_suggestions'].append(
                    f"{area}: 能力有提升空间，建议专项训练"
                )

        # 确定下一阶段重点学习领域
        sorted_areas = sorted(
            evaluation['area_scores'].items(),
            key=lambda x: x[1]['score']
        )

        evaluation['next_focus_areas'] = [
            area for area, _ in sorted_areas[:3]
            if evaluation['area_scores'][area]['score'] < 85
        ]

        return evaluation

    def get_all_profiles(self) -> dict[str, PatentLearningProfile]:
        """获取所有AI家庭成员的学习配置档案"""
        return self.learning_profiles


# 测试代码
async def test_ai_family_patent_learning_config():
    """测试AI家庭成员专利学习配置"""
    config = AIFamilyPatentLearningConfig()

    logger.info(str('=' * 60))
    logger.info('AI家庭成员专利学习配置测试')
    logger.info(str('=' * 60))

    # 测试任务分配
    logger.info("\n1. 专利任务分配测试:")
    task_assignment = config.get_patent_task_assignment('invention', 'high', 'medium')
    logger.info(f"   主要推荐: {task_assignment['primary_recommendation']}")
    logger.info(f"   次要推荐: {task_assignment['secondary_recommendation']}")
    logger.info(f"   置信度: {task_assignment['confidence_score']:.3f}")
    logger.info(f"   推理: {task_assignment['reasoning']}")

    # 测试学习计划生成
    logger.info("\n2. 学习计划生成测试 (Athena):")
    athena_plan = config.generate_learning_plan(
        'athena',
        ['patent_portfolio_strategy', 'innovation_assessment'],
        30
    )
    logger.info(f"   学习阶段数: {len(athena_plan['learning_phases'])}")
    logger.info(f"   学习资源数: {len(athena_plan['learning_resources'])}")
    logger.info(f"   评估标准数: {len(athena_plan['success_criteria'])}")

    # 测试学习进度评估
    logger.info("\n3. 学习进度评估测试 (小娜):")
    performance_data = {
        'novelty_analysis': 0.85,
        'inventiveness_assessment': 0.78,
        'legal_interpretation': 0.92,
        'prior_art_search': 0.81
    }
    progress_evaluation = config.evaluate_learning_progress('xiaona', performance_data)
    logger.info(f"   总体得分: {progress_evaluation['overall_score']:.2f}")
    logger.info(f"   改进建议数: {len(progress_evaluation['improvement_suggestions'])}")
    logger.info(f"   下一重点领域: {', '.join(progress_evaluation['next_focus_areas'])}")

    # 显示所有配置档案
    logger.info("\n4. AI家庭成员配置档案:")
    all_profiles = config.get_all_profiles()
    for member, profile in all_profiles.items():
        logger.info(f"   {member.title()}:")
        logger.info(f"     专长领域: {len(profile.specialization_areas)} 个")
        logger.info(f"     目标能力: {len(profile.target_capabilities)} 个")
        logger.info(f"     学习方法: {len(profile.learning_methods)} 种")

    return {
        'task_assignment': task_assignment['primary_recommendation'],
        'learning_plan_phases': len(athena_plan['learning_phases']),
        'progress_score': progress_evaluation['overall_score'],
        'total_profiles': len(all_profiles)
    }


if __name__ == '__main__':
    asyncio.run(test_ai_family_patent_learning_config())
