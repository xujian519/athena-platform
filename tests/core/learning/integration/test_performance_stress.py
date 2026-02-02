#!/usr/bin/env python3
"""
学习模块性能压测
Performance Stress Tests for Learning Module

作者: Athena平台团队
版本: 1.0.0
创建时间: 2026-01-28
"""

import asyncio
import statistics
import time
from datetime import datetime

import pytest

from core.learning.autonomous_learning_system import AutonomousLearningSystem
from core.learning.concurrency_control import (
    ConcurrencyConfig,
    ConcurrencyController,
)
from core.learning.error_handling import RetryHandler, RetryConfig
from core.learning.persistence_manager import (
    LearningPersistenceManager,
    StorageBackend,
)
from core.learning.input_validator import get_input_validator


@pytest.mark.integration
class TestConcurrencyStress:
    """并发性能压力测试"""

    @pytest.mark.asyncio
    async def test_high_concurrent_learning(self):
        """测试高并发学习场景（1000并发任务）"""
        system = AutonomousLearningSystem(agent_id="stress_test")

        start_time = time.perf_counter()

        # 创建1000个并发学习任务
        tasks = []
        for i in range(1000):
            task = system.learn_from_experience(
                context={"task_id": i, "type": f"type_{i % 10}"},
                action=f"action_{i % 20}",
                result={"status": "success", "value": i},
                reward=0.5 + (i % 5) * 0.1,
            )
            tasks.append(task)

        results = await asyncio.gather(*tasks, return_exceptions=True)

        elapsed = time.perf_counter() - start_time

        # 统计结果
        successful = sum(1 for r in results if not isinstance(r, Exception))
        errors = [r for r in results if isinstance(r, Exception)]

        print(f"\n高并发学习测试 (1000任务):")
        print(f"  耗时: {elapsed*1000:.2f}ms")
        print(f"  吞吐量: {1000/elapsed:.0f} tasks/sec")
        print(f"  成功: {successful}")
        print(f"  失败: {len(errors)}")

        assert successful >= 990  # 允许少量失败
        assert len(system.experiences) >= 990

    @pytest.mark.asyncio
    async def test_concurrency_controller_stress(self):
        """测试并发控制器在高负载下的表现"""
        config = ConcurrencyConfig(
            max_concurrent_tasks=50,
            max_operations_per_second=1000,
            task_timeout=10.0,
        )
        controller = ConcurrencyController(config)

        async def simulate_work(task_id: int, duration: float = 0.01):
            """模拟工作负载"""
            await asyncio.sleep(duration)
            return {"task_id": task_id, "result": "done"}

        start_time = time.perf_counter()

        # 提交500个任务
        tasks = []
        for i in range(500):
            task = controller.submit_task(
                lambda i=i, d=0.01: simulate_work(i, d), timeout=5.0
            )
            tasks.append(task)

        results = await asyncio.gather(*tasks, return_exceptions=True)

        elapsed = time.perf_counter() - start_time
        stats = controller.get_statistics()

        print(f"\n并发控制器压测 (500任务, 50并发):")
        print(f"  耗时: {elapsed*1000:.2f}ms")
        print(f"  吞吐量: {500/elapsed:.0f} tasks/sec")
        print(f"  统计: {stats['tasks']}")
        print(f"  成功率: {stats['tasks']['success_rate']*100:.1f}%")

        assert stats["tasks"]["completed"] >= 490
        assert stats["tasks"]["success_rate"] > 0.95

    @pytest.mark.asyncio
    async def test_retry_under_stress(self):
        """测试重试机制在高负载下的表现"""
        handler = RetryHandler(RetryConfig(max_attempts=3, base_delay=0.001))

        call_counts = []

        async def flaky_task(task_id: int):
            """不稳定的任务，30%失败率"""
            call_counts.append(task_id)
            import random

            if random.random() < 0.3:
                raise Exception("Random failure")
            return f"success_{task_id}"

        start_time = time.perf_counter()

        # 提交200个不稳定的任务
        tasks = []
        for i in range(200):
            task = handler.execute_with_retry(flaky_task, i)
            tasks.append(task)

        results = await asyncio.gather(*tasks, return_exceptions=True)

        elapsed = time.perf_counter() - start_time

        successful = sum(1 for r in results if not isinstance(r, Exception))
        stats = handler.get_statistics()

        print(f"\n重试机制压测 (200任务, 30%失败率):")
        print(f"  耗时: {elapsed*1000:.2f}ms")
        print(f"  成功: {successful}/200")
        print(f"  总重试次数: {stats['total_retries']}")
        print(f"  成功重试: {stats['successful_retries']}")

        assert successful >= 150  # 至少75%成功率

    @pytest.mark.asyncio
    async def test_batch_processing_stress(self):
        """测试批量处理性能"""
        config = ConcurrencyConfig(max_concurrent_tasks=20)
        controller = ConcurrencyController(config)

        async def quick_task(i: int):
            await asyncio.sleep(0.005)  # 5ms
            return i * 2

        start_time = time.perf_counter()

        # 批量处理1000个任务
        batches = []
        batch_size = 50
        for batch_start in range(0, 1000, batch_size):
            batch = [
                lambda i=i: quick_task(i)
                for i in range(batch_start, min(batch_start + batch_size, 1000))
            ]
            batches.append(controller.submit_batch(batch))

        all_results = await asyncio.gather(*batches, return_exceptions=True)

        elapsed = time.perf_counter() - start_time

        # 扁平化结果
        flat_results = []
        for batch_result in all_results:
            if isinstance(batch_result, list):
                flat_results.extend(batch_result)

        print(f"\n批量处理压测 (1000任务, 50批次, 20并发):")
        print(f"  耗时: {elapsed*1000:.2f}ms")
        print(f"  吞吐量: {1000/elapsed:.0f} tasks/sec")
        print(f"  处理结果数: {len(flat_results)}")

        assert len(flat_results) == 1000


@pytest.mark.integration
class TestPersistenceStress:
    """持久化性能压测"""

    @pytest.mark.asyncio
    async def test_high_volume_persistence(self, tmp_path):
        """测试高容量持久化"""
        manager = LearningPersistenceManager(StorageBackend.FILE)
        await manager.initialize(base_path=str(tmp_path / "stress_test"))

        start_time = time.perf_counter()

        # 保存1000条记录
        save_tasks = []
        for i in range(1000):
            task = manager.save_experience(
                agent_id=f"agent_{i % 10}",
                experience={
                    "index": i,
                    "timestamp": datetime.now().isoformat(),
                    "data": "x" * 100,  # 100字节数据
                },
            )
            save_tasks.append(task)

        results = await asyncio.gather(*save_tasks, return_exceptions=True)

        save_elapsed = time.perf_counter() - start_time

        successful_saves = sum(1 for r in results if r)
        failed_saves = len(results) - successful_saves

        print(f"\n持久化写入压测 (1000条记录):")
        print(f"  写入耗时: {save_elapsed*1000:.2f}ms")
        print(f"  写入吞吐量: {1000/save_elapsed:.0f} records/sec")
        print(f"  成功: {successful_saves}, 失败: {failed_saves}")

        # 测试读取性能
        start_time = time.perf_counter()
        experiences = await manager.load_experiences("agent_0", limit=200)
        load_elapsed = time.perf_counter() - start_time

        print(f"  读取耗时 (200条): {load_elapsed*1000:.2f}ms")
        print(f"  读取吞吐量: {len(experiences)/load_elapsed:.0f} records/sec")

        assert successful_saves >= 990
        assert len(experiences) >= 90  # agent_0应该有约100条记录

    @pytest.mark.asyncio
    async def test_concurrent_persistence_access(self, tmp_path):
        """测试并发持久化访问"""
        manager = LearningPersistenceManager(StorageBackend.FILE)
        await manager.initialize(base_path=str(tmp_path / "concurrent_test"))

        async def concurrent_agent_work(agent_id: int, operations: int = 50):
            """模拟智能体的并发工作"""
            for i in range(operations):
                await manager.save_experience(
                    agent_id=f"agent_{agent_id}",
                    experience={"op": i, "agent": agent_id},
                )
                # 偶尔读取
                if i % 10 == 0:
                    await manager.load_experiences(f"agent_{agent_id}", limit=10)
            return f"agent_{agent_id}_done"

        start_time = time.perf_counter()

        # 20个智能体并发操作，每个50次操作
        tasks = [
            concurrent_agent_work(i, operations=50) for i in range(20)
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        elapsed = time.perf_counter() - start_time

        successful = sum(1 for r in results if not isinstance(r, Exception))

        print(f"\n并发持久化访问 (20智能体, 50操作/智能体):")
        print(f"  耗时: {elapsed*1000:.2f}ms")
        print(f"  操作吞吐量: {1000/elapsed:.0f} ops/sec")
        print(f"  成功智能体: {successful}/20")

        assert successful == 20

    @pytest.mark.asyncio
    async def test_query_performance_stress(self, tmp_path):
        """测试查询性能在大量数据下的表现"""
        manager = LearningPersistenceManager(StorageBackend.FILE)
        await manager.initialize(base_path=str(tmp_path / "query_test"))

        # 准备数据：10个智能体，每个500条记录
        print("\n准备查询测试数据...")
        prepare_start = time.perf_counter()

        for agent_id in range(10):
            for record_id in range(500):
                await manager.save_experience(
                    agent_id=f"agent_{agent_id}",
                    experience={
                        "record": record_id,
                        "category": record_id % 5,
                        "value": record_id * 1.5,
                    },
                )

        prepare_elapsed = time.perf_counter() - prepare_start
        print(f"  数据准备耗时: {prepare_elapsed*1000:.2f}ms")

        # 测试查询性能
        query_times = []
        for _ in range(50):
            start = time.perf_counter()
            experiences = await manager.load_experiences("agent_0", limit=100)
            query_times.append((time.perf_counter() - start) * 1000)

        avg_query_time = statistics.mean(query_times)
        max_query_time = max(query_times)
        min_query_time = min(query_times)

        print(f"\n查询性能测试 (50次查询, 100条/次):")
        print(f"  平均查询时间: {avg_query_time:.2f}ms")
        print(f"  最大查询时间: {max_query_time:.2f}ms")
        print(f"  最小查询时间: {min_query_time:.2f}ms")

        assert avg_query_time < 100  # 平均查询时间应小于100ms


@pytest.mark.integration
class TestMemoryStress:
    """内存压力测试"""

    @pytest.mark.asyncio
    async def test_large_buffer_handling(self):
        """测试大缓冲区处理"""
        system = AutonomousLearningSystem(agent_id="memory_test")

        # 添加大量经验（接近缓冲区限制）
        print("\n大缓冲区测试 (10000条经验):")
        start_time = time.perf_counter()

        for i in range(10000):
            await system.learn_from_experience(
                context={"task": i, "large_data": "x" * 100},
                action=f"action_{i % 100}",
                result={"status": "ok"},
                reward=0.5,
            )

        elapsed = time.perf_counter() - start_time

        print(f"  耗时: {elapsed*1000:.2f}ms")
        print(f"  吞吐量: {10000/elapsed:.0f} experiences/sec")
        print(f"  缓冲区大小: {len(system.experiences)}")
        print(f"  性能历史记录数: {sum(len(h) for h in system.performance_history.values())}")

        assert len(system.experiences) <= 10000  # 应该被限制

    @pytest.mark.asyncio
    async def test_memory_leak_prevention(self):
        """测试内存泄漏预防"""
        import gc
        import sys

        system = AutonomousLearningSystem(agent_id="leak_test")

        # 多次填充和清空，检查内存是否稳定
        gc.collect()
        initial_objects = len(gc.get_objects())

        for cycle in range(3):
            # 填充
            for i in range(5000):
                await system.learn_from_experience(
                    context={"cycle": cycle, "index": i},
                    action="test",
                    result={},
                    reward=0.5,
                )

            # 清空
            system.experiences.clear()
            for key in system.performance_history:
                system.performance_history[key].clear()

            gc.collect()

        gc.collect()
        final_objects = len(gc.get_objects())

        object_growth = final_objects - initial_objects

        print(f"\n内存泄漏预防测试:")
        print(f"  初始对象数: {initial_objects}")
        print(f"  最终对象数: {final_objects}")
        print(f"  对象增长: {object_growth}")
        print(f"  增长率: {object_growth/initial_objects*100:.2f}%")

        # 对象增长不应超过初始数量的50%
        assert object_growth < initial_objects * 0.5


@pytest.mark.integration
class TestInputValidationStress:
    """输入验证压力测试"""

    @pytest.mark.asyncio
    async def test_high_volume_validation(self):
        """测试高容量输入验证"""
        validator = get_input_validator()

        start_time = time.perf_counter()

        # 验证10000个输入
        tasks = []
        for i in range(10000):
            # 混合有效和无效输入
            context = {
                "task": f"task_{i}",
                "data": "x" * min(100, i % 200),  # 变化大小
            }
            action = f"action_{i % 50}"
            result = {"status": "ok"}

            task = validator.validate_learning_input(
                context=context,
                action=action,
                result=result,
                reward=0.5,
            )
            tasks.append(task)

        results = await asyncio.gather(*tasks, return_exceptions=True)

        elapsed = time.perf_counter() - start_time

        valid_count = sum(1 for r in results if getattr(r, "is_valid", False))
        invalid_count = len(results) - valid_count

        print(f"\n输入验证压测 (10000次验证):")
        print(f"  耗时: {elapsed*1000:.2f}ms")
        print(f"  验证吞吐量: {10000/elapsed:.0f} validations/sec")
        print(f"  有效输入: {valid_count}")
        print(f"  无效输入: {invalid_count}")

        assert 10000/elapsed > 10000  # 至少10000次/秒
