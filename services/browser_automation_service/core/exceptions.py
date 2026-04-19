#!/usr/bin/env python3
"""
异常处理模块
Exception Handling Module for Browser Automation Service

提供统一的异常类和错误码规范

作者: 小诺·双鱼公主
版本: 1.0.0
"""

from enum import Enum
from typing import Any


class ErrorCode(str, Enum):
    """
    错误码枚举

    格式: BROWSER_<模块>_<错误类型>_<数字>
    """

    # 通用错误 (1000-1999)
    UNKNOWN_ERROR = "BROWSER_COMMON_0000"
    INTERNAL_ERROR = "BROWSER_COMMON_0001"
    INVALID_REQUEST = "BROWSER_COMMON_0002"
    INVALID_PARAMETER = "BROWSER_COMMON_0003"
    MISSING_PARAMETER = "BROWSER_COMMON_0004"
    OPERATION_TIMEOUT = "BROWSER_COMMON_0005"

    # 认证错误 (2000-2999)
    UNAUTHORIZED = "BROWSER_AUTH_2000"
    INVALID_TOKEN = "BROWSER_AUTH_2001"
    TOKEN_EXPIRED = "BROWSER_AUTH_2002"
    INVALID_API_KEY = "BROWSER_AUTH_2003"
    INSUFFICIENT_PERMISSION = "BROWSER_AUTH_2004"

    # 浏览器错误 (3000-3999)
    BROWSER_NOT_INITIALIZED = "BROWSER_ENGINE_3000"
    BROWSER_START_FAILED = "BROWSER_ENGINE_3001"
    BROWSER_CRASHED = "BROWSER_ENGINE_3002"
    CONTEXT_NOT_FOUND = "BROWSER_ENGINE_3003"
    PAGE_NOT_FOUND = "BROWSER_ENGINE_3004"

    # 导航错误 (4000-4999)
    NAVIGATION_FAILED = "BROWSER_NAVIGATE_4000"
    INVALID_URL = "BROWSER_NAVIGATE_4001"
    NAVIGATION_TIMEOUT = "BROWSER_NAVIGATE_4002"
    NETWORK_ERROR = "BROWSER_NAVIGATE_4003"

    # 元素操作错误 (5000-5999)
    ELEMENT_NOT_FOUND = "BROWSER_ELEMENT_5000"
    ELEMENT_NOT_VISIBLE = "BROWSER_ELEMENT_5001"
    ELEMENT_NOT_INTERACTABLE = "BROWSER_ELEMENT_5002"
    CLICK_FAILED = "BROWSER_ELEMENT_5003"
    FILL_FAILED = "BROWSER_ELEMENT_5004"

    # 会话错误 (6000-6999)
    SESSION_NOT_FOUND = "BROWSER_SESSION_6000"
    SESSION_EXPIRED = "BROWSER_SESSION_6001"
    SESSION_LIMIT_EXCEEDED = "BROWSER_SESSION_6002"
    SESSION_CREATE_FAILED = "BROWSER_SESSION_6003"

    # 任务执行错误 (7000-7999)
    TASK_EXECUTION_FAILED = "BROWSER_TASK_7000"
    TASK_PARSE_FAILED = "BROWSER_TASK_7001"
    TASK_TIMEOUT = "BROWSER_TASK_7002"
    TASK_STEPS_EXCEEDED = "BROWSER_TASK_7003"

    # 资源错误 (8000-8999)
    RESOURCE_EXHAUSTED = "BROWSER_RESOURCE_8000"
    MEMORY_LIMIT_EXCEEDED = "BROWSER_RESOURCE_8001"
    CONCURRENT_LIMIT_EXCEEDED = "BROWSER_RESOURCE_8002"

    # JavaScript执行错误 (9000-9999)
    JS_EXECUTION_FAILED = "BROWSER_JS_9000"
    JS_TIMEOUT = "BROWSER_JS_9001"
    JS_INVALID_SCRIPT = "BROWSER_JS_9002"
    JS_SANDBOX_VIOLATION = "BROWSER_JS_9003"


class BrowserServiceException(Exception):
    """
    浏览器服务基础异常类

    所有自定义异常的基类
    """

    def __init__(
        self,
        message: str,
        code: ErrorCode = ErrorCode.UNKNOWN_ERROR,
        details: dict[str, Any] | None = None,
        error_id: str | None = None,
    ):
        """
        初始化异常

        Args:
            message: 错误消息
            code: 错误码
            details: 错误详情
            error_id: 错误追踪ID
        """
        self.message = message
        self.code = code
        self.details = details or {}
        self.error_id = error_id

        # 构建完整的错误消息
        full_message = f"[{code.value}]"
        if error_id:
            full_message += f"[{error_id}]"
        full_message += f" {message}"

        super().__init__(full_message)

    def to_dict(self) -> dict[str, Any]:
        """
        转换为字典格式

        Returns:
            dict: 错误信息字典
        """
        return {
            "success": False,
            "error": self.code.value,
            "message": self.message,
            "error_id": self.error_id,
            "details": self.details,
        }


# =============================================================================
# 认证异常
# =============================================================================


class AuthenticationError(BrowserServiceException):
    """认证错误"""

    def __init__(
        self,
        message: str = "认证失败",
        details: dict[str, Any] | None = None,
        error_id: str | None = None,
    ):
        super().__init__(
            message=message,
            code=ErrorCode.UNAUTHORIZED,
            details=details,
            error_id=error_id,
        )


class InvalidTokenError(AuthenticationError):
    """无效令牌错误"""

    def __init__(
        self,
        message: str = "无效的令牌",
        details: dict[str, Any] | None = None,
    ):
        super().__init__(
            message=message,
            code=ErrorCode.INVALID_TOKEN,
            details=details,
        )


class TokenExpiredError(AuthenticationError):
    """令牌过期错误"""

    def __init__(
        self,
        message: str = "令牌已过期",
        details: dict[str, Any] | None = None,
    ):
        super().__init__(
            message=message,
            code=ErrorCode.TOKEN_EXPIRED,
            details=details,
        )


class AuthorizationError(BrowserServiceException):
    """授权错误"""

    def __init__(
        self,
        message: str = "权限不足",
        details: dict[str, Any] | None = None,
        error_id: str | None = None,
    ):
        super().__init__(
            message=message,
            code=ErrorCode.INSUFFICIENT_PERMISSION,
            details=details,
            error_id=error_id,
        )


# =============================================================================
# 浏览器异常
# =============================================================================


class BrowserEngineError(BrowserServiceException):
    """浏览器引擎错误"""

    def __init__(
        self,
        message: str,
        code: ErrorCode = ErrorCode.BROWSER_NOT_INITIALIZED,
        details: dict[str, Any] | None = None,
    ):
        super().__init__(
            message=message,
            code=code,
            details=details,
        )


class NavigationError(BrowserServiceException):
    """导航错误"""

    def __init__(
        self,
        message: str,
        url: str | None = None,
        code: ErrorCode = ErrorCode.NAVIGATION_FAILED,
        details: dict[str, Any] | None = None,
    ):
        details = details or {}
        if url:
            details["url"] = url

        super().__init__(
            message=message,
            code=code,
            details=details,
        )


class ElementOperationError(BrowserServiceException):
    """元素操作错误"""

    def __init__(
        self,
        message: str,
        selector: str | None = None,
        code: ErrorCode = ErrorCode.ELEMENT_NOT_FOUND,
        details: dict[str, Any] | None = None,
    ):
        details = details or {}
        if selector:
            details["selector"] = selector

        super().__init__(
            message=message,
            code=code,
            details=details,
        )


# =============================================================================
# 会话异常
# =============================================================================


class SessionError(BrowserServiceException):
    """会话错误"""

    def __init__(
        self,
        message: str,
        session_id: str | None = None,
        code: ErrorCode = ErrorCode.SESSION_NOT_FOUND,
        details: dict[str, Any] | None = None,
    ):
        details = details or {}
        if session_id:
            details["session_id"] = session_id

        super().__init__(
            message=message,
            code=code,
            details=details,
        )


class SessionLimitExceededError(SessionError):
    """会话数量超限错误"""

    def __init__(
        self,
        message: str = "会话数量已达上限",
        limit: int | None = None,
        details: dict[str, Any] | None = None,
    ):
        details = details or {}
        if limit:
            details["limit"] = limit

        super().__init__(
            message=message,
            code=ErrorCode.SESSION_LIMIT_EXCEEDED,
            details=details,
        )


# =============================================================================
# 任务异常
# =============================================================================


class TaskExecutionError(BrowserServiceException):
    """任务执行错误"""

    def __init__(
        self,
        message: str,
        task: str | None = None,
        step: int | None = None,
        code: ErrorCode = ErrorCode.TASK_EXECUTION_FAILED,
        details: dict[str, Any] | None = None,
    ):
        details = details or {}
        if task:
            details["task"] = task
        if step is not None:
            details["failed_at_step"] = step

        super().__init__(
            message=message,
            code=code,
            details=details,
        )


class TaskTimeoutError(TaskExecutionError):
    """任务超时错误"""

    def __init__(
        self,
        message: str = "任务执行超时",
        timeout: int | None = None,
        details: dict[str, Any] | None = None,
    ):
        details = details or {}
        if timeout:
            details["timeout_seconds"] = timeout

        super().__init__(
            message=message,
            code=ErrorCode.TASK_TIMEOUT,
            details=details,
        )


# =============================================================================
# JavaScript执行异常
# =============================================================================


class JavaScriptExecutionError(BrowserServiceException):
    """JavaScript执行错误"""

    def __init__(
        self,
        message: str,
        script: str | None = None,
        code: ErrorCode = ErrorCode.JS_EXECUTION_FAILED,
        details: dict[str, Any] | None = None,
    ):
        details = details or {}
        if script:
            details["script"] = script[:100]  # 只保留前100个字符

        super().__init__(
            message=message,
            code=code,
            details=details,
        )


class JavaScriptSandboxViolation(JavaScriptExecutionError):
    """JavaScript沙箱违规错误"""

    def __init__(
        self,
        message: str = "JavaScript操作违反沙箱限制",
        operation: str | None = None,
        details: dict[str, Any] | None = None,
    ):
        details = details or {}
        if operation:
            details["operation"] = operation

        super().__init__(
            message=message,
            code=ErrorCode.JS_SANDBOX_VIOLATION,
            details=details,
        )


# =============================================================================
# 资源异常
# =============================================================================


class ResourceError(BrowserServiceException):
    """资源错误"""

    def __init__(
        self,
        message: str,
        code: ErrorCode = ErrorCode.RESOURCE_EXHAUSTED,
        details: dict[str, Any] | None = None,
    ):
        super().__init__(
            message=message,
            code=code,
            details=details,
        )


class ConcurrentLimitExceededError(ResourceError):
    """并发限制超限错误"""

    def __init__(
        self,
        message: str = "并发请求数超过限制",
        limit: int | None = None,
        details: dict[str, Any] | None = None,
    ):
        details = details or {}
        if limit:
            details["limit"] = limit

        super().__init__(
            message=message,
            code=ErrorCode.CONCURRENT_LIMIT_EXCEEDED,
            details=details,
        )


# =============================================================================
# 辅助函数
# =============================================================================


def generate_error_id() -> str:
    """生成错误追踪ID"""
    import uuid

    return f"ERR-{uuid.uuid4().hex[:12].upper()}"


def create_exception_response(
    exception: BrowserServiceException,
    include_traceback: bool = False,
) -> dict[str, Any]:
    """
    创建异常响应

    Args:
        exception: 异常对象
        include_traceback: 是否包含堆栈跟踪

    Returns:
        dict: 响应字典
    """
    response = exception.to_dict()

    if include_traceback:
        import traceback

        response["traceback"] = traceback.format_exc()

    return response


# 导出
__all__ = [
    "ErrorCode",
    "BrowserServiceException",
    "AuthenticationError",
    "InvalidTokenError",
    "TokenExpiredError",
    "AuthorizationError",
    "BrowserEngineError",
    "NavigationError",
    "ElementOperationError",
    "SessionError",
    "SessionLimitExceededError",
    "TaskExecutionError",
    "TaskTimeoutError",
    "JavaScriptExecutionError",
    "JavaScriptSandboxViolation",
    "ResourceError",
    "ConcurrentLimitExceededError",
    "generate_error_id",
    "create_exception_response",
]
