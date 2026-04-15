#!/usr/bin/env python3
"""
小诺主编排中枢 - 系统级智能编排核心
Xiaonuo Main Orchestrator - System-Level Intelligent Orchestration Core

整合任务分解、资源调度、接口网关,提供完整的编排服务

作者: 小诺·双鱼座
创建时间: 2025-12-14
版本: v1.0.0
"""
from __future__ import annotations
import asyncio
import logging
import time
import uuid
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

import networkx as nx

from .cross_system_gateway import CrossSystemGateway

# 导入子模块
from .xiaonuo_orchestration_hub import (
    AgentCapability,
    AgentInfo,
    DynamicTaskDecomposer,
    ResourceAwareScheduler,
    SubTask,
    Task,
    TaskPriority,
    TaskStatus,
    TaskType,
)


class OrchestrationMode(Enum):
    """编排模式"""

    SEQUENTIAL = "sequential"  # 顺序执行
    PARALLEL = "parallel"  # 并行执行
    PIPELINE = "pipeline"  # 流水线执行
    ADAPTIVE = "adaptive"  # 自适应执行


class ExecutionResult:
    """执行结果"""

    def __init__(self):
        self.success = False
        self.subtask_results: dict[str, Any] = {}
        self.task_result: dict[str, Any] | None = None
        self.execution_time = 0.0
        self.error: str | None = None
        self.metrics: dict[str, Any] = {}


@dataclass
class OrchestrationReport:
    """编排报告"""

    task_id: str
    task_title: str
    orchestration_mode: OrchestrationMode
    start_time: datetime
    end_time: datetime | None = None
    total_subtasks: int = 0
    completed_subtasks: int = 0
    failed_subtasks: int = 0
    execution_time: float = 0.0
    success_rate: float = 0.0
    resource_utilization: dict[str, float] = field(default_factory=dict)
    agent_performance: dict[str, dict[str, Any]] = field(default_factory=dict)
    bottleneck_analysis: list[str] = field(default_factory=list)
    optimization_suggestions: list[str] = field(default_factory=list)


class XiaonuoMainOrchestrator:
    """小诺主编排中枢"""

    def __init__(self):
        self.name = "小诺·双鱼公主主编排中枢"
        self.version = "1.0.0"

        # 初始化核心组件
        self.task_decomposer = DynamicTaskDecomposer()
        self.resource_scheduler = ResourceAwareScheduler()
        self.gateway = CrossSystemGateway()

        # 执行器
        self.executor = ThreadPoolExecutor(max_workers=10)

        # 任务追踪
        self.active_tasks: dict[str, Task] = {}
        self.task_reports: dict[str, OrchestrationReport] = {}

        # 性能监控
        self.performance_metrics = {
            "total_orchestrations": 0,
            "successful_orchestrations": 0,
            "failed_orchestrations": 0,
            "avg_execution_time": 0.0,
            "total_subtasks": 0,
            "completed_subtasks": 0,
            "agent_utilization": {},
            "system_throughput": 0.0,
        }

        # 配置
        self.config = {
            "default_mode": OrchestrationMode.ADAPTIVE,
            "max_concurrent_tasks": 50,
            "resource_monitor_interval": 5.0,
            "auto_optimization": True,
            "retry_failed_tasks": True,
            "max_retries": 3,
        }

        # 注册智能体
        self._register_default_agents()

        # 日志配置
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(self.name)

        print(f"🎯 {self.name} 初始化完成")

    def _register_default_agents(self) -> Any:
        """注册默认智能体"""
        default_agents = [
            AgentInfo(
                id="patent_search_agent",
                name="专利检索专家",
                capabilities={AgentCapability.PATENT_SEARCH},
                max_concurrent_tasks=3,
                avg_task_duration=300.0,
                resource_pool={"cpu_cores": 2.0, "memory_gb": 4.0},
            ),
            AgentInfo(
                id="patent_writer_agent",
                name="专利撰写专家",
                capabilities={AgentCapability.PATENT_WRITING},
                max_concurrent_tasks=2,
                avg_task_duration=1800.0,
                resource_pool={"cpu_cores": 1.0, "memory_gb": 2.0},
            ),
            AgentInfo(
                id="content_creator_agent",
                name="内容创作专家",
                capabilities={AgentCapability.CONTENT_WRITING},
                max_concurrent_tasks=5,
                avg_task_duration=600.0,
                resource_pool={"cpu_cores": 1.5, "memory_gb": 3.0},
            ),
            AgentInfo(
                id="ai_analyst_agent",
                name="AI分析专家",
                capabilities={AgentCapability.DATA_PROCESSING, AgentCapability.GPU_COMPUTE},
                max_concurrent_tasks=2,
                avg_task_duration=1200.0,
                resource_pool={"cpu_cores": 4.0, "memory_gb": 8.0, "gpu_memory_gb": 8.0},
            ),
            AgentInfo(
                id="legal_expert_agent",
                name="法律专家",
                capabilities={AgentCapability.LEGAL_ANALYSIS},
                max_concurrent_tasks=2,
                avg_task_duration=900.0,
                resource_pool={"cpu_cores": 2.0, "memory_gb": 4.0},
            ),
            AgentInfo(
                id="developer_agent",
                name="开发工程师",
                capabilities={AgentCapability.CODE_DEVELOPMENT},
                max_concurrent_tasks=3,
                avg_task_duration=1800.0,
                resource_pool={"cpu_cores": 2.0, "memory_gb": 4.0},
            ),
        ]

        for agent in default_agents:
            self.resource_scheduler.register_agent(agent)

    async def initialize(self):
        """初始化编排中枢"""
        await self.gateway.initialize()
        self.logger.info("编排中枢初始化完成")

    async def shutdown(self):
        """关闭编排中枢"""
        await self.gateway.close()
        self.executor.shutdown(wait=True)
        self.logger.info("编排中枢已关闭")

    async def orchestrate_task(
        self,
        task_type: TaskType,
        title: str,
        description: str,
        priority: TaskPriority = TaskPriority.NORMAL,
        mode: OrchestrationMode | None = None,
        context: dict[str, Any] | None = None,
    ) -> OrchestrationReport:
        """编排执行任务"""
        # 创建任务
        task = Task(
            id=str(uuid.uuid4()),
            task_type=task_type,
            title=title,
            description=description,
            priority=priority,
        )

        # 设置编排模式
        orchestration_mode = mode or self.config["default_mode"]

        # 创建报告
        report = OrchestrationReport(
            task_id=task.id,
            task_title=title,
            orchestration_mode=orchestration_mode,
            start_time=datetime.now(),
        )

        try:
            self.logger.info(f"开始编排任务: {title}")

            # 1. 任务分解
            self.logger.info("执行任务分解...")
            subtasks = self.task_decomposer.decompose(task)
            report.total_subtasks = len(subtasks)

            # 2. 资源调度
            self.logger.info("执行资源调度...")
            assignments = self.resource_scheduler.assign_tasks(
                subtasks, strategy="resource_optimal"
            )

            # 3. 构建执行图
            self.logger.info("构建执行图...")
            execution_graph = self._build_execution_graph(subtasks)

            # 4. 执行任务
            self.logger.info("开始执行子任务...")
            execution_result = await self._execute_tasks(
                subtasks, assignments, execution_graph, orchestration_mode
            )

            # 5. 整合结果
            self.logger.info("整合执行结果...")
            task.result = self._integrate_results(subtasks, execution_result)
            task.status = TaskStatus.COMPLETED
            task.completed_at = datetime.now()

            # 6. 生成报告
            report = self._generate_report(task, subtasks, assignments, execution_result)

            # 更新指标
            self._update_performance_metrics(report)

            self.logger.info(f"任务编排完成: {title}")

        except Exception as e:
            self.logger.error(f"任务编排失败: {title}, 错误: {e!s}")
            task.status = TaskStatus.FAILED
            task.completed_at = datetime.now()
            report.end_time = datetime.now()
            report.error = str(e)

        finally:
            # 保存任务和报告
            self.active_tasks[task.id] = task
            self.task_reports[task.id] = report

        return report

    def _build_execution_graph(self, subtasks: list[SubTask]) -> nx.DiGraph:
        """构建执行图"""
        graph = nx.DiGraph()

        # 添加节点
        for subtask in subtasks:
            graph.add_node(
                subtask.id,
                subtask=subtask,
                estimated_duration=subtask.resource_requirement.estimated_duration,
            )

        # 添加依赖边
        for subtask in subtasks:
            for dep_id in subtask.dependencies:
                if dep_id in graph:
                    graph.add_edge(dep_id, subtask.id)

        return graph

    async def _execute_tasks(
        self,
        subtasks: list[SubTask],
        assignments: dict[str, str],
        execution_graph: nx.DiGraph,
        mode: OrchestrationMode,
    ) -> ExecutionResult:
        """执行任务"""
        result = ExecutionResult()
        start_time = time.time()

        try:
            if mode == OrchestrationMode.SEQUENTIAL:
                await self._execute_sequential(subtasks, assignments, result)
            elif mode == OrchestrationMode.PARALLEL:
                await self._execute_parallel(subtasks, assignments, result)
            elif mode == OrchestrationMode.PIPELINE:
                await self._execute_pipeline(subtasks, assignments, execution_graph, result)
            else:  # ADAPTIVE
                await self._execute_adaptive(subtasks, assignments, execution_graph, result)

            result.success = True

        except Exception as e:
            result.success = False
            result.error = str(e)
            self.logger.error(f"任务执行失败: {e!s}")

        finally:
            result.execution_time = time.time() - start_time

        return result

    async def _execute_sequential(
        self, subtasks: list[SubTask], assignments: dict[str, str], result: ExecutionResult
    ):
        """顺序执行"""
        for subtask in subtasks:
            subtask_result = await self._execute_subtask(subtask, assignments.get(subtask.id))
            result.subtask_results[subtask.id] = subtask_result

            if not subtask_result.get("success", False):
                raise Exception(f"子任务执行失败: {subtask.title}")

    async def _execute_parallel(
        self, subtasks: list[SubTask], assignments: dict[str, str], result: ExecutionResult
    ):
        """并行执行"""
        tasks = []
        for subtask in subtasks:
            task = self._execute_subtask(subtask, assignments.get(subtask.id))
            tasks.append(task)

        results = await asyncio.gather(*tasks, return_exceptions=True)

        for i, subtask in enumerate(subtasks):
            if isinstance(results[i], Exception):
                result.subtask_results[subtask.id] = False
            else:
                result.subtask_results[subtask.id] = results[i]

    async def _execute_pipeline(
        self,
        subtasks: list[SubTask],
        assignments: dict[str, str],
        execution_graph: nx.DiGraph,
        result: ExecutionResult,
    ):
        """流水线执行"""
        # 拓扑排序
        list(nx.topological_sort(execution_graph))

        # 分层执行
        for level, tasks in enumerate(nx.topological_generations(execution_graph)):
            self.logger.info(f"执行第 {level} 层,包含 {len(tasks)} 个任务")

            # 执行当前层
            current_tasks = []
            for task_id in tasks:
                subtask = next(s for s in subtasks if s.id == task_id)
                task = self._execute_subtask(subtask, assignments.get(task_id))
                current_tasks.append(task)

            layer_results = await asyncio.gather(*current_tasks, return_exceptions=True)

            # 处理结果
            for i, task_id in enumerate(tasks):
                subtask = next(s for s in subtasks if s.id == task_id)
                if isinstance(layer_results[i], Exception):
                    result.subtask_results[task_id] = {
                        "success": False,
                        "error": str(layer_results[i]),
                    }
                else:
                    result.subtask_results[task_id] = layer_results[i]

    async def _execute_adaptive(
        self,
        subtasks: list[SubTask],
        assignments: dict[str, str],
        execution_graph: nx.DiGraph,
        result: ExecutionResult,
    ):
        """自适应执行"""
        # 根据任务数量和依赖关系决定策略
        if len(subtasks) <= 3:
            await self._execute_sequential(subtasks, assignments, result)
        elif execution_graph.number_of_edges() == 0:
            await self._execute_parallel(subtasks, assignments, result)
        else:
            await self._execute_pipeline(subtasks, assignments, execution_graph, result)

    async def _execute_subtask(self, subtask: SubTask, agent_id: str,) -> dict[str, Any]:
        """执行单个子任务"""
        self.logger.info(f"执行子任务: {subtask.title}")

        subtask.status = TaskStatus.RUNNING
        subtask.started_at = datetime.now()

        try:
            if not agent_id:
                raise Exception(f"子任务 {subtask.id} 未分配到智能体")

            # 获取智能体信息
            agent = self.resource_scheduler.agents.get(agent_id)
            if not agent:
                raise Exception(f"智能体 {agent_id} 不存在")

            # 模拟执行(实际实现中会调用智能体的执行接口)
            # 这里可以使用网关调用外部服务
            execution_time = subtask.resource_requirement.estimated_duration * (
                0.8 + 0.4 * (1 - agent.success_rate)
            )

            # 模拟执行时间
            await asyncio.sleep(min(execution_time / 100, 2.0))  # 加速模拟

            # 生成结果
            subtask_result = {
                "success": True,
                "subtask_id": subtask.id,
                "agent_id": agent_id,
                "execution_time": execution_time,
                "result": f"子任务 {subtask.title} 执行完成",
                "output": {
                    "status": "completed",
                    "data": f"Generated data for {subtask.task_type.value}",
                    "quality_score": agent.success_rate,
                },
            }

            # 更新子任务状态
            subtask.status = TaskStatus.COMPLETED
            subtask.completed_at = datetime.now()
            subtask.result = subtask_result

            # 更新智能体状态
            self.resource_scheduler.update_agent_status(agent_id, True)

            return subtask_result

        except Exception as e:
            self.logger.error(f"子任务执行失败: {subtask.title}, 错误: {e!s}")

            subtask.status = TaskStatus.FAILED
            subtask.completed_at = datetime.now()
            subtask.error = str(e)

            # 更新智能体状态
            if agent_id:
                self.resource_scheduler.update_agent_status(agent_id, False)

            return {
                "success": False,
                "subtask_id": subtask.id,
                "agent_id": agent_id,
                "error": str(e),
            }

    def _integrate_results(
        self, subtasks: list[SubTask], execution_result: ExecutionResult
    ) -> dict[str, Any]:
        """整合子任务结果"""
        integrated_result = {
            "task_summary": {
                "total_subtasks": len(subtasks),
                "completed": len([s for s in subtasks if s.status == TaskStatus.COMPLETED]),
                "failed": len([s for s in subtasks if s.status == TaskStatus.FAILED]),
                "success_rate": len([s for s in subtasks if s.status == TaskStatus.COMPLETED])
                / len(subtasks),
            },
            "execution_details": {
                "execution_time": execution_result.execution_time,
                "subtask_results": execution_result.subtask_results,
            },
            "outputs": [],
        }

        # 收集所有子任务的输出
        for subtask in subtasks:
            if subtask.result and subtask.result.get("success"):
                integrated_result["outputs"].append(
                    {
                        "subtask_title": subtask.title,
                        "output": subtask.result.get("output", {}),
                        "agent": subtask.result.get("agent_id"),
                    }
                )

        return integrated_result

    def _generate_report(
        self,
        task: Task,
        subtasks: list[SubTask],
        assignments: dict[str, str],
        execution_result: ExecutionResult,
    ) -> OrchestrationReport:
        """生成编排报告"""
        report = OrchestrationReport(
            task_id=task.id,
            task_title=task.title,
            orchestration_mode=self.config["default_mode"],
            start_time=task.created_at,
            end_time=datetime.now(),
            total_subtasks=len(subtasks),
            completed_subtasks=len([s for s in subtasks if s.status == TaskStatus.COMPLETED]),
            failed_subtasks=len([s for s in subtasks if s.status == TaskStatus.FAILED]),
            execution_time=execution_result.execution_time,
            success_rate=len([s for s in subtasks if s.status == TaskStatus.COMPLETED])
            / len(subtasks),
        )

        # 资源利用率分析
        agent_usage = {}
        for agent_id in set(assignments.values()):
            assigned_tasks = sum(1 for aid in assignments.values() if aid == agent_id)
            agent = self.resource_scheduler.agents.get(agent_id)
            if agent:
                utilization = assigned_tasks / agent.max_concurrent_tasks
                agent_usage[agent_id] = utilization

        report.resource_utilization = agent_usage

        # 智能体性能分析
        for agent_id in set(assignments.values()):
            agent = self.resource_scheduler.agents.get(agent_id)
            if agent:
                report.agent_performance[agent_id] = {
                    "name": agent.name,
                    "assigned_tasks": sum(1 for aid in assignments.values() if aid == agent_id),
                    "success_rate": agent.success_rate,
                    "current_load": agent.current_load,
                }

        # 瓶颈分析
        if execution_result.execution_time > 300:  # 超过5分钟
            report.bottleneck_analysis.append("任务执行时间较长,建议优化或并行执行")

        low_utilization_agents = [aid for aid, util in agent_usage.items() if util < 0.5]
        if low_utilization_agents:
            report.bottleneck_analysis.append(
                f"智能体利用率偏低: {', '.join(low_utilization_agents)}"
            )

        # 优化建议
        if report.success_rate < 0.9:
            report.optimization_suggestions.append("成功率偏低,建议检查任务分配策略")

        if max(agent_usage.values()) > 0.9:
            report.optimization_suggestions.append(
                "部分智能体负载过高,建议增加智能体或优化任务分配"
            )

        return report

    def _update_performance_metrics(self, report: OrchestrationReport) -> Any:
        """更新性能指标"""
        self.performance_metrics["total_orchestrations"] += 1

        if report.success_rate == 1.0:
            self.performance_metrics["successful_orchestrations"] += 1
        else:
            self.performance_metrics["failed_orchestrations"] += 1

        # 更新平均执行时间
        total = self.performance_metrics["total_orchestrations"]
        current_avg = self.performance_metrics["avg_execution_time"]
        self.performance_metrics["avg_execution_time"] = (
            current_avg * (total - 1) + report.execution_time
        ) / total

        # 更新子任务统计
        self.performance_metrics["total_subtasks"] += report.total_subtasks
        self.performance_metrics["completed_subtasks"] += report.completed_subtasks

        # 计算吞吐量(最近1小时)
        now = datetime.now()
        recent_reports = [
            r for r in self.task_reports.values() if (now - r.end_time).total_seconds() < 3600
        ]
        self.performance_metrics["system_throughput"] = len(recent_reports) / 3600.0

    def get_system_status(self) -> dict[str, Any]:
        """获取系统状态"""
        scheduler_status = self.resource_scheduler.get_system_status()
        gateway_metrics = self.gateway.get_metrics()

        return {
            "orchestrator_status": {
                "active_tasks": len(self.active_tasks),
                "completed_tasks": len(self.task_reports),
                "performance_metrics": self.performance_metrics,
            },
            "scheduler_status": scheduler_status,
            "gateway_metrics": gateway_metrics,
        }

    def get_task_report(self, task_id: str) -> OrchestrationReport | None:
        """获取任务报告"""
        return self.task_reports.get(task_id)

    def list_recent_tasks(self, limit: int = 10) -> list[OrchestrationReport]:
        """列出最近的任务"""
        sorted_reports = sorted(
            self.task_reports.values(), key=lambda r: r.start_time, reverse=True
        )
        return sorted_reports[:limit]


# 导出主类
__all__ = ["ExecutionResult", "OrchestrationMode", "OrchestrationReport", "XiaonuoMainOrchestrator"]
