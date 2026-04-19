#!/usr/bin/env python3
"""
异常处理测试
Exception Handling Tests for Browser Automation Service

测试所有异常类和错误码

作者: 小诺·双鱼公主
版本: 1.0.0
"""

import pytest

from core.exceptions import (
    AuthenticationError,
    AuthorizationError,
    BrowserEngineError,
    BrowserServiceException,
    ConcurrentLimitExceededError,
    ElementOperationError,
    ErrorCode,
    InvalidTokenError,
    JavaScriptExecutionError,
    JavaScriptSandboxViolation,
    NavigationError,
    ResourceError,
    SessionError,
    SessionLimitExceededError,
    TaskExecutionError,
    TaskTimeoutError,
    TokenExpiredError,
    generate_error_id,
)


class TestErrorCode:
    """测试错误码枚举"""

    def test_error_code_format(self):
        """测试错误码格式"""
        assert ErrorCode.UNKNOWN_ERROR == "BROWSER_COMMON_0000"
        assert ErrorCode.UNAUTHORIZED == "BROWSER_AUTH_2000"
        assert ErrorCode.BROWSER_NOT_INITIALIZED == "BROWSER_ENGINE_3000"
        assert ErrorCode.NAVIGATION_FAILED == "BROWSER_NAVIGATE_4000"
        assert ErrorCode.ELEMENT_NOT_FOUND == "BROWSER_ELEMENT_5000"
        assert ErrorCode.SESSION_NOT_FOUND == "BROWSER_SESSION_6000"
        assert ErrorCode.TASK_EXECUTION_FAILED == "BROWSER_TASK_7000"
        assert ErrorCode.RESOURCE_EXHAUSTED == "BROWSER_RESOURCE_8000"
        assert ErrorCode.JS_EXECUTION_FAILED == "BROWSER_JS_9000"

    def test_error_code_categories(self):
        """测试错误码分类"""
        # 通用错误 (1000-1999)
        assert ErrorCode.INTERNAL_ERROR.value.startswith("BROWSER_COMMON_")

        # 认证错误 (2000-2999)
        assert ErrorCode.UNAUTHORIZED.value.startswith("BROWSER_AUTH_")

        # 浏览器错误 (3000-3999)
        assert ErrorCode.BROWSER_NOT_INITIALIZED.value.startswith("BROWSER_ENGINE_")

        # 导航错误 (4000-4999)
        assert ErrorCode.NAVIGATION_FAILED.value.startswith("BROWSER_NAVIGATE_")

        # 元素操作错误 (5000-5999)
        assert ErrorCode.ELEMENT_NOT_FOUND.value.startswith("BROWSER_ELEMENT_")

        # 会话错误 (6000-6999)
        assert ErrorCode.SESSION_NOT_FOUND.value.startswith("BROWSER_SESSION_")

        # 任务执行错误 (7000-7999)
        assert ErrorCode.TASK_EXECUTION_FAILED.value.startswith("BROWSER_TASK_")

        # 资源错误 (8000-8999)
        assert ErrorCode.RESOURCE_EXHAUSTED.value.startswith("BROWSER_RESOURCE_")

        # JavaScript执行错误 (9000-9999)
        assert ErrorCode.JS_EXECUTION_FAILED.value.startswith("BROWSER_JS_")


class TestGenerateErrorId:
    """测试错误ID生成"""

    def test_generate_error_id_format(self):
        """测试错误ID格式"""
        error_id = generate_error_id()
        assert error_id.startswith("ERR-")
        assert len(error_id) == 17  # ERR- + 12位hex

    def test_generate_error_id_unique(self):
        """测试错误ID唯一性"""
        ids = [generate_error_id() for _ in range(100)]
        assert len(set(ids)) == 100  # 全部唯一


class TestBrowserServiceException:
    """测试基础异常类"""

    def test_exception_creation(self):
        """测试异常创建"""
        exc = BrowserServiceException(
            message="测试错误",
            code=ErrorCode.UNKNOWN_ERROR,
            details={"key": "value"},
            error_id="ERR-TEST123",
        )

        assert str(exc) == "[BROWSER_COMMON_0000][ERR-TEST123] 测试错误"
        assert exc.message == "测试错误"
        assert exc.code == ErrorCode.UNKNOWN_ERROR
        assert exc.details == {"key": "value"}
        assert exc.error_id == "ERR-TEST123"

    def test_exception_to_dict(self):
        """测试异常转换为字典"""
        exc = BrowserServiceException(
            message="测试错误",
            code=ErrorCode.UNKNOWN_ERROR,
            error_id="ERR-TEST456",
        )

        result = exc.to_dict()

        assert result["success"] is False
        assert result["error"] == "BROWSER_COMMON_0000"
        assert result["message"] == "测试错误"
        assert result["error_id"] == "ERR-TEST456"
        assert result["details"] == {}

    def test_exception_without_error_id(self):
        """测试没有错误ID的异常"""
        exc = BrowserServiceException(
            message="测试错误",
            code=ErrorCode.UNKNOWN_ERROR,
        )

        assert exc.error_id is None
        assert "BROWSER_COMMON_0000" in str(exc)


class TestAuthenticationErrors:
    """测试认证异常"""

    def test_authentication_error(self):
        """测试认证错误"""
        exc = AuthenticationError(
            message="认证失败",
            error_id="ERR-AUTH001",
        )

        assert exc.code == ErrorCode.UNAUTHORIZED
        assert exc.message == "认证失败"
        assert exc.error_id == "ERR-AUTH001"

    def test_invalid_token_error(self):
        """测试无效令牌错误"""
        exc = InvalidTokenError(
            message="令牌无效",
            details={"token": "abc123"},
        )

        assert exc.code == ErrorCode.INVALID_TOKEN
        assert "令牌无效" in exc.message

    def test_token_expired_error(self):
        """测试令牌过期错误"""
        exc = TokenExpiredError()

        assert exc.code == ErrorCode.TOKEN_EXPIRED
        assert "过期" in exc.message

    def test_authorization_error(self):
        """测试授权错误"""
        exc = AuthorizationError(
            message="权限不足",
            details={"required": "admin", "current": "user"},
            error_id="ERR-AUTH002",
        )

        assert exc.code == ErrorCode.INSUFFICIENT_PERMISSION
        assert exc.details["required"] == "admin"


class TestBrowserEngineErrors:
    """测试浏览器引擎异常"""

    def test_browser_engine_error(self):
        """测试浏览器引擎错误"""
        exc = BrowserEngineError(
            message="浏览器未初始化",
            code=ErrorCode.BROWSER_NOT_INITIALIZED,
        )

        assert exc.code == ErrorCode.BROWSER_NOT_INITIALIZED

    def test_navigation_error(self):
        """测试导航错误"""
        exc = NavigationError(
            message="导航失败",
            url="https://example.com",
            details={"timeout": 30000},
        )

        assert exc.code == ErrorCode.NAVIGATION_FAILED
        assert exc.details["url"] == "https://example.com"
        assert exc.details["timeout"] == 30000

    def test_element_operation_error(self):
        """测试元素操作错误"""
        exc = ElementOperationError(
            message="元素未找到",
            selector="#submit-button",
            code=ErrorCode.ELEMENT_NOT_FOUND,
        )

        assert exc.code == ErrorCode.ELEMENT_NOT_FOUND
        assert exc.details["selector"] == "#submit-button"


class TestSessionErrors:
    """测试会话异常"""

    def test_session_error(self):
        """测试会话错误"""
        exc = SessionError(
            message="会话不存在",
            session_id="sess-123",
            code=ErrorCode.SESSION_NOT_FOUND,
        )

        assert exc.code == ErrorCode.SESSION_NOT_FOUND
        assert exc.details["session_id"] == "sess-123"

    def test_session_limit_exceeded_error(self):
        """测试会话限制超限错误"""
        exc = SessionLimitExceededError(
            message="会话数量已达上限",
            limit=10,
            details={"current": 10},
        )

        assert exc.code == ErrorCode.SESSION_LIMIT_EXCEEDED
        assert exc.details["limit"] == 10
        assert exc.details["current"] == 10


class TestTaskErrors:
    """测试任务异常"""

    def test_task_execution_error(self):
        """测试任务执行错误"""
        exc = TaskExecutionError(
            message="任务执行失败",
            task="打开百度并搜索",
            step=3,
            details={"error": "元素未找到"},
        )

        assert exc.code == ErrorCode.TASK_EXECUTION_FAILED
        assert exc.details["task"] == "打开百度并搜索"
        assert exc.details["failed_at_step"] == 3

    def test_task_timeout_error(self):
        """测试任务超时错误"""
        exc = TaskTimeoutError(
            message="任务执行超时",
            timeout=300,
        )

        assert exc.code == ErrorCode.TASK_TIMEOUT
        assert exc.details["timeout_seconds"] == 300


class TestJavaScriptErrors:
    """测试JavaScript异常"""

    def test_js_execution_error(self):
        """测试JavaScript执行错误"""
        exc = JavaScriptExecutionError(
            message="JavaScript执行失败",
            script="document.querySelector('.btn').click()",
            details={"line": 1},
        )

        assert exc.code == ErrorCode.JS_EXECUTION_FAILED
        # 检查脚本被截断
        assert len(exc.details["script"]) <= 100

    def test_js_sandbox_violation(self):
        """测试JavaScript沙箱违规"""
        exc = JavaScriptSandboxViolation(
            message="禁止使用危险操作",
            operation="window.location",
        )

        assert exc.code == ErrorCode.JS_SANDBOX_VIOLATION
        assert exc.details["operation"] == "window.location"


class TestResourceErrors:
    """测试资源异常"""

    def test_resource_error(self):
        """测试资源错误"""
        exc = ResourceError(
            message="资源耗尽",
            code=ErrorCode.MEMORY_LIMIT_EXCEEDED,
            details={"usage": "1.5GB", "limit": "1GB"},
        )

        assert exc.code == ErrorCode.MEMORY_LIMIT_EXCEEDED

    def test_concurrent_limit_exceeded_error(self):
        """测试并发限制超限错误"""
        exc = ConcurrentLimitExceededError(
            message="并发请求数超过限制",
            limit=5,
            details={"active": 5},
        )

        assert exc.code == ErrorCode.CONCURRENT_LIMIT_EXCEEDED
        assert exc.details["limit"] == 5


class TestExceptionChaining:
    """测试异常链"""

    def test_exception_from_exception(self):
        """测试从异常创建异常"""
        try:
            raise ValueError("原始错误")
        except ValueError as e:
            exc = BrowserServiceException(
                message="包装的错误",
                code=ErrorCode.INTERNAL_ERROR,
                details={"original_error": str(e)},
            )

        assert "包装的错误" in exc.message
        assert exc.details["original_error"] == "原始错误"


@pytest.mark.parametrize(
    "exception_class,code,message",
    [
        (AuthenticationError, ErrorCode.UNAUTHORIZED, "认证失败"),
        (InvalidTokenError, ErrorCode.INVALID_TOKEN, "无效令牌"),
        (TokenExpiredError, ErrorCode.TOKEN_EXPIRED, "令牌过期"),
        (AuthorizationError, ErrorCode.INSUFFICIENT_PERMISSION, "权限不足"),
        (BrowserEngineError, ErrorCode.BROWSER_NOT_INITIALIZED, "浏览器错误"),
        (NavigationError, ErrorCode.NAVIGATION_FAILED, "导航失败"),
        (ElementOperationError, ErrorCode.ELEMENT_NOT_FOUND, "元素错误"),
        (SessionError, ErrorCode.SESSION_NOT_FOUND, "会话错误"),
        (SessionLimitExceededError, ErrorCode.SESSION_LIMIT_EXCEEDED, "会话超限"),
        (TaskExecutionError, ErrorCode.TASK_EXECUTION_FAILED, "任务错误"),
        (TaskTimeoutError, ErrorCode.TASK_TIMEOUT, "任务超时"),
        (JavaScriptExecutionError, ErrorCode.JS_EXECUTION_FAILED, "JS错误"),
        (JavaScriptSandboxViolation, ErrorCode.JS_SANDBOX_VIOLATION, "沙箱违规"),
        (ResourceError, ErrorCode.RESOURCE_EXHAUSTED, "资源错误"),
        (ConcurrentLimitExceededError, ErrorCode.CONCURRENT_LIMIT_EXCEEDED, "并发超限"),
    ],
)
def test_all_exception_types(exception_class, code, message):
    """测试所有异常类型"""
    exc = exception_class(message=message)
    assert exc.code == code
    assert message in exc.message
    assert exc.to_dict()["success"] is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
