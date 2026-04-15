#!/usr/bin/env python3
"""
Athena平台编排器
Platform Orchestrator for Athena

智能编排和协调整个平台的运行:
1. 服务编排 - 管理所有服务的生命周期
2. 资源调度 - 智能分配计算资源
3. 任务路由 - 将任务路由到最合适的智能体
4. 负载均衡 - 平衡各智能体工作负载
5. 故障恢复 - 自动检测和恢复故障
6. 性能优化 - 持续优化平台性能

作者: Athena平台团队
创建时间: 2025-12-26
版本: v1.0.0 "平台指挥家"
"""

from __future__ import annotations
import logging
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any

import numpy as np

logger = logging.getLogger(__name__)


class ServiceState(Enum):
    """服务状态"""

    STARTING = "starting"  # 启动中
    RUNNING = "running"  # 运行中
    IDLE = "idle"  # 空闲
    BUSY = "busy"  # 忙碌
    DEGRADED = "degraded"  # 降级运行
    STOPPING = "stopping"  # 停止中
    STOPPED = "stopped"  # 已停止
    ERROR = "error"  # 错误状态


class AgentCapability(Enum):
    """智能体能力"""

    PERCEPTION = "perception"  # 感知能力
    COGNITION = "cognition"  # 认知能力
    DECISION = "decision"  # 决策能力
    EXECUTION = "execution"  # 执行能力
    LEARNING = "learning"  # 学习能力
    COMMUNICATION = "communication"  # 通信能力
    REFLECTION = "reflection"  # 反思能力
    MEMORY = "memory"  # 记忆能力
    KNOWLEDGE = "knowledge"  # 知识能力
    TOOLS = "tools"  # 工具能力


class TaskPriority(Enum):
    """任务优先级"""

    CRITICAL = 0  # 关键任务
    HIGH = 1  # 高优先级
    MEDIUM = 2  # 中等优先级
    LOW = 3  # 低优先级
    BACKGROUND = 4  # 后台任务


@dataclass
class AgentInfo:
    """智能体信息"""

    agent_id: str
    agent_name: str
    role: str
    capabilities: list[AgentCapability]
    state: ServiceState = ServiceState.IDLE
    current_load: float = 0.0  # 当前负载 0-1
    performance_score: float = 0.8  # 性能得分 0-1
    last_active: datetime = field(default_factory=datetime.now)
    task_queue_size: int = 0
    avg_response_time: float = 0.0
    error_rate: float = 0.0
    health_score: float = 1.0  # 健康得分 0-1


@dataclass
class ServiceInfo:
    """服务信息"""

    service_id: str
    service_name: str
    service_type: str
    state: ServiceState = ServiceState.STOPPED
    endpoint: str | None = None
    dependencies: list[str] = field(default_factory=list)
    health_check_url: str | None = None
    last_health_check: datetime | None = None
    restart_count: int = 0
    uptime_seconds: float = 0.0


@dataclass
class Task:
    """任务"""

    task_id: str
    task_type: str
    description: str
    required_capabilities: list[AgentCapability]
    priority: TaskPriority = TaskPriority.MEDIUM
    estimated_duration: timedelta = field(default_factory=lambda: timedelta(seconds=60))
    created_at: datetime = field(default_factory=datetime.now)
    deadline: datetime | None = None
    payload: dict[str, Any] = field(default_factory=dict)
    status: str = "pending"
    assigned_agent: str | None = None


@dataclass
class RoutingDecision:
    """路由决策"""

    task_id: str
    selected_agent: str
    confidence: float
    reasoning: str
    alternatives: list[str] = field(default_factory=list)
    estimated_completion: datetime = field(default_factory=datetime.now)


class PlatformOrchestrator:
    """
    平台编排器

    核心职责:
    1. 智能体注册和发现
    2. 服务生命周期管理
    3. 任务智能路由
    4. 负载均衡
    5. 故障检测和恢复
    6. 性能监控和优化
    """

    def __init__(self):
        # 智能体注册表
        self.agents: dict[str, AgentInfo] = {}

        # 服务注册表
        self.services: dict[str, ServiceInfo] = {}

        # 任务队列
        self.task_queue: deque[Task] = deque()
        self.pending_tasks: dict[str, Task] = {}
        self.running_tasks: dict[str, Task] = {}

        # 路由历史(用于学习)
        self.routing_history: deque[RoutingDecision] = deque(maxlen=10000)

        # 性能指标
        self.metrics = {
            "total_tasks_routed": 0,
            "successful_routes": 0,
            "failed_routes": 0,
            "avg_routing_time": 0.0,
            "agent_utilization": {},
            "service_uptime": {},
        }

        # 负载均衡策略
        self.load_balancing_strategy = "adaptive"  # adaptive, round_robin, least_loaded

        # 故障检测
        self.health_check_interval = 30  # 秒
        self.failure_threshold = 3
        self.failure_counts: dict[str, int] = defaultdict(int)

        logger.info("🎼 Athena平台编排器初始化完成")

    async def register_agent(self, agent_info: AgentInfo) -> bool:
        """注册智能体"""
        self.agents[agent_info.agent_id] = agent_info
        self.metrics["agent_utilization"][agent_info.agent_id] = 0.0

        logger.info(f"✅ 智能体已注册: {agent_info.agent_name} ({agent_info.agent_id})")
        logger.info(f"   能力: {[c.value for c in agent_info.capabilities]}")

        return True

    async def unregister_agent(self, agent_id: str) -> bool:
        """注销智能体"""
        if agent_id in self.agents:
            agent_info = self.agents[agent_id]
            logger.info(f"❌ 智能体已注销: {agent_info.agent_name} ({agent_id})")
            del self.agents[agent_id]
            return True
        return False

    async def register_service(self, service_info: ServiceInfo) -> bool:
        """注册服务"""
        self.services[service_info.service_id] = service_info
        logger.info(f"✅ 服务已注册: {service_info.service_name} ({service_info.service_id})")
        return True

    async def submit_task(self, task: Task) -> str:
        """提交任务"""
        self.task_queue.append(task)
        self.pending_tasks[task.task_id] = task
        self.metrics["total_tasks_routed"] += 1

        logger.info(f"📥 任务已提交: {task.description[:50]}... (优先级: {task.priority.name})")

        # 尝试立即路由
        await self._route_pending_tasks()

        return task.task_id

    async def _route_pending_tasks(self):
        """路由待处理的任务"""
        while self.task_queue:
            task = self.task_queue[0]  # 查看但不移除

            # 找到最合适的智能体
            decision = await self._select_agent_for_task(task)

            if decision:
                # 路由成功,从队列移除
                self.task_queue.popleft()
                await self._assign_task_to_agent(task, decision)
            else:
                # 没有可用智能体,等待
                break

    async def _select_agent_for_task(self, task: Task) -> RoutingDecision | None:
        """为任务选择最合适的智能体"""
        candidates = []

        # 筛选具备所需能力的智能体
        for _agent_id, agent_info in self.agents.items():
            # 检查能力匹配
            capabilities_match = all(
                cap in agent_info.capabilities for cap in task.required_capabilities
            )

            if not capabilities_match:
                continue

            # 检查状态
            if agent_info.state not in [ServiceState.IDLE, ServiceState.RUNNING]:
                continue

            # 检查负载
            if agent_info.current_load > 0.9:
                continue

            candidates.append(agent_info)

        if not candidates:
            logger.warning(f"⚠️ 没有找到可用的智能体处理任务: {task.task_id}")
            return None

        # 根据策略选择智能体
        if self.load_balancing_strategy == "adaptive":
            selected_agent = await self._adaptive_select(candidates, task)
        elif self.load_balancing_strategy == "least_loaded":
            selected_agent = min(candidates, key=lambda a: a.current_load)
        else:  # round_robin
            selected_agent = candidates[len(self.routing_history) % len(candidates)]

        # 计算置信度
        confidence = await self._calculate_routing_confidence(selected_agent, task)

        # 生成决策
        decision = RoutingDecision(
            task_id=task.task_id,
            selected_agent=selected_agent.agent_id,
            confidence=confidence,
            reasoning=await self._generate_routing_reasoning(selected_agent, task),
            alternatives=[a.agent_id for a in candidates if a != selected_agent][:3],
            estimated_completion=datetime.now() + task.estimated_duration,
        )

        self.routing_history.append(decision)
        self.metrics["successful_routes"] += 1

        return decision

    async def _adaptive_select(self, candidates: list[AgentInfo], task: Task) -> AgentInfo:
        """自适应选择智能体"""
        # 综合评分
        scored_candidates = []

        for agent in candidates:
            score = await self._calculate_agent_score(agent, task)
            scored_candidates.append((score, agent))

        # 选择得分最高的
        scored_candidates.sort(key=lambda x: x[0], reverse=True)
        return scored_candidates[0][1]

    async def _calculate_agent_score(self, agent: AgentInfo, task: Task) -> float:
        """计算智能体得分"""
        # 多维度评分
        scores = {
            "capability_match": await self._score_capability_match(agent, task),  # 40%
            "availability": 1.0 - agent.current_load,  # 30%
            "performance": agent.performance_score,  # 20%
            "health": agent.health_score,  # 10%
        }

        weights = {"capability_match": 0.4, "availability": 0.3, "performance": 0.2, "health": 0.1}

        total_score = sum(scores[k] * weights[k] for k in scores)
        return total_score

    async def _score_capability_match(self, agent: AgentInfo, task: Task) -> float:
        """评估能力匹配度"""
        required = set(task.required_capabilities)
        available = set(agent.capabilities)

        # 完全匹配
        if required.issubset(available):
            # 额外能力也是优势
            extra_capabilities = len(available - required)
            return min(1.0, 0.8 + extra_capabilities * 0.05)

        # 部分匹配
        overlap = len(required & available)
        match_ratio = overlap / len(required) if required else 0
        return match_ratio

    async def _calculate_routing_confidence(self, agent: AgentInfo, task: Task) -> float:
        """计算路由置信度"""
        # 基于多因素
        factors = {
            "capability_score": await self._score_capability_match(agent, task),
            "load_factor": 1.0 - agent.current_load,
            "performance": agent.performance_score,
            "health": agent.health_score,
            "recent_success": self._get_recent_success_rate(agent.agent_id),
        }

        return np.mean(list(factors.values()))

    async def _generate_routing_reasoning(self, agent: AgentInfo, task: Task) -> str:
        """生成路由决策理由"""
        reasons = [
            f"智能体 {agent.agent_name} 具备所需能力",
            f"当前负载: {agent.current_load:.1%}",
            f"性能得分: {agent.performance_score:.2f}",
            f"健康状态: {agent.health_score:.2f}",
        ]

        return "; ".join(reasons)

    def _get_recent_success_rate(self, agent_id: str) -> float:
        """获取最近的成功率"""
        recent_decisions = [d for d in self.routing_history if d.selected_agent == agent_id][
            -100:
        ]  # 最近100次

        if not recent_decisions:
            return 0.8  # 默认值

        # 简化:假设所有路由都是成功的
        # 实际应该跟踪任务完成情况
        return 0.9

    async def _assign_task_to_agent(self, task: Task, decision: RoutingDecision):
        """将任务分配给智能体"""
        task.assigned_agent = decision.selected_agent
        task.status = "assigned"

        # 从待处理移到运行中
        if task.task_id in self.pending_tasks:
            del self.pending_tasks[task.task_id]
        self.running_tasks[task.task_id] = task

        # 更新智能体负载
        if decision.selected_agent in self.agents:
            agent = self.agents[decision.selected_agent]
            agent.current_load = min(1.0, agent.current_load + 0.1)
            agent.state = ServiceState.BUSY

        logger.info(
            f"🎯 任务已分配: {task.task_id} -> {decision.selected_agent} "
            f"(置信度: {decision.confidence:.2f})"
        )

    async def mark_task_complete(self, task_id: str, success: bool = True):
        """标记任务完成"""
        if task_id not in self.running_tasks:
            logger.warning(f"任务不在运行列表中: {task_id}")
            return

        task = self.running_tasks[task_id]
        task.status = "completed" if success else "failed"
        del self.running_tasks[task_id]

        # 更新智能体负载
        if task.assigned_agent and task.assigned_agent in self.agents:
            agent = self.agents[task.assigned_agent]
            agent.current_load = max(0.0, agent.current_load - 0.1)
            agent.state = ServiceState.IDLE

            # 更新性能得分
            if success:
                agent.performance_score = min(1.0, agent.performance_score + 0.01)
            else:
                agent.performance_score = max(0.0, agent.performance_score - 0.05)

        logger.info(f"✅ 任务完成: {task_id} (成功: {success})")

    async def update_agent_state(
        self, agent_id: str, state: ServiceState, load: float | None = None
    ):
        """更新智能体状态"""
        if agent_id not in self.agents:
            return

        agent = self.agents[agent_id]
        agent.state = state
        agent.last_active = datetime.now()

        if load is not None:
            agent.current_load = load

    async def health_check(self) -> dict[str, Any]:
        """健康检查"""
        health_report = {
            "timestamp": datetime.now().isoformat(),
            "overall_status": "healthy",
            "agents": {},
            "services": {},
            "tasks": {
                "pending": len(self.pending_tasks),
                "running": len(self.running_tasks),
                "queued": len(self.task_queue),
            },
            "alerts": [],
        }

        # 检查智能体健康状态
        for agent_id, agent in self.agents.items():
            agent_health = {
                "state": agent.state.value,
                "load": agent.current_load,
                "performance": agent.performance_score,
                "last_active": agent.last_active.isoformat(),
            }

            # 检测问题智能体
            if agent.health_score < 0.5:
                health_report["alerts"].append(
                    f"⚠️ 智能体 {agent.agent_name} 健康度低: {agent.health_score:.2f}"
                )

            if agent.state == ServiceState.ERROR:
                health_report["alerts"].append(f"🔴 智能体 {agent.agent_name} 处于错误状态")

            health_report["agents"][agent_id] = agent_health

        # 检查服务健康状态
        for service_id, service in self.services.items():
            service_health = {
                "state": service.state.value,
                "uptime": service.uptime_seconds,
                "restart_count": service.restart_count,
            }

            if service.state == ServiceState.ERROR:
                health_report["alerts"].append(f"🔴 服务 {service.service_name} 处于错误状态")

            health_report["services"][service_id] = service_health

        # 整体状态判断
        if health_report["alerts"]:
            health_report["overall_status"] = "degraded"

        return health_report

    async def get_platform_metrics(self) -> dict[str, Any]:
        """获取平台指标"""
        return {
            "timestamp": datetime.now().isoformat(),
            "agents": {
                "total": len(self.agents),
                "idle": sum(1 for a in self.agents.values() if a.state == ServiceState.IDLE),
                "busy": sum(1 for a in self.agents.values() if a.state == ServiceState.BUSY),
                "error": sum(1 for a in self.agents.values() if a.state == ServiceState.ERROR),
                "avg_load": (
                    np.mean([a.current_load for a in self.agents.values()]) if self.agents else 0
                ),
            },
            "services": {
                "total": len(self.services),
                "running": sum(
                    1 for s in self.services.values() if s.state == ServiceState.RUNNING
                ),
                "stopped": sum(
                    1 for s in self.services.values() if s.state == ServiceState.STOPPED
                ),
                "error": sum(1 for s in self.services.values() if s.state == ServiceState.ERROR),
            },
            "tasks": {
                "total_routed": self.metrics["total_tasks_routed"],
                "success_rate": (
                    self.metrics["successful_routes"] / max(self.metrics["total_tasks_routed"], 1)
                ),
                "pending": len(self.task_queue) + len(self.pending_tasks),
                "running": len(self.running_tasks),
            },
            "routing": {
                "strategy": self.load_balancing_strategy,
                "avg_routing_time": self.metrics["avg_routing_time"],
                "recent_decisions": len(self.routing_history),
            },
        }

    async def optimize_performance(self):
        """性能优化"""
        # 分析路由历史,优化策略
        if len(self.routing_history) < 100:
            return

        # 统计各智能体的表现
        agent_performance = defaultdict(lambda: {"count": 0, "avg_confidence": 0.0, "success": 0})

        for decision in self.routing_history:
            agent = decision.selected_agent
            agent_performance[agent]["count"] += 1
            agent_performance[agent]["avg_confidence"] += decision.confidence

        # 生成优化建议
        recommendations = []

        for agent_id, perf in agent_performance.items():
            if perf["count"] > 10:
                avg_conf = perf["avg_confidence"] / perf["count"]
                if avg_conf < 0.6:
                    recommendations.append(
                        f"智能体 {agent_id} 平均置信度较低 ({avg_conf:.2f}),"
                        f"建议检查能力配置或性能"
                    )

        if recommendations:
            logger.info("🔧 性能优化建议:")
            for rec in recommendations:
                logger.info(f"   - {rec}")

        return recommendations


# 导出便捷函数
_platform_orchestrator: PlatformOrchestrator | None = None


def get_platform_orchestrator() -> PlatformOrchestrator:
    """获取平台编排器单例"""
    global _platform_orchestrator
    if _platform_orchestrator is None:
        _platform_orchestrator = PlatformOrchestrator()
    return _platform_orchestrator
