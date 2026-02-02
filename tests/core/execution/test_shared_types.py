#!/usr/bin/env python3
"""
执行模块单元测试
Execution Module Unit Tests

测试统一的类型定义和执行模块功能

作者: Athena AI系统
版本: 2.0.0
创建时间: 2026-01-27
"""

import asyncio
import pytest
import uuid
from datetime import datetime, timedelta
from typing import Any

# 测试导入
from core.execution.shared_types import (
    ActionType,
    ExecutionError,
    ResourceRequirement,
    ResourceUsage,
    ResourceType,
    Task,
    TaskExecutionError,
    TaskPriority,
    TaskQueue,
    TaskResult,
    TaskStatus,
    TaskTimeoutError,
    TaskType,
    Workflow,
)
from core.execution import ExecutionEngine


class TestTaskPriority:
    """测试 TaskPriority 枚举"""

    def test_priority_values(self):
        """测试优先级值正确性（值越小优先级越高）"""
        assert TaskPriority.CRITICAL.value == 1
        assert TaskPriority.HIGH.value == 2
        assert TaskPriority.NORMAL.value == 3
        assert TaskPriority.LOW.value == 4
        assert TaskPriority.BACKGROUND.value == 5

    def test_priority_ordering(self):
        """测试优先级排序"""
        priorities = [
            TaskPriority.NORMAL,
            TaskPriority.CRITICAL,
            TaskPriority.LOW,
            TaskPriority.HIGH,
        ]
        sorted_priorities = sorted(priorities, key=lambda p: p.value)
        assert sorted_priorities == [
            TaskPriority.CRITICAL,
            TaskPriority.HIGH,
            TaskPriority.NORMAL,
            TaskPriority.LOW,
        ]


class TestTaskStatus:
    """测试 TaskStatus 枚举"""

    def test_status_values(self):
        """测试状态值"""
        assert TaskStatus.PENDING.value == "pending"
        assert TaskStatus.QUEUED.value == "queued"
        assert TaskStatus.RUNNING.value == "running"
        assert TaskStatus.COMPLETED.value == "completed"
        assert TaskStatus.FAILED.value == "failed"
        assert TaskStatus.CANCELLED.value == "cancelled"
        assert TaskStatus.TIMEOUT.value == "timeout"
        assert TaskStatus.PAUSED.value == "paused"


class TestActionType:
    """测试 ActionType 枚举"""

    def test_action_types(self):
        """测试动作类型"""
        assert ActionType.COMMAND.value == "command"
        assert ActionType.FUNCTION.value == "function"
        assert ActionType.API_CALL.value == "api_call"
        assert ActionType.FILE_OPERATION.value == "file_operation"
        assert ActionType.DATABASE.value == "database"
        assert ActionType.HTTP_REQUEST.value == "http_request"
        assert ActionType.WORKFLOW.value == "workflow"
        assert ActionType.CUSTOM.value == "custom"


class TestTask:
    """测试 Task 类"""

    def test_task_creation_minimal(self):
        """测试创建最小任务"""
        task = Task(
            task_id="test_001",
            name="测试任务",
        )
        assert task.task_id == "test_001"
        assert task.name == "测试任务"
        assert task.priority == TaskPriority.NORMAL
        assert task.status == TaskStatus.PENDING
        assert task.created_at is not None

    def test_task_with_function(self):
        """测试基于函数的任务"""
        async def test_func():
            return "result"

        task = Task(
            task_id="test_002",
            name="函数任务",
            function=test_func,
            args=(1, 2),
            kwargs={"key": "value"},
        )
        assert task.function == test_func
        assert task.args == (1, 2)
        assert task.kwargs == {"key": "value"}

    def test_task_with_action(self):
        """测试基于动作的任务"""
        task = Task(
            task_id="test_003",
            name="动作任务",
            action_type=ActionType.API_CALL,
            action_data={"url": "https://api.example.com"},
        )
        assert task.action_type == ActionType.API_CALL
        assert task.action_data == {"url": "https://api.example.com"}

    def test_task_dependencies(self):
        """测试任务依赖"""
        task = Task(
            task_id="test_004",
            name="有依赖的任务",
            dependencies=["task_001", "task_002"],
        )
        assert len(task.dependencies) == 2
        assert "task_001" in task.dependencies
        assert "task_002" in task.dependencies

    def test_task_can_start(self):
        """测试任务是否可以开始"""
        task = Task(
            task_id="test_005",
            name="测试任务",
            dependencies=["dep_001"],
        )

        completed_tasks = {
            "dep_001": Task(
                task_id="dep_001",
                name="依赖任务",
            )
        }
        completed_tasks["dep_001"].status = TaskStatus.COMPLETED

        assert task.can_start(completed_tasks) is True

    def test_task_cannot_start_without_dependencies(self):
        """测试任务不能在没有完成依赖时开始"""
        task = Task(
            task_id="test_006",
            name="测试任务",
            dependencies=["dep_001"],
        )

        completed_tasks = {}  # 没有完成的依赖

        assert task.can_start(completed_tasks) is False

    def test_task_start(self):
        """测试任务开始"""
        task = Task(task_id="test_007", name="测试任务")
        task.start()
        assert task.status == TaskStatus.RUNNING
        assert task.started_at is not None

    def test_task_complete_success(self):
        """测试任务成功完成"""
        task = Task(task_id="test_008", name="测试任务")
        task.start()
        task.complete(True, "result_data")

        assert task.status == TaskStatus.COMPLETED
        assert task.result == "result_data"
        assert task.completed_at is not None

    def test_task_complete_failure(self):
        """测试任务失败完成"""
        task = Task(task_id="test_009", name="测试任务")
        task.start()
        task.complete(False, error="测试错误")

        assert task.status == TaskStatus.FAILED
        assert task.error == "测试错误"
        assert task.completed_at is not None

    def test_task_retry_within_limit(self):
        """测试任务在限制内重试"""
        task = Task(
            task_id="test_010",
            name="可重试任务",
            max_retries=3,
            retry_count=0,
        )
        task.status = TaskStatus.FAILED

        can_retry = task.retry()
        assert can_retry is True
        assert task.retry_count == 1
        assert task.status == TaskStatus.PENDING

    def test_task_retry_exceeds_limit(self):
        """测试任务超过重试限制"""
        task = Task(
            task_id="test_011",
            name="可重试任务",
            max_retries=3,
            retry_count=3,
        )
        task.status = TaskStatus.FAILED

        can_retry = task.retry()
        assert can_retry is False


class TestTaskQueue:
    """测试 TaskQueue 类"""

    def test_task_queue_creation(self):
        """测试创建任务队列"""
        queue = TaskQueue(max_size=100)
        assert queue.max_size == 100
        assert queue.size() == 0

    def test_task_queue_enqueue(self):
        """测试任务入队"""
        queue = TaskQueue(max_size=10)
        task = Task(task_id="test_001", name="测试任务")

        success = queue.enqueue(task)
        assert success is True
        assert queue.size() == 1

    def test_task_queue_dequeue(self):
        """测试任务出队"""
        queue = TaskQueue(max_size=10)
        task1 = Task(task_id="test_001", name="任务1", priority=TaskPriority.HIGH)
        task2 = Task(task_id="test_002", name="任务2", priority=TaskPriority.LOW)

        queue.enqueue(task1)
        queue.enqueue(task2)

        # 高优先级任务应该先出队
        first_task = queue.dequeue()
        assert first_task.task_id == "test_001"
        assert queue.size() == 1

    def test_task_queue_max_size(self):
        """测试队列最大容量"""
        queue = TaskQueue(max_size=2)

        task1 = Task(task_id="test_001", name="任务1")
        task2 = Task(task_id="test_002", name="任务2")
        task3 = Task(task_id="test_003", name="任务3")

        assert queue.enqueue(task1) is True
        assert queue.enqueue(task2) is True
        assert queue.enqueue(task3) is False  # 超过最大容量

    def test_task_queue_priority_ordering(self):
        """测试队列按优先级排序"""
        queue = TaskQueue(max_size=10)

        # 按随机顺序添加不同优先级的任务
        queue.enqueue(Task(task_id="low", name="低优先级", priority=TaskPriority.LOW))
        queue.enqueue(Task(task_id="critical", name="关键任务", priority=TaskPriority.CRITICAL))
        queue.enqueue(Task(task_id="normal", name="普通任务", priority=TaskPriority.NORMAL))
        queue.enqueue(Task(task_id="high", name="高优先级", priority=TaskPriority.HIGH))

        # 出队顺序应该是：critical, high, normal, low
        order = []
        while queue.size() > 0:
            task = queue.dequeue()
            order.append(task.task_id)

        assert order == ["critical", "high", "normal", "low"]

    def test_task_queue_get_task(self):
        """测试从队列获取任务"""
        queue = TaskQueue(max_size=10)
        task = Task(task_id="test_001", name="测试任务")
        queue.enqueue(task)

        retrieved = queue.get_task("test_001")
        assert retrieved is not None
        assert retrieved.task_id == "test_001"

        # 非存在的任务
        assert queue.get_task("non_existent") is None

    def test_task_queue_clear(self):
        """测试清空队列"""
        queue = TaskQueue(max_size=10)
        queue.enqueue(Task(task_id="test_001", name="任务1"))
        queue.enqueue(Task(task_id="test_002", name="任务2"))

        assert queue.size() == 2
        queue.clear()
        assert queue.size() == 0

    def test_task_queue_summary(self):
        """测试队列摘要"""
        queue = TaskQueue(max_size=10)
        queue.enqueue(Task(task_id="test_001", name="任务1", priority=TaskPriority.HIGH))
        queue.enqueue(Task(task_id="test_002", name="任务2", priority=TaskPriority.NORMAL))

        summary = queue.get_summary()
        assert summary["size"] == 2
        assert summary["max_size"] == 10
        assert "priority_distribution" in summary


class TestTaskResult:
    """测试 TaskResult 类"""

    def test_task_result_creation(self):
        """测试创建任务结果"""
        result = TaskResult(
            task_id="test_001",
            status=TaskStatus.COMPLETED,
            result="success",
        )
        assert result.task_id == "test_001"
        assert result.status == TaskStatus.COMPLETED
        assert result.result == "success"

    def test_task_result_with_metrics(self):
        """测试带指标的任务结果"""
        result = TaskResult(
            task_id="test_002",
            status=TaskStatus.COMPLETED,
            metrics={"cpu_time": 0.5, "memory_mb": 100},
        )
        assert result.metrics["cpu_time"] == 0.5
        assert result.metrics["memory_mb"] == 100


class TestWorkflow:
    """测试 Workflow 类"""

    def test_workflow_creation(self):
        """测试创建工作流"""
        workflow = Workflow(
            id="workflow_001",
            name="测试工作流",
            parallel=False,
            max_concurrent=5,
        )
        assert workflow.id == "workflow_001"
        assert workflow.name == "测试工作流"
        assert workflow.parallel is False
        assert workflow.max_concurrent == 5
        assert len(workflow.tasks) == 0


class TestResourceRequirement:
    """测试 ResourceRequirement 类"""

    def test_resource_requirement_defaults(self):
        """测试资源需求默认值"""
        req = ResourceRequirement()
        assert req.cpu_cores == 1.0
        assert req.memory_mb == 512.0


class TestResourceUsage:
    """测试 ResourceUsage 类"""

    def test_resource_usage_creation(self):
        """测试创建资源使用情况"""
        usage = ResourceUsage(
            cpu_cores=2.5,
            memory_mb=1024.0,
        )
        assert usage.cpu_cores == 2.5
        assert usage.memory_mb == 1024.0
        assert usage.timestamp is not None


class TestExceptions:
    """测试异常类"""

    def test_execution_error(self):
        """测试执行错误"""
        with pytest.raises(ExecutionError):
            raise ExecutionError("测试错误")

    def test_task_execution_error(self):
        """测试任务执行错误"""
        with pytest.raises(TaskExecutionError):
            raise TaskExecutionError("任务执行失败")

    def test_task_timeout_error(self):
        """测试任务超时错误"""
        with pytest.raises(TaskTimeoutError):
            raise TaskTimeoutError("任务超时")


class TestExecutionEngine:
    """测试 ExecutionEngine 类"""

    def test_execution_engine_creation(self):
        """测试创建执行引擎"""
        engine = ExecutionEngine(agent_id="test_agent")
        assert engine.agent_id == "test_agent"
        assert engine.initialized is False

    @pytest.mark.asyncio
    async def test_execution_engine_initialize(self):
        """测试初始化执行引擎"""
        engine = ExecutionEngine(agent_id="test_agent")
        await engine.initialize()
        assert engine.initialized is True

    @pytest.mark.asyncio
    async def test_execution_engine_shutdown(self):
        """测试关闭执行引擎"""
        engine = ExecutionEngine(agent_id="test_agent")
        await engine.initialize()
        await engine.shutdown()
        assert engine.initialized is False

    @pytest.mark.asyncio
    async def test_execution_engine_execute(self):
        """测试执行动作"""
        engine = ExecutionEngine(agent_id="test_agent")
        await engine.initialize()

        result = await engine.execute([])
        assert "results" in result


class TestTypeConsistency:
    """测试类型一致性 - 确保修复后的类型系统工作正常"""

    def test_task_priority_consistency(self):
        """测试 TaskPriority 在整个模块中一致"""
        # 从不同位置导入应该是相同的枚举
        from core.execution.shared_types import TaskPriority as TP1
        from core.execution import TaskPriority as TP2

        assert TP1.CRITICAL == TP2.CRITICAL
        assert TP1.NORMAL == TP2.NORMAL

        # 测试值正确
        assert TP1.CRITICAL.value == 1
        assert TP2.CRITICAL.value == 1

    def test_task_status_consistency(self):
        """测试 TaskStatus 在整个模块中一致"""
        from core.execution.shared_types import TaskStatus as TS1
        from core.execution import TaskStatus as TS2

        assert TS1.PENDING == TS2.PENDING
        assert TS1.COMPLETED == TS2.COMPLETED

    def test_task_class_consistency(self):
        """测试 Task 类在整个模块中一致"""
        from core.execution.shared_types import Task as Task1
        from core.execution import Task as Task2

        task1 = Task1(task_id="test", name="测试")
        task2 = Task2(task_id="test", name="测试")

        # 两个类应该是同一个类
        assert type(task1) == type(task2)
        assert task1.priority == task2.priority
        assert task1.status == task2.status


@pytest.mark.integration
class TestTaskExecutionIntegration:
    """集成测试 - 测试完整的任务执行流程"""

    @pytest.mark.asyncio
    async def test_complete_task_lifecycle(self):
        """测试完整的任务生命周期"""
        # 创建任务
        task = Task(
            task_id="integration_001",
            name="集成测试任务",
            priority=TaskPriority.HIGH,
        )

        # 初始状态
        assert task.status == TaskStatus.PENDING

        # 开始任务
        task.start()
        assert task.status == TaskStatus.RUNNING
        assert task.started_at is not None

        # 模拟执行
        await asyncio.sleep(0.1)

        # 完成任务
        task.complete(True, "integration_result")
        assert task.status == TaskStatus.COMPLETED
        assert task.result == "integration_result"
        assert task.completed_at is not None

        # 验证执行时间被记录
        assert "execution_time" in task.metadata

    @pytest.mark.asyncio
    async def test_task_with_dependencies_execution(self):
        """测试带依赖的任务执行"""
        # 创建依赖任务
        dep_task = Task(
            task_id="dep_001",
            name="依赖任务",
        )
        dep_task.start()
        dep_task.complete(True, "dep_result")
        dep_task.status = TaskStatus.COMPLETED

        # 创建主任务
        main_task = Task(
            task_id="main_001",
            name="主任务",
            dependencies=["dep_001"],
        )

        completed_tasks = {"dep_001": dep_task}

        # 验证可以开始
        assert main_task.can_start(completed_tasks) is True

    @pytest.mark.asyncio
    async def test_task_retry_workflow(self):
        """测试任务重试工作流"""
        task = Task(
            task_id="retry_001",
            name="重试任务",
            max_retries=3,
        )

        # 第一次失败
        task.start()
        task.complete(False, error="第一次失败")
        task.status = TaskStatus.FAILED

        # 重试 1
        assert task.retry() is True
        assert task.retry_count == 1
        assert task.status == TaskStatus.PENDING

        # 重试 2
        task.status = TaskStatus.FAILED
        assert task.retry() is True
        assert task.retry_count == 2

        # 重试 3
        task.status = TaskStatus.FAILED
        assert task.retry() is True
        assert task.retry_count == 3

        # 超过重试限制
        task.status = TaskStatus.FAILED
        assert task.retry() is False


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
