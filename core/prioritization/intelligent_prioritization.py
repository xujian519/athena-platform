#!/usr/bin/env python3
from __future__ import annotations
"""
智能优先级系统
Intelligent Prioritization System

基于《Agentic Design Patterns》第17章:Prioritization
实现智能任务的优先级排序和动态调整能力:
1. 多维度优先级评估
2. 动态优先级重排序
3. 上下文感知调度
4. 资源约束优化

作者: 小诺·双鱼座
版本: v1.0.0 "智能调度"
创建时间: 2025-01-05
"""

import heapq
import logging
import sys
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))


class PriorityFactor(Enum):
    """优先级考虑因素"""

    URGENCY = "urgency"  # 紧急性
    IMPORTANCE = "importance"  # 重要性
    DEPENDENCY = "dependency"  # 依赖关系
    RESOURCE_AVAILABILITY = "resource_availability"  # 资源可用性
    USER_PREFERENCE = "user_preference"  # 用户偏好
    DEADLINE = "deadline"  # 截止时间
    STRATEGIC_VALUE = "strategic_value"  # 战略价值
    LEARNING_OPPORTUNITY = "learning_opportunity"  # 学习机会


class TaskStatus(Enum):
    """任务状态"""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    BLOCKED = "blocked"
    CANCELLED = "cancelled"


@dataclass(order=True)
class PrioritizedTask:
    """优先级任务"""

    priority_score: float
    task_id: str = field(compare=False)
    title: str = field(compare=False)
    description: str = field(compare=False)
    domain: str = field(compare=False)
    status: TaskStatus = field(default=TaskStatus.PENDING, compare=False)
    factors: dict[str, float] = field(default_factory=dict, compare=False)
    estimated_duration: float = 0.0  # 预估时长(小时)
    deadline: datetime = field(default=None, compare=False)
    dependencies: list[str] = field(default_factory=list, compare=False)
    created_at: datetime = field(default_factory=datetime.now, compare=False)
    metadata: dict[str, Any] = field(default_factory=dict, compare=False)


@dataclass
class ReprioritizationResult:
    """重排序结果"""

    timestamp: datetime
    old_order: list[str]
    new_order: list[str]
    changes: list[dict[str, Any]]
    reason: str


class IntelligentPrioritizationSystem:
    """智能优先级系统"""

    def __init__(self):
        """初始化优先级系统"""
        self.name = "智能优先级系统"
        self.version = "1.0.0"

        # 日志配置
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(self.name)

        # 任务队列 (最大堆)
        self.task_queue: list[PrioritizedTask] = []

        # 任务索引
        self.task_index: dict[str, PrioritizedTask] = {}

        # 优先级权重
        self.priority_weights = {
            PriorityFactor.URGENCY.value: 0.25,
            PriorityFactor.IMPORTANCE.value: 0.25,
            PriorityFactor.DEADLINE.value: 0.20,
            PriorityFactor.DEPENDENCY.value: 0.10,
            PriorityFactor.STRATEGIC_VALUE.value: 0.10,
            PriorityFactor.USER_PREFERENCE.value: 0.05,
            PriorityFactor.RESOURCE_AVAILABILITY.value: 0.03,
            PriorityFactor.LEARNING_OPPORTUNITY.value: 0.02,
        }

        # 统计信息
        self.stats = {
            "total_tasks": 0,
            "completed_tasks": 0,
            "reprioritizations": 0,
            "avg_priority_score": 0.0,
        }

        # 重排序历史
        self.reprioritization_history: list[ReprioritizationResult] = []

        print(f"⚡ {self.name} v{self.version} 初始化完成")

    async def calculate_priority(
        self, task: dict[str, Any], context: Optional[dict[str, Any]] = None
    ) -> float:
        """
        计算任务优先级分数

        Args:
            task: 任务信息
            context: 上下文信息

        Returns:
            float: 优先级分数 (0-1)
        """
        factors = {}

        try:
            # 1. 紧急性评估
            factors[PriorityFactor.URGENCY.value] = await self._assess_urgency(task, context)

            # 2. 重要性评估
            factors[PriorityFactor.IMPORTANCE.value] = await self._assess_importance(task, context)

            # 3. 截止时间评估
            factors[PriorityFactor.DEADLINE.value] = await self._assess_deadline(task, context)

            # 4. 依赖关系评估
            factors[PriorityFactor.DEPENDENCY.value] = await self._assess_dependencies(
                task, context
            )

            # 5. 战略价值评估
            factors[PriorityFactor.STRATEGIC_VALUE.value] = await self._assess_strategic_value(
                task, context
            )

            # 6. 用户偏好评估
            factors[PriorityFactor.USER_PREFERENCE.value] = await self._assess_user_preference(
                task, context
            )

            # 7. 资源可用性评估
            factors[PriorityFactor.RESOURCE_AVAILABILITY.value] = (
                await self._assess_resource_availability(task, context)
            )

            # 8. 学习机会评估
            factors[PriorityFactor.LEARNING_OPPORTUNITY.value] = (
                await self._assess_learning_opportunity(task, context)
            )

            # 9. 计算加权分数
            priority_score = sum(
                factors.get(factor.value, 0) * weight
                for factor, weight in self.priority_weights.items()
            )

            self.logger.info(
                f"📊 任务优先级: {task.get('title', 'unknown')} = {priority_score:.2f}"
            )
            return priority_score

        except Exception as e:
            self.logger.error(f"❌ 优先级计算失败: {e}")
            return 0.5

    async def add_task(
        self, task_id: str, title: str, description: str, domain: str, **kwargs
    ) -> PrioritizedTask:
        """
        添加任务到优先级队列

        Args:
            task_id: 任务ID
            title: 任务标题
            description: 任务描述
            domain: 任务领域
            **kwargs: 其他任务属性

        Returns:
            PrioritizedTask: 优先级任务对象
        """
        task_info = {
            "task_id": task_id,
            "title": title,
            "description": description,
            "domain": domain,
            **kwargs,
        }

        # 计算优先级
        priority_score = await self.calculate_priority(task_info)

        # 创建优先级任务
        prioritized_task = PrioritizedTask(
            priority_score=priority_score,
            task_id=task_id,
            title=title,
            description=description,
            domain=domain,
            deadline=kwargs.get("deadline"),
            dependencies=kwargs.get("dependencies", []),
            estimated_duration=kwargs.get("estimated_duration", 0.0),
            metadata=kwargs,
        )

        # 添加到队列
        heapq.heappush(self.task_queue, prioritized_task)
        self.task_index[task_id] = prioritized_task

        self.stats["total_tasks"] += 1
        self.logger.info(f"✅ 任务已添加: {title} (优先级: {priority_score:.2f})")

        return prioritized_task

    async def get_next_task(self) -> PrioritizedTask | None:
        """
        获取下一个优先级最高的任务

        Returns:
            Optional[PrioritizedTask]: 下一个任务
        """
        if not self.task_queue:
            return None

        # 检查任务是否可执行(依赖已满足)
        while self.task_queue:
            task = heapq.heappop(self.task_queue)

            if task.status == TaskStatus.PENDING:
                # 检查依赖
                if await self._check_dependencies(task):
                    # 放回队列(因为已经pop了)
                    heapq.heappush(self.task_queue, task)
                    return task
                else:
                    # 依赖未满足,任务阻塞
                    task.status = TaskStatus.BLOCKED
                    heapq.heappush(self.task_queue, task)

        return None

    async def reprioritize_all(
        self, reason: str = "定期调整", context: Optional[dict[str, Any]] = None
    ) -> ReprioritizationResult:
        """
        重新对所有任务排序

        Args:
            reason: 重排序原因
            context: 上下文信息

        Returns:
            ReprioritizationResult: 重排序结果
        """
        self.logger.info(f"🔄 重新排序所有任务: {reason}")

        # 保存旧顺序
        old_order = [t.task_id for t in sorted(self.task_queue, key=lambda x: x.priority_score)]

        # 重新计算所有任务的优先级
        tasks = list(self.task_queue)
        self.task_queue.clear()

        for task in tasks:
            task_info = {
                "task_id": task.task_id,
                "title": task.title,
                "description": task.description,
                "domain": task.domain,
                "deadline": task.deadline,
                "dependencies": task.dependencies,
                "estimated_duration": task.estimated_duration,
                **task.metadata,
            }

            new_priority = await self.calculate_priority(task_info, context)
            task.priority_score = new_priority

            if task.status == TaskStatus.BLOCKED:
                # 检查依赖是否已满足
                if await self._check_dependencies(task):
                    task.status = TaskStatus.PENDING

            heapq.heappush(self.task_queue, task)

        # 新顺序
        new_order = [t.task_id for t in sorted(self.task_queue, key=lambda x: x.priority_score)]

        # 分析变化
        changes = []
        for old_idx, old_id in enumerate(old_order):
            if old_id in new_order:
                new_idx = new_order.index(old_id)
                if old_idx != new_idx:
                    changes.append(
                        {
                            "task_id": old_id,
                            "old_position": old_idx,
                            "new_position": new_idx,
                            "shift": new_idx - old_idx,
                        }
                    )

        # 创建结果
        result = ReprioritizationResult(
            timestamp=datetime.now(),
            old_order=old_order,
            new_order=new_order,
            changes=changes,
            reason=reason,
        )

        self.reprioritization_history.append(result)
        self.stats["reprioritizations"] += 1

        self.logger.info(f"✅ 重排序完成: {len(changes)} 个任务位置变化")
        return result

    async def dynamic_reprioritize(self, trigger_event: dict[str, Any]) -> list[dict[str, Any]]:
        """
        动态优先级调整

        Args:
            trigger_event: 触发事件

        Returns:
            list[Dict]: 受影响的任务
        """
        self.logger.info(f"⚡ 动态优先级调整: {trigger_event.get('type', 'unknown')}")

        affected_tasks = []

        try:
            event_type = trigger_event.get("type")

            if event_type == "deadline_approaching":
                # 截止时间临近
                affected_tasks = await self._handle_deadline_approaching(trigger_event)

            elif event_type == "task_completed":
                # 任务完成
                affected_tasks = await self._handle_task_completion(trigger_event)

            elif event_type == "dependency_satisfied":
                # 依赖满足
                affected_tasks = await self._handle_dependency_satisfied(trigger_event)

            elif event_type == "resource_changed":
                # 资源变化
                affected_tasks = await self._handle_resource_change(trigger_event)

            elif event_type == "user_feedback":
                # 用户反馈
                affected_tasks = await self._handle_user_feedback(trigger_event)

            # 更新受影响的任务
            for task_info in affected_tasks:
                task = self.task_index.get(task_info["task_id"])
                if task:
                    new_priority = await self.calculate_priority(
                        {
                            "task_id": task.task_id,
                            "title": task.title,
                            "description": task.description,
                            "domain": task.domain,
                            "deadline": task.deadline,
                            "dependencies": task.dependencies,
                            **task.metadata,
                        },
                        trigger_event,
                    )
                    task.priority_score = new_priority

            self.logger.info(f"✅ 动态调整完成: {len(affected_tasks)} 个任务受影响")
            return affected_tasks

        except Exception as e:
            self.logger.error(f"❌ 动态调整失败: {e}")
            return []

    async def update_priority_weights(self, weights: dict[str, float]) -> bool:
        """
        更新优先级权重

        Args:
            weights: 新的权重配置

        Returns:
            bool: 是否成功更新
        """
        try:
            # 验证权重总和为1
            total = sum(weights.values())
            if abs(total - 1.0) > 0.01:
                self.logger.error(f"权重总和必须为1,当前为{total}")
                return False

            self.priority_weights.update(weights)
            self.logger.info("✅ 优先级权重已更新")
            return True

        except Exception as e:
            self.logger.error(f"❌ 权重更新失败: {e}")
            return False

    # ==================== 评估方法 ====================

    async def _assess_urgency(
        self, task: dict[str, Any], context: dict[str, Any]
    ) -> float:
        """评估紧急性"""
        deadline = task.get("deadline")
        if deadline:
            if isinstance(deadline, str):
                deadline = datetime.fromisoformat(deadline)

            time_remaining = (deadline - datetime.now()).total_seconds() / 3600  # 小时

            if time_remaining < 1:
                return 1.0  # 1小时内,最高紧急性
            elif time_remaining < 4:
                return 0.8
            elif time_remaining < 24:
                return 0.6
            elif time_remaining < 72:
                return 0.4
            else:
                return 0.2

        return 0.3  # 默认中等紧急性

    async def _assess_importance(
        self, task: dict[str, Any], context: dict[str, Any]
    ) -> float:
        """评估重要性"""
        importance = task.get("importance", 0.5)
        return float(importance)

    async def _assess_deadline(
        self, task: dict[str, Any], context: dict[str, Any]
    ) -> float:
        """评估截止时间压力"""
        deadline = task.get("deadline")
        if deadline:
            if isinstance(deadline, str):
                deadline = datetime.fromisoformat(deadline)

            days_remaining = (deadline - datetime.now()).days

            if days_remaining <= 0:
                return 1.0  # 已过期
            elif days_remaining <= 1:
                return 0.9
            elif days_remaining <= 3:
                return 0.7
            elif days_remaining <= 7:
                return 0.5
            else:
                return 0.3

        return 0.5

    async def _assess_dependencies(
        self, task: dict[str, Any], context: dict[str, Any]
    ) -> float:
        """评估依赖关系"""
        dependencies = task.get("dependencies", [])

        if not dependencies:
            return 1.0  # 无依赖,可以立即执行

        # 检查依赖是否已完成
        completed_count = 0
        for dep_id in dependencies:
            dep_task = self.task_index.get(dep_id)
            if dep_task is not None and dep_task.status == TaskStatus.COMPLETED:
                completed_count += 1

        return completed_count / len(dependencies) if dependencies else 1.0

    async def _assess_strategic_value(
        self, task: dict[str, Any], context: dict[str, Any]
    ) -> float:
        """评估战略价值"""
        strategic_value = task.get("strategic_value", 0.5)
        return float(strategic_value)

    async def _assess_user_preference(
        self, task: dict[str, Any], context: dict[str, Any]
    ) -> float:
        """评估用户偏好"""
        user_preference = task.get("user_preference", 0.5)
        return float(user_preference)

    async def _assess_resource_availability(
        self, task: dict[str, Any], context: dict[str, Any]
    ) -> float:
        """评估资源可用性"""
        # 简化实现
        return 0.7

    async def _assess_learning_opportunity(
        self, task: dict[str, Any], context: dict[str, Any]
    ) -> float:
        """评估学习机会"""
        learning_value = task.get("learning_value", 0.5)
        return float(learning_value)

    async def _check_dependencies(self, task: PrioritizedTask) -> bool:
        """检查依赖是否满足"""
        if not task.dependencies:
            return True

        for dep_id in task.dependencies:
            dep_task = self.task_index.get(dep_id)
            if dep_task and dep_task.status != TaskStatus.COMPLETED:
                return False

        return True

    # ==================== 事件处理方法 ====================

    async def _handle_deadline_approaching(self, event: dict[str, Any]) -> list[dict[str, Any]]:
        """处理截止时间临近事件"""
        task_id = event.get("task_id")
        if task_id in self.task_index:
            return [{"task_id": task_id, "reason": "deadline approaching"}]
        return []

    async def _handle_task_completion(self, event: dict[str, Any]) -> list[dict[str, Any]]:
        """处理任务完成事件"""
        task_id = event.get("task_id")
        if task_id in self.task_index:
            self.task_index[task_id].status = TaskStatus.COMPLETED
            self.stats["completed_tasks"] += 1

            # 查找依赖此任务的任务
            affected = []
            for t in self.task_index.values():
                if task_id in t.dependencies:
                    affected.append({"task_id": t.task_id, "reason": "dependency satisfied"})

            return affected

        return []

    async def _handle_dependency_satisfied(self, event: dict[str, Any]) -> list[dict[str, Any]]:
        """处理依赖满足事件"""
        task_id = event.get("task_id")
        if task_id in self.task_index:
            return [{"task_id": task_id, "reason": "unblocked"}]
        return []

    async def _handle_resource_change(self, event: dict[str, Any]) -> list[dict[str, Any]]:
        """处理资源变化事件"""
        # 简化实现:返回所有待处理任务
        return [
            {"task_id": t.task_id, "reason": "resource changed"}
            for t in self.task_index.values()
            if t.status == TaskStatus.PENDING
        ]

    async def _handle_user_feedback(self, event: dict[str, Any]) -> list[dict[str, Any]]:
        """处理用户反馈事件"""
        task_id = event.get("task_id")
        if task_id in self.task_index:
            return [{"task_id": task_id, "reason": "user feedback"}]
        return []

    def get_queue_status(self) -> dict[str, Any]:
        """获取队列状态"""
        pending = [t for t in self.task_queue if t.status == TaskStatus.PENDING]
        in_progress = [t for t in self.task_queue if t.status == TaskStatus.IN_PROGRESS]
        blocked = [t for t in self.task_queue if t.status == TaskStatus.BLOCKED]

        return {
            "total_tasks": len(self.task_queue),
            "pending": len(pending),
            "in_progress": len(in_progress),
            "blocked": len(blocked),
            "avg_priority": (
                sum(t.priority_score for t in self.task_queue) / len(self.task_queue)
                if self.task_queue
                else 0.0
            ),
            **self.stats,
        }

    def get_top_tasks(self, limit: int = 10) -> list[PrioritizedTask]:
        """获取优先级最高的N个任务"""
        sorted_tasks = sorted(self.task_queue, key=lambda x: x.priority_score, reverse=True)
        return sorted_tasks[:limit]


# ==================== 全局实例 ====================

_intelligent_prioritization_system: IntelligentPrioritizationSystem | None = None


def get_intelligent_prioritization_system() -> IntelligentPrioritizationSystem:
    """获取智能优先级系统单例"""
    global _intelligent_prioritization_system
    if _intelligent_prioritization_system is None:
        _intelligent_prioritization_system = IntelligentPrioritizationSystem()
    return _intelligent_prioritization_system


# ==================== 导出 ====================

__all__ = [
    "IntelligentPrioritizationSystem",
    "PrioritizedTask",
    "PriorityFactor",
    "ReprioritizationResult",
    "TaskStatus",
    "get_intelligent_prioritization_system",
]
