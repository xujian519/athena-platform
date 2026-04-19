#!/usr/bin/env python3
from __future__ import annotations
"""
输入验证模块
Input Validation Module

提供通信模块的输入验证功能,防止无效或恶意输入

作者: Athena AI系统
创建时间: 2026-01-25
版本: 1.0.0
"""

import json
import logging
import re
from dataclasses import dataclass
from enum import Enum
from functools import wraps
from typing import Any

logger = logging.getLogger(__name__)


class ValidationException(Exception):
    """验证异常"""

    pass


class ValidationErrorCode(Enum):
    """验证错误代码"""

    MISSING_REQUIRED_FIELD = "MISSING_REQUIRED_FIELD"
    INVALID_FORMAT = "INVALID_FORMAT"
    INVALID_TYPE = "INVALID_TYPE"
    EMPTY_VALUE = "EMPTY_VALUE"
    TOO_LONG = "TOO_LONG"
    TOO_SHORT = "TOO_SHORT"
    INVALID_PATTERN = "INVALID_PATTERN"
    OUT_OF_RANGE = "OUT_OF_RANGE"
    UNKNOWN_FIELD = "UNKNOWN_FIELD"


@dataclass
class ValidationError:
    """验证错误详情"""

    field: str
    code: ValidationErrorCode
    message: str
    value: Any = None

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "field": self.field,
            "code": self.code.value,
            "message": self.message,
            "value": str(self.value) if self.value is not None else None,
        }


class InputValidator:
    """输入验证器基类"""

    # 验证规则
    AGENT_ID_PATTERN = re.compile(r"^[a-zA-Z0-9_-]{1,64}$")
    CHANNEL_ID_PATTERN = re.compile(r"^[a-zA-Z0-9_-]{1,128}$")
    MESSAGE_ID_PATTERN = re.compile(r"^[a-f0-9-]{36}$")  # UUID格式

    # 长度限制
    MAX_MESSAGE_SIZE = 10 * 1024 * 1024  # 10MB
    MAX_METADATA_SIZE = 64 * 1024  # 64KB
    MAX_CONTENT_LENGTH = 1024 * 1024  # 1MB

    @staticmethod
    def validate_agent_id(agent_id: Any) -> str:
        """
        验证代理ID

        Args:
            agent_id: 代理ID

        Returns:
            str: 验证通过的代理ID

        Raises:
            ValidationException: 验证失败
        """
        if agent_id is None:
            raise ValidationException(
                ValidationError(
                    "agent_id", ValidationErrorCode.MISSING_REQUIRED_FIELD, "代理ID不能为空"
                )
            )

        if not isinstance(agent_id, str):
            raise ValidationException(
                ValidationError(
                    "agent_id",
                    ValidationErrorCode.INVALID_TYPE,
                    f"代理ID必须是字符串,实际类型: {type(agent_id).__name__}",
                    agent_id,
                )
            )

        agent_id = agent_id.strip()

        if not agent_id:
            raise ValidationException(
                ValidationError("agent_id", ValidationErrorCode.EMPTY_VALUE, "代理ID不能为空字符串")
            )

        if len(agent_id) > 64:
            raise ValidationException(
                ValidationError(
                    "agent_id",
                    ValidationErrorCode.TOO_LONG,
                    f"代理ID长度不能超过64字符,实际长度: {len(agent_id)}",
                    agent_id,
                )
            )

        if not InputValidator.AGENT_ID_PATTERN.match(agent_id):
            raise ValidationException(
                ValidationError(
                    "agent_id",
                    ValidationErrorCode.INVALID_PATTERN,
                    "代理ID只能包含字母、数字、下划线和连字符",
                    agent_id,
                )
            )

        return agent_id

    @staticmethod
    def validate_channel_id(channel_id: Any) -> str:
        """
        验证通道ID

        Args:
            channel_id: 通道ID

        Returns:
            str: 验证通过的通道ID

        Raises:
            ValidationException: 验证失败
        """
        if channel_id is None:
            raise ValidationException(
                ValidationError(
                    "channel_id", ValidationErrorCode.MISSING_REQUIRED_FIELD, "通道ID不能为空"
                )
            )

        if not isinstance(channel_id, str):
            raise ValidationException(
                ValidationError(
                    "channel_id",
                    ValidationErrorCode.INVALID_TYPE,
                    f"通道ID必须是字符串,实际类型: {type(channel_id).__name__}",
                    channel_id,
                )
            )

        channel_id = channel_id.strip()

        if not channel_id:
            raise ValidationException(
                ValidationError(
                    "channel_id", ValidationErrorCode.EMPTY_VALUE, "通道ID不能为空字符串"
                )
            )

        if len(channel_id) > 128:
            raise ValidationException(
                ValidationError(
                    "channel_id",
                    ValidationErrorCode.TOO_LONG,
                    f"通道ID长度不能超过128字符,实际长度: {len(channel_id)}",
                    channel_id,
                )
            )

        if not InputValidator.CHANNEL_ID_PATTERN.match(channel_id):
            raise ValidationException(
                ValidationError(
                    "channel_id",
                    ValidationErrorCode.INVALID_PATTERN,
                    "通道ID只能包含字母、数字、下划线和连字符",
                    channel_id,
                )
            )

        return channel_id

    @staticmethod
    def validate_message_content(content: Any, max_length: int | None = None) -> Any:
        """
        验证消息内容

        Args:
            content: 消息内容
            max_length: 最大长度限制

        Returns:
            Any: 验证通过的消息内容

        Raises:
            ValidationException: 验证失败
        """
        if content is None:
            raise ValidationException(
                ValidationError(
                    "content", ValidationErrorCode.MISSING_REQUIRED_FIELD, "消息内容不能为空"
                )
            )

        max_length = max_length or InputValidator.MAX_CONTENT_LENGTH

        # 字符串内容验证
        if isinstance(content, str):
            if len(content.encode("utf-8")) > max_length:
                raise ValidationException(
                    ValidationError(
                        "content",
                        ValidationErrorCode.TOO_LONG,
                        f"消息内容大小超过限制 ({max_length} bytes)",
                    )
                )
            return content

        # 字典内容验证
        if isinstance(content, dict):
            try:
                json_str = json.dumps(content)
                if len(json_str.encode("utf-8")) > max_length:
                    raise ValidationException(
                        ValidationError(
                            "content",
                            ValidationErrorCode.TOO_LONG,
                            f"消息内容大小超过限制 ({max_length} bytes)",
                        )
                    )
                return content
            except (TypeError, ValueError) as e:
                raise ValidationException(
                    ValidationError(
                        "content",
                        ValidationErrorCode.INVALID_FORMAT,
                        f"消息内容无法序列化为JSON: {e}",
                    )
                ) from e

        # 二进制内容验证
        if isinstance(content, bytes):
            if len(content) > InputValidator.MAX_MESSAGE_SIZE:
                raise ValidationException(
                    ValidationError(
                        "content",
                        ValidationErrorCode.TOO_LONG,
                        f"二进制消息大小超过限制 ({InputValidator.MAX_MESSAGE_SIZE} bytes)",
                    )
                )
            return content

        # 其他类型(列表、数字等)
        return content

    @staticmethod
    def validate_metadata(metadata: Any) -> dict[str, Any]:
        """
        验证元数据

        Args:
            metadata: 元数据

        Returns:
            dict[str, Any]: 验证通过的元数据

        Raises:
            ValidationException: 验证失败
        """
        if metadata is None:
            return {}

        if not isinstance(metadata, dict):
            raise ValidationException(
                ValidationError(
                    "metadata",
                    ValidationErrorCode.INVALID_TYPE,
                    f"元数据必须是字典,实际类型: {type(metadata).__name__}",
                    metadata,
                )
            )

        try:
            json_str = json.dumps(metadata)
            if len(json_str.encode("utf-8")) > InputValidator.MAX_METADATA_SIZE:
                raise ValidationException(
                    ValidationError(
                        "metadata",
                        ValidationErrorCode.TOO_LONG,
                        f"元数据大小超过限制 ({InputValidator.MAX_METADATA_SIZE} bytes)",
                    )
                )
        except (TypeError, ValueError) as e:
            raise ValidationException(
                ValidationError(
                    "metadata", ValidationErrorCode.INVALID_FORMAT, f"元数据无法序列化为JSON: {e}"
                )
            ) from e

        return metadata


class MessageValidator:
    """消息验证器"""

    # 允许的消息类型
    VALID_MESSAGE_TYPES = {
        "text",
        "image",
        "audio",
        "video",
        "file",
        "system",
        "command",
        "notification",
        "broadcast",
    }

    # 允许的优先级范围
    PRIORITY_RANGE = (0, 9)

    @classmethod
    def validate_message_dict(cls, message: dict[str, Any]) -> dict[str, Any]:
        """
        验证消息字典

        Args:
            message: 消息字典

        Returns:
            dict[str, Any]: 验证通过的消息

        Raises:
            ValidationException: 验证失败
        """
        if not isinstance(message, dict):
            raise ValidationException(
                ValidationError(
                    "message",
                    ValidationErrorCode.INVALID_TYPE,
                    f"消息必须是字典,实际类型: {type(message).__name__}",
                )
            )

        # 验证必需字段
        required_fields = ["sender_id", "content"]
        for field in required_fields:
            if field not in message:
                raise ValidationException(
                    ValidationError(
                        field,
                        ValidationErrorCode.MISSING_REQUIRED_FIELD,
                        f"消息缺少必需字段: {field}",
                    )
                )

        # 验证sender_id
        try:
            message["sender_id"] = InputValidator.validate_agent_id(message["sender_id"])
        except ValidationException as e:
            # 转换错误字段名为sender_id
            error = e.args[0] if e.args else ValidationError(
                "sender_id", ValidationErrorCode.INVALID_PATTERN, str(e)
            )
            error.field = "sender_id"
            raise ValidationException(error) from e

        # 验证receiver_id(如果存在)
        if message.get("receiver_id"):
            try:
                message["receiver_id"] = InputValidator.validate_agent_id(message["receiver_id"])
            except ValidationException as e:
                # 转换错误字段名为receiver_id
                error = e.args[0] if e.args else ValidationError(
                    "receiver_id", ValidationErrorCode.INVALID_PATTERN, str(e)
                )
                error.field = "receiver_id"
                raise ValidationException(error) from e

        # 验证channel_id(如果存在)
        if message.get("channel_id"):
            message["channel_id"] = InputValidator.validate_channel_id(message["channel_id"])

        # 验证content
        message["content"] = InputValidator.validate_message_content(message["content"])

        # 验证message_type(如果存在)
        if message.get("message_type"):
            if message["message_type"] not in cls.VALID_MESSAGE_TYPES:
                raise ValidationException(
                    ValidationError(
                        "message_type",
                        ValidationErrorCode.INVALID_PATTERN,
                        f"无效的消息类型: {message['message_type']}",
                        message["message_type"],
                    )
                )

        # 验证priority(如果存在)
        if "priority" in message and message["priority"] is not None:
            priority = message["priority"]
            if not isinstance(priority, int):
                raise ValidationException(
                    ValidationError(
                        "priority",
                        ValidationErrorCode.INVALID_TYPE,
                        f"优先级必须是整数,实际类型: {type(priority).__name__}",
                    )
                )
            if not (cls.PRIORITY_RANGE[0] <= priority <= cls.PRIORITY_RANGE[1]):
                raise ValidationException(
                    ValidationError(
                        "priority",
                        ValidationErrorCode.OUT_OF_RANGE,
                        f"优先级必须在 {cls.PRIORITY_RANGE[0]}-{cls.PRIORITY_RANGE[1]} 范围内,实际值: {priority}",
                    )
                )

        # 验证metadata(如果存在)
        if message.get("metadata"):
            message["metadata"] = InputValidator.validate_metadata(message["metadata"])

        return message


def validate_message(func):
    """
    消息验证装饰器

    用法:
        @validate_message
        async def send_message(self, receiver_id: str, content: Any, **kwargs):
            # 函数实现
            pass

        或独立函数:
        @validate_message
        async def send_message(receiver_id: str, content: Any, **kwargs):
            # 函数实现
            pass
    """

    @wraps(func)
    async def wrapper(*args, **kwargs):
        import inspect
        sig = inspect.signature(func)
        params = list(sig.parameters.values())

        # 检测第一个参数是self还是直接是receiver_id
        is_method = params and params[0].name == 'self'

        # 确定参数起始索引
        arg_offset = 1 if is_method else 0

        # 验证receiver_id
        receiver_id = kwargs.get("receiver_id")
        if receiver_id is None and len(args) > arg_offset:
            receiver_id = args[arg_offset]
        if receiver_id:
            InputValidator.validate_agent_id(receiver_id)

        # 验证content
        content = kwargs.get("content")
        if content is None and len(args) > arg_offset + 1:
            content = args[arg_offset + 1]
        if content is not None:
            InputValidator.validate_message_content(content)

        # 验证channel_id
        if "channel_id" in kwargs:
            channel_id = kwargs["channel_id"]
            if channel_id:
                InputValidator.validate_channel_id(channel_id)

        return await func(*args, **kwargs)

    return wrapper


def validate_channel_id(func):
    """
    通道ID验证装饰器

    用法:
        @validate_channel_id
        async def create_channel(self, channel_id: str, **kwargs):
            # 函数实现
            pass

        或独立函数:
        @validate_channel_id
        async def create_channel(channel_id: str, **kwargs):
            # 函数实现
            pass
    """

    @wraps(func)
    async def wrapper(*args, **kwargs):
        # 检测第一个参数是self还是channel_id
        if args:
            # 如果是类方法调用,第一个参数是self
            # 检查参数数量来决定
            import inspect
            sig = inspect.signature(func)
            params = list(sig.parameters.values())
            if params and params[0].name == 'self':
                # 类方法
                if len(args) >= 2:
                    self = args[0]
                    channel_id = args[1]
                    validated_id = InputValidator.validate_channel_id(channel_id)
                    return await func(self, validated_id, *args)
                else:
                    raise TypeError(f"{func.__name__} missing required positional argument")
            else:
                # 独立函数
                if args:
                    channel_id = args[0]
                    validated_id = InputValidator.validate_channel_id(channel_id)
                    return await func(validated_id, *args)
        return await func(*args, **kwargs)

    return wrapper


def validate_agent_id(func):
    """
    代理ID验证装饰器

    用法:
        @validate_agent_id
        async def get_agent_status(self, agent_id: str, **kwargs):
            # 函数实现
            pass

        或独立函数:
        @validate_agent_id
        async def get_agent_status(agent_id: str, **kwargs):
            # 函数实现
            pass
    """

    @wraps(func)
    async def wrapper(*args, **kwargs):
        # 检测第一个参数是self还是agent_id
        if args:
            import inspect
            sig = inspect.signature(func)
            params = list(sig.parameters.values())
            if params and params[0].name == 'self':
                # 类方法
                if len(args) >= 2:
                    self = args[0]
                    agent_id = args[1]
                    validated_id = InputValidator.validate_agent_id(agent_id)
                    return await func(self, validated_id, *args)
                else:
                    raise TypeError(f"{func.__name__} missing required positional argument")
            else:
                # 独立函数
                if args:
                    agent_id = args[0]
                    validated_id = InputValidator.validate_agent_id(agent_id)
                    return await func(validated_id, *args)
        return await func(*args, **kwargs)

    return wrapper


# 导出
__all__ = [
    "InputValidator",
    "MessageValidator",
    "ValidationError",
    "ValidationErrorCode",
    "ValidationException",
    "validate_agent_id",
    "validate_channel_id",
    "validate_message",
]
