#!/usr/bin/env python3
from __future__ import annotations
"""
统一推理引擎编排器
Unified Reasoning Orchestrator

作者: 小诺·双鱼公主 v4.0.0
版本: v1.0.0
创建时间: 2025-12-31

核心职责:
1. 根据任务类型自动选择最合适的推理引擎
2. 为专业任务直接路由到专业能力(绕过超级推理)
3. 为通用任务使用通用推理引擎
4. 提供统一的推理接口

路由原则:
- 专业法律任务 → 专业引擎(不使用7阶段超级推理)
- 通用推理任务 → 通用推理引擎
- 语义分析任务 → 语义推理引擎
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class TaskDomain(Enum):
    """任务领域"""

    PATENT_LAW = "patent_law"  # 专利法律
    IP_MANAGEMENT = "ip_management"  # IP管理
    GENERAL_ANALYSIS = "general_analysis"  # 通用分析
    SEMANTIC_SEARCH = "semantic_search"  # 语义搜索
    TECHNICAL_RESEARCH = "technical_research"  # 技术研究


class TaskComplexity(Enum):
    """任务复杂度"""

    LOW = "low"  # 简单任务
    MEDIUM = "medium"  # 中等任务
    HIGH = "high"  # 复杂任务
    EXPERT = "expert"  # 专家级任务


class TaskType(Enum):
    """任务类型(详细)"""

    # 专业法律任务(直接使用专业能力,不使用超级推理)
    OFFICE_ACTION_RESPONSE = "office_action_response"  # 意见答复 ⭐ 最高优先级
    INVALIDITY_REQUEST = "invalidity_request"  # 无效宣告
    PATENT_DRAFTING = "patent_drafting"  # 专利撰写
    PATENT_COMPLIANCE = "patent_compliance"  # 专利合规
    NOVELTY_ANALYSIS = "novelty_analysis"  # 新颖性分析
    INVENTIVENESS_ANALYSIS = "inventiveness_analysis"  # 创造性分析
    CLAIM_ANALYSIS = "claim_analysis"  # 权利要求分析

    # 通用分析任务(可以使用通用推理)
    GENERAL_REASONING = "general_reasoning"  # 通用推理
    COMPLEX_PROBLEM_SOLVING = "complex_problem_solving"  # 复杂问题解决
    DECISION_SUPPORT = "decision_support"  # 决策支持

    # 语义分析任务
    SEMANTIC_SEARCH = "semantic_search"  # 语义搜索
    KNOWLEDGE_GRAPH_QUERY = "knowledge_graph_query"  # 知识图谱查询

    # 技术研究任务
    TECHNOLOGY_LANDSCAPE = "technology_landscape"  # 技术态势分析
    ROADMAP_GENERATION = "roadmap_generation"  # 路线图生成


@dataclass
class TaskProfile:
    """任务画像"""

    task_type: TaskType
    domain: TaskDomain
    complexity: TaskComplexity
    requires_human_in_loop: bool = False
    is_legal_task: bool = False

    # 任务元数据
    metadata: dict[str, Any] = field(default_factory=dict)

    # 推理结果
    selected_engine: str | None = None
    confidence: float = 0.0
    reasoning_trace: list[dict] = field(default_factory=list)


@dataclass
class EngineRecommendation:
    """引擎推荐"""

    engine_name: str
    engine_type: str
    confidence: float
    reason: str
    bypass_super_reasoning: bool = False  # 是否绕过超级推理
    direct_capability: bool = False  # 是否直接调用专业能力


class UnifiedReasoningOrchestrator:
    """
    统一推理引擎编排器

    核心原则:
    1. 专业任务直接调用专业能力(不使用7阶段超级推理)
    2. 通用任务使用适当的推理引擎
    3. 提供统一的路由接口
    """

    def __init__(self):
        self.version = "1.0.0"
        self.created_at = datetime.now()

        # 路由规则
        self._build_routing_rules()

        # 引擎缓存
        self._engine_cache: dict[str, Any] = {}

        # 统计信息
        self._statistics = {
            "total_requests": 0,
            "professional_tasks": 0,
            "general_tasks": 0,
            "semantic_tasks": 0,
            "bypass_count": 0,
        }

    def _build_routing_rules(self) -> Any:
        """构建路由规则"""

        # 专业任务路由表(直接使用专业能力,不使用超级推理)
        self.professional_routes = {
            # 意见答复 → 专业意见答复服务(绕过超级推理)⭐
            TaskType.OFFICE_ACTION_RESPONSE: EngineRecommendation(
                engine_name="professional_oa_responder",
                engine_type="direct_capability",
                confidence=1.0,
                reason="意见答复是专业法律任务,使用专业意见答复服务",
                bypass_super_reasoning=True,
                direct_capability=True,
            ),
            # 无效宣告 → 小娜超级推理引擎(法律专业)
            TaskType.INVALIDITY_REQUEST: EngineRecommendation(
                engine_name="xiaona_super_reasoning_engine",
                engine_type="legal_reasoning",
                confidence=0.95,
                reason="无效宣告需要专业法律推理",
                bypass_super_reasoning=True,
                direct_capability=True,
            ),
            # 专利撰写 → 小娜超级推理引擎
            TaskType.PATENT_DRAFTING: EngineRecommendation(
                engine_name="xiaona_super_reasoning_engine",
                engine_type="legal_reasoning",
                confidence=0.95,
                reason="专利撰写需要专业法律推理",
                bypass_super_reasoning=True,
                direct_capability=True,
            ),
            # 专利合规 → 专家规则引擎
            TaskType.PATENT_COMPLIANCE: EngineRecommendation(
                engine_name="expert_rule_engine",
                engine_type="rule_based",
                confidence=0.98,
                reason="专利合规检查使用专家规则",
                bypass_super_reasoning=True,
                direct_capability=True,
            ),
            # 新颖性分析 → 增强法律推理引擎
            TaskType.NOVELTY_ANALYSIS: EngineRecommendation(
                engine_name="enhanced_legal_reasoning_engine",
                engine_type="legal_reasoning",
                confidence=0.92,
                reason="新颖性分析需要专业法律推理",
                bypass_super_reasoning=True,
                direct_capability=True,
            ),
            # 创造性分析 → 现有技术分析器 + LLM增强判断
            TaskType.INVENTIVENESS_ANALYSIS: EngineRecommendation(
                engine_name="prior_art_analyzer + llm_enhanced_judgment",
                engine_type="hybrid_legal",
                confidence=0.93,
                reason="创造性分析需要现有技术图谱+LLM判断",
                bypass_super_reasoning=True,
                direct_capability=True,
            ),
            # 权利要求分析 → 专利规则链
            TaskType.CLAIM_ANALYSIS: EngineRecommendation(
                engine_name="patent_rule_chain",
                engine_type="rule_chain",
                confidence=0.94,
                reason="权利要求分析使用规则链推理",
                bypass_super_reasoning=True,
                direct_capability=True,
            ),
        }

        # 通用任务路由表(可以使用通用推理)
        self.general_routes = {
            TaskType.GENERAL_REASONING: EngineRecommendation(
                engine_name="unified_reasoning_engine",
                engine_type="general_reasoning",
                confidence=0.85,
                reason="通用推理使用统一推理引擎",
                bypass_super_reasoning=False,
                direct_capability=False,
            ),
            TaskType.COMPLEX_PROBLEM_SOLVING: EngineRecommendation(
                engine_name="athena_super_reasoning",
                engine_type="super_reasoning",
                confidence=0.90,
                reason="复杂问题使用Athena超级推理(仅非法律任务)",
                bypass_super_reasoning=False,
                direct_capability=False,
            ),
            TaskType.DECISION_SUPPORT: EngineRecommendation(
                engine_name="dual_system_reasoning",
                engine_type="dual_system",
                confidence=0.88,
                reason="决策支持使用双系统推理",
                bypass_super_reasoning=False,
                direct_capability=False,
            ),
        }

        # 语义分析路由表
        self.semantic_routes = {
            TaskType.SEMANTIC_SEARCH: EngineRecommendation(
                engine_name="semantic_reasoning_engine_v4",
                engine_type="semantic",
                confidence=0.95,
                reason="语义搜索使用v4语义推理引擎",
                bypass_super_reasoning=True,
                direct_capability=True,
            ),
            TaskType.KNOWLEDGE_GRAPH_QUERY: EngineRecommendation(
                engine_name="semantic_reasoning_engine",
                engine_type="semantic",
                confidence=0.92,
                reason="知识图谱查询使用语义推理",
                bypass_super_reasoning=True,
                direct_capability=True,
            ),
        }

        # 技术研究路由表
        self.technical_routes = {
            TaskType.TECHNOLOGY_LANDSCAPE: EngineRecommendation(
                engine_name="prior_art_analyzer",
                engine_type="knowledge_graph",
                confidence=0.93,
                reason="技术态势分析使用现有技术分析器",
                bypass_super_reasoning=True,
                direct_capability=True,
            ),
            TaskType.ROADMAP_GENERATION: EngineRecommendation(
                engine_name="roadmap_generator",
                engine_type="roadmap",
                confidence=0.94,
                reason="路线图生成使用专用引擎",
                bypass_super_reasoning=True,
                direct_capability=True,
            ),
        }

    def analyze_task(
        self,
        task_description: str,
        task_type: TaskType | None = None,
        metadata: dict | None = None,
    ) -> TaskProfile:
        """
        分析任务特征

        Args:
            task_description: 任务描述
            task_type: 任务类型(可选,如果不提供则自动推断)
            metadata: 额外元数据

        Returns:
            TaskProfile: 任务画像
        """
        # 统计
        self._statistics["total_requests"] += 1

        # 如果未提供任务类型,则自动推断
        if task_type is None:
            task_type = self._infer_task_type(task_description, metadata or {})

        # 确定领域
        domain = self._infer_domain(task_type, metadata or {})

        # 确定复杂度
        complexity = self._infer_complexity(task_type, metadata or {})

        # 判断是否需要HITL
        requires_hitl = self._requires_human_in_loop(task_type)

        # 判断是否是法律任务
        is_legal = self._is_legal_task(task_type)

        profile = TaskProfile(
            task_type=task_type,
            domain=domain,
            complexity=complexity,
            requires_human_in_loop=requires_hitl,
            is_legal_task=is_legal,
            metadata=metadata or {},
        )

        logger.info(
            f"任务分析完成: {task_type.value} | 领域: {domain.value} | "
            f"复杂度: {complexity.value} | HITL: {requires_hitl}"
        )

        return profile

    def select_engine(self, profile: TaskProfile) -> EngineRecommendation:
        """
        选择最合适的推理引擎

        Args:
            profile: 任务画像

        Returns:
            EngineRecommendation: 引擎推荐
        """
        task_type = profile.task_type

        # 优先检查专业任务路由
        if task_type in self.professional_routes:
            recommendation = self.professional_routes[task_type]
            self._statistics["professional_tasks"] += 1
            if recommendation.bypass_super_reasoning:
                self._statistics["bypass_count"] += 1

        # 然后检查通用任务路由
        elif task_type in self.general_routes:
            recommendation = self.general_routes[task_type]
            self._statistics["general_tasks"] += 1

        # 然后检查语义路由
        elif task_type in self.semantic_routes:
            recommendation = self.semantic_routes[task_type]
            self._statistics["semantic_tasks"] += 1

        # 最后检查技术研究路由
        elif task_type in self.technical_routes:
            recommendation = self.technical_routes[task_type]
            self._statistics["professional_tasks"] += 1

        # 默认使用统一推理引擎
        else:
            recommendation = EngineRecommendation(
                engine_name="unified_reasoning_engine",
                engine_type="general_reasoning",
                confidence=0.70,
                reason="未找到特定路由,使用默认统一推理引擎",
                bypass_super_reasoning=False,
                direct_capability=False,
            )

        # 更新画像
        profile.selected_engine = recommendation.engine_name
        profile.confidence = recommendation.confidence

        logger.info(
            f"引擎选择: {recommendation.engine_name} | "
            f"置信度: {recommendation.confidence:.2f} | "
            f"绕过超级推理: {recommendation.bypass_super_reasoning}"
        )

        return recommendation

    def execute_reasoning(
        self,
        task_description: str,
        task_type: TaskType | None = None,
        metadata: dict | None = None,
        **kwargs,
    ) -> dict[str, Any]:
        """
        执行推理(统一入口)

        Args:
            task_description: 任务描述
            task_type: 任务类型(可选)
            metadata: 元数据
            **kwargs: 其他参数

        Returns:
            推理结果
        """
        # 1. 分析任务
        profile = self.analyze_task(task_description, task_type, metadata)

        # 2. 选择引擎
        recommendation = self.select_engine(profile)

        # 3. 记录推理轨迹
        profile.reasoning_trace.append(
            {
                "timestamp": datetime.now().isoformat(),
                "action": "engine_selection",
                "engine": recommendation.engine_name,
                "reason": recommendation.reason,
                "bypass_super_reasoning": recommendation.bypass_super_reasoning,
            }
        )

        # 4. 实际执行推理(这里需要根据引擎类型调用相应的引擎)
        result = self._execute_with_engine(task_description, recommendation, **kwargs)

        return {"result": result, "profile": profile, "recommendation": recommendation}

    def _execute_with_engine(
        self, task_description: str, recommendation: EngineRecommendation, **kwargs
    ) -> dict[str, Any]:
        """使用指定引擎执行推理"""

        # 如果是直接调用专业能力
        if recommendation.direct_capability:
            return self._call_direct_capability(task_description, recommendation, **kwargs)

        # 否则使用通用推理引擎
        return self._call_reasoning_engine(task_description, recommendation, **kwargs)

    def _call_direct_capability(
        self, task_description: str, recommendation: EngineRecommendation, **kwargs
    ) -> dict[str, Any]:
        """调用专业能力"""
        logger.info(f"调用专业能力: {recommendation.engine_name}")

        # 这里需要根据engine_name调用相应的专业能力
        # 例如:
        # if recommendation.engine_name == "professional_oa_responder":
        #     # TODO: ARCHITECTURE - 需要迁移到依赖注入模式
from services.office_action_response.src.professional_oa_responder import respond_to_office_action
        #     return await respond_to_office_action(...)

        return {
            "status": "success",
            "message": f"使用专业能力: {recommendation.engine_name}",
            "engine": recommendation.engine_name,
        }

    def _call_reasoning_engine(
        self, task_description: str, recommendation: EngineRecommendation, **kwargs
    ) -> dict[str, Any]:
        """调用推理引擎"""
        logger.info(f"调用推理引擎: {recommendation.engine_name}")

        # 这里需要根据engine_name调用相应的推理引擎
        return {
            "status": "success",
            "message": f"使用推理引擎: {recommendation.engine_name}",
            "engine": recommendation.engine_name,
        }

    def _infer_task_type(self, description: str, metadata: dict) -> TaskType:
        """推断任务类型"""
        # 简化版:基于关键词推断
        desc_lower = description.lower()

        if any(kw in desc_lower for kw in ["意见答复", "审查意见", "oa", "office action"]):
            return TaskType.OFFICE_ACTION_RESPONSE
        elif any(kw in desc_lower for kw in ["无效", "无效宣告", "invalidity"]):
            return TaskType.INVALIDITY_REQUEST
        elif any(kw in desc_lower for kw in ["专利撰写", "patent drafting", "申请文件"]):
            return TaskType.PATENT_DRAFTING
        elif any(kw in desc_lower for kw in ["合规", "compliance"]):
            return TaskType.PATENT_COMPLIANCE
        elif any(kw in desc_lower for kw in ["新颖性", "novelty"]):
            return TaskType.NOVELTY_ANALYSIS
        elif any(kw in desc_lower for kw in ["创造性", "inventiveness", "non-obvious"]):
            return TaskType.INVENTIVENESS_ANALYSIS
        elif any(kw in desc_lower for kw in ["权利要求", "claim"]):
            return TaskType.CLAIM_ANALYSIS
        elif any(kw in desc_lower for kw in ["语义搜索", "semantic"]):
            return TaskType.SEMANTIC_SEARCH
        elif any(kw in desc_lower for kw in ["技术态势", "landscape", "技术路线图"]):
            return TaskType.TECHNOLOGY_LANDSCAPE
        else:
            return TaskType.GENERAL_REASONING

    def _infer_domain(self, task_type: TaskType, metadata: dict) -> TaskDomain:
        """推断任务领域"""
        if task_type in [
            TaskType.OFFICE_ACTION_RESPONSE,
            TaskType.INVALIDITY_REQUEST,
            TaskType.PATENT_DRAFTING,
            TaskType.PATENT_COMPLIANCE,
            TaskType.NOVELTY_ANALYSIS,
            TaskType.INVENTIVENESS_ANALYSIS,
            TaskType.CLAIM_ANALYSIS,
        ]:
            return TaskDomain.PATENT_LAW
        elif task_type in [TaskType.SEMANTIC_SEARCH, TaskType.KNOWLEDGE_GRAPH_QUERY]:
            return TaskDomain.SEMANTIC_SEARCH
        elif task_type in [TaskType.TECHNOLOGY_LANDSCAPE, TaskType.ROADMAP_GENERATION]:
            return TaskDomain.TECHNICAL_RESEARCH
        else:
            return TaskDomain.GENERAL_ANALYSIS

    def _infer_complexity(self, task_type: TaskType, metadata: dict) -> TaskComplexity:
        """推断任务复杂度"""
        # 专业法律任务通常是专家级
        if task_type in [
            TaskType.OFFICE_ACTION_RESPONSE,
            TaskType.INVALIDITY_REQUEST,
            TaskType.PATENT_DRAFTING,
            TaskType.INVENTIVENESS_ANALYSIS,
        ]:
            return TaskComplexity.EXPERT

        # 其他专业任务通常是高复杂度
        elif task_type in [
            TaskType.NOVELTY_ANALYSIS,
            TaskType.CLAIM_ANALYSIS,
            TaskType.COMPLEX_PROBLEM_SOLVING,
        ]:
            return TaskComplexity.HIGH

        # 简单任务
        elif metadata.get("is_simple_task"):
            return TaskComplexity.LOW

        else:
            return TaskComplexity.MEDIUM

    def _requires_human_in_loop(self, task_type: TaskType) -> bool:
        """判断是否需要HITL"""
        high_difficulty_tasks = [
            TaskType.OFFICE_ACTION_RESPONSE,
            TaskType.INVALIDITY_REQUEST,
            TaskType.PATENT_DRAFTING,
            TaskType.INVENTIVENESS_ANALYSIS,
            TaskType.CLAIM_ANALYSIS,
        ]
        return task_type in high_difficulty_tasks

    def _is_legal_task(self, task_type: TaskType) -> bool:
        """判断是否是法律任务"""
        legal_tasks = [
            TaskType.OFFICE_ACTION_RESPONSE,
            TaskType.INVALIDITY_REQUEST,
            TaskType.PATENT_DRAFTING,
            TaskType.PATENT_COMPLIANCE,
            TaskType.NOVELTY_ANALYSIS,
            TaskType.INVENTIVENESS_ANALYSIS,
            TaskType.CLAIM_ANALYSIS,
        ]
        return task_type in legal_tasks

    def get_statistics(self) -> dict[str, Any]:
        """获取统计信息"""
        return {
            **self._statistics,
            "version": self.version,
            "created_at": self.created_at.isoformat(),
        }

    def reset_statistics(self) -> Any:
        """重置统计信息"""
        self._statistics = {
            "total_requests": 0,
            "professional_tasks": 0,
            "general_tasks": 0,
            "semantic_tasks": 0,
            "bypass_count": 0,
        }


# 全局单例
_orchestrator_instance: UnifiedReasoningOrchestrator | None = None


def get_orchestrator() -> UnifiedReasoningOrchestrator:
    """获取全局编排器实例"""
    global _orchestrator_instance
    if _orchestrator_instance is None:
        _orchestrator_instance = UnifiedReasoningOrchestrator()
    return _orchestrator_instance


# 便捷函数
def execute_reasoning(
    task_description: str,
    task_type: TaskType | None = None,
    metadata: dict | None = None,
    **kwargs,
) -> dict[str, Any]:
    """
    执行推理(便捷函数)

    Args:
        task_description: 任务描述
        task_type: 任务类型(可选)
        metadata: 元数据
        **kwargs: 其他参数

    Returns:
        推理结果
    """
    orchestrator = get_orchestrator()
    return orchestrator.execute_reasoning(task_description, task_type, metadata, **kwargs)


# 测试代码
if __name__ == "__main__":
    # 测试意见答复任务
    result = execute_reasoning(
        task_description="需要答复审查意见,审查员认为权利要求1-3不具备创造性",
        task_type=TaskType.OFFICE_ACTION_RESPONSE,
    )

    print("=" * 60)
    print("推理引擎编排器测试")
    print("=" * 60)
    print(f"任务类型: {result.get('profile').task_type.value}")
    print(f"领域: {result.get('profile').domain.value}")
    print(f"复杂度: {result.get('profile').complexity.value}")
    print(f"需要HITL: {result.get('profile').requires_human_in_loop}")
    print(f"法律任务: {result.get('profile').is_legal_task}")
    print(f"选择引擎: {result.get('recommendation').engine_name}")
    print(f"引擎类型: {result.get('recommendation').engine_type}")
    print(f"置信度: {result.get('recommendation').confidence:.2f}")
    print(f"绕过超级推理: {result.get('recommendation').bypass_super_reasoning}")
    print(f"直接专业能力: {result.get('recommendation').direct_capability}")
    print(f"原因: {result.get('recommendation').reason}")
    print("=" * 60)
