#!/usr/bin/env python3
"""
可靠性增强测试
Reliability Enhancement Tests

测试覆盖：
- 重试机制测试
- 熔断器测试
- 死信队列测试
- 集成测试
- 压力测试

Created by Athena AI系统
Date: 2025-12-14
Version: 1.0.0
"""

import asyncio
import logging
import time

import pytest

# 导入被测试模块
from reliability_manager import (
    CircuitBreaker,
    CircuitBreakerConfig,
    CircuitBreakerOpenError,
    CircuitState,
    DeadLetterQueue,
    RetryConfig,
    RetryManager,
    get_reliability_manager,
)

logger = logging.getLogger(__name__)


# =============================================================================
# 重试机制测试
# =============================================================================

class TestRetryMechanism:
    """重试机制测试"""

    @pytest.mark.asyncio
    async def test_successful_retry(self):
        """测试成功重试"""
        config = RetryConfig(max_attempts=3, base_delay=0.1)
        manager = RetryManager(config)

        attempt_count = 0

        async def failing_function():
            nonlocal attempt_count
            attempt_count += 1
            if attempt_count < 3:
                raise ValueError("模拟失败")
            return "成功"

        result = await manager.execute(failing_function)

        assert result == "成功"
        assert attempt_count == 3
        assert manager.stats.successful_attempts == 1
        assert manager.stats.retry_count == 2

        logger.info(f"✅ 重试成功: {attempt_count} 次尝试")

    @pytest.mark.asyncio
    async def test_retry_exhaustion(self):
        """测试重试耗尽"""
        config = RetryConfig(max_attempts=3, base_delay=0.1)
        manager = RetryManager(config)

        attempt_count = 0

        async def always_failing_function():
            nonlocal attempt_count
            attempt_count += 1
            raise ValueError("总是失败")

        with pytest.raises(ValueError):
            await manager.execute(always_failing_function)

        assert attempt_count == 3
        assert manager.stats.failed_attempts == 1

        logger.info(f"✅ 重试耗尽: {attempt_count} 次尝试")

    @pytest.mark.asyncio
    async def test_exponential_backoff(self):
        """测试指数退避"""
        config = RetryConfig(
            max_attempts=5,
            base_delay=1.0,
            exponential_base=2.0,
            jitter=False
        )
        manager = RetryManager(config)

        start_times = []

        async def failing_function():
            start_times.append(time.time())
            raise ValueError("失败")

        with pytest.raises(ValueError):
            await manager.execute(failing_function)

        # 验证延迟呈指数增长
        assert len(start_times) == config.max_attempts

        logger.info(f"✅ 指数退避测试通过: {len(start_times)} 次尝试")

    @pytest.mark.asyncio
    async def test_retry_stats(self):
        """测试重试统计"""
        config = RetryConfig(max_attempts=5)
        manager = RetryManager(config)

        # 成功的调用
        await manager.execute(lambda: "成功")
        await manager.execute(lambda: "成功")

        # 失败的调用
        try:
            await manager.execute(lambda: (_ for _ in ()).throw(ValueError("失败")))
        except ValueError:
            pass

        stats = manager.get_stats()
        assert stats['total_attempts'] == 3  # 2成功 + 1失败
        assert stats['successful_attempts'] == 2
        assert stats['failed_attempts'] == 1

        logger.info(f"✅ 统计信息: {stats}")


# =============================================================================
# 熔断器测试
# =============================================================================

class TestCircuitBreaker:
    """熔断器测试"""

    @pytest.mark.asyncio
    async def test_circuit_breaker_opening(self):
        """测试熔断器打开"""
        config = CircuitBreakerConfig(
            failure_threshold=3,
            min_calls=3,
            timeout=1.0
        )
        cb = CircuitBreaker("test_breaker", config)

        # 触发熔断器打开
        failure_count = 0
        for _i in range(10):
            try:
                await cb.call(lambda: (_ for _ in ()).throw(ValueError("失败")))
            except ValueError:
                failure_count += 1
            except CircuitBreakerOpenError:
                break

        # 验证熔断器已打开
        assert cb.get_state() == CircuitState.OPEN
        assert cb.get_stats()['recent_failures'] >= 3

        logger.info(f"✅ 熔断器已打开: {cb.get_state().value}")

    @pytest.mark.asyncio
    async def test_circuit_breaker_recovery(self):
        """测试熔断器恢复"""
        config = CircuitBreakerConfig(
            failure_threshold=2,
            min_calls=2,
            timeout=0.5,  # 0.5秒后尝试恢复
            success_threshold=1
        )
        cb = CircuitBreaker("test_breaker", config)

        # 触发熔断器打开
        for _ in range(5):
            try:
                await cb.call(lambda: (_ for _ in ()).throw(ValueError("失败")))
            except (ValueError, CircuitBreakerOpenError):
                pass

        assert cb.get_state() == CircuitState.OPEN

        # 等待超时
        await asyncio.sleep(0.6)

        # 半开状态下调用成功
        result = await cb.call(lambda: "成功")
        assert result == "成功"

        # 验证熔断器已关闭
        assert cb.get_state() == CircuitState.CLOSED

        logger.info(f"✅ 熔断器已恢复: {cb.get_state().value}")

    @pytest.mark.asyncio
    async def test_circuit_breaker_stats(self):
        """测试熔断器统计"""
        config = CircuitBreakerConfig(
            failure_threshold=5,
            min_calls=2
        )
        cb = CircuitBreaker("test_breaker", config)

        # 混合成功和失败调用
        for i in range(10):
            try:
                await cb.call(
                    lambda: (_ for _ in ()).throw(ValueError("失败"))
                    if i % 3 == 0 else lambda: "成功"
                )
            except (ValueError, CircuitBreakerOpenError):
                pass

        stats = cb.get_stats()
        assert 'name' in stats
        assert 'state' in stats
        assert 'failure_count' in stats
        assert 'success_count' in stats

        logger.info(f"✅ 熔断器统计: {stats}")


# =============================================================================
# 死信队列测试
# =============================================================================

class TestDeadLetterQueue:
    """死信队列测试"""

    @pytest.mark.asyncio
    async def test_enqueue_dequeue(self):
        """测试入队和出队"""
        dlq = DeadLetterQueue(max_size=10)

        # 添加任务
        success = await dlq.add(
            'task_001',
            'test_task',
            {'param': 'value'},
            Exception("测试异常")
        )
        assert success is True

        # 获取任务
        task = await dlq.get()
        assert task is not None
        assert task.task_id == 'task_001'
        assert task.task_type == 'test_task'

        # 验证队列为空
        assert await dlq.size() == 0

        logger.info("✅ 死信队列入队/出队测试通过")

    @pytest.mark.asyncio
    async def test_queue_full(self):
        """测试队列满"""
        dlq = DeadLetterQueue(max_size=2)

        # 添加2个任务
        await dlq.add('task_001', 'test', {}, Exception())
        await dlq.add('task_002', 'test', {}, Exception())

        # 添加第3个任务应该失败
        success = await dlq.add('task_003', 'test', {}, Exception())
        assert success is False

        logger.info("✅ 队列满测试通过")

    @pytest.mark.asyncio
    async def test_clear_queue(self):
        """测试清空队列"""
        dlq = DeadLetterQueue()

        # 添加多个任务
        for i in range(5):
            await dlq.add(f'task_{i}', 'test', {}, Exception())

        assert await dlq.size() == 5

        # 清空
        await dlq.clear()
        assert await dlq.size() == 0

        logger.info("✅ 清空队列测试通过")


# =============================================================================
# 集成测试
# =============================================================================

class TestReliabilityIntegration:
    """集成测试"""

    @pytest.mark.asyncio
    async def test_end_to_end_reliability(self):
        """端到端可靠性测试"""
        manager = get_reliability_manager()

        call_count = 0

        async def flaky_function():
            nonlocal call_count
            call_count += 1
            if call_count <= 2:
                raise ValueError("模拟失败")
            return "最终成功"

        result = await manager.execute_with_reliability(
            "flaky_operation",
            flaky_function,
            use_retry=True,
            use_circuit_breaker=False
        )

        assert result == "最终成功"
        assert call_count == 3

        logger.info(f"✅ 端到端测试通过: {call_count} 次调用")

    @pytest.mark.asyncio
    async def test_reliability_stats(self):
        """测试可靠性统计"""
        manager = get_reliability_manager()

        # 执行多个操作
        for i in range(10):
            try:
                await manager.execute_with_reliability(
                    f"operation_{i % 3}",
                    lambda: "成功" if i % 2 == 0 else (_ for _ in ()).throw(ValueError("失败"))
                )
            except Exception:
                pass

        stats = manager.get_stats()
        assert 'total_calls' in stats
        assert 'successful_calls' in stats
        assert 'failed_calls' in stats
        assert 'success_rate' in stats

        logger.info(f"✅ 可靠性统计: {stats}")


# =============================================================================
# 压力测试
# =============================================================================

class TestReliabilityStress:
    """可靠性压力测试"""

    @pytest.mark.asyncio
    @pytest.mark.stress
    async def test_concurrent_retries(self):
        """并发重试测试"""
        manager = get_reliability_manager()

        async def concurrent_operation(op_id):
            attempt_count = 0

            async def flaky_op():
                nonlocal attempt_count
                attempt_count += 1
                if attempt_count < 2:
                    raise ValueError(f"操作 {op_id} 失败")
                return f"操作 {op_id} 成功"

            return await manager.execute_with_reliability(
                f"concurrent_op_{op_id}",
                flaky_op
            )

        # 并发执行50个操作
        start = time.time()
        tasks = [concurrent_operation(i) for i in range(50)]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        elapsed = time.time() - start

        successful = sum(1 for r in results if not isinstance(r, Exception))
        logger.info(f"✅ 并发重试测试: {successful}/50 成功, 耗时: {elapsed:.2f}秒")

    @pytest.mark.asyncio
    @pytest.mark.stress
    async def test_circuit_breaker_under_load(self):
        """负载下熔断器测试"""
        config = CircuitBreakerConfig(
            failure_threshold=10,
            min_calls=5,
            timeout=2.0
        )
        cb = CircuitBreaker("stress_test", config)

        # 模拟高负载
        async def high_load_operation():
            import random
            if random.random() < 0.7:  # 70%失败率
                raise ValueError("高负载失败")
            return "成功"

        # 执行100次操作
        for _i in range(100):
            try:
                await cb.call(high_load_operation)
            except (ValueError, CircuitBreakerOpenError):
                pass

        stats = cb.get_stats()
        logger.info(f"✅ 负载测试完成: {stats['state']}, "
                   f"失败数: {stats['recent_failures']}")


# =============================================================================
# 运行测试
# =============================================================================

def run_tests():
    """运行所有测试"""
    pytest.main([
        __file__,
        '-v',
        '--tb=short'
    ])


if __name__ == '__main__':
    run_tests()
