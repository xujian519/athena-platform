"""
TaskScheduler单元测试
"""



from core.framework.agents.task_tool.models import TaskStatus


class MockBackgroundTaskManager:
    """Mock BackgroundTaskManager"""

    def __init__(self, max_workers=10):
        self.max_workers = max_workers
        self.submitted_tasks = []
        self._tasks = {}

    def submit(self, func, args=None, kwargs=None, agent_id=None, input_data=None):
        """模拟提交任务"""
        from concurrent.futures import Future

        from core.framework.agents.task_tool.models import BackgroundTask

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


def test_task_scheduler_initialization():
    """测试TaskScheduler初始化"""
    from core.task.task_scheduler import TaskScheduler

    bg_manager = MockBackgroundTaskManager()
    scheduler = TaskScheduler(bg_manager)

    assert scheduler is not None
    assert scheduler._background_manager == bg_manager


def test_schedule_task_basic():
    """测试基本任务调度"""
    from core.task.task_scheduler import TaskScheduler

    bg_manager = MockBackgroundTaskManager()
    scheduler = TaskScheduler(bg_manager)

    def mock_task():
        return "task_completed"

    # 调度任务
    task = scheduler.schedule_task(mock_task, priority=5)

    assert task is not None
    assert task.task_id == "0"


def test_schedule_task_with_priority():
    """测试带优先级的任务调度"""
    from core.task.task_scheduler import TaskScheduler

    bg_manager = MockBackgroundTaskManager()
    scheduler = TaskScheduler(bg_manager)

    # 提交不同优先级的任务
    task1 = scheduler.schedule_task(lambda: "low", priority=1)
    task2 = scheduler.schedule_task(lambda: "high", priority=10)
    task3 = scheduler.schedule_task(lambda: "medium", priority=5)

    # 获取待处理任务队列
    queue = scheduler.get_pending_queue()

    # 验证优先级顺序（高优先级在前）
    assert queue[0].task_id == task2.task_id  # priority 10
    assert queue[1].task_id == task3.task_id  # priority 5
    assert queue[2].task_id == task1.task_id  # priority 1


def test_schedule_task_with_timeout():
    """测试带超时的任务调度"""
    from core.task.task_scheduler import TaskScheduler

    bg_manager = MockBackgroundTaskManager()
    scheduler = TaskScheduler(bg_manager)

    def slow_task():
        import time

        time.sleep(2)
        return "completed"

    # 调度带超时的任务
    task = scheduler.schedule_task(
        slow_task,
        priority=5,
        timeout=1.0,  # 1秒超时
    )

    assert task is not None
    # 注意：由于是Mock，这里不会真正超时


def test_cancel_task():
    """测试取消任务"""
    from core.task.task_scheduler import TaskScheduler

    bg_manager = MockBackgroundTaskManager()
    scheduler = TaskScheduler(bg_manager)

    def mock_task():
        return "task_result"

    # 调度任务
    task = scheduler.schedule_task(mock_task, priority=5)

    # 取消任务
    result = scheduler.cancel_task(task.task_id)

    assert result is True


def test_get_pending_queue():
    """测试获取待处理队列"""
    from core.task.task_scheduler import TaskScheduler

    bg_manager = MockBackgroundTaskManager()
    scheduler = TaskScheduler(bg_manager)

    # 调度多个任务
    scheduler.schedule_task(lambda: "task1", priority=1)
    scheduler.schedule_task(lambda: "task2", priority=10)
    scheduler.schedule_task(lambda: lambda: "task3", priority=5)

    # 获取待处理队列
    queue = scheduler.get_pending_queue()

    assert len(queue) == 3


def test_get_running_tasks():
    """测试获取运行中的任务"""
    from core.task.task_scheduler import TaskScheduler

    bg_manager = MockBackgroundTaskManager()
    scheduler = TaskScheduler(bg_manager)

    # 获取运行中的任务（初始应该为空）
    running_tasks = scheduler.get_running_tasks()

    assert len(running_tasks) == 0


def test_task_timeout_handling():
    """测试任务超时处理"""
    from core.task.task_scheduler import TaskScheduler

    bg_manager = MockBackgroundTaskManager()
    scheduler = TaskScheduler(bg_manager)

    def timeout_task():
        import time

        time.sleep(5)
        return "never_reached"

    # 调度任务并设置超时
    task = scheduler.schedule_task(timeout_task, priority=5, timeout=1.0)

    # 获取任务状态
    scheduled_task = scheduler.get_task(task.task_id)

    assert scheduled_task is not None


def test_concurrent_task_limit():
    """测试并发任务限制"""
    from core.task.task_scheduler import TaskScheduler

    bg_manager = MockBackgroundTaskManager(max_workers=2)
    scheduler = TaskScheduler(bg_manager, max_concurrent=2)

    # 提交多个任务
    tasks = []
    for i in range(5):
        task = scheduler.schedule_task(lambda i=i: f"task_{i}", priority=i)
        tasks.append(task)

    assert len(tasks) == 5
