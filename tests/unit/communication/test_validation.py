#!/usr/bin/env python3
"""
输入验证模块单元测试
Unit Tests for Input Validation Module

作者: Athena AI系统
创建时间: 2026-01-25
版本: 1.0.0
"""

import pytest
import json
from core.communication.utils.validation import (
    ValidationException,
    ValidationErrorCode,
    ValidationError,
    InputValidator,
    MessageValidator,
    validate_message,
    validate_channel_id,
    validate_agent_id
)


@pytest.mark.unit
class TestValidationError:
    """验证错误类测试"""

    def test_to_dict(self):
        """测试转换为字典"""
        error = ValidationError(
            field="test_field",
            code=ValidationErrorCode.INVALID_FORMAT,
            message="Test error message",
            value="test_value"
        )

        result = error.to_dict()

        assert result["field"] == "test_field"
        assert result["code"] == "INVALID_FORMAT"
        assert result["message"] == "Test error message"
        assert result["value"] == "test_value"


@pytest.mark.unit
class TestInputValidator:
    """输入验证器测试"""

    def test_validate_agent_id_success(self):
        """测试代理ID验证成功"""
        # 有效的ID
        valid_ids = [
            "agent_001",
            "TestAgent-123",
            "aBc-XyZ-123",
            "agent"
        ]

        for agent_id in valid_ids:
            result = InputValidator.validate_agent_id(agent_id)
            assert result == agent_id

    def test_validate_agent_id_none(self):
        """测试代理ID为None"""
        with pytest.raises(ValidationException) as exc_info:
            InputValidator.validate_agent_id(None)

        error = exc_info.value.args[0]
        assert error.code == ValidationErrorCode.MISSING_REQUIRED_FIELD

    def test_validate_agent_id_wrong_type(self):
        """测试代理ID类型错误"""
        with pytest.raises(ValidationException) as exc_info:
            InputValidator.validate_agent_id(123)

        error = exc_info.value.args[0]
        assert error.code == ValidationErrorCode.INVALID_TYPE
        assert "整数" in error.message or "int" in error.message.lower()

    def test_validate_agent_id_empty_string(self):
        """测试代理ID为空字符串"""
        with pytest.raises(ValidationException) as exc_info:
            InputValidator.validate_agent_id("   ")

        error = exc_info.value.args[0]
        assert error.code == ValidationErrorCode.EMPTY_VALUE

    def test_validate_agent_id_too_long(self):
        """测试代理ID过长"""
        long_id = "a" * 65
        with pytest.raises(ValidationException) as exc_info:
            InputValidator.validate_agent_id(long_id)

        error = exc_info.value.args[0]
        assert error.code == ValidationErrorCode.TOO_LONG

    def test_validate_agent_id_invalid_pattern(self):
        """测试代理ID包含非法字符"""
        invalid_ids = [
            "agent.001",  # 点号
            "agent@123",  # @符号
            "agent#123",  # #符号
            "agent 123",  # 空格
            "中文agent",  # 中文字符
        ]

        for invalid_id in invalid_ids:
            with pytest.raises(ValidationException) as exc_info:
                InputValidator.validate_agent_id(invalid_id)

            error = exc_info.value.args[0]
            assert error.code == ValidationErrorCode.INVALID_PATTERN

    def test_validate_channel_id_success(self):
        """测试通道ID验证成功"""
        valid_ids = [
            "channel_001",
            "Test-Channel-123",
            "aBc-XyZ"
        ]

        for channel_id in valid_ids:
            result = InputValidator.validate_channel_id(channel_id)
            assert result == channel_id

    def test_validate_channel_id_too_long(self):
        """测试通道ID过长"""
        long_id = "a" * 129
        with pytest.raises(ValidationException) as exc_info:
            InputValidator.validate_channel_id(long_id)

        error = exc_info.value.args[0]
        assert error.code == ValidationErrorCode.TOO_LONG

    def test_validate_message_content_string(self):
        """测试字符串内容验证"""
        # 短字符串
        content = "Test message"
        result = InputValidator.validate_message_content(content)
        assert result == content

        # 长字符串（但在限制内）
        long_content = "a" * 1000
        result = InputValidator.validate_message_content(long_content, max_length=2000)
        assert result == long_content

    def test_validate_message_content_too_long(self):
        """测试内容过长"""
        long_content = "a" * 2000
        with pytest.raises(ValidationException) as exc_info:
            InputValidator.validate_message_content(long_content, max_length=1000)

        error = exc_info.value.args[0]
        assert error.code == ValidationErrorCode.TOO_LONG

    def test_validate_message_content_none(self):
        """测试内容为None"""
        with pytest.raises(ValidationException) as exc_info:
            InputValidator.validate_message_content(None)

        error = exc_info.value.args[0]
        assert error.code == ValidationErrorCode.MISSING_REQUIRED_FIELD

    def test_validate_message_content_dict(self):
        """测试字典内容验证"""
        content = {"key": "value", "number": 123}
        result = InputValidator.validate_message_content(content)
        assert result == content

    def test_validate_message_content_dict_unserializable(self):
        """测试字典内容无法序列化"""
        # 包含无法序列化的对象
        content = {"key": object()}
        with pytest.raises(ValidationException) as exc_info:
            InputValidator.validate_message_content(content)

        error = exc_info.value.args[0]
        assert error.code == ValidationErrorCode.INVALID_FORMAT

    def test_validate_message_content_bytes(self):
        """测试二进制内容验证"""
        # 小文件
        content = b"test content"
        result = InputValidator.validate_message_content(content)
        assert result == content

        # 大文件（超过限制）
        large_content = b"a" * (11 * 1024 * 1024)  # 11MB
        with pytest.raises(ValidationException) as exc_info:
            InputValidator.validate_message_content(large_content)

        error = exc_info.value.args[0]
        assert error.code == ValidationErrorCode.TOO_LONG

    def test_validate_metadata_none(self):
        """测试元数据为None"""
        result = InputValidator.validate_metadata(None)
        assert result == {}

    def test_validate_metadata_valid(self):
        """测试有效元数据"""
        metadata = {"key1": "value1", "key2": 123}
        result = InputValidator.validate_metadata(metadata)
        assert result == metadata

    def test_validate_metadata_invalid_type(self):
        """测试元数据类型错误"""
        with pytest.raises(ValidationException) as exc_info:
            InputValidator.validate_metadata("not a dict")

        error = exc_info.value.args[0]
        assert error.code == ValidationErrorCode.INVALID_TYPE

    def test_validate_metadata_too_large(self):
        """测试元数据过大"""
        # 创建超过64KB的元数据
        large_metadata = {"data": "a" * (70 * 1024)}
        with pytest.raises(ValidationException) as exc_info:
            InputValidator.validate_metadata(large_metadata)

        error = exc_info.value.args[0]
        assert error.code == ValidationErrorCode.TOO_LONG


@pytest.mark.unit
class TestMessageValidator:
    """消息验证器测试"""

    def test_validate_message_dict_success(self):
        """测试消息字典验证成功"""
        message = {
            "sender_id": "agent_001",
            "content": "Test message"
        }

        result = MessageValidator.validate_message_dict(message)
        assert result["sender_id"] == "agent_001"
        assert result["content"] == "Test message"

    def test_validate_message_dict_with_optional_fields(self):
        """测试包含可选字段的消息验证"""
        message = {
            "sender_id": "agent_001",
            "receiver_id": "agent_002",
            "channel_id": "channel_001",
            "content": "Test message",
            "message_type": "text",
            "priority": 5,
            "metadata": {"key": "value"}
        }

        result = MessageValidator.validate_message_dict(message)
        assert result["sender_id"] == "agent_001"
        assert result["receiver_id"] == "agent_002"
        assert result["channel_id"] == "channel_001"

    def test_validate_message_dict_missing_sender(self):
        """测试缺少发送者ID"""
        message = {
            "content": "Test message"
        }

        with pytest.raises(ValidationException) as exc_info:
            MessageValidator.validate_message_dict(message)

        error = exc_info.value.args[0]
        assert error.code == ValidationErrorCode.MISSING_REQUIRED_FIELD
        assert "sender_id" in error.message

    def test_validate_message_dict_missing_content(self):
        """测试缺少内容"""
        message = {
            "sender_id": "agent_001"
        }

        with pytest.raises(ValidationException) as exc_info:
            MessageValidator.validate_message_dict(message)

        error = exc_info.value.args[0]
        assert error.code == ValidationErrorCode.MISSING_REQUIRED_FIELD
        assert "content" in error.message

    def test_validate_message_dict_invalid_sender_id(self):
        """测试无效的发送者ID"""
        message = {
            "sender_id": "invalid@id!",
            "content": "Test message"
        }

        with pytest.raises(ValidationException) as exc_info:
            MessageValidator.validate_message_dict(message)

        error = exc_info.value.args[0]
        assert error.field == "sender_id"

    def test_validate_message_dict_invalid_message_type(self):
        """测试无效的消息类型"""
        message = {
            "sender_id": "agent_001",
            "content": "Test message",
            "message_type": "invalid_type"
        }

        with pytest.raises(ValidationException) as exc_info:
            MessageValidator.validate_message_dict(message)

        error = exc_info.value.args[0]
        assert error.field == "message_type"

    def test_validate_message_dict_invalid_priority_type(self):
        """测试优先级类型错误"""
        message = {
            "sender_id": "agent_001",
            "content": "Test message",
            "priority": "high"
        }

        with pytest.raises(ValidationException) as exc_info:
            MessageValidator.validate_message_dict(message)

        error = exc_info.value.args[0]
        assert error.code == ValidationErrorCode.INVALID_TYPE

    def test_validate_message_dict_invalid_priority_range(self):
        """测试优先级超出范围"""
        message = {
            "sender_id": "agent_001",
            "content": "Test message",
            "priority": 15  # 超出0-9范围
        }

        with pytest.raises(ValidationException) as exc_info:
            MessageValidator.validate_message_dict(message)

        error = exc_info.value.args[0]
        assert error.code == ValidationErrorCode.OUT_OF_RANGE

    def test_validate_message_dict_invalid_metadata(self):
        """测试无效的元数据"""
        message = {
            "sender_id": "agent_001",
            "content": "Test message",
            "metadata": "not a dict"
        }

        with pytest.raises(ValidationException) as exc_info:
            MessageValidator.validate_message_dict(message)

        error = exc_info.value.args[0]
        assert error.field == "metadata"


@pytest.mark.asyncio
@pytest.mark.unit
class TestValidationDecorators:
    """验证装饰器测试"""

    async def test_validate_message_decorator(self):
        """测试消息验证装饰器"""
        @validate_message
        async def test_func(receiver_id, content, metadata=None):
            return {"receiver_id": receiver_id, "content": content, "metadata": metadata}

        # 有效调用
        result = await test_func("agent_001", "test content")
        assert result["receiver_id"] == "agent_001"
        assert result["content"] == "test content"

    async def test_validate_message_decorator_invalid_receiver(self):
        """测试装饰器拒绝无效接收者"""
        @validate_message
        async def test_func(receiver_id, content):
            return True

        with pytest.raises(ValidationException):
            await test_func("invalid@id!", "test content")

    async def test_validate_channel_id_decorator(self):
        """测试通道ID验证装饰器"""
        @validate_channel_id
        async def test_func(channel_id):
            return f"Channel: {channel_id}"

        result = await test_func("channel_001")
        assert result == "Channel: channel_001"

    async def test_validate_channel_id_decorator_invalid(self):
        """测试装饰器拒绝无效通道ID"""
        @validate_channel_id
        async def test_func(channel_id):
            return True

        with pytest.raises(ValidationException):
            await test_func("invalid channel!")

    async def test_validate_agent_id_decorator(self):
        """测试代理ID验证装饰器"""
        @validate_agent_id
        async def test_func(agent_id):
            return f"Agent: {agent_id}"

        result = await test_func("agent_001")
        assert result == "Agent: agent_001"

    async def test_validate_agent_id_decorator_invalid(self):
        """测试装饰器拒绝无效代理ID"""
        @validate_agent_id
        async def test_func(agent_id):
            return True

        with pytest.raises(ValidationException):
            await test_func("agent@123")


@pytest.mark.unit
class TestValidationErrorCode:
    """验证错误代码测试"""

    def test_all_codes_defined(self):
        """测试所有错误代码已定义"""
        required_codes = [
            "MISSING_REQUIRED_FIELD",
            "INVALID_FORMAT",
            "INVALID_TYPE",
            "EMPTY_VALUE",
            "TOO_LONG",
            "TOO_SHORT",
            "INVALID_PATTERN",
            "OUT_OF_RANGE",
            "UNKNOWN_FIELD"
        ]

        for code_name in required_codes:
            assert hasattr(ValidationErrorCode, code_name)
            code = getattr(ValidationErrorCode, code_name)
            assert isinstance(code.value, str)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
