from __future__ import annotations
"""
意图识别服务 - 统一异常处理体系

本模块定义了意图识别服务的所有异常类型,提供结构化错误处理。

Author: Xiaonuo
Created: 2025-01-17
Version: 1.0.0
"""

from typing import Any


class IntentRecognitionError(Exception):
    """
    意图识别基础异常类

    所有意图识别相关异常的基类,提供统一的错误信息和错误码。
    """

    def __init__(
        self,
        message: str,
        error_code: str = "INTENT_ERROR",
        details: Optional[dict[str, Any]] = None,
    ):
        """
        初始化异常

        Args:
            message: 错误消息
            error_code: 错误码,用于分类和追踪
            details: 额外的错误详情
        """
        self.message = message
        self.error_code = error_code
        self.details = details or {}
        super().__init__(self.message)

    def __str__(self) -> str:
        """返回格式化的错误信息"""
        base = f"[{self.error_code}] {self.message}"
        if self.details:
            details_str = ", ".join(f"{k}={v}" for k, v in self.details.items())
            return f"{base} | Details: {details_str}"
        return base

    def to_dict(self) -> dict[str, Any]:
        """转换为字典格式,便于API返回"""
        return {"error_code": self.error_code, "message": self.message, "details": self.details}


class ModelLoadError(IntentRecognitionError):
    """
    模型加载失败异常

    当模型文件不存在、加载失败或初始化错误时抛出。
    """

    def __init__(self, model_name: str, reason: str, details: Optional[dict[str, Any]] = None):
        self.model_name = model_name
        self.reason = reason
        full_details = {"model_name": model_name, "reason": reason}
        if details:
            full_details.update(details)

        super().__init__(
            message=f"模型加载失败: {model_name} - {reason}",
            error_code="MODEL_LOAD_ERROR",
            details=full_details,
        )


class ModelNotFoundError(ModelLoadError):
    """模型文件不存在异常"""

    def __init__(self, model_path: str):
        super().__init__(
            model_name=model_path, reason="模型文件或目录不存在", details={"model_path": model_path}
        )


class ModelInferenceError(IntentRecognitionError):
    """
    模型推理失败异常

    当模型推理过程中发生错误时抛出。
    """

    def __init__(
        self,
        model_name: str,
        input_text: str,
        reason: str,
        details: Optional[dict[str, Any]] = None,
    ):
        self.model_name = model_name
        self.input_text = input_text[:100]  # 只保留前100字符
        self.reason = reason
        full_details = {
            "model_name": model_name,
            "input_preview": self.input_text,
            "reason": reason,
        }
        if details:
            full_details.update(details)

        super().__init__(
            message=f"模型推理失败: {model_name} - {reason}",
            error_code="MODEL_INFERENCE_ERROR",
            details=full_details,
        )


class SemanticMatchError(IntentRecognitionError):
    """
    语义匹配失败异常

    当语义相似度匹配过程失败时抛出。
    """

    def __init__(
        self,
        query: str,
        candidates_count: int,
        reason: str,
        details: Optional[dict[str, Any]] = None,
    ):
        self.query = query[:100]
        self.candidates_count = candidates_count
        self.reason = reason
        full_details = {
            "query_preview": self.query,
            "candidates_count": candidates_count,
            "reason": reason,
        }
        if details:
            full_details.update(details)

        super().__init__(
            message=f"语义匹配失败 - {reason}",
            error_code="SEMANTIC_MATCH_ERROR",
            details=full_details,
        )


class ConfigurationError(IntentRecognitionError):
    """
    配置错误异常

    当配置文件缺失、格式错误或配置项无效时抛出。
    """

    def __init__(self, config_key: str, reason: str, details: Optional[dict[str, Any]] = None):
        self.config_key = config_key
        self.reason = reason
        full_details = {"config_key": config_key, "reason": reason}
        if details:
            full_details.update(details)

        super().__init__(
            message=f"配置错误: {config_key} - {reason}",
            error_code="CONFIG_ERROR",
            details=full_details,
        )


class CacheError(IntentRecognitionError):
    """
    缓存操作失败异常

    当缓存读写、连接或操作失败时抛出。
    """

    def __init__(
        self, cache_key: str, operation: str, reason: str, details: Optional[dict[str, Any]] = None
    ):
        self.cache_key = cache_key
        self.operation = operation
        self.reason = reason
        full_details = {"cache_key": cache_key, "operation": operation, "reason": reason}
        if details:
            full_details.update(details)

        super().__init__(
            message=f"缓存{operation}失败: {cache_key} - {reason}",
            error_code="CACHE_ERROR",
            details=full_details,
        )


class ValidationError(IntentRecognitionError):
    """
    输入验证失败异常

    当输入数据不符合要求时抛出。
    """

    def __init__(
        self,
        field_name: str,
        provided_value: Any,
        reason: str,
        details: Optional[dict[str, Any]] = None,
    ):
        self.field_name = field_name
        self.provided_value = str(provided_value)[:100]
        self.reason = reason
        full_details = {
            "field": field_name,
            "provided_value": self.provided_value,
            "reason": reason,
        }
        if details:
            full_details.update(details)

        super().__init__(
            message=f"输入验证失败: {field_name} - {reason}",
            error_code="VALIDATION_ERROR",
            details=full_details,
        )


class IntentRecognitionTimeoutError(IntentRecognitionError):
    """
    意图识别超时异常

    当识别操作超过指定时间限制时抛出。
    """

    def __init__(
        self, timeout_seconds: float, operation: str, details: Optional[dict[str, Any]] = None
    ):
        self.timeout_seconds = timeout_seconds
        self.operation = operation
        full_details = {"timeout_seconds": timeout_seconds, "operation": operation}
        if details:
            full_details.update(details)

        super().__init__(
            message=f"操作超时: {operation} (超时时间: {timeout_seconds}秒)",
            error_code="TIMEOUT_ERROR",
            details=full_details,
        )


# 异常处理工具函数
def handle_intent_error(
    error: Exception, context: Optional[dict[str, Any]] = None
) -> IntentRecognitionError:
    """
    将通用异常转换为意图识别异常

    Args:
        error: 原始异常
        context: 错误上下文信息

    Returns:
        转换后的意图识别异常
    """
    if isinstance(error, IntentRecognitionError):
        return error

    # 根据异常类型进行映射
    error_type = type(error).__name__
    error_message = str(error)

    if "FileNotFoundError" in error_type or "file not found" in error_message.lower():
        return ModelNotFoundError(str(error))

    if "timeout" in error_message.lower():
        return IntentRecognitionTimeoutError(
            timeout_seconds=0.0, operation="unknown", details={"original_error": error_message}
        )

    # 默认返回通用异常
    return IntentRecognitionError(
        message=error_message,
        error_code="UNKNOWN_ERROR",
        details={"original_type": error_type, "context": context or {}},
    )
