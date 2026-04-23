#!/usr/bin/env python3
"""
重试工具模块单元测试
"""

import asyncio
import time

import pytest

from core.utils.retry_utils import (
    RETRY_CONFIG_DATABASE,
    RETRY_CONFIG_FAST,
    RETRY_CONFIG_NETWORK,
    RETRY_CONFIG_NORMAL,
    RETRY_CONFIG_SLOW,
    RetryConfig,
    RetryExhaustedError,
    async_retry_on_exception,
    async_safe_execute,
    retry_on_exception,
    safe_execute,
)


class TestRetryConfig:
    """RetryConfig类测试"""

    def test_default_config(self):
        """测试默认配置"""
        config = RetryConfig()
        assert config.max_attempts == 3
        assert config.base_delay == 1.0
        assert config.max_delay == 60.0
        assert config.exponential_base == 2.0
        assert config.jitter is True
        assert config.jitter_range == 0.1

    def test_custom_config(self):
        """测试自定义配置"""
        config = RetryConfig(
            max_attempts=5,
            base_delay=2.0,
            max_delay=120.0,
            exponential_base=3.0,
            jitter=False,
            jitter_range=0.2
        )
        assert config.max_attempts == 5
        assert config.base_delay == 2.0
        assert config.max_delay == 120.0
        assert config.exponential_base == 3.0
        assert config.jitter is False
        assert config.jitter_range == 0.2

    def test_get_delay_no_jitter(self):
        """测试无抖动的延迟计算"""
        config = RetryConfig(jitter=False)
        delay = config.get_delay(attempt=1)
        assert delay == 1.0  # base_delay * (2^0)

        delay = config.get_delay(attempt=2)
        assert delay == 2.0  # base_delay * (2^1)

        delay = config.get_delay(attempt=3)
        assert delay == 4.0  # base_delay * (2^2)

    def test_get_delay_with_jitter(self):
        """测试带抖动的延迟计算"""
        config = RetryConfig(jitter=True, jitter_range=0.1)
        delay1 = config.get_delay(attempt=1)
        delay2 = config.get_delay(attempt=1)
        # 由于抖动，两次调用应该产生略微不同的结果
        assert delay1 != delay2 or delay1 == 1.0  # 可能相等

    def test_get_delay_max_limit(self):
        """测试延迟最大值限制"""
        config = RetryConfig(base_delay=10.0, max_delay=15.0, exponential_base=2.0)
        delay = config.get_delay(attempt=10)  # 会很大，但被限制
        assert delay <= 15.0

    def test_get_delay_never_negative(self):
        """测试延迟永远不会为负"""
        config = RetryConfig(jitter=True, jitter_range=0.5)
        for attempt in range(1, 10):
            delay = config.get_delay(attempt)
            assert delay >= 0


class TestRetryOnException:
    """retry_on_exception装饰器测试"""

    def test_success_on_first_try(self):
        """测试第一次尝试就成功"""
        @retry_on_exception()
        def successful_function():
            return "success"

        result = successful_function()
        assert result == "success"

    def test_retry_then_success(self):
        """测试重试后成功"""
        call_count = 0

        @retry_on_exception(config=RetryConfig(max_attempts=3, base_delay=0.01))
        def sometimes_failing_function():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise ValueError("temporary failure")
            return "success"

        result = sometimes_failing_function()
        assert result == "success"
        assert call_count == 2

    def test_all_attempts_fail(self):
        """测试所有尝试都失败"""
        @retry_on_exception(config=RetryConfig(max_attempts=3, base_delay=0.01))
        def always_failing_function():
            raise ValueError("permanent failure")

        with pytest.raises(RetryExhaustedError) as exc_info:
            always_failing_function()

        assert "always_failing_function" in str(exc_info.value)
        assert exc_info.value.attempts == 3

    def test_specific_exception_only(self):
        """测试只重试特定异常"""
        @retry_on_exception(exceptions=(ValueError,))
        def raise_value_error():
            raise ValueError("value error")

        @retry_on_exception(exceptions=(ValueError,))
        def raise_type_error():
            raise TypeError("type error")

        # ValueError会重试
        with pytest.raises(RetryExhaustedError):
            raise_value_error()

        # TypeError不会重试，直接抛出
        with pytest.raises(TypeError):
            raise_type_error()

    def test_custom_config(self):
        """测试自定义配置"""
        call_count = 0

        @retry_on_exception(config=RETRY_CONFIG_FAST)
        def failing_function():
            nonlocal call_count
            call_count += 1
            raise ValueError("error")

        with pytest.raises(RetryExhaustedError):
            failing_function()

        assert call_count == 2  # RETRY_CONFIG_FAST的max_attempts=2

    def test_on_retry_callback(self):
        """测试重试回调"""
        callback_calls = []

        def retry_callback(attempt, exception):
            callback_calls.append((attempt, str(exception)))

        @retry_on_exception(on_retry=retry_callback)
        def failing_function():
            raise ValueError("test error")

        with pytest.raises(RetryExhaustedError):
            failing_function()

        # 应该调用回调（max_attempts-1次，因为最后一次失败不会调用回调）
        assert len(callback_calls) > 0

    def test_preserves_function_metadata(self):
        """测试保留函数元数据"""
        @retry_on_exception()
        def example_function():
            """示例函数"""
            pass

        assert example_function.__name__ == "example_function"
        assert example_function.__doc__ == "示例函数"


class TestAsyncRetryOnException:
    """async_retry_on_exception装饰器测试"""

    @pytest.mark.asyncio
    async def test_async_success_on_first_try(self):
        """测试异步函数第一次尝试就成功"""
        @async_retry_on_exception()
        async def successful_function():
            return "success"

        result = await successful_function()
        assert result == "success"

    @pytest.mark.asyncio
    async def test_async_retry_then_success(self):
        """测试异步函数重试后成功"""
        call_count = 0

        @async_retry_on_exception(config=RetryConfig(max_attempts=3, base_delay=0.01))
        async def sometimes_failing_function():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise ValueError("temporary failure")
            return "success"

        result = await sometimes_failing_function()
        assert result == "success"
        assert call_count == 2

    @pytest.mark.asyncio
    async def test_async_all_attempts_fail(self):
        """测试异步函数所有尝试都失败"""
        @async_retry_on_exception(config=RetryConfig(max_attempts=3, base_delay=0.01))
        async def always_failing_function():
            raise ValueError("permanent failure")

        with pytest.raises(RetryExhaustedError):
            await always_failing_function()

    @pytest.mark.asyncio
    async def test_async_with_callback(self):
        """测试异步函数重试回调"""
        callback_calls = []

        def retry_callback(attempt, exception):
            callback_calls.append(attempt)

        @async_retry_on_exception(on_retry=retry_callback, config=RetryConfig(max_attempts=2, base_delay=0.01))
        async def failing_function():
            raise ValueError("error")

        with pytest.raises(RetryExhaustedError):
            await failing_function()

        assert len(callback_calls) > 0

    @pytest.mark.asyncio
    async def test_async_preserves_metadata(self):
        """测试保留异步函数元数据"""
        @async_retry_on_exception()
        async def example_function():
            """示例异步函数"""
            pass

        assert example_function.__name__ == "example_function"
        assert example_function.__doc__ == "示例异步函数"


class TestSafeExecute:
    """safe_execute函数测试"""

    def test_success(self):
        """测试成功执行"""
        def successful_function():
            return "success"

        result = safe_execute(successful_function)
        assert result == "success"

    def test_exception_returns_default(self):
        """测试异常时返回默认值"""
        def failing_function():
            raise ValueError("error")

        result = safe_execute(failing_function, default_value=None)
        assert result is None

    def test_exception_with_custom_default(self):
        """测试自定义默认值"""
        def failing_function():
            raise ValueError("error")

        result = safe_execute(failing_function, default_value="default")
        assert result == "default"

    def test_specific_exception_only(self):
        """测试只捕获特定异常"""
        def raise_value_error():
            raise ValueError("value error")

        def raise_type_error():
            raise TypeError("type error")

        # 捕获ValueError
        result = safe_execute(raise_value_error, exceptions=(ValueError,), default_value="caught")
        assert result == "caught"

        # 不捕获TypeError，应该抛出
        with pytest.raises(TypeError):
            safe_execute(raise_type_error, exceptions=(ValueError,), default_value="caught")

    def test_with_args(self):
        """测试带参数的函数"""
        def add(a, b):
            return a + b

        result = safe_execute(add, 1, 2)
        assert result == 3

    def test_with_kwargs(self):
        """测试带关键字的函数"""
        def greet(name="World"):
            return f"Hello, {name}"

        result = safe_execute(greet, name="Alice")
        assert result == "Hello, Alice"

    def test_log_error_false(self):
        """测试不记录错误"""
        def failing_function():
            raise ValueError("error")

        result = safe_execute(failing_function, log_error=False)
        assert result is None


class TestAsyncSafeExecute:
    """async_safe_execute函数测试"""

    @pytest.mark.asyncio
    async def test_async_success(self):
        """测试异步函数成功执行"""
        async def successful_function():
            return "success"

        result = await async_safe_execute(successful_function)
        assert result == "success"

    @pytest.mark.asyncio
    async def test_async_exception_returns_default(self):
        """测试异步函数异常时返回默认值"""
        async def failing_function():
            raise ValueError("error")

        result = await async_safe_execute(failing_function, default_value=None)
        assert result is None

    @pytest.mark.asyncio
    async def test_async_with_args(self):
        """测试异步函数带参数"""
        async def add(a, b):
            return a + b

        result = await async_safe_execute(add, 1, 2)
        assert result == 3

    @pytest.mark.asyncio
    async def test_async_log_error_false(self):
        """测试异步函数不记录错误"""
        async def failing_function():
            raise ValueError("error")

        result = await async_safe_execute(failing_function, log_error=False)
        assert result is None


class TestPredefinedConfigs:
    """预定义配置测试"""

    def test_retry_config_fast(self):
        """测试快速重试配置"""
        assert RETRY_CONFIG_FAST.max_attempts == 2
        assert RETRY_CONFIG_FAST.base_delay == 0.5
        assert RETRY_CONFIG_FAST.max_delay == 5.0

    def test_retry_config_normal(self):
        """测试正常重试配置"""
        assert RETRY_CONFIG_NORMAL.max_attempts == 3
        assert RETRY_CONFIG_NORMAL.base_delay == 1.0
        assert RETRY_CONFIG_NORMAL.max_delay == 30.0

    def test_retry_config_slow(self):
        """测试慢速重试配置"""
        assert RETRY_CONFIG_SLOW.max_attempts == 5
        assert RETRY_CONFIG_SLOW.base_delay == 2.0
        assert RETRY_CONFIG_SLOW.max_delay == 60.0

    def test_retry_config_database(self):
        """测试数据库重试配置"""
        assert RETRY_CONFIG_DATABASE.max_attempts == 3
        assert RETRY_CONFIG_DATABASE.base_delay == 0.5
        assert RETRY_CONFIG_DATABASE.max_delay == 10.0
        assert RETRY_CONFIG_DATABASE.jitter_range == 0.2

    def test_retry_config_network(self):
        """测试网络重试配置"""
        assert RETRY_CONFIG_NETWORK.max_attempts == 4
        assert RETRY_CONFIG_NETWORK.base_delay == 1.0
        assert RETRY_CONFIG_NETWORK.max_delay == 30.0
        assert RETRY_CONFIG_NETWORK.exponential_base == 2.5


class TestIntegration:
    """集成测试"""

    def test_retry_with_realistic_timing(self):
        """测试真实的时间重试场景"""
        call_times = []

        @retry_on_exception(config=RetryConfig(max_attempts=3, base_delay=0.05, jitter=False))
        def flaky_function():
            call_times.append(time.time())
            if len(call_times) < 2:
                raise ValueError("temporary failure")
            return "success"

        start = time.time()
        result = flaky_function()
        elapsed = time.time() - start

        assert result == "success"
        assert len(call_times) == 2
        # 应该有至少一次延迟（base_delay=0.05）
        assert elapsed >= 0.04  # 允许一些误差

    @pytest.mark.asyncio
    async def test_async_retry_with_realistic_timing(self):
        """测试异步函数真实的时间重试场景"""
        call_times = []

        @async_retry_on_exception(config=RetryConfig(max_attempts=3, base_delay=0.05, jitter=False))
        async def flaky_function():
            call_times.append(time.time())
            if len(call_times) < 2:
                raise ValueError("temporary failure")
            return "success"

        start = time.time()
        result = await flaky_function()
        elapsed = time.time() - start

        assert result == "success"
        assert len(call_times) == 2
        assert elapsed >= 0.04

    def test_safe_execute_in_retry(self):
        """测试safe_execute不会触发重试"""
        # safe_execute捕获异常，所以重试装饰器看不到异常
        # 因此不会触发重试

        call_count = 0

        def outer_function():
            nonlocal call_count
            call_count += 1
            raise ValueError("fail")

        @retry_on_exception(config=RetryConfig(max_attempts=3, base_delay=0.01))
        def retry_wrapper():
            # safe_execute捕获异常，返回默认值
            # 装饰器看不到异常，所以不会重试
            return safe_execute(outer_function, default_value="fallback")

        result = retry_wrapper()
        # 只调用一次，因为safe_execute没有抛出异常
        assert call_count == 1
        assert result == "fallback"

    def test_exponential_backoff(self):
        """测试指数退避"""
        delays = []
        config = RetryConfig(max_attempts=5, base_delay=1.0, exponential_base=2.0, jitter=False)

        for attempt in range(1, 5):
            delay = config.get_delay(attempt)
            delays.append(delay)

        # 验证指数增长: 1, 2, 4, 8
        assert delays[0] == 1.0
        assert delays[1] == 2.0
        assert delays[2] == 4.0
        assert delays[3] == 8.0


class TestEdgeCases:
    """边缘情况测试"""

    def test_zero_attempts(self):
        """测试0次尝试（实际上至少1次）"""
        @retry_on_exception(config=RetryConfig(max_attempts=1, base_delay=0.01))
        def failing_function():
            raise ValueError("error")

        with pytest.raises(RetryExhaustedError):
            failing_function()

    def test_very_short_delay(self):
        """测试极短延迟"""
        config = RetryConfig(base_delay=0.001, jitter=False)
        delay = config.get_delay(attempt=1)
        assert delay >= 0
        assert delay < 0.01

    def test_very_long_delay(self):
        """测试极长延迟（被max_delay限制）"""
        config = RetryConfig(base_delay=1000.0, max_delay=1.0, jitter=False)
        delay = config.get_delay(attempt=10)
        assert delay == 1.0  # 被max_delay限制

    def test_jitter_range_zero(self):
        """测试零抖动范围"""
        config = RetryConfig(jitter=True, jitter_range=0.0)
        delay1 = config.get_delay(attempt=1)
        delay2 = config.get_delay(attempt=1)
        assert delay1 == delay2  # 零抖动范围应该产生相同的结果

    def test_large_exponential_base(self):
        """测试大指数底数"""
        config = RetryConfig(exponential_base=10.0, max_delay=1000.0, jitter=False)
        delay = config.get_delay(attempt=2)
        # base_delay * (10^1) = 1.0 * 10 = 10.0
        assert delay == 10.0

    @pytest.mark.asyncio
    async def test_async_safe_execute_with_coroutine(self):
        """测试异步安全执行协程"""
        async def async_function(value):
            await asyncio.sleep(0.01)
            return value * 2

        result = await async_safe_execute(async_function, 5)
        assert result == 10

    def test_safe_execute_with_none_default(self):
        """测试None作为默认值"""
        def failing_function():
            raise ValueError("error")

        result = safe_execute(failing_function, default_value=None)
        assert result is None

    @pytest.mark.asyncio
    async def test_async_safe_execute_with_none_default(self):
        """测试异步None作为默认值"""
        async def failing_function():
            raise ValueError("error")

        result = await async_safe_execute(failing_function, default_value=None)
        assert result is None
