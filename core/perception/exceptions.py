#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
感知模块自定义异常类体系
Perception Module Custom Exception Hierarchy

提供完善的异常类型定义，更好地处理和报告错误

作者: Athena AI系统
创建时间: 2026-01-26
版本: 1.0.0
"""

from typing import Any, Optional


class PerceptionError(Exception):
    """感知模块基础异常类

    所有感知模块相关异常的基类
    """

    def __init__(self, message: str, error_code: str | None = None, details: dict[str, Any] | None = None):
        self.message = message
        self.error_code = error_code or "PERCEPTION_ERROR"
        self.details = details or {}
        super().__init__(self.message)

    def to_dict(self) -> dict:
        """转换为字典格式"""
        return {
            "error_type": self.__class__.__name__,
            "error_code": self.error_code,
            "message": self.message,
            "details": self.details
        }


class ProcessingError(PerceptionError):
    """处理错误

    当数据处理过程中发生错误时抛出
    """

    def __init__(self, message: str, processor_id: str | None = None, input_type: str | None = None):
        self.processor_id = processor_id
        self.input_type = input_type
        details = {}
        if processor_id:
            details["processor_id"] = processor_id
        if input_type:
            details["input_type"] = input_type
        super().__init__(message, "PROCESSING_ERROR", details)


class ValidationError(PerceptionError):
    """验证错误

    当输入验证失败时抛出
    """

    def __init__(self, message: str, field_name: str | None = None, value: Any = None):
        self.field_name = field_name
        details = {}
        if field_name:
            details["field_name"] = field_name
        if value is not None:
            details["value"] = str(value)[:100]  # 限制长度
        super().__init__(message, "VALIDATION_ERROR", details)


class InitializationError(PerceptionError):
    """初始化错误

    当处理器或引擎初始化失败时抛出
    """

    def __init__(self, message: str, component: str | None = None):
        details = {}
        if component:
            details["component"] = component
        super().__init__(message, "INITIALIZATION_ERROR", details)


class ConfigurationError(PerceptionError):
    """配置错误

    当配置无效或缺失时抛出
    """

    def __init__(self, message: str, config_key: str | None = None, config_value: Any = None):
        details = {}
        if config_key:
            details["config_key"] = config_key
        if config_value is not None:
            details["config_value"] = str(config_value)[:100]
        super().__init__(message, "CONFIGURATION_ERROR", details)


class ResourceError(PerceptionError):
    """资源错误

    当资源（内存、文件、网络等）不可用时抛出
    """

    def __init__(self, message: str, resource_type: str | None = None, resource_path: str | None = None):
        details = {}
        if resource_type:
            details["resource_type"] = resource_type
        if resource_path:
            details["resource_path"] = resource_path
        super().__init__(message, "RESOURCE_ERROR", details)


class ModelLoadError(ResourceError):
    """模型加载错误

    当AI模型加载失败时抛出
    """

    def __init__(self, message: str, model_name: str | None = None):
        self.model_name = model_name
        super().__init__(message, "model", model_name)
        self.error_code = "MODEL_LOAD_ERROR"


class FileReadError(ResourceError):
    """文件读取错误

    当文件读取失败时抛出
    """

    def __init__(self, message: str, file_path: str | None = None):
        self.file_path = file_path
        super().__init__(message, "file", file_path)
        self.error_code = "FILE_READ_ERROR"


class NetworkError(PerceptionError):
    """网络错误

    当网络请求失败时抛出
    """

    def __init__(self, message: str, url: str | None = None, status_code: int | None = None):
        self.url = url
        self.status_code = status_code
        details: dict[str, str | int] = {}
        if url:
            details["url"] = url
        if status_code is not None:
            details["status_code"] = status_code
        super().__init__(message, "NETWORK_ERROR", details)


class TimeoutError(PerceptionError):
    """超时错误

    当操作超时时抛出
    """

    def __init__(self, message: str, timeout_seconds: float | None = None):
        self.timeout_seconds = timeout_seconds
        details = {}
        if timeout_seconds:
            details["timeout_seconds"] = timeout_seconds
        super().__init__(message, "TIMEOUT_ERROR", details)


class RateLimitError(PerceptionError):
    """速率限制错误

    当超过速率限制时抛出
    """

    def __init__(self, message: str, retry_after: float | None = None):
        self.retry_after = retry_after
        details = {}
        if retry_after:
            details["retry_after"] = retry_after
        super().__init__(message, "RATE_LIMIT_ERROR", details)


class MemoryError(PerceptionError):
    """内存错误

    当内存不足时抛出
    """

    def __init__(self, message: str, required_mb: Optional[float] = None, available_mb: float | None = None):
        details = {}
        if required_mb:
            details["required_mb"] = required_mb
        if available_mb:
            details["available_mb"] = available_mb
        super().__init__(message, "MEMORY_ERROR", details)


class ConcurrencyError(PerceptionError):
    """并发错误

    当并发控制失败时抛出
    """

    def __init__(self, message: str, max_concurrent: int | None = None):
        details = {}
        if max_concurrent:
            details["max_concurrent"] = max_concurrent
        super().__init__(message, "CONCURRENCY_ERROR", details)


class CacheError(PerceptionError):
    """缓存错误

    当缓存操作失败时抛出
    """

    def __init__(self, message: str, cache_key: str | None = None, operation: str | None = None):
        details = {}
        if cache_key:
            details["cache_key"] = cache_key
        if operation:
            details["operation"] = operation
        super().__init__(message, "CACHE_ERROR", details)


class FormatError(PerceptionError):
    """格式错误

    当输入格式不正确时抛出
    """

    def __init__(self, message: str, expected_format: str | None = None, actual_format: str | None = None):
        details = {}
        if expected_format:
            details["expected_format"] = expected_format
        if actual_format:
            details["actual_format"] = actual_format
        super().__init__(message, "FORMAT_ERROR", details)


class ImageFormatError(FormatError):
    """图像格式错误"""

    def __init__(self, message: str, supported_formats: list[str] | None = None):
        details = {}
        if supported_formats:
            details["supported_formats"] = ", ".join(supported_formats)
        super().__init__(message)
        # 合并details到父类的details
        self.details.update(details)
        self.error_code = "IMAGE_FORMAT_ERROR"


class AudioFormatError(FormatError):
    """音频格式错误"""

    def __init__(self, message: str, supported_formats: list[str] | None = None):
        details = {}
        if supported_formats:
            details["supported_formats"] = ", ".join(supported_formats)
        super().__init__(message)
        # 合并details到父类的details
        self.details.update(details)
        self.error_code = "AUDIO_FORMAT_ERROR"


class VideoFormatError(FormatError):
    """视频格式错误"""

    def __init__(self, message: str, supported_formats: list[str] | None = None):
        details = {}
        if supported_formats:
            details["supported_formats"] = ", ".join(supported_formats)
        super().__init__(message)
        # 合并details到父类的details
        self.details.update(details)
        self.error_code = "VIDEO_FORMAT_ERROR"


# 导出所有异常类
__all__ = [
    # 基础异常
    "PerceptionError",

    # 处理相关
    "ProcessingError",
    "ValidationError",
    "InitializationError",
    "ConfigurationError",

    # 资源相关
    "ResourceError",
    "ModelLoadError",
    "FileReadError",
    "NetworkError",
    "TimeoutError",
    "RateLimitError",
    "MemoryError",
    "ConcurrencyError",
    "CacheError",

    # 格式相关
    "FormatError",
    "ImageFormatError",
    "AudioFormatError",
    "VideoFormatError",
]
