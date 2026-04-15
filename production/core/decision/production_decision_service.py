#!/usr/bin/env python3
"""
生产环境决策服务
Production Decision Service

统一的决策服务入口，集成多种决策引擎
支持规则引擎、机器学习、强化学习的混合决策

作者: 徐健 (xujian519@gmail.com)
版本: v1.0.0
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from production.core.decision.enhanced_decision_model import TaskComplexity

logger = logging.getLogger(__name__)


class DecisionPriority(Enum):
    """决策优先级"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class DecisionDomain(Enum):
    """决策领域"""
    PATENT = "patent"           # 专利相关决策
    LEGAL = "legal"             # 法律相关决策
    RESOURCE = "resource"       # 资源分配决策
    TASK = "task"               # 任务调度决策
    AGENT = "agent"             # 智能体分配决策
    GENERAL = "general"         # 通用决策


@dataclass
class ProductionDecisionRequest:
    """生产环境决策请求"""
    request_id: str
    domain: DecisionDomain
    task_type: str
    task_description: str
    context: dict[str, Any] = field(default_factory=dict)
    priority: DecisionPriority = DecisionPriority.MEDIUM
    constraints: dict[str, Any] = field(default_factory=dict)
    preferences: dict[str, Any] = field(default_factory=dict)
    timeout_ms: int = 5000
    require_explanation: bool = False


@dataclass
class ProductionDecisionResponse:
    """生产环境决策响应"""
    request_id: str
    decision_id: str
    action: str
    target: str
    confidence: float
    reasoning: str
    alternatives: list[str] = field(default_factory=list)
    explanation: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)
    processing_time_ms: float = 0.0
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


class ProductionDecisionService:
    """
    生产环境决策服务

    特点:
    - 统一的决策接口
    - 多引擎集成（规则、ML、RL）
    - 决策缓存
    - 监控和统计
    - 异步处理
    """

    def __init__(
        self,
        enable_cache: bool = True,
        cache_ttl_seconds: int = 300,
        enable_monitoring: bool = True,
    ):
        """
        初始化生产环境决策服务

        Args:
            enable_cache: 是否启用决策缓存
            cache_ttl_seconds: 缓存过期时间(秒)
            enable_monitoring: 是否启用监控
        """
        self.enable_cache = enable_cache
        self.cache_ttl_seconds = cache_ttl_seconds
        self.enable_monitoring = enable_monitoring

        # 决策引擎
        self._enhanced_model = None
        self._integrated_engine = None

        # 决策缓存
        self._cache: dict[str, tuple[ProductionDecisionResponse, float]] = {}

        # 统计信息
        self._stats = {
            "total_requests": 0,
            "successful_decisions": 0,
            "failed_decisions": 0,
            "cache_hits": 0,
            "cache_misses": 0,
            "average_confidence": 0.0,
            "average_processing_time_ms": 0.0,
            "decisions_by_domain": {},
            "decisions_by_priority": {},
        }

        logger.info("✅ 生产环境决策服务初始化完成")

    async def initialize(self) -> bool:
        """初始化决策引擎"""
        try:
            from production.core.decision.enhanced_decision_model import EnhancedDecisionModel
            from production.core.decision.integrated_decision_engine import IntegratedDecisionEngine

            self._enhanced_model = EnhancedDecisionModel()
            self._integrated_engine = IntegratedDecisionEngine()

            logger.info("✅ 决策引擎初始化成功")
            return True

        except Exception as e:
            logger.error(f"❌ 决策引擎初始化失败: {e}")
            return False

    async def decide(
        self,
        request: ProductionDecisionRequest
    ) -> ProductionDecisionResponse:
        """
        执行决策

        Args:
            request: 决策请求

        Returns:
            ProductionDecisionResponse: 决策响应
        """
        import time
        start_time = time.time()

        self._stats["total_requests"] += 1
        self._update_domain_stats(request.domain)
        self._update_priority_stats(request.priority)

        # 检查缓存
        if self.enable_cache:
            cached = self._get_from_cache(request)
            if cached:
                self._stats["cache_hits"] += 1
                logger.debug(f"缓存命中: {request.request_id}")
                return cached

        self._stats["cache_misses"] += 1

        try:
            # 执行决策
            response = await self._execute_decision(request)

            # 更新缓存
            if self.enable_cache:
                self._add_to_cache(request, response)

            # 更新统计
            self._stats["successful_decisions"] += 1
            self._update_confidence_stats(response.confidence)

            processing_time = (time.time() - start_time) * 1000
            response.processing_time_ms = processing_time
            self._update_time_stats(processing_time)

            logger.info(
                f"决策完成: request_id={request.request_id}, "
                f"action={response.action}, confidence={response.confidence:.2f}, "
                f"time={processing_time:.1f}ms"
            )

            return response

        except Exception as e:
            self._stats["failed_decisions"] += 1
            logger.error(f"决策失败: {e}")

            # 返回降级响应
            return ProductionDecisionResponse(
                request_id=request.request_id,
                decision_id=f"fallback_{datetime.now().timestamp()}",
                action="fallback_action",
                target="fallback_target",
                confidence=0.5,
                reasoning=f"决策失败，使用降级策略: {str(e)}",
                metadata={"error": str(e), "fallback": True},
            )

    async def _execute_decision(
        self,
        request: ProductionDecisionRequest
    ) -> ProductionDecisionResponse:
        """执行实际决策"""
        from production.core.decision.enhanced_decision_model import (
            DecisionContext,
        )

        # 构建决策上下文
        complexity = self._assess_complexity(request)
        context = DecisionContext(
            task_type=request.task_type,
            task_description=request.task_description,
            complexity=complexity,
            available_tools=request.context.get("available_tools", []),
            available_agents=request.context.get("available_agents", []),
            historical_success_rate=request.context.get("success_rate", 0.8),
            resource_constraints=request.constraints,
            time_constraints={"timeout_ms": request.timeout_ms},
            user_preferences=request.preferences,
        )

        # 使用增强决策模型
        decision = await self._enhanced_model.decide(context)

        # 构建响应
        explanation = ""
        if request.require_explanation:
            explanation = self._generate_explanation(decision, request)

        return ProductionDecisionResponse(
            request_id=request.request_id,
            decision_id=decision.decision_id,
            action=decision.action,
            target=decision.target,
            confidence=decision.confidence,
            reasoning=decision.reasoning,
            alternatives=decision.alternative_actions,
            explanation=explanation,
            metadata={
                "risk_level": decision.risk_level,
                "expected_outcome": decision.expected_outcome,
                "domain": request.domain.value,
                "priority": request.priority.value,
            },
        )

    def _assess_complexity(self, request: ProductionDecisionRequest) -> TaskComplexity:
        """评估任务复杂度"""
        from production.core.decision.enhanced_decision_model import TaskComplexity

        # 基于优先级和领域评估复杂度
        if request.priority == DecisionPriority.CRITICAL:
            return TaskComplexity.EXPERT
        elif request.priority == DecisionPriority.HIGH:
            return TaskComplexity.COMPLEX
        elif request.domain in [DecisionDomain.PATENT, DecisionDomain.LEGAL]:
            return TaskComplexity.MODERATE
        else:
            return TaskComplexity.SIMPLE

    def _generate_explanation(
        self,
        decision: Any,
        request: ProductionDecisionRequest
    ) -> str:
        """生成决策解释"""
        return (
            f"决策引擎基于{request.task_type}任务类型，"
            f"综合规则引擎(权重0.4)、机器学习引擎(权重0.3)和强化学习引擎(权重0.3)的分析结果，"
            f"选择执行动作'{decision.action}'，置信度为{decision.confidence:.2f}。"
            f"主要原因：{decision.reasoning}"
        )

    def _get_cache_key(self, request: ProductionDecisionRequest) -> str:
        """生成缓存键"""
        return f"{request.domain.value}_{request.task_type}_{hash(request.task_description)}"

    def _get_from_cache(
        self,
        request: ProductionDecisionRequest
    ) -> ProductionDecisionResponse | None:
        """从缓存获取决策"""
        import time
        key = self._get_cache_key(request)

        if key in self._cache:
            response, timestamp = self._cache[key]
            if time.time() - timestamp < self.cache_ttl_seconds:
                return response
            else:
                del self._cache[key]

        return None

    def _add_to_cache(
        self,
        request: ProductionDecisionRequest,
        response: ProductionDecisionResponse
    ):
        """添加到缓存"""
        import time
        key = self._get_cache_key(request)
        self._cache[key] = (response, time.time())

    def _update_domain_stats(self, domain: DecisionDomain):
        """更新领域统计"""
        domain_str = domain.value
        self._stats["decisions_by_domain"][domain_str] = \
            self._stats["decisions_by_domain"].get(domain_str, 0) + 1

    def _update_priority_stats(self, priority: DecisionPriority):
        """更新优先级统计"""
        priority_str = priority.value
        self._stats["decisions_by_priority"][priority_str] = \
            self._stats["decisions_by_priority"].get(priority_str, 0) + 1

    def _update_confidence_stats(self, confidence: float):
        """更新置信度统计"""
        n = self._stats["successful_decisions"]
        old_avg = self._stats["average_confidence"]
        self._stats["average_confidence"] = (old_avg * (n - 1) + confidence) / n

    def _update_time_stats(self, processing_time_ms: float):
        """更新处理时间统计"""
        n = self._stats["successful_decisions"]
        old_avg = self._stats["average_processing_time_ms"]
        self._stats["average_processing_time_ms"] = (old_avg * (n - 1) + processing_time_ms) / n

    def get_stats(self) -> dict[str, Any]:
        """获取统计信息"""
        total = self._stats["total_requests"]
        if total > 0:
            cache_hit_rate = self._stats["cache_hits"] / total
            success_rate = self._stats["successful_decisions"] / total
        else:
            cache_hit_rate = 0.0
            success_rate = 0.0

        return {
            **self._stats,
            "cache_hit_rate": cache_hit_rate,
            "success_rate": success_rate,
            "cache_size": len(self._cache),
        }

    def clear_cache(self):
        """清空缓存"""
        self._cache.clear()
        logger.info("决策缓存已清空")

    async def learn_from_feedback(
        self,
        request_id: str,
        decision_id: str,
        outcome: str,
        feedback_score: float,
    ):
        """
        从反馈中学习

        Args:
            request_id: 请求ID
            decision_id: 决策ID
            outcome: 结果描述
            feedback_score: 反馈分数 (0.0-1.0)
        """
        try:
            if self._enhanced_model:
                await self._enhanced_model.learn_from_feedback(
                    trace_id=decision_id,
                    outcome=outcome,
                    feedback=feedback_score,
                )
                logger.info(f"反馈学习完成: decision_id={decision_id}, score={feedback_score}")
        except Exception as e:
            logger.warning(f"反馈学习失败: {e}")


# 单例实例
_production_decision_service: ProductionDecisionService | None = None


async def get_production_decision_service() -> ProductionDecisionService:
    """获取生产环境决策服务单例"""
    global _production_decision_service
    if _production_decision_service is None:
        _production_decision_service = ProductionDecisionService()
        await _production_decision_service.initialize()
    return _production_decision_service


# 便捷函数
async def make_decision(
    task_type: str,
    task_description: str,
    domain: DecisionDomain = DecisionDomain.GENERAL,
    **kwargs
) -> ProductionDecisionResponse:
    """
    便捷决策函数

    Args:
        task_type: 任务类型
        task_description: 任务描述
        domain: 决策领域
        **kwargs: 其他参数

    Returns:
        ProductionDecisionResponse: 决策响应
    """
    service = await get_production_decision_service()

    request = ProductionDecisionRequest(
        request_id=f"req_{datetime.now().timestamp()}",
        domain=domain,
        task_type=task_type,
        task_description=task_description,
        **kwargs
    )

    return await service.decide(request)
