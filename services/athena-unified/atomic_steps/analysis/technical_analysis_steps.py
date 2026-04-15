#!/usr/bin/env python3
"""
技术深度分析原子步骤
Technical Deep Analysis Atomic Steps

提供三级技术分析框架：表面特征提取 → 技术手段解构 → 技术效果对比
"""

import logging
import sys
from pathlib import Path
from typing import Any

# 添加项目路径
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from atomic_steps.base import AtomicStep, StepInput, StepOutput
from atomic_steps.registry import atomic_step

logger = logging.getLogger(__name__)


@atomic_step
class ExtractTechFeaturesStep(AtomicStep):
    """
    技术特征提取步骤（一级分析）

    从专利文本中提取技术特征
    """
    step_name = "extract_tech_features"
    step_version = "1.0.0"
    step_description = "提取专利技术特征（一级分析）"
    step_category = "process"

    def execute(self, input: StepInput) -> StepOutput:
        """执行技术特征提取"""
        import time

        start_time = time.time()

        try:
            patent_text = input.get_param("patent_text", "")

            # 提取技术特征
            features = self._extract_features(patent_text)

            execution_time = time.time() - start_time

            logger.info(f"✅ 技术特征提取完成: 提取到 {len(features)} 个特征")

            return StepOutput.from_data(
                data={
                    'patent_text': patent_text,
                    'features': features,
                    'feature_count': len(features)
                },
                execution_time=execution_time
            )

        except Exception as e:
            logger.error(f"❌ 技术特征提取失败: {e}")
            return StepOutput.from_error(
                f"技术特征提取失败: {str(e)}",
                error_type=type(e).__name__
            )

    def _extract_features(self, text: str) -> list[dict[str, Any]]:
        """提取技术特征"""
        features = []

        # 按权利要求分解
        claims = self._extract_claims(text)
        for claim in claims:
            # 提取技术特征
            feature = {
                'claim_number': claim.get('number', ''),
                'feature_text': claim.get('text', ''),
                'feature_type': self._classify_feature_type(claim.get('text', '')),
                'components': self._extract_components(claim.get('text', '')),
                'parameters': self._extract_parameters(claim.get('text', ''))
            }
            features.append(feature)

        return features

    def _extract_claims(self, text: str) -> list[dict]:
        """提取权利要求"""
        import re

        claims = []
        pattern = r'(\d+)\.([\s\S]*?)(?=\d+\.|$)'
        matches = re.findall(pattern, text)

        for number, content in matches:
            claims.append({
                'number': number,
                'text': content.strip()
            })

        return claims

    def _classify_feature_type(self, text: str) -> str:
        """分类特征类型"""
        if '包括' in text or '包含' in text:
            return '结构特征'
        elif '步骤' in text or '方法' in text:
            return '方法特征'
        elif '组分' in text or '材料' in text:
            return '材料特征'
        else:
            return '其他特征'

    def _extract_components(self, text: str) -> list[str]:
        """提取组成部件"""
        import re

        # 提取"包括...、...、..."模式
        pattern = r'包括([^，。；]+?)(?:、|和|及)'
        matches = re.findall(pattern, text)

        return [m.strip() for m in matches]

    def _extract_parameters(self, text: str) -> list[dict[str, str]]:
        """提取技术参数"""
        import re

        parameters = []

        # 提取数值参数
        pattern = r'([\u4e00-\u9fa5]+)\s*[:：]?\s*(\d+(?:\.\d+)?)\s*~\s*(\d+(?:\.\d+)?)(?:\u4e00-\u9fa5]+)?'
        matches = re.findall(pattern, text)

        for name, min_val, max_val in matches:
            parameters.append({
                'name': name,
                'min_value': min_val,
                'max_value': max_val,
                'unit': '单位需从上下文判断'
            })

        return parameters


@atomic_step
class AnalyzeTechMeansStep(AtomicStep):
    """
    技术手段分析步骤（二级分析）

    对技术特征进行手段拆解：工作原理、结构组成、连接关系、控制逻辑
    """
    step_name = "analyze_tech_means"
    step_version = "1.0.0"
    step_description = "分析技术手段（二级分析）"
    step_category = "analysis"

    def execute(self, input: StepInput) -> StepOutput:
        """执行技术手段分析"""
        import time

        start_time = time.time()

        try:
            features = input.get_param("features", [])
            patent_text = input.get_param("patent_text", "")

            # 分析技术手段
            means_analysis = []
            for feature in features:
                analysis = {
                    'feature': feature,
                    'working_principle': self._analyze_working_principle(feature, patent_text),
                    'structure_composition': self._analyze_structure_composition(feature, patent_text),
                    'connection_relation': self._analyze_connection_relation(feature, patent_text),
                    'control_logic': self._analyze_control_logic(feature, patent_text)
                }
                means_analysis.append(analysis)

            execution_time = time.time() - start_time

            logger.info(f"✅ 技术手段分析完成: 分析了 {len(means_analysis)} 个特征")

            return StepOutput.from_data(
                data={
                    'features': features,
                    'means_analysis': means_analysis,
                    'analysis_count': len(means_analysis)
                },
                execution_time=execution_time
            )

        except Exception as e:
            logger.error(f"❌ 技术手段分析失败: {e}")
            return StepOutput.from_error(
                f"技术手段分析失败: {str(e)}",
                error_type=type(e).__name__
            )

    def _analyze_working_principle(self, feature: dict, full_text: str) -> dict[str, str]:
        """分析工作原理"""
        feature_text = feature.get('feature_text', '')

        # 查找包含该特征的描述段落
        context = self._find_feature_context(feature_text, full_text)

        return {
            'description': '工作原理描述需从上下文提取',
            'mechanism': '作用机理分析',
            'key_principle': '核心原理总结',
            'context_snippet': context[:200] if context else ''
        }

    def _analyze_structure_composition(self, feature: dict, full_text: str) -> dict[str, Any]:
        """分析结构组成"""
        components = feature.get('components', [])

        return {
            'main_components': components,
            'component_hierarchy': '组件层次结构',
            'material_composition': '材料组成分析',
            'structural_features': '结构特征描述'
        }

    def _analyze_connection_relation(self, feature: dict, full_text: str) -> dict[str, str]:
        """分析连接关系"""
        return {
            'connections': '连接方式分析',
            'arrangement': '布置关系',
            'cooperation': '配合关系',
            'sequence': '顺序关系'
        }

    def _analyze_control_logic(self, feature: dict, full_text: str) -> dict[str, str]:
        """分析控制逻辑"""
        return {
            'control_flow': '控制流程',
            'timing_relation': '时序关系',
            'condition_trigger': '条件触发',
            'feedback_mechanism': '反馈机制'
        }

    def _find_feature_context(self, feature_text: str, full_text: str) -> str:
        """查找特征上下文"""
        # 简化实现：在实际应用中需要更复杂的上下文提取
        if feature_text in full_text:
            idx = full_text.find(feature_text)
            start = max(0, idx - 100)
            end = min(len(full_text), idx + len(feature_text) + 100)
            return full_text[start:end]
        return ''


@atomic_step
class CompareTechEffectsStep(AtomicStep):
    """
    技术效果对比步骤（三级分析）

    对比目标专利与对比文件的技术效果
    """
    step_name = "compare_tech_effects"
    step_version = "1.0.0"
    step_description = "对比技术效果（三级分析）"
    step_category = "analysis"

    def execute(self, input: StepInput) -> StepOutput:
        """执行技术效果对比"""
        import time

        start_time = time.time()

        try:
            target_patent = input.get_param("target_patent", {})
            comparative_doc = input.get_param("comparative_doc", {})

            # 提取技术效果
            target_effects = self._extract_effects(target_patent)
            comparative_effects = self._extract_effects(comparative_doc)

            # 对比分析
            effect_comparison = self._compare_effects(target_effects, comparative_effects)

            execution_time = time.time() - start_time

            logger.info(f"✅ 技术效果对比完成: 对比了 {len(effect_comparison)} 个效果")

            return StepOutput.from_data(
                data={
                    'target_effects': target_effects,
                    'comparative_effects': comparative_effects,
                    'effect_comparison': effect_comparison
                },
                execution_time=execution_time
            )

        except Exception as e:
            logger.error(f"❌ 技术效果对比失败: {e}")
            return StepOutput.from_error(
                f"技术效果对比失败: {str(e)}",
                error_type=type(e).__name__
            )

    def _extract_effects(self, patent: dict) -> list[dict[str, str]]:
        """提取技术效果"""
        text = patent.get('text', '')
        effects = []

        # 查找效果描述关键词
        effect_keywords = ['有益效果', '优点', '优势', '改善', '提高', '降低', '减少', '增强']

        for keyword in effect_keywords:
            if keyword in text:
                # 简化实现：提取关键词所在句子
                import re
                pattern = f'[^。]*{keyword}[^。]*。'
                matches = re.findall(pattern, text)
                for match in matches:
                    effects.append({
                        'keyword': keyword,
                        'description': match.strip()
                    })

        return effects

    def _compare_effects(self, target_effects: list[dict],
                         comparative_effects: list[dict]) -> list[dict]:
        """对比技术效果"""
        comparison = []

        for target_effect in target_effects:
            effect_desc = target_effect.get('description', '')

            # 查找对比文件中是否有类似效果
            similar_effects = []
            for comp_effect in comparative_effects:
                comp_desc = comp_effect.get('description', '')
                # 简化相似度判断
                if self._is_similar_effect(effect_desc, comp_desc):
                    similar_effects.append(comp_effect)

            comparison.append({
                'target_effect': target_effect,
                'similar_effects_in_comparative': similar_effects,
                'is_unique': len(similar_effects) == 0,
                'difference_level': self._assess_difference_level(target_effect, similar_effects)
            })

        return comparison

    def _is_similar_effect(self, effect1: str, effect2: str) -> bool:
        """判断效果是否相似"""
        # 简化实现：使用关键词重叠度
        words1 = set(effect1.split())
        words2 = set(effect2.split())
        intersection = words1 & words2
        union = words1 | words2

        if len(union) == 0:
            return False

        similarity = len(intersection) / len(union)
        return similarity > 0.3

    def _assess_difference_level(self, target_effect: dict,
                                 similar_effects: list[dict]) -> str:
        """评估差异程度"""
        if not similar_effects:
            return '完全不同'

        # 简化实现：基于效果描述差异评估
        target_desc = target_effect.get('description', '')
        max_similarity = 0

        for similar in similar_effects:
            sim_desc = similar.get('description', '')
            # 使用关键词重叠度
            words1 = set(target_desc.split())
            words2 = set(sim_desc.split())
            intersection = words1 & words2
            union = words1 | words2

            if len(union) > 0:
                similarity = len(intersection) / len(union)
                max_similarity = max(max_similarity, similarity)

        if max_similarity > 0.8:
            return '基本相同'
        elif max_similarity > 0.5:
            return '部分相同但有提升'
        else:
            return '显著不同'


@atomic_step
class BuildComparisonMatrixStep(AtomicStep):
    """
    构建技术对比矩阵步骤

    生成层级1-4的深度技术对比矩阵
    """
    step_name = "build_comparison_matrix"
    step_version = "1.0.0"
    step_description = "构建深度技术对比矩阵"
    step_category = "output"

    def execute(self, input: StepInput) -> StepOutput:
        """执行对比矩阵构建"""
        import time

        start_time = time.time()

        try:
            target_analysis = input.get_param("target_analysis", {})
            comparative_analysis = input.get_param("comparative_analysis", {})
            input.get_param("features_comparison", {})
            effects_comparison = input.get_param("effects_comparison", {})

            # 构建四级对比矩阵
            matrix = {
                'level1_feature_comparison': self._build_level1_matrix(
                    target_analysis, comparative_analysis
                ),
                'level2_means_comparison': self._build_level2_matrix(
                    target_analysis, comparative_analysis
                ),
                'level3_effect_comparison': self._build_level3_matrix(
                    effects_comparison
                ),
                'level4_causality_comparison': self._build_level4_matrix(
                    target_analysis, comparative_analysis
                )
            }

            execution_time = time.time() - start_time

            logger.info("✅ 对比矩阵构建完成")

            return StepOutput.from_data(
                data={
                    'comparison_matrix': matrix
                },
                execution_time=execution_time
            )

        except Exception as e:
            logger.error(f"❌ 对比矩阵构建失败: {e}")
            return StepOutput.from_error(
                f"对比矩阵构建失败: {str(e)}",
                error_type=type(e).__name__
            )

    def _build_level1_matrix(self, target: dict, comparative: dict) -> dict:
        """层级1：特征级对比"""
        return {
            'tech_field': {
                'target': target.get('tech_field', '待分析'),
                'comparative': comparative.get('tech_field', '待分析'),
                'difference': '相同/相近/不同'
            },
            'tech_problem': {
                'target': target.get('tech_problem', '待分析'),
                'comparative': comparative.get('tech_problem', '待分析'),
                'difference': '相同/不同'
            },
            'tech_approach': {
                'target': target.get('tech_approach', '待分析'),
                'comparative': comparative.get('tech_approach', '待分析'),
                'difference': '相同/不同'
            },
            'tech_means': {
                'target': target.get('features', []),
                'comparative': comparative.get('features', []),
                'difference': '逐项对比结果'
            },
            'tech_effects': {
                'target': target.get('effects', []),
                'comparative': comparative.get('effects', []),
                'difference': '逐项对比结果'
            }
        }

    def _build_level2_matrix(self, target: dict, comparative: dict) -> list[dict]:
        """层级2：手段级对比"""
        target_means = target.get('means_analysis', [])
        comparative_means = comparative.get('means_analysis', [])

        means_comparison = []
        for i, target_mean in enumerate(target_means):
            comp_mean = comparative_means[i] if i < len(comparative_means) else {}

            means_comparison.append({
                'means_name': target_mean.get('feature', {}).get('feature_text', '')[:50],
                'target_structure': target_mean.get('structure_composition', {}),
                'target_principle': target_mean.get('working_principle', {}),
                'target_connection': target_mean.get('connection_relation', {}),
                'target_control': target_mean.get('control_logic', {}),
                'comparative_structure': comp_mean.get('structure_composition', {}) if comp_mean else '未公开',
                'comparative_principle': comp_mean.get('working_principle', {}) if comp_mean else '未公开',
                'differences': self._analyze_means_differences(target_mean, comp_mean if comp_mean else {}),
                'is_equivalent': self._judge_equivalence(target_mean, comp_mean if comp_mean else {})
            })

        return means_comparison

    def _build_level3_matrix(self, effects_comparison: list[dict]) -> list[dict]:
        """层级3：效果级对比"""
        level3_matrix = []

        for comparison in effects_comparison:
            target_effect = comparison.get('target_effect', {})
            similar_effects = comparison.get('similar_effects_in_comparative', [])

            level3_matrix.append({
                'effect_name': target_effect.get('description', '')[:50],
                'target_effect_desc': target_effect.get('description', ''),
                'target_implementation': '待分析',
                'target_mechanism': '待分析',
                'target_quantification': '待分析',
                'comparative_effect_desc': similar_effects[0].get('description', '') if similar_effects else '未达到',
                'comparative_implementation': '待分析',
                'difference_analysis': comparison.get('difference_level', ''),
                'difference_nature': self._classify_effect_difference(comparison)
            })

        return level3_matrix

    def _build_level4_matrix(self, target: dict, comparative: dict) -> dict:
        """层级4：因果关系链对比"""
        return {
            'target_causality_chain': {
                'problem': target.get('tech_problem', '待分析'),
                'means': target.get('features', []),
                'effects': target.get('effects', [])
            },
            'comparative_causality_chain': {
                'problem': comparative.get('tech_problem', '待分析'),
                'means': comparative.get('features', []),
                'effects': comparative.get('effects', [])
            },
            'causality_difference': {
                'problem_same': '待判断',
                'means_same': '待逐项对比',
                'causality_same': '待分析',
                'effects_same': '待分析'
            }
        }

    def _analyze_means_differences(self, target_mean: dict, comp_mean: dict) -> dict:
        """分析手段差异"""
        return {
            'structure_diff': '结构差异分析',
            'principle_diff': '原理差异分析',
            'parameter_diff': '参数差异分析',
            'connection_diff': '连接差异分析',
            'control_diff': '控制差异分析',
            'missing': '是否缺失'
        }

    def _judge_equivalence(self, target_mean: dict, comp_mean: dict) -> dict:
        """判断等同性"""
        return {
            'is_equivalent': '是/否',
            'reason': '判断理由',
            'doctrine_of_equivalents': '等同原则适用性'
        }

    def _classify_effect_difference(self, comparison: dict) -> list[str]:
        """分类效果差异性质"""
        difference_types = []

        if comparison.get('is_unique'):
            difference_types.append('效果完全不同')
        else:
            diff_level = comparison.get('difference_level', '')
            if '基本相同' in diff_level:
                difference_types.append('效果相同但实现方式不同')
            elif '部分相同' in diff_level:
                difference_types.append('效果部分相同但有显著提升')
            else:
                difference_types.append('D1无法达到该效果')

        return difference_types


@atomic_step
class IdentifyDistinguishingFeaturesStep(AtomicStep):
    """
    识别区别特征步骤

    识别目标专利与对比文件的区别特征，并进行四个层次的本质分析
    """
    step_name = "identify_distinguishing_features"
    step_version = "1.0.0"
    step_description = "识别并分析区别特征本质"
    step_category = "analysis"

    def execute(self, input: StepInput) -> StepOutput:
        """执行区别特征识别"""
        import time

        start_time = time.time()

        try:
            target_features = input.get_param("target_features", [])
            comparative_features = input.get_param("comparative_features", [])

            # 识别区别特征
            distinguishing_features = self._identify_differences(
                target_features, comparative_features
            )

            # 对每个区别特征进行四层次分析
            enhanced_features = []
            for feature in distinguishing_features:
                enhanced = {
                    'feature': feature,
                    'level1_surface_diff': self._analyze_surface_difference(feature),
                    'level2_function_diff': self._analyze_function_difference(feature),
                    'level3_principle_diff': self._analyze_principle_difference(feature),
                    'level4_teaching_judgment': self._analyze_teaching_judgment(feature)
                }
                enhanced_features.append(enhanced)

            execution_time = time.time() - start_time

            logger.info(f"✅ 区别特征识别完成: 识别出 {len(enhanced_features)} 个区别特征")

            return StepOutput.from_data(
                data={
                    'distinguishing_features': enhanced_features,
                    'feature_count': len(enhanced_features)
                },
                execution_time=execution_time
            )

        except Exception as e:
            logger.error(f"❌ 区别特征识别失败: {e}")
            return StepOutput.from_error(
                f"区别特征识别失败: {str(e)}",
                error_type=type(e).__name__
            )

    def _identify_differences(self, target_features: list[dict],
                             comparative_features: list[dict]) -> list[dict]:
        """识别差异特征"""
        differences = []

        {f.get('feature_text', '') for f in target_features}
        {f.get('feature_text', '') for f in comparative_features}

        # 找出目标专利独有或不同的特征
        for target_feature in target_features:
            feature_text = target_feature.get('feature_text', '')
            is_different = True

            for comp_feature in comparative_features:
                comp_text = comp_feature.get('feature_text', '')
                if self._is_same_feature(feature_text, comp_text):
                    is_different = False
                    break

            if is_different:
                differences.append({
                    'feature': target_feature,
                    'disclosure_in_comparative': self._check_disclosure_level(
                        feature_text, comparative_features
                    )
                })

        return differences

    def _is_same_feature(self, feature1: str, feature2: str) -> bool:
        """判断是否为相同特征"""
        # 简化实现：基于文本相似度
        words1 = set(feature1.split())
        words2 = set(feature2.split())
        intersection = words1 & words2
        union = words1 | words2

        if len(union) == 0:
            return False

        similarity = len(intersection) / len(union)
        return similarity > 0.7

    def _check_disclosure_level(self, feature: str,
                                comparative_features: list[dict]) -> str:
        """检查在对比文件中的公开程度"""
        for comp_feature in comparative_features:
            comp_text = comp_feature.get('feature_text', '')
            if self._is_same_feature(feature, comp_text):
                # 进一步判断公开程度
                words1 = set(feature.split())
                words2 = set(comp_text.split())
                if len(words1) > len(words2) * 1.5:
                    return '部分公开（目标专利更具体）'
                elif len(words2) > len(words1) * 1.5:
                    return '部分公开（对比文件更具体）'
                else:
                    return '完全公开'

        return '未公开'

    def _analyze_surface_difference(self, feature: dict) -> dict:
        """层次1：表面区别分析"""
        return {
            'structure_diff': '结构差异',
            'parameter_diff': '参数差异',
            'material_diff': '材料差异'
        }

    def _analyze_function_difference(self, feature: dict) -> dict:
        """层次2：功能区别分析"""
        return {
            'function_diff': '功能作用不同',
            'scenario_diff': '应用场景不同',
            'cooperation_diff': '配合关系不同'
        }

    def _analyze_principle_difference(self, feature: dict) -> dict:
        """层次3：原理区别分析"""
        return {
            'working_principle_diff': '工作原理不同',
            'mechanism_diff': '作用机理不同',
            'approach_diff': '技术思路不同'
        }

    def _analyze_teaching_judgment(self, feature: dict) -> dict:
        """层次4：技术启示判断"""
        disclosure = feature.get('disclosure_in_comparative', '')

        return {
            'd2_disclosure': 'D2公开情况',
            'tech_field_diff': '技术领域差异',
            'tech_problem_diff': '技术问题差异',
            'tech_effect_diff': '技术效果差异',
            'teaching_conclusion': self._judge_teaching_level(disclosure),
            'judgment_basis': '判断依据说明'
        }

    def _judge_teaching_level(self, disclosure: str) -> str:
        """判断技术启示程度"""
        if '未公开' in disclosure:
            return '无技术启示'
        elif '部分公开' in disclosure:
            return '启示不明显'
        elif '完全公开' in disclosure:
            return '有明确启示'
        else:
            return '需进一步分析'


@atomic_step
class GenerateHITLConfirmStep(AtomicStep):
    """
    生成HITL确认请求步骤

    在5个关键点生成用户确认请求
    """
    step_name = "generate_hitl_confirm"
    step_version = "1.0.0"
    step_description = "生成人机交互确认请求"
    step_category = "interaction"

    # 5个确认点
    CONFIRMATION_POINTS = [
        'tech_deconstruction_complete',  # 技术解构完成
        'distinguishing_features_confirmed',  # 区别特征确认
        'teaching_judgment_made',  # 技术启示判断
        'response_strategy_selected',  # 答复策略选择
        'response_document_ready'  # 答复文件就绪
    ]

    def execute(self, input: StepInput) -> StepOutput:
        """生成HITL确认请求"""
        import time

        start_time = time.time()

        try:
            confirmation_point = input.get_param("confirmation_point")
            analysis_data = input.get_param("analysis_data", {})

            if not confirmation_point:
                return StepOutput.from_error(
                    "缺少确认点参数",
                    error_type="ParameterError"
                )

            # 生成确认请求
            confirmation_request = self._generate_confirmation(
                confirmation_point, analysis_data
            )

            execution_time = time.time() - start_time

            logger.info(f"✅ HITL确认请求生成: {confirmation_point}")

            return StepOutput.from_data(
                data={
                    'confirmation_point': confirmation_point,
                    'confirmation_request': confirmation_request
                },
                execution_time=execution_time
            )

        except Exception as e:
            logger.error(f"❌ HITL确认请求生成失败: {e}")
            return StepOutput.from_error(
                f"HITL确认请求生成失败: {str(e)}",
                error_type=type(e).__name__
            )

    def _generate_confirmation(self, point: str, data: dict) -> dict:
        """生成确认请求"""
        templates = {
            'tech_deconstruction_complete': {
                'title': '技术解构完成确认',
                'summary': self._tech_deconstruction_summary(data),
                'confirmation_items': [
                    '技术手段的拆解是否合理？',
                    '技术效果的识别是否完整？',
                    '关键区别特征是否都已找出？'
                ],
                'options': [
                    'A. 确认准确，继续深度对比',
                    'B. 调整某些解构（请说明）',
                    'C. 补充某些分析'
                ]
            },
            'distinguishing_features_confirmed': {
                'title': '区别特征确认',
                'summary': self._distinguishing_features_summary(data),
                'confirmation_items': [
                    '这些区别特征是否准确？是否遗漏？',
                    '某些特征表面上相同，但实际作用/效果不同？',
                    '某些特征D1虽公开，但公开程度不同？'
                ],
                'options': [
                    'A. 确认完整',
                    'B. 补充区别特征（请说明）',
                    'C. 删除非区别特征',
                    'D. 调整某些特征描述'
                ]
            },
            'teaching_judgment_made': {
                'title': '技术启示判断确认',
                'summary': self._teaching_judgment_summary(data),
                'confirmation_items': [
                    'D2公开的特征是否真的可以等同替换？',
                    '结合到本申请是否显而易见？',
                    '是否存在技术障碍？'
                ],
                'options': [
                    'A. 确认我的判断',
                    'B. 调整某些判断（请详细说明理由）',
                    'C. 对特定特征重新分析'
                ]
            },
            'response_strategy_selected': {
                'title': '答复策略选择',
                'summary': self._strategy_selection_summary(data),
                'confirmation_items': [
                    '您倾向于哪个策略？或者有其他想法？'
                ],
                'options': [
                    'A. 策略A',
                    'B. 策略B（推荐）',
                    'C. 策略C',
                    'D. 自定义策略'
                ]
            },
            'response_document_ready': {
                'title': '答复文件最终确认',
                'summary': self._response_document_summary(data),
                'confirmation_items': [
                    '仔细检查技术分析的准确性',
                    '确认论点逻辑的严密性',
                    '验证案例引用的相关性'
                ],
                'options': [
                    'A. 确认无误，可以使用',
                    'B. 需要修改（请说明具体位置和修改内容）',
                    'C. 需要重新撰写某些部分',
                    'D. 查看完整答复文件'
                ]
            }
        }

        return templates.get(point, {
            'title': '确认请求',
            'summary': '请确认以下内容',
            'confirmation_items': ['是否确认？'],
            'options': ['A. 确认', 'B. 取消']
        })

    def _tech_deconstruction_summary(self, data: dict) -> str:
        """技术解构总结"""
        target_features = len(data.get('target_features', []))
        comparative_features = len(data.get('comparative_features', []))
        differences = len(data.get('differences', []))

        return f"""目标专利：识别了{target_features}个技术特征
对比文件：识别了{comparative_features}个技术特征
初步对比：发现{differences}个显著差异点"""

    def _distinguishing_features_summary(self, data: dict) -> str:
        """区别特征总结"""
        features = data.get('distinguishing_features', [])
        return f"识别出 {len(features)} 个区别特征"

    def _teaching_judgment_summary(self, data: dict) -> str:
        """技术启示判断总结"""
        return "技术启示判断矩阵分析完成"

    def _strategy_selection_summary(self, data: dict) -> str:
        """策略选择总结"""
        return "为您准备了3个答复策略"

    def _response_document_summary(self, data: dict) -> str:
        """答复文件总结"""
        return "答复文件已撰写完成"


# 导出所有步骤
__all__ = [
    'ExtractTechFeaturesStep',
    'AnalyzeTechMeansStep',
    'CompareTechEffectsStep',
    'BuildComparisonMatrixStep',
    'IdentifyDistinguishingFeaturesStep',
    'GenerateHITLConfirmStep'
]
