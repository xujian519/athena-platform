#!/usr/bin/env python3
"""
自适应元规划器 - 核心类
Adaptive Meta Planner - Core Class

作者: Athena平台团队
创建时间: 2026-01-20
重构时间: 2026-01-26
版本: 2.0.0
"""

import logging
from datetime import datetime
from typing import Any

from ..exceptions import (
    ConfigurationError,
    PerformanceTrackingError,
    StrategySelectionError,
    TaskExecutionError,
    TaskValidationError,
    WorkflowExecutionError,
)
from ..models import (
    ComplexityAnalysis,
    ComplexityLevel,
    ExecutionPlan,
    StrategyType,
    Task,
)
from ..task_complexity_analyzer import TaskComplexityAnalyzer
from .constants import DEFAULT_SIMILARITY_THRESHOLD
from .performance import PerformanceTracker
from .workflow_reuse import WorkflowReuseManager


logger = logging.getLogger(__name__)


class AdaptiveMetaPlanner:
    """
    自适应元规划器

    根据任务复杂度、历史性能和工作流复用可能性,
    自适应选择最优的规划策略。

    决策流程:
    1. 分析任务复杂度
    2. 检查是否有可复用的工作流 (高置信度优先复用)
    3. 查询历史性能数据
    4. 根据复杂度和历史选择策略
    5. 返回执行计划
    """

    # 策略选择配置
    STRATEGY_SELECTION = {
        ComplexityLevel.SIMPLE: [StrategyType.REACT, StrategyType.PLANNING],
        ComplexityLevel.MEDIUM: [
            StrategyType.PLANNING,
            StrategyType.REACT,
            StrategyType.WORKFLOW_REUSE,
        ],
        ComplexityLevel.COMPLEX: [
            StrategyType.ADAPTIVE,
            StrategyType.WORKFLOW_REUSE,
            StrategyType.PLANNING,
        ],
    }

    def __init__(self):
        """初始化自适应元规划器"""
        self.complexity_analyzer = TaskComplexityAnalyzer()
        self.performance_tracker = PerformanceTracker()
        self.workflow_manager = WorkflowReuseManager()

        # 规划器实例 (懒加载)
        self._planners: dict[StrategyType, Any] = {}

        logger.info("🎯 自适应元规划器初始化完成")

    async def plan(self, task: Task) -> ExecutionPlan:
        """
        为任务生成自适应执行计划

        Args:
            task: 任务对象

        Returns:
            ExecutionPlan: 执行计划

        Raises:
            TaskValidationError: 当任务验证失败时
            StrategySelectionError: 当无法选择策略时
            TaskExecutionError: 当规划失败时
        """
        # 任务验证
        if not task.task_id:
            raise TaskValidationError(message="任务ID不能为空", field="task_id")

        if not task.description:
            raise TaskValidationError(message="任务描述不能为空", field="description")

        logger.info(f"🎯 开始规划: {task.task_id}")
        logger.info(f"   任务描述: {task.description[:100]}...")

        try:
            # 步骤1: 分析任务复杂度
            complexity_analysis = await self.complexity_analyzer.analyze(task)

            logger.info(
                f"📊 复杂度分析: {complexity_analysis.complexity.value} "
                f"(分数: {complexity_analysis.score:.1f}, "
                f"置信度: {complexity_analysis.confidence:.2%})"
            )

            # 保存分析结果到任务
            task.complexity_analysis = complexity_analysis

            # 步骤2: 检查工作流复用
            similar_workflow = await self.workflow_manager.find_similar_workflow(task)

            if (
                similar_workflow
                and similar_workflow.calculate_similarity(task) > DEFAULT_SIMILARITY_THRESHOLD
            ):
                logger.info(f"♻️ 复用工作流: {similar_workflow.name}")
                try:
                    plan = await self.workflow_manager.reuse_workflow(task, similar_workflow)
                    return self._finalize_plan(plan, complexity_analysis, "workflow_reuse")
                except Exception as e:
                    logger.warning(f"⚠️ 工作流复用失败: {e},回退到策略选择")
                    raise WorkflowExecutionError(
                        message=f"工作流复用失败: {e!s}",
                        workflow_id=similar_workflow.pattern_id,
                        cause=e,
                    )

            # 步骤3: 查询历史性能
            best_strategy = self.performance_tracker.get_best_strategy(
                task_type=task.task_type, complexity=complexity_analysis.complexity
            )

            # 步骤4: 选择策略
            try:
                selected_strategy = self._select_strategy(
                    complexity_analysis.complexity, task, best_strategy
                )
            except Exception as e:
                raise StrategySelectionError(
                    message=f"无法为任务选择策略: {e!s}",
                    task_id=task.task_id,
                    available_strategies=list(StrategyType),
                ) from e

            logger.info(f"🎭 选择策略: {selected_strategy.value}")

            # 步骤5: 生成执行计划
            try:
                plan = await self._generate_plan(task, selected_strategy, complexity_analysis)
            except Exception as e:
                raise WorkflowExecutionError(
                    message=f"生成执行计划失败: {e!s}",
                    task_id=task.task_id,
                    cause=e
                )

            # 步骤6: 保存规划指标
            plan.metadata["complexity_analysis"] = complexity_analysis.to_dict()
            plan.metadata["selection_reasoning"] = self._explain_selection(
                complexity_analysis, selected_strategy, best_strategy
            )

            return self._finalize_plan(plan, complexity_analysis, selected_strategy.value)

        except (
            TaskValidationError,
            StrategySelectionError,
            TaskExecutionError,
            WorkflowExecutionError,
        ):
            # 重新抛出我们的自定义异常
            raise
        except Exception as e:
            logger.error(f"❌ 规划过程中发生未知错误: {e}")
            raise TaskExecutionError(message=f"规划失败: {e!s}", task_id=task.task_id, cause=e)

    def _select_strategy(
        self, complexity: ComplexityLevel, task: Task, best_strategy: StrategyType,
    ) -> StrategyType:
        """
        选择执行策略

        选择逻辑:
        1. 如果有历史最佳策略,优先考虑
        2. 否则根据复杂度选择默认策略
        """
        # 有历史最佳策略且性能良好
        if best_strategy:
            perf = self.performance_tracker.get_performance(
                task.task_type, complexity, best_strategy
            )
            if perf and perf.success_rate > 0.85:
                return best_strategy

        # 根据复杂度选择默认策略
        return self.STRATEGY_SELECTION[complexity][0]

    async def _generate_plan(
        self, task: Task, strategy: StrategyType, complexity_analysis: ComplexityAnalysis
    ) -> ExecutionPlan:
        """生成执行计划"""
        # 获取对应的规划器
        self._get_planner(strategy)

        # 生成计划
        if strategy == StrategyType.REACT:
            plan = await self._generate_react_plan(task, complexity_analysis)
        elif strategy == StrategyType.PLANNING:
            plan = await self._generate_planning_plan(task, complexity_analysis)
        elif strategy == StrategyType.WORKFLOW_REUSE:
            plan = await self._generate_workflow_reuse_plan(task, complexity_analysis)
        else:  # ADAPTIVE
            plan = await self._generate_adaptive_plan(task, complexity_analysis)

        plan.strategy = strategy
        return plan

    def _get_planner(self, strategy: StrategyType) -> Any:
        """获取规划器实例"""
        if strategy not in self._planners:
            # TODO: 实际实现应该返回对应的规划器实例
            # 这里先创建空对象占位
            self._planners["key"] = None

        return self._planners[strategy]

    async def _generate_react_plan(
        self, task: Task, complexity: ComplexityAnalysis
    ) -> ExecutionPlan:
        """生成ReAct策略的执行计划"""
        plan = ExecutionPlan(
            task_id=task.task_id, strategy=StrategyType.REACT, confidence=complexity.confidence
        )

        # ReAct策略通常不需要预先规划步骤
        # 这里可以添加一些初始化步骤
        plan.metadata["planning_mode"] = "reactive"
        plan.metadata["check_interval"] = 10

        return plan

    async def _generate_planning_plan(
        self, task: Task, complexity: ComplexityAnalysis
    ) -> ExecutionPlan:
        """生成Planning策略的执行计划"""
        plan = ExecutionPlan(
            task_id=task.task_id, strategy=StrategyType.PLANNING, confidence=complexity.confidence
        )

        # Planning策略需要预先规划步骤
        estimated_steps = complexity.factors.estimated_steps

        # 生成模拟步骤
        for i in range(estimated_steps):
            step = {
                "step_number": i + 1,
                "name": f"步骤{i + 1}",
                "description": f"执行第{i + 1}个操作",
                "status": "pending",
            }
            plan.steps.append(step)

        plan.metadata["planning_mode"] = "explicit_planning"

        return plan

    async def _generate_workflow_reuse_plan(
        self, task: Task, complexity: ComplexityAnalysis
    ) -> ExecutionPlan:
        """生成WorkflowReuse策略的执行计划"""
        plan = ExecutionPlan(
            task_id=task.task_id,
            strategy=StrategyType.WORKFLOW_REUSE,
            confidence=complexity.confidence * 0.9,  # 复用工作流置信度略高
        )

        plan.metadata["planning_mode"] = "workflow_reuse"

        return plan

    async def _generate_adaptive_plan(
        self, task: Task, complexity: ComplexityAnalysis
    ) -> ExecutionPlan:
        """生成Adaptive策略的执行计划"""
        plan = ExecutionPlan(
            task_id=task.task_id, strategy=StrategyType.ADAPTIVE, confidence=complexity.confidence
        )

        # Adaptive策略会在执行过程中动态调整
        plan.metadata["planning_mode"] = "adaptive"
        plan.metadata["adjust_interval"] = 3  # 每3步检查一次

        return plan

    def _explain_selection(
        self,
        complexity: ComplexityAnalysis,
        selected: StrategyType,
        best_from_history: StrategyType,
    ) -> str:
        """解释策略选择"""
        reasons = [
            f"复杂度: {complexity.complexity.value} (分数: {complexity.score:.1f})",
            f"置信度: {complexity.confidence:.2%}",
        ]

        if best_from_history:
            reasons.append(f"历史最佳策略: {best_from_history.value}")

        reasons.append(f"选择策略: {selected.value}")

        return " | ".join(reasons)

    def _finalize_plan(
        self, plan: ExecutionPlan, complexity: ComplexityAnalysis, strategy_source: str
    ) -> ExecutionPlan:
        """完成并返回执行计划"""
        plan.metadata["strategy_source"] = strategy_source
        plan.metadata["planning_timestamp"] = datetime.now().isoformat()

        # 预估执行时间
        plan.estimated_duration = self._estimate_duration(complexity, plan.strategy)

        logger.info(
            f"✅ 规划完成: {plan.plan_id} | "
            f"策略: {plan.strategy.value} | "
            f"置信度: {plan.confidence:.2%} | "
            f"预估耗时: {plan.estimated_duration}s"
        )

        return plan

    def _estimate_duration(self, complexity: ComplexityAnalysis, strategy: StrategyType) -> int:
        """预估执行时间(秒)"""
        base_duration = 30  # 基础时间30秒

        # 根据复杂度调整
        if complexity.complexity == ComplexityLevel.SIMPLE:
            multiplier = 1.0
        elif complexity.complexity == ComplexityLevel.MEDIUM:
            multiplier = 2.0
        else:
            multiplier = 4.0

        # 根据策略调整
        if strategy == StrategyType.REACT:
            strategy_multiplier = 1.0
        elif strategy == StrategyType.PLANNING:
            strategy_multiplier = 0.8  # 规划后执行更快
        elif strategy == StrategyType.WORKFLOW_REUSE:
            strategy_multiplier = 0.5  # 复用最快
        else:  # ADAPTIVE
            strategy_multiplier = 1.2  # 动态调整有开销

        estimated = base_duration * multiplier * strategy_multiplier

        return int(estimated)

    async def record_performance(
        self,
        task: Task,
        plan: ExecutionPlan,
        success: bool,
        execution_time: float,
        quality_score: float,
    ) -> None:
        """
        记录执行性能

        Args:
            task: 任务对象
            plan: 执行计划
            success: 是否成功
            execution_time: 执行时间(秒)
            quality_score: 质量分数 (0-1)

        Raises:
            PerformanceTrackingError: 当性能记录失败时
        """
        try:
            # 获取复杂度分析
            complexity_analysis = plan.metadata.get("complexity_analysis", {})
            complexity_str = complexity_analysis.get("complexity", "medium")

            # 转换字符串为ComplexityLevel枚举
            try:
                complexity = ComplexityLevel(complexity_str)
            except (ValueError, KeyError):
                complexity = ComplexityLevel.MEDIUM

            # 验证参数
            if execution_time < 0:
                raise ValueError("执行时间不能为负数")

            if not 0 <= quality_score <= 1:
                raise ValueError("质量分数必须在0-1之间")

            self.performance_tracker.record_performance(
                task_type=task.task_type,
                complexity=complexity,
                strategy=plan.strategy,
                success=success,
                execution_time=execution_time,
                quality_score=quality_score,
            )

            logger.info(
                f"📊 性能记录: {plan.strategy.value} | "
                f"{'✅' if success else '❌'} | "
                f"耗时: {execution_time:.2f}s | "
                f"质量: {quality_score:.2f}"
            )

        except ValueError as e:
            raise PerformanceTrackingError(
                message=f"性能参数验证失败: {e!s}", metric_name="performance_record"
            )
        except Exception as e:
            raise PerformanceTrackingError(
                message=f"记录性能失败: {e!s}",
                metric_name="performance_record",
                operation="record_performance",
            )

    def get_statistics(self) -> dict[str, Any]:
        """获取统计信息"""
        perf_stats = self.performance_tracker.get_statistics()

        return {
            "performance_tracker": perf_stats,
            "available_strategies": [s.value for s in StrategyType],
            "complexity_levels": [s.value for s in ComplexityLevel],
        }


# ============================================================================
# 便捷函数
# ============================================================================

# 全局单例
_adaptive_planner: AdaptiveMetaPlanner | None = None


def get_adaptive_meta_planner() -> AdaptiveMetaPlanner:
    """获取全局自适应元规划器单例"""
    global _adaptive_planner
    if _adaptive_planner is None:
        _adaptive_planner = AdaptiveMetaPlanner()
    return _adaptive_planner


async def plan_adaptive(task: Task) -> ExecutionPlan:
    """
    便捷的自适应规划函数

    Args:
        task: 任务对象

    Returns:
        ExecutionPlan: 执行计划

    Example:
        >>> from core.planning.models import Task
        >>> result = await plan_adaptive(
        ...     Task(description="分析专利的新颖性")
        ... )
        >>> print(result.strategy)
        StrategyType.PLANNING
    """
    planner = get_adaptive_meta_planner()
    return await planner.plan(task)
