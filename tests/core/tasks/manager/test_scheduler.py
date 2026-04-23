#!/usr/bin/env python3

"""
任务调度器测试
Task Scheduler Tests

作者: Athena平台团队
创建时间: 2026-04-20
版本: 1.0.0
"""

import shutil
import tempfile
from datetime import datetime, timedelta

import pytest

from core.tasks.manager.exceptions import (
    TaskDependencyError,
    TaskManagerError,
)
from core.tasks.manager.models import (
    Task,
    TaskPriority,
    TaskResult,
    TaskStatus,
)
from core.tasks.manager.scheduler import TaskScheduler
from core.tasks.manager.storage import FileTaskStorage


@pytest.fixture
def temp_storage_dir():
    """临时存储目录"""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def storage(temp_storage_dir):
    """任务存储实例"""
    return FileTaskStorage(storage_dir=temp_storage_dir)


@pytest.fixture
def scheduler(storage):
    """任务调度器实例"""
    return TaskScheduler(storage=storage)


class TestTaskScheduler:
    """测试TaskScheduler类"""

    def test_init(self, scheduler):
        """测试初始化"""
        assert scheduler.storage is not None
        assert len(scheduler._task_index) == 0
        assert len(scheduler._completed_tasks) == 0
        assert len(scheduler._running_tasks) == 0

    def test_schedule_task(self, scheduler):
        """测试调度任务"""
        task = Task(id="task_1", title="测试任务")
        result = scheduler.schedule_task(task)

        assert result is True
        assert task.id in scheduler._task_index
        assert task.status == TaskStatus.READY

    def test_schedule_task_with_dependencies(self, scheduler):
        """测试调度带依赖的任务"""
        task = Task(id="task_1", title="测试任务")
        task.add_dependency("task_2")
        scheduler.schedule_task(task)

        assert task.status == TaskStatus.BLOCKED

    def test_schedule_task_update_existing(self, scheduler):
        """测试更新现有任务"""
        task1 = Task(id="task_1", title="原始任务", priority=TaskPriority.NORMAL)
        scheduler.schedule_task(task1)

        task2 = Task(id="task_1", title="更新任务", priority=TaskPriority.HIGH)
        scheduler.schedule_task(task2)

        loaded_task = scheduler.get_task("task_1")
        assert loaded_task.title == "更新任务"
        assert loaded_task.priority == TaskPriority.HIGH

    def test_get_next_task_empty_queue(self, scheduler):
        """测试从空队列获取任务"""
        task = scheduler.get_next_task()
        assert task is None

    def test_get_next_task_with_ready_task(self, scheduler):
        """测试获取准备就绪的任务"""
        task = Task(id="task_1", title="测试任务")
        scheduler.schedule_task(task)

        next_task = scheduler.get_next_task()
        assert next_task is not None
        assert next_task.id == "task_1"

    def test_get_next_task_priority_order(self, scheduler):
        """测试按优先级获取任务"""
        low_task = Task(id="low", title="低优先级", priority=TaskPriority.LOW)
        high_task = Task(id="high", title="高优先级", priority=TaskPriority.HIGH)
        normal_task = Task(id="normal", title="普通优先级", priority=TaskPriority.NORMAL)

        scheduler.schedule_task(low_task)
        scheduler.schedule_task(high_task)
        scheduler.schedule_task(normal_task)

        # 高优先级任务应该先出队
        first = scheduler.get_next_task()
        assert first.id == "high"

        second = scheduler.get_next_task()
        assert second.id == "normal"

        third = scheduler.get_next_task()
        assert third.id == "low"

    def test_get_next_task_skips_completed(self, scheduler):
        """测试跳过已完成的任务"""
        task = Task(id="task_1", title="测试任务")
        task.status = TaskStatus.COMPLETED
        # 不调度已完成任务，直接添加到索引
        scheduler._task_index[task.id] = task
        scheduler._completed_tasks.add(task.id)

        next_task = scheduler.get_next_task()
        assert next_task is None

    def test_start_task(self, scheduler):
        """测试开始任务"""
        task = Task(id="task_1", title="测试任务")
        scheduler.schedule_task(task)

        result = scheduler.start_task("task_1", "agent_1")

        assert result is True
        assert task.status == TaskStatus.RUNNING
        assert task.assigned_to == "agent_1"
        assert "task_1" in scheduler._running_tasks

    def test_start_task_not_found(self, scheduler):
        """测试开始不存在的任务"""
        with pytest.raises(TaskManagerError):
            scheduler.start_task("nonexistent", "agent_1")

    def test_start_task_with_unsatisfied_dependencies(self, scheduler):
        """测试开始依赖未满足的任务"""
        task = Task(id="task_1", title="测试任务")
        task.add_dependency("task_2")
        scheduler.schedule_task(task)

        with pytest.raises(TaskDependencyError):
            scheduler.start_task("task_1", "agent_1")

    def test_complete_task_successfully(self, scheduler):
        """测试成功完成任务"""
        task = Task(id="task_1", title="测试任务")
        scheduler.schedule_task(task)
        scheduler.start_task("task_1", "agent_1")

        result = TaskResult(
            success=True,
            data={"output": "done"},
            execution_time=1.5,
        )
        scheduler.complete_task("task_1", result)

        assert task.status == TaskStatus.COMPLETED
        assert "task_1" not in scheduler._running_tasks
        assert "task_1" in scheduler._completed_tasks

    def test_complete_task_unsuccessfully(self, scheduler):
        """测试任务完成但失败"""
        task = Task(id="task_1", title="测试任务")
        scheduler.schedule_task(task)
        scheduler.start_task("task_1", "agent_1")

        result = TaskResult(
            success=False,
            error="执行失败",
        )
        scheduler.complete_task("task_1", result)

        assert task.status == TaskStatus.FAILED
        assert "task_1" not in scheduler._running_tasks
        assert "task_1" not in scheduler._completed_tasks

    def test_complete_task_unblocks_dependents(self, scheduler):
        """测试完成任务解除依赖阻塞"""
        # 创建依赖链：task_2 依赖 task_1
        task1 = Task(id="task_1", title="前置任务")
        task2 = Task(id="task_2", title="后置任务")
        task2.add_dependency("task_1")

        scheduler.schedule_task(task1)
        scheduler.schedule_task(task2)

        assert task2.status == TaskStatus.BLOCKED

        # 完成task_1
        scheduler.start_task("task_1", "agent_1")
        result = TaskResult(success=True)
        scheduler.complete_task("task_1", result)

        # task_2应该解除阻塞
        assert task2.status == TaskStatus.READY

    def test_fail_task_with_retry(self, scheduler):
        """测试任务失败并重试"""
        task = Task(id="task_1", title="测试任务", max_retries=3)
        scheduler.schedule_task(task)
        scheduler.start_task("task_1", "agent_1")

        scheduler.fail_task("task_1", "执行出错")

        assert task.status == TaskStatus.READY  # 无依赖，重试后变为READY
        assert task.retry_count == 1

    def test_fail_task_max_retries_exceeded(self, scheduler):
        """测试超过最大重试次数"""
        task = Task(id="task_1", title="测试任务", max_retries=2, retry_count=2)
        scheduler.schedule_task(task)
        scheduler.start_task("task_1", "agent_1")

        scheduler.fail_task("task_1", "执行出错")

        assert task.status == TaskStatus.FAILED
        assert task.retry_count == 2  # 不再增加

    def test_cancel_task(self, scheduler):
        """测试取消任务"""
        task = Task(id="task_1", title="测试任务")
        scheduler.schedule_task(task)

        result = scheduler.cancel_task("task_1")

        assert result is True
        assert task.status == TaskStatus.CANCELLED

    def test_cancel_completed_task(self, scheduler):
        """测试取消已完成的任务"""
        task = Task(id="task_1", title="测试任务", status=TaskStatus.COMPLETED)
        # 不直接调度已完成任务
        scheduler._task_index[task.id] = task
        scheduler._completed_tasks.add(task.id)

        result = scheduler.cancel_task("task_1")

        assert result is False

    def test_get_task(self, scheduler):
        """测试获取任务"""
        task = Task(id="task_1", title="测试任务")
        scheduler.schedule_task(task)

        loaded_task = scheduler.get_task("task_1")
        assert loaded_task is not None
        assert loaded_task.id == "task_1"

    def test_get_task_not_found(self, scheduler):
        """测试获取不存在的任务"""
        task = scheduler.get_task("nonexistent")
        assert task is None

    def test_get_metrics(self, scheduler):
        """测试获取指标"""
        task1 = Task(id="task_1", title="任务1", status=TaskStatus.PENDING)
        task2 = Task(id="task_2", title="任务2", status=TaskStatus.RUNNING)
        task3 = Task(id="task_3", title="任务3", status=TaskStatus.COMPLETED)

        scheduler.schedule_task(task1)
        scheduler.schedule_task(task2)
        scheduler.schedule_task(task3)
        scheduler._running_tasks.add("task_2")
        scheduler._completed_tasks.add("task_3")

        metrics = scheduler.get_metrics()

        assert metrics.total_tasks == 3
        assert metrics.pending_tasks >= 1
        assert metrics.running_tasks == 1
        assert metrics.completed_tasks == 1

    def test_get_ready_tasks(self, scheduler):
        """测试获取准备就绪的任务"""
        task1 = Task(id="task_1", title="任务1")
        task2 = Task(id="task_2", title="任务2")
        task2.add_dependency("task_x")  # 添加依赖使其被阻塞
        task3 = Task(id="task_3", title="任务3")

        scheduler.schedule_task(task1)
        scheduler.schedule_task(task2)
        scheduler.schedule_task(task3)

        ready_tasks = scheduler.get_ready_tasks()
        assert len(ready_tasks) == 2  # task1和task3准备就绪

    def test_get_blocked_tasks(self, scheduler):
        """测试获取被阻塞的任务"""
        task1 = Task(id="task_1", title="任务1")
        task2 = Task(id="task_2", title="任务2")
        task2.add_dependency("task_x")  # 添加依赖使其被阻塞

        scheduler.schedule_task(task1)
        scheduler.schedule_task(task2)

        blocked_tasks = scheduler.get_blocked_tasks()
        assert len(blocked_tasks) == 1
        assert blocked_tasks[0].id == "task_2"

    def test_get_overdue_tasks(self, scheduler):
        """测试获取过期任务"""
        task1 = Task(
            id="task_1",
            title="过期任务",
            deadline=datetime.now() - timedelta(hours=1),
        )
        task2 = Task(
            id="task_2",
            title="未过期任务",
            deadline=datetime.now() + timedelta(hours=1),
        )

        scheduler.schedule_task(task1)
        scheduler.schedule_task(task2)

        overdue_tasks = scheduler.get_overdue_tasks()
        assert len(overdue_tasks) == 1
        assert overdue_tasks[0].id == "task_1"

    def test_cleanup_completed(self, scheduler):
        """测试清理已完成的任务"""
        # 创建已完成的任务（10天前）
        old_task = Task(
            id="old_task",
            title="旧任务",
            completed_at=datetime.now() - timedelta(days=10),
        )
        old_task.status = TaskStatus.COMPLETED

        # 创建最近完成的任务
        recent_task = Task(
            id="recent_task",
            title="最近任务",
            completed_at=datetime.now() - timedelta(days=1),
        )
        recent_task.status = TaskStatus.COMPLETED

        # 直接添加到索引和完成集合
        scheduler._task_index[old_task.id] = old_task
        scheduler._task_index[recent_task.id] = recent_task
        scheduler._completed_tasks.add("old_task")
        scheduler._completed_tasks.add("recent_task")

        # 清理7天前的任务
        cleaned = scheduler.cleanup_completed(keep_days=7)

        assert cleaned == 1
        assert scheduler.get_task("old_task") is None
        assert scheduler.get_task("recent_task") is not None

    def test_create_task(self, scheduler):
        """测试创建任务"""
        task = scheduler.create_task(
            title="新任务",
            description="任务描述",
            priority=TaskPriority.HIGH,
            assigned_to="agent_1",
            created_by="user_1",
            session_id="session_1",
            skill_id="skill_1",
            tags=["test"],
        )

        assert task.id is not None
        assert task.title == "新任务"
        assert task.priority == TaskPriority.HIGH
        assert task.assigned_to == "agent_1"
        assert task.tags == ["test"]
        assert task.status == TaskStatus.READY

    def test_create_task_with_dependencies(self, scheduler):
        """测试创建带依赖的任务"""
        task = scheduler.create_task(
            title="依赖任务",
            dependencies=["task_1", "task_2"],
        )

        assert len(task.dependencies) == 2
        assert task.status == TaskStatus.BLOCKED

    def test_get_tasks_by_agent(self, scheduler):
        """测试按Agent获取任务"""
        task1 = Task(id="task_1", title="任务1", assigned_to="agent_1")
        task2 = Task(id="task_2", title="任务2", assigned_to="agent_2")
        task3 = Task(id="task_3", title="任务3", assigned_to="agent_1")

        scheduler.schedule_task(task1)
        scheduler.schedule_task(task2)
        scheduler.schedule_task(task3)

        agent1_tasks = scheduler.get_tasks_by_agent("agent_1")
        agent2_tasks = scheduler.get_tasks_by_agent("agent_2")

        assert len(agent1_tasks) == 2
        assert len(agent2_tasks) == 1

    def test_get_tasks_by_session(self, scheduler):
        """测试按会话获取任务"""
        task1 = Task(id="task_1", title="任务1", session_id="session_1")
        task2 = Task(id="task_2", title="任务2", session_id="session_2")
        task3 = Task(id="task_3", title="任务3", session_id="session_1")

        scheduler.schedule_task(task1)
        scheduler.schedule_task(task2)
        scheduler.schedule_task(task3)

        session1_tasks = scheduler.get_tasks_by_session("session_1")
        session2_tasks = scheduler.get_tasks_by_session("session_2")

        assert len(session1_tasks) == 2
        assert len(session2_tasks) == 1

    def test_get_pending_count(self, scheduler):
        """测试获取等待中的任务数量"""
        task1 = Task(id="task_1", title="任务1")
        task2 = Task(id="task_2", title="任务2")
        task3 = Task(id="task_3", title="任务3")
        task3.add_dependency("task_x")  # 被阻塞

        scheduler.schedule_task(task1)
        scheduler.schedule_task(task2)
        scheduler.schedule_task(task3)

        count = scheduler.get_pending_count()
        assert count == 2  # task1和task2准备就绪

    def test_is_empty(self, scheduler):
        """测试队列是否为空"""
        assert scheduler.is_empty() is True

        task = Task(id="task_1", title="测试任务")
        scheduler.schedule_task(task)

        assert scheduler.is_empty() is False

    def test_complex_dependency_chain(self, scheduler):
        """测试复杂依赖链"""
        # task_3 -> task_2 -> task_1
        task1 = Task(id="task_1", title="第一步")
        task2 = Task(id="task_2", title="第二步")
        task2.add_dependency("task_1")
        task3 = Task(id="task_3", title="第三步")
        task3.add_dependency("task_2")

        scheduler.schedule_task(task1)
        scheduler.schedule_task(task2)
        scheduler.schedule_task(task3)

        # 只有task_1准备就绪
        assert task1.status == TaskStatus.READY
        assert task2.status == TaskStatus.BLOCKED
        assert task3.status == TaskStatus.BLOCKED

        # 完成task_1
        scheduler.start_task("task_1", "agent_1")
        scheduler.complete_task("task_1", TaskResult(success=True))

        # task_2应该准备就绪
        assert task2.status == TaskStatus.READY
        assert task3.status == TaskStatus.BLOCKED

        # 完成task_2
        scheduler.start_task("task_2", "agent_1")
        scheduler.complete_task("task_2", TaskResult(success=True))

        # task_3应该准备就绪
        assert task3.status == TaskStatus.READY

