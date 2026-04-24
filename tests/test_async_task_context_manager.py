#!/usr/bin/env python3
"""异步任务上下文管理器单元测试 - 验证异步I/O性能优化"""

import pytest
import asyncio
import time
from pathlib import Path
from core.context_management.async_task_context_manager import (
    AsyncTaskContextManager,
    TaskContext,
    ContextStatus,
    create_task_context,
    resume_task_context,
)


@pytest.fixture
async def manager():
    """创建异步管理器实例"""
    # 使用临时目录
    temp_path = Path("/tmp/test_async_contexts")
    manager = AsyncTaskContextManager(storage_path=temp_path)
    yield manager
    # 清理
    import shutil
    if temp_path.exists():
        shutil.rmtree(temp_path)


@pytest.mark.asyncio
class TestAsyncTaskContextManager:
    """异步任务上下文管理器测试套件"""

    async def test_create_context(self, manager: AsyncTaskContextManager):
        """测试创建上下文"""
        context = await manager.create_context(
            task_id="test_001",
            task_description="测试任务",
            total_steps=5
        )

        assert context.task_id == "test_001"
        assert context.task_description == "测试任务"
        assert context.total_steps == 5
        assert context.status == ContextStatus.ACTIVE
        assert len(context.steps) == 0

    async def test_save_and_load_context(self, manager: AsyncTaskContextManager):
        """测试保存和加载上下文"""
        # 创建并保存
        context = await manager.create_context(
            task_id="test_002",
            task_description="保存测试"
        )

        # 加载
        loaded = await manager.load_context("test_002")

        assert loaded is not None
        assert loaded.task_id == context.task_id
        assert loaded.task_description == context.task_description
        assert loaded.status == context.status

    async def test_update_step(self, manager: AsyncTaskContextManager):
        """测试更新步骤"""
        # 创建上下文
        await manager.create_context(
            task_id="test_003",
            task_description="步骤测试",
            total_steps=3
        )

        # 更新步骤
        success = await manager.update_step(
            task_id="test_003",
            step_id="step_1",
            step_name="第一步",
            status="completed",
            input_data={"param": "value"},
            output_data={"result": "success"}
        )

        assert success is True

        # 验证
        context = await manager.load_context("test_003")
        assert len(context.steps) == 1
        assert context.steps[0].step_id == "step_1"
        assert context.steps[0].status == "completed"
        assert context.steps[0].input_data == {"param": "value"}

    async def test_global_variables(self, manager: AsyncTaskContextManager):
        """测试全局变量管理"""
        await manager.create_context(
            task_id="test_004",
            task_description="变量测试"
        )

        # 设置变量
        success = await manager.set_variable("test_004", "key1", "value1")
        assert success is True

        # 获取变量
        value = await manager.get_variable("test_004", "key1")
        assert value == "value1"

        # 获取不存在的变量
        default = await manager.get_variable("test_004", "nonexistent", "default_value")
        assert default == "default_value"

    async def test_set_status(self, manager: AsyncTaskContextManager):
        """测试设置状态"""
        await manager.create_context(
            task_id="test_005",
            task_description="状态测试"
        )

        # 设置为完成
        success = await manager.set_status("test_005", ContextStatus.COMPLETED)
        assert success is True

        # 验证
        context = await manager.load_context("test_005")
        assert context.status == ContextStatus.COMPLETED

    async def test_get_progress(self, manager: AsyncTaskContextManager):
        """测试获取进度"""
        await manager.create_context(
            task_id="test_006",
            task_description="进度测试",
            total_steps=10
        )

        # 添加5个完成的步骤
        for i in range(5):
            await manager.update_step(
                task_id="test_006",
                step_id=f"step_{i}",
                step_name=f"步骤{i}",
                status="completed"
            )

        # 获取进度
        progress = await manager.get_progress("test_006")

        assert progress is not None
        assert progress["total_steps"] == 10
        assert progress["completed_steps"] == 5
        assert progress["progress"] == 0.5

    async def test_delete_context(self, manager: AsyncTaskContextManager):
        """测试删除上下文"""
        await manager.create_context(
            task_id="test_007",
            task_description="删除测试"
        )

        # 删除
        success = await manager.delete_context("test_007")
        assert success is True

        # 验证已删除
        context = await manager.load_context("test_007")
        assert context is None

    async def test_list_contexts(self, manager: AsyncTaskContextManager):
        """测试列出上下文"""
        # 创建多个上下文
        for i in range(3):
            await manager.create_context(
                task_id=f"test_list_{i}",
                task_description=f"测试{i}",
                total_steps=5
            )

        # 列出所有
        all_ids = await manager.list_contexts()
        assert len(all_ids) >= 3
        assert "test_list_0" in all_ids
        assert "test_list_1" in all_ids
        assert "test_list_2" in all_ids

        # 按状态过滤
        await manager.set_status("test_list_0", ContextStatus.COMPLETED)
        active_ids = await manager.list_contexts(status=ContextStatus.ACTIVE)
        completed_ids = await manager.list_contexts(status=ContextStatus.COMPLETED)

        assert "test_list_0" in completed_ids
        assert "test_list_0" not in active_ids

    async def test_batch_load_contexts(self, manager: AsyncTaskContextManager):
        """测试批量加载（并发优化）"""
        # 创建多个上下文
        task_ids = [f"batch_{i}" for i in range(10)]
        for tid in task_ids:
            await manager.create_context(
                task_id=tid,
                task_description=f"批量测试{tid}",
                total_steps=5
            )

        # 批量加载
        start = time.perf_counter()
        contexts = await manager.batch_load_contexts(task_ids)
        elapsed = (time.perf_counter() - start) * 1000

        assert len(contexts) == 10
        for tid in task_ids:
            assert tid in contexts

        print(f"\n批量加载10个上下文耗时: {elapsed:.2f}ms")
        print(f"平均每个: {elapsed/10:.2f}ms")

        # 性能验证：批量加载应该比顺序加载快
        # 顺序加载预估时间（每个8ms）
        sequential_estimate = 10 * 8
        assert elapsed < sequential_estimate, f"批量加载性能未达标: {elapsed:.2f}ms > {sequential_estimate:.2f}ms"


@pytest.mark.asyncio
class TestAsyncTaskContextManagerPerformance:
    """异步任务上下文管理器性能测试"""

    async def test_load_performance(self, manager: AsyncTaskContextManager):
        """测试加载性能（目标<10ms）"""
        # 创建测试上下文
        await manager.create_context(
            task_id="perf_test",
            task_description="性能测试" * 100,  # 较大的描述
            total_steps=50
        )

        # 添加步骤
        for i in range(50):
            await manager.update_step(
                task_id="perf_test",
                step_id=f"step_{i}",
                step_name=f"步骤{i}",
                status="completed" if i < 25 else "pending"
            )

        # 测试加载性能
        times = []
        for _ in range(100):
            start = time.perf_counter()
            await manager.load_context("perf_test")
            elapsed = (time.perf_counter() - start) * 1000
            times.append(elapsed)

        avg_time = sum(times) / len(times)
        p95_time = sorted(times)[94]  # P95

        print(f"\n加载性能测试:")
        print(f"平均: {avg_time:.3f}ms")
        print(f"P95: {p95_time:.3f}ms")

        # 性能验证：目标<10ms
        assert avg_time < 10, f"平均加载时间未达标: {avg_time:.3f}ms > 10ms"
        assert p95_time < 15, f"P95加载时间未达标: {p95_time:.3f}ms > 15ms"

    async def test_save_performance(self, manager: AsyncTaskContextManager):
        """测试保存性能（目标<8ms）"""
        # 创建测试上下文
        await manager.create_context(
            task_id="perf_save_test",
            task_description="保存性能测试" * 100,
            total_steps=50
        )

        # 测试保存性能
        times = []
        for i in range(100):
            # 修改一些数据
            await manager.set_variable("perf_save_test", "counter", i)

            start = time.perf_counter()
            await manager.save_context(await manager.load_context("perf_save_test"))
            elapsed = (time.perf_counter() - start) * 1000
            times.append(elapsed)

        avg_time = sum(times) / len(times)
        p95_time = sorted(times)[94]  # P95

        print(f"\n保存性能测试:")
        print(f"平均: {avg_time:.3f}ms")
        print(f"P95: {p95_time:.3f}ms")

        # 性能验证：目标<8ms
        assert avg_time < 8, f"平均保存时间未达标: {avg_time:.3f}ms > 8ms"
        assert p95_time < 12, f"P95保存时间未达标: {p95_time:.3f}ms > 12ms"

    async def test_concurrent_performance(self, manager: AsyncTaskContextManager):
        """测试并发性能（目标>1000 QPS）"""
        # 创建100个上下文
        task_ids = [f"concurrent_{i}" for i in range(100)]
        for tid in task_ids:
            await manager.create_context(
                task_id=tid,
                task_description=f"并发测试{tid}",
                total_steps=10
            )

        # 并发读取测试
        async def concurrent_reader():
            tid = task_ids[hash(asyncio.current_task().get_name()) % len(task_ids)]
            await manager.load_context(tid)

        # 测量并发吞吐量
        start = time.time()

        # 创建100个并发任务，每个执行10次读取
        tasks = []
        for _ in range(100):
            for _ in range(10):
                task = asyncio.create_task(concurrent_reader())
                tasks.append(task)

        await asyncio.gather(*tasks)

        elapsed = time.time() - start
        qps = len(tasks) / elapsed

        print(f"\n并发性能测试:")
        print(f"总请求数: {len(tasks)}")
        print(f"总耗时: {elapsed:.2f}s")
        print(f"QPS: {qps:.2f}")

        # 性能验证：目标>1000 QPS
        assert qps > 1000, f"并发吞吐量未达标: {qps:.2f} QPS < 1000 QPS"


if __name__ == "__main__":
    # 运行测试
    pytest.main([__file__, "-v", "-s"])
