#!/usr/bin/env python3
from __future__ import annotations
"""
冲突检测与拍卖管理器
Conflict Detection and Auction Manager

使用拍卖算法和Shapley值处理资源冲突,实现公平高效的资源分配

作者: 小诺·双鱼座
创建时间: 2025-12-14
"""

import math
import time
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Any


class ConflictType(Enum):
    """冲突类型"""

    RESOURCE_EXCLUSIVE = "resource_exclusive"  # 独占资源冲突
    CAPACITY_LIMIT = "capacity_limit"  # 容量限制冲突
    TIME_WINDOW = "time_window"  # 时间窗口冲突
    PRIORITY_DEADLOCK = "priority_deadlock"  # 优先级死锁
    DEPENDENCY_CYCLE = "dependency_cycle"  # 依赖循环


class AuctionType(Enum):
    """拍卖类型"""

    FIRST_PRICE_SEALED_BID = "first_price"  # 一级价格密封拍卖
    SECOND_PRICE_SEALED_BID = "second_price"  # 二级价格密封拍卖
    ENGLISH_AUCTION = "english"  # 英式拍卖
    DUTCH_AUCTION = "dutch"  # 荷式拍卖
    VICKREY_AUCTION = "vickrey"  # 维克里拍卖
    COMBINATORIAL_AUCTION = "combinatorial"  # 组合拍卖


@dataclass
class ResourceConflict:
    """资源冲突"""

    conflict_id: str
    resource_id: str
    conflict_type: ConflictType
    competing_tasks: list[str]  # 竞争的任务ID
    time_window: tuple[datetime, datetime]  # 冲突时间窗口
    resource_capacity: float
    total_demand: float
    detected_at: datetime


@dataclass
class Bid:
    """出价"""

    task_id: str
    agent_id: str
    resource_id: str
    bid_amount: float  # 出价金额
    utility_value: float  # 效用值
    urgency_score: float  # 紧急度分数
    budget_constraint: float  # 预算约束
    submission_time: datetime


@dataclass
class AuctionResult:
    """拍卖结果"""

    auction_id: str
    winner_task_id: str
    winner_agent_id: str
    winning_bid: float
    payment_amount: float
    allocation: dict[str, Any]
    total_surplus: float  # 总剩余
    efficiency_score: float  # 效率分数


class ConflictDetector:
    """冲突检测器"""

    def __init__(self):
        self.name = "小诺冲突检测器"
        self.conflict_history: list[ResourceConflict] = []
        self.detection_rules = {
            ConflictType.RESOURCE_EXCLUSIVE: self._detect_exclusive_resource_conflict,
            ConflictType.CAPACITY_LIMIT: self._detect_capacity_conflict,
            ConflictType.TIME_WINDOW: self._detect_time_window_conflict,
            ConflictType.PRIORITY_DEADLOCK: self._detect_priority_deadlock,
            ConflictType.DEPENDENCY_CYCLE: self._detect_dependency_cycle,
        }

    def detect_conflicts(
        self,
        tasks: list[dict[str, Any]],
        resources: dict[str, dict[str, Any]],
        current_time: datetime,
    ) -> list[ResourceConflict]:
        """检测所有类型的冲突"""
        conflicts = []

        for _conflict_type, detection_func in self.detection_rules.items():
            type_conflicts = detection_func(tasks, resources, current_time)
            conflicts.extend(type_conflicts)

        # 记录冲突历史
        self.conflict_history.extend(conflicts)

        return conflicts

    def _detect_exclusive_resource_conflict(
        self,
        tasks: list[dict[str, Any]],
        resources: dict[str, dict[str, Any]],
        current_time: datetime,
    ) -> list[ResourceConflict]:
        """检测独占资源冲突"""
        conflicts = []

        # 查找所有独占资源
        exclusive_resources = {
            rid: r
            for rid, r in resources.items()
            if r.get("type") == "exclusive" or r.get("capacity", 1) == 1
        }

        for resource_id, _resource in exclusive_resources.items():
            # 查找需要该资源的任务
            competing_tasks = []
            for task in tasks:
                if resource_id in task.get("required_resources", []):
                    # 检查时间重叠
                    if self._time_overlap(task, resource_id, tasks):
                        competing_tasks.append(task["id"])

            # 如果有多个任务竞争独占资源,产生冲突
            if len(competing_tasks) > 1:
                conflict = ResourceConflict(
                    conflict_id=f"exclusive_{resource_id}_{int(time.time())}",
                    resource_id=resource_id,
                    conflict_type=ConflictType.RESOURCE_EXCLUSIVE,
                    competing_tasks=competing_tasks,
                    time_window=(current_time, current_time + timedelta(hours=1)),
                    resource_capacity=1.0,
                    total_demand=len(competing_tasks),
                    detected_at=current_time,
                )
                conflicts.append(conflict)

        return conflicts

    def _detect_capacity_conflict(
        self,
        tasks: list[dict[str, Any]],
        resources: dict[str, dict[str, Any]],
        current_time: datetime,
    ) -> list[ResourceConflict]:
        """检测容量限制冲突"""
        conflicts = []

        for resource_id, resource in resources.items():
            capacity = resource.get("capacity", float("inf"))
            if capacity == float("inf"):
                continue

            # 计算总需求
            total_demand = 0
            competing_tasks = []
            for task in tasks:
                if resource_id in task.get("required_resources", []):
                    demand = task.get("resource_demands", {}).get(resource_id, 0)
                    total_demand += demand
                    competing_tasks.append(task["id"])

            if total_demand > capacity:
                conflict = ResourceConflict(
                    conflict_id=f"capacity_{resource_id}_{int(time.time())}",
                    resource_id=resource_id,
                    conflict_type=ConflictType.CAPACITY_LIMIT,
                    competing_tasks=competing_tasks,
                    time_window=(current_time, current_time + timedelta(hours=1)),
                    resource_capacity=capacity,
                    total_demand=total_demand,
                    detected_at=current_time,
                )
                conflicts.append(conflict)

        return conflicts

    def _detect_time_window_conflict(
        self,
        tasks: list[dict[str, Any]],
        resources: dict[str, dict[str, Any]],
        current_time: datetime,
    ) -> list[ResourceConflict]:
        """检测时间窗口冲突"""
        conflicts = []

        # 按资源分组任务
        resource_tasks = defaultdict(list)
        for task in tasks:
            for resource_id in task.get("required_resources", []):
                resource_tasks[resource_id].append(task)

        # 检查每个资源的时间窗口
        for resource_id, r_tasks in resource_tasks.items():
            # 按开始时间排序
            sorted_tasks = sorted(r_tasks, key=lambda t: t.get("start_time", current_time))

            # 检查重叠
            for i in range(len(sorted_tasks)):
                for j in range(i + 1, len(sorted_tasks)):
                    task1 = sorted_tasks[i]
                    task2 = sorted_tasks[j]

                    if self._time_windows_overlap(task1, task2):
                        conflict = ResourceConflict(
                            conflict_id=f"time_{resource_id}_{int(time.time())}",
                            resource_id=resource_id,
                            conflict_type=ConflictType.TIME_WINDOW,
                            competing_tasks=[task1["id"], task2["id"]],
                            time_window=(
                                max(
                                    task1.get("start_time", current_time),
                                    task2.get("start_time", current_time),
                                ),
                                min(
                                    task1.get("end_time", current_time),
                                    task2.get("end_time", current_time),
                                ),
                            ),
                            resource_capacity=resources.get(resource_id, {}).get("capacity", 1),
                            total_demand=2,
                            detected_at=current_time,
                        )
                        conflicts.append(conflict)

        return conflicts

    def _detect_priority_deadlock(
        self,
        tasks: list[dict[str, Any]],
        resources: dict[str, dict[str, Any]],
        current_time: datetime,
    ) -> list[ResourceConflict]:
        """检测优先级死锁"""
        conflicts = []

        # 简化检测:高优先级任务等待低优先级任务释放资源
        resource_holders = defaultdict(list)
        for task in tasks:
            for resource_id in task.get("held_resources", []):
                resource_holders[resource_id].append(task)

        for task in tasks:
            if task.get("priority", 1) >= 3:  # 高优先级任务
                for resource_id in task.get("required_resources", []):
                    if resource_id in resource_holders:
                        # 检查是否有更低优先级的任务持有资源
                        for holder in resource_holders[resource_id]:
                            if holder.get("priority", 1) < task.get("priority", 1):
                                conflict = ResourceConflict(
                                    conflict_id=f"priority_{resource_id}_{int(time.time())}",
                                    resource_id=resource_id,
                                    conflict_type=ConflictType.PRIORITY_DEADLOCK,
                                    competing_tasks=[task["id"], holder["id"]],
                                    time_window=(current_time, current_time + timedelta(hours=1)),
                                    resource_capacity=1,
                                    total_demand=2,
                                    detected_at=current_time,
                                )
                                conflicts.append(conflict)

        return conflicts

    def _detect_dependency_cycle(
        self,
        tasks: list[dict[str, Any]],
        resources: dict[str, dict[str, Any]],
        current_time: datetime,
    ) -> list[ResourceConflict]:
        """检测依赖循环"""
        conflicts = []

        # 构建依赖图
        dependency_graph = defaultdict(list)
        for task in tasks:
            for dep in task.get("dependencies", []):
                dependency_graph[dep].append(task["id"])

        # 使用DFS检测循环
        visited = set()
        rec_stack = set()

        def dfs(node, path) -> None:
            if node in rec_stack:
                # 找到循环
                cycle_start = path.index(node)
                cycle = [*path[cycle_start:], node]
                return cycle
            if node in visited:
                return None

            visited.add(node)
            rec_stack.add(node)
            path.append(node)

            for neighbor in dependency_graph[node]:
                result = dfs(neighbor, path.copy())
                if result:
                    return result

            rec_stack.remove(node)
            return None

        for task in tasks:
            cycle = dfs(task["id"], [])
            if cycle:
                conflict = ResourceConflict(
                    conflict_id=f"cycle_{int(time.time())}",
                    resource_id="dependency",
                    conflict_type=ConflictType.DEPENDENCY_CYCLE,
                    competing_tasks=cycle,
                    time_window=(current_time, current_time + timedelta(hours=1)),
                    resource_capacity=1,
                    total_demand=len(cycle),
                    detected_at=current_time,
                )
                conflicts.append(conflict)

        return conflicts

    def _time_overlap(
        self, task: dict[str, Any], resource_id: str, all_tasks: list[dict[str, Any]]) -> bool:
        """检查任务时间重叠"""
        # 简化实现
        return True

    def _time_windows_overlap(self, task1: dict[str, str], task2: dict[str, str]) -> bool:
        """检查两个任务的时间窗口是否重叠"""
        start1 = task1.get("start_time", datetime.now())
        end1 = task1.get("end_time", datetime.now() + timedelta(hours=1))
        start2 = task2.get("start_time", datetime.now())
        end2 = task2.get("end_time", datetime.now() + timedelta(hours=1))

        return not (end1 <= start2 or end2 <= start1)


class AuctionManager:
    """拍卖管理器"""

    def __init__(self):
        self.name = "小诺拍卖管理器"
        self.active_auctions: dict[str, dict[str, Any]] = {}
        self.auction_history: list[dict[str, Any]] = []
        self.shapley_calculator = ShapleyValueCalculator()

    def resolve_conflict_with_auction(
        self,
        conflict: ResourceConflict,
        tasks: list[dict[str, Any]],        agents: list[dict[str, Any]],        auction_type: AuctionType = AuctionType.VICKREY_AUCTION,
    ) -> AuctionResult:
        """使用拍卖解决冲突"""
        auction_id = f"auction_{conflict.conflict_id}"
        print(f"🔨 开始拍卖解决冲突: {conflict.conflict_id}")

        # 收集所有竞争任务的出价
        bids = self._collect_bids(conflict, tasks, agents)

        if not bids:
            # 没有出价,随机分配
            winner_task = conflict.competing_tasks[0]
            return self._create_default_result(auction_id, winner_task, conflict)

        # 执行拍卖
        if auction_type == AuctionType.VICKREY_AUCTION:
            result = self._run_vickrey_auction(auction_id, bids, conflict)
        elif auction_type == AuctionType.COMBINATORIAL_AUCTION:
            result = self._run_combinatorial_auction(auction_id, bids, conflict)
        elif auction_type == AuctionType.ENGLISH_AUCTION:
            result = self._run_english_auction(auction_id, bids, conflict)
        else:
            result = self._run_first_price_auction(auction_id, bids, conflict)

        # 记录拍卖历史
        self.auction_history.append(
            {
                "auction_id": auction_id,
                "conflict": conflict,
                "bids": bids,
                "result": result,
                "timestamp": datetime.now(),
            }
        )

        print(f"✅ 拍卖完成: 获胜者任务 {result.winner_task_id}, 支付 {result.payment_amount}")
        return result

    def calculate_shapley_values(
        self, conflict: ResourceConflict, tasks: list[dict[str, Any]]) -> dict[str, float]:
        """计算Shapley值进行公平分配"""
        return self.shapley_calculator.calculate(conflict, tasks)

    def _collect_bids(
        self, conflict: ResourceConflict, tasks: list[dict[str, Any]], agents: list[dict[str, Any]]) -> list[Bid]:
        """收集出价"""
        bids = []

        for task_id in conflict.competing_tasks:
            task = next((t for t in tasks if t["id"] == task_id), None)
            if not task:
                continue

            for agent in agents:
                if self._can_agent_handle_task(agent, task):
                    # 计算出价
                    bid_amount = self._calculate_bid_amount(task, agent, conflict)
                    utility_value = self._calculate_utility(task, agent, conflict)
                    urgency_score = self._calculate_urgency(task)
                    budget = agent.get("budget", 1000)

                    bid = Bid(
                        task_id=task_id,
                        agent_id=agent["id"],
                        resource_id=conflict.resource_id,
                        bid_amount=bid_amount,
                        utility_value=utility_value,
                        urgency_score=urgency_score,
                        budget_constraint=budget,
                        submission_time=datetime.now(),
                    )
                    bids.append(bid)

        return bids

    def _run_vickrey_auction(
        self, auction_id: str, bids: list[Bid], conflict: ResourceConflict
    ) -> AuctionResult:
        """运行维克里拍卖(二级价格密封拍卖)"""
        # 按出价排序
        sorted_bids = sorted(bids, key=lambda b: b.bid_amount, reverse=True)

        if len(sorted_bids) < 1:
            raise ValueError("没有足够的出价")

        # 获胜者支付第二高价
        winner = sorted_bids[0]
        payment = sorted_bids[1].bid_amount if len(sorted_bids) > 1 else winner.bid_amount

        # 计算总剩余
        total_surplus = sum(bid.utility_value for bid in bids) - payment

        result = AuctionResult(
            auction_id=auction_id,
            winner_task_id=winner.task_id,
            winner_agent_id=winner.agent_id,
            winning_bid=winner.bid_amount,
            payment_amount=payment,
            allocation={
                "resource_id": conflict.resource_id,
                "time_window": conflict.time_window,
                "capacity": conflict.resource_capacity,
            },
            total_surplus=total_surplus,
            efficiency_score=self._calculate_efficiency(sorted_bids, payment),
        )

        return result

    def _run_combinatorial_auction(
        self, auction_id: str, bids: list[Bid], conflict: ResourceConflict
    ) -> AuctionResult:
        """运行组合拍卖"""
        # 简化的组合拍卖:选择总效用最高的组合
        max_utility = 0
        best_combination = None

        # 尝试所有可能的组合(简化版)
        for r in range(1, min(3, len(bids) + 1)):  # 最多3个任务的组合
            from itertools import combinations

            for combo in combinations(bids, r):
                total_utility = sum(bid.utility_value for bid in combo)
                total_payment = sum(bid.bid_amount for bid in combo)

                # 检查资源约束
                if self._check_resource_constraints(combo, conflict):
                    if total_utility > max_utility:
                        max_utility = total_utility
                        best_combination = combo

        if not best_combination:
            # 回退到单任务拍卖
            return self._run_vickrey_auction(auction_id, bids, conflict)

        # 创建结果
        best_combination[0]
        total_payment = sum(bid.bid_amount for bid in best_combination)

        result = AuctionResult(
            auction_id=auction_id,
            winner_task_id="multiple",  # 多个获胜者
            winner_agent_id="multiple",
            winning_bid=sum(bid.bid_amount for bid in best_combination),
            payment_amount=total_payment,
            allocation={
                "resource_id": conflict.resource_id,
                "winners": [bid.task_id for bid in best_combination],
                "split_allocation": True,
            },
            total_surplus=max_utility - total_payment,
            efficiency_score=self._calculate_efficiency(best_combination, total_payment),
        )

        return result

    def _run_english_auction(
        self, auction_id: str, bids: list[Bid], conflict: ResourceConflict
    ) -> AuctionResult:
        """运行英式拍卖"""
        # 模拟英式拍卖过程
        current_price = 0
        current_winner = None
        remaining_bidders = bids.copy()

        while len(remaining_bidders) > 1:
            # 每轮加价
            current_price += 10
            new_bidders = []

            for bid in remaining_bidders:
                if bid.bid_amount >= current_price and bid.budget_constraint >= current_price:
                    new_bidders.append(bid)
                    current_winner = bid

            if len(new_bidders) == len(remaining_bidders):
                # 没有人退出,结束拍卖
                break

            remaining_bidders = new_bidders

        if not current_winner:
            raise ValueError("拍卖失败:没有获胜者")

        result = AuctionResult(
            auction_id=auction_id,
            winner_task_id=current_winner.task_id,
            winner_agent_id=current_winner.agent_id,
            winning_bid=current_winner.bid_amount,
            payment_amount=current_price,
            allocation={
                "resource_id": conflict.resource_id,
                "time_window": conflict.time_window,
                "capacity": conflict.resource_capacity,
            },
            total_surplus=current_winner.utility_value - current_price,
            efficiency_score=self._calculate_efficiency([current_winner], current_price),
        )

        return result

    def _run_first_price_auction(
        self, auction_id: str, bids: list[Bid], conflict: ResourceConflict
    ) -> AuctionResult:
        """运行一级价格密封拍卖"""
        sorted_bids = sorted(bids, key=lambda b: b.bid_amount, reverse=True)
        winner = sorted_bids[0]

        result = AuctionResult(
            auction_id=auction_id,
            winner_task_id=winner.task_id,
            winner_agent_id=winner.agent_id,
            winning_bid=winner.bid_amount,
            payment_amount=winner.bid_amount,
            allocation={
                "resource_id": conflict.resource_id,
                "time_window": conflict.time_window,
                "capacity": conflict.resource_capacity,
            },
            total_surplus=winner.utility_value - winner.bid_amount,
            efficiency_score=self._calculate_efficiency([winner], winner.bid_amount),
        )

        return result

    def _can_agent_handle_task(self, agent: dict[str, str], task: dict[str, str]) -> bool:
        """检查智能体是否能处理任务"""
        task_requirements = task.get("required_capabilities", [])
        agent_capabilities = agent.get("capabilities", [])
        return all(req in agent_capabilities for req in task_requirements)

    def _calculate_bid_amount(
        self, task: dict[str, Any], agent: dict[str, Any], conflict: ResourceConflict
    ) -> float:
        """计算出价金额"""
        base_value = task.get("value_score", 1.0) * 100

        # 根据资源稀缺性调整
        scarcity_multiplier = conflict.total_demand / conflict.resource_capacity

        # 根据紧急度调整
        urgency_multiplier = 1.0 + (task.get("priority", 1) - 1) * 0.5

        # 智能体效率调整
        efficiency = agent.get("success_rate", 0.9)

        bid = base_value * scarcity_multiplier * urgency_multiplier * efficiency
        return min(bid, agent.get("budget", 1000))

    def _calculate_utility(
        self, task: dict[str, Any], agent: dict[str, Any], conflict: ResourceConflict
    ) -> float:
        """计算效用值"""
        task_value = task.get("value_score", 1.0)
        agent_efficiency = agent.get("success_rate", 0.9)
        time_sensitivity = task.get("priority", 1) / 3.0

        return task_value * agent_efficiency * time_sensitivity

    def _calculate_urgency(self, task: dict[str, Any]) -> float:
        """计算紧急度分数"""
        priority = task.get("priority", 1)
        deadline_hours = task.get("deadline_hours", 24)

        # 越接近截止时间,紧急度越高
        time_pressure = max(0, (24 - deadline_hours) / 24)

        return priority * (1 + time_pressure)

    def _check_resource_constraints(self, bids: list[Bid], conflict: ResourceConflict) -> bool:
        """检查资源约束"""
        # 简化检查:确保不超过资源容量
        total_demand = len(bids)
        return total_demand <= conflict.resource_capacity

    def _calculate_efficiency(self, bids: list[Bid], payment: float) -> float:
        """计算效率分数"""
        total_utility = sum(bid.utility_value for bid in bids)
        if payment == 0:
            return 1.0
        return total_utility / payment

    def _create_default_result(
        self, auction_id: str, winner_task: str, conflict: ResourceConflict
    ) -> AuctionResult:
        """创建默认结果"""
        return AuctionResult(
            auction_id=auction_id,
            winner_task_id=winner_task,
            winner_agent_id="default",
            winning_bid=0,
            payment_amount=0,
            allocation={
                "resource_id": conflict.resource_id,
                "time_window": conflict.time_window,
                "capacity": conflict.resource_capacity,
            },
            total_surplus=0,
            efficiency_score=0.5,
        )


class ShapleyValueCalculator:
    """Shapley值计算器"""

    def calculate(
        self, conflict: ResourceConflict, tasks: list[dict[str, Any]]) -> dict[str, float]:
        """计算Shapley值"""
        n = len(conflict.competing_tasks)
        if n == 0:
            return {}

        shapley_values = {}

        # 计算每个任务的Shapley值
        for task_id in conflict.competing_tasks:
            task_value = 0

            # 遍历所有可能的联盟
            from itertools import combinations

            for r in range(n):
                for coalition in combinations(conflict.competing_tasks, r):
                    if task_id in coalition:
                        continue

                    # 计算联盟的边际贡献
                    value_without = self._calculate_coalition_value(coalition)
                    value_with = self._calculate_coalition_value((*coalition, task_id))

                    marginal_contribution = value_with - value_without

                    # Shapley值权重
                    weight = (math.factorial(r) * math.factorial(n - r - 1)) / math.factorial(n)
                    task_value += weight * marginal_contribution

            shapley_values[task_id] = task_value

        # 归一化
        total_value = sum(shapley_values.values())
        if total_value > 0:
            shapley_values = {k: v / total_value for k, v in shapley_values.items()}

        return shapley_values

    def _calculate_coalition_value(self, coalition: tuple[str, ...]) -> float:
        """计算联盟价值"""
        # 简化计算:联盟价值等于成员价值之和乘以协同系数
        base_value = len(coalition) * 100
        synergy_bonus = len(coalition) * 10  # 协同效应
        return base_value + synergy_bonus


# 导出主类
__all__ = [
    "AuctionManager",
    "AuctionResult",
    "AuctionType",
    "Bid",
    "ConflictDetector",
    "ConflictType",
    "ResourceConflict",
    "ShapleyValueCalculator",
]
