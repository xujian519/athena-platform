#!/usr/bin/env python3
"""
Athena通信系统 - 消息验证器
Message Validator for Communication System

实现消息验证功能,防止注入攻击和无效消息。

主要功能:
1. 消息大小验证
2. 必填字段验证
3. 字段格式验证
4. 注入攻击检测
5. 元数据验证

作者: Athena平台团队
创建时间: 2026-01-16
版本: v1.0.0
"""

import logging
import re

from .types import Message, MessageType

logger = logging.getLogger(__name__)


class MessageValidator:
    """
    消息验证器

    验证消息格式和内容,防止安全漏洞。
    """

    # 配置常量
    MAX_MESSAGE_SIZE = 1024 * 1024  # 1MB
    MAX_METADATA_SIZE = 1024 * 10  # 10KB
    MAX_CONTENT_LENGTH = 1024 * 100  # 100KB

    # 危险模式检测
    DANGEROUS_PATTERNS = [
        r"<script[^>]*>.*?</script>",  # XSS脚本标签
        r"javascript:",  # JavaScript伪协议
        r"onerror\s*=",  # 错误事件处理器
        r"onclick\s*=",  # 点击事件处理器
        r"onload\s*=",  # 加载事件处理器
        r"<iframe[^>]*>",  # iframe标签
        r"<object[^>]*>",  # object标签
        r"<embed[^>]*>",  # embed标签
    ]

    # ID格式验证
    ID_PATTERN = re.compile(r"^[a-z_a-Z0-9_-]+$")

    def __init__(
        self,
        max_message_size: int = MAX_MESSAGE_SIZE,
        max_metadata_size: int = MAX_METADATA_SIZE,
        max_content_length: int = MAX_CONTENT_LENGTH,
    ):
        """
        初始化消息验证器

        Args:
            max_message_size: 最大消息大小(字节)
            max_metadata_size: 最大元数据大小(字节)
            max_content_length: 最大内容长度(字符)
        """
        self.max_message_size = max_message_size
        self.max_metadata_size = max_metadata_size
        self.max_content_length = max_content_length

        # 编译危险模式正则
        self.dangerous_regex = [re.compile(p, re.IGNORECASE) for p in self.DANGEROUS_PATTERNS]

    def validate(self, message: Message) -> tuple[bool, str | None]:
        """
        验证消息

        Args:
            message: 要验证的消息

        Returns:
            (是否有效, 错误信息)元组
        """
        # 检查消息大小
        size_error = self._validate_size(message)
        if size_error:
            return False, size_error

        # 检查必填字段
        field_error = self._validate_required_fields(message)
        if field_error:
            return False, field_error

        # 检查字段格式
        format_error = self._validate_formats(message)
        if format_error:
            return False, format_error

        # 检查内容安全性
        security_error = self._validate_security(message)
        if security_error:
            return False, security_error

        # 检查元数据
        metadata_error = self._validate_metadata(message)
        if metadata_error:
            return False, metadata_error

        return True, None

    def _validate_size(self, message: Message) -> str | None:
        """验证消息大小"""
        # 估算消息大小
        message_str = str(message.to_dict())
        size = len(message_str.encode("utf-8"))

        if size > self.max_message_size:
            return f"消息过大: {size}字节,最大允许{self.max_message_size}字节"

        return None

    def _validate_required_fields(self, message: Message) -> str | None:
        """验证必填字段"""
        if not message.id:
            return "消息ID不能为空"

        if not message.sender:
            return "发送者不能为空"

        # 检查接收者(广播消息除外)
        from .types import ChannelType

        if message.channel_type not in [ChannelType.BROADCAST, ChannelType.TOPIC]:
            if not message.receiver:
                return "接收者不能为空(广播和主题通道除外)"

        # 检查内容
        if message.content is None and message.type not in [
            MessageType.SYSTEM,
            MessageType.HEARTBEAT,
        ]:
            return "消息内容不能为空"

        return None

    def _validate_formats(self, message: Message) -> str | None:
        """验证字段格式"""
        # 验证ID格式
        if message.id and not self.ID_PATTERN.match(message.id):
            return f"无效的消息ID格式: {message.id}"

        if message.sender and not self.ID_PATTERN.match(message.sender):
            return f"无效的发送者ID格式: {message.sender}"

        if message.receiver and not self.ID_PATTERN.match(message.receiver):
            return f"无效的接收者ID格式: {message.receiver}"

        # 验证回复消息ID
        if message.reply_to and not self.ID_PATTERN.match(message.reply_to):
            return f"无效的回复消息ID格式: {message.reply_to}"

        # 验证关联ID
        if message.correlation_id and not self.ID_PATTERN.match(message.correlation_id):
            return f"无效的关联ID格式: {message.correlation_id}"

        return None

    def _validate_security(self, message: Message) -> str | None:
        """验证内容安全性"""
        content = message.content

        if not content or not isinstance(content, str):
            return None

        # 检查内容长度
        if len(content) > self.max_content_length:
            return f"内容过长: {len(content)}字符,最大允许{self.max_content_length}字符"

        # 检查危险模式
        for pattern in self.dangerous_regex:
            if pattern.search(content):
                return f"检测到潜在的安全威胁: {pattern.pattern}"

        return None

    def _validate_metadata(self, message: Message) -> str | None:
        """验证元数据"""
        if not message.metadata:
            return None

        # 检查元数据大小
        metadata_str = str(message.metadata)
        metadata_size = len(metadata_str.encode("utf-8"))

        if metadata_size > self.max_metadata_size:
            return f"元数据过大: {metadata_size}字节,最大允许{self.max_metadata_size}字节"

        # 递归验证元数据中的字符串值
        for key, value in message.metadata.items():
            if isinstance(value, str):
                # 检查元数据中的危险模式
                for pattern in self.dangerous_regex:
                    if pattern.search(value):
                        return f"元数据中检测到安全威胁: {key}"

        return None


# =============================================================================
# 便捷函数
# =============================================================================


def create_message_validator(
    max_message_size: int = MessageValidator.MAX_MESSAGE_SIZE,
    max_metadata_size: int = MessageValidator.MAX_METADATA_SIZE,
    max_content_length: int = MessageValidator.MAX_CONTENT_LENGTH,
) -> MessageValidator:
    """创建消息验证器实例"""
    return MessageValidator(max_message_size, max_metadata_size, max_content_length)


# 默认验证器实例
_default_validator: MessageValidator | None = None


def get_default_validator() -> MessageValidator:
    """获取默认消息验证器"""
    global _default_validator
    if _default_validator is None:
        _default_validator = MessageValidator()
    return _default_validator


def validate_message(message: Message) -> tuple[bool, str | None]:
    """
    使用默认验证器验证消息

    Args:
        message: 要验证的消息

    Returns:
        (是否有效, 错误信息)元组
    """
    return get_default_validator().validate(message)


# =============================================================================
# 导出
# =============================================================================

__all__ = [
    "MessageValidator",
    "create_message_validator",
    "get_default_validator",
    "validate_message",
]
