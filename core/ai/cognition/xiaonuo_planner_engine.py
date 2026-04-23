#!/usr/bin/env python3

"""
小诺·双鱼公主智能规划引擎 v3.0
Xiaonuo Pisces Princess Intelligent Planner Engine v3.0

核心能力:
1. 智能意图理解 - 深度理解用户真实需求
2. 多方案生成 - 生成多个可行方案
3. 智能方案选择 - 基于成本/风险/时间对比选择最优方案
4. 资源状态评估 - 评估平台资源状态
5. 风险预测分析 - 预测潜在风险

Phase 3 学习优化系统:
6. 反馈收集 - 收集执行反馈和用户满意度
7. 方案评估 - 多维度评估方案质量
8. 策略优化 - 基于历史数据优化规划策略
9. 知识库管理 - 存储和检索规划经验

Author: Athena Team
Version: 3.0.0
Date: 2026-02-24
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Optional

# Import PlanStrategy for type hints in Phase 3 methods
# This is imported locally to avoid circular dependencies
try:
    from .multi_plan_generator import PlanStrategy
except ImportError:
    PlanStrategy = None  # type: ignore

logger = logging.getLogger(__name__)


# ========== 数据结构 ==========


class IntentType(Enum):
    """意图类型"""
    QUERY = "query"  # 查询类请求
    TASK = "task"  # 任务执行类请求
    ANALYSIS = "analysis"  # 分析类请求
    OPTIMIZATION = "optimization"  # 优化类请求
    COORDINATION = "coordination"  # 协调类请求
    CHAT = "chat"  # 聊天陪伴
    UNKNOWN = "unknown"


class PlanConfidence(Enum):
    """方案置信度"""
    HIGH = "high"  # 高置信度 (>0.8)
    MEDIUM = "medium"  # 中置信度 (0.5-0.8)
    LOW = "low"  # 低置信度 (<0.5)


class ExecutionMode(Enum):
    """执行模式"""
    SEQUENTIAL = "sequential"  # 顺序执行
    PARALLEL = "parallel"  # 并行执行
    HYBRID = "hybrid"  # 混合执行


@dataclass
class Intent:
    """用户意图"""
    intent_type: IntentType
    primary_goal: str
    sub_goals: list[str] = field(default_factory=list)
    entities: dict[str, Any] = field(default_factory=dict)
    confidence: float = 0.0
    context: dict[str, Any] = field(default_factory=dict)


@dataclass
class ResourceRequirement:
    """资源需求"""
    agents: list[str] = field(default_factory=list)  # 需要的智能体
    services: list[str] = field(default_factory=list)  # 需要的服务
    databases: list[str] = field(default_factory=list)  # 需要的数据库
    estimated_time: int = 0  # 预估时间(秒)
    memory_mb: int = 0  # 预估内存使用(MB)


@dataclass
class Risk:
    """风险"""
    type: str
    description: str
    probability: float  # 发生概率 0-1
    impact: str  # 影响程度: low/medium/high
    mitigation: str = ""  # 缓解措施


@dataclass
class ExecutionStep:
    """执行步骤"""
    id: str
    description: str
    agent: str
    action: str
    parameters: dict[str, Any] = field(default_factory=dict)
    dependencies: list[str] = field(default_factory=list)
    estimated_time: int = 0
    required_resources: list[str] = field(default_factory=list)
    fallback_strategy: Optional[str] = None


@dataclass
class ExecutionPlan:
    """执行方案"""
    plan_id: str
    intent: Intent
    steps: list[ExecutionStep]
    mode: ExecutionMode = ExecutionMode.SEQUENTIAL
    resource_requirements: ResourceRequirement = field(default_factory=ResourceRequirement)
    risks: list[Risk] = field(default_factory=list)
    confidence: PlanConfidence = PlanConfidence.MEDIUM
    estimated_time: int = 0
    created_at: datetime = field(default_factory=datetime.now)
    metadata: dict[str, Any] = field(default_factory=dict)


# ========== 核心规划器 ==========


class XiaonuoPlannerEngine:
    """
    小诺智能规划引擎

    核心功能:
    1. 意图理解与分析
    2. 方案生成与优化
    3. 资源评估与分配
    4. 风险识别与缓解
    """

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.planning_history: list[ExecutionPlan] = []

        # 初始化子系统
        from .intent_analyzer import IntentAnalyzer
        from .task_decomposer import TaskDecomposer

        self.intent_analyzer = IntentAnalyzer()
        self.task_decomposer = TaskDecomposer()

        # Phase 2: 智能规划增强模块
        try:
            from .cost_evaluator import CostEvaluator
            from .multi_plan_generator import MultiPlanGenerator
            from .plan_selector import PlanSelector
            from .risk_predictor import RiskPredictor

            self.multi_plan_generator = MultiPlanGenerator()
            self.cost_evaluator = CostEvaluator()
            self.risk_predictor = RiskPredictor()
            self.plan_selector = PlanSelector()
            self.phase2_enabled = True
            self.logger.info("   ✅ Phase 2 智能规划模块加载成功")
        except ImportError as e:
            self.phase2_enabled = False
            self.logger.warning(f"   ⚠️ Phase 2 模块未加载: {e}")

        # Phase 3: 学习优化系统模块
        try:
            from .feedback_collector import FeedbackCollector
            from .plan_evaluator import PlanEvaluator
            from .planning_knowledge_base import PlanningKnowledgeBase
            from .strategy_optimizer import StrategyOptimizer

            self.feedback_collector = FeedbackCollector()
            self.plan_evaluator = PlanEvaluator()
            self.strategy_optimizer = StrategyOptimizer()
            self.knowledge_base = PlanningKnowledgeBase()
            self.phase3_enabled = True
            self.logger.info("   ✅ Phase 3 学习优化模块加载成功")
        except ImportError as e:
            self.phase3_enabled = False
            self.logger.warning(f"   ⚠️ Phase 3 模块未加载: {e}")

        # 智能体能力配置
        self.agent_capabilities = self._load_agent_capabilities()

        # 平台资源状态
        self.platform_resources = self._get_platform_resources()

        self.logger.info("💝 小诺智能规划引擎初始化完成")

    def _load_agent_capabilities(self) -> dict[str, dict[str, Any]]:
        """加载智能体能力配置"""
        return {
            "xiaona": {
                "name": "小娜·天秤女神",
                "specialties": ["专利检索", "法律分析", "文档处理", "智能对话"],
                "max_concurrent": 2,
                "avg_response_time": 3.0,
                "success_rate": 0.95,
            },
            "xiaonuo": {
                "name": "小诺·双鱼座",
                "specialties": ["任务协调", "数据分析", "系统优化", "技术诊断"],
                "max_concurrent": 3,
                "avg_response_time": 1.5,
                "success_rate": 0.98,
            },
        }

    def _get_platform_resources(self) -> dict[str, Any]:
        """获取平台资源状态"""
        return {
            "total_agents": 2,
            "active_agents": 2,
            "database_status": {
                "athena_db": "healthy",
                "patent_db": "healthy",
                "vector_db": "healthy",
            },
            "cache_status": "healthy",
            "memory_usage": "45%",
            "cpu_usage": "30%",
        }

    async def plan(
        self,
        user_input: str,
        context: Optional[dict[str, Any]] = None
    ) -> ExecutionPlan:
        """
        生成执行规划

        Args:
            user_input: 用户输入
            context: 上下文信息

        Returns:
            ExecutionPlan: 执行方案
        """
        self.logger.info(f"🎯 开始规划: {user_input[:50]}...")

        # 1. 意图分析
        intent = await self.intent_analyzer.analyze(user_input, context or {})
        self.logger.info(
            f"   📊 意图识别: {intent.intent_type.value} "
            f"(置信度: {intent.confidence:.2f})"
        )

        # 2. 任务分解
        steps = await self.task_decomposer.decompose(intent, context or {})
        self.logger.info(f"   📋 任务分解: {len(steps)} 个步骤")

        # 3. 资源评估
        resource_req = self._evaluate_resources(steps, intent)

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
                "planner_version": "1.0.0",
                "platform_status": self.platform_resources,
            }
        )

        # 7. 保存历史
        self.planning_history.append(plan)

        self.logger.info(f"   ✅ 方案生成完成: {plan.plan_id} (置信度: {plan.confidence.value})")
        return plan

    async def plan_with_options(
        self,
        user_input: str,
        context: Optional[dict[str, Any]] = None,
        strategies: Optional[list] = None,
        selection_criteria: Optional[str] = None,
        user_preferences: Optional[dict[str, Any]] = None
    ) -> dict[str, Any]:
        """
        智能多方案规划（Phase 2增强功能）

        生成多个可行方案，基于成本/风险/时间对比选择最优方案

        Args:
            user_input: 用户输入
            context: 上下文信息
            strategies: 要生成的策略列表 (默认: [FAST, RELIABLE, BALANCED])
            selection_criteria: 选择标准 (fastest/most_reliable/lowest_cost/balanced)
            user_preferences: 用户偏好配置

        Returns:
            Dict: 包含选定方案和所有方案的对比信息
        """
        self.logger.info(f"🎯 开始智能多方案规划: {user_input[:50]}...")

        # 检查Phase 2是否启用
        if not self.phase2_enabled:
            self.logger.warning("   ⚠️ Phase 2 模块未启用，回退到标准规划")
            plan = await self.plan(user_input, context)
            return {
                "selected_plan": plan,
                "mode": "standard",
                "all_variants": [],
                "comparison": [],
            }

        # 1. 意图分析
        intent = await self.intent_analyzer.analyze(user_input, context or {})
        self.logger.info(
            f"   📊 意图识别: {intent.intent_type.value} "
            f"(置信度: {intent.confidence:.2f})"
        )

        # 2. 生成多个方案变体
        from .multi_plan_generator import PlanStrategy
        if strategies is None:
            strategies = [PlanStrategy.FAST, PlanStrategy.RELIABLE, PlanStrategy.BALANCED]

        variants = await self.multi_plan_generator.generate(intent, context or {}, strategies)
        self.logger.info(f"   📋 生成 {len(variants)} 个方案变体")

        # 3. 成本评估
        all_plans = [v.plan for v in variants]
        cost_comparisons = self.cost_evaluator.compare_plans(all_plans)
        self.logger.info("   💰 成本评估完成")

        # 4. 风险预测
        risk_assessments = []
        for plan in all_plans:
            assessment = self.risk_predictor.predict(plan, context)
            risk_assessments.append(assessment)
        self.logger.info("   ⚠️ 风险预测完成")

        # 5. 方案选择
        from .plan_selector import SelectionCriteria
        if selection_criteria:
            criteria = SelectionCriteria(selection_criteria)
        else:
            criteria = SelectionCriteria.BALANCED

        selection_result = await self.plan_selector.select(
            variants, cost_comparisons, risk_assessments, criteria, user_preferences
        )

        # 6. 保存选定的方案到历史
        self.planning_history.append(selection_result.selected_plan)

        # 7. 构建返回结果
        result = {
            "selected_plan": selection_result.selected_plan,
            "strategy": selection_result.strategy.value,
            "reason": selection_result.reason,
            "confidence": selection_result.confidence,
            "mode": "intelligent_multi_plan",
            "all_variants": [
                {
                    "strategy": v.strategy.value,
                    "plan_id": v.plan.plan_id,
                    "score": v.score,
                    "advantages": v.advantages,
                    "disadvantages": v.disadvantages,
                    "estimated_time": v.plan.estimated_time,
                    "steps_count": len(v.plan.steps),
                    "confidence": v.plan.confidence.value,
                }
                for v in variants
            ],
            "comparison": [
                {
                    **comp,
                    "cost_breakdown": {
                        "time_cost": cb.breakdown.time_cost,
                        "compute_cost": cb.breakdown.compute_cost,
                        "resource_cost": cb.breakdown.resource_cost,
                        "total_cost": cb.breakdown.total_cost,
                        "rank": cb.rank,
                    }
                }
                for comp, cb in zip(selection_result.comparison, cost_comparisons, strict=False)
            ],
            "risk_summary": [
                {
                    "plan_id": ra.plan_id,
                    "overall_risk": ra.overall_risk.value,
                    "overall_score": ra.overall_score,
                    "risk_count": len(ra.risks),
                    "mitigation_count": len(ra.mitigation_suggestions),
                }
                for ra in risk_assessments
            ],
        }

        self.logger.info(
            f"   ✅ 智能方案选择完成: {selection_result.strategy.value} - "
            f"{selection_result.reason}"
        )

        return result

    def _evaluate_resources(
        self,
        steps: list[ExecutionStep],
        intent: Intent
    ) -> ResourceRequirement:
        """评估资源需求"""
        required_agents = list({s.agent for s in steps})
        required_services = []
        required_databases = []

        # 分析每个步骤的资源需求
        for step in steps:
            required_services.extend(step.required_resources)

            # 根据意图类型推断数据库需求
            if intent.intent_type == IntentType.QUERY:
                required_databases.append("athena_db")
            elif "专利" in str(intent.context):
                required_databases.extend(["patent_db", "vector_db"])

        # 去重
        required_services = list(set(required_services))
        required_databases = list(set(required_databases))

        # 估算时间和内存
        total_time = sum(s.estimated_time for s in steps)
        memory_mb = len(steps) * 50  # 每个步骤预估50MB

        return ResourceRequirement(
            agents=required_agents,
            services=required_services,
            databases=required_databases,
            estimated_time=total_time,
            memory_mb=memory_mb
        )

    def _assess_risks(
        self,
        steps: list[ExecutionStep],
        intent: Intent,
        resources: ResourceRequirement
    ) -> list[Risk]:
        """评估风险"""
        risks = []

        # 时间风险
        if resources.estimated_time > 300:  # 超过5分钟
            risks.append(Risk(
                type="time",
                description="执行时间过长可能导致用户等待",
                probability=0.7,
                impact="medium",
                mitigation="考虑异步执行或分批返回结果"
            ))

        # 资源冲突风险
        agent_usage = {}
        for step in steps:
            agent_usage[step.agent] = agent_usage.get(step.agent, 0) + 1

        for agent, count in agent_usage.items():
            if count > self.agent_capabilities[agent]["max_concurrent"]:
                risks.append(Risk(
                    type="resource",
                    description=f"{agent} 智能体可能过载",
                    probability=0.6,
                    impact="high",
                    mitigation=f"限制{agent}并发数或使用任务队列"
                ))

        # 依赖风险
        dependency_count = sum(len(s.dependencies) for s in steps)
        if dependency_count > len(steps) * 1.5:  # 依赖过多
            risks.append(Risk(
                type="dependency",
                description="任务依赖关系复杂，可能影响执行效率",
                probability=0.5,
                impact="medium",
                mitigation="尝试并行化部分任务或简化依赖关系"
            ))

        # 置信度风险
        if intent.confidence < 0.6:
            risks.append(Risk(
                type="understanding",
                description="用户意图理解不够明确",
                probability=intent.confidence,
                impact="medium",
                mitigation="增加澄清环节或提供多方案选择"
            ))

        return risks

    def _select_execution_mode(
        self,
        steps: list[ExecutionStep],
        intent: Intent
    ) -> ExecutionMode:
        """选择执行模式"""
        # 检查步骤之间的依赖关系
        has_dependencies = any(step.dependencies for step in steps)

        if not has_dependencies:
            # 无依赖关系，可以并行执行
            return ExecutionMode.PARALLEL
        elif len(steps) <= 3:
            # 步骤较少，使用顺序执行
            return ExecutionMode.SEQUENTIAL
        else:
            # 复杂场景，使用混合模式
            return ExecutionMode.HYBRID

    def _calculate_confidence(
        self,
        intent: Intent,
        steps: list[ExecutionStep],
        risks: list[Risk]
    ) -> PlanConfidence:
        """计算方案置信度"""
        # 基础置信度来自意图识别
        base_confidence = intent.confidence

        # 风险调整
        risk_penalty = sum(r.probability for r in risks) * 0.1
        final_confidence = max(0, min(1, base_confidence - risk_penalty))

        if final_confidence >= 0.8:
            return PlanConfidence.HIGH
        elif final_confidence >= 0.5:
            return PlanConfidence.MEDIUM
        else:
            return PlanConfidence.LOW

    def get_planning_stats(self) -> dict[str, Any]:
        """获取规划统计信息"""
        if not self.planning_history:
            return {"total_plans": 0}

        intent_distribution = {}
        for plan in self.planning_history:
            intent_type = plan.intent.intent_type.value
            intent_distribution[intent_type] = intent_distribution.get(intent_type, 0) + 1

        return {
            "total_plans": len(self.planning_history),
            "intent_distribution": intent_distribution,
            "average_confidence": sum(
                0.9 if p.confidence == PlanConfidence.HIGH else
                0.65 if p.confidence == PlanConfidence.MEDIUM else 0.25
                for p in self.planning_history
            ) / len(self.planning_history),
            "average_steps": (
                sum(len(p.steps) for p in self.planning_history) /
                len(self.planning_history)
            ),
        }

    # ========== Phase 3: 学习优化方法 ==========

    async def collect_feedback(
        self,
        plan: ExecutionPlan,
        feedback_type: str,
        satisfaction: Optional[str] = None,
        execution_time: Optional[int] = None,
        success_rate: Optional[float] = None,
        user_comments: Optional[str] = None,
    ) -> dict[str, Any]:
        """收集方案执行反馈（Phase 3）"""
        if not self.phase3_enabled:
            self.logger.warning("Phase 3 未启用，反馈收集功能不可用")
            return {"status": "disabled"}

        from .feedback_collector import FeedbackType, SatisfactionLevel

        feedback = self.feedback_collector.collect(
            plan=plan,
            feedback_type=FeedbackType(feedback_type),
            satisfaction=SatisfactionLevel(satisfaction) if satisfaction else None,
            execution_time=execution_time,
            success_rate=success_rate,
            user_comments=user_comments,
        )

        # 自动提取经验教训并存储到知识库
        if feedback.feedback_type == FeedbackType.EXECUTION_FAILURE:
            lessons = [
                f"失败原因: {', '.join(feedback.error_messages)}",
                f"需要改进的步骤: {', '.join(feedback.failed_steps)}",
            ]
        elif feedback.feedback_type == FeedbackType.EXECUTION_SUCCESS:
            lessons = ["执行成功，保持当前策略"]
        else:
            lessons = ["部分成功，需要优化"]

        return {
            "status": "success",
            "feedback_id": feedback.feedback_id,
            "lessons_learned": lessons,
        }

    async def evaluate_plan(
        self,
        plan: ExecutionPlan,
        actual_execution_time: Optional[int] = None,
    ) -> dict[str, Any]:
        """评估方案执行效果（Phase 3）"""
        if not self.phase3_enabled:
            self.logger.warning("Phase 3 未启用，评估功能不可用")
            return {"status": "disabled"}

        # 获取该方案的反馈
        feedback_list = self.feedback_collector.get_feedback_for_plan(plan.plan_id)

        # 执行评估
        evaluation = self.plan_evaluator.evaluate(
            plan=plan,
            feedback=feedback_list,
            actual_execution_time=actual_execution_time,
        )

        # 将案例添加到知识库
        lessons = self.knowledge_base.extract_lessons_from_evaluation(evaluation, plan)
        self.knowledge_base.add_case(
            intent=plan.intent,
            user_input=plan.intent.primary_goal,
            strategy=PlanStrategy(plan.mode.value),
            plan=plan,
            evaluation=evaluation,
            lessons_learned=lessons,
        )

        return {
            "status": "success",
            "evaluation_id": evaluation.evaluation_id,
            "overall_score": evaluation.overall_score,
            "grade": evaluation.grade,
            "strengths": evaluation.strengths,
            "weaknesses": evaluation.weaknesses,
            "optimization_opportunities": evaluation.optimization_opportunities,
        }

    def optimize_strategies(self) -> dict[str, Any]:
        """优化规划策略（Phase 3）"""
        if not self.phase3_enabled:
            self.logger.warning("Phase 3 未启用，优化功能不可用")
            return {"status": "disabled"}

        # 获取所有评估和反馈
        evaluations = self.plan_evaluator.evaluation_history
        feedback_list = self.feedback_collector.feedback_history

        if not evaluations and not feedback_list:
            return {"status": "insufficient_data", "message": "需要更多数据才能优化"}

        # 生成优化建议
        recommendations = self.strategy_optimizer.generate_optimization_recommendations(
            evaluations=evaluations,
            feedback_list=feedback_list,
        )

        # 自动应用高置信度的优化
        applied = []
        for rec in recommendations:
            if rec.confidence > 0.7 and rec.priority == "high":
                if self.strategy_optimizer.apply_optimization(rec):
                    applied.append(rec.description)

        return {
            "status": "success",
            "recommendations_count": len(recommendations),
            "applied_count": len(applied),
            "recommendations": [
                {
                    "type": r.optimization_type.value,
                    "description": r.description,
                    "priority": r.priority,
                    "confidence": r.confidence,
                }
                for r in recommendations
            ],
            "applied_optimizations": applied,
            "current_parameters": self.strategy_optimizer.get_current_parameters(),
        }

    def query_knowledge(
        self,
        intent_type: Optional[str] = None,
        strategy: Optional[str] = None,
        tags: Optional[list[str]] = None,
        limit: int = 5,
    ) -> dict[str, Any]:
        """查询规划知识库（Phase 3）"""
        if not self.phase3_enabled:
            self.logger.warning("Phase 3 未启用，知识库功能不可用")
            return {"status": "disabled"}

        from .multi_plan_generator import PlanStrategy

        # 查询相似案例
        similar_cases = self.knowledge_base.query_similar_cases(
            intent_type=IntentType(intent_type) if intent_type else None,
            strategy=PlanStrategy(strategy) if strategy else None,
            tags=tags,
            limit=limit,
        )

        # 获取最佳实践
        best_practices = self.knowledge_base.get_best_practices(
            scenario=intent_type,
            limit=limit,
        )

        return {
            "status": "success",
            "similar_cases": [
                {
                    "case_id": c.case_id,
                    "intent_type": c.intent_type.value,
                    "strategy": c.strategy_used.value,
                    "score": c.evaluation.overall_score if c.evaluation else None,
                    "grade": c.evaluation.grade if c.evaluation else None,
                    "lessons": c.lessons_learned,
                }
                for c in similar_cases
            ],
            "best_practices": [
                {
                    "title": p.title,
                    "description": p.description,
                    "confidence": p.confidence,
                }
                for p in best_practices
            ],
            "statistics": self.knowledge_base.get_statistics(),
        }

    def get_learning_stats(self) -> dict[str, Any]:
        """获取学习和优化统计（Phase 3）"""
        if not self.phase3_enabled:
            return {"status": "disabled"}

        return {
            "feedback_stats": self.feedback_collector.get_stats(),
            "evaluation_stats": self.plan_evaluator.get_evaluation_stats(),
            "optimization_stats": self.strategy_optimizer.get_optimization_stats(),
            "knowledge_base_stats": self.knowledge_base.get_statistics(),
            "phase_enabled": {
                "phase2": self.phase2_enabled,
                "phase3": self.phase3_enabled,
            },
        }


# ========== 便捷函数 ==========


async def create_plan(
    user_input: str,
    context: Optional[dict[str, Any]] = None
) -> ExecutionPlan:
    """便捷函数：创建执行规划"""
    planner = XiaonuoPlannerEngine()
    return await planner.plan(user_input, context)

