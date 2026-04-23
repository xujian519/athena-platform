from __future__ import annotations
# pyright: ignore
# !/usr/bin/env python3
"""
智能体任务规划器 (Planning Pattern)
基于《智能体设计》规划模式的实现

应用场景:
- 小诺: 复杂分析任务的系统化执行
- 小娜: 专利检索流程优化
- 云熙: IP管理流程自动化
- 小宸: 运营任务规划

实施优先级: ⭐⭐⭐⭐⭐ (最高)
预期收益: 显著提升智能体执行效率和质量
"""

import asyncio
import logging
import sys
import time
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

# 导入性能监控
from planning.planning_monitor import monitor

logger = logging.getLogger(__name__)


class TaskStatus(Enum):
    """任务状态"""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TaskPriority(Enum):
    """任务优先级"""

    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4


@dataclass
class TaskStep:
    """任务步骤"""

    id: str
    description: str
    agent: str  # 负责执行的智能体
    dependencies: list[str] = field(default_factory=list)  # 依赖的步骤ID
    estimated_time: int = 0  # 预估执行时间(秒)
    required_resources: list[str] = field(default_factory=list)
    success_criteria: dict[str, Any] = field(default_factory=dict)
    failure_recovery: dict[str, Any] = field(default_factory=dict)


@dataclass
class ExecutionPlan:
    """执行计划"""

    goal: str
    context: dict[str, Any]
    steps: list[TaskStep]
    id: str = field(
        default_factory=lambda: f"plan_{int(time.time())}_{hash(str(time.time())) % 10000}"
    )
    estimated_total_time: int = 0
    created_at: datetime = field(default_factory=datetime.now)
    status: TaskStatus = TaskStatus.PENDING


class AgenticTaskPlanner:
    """智能体任务规划器"""

    def __init__(self):
        self.planning_history = []
        self.agent_capabilities = self._initialize_agent_capabilities()
        self.execution_templates = self._load_execution_templates()
        self.performance_analytics = PerformanceAnalytics()

    def _initialize_agent_capabilities(self) -> dict[str, dict[str, Any]]:
        """初始化智能体能力配置"""
        return {
            "xiaonuo": {
                "name": "小诺·双鱼座",
                "specialties": ["数据分析", "系统优化", "技术诊断", "代码生成"],
                "max_concurrent_tasks": 3,
                "preferred_task_types": ["analysis", "optimization", "technical"],
            },
            "xiaona": {
                "name": "小娜·天秤女神",
                "specialties": ["专利检索", "法律分析", "文档处理", "智能对话"],
                "max_concurrent_tasks": 2,
                "preferred_task_types": ["research", "analysis", "legal"],
            },
            "xiaochen": {
                "name": "小宸·运营星",
                "specialties": ["运营策略", "用户分析", "内容生成", "市场调研"],
                "max_concurrent_tasks": 4,
                "preferred_task_types": ["strategy", "content", "analysis"],
            },
        }

    def _load_execution_templates(self) -> dict[str, list[TaskStep]]:
        """加载执行模板"""
        return {
            "patent_retrieval": [
                TaskStep(
                    id="search_strategy",
                    description="制定专利检索策略",
                    agent="xiaona",
                    estimated_time=30,
                    success_criteria={"strategy_defined": True},
                ),
                TaskStep(
                    id="database_search",
                    description="执行数据库检索",
                    agent="xiaona",
                    dependencies=["search_strategy"],
                    estimated_time=60,
                    required_resources=["patent_database", "search_api"],
                    success_criteria={"results_count": "> 0"},
                ),
                TaskStep(
                    id="result_analysis",
                    description="分析检索结果",
                    agent="xiaona",
                    dependencies=["database_search"],
                    estimated_time=45,
                    success_criteria={"analysis_complete": True},
                ),
                TaskStep(
                    id="report_generation",
                    description="生成检索报告",
                    agent="xiaona",
                    dependencies=["result_analysis"],
                    estimated_time=30,
                    success_criteria={"report_generated": True},
                ),
            ],
            "system_optimization": [
                TaskStep(
                    id="performance_analysis",
                    description="系统性能分析",
                    agent="xiaonuo",
                    estimated_time=120,
                    required_resources=["monitoring_tools", "performance_data"],
                    success_criteria={"bottlenecks_identified": True},
                ),
                TaskStep(
                    id="optimization_strategy",
                    description="制定优化策略",
                    agent="xiaonuo",
                    dependencies=["performance_analysis"],
                    estimated_time=60,
                    success_criteria={"strategy_defined": True},
                ),
                TaskStep(
                    id="implementation",
                    description="实施优化方案",
                    agent="xiaonuo",
                    dependencies=["optimization_strategy"],
                    estimated_time=300,
                    required_resources=["development_tools", "test_environment"],
                    success_criteria={"optimization_applied": True},
                ),
                TaskStep(
                    id="verification",
                    description="验证优化效果",
                    agent="xiaonuo",
                    dependencies=["implementation"],
                    estimated_time=180,
                    success_criteria={"improvement_measured": True},
                ),
            ],
        }

    def plan_task(self, context: dict[str, Any]) -> ExecutionPlan:
        """
        规划任务执行计划(统一接口方法)

        Args:
            context: 包含任务信息的上下文字典
                - goal: 任务目标
                - task_type: 任务类型(可选)
                - priority: 优先级(可选)
                - deadline: 截止时间(可选)
                - requirements: 特殊要求(可选)

        Returns:
            ExecutionPlan: 执行计划对象
        """
        # 从上下文中提取目标
        goal = context.get("goal", "未定义目标")

        # 如果没有明确的目标,尝试从其他字段构建
        if goal == "未定义目标":
            if "task_type" in context:
                goal = f"执行{context['task_type']}任务"
            elif "title" in context:
                goal = context["title"]
            elif "description" in context:
                goal = context["description"]

        print(f"🎯 小诺规划器: 开始规划任务 - {goal}")

        # 确保任务优先级
        if "priority" not in context:
            context["priority"] = TaskPriority.MEDIUM

            # 开始性能监控计时
            timer_id = (
                monitor.start_planning_timer("AgenticTaskPlanner", f"plan_{int(time.time())}")
                if monitor
                else None
            )

        try:
            # 创建执行计划
            plan = self.create_execution_plan(goal, context)

            # 记录规划历史
            self.planning_history.append(
                {
                    "timestamp": datetime.now(),
                    "goal": goal,
                    "plan_id": plan.id,
                    "steps_count": len(plan.steps),
                    "estimated_time": plan.estimated_total_time,
                }
            )

            # 更新性能分析
            # 结束性能监控计时
            duration = monitor.end_planning_timer(
                timer_id, "AgenticTaskPlanner", plan.id, success=True
            )

            print(
                f"✅ 任务规划完成: {len(plan.steps)}个步骤, 预计{plan.estimated_total_time}秒 (耗时: {duration:.2f}s)"
            )

            return plan

        except Exception as e:
            monitor.end_planning_timer(
                timer_id, "AgenticTaskPlanner", "unknown", success=False, error=str(e)
            )
            logger.error(f"操作失败: {e}", exc_info=True)
            raise

    def create_execution_plan(self, goal: str, context: dict[str, Any]) -> ExecutionPlan:
        """创建执行计划"""
        print(f"🎯 为目标创建执行计划: {goal}")

        # 1. 目标分析和类型识别
        goal_analysis = self._analyze_goal(goal, context)
        print(f"   📊 目标类型: {goal_analysis['type']}")

        # 2. 选择执行模板
        template = self._select_template(goal_analysis)
        if template:
            print(f"   📋 使用模板: {template}")
            steps = self._adapt_template(template, goal, context)
        else:
            print("   🛠️ 自定义规划")
            steps = self._create_custom_steps(goal, goal_analysis, context)

        # 3. 优化执行顺序
        optimized_steps = self._optimize_execution_order(steps)
        print(f"   🔄 步骤优化: {len(optimized_steps)} 个步骤")

        # 4. 资源分配和风险评估
        resource_plan = self._allocate_resources(optimized_steps)
        risk_assessment = self._assess_risks(optimized_steps, context)

        # 5. 时间估算
        total_time = self._estimate_execution_time(optimized_steps)

        # 6. 创建执行计划
        plan = ExecutionPlan(
            goal=goal,
            context={
                **context,
                "goal_analysis": goal_analysis,
                "resource_plan": resource_plan,
                "risk_assessment": risk_assessment,
            },
            steps=optimized_steps,
            estimated_total_time=total_time,
        )

        # 7. 保存规划历史
        self.planning_history.append(
            {
                "timestamp": datetime.now(),
                "goal": goal,
                "plan_id": f"plan_{len(self.planning_history) + 1}",
                "steps_count": len(optimized_steps),
                "estimated_time": total_time,
            }
        )

        print(f"   ✅ 执行计划创建完成: {total_time} 秒, {len(optimized_steps)} 个步骤")
        return plan

    def _analyze_goal(self, goal: str, context: dict[str, Any]) -> dict[str, Any]:
        """分析目标"""
        goal_lower = goal.lower()

        # 目标类型识别
        if any(keyword in goal_lower for keyword in ["专利", "patent", "检索", "search"]):
            return {"type": "patent_retrieval", "complexity": "medium"}
        elif any(keyword in goal_lower for keyword in ["优化", "optimize", "改进", "improve"]):
            return {"type": "system_optimization", "complexity": "high"}
        elif any(keyword in goal_lower for keyword in ["分析", "analysis", "诊断", "diagnose"]):
            return {"type": "data_analysis", "complexity": "medium"}
        elif any(keyword in goal_lower for keyword in ["管理", "manage", "组织", "organize"]):
            return {"type": "project_management", "complexity": "low"}
        elif any(keyword in goal_lower for keyword in ["生成", "generate", "创建", "create"]):
            return {"type": "content_generation", "complexity": "medium"}
        else:
            return {"type": "general_task", "complexity": "medium"}

    def _select_template(self, goal_analysis: dict[str, Any]) -> str | None:
        """选择执行模板"""
        goal_type = goal_analysis["type"]
        return self.execution_templates.get(goal_type)

    def _adapt_template(
        self, template: list[TaskStep] | str, goal: str, context: dict[str, Any]
    ) -> list[TaskStep]:
        """适配模板"""
        # 如果template是字符串（模板名称），则查找模板
        if isinstance(template, str):
            if template not in self.execution_templates:
                return []
            template_steps = self.execution_templates[template]
        # 如果template是列表（直接传入的模板步骤）
        elif isinstance(template, list):
            template_steps = template
        else:
            return []

        adapted_steps = []

        for i, step in enumerate(template_steps):
            adapted_step = TaskStep(
                id=f"{step.id}_{int(time.time())}_{i}",
                description=step.description,
                agent=step.agent,
                dependencies=step.dependencies.copy(),
                estimated_time=step.estimated_time,
                required_resources=step.required_resources.copy(),
                success_criteria=step.success_criteria.copy(),
                failure_recovery=step.failure_recovery.copy(),
            )
            adapted_steps.append(adapted_step)

        return adapted_steps

    def _create_custom_steps(
        self, goal: str, goal_analysis: dict[str, Any], context: dict[str, Any]
    ) -> list[TaskStep]:
        """创建自定义步骤"""
        steps = []

        # 基于目标分析生成步骤
        if goal_analysis["type"] == "general_task":
            steps = [
                TaskStep(
                    id="task_analysis",
                    description="分析任务需求",
                    agent="xiaonuo",
                    estimated_time=30,
                    success_criteria={"requirements_defined": True},
                ),
                TaskStep(
                    id="execution",
                    description="执行任务",
                    agent=self._select_best_agent_for_task(goal),
                    dependencies=["task_analysis"],
                    estimated_time=180,
                    success_criteria={"task_completed": True},
                ),
                TaskStep(
                    id="validation",
                    description="验证执行结果",
                    agent="xiaonuo",
                    dependencies=["execution"],
                    estimated_time=30,
                    success_criteria={"validation_passed": True},
                ),
            ]

        return steps

    def _optimize_execution_order(self, steps: list[TaskStep]) -> list[TaskStep]:
        """优化执行顺序"""
        # 简单的拓扑排序,确保依赖关系正确
        optimized = []
        remaining = steps.copy()

        while remaining:
            # 找出没有未满足依赖的步骤
            ready_steps = [
                step
                for step in remaining
                if all(dep in [s.id for s in optimized] for dep in step.dependencies)
            ]

            if not ready_steps:
                # 如果没有就绪的步骤,说明存在循环依赖,按优先级选择
                ready_steps = [min(remaining, key=lambda x: x.estimated_time)]

            # 选择优先级最高的就绪步骤
            next_step = max(
                ready_steps,
                key=lambda x: (
                    self.agent_capabilities[x.agent]["max_concurrent_tasks"],
                    -x.estimated_time,  # 时间短的优先
                ),
            )

            optimized.append(next_step)
            remaining.remove(next_step)

        return optimized

    def _allocate_resources(self, steps: list[TaskStep]) -> dict[str, Any]:
        """分配资源"""
        resource_allocation = {"agent_utilization": {}, "timeline": [], "resource_conflicts": []}

        # 计算每个智能体的利用率
        for agent in self.agent_capabilities:
            agent_steps = [s for s in steps if s.agent == agent]
            utilization = len(agent_steps) / self.agent_capabilities[agent]["max_concurrent_tasks"]
            resource_allocation["agent_utilization"][agent] = {  # type: ignore
                "steps_count": len(agent_steps),
                "max_concurrent": self.agent_capabilities[agent]["max_concurrent_tasks"],
                "utilization_rate": min(utilization, 1.0),
            }

        return resource_allocation

    def _assess_risks(self, steps: list[TaskStep], context: dict[str, Any]) -> dict[str, Any]:
        """评估风险"""
        risks = {
            "time_risks": [],
            "resource_risks": [],
            "dependency_risks": [],
            "complexity_risks": [],
        }

        total_time = sum(s.estimated_time for s in steps)
        if total_time > 3600:  # 超过1小时
            risks["time_risks"].append(
                {"risk": "执行时间过长", "impact": "high", "mitigation": "考虑并行执行或任务分解"}
            )

        # 检查资源冲突
        agent_usage = {}
        for step in steps:
            if step.agent not in agent_usage:
                agent_usage[step.agent] = 0
            agent_usage[step.agent] += 1

        for agent, usage in agent_usage.items():
            max_concurrent = self.agent_capabilities[agent]["max_concurrent_tasks"]
            if usage > max_concurrent:
                risks["resource_risks"].append(
                    {
                        "risk": f"{agent} 智能体过载",
                        "impact": "medium",
                        "mitigation": "重新分配任务或增加并行度",
                    }
                )

        return risks

    def _estimate_execution_time(self, steps: list[TaskStep]) -> int:
        """估算执行时间"""
        # 考虑并行执行的可能性
        parallel_groups = self._group_parallel_steps(steps)

        total_time = 0
        for group in parallel_groups:
            group_time = max(step.estimated_time for step in group)
            total_time += group_time

        return total_time

    def _group_parallel_steps(self, steps: list[TaskStep]) -> list[list[TaskStep]]:
        """将步骤分组为可以并行执行的组"""
        groups = []
        remaining = steps.copy()

        while remaining:
            # 找出可以并行执行的步骤
            current_group = []
            for step in remaining[:]:  # 创建副本以避免修改原列表
                # 检查是否与当前组中的步骤有依赖关系
                can_parallel = True
                for group_step in current_group:
                    if step.id in group_step.dependencies or group_step.id in step.dependencies:
                        can_parallel = False
                        break

                if can_parallel:
                    current_group.append(step)
                    remaining.remove(step)

            if current_group:
                groups.append(current_group)
            elif remaining:
                # 如果没有可以并行的,取第一个作为单独组
                groups.append([remaining.pop(0)])

        return groups

    def _select_best_agent_for_task(self, goal: str) -> str:
        """为任务选择最佳智能体"""
        goal_lower = goal.lower()

        agent_scores = {}
        for agent, capabilities in self.agent_capabilities.items():
            score = 0
            for specialty in capabilities["specialties"]:
                for keyword in specialty.lower().split():
                    if keyword in goal_lower:
                        score += 1
            agent_scores[agent] = score

        # 选择得分最高的智能体
        best_agent = max(agent_scores, key=agent_scores.get) if agent_scores else "xiaonuo"  # type: ignore
        return best_agent

    async def execute_plan(self, plan: ExecutionPlan) -> dict[str, Any]:
        """执行计划"""
        print(f"🚀 开始执行计划: {plan.goal}")

        execution_results = {
            "plan_id": f"execution_{int(time.time())}",
            "start_time": datetime.now(),
            "steps_completed": 0,
            "steps_failed": 0,
            "actual_time": 0,
            "success": False,
            "results": {},
            "errors": [],
        }

        try:
            for step in plan.steps:
                print(f"   📋 执行步骤: {step.description} ({step.agent})")

                time.time()

            execution_results["actual_time"] = (
                datetime.now() - execution_results.get("start_time")
            ).total_seconds()
            execution_results["success"] = execution_results["steps_failed"] == 0
            execution_results["end_time"] = datetime.now()

            if execution_results.get("success"):
                plan.status = TaskStatus.COMPLETED
                print("   🎉 计划执行成功!")
            else:
                plan.status = TaskStatus.FAILED
                print(
                    f"   ⚠️ 计划执行部分失败: {execution_results.get('steps_completed')}/{len(plan.steps)} 步骤完成"
                )

        except Exception:
            plan.status = TaskStatus.FAILED

        return execution_results

    async def _execute_step(self, step: TaskStep, context: dict[str, Any]) -> Any:
        """执行单个步骤"""
        # 这里应该调用相应的智能体来执行步骤
        # 模拟执行过程
        await asyncio.sleep(step.estimated_time / 10)  # 加速执行以演示

        # 模拟返回结果
        return {
            "step_id": step.id,
            "agent": step.agent,
            "success": True,
            "message": f"{step.description} 执行完成",
        }

    def _can_continue_after_failure(
        self, failed_step: TaskStep, execution_results: dict[str, Any]
    ) -> bool:
        """判断失败后是否可以继续"""
        # 如果失败步骤是关键步骤,则无法继续
        if "critical" in failed_step.description.lower():
            return False

        # 如果失败率超过50%,则停止执行
        failure_rate = execution_results.get("steps_failed") / (
            execution_results.get("steps_completed") + execution_results.get("steps_failed")  # type: ignore
        )
        return not failure_rate > 0.5

    def get_planning_analytics(self) -> dict[str, Any]:
        """获取规划分析数据"""
        return {
            "total_plans": len(self.planning_history),
            "average_steps_per_plan": (
                sum(p["steps_count"] for p in self.planning_history) / len(self.planning_history)
                if self.planning_history
                else 0
            ),
            "average_estimated_time": (
                sum(p["estimated_time"] for p in self.planning_history) / len(self.planning_history)
                if self.planning_history
                else 0
            ),
            "most_common_goal_types": self._analyze_goal_types(),
            "agent_utilization": self._analyze_agent_utilization(),
        }

    def _analyze_goal_types(self) -> dict[str, int]:
        """分析目标类型分布"""
        goal_types = {}
        for plan in self.planning_history:
            goal_type = plan.get("goal_type", "unknown")
            goal_types[goal_type] = goal_types.get(goal_type, 0) + 1
        return goal_types

    def _analyze_agent_utilization(self) -> dict[str, float]:
        """分析智能体利用率"""
        agent_usage = {}
        for agent in self.agent_capabilities:
            agent_usage[agent] = 0.0  # 这里应该计算实际的利用率

        return agent_usage


class PerformanceAnalytics:
    """性能分析器"""

    def __init__(self):
        self.execution_history = []

    def record_execution(self, plan: ExecutionPlan, results: dict[str, Any]) -> Any:
        """记录执行结果"""
        self.execution_history.append(
            {"timestamp": datetime.now(), "plan": plan, "results": results}
        )

    def get_performance_metrics(self) -> dict[str, Any]:
        """获取性能指标"""
        if not self.execution_history:
            return {}

        # 计算各种性能指标
        total_plans = len(self.execution_history)
        successful_plans = sum(1 for h in self.execution_history if h["results"]["success"])

        return {
            "total_executions": total_plans,
            "success_rate": successful_plans / total_plans,
            "average_execution_time": sum(
                h["results"]["actual_time"] for h in self.execution_history
            )
            / total_plans,
            "most_efficient_agent": self._find_most_efficient_agent(),
        }

    def _find_most_efficient_agent(self) -> str:
        """找到最高效的智能体"""
        # 分析各个智能体的执行效率
        agent_performance = {}
        for history in self.execution_history:
            for step_result in history["results"]["results"].values():
                if step_result.get("success"):
                    agent = step_result.get("agent")
                    if agent not in agent_performance:
                        agent_performance[agent] = []
                    agent_performance[agent].append(step_result.get("execution_time"))

        # 计算平均执行时间
        agent_efficiency = {}
        for agent, times in agent_performance.items():
            agent_efficiency[agent] = sum(times) / len(times)

        # 返回最快速的智能体
        if agent_efficiency:
            return min(agent_efficiency, key=agent_efficiency.get)  # type: ignore

        return "unknown"


# 使用示例
async def main():
    """使用示例"""
    planner = AgenticTaskPlanner()

    # 示例1: 专利检索任务
    plan1 = planner.create_execution_plan(
        goal="检索与AI相关的专利技术",
        context={"user_id": "demo_user", "priority": "high", "deadline": "2024-01-01"},
    )

    print(f"\n📋 计划1: {plan1.goal}")
    print(f"   步骤数: {len(plan1.steps)}")
    print(f"   预估时间: {plan1.estimated_total_time} 秒")

    # 示例2: 系统优化任务
    plan2 = planner.create_execution_plan(
        goal="优化存储系统性能",
        context={"current_performance": "slow", "target_improvement": "50%"},
    )

    print(f"\n📋 计划2: {plan2.goal}")
    print(f"   步骤数: {len(plan2.steps)}")
    print(f"   预估时间: {plan2.estimated_total_time} 秒")

    # 执行示例
    if plan1.steps:
        print("\n🚀 执行计划1...")
        result = await planner.execute_plan(plan1)
        print(f"   执行结果: {'成功' if result.get('success') else '失败'}")
        print(f"   完成步骤: {result.get('steps_completed')}/{len(plan1.steps)}")

    # 获取分析数据
    analytics = planner.get_planning_analytics()
    print("\n📊 规划分析:")
    print(f"   总计划数: {analytics['total_plans']}")
    print(f"   平均步骤数: {analytics['average_steps_per_plan']:.1f}")


# 入口点: @async_main装饰器已添加到main函数
