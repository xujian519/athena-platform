#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
错误处理和重试机制单元测试
Error Handling and Retry Mechanism Unit Tests

测试错误处理相关功能：
1. 重试处理器
2. 断路器
3. 降级处理器
4. 错误分类

作者: Athena平台团队
版本: 1.0.0
创建时间: 2026-01-28
"""

import asyncio

import pytest

from core.learning.error_handling import (
    CircuitBreaker,
    ErrorCategory,
    ErrorContext,
    ErrorHandlingMixin,
    ErrorSeverity,
    FallbackHandler,
    LearningEngineError,
    PermanentError,
    RetryConfig,
    RetryHandler,
    TransientError,
    ValidationError,
)


class TestErrorTypes:
    """错误类型测试"""

    def test_transient_error(self):
        """测试临时错误"""
        error = TransientError("测试临时错误", metadata={"key": "value"})

        assert error.message == "测试临时错误"
        assert error.severity == ErrorSeverity.MEDIUM
        assert error.category == ErrorCategory.TRANSIENT
        # metadata被包装在内部字典中
        assert error.metadata == {"metadata": {"key": "value"}}

    def test_permanent_error(self):
        """测试永久错误"""
        error = PermanentError("测试永久错误")

        assert error.severity == ErrorSeverity.HIGH
        assert error.category == ErrorCategory.PERMANENT

    def test_validation_error(self):
        """测试验证错误"""
        error = ValidationError("输入无效")

        assert error.severity == ErrorSeverity.LOW
        assert error.category == ErrorCategory.VALIDATION

    def test_error_context(self):
        """测试错误上下文"""
        context = ErrorContext(
            error_type="TestError",
            error_message="测试消息",
            severity=ErrorSeverity.HIGH,
            category=ErrorCategory.RESOURCE,
            retry_count=2,
            metadata={"info": "test"},
        )

        assert context.error_type == "TestError"
        assert context.retry_count == 2


class TestRetryHandler:
    """重试处理器测试"""

    @pytest.fixture
    def retry_handler(self):
        """创建重试处理器"""
        return RetryHandler(
            RetryConfig(
                max_attempts=3,
                base_delay=0.1,
                exponential_base=2.0,
            )
        )

    @pytest.mark.asyncio
    async def test_successful_execution(self, retry_handler):
        """测试成功执行"""
        async def successful_task():
            return "success"

        result = await retry_handler.execute_with_retry(successful_task)
        assert result == "success"

    @pytest.mark.asyncio
    async def test_retry_on_transient_error(self, retry_handler):
        """测试临时错误重试"""
        attempt_count = 0

        async def failing_task():
            nonlocal attempt_count
            attempt_count += 1
            if attempt_count < 2:
                raise TransientError("临时失败")
            return "success"

        result = await retry_handler.execute_with_retry(failing_task)
        assert result == "success"
        assert attempt_count == 2

    @pytest.mark.asyncio
    async def test_no_retry_on_permanent_error(self, retry_handler):
        """测试永久错误不重试"""
        attempt_count = 0

        async def permanent_failing_task():
            nonlocal attempt_count
            attempt_count += 1
            raise PermanentError("永久失败")

        with pytest.raises(LearningEngineError):
            await retry_handler.execute_with_retry(permanent_failing_task)

        # 永久错误应该立即失败，不重试
        assert attempt_count == 1

    @pytest.mark.asyncio
    async def test_no_retry_on_validation_error(self, retry_handler):
        """测试验证错误不重试"""
        attempt_count = 0

        async def validation_failing_task():
            nonlocal attempt_count
            attempt_count += 1
            raise ValidationError("输入无效")

        with pytest.raises(ValidationError):
            await retry_handler.execute_with_retry(validation_failing_task)

        # 验证错误应该立即失败，不重试
        assert attempt_count == 1

    @pytest.mark.asyncio
    async def test_retry_exhausted(self, retry_handler):
        """测试重试耗尽"""
        async def always_failing_task():
            raise TransientError("总是失败")

        with pytest.raises(LearningEngineError) as exc_info:
            await retry_handler.execute_with_retry(always_failing_task)

        assert "重试3次后仍然失败" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_exponential_backoff(self, retry_handler):
        """测试指数退避"""
        attempt_times = []

        async def tracking_task():
            attempt_times.append(asyncio.get_event_loop().time())
            raise TransientError("失败")

        with pytest.raises(LearningEngineError):
            await retry_handler.execute_with_retry(tracking_task)

        # 验证延迟递增（指数退避）
        assert len(attempt_times) == 3
        delay1 = attempt_times[1] - attempt_times[0]
        delay2 = attempt_times[2] - attempt_times[1]
        assert delay2 > delay1  # 延迟应该增加

    def test_get_statistics(self, retry_handler):
        """测试获取统计信息"""
        stats = retry_handler.get_statistics()
        assert "total_retries" in stats
        assert "successful_retries" in stats
        assert "recent_errors" in stats


class TestCircuitBreaker:
    """断路器测试"""

    @pytest.fixture
    def circuit_breaker(self):
        """创建断路器"""
        return CircuitBreaker(
            failure_threshold=3,
            timeout=1.0,
        )

    @pytest.mark.asyncio
    async def test_normal_operation(self, circuit_breaker):
        """测试正常操作"""
        async def working_task():
            return "success"

        result = await circuit_breaker.call(working_task)
        assert result == "success"

        state = circuit_breaker.get_state()
        assert state["state"] == "closed"
        assert state["failures"] == 0

    @pytest.mark.asyncio
    async def test_circuit_opens_on_failures(self, circuit_breaker):
        """测试失败后断路器打开"""
        async def failing_task():
            raise Exception("失败")

        # 触发3次失败
        for _ in range(3):
            with pytest.raises(Exception):
                await circuit_breaker.call(failing_task)

        # 断路器应该打开
        state = circuit_breaker.get_state()
        assert state["state"] == "open"
        assert state["failures"] == 3

    @pytest.mark.asyncio
    async def test_rejects_requests_when_open(self, circuit_breaker):
        """测试打开状态拒绝请求"""
        # 先让断路器打开
        async def failing_task():
            raise Exception("失败")

        for _ in range(3):
            try:
                await circuit_breaker.call(failing_task)
            except Exception:
                pass

        # 现在应该拒绝请求
        with pytest.raises(LearningEngineError) as exc_info:
            await circuit_breaker.call(failing_task)

        assert "断路器处于打开状态" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_half_open_state(self, circuit_breaker):
        """测试半开状态"""
        # 先让断路器打开
        async def failing_task():
            raise Exception("失败")

        for _ in range(3):
            try:
                await circuit_breaker.call(failing_task)
            except Exception:
                pass

        # 等待超时
        await asyncio.sleep(1.1)

        # 下一个调用应该进入半开状态
        # 需要实际调用才会进入半开状态
        try:
            await circuit_breaker.call(failing_task)
        except Exception:
            pass

        state = circuit_breaker.get_state()
        # 可能是half_open或open，取决于具体实现
        assert state["state"] in ["half_open", "open"]

    @pytest.mark.asyncio
    async def test_circuit_closes_on_success(self, circuit_breaker):
        """测试成功后断路器关闭"""
        # 先让断路器打开
        async def failing_task():
            raise Exception("失败")

        for _ in range(3):
            try:
                await circuit_breaker.call(failing_task)
            except Exception:
                pass

        # 等待超时
        await asyncio.sleep(1.1)

        # 执行成功任务
        async def success_task():
            return "success"

        # 需要多次成功才能关闭
        for _ in range(3):
            result = await circuit_breaker.call(success_task)
            assert result == "success"

        # 断路器应该关闭
        state = circuit_breaker.get_state()
        assert state["state"] == "closed"


class TestFallbackHandler:
    """降级处理器测试"""

    @pytest.fixture
    def fallback_handler(self):
        """创建降级处理器"""
        return FallbackHandler()

    @pytest.mark.asyncio
    async def test_primary_success(self, fallback_handler):
        """测试主函数成功"""
        async def primary_func():
            return "primary_result"

        result = await fallback_handler.execute_with_fallback(
            "test", primary_func
        )
        assert result == "primary_result"

    @pytest.mark.asyncio
    async def test_fallback_on_failure(self, fallback_handler):
        """测试失败时使用降级函数"""
        async def primary_func():
            raise Exception("主函数失败")

        async def fallback_func():
            return "fallback_result"

        fallback_handler.register_fallback("test", fallback_func)

        result = await fallback_handler.execute_with_fallback(
            "test", primary_func
        )
        assert result == "fallback_result"

    @pytest.mark.asyncio
    async def test_both_fail(self, fallback_handler):
        """测试主函数和降级函数都失败"""
        async def primary_func():
            raise Exception("主函数失败")

        async def fallback_func():
            raise Exception("降级函数失败")

        fallback_handler.register_fallback("test", fallback_func)

        with pytest.raises(LearningEngineError) as exc_info:
            await fallback_handler.execute_with_fallback("test", primary_func)

        assert "主函数和降级函数都失败" in str(exc_info.value)

    def test_get_statistics(self, fallback_handler):
        """测试获取统计信息"""
        async def dummy_func():
            return "result"

        fallback_handler.register_fallback("test", dummy_func)
        stats = fallback_handler.get_statistics()
        assert "test" in stats


class TestErrorHandlingMixin:
    """错误处理混入类测试"""

    @pytest.mark.asyncio
    async def test_handle_learning_engine_error(self):
        """测试处理学习引擎错误"""
        class TestClass(ErrorHandlingMixin):
            def __init__(self):
                ErrorHandlingMixin.__init__(self)

        obj = TestClass()

        # 处理错误
        error = TransientError("测试错误", context={"key": "value"})
        obj._handle_error(error)

        # 验证错误被记录
        assert len(obj.error_history) == 1
        assert obj.error_history[0].error_message == "测试错误"

    @pytest.mark.asyncio
    async def test_handle_generic_error(self):
        """测试处理普通异常"""
        class TestClass(ErrorHandlingMixin):
            def __init__(self):
                ErrorHandlingMixin.__init__(self)

        obj = TestClass()

        # 处理普通异常
        error = ValueError("普通错误")
        obj._handle_error(error)

        # 验证错误被记录
        assert len(obj.error_history) == 1
        assert obj.error_history[0].error_type == "ValueError"

    def test_get_error_statistics(self):
        """测试获取错误统计"""
        class TestClass(ErrorHandlingMixin):
            def __init__(self):
                ErrorHandlingMixin.__init__(self)

        obj = TestClass()

        # 添加一些错误
        obj._handle_error(TransientError("错误1"))
        obj._handle_error(PermanentError("错误2"))

        stats = obj.get_error_statistics()
        assert stats["total_errors"] == 2
        assert "retry_stats" in stats
        assert "circuit_breaker" in stats
        assert "fallback_stats" in stats


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
