#!/usr/bin/env python3
from __future__ import annotations
"""
高级协调机制
Advanced Coordination Mechanisms

实现智能体间的高级协调功能,包括:
- 动态任务分配
- 自适应负载均衡
- 智能资源调度
- 协作优化
- 性能监控
"""

import asyncio
import heapq
import itertools
import logging
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class CoordinationStrategy(Enum):
    """协调策略枚举"""

    ADAPTIVE = "adaptive"  # 自适应协调
    PREDICTIVE = "predictive"  # 预测性协调
    OPPORTUNISTIC = "opportunistic"  # 机会性协调
    MARKET_BASED = "market_based"  # 基于市场的协调
    HIERARCHICAL = "hierarchical"  # 层次协调
    PEER_TO_PEER = "peer_to_peer"  # 点对点协调


class ResourceType(Enum):
    """资源类型枚举"""

    COMPUTE = "compute"  # 计算资源
    MEMORY = "memory"  # 内存资源
    STORAGE = "storage"  # 存储资源
    NETWORK = "network"  # 网络资源
    DATA = "data"  # 数据资源
    EXTERNAL_API = "external_api"  # 外部API资源


class TaskPriority(Enum):
    """任务优先级"""

    CRITICAL = 4  # 关键任务
    HIGH = 3  # 高优先级
    NORMAL = 2  # 正常优先级
    LOW = 1  # 低优先级


@dataclass
class ResourceRequirement:
    """资源需求"""

    resource_type: ResourceType
    amount: float
    unit: str
    duration: timedelta | None = None
    quality_requirements: dict[str, Any] = field(default_factory=dict)


@dataclass
class TaskSpecification:
    """任务规格"""

    task_id: str
    task_type: str
    priority: TaskPriority
    deadline: datetime | None = None
    estimated_duration: timedelta | None = None
    required_capabilities: list[str] = field(default_factory=list)
    resource_requirements: list[ResourceRequirement] = field(default_factory=list)
    dependencies: list[str] = field(default_factory=list)
    constraints: dict[str, Any] = field(default_factory=dict)
    quality_requirements: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class AgentCapability:
    """智能体能力"""

    capability_name: str
    proficiency: float  # 熟练度 (0.0-1.0)
    availability: float  # 可用性 (0.0-1.0)
    cost_per_hour: float  # 每小时成本
    quality_metrics: dict[str, float] = field(default_factory=dict)
    specializations: list[str] = field(default_factory=list)


@dataclass
class AgentState:
    """智能体状态"""

    agent_id: str
    current_tasks: list[str] = field(default_factory=list)
    available_capabilities: list[AgentCapability] = field(default_factory=list)
    current_load: float = 0.0
    max_load: float = 1.0
    performance_metrics: dict[str, float] = field(default_factory=dict)
    resource_usage: dict[str, float] = field(default_factory=dict)
    last_updated: datetime = field(default_factory=datetime.now)


class TaskQueue:
    """优先级任务队列"""

    def __init__(self):
        self.heap = []  # 优先级堆
        self.entry_finder = {}  # 任务ID到堆条目的映射
        self.REMOVED = "<removed-task>"
        self.counter = itertools.count()

    def add_task(self, task_spec: TaskSpecification) -> None:
        """添加任务到队列"""
        # 计算任务优先级分数
        priority_score = self._calculate_priority_score(task_spec)

        # 创建堆条目
        count = next(self.counter)
        entry = [priority_score, count, task_spec]
        self.entry_finder[task_spec.task_id] = entry
        heapq.heappush(self.heap, entry)

    def remove_task(self, task_id: str) -> bool:
        """从队列中移除任务"""
        entry = self.entry_finder.pop(task_id, None)
        if entry:
            entry[-1] = self.REMOVED
            return True
        return False

    def pop_task(self) -> TaskSpecification | None:
        """弹出最高优先级任务"""
        while self.heap:
            _priority_score, _count, task_spec = heapq.heappop(self.heap)
            if task_spec is not self.REMOVED:
                del self.entry_finder[task_spec.task_id]
                return task_spec
        return None

    def peek_task(self) -> TaskSpecification | None:
        """查看最高优先级任务(不弹出)"""
        while self.heap:
            _priority_score, _count, task_spec = self.heap[0]
            if task_spec is self.REMOVED:
                heapq.heappop(self.heap)
            else:
                return task_spec
        return None

    def _calculate_priority_score(self, task_spec: TaskSpecification) -> float:
        """计算任务优先级分数(越高优先级越高)"""
        score = 0.0

        # 基础优先级分数
        score += task_spec.priority.value * 10

        # 截止时间紧迫性
        if task_spec.deadline:
            time_to_deadline = task_spec.deadline - datetime.now()
            urgency = max(0, 1.0 - time_to_deadline.total_seconds() / 3600)  # 1小时为单位
            score += urgency * 20

        # 依赖复杂度(依赖越多优先级越低)
        score -= len(task_spec.dependencies) * 2

        # 资源需求(需求越多优先级越低)
        score -= len(task_spec.resource_requirements) * 1

        return -score  # 使用负数因为heapq是最小堆


class ResourcePool:
    """资源池管理"""

    def __init__(self):
        self.resources: dict[str, dict[str, Any]] = {}
        self.allocations: dict[str, list[dict[str, Any]], defaultdict(
            list
        )  # resource_type -> allocations
        self.reservation_queue: list[dict[str, Any]] = []

    def add_resource(
        self,
        resource_id: str,
        resource_type: ResourceType,
        capacity: float,
        unit: str,
        **properties,
    ) -> None:
        """添加资源"""
        self.resources[resource_id] = {
            "resource_type": resource_type,
            "capacity": capacity,
            "available": capacity,
            "unit": unit,
            "properties": properties,
            "quality_metrics": properties.get("quality_metrics", {}),
        }

    def allocate_resource(
        self, requirement: ResourceRequirement, task_id: str, duration: timedelta | None = None
    ) -> Optional[str]:
        """分配资源"""
        # 寻找合适的资源
        suitable_resources = []
        for resource_id, resource_info in self.resources.items():
            if (
                resource_info["resource_type"] == requirement.resource_type
                and resource_info["available"] >= requirement.amount
            ):

                # 检查质量要求
                if self._check_quality_requirements(
                    resource_info, requirement.quality_requirements
                ):
                    suitable_resources.append((resource_id, resource_info))

        if not suitable_resources:
            # 加入预约队列
            self.reservation_queue.append(
                {
                    "requirement": requirement,
                    "task_id": task_id,
                    "duration": duration,
                    "timestamp": datetime.now(),
                }
            )
            return None

        # 选择最优资源(基于质量、利用率等)
        best_resource_id = self._select_best_resource(suitable_resources, requirement)

        # 分配资源
        resource = self.resources[best_resource_id]
        resource["available"] -= requirement.amount

        # 记录分配
        allocation = {
            "task_id": task_id,
            "amount": requirement.amount,
            "allocated_at": datetime.now(),
            "duration": duration,
            "expires_at": datetime.now() + duration if duration else None,
        }
        self.allocations[best_resource_id].append(allocation)

        return best_resource_id

    def release_resource(self, resource_id: str, task_id: str, amount: float) -> bool:
        """释放资源"""
        if resource_id not in self.resources:
            return False

        # 查找并移除分配记录
        allocation_found = False
        allocations = self.allocations[resource_id]
        for i, allocation in enumerate(allocations):
            if allocation["task_id"] == task_id:
                allocations.pop(i)
                allocation_found = True
                break

        if allocation_found:
            # 恢复资源可用量
            self.resources[resource_id]["available"] += amount

            # 检查预约队列
            self._process_reservation_queue()
            return True

        return False

    def _check_quality_requirements(
        self, resource_info: dict[str, Any], quality_requirements: dict[str, Any]
    ) -> bool:
        """检查质量要求"""
        resource_quality = resource_info.get("quality_metrics", {})

        for metric, requirement in quality_requirements.items():
            if metric in resource_quality:
                if isinstance(requirement, dict):
                    # 范围要求
                    min_val = requirement.get("min", float("-inf"))
                    max_val = requirement.get("max", float("inf"))
                    if not (min_val <= resource_quality[metric] <= max_val):
                        return False
                else:
                    # 精确要求
                    if resource_quality[metric] < requirement:
                        return False

        return True

    def _select_best_resource(
        self, suitable_resources: list[tuple[str, dict[str, Any]], requirement: ResourceRequirement
    ) -> str:
        """选择最优资源"""
        best_resource_id = None
        best_score = float("-inf")

        for resource_id, resource_info in suitable_resources:
            score = 0.0

            # 利用率评分(利用率低的资源得分高)
            utilization_rate = (
                resource_info["capacity"] - resource_info["available"]
            ) / resource_info["capacity"]
            score += (1.0 - utilization_rate) * 10

            # 质量评分
            quality_score = self._calculate_quality_score(
                resource_info, requirement.quality_requirements
            )
            score += quality_score * 5

            if score > best_score:
                best_score = score
                best_resource_id = resource_id

        return best_resource_id

    def _calculate_quality_score(
        self, resource_info: dict[str, Any], quality_requirements: dict[str, Any]
    ) -> float:
        """计算资源质量分数"""
        if not quality_requirements:
            return 1.0

        resource_quality = resource_info.get("quality_metrics", {})
        scores = []

        for metric, requirement in quality_requirements.items():
            if metric in resource_quality:
                resource_value = resource_quality[metric]

                if isinstance(requirement, dict):
                    min_val = requirement.get("min", float("-inf"))
                    max_val = requirement.get("max", float("inf"))

                    # 计算在要求范围内的得分
                    if resource_value < min_val:
                        score = 0.0
                    elif resource_value > max_val:
                        # 超过要求时得分递减
                        excess = resource_value - max_val
                        score = max(0.0, 1.0 - excess / max_val)
                    else:
                        # 在要求范围内
                        score = 1.0
                else:
                    # 精确要求
                    score = 1.0 if resource_value >= requirement else resource_value / requirement

                scores.append(score)

        return sum(scores) / len(scores) if scores else 0.0

    def _process_reservation_queue(self) -> None:
        """处理资源预约队列"""
        if not self.reservation_queue:
            return

        # 按时间排序
        self.reservation_queue.sort(key=lambda x: x["timestamp"])

        processed = []
        for reservation in self.reservation_queue:
            requirement = reservation["requirement"]
            task_id = reservation["task_id"]
            duration = reservation["duration"]

            resource_id = self.allocate_resource(requirement, task_id, duration)
            if resource_id:
                processed.append(reservation)
                logger.info(f"为任务 {task_id} 分配预约资源 {resource_id}")

        # 移除已处理的预约
        for reservation in processed:
            self.reservation_queue.remove(reservation)


class AdvancedCoordinationEngine:
    """高级协调引擎"""

    def __init__(self):
        self.agents: dict[str, AgentState] = {}
        self.task_queue = TaskQueue()
        self.resource_pool = ResourcePool()
        self.coordination_strategy = CoordinationStrategy.ADAPTIVE
        self.task_assignments: dict[str, str] = {}  # task_id -> agent_id
        self.agent_tasks: dict[str, list[str]] = defaultdict(list)  # agent_id -> task_ids
        self.coordination_history: list[dict[str, Any]] = []
        self.performance_metrics: dict[str, float] = defaultdict(float)

    def register_agent(
        self, agent_id: str, capabilities: list[AgentCapability], max_load: float = 1.0
    ) -> bool:
        """注册智能体"""
        try:
            agent_state = AgentState(
                agent_id=agent_id, available_capabilities=capabilities, max_load=max_load
            )
            self.agents[agent_id] = agent_state

            logger.info(f"智能体 {agent_id} 注册成功,能力数量: {len(capabilities)}")
            return True
        except Exception as e:
            logger.error(f"注册智能体失败: {e}")
            return False

    def submit_task(self, task_spec: TaskSpecification) -> bool:
        """提交任务"""
        try:
            self.task_queue.add_task(task_spec)
            logger.info(f"任务 {task_spec.task_id} 已提交到队列")
            return True
        except Exception as e:
            logger.error(f"提交任务失败: {e}")
            return False

    async def coordinate_tasks(self) -> None:
        """协调任务分配"""
        try:
            while True:
                # 获取最高优先级任务
                task_spec = self.task_queue.peek_task()
                if not task_spec:
                    await asyncio.sleep(1)  # 队列为空,等待
                    continue

                # 寻找合适的智能体
                suitable_agents = await self._find_suitable_agents(task_spec)

                if suitable_agents:
                    # 选择最优智能体
                    best_agent_id = await self._select_best_agent(task_spec, suitable_agents)

                    if best_agent_id:
                        # 分配任务
                        success = await self._assign_task(task_spec, best_agent_id)
                        if success:
                            self.task_queue.pop_task()  # 从队列中移除
                            continue

                # 没有合适的智能体,等待
                await asyncio.sleep(5)

        except Exception as e:
            logger.error(f"协调任务失败: {e}")

    async def _find_suitable_agents(self, task_spec: TaskSpecification) -> list[str]:
        """寻找合适的智能体"""
        suitable_agents = []

        for agent_id, agent_state in self.agents.items():
            # 检查能力匹配
            if self._check_capability_match(agent_state, task_spec.required_capabilities):
                # 检查负载容量
                if agent_state.current_load < agent_state.max_load:
                    # 检查资源可用性
                    if await self._check_resource_availability(agent_state, task_spec):
                        suitable_agents.append(agent_id)

        return suitable_agents

    def _check_capability_match(
        self, agent_state: AgentState, required_capabilities: list[str]
    ) -> bool:
        """检查能力匹配"""
        agent_capabilities = {cap.capability_name for cap in agent_state.available_capabilities}
        required_set = set(required_capabilities)

        return required_set.issubset(agent_capabilities)

    async def _check_resource_availability(
        self, agent_state: AgentState, task_spec: TaskSpecification
    ) -> bool:
        """检查资源可用性"""
        for req in task_spec.resource_requirements:
            # 尝试预留资源
            resource_id = self.resource_pool.allocate_resource(
                req, task_spec.task_id, task_spec.estimated_duration
            )
            if not resource_id:
                # 如果无法分配,释放之前预留的资源
                await self._release_reserved_resources(task_spec.task_id)
                return False

        # 成功预留所有资源
        return True

    async def _release_reserved_resources(self, task_id: str) -> None:
        """释放为任务预留的资源"""
        for resource_id, allocations in self.resource_pool.allocations.items():
            for allocation in allocations[:]:  # 使用副本遍历
                if allocation["task_id"] == task_id:
                    # 移除临时分配
                    allocations.remove(allocation)
                    # 恢复资源可用量
                    self.resource_pool.resources[resource_id]["available"] += allocation["amount"]

    async def _select_best_agent(
        self, task_spec: TaskSpecification, suitable_agents: list[str]
    ) -> Optional[str]:
        """选择最优智能体"""
        if self.coordination_strategy == CoordinationStrategy.ADAPTIVE:
            return await self._select_agent_adaptive(task_spec, suitable_agents)
        elif self.coordination_strategy == CoordinationStrategy.PREDICTIVE:
            return await self._select_agent_predictive(task_spec, suitable_agents)
        elif self.coordination_strategy == CoordinationStrategy.MARKET_BASED:
            return await self._select_agent_market_based(task_spec, suitable_agents)
        else:
            return await self._select_agent_adaptive(task_spec, suitable_agents)

    async def _select_agent_adaptive(
        self, task_spec: TaskSpecification, suitable_agents: list[str]
    ) -> Optional[str]:
        """自适应选择智能体"""
        best_agent_id = None
        best_score = float("-inf")

        for agent_id in suitable_agents:
            agent_state = self.agents[agent_id]
            score = 0.0

            # 负载评分
            load_score = 1.0 - (agent_state.current_load / agent_state.max_load)
            score += load_score * 0.3

            # 能力匹配评分
            capability_score = self._calculate_capability_score(agent_state, task_spec)
            score += capability_score * 0.4

            # 历史表现评分
            performance_score = self._calculate_performance_score(agent_id, task_spec.task_type)
            score += performance_score * 0.2

            # 可用性评分
            availability_score = self._calculate_availability_score(agent_state)
            score += availability_score * 0.1

            if score > best_score:
                best_score = score
                best_agent_id = agent_id

        return best_agent_id

    async def _select_agent_predictive(
        self, task_spec: TaskSpecification, suitable_agents: list[str]
    ) -> Optional[str]:
        """预测性选择智能体"""
        # 基于历史数据和机器学习预测最优智能体
        # 这里简化为使用历史表现
        return await self._select_agent_adaptive(task_spec, suitable_agents)

    async def _select_agent_market_based(
        self, task_spec: TaskSpecification, suitable_agents: list[str]
    ) -> Optional[str]:
        """基于市场机制选择智能体"""
        best_agent_id = None
        best_bid = float("inf")

        for agent_id in suitable_agents:
            agent_state = self.agents[agent_id]

            # 计算智能体的出价(成本)
            bid = self._calculate_agent_bid(agent_state, task_spec)

            if bid < best_bid:
                best_bid = bid
                best_agent_id = agent_id

        return best_agent_id

    def _calculate_capability_score(
        self, agent_state: AgentState, task_spec: TaskSpecification
    ) -> float:
        """计算能力匹配分数"""
        total_score = 0.0
        required_count = len(task_spec.required_capabilities)

        for req_cap in task_spec.required_capabilities:
            for cap in agent_state.available_capabilities:
                if cap.capability_name == req_cap:
                    total_score += cap.proficiency
                    break

        return total_score / required_count if required_count > 0 else 0.0

    def _calculate_performance_score(self, agent_id: str, task_type: str) -> float:
        """计算历史表现分数"""
        # 从协调历史中计算平均表现
        related_tasks = [
            record
            for record in self.coordination_history
            if record.get("agent_id") == agent_id and record.get("task_type") == task_type
        ]

        if not related_tasks:
            return 0.5  # 默认分数

        performances = [record.get("performance_score", 0.5) for record in related_tasks]
        return sum(performances) / len(performances)

    def _calculate_availability_score(self, agent_state: AgentState) -> float:
        """计算可用性分数"""
        total_availability = sum(cap.availability for cap in agent_state.available_capabilities)
        return (
            total_availability / len(agent_state.available_capabilities)
            if agent_state.available_capabilities
            else 0.0
        )

    def _calculate_agent_bid(self, agent_state: AgentState, task_spec: TaskSpecification) -> float:
        """计算智能体出价"""
        # 基础成本
        base_cost = sum(cap.cost_per_hour for cap in agent_state.available_capabilities)

        # 负载调整(负载越高,成本越高)
        load_multiplier = 1.0 + agent_state.current_load

        # 紧急任务调整
        if task_spec.priority == TaskPriority.CRITICAL:
            urgency_multiplier = 1.5
        elif task_spec.priority == TaskPriority.HIGH:
            urgency_multiplier = 1.2
        else:
            urgency_multiplier = 1.0

        return base_cost * load_multiplier * urgency_multiplier

    async def _assign_task(self, task_spec: TaskSpecification, agent_id: str) -> bool:
        """分配任务给智能体"""
        try:
            agent_state = self.agents[agent_id]

            # 更新智能体状态
            agent_state.current_tasks.append(task_spec.task_id)
            agent_state.current_load += 1.0 / agent_state.max_load

            # 记录任务分配
            self.task_assignments[task_spec.task_id] = agent_id
            self.agent_tasks[agent_id].append(task_spec.task_id)

            # 分配资源
            for req in task_spec.resource_requirements:
                resource_id = self.resource_pool.allocate_resource(
                    req, task_spec.task_id, task_spec.estimated_duration
                )
                if not resource_id:
                    logger.warning(f"任务 {task_spec.task_id} 资源分配失败")
                    return False

            # 记录协调历史
            coordination_record = {
                "task_id": task_spec.task_id,
                "agent_id": agent_id,
                "task_type": task_spec.task_type,
                "assigned_at": datetime.now(),
                "coordination_strategy": self.coordination_strategy.value,
                "estimated_duration": task_spec.estimated_duration,
            }
            self.coordination_history.append(coordination_record)

            logger.info(f"任务 {task_spec.task_id} 已分配给智能体 {agent_id}")
            return True

        except Exception as e:
            logger.error(f"分配任务失败: {e}")
            return False

    def complete_task(self, task_id: str, agent_id: str, performance_score: float = 1.0) -> bool:
        """完成任务"""
        try:
            # 验证任务分配
            if self.task_assignments.get(task_id) != agent_id:
                logger.warning(f"任务 {task_id} 未分配给智能体 {agent_id}")
                return False

            # 更新智能体状态
            agent_state = self.agents[agent_id]
            if task_id in agent_state.current_tasks:
                agent_state.current_tasks.remove(task_id)
            agent_state.current_load = max(0, agent_state.current_load - 1.0 / agent_state.max_load)

            # 清理任务分配记录
            del self.task_assignments[task_id]
            self.agent_tasks[agent_id].remove(task_id)

            # 释放资源
            for resource_id, allocations in self.resource_pool.allocations.items():
                for allocation in allocations[:]:
                    if allocation["task_id"] == task_id:
                        self.resource_pool.release_resource(
                            resource_id, task_id, allocation["amount"]
                        )

            # 更新协调历史
            for record in self.coordination_history:
                if record.get("task_id") == task_id:
                    record["completed_at"] = datetime.now()
                    record["performance_score"] = performance_score
                    break

            # 更新性能指标
            self._update_performance_metrics(agent_id, performance_score)

            logger.info(f"任务 {task_id} 由智能体 {agent_id} 完成,性能分数: {performance_score}")
            return True

        except Exception as e:
            logger.error(f"完成任务失败: {e}")
            return False

    def _update_performance_metrics(self, agent_id: str, performance_score: float) -> None:
        """更新性能指标"""
        # 使用指数移动平均更新性能指标
        alpha = 0.1  # 平滑因子
        current_avg = self.performance_metrics.get(agent_id, 0.5)
        new_avg = alpha * performance_score + (1 - alpha) * current_avg
        self.performance_metrics[agent_id] = new_avg

    def get_coordination_status(self) -> dict[str, Any]:
        """获取协调状态"""
        return {
            "registered_agents": len(self.agents),
            "active_tasks": len(self.task_assignments),
            "queued_tasks": len(self.task_queue.heap),
            "coordination_strategy": self.coordination_strategy.value,
            "resource_utilization": self._calculate_resource_utilization(),
            "average_agent_load": self._calculate_average_load(),
            "coordination_history_size": len(self.coordination_history),
        }

    def _calculate_resource_utilization(self) -> dict[str, float]:
        """计算资源利用率"""
        utilization = {}
        for resource_id, resource_info in self.resource_pool.resources.items():
            if resource_info["capacity"] > 0:
                used = resource_info["capacity"] - resource_info["available"]
                utilization[resource_id] = used / resource_info["capacity"]
            else:
                utilization[resource_id] = 0.0
        return utilization

    def _calculate_average_load(self) -> float:
        """计算平均负载"""
        if not self.agents:
            return 0.0

        total_load = sum(agent.current_load for agent in self.agents.values())
        return total_load / len(self.agents)

    async def optimize_coordination(self) -> None:
        """优化协调策略"""
        try:
            # 分析当前性能指标
            current_status = self.get_coordination_status()

            # 根据性能调整策略
            if current_status["average_agent_load"] > 0.8:
                # 负载过高,考虑负载均衡策略
                await self._apply_load_balancing()
            elif current_status["average_agent_load"] < 0.3:
                # 负载过低,考虑机会性策略
                self.coordination_strategy = CoordinationStrategy.OPPORTUNISTIC
            else:
                # 使用自适应策略
                self.coordination_strategy = CoordinationStrategy.ADAPTIVE

            logger.info(f"协调策略已更新为: {self.coordination_strategy.value}")

        except Exception as e:
            logger.error(f"优化协调策略失败: {e}")

    async def _apply_load_balancing(self) -> None:
        """应用负载均衡"""
        # 重新分配一些任务以平衡负载
        # 这里可以实现具体的负载均衡逻辑
        pass


# 全局协调引擎实例
coordination_engine = AdvancedCoordinationEngine()


# 便捷函数
def register_agent(
    agent_id: str, capabilities: list[AgentCapability], max_load: float = 1.0
) -> bool:
    """注册智能体的便捷函数"""
    return coordination_engine.register_agent(agent_id, capabilities, max_load)


def submit_task(task_spec: TaskSpecification) -> bool:
    """提交任务的便捷函数"""
    return coordination_engine.submit_task(task_spec)


async def start_coordination() -> None:
    """启动协调引擎的便捷函数"""
    await coordination_engine.coordinate_tasks()


def get_coordination_status() -> dict[str, Any]:
    """获取协调状态的便捷函数"""
    return coordination_engine.get_coordination_status()
