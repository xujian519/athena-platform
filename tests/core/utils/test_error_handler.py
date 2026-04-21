#!/usr/bin/env python3
"""
错误处理器单元测试
"""

import asyncio
import logging
from datetime import datetime
from unittest.mock import Mock, patch

import pytest

from core.exceptions import AthenaError
from core.utils.error_handler import (
    ErrorHandler,
    async_error_handler,
    async_safe_execute,
    create_error_handler,
    format_error_response,
    log_error,
    retry_on_error,
    safe_execute,
    sync_error_handler,
)


class TestErrorHandlerInit:
    """ErrorHandler初始化测试"""

    def test_init_basic(self):
        """测试基本初始化"""
        handler = ErrorHandler("test_component")
        assert handler.component_name == "test_component"
        assert handler.raise_on_error is False
        assert handler.error_count == 0
        assert handler.last_error is None
        assert handler.last_error_time is None

    def test_init_with_raise_on_error(self):
        """测试启用raise_on_error"""
        handler = ErrorHandler("test_component", raise_on_error=True)
        assert handler.raise_on_error is True


class TestHandleError:
    """handle_error方法测试"""

    def test_handle_basic_error(self, caplog):
        """测试基本错误处理"""
        handler = ErrorHandler("test_component")

        with caplog.at_level(logging.ERROR):
            error_info = handler.handle_error(
                ValueError("test error"),
                context="test context"
            )

        assert handler.error_count == 1
        assert handler.last_error is not None
        assert isinstance(handler.last_error_time, datetime)
        assert error_info["component"] == "test_component"
        assert error_info["context"] == "test context"

    def test_handle_athena_error(self, caplog):
        """测试处理AthenaError"""
        handler = ErrorHandler("test_component")

        with caplog.at_level(logging.WARNING):
            error_info = handler.handle_error(
                AthenaError("athena error"),
                context="athena context"
            )

        # AthenaError应该使用WARNING级别
        assert any(record.levelname == "WARNING" for record in caplog.records)

    def test_handle_error_with_additional_info(self, caplog):
        """测试带附加信息的错误处理"""
        handler = ErrorHandler("test_component")

        with caplog.at_level(logging.ERROR):
            error_info = handler.handle_error(
                ValueError("test error"),
                context="test",
                additional_info={"user_id": 123, "action": "test"}
            )

        assert "additional_info" in error_info
        assert error_info["additional_info"]["user_id"] == 123
        assert error_info["additional_info"]["action"] == "test"

    def test_handle_error_with_raise(self, caplog):
        """测试重新抛出异常"""
        handler = ErrorHandler("test_component", raise_on_error=True)

        with caplog.at_level(logging.ERROR):
            with pytest.raises(ValueError):
                handler.handle_error(ValueError("test error"))

        # 错误应该被记录
        assert handler.error_count == 1

    def test_handle_multiple_errors(self, caplog):
        """测试处理多个错误"""
        handler = ErrorHandler("test_component")

        with caplog.at_level(logging.ERROR):
            handler.handle_error(ValueError("error 1"))
            handler.handle_error(RuntimeError("error 2"))
            handler.handle_error(TypeError("error 3"))

        assert handler.error_count == 3
        assert isinstance(handler.last_error, TypeError)


class TestErrorBoundary:
    """error_boundary上下文管理器测试"""

    def test_error_boundary_success(self):
        """测试正常执行"""
        handler = ErrorHandler("test_component")

        with handler.error_boundary("test operation"):
            result = 1 + 1

        assert result == 2
        assert handler.error_count == 0

    def test_error_boundary_catches_error(self, caplog):
        """测试错误边界捕获异常"""
        handler = ErrorHandler("test_component")

        with caplog.at_level(logging.ERROR):
            with handler.error_boundary("risky operation"):
                raise ValueError("test error")

        # 错误应该被捕获
        assert handler.error_count == 1
        assert isinstance(handler.last_error, ValueError)

    def test_error_boundary_with_context(self, caplog):
        """测试带上下文的错误边界"""
        handler = ErrorHandler("test_component")

        with caplog.at_level(logging.ERROR):
            with handler.error_boundary("processing data"):
                raise RuntimeError("processing failed")

        # error_boundary已经处理了错误,检查error_count
        assert handler.error_count == 1
        # 验证last_error被正确设置
        assert isinstance(handler.last_error, RuntimeError)
        assert str(handler.last_error) == "processing failed"


class TestGetStats:
    """get_stats方法测试"""

    def test_get_stats_no_errors(self):
        """测试无错误时的统计"""
        handler = ErrorHandler("test_component")

        stats = handler.get_stats()

        assert stats["component"] == "test_component"
        assert stats["total_errors"] == 0
        assert stats["last_error"] is None
        assert stats["last_error_time"] is None

    def test_get_stats_with_errors(self):
        """测试有错误时的统计"""
        handler = ErrorHandler("test_component")

        handler.handle_error(ValueError("test error"))

        stats = handler.get_stats()

        assert stats["total_errors"] == 1
        assert "ValueError: test error" in stats["last_error"]
        assert stats["last_error_time"] is not None

    def test_get_stats_error_without_message(self):
        """测试无错误消息的格式化"""
        handler = ErrorHandler("test_component")

        handler.handle_error(ValueError())

        stats = handler.get_stats()

        # 应该只有异常类型名（没有冒号,因为消息为空）
        assert stats["last_error"] == "ValueError"

    def test_get_stats_multiple_errors(self):
        """测试多个错误的统计"""
        handler = ErrorHandler("test_component")

        handler.handle_error(ValueError("error 1"))
        handler.handle_error(RuntimeError("error 2"))

        stats = handler.get_stats()

        assert stats["total_errors"] == 2
        assert "RuntimeError: error 2" in stats["last_error"]


class TestCreateErrorHandler:
    """create_error_handler函数测试"""

    def test_create_basic_handler(self):
        """测试创建基本处理器"""
        handler = create_error_handler("test")

        assert isinstance(handler, ErrorHandler)
        assert handler.component_name == "test"
        assert handler.raise_on_error is False

    def test_create_handler_with_raise(self):
        """测试创建带raise的处理器"""
        handler = create_error_handler("test", raise_on_error=True)

        assert handler.raise_on_error is True


class TestAsyncErrorHandler:
    """async_error_handler装饰器测试"""

    @pytest.mark.asyncio
    async def test_async_handler_success(self):
        """测试异步函数正常执行"""
        @async_error_handler("test context")
        async def test_func():
            return "success"

        result = await test_func()
        assert result == "success"

    @pytest.mark.asyncio
    async def test_async_handler_catches_error(self, caplog):
        """测试异步装饰器捕获错误"""
        @async_error_handler("test context")
        async def failing_func():
            raise ValueError("test error")

        with caplog.at_level(logging.ERROR):
            result = await failing_func()

        # 错误应该被捕获,返回None
        assert result is None
        assert len(caplog.records) > 0

    @pytest.mark.asyncio
    async def test_async_handler_with_raise(self, caplog):
        """测试异步装饰器重新抛出"""
        @async_error_handler("test context", raise_on_error=True)
        async def failing_func():
            raise ValueError("test error")

        with caplog.at_level(logging.ERROR):
            with pytest.raises(ValueError):
                await failing_func()

    @pytest.mark.asyncio
    async def test_async_handler_custom_component(self, caplog):
        """测试自定义组件名称"""
        @async_error_handler("test context", component_name="custom_component")
        async def failing_func():
            raise ValueError("test error")

        with caplog.at_level(logging.ERROR):
            await failing_func()

        # 检查日志中的组件名
        assert any("custom_component" in record.message for record in caplog.records)

    @pytest.mark.asyncio
    async def test_async_handler_preserves_metadata(self):
        """测试保留函数元数据"""
        @async_error_handler("test context")
        async def test_func():
            """Test function docstring"""
            pass

        assert test_func.__name__ == "test_func"
        assert test_func.__doc__ == "Test function docstring"


class TestSyncErrorHandler:
    """sync_error_handler装饰器测试"""

    def test_sync_handler_success(self):
        """测试同步函数正常执行"""
        @sync_error_handler("test context")
        def test_func():
            return "success"

        result = test_func()
        assert result == "success"

    def test_sync_handler_catches_error(self, caplog):
        """测试同步装饰器捕获错误"""
        @sync_error_handler("test context")
        def failing_func():
            raise ValueError("test error")

        with caplog.at_level(logging.ERROR):
            result = failing_func()

        assert result is None
        assert len(caplog.records) > 0

    def test_sync_handler_with_raise(self, caplog):
        """测试同步装饰器重新抛出"""
        @sync_error_handler("test context", raise_on_error=True)
        def failing_func():
            raise ValueError("test error")

        with caplog.at_level(logging.ERROR):
            with pytest.raises(ValueError):
                failing_func()

    def test_sync_handler_preserves_metadata(self):
        """测试保留函数元数据"""
        @sync_error_handler("test context")
        def test_func():
            """Test function docstring"""
            pass

        assert test_func.__name__ == "test_func"
        assert test_func.__doc__ == "Test function docstring"


class TestRetryOnError:
    """retry_on_error装饰器测试"""

    @pytest.mark.asyncio
    async def test_retry_async_success(self):
        """测试异步函数重试成功"""
        call_count = 0

        @retry_on_error(max_attempts=3, delay=0.01)
        async def sometimes_failing():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise ValueError("temp error")
            return "success"

        result = await sometimes_failing()
        assert result == "success"
        assert call_count == 2

    @pytest.mark.asyncio
    async def test_retry_async_all_fail(self, caplog):
        """测试异步函数全部失败"""
        @retry_on_error(max_attempts=3, delay=0.01)
        async def always_failing():
            raise ValueError("permanent error")

        with caplog.at_level(logging.ERROR):
            with pytest.raises(ValueError):
                await always_failing()

        # 应该有重试日志
        assert any("重试" in record.message for record in caplog.records)

    @pytest.mark.asyncio
    async def test_retry_async_specific_exception(self):
        """测试异步函数只重试特定异常"""
        @retry_on_error(max_attempts=3, delay=0.01, retry_on=(ValueError,))
        async def raise_value_error():
            raise ValueError("value error")

        @retry_on_error(max_attempts=3, delay=0.01, retry_on=(ValueError,))
        async def raise_type_error():
            raise TypeError("type error")

        # ValueError会重试
        with pytest.raises(ValueError):
            await raise_value_error()

        # TypeError不会重试,直接抛出
        with pytest.raises(TypeError):
            await raise_type_error()

    def test_retry_sync_success(self):
        """测试同步函数重试成功"""
        call_count = 0

        @retry_on_error(max_attempts=3, delay=0.01)
        def sometimes_failing():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise ValueError("temp error")
            return "success"

        result = sometimes_failing()
        assert result == "success"
        assert call_count == 2

    def test_retry_sync_all_fail(self, caplog):
        """测试同步函数全部失败"""
        @retry_on_error(max_attempts=3, delay=0.01)
        def always_failing():
            raise ValueError("permanent error")

        with caplog.at_level(logging.ERROR):
            with pytest.raises(ValueError):
                always_failing()

    @pytest.mark.asyncio
    async def test_retry_with_backoff(self):
        """测试指数退避"""
        import time

        call_times = []

        @retry_on_error(max_attempts=3, delay=0.05, backoff_factor=2.0)
        async def failing_func():
            call_times.append(time.time())
            raise ValueError("error")

        with pytest.raises(ValueError):
            await failing_func()

        # 应该有3次尝试
        assert len(call_times) == 3

        # 验证退避: 第2次-第1次 ≈ 0.05, 第3次-第2次 ≈ 0.10
        if len(call_times) >= 3:
            delay1 = call_times[1] - call_times[0]
            delay2 = call_times[2] - call_times[1]
            # delay2应该大约是delay1的2倍
            assert delay2 > delay1 * 1.5


class TestLogError:
    """log_error函数测试"""

    def test_log_error_basic(self, caplog):
        """测试基本错误日志"""
        error = ValueError("test error")

        with caplog.at_level(logging.ERROR):
            log_error(error, context="test context")

        assert len(caplog.records) >= 1
        assert "test context" in caplog.records[0].message

    def test_log_error_with_level(self, caplog):
        """测试指定日志级别"""
        error = ValueError("test error")

        with caplog.at_level(logging.WARNING):
            log_error(error, context="test", level="WARNING")

        assert any(record.levelname == "WARNING" for record in caplog.records)

    def test_log_error_with_extra(self, caplog):
        """测试带额外信息"""
        error = ValueError("test error")

        with caplog.at_level(logging.ERROR):
            log_error(error, context="test", extra={"user_id": 123})

        # extra信息应该在error_info中
        assert any(
            "error_info" in record.__dict__
            for record in caplog.records
        )


class TestFormatErrorResponse:
    """format_error_response函数测试"""

    def test_format_basic_error(self):
        """测试基本错误格式化"""
        error = ValueError("test error")
        response = format_error_response(error)

        assert "error_type" in response
        assert response["error_type"] == "ValueError"
        assert "test error" in response["error_message"]

    def test_format_error_with_traceback(self):
        """测试包含堆栈跟踪"""
        error = ValueError("test error")
        response = format_error_response(error, include_traceback=True)

        assert "traceback" in response
        assert isinstance(response["traceback"], str)
        assert len(response["traceback"]) > 0


class TestSafeExecute:
    """safe_execute函数测试"""

    def test_safe_execute_success(self):
        """测试成功执行"""
        def success_func():
            return "success"

        result = safe_execute(success_func)
        assert result == "success"

    def test_safe_execute_with_args(self):
        """测试带参数的函数"""
        def add(a, b):
            return a + b

        result = safe_execute(add, 1, 2)
        assert result == 3

    def test_safe_execute_error_returns_default(self, caplog):
        """测试错误时返回默认值"""
        def failing_func():
            raise ValueError("error")

        with caplog.at_level(logging.ERROR):
            result = safe_execute(failing_func, default=None)

        assert result is None
        assert len(caplog.records) > 0

    def test_safe_execute_custom_default(self):
        """测试自定义默认值"""
        def failing_func():
            raise ValueError("error")

        result = safe_execute(failing_func, default="fallback")
        assert result == "fallback"

    def test_safe_execute_with_on_error(self):
        """测试错误回调"""
        def failing_func():
            raise ValueError("error")

        def error_handler(e):
            return f"handled: {e}"

        result = safe_execute(failing_func, on_error=error_handler)
        assert "handled: error" in result


class TestAsyncSafeExecute:
    """async_safe_execute函数测试"""

    @pytest.mark.asyncio
    async def test_async_safe_execute_success(self):
        """测试异步函数成功执行"""
        async def success_func():
            return "success"

        result = await async_safe_execute(success_func)
        assert result == "success"

    @pytest.mark.asyncio
    async def test_async_safe_execute_error_returns_default(self, caplog):
        """测试异步函数错误时返回默认值"""
        async def failing_func():
            raise ValueError("error")

        with caplog.at_level(logging.ERROR):
            result = await async_safe_execute(failing_func, default=None)

        assert result is None
        assert len(caplog.records) > 0

    @pytest.mark.asyncio
    async def test_async_safe_execute_with_args(self):
        """测试异步函数带参数"""
        async def add(a, b):
            return a + b

        result = await async_safe_execute(add, 1, 2)
        assert result == 3


class TestIntegration:
    """集成测试"""

    def test_error_handler_workflow(self, caplog):
        """测试错误处理完整工作流"""
        handler = ErrorHandler("integration_test")

        with caplog.at_level(logging.ERROR):
            # 1. 处理第一个错误
            handler.handle_error(ValueError("error 1"), context="operation 1")

            # 2. 处理第二个错误
            handler.handle_error(RuntimeError("error 2"), context="operation 2")

            # 3. 获取统计
            stats = handler.get_stats()

        assert stats["total_errors"] == 2
        assert "error 2" in stats["last_error"]

    @pytest.mark.asyncio
    async def test_async_handler_with_retry(self, caplog):
        """测试异步错误处理与重试组合"""
        call_count = 0

        @async_error_handler("test")
        @retry_on_error(max_attempts=3, delay=0.01)
        async def sometimes_failing():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise ValueError("temp error")
            return "success"

        with caplog.at_level(logging.WARNING):
            result = await sometimes_failing()

        assert result == "success"
        assert call_count == 2

    def test_sync_handler_with_safe_execute(self, caplog):
        """测试同步错误处理与安全执行组合"""
        @sync_error_handler("test")
        def risky_operation(value):
            if value < 0:
                raise ValueError("negative value")
            return value * 2

        with caplog.at_level(logging.ERROR):
            # 成功情况
            result1 = safe_execute(risky_operation, 5)
            assert result1 == 10

            # 失败情况
            result2 = safe_execute(risky_operation, -1, default=None)
            assert result2 is None


class TestEdgeCases:
    """边缘情况测试"""

    def test_error_handler_empty_context(self, caplog):
        """测试空上下文"""
        handler = ErrorHandler("test")

        with caplog.at_level(logging.ERROR):
            handler.handle_error(ValueError("error"), context="")

        assert handler.error_count == 1

    def test_error_handler_none_additional_info(self, caplog):
        """测试None附加信息"""
        handler = ErrorHandler("test")

        with caplog.at_level(logging.ERROR):
            handler.handle_error(ValueError("error"), additional_info=None)

        # 不应该崩溃
        assert handler.error_count == 1

    @pytest.mark.asyncio
    async def test_async_handler_no_context(self):
        """测试无上下文的异步装饰器"""
        @async_error_handler()
        async def test_func():
            return "success"

        result = await test_func()
        assert result == "success"

    def test_sync_handler_no_context(self):
        """测试无上下文的同步装饰器"""
        @sync_error_handler()
        def test_func():
            return "success"

        result = test_func()
        assert result == "success"

    def test_retry_zero_attempts(self):
        """测试0次尝试(实际上至少1次)"""
        @retry_on_error(max_attempts=1, delay=0.01)
        def failing_func():
            raise ValueError("error")

        with pytest.raises(ValueError):
            failing_func()

    def test_safe_execute_none_error_callback(self):
        """测试None错误回调"""
        def failing_func():
            raise ValueError("error")

        result = safe_execute(failing_func, on_error=None)
        assert result is None

    @pytest.mark.asyncio
    async def test_async_safe_execute_none_error_callback(self):
        """测试异步None错误回调"""
        async def failing_func():
            raise ValueError("error")

        result = await async_safe_execute(failing_func, on_error=None)
        assert result is None
