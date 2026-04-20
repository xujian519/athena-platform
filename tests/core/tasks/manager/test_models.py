#!/usr/bin/env python3
from __future__ import annotations
"""
任务管理器模型测试
Task Manager Models Tests

作者: Athena平台团队
创建时间: 2026-04-20
版本: 1.0.0
"""

import pytest
from datetime import datetime, timedelta

from core.tasks.manager.models import (
    Task,
    TaskStatus,
    TaskPriority,
    TaskDependency,
    TaskDependencyType,
    TaskResult,
    TaskMetrics,
)


class TestTaskStatus:
    """测试TaskStatus枚举"""

    def test_status_values(self):
        """测试状态值"""
        assert TaskStatus.PENDING.value == "pending"
        assert TaskStatus.READY.value == "ready"
        assert TaskStatus.ASSIGNED.value == "assigned"
        assert TaskStatus.RUNNING.value == "running"
        assert TaskStatus.COMPLETED.value == "completed"
        assert TaskStatus.FAILED.value == "failed"
        assert TaskStatus.CANCELLED.value == "cancelled"
        assert TaskStatus.BLOCKED.value == "blocked"
        assert TaskStatus.TIMEOUT.value == "timeout"


class TestTaskPriority:
    """测试TaskPriority枚举"""

    def test_priority_values(self):
        """测试优先级值"""
        assert TaskPriority.LOW.value == 1
        assert TaskPriority.NORMAL.value == 2
        assert TaskPriority.HIGH.value == 3
        assert TaskPriority.URGENT.value == 4
        assert TaskPriority.CRITICAL.value == 5

    def test_priority_comparison(self):
        """测试优先级比较"""
        assert TaskPriority.CRITICAL.value > TaskPriority.URGENT.value
        assert TaskPriority.URGENT.value > TaskPriority.HIGH.value
        assert TaskPriority.HIGH.value > TaskPriority.NORMAL.value
        assert TaskPriority.NORMAL.value > TaskPriority.LOW.value


class TestTaskDependency:
    """测试TaskDependency类"""

    def test_create_dependency(self):
        """测试创建依赖"""
        dep = TaskDependency(task_id="task_1")
        assert dep.task_id == "task_1"
        assert dep.dependency_type == TaskDependencyType.FINISH_TO_START
        assert dep.required is True

    def test_dependency_with_type(self):
        """测试带类型的依赖"""
        dep = TaskDependency(
            task_id="task_1",
            dependency_type=TaskDependencyType.START_TO_START,
            required=False,
        )
        assert dep.dependency_type == TaskDependencyType.START_TO_START
        assert dep.required is False


class TestTaskResult:
    """测试TaskResult类"""

    def test_successful_result(self):
        """测试成功结果"""
        result = TaskResult(
            success=True,
            data={"output": "test"},
            execution_time=1.5,
            token_usage=100,
        )
        assert result.success is True
        assert result.data == {"output": "test"}
        assert result.execution_time == 1.5
        assert result.token_usage == 100
        assert result.error is None

    def test_failed_result(self):
        """测试失败结果"""
        result = TaskResult(
            success=False,
            error="执行失败",
        )
        assert result.success is False
        assert result.error == "执行失败"
        assert result.data is None


class TestTask:
    """测试Task类"""

    def test_create_task(self):
        """测试创建任务"""
        task = Task(
            id="task_1",
            title="测试任务",
        )
        assert task.id == "task_1"
        assert task.title == "测试任务"
        assert task.description == ""
        assert task.status == TaskStatus.PENDING
        assert task.priority == TaskPriority.NORMAL
        assert task.progress == 0.0
        assert task.retry_count == 0
        assert task.max_retries == 3

    def test_task_with_all_fields(self):
        """测试带所有字段的任务"""
        now = datetime.now()
        deadline = now + timedelta(hours=1)

        task = Task(
            id="task_1",
            title="完整任务",
            description="任务描述",
            status=TaskStatus.ASSIGNED,
            priority=TaskPriority.HIGH,
            created_at=now,
            updated_at=now,
            deadline=deadline,
            assigned_to="agent_1",
            created_by="user_1",
            session_id="session_1",
            skill_id="skill_1",
            tags=["test", "important"],
            metadata={"key": "value"},
        )

        assert task.id == "task_1"
        assert task.title == "完整任务"
        assert task.status == TaskStatus.ASSIGNED
        assert task.priority == TaskPriority.HIGH
        assert task.assigned_to == "agent_1"
        assert task.tags == ["test", "important"]

    def test_add_dependency(self):
        """测试添加依赖"""
        task = Task(id="task_1", title="测试任务")
        task.add_dependency("task_2", TaskDependencyType.FINISH_TO_START)

        assert len(task.dependencies) == 1
        assert task.dependencies[0].task_id == "task_2"
        assert task.dependencies[0].dependency_type == TaskDependencyType.FINISH_TO_START

    def test_add_duplicate_dependency(self):
        """测试添加重复依赖"""
        task = Task(id="task_1", title="测试任务")
        task.add_dependency("task_2")
        task.add_dependency("task_2")  # 重复添加

        assert len(task.dependencies) == 1

    def test_can_start_with_no_dependencies(self):
        """测试无依赖时可以开始"""
        task = Task(id="task_1", title="测试任务")
        assert task.can_start(set()) is True

    def test_can_start_with_satisfied_dependencies(self):
        """测试依赖已满足时可以开始"""
        task = Task(id="task_1", title="测试任务")
        task.add_dependency("task_2")

        completed_tasks = {"task_2"}
        assert task.can_start(completed_tasks) is True

    def test_cannot_start_with_unsatisfied_dependencies(self):
        """测试依赖未满足时不能开始"""
        task = Task(id="task_1", title="测试任务")
        task.add_dependency("task_2")

        completed_tasks = set()
        assert task.can_start(completed_tasks) is False

    def test_can_start_with_optional_dependency(self):
        """测试可选依赖不影响开始"""
        task = Task(id="task_1", title="测试任务")
        task.dependencies.append(TaskDependency(
            task_id="task_2",
            required=False,
        ))

        assert task.can_start(set()) is True

    def test_assign_to(self):
        """测试分配任务"""
        task = Task(id="task_1", title="测试任务")
        task.assign_to("agent_1")

        assert task.assigned_to == "agent_1"
        assert task.status == TaskStatus.ASSIGNED

    def test_start(self):
        """测试开始任务"""
        task = Task(id="task_1", title="测试任务")
        task.start()

        assert task.status == TaskStatus.RUNNING
        assert task.started_at is not None
        assert isinstance(task.started_at, datetime)

    def test_complete_successfully(self):
        """测试成功完成任务"""
        task = Task(id="task_1", title="测试任务")
        result = TaskResult(success=True, data={"output": "done"})
        task.complete(result)

        assert task.status == TaskStatus.COMPLETED
        assert task.result == result
        assert task.completed_at is not None
        assert task.progress == 1.0

    def test_complete_with_failure(self):
        """测试失败完成任务"""
        task = Task(id="task_1", title="测试任务")
        result = TaskResult(success=False, error="执行失败")
        task.complete(result)

        assert task.status == TaskStatus.FAILED
        assert task.result == result
        assert task.progress == 0.0  # 进度不变

    def test_fail(self):
        """测试标记任务失败"""
        task = Task(id="task_1", title="测试任务")
        task.fail("执行出错")

        assert task.status == TaskStatus.FAILED
        assert task.result is not None
        assert task.result.success is False
        assert task.result.error == "执行出错"

    def test_cancel(self):
        """测试取消任务"""
        task = Task(id="task_1", title="测试任务")
        task.cancel()

        assert task.status == TaskStatus.CANCELLED

    def test_update_progress(self):
        """测试更新进度"""
        task = Task(id="task_1", title="测试任务")

        task.update_progress(0.5)
        assert task.progress == 0.5

        task.update_progress(0.8)
        assert task.progress == 0.8

    def test_update_progress_clamps_to_valid_range(self):
        """测试进度限制在有效范围内"""
        task = Task(id="task_1", title="测试任务")

        task.update_progress(-0.5)
        assert task.progress == 0.0

        task.update_progress(1.5)
        assert task.progress == 1.0

    def test_is_overdue_with_deadline_passed(self):
        """测试任务过期"""
        task = Task(
            id="task_1",
            title="测试任务",
            deadline=datetime.now() - timedelta(hours=1),
        )
        assert task.is_overdue() is True

    def test_is_overdue_with_future_deadline(self):
        """测试任务未过期"""
        task = Task(
            id="task_1",
            title="测试任务",
            deadline=datetime.now() + timedelta(hours=1),
        )
        assert task.is_overdue() is False

    def test_is_overdue_when_completed(self):
        """测试已完成任务不算过期"""
        task = Task(
            id="task_1",
            title="测试任务",
            deadline=datetime.now() - timedelta(hours=1),
            status=TaskStatus.COMPLETED,
        )
        assert task.is_overdue() is False

    def test_is_overdue_when_no_deadline(self):
        """测试无截止时间不算过期"""
        task = Task(id="task_1", title="测试任务")
        assert task.is_overdue() is False

    def test_can_retry(self):
        """测试可以重试"""
        task = Task(
            id="task_1",
            title="测试任务",
            status=TaskStatus.FAILED,
            retry_count=0,
            max_retries=3,
        )
        assert task.can_retry() is True

    def test_cannot_retry_when_max_retries_exceeded(self):
        """测试超过最大重试次数不能重试"""
        task = Task(
            id="task_1",
            title="测试任务",
            status=TaskStatus.FAILED,
            retry_count=3,
            max_retries=3,
        )
        assert task.can_retry() is False

    def test_cannot_retry_when_not_failed(self):
        """测试非失败状态不能重试"""
        task = Task(
            id="task_1",
            title="测试任务",
            status=TaskStatus.PENDING,
        )
        assert task.can_retry() is False

    def test_increment_retry(self):
        """测试增加重试次数"""
        task = Task(
            id="task_1",
            title="测试任务",
            status=TaskStatus.FAILED,
            retry_count=0,
        )
        task.increment_retry()

        assert task.retry_count == 1
        assert task.status == TaskStatus.PENDING

    def test_to_dict(self):
        """测试转换为字典"""
        task = Task(
            id="task_1",
            title="测试任务",
            description="任务描述",
            priority=TaskPriority.HIGH,
            tags=["test"],
        )
        task.add_dependency("task_2")

        data = task.to_dict()

        assert data["id"] == "task_1"
        assert data["title"] == "测试任务"
        assert data["description"] == "任务描述"
        assert data["priority"] == TaskPriority.HIGH.value
        assert data["status"] == TaskStatus.PENDING.value
        assert len(data["dependencies"]) == 1
        assert data["tags"] == ["test"]

    def test_from_dict(self):
        """测试从字典创建"""
        data = {
            "id": "task_1",
            "title": "测试任务",
            "description": "任务描述",
            "status": "pending",
            "priority": 3,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "dependencies": [
                {
                    "task_id": "task_2",
                    "dependency_type": "fts",
                    "required": True,
                }
            ],
            "tags": ["test"],
        }

        task = Task.from_dict(data)

        assert task.id == "task_1"
        assert task.title == "测试任务"
        assert task.status == TaskStatus.PENDING
        assert task.priority == TaskPriority.HIGH
        assert len(task.dependencies) == 1
        assert task.tags == ["test"]


class TestTaskMetrics:
    """测试TaskMetrics类"""

    def test_default_metrics(self):
        """测试默认指标"""
        metrics = TaskMetrics()
        assert metrics.total_tasks == 0
        assert metrics.pending_tasks == 0
        assert metrics.running_tasks == 0
        assert metrics.completed_tasks == 0
        assert metrics.failed_tasks == 0
        assert metrics.blocked_tasks == 0

    def test_metrics_with_values(self):
        """测试带值的指标"""
        metrics = TaskMetrics(
            total_tasks=100,
            pending_tasks=20,
            running_tasks=10,
            completed_tasks=60,
            failed_tasks=5,
            blocked_tasks=5,
            average_execution_time=5.5,
            total_token_usage=50000,
        )

        assert metrics.total_tasks == 100
        assert metrics.pending_tasks == 20
        assert metrics.running_tasks == 10
        assert metrics.completed_tasks == 60
        assert metrics.failed_tasks == 5
        assert metrics.blocked_tasks == 5
        assert metrics.average_execution_time == 5.5
        assert metrics.total_token_usage == 50000
