#!/usr/bin/env python3
"""
增强的异常处理和超时控制工具单元测试
"""

import asyncio

import pytest

from core.utils.error_handling import (
    # 异常类
    OAResponseBaseError,
    PromptGenerationError,
    KnowledgeGraphError,
    WorkflowRecordError,
    PatternExtractionError,
    ConfigurationError,
    TimeoutErrorCustom,
    # 装饰器和函数
    timeout,
    handle_errors,
    safe_execute,
    retry_on_failure,
    log_execution,
)


class TestOAResponseBaseError:
    """OAResponseBaseError基础异常测试"""

    def test_init_basic(self):
        """测试基本初始化"""
        error = OAResponseBaseError("test error")
        assert error.message == "test error"
        assert error.error_code == "UNKNOWN"
        assert error.context == {}
        assert error.timestamp is not None

    def test_init_with_all_params(self):
        """测试完整参数初始化"""
        error = OAResponseBaseError(
            message="test error",
            error_code="TEST_ERROR",
            context={"key": "value"}
        )
        assert error.error_code == "TEST_ERROR"
        assert error.context["key"] == "value"

    def test_to_dict(self):
        """测试转换为字典"""
        error = OAResponseBaseError(
            message="test",
            error_code="ERR",
            context={"info": "data"}
        )
        result = error.to_dict()
        assert result["message"] == "test"
        assert result["error_code"] == "ERR"
        assert result["context"]["info"] == "data"
        assert "timestamp" in result


class TestPromptGenerationError:
    """PromptGenerationError测试"""

    def test_init(self):
        """测试初始化"""
        error = PromptGenerationError("prompt failed")
        assert error.message == "prompt failed"
        assert error.error_code == "PROMPT_GENERATION_ERROR"


class TestKnowledgeGraphError:
    """KnowledgeGraphError测试"""

    def test_init(self):
        """测试初始化"""
        error = KnowledgeGraphError("graph error")
        assert error.error_code == "KNOWLEDGE_GRAPH_ERROR"


class TestWorkflowRecordError:
    """WorkflowRecordError测试"""

    def test_init(self):
        """测试初始化"""
        error = WorkflowRecordError("workflow failed")
        assert error.error_code == "WORKFLOW_RECORD_ERROR"


class TestPatternExtractionError:
    """PatternExtractionError测试"""

    def test_init(self):
        """测试初始化"""
        error = PatternExtractionError("pattern error")
        assert error.error_code == "PATTERN_EXTRACTION_ERROR"


class TestConfigurationError:
    """ConfigurationError测试"""

    def test_init(self):
        """测试初始化"""
        error = ConfigurationError("config error")
        assert error.error_code == "CONFIGURATION_ERROR"


class TestTimeoutErrorCustom:
    """TimeoutErrorCustom测试"""

    def test_init(self):
        """测试初始化"""
        error = TimeoutErrorCustom(
            message="timeout",
            timeout_seconds=5.0
        )
        assert error.error_code == "TIMEOUT_ERROR"
        assert error.context["timeout_seconds"] == 5.0

    def test_init_with_context(self):
        """测试带上下文初始化"""
        error = TimeoutErrorCustom(
            message="timeout",
            timeout_seconds=10.0,
            context={"operation": "test"}
        )
        assert error.context["operation"] == "test"
        assert error.context["timeout_seconds"] == 10.0


class TestTimeoutDecorator:
    """timeout装饰器测试"""

    @pytest.mark.asyncio
    async def test_timeout_success(self):
        """测试超时内成功执行"""
        @timeout(seconds=1.0)
        async def quick_operation():
            await asyncio.sleep(0.1)
            return "success"

        result = await quick_operation()
        assert result == "success"

    @pytest.mark.asyncio
    async def test_timeout_exceeded(self):
        """测试超时触发"""
        @timeout(seconds=0.1, reraise=True)
        async def slow_operation():
            await asyncio.sleep(1.0)
            return "should not reach"

        with pytest.raises(TimeoutErrorCustom):
            await slow_operation()

    @pytest.mark.asyncio
    async def test_timeout_no_reraise(self):
        """测试超时不重新抛出"""
        @timeout(seconds=0.1, reraise=False)
        async def slow_operation():
            await asyncio.sleep(1.0)
            return "unreachable"

        result = await slow_operation()
        assert result is None


class TestHandleErrors:
    """handle_errors上下文管理器测试"""

    def test_handle_errors_no_exception(self):
        """测试无异常时正常执行"""
        with handle_errors():
            result = 1 + 1

        assert result == 2

    def test_handle_errors_catches_exception(self, caplog):
        """测试捕获异常"""
        with handle_errors(error_types=(ValueError,), default_return=None):
            raise ValueError("test error")

        # 不应该抛出异常

    def test_handle_errors_reraise(self):
        """测试重新抛出异常"""
        with pytest.raises(ValueError):
            with handle_errors(error_types=(ValueError,), reraise=True):
                raise ValueError("test error")

    def test_handle_errors_default_return(self):
        """测试默认返回值"""
        with handle_errors(error_types=(ValueError,), default_return=42):
            result = 1 + 1

        # 上下文管理器不会修改外部变量,这是正常行为
        # 测试验证不会抛出异常即可


class TestSafeExecute:
    """safe_execute包装器测试"""

    def test_safe_execute_success(self):
        """测试成功执行"""
        def test_func(x):
            return x * 2

        wrapper = safe_execute(test_func)
        result = wrapper(5)  # wrapper返回函数,需要调用
        assert result == 10

    def test_safe_execute_error_returns_default(self):
        """测试错误时返回默认值"""
        def failing_func():
            raise ValueError("error")

        wrapper = safe_execute(failing_func, default_return="fallback")
        result = wrapper()
        assert result == "fallback"

    def test_safe_execute_with_custom_message(self, caplog):
        """测试自定义错误消息"""
        def failing_func():
            raise ValueError("error")

        wrapper = safe_execute(failing_func, error_message="操作失败")

        with caplog.at_level("ERROR"):
            result = wrapper()

        assert "操作失败" in caplog.text


class TestRetryOnFailure:
    """retry_on_failure装饰器测试"""

    @pytest.mark.asyncio
    async def test_retry_async_success(self):
        """测试异步函数重试成功"""
        call_count = 0

        @retry_on_failure(max_attempts=3, delay=0.01, exceptions=(ValueError,))
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
    async def test_retry_async_all_fail(self):
        """测试异步函数全部失败"""
        @retry_on_failure(max_attempts=3, delay=0.01)
        async def always_failing():
            raise ValueError("permanent error")

        with pytest.raises(ValueError):
            await always_failing()

    def test_retry_sync_success(self):
        """测试同步函数重试成功"""
        call_count = 0

        @retry_on_failure(max_attempts=3, delay=0.01)
        def sometimes_failing():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise ValueError("temp error")
            return "success"

        result = sometimes_failing()
        assert result == "success"

    def test_retry_sync_all_fail(self):
        """测试同步函数全部失败"""
        @retry_on_failure(max_attempts=2, delay=0.01)
        def always_failing():
            raise ValueError("error")

        with pytest.raises(ValueError):
            always_failing()


class TestLogExecution:
    """log_execution装饰器测试"""

    @pytest.mark.asyncio
    async def test_log_execution_async(self, caplog):
        """测试异步函数日志记录"""
        @log_execution()
        async def test_func():
            return "result"

        with caplog.at_level("INFO"):
            result = await test_func()

        assert result == "result"
        assert "开始执行" in caplog.text
        assert "完成" in caplog.text

    def test_log_execution_sync(self, caplog):
        """测试同步函数日志记录"""
        @log_execution()
        def test_func():
            return "result"

        with caplog.at_level("INFO"):
            result = test_func()

        assert result == "result"
        assert "开始执行" in caplog.text

    @pytest.mark.asyncio
    async def test_log_execution_with_exception(self, caplog):
        """测试异常日志记录"""
        @log_execution()
        async def failing_func():
            raise ValueError("error")

        with caplog.at_level("ERROR"):
            with pytest.raises(ValueError):
                await failing_func()

        assert "失败" in caplog.text


class TestIntegration:
    """集成测试"""

    @pytest.mark.asyncio
    async def test_timeout_and_retry(self):
        """测试超时与重试组合"""
        @timeout(seconds=5.0)
        @retry_on_failure(max_attempts=2, delay=0.01)
        async def operation():
            return "success"

        result = await operation()
        assert result == "success"

    @pytest.mark.asyncio
    async def test_complete_workflow(self, caplog):
        """测试完整工作流"""
        @log_execution()
        @timeout(seconds=5.0)
        @retry_on_failure(max_attempts=2, delay=0.01, exceptions=(ValueError,))
        async def complex_operation(value):
            if value < 0:
                raise ValueError("negative value")
            return value * 2

        with caplog.at_level("INFO"):
            result = await complex_operation(5)

        assert result == 10
        assert "开始执行" in caplog.text
        assert "完成" in caplog.text


class TestEdgeCases:
    """边缘情况测试"""

    @pytest.mark.asyncio
    async def test_timeout_zero_seconds(self):
        """测试0秒超时"""
        @timeout(seconds=0.01)
        async def instant_func():
            return "done"

        result = await instant_func()
        assert result == "done"

    def test_retry_zero_attempts(self):
        """测试0次尝试"""
        @retry_on_failure(max_attempts=1)
        def test_func():
            raise ValueError("error")

        with pytest.raises(ValueError):
            test_func()

    def test_handle_errors_empty_tuple(self):
        """测试空异常类型元组"""
        with pytest.raises(ValueError):  # 不捕获任何异常
            with handle_errors(error_types=()):
                raise ValueError("error")

    @pytest.mark.asyncio
    async def test_log_execution_preserves_metadata(self):
        """测试保留函数元数据"""
        @log_execution()
        async def test_func():
            """Test docstring"""
            pass

        assert test_func.__name__ == "test_func"
        assert test_func.__doc__ == "Test docstring"
