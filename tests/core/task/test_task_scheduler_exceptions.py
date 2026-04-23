"""
TaskScheduler异常处理测试
"""




def test_task_scheduler_future_timeout():
    """测试Future超时异常处理"""
    from concurrent.futures import Future

    from core.task.task_scheduler import TaskScheduler

    # 创建一个模拟超时的Future
    from core.framework.agents.task_tool.models import BackgroundTask, TaskStatus

    class TimeoutMockBackgroundTaskManager:
        def __init__(self):
            self.submitted_tasks = []
            self._tasks = {}
            self.task_count = 0

        def submit(self, func, args=None, kwargs=None, agent_id=None, input_data=None):
            self.task_count += 1
            task_id = str(self.task_count)

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

            # 创建一个会超时的Future
            future = Future()

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
            return self._tasks.get(task_id)

        def get_running_tasks(self):
            return []

        def cancel(self, task_id):
            task = self._tasks.get(task_id)
            if task:
                task.update_status(TaskStatus.CANCELLED)
                return True
            return False

    bg_manager = TimeoutMockBackgroundTaskManager()
    scheduler = TaskScheduler(bg_manager, max_concurrent=10)

    # 调度一个带超时的任务
    task = scheduler.schedule_task(lambda: "task", priority=5, timeout=0.001)

    # 手动调用_process_next_task来触发超时异常
    scheduler._process_next_task()

    # 验证任务状态变为FAILED
    updated_task = scheduler.get_task(task.task_id)
    assert updated_task.status == TaskStatus.FAILED


def test_task_scheduler_future_exception():
    """测试Future执行异常处理"""
    from concurrent.futures import Future

    from core.task.task_scheduler import TaskScheduler

    # 创建一个会抛出异常的Future
    from core.framework.agents.task_tool.models import BackgroundTask, TaskStatus

    class ExceptionMockBackgroundTaskManager:
        def __init__(self):
            self.submitted_tasks = []
            self._tasks = {}
            self.task_count = 0

        def submit(self, func, args=None, kwargs=None, agent_id=None, input_data=None):
            self.task_count += 1
            task_id = str(self.task_count)

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

            # 创建一个会抛出异常的Future
            future = Future()
            future.set_exception(ValueError("Simulated exception"))

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
            return self._tasks.get(task_id)

        def get_running_tasks(self):
            return []

        def cancel(self, task_id):
            task = self._tasks.get(task_id)
            if task:
                task.update_status(TaskStatus.CANCELLED)
                return True
            return False

    bg_manager = ExceptionMockBackgroundTaskManager()
    scheduler = TaskScheduler(bg_manager, max_concurrent=10)

    # 调度一个任务
    task = scheduler.schedule_task(lambda: "task", priority=5)

    # 手动调用_process_next_task来触发异常
    scheduler._process_next_task()

    # 验证任务状态变为FAILED
    updated_task = scheduler.get_task(task.task_id)
    assert updated_task.status == TaskStatus.FAILED
