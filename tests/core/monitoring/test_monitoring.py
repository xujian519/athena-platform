"""
监控模块测试
"""


import pytest

from core.monitoring.logger import (
    UnifiedLogger,
    bind_context,
    get_logger,
)
from core.monitoring.metrics import (
    record_agent_execution,
    record_http_request,
)


class TestUnifiedLogger:
    """测试统一日志记录器"""

    def test_logger_creation(self):
        """测试日志记录器创建"""
        logger = get_logger("test")
        assert isinstance(logger, UnifiedLogger)

    def test_log_levels(self):
        """测试日志级别"""
        logger = get_logger("test")

        # 应该不抛出异常
        logger.debug("Debug message")
        logger.info("Info message")
        logger.warning("Warning message")
        logger.error("Error message")

    def test_log_with_context(self):
        """测试带上下文的日志"""
        logger = get_logger("test")

        # 应该不抛出异常
        logger.info("Test message", user_id="user-123", task_id="task-456")


class TestLogContext:
    """测试日志上下文"""

    def test_bind_context(self):
        """测试绑定上下文"""
        logger = get_logger("test")

        with bind_context(agent_id="xiaona-001"):
            logger.info("Test with context")
            # 上下文应该在with块内有效


class TestMetrics:
    """测试监控指标"""

    def test_record_http_request(self):
        """测试记录HTTP请求"""
        # 应该不抛出异常
        record_http_request(
            method="GET",
            endpoint="/api/test",
            status_code=200,
            duration=0.5
        )

    def test_record_agent_execution(self):
        """测试记录Agent执行"""
        # 应该不抛出异常
        record_agent_execution(
            agent_name="xiaona",
            status="success",
            duration=1.2
        )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
