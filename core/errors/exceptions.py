#!/usr/bin/env python3
"""
统一异常定义 - Athena平台异常体系
Unified Exception Definitions - Athena Platform Exception Hierarchy

定义所有自定义异常类,提供一致的错误处理接口

作者: Athena平台团队
创建时间: 2026-01-16
版本: 1.0.0
"""

from datetime import datetime
from typing import Any, Dict, Optional


class AthenaException(Exception):
    """
    基础异常类

    所有Athena平台自定义异常的基类

    Attributes:
        message: 错误消息
        code: 错误代码
        status_code: HTTP状态码
        details: 额外错误详情
    """

    def __init__(
        self,
        message: str,
        code: str = "INTERNAL_ERROR",
        status_code: int = 500,
        details: dict[str, Any] | None = None,
    ):
        self.message = message
        self.code = code
        self.status_code = status_code
        self.details = details or {}
        self.timestamp = datetime.now()
        super().__init__(self.message)

    def to_dict(self) -> dict[str, Any]:
        """转换为字典格式"""
        return {
            "error": {
                "code": self.code,
                "message": self.message,
                "details": self.details,
                "timestamp": self.timestamp.isoformat(),
            }
        }

    def __str__(self) -> str:
        return f"[{self.code}] {self.message}"


# 别名
AthenaError = AthenaException


# ============================================================================
# 文件相关异常
# ============================================================================


class FileException(AthenaException):
    """文件操作异常基类"""

    def __init__(
        self,
        message: str,
        file_path: str | None = None,
        code: str = "FILE_ERROR",
        status_code: int = 500,
        details: dict[str, Any] | None = None,
    ):
        details = details or {}
        if file_path:
            details["file_path"] = file_path
        super().__init__(message, code, status_code, details)


class FileUploadException(FileException):
    """文件上传异常"""

    def __init__(
        self,
        message: str,
        file_path: str | None = None,
        details: dict[str, Any] | None = None,
    ):
        super().__init__(
            message, file_path, code="FILE_UPLOAD_ERROR", status_code=400, details=details
        )


class FileProcessingException(FileException):
    """文件处理异常"""

    def __init__(
        self,
        message: str,
        file_path: str | None = None,
        operation: str | None = None,
        details: dict[str, Any] | None = None,
    ):
        details = details or {}
        if operation:
            details["operation"] = operation
        super().__init__(
            message, file_path, code="FILE_PROCESSING_ERROR", status_code=500, details=details
        )


class FileNotFoundException(FileException):
    """文件未找到异常"""

    def __init__(self, file_path: str, details: dict[str, Any] | None = None):
        super().__init__(
            f"文件未找到: {file_path}",
            file_path,
            code="FILE_NOT_FOUND",
            status_code=404,
            details=details,
        )


class FileValidationException(FileException):
    """文件验证异常"""

    def __init__(
        self,
        message: str,
        file_path: str | None = None,
        validation_errors: list | None = None,
        details: dict[str, Any] | None = None,
    ):
        details = details or {}
        if validation_errors:
            details["validation_errors"] = validation_errors
        super().__init__(
            message, file_path, code="FILE_VALIDATION_ERROR", status_code=400, details=details
        )


class FileSizeException(FileException):
    """文件大小异常"""

    def __init__(
        self,
        file_path: str,
        file_size: int,
        max_size: int,
        details: dict[str, Any] | None = None,
    ):
        details = details or {}
        details.update(
            {
                "file_size": file_size,
                "max_size": max_size,
                "size_mb": round(file_size / (1024 * 1024), 2),
                "max_mb": round(max_size / (1024 * 1024), 2),
            }
        )
        super().__init__(
            f"文件过大: {details['size_mb']}MB (最大 {details['max_mb']}MB)",
            file_path,
            code="FILE_SIZE_EXCEEDED",
            status_code=413,
            details=details,
        )


class FileTypeException(FileException):
    """文件类型异常"""

    def __init__(
        self,
        file_path: str,
        file_type: str,
        allowed_types: list,
        details: dict[str, Any] | None = None,
    ):
        details = details or {}
        details.update({"file_type": file_type, "allowed_types": allowed_types})
        super().__init__(
            f"不支持的文件类型: {file_type}",
            file_path,
            code="FILE_TYPE_NOT_ALLOWED",
            status_code=415,
            details=details,
        )


# ============================================================================
# 配置相关异常
# ============================================================================


class ConfigurationException(AthenaException):
    """配置异常"""

    def __init__(
        self,
        message: str,
        config_key: str | None = None,
        details: dict[str, Any] | None = None,
    ):
        details = details or {}
        if config_key:
            details["config_key"] = config_key
        super().__init__(message, code="CONFIGURATION_ERROR", status_code=500, details=details)


class MissingConfigException(ConfigurationException):
    """缺少配置异常"""

    def __init__(self, config_key: str, details: dict[str, Any] | None = None):
        super().__init__(
            f"缺少必需的配置: {config_key}",
            config_key,
            code="MISSING_CONFIG",
            status_code=500,
            details=details,
        )


class InvalidConfigException(ConfigurationException):
    """无效配置异常"""

    def __init__(
        self, config_key: str, value: Any, reason: str, details: dict[str, Any] | None = None
    ):
        details = details or {}
        details.update({"config_key": config_key, "value": str(value), "reason": reason})
        super().__init__(
            f"无效的配置值: {config_key} = {value} ({reason})",
            config_key,
            code="INVALID_CONFIG",
            status_code=500,
            details=details,
        )


# ============================================================================
# 缓存相关异常
# ============================================================================


class CacheException(AthenaException):
    """缓存异常基类"""

    def __init__(
        self,
        message: str,
        cache_key: str | None = None,
        code: str = "CACHE_ERROR",
        status_code: int = 500,
        details: dict[str, Any] | None = None,
    ):
        details = details or {}
        if cache_key:
            details["cache_key"] = cache_key
        super().__init__(message, code, status_code, details)


class CacheMissException(CacheException):
    """缓存未命中异常"""

    def __init__(self, cache_key: str, details: dict[str, Any] | None = None):
        super().__init__(
            f"缓存未命中: {cache_key}",
            cache_key,
            code="CACHE_MISS",
            status_code=404,
            details=details,
        )


# ============================================================================
# 网络相关异常
# ============================================================================


class NetworkException(AthenaException):
    """网络异常基类"""

    def __init__(
        self,
        message: str,
        url: str | None = None,
        status_code: int = 503,
        details: dict[str, Any] | None = None,
    ):
        details = details or {}
        if url:
            details["url"] = url
        super().__init__(message, code="NETWORK_ERROR", status_code=status_code, details=details)


class AuthenticationException(AthenaException):
    """认证异常"""

    def __init__(self, message: str = "认证失败", details: dict[str, Any] | None = None):
        super().__init__(message, code="AUTHENTICATION_ERROR", status_code=401, details=details)


class AuthorizationException(AthenaException):
    """授权异常"""

    def __init__(
        self,
        message: str = "权限不足",
        required_permission: str | None = None,
        details: dict[str, Any] = None,
    ):
        details = details or {}
        if required_permission:
            details["required_permission"] = required_permission
        super().__init__(message, code="AUTHORIZATION_ERROR", status_code=403, details=details)


class RequestTimeoutException(NetworkException):
    """请求超时异常"""

    def __init__(self, url: str, timeout: float, details: dict[str, Any] | None = None):
        details = details or {}
        details["timeout_seconds"] = timeout
        super().__init__(
            f"请求超时: {url} (超时时间: {timeout}秒)", url, status_code=504, details=details
        )


# ============================================================================
# 存储相关异常
# ============================================================================


class StorageException(AthenaException):
    """存储异常基类"""

    def __init__(
        self,
        message: str,
        storage_type: str | None = None,
        code: str = "STORAGE_ERROR",
        status_code: int = 500,
        details: dict[str, Any] | None = None,
    ):
        details = details or {}
        if storage_type:
            details["storage_type"] = storage_type
        super().__init__(message, code, status_code, details)


class DatabaseException(StorageException):
    """数据库异常"""

    def __init__(
        self, message: str, query: str | None = None, details: dict[str, Any] | None = None
    ):
        details = details or {}
        if query:
            details["query"] = query[:500]  # 限制查询长度
        super().__init__(
            message,
            storage_type="database",
            code="DATABASE_ERROR",
            status_code=500,
            details=details,
        )


class ConnectionException(StorageException):
    """连接异常"""

    def __init__(
        self,
        message: str,
        connection_string: str | None = None,
        details: dict[str, Any] | None = None,
    ):
        details = details or {}
        if connection_string:
            # 隐藏敏感信息
            safe_string = connection_string
            if "@" in connection_string:
                safe_string = connection_string[: connection_string.index("@") + 1]
            details["connection"] = safe_string
        super().__init__(
            message,
            storage_type="connection",
            code="CONNECTION_ERROR",
            status_code=503,
            details=details,
        )


# ============================================================================
# 验证相关异常
# ============================================================================


class ValidationException(AthenaException):
    """验证异常"""

    def __init__(
        self,
        message: str,
        field: str | None = None,
        value: Any | None = None,
        details: dict[str, Any] | None = None,
    ):
        details = details or {}
        if field:
            details["field"] = field
        if value is not None:
            details["value"] = str(value)[:500]
        super().__init__(message, code="VALIDATION_ERROR", status_code=400, details=details)


class RequiredFieldException(ValidationException):
    """必填字段缺失异常"""

    def __init__(self, field: str, details: dict[str, Any] | None = None):
        super().__init__(
            f"必填字段缺失: {field}", field=field, code="REQUIRED_FIELD", details=details
        )


class InvalidFormatException(ValidationException):
    """无效格式异常"""

    def __init__(
        self, field: str, value: Any, expected_format: str, details: dict[str, Any] | None = None
    ):
        details = details or {}
        details["expected_format"] = expected_format
        super().__init__(
            f"无效格式: {field} (期望格式: {expected_format})",
            field=field,
            value=value,
            code="INVALID_FORMAT",
            details=details,
        )


# ============================================================================
# 业务逻辑异常
# ============================================================================


class BusinessException(AthenaException):
    """业务逻辑异常基类"""

    def __init__(
        self,
        message: str,
        code: str = "BUSINESS_ERROR",
        status_code: int = 400,
        details: dict[str, Any] | None = None,
    ):
        super().__init__(message, code, status_code, details)


class ResourceNotFoundException(BusinessException):
    """资源未找到异常"""

    def __init__(
        self, resource_type: str, resource_id: str, details: dict[str, Any] | None = None
    ):
        details = details or {}
        details.update({"resource_type": resource_type, "resource_id": resource_id})
        super().__init__(
            f"{resource_type} 未找到: {resource_id}",
            code="RESOURCE_NOT_FOUND",
            status_code=404,
            details=details,
        )


class DuplicateResourceException(BusinessException):
    """重复资源异常"""

    def __init__(
        self, resource_type: str, identifier: str, details: dict[str, Any] | None = None
    ):
        details = details or {}
        details.update({"resource_type": resource_type, "identifier": identifier})
        super().__init__(
            f"{resource_type} 已存在: {identifier}",
            code="DUPLICATE_RESOURCE",
            status_code=409,
            details=details,
        )


class OperationNotAllowedException(BusinessException):
    """操作不允许异常"""

    def __init__(
        self,
        message: str,
        operation: str | None = None,
        reason: str | None = None,
        details: dict[str, Any] | None = None,
    ):
        details = details or {}
        if operation:
            details["operation"] = operation
        if reason:
            details["reason"] = reason
        super().__init__(message, code="OPERATION_NOT_ALLOWED", status_code=403, details=details)
