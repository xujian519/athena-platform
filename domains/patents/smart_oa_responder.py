#!/usr/bin/env python3
from __future__ import annotations

"""
智能意见答复系统
Smart Office Action Response System

基于赫布定律和案例学习构建的智能答复系统:
- 成功案例库:从历史成功答复中学习
- 赫布学习:相似案例协同激活,强化成功模式
- 策略推荐:基于审查意见类型推荐最佳答复策略
- 成功概率:预测答复成功的可能性

v0.2.0 增强版特性:
- ✅ 集成动态提示词系统(2442个AI术语知识图谱)
- ✅ 使用125万+实体专利知识图谱
- ✅ 多维上下文感知分析
- ✅ 智能提示词效果评估
- ✅ 闭环学习优化机制

作者: 小诺·双鱼公主
创建时间: 2025-12-24
版本: v0.2.0 "智能增强"
"""

import json
import logging

# 导入相关模块
import sys
from collections import Counter
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any

from core.logging_config import setup_logging

sys.path.insert(0, str(Path(__file__).parent.parent))

from core.patents.case_database import (
    CaseStatus,
    CaseType,
    PatentCase,
    TechnicalField,
    get_patent_case_db,
)
from core.patents.qualitative_rules import get_qualitative_rule_engine

from domains.biology.hebbian_optimizer import get_hebbian_optimizer

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = setup_logging()


class RejectionType(Enum):
    """驳回类型"""

    NOVELTY = "novelty"  # 新颖性
    INVENTIVENESS = "inventiveness"  # 创造性
    UTILITY = "utility"  # 实用性
    CLARITY = "clarity"  # 清晰度
    SUPPORT = "support"  # 说明书支持
    UNITY = "unity"  # 单一性


class ResponseStrategy(Enum):
    """答复策略"""

    ARGUE_DIFFERENCES = "argue_differences"  # 争辩区别特征
    MODIFY_CLAIMS = "modify_claims"  # 修改权利要求
    AMEND_DESCRIPTION = "amend_description"  # 修改说明书
    COMBINE = "combine"  # 组合策略
    ABANDON = "abandon"  # 放弃


@dataclass
class OfficeAction:
    """审查意见"""

    oa_id: str
    rejection_type: RejectionType
    rejection_reason: str  # 驳回理由
    prior_art_references: list[str]  # 对比文件
    cited_claims: list[int]  # 被引用的权利要求

    # 审查员观点
    examiner_arguments: list[str]  # 审查员论点
    missing_features: list[str]  # 缺失的技术特征

    # 元数据
    received_date: str
    response_deadline: str


@dataclass
class ResponsePlan:
    """答复方案"""

    plan_id: str
    oa_id: str
    recommended_strategy: ResponseStrategy
    strategy_rationale: str  # 策略理由

    # 具体答复内容
    arguments: list[str]  # 争辩论点
    claim_modifications: list[str]  # 权利要求修改建议
    additional_evidence: list[str]  # 补充证据建议

    # 预测
    success_probability: float  # 成功概率
    confidence: float  # 置信度

    # 参考案例
    reference_cases: list[str]

    # 元数据
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class ResponseResult:
    """答复结果"""

    response_id: str
    plan_id: str
    final_response: str  # 最终答复文本
    submitted_date: str
    final_outcome: str  # 最终结果
    success: bool  # 是否成功


class SmartOfficeActionResponder:
    """
    智能意见答复系统

    核心思想:
    1. 赫布学习:相似案例协同激活
    2. 案例推理:从成功案例中学习策略
    3. 策略优化:综合多种策略选择最优
    4. 概率预测:基于历史数据预测成功率
    """

    def __init__(self):
        """初始化答复系统"""
        self.name = "智能意见答复系统"
        self.version = "v0.2.0"  # 升级版本号

        # 子系统
        self.case_db = get_patent_case_db()
        self.rule_engine = get_qualitative_rule_engine()
        self.hebbian_optimizer = get_hebbian_optimizer()

        # 动态提示词生成器（新增）
        self.prompt_generator = None
        try:
            from core.intelligence.enhanced_dynamic_prompt_generator import (
                get_enhanced_dynamic_prompt_generator,
            )

            self.prompt_generator = get_enhanced_dynamic_prompt_generator()
            logger.info("✅ 动态提示词生成器初始化成功")
        except Exception as e:
            logger.warning(f"⚠️ 动态提示词生成器初始化失败: {e}")

        # 答复历史
        self.response_history: list[ResponseResult] = []

        # 策略统计
        self.strategy_stats: dict[str, dict[str, Any] = {}

        # 动态提示词缓存（新增）
        self.dynamic_prompt_cache: dict[str, Any] = {}

        # Prometheus性能监控（新增）
        self.prompt_metrics = None
        try:
            from core.patents.dynamic_prompt_metrics import get_dynamic_prompt_metrics

            self.prompt_metrics = get_dynamic_prompt_metrics()
            logger.info("✅ 动态提示词性能监控初始化成功")
        except Exception as e:
            logger.warning(f"⚠️ 动态提示词性能监控初始化失败: {e}")

        logger.info(f"📝 {self.name} ({self.version}) 初始化完成")

    # ========== P0: 动态上下文构建方法 ==========

    def _build_dynamic_context(
        self,
        office_action: dict[str, Any],        patent_info: dict[str, Any] | None = None,
        knowledge_graph: dict[str, Any] | None = None,
    ) -> str:
        """
        构建动态提示词生成器的输入上下文

        Args:
            office_action: 审查意见
            patent_info: 专利信息
            knowledge_graph: 知识图谱数据

        Returns:
            构建的上下文字符串
        """
        context_parts = []

        # 1. 业务类型（固定为专利审查）
        context_parts.append("专利审查")

        # 2. 驳回类型和理由
        rejection_type = office_action.get("rejection_type", "")
        if rejection_type:
            rejection_mapping = {
                "novelty": "新颖性",
                "inventiveness": "创造性",
                "utility": "实用性",
                "clarity": "清晰度",
                "support": "说明书支持",
                "unity": "单一性",
            }
            cn_rejection = rejection_mapping.get(rejection_type, rejection_type)
            context_parts.append(f"驳回类型：{cn_rejection}")

        # 3. 技术领域（从专利信息中提取）
        if patent_info:
            title = patent_info.get("title", "")
            if title:
                context_parts.append(f"技术领域：{title}")

            abstract = patent_info.get("abstract", "")
            if abstract and len(abstract) > 50:
                # 添加技术摘要的前100个字符
                context_parts.append(f"技术方案：{abstract[:100]}...")

        # 4. 核心技术特征（从知识图谱中提取）
        if knowledge_graph:
            core_features = knowledge_graph.get("core_innovation_features", [])
            if core_features:
                top_features = core_features[:5]  # 取前5个核心特征
                context_parts.append(f"核心特征：{', '.join(top_features)}")

            # 技术术语（从三元关系中提取）
            triples = knowledge_graph.get("problem_effect_triples", [])
            if triples:
                # 提取技术特征
                features = []
                for triple in triples[:3]:
                    if isinstance(triple, dict):
                        feature = triple.get("technical_feature", "")
                        if feature:
                            features.append(feature)
                if features:
                    context_parts.append(f"技术特征：{', '.join(features)}")

        # 5. 对比文件信息
        prior_art_refs = office_action.get("prior_art_references", [])
        if prior_art_refs:
            refs_str = "、".join(prior_art_refs[:3])  # 最多显示3个
            context_parts.append(f"对比文件：{refs_str}")

        # 6. 审查员论点
        examiner_args = office_action.get("examiner_arguments", [])
        if examiner_args:
            args_str = "；".join(examiner_args[:2])  # 最多显示2个论点
            context_parts.append(f"审查员观点：{args_str}")

        return "，".join(context_parts)

    async def _generate_dynamic_prompt(
        self,
        office_action: dict[str, Any],        patent_info: dict[str, Any] | None = None,
        knowledge_graph: dict[str, Any] | None = None,
    ) -> dict[str, Any] | None:
        """
        生成动态提示词

        Returns:
            动态提示词数据，如果生成失败则返回None
        """
        if not self.prompt_generator:
            return None

        # 开始计时（如果启用了监控）
        timer = None
        if self.prompt_metrics:
            from core.patents.dynamic_prompt_metrics import PromptGenerationTimer

            timer = PromptGenerationTimer(self.prompt_metrics)
            timer.__enter__()

        try:
            # 构建上下文
            context_input = self._build_dynamic_context(
                office_action, patent_info, knowledge_graph
            )

            # 生成动态提示词
            dynamic_prompt = await self.prompt_generator.generate_enhanced_dynamic_prompt(
                context_input
            )

            result = {
                "system_prompt": dynamic_prompt.system_prompt,
                "context_prompt": dynamic_prompt.context_prompt,
                "patent_rules_prompt": dynamic_prompt.patent_rules_prompt,
                "technical_terms_prompt": dynamic_prompt.technical_terms_prompt,
                "knowledge_prompt": dynamic_prompt.knowledge_prompt,
                "sqlite_knowledge_prompt": dynamic_prompt.sqlite_knowledge_prompt,
                "action_prompt": dynamic_prompt.action_prompt,
                "search_strategy_prompt": dynamic_prompt.search_strategy_prompt,
                "confidence_score": dynamic_prompt.confidence_score,
                "sources": dynamic_prompt.sources,
            }

            # 记录监控指标
            if self.prompt_metrics and timer:
                timer.__exit__(None, None, None)

                # 提取参数
                oa_id = office_action.get("oa_id", "unknown")
                rejection_type = office_action.get("rejection_type", "unknown")
                tech_field = patent_info.get("technical_field", "unknown") if patent_info else "unknown"

                # 记录生成指标
                self.prompt_metrics.record_generation(
                    success=True,
                    duration=timer.duration if timer else 0.0,
                    oa_id=oa_id,
                    rejection_type=rejection_type,
                    tech_field=tech_field,
                    confidence=dynamic_prompt.confidence_score,
                    sources=dynamic_prompt.sources,
                )

                # 记录各维度生成情况
                self.prompt_metrics.record_prompt_dimensions(result)

            return result

        except Exception as e:
            # 记录失败的监控指标
            if self.prompt_metrics and timer:
                timer.__exit__(None, None, None)

                oa_id = office_action.get("oa_id", "unknown")
                rejection_type = office_action.get("rejection_type", "unknown")

                self.prompt_metrics.prompt_generation_total.labels(success="false").inc()
                self.prompt_metrics.prompt_generation_by_rejection.labels(
                    rejection_type=rejection_type
                ).inc()

            logger.warning(f"⚠️ 动态提示词生成失败: {e}")
            return None

    async def create_response_plan(
        self,
        office_action: dict[str, Any],  # 改为接收字典
        patent_info: dict[str, Any] | None = None,
        knowledge_graph: dict[str, Any] | None = None,  # 新增：知识图谱数据
    ) -> ResponsePlan:
        """
        创建答复方案

        Args:
            office_action: 审查意见(字典)
            patent_info: 专利信息
            knowledge_graph: 技术知识图谱数据（包含问题-特征-效果三元关系、特征关联等）

        Returns:
            答复方案
        """
        # ========== P0: 生成动态提示词 ==========
        dynamic_prompt_data = None
        if self.prompt_generator:
            dynamic_prompt_data = await self._generate_dynamic_prompt(
                office_action, patent_info, knowledge_graph
            )
            if dynamic_prompt_data:
                logger.info(
                    f"✅ 动态提示词生成成功 (置信度: {dynamic_prompt_data['confidence_score']:.2f})"
                )
                logger.info(f"   数据来源: {dynamic_prompt_data['sources']}")

                # 缓存动态提示词，供后续步骤使用
                self.dynamic_prompt_cache[office_action.get("oa_id", "")] = dynamic_prompt_data

        # 首先构造OfficeAction对象
        oa = OfficeAction(
            oa_id=office_action.get("oa_id", f"OA_{datetime.now().timestamp()}"),
            rejection_type=RejectionType(office_action.get("rejection_type", "novelty")),
            rejection_reason=office_action.get("rejection_reason", ""),
            prior_art_references=office_action.get("prior_art_references", []),
            cited_claims=office_action.get("cited_claims", []),
            examiner_arguments=office_action.get("examiner_arguments", []),
            missing_features=office_action.get("missing_features", []),
            received_date=office_action.get("received_date", datetime.now().isoformat()),
            response_deadline=office_action.get("response_deadline", ""),
        )

        # 1. 检索相似案例
        similar_cases = await self._find_similar_cases(oa)

        # 2. 分析最佳策略（增强：使用知识图谱）
        strategy = await self._analyze_best_strategy_with_graph(
            oa, similar_cases, knowledge_graph, dynamic_prompt_data
        )

        # 3. 生成具体论点（P1增强：使用技术术语提示词）
        arguments = await self._generate_arguments_with_dynamic_terms(
            oa, strategy, patent_info, knowledge_graph, dynamic_prompt_data
        )

        # 4. 生成修改建议（P1增强：使用知识图谱）
        modifications = await self._generate_modifications_with_kg(
            oa, strategy, patent_info, knowledge_graph, dynamic_prompt_data
        )

        # 5. 预测成功概率（P1增强：使用专利规则）
        success_prob, confidence = await self._predict_success_with_rules(
            oa, strategy, similar_cases, knowledge_graph, dynamic_prompt_data
        )

        # 6. 策略理由（增强：包含图谱分析和动态提示词）
        rationale = self._generate_strategy_rationale_with_dynamic_prompt(
            strategy, similar_cases, oa, knowledge_graph, dynamic_prompt_data
        )

        plan = ResponsePlan(
            plan_id=f"plan_{datetime.now().timestamp()}",
            oa_id=oa.oa_id,
            recommended_strategy=strategy,
            strategy_rationale=rationale,
            arguments=arguments,
            claim_modifications=modifications,
            additional_evidence=[],
            success_probability=success_prob,
            confidence=confidence,
            reference_cases=[c.case_id for c in similar_cases[:3],
        )

        # 记录赫布学习:策略与审查类型的协同激活
        self.hebbian_optimizer.record_activation(
            nodes=["意见答复", oa.rejection_type.value, strategy.value], context={"oa_id": oa.oa_id}
        )

        logger.info(
            f"📝 生成答复方案: {strategy.value} "
            f"(成功概率: {success_prob:.1%}, 置信度: {confidence:.1%})"
        )

        return plan

    async def _find_similar_cases(self, office_action: OfficeAction) -> list[PatentCase]:
        """查找相似案例"""
        # 构造查询案例
        query_case = PatentCase(
            case_id="",
            case_type=CaseType.OFFICE_ACTION,
            status=CaseStatus.SUCCESS,  # 只看成功案例
            technical_field=TechnicalField.SOFTWARE,
            title=f"{office_action.rejection_type.value}答复",
            description=office_action.rejection_reason,
            input_data={"rejection_type": office_action.rejection_type.value},
            output_result={},
            solution="",
            tags=[office_action.rejection_type.value],
        )

        # 检索相似案例
        result = self.case_db.retrieve_similar_cases(
            query_case, top_n=10, case_type=CaseType.OFFICE_ACTION, status=CaseStatus.SUCCESS
        )

        return result.cases

    async def _analyze_best_strategy(
        self, office_action: OfficeAction, similar_cases: list[PatentCase]
    ) -> ResponseStrategy:
        """分析最佳策略"""
        # 基于驳回类型的默认策略
        default_strategies = {
            RejectionType.NOVELTY: ResponseStrategy.ARGUE_DIFFERENCES,
            RejectionType.INVENTIVENESS: ResponseStrategy.COMBINE,
            RejectionType.UTILITY: ResponseStrategy.AMEND_DESCRIPTION,
            RejectionType.CLARITY: ResponseStrategy.MODIFY_CLAIMS,
            RejectionType.SUPPORT: ResponseStrategy.AMEND_DESCRIPTION,
            RejectionType.UNITY: ResponseStrategy.MODIFY_CLAIMS,
        }

        # 统计相似案例中的成功策略
        if similar_cases:
            strategy_counter = Counter()
            for case in similar_cases:
                # 从案例解决方案中提取策略
                solution = case.solution.lower()

                if "区别" in solution or "差异" in solution:
                    strategy_counter[ResponseStrategy.ARGUE_DIFFERENCES] += case.fitness
                elif "修改" in solution and "权利要求" in solution:
                    strategy_counter[ResponseStrategy.MODIFY_CLAIMS] += case.fitness
                elif "说明书" in solution:
                    strategy_counter[ResponseStrategy.AMEND_DESCRIPTION] += case.fitness
                elif "组合" in solution:
                    strategy_counter[ResponseStrategy.COMBINE] += case.fitness

            # 选择最常用的策略
            if strategy_counter:
                return strategy_counter.most_common(1)[0][0]

        # 返回默认策略
        return default_strategies.get(
            office_action.rejection_type, ResponseStrategy.ARGUE_DIFFERENCES
        )

    async def _generate_arguments(
        self,
        office_action: OfficeAction,
        strategy: ResponseStrategy,
        patent_info: dict[str, Any] | None = None,
    ) -> list[str]:
        """生成争辩论点"""
        arguments = []

        if strategy == ResponseStrategy.ARGUE_DIFFERENCES:
            arguments.append("本申请与对比文件存在以下区别技术特征:")
            if office_action.missing_features:
                for feature in office_action.missing_features:
                    arguments.append(f"  • 对比文件未公开:{feature}")

            arguments.append("上述区别技术特征带来了以下技术效果:")
            arguments.append("  • 提高了[具体效果]")
            arguments.append("  • 解决了[具体问题]")

        elif strategy == ResponseStrategy.COMBINE:
            arguments.append("本申请具备创造性,理由如下:")
            arguments.append("1. 区别技术特征非本领域技术人员的常规选择")
            arguments.append("2. 特征组合产生了预料不到的技术效果")

        return arguments

    async def _generate_modifications(
        self,
        office_action: OfficeAction,
        strategy: ResponseStrategy,
        patent_info: dict[str, Any] | None = None,
    ) -> list[str]:
        """生成修改建议"""
        modifications = []

        if strategy in [ResponseStrategy.MODIFY_CLAIMS, ResponseStrategy.COMBINE]:
            if office_action.cited_claims:
                for claim_num in office_action.cited_claims:
                    modifications.append(
                        f"权利要求{claim_num}:建议增加[具体技术特征]进行进一步限定"
                    )

            modifications.append("建议将从属权利要求中的特征并入独立权利要求")

        elif strategy == ResponseStrategy.AMEND_DESCRIPTION:
            modifications.append("建议在说明书中补充[具体技术特征]的详细描述")
            modifications.append("建议增加实施例以支持权利要求的保护范围")

        return modifications

    async def _predict_success(
        self,
        office_action: OfficeAction,
        strategy: ResponseStrategy,
        similar_cases: list[PatentCase],
    ) -> tuple[float, float]:
        """预测成功概率"""
        if not similar_cases:
            # 无相似案例,基于驳回类型给默认概率
            default_probs = {
                RejectionType.NOVELTY: 0.6,
                RejectionType.INVENTIVENESS: 0.5,
                RejectionType.UTILITY: 0.7,
                RejectionType.CLARITY: 0.8,
                RejectionType.SUPPORT: 0.7,
                RejectionType.UNITY: 0.6,
            }
            prob = default_probs.get(office_action.rejection_type, 0.5)
            return prob, 0.5

        # 基于相似案例的成功率
        success_cases = [c for c in similar_cases if c.status == CaseStatus.SUCCESS]
        success_rate = len(success_cases) / len(similar_cases)

        # 计算平均适应度
        avg_fitness = sum(c.fitness for c in similar_cases) / len(similar_cases)

        # 综合计算
        success_probability = success_rate * 0.6 + avg_fitness * 0.4

        # 置信度基于案例数量
        confidence = min(1.0, len(similar_cases) / 10)

        return success_probability, confidence

    def _generate_strategy_rationale(
        self,
        strategy: ResponseStrategy,
        similar_cases: list[PatentCase],
        office_action: OfficeAction,
    ) -> str:
        """生成策略理由"""
        rationale = f"针对{office_action.rejection_type.value}驳回,建议采用{strategy.value}策略。"

        if similar_cases:
            success_count = sum(1 for c in similar_cases if c.status == CaseStatus.SUCCESS)
            rationale += f" 基于历史案例,该策略在类似情况下的成功率为{success_count/len(similar_cases):.1%}。"

        return rationale

    # ========== 新增：基于知识图谱的增强方法 ==========

    async def _analyze_best_strategy_with_graph(
        self,
        office_action: OfficeAction,
        similar_cases: list[PatentCase],
        knowledge_graph: dict[str, Any],    ) -> ResponseStrategy:
        """
        使用知识图谱分析最佳策略

        知识图谱增强：
        - 分析核心创新特征的差异
        - 评估问题-特征-效果三元关系
        - 识别关键区别技术特征
        """
        # 先调用原有策略分析
        strategy = await self._analyze_best_strategy(office_action, similar_cases)

        # 如果有知识图谱，进行增强分析
        if knowledge_graph:
            core_features = knowledge_graph.get("core_innovation_features", [])
            centrality_ranking = knowledge_graph.get("graph_centrality_ranking", [])

            # 如果有核心创新特征且有高中心性特征，倾向于争辩策略
            if core_features and centrality_ranking:
                top_centrality = centrality_ranking[0][1] if centrality_ranking else 0
                if top_centrality > 0.7:  # 高中心性
                    logger.info(f"   📊 基于图谱分析: 检测到高中心性特征 (中心性={top_centrality:.3f})，建议争辩策略")
                    # 对于高中心性特征，更倾向于争辩而非修改
                    if strategy == ResponseStrategy.MODIFY_CLAIMS:
                        strategy = ResponseStrategy.ARGUE_DIFFERENCES

        return strategy

    async def _generate_arguments_with_graph(
        self,
        office_action: OfficeAction,
        strategy: ResponseStrategy,
        patent_info: dict[str, Any],        knowledge_graph: dict[str, Any],    ) -> list[str]:
        """
        使用知识图谱生成增强论点

        知识图谱增强：
        - 利用问题-特征-效果三元关系构建论证链
        - 使用特征关联关系说明区别技术特征
        - 基于图谱中心性强调核心创新点
        """
        # 先调用原有论点生成
        arguments = await self._generate_arguments(office_action, strategy, patent_info)

        # 如果有知识图谱，添加增强论点
        if knowledge_graph:
            # 问题-特征-效果三元关系
            triples = knowledge_graph.get("problem_effect_triples", [])
            if triples:
                arguments.append(
                    "### 基于技术知识图谱的深度分析:\n"
                    "根据问题-特征-效果三元关系分析，本发明的技术特征形成完整的技术解决方案链条："
                )
                for triple in triples[:3]:  # 最多3个三元关系
                    arguments.append(
                        f"- 技术问题: {triple.get('technical_problem', 'N/A')}\n"
                        f"  → 技术特征: {triple.get('technical_feature', 'N/A')}\n"
                        f"  → 技术效果: {triple.get('technical_effect', 'N/A')}\n"
                        f"  (置信度: {triple.get('confidence', 0):.1%})"
                    )

            # 核心创新特征
            core_features = knowledge_graph.get("core_innovation_features", [])
            if core_features:
                arguments.append(
                    "\n### 核心创新特征识别:\n"
                    "基于图谱中心性和创新性分析，以下特征为核心创新点："
                )
                for feature_id in core_features:
                    arguments.append(f"- 特征 {feature_id} (图谱中心性排名Top)")

        return arguments

    async def _generate_modifications_with_graph(
        self,
        office_action: OfficeAction,
        strategy: ResponseStrategy,
        patent_info: dict[str, Any],        knowledge_graph: dict[str, Any],    ) -> list[str]:
        """
        使用知识图谱生成增强的修改建议

        知识图谱增强：
        - 基于特征关联关系建议保护范围
        - 利用核心创新特征优化权利要求
        """
        # 先调用原有修改建议
        modifications = await self._generate_modifications(office_action, strategy, patent_info)

        # 如果有知识图谱且需要修改，添加增强建议
        if knowledge_graph and strategy == ResponseStrategy.MODIFY_CLAIMS:
            core_features = knowledge_graph.get("core_innovation_features", [])
            if core_features:
                modifications.append(
                    "\n### 基于知识图谱的修改建议:\n"
                    "建议将核心创新特征纳入独立权利要求，以获得更好的保护："
                )
                for feature_id in core_features[:3]:
                    modifications.append(f"- 考虑增加对特征 {feature_id} 的保护")

        return modifications

    async def _predict_success_with_graph(
        self,
        office_action: OfficeAction,
        strategy: ResponseStrategy,
        similar_cases: list[PatentCase],
        knowledge_graph: dict[str, Any],    ) -> tuple[float, float]:
        """
        使用知识图谱增强成功概率预测

        知识图谱增强：
        - 考虑图谱密度（技术复杂度）
        - 分析核心创新特征（创新强度）
        """
        # 先调用原有预测
        success_prob, confidence = await self._predict_success(
            office_action, strategy, similar_cases
        )

        # 如果有知识图谱，调整预测
        if knowledge_graph:
            graph_density = knowledge_graph.get("graph_density", 0)
            core_features_count = len(knowledge_graph.get("core_innovation_features", []))

            # 图谱密度越高，技术方案越复杂，可能更难争辩
            if graph_density > 0.3:
                success_prob *= 0.95  # 略微降低成功率
                confidence *= 0.95

            # 核心创新特征越多，创新性越强，争辩成功率越高
            if core_features_count > 2:
                success_prob *= 1.1  # 提高成功率
                success_prob = min(success_prob, 0.95)  # 最多95%

        return success_prob, confidence

    def _generate_strategy_rationale_with_graph(
        self,
        strategy: ResponseStrategy,
        similar_cases: list[PatentCase],
        office_action: OfficeAction,
        knowledge_graph: dict[str, Any],    ) -> str:
        """
        使用知识图谱生成增强的策略理由

        知识图谱增强：
        - 基于图谱分析说明策略选择理由
        - 利用问题-特征-效果三元关系解释技术差异
        """
        # 先调用原有理由生成
        rationale = self._generate_strategy_rationale(strategy, similar_cases, office_action)

        # 如果有知识图谱，添加图谱分析说明
        if knowledge_graph:
            graph_density = knowledge_graph.get("graph_density", 0)
            core_features_count = len(knowledge_graph.get("core_innovation_features", []))

            rationale += "\n\n### 技术知识图谱分析:\n"
            rationale += f"- 图谱密度: {graph_density:.3f} (反映技术复杂度)\n"
            rationale += f"- 核心创新特征: {core_features_count}个 (反映创新强度)\n"

            if core_features_count > 0:
                rationale += "- 基于图谱分析，目标专利具有明确的创新技术特征，"
                rationale += "建议通过争辩这些核心特征与对比文件的技术差异来答复。\n"

        return rationale

    # ========== P1: 增强方法（使用动态提示词） ==========

    async def _generate_arguments_with_dynamic_terms(
        self,
        office_action: OfficeAction,
        strategy: ResponseStrategy,
        patent_info: dict[str, Any],        knowledge_graph: dict[str, Any],        dynamic_prompt_data: dict[str, Any],    ) -> list[str]:
        """
        P1增强: 使用技术术语提示词生成答复论点

        增强内容：
        - 利用2442个AI术语知识图谱
        - 精确识别和解释技术特征
        - 基于术语复杂度调整论点深度
        """
        # 先调用原有论点生成
        arguments = await self._generate_arguments_with_graph(
            office_action, strategy, patent_info, knowledge_graph
        )

        # 如果有动态提示词，添加技术术语增强论点
        if dynamic_prompt_data and dynamic_prompt_data.get("technical_terms_prompt"):
            arguments.append("\n### 🔬 技术术语深度分析:\n")
            arguments.append(dynamic_prompt_data["technical_terms_prompt"])

            # 使用知识图谱洞察
            if dynamic_prompt_data.get("knowledge_prompt"):
                arguments.append("\n### 📊 技术复杂度分析:\n")
                arguments.append(dynamic_prompt_data["knowledge_prompt"])

            # 使用SQLite知识图谱
            if dynamic_prompt_data.get("sqlite_knowledge_prompt"):
                arguments.append("\n### 🕸️ 专利知识图谱关联:\n")
                arguments.append(dynamic_prompt_data["sqlite_knowledge_prompt"])

        return arguments

    async def _generate_modifications_with_kg(
        self,
        office_action: OfficeAction,
        strategy: ResponseStrategy,
        patent_info: dict[str, Any],        knowledge_graph: dict[str, Any],        dynamic_prompt_data: dict[str, Any],    ) -> list[str]:
        """
        P1增强: 使用知识图谱生成权利要求修改建议

        增强内容：
        - 基于特征关联图谱建议修改方向
        - 利用核心特征保护范围
        - 参考技术演化趋势
        """
        # 先调用原有修改建议生成
        modifications = await self._generate_modifications_with_graph(
            office_action, strategy, patent_info, knowledge_graph
        )

        # 如果有动态提示词和知识图谱，添加增强建议
        if dynamic_prompt_data and knowledge_graph:
            # 基于中心性排序建议保护核心特征
            centrality_ranking = knowledge_graph.get("graph_centrality_ranking", [])
            if centrality_ranking:
                modifications.append(
                    "\n### ⭐ 基于图谱中心性的修改建议:\n"
                    "根据技术特征的中心性分析，建议重点保护以下高中心性特征："
                )
                for feature, score in centrality_ranking[:3]:
                    modifications.append(f"- {feature} (中心性: {score:.4f})")

            # 基于检索策略优化
            if dynamic_prompt_data.get("search_strategy_prompt"):
                modifications.append("\n### 🔍 技术检索建议:\n")
                modifications.append(dynamic_prompt_data["search_strategy_prompt"])

        return modifications

    async def _predict_success_with_rules(
        self,
        office_action: OfficeAction,
        strategy: ResponseStrategy,
        similar_cases: list[PatentCase],
        knowledge_graph: dict[str, Any],        dynamic_prompt_data: dict[str, Any],    ) -> tuple[float, float]:
        """
        P1增强: 使用专利规则提升成功概率预测

        增强内容：
        - 基于相关专利规则评估
        - 利用125万+实体知识图谱
        - 综合动态提示词置信度
        """
        # 先调用原有预测方法
        base_prob, base_confidence = await self._predict_success_with_graph(
            office_action, strategy, similar_cases, knowledge_graph
        )

        # 如果有动态提示词，调整预测
        if dynamic_prompt_data:
            # 使用动态提示词的置信度调整
            dynamic_confidence = dynamic_prompt_data.get("confidence_score", 0.5)

            # 综合置信度（原有置信度和动态置信度加权平均）
            enhanced_confidence = (base_confidence * 0.6) + (dynamic_confidence * 0.4)

            # 使用专利规则调整成功概率
            patent_rules_prompt = dynamic_prompt_data.get("patent_rules_prompt", "")
            if patent_rules_prompt:
                # 如果有相关专利规则支持，提高成功概率
                enhanced_prob = base_prob * 1.05  # 5%的提升
                enhanced_prob = min(enhanced_prob, 0.95)  # 上限95%
            else:
                enhanced_prob = base_prob

            logger.info(
                f"   📊 预测增强: 基础{base_prob:.1%} -> "
                f"增强{enhanced_prob:.1%} (动态置信度: {dynamic_confidence:.2f})"
            )

            return enhanced_prob, enhanced_confidence

        return base_prob, base_confidence

    def _generate_strategy_rationale_with_dynamic_prompt(
        self,
        strategy: ResponseStrategy,
        similar_cases: list[PatentCase],
        office_action: OfficeAction,
        knowledge_graph: dict[str, Any],        dynamic_prompt_data: dict[str, Any],    ) -> str:
        """
        P1增强: 生成包含动态提示词的策略理由

        增强内容：
        - 整合专利规则参考
        - 说明技术术语分析结果
        - 展示知识图谱洞察
        """
        # 先调用原有策略理由生成
        rationale = self._generate_strategy_rationale_with_graph(
            strategy, similar_cases, office_action, knowledge_graph
        )

        # 如果有动态提示词，添加增强说明
        if dynamic_prompt_data:
            # 添加数据来源说明
            sources = dynamic_prompt_data.get("sources", [])
            if sources:
                rationale += "\n\n### 📚 分析数据来源:\n"
                for source in sources:
                    source_type = source.get("type", "unknown")
                    count = source.get("count", 0)
                    if source_type == "patent_rules":
                        rationale += f"- 专利规则向量库: {count}条相关规则\n"
                    elif source_type == "ai_terminology":
                        rationale += f"- AI术语知识图谱: {count}个相关术语\n"
                    elif source_type == "sqlite_knowledge_graph":
                        rationale += f"- 专利知识图谱: {count}个相关实体\n"
                    elif source_type == "ai_vectors":
                        rationale += f"- 向量相似度匹配: {count}个相关项\n"

            # 添加行动建议
            action_prompt = dynamic_prompt_data.get("action_prompt", "")
            if action_prompt:
                rationale += f"\n### 💡 行动建议:\n{action_prompt}"

        return rationale

    # ========== P2: 高级功能 ==========

    def build_prompt_template_for_rejection_type(
        self, rejection_type: str, technology_field: str = "通用"
    ) -> dict[str, str]:
        """
        P2: 为不同驳回类型构建动态提示词模板

        支持10种驳回类型（v0.2.0扩展版）:
        1. novelty - 新颖性
        2. inventiveness - 创造性
        3. utility - 实用性
        4. clarity - 清晰度
        5. sufficiency - 充分性
        6. support - 支持关系
        7. unity - 单一性
        8. clarity-2 - 清楚性
        9. amended-matter - 修改超范围
        10. form - 形式问题

        Args:
            rejection_type: 驳回类型
            technology_field: 技术领域

        Returns:
            提示词模板字典
        """
        templates = {
            # 1. 新颖性驳回
            "novelty": {
                "system": "你是专利新颖性审查答复专家，擅长识别区别技术特征。",
                "context": f"针对{technology_field}领域的新颖性驳回，重点分析:",
                "key_points": [
                    "识别目标专利与对比文件的实质性区别",
                    "分析技术特征的具体实现方式差异",
                    "强调技术效果的显著不同",
                ],
            },
            # 2. 创造性驳回
            "inventiveness": {
                "system": "你是专利创造性审查答复专家，擅长论证突出的实质性特点和显著进步。",
                "context": f"针对{technology_field}领域的创造性驳回，重点分析:",
                "key_points": [
                    "论证技术特征对本领域技术人员来说是非显而易见的",
                    "说明技术方案产生了预料不到的技术效果",
                    "强调发明在技术上的显著进步",
                ],
            },
            # 3. 实用性驳回
            "utility": {
                "system": "你是专利实用性审查答复专家，擅长论证技术方案的可用性。",
                "context": f"针对{technology_field}领域的实用性驳回，重点分析:",
                "key_points": [
                    "说明技术方案能够在产业上制造或使用",
                    "证明技术方案产生了积极效果",
                    "强调实际应用的可行性",
                ],
            },
            # 4. 清晰度驳回
            "clarity": {
                "system": "你是专利清晰度审查答复专家，擅长澄清技术方案。",
                "context": f"针对{technology_field}领域的清晰度驳回，重点分析:",
                "key_points": [
                    "澄清技术术语的准确含义",
                    "补充技术特征的具体描述",
                    "明确技术方案的保护范围",
                ],
            },
            # 5. 充分性驳回（新增）
            "sufficiency": {
                "system": "你是专利充分性审查答复专家，擅长论证技术方案的完整公开。",
                "context": f"针对{technology_field}领域的充分性驳回，重点分析:",
                "key_points": [
                    "说明说明书已充分公开技术方案",
                    "论证本领域技术人员能够实现该技术方案",
                    "强调技术方案的完整性和可实施性",
                ],
            },
            # 6. 支持关系驳回（新增）
            "support": {
                "system": "你是专利支持关系审查答复专家，擅长论证权利要求与说明书的一致性。",
                "context": f"针对{technology_field}领域的支持关系驳回，重点分析:",
                "key_points": [
                    "论证权利要求得到说明书的支持",
                    "说明权利要求的保护范围适当",
                    "强调技术特征在说明书中有明确依据",
                ],
            },
            # 7. 单一性驳回（新增）
            "unity": {
                "system": "你是专利单一性审查答复专家，擅长处理多项发明的单一性问题。",
                "context": f"针对{technology_field}领域的单一性驳回，重点分析:",
                "key_points": [
                    "论证各项权利要求属于一个总的发明构思",
                    "说明技术特征之间存在关联性",
                    "强调技术方案的协同作用",
                ],
            },
            # 8. 清楚性驳回（新增）
            "clarity-2": {
                "system": "你是专利清楚性审查答复专家，擅长澄清技术方案的表述。",
                "context": f"针对{technology_field}领域的清楚性驳回，重点分析:",
                "key_points": [
                    "澄清技术术语的歧义",
                    "消除技术方案的不确定性",
                    "明确技术特征的含义和范围",
                ],
            },
            # 9. 修改超范围驳回（新增）
            "amended-matter": {
                "system": "你是专利修改超范围审查答复专家，擅长论证修改的合法性。",
                "context": f"针对{technology_field}领域的修改超范围驳回，重点分析:",
                "key_points": [
                    "论证修改未超出原说明书和权利要求书记载的范围",
                    "说明修改内容的依据",
                    "强调修改符合专利法规定",
                ],
            },
            # 10. 形式问题驳回（新增）
            "form": {
                "system": "你是专利形式问题审查答复专家，擅长处理各类形式缺陷。",
                "context": f"针对{technology_field}领域的形式问题驳回，重点分析:",
                "key_points": [
                    "识别并修正形式缺陷",
                    "确保申请文件符合规范要求",
                    "完善申请文件的结构和格式",
                ],
            },
        }

        return templates.get(
            rejection_type,
            {
                "system": "你是专利审查答复专家，擅长处理各种类型的驳回。",
                "context": f"针对{technology_field}领域的专利审查，需要专业分析。",
                "key_points": ["全面分析审查意见", "制定针对性的答复策略"],
            },
        )

    def evaluate_prompt_effectiveness(
        self,
        plan_id: str,
        actual_outcome: str,
        predicted_success_prob: float,
        dynamic_prompt_confidence: float,
    ) -> dict[str, Any]:
        """
        P2: 评估提示词效果

        Args:
            plan_id: 方案ID
            actual_outcome: 实际结果
            predicted_success_prob: 预测成功概率
            dynamic_prompt_confidence: 动态提示词置信度

        Returns:
            效果评估结果
        """
        # 计算预测准确性
        success = actual_outcome.lower() in ["授权", "成功", "通过"]
        prediction_accuracy = 1.0 if (success and predicted_success_prob > 0.5) else 0.0

        # 计算置信度校准
        confidence_calibration = abs(dynamic_prompt_confidence - prediction_accuracy)

        # 计算综合效果分数
        effectiveness_score = (prediction_accuracy * 0.7) + (
            (1 - confidence_calibration) * 0.3
        )

        return {
            "plan_id": plan_id,
            "prediction_accuracy": prediction_accuracy,
            "confidence_calibration": confidence_calibration,
            "effectiveness_score": effectiveness_score,
            "evaluation": "优秀" if effectiveness_score > 0.8 else "良好" if effectiveness_score > 0.6 else "需改进",
            "recommendations": self._generate_optimization_recommendations(
                effectiveness_score, prediction_accuracy, confidence_calibration
            ),
        }

    def _generate_optimization_recommendations(
        self, effectiveness_score: float, prediction_accuracy: float, confidence_calibration: float
    ) -> list[str]:
        """生成优化建议"""
        recommendations = []

        if effectiveness_score < 0.6:
            recommendations.append("提示词效果需要显著改进")
            if prediction_accuracy < 0.5:
                recommendations.append("预测准确性较低，建议调整提示词特征权重")
            if confidence_calibration > 0.3:
                recommendations.append("置信度校准偏差较大，建议调整置信度计算方法")
        elif effectiveness_score < 0.8:
            recommendations.append("提示词效果良好，仍有优化空间")
            if prediction_accuracy < 0.8:
                recommendations.append("建议增加更多领域特定的提示词特征")
        else:
            recommendations.append("提示词效果优秀，可以作为最佳实践")

        return recommendations

    def record_feedback_for_learning(
        self,
        plan_id: str,
        dynamic_prompt_data: dict[str, Any],        actual_outcome: str,
        user_feedback: str | None = None,
    ) -> None:
        """
        P2: 记录反馈用于学习优化

        Args:
            plan_id: 方案ID
            dynamic_prompt_data: 动态提示词数据
            actual_outcome: 实际结果
            user_feedback: 用户反馈
        """
        # 构建反馈记录
        feedback_record = {
            "plan_id": plan_id,
            "timestamp": datetime.now().isoformat(),
            "dynamic_prompt_data": dynamic_prompt_data,
            "actual_outcome": actual_outcome,
            "user_feedback": user_feedback,
            "confidence_score": dynamic_prompt_data.get("confidence_score", 0.0)
            if dynamic_prompt_data
            else 0.0,
            "sources": dynamic_prompt_data.get("sources", []) if dynamic_prompt_data else [],
        }

        # 记录到历史（实际应该持久化到数据库）
        self.response_history.append(feedback_record)

        # 触发赫布学习优化
        if dynamic_prompt_data and dynamic_prompt_data.get("sources"):
            # 提取有效的数据源类型
            effective_sources = [
                s.get("type", "") for s in dynamic_prompt_data.get("sources", []) if s.get("count", 0) > 0
            ]

            if effective_sources:
                # 强化有效数据源的激活
                self.hebbian_optimizer.record_activation(
                    nodes=["动态提示词"] + effective_sources,
                    context={"plan_id": plan_id, "outcome": actual_outcome},
                )

        # 记录效果评估分数（如果有监控）
        if self.prompt_metrics:
            # 计算效果分数（简化版）
            success = actual_outcome.lower() in ["授权", "成功", "通过"]
            confidence = dynamic_prompt_data.get("confidence_score", 0.5) if dynamic_prompt_data else 0.5

            # 简单的效果分数计算
            prediction_accuracy = 1.0 if (success and confidence > 0.5) or (not success and confidence <= 0.5) else 0.0
            confidence_calibration = abs(confidence - prediction_accuracy)
            effectiveness_score = (prediction_accuracy * 0.7) + ((1 - confidence_calibration) * 0.3)

            self.prompt_metrics.record_effectiveness(plan_id, effectiveness_score)

        logger.info(f"📚 已记录反馈用于学习优化: {plan_id}")

    async def record_response_outcome(self, plan_id: str, outcome: str, success: bool) -> None:
        """
        记录答复结果

        Args:
            plan_id: 方案ID
            outcome: 最终结果
            success: 是否成功
        """
        result = ResponseResult(
            response_id=f"resp_{datetime.now().timestamp()}",
            plan_id=plan_id,
            final_response="",  # 实际答复文本
            submitted_date=datetime.now().isoformat(),
            final_outcome=outcome,
            success=success,
        )

        self.response_history.append(result)

        # 更新策略统计
        # 这里简化处理,实际应该从plan中获取策略信息

        logger.info(f"📝 记录答复结果: {'成功' if success else '失败'} - {outcome}")

    def get_strategy_statistics(self) -> dict[str, Any]:
        """获取策略统计"""
        if not self.response_history:
            return {"message": "暂无答复历史"}

        total = len(self.response_history)
        success_count = sum(1 for r in self.response_history if r.success)
        success_rate = success_count / total if total > 0 else 0

        return {
            "total_responses": total,
            "successful_responses": success_count,
            "success_rate": success_rate,
            "recent_responses": [
                {"response_id": r.response_id, "outcome": r.final_outcome, "success": r.success}
                for r in self.response_history[-10:]
            ],
        }


# 全局单例
_smart_oa_responder_instance = None


def get_smart_oa_responder() -> SmartOfficeActionResponder:
    """获取智能意见答复系统单例"""
    global _smart_oa_responder_instance
    if _smart_oa_responder_instance is None:
        _smart_oa_responder_instance = SmartOfficeActionResponder()
    return _smart_oa_responder_instance


# 测试代码
async def main():
    """测试智能意见答复系统"""

    print("\n" + "=" * 60)
    print("📝 智能意见答复系统测试")
    print("=" * 60 + "\n")

    responder = get_smart_oa_responder()

    # 测试审查意见
    oa = OfficeAction(
        oa_id="OA202312001",
        rejection_type=RejectionType.NOVELTY,
        rejection_reason="对比文件D1公开了权利要求1的全部技术特征,不具备新颖性",
        prior_art_references=["CN112345678A"],
        cited_claims=[1],
        examiner_arguments=["D1公开了基于深度学习的图像识别方法", "D1也使用了注意力机制"],
        missing_features=["特殊的损失函数", "特征金字塔的具体结构"],
        received_date="2023-12-01",
        response_deadline="2024-03-01",
    )

    print("📝 测试1: 创建答复方案")

    plan = await responder.create_response_plan(oa)

    print(f"方案ID: {plan.plan_id}")
    print(f"推荐策略: {plan.recommended_strategy.value}")
    print(f"策略理由: {plan.strategy_rationale}")
    print(f"成功概率: {plan.success_probability:.1%}")
    print(f"置信度: {plan.confidence:.1%}")
    print(f"参考案例: {len(plan.reference_cases)} 个\n")

    print("📝 争辩论点:")
    for arg in plan.arguments:
        print(f"  {arg}")
    print()

    print("📝 修改建议:")
    for mod in plan.claim_modifications:
        print(f"  • {mod}")
    print()

    # 测试2:记录结果
    print("📝 测试2: 记录答复结果")

    await responder.record_response_outcome(
        plan_id=plan.plan_id, outcome="审查员接受,专利授权", success=True
    )

    # 测试3:统计信息
    print("📝 测试3: 策略统计")

    stats = responder.get_strategy_statistics()
    print(json.dumps(stats, ensure_ascii=False, indent=2))

    print("\n✅ 测试完成!")


# 入口点: @async_main装饰器已添加到main函数
