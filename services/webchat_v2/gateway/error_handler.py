#!/usr/bin/env python3
"""
Gateway错误处理器
提供统一的错误分类、格式化和响应

作者: Athena平台团队
创建时间: 2025-01-31
版本: 2.0.0
"""

from enum import IntEnum
from typing import Any, Dict, Optional
from datetime import datetime


class GatewayErrorCode(IntEnum):
    """Gateway错误码"""

    # 认证错误 (1000-1999)
    AUTH_TOKEN_MISSING = 1001
    AUTH_TOKEN_INVALID = 1002
    AUTH_TOKEN_EXPIRED = 1003
    AUTH_USER_MISMATCH = 1004
    AUTH_FAILED = 1005

    # 验证错误 (2000-2999)
    VALIDATION_FRAME_INVALID = 2001
    VALIDATION_MISSING_FIELD = 2002
    VALIDATION_INVALID_TYPE = 2003
    VALIDATION_MESSAGE_TOO_LARGE = 2004

    # 方法错误 (3000-3999)
    METHOD_UNKNOWN = 3001
    METHOD_MISSING_PARAM = 3002
    METHOD_FAILED = 3003
    METHOD_TIMEOUT = 3004

    # 模块错误 (4000-4999)
    MODULE_NOT_FOUND = 4001
    MODULE_ACTION_NOT_FOUND = 4002
    MODULE_INVOKE_FAILED = 4003
    MODULE_TIMEOUT = 4004

    # 会话错误 (5000-5999)
    SESSION_NOT_FOUND = 5001
    SESSION_LIMIT_EXCEEDED = 5002

    # 服务器错误 (9000-9999)
    INTERNAL_ERROR = 9001
    SERVICE_UNAVAILABLE = 9002


class GatewayError(Exception):
    """Gateway基础错误"""

    def __init__(
        self,
        message: str,
        code: GatewayErrorCode,
        details: Optional[Dict[str, Any]] = None
    ):
        self.message = message
        self.code = code
        self.details = details or {}
        super().__init__(self.message)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "error": {
                "code": int(self.code),
                "message": self.message,
                "details": self.details
            },
            "timestamp": datetime.utcnow().isoformat()
        }


class AuthenticationError(GatewayError):
    """认证错误"""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, GatewayErrorCode.AUTH_FAILED, details)


class ValidationError(GatewayError):
    """验证错误"""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, GatewayErrorCode.VALIDATION_FRAME_INVALID, details)


class MethodError(GatewayError):
    """方法错误"""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, GatewayErrorCode.METHOD_FAILED, details)


class ModuleError(GatewayError):
    """模块错误"""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, GatewayErrorCode.MODULE_INVOKE_FAILED, details)


class GatewayErrorHandler:
    """Gateway错误处理器"""

    @staticmethod
    def handle_websocket_close(code: int, reason: str) -> GatewayError:
        """
        处理WebSocket关闭错误

        Args:
            code: 关闭码
            reason: 关闭原因

        Returns:
            GatewayError实例
        """
        # 正常关闭
        if code == 1000:
            return None

        # 认证失败
        if code == 1008:
            return AuthenticationError(
                "认证失败",
                {"close_code": code, "reason": reason}
            )

        # 其他错误
        return GatewayError(
            f"连接关闭: {reason or '未知原因'}",
            GatewayErrorCode.SERVICE_UNAVAILABLE,
            {"close_code": code}
        )

    @staticmethod
    def handle_frame_validation_error(validation_result: Dict[str, Any]) -> ValidationError:
        """
        处理帧验证错误

        Args:
            validation_result: 验证结果

        Returns:
            ValidationError实例
        """
        return ValidationError(
            validation_result.get("error", "帧验证失败"),
            {"validation_error": validation_result.get("error")}
        )

    @staticmethod
    def handle_method_error(method: str, error: Exception) -> MethodError:
        """
        处理方法执行错误

        Args:
            method: 方法名
            error: 异常对象

        Returns:
            MethodError实例
        """
        error_message = str(error)

        # 根据错误类型确定错误码
        if "timeout" in error_message.lower():
            code = GatewayErrorCode.METHOD_TIMEOUT
        elif "not found" in error_message.lower():
            code = GatewayErrorCode.METHOD_UNKNOWN
        else:
            code = GatewayErrorCode.METHOD_FAILED

        return MethodError(
            f"方法执行失败: {method}",
            {
                "method": method,
                "error": error_message,
                "error_type": type(error).__name__
            }
        )

    @staticmethod
    def handle_module_error(module: str, action: str, error: Exception) -> ModuleError:
        """
        处理模块调用错误

        Args:
            module: 模块名
            action: 操作名
            error: 异常对象

        Returns:
            ModuleError实例
        """
        error_message = str(error)

        # 根据错误类型确定错误码
        if "not found" in error_message.lower():
            code = GatewayErrorCode.MODULE_NOT_FOUND
        elif "timeout" in error_message.lower():
            code = GatewayErrorCode.MODULE_TIMEOUT
        else:
            code = GatewayErrorCode.MODULE_INVOKE_FAILED

        return ModuleError(
            f"模块调用失败: {module}.{action}",
            {
                "module": module,
                "action": action,
                "error": error_message,
                "error_type": type(error).__name__
            }
        )

    @staticmethod
    def create_error_response(
        request_id: str,
        error: GatewayError
    ) -> Dict[str, Any]:
        """
        创建错误响应

        Args:
            request_id: 请求ID
            error: 错误对象

        Returns:
            响应帧字典
        """
        from ..gateway.protocol import GatewayProtocol

        # 使用create_response创建错误响应
        response = GatewayProtocol.create_response(
            request_id=request_id,
            error=error.message
        )

        # 添加错误详情
        response["error_code"] = int(error.code)
        if error.details:
            response["error_details"] = error.details

        return response

    @staticmethod
    def log_error(logger, error: GatewayError, context: Optional[Dict[str, Any]] = None):
        """
        记录错误

        Args:
            logger: 日志记录器
            error: 错误对象
            context: 上下文信息
        """
        log_context = {
            "error_code": int(error.code),
            "error_message": error.message
        }
        if error.details:
            log_context.update(error.details)
        if context:
            log_context.update(context)

        # 根据错误码范围确定日志级别
        if error.code >= 9000:
            logger.log_error("服务器错误", **log_context)
        elif error.code >= 4000:
            logger.log_warning("模块错误", **log_context)
        elif error.code >= 2000:
            logger.log_debug("验证错误", **log_context)
        else:
            logger.log_warning("错误", **log_context)


# 便捷函数
def create_auth_error(message: str, **details) -> AuthenticationError:
    """创建认证错误"""
    return AuthenticationError(message, details)


def create_validation_error(message: str, **details) -> ValidationError:
    """创建验证错误"""
    return ValidationError(message, details)


def create_method_error(method: str, message: str, **details) -> MethodError:
    """创建方法错误"""
    details["method"] = method
    return MethodError(message, details)


def create_module_error(module: str, action: str, message: str, **details) -> ModuleError:
    """创建模块错误"""
    details["module"] = module
    details["action"] = action
    return ModuleError(message, details)
