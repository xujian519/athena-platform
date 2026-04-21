#!/usr/bin/env python3
"""
装饰器工具模块单元测试
"""

import logging
import time
from unittest.mock import Mock

import pytest

from core.utils.decorator_utils import log_errors, retry, timer


class TestLogErrorsDecorator:
    """log_errors装饰器测试"""

    def test_log_errors_success(self, caplog):
        """测试成功执行不记录日志"""
        @log_errors()
        def successful_function():
            return "success"

        with caplog.at_level(logging.ERROR):
            result = successful_function()

        assert result == "success"
        assert len(caplog.records) == 0

    def test_log_errors_with_exception(self, caplog):
        """测试异常时记录日志"""
        @log_errors()
        def failing_function():
            raise ValueError("test error")

        with caplog.at_level(logging.ERROR):
            with pytest.raises(ValueError):
                failing_function()

        assert len(caplog.records) == 1
        assert "failing_function执行失败" in caplog.records[0].message
        assert "test error" in caplog.records[0].message

    def test_log_errors_with_custom_logger(self, caplog):
        """测试使用自定义logger"""
        custom_logger = logging.getLogger("custom_test")

        @log_errors(logger_obj=custom_logger)
        def failing_function():
            raise RuntimeError("custom error")

        with caplog.at_level(logging.ERROR):
            with pytest.raises(RuntimeError):
                failing_function()

        assert len(caplog.records) == 1
        assert "failing_function执行失败" in caplog.records[0].message

    def test_log_errors_preserves_exception(self):
        """测试保留原始异常"""
        @log_errors()
        def failing_function():
            raise ValueError("original error")

        with pytest.raises(ValueError) as exc_info:
            failing_function()

        assert str(exc_info.value) == "original error"

    def test_log_errors_with_args_kwargs(self, caplog):
        """测试带参数和关键字的函数"""
        @log_errors()
        def function_with_args(a, b, c=None):
            if a == 0:
                raise ValueError("a is zero")
            return a + b + (c or 0)

        with caplog.at_level(logging.ERROR):
            result = function_with_args(1, 2)
            assert result == 3

        with caplog.at_level(logging.ERROR):
            with pytest.raises(ValueError):
                function_with_args(0, 1)

        assert "a is zero" in caplog.records[0].message


class TestRetryDecorator:
    """retry装饰器测试"""

    def test_retry_success_on_first_try(self):
        """测试第一次尝试就成功"""
        @retry(max_attempts=3, delay=0.01)
        def successful_function():
            return "success"

        result = successful_function()
        assert result == "success"

    def test_retry_success_after_retry(self, caplog):
        """测试重试后成功"""
        call_count = 0

        @retry(max_attempts=3, delay=0.01)
        def sometimes_failing_function():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise ValueError("temporary failure")
            return "success"

        with caplog.at_level(logging.WARNING):
            result = sometimes_failing_function()

        assert result == "success"
        assert call_count == 2
        # 应该有1条警告日志
        assert len(caplog.records) >= 1

    def test_retry_all_attempts_fail(self, caplog):
        """测试所有尝试都失败"""
        @retry(max_attempts=3, delay=0.01)
        def always_failing_function():
            raise ValueError("permanent failure")

        with caplog.at_level(logging.ERROR):
            with pytest.raises(ValueError) as exc_info:
                always_failing_function()

        assert str(exc_info.value) == "permanent failure"
        # 应该有错误日志
        assert any("重试3次后仍失败" in record.message for record in caplog.records)

    def test_retry_custom_max_attempts(self):
        """测试自定义最大尝试次数"""
        call_count = 0

        @retry(max_attempts=5, delay=0.01)
        def failing_function():
            nonlocal call_count
            call_count += 1
            raise ValueError("error")

        with pytest.raises(ValueError):
            failing_function()

        assert call_count == 5

    def test_retry_custom_delay(self):
        """测试自定义延迟时间"""
        call_count = 0
        start_time = time.time()

        @retry(max_attempts=3, delay=0.05)
        def failing_function():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ValueError("error")
            return "success"

        result = failing_function()
        elapsed = time.time() - start_time

        assert result == "success"
        assert call_count == 3
        # 应该至少延迟了2次（第3次成功不需要延迟）
        assert elapsed >= 0.05 * 2

    def test_retry_custom_exceptions(self):
        """测试自定义异常类型"""
        @retry(max_attempts=3, delay=0.01, exceptions=(ValueError,))
        def raise_value_error():
            raise ValueError("value error")

        @retry(max_attempts=3, delay=0.01, exceptions=(ValueError,))
        def raise_type_error():
            raise TypeError("type error")

        # ValueError会重试
        with pytest.raises(ValueError):
            raise_value_error()

        # TypeError不会重试，直接抛出
        with pytest.raises(TypeError):
            raise_type_error()

    def test_retry_with_function_args(self):
        """测试带参数的函数"""
        @retry(max_attempts=2, delay=0.01)
        def function_with_args(a, b, c=None):
            if a == 0:
                raise ValueError("a is zero")
            return a + b + (c or 0)

        result = function_with_args(1, 2, c=3)
        assert result == 6

        with pytest.raises(ValueError):
            function_with_args(0, 1)


class TestTimerDecorator:
    """timer装饰器测试"""

    def test_timer_logs_execution_time(self, caplog):
        """测试记录执行时间"""
        @timer
        def quick_function():
            return "done"

        with caplog.at_level(logging.DEBUG):
            result = quick_function()

        assert result == "done"
        assert len(caplog.records) == 1
        assert "quick_function耗时" in caplog.records[0].message
        assert "秒" in caplog.records[0].message

    def test_timer_with_exception(self, caplog):
        """测试异常时也记录时间"""
        @timer
        def failing_function():
            raise ValueError("error")

        with caplog.at_level(logging.DEBUG):
            with pytest.raises(ValueError):
                failing_function()

        # 即使抛出异常，也应该记录时间
        assert len(caplog.records) == 1
        assert "failing_function耗时" in caplog.records[0].message

    def test_timer_with_slow_function(self, caplog):
        """测试慢速函数计时"""
        @timer
        def slow_function():
            time.sleep(0.05)
            return "done"

        with caplog.at_level(logging.DEBUG):
            result = slow_function()

        assert result == "done"
        assert len(caplog.records) == 1
        # 解析时间，应该大约0.05秒
        message = caplog.records[0].message
        assert "slow_function耗时" in message

    def test_timer_with_args_kwargs(self, caplog):
        """测试带参数的函数"""
        @timer
        def function_with_args(a, b, c=None):
            time.sleep(0.01)
            return a + b + (c or 0)

        with caplog.at_level(logging.DEBUG):
            result = function_with_args(1, 2, c=3)

        assert result == 6
        assert len(caplog.records) == 1


class TestDecoratorCombinations:
    """装饰器组合测试"""

    def test_timer_and_retry(self, caplog):
        """测试timer和retry组合"""
        call_count = 0

        @retry(max_attempts=3, delay=0.01)
        @timer
        def sometimes_failing_function():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise ValueError("temporary failure")
            return "success"

        with caplog.at_level(logging.DEBUG):
            result = sometimes_failing_function()

        assert result == "success"
        assert call_count == 2

    def test_log_errors_and_retry(self, caplog):
        """测试log_errors和retry组合"""
        @retry(max_attempts=2, delay=0.01)
        @log_errors()
        def failing_function():
            raise ValueError("error")

        with caplog.at_level(logging.ERROR):
            with pytest.raises(ValueError):
                failing_function()

        # 应该有错误日志
        assert len(caplog.records) >= 1


class TestEdgeCases:
    """边缘情况测试"""

    def test_retry_zero_attempts(self):
        """测试0次尝试（实际上至少会尝试1次）"""
        @retry(max_attempts=1, delay=0.01)
        def failing_function():
            raise ValueError("error")

        with pytest.raises(ValueError):
            failing_function()

    def test_retry_zero_delay(self):
        """测试0延迟"""
        call_count = 0

        @retry(max_attempts=3, delay=0)
        def failing_function():
            nonlocal call_count
            call_count += 1
            raise ValueError("error")

        start_time = time.time()
        with pytest.raises(ValueError):
            failing_function()
        elapsed = time.time() - start_time

        assert call_count == 3
        # 0延迟应该很快完成
        assert elapsed < 0.1

    def test_log_errors_with_none_result(self, caplog):
        """测试返回None的函数"""
        @log_errors()
        def return_none():
            return None

        with caplog.at_level(logging.ERROR):
            result = return_none()

        assert result is None
        assert len(caplog.records) == 0

    def test_timer_preserves_function_metadata(self):
        """测试timer保留函数元数据"""
        @timer
        def example_function():
            """示例函数"""
            return "result"

        assert example_function.__name__ == "example_function"
        assert example_function.__doc__ == "示例函数"

    def test_retry_preserves_function_metadata(self):
        """测试retry保留函数元数据"""
        @retry(max_attempts=3)
        def example_function():
            """示例函数"""
            return "result"

        assert example_function.__name__ == "example_function"
        assert example_function.__doc__ == "示例函数"

    def test_log_errors_preserves_function_metadata(self):
        """测试log_errors保留函数元数据"""
        @log_errors()
        def example_function():
            """示例函数"""
            return "result"

        assert example_function.__name__ == "example_function"
        assert example_function.__doc__ == "示例函数"


class TestIntegration:
    """集成测试"""

    def test_complete_workflow_with_retry_and_timer(self, caplog):
        """测试完整工作流：重试+计时"""
        call_count = 0

        @timer
        @retry(max_attempts=3, delay=0.02)
        def unstable_function(x, y):
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise ValueError(f"Attempt {call_count} failed")
            return x + y

        with caplog.at_level(logging.DEBUG):
            result = unstable_function(5, 3)

        assert result == 8
        assert call_count == 2

        # 应该有计时日志
        timer_logs = [r for r in caplog.records if "耗时" in r.message]
        assert len(timer_logs) >= 1

    def test_complete_workflow_with_all_decorators(self, caplog):
        """测试完整工作流：所有装饰器"""
        call_count = 0

        @log_errors()
        @retry(max_attempts=3, delay=0.01)
        @timer
        def complex_function(value):
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise ValueError("Fail")
            time.sleep(0.01)
            return value * 2

        with caplog.at_level(logging.DEBUG):
            result = complex_function(5)

        assert result == 10
        assert call_count == 2
