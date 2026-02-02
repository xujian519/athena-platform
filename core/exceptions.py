#!/usr/bin/env python3
"""
统一异常体系
Unified Exception System

定义Athena平台的所有异常类型

作者: Athena平台团队
创建时间: 2026-01-16
版本: 1.0.0
"""

from datetime import datetime
from typing import Any, Dict, Optional


class AthenaError(Exception):
    """
    Athena平台错误基类

    所有自定义异常的基类,提供统一的错误信息格式
    """

    def __init__(
        self,
        message: str,
        code: str = "UNKNOWN_ERROR",
        details: dict[str, Any] | None = None,
        cause: Exception | None = None,
    ):
        """
        初始化异常

        Args:
            message: 错误消息
            code: 错误代码
            details: 详细信息字典
            cause: 原始异常(用于异常链)
        """
        self.message = message
        self.code = code
        self.details = details or {}
        self.cause = cause
        self.timestamp = datetime.now()

        # 构建完整的错误消息
        full_message = f"[{code}] {message}"
        if cause:
            full_message += f" (caused by: {type(cause).__name__}: {cause})"

        super().__init__(full_message)

    def to_dict(self) -> dict[str, Any]:
        """转换为字典格式"""
        result = {
            "error_code": self.code,
            "error_message": self.message,
            "error_type": type(self).__name__,
            "timestamp": self.timestamp.isoformat(),
        }

        if self.details:
            result["details"] = self.details

        if self.cause:
            result["cause"] = str(self.cause)

        return result

    def __repr__(self) -> str:
        return f"{type(self).__name__}(code={self.code}, message={self.message})"


# ==================== 感知模块异常 ====================


class PerceptionError(AthenaError):
    """感知模块错误基类"""

    def __init__(
        self,
        message: str,
        details: dict[str, Any] | None = None,
        cause: Exception | None = None,
    ):
        super().__init__(message, "PERCEPTION_ERROR", details, cause)


class InputValidationError(PerceptionError):
    """输入验证错误"""

    def __init__(
        self,
        message: str,
        field_name: str | None = None,
        validation_errors: list | None = None,
    ):
        details = {}
        if field_name:
            details["field_name"] = field_name
        if validation_errors:
            details["validation_errors"] = validation_errors

        super().__init__(message, details)
        self.code = "INPUT_VALIDATION_ERROR"


class UnsupportedInputTypeError(PerceptionError):
    """不支持的输入类型错误"""

    def __init__(self, input_type: str, supported_types: list):
        message = f"不支持的输入类型: {input_type}"
        details = {"input_type": input_type, "supported_types": supported_types}
        super().__init__(message, details)
        self.code = "UNSUPPORTED_INPUT_TYPE"


class ProcessorNotFoundError(PerceptionError):
    """处理器未找到错误"""

    def __init__(self, input_type: str):
        message = f"未找到适合的处理器: {input_type}"
        details = {"input_type": input_type}
        super().__init__(message, details)
        self.code = "PROCESSOR_NOT_FOUND"


# ==================== 意图识别异常 ====================


class IntentRecognitionError(AthenaError):
    """意图识别错误"""

    def __init__(
        self, message: str, query: str | None = None, details: dict[str, Any] | None = None
    ):
        if details is None:
            details = {}
        if query:
            details["query"] = query[:100]  # 限制查询长度

        super().__init__(message, "INTENT_RECOGNITION_ERROR", details)


class IntentClassifierNotFoundError(IntentRecognitionError):
    """意图分类器未找到错误"""

    def __init__(self, classifier_name: str):
        message = f"意图分类器未找到: {classifier_name}"
        super().__init__(message, details={"classifier_name": classifier_name})
        self.code = "INTENT_CLASSIFIER_NOT_FOUND"


class LowConfidenceError(IntentRecognitionError):
    """低置信度错误"""

    def __init__(self, query: str, confidence: float, threshold: float):
        message = f"意图识别置信度过低: {confidence:.2f} < {threshold:.2f}"
        details = {"confidence": confidence, "threshold": threshold}
        super().__init__(message, query=query, details=details)
        self.code = "LOW_CONFIDENCE"


# ==================== 智能体异常 ====================


class AgentError(AthenaError):
    """智能体错误基类"""

    def __init__(
        self, message: str, agent_id: str | None = None, details: dict[str, Any] | None = None
    ):
        if details is None:
            details = {}
        if agent_id:
            details["agent_id"] = agent_id

        super().__init__(message, "AGENT_ERROR", details)


class AgentInitializationError(AgentError):
    """智能体初始化错误"""

    def __init__(self, agent_id: str, reason: str, details: dict[str, Any] | None = None):
        message = f"智能体初始化失败: {agent_id} - {reason}"
        super().__init__(message, agent_id, details)
        self.code = "AGENT_INITIALIZATION_ERROR"


class AgentTaskError(AgentError):
    """智能体任务错误"""

    def __init__(
        self,
        message: str,
        task_id: str | None = None,
        agent_id: str | None = None,
        task_type: str | None = None,
    ):
        details = {}
        if task_id:
            details["task_id"] = task_id
        if agent_id:
            details["agent_id"] = agent_id
        if task_type:
            details["task_type"] = task_type

        super().__init__(message, agent_id, details)
        self.code = "AGENT_TASK_ERROR"


class AgentNotFoundError(AgentError):
    """智能体未找到错误"""

    def __init__(self, agent_id: str):
        message = f"智能体未找到: {agent_id}"
        super().__init__(message, agent_id)
        self.code = "AGENT_NOT_FOUND"


class AgentUnavailableError(AgentError):
    """智能体不可用错误"""

    def __init__(self, agent_id: str, status: str, reason: str | None = None):
        message = f"智能体不可用: {agent_id} (状态: {status})"
        if reason:
            message += f" - {reason}"

        details = {"agent_id": agent_id, "status": status}
        if reason:
            details["reason"] = reason

        super().__init__(message, agent_id, details)
        self.code = "AGENT_UNAVAILABLE"


# ==================== 协作异常 ====================


class CollaborationError(AthenaError):
    """协作错误基类"""

    def __init__(
        self, message: str, team_id: str | None = None, details: dict[str, Any] | None = None
    ):
        if details is None:
            details = {}
        if team_id:
            details["team_id"] = team_id

        super().__init__(message, "COLLABORATION_ERROR", details)


class TeamFormationError(CollaborationError):
    """团队组建错误"""

    def __init__(self, message: str, required_agents: list, available_agents: list):
        details = {"required_agents": required_agents, "available_agents": available_agents}
        super().__init__(message, details=details)
        self.code = "TEAM_FORMATION_ERROR"


class TaskDistributionError(CollaborationError):
    """任务分发错误"""

    def __init__(self, message: str, task_id: str | None = None, agent_id: str | None = None):
        details = {}
        if task_id:
            details["task_id"] = task_id
        if agent_id:
            details["agent_id"] = agent_id

        super().__init__(message, details=details)
        self.code = "TASK_DISTRIBUTION_ERROR"


# ==================== 通信异常 ====================


class CommunicationError(AthenaError):
    """通信错误基类"""

    def __init__(
        self,
        message: str,
        from_agent: str | None = None,
        to_agent: str | None = None,
        details: dict[str, Any] | None = None,
    ):
        if details is None:
            details = {}
        if from_agent:
            details["from_agent"] = from_agent
        if to_agent:
            details["to_agent"] = to_agent

        super().__init__(message, "COMMUNICATION_ERROR", details)


class MessageSendError(CommunicationError):
    """消息发送错误"""

    def __init__(
        self, message: str, message_type: str | None = None, recipient: str | None = None
    ):
        details = {}
        if message_type:
            details["message_type"] = message_type
        if recipient:
            details["recipient"] = recipient

        super().__init__(message, details=details)
        self.code = "MESSAGE_SEND_ERROR"


class MessageTimeoutError(CommunicationError):
    """消息超时错误"""

    def __init__(self, message_id: str, timeout: float, recipient: str | None = None):
        message_str = f"消息超时: {message_id} (超时时间: {timeout}秒)"
        details = {"message_id": message_id, "timeout": timeout}
        if recipient:
            details["recipient"] = recipient

        super().__init__(message_str, details=details)
        self.code = "MESSAGE_TIMEOUT"


# ==================== 配置异常 ====================


class ConfigurationError(AthenaError):
    """配置错误基类"""

    def __init__(
        self,
        message: str,
        config_key: str | None = None,
        details: dict[str, Any] | None = None,
    ):
        if details is None:
            details = {}
        if config_key:
            details["config_key"] = config_key

        super().__init__(message, "CONFIGURATION_ERROR", details)


class MissingConfigurationError(ConfigurationError):
    """缺失配置错误"""

    def __init__(self, config_key: str, config_file: str | None = None):
        message = f"缺失必需的配置: {config_key}"
        details = {"config_key": config_key}
        if config_file:
            details["config_file"] = config_file

        super().__init__(message, config_key, details)
        self.code = "MISSING_CONFIGURATION"


class InvalidConfigurationError(ConfigurationError):
    """无效配置错误"""

    def __init__(
        self, config_key: str, value: Any, expected_type: str, reason: str | None = None
    ):
        message = f"无效的配置值: {config_key} = {value}"
        if reason:
            message += f" - {reason}"

        details = {"config_key": config_key, "value": str(value), "expected_type": expected_type}

        super().__init__(message, config_key, details)
        self.code = "INVALID_CONFIGURATION"


# ==================== 安全异常 ====================


class SecurityError(AthenaError):
    """安全错误基类"""

    def __init__(
        self,
        message: str,
        threat_type: str | None = None,
        details: dict[str, Any] | None = None,
    ):
        if details is None:
            details = {}
        if threat_type:
            details["threat_type"] = threat_type

        super().__init__(message, "SECURITY_ERROR", details)


class InputThreatDetectedError(SecurityError):
    """检测到输入威胁错误"""

    def __init__(
        self,
        message: str,
        threat_type: str,
        detected_patterns: list,
        input_preview: str | None = None,
    ):
        details = {"threat_type": threat_type, "detected_patterns": detected_patterns}
        if input_preview:
            details["input_preview"] = input_preview[:200]

        super().__init__(message, threat_type, details)
        self.code = "INPUT_THREAT_DETECTED"


class RateLimitExceededError(SecurityError):
    """速率限制超出错误"""

    def __init__(self, client_id: str, limit: int, window: str):
        message = f"速率限制超出: 客户端 {client_id} 超过了 {window} {limit} 次请求的限制"
        details = {"client_id": client_id, "limit": limit, "window": window}
        super().__init__(message, details=details)
        self.code = "RATE_LIMIT_EXCEEDED"


class AuthenticationError(SecurityError):
    """认证错误"""

    def __init__(
        self, message: str, user_id: str | None = None, details: dict[str, Any] | None = None
    ):
        if details is None:
            details = {}
        if user_id:
            details["user_id"] = user_id

        super().__init__(message, details=details)
        self.code = "AUTHENTICATION_ERROR"


class AuthorizationError(SecurityError):
    """授权错误"""

    def __init__(
        self,
        message: str,
        user_id: str | None = None,
        required_permission: str | None = None,
        resource: str | None = None,
    ):
        details = {}
        if user_id:
            details["user_id"] = user_id
        if required_permission:
            details["required_permission"] = required_permission
        if resource:
            details["resource"] = resource

        super().__init__(message, details=details)
        self.code = "AUTHORIZATION_ERROR"


# ==================== 数据库异常 ====================


class DatabaseError(AthenaError):
    """数据库错误基类"""

    def __init__(
        self, message: str, query: str | None = None, details: dict[str, Any] | None = None
    ):
        if details is None:
            details = {}
        if query:
            details["query"] = query[:500]  # 限制查询长度

        super().__init__(message, "DATABASE_ERROR", details)


class ConnectionError(DatabaseError):
    """数据库连接错误"""

    def __init__(self, database: str, host: str, port: int, reason: str | None = None):
        message = f"数据库连接失败: {database}@{host}:{port}"
        if reason:
            message += f" - {reason}"

        details = {"database": database, "host": host, "port": port}
        if reason:
            details["reason"] = reason

        super().__init__(message, details=details)
        self.code = "DATABASE_CONNECTION_ERROR"


class QueryExecutionError(DatabaseError):
    """查询执行错误"""

    def __init__(self, message: str, query: str, params: tuple | None = None):
        details = {"query": query[:500]}
        if params:
            details["params"] = str(params)[:200]

        super().__init__(message, query, details)
        self.code = "QUERY_EXECUTION_ERROR"


# ==================== 外部服务异常 ====================


class ExternalServiceError(AthenaError):
    """外部服务错误基类"""

    def __init__(
        self,
        message: str,
        service_name: str | None = None,
        details: dict[str, Any] | None = None,
    ):
        if details is None:
            details = {}
        if service_name:
            details["service_name"] = service_name

        super().__init__(message, "EXTERNAL_SERVICE_ERROR", details)


class ServiceUnavailableError(ExternalServiceError):
    """服务不可用错误"""

    def __init__(
        self, service_name: str, status_code: int | None = None, reason: str | None = None
    ):
        message = f"外部服务不可用: {service_name}"
        if status_code:
            message += f" (状态码: {status_code})"
        if reason:
            message += f" - {reason}"

        details = {"service_name": service_name}
        if status_code:
            details["status_code"] = status_code
        if reason:
            details["reason"] = reason

        super().__init__(message, service_name, details)
        self.code = "SERVICE_UNAVAILABLE"


class ServiceTimeoutError(ExternalServiceError):
    """服务超时错误"""

    def __init__(self, service_name: str, timeout: float, endpoint: str | None = None):
        message = f"外部服务超时: {service_name} (超时时间: {timeout}秒)"
        details = {"service_name": service_name, "timeout": timeout}
        if endpoint:
            details["endpoint"] = endpoint

        super().__init__(message, service_name, details)
        self.code = "SERVICE_TIMEOUT"


# ==================== 工具函数 ====================


def format_error(error: Exception) -> dict[str, Any]:
    """
    格式化异常为统一格式

    Args:
        error: 异常对象

    Returns:
        Dict: 格式化的错误信息
    """
    if isinstance(error, AthenaError):
        return error.to_dict()

    # 处理标准Python异常
    return {
        "error_code": type(error).__name__,
        "error_message": str(error),
        "error_type": type(error).__name__,
        "timestamp": datetime.now().isoformat(),
    }


def get_error_code(error: Exception) -> str:
    """
    获取异常的错误代码

    Args:
        error: 异常对象

    Returns:
        str: 错误代码
    """
    if isinstance(error, AthenaError):
        return error.code
    return type(error).__name__


def is_retriable_error(error: Exception) -> bool:
    """
    判断异常是否可重试

    Args:
        error: 异常对象

    Returns:
        bool: 是否可重试
    """
    # 可重试的异常类型
    retriable_types = (
        ServiceTimeoutError,
        ServiceUnavailableError,
        MessageTimeoutError,
    )

    return isinstance(error, retriable_types)


# 导出所有异常类
__all__ = [
    # 智能体异常
    "AgentError",
    "AgentInitializationError",
    "AgentNotFoundError",
    "AgentTaskError",
    "AgentUnavailableError",
    # 基类
    "AthenaError",
    "AuthenticationError",
    "AuthorizationError",
    # 协作异常
    "CollaborationError",
    # 通信异常
    "CommunicationError",
    # 配置异常
    "ConfigurationError",
    "ConnectionError",
    # 数据库异常
    "DatabaseError",
    # 外部服务异常
    "ExternalServiceError",
    "InputThreatDetectedError",
    "InputValidationError",
    "IntentClassifierNotFoundError",
    # 意图识别异常
    "IntentRecognitionError",
    "InvalidConfigurationError",
    "LowConfidenceError",
    "MessageSendError",
    "MessageTimeoutError",
    "MissingConfigurationError",
    # 感知模块异常
    "PerceptionError",
    "ProcessorNotFoundError",
    "QueryExecutionError",
    "RateLimitExceededError",
    # 安全异常
    "SecurityError",
    "ServiceTimeoutError",
    "ServiceUnavailableError",
    "TaskDistributionError",
    "TeamFormationError",
    "UnsupportedInputTypeError",
    # 工具函数
    "format_error",
    "get_error_code",
    "is_retriable_error",
]
