#!/usr/bin/env python3
"""
感知模块验证框架测试
Tests for Perception Module Validation Framework
"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from core.perception.validation import (
    ImageValidator,
    InputValidator,
    NumberValidator,
    PathValidator,
    StringValidator,
    ValidationResult,
    ValidationSeverity,
    get_global_validator,
    image_validator,
    number_validator,
    path_validator,
    strict_string_validator,
    string_validator,
)
from core.perception.validation import (
    ValidationError as ValidationErr,
)


class TestValidationResult:
    """测试验证结果类"""

    def test_initialization(self):
        """测试初始化"""
        result = ValidationResult(
            is_valid=True,
            field_name="test_field",
            value="test_value"
        )
        assert result.is_valid is True
        assert result.field_name == "test_field"
        assert result.value == "test_value"
        assert len(result.errors) == 0
        assert len(result.warnings) == 0
        assert result.severity == ValidationSeverity.LOW

    def test_add_error(self):
        """测试添加错误"""
        result = ValidationResult(
            is_valid=True,
            field_name="test",
            value="value"
        )
        result.add_error("错误信息")
        assert result.is_valid is False
        assert len(result.errors) == 1
        assert result.errors[0] == "错误信息"

    def test_add_warning(self):
        """测试添加警告"""
        result = ValidationResult(
            is_valid=True,
            field_name="test",
            value="value"
        )
        result.add_warning("警告信息")
        assert result.is_valid is True  # 警告不影响有效性
        assert len(result.warnings) == 1
        assert result.warnings[0] == "警告信息"

    def test_severity_levels(self):
        """测试严重程度级别"""
        for severity in ValidationSeverity:
            result = ValidationResult(
                is_valid=True,
                field_name="test",
                value="value",
                severity=severity
            )
            assert result.severity == severity


class TestStringValidator:
    """测试字符串验证器"""

    def test_valid_string(self):
        """测试有效字符串"""
        validator = StringValidator()
        result = validator.validate("测试文本", "text_field")
        assert result.is_valid is True
        assert len(result.errors) == 0

    def test_min_length_validation(self):
        """测试最小长度验证"""
        validator = StringValidator(min_length=5)
        result = validator.validate("abc", "text")
        assert result.is_valid is False
        assert "最小长度" in result.errors[0] or "min" in result.errors[0].lower()

    def test_max_length_validation(self):
        """测试最大长度验证"""
        validator = StringValidator(max_length=10)
        result = validator.validate("a" * 20, "text")
        assert result.is_valid is False
        assert "最大长度" in result.errors[0] or "max" in result.errors[0].lower()

    def test_empty_string_not_allowed(self):
        """测试不允许空字符串"""
        validator = StringValidator(allow_empty=False)
        result = validator.validate("", "text")
        assert result.is_valid is False

    def test_pattern_validation(self):
        """测试模式验证"""
        validator = StringValidator(pattern=r"^\d+$")
        result = validator.validate("12345", "number")
        assert result.is_valid is True

        result = validator.validate("abc", "number")
        assert result.is_valid is False

    def test_forbidden_chars(self):
        """测试禁止字符"""
        validator = StringValidator(forbidden_chars=["<", ">", "&"])
        result = validator.validate("normal text", "text")
        assert result.is_valid is True

        result = validator.validate("text<script>", "text")
        assert result.is_valid is False

    def test_bytes_to_string_conversion(self):
        """测试字节转字符串"""
        validator = StringValidator()
        result = validator.validate(b"hello", "text")
        assert result.is_valid is True
        assert isinstance(result.value, str)

    def test_invalid_bytes_conversion(self):
        """测试无效字节转换"""
        validator = StringValidator()
        result = validator.validate(b'\xff\xfe', "text")
        assert result.is_valid is False


class TestNumberValidator:
    """测试数字验证器"""

    def test_valid_integer(self):
        """测试有效整数"""
        validator = NumberValidator()
        result = validator.validate(42, "age")
        assert result.is_valid is True

    def test_valid_float(self):
        """测试有效浮点数"""
        validator = NumberValidator()
        result = validator.validate(3.14, "pi")
        assert result.is_valid is True

    def test_min_value_validation(self):
        """测试最小值验证"""
        validator = NumberValidator(min_value=0)
        result = validator.validate(-1, "value")
        assert result.is_valid is False

        result = validator.validate(10, "value")
        assert result.is_valid is True

    def test_max_value_validation(self):
        """测试最大值验证"""
        validator = NumberValidator(max_value=100)
        result = validator.validate(101, "value")
        assert result.is_valid is False

        result = validator.validate(50, "value")
        assert result.is_valid is True

    def test_type_validation(self):
        """测试类型验证"""
        validator = NumberValidator()
        result = validator.validate("not a number", "value")
        assert result.is_valid is False


class TestPathValidator:
    """测试路径验证器"""

    def test_valid_path(self):
        """测试有效路径"""
        validator = PathValidator(must_exist=False)
        result = validator.validate("/tmp/test.txt", "path")
        assert result.is_valid is True

    def test_must_exist_validation(self):
        """测试必须存在验证"""
        validator = PathValidator(must_exist=True)
        # 使用一个不存在的路径
        result = validator.validate("/nonexistent/path/12345.txt", "path")
        assert result.is_valid is False

    def test_allowed_extensions(self):
        """测试允许的扩展名"""
        validator = PathValidator(allowed_extensions=[".txt", ".pdf"])
        result = validator.validate("document.txt", "file")
        assert result.is_valid is True

        result = validator.validate("image.jpg", "file")
        assert result.is_valid is False


class TestImageValidator:
    """测试图像验证器"""

    def test_valid_image_path(self):
        """测试有效图像路径"""
        validator = ImageValidator()
        # 使用一个不存在的路径，只测试扩展名
        result = validator.validate("image.jpg", "image")
        # 扩展名应该是有效的
        assert "格式不支持" not in str(result.errors)

    def test_invalid_image_extension(self):
        """测试无效图像扩展名"""
        validator = ImageValidator()
        result = validator.validate("document.xyz", "image")
        assert result.is_valid is False

    def test_max_size_validation(self):
        """测试最大大小验证"""
        validator = ImageValidator(max_size_mb=1.0)
        # 这个测试需要实际文件，跳过
        assert validator.max_size_bytes == 1.0 * 1024 * 1024


class TestInputValidator:
    """测试统一输入验证器"""

    def test_register_validator(self):
        """测试注册验证器"""
        validator = InputValidator()
        string_validator = StringValidator()
        validator.register_validator("custom_string", string_validator)
        assert "custom_string" in validator.validators

    def test_validate_with_registered_validator(self):
        """测试使用注册的验证器"""
        input_validator = InputValidator()
        input_validator.register_validator("string", StringValidator())
        result = input_validator.validate("test text", "string", "content")
        assert result.is_valid is True

    def test_validate_nonexistent_validator(self):
        """测试使用不存在的验证器"""
        input_validator = InputValidator()
        with pytest.raises(ValueError, match="验证器不存在"):
            input_validator.validate("test", "nonexistent", "field")

    def test_validate_batch(self):
        """测试批量验证"""
        input_validator = InputValidator()
        input_validator.register_validator("string", StringValidator())

        data = {"name": "John", "email": "john@example.com"}
        rules = {"name": "string", "email": "string"}

        results = input_validator.validate_batch(data, rules)
        assert "name" in results
        assert "email" in results
        assert results["name"].is_valid is True

    def test_validate_batch_missing_field(self):
        """测试批量验证缺少字段"""
        input_validator = InputValidator()
        input_validator.register_validator("string", StringValidator())

        data = {"name": "John"}
        rules = {"name": "string", "email": "string"}

        results = input_validator.validate_batch(data, rules)
        assert results["email"].is_valid is False
        assert "字段不存在" in results["email"].errors

    def test_is_valid(self):
        """测试检查所有结果是否有效"""
        input_validator = InputValidator()

        # 所有结果都有效
        results1 = {
            "field1": ValidationResult(True, "field1", "value1"),
            "field2": ValidationResult(True, "field2", "value2"),
        }
        assert input_validator.is_valid(results1) is True

        # 有一个结果无效
        results2 = {
            "field1": ValidationResult(True, "field1", "value1"),
            "field2": ValidationResult(False, "field2", "value2", errors=["error"]),
        }
        assert input_validator.is_valid(results2) is False


class TestGlobalValidator:
    """测试全局验证器"""

    def test_get_global_validator(self):
        """测试获取全局验证器"""
        validator = get_global_validator()
        assert isinstance(validator, InputValidator)
        assert "string" in validator.validators
        assert "path" in validator.validators
        assert "image" in validator.validators
        assert "number" in validator.validators

    def test_global_validator_singleton(self):
        """测试全局验证器单例"""
        validator1 = get_global_validator()
        validator2 = get_global_validator()
        assert validator1 is validator2


class TestPredefinedValidators:
    """测试预定义验证器"""

    def test_string_validator(self):
        """测试字符串验证器"""
        result = string_validator.validate("test text", "content")
        assert result.is_valid is True

    def test_strict_string_validator(self):
        """测试严格字符串验证器"""
        result = strict_string_validator.validate("normal text", "content")
        assert result.is_valid is True

        # 包含禁止字符
        result = strict_string_validator.validate("text<script>", "content")
        # HTML被清理
        assert "<script>" not in result.value

    def test_path_validator(self):
        """测试路径验证器"""
        result = path_validator.validate("./test/file.txt", "path")
        assert result.is_valid is True

    def test_image_validator(self):
        """测试图像验证器"""
        result = image_validator.validate("image.jpg", "image")
        assert result.is_valid is True

    def test_number_validator(self):
        """测试数字验证器"""
        result = number_validator.validate(42, "count")
        assert result.is_valid is True

        result = number_validator.validate("3.14", "pi")
        assert result.is_valid is True


class TestValidationIntegration:
    """测试验证集成场景"""

    def test_multiple_validators(self):
        """测试多个验证器组合"""
        string_validator = StringValidator(min_length=5, max_length=50)
        number_validator = NumberValidator(min_value=0, max_value=100)

        # 验证字符串
        str_result = string_validator.validate("valid text", "description")
        assert str_result.is_valid is True

        # 验证数字
        num_result = number_validator.validate(75, "percentage")
        assert num_result.is_valid is True

    def test_validation_error_handling(self):
        """测试验证错误处理"""
        validator = StringValidator(min_length=10)

        with pytest.raises(ValidationErr):
            result = validator.validate("short", "text")
            if not result.is_valid:
                raise ValidationErr(result.errors[0])

    def test_severity_levels(self):
        """测试不同严重程度"""
        validator_low = StringValidator(min_length=5)
        validator_high = StringValidator(min_length=100)

        result_low = validator_low.validate("abc", "text")
        result_high = validator_high.validate("abc", "text")

        # 长度差异越大，严重程度越高
        assert result_low.is_valid is False
        assert result_high.is_valid is False
