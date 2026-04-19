#!/usr/bin/env python3
from __future__ import annotations
"""
协作协议 - 协调协议实现
Collaboration Protocols - Coordination Protocol Implementation

处理智能体间的任务协调和资源分配

作者: Athena AI系统
创建时间: 2025-12-04
重构时间: 2026-01-26
版本: 2.1.0
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Any

# 从本地模块导入
from core.protocols.collaboration.base import BaseProtocol
from core.protocols.collaboration.types import (
    ProtocolMessage,
    ProtocolPhase,
    ProtocolType,
)

logger = logging.getLogger(__name__)


class CoordinationProtocol(BaseProtocol):
    """协调协议 - 处理智能体间的任务协调和资源分配"""

    def __init__(self, protocol_id: str):
        super().__init__(protocol_id, ProtocolType.COORDINATION)
        self.coordination_rules: dict[str, Any] = {}
        self.resource_pools: dict[str, dict[str, Any]] = (
            {}
        )  # resource_name -> pool_info
        self.task_queue: list[dict[str, Any]] = []
        self.assignment_history: list[dict[str, Any]] = []

    async def initialize(self) -> bool:
        """初始化协调协议"""
        try:
            # 设置协调规则
            self.coordination_rules = {
                "assignment_strategy": "capability_based",  # capability_based, load_balanced, priority_based
                "conflict_resolution": "negotiation",  # priority_based, negotiation, arbitration
                "resource_sharing": "fair",  # fair, priority_based, market_based
                "task_deadline_policy": "flexible",  # strict, flexible, adaptive
                "coordination_interval": timedelta(seconds=10),
            }

            # 注册消息处理器
            self.register_message_handler("task_request", self._handle_task_request)
            self.register_message_handler(
                "resource_request", self._handle_resource_request
            )
            self.register_message_handler("task_update", self._handle_task_update)
            self.register_message_handler(
                "coordination_request", self._handle_coordination_request
            )

            # 初始化资源池
            self._initialize_resource_pools()

            logger.info(f"协调协议 {self.protocol_id} 初始化完成")
            return True

        except Exception as e:
            logger.error(f"协调协议 {self.protocol_id} 初始化失败: {e}")
            return False

    async def execute(self) -> bool:
        """执行协调协议"""
        try:
            self.context.current_phase = ProtocolPhase.EXECUTION

            # 执行协调循环
            while self.running:
                # 处理任务分配
                await self._process_task_assignment()

                # 处理资源分配
                await self._process_resource_allocation()

                # 检测和解决冲突
                await self._detect_and_resolve_conflicts()

                # 等待下次协调
                await asyncio.sleep(
                    self.coordination_rules["coordination_interval"].total_seconds()
                )

            return True

        except Exception as e:
            logger.error(f"协调协议 {self.protocol_id} 执行失败: {e}")
            return False

    def _initialize_resource_pools(self) -> None:
        """初始化资源池"""
        default_resources = [
            {"name": "cpu", "total": 100, "unit": "percent"},
            {"name": "memory", "total": 16, "unit": "GB"},
            {"name": "storage", "total": 1000, "unit": "GB"},
            {"name": "network_bandwidth", "total": 1000, "unit": "Mbps"},
        ]

        for resource in default_resources:
            self.resource_pools[resource["name"]] = {
                "total": resource["total"],
                "available": resource["total"],
                "allocated": 0,
                "unit": resource["unit"],
                "allocations": {},  # agent_id -> amount
            }

    async def _process_task_assignment(self) -> None:
        """处理任务分配"""
        try:
            # 处理待分配任务
            while self.task_queue:
                task = self.task_queue.pop(0)
                assignment = await self._assign_task(task)

                if assignment:
                    self.assignment_history.append(
                        {
                            "task_id": task["task_id"],
                            "assigned_to": assignment["agent_id"],
                            "assigned_at": datetime.now(),
                            "strategy": assignment["strategy"],
                        }
                    )

                    # 通知被分配的智能体
                    notification = ProtocolMessage(
                        sender_id="coordination_protocol",
                        receiver_id=assignment["agent_id"],
                        message_type="coordination_request",
                        content={
                            "action": "task_assignment",
                            "task": task,
                            "assignment_info": assignment,
                        },
                    )
                    self.send_message(notification)

        except Exception as e:
            logger.error(f"处理任务分配失败: {e}")

    async def _assign_task(self, task: dict[str, Any]) -> dict[str, Any] | None:
        """分配任务"""
        try:
            strategy = self.coordination_rules["assignment_strategy"]

            if strategy == "capability_based":
                return await self._assign_task_capability_based(task)
            elif strategy == "load_balanced":
                return await self._assign_task_load_balanced(task)
            elif strategy == "priority_based":
                return await self._assign_task_priority_based(task)

            return None

        except Exception as e:
            logger.error(f"任务分配失败: {e}")
            return None

    async def _assign_task_capability_based(
        self, task: dict[str, Any]
    ) -> dict[str, Any] | None:
        """基于能力分配任务"""
        required_capabilities = task.get("required_capabilities", [])
        candidate_scores = []

        for participant in self.context.participants:
            # 获取智能体能力(从私有状态)
            capabilities = self.context.private_states[participant].get(
                "capabilities", []
            )
            current_load = self.context.private_states[participant].get(
                "current_load", 0
            )
            max_load = self.context.private_states[participant].get("max_load", 10)

            # 计算能力匹配分数
            matched_capabilities = set(required_capabilities) & set(capabilities)
            capability_score = (
                len(matched_capabilities) / len(required_capabilities)
                if required_capabilities
                else 0
            )

            # 计算负载分数
            load_score = (max_load - current_load) / max_load

            # 综合分数
            total_score = capability_score * 0.7 + load_score * 0.3

            candidate_scores.append(
                {
                    "agent_id": participant,
                    "score": total_score,
                    "capability_match": capability_score,
                    "load_factor": load_score,
                }
            )

        # 选择最高分数的智能体
        if candidate_scores:
            candidate_scores.sort(key=lambda x: x["score"], reverse=True)
            best_candidate = candidate_scores[0]

            return {
                "agent_id": best_candidate["agent_id"],
                "strategy": "capability_based",
                "score": best_candidate["score"],
                "reasoning": f"能力匹配度: {best_candidate['capability_match']:.2f}, 负载因子: {best_candidate['load_factor']:.2f}",
            }

        return None

    async def _assign_task_load_balanced(
        self, task: dict[str, Any]
    ) -> dict[str, Any] | None:
        """负载均衡分配任务"""
        candidate_loads = []

        for participant in self.context.participants:
            current_load = self.context.private_states[participant].get(
                "current_load", 0
            )
            max_load = self.context.private_states[participant].get("max_load", 10)

            candidate_loads.append(
                {
                    "agent_id": participant,
                    "current_load": current_load,
                    "max_load": max_load,
                    "load_ratio": current_load / max_load,
                }
            )

        # 选择负载最低的智能体
        candidate_loads.sort(key=lambda x: x["load_ratio"])
        best_candidate = candidate_loads[0]

        return {
            "agent_id": best_candidate["agent_id"],
            "strategy": "load_balanced",
            "load_ratio": best_candidate["load_ratio"],
            "reasoning": f"当前负载: {best_candidate['current_load']}/{best_candidate['max_load']}",
        }

    async def _assign_task_priority_based(
        self, task: dict[str, Any]
    ) -> dict[str, Any] | None:
        """基于优先级分配任务"""
        task_priority = task.get("priority", 5)
        candidate_priorities = []

        for participant in self.context.participants:
            agent_priority = self.context.private_states[participant].get("priority", 5)
            current_load = self.context.private_states[participant].get(
                "current_load", 0
            )
            max_load = self.context.private_states[participant].get("max_load", 10)

            # 只有智能体优先级 >= 任务优先级时才分配
            if agent_priority >= task_priority and current_load < max_load:
                candidate_priorities.append(
                    {
                        "agent_id": participant,
                        "priority": agent_priority,
                        "current_load": current_load,
                    }
                )

        if candidate_priorities:
            # 选择优先级最高且负载适中的智能体
            candidate_priorities.sort(key=lambda x: (-x["priority"], x["current_load"]))
            best_candidate = candidate_priorities[0]

            return {
                "agent_id": best_candidate["agent_id"],
                "strategy": "priority_based",
                "agent_priority": best_candidate["priority"],
                "task_priority": task_priority,
                "reasoning": f"智能体优先级: {best_candidate['priority']}, 任务优先级: {task_priority}",
            }

        return None

    async def _process_resource_allocation(self) -> None:
        """处理资源分配"""
        try:
            # 检查资源使用情况
            for resource_name, pool_info in self.resource_pools.items():
                # 检查是否有资源不足的情况
                if pool_info["available"] < pool_info["total"] * 0.1:  # 可用资源少于10%
                    self.trigger_event(
                        "resource_shortage",
                        {
                            "resource_name": resource_name,
                            "available": pool_info["available"],
                            "total": pool_info["total"],
                            "utilization": (pool_info["total"] - pool_info["available"])
                            / pool_info["total"],
                        },
                    )

        except Exception as e:
            logger.error(f"处理资源分配失败: {e}")

    async def _detect_and_resolve_conflicts(self) -> None:
        """检测和解决冲突"""
        try:
            # 检测资源冲突
            resource_conflicts = await self._detect_resource_conflicts()
            if resource_conflicts:
                await self._resolve_resource_conflicts(resource_conflicts)

            # 检测任务冲突
            task_conflicts = await self._detect_task_conflicts()
            if task_conflicts:
                await self._resolve_task_conflicts(task_conflicts)

        except Exception as e:
            logger.error(f"检测和解决冲突失败: {e}")

    async def _detect_resource_conflicts(self) -> list[dict[str, Any]]:
        """检测资源冲突"""
        conflicts = []

        for resource_name, pool_info in self.resource_pools.items():
            if pool_info["allocated"] > pool_info["total"]:
                conflicts.append(
                    {
                        "type": "resource_overallocation",
                        "resource_name": resource_name,
                        "allocated": pool_info["allocated"],
                        "total": pool_info["total"],
                        "overallocation": pool_info["allocated"] - pool_info["total"],
                    }
                )

        return conflicts

    async def _detect_task_conflicts(self) -> list[dict[str, Any]]:
        """检测任务冲突"""
        conflicts = []

        # 检测智能体过载
        for participant in self.context.participants:
            current_load = self.context.private_states[participant].get(
                "current_load", 0
            )
            max_load = self.context.private_states[participant].get("max_load", 10)

            if current_load > max_load:
                conflicts.append(
                    {
                        "type": "agent_overload",
                        "agent_id": participant,
                        "current_load": current_load,
                        "max_load": max_load,
                        "overload": current_load - max_load,
                    }
                )

        return conflicts

    async def _resolve_resource_conflicts(
        self, conflicts: list[dict[str, Any]]
    ) -> None:
        """解决资源冲突"""
        resolution_strategy = self.coordination_rules["conflict_resolution"]

        for conflict in conflicts:
            if resolution_strategy == "priority_based":
                await self._resolve_resource_conflict_priority_based(conflict)
            elif resolution_strategy == "negotiation":
                await self._resolve_resource_conflict_negotiation(conflict)

    async def _resolve_task_conflicts(self, conflicts: list[dict[str, Any]]) -> None:
        """解决任务冲突"""
        resolution_strategy = self.coordination_rules["conflict_resolution"]

        for conflict in conflicts:
            if resolution_strategy == "priority_based":
                await self._resolve_task_conflict_priority_based(conflict)
            elif resolution_strategy == "negotiation":
                await self._resolve_task_conflict_negotiation(conflict)

    async def _resolve_resource_conflict_priority_based(
        self, conflict: dict[str, Any]
    ) -> None:
        """基于优先级解决资源冲突"""
        # 实现基于优先级的资源冲突解决
        pass

    async def _resolve_resource_conflict_negotiation(
        self, conflict: dict[str, Any]
    ) -> None:
        """通过协商解决资源冲突"""
        # 实现协商式资源冲突解决
        pass

    async def _resolve_task_conflict_priority_based(
        self, conflict: dict[str, Any]
    ) -> None:
        """基于优先级解决任务冲突"""
        # 实现基于优先级的任务冲突解决
        pass

    async def _resolve_task_conflict_negotiation(
        self, conflict: dict[str, Any]
    ) -> None:
        """通过协商解决任务冲突"""
        # 实现协商式任务冲突解决
        pass

    async def _handle_task_request(self, message: ProtocolMessage) -> None:
        """处理任务请求"""
        try:
            task = message.content.get("task")
            if task:
                self.task_queue.append(task)
                self.update_shared_state("pending_tasks", len(self.task_queue))

                # 发送确认
                response = ProtocolMessage(
                    sender_id="coordination_protocol",
                    receiver_id=message.sender_id,
                    message_type="response",
                    content={
                        "request_id": message.content.get("request_id"),
                        "status": "queued",
                        "result": {"message": "Task queued for assignment"},
                    },
                )
                self.send_message(response)

        except Exception as e:
            logger.error(f"处理任务请求失败: {e}")

    async def _handle_resource_request(self, message: ProtocolMessage) -> None:
        """处理资源请求"""
        try:
            resource_name = message.content.get("resource_name")
            amount = message.content.get("amount", 1)
            agent_id = message.sender_id

            if resource_name in self.resource_pools:
                pool = self.resource_pools[resource_name]

                if pool["available"] >= amount:
                    # 分配资源
                    pool["available"] -= amount
                    pool["allocated"] += amount
                    pool["allocations"][agent_id] = (
                        pool["allocations"].get(agent_id, 0) + amount
                    )

                    response = ProtocolMessage(
                        sender_id="coordination_protocol",
                        receiver_id=agent_id,
                        message_type="response",
                        content={
                            "request_id": message.content.get("request_id"),
                            "status": "granted",
                            "result": {
                                "resource_name": resource_name,
                                "amount": amount,
                                "remaining": pool["available"],
                            },
                        },
                    )
                else:
                    # 资源不足
                    response = ProtocolMessage(
                        sender_id="coordination_protocol",
                        receiver_id=agent_id,
                        message_type="response",
                        content={
                            "request_id": message.content.get("request_id"),
                            "status": "denied",
                            "result": {
                                "reason": "insufficient_resources",
                                "requested": amount,
                                "available": pool["available"],
                            },
                        },
                    )

                self.send_message(response)

        except Exception as e:
            logger.error(f"处理资源请求失败: {e}")

    async def _handle_task_update(self, message: ProtocolMessage) -> None:
        """处理任务更新"""
        try:
            task_id = message.content.get("task_id")
            status = message.content.get("status")
            agent_id = message.sender_id

            if task_id and status:
                # 更新任务状态
                self.update_shared_state(f"task_{task_id}_status", status)
                self.update_shared_state(f"task_{task_id}_updated_by", agent_id)

                # 如果任务完成,释放相关资源
                if status == "completed":
                    await self._release_task_resources(task_id, agent_id)

        except Exception as e:
            logger.error(f"处理任务更新失败: {e}")

    async def _handle_coordination_request(self, message: ProtocolMessage) -> None:
        """处理协调请求"""
        try:
            action = message.content.get("action")

            if action == "task_assignment":
                # 处理任务分配确认
                task = message.content.get("task")
                assignment_info = message.content.get("assignment_info")

                if task and assignment_info:
                    # 更新智能体负载
                    agent_id = assignment_info["agent_id"]
                    current_load = self.context.private_states[agent_id].get(
                        "current_load", 0
                    )
                    self.update_private_state(
                        agent_id, "current_load", current_load + 1
                    )

        except Exception as e:
            logger.error(f"处理协调请求失败: {e}")

    async def _release_task_resources(self, task_id: str, agent_id: str) -> None:
        """释放任务相关资源"""
        try:
            # 更新智能体负载
            current_load = self.context.private_states[agent_id].get("current_load", 0)
            self.update_private_state(
                agent_id, "current_load", max(0, current_load - 1)
            )

            # 释放分配给任务的资源
            # 这里可以根据需要实现具体的资源释放逻辑

        except Exception as e:
            logger.error(f"释放任务资源失败: {e}")
