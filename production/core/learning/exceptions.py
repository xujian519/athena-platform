#!/usr/bin/env python3
"""
学习模块自定义异常
Learning Module Custom Exceptions

定义学习与适应模块中使用的所有自定义异常类。

作者: Athena AI系统
创建时间: 2026-01-27
版本: 2.0.0
"""


from __future__ import annotations
class LearningModuleError(Exception):
    """学习模块基础异常类

    所有学习模块自定义异常的基类。
    """

    def __init__(self, message: str, error_code: str | None = None):
        """初始化异常

        Args:
            message: 错误消息
            error_code: 错误代码（可选）
        """
        self.message = message
        self.error_code = error_code
        super().__init__(self.message)

    def __str__(self) -> str:
        if self.error_code:
            return f"[{self.error_code}] {self.message}"
        return self.message


class LearningEngineError(LearningModuleError):
    """学习引擎异常

    当学习引擎初始化、运行或关闭失败时抛出。
    """

    pass


class ExperienceStoreError(LearningModuleError):
    """经验存储异常

    当经验存储操作失败时抛出。
    """

    pass


class PatternRecognitionError(LearningModuleError):
    """模式识别异常

    当模式识别过程失败时抛出。
    """

    pass


class OptimizationError(LearningModuleError):
    """优化异常

    当自适应优化过程失败时抛出。
    """

    pass


class ModelValidationError(LearningModuleError):
    """模型验证异常

    当模型验证失败时抛出（安全相关）。
    """

    pass


class ModelSerializationError(LearningModuleError):
    """模型序列化异常

    当模型序列化或反序列化失败时抛出。
    """

    pass


class AdaptationError(LearningModuleError):
    """适应异常

    当环境适应过程失败时抛出。
    """

    pass


class ConfigurationError(LearningModuleError):
    """配置异常

    当配置无效或缺失时抛出。
    """

    pass


class KnowledgeBaseError(LearningModuleError):
    """知识库异常

    当知识库操作失败时抛出。
    """

    pass


class FailureAnalysisError(LearningModuleError):
    """失败分析异常

    当失败案例分析失败时抛出。
    """

    pass


# 错误代码常量
class ErrorCodes:
    """错误代码常量"""

    # 学习引擎错误 (LE-001 到 LE-099)
    ENGINE_NOT_INITIALIZED = "LE-001"
    ENGINE_ALREADY_INITIALIZED = "LE-002"
    ENGINE_SHUTDOWN_FAILED = "LE-003"

    # 经验存储错误 (ES-001 到 ES-099)
    EXPERIENCE_STORE_FULL = "ES-001"
    EXPERIENCE_NOT_FOUND = "ES-002"
    EXPERIENCE_INVALID_FORMAT = "ES-003"

    # 模式识别错误 (PR-001 到 PR-099)
    PATTERN_RECOGNITION_FAILED = "PR-001"
    INSUFFICIENT_DATA_FOR_PATTERN = "PR-002"

    # 优化错误 (OP-001 到 OP-099)
    OPTIMIZATION_FAILED = "OP-001"
    INVALID_PARAMETERS = "OP-002"

    # 模型验证错误 (MV-001 到 MV-099)
    MODEL_VALIDATION_FAILED = "MV-001"
    MODEL_SIZE_EXCEEDED = "MV-002"
    MODEL_TYPE_INVALID = "MV-003"
    MODEL_DATA_CORRUPTED = "MV-004"

    # 模型序列化错误 (MS-001 到 MS-099)
    MODEL_SERIALIZATION_FAILED = "MS-001"
    MODEL_DESERIALIZATION_FAILED = "MS-002"

    # 适应错误 (AD-001 到 AD-099)
    ADAPTATION_FAILED = "AD-001"
    INVALID_STRATEGY = "AD-002"

    # 配置错误 (CF-001 到 CF-099)
    INVALID_CONFIG = "CF-001"
    MISSING_CONFIG = "CF-002"

    # 知识库错误 (KB-001 到 KB-099)
    KNOWLEDGE_NOT_FOUND = "KB-001"
    KNOWLEDGE_SAVE_FAILED = "KB-002"

    # 失败分析错误 (FA-001 到 FA-099)
    FAILURE_ANALYSIS_FAILED = "FA-001"
    SIMILAR_CASE_NOT_FOUND = "FA-002"


# 为保持兼容性，提供别名
LearningException = LearningModuleError


__all__ = [
    "LearningModuleError",
    "LearningException",  # 别名
    "LearningEngineError",
    "ExperienceStoreError",
    "PatternRecognitionError",
    "OptimizationError",
    "ModelValidationError",
    "ModelSerializationError",
    "AdaptationError",
    "ConfigurationError",
    "KnowledgeBaseError",
    "FailureAnalysisError",
    "ErrorCodes",
]
