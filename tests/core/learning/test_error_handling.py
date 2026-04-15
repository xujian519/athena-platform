#!/usr/bin/env python3
"""
错误处理模块单元测试
Unit Tests for Error Handling Module

作者: Athena平台团队
版本: 1.0.0
创建时间: 2026-01-28
"""

import asyncio
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from core.learning.error_handling import (
    ErrorCategory,
    ErrorContext,
    ErrorHandlingMixin,
    ErrorSeverity,
    FallbackHandler,
    LearningEngineError,
    PermanentError,
    ResourceError,
    RetryConfig,
    RetryHandler,
    TransientError,
    ValidationError,
)


class TestLearningEngineError:
    """学习引擎异常测试"""

    def test_create_error_with_defaults(self):
        """测试使用默认参数创建异常"""
        error = LearningEngineError("Test error")
        assert error.message == "Test error"
        assert error.severity == ErrorSeverity.MEDIUM
        assert error.category == ErrorCategory.TRANSIENT
        assert error.metadata == {}

    def test_create_error_with_custom_severity(self):
        """测试创建自定义严重程度的异常"""
        error = LearningEngineError(
            "Critical error", severity=ErrorSeverity.CRITICAL
        )
        assert error.severity == ErrorSeverity.CRITICAL

    def test_create_error_with_metadata(self):
        """测试创建带元数据的异常"""
        error = LearningEngineError(
            "Error with data", key1="value1", key2="value2"
        )
        assert error.metadata == {"key1": "value1", "key2": "value2"}


class TestErrorSubclasses:
    """异常子类测试"""

    def test_transient_error(self):
        """测试临时错误"""
        error = TransientError("Temporary failure")
        assert error.severity == ErrorSeverity.MEDIUM
        assert error.category == ErrorCategory.TRANSIENT

    def test_permanent_error(self):
        """测试永久错误"""
        error = PermanentError("Permanent failure")
        assert error.severity == ErrorSeverity.HIGH
        assert error.category == ErrorCategory.PERMANENT

    def test_validation_error(self):
        """测试验证错误"""
        error = ValidationError("Invalid input")
        assert error.severity == ErrorSeverity.LOW
        assert error.category == ErrorCategory.VALIDATION

    def test_resource_error(self):
        """测试资源错误"""
        error = ResourceError("Out of memory")
        assert error.severity == ErrorSeverity.HIGH
        assert error.category == ErrorCategory.RESOURCE


class TestRetryHandler:
    """重试处理器测试"""

    @pytest.mark.asyncio
    async def test_successful_on_first_try(self):
        """测试第一次尝试就成功"""
        handler = RetryHandler()
        call_count = 0

        async def successful_func():
            nonlocal call_count
            call_count += 1
            return "success"

        result = await handler.execute_with_retry(successful_func)
        assert result == "success"
        assert call_count == 1

    @pytest.mark.asyncio
    async def test_retry_on_transient_error(self):
        """测试临时错误时重试"""
        handler = RetryHandler(RetryConfig(max_attempts=3, base_delay=0.01))
        call_count = 0

        async def failing_then_success():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise TransientError("Temporary failure")
            return "success"

        result = await handler.execute_with_retry(failing_then_success)
        assert result == "success"
        assert call_count == 3

    @pytest.mark.asyncio
    async def test_no_retry_on_permanent_error(self):
        """测试永久错误时不重试"""
        handler = RetryHandler(RetryConfig(max_attempts=3))
        call_count = 0

        async def permanent_failure():
            nonlocal call_count
            call_count += 1
            raise PermanentError("Permanent failure")

        with pytest.raises(LearningEngineError):
            await handler.execute_with_retry(permanent_failure)
        assert call_count == 1

    @pytest.mark.asyncio
    async def test_no_retry_on_validation_error(self):
        """测试验证错误时不重试"""
        handler = RetryHandler(RetryConfig(max_attempts=3))
        call_count = 0

        async def validation_failure():
            nonlocal call_count
            call_count += 1
            raise ValidationError("Invalid input")

        with pytest.raises(LearningEngineError):
            await handler.execute_with_retry(validation_failure)
        assert call_count == 1

    @pytest.mark.asyncio
    async def test_exhausted_retries(self):
        """测试重试耗尽"""
        handler = RetryHandler(RetryConfig(max_attempts=3, base_delay=0.01))
        call_count = 0

        async def always_fails():
            nonlocal call_count
            call_count += 1
            raise TransientError("Always fails")

        with pytest.raises(LearningEngineError, match="重试3次后仍然失败"):
            await handler.execute_with_retry(always_fails)
        assert call_count == 3

    def test_calculate_delay_with_exponential_backoff(self):
        """测试指数退避延迟计算"""
        handler = RetryHandler(
            RetryConfig(
                max_attempts=5,
                base_delay=1.0,
                exponential_base=2.0,
                jitter=False  # 禁用抖动以获得确定结果
            )
        )

        # 第一次重试: 1 * 2^0 = 1秒
        delay_0 = handler._calculate_delay(0)
        assert delay_0 == 1.0

        # 第二次重试: 1 * 2^1 = 2秒
        delay_1 = handler._calculate_delay(1)
        assert delay_1 == 2.0

        # 第三次重试: 1 * 2^2 = 4秒
        delay_2 = handler._calculate_delay(2)
        assert delay_2 == 4.0

    def test_calculate_delay_with_max_limit(self):
        """测试延迟最大值限制"""
        handler = RetryHandler(
            RetryConfig(
                max_attempts=10,
                base_delay=1.0,
                max_delay=5.0,
                jitter=False  # 禁用抖动
            )
        )

        # 即使指数增长很大，也受max_delay限制
        delay_large = handler._calculate_delay(10)
        assert delay_large <= 5.0

    def test_get_statistics(self):
        """测试获取统计信息"""
        handler = RetryHandler()
        stats = handler.get_statistics()
        assert "total_retries" in stats
        assert "successful_retries" in stats
        assert "recent_errors" in stats


class TestCircuitBreaker:
    """断路器测试"""

    @pytest.mark.asyncio
    async def test_closed_allows_calls(self):
        """测试关闭状态允许调用"""
        breaker = self._create_breaker()

        async def success_func():
            return "success"

        result = await breaker.call(success_func)
        assert result == "success"
        assert breaker._state == "closed"
        assert breaker._failures == 0

    @pytest.mark.asyncio
    async def test_open_blocks_calls(self):
        """测试打开状态阻止调用"""
        breaker = self._create_breaker(failure_threshold=2)

        async def failing_func():
            raise Exception("Failure")

        # 触发失败
        with pytest.raises(Exception):
            await breaker.call(failing_func)

        with pytest.raises(Exception):
            await breaker.call(failing_func)

        # 断路器应该打开
        assert breaker._state == "open"

        # 下一个调用应该被阻止
        with pytest.raises(LearningEngineError, match="断路器处于打开状态"):
            await breaker.call(failing_func)

    @pytest.mark.asyncio
    async def test_half_open_allows_recovery(self):
        """测试半开状态允许恢复"""
        breaker = self._create_breaker(failure_threshold=2, timeout=0.1)

        async def failing_func():
            raise Exception("Failure")

        async def success_func():
            return "success"

        # 触发断路器打开
        with pytest.raises(Exception):
            await breaker.call(failing_func)
        with pytest.raises(Exception):
            await breaker.call(failing_func)

        assert breaker._state == "open"

        # 等待超时
        await asyncio.sleep(0.15)

        # 下一个调用应该成功并恢复到关闭状态
        result = await breaker.call(success_func)
        assert result == "success"
        assert breaker._state == "closed"

    def test_get_state(self):
        """测试获取断路器状态"""
        breaker = self._create_breaker()
        state = breaker.get_state()
        assert "state" in state
        assert "failures" in state
        assert "failure_threshold" in state

    def _create_breaker(self, failure_threshold=5, timeout=60.0, half_open_attempts=1):
        """辅助方法：创建断路器"""
        from core.learning.error_handling import CircuitBreaker
        return CircuitBreaker(failure_threshold, timeout, half_open_attempts)


class TestFallbackHandler:
    """降级处理器测试"""

    @pytest.mark.asyncio
    async def test_execute_primary_success(self):
        """测试主函数成功"""
        handler = FallbackHandler()

        async def primary_func():
            return "primary_result"

        result = await handler.execute_with_fallback("test", primary_func)
        assert result == "primary_result"

    @pytest.mark.asyncio
    async def test_execute_primary_failure_with_fallback(self):
        """测试主函数失败时使用降级函数"""
        handler = FallbackHandler()

        async def primary_func():
            raise Exception("Primary failed")

        async def fallback_func():
            return "fallback_result"

        handler.register_fallback("test", fallback_func)
        result = await handler.execute_with_fallback("test", primary_func)
        assert result == "fallback_result"

    @pytest.mark.asyncio
    async def test_execute_both_fail(self):
        """测试主函数和降级函数都失败"""
        handler = FallbackHandler()

        async def primary_func():
            raise Exception("Primary failed")

        async def fallback_func():
            raise Exception("Fallback failed")

        handler.register_fallback("test", fallback_func)

        with pytest.raises(LearningEngineError, match="主函数和降级函数都失败"):
            await handler.execute_with_fallback("test", primary_func)

    def test_get_statistics(self):
        """测试获取统计信息"""
        handler = FallbackHandler()
        stats = handler.get_statistics()
        assert isinstance(stats, dict)


class TestErrorHandlingMixin:
    """错误处理混入类测试"""

    def test_handle_learning_engine_error(self):
        """测试处理学习引擎异常"""
        mixin = ErrorHandlingMixin()
        error = TransientError("Test error", context={"key": "value"})

        mixin._handle_error(error)
        assert len(mixin.error_history) == 1
        assert mixin.error_history[0].error_type == "TransientError"

    def test_handle_generic_error(self):
        """测试处理通用异常"""
        mixin = ErrorHandlingMixin()
        error = ValueError("Generic error")

        mixin._handle_error(error)
        assert len(mixin.error_history) == 1
        assert mixin.error_history[0].severity == ErrorSeverity.MEDIUM

    def test_error_history_limit(self):
        """测试错误历史限制"""
        mixin = ErrorHandlingMixin()

        # 添加超过限制的错误
        for i in range(1100):
            mixin._handle_error(ValueError(f"Error {i}"))

        # 应该被限制在1000
        assert len(mixin.error_history) == 1000

    def test_get_error_statistics(self):
        """测试获取错误统计"""
        mixin = ErrorHandlingMixin()
        mixin._handle_error(TransientError("Test error"))

        stats = mixin.get_error_statistics()
        assert "total_errors" in stats
        assert "recent_errors" in stats
        assert "retry_stats" in stats
        assert "circuit_breaker" in stats


@pytest.mark.unit
class TestRetryConfig:
    """重试配置测试"""

    def test_default_config(self):
        """测试默认配置"""
        config = RetryConfig()
        assert config.max_attempts == 3
        assert config.base_delay == 1.0
        assert config.max_delay == 60.0
        assert config.exponential_base == 2.0
        assert config.jitter is True

    def test_custom_config(self):
        """测试自定义配置"""
        config = RetryConfig(max_attempts=5, base_delay=2.0)
        assert config.max_attempts == 5
        assert config.base_delay == 2.0


@pytest.mark.unit
class TestErrorContext:
    """错误上下文测试"""

    def test_create_error_context(self):
        """测试创建错误上下文"""
        context = ErrorContext(
            error_type="TestError",
            error_message="Test message",
            severity=ErrorSeverity.HIGH,
            category=ErrorCategory.TRANSIENT,
        )
        assert context.error_type == "TestError"
        assert context.error_message == "Test message"
        assert context.severity == ErrorSeverity.HIGH
        assert context.retry_count == 0
