#!/usr/bin/env python3
from __future__ import annotations
"""
统一规划器接口
Unified Planner Interface

建立小诺系统所有规划器的统一接口,
实现模块间的标准化通信和协作。

作者: 小诺·双鱼座
创建时间: 2025-12-17
版本: v1.0.0 "统一接口"
"""

import asyncio
import logging
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class PlannerType(Enum):
    """规划器类型"""

    TASK_PLANNER = "task_planner"
    GOAL_MANAGER = "goal_manager"
    SCHEDULER = "scheduler"
    ORCHESTRATOR = "orchestrator"


class TaskStatus(Enum):
    """任务状态"""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class Priority(Enum):
    """优先级"""

    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4
    URGENT = 5


@dataclass
class PlanningRequest:
    """规划请求"""

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    type: PlannerType = PlannerType.TASK_PLANNER
    title: str = ""
    description: str = ""
    context: dict[str, Any] = field(default_factory=dict)
    requirements: list[str] = field(default_factory=list)
    constraints: list[str] = field(default_factory=list)
    priority: Priority = Priority.MEDIUM
    deadline: datetime | None = None
    assigned_agent: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class PlanningResult:
    """规划结果"""

    request_id: str
    planner_type: PlannerType
    success: bool
    plan_id: str | None = None
    steps: list[dict[str, Any]] = field(default_factory=list)
    timeline: dict[str, Any] | None = None
    resources: list[str] = field(default_factory=list)
    dependencies: list[str] = field(default_factory=list)
    estimated_duration: timedelta | None = None
    confidence_score: float = 0.0
    created_at: datetime = field(default_factory=datetime.now)
    status: TaskStatus = TaskStatus.PENDING
    feedback: str = ""


class BasePlanner(ABC):
    """规划器基类"""

    def __init__(self, name: str, planner_type: PlannerType):
        self.name = name
        self.planner_type = planner_type
        self.active_plans = {}
        self.planning_history = []

    @abstractmethod
    async def create_plan(self, request: PlanningRequest) -> PlanningResult:
        """创建规划"""
        pass

    @abstractmethod
    async def execute_plan(self, plan_id: str) -> bool:
        """执行规划"""
        pass

    @abstractmethod
    async def get_plan_status(self, plan_id: str) -> dict[str, Any]:
        """获取规划状态"""
        pass

    @abstractmethod
    async def update_plan(self, plan_id: str, updates: dict[str, Any]) -> bool:
        """更新规划"""
        pass

    def get_planner_info(self) -> dict[str, Any]:
        """获取规划器信息"""
        return {
            "name": self.name,
            "type": self.planner_type.value,
            "active_plans": len(self.active_plans),
            "total_plans": len(self.planning_history),
        }


class UnifiedPlannerRegistry:
    """统一规划器注册中心"""

    def __init__(self):
        self.planners: dict[PlannerType, BasePlanner] = {}
        self.request_queue = asyncio.Queue()
        self.results_cache = {}
        self.is_running = False

    def register_planner(self, planner: BasePlanner) -> Any:
        """注册规划器"""
        self.planners[planner.planner_type] = planner
        print(f"✅ 注册规划器: {planner.name} ({planner.planner_type.value})")

    def get_planner(self, planner_type: PlannerType) -> BasePlanner | None:
        """获取规划器"""
        return self.planners.get(planner_type)

    async def submit_request(self, request: PlanningRequest) -> PlanningResult:
        """提交规划请求"""
        if request.type not in self.planners:
            return PlanningResult(
                request_id=request.id,
                planner_type=request.type,
                success=False,
                feedback=f"未找到类型为 {request.type.value} 的规划器",
            )

        planner = self.planners[request.type]

        try:
            result = await planner.create_plan(request)
            self.results_cache[request.id] = result
            return result
        except Exception as e:
            logger.error(f"规划执行失败: {e}")
            # 返回失败结果
            return PlanningResult(
                request_id=request.id,
                planner_type=request.type,
                success=False,
                feedback=f"规划执行失败: {e!s}",
            )

    async def get_result(self, request_id: str) -> PlanningResult | None:
        """获取规划结果"""
        return self.results_cache.get(request_id)

    def get_status(self) -> dict[str, Any]:
        """获取注册中心状态"""
        return {
            "registered_planners": len(self.planners),
            "planner_types": [pt.value for pt in self.planners],
            "pending_requests": self.request_queue.qsize(),
            "cached_results": len(self.results_cache),
        }


class PlannerIntegrationBridge:
    """规划器集成桥接"""

    def __init__(self, registry: UnifiedPlannerRegistry):
        self.registry = registry
        self.integration_adapters = {}

    def register_integration_adapter(
        self, source_type: str, target_planner: PlannerType, adapter_func
    ) -> None:
        """注册集成适配器"""
        key = f"{source_type} -> {target_planner.value}"
        self.integration_adapters[key] = adapter_func
        print(f"✅ 注册集成适配器: {key}")

    async def integrate_request(
        self, source_data: dict[str, Any], source_type: str, target_planner: PlannerType
    ) -> PlanningResult:
        """集成请求处理"""
        key = f"{source_type} -> {target_planner.value}"

        if key not in self.integration_adapters:
            return PlanningResult(
                request_id="integration_failed",
                planner_type=target_planner,
                success=False,
                feedback=f"未找到集成适配器: {key}",
            )

        try:
            adapter_func = self.integration_adapters[key]
            planning_request = adapter_func(source_data)
            return await self.registry.submit_request(planning_request)
        except Exception as e:
            return PlanningResult(
                request_id="integration_failed",
                planner_type=target_planner,
                success=False,
                feedback=f"集成处理失败: {e!s}",
            )


class PlannerCoordinator:
    """规划器协调器"""

    def __init__(self, registry: UnifiedPlannerRegistry):
        self.registry = registry
        self.active_coordinations = {}

    async def coordinate_multi_planner_request(
        self, requests: list[PlanningRequest]
    ) -> list[PlanningResult]:
        """协调多规划器请求"""
        results = []

        # 按优先级排序
        sorted_requests = sorted(requests, key=lambda r: r.priority.value, reverse=True)

        # 并行处理请求
        tasks = []
        for request in sorted_requests:
            task = self.registry.submit_request(request)
            tasks.append(task)

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # 处理异常
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                processed_results.append(
                    PlanningResult(
                        request_id=sorted_requests[i].id,
                        planner_type=sorted_requests[i].type,
                        success=False,
                        feedback=f"协调处理异常: {result!s}",
                    )
                )
            else:
                processed_results.append(result)

        return processed_results

    async def create_dependency_chain(
        self, requests: list[PlanningRequest], dependencies: dict[str, list[str]]
    ) -> dict[str, PlanningResult]:
        """创建依赖链"""
        # 构建依赖图
        dependency_graph = self._build_dependency_graph(requests, dependencies)

        # 拓扑排序执行
        execution_order = self._topological_sort(dependency_graph)

        # 按序执行
        results = {}
        for request_id in execution_order:
            request = next(r for r in requests if r.id == request_id)
            result = await self.registry.submit_request(request)
            results[request_id] = result

            # 检查前置依赖是否成功
            if not result.success:
                # 标记后续依赖为失败
                dependent_requests = self._get_dependent_requests(request_id, dependency_graph)
                for dep_id in dependent_requests:
                    results[dep_id] = PlanningResult(
                        request_id=dep_id,
                        planner_type=request.type,
                        success=False,
                        feedback=f"前置依赖 {request_id} 失败",
                    )

        return results

    def _build_dependency_graph(
        self, requests: list[PlanningRequest], dependencies: dict[str, list[str]]
    ) -> dict[str, list[str]]:
        """构建依赖图"""
        graph = {req.id: [] for req in requests}
        for request_id, deps in dependencies.items():
            if request_id in graph:
                graph[request_id] = deps
        return graph

    def _topological_sort(self, graph: dict[str, list[str]]) -> list[str]:
        """拓扑排序"""
        in_degree = dict.fromkeys(graph, 0)
        for node in graph:
            for neighbor in graph[node]:
                if neighbor in in_degree:
                    in_degree[neighbor] += 1

        queue = [node for node in in_degree if in_degree[node] == 0]
        result = []

        while queue:
            node = queue.pop(0)
            result.append(node)

            for neighbor in graph[node]:
                if neighbor in in_degree:
                    in_degree[neighbor] -= 1
                    if in_degree[neighbor] == 0:
                        queue.append(neighbor)

        return result

    def _get_dependent_requests(self, request_id: str, graph: dict[str, list[str]]) -> list[str]:
        """获取依赖当前请求的其他请求"""
        dependents = []
        for node, deps in graph.items():
            if request_id in deps:
                dependents.append(node)
        return dependents


# 全局规划器实例
_global_registry = UnifiedPlannerRegistry()
_global_bridge = PlannerIntegrationBridge(_global_registry)
_global_coordinator = PlannerCoordinator(_global_registry)


def get_planner_registry() -> UnifiedPlannerRegistry:
    """获取全局规划器注册中心"""
    return _global_registry


def get_integration_bridge() -> PlannerIntegrationBridge:
    """获取全局集成桥接器"""
    return _global_bridge


def get_planner_coordinator() -> PlannerCoordinator:
    """获取全局规划器协调器"""
    return _global_coordinator


# 导出主要接口
__all__ = [
    "BasePlanner",
    "PlannerCoordinator",
    "PlannerIntegrationBridge",
    "PlannerType",
    "PlanningRequest",
    "PlanningResult",
    "UnifiedPlannerRegistry",
    "get_integration_bridge",
    "get_planner_coordinator",
    "get_planner_registry",
]
