"""
TaskScheduler单元测试 - 额外测试以提高覆盖率
"""


import pytest

from core.agents.task_tool.models import TaskStatus


class MockBackgroundTaskManager:
    """Mock BackgroundTaskManager - 支持更多功能"""

    def __init__(self, max_workers=10):
        self.max_workers = max_workers
        self.submitted_tasks = []
        self._tasks = {}
        self._is_shutdown = False

    def submit(self, func, args=None, kwargs=None, agent_id=None, input_data=None):
        """模拟提交任务"""
        from concurrent.futures import Future

        from core.agents.task_tool.models import BackgroundTask

        if self._is_shutdown:
            raise RuntimeError("BackgroundTaskManager has been shut down")

        task_id = str(len(self.submitted_tasks))
        self.submitted_tasks.append(
            {
                "func": func,
                "args": args,
                "kwargs": kwargs,
                "agent_id": agent_id,
                "input_data": input_data,
                "task_id": task_id,
            }
        )

        # 创建模拟的Future
        future = Future()
        future.set_result("mock_result")

        # 创建BackgroundTask
        task = BackgroundTask(
            task_id=task_id,
            status=TaskStatus.PENDING,
            future=future,
            agent_id=agent_id or "unknown",
            input_data=input_data,
        )

        self._tasks[task_id] = task
        return task

    def get_task(self, task_id):
        """获取任务"""
        return self._tasks.get(task_id)

    def get_running_tasks(self):
        """获取运行中的任务"""
        return [t for t in self._tasks.values() if t.status == TaskStatus.RUNNING]

    def cancel(self, task_id):
        """取消任务"""
        task = self._tasks.get(task_id)
        if task:
            task.update_status(TaskStatus.CANCELLED)
            return True
        return False


def test_task_scheduler_start_stop():
    """测试调度器的启动和停止"""
    from core.task.task_scheduler import TaskScheduler

    bg_manager = MockBackgroundTaskManager()
    scheduler = TaskScheduler(bg_manager)

    # 启动调度器
    scheduler.start()
    assert scheduler._running is True
    assert scheduler._scheduler_thread is not None

    # 停止调度器
    scheduler.stop()
    assert scheduler._running is False


def test_task_scheduler_start_already_running():
    """测试启动已运行的调度器"""
    from core.task.task_scheduler import TaskScheduler

    bg_manager = MockBackgroundTaskManager()
    scheduler = TaskScheduler(bg_manager)

    # 第一次启动
    scheduler.start()
    assert scheduler._running is True

    # 第二次启动（应该警告但不抛出异常）
    scheduler.start()
    assert scheduler._running is True

    # 清理
    scheduler.stop()


def test_task_scheduler_shutdown_manager():
    """测试关闭管理器后调度任务"""
    from core.task.task_scheduler import TaskScheduler

    bg_manager = MockBackgroundTaskManager()
    scheduler = TaskScheduler(bg_manager)

    # 关闭后台管理器
    bg_manager._is_shutdown = True

    # 尝试调度任务（应该抛出异常）
    with pytest.raises(RuntimeError, match="has been shut down"):
        scheduler.schedule_task(lambda: "task", priority=5)


def test_task_scheduler_get_task_not_found():
    """测试获取不存在的任务"""
    from core.task.task_scheduler import TaskScheduler

    bg_manager = MockBackgroundTaskManager()
    scheduler = TaskScheduler(bg_manager)

    # 获取不存在的任务
    task = scheduler.get_task("non_existent_task_id")
    assert task is None


def test_task_scheduler_cancel_task_in_queue():
    """测试取消队列中的任务"""
    from core.task.task_scheduler import TaskScheduler

    bg_manager = MockBackgroundTaskManager()
    scheduler = TaskScheduler(bg_manager)

    # 调度任务
    task = scheduler.schedule_task(lambda: "task", priority=5)

    # 取消任务
    result = scheduler.cancel_task(task.task_id)
    assert result is True

    # 验证任务状态
    updated_task = scheduler.get_task(task.task_id)
    assert updated_task.status == TaskStatus.CANCELLED


def test_task_scheduler_cancel_non_existent_task():
    """测试取消不存在的任务"""
    from core.task.task_scheduler import TaskScheduler

    bg_manager = MockBackgroundTaskManager()
    scheduler = TaskScheduler(bg_manager)

    # 尝试取消不存在的任务
    result = scheduler.cancel_task("non_existent_task_id")
    assert result is False


def test_task_scheduler_process_next_task_no_tasks():
    """测试处理下一个任务（没有待处理任务）"""
    from core.task.task_scheduler import TaskScheduler

    bg_manager = MockBackgroundTaskManager()
    scheduler = TaskScheduler(bg_manager)
    scheduler._max_concurrent = 10

    # 处理下一个任务（没有待处理任务）
    scheduler._process_next_task()

    # 验证没有运行中的任务
    running = scheduler.get_running_tasks()
    assert len(running) == 0


def test_task_scheduler_process_next_task_max_concurrent_reached():
    """测试处理下一个任务（已达到最大并发数）"""
    from core.task.task_scheduler import TaskScheduler

    bg_manager = MockBackgroundTaskManager()
    scheduler = TaskScheduler(bg_manager)
    scheduler._max_concurrent = 0  # 设置为0，表示不允许并发

    # 调度一个任务
    scheduler.schedule_task(lambda: "task", priority=5)

    # 处理下一个任务（应该不执行，因为已达到最大并发数）
    scheduler._process_next_task()

    # 验证任务仍在队列中
    pending = scheduler.get_pending_queue()
    assert len(pending) == 1


def test_task_scheduler_get_pending_queue_empty():
    """测试获取空的待处理队列"""
    from core.task.task_scheduler import TaskScheduler

    bg_manager = MockBackgroundTaskManager()
    scheduler = TaskScheduler(bg_manager)

    # 获取空的队列
    pending = scheduler.get_pending_queue()
    assert len(pending) == 0


def test_scheduled_task_comparison():
    """测试调度任务的比较（基于优先级）"""
    from concurrent.futures import Future

    from core.agents.task_tool.models import BackgroundTask, TaskStatus
    from core.task.task_scheduler import ScheduledTask

    # 创建模拟任务
    future1 = Future()
    future1.set_result("result1")
    task1 = BackgroundTask(
        task_id="task1",
        status=TaskStatus.PENDING,
        future=future1,
        agent_id="agent1",
    )

    future2 = Future()
    future2.set_result("result2")
    task2 = BackgroundTask(
        task_id="task2",
        status=TaskStatus.PENDING,
        future=future2,
        agent_id="agent2",
    )

    # 创建调度任务
    scheduled1 = ScheduledTask(priority=1, task_id="task1", task=task1)
    scheduled2 = ScheduledTask(priority=10, task_id="task2", task=task2)

    # 验证比较（优先级高的应该"更小"）
    assert scheduled1 < scheduled2  # priority=1 < priority=10（数字小的在前）
    assert scheduled2 > scheduled1


def test_task_scheduler_with_real_timeout():
    """测试带超时的任务调度（使用真实时间）"""
    from core.task.task_scheduler import TaskScheduler

    bg_manager = MockBackgroundTaskManager()
    scheduler = TaskScheduler(bg_manager)

    def quick_task():
        return "quick"

    # 调度快速任务
    task = scheduler.schedule_task(quick_task, priority=5, timeout=10.0)

    assert task is not None
    assert task.task_id is not None


def test_task_scheduler_multiple_tasks_priority_order():
    """测试多个任务的优先级顺序"""
    from core.task.task_scheduler import TaskScheduler

    bg_manager = MockBackgroundTaskManager()
    scheduler = TaskScheduler(bg_manager)

    # 调度多个不同优先级的任务
    task1 = scheduler.schedule_task(lambda: "low", priority=1)
    task2 = scheduler.schedule_task(lambda: "high", priority=10)
    task3 = scheduler.schedule_task(lambda: "medium", priority=5)
    task4 = scheduler.schedule_task(lambda: "very_high", priority=9)
    task5 = scheduler.schedule_task(lambda: "very_low", priority=2)

    # 获取待处理队列
    pending = scheduler.get_pending_queue()

    # 验证顺序（高优先级在前）
    assert pending[0].task_id == task2.task_id  # priority 10
    assert pending[1].task_id == task4.task_id  # priority 9
    assert pending[2].task_id == task3.task_id  # priority 5
    assert pending[3].task_id == task5.task_id  # priority 2
    assert pending[4].task_id == task1.task_id  # priority 1
