#!/usr/bin/env python3
"""
创造性分析原子步骤
Inventive Step Analysis Atomic Steps

提供基于"三步法"的专利创造性分析步骤
"""

import logging
import sys
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from atomic_steps.base import AtomicStep, StepInput, StepOutput
from atomic_steps.clients import encode_text, get_qdrant_client
from atomic_steps.registry import atomic_step

logger = logging.getLogger(__name__)


@atomic_step
class FindClosestPriorArtStep(AtomicStep):
    """
    查找最接近的现有技术步骤

    "三步法"第一步：确定最接近的现有技术
    """
    step_name = "find_closest_prior_art"
    step_version = "1.0.0"
    step_description = "查找最接近的现有技术（三步法第一步）"
    step_category = "analysis"

    # 默认配置
    DEFAULT_LIMIT = 20
    DEFAULT_THRESHOLD = 0.4

    def execute(self, input: StepInput) -> StepOutput:
        """执行查找最接近的现有技术"""
        import time

        start_time = time.time()

        try:
            # 获取目标专利信息
            target_patent = input.get_param("target_patent", {})
            ipc_class = target_patent.get("ipc_main_class")
            application_date = target_patent.get("application_date")
            title = target_patent.get("title", "")
            abstract = target_patent.get("abstract", "")

            if not ipc_class:
                return StepOutput.from_error(
                    "缺少IPC分类号",
                    error_type="ParameterError"
                )

            logger.info(f"🔍 查找最接近的现有技术: IPC={ipc_class}")

            # 获取Qdrant客户端
            client = get_qdrant_client()
            if not client:
                return StepOutput.from_error(
                    "无法连接到Qdrant服务",
                    error_type="ConnectionError"
                )

            # 向量检索语义相似的专利
            query_text = f"{title} {abstract}"
            query_vector = self._get_query_vector(input, query_text)

            if not query_vector:
                return StepOutput.from_error(
                    "无法获取查询向量",
                    error_type="VectorError"
                )

            # 检索
            search_result = client.query_points(
                collection_name="patents_data_1024",
                query=query_vector,
                limit=input.get_param("limit", self.DEFAULT_LIMIT),
                score_threshold=input.get_param("threshold", self.DEFAULT_THRESHOLD)
            )

            # 筛选：相同IPC分类、申请日早于目标专利
            candidates = self._filter_candidates(
                search_result.points,
                ipc_class,
                application_date
            )

            # 选择最接近的现有技术
            closest = self._select_closest(candidates, target_patent)

            execution_time = time.time() - start_time

            logger.info(f"✅ 查找最接近的现有技术完成: 找到 {len(candidates)} 个候选")

            return StepOutput.from_data(
                data={
                    'candidates': candidates,
                    'closest_prior_art': closest,
                    'total_candidates': len(candidates)
                },
                execution_time=execution_time
            )

        except Exception as e:
            logger.error(f"❌ 查找最接近的现有技术失败: {e}")
            return StepOutput.from_error(
                f"查找最接近的现有技术失败: {str(e)}",
                error_type=type(e).__name__
            )

    def _get_query_vector(self, input: StepInput, query_text: str) -> list[float | None]:
        """获取查询向量

        优先从参数中获取向量，否则使用BGE-M3实时编码
        """
        # 从参数中获取
        query_vector = input.get_param("query_vector")
        if query_vector:
            return query_vector

        # 使用统一的encode_text函数实时编码
        try:
            vector = encode_text(query_text, normalize=True)
            if vector:
                logger.debug(f"查询文本已编码: {query_text[:50]}...")
                return vector
        except Exception as e:
            logger.warning(f"查询文本编码失败: {e}")

        return None

    def _filter_candidates(
        self,
        points: list,
        ipc_class: str,
        application_date: str
    ) -> list[dict]:
        """筛选候选现有技术"""
        candidates = []

        for point in points:
            payload = point.payload or {}

            # 检查IPC分类
            candidate_ipc = payload.get("ipc_main_class", "")
            if not self._same_ipc_class(candidate_ipc, ipc_class):
                continue

            # 检查申请日
            candidate_date = payload.get("application_date", "")
            if candidate_date >= application_date:
                continue

            candidates.append({
                'id': point.id,
                'score': point.score,
                'payload': payload
            })

        return candidates

    def _same_ipc_class(self, ipc1: str, ipc2: str) -> bool:
        """判断是否相同IPC分类（大类级别）"""
        if not ipc1 or not ipc2:
            return False
        return ipc1[:4] == ipc2[:4]

    def _select_closest(self, candidates: list[dict], target: dict) -> dict | None:
        """选择最接近的现有技术"""
        if not candidates:
            return None

        # 按相似度和特征重合度排序
        for candidate in candidates:
            # 计算特征重合度
            payload = candidate['payload']
            target_features = set(target.get('features', []))
            candidate_features = set(payload.get('features', []))

            overlap = len(target_features & candidate_features)
            total = len(target_features)
            candidate['feature_overlap'] = overlap / total if total > 0 else 0

        # 综合排序
        candidates.sort(key=lambda x: (x['feature_overlap'], x['score']), reverse=True)

        return candidates[0] if candidates else None


@atomic_step
class IdentifyDistinguishingFeaturesStep(AtomicStep):
    """
    识别区别特征步骤

    "三步法"第二步：确定区别特征和实际解决的技术问题
    """
    step_name = "identify_distinguishing_features"
    step_version = "1.0.0"
    step_description = "识别区别特征和技术问题（三步法第二步）"
    step_category = "analysis"

    def execute(self, input: StepInput) -> StepOutput:
        """执行区别特征识别"""
        import time

        start_time = time.time()

        try:
            # 获取目标专利和最接近的现有技术
            target_patent = input.get_param("target_patent", {})
            closest_prior_art = input.get_param("closest_prior_art", {})

            if not target_patent or not closest_prior_art:
                return StepOutput.from_error(
                    "缺少目标专利或最接近的现有技术",
                    error_type="ParameterError"
                )

            # 提取技术特征
            target_features = set(target_patent.get('features', []))
            prior_features = set(closest_prior_art.get('payload', {}).get('features', []))

            # 识别区别特征
            distinguishing_features = target_features - prior_features

            # 确定实际解决的技术问题
            technical_problem = self._determine_technical_problem(
                distinguishing_features,
                target_patent,
                closest_prior_art
            )

            # 分析技术效果
            technical_effects = self._analyze_technical_effects(
                distinguishing_features,
                target_patent
            )

            execution_time = time.time() - start_time

            logger.info(f"✅ 区别特征识别完成: {len(distinguishing_features)} 个区别特征")

            return StepOutput.from_data(
                data={
                    'distinguishing_features': list(distinguishing_features),
                    'technical_problem': technical_problem,
                    'technical_effects': technical_effects,
                    'target_features': list(target_features),
                    'prior_features': list(prior_features),
                    'feature_comparison': {
                        'common': list(target_features & prior_features),
                        'distinguishing': list(distinguishing_features)
                    }
                },
                execution_time=execution_time
            )

        except Exception as e:
            logger.error(f"❌ 区别特征识别失败: {e}")
            return StepOutput.from_error(
                f"区别特征识别失败: {str(e)}",
                error_type=type(e).__name__
            )

    def _determine_technical_problem(
        self,
        distinguishing_features: set,
        target_patent: dict,
        closest_prior_art: dict
    ) -> str:
        """确定实际解决的技术问题"""
        # 基于区别特征确定技术问题
        if not distinguishing_features:
            return "无区别特征"

        # 从目标专利的说明书或背景技术中提取技术问题
        problem = target_patent.get('technical_problem', '')

        if problem:
            return problem

        # 如果没有明确的技术问题，基于区别特征推断
        prior_art_problem = closest_prior_art.get('payload', {}).get('technical_problem', '')
        return f"改进{prior_art_problem or '现有技术'}的问题"

    def _analyze_technical_effects(
        self,
        distinguishing_features: set,
        target_patent: dict
    ) -> list[dict]:
        """分析技术效果"""
        effects = []

        # 从目标专利中提取技术效果
        patent_effects = target_patent.get('technical_effects', [])
        if isinstance(patent_effects, list):
            for effect in patent_effects:
                effects.append({
                    'effect': effect,
                    'type': self._classify_effect_type(effect)
                })

        return effects

    def _classify_effect_type(self, effect: str) -> str:
        """分类技术效果类型"""
        effect_lower = effect.lower()

        if any(word in effect_lower for word in ['提升', '提高', '增加', '改善', '优化']):
            if '速度' in effect_lower or '性能' in effect_lower:
                return '性能提升'
            elif '效率' in effect_lower:
                return '效率提升'
            elif '精度' in effect_lower:
                return '精度提升'
            else:
                return '性能提升'

        elif any(word in effect_lower for word in ['降低', '减少', '节约', '节省']):
            if '成本' in effect_lower:
                return '成本降低'
            elif '时间' in effect_lower:
                return '时间节省'
            else:
                return '资源节约'

        elif any(word in effect_lower for word in ['简化', '减少', '集成', '整合']):
            return '结构简化'

        elif any(word in effect_lower for word in ['增强', '扩展', '多功能']):
            return '功能增强'

        else:
            return '其他'


@atomic_step
class AssessTechnicalTeachingStep(AtomicStep):
    """
    技术启示判断步骤

    "三步法"第三步：判断是否显而易见
    """
    step_name = "assess_technical_teaching"
    step_version = "1.0.0"
    step_description = "判断是否存在技术启示（三步法第三步）"
    step_category = "analysis"

    def execute(self, input: StepInput) -> StepOutput:
        """执行技术启示判断"""
        import time

        start_time = time.time()

        try:
            distinguishing_features = input.get_param("distinguishing_features", [])
            closest_prior_art = input.get_param("closest_prior_art", {})

            if not distinguishing_features:
                return StepOutput.from_error(
                    "缺少区别特征",
                    error_type="ParameterError"
                )

            logger.info(f"🔍 技术启示判断: {len(distinguishing_features)} 个区别特征")

            # 获取Qdrant客户端
            client = get_qdrant_client()
            if not client:
                return StepOutput.from_error(
                    "无法连接到Qdrant服务",
                    error_type="ConnectionError"
                )

            # 对每个区别特征检索技术启示
            teaching_analysis = []
            for feature in distinguishing_features:
                analysis = self._analyze_feature_teaching(
                    client,
                    feature,
                    closest_prior_art
                )
                teaching_analysis.append(analysis)

            # 综合判断
            conclusion = self._make_conclusion(teaching_analysis)

            # 检索类似案例
            similar_cases = self._retrieve_similar_cases(client, teaching_analysis)

            execution_time = time.time() - start_time

            logger.info(f"✅ 技术启示判断完成: {conclusion['has_teaching']}")

            return StepOutput.from_data(
                data={
                    'teaching_analysis': teaching_analysis,
                    'conclusion': conclusion,
                    'similar_cases': similar_cases
                },
                execution_time=execution_time
            )

        except Exception as e:
            logger.error(f"❌ 技术启示判断失败: {e}")
            return StepOutput.from_error(
                f"技术启示判断失败: {str(e)}",
                error_type=type(e).__name__
            )

    def _analyze_feature_teaching(
        self,
        client,
        feature: str,
        closest_prior_art: dict
    ) -> dict:
        """分析单个特征的技术启示"""
        # 向量检索该特征是否被其他现有技术公开
        query_vector = self._get_feature_vector(client, feature)

        if not query_vector:
            return {
                'feature': feature,
                'found_in_prior_art': False,
                'teaching_exists': False,
                'analysis': '无法检索'
            }

        # 检索
        search_result = client.query_points(
            collection_name="patents_data_1024",
            query=query_vector,
            limit=5,
            score_threshold=0.5
        )

        # 分析检索结果
        found = len(search_result.points) > 0

        # 判断是否存在结合启示
        has_teaching = False
        teaching_details = []

        if found:
            for point in search_result.points:
                payload = point.payload or {}
                prior_art_field = payload.get('ipc_main_class', '')
                closest_field = closest_prior_art.get('payload', {}).get('ipc_main_class', '')

                # 同一技术领域 → 可能存在启示
                if prior_art_field[:4] == closest_field[:4]:
                    has_teaching = True
                    teaching_details.append({
                        'source': payload.get('patent_id', ''),
                        'field': prior_art_field,
                        'relevance': 'same_field'
                    })

        return {
            'feature': feature,
            'found_in_prior_art': found,
            'teaching_exists': has_teaching,
            'teaching_details': teaching_details,
            'analysis': self._generate_analysis(feature, found, has_teaching)
        }

    def _get_feature_vector(self, client, feature: str) -> list[float | None]:
        """获取特征的向量表示

        使用BGE-M3模型将特征文本编码为向量
        """
        try:
            # 使用统一的encode_text函数
            vector = encode_text(feature, normalize=True)
            if vector is None:
                logger.error(f"向量编码失败: {feature}")
                return None
            return vector
        except Exception as e:
            logger.error(f"获取特征向量失败: {e}")
            return None

    def _generate_analysis(self, feature: str, found: bool, has_teaching: bool) -> str:
        """生成分析文本"""
        if not found:
            return f"区别特征{feature}未被其他现有技术公开"
        elif has_teaching:
            return f"区别特征{feature}被其他现有技术公开，且可能存在结合启示"
        else:
            return f"区别特征{feature}被其他现有技术公开，但不存在明确的结合启示"

    def _make_conclusion(self, teaching_analysis: list[dict]) -> dict:
        """综合判断结论"""
        # 统计有技术启示的特征数
        with_teaching = sum(1 for a in teaching_analysis if a['teaching_exists'])
        total_features = len(teaching_analysis)

        # 判断是否显而易见
        has_teaching = with_teaching > total_features / 2

        confidence = with_teaching / total_features if total_features > 0 else 0

        return {
            'has_teaching': has_teaching,
            'features_with_teaching': with_teaching,
            'total_features': total_features,
            'confidence': confidence,
            'conclusion': self._format_conclusion(has_teaching, confidence)
        }

    def _format_conclusion(self, has_teaching: bool, confidence: float) -> str:
        """格式化结论"""
        if has_teaching:
            return f"存在技术启示，可能不具备创造性（置信度: {confidence:.1%}）"
        else:
            return f"不存在明显的技术启示，可能具备创造性（置信度: {confidence:.1%}）"

    def _retrieve_similar_cases(self, client, teaching_analysis: list[dict]) -> list[dict]:
        """检索类似案例"""
        # 检索相关的复审无效案例
        query = "创造性 技术启示 三步法"
        query_vector = self._get_feature_vector(client, query)

        if not query_vector:
            return []

        search_result = client.query_points(
            collection_name="patent_decisions",
            query=query_vector,
            limit=5,
            score_threshold=0.5
        )

        cases = []
        for point in search_result.points:
            payload = point.payload or {}
            cases.append({
                'id': point.id,
                'score': point.score,
                'case_number': payload.get('case_number', ''),
                'decision': payload.get('decision', ''),
                'reasoning': payload.get('reasoning', '')
            })

        return cases


@atomic_step
class InventiveStepAnalysisStep(AtomicStep):
    """
    创造性分析综合步骤

    完整的"三步法"创造性分析
    """
    step_name = "inventive_step_analysis"
    step_version = "1.0.0"
    step_description = "完整的创造性分析（三步法）"
    step_category = "analysis"

    def execute(self, input: StepInput) -> StepOutput:
        """执行完整的创造性分析"""
        import time

        start_time = time.time()

        try:
            target_patent = input.get_param("target_patent", {})

            logger.info(f"🔍 开始创造性分析: {target_patent.get('title', '')}")

            # 第一步：查找最接近的现有技术
            closest_prior_art_result = self._step1_find_closest_prior_art(input)
            if not closest_prior_art_result.success:
                return closest_prior_art_result

            closest = closest_prior_art_result.data.get('closest_prior_art')

            # 第二步：识别区别特征
            distinguishing_result = self._step2_identify_features(input, closest)
            if not distinguishing_result.success:
                return distinguishing_result

            # 第三步：判断技术启示
            teaching_result = self._step3_assess_teaching(input, distinguishing_result.data)

            # 综合分析
            analysis_report = self._generate_report(
                target_patent,
                closest_prior_art_result.data,
                distinguishing_result.data,
                teaching_result.data
            )

            execution_time = time.time() - start_time

            logger.info("✅ 创造性分析完成")

            return StepOutput.from_data(
                data=analysis_report,
                execution_time=execution_time
            )

        except Exception as e:
            logger.error(f"❌ 创造性分析失败: {e}")
            return StepOutput.from_error(
                f"创造性分析失败: {str(e)}",
                error_type=type(e).__name__
            )

    def _step1_find_closest_prior_art(self, input: StepInput) -> StepOutput:
        """第一步：查找最接近的现有技术"""
        step = FindClosestPriorArtStep()
        return step.execute(input)

    def _step2_identify_features(self, input: StepInput, closest: dict) -> StepOutput:
        """第二步：识别区别特征"""
        # 创建新的输入
        new_input = StepInput(
            query=input.query,
            params={
                **input.params,
                'closest_prior_art': closest
            }
        )

        step = IdentifyDistinguishingFeaturesStep()
        return step.execute(new_input)

    def _step3_assess_teaching(self, input: StepInput, distinguishing_data: dict) -> StepOutput:
        """第三步：判断技术启示"""
        new_input = StepInput(
            query=input.query,
            params={
                **input.params,
                'distinguishing_features': distinguishing_data.get('distinguishing_features', []),
                'closest_prior_art': distinguishing_data.get('target_features', [])
            }
        )

        step = AssessTechnicalTeachingStep()
        return step.execute(new_input)

    def _generate_report(
        self,
        target_patent: dict,
        step1_result: dict,
        step2_result: dict,
        step3_result: dict
    ) -> dict:
        """生成分析报告"""
        conclusion = step3_result.get('conclusion', {})

        return {
            'target_patent': target_patent.get('title', ''),
            'patent_number': target_patent.get('patent_number', ''),

            'step1_closest_prior_art': step1_result.get('closest_prior_art'),

            'step2_distinguishing_features': step2_result.get('distinguishing_features'),
            'step2_technical_problem': step2_result.get('technical_problem'),
            'step2_technical_effects': step2_result.get('technical_effects'),

            'step3_teaching_analysis': step3_result.get('teaching_analysis'),
            'step3_conclusion': conclusion.get('conclusion', ''),
            'step3_has_teaching': conclusion.get('has_teaching', False),
            'step3_confidence': conclusion.get('confidence', 0),

            'overall_conclusion': self._make_overall_conclusion(
                step1_result,
                step2_result,
                step3_result
            ),

            'authorization_probability': self._estimate_authorization_probability(
                step3_result
            ),

            'similar_cases': step3_result.get('similar_cases', [])
        }

    def _make_overall_conclusion(
        self,
        step1_result: dict,
        step2_result: dict,
        step3_result: dict
    ) -> str:
        """做出整体结论"""
        has_teaching = step3_result.get('conclusion', {}).get('has_teaching', False)

        if has_teaching:
            return "目标专利权利要求可能不具备《专利法》第22条第3款规定的创造性"
        else:
            return "目标专利权利要求可能具备《专利法》第22条第3款规定的创造性"

    def _estimate_authorization_probability(self, step3_result: dict) -> dict:
        """估算授权概率"""
        has_teaching = step3_result.get('conclusion', {}).get('has_teaching', False)
        confidence = step3_result.get('conclusion', {}).get('confidence', 0.5)

        if has_teaching:
            # 有技术启示，授权概率较低
            probability = 0.3 + (1 - confidence) * 0.2
            level = '低'
        else:
            # 无技术启示，授权概率较高
            probability = 0.6 + confidence * 0.3
            level = '高' if probability > 0.7 else '中'

        return {
            'probability': probability,
            'level': level,
            'percentage': f"{probability * 100:.0f}%"
        }


# 导出所有步骤
__all__ = [
    'FindClosestPriorArtStep',
    'IdentifyDistinguishingFeaturesStep',
    'AssessTechnicalTeachingStep',
    'InventiveStepAnalysisStep'
]
