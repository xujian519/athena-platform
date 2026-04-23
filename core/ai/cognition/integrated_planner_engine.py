#!/usr/bin/env python3

"""
智能规划引擎集成增强意图分析器
Intelligent Planner Engine - Enhanced Intent Analyzer Integration

将增强意图分析器集成到智能规划引擎中，提供更精准的意图识别能力。

集成策略：
1. 保持向后兼容性
2. 使用增强分析器替换基础分析器
3. 扩展Intent数据结构支持增强信息
4. 提供降级机制（当增强分析器不可用时）

Author: Athena Team
Version: 1.0.0
Date: 2026-02-24
"""

import logging
from datetime import datetime
from typing import Any, Optional

from core.cognition.xiaonuo_planner_engine import (
    ExecutionPlan,
    Intent,
    IntentType,
    XiaonuoPlannerEngine,
)

logger = logging.getLogger(__name__)


# ========== 增强意图类型映射 ==========


class EnhancedIntentTypeMapping:
    """增强意图类型到基础意图类型的映射"""

    # 映射规则
    MAPPING = {
        # 专利相关意图 -> ANALYSIS 或 TASK
        "patent_writing": IntentType.TASK,
        "patent_search": IntentType.QUERY,
        "patent_analysis": IntentType.ANALYSIS,
        "patent_novelty": IntentType.ANALYSIS,
        "patent_creativity": IntentType.ANALYSIS,
        "patent_infringement": IntentType.ANALYSIS,
        "patent_invalidation": IntentType.ANALYSIS,
        "patent_comparison": IntentType.ANALYSIS,

        # 法律相关意图 -> ANALYSIS 或 TASK
        "legal_consultation": IntentType.QUERY,
        "legal_document_review": IntentType.ANALYSIS,
        "legal_research": IntentType.QUERY,
        "contract_review": IntentType.ANALYSIS,

        # 商标相关意图
        "trademark_search": IntentType.QUERY,
        "trademark_registration": IntentType.TASK,
        "trademark_analysis": IntentType.ANALYSIS,

        # 通用意图
        "query": IntentType.QUERY,
        "chat": IntentType.CHAT,
        "unknown": IntentType.UNKNOWN,
    }

    @classmethod
    def map(cls, enhanced_intent_type_str: str) -> IntentType:
        """将增强意图类型映射到基础意图类型"""
        return cls.MAPPING.get(enhanced_intent_type_str, IntentType.UNKNOWN)


# ========== 增强意图适配器 ==========


class EnhancedIntentAdapter:
    """增强意图适配器 - 将EnhancedIntent转换为Intent"""

    @staticmethod
    def to_intent(enhanced_intent: Any) -> Intent:
        """
        将增强意图对象转换为标准意图对象

        Args:
            enhanced_intent: EnhancedIntent对象

        Returns:
            Intent: 标准意图对象
        """
        # 映射意图类型
        enhanced_type_str = enhanced_intent.intent_type.value
        base_intent_type = EnhancedIntentTypeMapping.map(enhanced_type_str)

        # 扩展子目标列表，包含增强信息
        sub_goals = []

        # 添加业务阶段作为子目标
        if enhanced_intent.phase:
            sub_goals.append(f"业务阶段: {enhanced_intent.phase.value}")

        # 添加专利类型信息
        if enhanced_intent.patent_type:
            sub_goals.append(f"专利类型: {enhanced_intent.patent_type.value}")

        # 添加子领域信息
        if enhanced_intent.patent_sub_domain:
            sub_goals.append(f"技术领域: {enhanced_intent.patent_sub_domain.value}")

        # 添加需要的层级
        if enhanced_intent.required_layers:
            sub_goals.append(f"需要层级: {', '.join(l.value for l in enhanced_intent.required_layers)}")

        # 扩展实体信息
        entities = enhanced_intent.entities.copy()

        # 添加法律世界模型相关信息
        entities["domain"] = enhanced_intent.domain.value
        if enhanced_intent.task_type:
            entities["task_type"] = enhanced_intent.task_type.value
        if enhanced_intent.phase:
            entities["phase"] = enhanced_intent.phase.value
        if enhanced_intent.layer_type:
            entities["layer_type"] = enhanced_intent.layer_type.value
        if enhanced_intent.patent_type:
            entities["patent_type"] = enhanced_intent.patent_type.value
        if enhanced_intent.patent_sub_domain:
            entities["patent_sub_domain"] = enhanced_intent.patent_sub_domain.value
        if enhanced_intent.suggested_agent:
            entities["suggested_agent"] = enhanced_intent.suggested_agent
        if enhanced_intent.required_documents:
            entities["required_documents"]] = [doc.value for doc in enhanced_intent.required_documents]

        # 合并提取的变量
        entities.update(enhanced_intent.extracted_variables)

        # 扩展上下文信息
        context = enhanced_intent.context.copy()
        context["enhanced_analysis"] = True
        context["required_layers"]] = [layer.value for layer in enhanced_intent.required_layers]

        return Intent(
            intent_type=base_intent_type,
            primary_goal=enhanced_intent.primary_goal,
            sub_goals=sub_goals,
            entities=entities,
            confidence=enhanced_intent.confidence,
            context=context,
        )


# ========== 集成智能规划引擎 ==========


class IntegratedPlannerEngine(XiaonuoPlannerEngine):
    """
    集成增强意图分析器的智能规划引擎

    继承自XiaonuoPlannerEngine，使用增强意图分析器替换基础分析器。
    """

    def __init__(self, use_enhanced_analyzer: bool = True):
        """
        初始化集成规划引擎

        Args:
            use_enhanced_analyzer: 是否使用增强意图分析器
        """
        # 调用父类初始化
        super().__init__()

        self.use_enhanced_analyzer = use_enhanced_analyzer

        # 尝试初始化增强意图分析器
        if use_enhanced_analyzer:
            try:
                from core.cognition.enhanced_intent_analyzer import (
                    EnhancedIntentAnalyzer,
                )

                self.enhanced_intent_analyzer = EnhancedIntentAnalyzer()
                self.intent_analyzer = self  # 替换父类的分析器引用
                self.enhanced_available = True
                self.logger.info("   ✅ 增强意图分析器已启用")
            except ImportError as e:
                self.enhanced_available = False
                self.logger.warning(f"   ⚠️ 增强意图分析器加载失败: {e}")
                self.logger.info("   📌 使用基础意图分析器")
        else:
            self.enhanced_available = False
            self.logger.info("   📌 使用基础意图分析器（增强分析器已禁用）")

    async def analyze(self, user_input: str, context: Optional[dict[str, Any]] = None):
        """
        分析用户意图 - 集成版本

        如果增强分析器可用，使用增强分析器；
        否则使用基础分析器。

        Args:
            user_input: 用户输入
            context: 上下文信息

        Returns:
            Intent: 意图对象（基础格式）
        """
        if self.enhanced_available and self.enhanced_intent_analyzer:
            # 使用增强意图分析器
            enhanced_intent = await self.enhanced_intent_analyzer.analyze(
                user_input, context or {}
            )

            # 转换为标准Intent格式
            intent = EnhancedIntentAdapter.to_intent(enhanced_intent)

            # 记录增强分析结果
            self.logger.info(
                f"   🔍 [增强分析] "
                f"意图={enhanced_intent.intent_type.value}, "
                f"领域={enhanced_intent.domain.value}"
            )

            if enhanced_intent.patent_type:
                self.logger.info(f"   📋 专利类型: {enhanced_intent.patent_type.value}")

            if enhanced_intent.patent_sub_domain:
                self.logger.info(f"   🌾 子领域: {enhanced_intent.patent_sub_domain.value}")

            if enhanced_intent.required_layers:
                layers_str = ", ".join(l.value for l in enhanced_intent.required_layers)
                self.logger.info(f"   📚 需要层级: {layers_str}")

            return intent
        else:
            # 使用基础意图分析器（父类已初始化）
            return await super().analyze(user_input, context)

    async def plan(
        self,
        user_input: str,
        context: Optional[dict[str, Any]] = None
    ) -> ExecutionPlan:
        """
        生成执行规划 - 集成版本

        Args:
            user_input: 用户输入
            context: 上下文信息

        Returns:
            ExecutionPlan: 执行方案
        """
        # 使用集成的analyze方法
        intent = await self.analyze(user_input, context or {})

        # 获取增强信息（如果存在）
        enhanced_info = intent.context.get("enhanced_analysis", {})
        required_layers = intent.context.get("required_layers", [])
        suggested_agent = intent.entities.get("suggested_agent")

        self.logger.info(
            f"   📊 意图识别: {intent.intent_type.value} "
            f"(置信度: {intent.confidence:.2f})"
        )

        if enhanced_info:
            self.logger.info("   ✨ 使用增强意图分析")

        # 2. 任务分解
        steps = await self.task_decomposer.decompose(intent, context or {})
        self.logger.info(f"   📋 任务分解: {len(steps)} 个步骤")

        # 如果有建议的智能体，可以优化步骤分配
        if suggested_agent and steps:
            self.logger.info(f"   👤 建议智能体: {suggested_agent}")
            # 可以在这里优化步骤分配逻辑

        # 3. 资源评估（考虑需要的层级）
        resource_req = self._evaluate_resources(steps, intent)
        if required_layers:
            resource_req.databases.extend([f"{layer}_db" for layer in required_layers])

        # 4. 风险评估
        risks = self._assess_risks(steps, intent, resource_req)

        # 5. 执行模式选择
        mode = self._select_execution_mode(steps, intent)

        # 6. 生成方案
        plan = ExecutionPlan(
            plan_id=f"plan_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            intent=intent,
            steps=steps,
            mode=mode,
            resource_requirements=resource_req,
            risks=risks,
            confidence=self._calculate_confidence(intent, steps, risks),
            estimated_time=sum(s.estimated_time for s in steps),
            metadata={
                "planner_version": "2.0.0-enhanced",
                "platform_status": self.platform_resources,
                "enhanced_analysis": enhanced_info,
                "required_layers": required_layers,
                "suggested_agent": suggested_agent,
            }
        )

        # 7. 保存历史
        self.planning_history.append(plan)

        self.logger.info(f"   ✅ 方案生成完成: {plan.plan_id} (置信度: {plan.confidence.value})")
        return plan

    def get_planning_stats(self) -> dict[str, Any]:
        """获取规划统计信息"""
        stats = super().get_planning_stats()

        # 添加增强分析器统计
        if self.enhanced_available:
            enhanced_stats = self.enhanced_intent_analyzer.get_recognition_stats()
            stats["enhanced_analyzer"] = enhanced_stats

        stats["integration_mode"] = "enhanced" if self.enhanced_available else "basic"

        return stats


# ========== 工厂函数 ==========


def create_planner_engine(use_enhanced: bool = True) -> XiaonuoPlannerEngine:
    """
    创建规划引擎

    Args:
        use_enhanced: 是否使用增强版本

    Returns:
        XiaonuoPlannerEngine: 规划引擎实例
    """
    if use_enhanced:
        return IntegratedPlannerEngine(use_enhanced_analyzer=True)
    else:
        return XiaonuoPlannerEngine()


# ========== 导出 ==========

__all__ = [
    "IntegratedPlannerEngine",
    "EnhancedIntentTypeMapping",
    "EnhancedIntentAdapter",
    "create_planner_engine",
]

