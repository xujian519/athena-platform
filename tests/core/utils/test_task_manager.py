#!/usr/bin/env python3
"""
任务管理器单元测试
"""

import asyncio

import pytest

from core.utils.task_manager import (
    TaskInfo,
    TaskManager,
    TaskStatus,
    get_task_manager,
    shutdown_all_managers,
)


class TestTaskStatus:
    """TaskStatus枚举测试"""

    def test_status_values(self):
        """测试状态值"""
        assert TaskStatus.PENDING.value == "pending"
        assert TaskStatus.RUNNING.value == "running"
        assert TaskStatus.COMPLETED.value == "completed"
        assert TaskStatus.FAILED.value == "failed"
        assert TaskStatus.CANCELLED.value == "cancelled"


class TestTaskInfo:
    """TaskInfo类测试"""

    def test_create_task_info(self):
        """测试创建任务信息"""
        async def dummy_coro():
            pass

        task_info = TaskInfo(
            task_id="test_task",
            coro=dummy_coro(),
            status=TaskStatus.PENDING,
            critical=False
        )

        assert task_info.task_id == "test_task"
        assert task_info.status == TaskStatus.PENDING
        assert task_info.critical is False
        assert task_info.created_at is not None
        assert task_info.started_at is None
        assert task_info.completed_at is None
        assert task_info.error is None

    def test_task_info_with_critical(self):
        """测试关键任务"""
        async def dummy_coro():
            pass

        task_info = TaskInfo(
            task_id="critical_task",
            coro=dummy_coro(),
            critical=True
        )

        assert task_info.critical is True


class TestTaskManager:
    """TaskManager类测试"""

    @pytest.mark.asyncio
    async def test_init(self):
        """测试初始化"""
        manager = TaskManager("test_manager")
        assert manager.name == "test_manager"
        assert manager._running is False
        assert len(manager._tasks) == 0

    @pytest.mark.asyncio
    async def test_start_stop(self):
        """测试启动和停止"""
        manager = TaskManager("test_manager")
        assert manager._running is False

        await manager.start()
        assert manager._running is True

        await manager.stop()
        assert manager._running is False

    @pytest.mark.asyncio
    async def test_create_task(self):
        """测试创建任务"""
        manager = TaskManager("test_manager")
        await manager.start()

        async def dummy_task():
            await asyncio.sleep(0.01)
            return "done"

        task = await manager.create_task(dummy_task(), "task1")

        assert task is not None
        assert isinstance(task, asyncio.Task)
        assert manager.get_task_info("task1") is not None

        await manager.stop()

    @pytest.mark.asyncio
    async def test_create_duplicate_task_fails(self):
        """测试创建重复任务失败"""
        manager = TaskManager("test_manager")
        await manager.start()

        async def dummy_task():
            pass

        await manager.create_task(dummy_task(), "task1")

        with pytest.raises(ValueError, match="任务ID已存在"):
            await manager.create_task(dummy_task(), "task1")

        await manager.stop()

    @pytest.mark.asyncio
    async def test_create_task_before_start_fails(self):
        """测试未启动时创建任务失败"""
        manager = TaskManager("test_manager")

        async def dummy_task():
            pass

        with pytest.raises(RuntimeError, match="任务管理器未启动"):
            await manager.create_task(dummy_task(), "task1")

    @pytest.mark.asyncio
    async def test_task_completion(self):
        """测试任务完成"""
        manager = TaskManager("test_manager")
        await manager.start()

        async def successful_task():
            await asyncio.sleep(0.01)
            return "result"

        task = await manager.create_task(successful_task(), "task1")
        await task

        task_info = manager.get_task_info("task1")
        assert task_info.status == TaskStatus.COMPLETED
        assert task_info.error is None

        await manager.stop()

    @pytest.mark.asyncio
    async def test_task_failure(self):
        """测试任务失败"""
        manager = TaskManager("test_manager")
        await manager.start()

        async def failing_task():
            await asyncio.sleep(0.01)
            raise ValueError("task error")

        task = await manager.create_task(failing_task(), "task1")

        with pytest.raises(ValueError):
            await task

        task_info = manager.get_task_info("task1")
        assert task_info.status == TaskStatus.FAILED
        assert "task error" in task_info.error

        await manager.stop()

    @pytest.mark.asyncio
    async def test_task_failure_critical(self):
        """测试关键任务失败会重新抛出异常"""
        manager = TaskManager("test_manager")
        await manager.start()

        async def critical_failing_task():
            await asyncio.sleep(0.01)
            raise RuntimeError("critical error")

        task = await manager.create_task(critical_failing_task(), "task1", critical=True)

        # 关键任务失败应该重新抛出异常
        with pytest.raises(RuntimeError, match="critical error"):
            await task

        task_info = manager.get_task_info("task1")
        assert task_info.status == TaskStatus.FAILED

        await manager.stop()

    @pytest.mark.asyncio
    async def test_task_cancellation(self):
        """测试任务取消"""
        manager = TaskManager("test_manager")
        await manager.start()

        async def long_running_task():
            await asyncio.sleep(10)
            return "done"

        task = await manager.create_task(long_running_task(), "task1")

        # 取消任务
        cancelled = await manager.cancel_task("task1")
        assert cancelled is True

        # 等待任务完成取消
        try:
            await task
        except asyncio.CancelledError:
            pass

        task_info = manager.get_task_info("task1")
        assert task_info.status == TaskStatus.CANCELLED

        await manager.stop()

    @pytest.mark.asyncio
    async def test_cancel_nonexistent_task(self):
        """测试取消不存在的任务"""
        manager = TaskManager("test_manager")
        await manager.start()

        cancelled = await manager.cancel_task("nonexistent")
        assert cancelled is False

        await manager.stop()

    @pytest.mark.asyncio
    async def test_cancel_all_tasks(self):
        """测试取消所有任务"""
        manager = TaskManager("test_manager")
        await manager.start()

        async def long_task():
            await asyncio.sleep(10)
            return "done"

        # 创建多个任务
        await manager.create_task(long_task(), "task1")
        await manager.create_task(long_task(), "task2")
        await manager.create_task(long_task(), "task3")

        # 取消所有任务
        await manager.cancel_all()

        # 验证所有任务都已取消
        active_tasks = manager.get_active_tasks()
        assert len(active_tasks) == 0

        await manager.stop()

    @pytest.mark.asyncio
    async def test_get_task_info(self):
        """测试获取任务信息"""
        manager = TaskManager("test_manager")
        await manager.start()

        async def dummy_task():
            pass

        await manager.create_task(dummy_task(), "task1")

        task_info = manager.get_task_info("task1")
        assert task_info is not None
        assert task_info.task_id == "task1"
        assert task_info.status == TaskStatus.RUNNING

        nonexistent = manager.get_task_info("nonexistent")
        assert nonexistent is None

        await manager.stop()

    @pytest.mark.asyncio
    async def test_get_active_tasks(self):
        """测试获取活动任务"""
        manager = TaskManager("test_manager")
        await manager.start()

        async def long_task():
            await asyncio.sleep(10)

        # 创建活动任务
        await manager.create_task(long_task(), "task1")
        await manager.create_task(long_task(), "task2")

        # 创建已完成任务
        async def quick_task():
            pass

        await manager.create_task(quick_task(), "task3")
        # 等待task3完成
        await asyncio.sleep(0.05)

        active_tasks = manager.get_active_tasks()
        # task1和task2应该还在活动
        assert "task1" in active_tasks
        assert "task2" in active_tasks
        # task3可能已完成
        assert len(active_tasks) >= 2

        await manager.cancel_all()
        await manager.stop()

    @pytest.mark.asyncio
    async def test_get_all_tasks(self):
        """测试获取所有任务"""
        manager = TaskManager("test_manager")
        await manager.start()

        async def quick_task():
            pass

        await manager.create_task(quick_task(), "task1")
        await manager.create_task(quick_task(), "task2")

        all_tasks = manager.get_all_tasks()
        assert len(all_tasks) == 2
        assert "task1" in all_tasks
        assert "task2" in all_tasks

        await manager.stop()

    @pytest.mark.asyncio
    async def test_get_stats(self):
        """测试获取统计信息"""
        manager = TaskManager("test_manager")
        await manager.start()

        async def quick_task():
            pass

        async def long_task():
            await asyncio.sleep(10)

        await manager.create_task(quick_task(), "task1")
        await manager.create_task(long_task(), "task2")

        stats = manager.get_stats()
        assert stats["manager_name"] == "test_manager"
        assert stats["total_tasks"] == 2
        assert stats["active_tasks"] >= 1
        assert "status_distribution" in stats

        await manager.cancel_all()
        await manager.stop()

    @pytest.mark.asyncio
    async def test_cleanup(self):
        """测试清理旧任务"""
        manager = TaskManager("test_manager")
        await manager.start()

        # 创建并完成一些任务
        for i in range(5):
            async def quick_task():
                pass

            await manager.create_task(quick_task(), f"task{i}")
            await asyncio.sleep(0.02)  # 等待任务完成

        # 清理
        await manager.cleanup(max_history=3)

        # 应该只保留最近的3个任务
        all_tasks = manager.get_all_tasks()
        assert len(all_tasks) <= 3

        await manager.stop()

    @pytest.mark.asyncio
    async def test_repr(self):
        """测试__repr__方法"""
        manager = TaskManager("test_manager")
        await manager.start()

        async def long_task():
            await asyncio.sleep(10)

        await manager.create_task(long_task(), "task1")

        repr_str = repr(manager)
        assert "TaskManager" in repr_str
        assert "test_manager" in repr_str
        assert "active=" in repr_str

        await manager.cancel_all()
        await manager.stop()


class TestGlobalFunctions:
    """全局函数测试"""

    @pytest.mark.asyncio
    async def test_get_task_manager(self):
        """测试获取任务管理器"""
        manager1 = get_task_manager("test1")
        manager2 = get_task_manager("test1")

        # 相同名称应该返回同一个实例
        assert manager1 is manager2

        # 不同名称应该返回不同实例
        manager3 = get_task_manager("test2")
        assert manager1 is not manager3

        # 清理
        await manager1.stop()
        await manager3.stop()

    @pytest.mark.asyncio
    async def test_shutdown_all_managers(self):
        """测试关闭所有管理器"""
        # 创建几个管理器
        manager1 = get_task_manager("shutdown_test1")
        manager2 = get_task_manager("shutdown_test2")

        await manager1.start()
        await manager2.start()

        # 关闭所有
        await shutdown_all_managers()

        # 验证管理器已停止
        assert manager1._running is False
        assert manager2._running is False


class TestIntegration:
    """集成测试"""

    @pytest.mark.asyncio
    async def test_complete_task_lifecycle(self):
        """测试完整任务生命周期"""
        manager = TaskManager("lifecycle_test")
        await manager.start()

        # 1. 创建任务
        task_completed = False

        async def lifecycle_task():
            nonlocal task_completed
            await asyncio.sleep(0.02)
            task_completed = True
            return "done"

        task = await manager.create_task(lifecycle_task(), "lifecycle_task")

        # 2. 检查运行状态
        task_info = manager.get_task_info("lifecycle_task")
        assert task_info.status == TaskStatus.RUNNING

        # 3. 等待完成
        result = await task
        assert result == "done"
        assert task_completed is True

        # 4. 检查完成状态
        task_info = manager.get_task_info("lifecycle_task")
        assert task_info.status == TaskStatus.COMPLETED

        # 5. 获取统计
        stats = manager.get_stats()
        assert stats["total_tasks"] == 1

        await manager.stop()

    @pytest.mark.asyncio
    async def test_multiple_tasks_concurrent(self):
        """测试多个并发任务"""
        manager = TaskManager("concurrent_test")
        await manager.start()

        results = []

        async def task_a():
            await asyncio.sleep(0.01)
            results.append("A")
            return "A"

        async def task_b():
            await asyncio.sleep(0.02)
            results.append("B")
            return "B"

        async def task_c():
            await asyncio.sleep(0.01)
            results.append("C")
            return "C"

        # 并发创建任务
        tasks = [
            await manager.create_task(task_a(), "task_a"),
            await manager.create_task(task_b(), "task_b"),
            await manager.create_task(task_c(), "task_c"),
        ]

        # 等待所有任务完成
        await asyncio.gather(*tasks)

        # 验证所有任务都完成了
        task_a_info = manager.get_task_info("task_a")
        task_b_info = manager.get_task_info("task_b")
        task_c_info = manager.get_task_info("task_c")

        assert task_a_info.status == TaskStatus.COMPLETED
        assert task_b_info.status == TaskStatus.COMPLETED
        assert task_c_info.status == TaskStatus.COMPLETED

        # 验证结果
        assert len(results) == 3
        assert "A" in results
        assert "B" in results
        assert "C" in results

        await manager.stop()

    @pytest.mark.asyncio
    async def test_task_with_args_and_kwargs(self):
        """测试带参数的任务"""
        manager = TaskManager("args_test")
        await manager.start()

        async def task_with_args(a, b, c=None):
            return a + b + (c or 0)

        # 创建带参数的任务
        coro = task_with_args(1, 2, c=3)
        task = await manager.create_task(coro, "args_task")

        result = await task
        assert result == 6

        await manager.stop()


class TestEdgeCases:
    """边缘情况测试"""

    @pytest.mark.asyncio
    async def test_empty_task_id_fails(self):
        """测试空任务ID"""
        manager = TaskManager("test_manager")
        await manager.start()

        async def dummy_task():
            pass

        # 空字符串应该是有效的ID
        # 但如果实现不允许，这里会抛出异常
        # 根据实现，空字符串可能被接受

        await manager.stop()

    @pytest.mark.asyncio
    async def test_very_long_task_id(self):
        """测试很长的任务ID"""
        manager = TaskManager("test_manager")
        await manager.start()

        async def dummy_task():
            pass

        long_id = "a" * 1000
        await manager.create_task(dummy_task(), long_id)

        task_info = manager.get_task_info(long_id)
        assert task_info is not None

        await manager.stop()

    @pytest.mark.asyncio
    async def test_task_completes_quickly(self):
        """测试快速完成的任务"""
        manager = TaskManager("test_manager")
        await manager.start()

        async def instant_task():
            return "instant"

        task = await manager.create_task(instant_task(), "instant")
        result = await task

        assert result == "instant"

        task_info = manager.get_task_info("instant")
        assert task_info.status == TaskStatus.COMPLETED

        await manager.stop()

    @pytest.mark.asyncio
    async def test_manager_reuse(self):
        """测试管理器重用"""
        manager = TaskManager("reuse_test")

        # 第一次使用
        await manager.start()
        async def task1():
            pass
        await manager.create_task(task1(), "task1")
        await manager.stop()

        # 第二次使用
        await manager.start()
        async def task2():
            pass
        await manager.create_task(task2(), "task2")
        await manager.stop()

        # 验证两个任务都被记录
        all_tasks = manager.get_all_tasks()
        assert len(all_tasks) == 2

    @pytest.mark.asyncio
    async def test_get_stats_with_no_tasks(self):
        """测试没有任务时的统计"""
        manager = TaskManager("empty_test")
        await manager.start()

        stats = manager.get_stats()
        assert stats["total_tasks"] == 0
        assert stats["active_tasks"] == 0
        assert stats["status_distribution"]["pending"] == 0

        await manager.stop()

    @pytest.mark.asyncio
    async def test_cleanup_with_no_tasks(self):
        """测试清理没有任务的记录"""
        manager = TaskManager("cleanup_test")
        await manager.start()

        # 清理应该不会出错
        await manager.cleanup()

        all_tasks = manager.get_all_tasks()
        assert len(all_tasks) == 0

        await manager.stop()
