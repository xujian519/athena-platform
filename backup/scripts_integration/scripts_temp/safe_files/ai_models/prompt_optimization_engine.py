#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Athena提示词优化引擎 - 基于Lyra框架的专业提示词优化系统
Athena Prompt Optimization Engine - Professional Prompt Optimization System based on Lyra Framework
"""

import json
import logging
import re
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple, Union

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TargetAI(Enum):
    """目标AI平台"""
    CHATGPT = 'chatgpt'
    CLAUDE = 'claude'
    GEMINI = 'gemini'
    OTHER = 'other'

class ProcessingMode(Enum):
    """处理模式"""
    BASIC = 'basic'      # 快速优化
    DETAIL = 'detail'    # 深度优化

class RequestType(Enum):
    """请求类型"""
    CREATIVE = 'creative'     # 创意类
    TECHNICAL = 'technical'   # 技术类
    EDUCATIONAL = 'educational' # 教育类
    COMPLEX = 'complex'       # 复杂类

@dataclass
class PromptAnalysis:
    """提示词分析结果"""
    core_intent: str
    key_entities: List[str]
    context: Dict[str, Any]
    output_requirements: List[str]
    constraints: List[str]
    missing_elements: List[str]
    clarity_issues: List[str]

@dataclass
class OptimizationPlan:
    """优化计划"""
    selected_techniques: List[str]
    recommended_role: str
    structure_suggestions: List[str]
    context_enhancements: Dict[str, Any]
    platform_adjustments: Dict[str, str]

class PromptOptimizationEngine:
    """提示词优化引擎"""

    def __init__(self):
        # 核心组件
        self.deconstructor = PromptDeconstructor()
        self.diagnostician = PromptDiagnostician()
        self.developer = PromptDeveloper()
        self.deliverer = PromptDeliverer()

        # 技巧库
        self.techniques = TechniqueLibrary()
        self.platform_knowledge = PlatformKnowledgeBase()

        # 历史和学习
        self.optimization_history = []
        self.success_patterns = {}

    def optimize(self,
                 user_input: str,
                 target_ai: str = 'claude',
                 mode: str = 'auto') -> Dict[str, Any]:
        """优化提示词"""
        logger.info(f"🚀 开始优化提示词: {user_input[:50]}...")

        # 自动检测复杂度和选择模式
        if mode == 'auto':
            mode = self._auto_detect_mode(user_input)

        logger.info(f"📝 使用{mode.upper()}模式优化，目标AI: {target_ai}")

        try:
            # 4-D Methodology
            # 1. DECONSTRUCT
            analysis = self.deconstructor.extract(user_input)

            # 2. DIAGNOSE
            diagnosis = self.diagnostician.audit(analysis, user_input)

            # 3. DEVELOP
            plan = self.developer.create_plan(
                analysis, diagnosis, target_ai, mode
            )

            # 4. DELIVER
            result = self.deliverer.construct(
                user_input, analysis, plan, mode
            )

            # 记录优化历史
            self._record_optimization(user_input, result, mode, target_ai)

            return result

        except Exception as e:
            logger.error(f"❌ 优化失败: {str(e)}")
            return {
                'error': str(e),
                'original_prompt': user_input,
                'status': 'failed'
            }

    def _auto_detect_mode(self, user_input: str) -> str:
        """自动检测处理模式"""
        complexity_indicators = {
            # 明确的复杂性指标
            'explicit': [
                '要求', '格式', '结构', '角色', '场景',
                '步骤', '规则', '限制', '详细', '全面'
            ],
            # 隐含的复杂性指标
            'implicit': [
                '分析', '设计', '开发', '评估', '优化',
                '策略', '方案', '系统', '架构'
            ],
            # 长度指标
            'length': len(user_input) > 100
        }

        score = 0
        for indicator_list in [complexity_indicators['explicit'],
                             complexity_indicators['implicit']]:
            for indicator in indicator_list:
                if indicator in user_input.lower():
                    score += 1

        if complexity_indicators['length']:
            score += 1

        # 决定模式
        return 'detail' if score >= 2 else 'basic'

    def _record_optimization(self,
                            original: str,
                            result: Dict,
                            mode: str,
                            target_ai: str):
        """记录优化历史"""
        record = {
            'timestamp': datetime.now().isoformat(),
            'original': original,
            'optimized': result.get('optimized_prompt', ''),
            'mode': mode,
            'target_ai': target_ai,
            'techniques': result.get('techniques_applied', []),
            'improvements': result.get('key_improvements', [])
        }

        self.optimization_history.append(record)

        # 更新成功模式
        self._update_success_patterns(record)

    def _update_success_patterns(self, record: Dict):
        """更新成功模式库"""
        # 简化实现：记录有效的技巧组合
        techniques = tuple(record['techniques'])
        if techniques not in self.success_patterns:
            self.success_patterns[techniques] = {
                'usage_count': 0,
                'success_rate': 0.0
            }

        self.success_patterns[techniques]['usage_count'] += 1

    def get_welcome_message(self) -> str:
        """获取欢迎消息"""
        return """Hello! I'm Athena's Prompt Optimizer. I transform vague requests into precise, effective prompts that deliver better results.

**What I need to know:**
- **Target AI:** ChatGPT, Claude, Gemini, or Other
- **Optimization Style:** DETAIL (I'll analyze deeply first) or BASIC (quick optimization)

**Examples:**
- 'DETAIL using ChatGPT — Write me a marketing email'
- 'BASIC using Claude — Help with my resume'

Just share your rough prompt and I'll handle the optimization!"""

class PromptDeconstructor:
    """提示词解构器"""

    def extract(self, user_input: str) -> PromptAnalysis:
        """提取核心要素"""
        logger.info('1️⃣ DECONSTRUCT - 提取核心要素')

        # 提取核心意图
        core_intent = self._extract_intent(user_input)

        # 识别关键实体
        key_entities = self._extract_entities(user_input)

        # 分析上下文
        context = self._extract_context(user_input)

        # 识别输出要求
        output_requirements = self._extract_requirements(user_input)

        # 识别约束
        constraints = self._extract_constraints(user_input)

        # 识别缺失元素
        missing_elements = self._identify_missing(user_input)

        # 识别清晰度问题
        clarity_issues = self._check_clarity(user_input)

        return PromptAnalysis(
            core_intent=core_intent,
            key_entities=key_entities,
            context=context,
            output_requirements=output_requirements,
            constraints=constraints,
            missing_elements=missing_elements,
            clarity_issues=clarity_issues
        )

    def _extract_intent(self, text: str) -> str:
        """提取核心意图"""
        # 简化实现：基于关键词识别
        intent_patterns = {
            'write': '撰写/创作',
            'analyze': '分析',
            'explain': '解释说明',
            'create': '创建/生成',
            'help': '帮助/协助',
            'design': '设计',
            'review': '审查/评估',
            'compare': '比较/对比'
        }

        for pattern, intent in intent_patterns.items():
            if pattern in text.lower():
                return intent

        return '通用任务'

    def _extract_entities(self, text: str) -> List[str]:
        """提取关键实体"""
        # 简化实现：提取名词短语
        entities = []

        # 匹配常见的实体模式
        patterns = [
            r'\b(?:邮件|报告|文档|代码|方案|计划)\b',
            r'\b(?:Python|Java|JavaScript)\b',
            r'\b(?:AI|机器学习|深度学习)\b'
        ]

        for pattern in patterns:
            matches = re.findall(pattern, text)
            entities.extend(matches)

        return list(set(entities))

    def _extract_context(self, text: str) -> Dict[str, Any]:
        """提取上下文"""
        context = {
            'domain': 'general',
            'audience': 'unknown',
            'purpose': 'unknown'
        }

        # 识别领域
        if any(word in text.lower() for word in ['技术', '代码', '编程']):
            context['domain'] = 'technology'
        elif any(word in text.lower() for word in ['营销', '销售', '市场']):
            context['domain'] = 'marketing'
        elif any(word in text.lower() for word in ['教育', '学习', '培训']):
            context['domain'] = 'education'

        return context

    def _extract_requirements(self, text: str) -> List[str]:
        """提取输出要求"""
        requirements = []

        # 查找明确的要求
        requirement_patterns = [
            r'需要(.{0,50})',
            r'要求(.{0,50})',
            r'请(.{0,50})'
        ]

        for pattern in requirement_patterns:
            matches = re.findall(pattern, text)
            requirements.extend(matches)

        return requirements

    def _extract_constraints(self, text: str) -> List[str]:
        """提取约束条件"""
        constraints = []

        # 查找约束词
        constraint_patterns = [
            r'不(.{0,30})',
            r'避免(.{0,30})',
            r'限制(.{0,30})'
        ]

        for pattern in constraint_patterns:
            matches = re.findall(pattern, text)
            constraints.extend(matches)

        return constraints

    def _identify_missing(self, text: str) -> List[str]:
        """识别缺失元素"""
        missing = []

        # 检查常见缺失
        if '格式' not in text and len(text) < 50:
            missing.append('格式要求')

        if '例子' not in text and '示例' not in text and len(text) < 100:
            missing.append('具体例子')

        if '目标' not in text and '目的' not in text:
            missing.append('明确目标')

        return missing

    def _check_clarity(self, text: str) -> List[str]:
        """检查清晰度问题"""
        issues = []

        # 模糊词汇
        vague_words = ['一些', '某些', '相关', '适当的', '合理的']
        for word in vague_words:
            if word in text:
                issues.append(f"包含模糊词汇: {word}")

        # 长句问题
        sentences = text.split('。')
        for sentence in sentences:
            if len(sentence) > 100:
                issues.append('存在过长的句子')

        return issues

class PromptDiagnostician:
    """提示词诊断器"""

    def audit(self, analysis: PromptAnalysis, original_text: str) -> Dict[str, Any]:
        """审计提示词问题"""
        logger.info('2️⃣ DIAGNOSE - 诊断清晰度和完整性')

        diagnosis = {
            'clarity_score': self._calculate_clarity_score(analysis),
            'completeness_score': self._calculate_completeness_score(analysis),
            'specificity_issues': self._check_specificity(analysis),
            'structure_needs': self._assess_structure_needs(analysis),
            'optimization_priority': []
        }

        # 确定优化优先级
        if diagnosis['clarity_score'] < 0.7:
            diagnosis['optimization_priority'].append('clarify_intent')

        if diagnosis['completeness_score'] < 0.7:
            diagnosis['optimization_priority'].append('add_missing_elements')

        if not analysis.output_requirements:
            diagnosis['optimization_priority'].append('define_output_spec')

        return diagnosis

    def _calculate_clarity_score(self, analysis: PromptAnalysis) -> float:
        """计算清晰度分数"""
        base_score = 1.0

        # 每个清晰度问题扣分
        issues_count = len(analysis.clarity_issues)
        clarity_penalty = min(0.5, issues_count * 0.1)

        # 模糊词汇扣分
        vague_count = sum(1 for issue in analysis.clarity_issues
                         if '模糊词汇' in issue)
        vague_penalty = min(0.3, vague_count * 0.1)

        return max(0.0, base_score - clarity_penalty - vague_penalty)

    def _calculate_completeness_score(self, analysis: PromptAnalysis) -> float:
        """计算完整性分数"""
        required_elements = [
            analysis.core_intent,
            analysis.output_requirements,
            analysis.constraints
        ]

        present_elements = sum(1 for elem in required_elements if elem)

        return present_elements / len(required_elements)

    def _check_specificity(self, analysis: PromptAnalysis) -> List[str]:
        """检查具体性问题"""
        specificity_issues = []

        if len(analysis.core_intent) < 10:
            specificity_issues.append('意图描述过于简短')

        if not analysis.key_entities:
            specificity_issues.append('缺少具体实体')

        if not analysis.output_requirements:
            specificity_issues.append('缺少输出要求')

        return specificity_issues

    def _assess_structure_needs(self, analysis: PromptAnalysis) -> List[str]:
        """评估结构需求"""
        structure_needs = []

        # 基于意图类型判断
        if '分析' in analysis.core_intent:
            structure_needs.append('需要分析框架')

        if '步骤' in analysis.core_intent or '流程' in analysis.core_intent:
            structure_needs.append('需要步骤说明')

        if len(analysis.output_requirements) > 2:
            structure_needs.append('需要列表结构')

        return structure_needs

class PromptDeveloper:
    """提示词开发者"""

    def create_plan(self,
                   analysis: PromptAnalysis,
                   diagnosis: Dict,
                   target_ai: str,
                   mode: str) -> OptimizationPlan:
        """创建优化计划"""
        logger.info('3️⃣ DEVELOP - 创建优化计划')

        # 选择技巧
        techniques = self._select_techniques(
            analysis, diagnosis, target_ai, mode
        )

        # 推荐角色
        role = self._recommend_role(analysis, target_ai)

        # 结构建议
        structure = self._suggest_structure(analysis, diagnosis)

        # 上下文增强
        context_enhancement = self._enhance_context(analysis)

        # 平台调整
        platform_adjustments = self._get_platform_adjustments(target_ai)

        return OptimizationPlan(
            selected_techniques=techniques,
            recommended_role=role,
            structure_suggestions=structure,
            context_enhancements=context_enhancement,
            platform_adjustments=platform_adjustments
        )

    def _select_techniques(self,
                         analysis: PromptAnalysis,
                         diagnosis: Dict,
                         target_ai: str,
                         mode: str) -> List[str]:
        """选择优化技巧"""
        techniques = []

        # 基础技巧
        techniques.extend(['role_assignment', 'context_layering'])

        # 基于意图类型的技巧
        if '创意' in analysis.core_intent or '创作' in analysis.core_intent:
            techniques.extend(['multi_perspective', 'tone_emphasis'])

        if '技术' in analysis.core_intent or '代码' in analysis.core_intent:
            techniques.extend(['constraint_based', 'precision_focus'])

        if '教育' in analysis.core_intent or '解释' in analysis.core_intent:
            techniques.extend(['few_shot_examples', 'clear_structure'])

        # 基于诊断结果的技巧
        if diagnosis['clarity_score'] < 0.7:
            techniques.append('clarification_enhancement')

        if diagnosis['completeness_score'] < 0.7:
            techniques.append('context_expansion')

        # 基于复杂度的技巧
        if mode == 'detail':
            techniques.extend(['chain_of_thought', 'systematic_frameworks'])

        return techniques

    def _recommend_role(self, analysis: PromptAnalysis, target_ai: str) -> str:
        """推荐AI角色"""
        domain = analysis.context.get('domain', 'general')

        role_mapping = {
            'technology': '技术专家/软件工程师',
            'marketing': '营销专家/文案策划',
            'education': '教育专家/培训师',
            'business': '商业顾问/分析师',
            'creative': '创意总监/设计师',
            'general': '全能助手/问题解决专家'
        }

        return role_mapping.get(domain, role_mapping['general'])

    def _suggest_structure(self,
                          analysis: PromptAnalysis,
                          diagnosis: Dict) -> List[str]:
        """建议结构"""
        structures = []

        # 基于需求的结构
        if diagnosis.get('structure_needs'):
            structures.extend(diagnosis['structure_needs'])

        # 基于输出要求的结构
        if analysis.output_requirements:
            if len(analysis.output_requirements) > 3:
                structures.append('编号列表')
            else:
                structures.append('段落结构')

        return structures

    def _enhance_context(self, analysis: PromptAnalysis) -> Dict[str, Any]:
        """增强上下文"""
        enhancements = {
            'domain_knowledge': self._get_domain_knowledge(analysis),
            'audience_definition': '默认为普通用户',
            'purpose_clarification': '需要明确输出目的'
        }

        return enhancements

    def _get_domain_knowledge(self, analysis: PromptAnalysis) -> str:
        """获取领域知识"""
        domain = analysis.context.get('domain', 'general')

        domain_knowledge = {
            'technology': '考虑技术可行性、最佳实践、代码规范',
            'marketing': '考虑目标受众、品牌调性、转化率',
            'education': '考虑学习目标、难度梯度、理解度',
            'business': '考虑商业价值、ROI、可行性'
        }

        return domain_knowledge.get(domain, '通用最佳实践')

    def _get_platform_adjustments(self, target_ai: str) -> Dict[str, str]:
        """获取平台调整建议"""
        adjustments = {
            'chatgpt': {
                'format': '使用清晰的标题和列表',
                'style': '简洁直接的指令',
                'limitation': '注意上下文窗口限制'
            },
            'claude': {
                'format': '可以使用更长的推理框架',
                'style': '鼓励详细的分析过程',
                'limitation': '可以处理更复杂的任务'
            },
            'gemini': {
                'format': '适合创意和对比分析',
                'style': '鼓励多角度思考',
                'limitation': '在某些专业领域可能需要更多引导'
            }
        }

        return adjustments.get(target_ai, adjustments['other'] if 'other' in adjustments else {})

class PromptDeliverer:
    """提示词交付器"""

    def construct(self,
                  original: str,
                  analysis: PromptAnalysis,
                  plan: OptimizationPlan,
                  mode: str) -> Dict[str, Any]:
        """构造优化后的提示词"""
        logger.info('4️⃣ DELIVER - 构造优化提示词')

        # 构建优化后的提示词
        optimized = self._build_optimized_prompt(original, analysis, plan)

        # 计算改进点
        improvements = self._calculate_improvements(original, optimized, analysis, plan)

        # 准备结果
        result = {
            'optimized_prompt': optimized,
            'key_improvements': improvements['key_improvements'],
            'techniques_applied': plan.selected_techniques,
            'pro_tip': self._generate_pro_tip(plan, mode),
            'analysis': {
                'original_intent': analysis.core_intent,
                'identified_entities': analysis.key_entities,
                'detected_issues': analysis.clarity_issues
            }
        }

        # 根据模式调整输出格式
        if mode == 'basic':
            result = self._format_basic_result(result)
        else:
            result = self._format_detail_result(result)

        return result

    def _build_optimized_prompt(self,
                              original: str,
                              analysis: PromptAnalysis,
                              plan: OptimizationPlan) -> str:
        """构建优化后的提示词"""
        parts = []

        # 角色定义
        if plan.recommended_role:
            parts.append(f"作为一名{plan.recommended_role}，")

        # 任务描述
        parts.append(f"请{analysis.core_intent}。")

        # 上下文增强
        if plan.context_enhancements:
            parts.append("\n**背景信息：**")
            for key, value in plan.context_enhancements.items():
                parts.append(f"- {key}: {value}")

        # 输出要求
        if analysis.output_requirements:
            parts.append("\n**具体要求：**")
            for req in analysis.output_requirements:
                parts.append(f"- {req}")

        # 约束条件
        if analysis.constraints:
            parts.append("\n**注意事项：**")
            for constraint in analysis.constraints:
                parts.append(f"- {constraint}")

        # 结构指导
        if plan.structure_suggestions:
            parts.append(f"\n**建议格式：**{', '.join(plan.structure_suggestions)}")

        # 添加原始输入作为参考
        parts.append(f"\n**原始需求：**{original}")

        return "\n".join(parts)

    def _calculate_improvements(self,
                              original: str,
                              optimized: str,
                              analysis: PromptAnalysis,
                              plan: OptimizationPlan) -> Dict[str, Any]:
        """计算改进点"""
        improvements = {
            'key_improvements': [
                f"添加了专业角色定义: {plan.recommended_role}",
                f"明确了任务要求: {len(analysis.output_requirements)}项",
                f"应用了{len(plan.selected_techniques)}项优化技巧"
            ],
            'metrics': {
                'length_increase': len(optimized) - len(original),
                'clarity_boost': '显著提升' if analysis.clarity_issues else '一般提升',
                'structure_added': len(plan.structure_suggestions) > 0
            }
        }

        return improvements

    def _generate_pro_tip(self, plan: OptimizationPlan, mode: str) -> str:
        """生成专业提示"""
        tips = {
            'role_assignment': '明确角色能大幅提升输出质量',
            'context_layering': '提供充分的上下文有助于理解',
            'few_shot_examples': '添加具体例子能获得更精准的结果'
        }

        # 根据主要技巧返回提示
        if plan.selected_techniques:
            primary_technique = plan.selected_techniques[0]
            return tips.get(primary_technique, '根据需要调整提示词细节以获得最佳效果')

        return '使用此提示词时，可以根据具体需求微调细节'

    def _format_basic_result(self, result: Dict) -> Dict:
        """格式化基础模式结果"""
        return {
            'optimized_prompt': result['optimized_prompt'],
            'what_changed': ', '.join(result['key_improvements'][:2])
        }

    def _format_detail_result(self, result: Dict) -> Dict:
        """格式化详细模式结果"""
        return {
            'optimized_prompt': result['optimized_prompt'],
            'key_improvements': result['key_improvements'],
            'techniques_applied': result['techniques_applied'],
            'pro_tip': result['pro_tip'],
            'analysis': result['analysis']
        }

class TechniqueLibrary:
    """技巧库"""

    def __init__(self):
        self.techniques = {
            'role_assignment': '为AI分配专业角色',
            'context_layering': '分层提供上下文信息',
            'output_specs': '明确输出格式要求',
            'task_decomposition': '将任务分解为子任务',
            'chain_of_thought': '引导AI逐步推理',
            'few_shot_examples': '提供具体示例',
            'multi_perspective': '从多个角度分析',
            'constraint_optimization': '优化约束条件'
        }

class PlatformKnowledgeBase:
    """平台知识库"""

    def __init__(self):
        self.platforms = {
            'chatgpt': {
                'strengths': ['通用能力强', '响应速度快'],
                'limitations': ['上下文窗口限制', '偶尔会产生幻觉'],
                'best_practices': ['清晰的指令', '结构化输出']
            },
            'claude': {
                'strengths': ['长文本理解', '推理能力强'],
                'limitations': ['响应稍慢', '某些领域知识有限'],
                'best_practices': ['详细分析', '逐步推理']
            },
            'gemini': {
                'strengths': ['多模态处理', '创意能力强'],
                'limitations': ['新平台，正在优化', '专业领域待加强'],
                'best_practices': ['创意任务', '对比分析']
            }
        }

# 导出主类
__all__ = [
    'PromptOptimizationEngine',
    'TargetAI',
    'ProcessingMode',
    'RequestType'
]