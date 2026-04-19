#!/usr/bin/env python3
"""
模块集成适配器
Module Integration Adapter

将新创建的核心模块集成到现有的Athena和小诺服务中

作者: Athena平台团队
创建时间: 2025-12-31
版本: 1.0.0
"""

from __future__ import annotations
import logging
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class IntegrationStatus(Enum):
    """集成状态"""
    NOT_INITIALIZED = "not_initialized"
    INITIALIZING = "initializing"
    READY = "ready"
    ACTIVE = "active"
    ERROR = "error"


@dataclass
class IntegrationMetrics:
    """集成指标"""
    module_name: str
    status: IntegrationStatus
    initialization_time: float = 0.0
    last_active_time: datetime | None = None
    call_count: int = 0
    success_count: int = 0
    failure_count: int = 0
    average_response_time: float = 0.0
    last_error: str | None = None


class ModuleIntegrationAdapter:
    """
    模块集成适配器

    负责将新模块集成到现有服务中，并提供统一的接口
    """

    def __init__(self):
        self.modules: dict[str, Any] = {}
        self.metrics: dict[str, IntegrationMetrics] = {}
        self.status: IntegrationStatus = IntegrationStatus.NOT_INITIALIZED
        self.initialization_start: datetime | None = None

    async def initialize(
        self,
        enable_emotion_creative: bool = True,
        enable_semantic_fusion: bool = True,
        enable_family_cocreation: bool = True,
    ):
        """
        初始化集成适配器

        Args:
            enable_emotion_creative: 是否启用情感驱动创意引擎
            enable_semantic_fusion: 是否启用语义级跨域融合引擎
            enable_family_cocreation: 是否启用父女三人共创系统
        """
        logger.info("🔧 初始化模块集成适配器...")
        self.initialization_start = datetime.now()
        self.status = IntegrationStatus.INITIALIZING

        try:
            # 初始化情感驱动创意引擎
            if enable_emotion_creative:
                await self._init_emotion_creative_engine()

            # 初始化语义级跨域融合引擎
            if enable_semantic_fusion:
                await self._init_semantic_fusion_engine()

            # 初始化父女三人共创系统
            if enable_family_cocreation:
                await self._init_family_cocreation_system()

            self.status = IntegrationStatus.READY
            init_time = (datetime.now() - self.initialization_start).total_seconds()

            logger.info(f"✅ 模块集成适配器初始化完成 (耗时: {init_time:.2f}秒)")
            logger.info(f"   已加载模块: {', '.join(self.modules.keys())}")

        except Exception as e:
            logger.error(f"❌ 模块集成适配器初始化失败: {e}")
            self.status = IntegrationStatus.ERROR
            raise

    async def _init_emotion_creative_engine(self):
        """初始化情感驱动创意引擎"""
        from production.core.cognition.emotion_creative_engine import (
            get_emotion_creative_engine,
        )

        logger.info("🎨 初始化情感驱动创意引擎...")
        engine = await get_emotion_creative_engine()
        self.modules["emotion_creative"] = engine
        self.metrics["emotion_creative"] = IntegrationMetrics(
            module_name="情感驱动创意引擎",
            status=IntegrationStatus.READY,
            initialization_time=(datetime.now() - self.initialization_start).total_seconds()
            if self.initialization_start else 0.0,
        )
        logger.info("✅ 情感驱动创意引擎已加载")

    async def _init_semantic_fusion_engine(self):
        """初始化语义级跨域融合引擎"""
        from production.core.fusion.semantic_cross_domain_fusion import (
            get_semantic_fusion_engine,
        )

        logger.info("🔗 初始化语义级跨域融合引擎...")
        engine = await get_semantic_fusion_engine()
        self.modules["semantic_fusion"] = engine
        self.metrics["semantic_fusion"] = IntegrationMetrics(
            module_name="语义级跨域融合引擎",
            status=IntegrationStatus.READY,
            initialization_time=(datetime.now() - self.initialization_start).total_seconds()
            if self.initialization_start else 0.0,
        )
        logger.info("✅ 语义级跨域融合引擎已加载")

    async def _init_family_cocreation_system(self):
        """初始化父女三人共创系统"""
        from production.core.collaboration.family_cocreation_system import (
            get_family_cocreation_system,
        )

        logger.info("👨‍👩‍👧 初始化父女三人共创系统...")
        system = await get_family_cocreation_system()
        self.modules["family_cocreation"] = system
        self.metrics["family_cocreation"] = IntegrationMetrics(
            module_name="父女三人共创系统",
            status=IntegrationStatus.READY,
            initialization_time=(datetime.now() - self.initialization_start).total_seconds()
            if self.initialization_start else 0.0,
        )
        logger.info("✅ 父女三人共创系统已加载")

    # ==================== 小诺服务接口 ====================

    async def xiaonuo_generate_creative_idea(
        self,
        query: str,
        user_emotion: str = "neutral",
        domain: str = "general",
        context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """
        小诺服务：生成创意方案

        Args:
            query: 用户查询
            user_emotion: 用户情感 (frustration, urgency, uncertainty, satisfaction, neutral)
            domain: 领域
            context: 上下文

        Returns:
            创意方案字典
        """
        from production.core.cognition.emotion_creative_engine import UserEmotion

        module = self.modules.get("emotion_creative")
        if not module:
            return {"error": "情感驱动创意引擎未初始化"}

        emotion = UserEmotion(user_emotion) if user_emotion != "neutral" else UserEmotion.NEUTRAL

        idea = await module.generate_with_emotion(
            user_query=query,
            user_emotion=emotion,
            domain=domain,
            context=context,
        )

        self._update_metrics("emotion_creative", True)

        return {
            "idea_id": idea.idea_id,
            "title": idea.title,
            "description": idea.description,
            "creativity_mode": idea.creativity_mode.value,
            "practicality": {
                "overall": idea.practicality.overall_practicality,
                "actionability": idea.practicality.actionability,
                "resource_feasibility": idea.practicality.resource_feasibility,
                "time_to_value": idea.practicality.time_to_value,
                "implementation_complexity": idea.practicality.implementation_complexity,
                "user_friendly_score": idea.practicality.user_friendly_score,
            },
            "implementation_steps": idea.implementation_steps,
            "estimated_effort": idea.estimated_effort,
            "confidence_score": idea.confidence_score,
        }

    async def xiaonuo_generate_roadmap(
        self, idea_id: str, domain: str = "general"
    ) -> dict[str, Any]:
        """小诺服务：生成实施路线图"""
        from production.core.cognition.emotion_creative_engine import (
            CreativeIdea,
        )

        module = self.modules.get("emotion_creative")
        if not module:
            return {"error": "情感驱动创意引擎未初始化"}

        # 创建一个临时创意对象
        from production.core.cognition.emotion_creative_engine import (
            CreativityMode,
            PracticalityMetrics,
            UserEmotion,
        )

        idea = CreativeIdea(
            idea_id=idea_id,
            title="临时创意",
            description="用于生成路线图",
            emotion_source=UserEmotion.NEUTRAL,
            creativity_mode=CreativityMode.BALANCED,
            practicality=PracticalityMetrics(),
        )

        roadmap = await module.generate_roadmap(idea, domain)

        return {
            "idea_id": roadmap.idea_id,
            "phases": roadmap.phases,
            "total_estimated_time": roadmap.total_estimated_time,
            "resource_summary": roadmap.resource_summary,
            "success_metrics": roadmap.success_metrics,
            "risk_mitigation": roadmap.risk_mitigation,
        }

    # ==================== Athena服务接口 ====================

    async def athena_cross_domain_fusion(
        self,
        query: str,
        domains: list[str],
        fusion_depth: str = "semantic",
    ) -> dict[str, Any]:
        """
        Athena服务：跨域融合分析

        Args:
            query: 查询内容
            domains: 领域列表 (patent_law, technology, business, ai_ml, legal, finance, medical, education)
            fusion_depth: 融合深度 (surface, functional, semantic, conceptual, integrated)

        Returns:
            融合分析结果
        """
        from production.core.fusion.semantic_cross_domain_fusion import (
            DomainType,
            FusionDepth,
        )

        module = self.modules.get("semantic_fusion")
        if not module:
            return {"error": "语义级跨域融合引擎未初始化"}

        # 转换领域
        domain_map = {
            "patent_law": DomainType.PATENT_LAW,
            "technology": DomainType.TECHNOLOGY,
            "business": DomainType.BUSINESS,
            "ai_ml": DomainType.AI_ML,
            "legal": DomainType.LEGAL,
            "finance": DomainType.FINANCE,
            "medical": DomainType.MEDICAL,
            "education": DomainType.EDUCATION,
            "general": DomainType.GENERAL,
        }

        domain_types = [domain_map.get(d, DomainType.GENERAL) for d in domains]
        depth = FusionDepth(fusion_depth) if fusion_depth != "semantic" else FusionDepth.SEMANTIC

        insight = await module.deep_semantic_fusion(query, domain_types, depth)

        self._update_metrics("semantic_fusion", True)

        return {
            "insight_id": insight.insight_id,
            "source_domains": [d.value for d in insight.source_domains],
            "concept_mappings": [
                {
                    "source": m.source_concept,
                    "target": m.target_concept,
                    "source_domain": m.source_domain.value,
                    "target_domain": m.target_domain.value,
                    "similarity": m.semantic_similarity,
                }
                for m in insight.concept_mappings
            ],
            "cross_domain_insights": insight.cross_domain_insights,
            "fused_understanding": insight.fused_understanding,
            "novelty_score": insight.novelty_score,
            "utility_score": insight.utility_score,
            "fusion_depth": insight.fusion_depth.value,
        }

    async def athena_multimodal_fusion(
        self,
        text: str,
        structured_data: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Athena服务：多模态融合"""
        module = self.modules.get("semantic_fusion")
        if not module:
            return {"error": "语义级跨域融合引擎未初始化"}

        result = await module.fuse_multimodal(text, structured_data)

        self._update_metrics("semantic_fusion", True)

        return {
            "text_understanding": result.text_understanding,
            "structured_insights": result.structured_insights,
            "cross_modal_associations": result.cross_modal_associations,
            "unified_representation": result.unified_representation,
        }

    # ==================== 父女三人协作接口 ====================

    async def family_cocreate(
        self,
        task_title: str,
        task_description: str,
        complexity: str = "moderate",
        pattern: str = "sequential",
        context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """
        父女三人协作：共创任务

        Args:
            task_title: 任务标题
            task_description: 任务描述
            complexity: 复杂度 (simple, moderate, complex, very_complex)
            pattern: 协作模式 (sequential, parallel, iterative)
            context: 上下文

        Returns:
            共创结果
        """
        from production.core.collaboration.family_cocreation_system import (
            ComplexTask,
            TaskComplexity,
        )

        module = self.modules.get("family_cocreation")
        if not module:
            return {"error": "父女三人共创系统未初始化"}

        complexity_map = {
            "simple": TaskComplexity.SIMPLE,
            "moderate": TaskComplexity.MODERATE,
            "complex": TaskComplexity.COMPLEX,
            "very_complex": TaskComplexity.VERY_COMPLEX,
        }

        task = ComplexTask(
            task_id=f"TASK_{datetime.now().strftime('%Y%m%d%H%M%S')}",
            title=task_title,
            description=task_description,
            complexity=complexity_map.get(complexity, TaskComplexity.MODERATE),
            required_capabilities=["分析", "创意", "执行"],
            estimated_duration="根据复杂度确定",
            priority="normal",
            context=context or {},
        )

        result = await module.cocreate(task, pattern, context)

        self._update_metrics("family_cocreation", True)

        return {
            "session_id": result.session_id,
            "task_id": result.task_id,
            "final_decision": result.final_decision,
            "execution_plan": result.execution_plan,
            "insights": result.insights,
            "quality_score": result.quality_score,
            "satisfaction_scores": {k.value: v for k, v in result.satisfaction_scores.items()},
            "collaboration_metrics": result.collaboration_metrics,
            "next_steps": result.next_steps,
        }

    # ==================== 性能监控接口 ====================

    def _update_metrics(self, module_name: str, success: bool):
        """更新模块指标"""
        if module_name in self.metrics:
            metric = self.metrics[module_name]
            metric.call_count += 1
            if success:
                metric.success_count += 1
            else:
                metric.failure_count += 1
            metric.last_active_time = datetime.now()
            metric.status = IntegrationStatus.ACTIVE

    async def get_module_metrics(self) -> dict[str, dict[str, Any]]:
        """获取所有模块的性能指标"""
        return {
            name: {
                "module": metric.module_name,
                "status": metric.status.value,
                "call_count": metric.call_count,
                "success_count": metric.success_count,
                "failure_count": metric.failure_count,
                "success_rate": (
                    metric.success_count / metric.call_count if metric.call_count > 0 else 0
                ),
                "average_response_time": metric.average_response_time,
                "last_error": metric.last_error,
            }
            for name, metric in self.metrics.items()
        }

    async def get_module_statistics(self) -> dict[str, Any]:
        """获取模块统计信息"""
        stats = {}

        if "emotion_creative" in self.modules:
            from production.core.cognition.emotion_creative_engine import (
                get_emotion_creative_engine,
            )
            engine = await get_emotion_creative_engine()
            stats["emotion_creative"] = await engine.get_creative_statistics()

        if "semantic_fusion" in self.modules:
            from production.core.fusion.semantic_cross_domain_fusion import (
                get_semantic_fusion_engine,
            )
            engine = await get_semantic_fusion_engine()
            stats["semantic_fusion"] = await engine.get_fusion_statistics()

        if "family_cocreation" in self.modules:
            from production.core.collaboration.family_cocreation_system import (
                get_family_cocreation_system,
            )
            system = await get_family_cocreation_system()
            stats["family_cocreation"] = await system.get_collaboration_statistics()

        return stats

    async def health_check(self) -> dict[str, Any]:
        """健康检查"""
        return {
            "adapter_status": self.status.value,
            "modules_loaded": list(self.modules.keys()),
            "module_count": len(self.modules),
            "total_calls": sum(m.call_count for m in self.metrics.values()),
            "total_successes": sum(m.success_count for m in self.metrics.values()),
            "overall_health": "healthy" if self.status == IntegrationStatus.READY else "unhealthy",
        }

    async def shutdown(self):
        """关闭适配器"""
        logger.info("🛑 关闭模块集成适配器...")

        for name, module in self.modules.items():
            try:
                if hasattr(module, "shutdown"):
                    await module.shutdown()
                    logger.info(f"✅ {name} 已关闭")
            except Exception as e:
                logger.error(f"❌ 关闭 {name} 时出错: {e}")

        self.modules.clear()
        self.metrics.clear()
        self.status = IntegrationStatus.NOT_INITIALIZED

        logger.info("✅ 模块集成适配器已关闭")


# 全局单例
_integration_adapter: ModuleIntegrationAdapter | None = None


async def get_integration_adapter() -> ModuleIntegrationAdapter:
    """获取集成适配器单例"""
    global _integration_adapter
    if _integration_adapter is None:
        _integration_adapter = ModuleIntegrationAdapter()
        await _integration_adapter.initialize()
    return _integration_adapter
