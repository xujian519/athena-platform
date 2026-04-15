#!/usr/bin/env python3
"""
测试：输入验证框架
Test: Input Validation Framework
"""

from __future__ import annotations
import sys
from pathlib import Path

import pytest

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from core.perception.validation import (
    NumberValidator,
    PathValidator,
    StringValidator,
    get_global_validator,
)


class TestStringValidator:
    """测试字符串验证器"""

    def test_valid_string(self):
        """测试有效字符串"""
        validator = StringValidator()
        result = validator.validate("Hello, World!", "test_field")
        assert result.is_valid
        assert not result.errors

    def test_empty_string(self):
        """测试空字符串"""
        validator = StringValidator(allow_empty=False)
        result = validator.validate("", "test_field")
        assert not result.is_valid
        assert "不能为空" in result.errors[0]

    def test_string_too_long(self):
        """测试字符串过长"""
        validator = StringValidator(max_length=10)
        result = validator.validate("This is a very long string", "test_field")
        assert not result.is_valid
        assert "长度不能超过" in result.errors[0]  # 错误消息包含"长度不能超过"

    def test_html_sanitization(self):
        """测试HTML清理"""
        validator = StringValidator(sanitize_html=True)
        result = validator.validate("<script>alert('xss')</script>Hello", "test_field")
        # 应该清理HTML并返回
        assert "<script>" not in result.value
        assert result.warnings


class TestPathValidator:
    """测试路径验证器"""

    def test_valid_path(self):
        """测试有效路径"""
        validator = PathValidator()
        result = validator.validate("./test.txt", "test_field")
        assert result.is_valid

    def test_path_traversal(self):
        """测试路径遍历攻击"""
        validator = PathValidator()
        result = validator.validate("../../../etc/passwd", "test_field")
        assert not result.is_valid
        assert "路径遍历" in result.errors[0]

    def test_absolute_path_blocked(self):
        """测试绝对路径被阻止"""
        validator = PathValidator(allow_absolute=False)
        result = validator.validate("/etc/passwd", "test_field")
        assert not result.is_valid
        assert "不允许使用绝对路径" in result.errors[0]


class TestNumberValidator:
    """测试数字验证器"""

    def test_valid_integer(self):
        """测试有效整数"""
        validator = NumberValidator()
        result = validator.validate(42, "test_field")
        assert result.is_valid
        assert result.value == 42

    def test_string_to_number(self):
        """测试字符串转数字"""
        validator = NumberValidator()
        result = validator.validate("123", "test_field")
        assert result.is_valid
        assert result.value == 123

    def test_negative_number_blocked(self):
        """测试负数被阻止"""
        validator = NumberValidator(allow_negative=False)
        result = validator.validate(-5, "test_field")
        assert not result.is_valid
        assert "不能为负数" in result.errors[0]

    def test_out_of_range(self):
        """测试超出范围"""
        validator = NumberValidator(min_value=0, max_value=100)
        result = validator.validate(150, "test_field")
        assert not result.is_valid
        assert "不能大于" in result.errors[0]


class TestInputValidator:
    """测试统一输入验证器"""

    def test_batch_validation(self):
        """测试批量验证"""
        validator = get_global_validator()  # 使用全局验证器
        data = {
            "username": "test_user",
            "age": "25",
            "email": "test@example.com",
        }
        rules = {
            "username": "string",  # 使用string而不是strict_string
            "age": "number",
            "email": "string",
        }

        results = validator.validate_batch(data, rules)
        assert validator.is_valid(results)
        assert all(r.is_valid for r in results.values())

    def test_batch_validation_failure(self):
        """测试批量验证失败"""
        validator = get_global_validator()  # 使用全局验证器
        data = {
            "username": "",  # 空字符串，对string验证器应该通过
            "age": "abc",  # 无效数字，应该失败
        }
        rules = {
            "username": "string",  # 空字符串对string验证器是允许的
            "age": "number",
        }

        results = validator.validate_batch(data, rules)
        # username应该通过（string允许空字符串），age应该失败
        assert results["username"].is_valid
        assert not results["age"].is_valid


class TestGlobalValidator:
    """测试全局验证器"""

    def test_get_global_validator(self):
        """测试获取全局验证器"""
        validator = get_global_validator()
        assert validator is not None
        assert "string" in validator.validators
        assert "path" in validator.validators
        assert "image" in validator.validators
        assert "number" in validator.validators


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
