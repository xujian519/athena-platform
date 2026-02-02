#!/usr/bin/env python3
"""
Agent协调器 - 调度策略
Agent Coordinator - Coordination Strategies

作者: Athena AI系统
创建时间: 2025-12-04
重构时间: 2026-01-26
版本: 2.0.0
"""

import logging
from typing import Any

from .types import TaskExecution, TaskStatus


logger = logging.getLogger(__name__)


class CoordinationStrategies:
    """协调策略集合"""

    def __init__(self, coordinator):
        """
        初始化协调策略

        Args:
            coordinator: AgentCoordinator实例
        """
        self.coordinator = coordinator
        self.coordination_strategies = {
            "load_balancing": True,
            "specialization_matching": True,
            "performance_optimization": True,
            "deadline_aware": True,
            "intelligent_routing": True,
            "adaptive_scheduling": True,
            "resource_monitoring": True,
            "failure_recovery": True,
        }

    async def intelligent_task_assignment(self, task_data: dict[str, Any]) -> dict[str, Any]:
        """
        智能任务分配算法

        Args:
            task_data: 任务数据

        Returns:
            分配结果
        """
        try:
            task_complexity = self._calculate_task_complexity(task_data)
            agent_scores = await self._evaluate_agent_performance()

            # 基于性能评分选择最佳Agent
            best_agent = max(agent_scores.items(), key=lambda x: x[1])[0]

            # 动态调整任务优先级
            priority = self._calculate_dynamic_priority(task_complexity, task_data)

            result = {
                "assigned_agent": best_agent,
                "priority": priority,
                "complexity": task_complexity,
                "assignment_strategy": "intelligent_performance_based",
                "estimated_duration": self._estimate_task_duration_with_complexity(
                    task_complexity, best_agent
                ),
            }

            logger.info(f"🧠 智能分配任务给 {best_agent} (复杂度: {task_complexity:.2f})")
            return result

        except Exception as e:
            logger.error(f"❌ 智能任务分配失败: {e}")
            return {"error": str(e)}

    async def load_balancing_assignment(self, task_data: dict[str, Any]) -> dict[str, Any]:
        """
        负载均衡任务分配

        Args:
            task_data: 任务数据

        Returns:
            分配结果
        """
        try:
            # 获取各Agent当前负载
            agent_loads = await self._get_agent_loads()

            # 选择负载最轻的Agent
            best_agent = min(agent_loads.items(), key=lambda x: x[1]["load"])[0]

            result = {
                "assigned_agent": best_agent,
                "agent_loads": agent_loads,
                "assignment_strategy": "load_balanced",
                "load_distribution": self._calculate_load_distribution(agent_loads),
            }

            logger.info(
                f"⚖️ 负载均衡分配任务给 {best_agent} (负载: {agent_loads[best_agent]['load']})"
            )
            return result

        except Exception as e:
            logger.error(f"❌ 负载均衡分配失败: {e}")
            return {"error": str(e)}

    async def handle_task_failure(self, failure_data: dict[str, Any]) -> dict[str, Any]:
        """
        任务失败处理和恢复

        Args:
            failure_data: 失败数据

        Returns:
            处理结果
        """
        try:
            failed_task_id = failure_data.get("task_id")
            error_message = failure_data.get("error")

            if failed_task_id in self.coordinator.active_tasks:
                task_execution = self.coordinator.active_tasks[failed_task_id]

                # 更新失败统计
                self.coordinator.failed_tasks += 1

                # 重试逻辑
                retry_count = failure_data.get("retry_count", 0)
                if retry_count < self.coordinator.retry_attempts:
                    # 重新分配给不同的Agent
                    new_assignment = await self._reassign_task(task_execution)
                    return {
                        "action": "retry",
                        "new_assignment": new_assignment,
                        "retry_count": retry_count + 1,
                    }
                else:
                    # 标记为最终失败
                    task_execution.status = TaskStatus.FAILED
                    task_execution.error_message = error_message

                    # 移到完成任务历史
                    self.coordinator.completed_tasks[failed_task_id] = task_execution
                    del self.coordinator.active_tasks[failed_task_id]

                    return {
                        "action": "final_failure",
                        "reason": "max_retries_exceeded",
                        "error": error_message,
                    }

            return {"action": "task_not_found"}

        except Exception as e:
            logger.error(f"❌ 故障处理失败: {e}")
            return {"error": str(e)}

    def _calculate_task_complexity(self, task_data: dict[str, Any]) -> float:
        """
        计算任务复杂度 (0.0-1.0)

        Args:
            task_data: 任务数据

        Returns:
            复杂度分数
        """
        complexity_score = 0.0

        # 基于任务类型
        task_type = task_data.get("task_type", "")
        if "analysis" in task_type.lower():
            complexity_score += 0.3
        if "creative" in task_type.lower():
            complexity_score += 0.4
        if "multi_step" in task_type.lower():
            complexity_score += 0.3

        # 基于内容长度
        content_length = len(str(task_data.get("content", "")))
        if content_length > 1000:
            complexity_score += 0.2
        elif content_length > 500:
            complexity_score += 0.1

        # 基于所需Agent数量
        required_agents = task_data.get("required_agents", [])
        complexity_score += len(required_agents) * 0.1

        return min(complexity_score, 1.0)

    async def _evaluate_agent_performance(self) -> dict[str, float]:
        """
        评估Agent性能评分

        Returns:
            Agent性能评分字典
        """
        scores = {}

        # 模拟性能评分(实际应该基于历史数据)
        scores[self.coordinator.search_agent.agent_id] = 0.85
        scores[self.coordinator.analysis_agent.agent_id] = 0.80
        scores[self.coordinator.creative_agent.agent_id] = 0.75

        # 添加随机波动模拟实际性能变化
        import random

        for agent_id in scores:
            scores[agent_id] += random.uniform(-0.05, 0.05)
            scores[agent_id] = max(0.0, min(1.0, scores[agent_id]))

        return scores

    def _calculate_dynamic_priority(self, complexity: float, task_data: dict[str, Any]) -> int:
        """
        动态计算任务优先级 (1-5)

        Args:
            complexity: 任务复杂度
            task_data: 任务数据

        Returns:
            优先级值
        """
        base_priority = task_data.get("priority", 3)

        # 复杂任务降低优先级
        complexity_adjustment = int(complexity * 2)

        # 基于截止时间调整
        deadline = task_data.get("deadline")
        if deadline:
            time_remaining = (
                datetime.fromisoformat(deadline) - datetime.now()
            ).total_seconds() / 3600
            if time_remaining < 1:  # 1小时内
                return 5  # 最高优先级
            elif time_remaining < 24:  # 24小时内
                base_priority += 1

        return min(5, max(1, base_priority - complexity_adjustment))

    def _estimate_task_duration_with_complexity(self, complexity: float, agent_id: str) -> float:
        """
        基于复杂度和Agent类型估算任务执行时间(秒)

        Args:
            complexity: 任务复杂度
            agent_id: Agent ID

        Returns:
            估算时长(秒)
        """
        base_duration = 30  # 基础30秒

        # 根据复杂度调整
        complexity_factor = 1 + complexity * 3  # 最多4倍时间

        # 根据Agent类型调整
        if "analysis" in agent_id.lower():
            complexity_factor *= 1.5
        elif "creative" in agent_id.lower():
            complexity_factor *= 2.0

        return base_duration * complexity_factor

    async def _get_agent_loads(self) -> dict[str, dict[str, Any]]:
        """
        获取各Agent负载情况

        Returns:
            Agent负载字典
        """
        loads = {}

        agents = [
            self.coordinator.search_agent,
            self.coordinator.analysis_agent,
            self.coordinator.creative_agent,
        ]
        for agent in agents:
            active_count = sum(
                1
                for task in self.coordinator.active_tasks.values()
                if task.assigned_agents and agent.agent_id in task.assigned_agents
            )

            loads[agent.agent_id] = {
                "load": active_count,
                "max_capacity": 5,  # 假设最大容量5个任务
                "availability": max(0, 5 - active_count) / 5,
            }

        return loads

    def _calculate_load_distribution(self, agent_loads: dict[str, dict[str, Any]]) -> dict[str, float]:
        """
        计算负载分布

        Args:
            agent_loads: Agent负载数据

        Returns:
            负载分布百分比
        """
        total_load = sum(load_info["load"] for load_info in agent_loads.values())
        if total_load == 0:
            return dict.fromkeys(agent_loads.keys(), 0.33)

        return {
            agent_id: load_info["load"] / total_load
            for agent_id, load_info in agent_loads.items()
        }

    async def _reassign_task(self, task_execution: TaskExecution) -> dict[str, Any]:
        """
        重新分配失败的任务

        Args:
            task_execution: 任务执行实例

        Returns:
            重新分配结果
        """
        # 获取当前执行失败的Agent
        failed_agents = task_execution.assigned_agents or []

        # 获取其他可用Agent
        available_agents = [
            self.coordinator.search_agent,
            self.coordinator.analysis_agent,
            self.coordinator.creative_agent,
        ]
        other_agents = [
            agent for agent in available_agents if agent.agent_id not in failed_agents
        ]

        if other_agents:
            # 选择性能最好的可用Agent
            best_agent = other_agents[0]
            task_execution.assigned_agents = [best_agent.agent_id]

            return {"reassigned_to": best_agent.agent_id, "reason": "original_agent_failed"}
        else:
            return {"reassigned_to": None, "reason": "no_available_agents"}
