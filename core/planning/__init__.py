from __future__ import annotations
"""
planning - 规划引擎模块

提供显式规划能力,按照《智能体设计模式》书中的标准实现:
1. 任务分解为清晰的执行步骤
2. 等待用户确认后执行
3. 支持动态调整
4. 多种可视化方式
5. 任务复杂度分析 (Phase 2)
6. 自适应策略选择 (Phase 2)

主要组件:
- ExplicitPlanner: 显式规划器
- PlanVisualizer: 计划可视化器
- PlanningAPIService: RESTful API服务
- TaskComplexityAnalyzer: 任务复杂度分析器 (Phase 2)
- TaskClassifier: 任务分类器

作者: 小诺·双鱼座
版本: v2.0.0 "Phase 2"
"""

from .adaptive_meta_planner import (
    AdaptiveMetaPlanner,
    PerformanceTracker,
    WorkflowReuseManager,
    get_adaptive_meta_planner,
    plan_adaptive,
)
from .explicit_planner import (
    ExecutionPlan as ExplicitExecutionPlan,
)
from .explicit_planner import (
    ExplicitPlanner,
    PlanStep,
    PlanStepStatus,
    get_explicit_planner,
)
from .models import (
    ComplexityAnalysis,
    ComplexityFactors,
    ComplexityLevel,
    ExecutionPlan,
    PlanningMetrics,
    StrategyType,
    Task,
)
from .rl_optimized_planner import (
    ExperienceReplay,
    QLearningAgent,
    QNetwork,
    RewardFunction,
    RLOptimizedPlanner,
    get_rl_optimized_planner,
    plan_with_rl,
)
from .task_classifier import (
    TaskCategory,
    TaskClassification,
    TaskClassifier,
    TaskDomain,
    classify_task,
)

__all__ = [
    "AdaptiveMetaPlanner",
    "ComplexityAnalysis",
    "ComplexityFactors",
    # 数据模型 (Phase 2)
    "ComplexityLevel",
    "ExecutionPlan",
    "ExperienceReplay",
    # 核心类
    "ExplicitPlanner",
    "PerformanceTracker",
    "PlanStep",
    "PlanStepStatus",
    "PlanVisualizer",
    "PlanningMetrics",
    "QLearningAgent",
    "QNetwork",
    "RLOptimizedPlanner",
    "RewardFunction",
    "StrategyType",
    "Task",
    # TaskClassifier相关
    "TaskCategory",
    "TaskClassification",
    "TaskClassifier",
    "TaskComplexityAnalyzer",
    "TaskDomain",
    "WorkflowReuseManager",
    "analyze_task_complexity",
    "classify_task",
    "get_adaptive_meta_planner",
    # 便捷函数
    "get_explicit_planner",
    "get_plan_visualizer",
    "get_rl_optimized_planner",
    "plan_adaptive",
    "plan_with_rl",
    # API
    "planning_api_app",
    "start_planning_api",
]

__version__ = "2.0.0"
__author__ = "小诺·双鱼座"
