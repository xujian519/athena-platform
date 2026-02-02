#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
感知模块统一输入验证框架
Perception Module Unified Input Validation Framework

提供统一的输入验证、清理和安全检查功能

作者: Athena AI系统
创建时间: 2026-01-26
版本: 1.0.0
"""

import re
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class ValidationError(Exception):
    """验证错误"""
    pass


class ValidationSeverity(Enum):
    """验证严重程度"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class ValidationResult:
    """验证结果"""
    is_valid: bool
    field_name: str
    value: Any
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    severity: ValidationSeverity = ValidationSeverity.LOW

    def add_error(self, message: str) -> None:
        """添加错误信息"""
        self.errors.append(message)
        self.is_valid = False

    def add_warning(self, message: str) -> None:
        """添加警告信息"""
        self.warnings.append(message)


class Validator(ABC):
    """验证器基类"""

    @abstractmethod
    def validate(self, value: Any, field_name: str = "field") -> ValidationResult:
        """验证输入值"""
        pass


class StringValidator(Validator):
    """字符串验证器"""

    def __init__(
        self,
        min_length: int = 0,
        max_length: int = 10000,
        allow_empty: bool = True,
        pattern: str | None = None,
        forbidden_chars: list[str] | None = None,
        sanitize_html: bool = True,
    ):
        self.min_length = min_length
        self.max_length = max_length
        self.allow_empty = allow_empty
        self.pattern = re.compile(pattern) if pattern else None
        self.forbidden_chars = forbidden_chars or []
        self.sanitize_html = sanitize_html

    def validate(self, value: Any, field_name: str = "field") -> ValidationResult:
        """验证字符串"""
        result = ValidationResult(is_valid=True, field_name=field_name, value=value)

        # 类型检查
        if not isinstance(value, (str, bytes)):
            result.add_error(f"{field_name}必须是字符串类型")
            return result

        # 如果是bytes，转换为str
        if isinstance(value, bytes):
            try:
                value = value.decode('utf-8')
            except UnicodeDecodeError:
                result.add_error(f"{field_name}包含无效的字符编码")
                return result

        # 长度检查
        if not self.allow_empty and not value:
            result.add_error(f"{field_name}不能为空")
        elif len(value) < self.min_length:
            result.add_error(f"{field_name}长度不能少于{self.min_length}个字符")
        elif len(value) > self.max_length:
            result.add_error(f"{field_name}长度不能超过{self.max_length}个字符")

        # 模式匹配
        if self.pattern and value:
            if not self.pattern.match(value):
                result.add_error(f"{field_name}格式不正确")

        # 禁止字符检查
        for char in self.forbidden_chars:
            if char in value:
                result.add_error(f"{field_name}包含禁止的字符: {char}")

        # HTML清理（防止XSS）
        if self.sanitize_html and value:
            cleaned = self._sanitize_html(value)
            if cleaned != value:
                result.add_warning(f"{field_name}中的HTML标签已被清理")
                result.value = cleaned

        return result

    def _sanitize_html(self, text: str) -> str:
        """清理HTML标签"""
        # 移除常见的危险HTML标签
        dangerous_tags = ['<script', '</script>', '<iframe', '</iframe>',
                          '<object', '</object>', '<embed', '</embed>']
        cleaned = text
        for tag in dangerous_tags:
            cleaned = cleaned.replace(tag, '')
        return cleaned


class PathValidator(Validator):
    """路径验证器"""

    def __init__(
        self,
        allow_absolute: bool = False,
        allow_relative: bool = True,
        allowed_extensions: list[str] | None = None,
        max_length: int = 255,
        check_existence: bool = False,
    ):
        self.allow_absolute = allow_absolute
        self.allow_relative = allow_relative
        self.allowed_extensions = allowed_extensions
        self.max_length = max_length
        self.check_existence = check_existence

    def validate(self, value: Any, field_name: str = "path") -> ValidationResult:
        """验证路径"""
        result = ValidationResult(is_valid=True, field_name=field_name, value=value)

        if not isinstance(value, (str, Path)):
            result.add_error(f"{field_name}必须是路径类型")
            return result

        try:
            path = Path(value) if isinstance(value, str) else value
        except Exception as e:
            result.add_error(f"{field_name}路径格式无效: {e}")
            return result

        # 路径长度检查
        if len(str(path)) > self.max_length:
            result.add_error(f"{field_name}路径过长（最大{self.max_length}字符）")

        # 路径类型检查
        if path.is_absolute() and not self.allow_absolute:
            result.add_error(f"{field_name}不允许使用绝对路径")

        if not path.is_absolute() and not self.allow_relative:
            result.add_error(f"{field_name}不允许使用相对路径")

        # 路径遍历攻击检查
        if '..' in path.parts:
            result.add_error(f"{field_name}包含路径遍历攻击风险（..）")

        # 扩展名检查
        if self.allowed_extensions and path.suffix:
            if path.suffix.lower() not in self.allowed_extensions:
                result.add_error(
                    f"{field_name}文件类型不允许。允许的类型: {', '.join(self.allowed_extensions)}"
                )

        # 存在性检查
        if self.check_existence and not path.exists():
            result.add_warning(f"{field_name}路径不存在")

        result.value = path
        return result


class ImageValidator(Validator):
    """图像验证器"""

    def __init__(
        self,
        max_size_mb: float = 10.0,
        min_dimensions: tuple[int, int] = (1, 1),
        max_dimensions: tuple[int, int] = (10000, 10000),
        allowed_formats: list[str] | None = None,
    ):
        self.max_size_bytes = max_size_mb * 1024 * 1024
        self.min_dimensions = min_dimensions
        self.max_dimensions = max_dimensions
        self.allowed_formats = allowed_formats or ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp']

    def validate(self, value: Any, field_name: str = "image") -> ValidationResult:
        """验证图像"""
        result = ValidationResult(is_valid=True, field_name=field_name, value=value)

        # 如果是文件路径
        if isinstance(value, (str, Path)):
            path = Path(value) if isinstance(value, str) else value

            # 文件扩展名检查
            if path.suffix.lower() not in self.allowed_formats:
                result.add_error(
                    f"{field_name}格式不支持。支持的格式: {', '.join(self.allowed_formats)}"
                )

            # 文件大小检查
            if path.exists():
                size = path.stat().st_size
                if size > self.max_size_bytes:
                    result.add_error(f"{field_name}文件过大（最大{self.max_size_bytes / 1024 / 1024}MB）")

        # 如果是PIL Image对象
        elif hasattr(value, 'size'):  # PIL Image
            width, height = value.size
            if width < self.min_dimensions[0] or height < self.min_dimensions[1]:
                result.add_error(
                    f"{field_name}尺寸过小（最小{self.min_dimensions[0]}x{self.min_dimensions[1]}）"
                )
            if width > self.max_dimensions[0] or height > self.max_dimensions[1]:
                result.add_error(
                    f"{field_name}尺寸过大（最大{self.max_dimensions[0]}x{self.max_dimensions[1]}）"
                )

        return result


class NumberValidator(Validator):
    """数字验证器"""

    def __init__(
        self,
        min_value: float | None = None,
        max_value: float | None = None,
        allow_float: bool = True,
        allow_negative: bool = True,
    ):
        self.min_value = min_value
        self.max_value = max_value
        self.allow_float = allow_float
        self.allow_negative = allow_negative

    def validate(self, value: Any, field_name: str = "number") -> ValidationResult:
        """验证数字"""
        result = ValidationResult(is_valid=True, field_name=field_name, value=value)

        # 类型检查和转换
        if isinstance(value, str):
            # 尝试转换字符串
            try:
                if '.' in value:
                    value = float(value)
                else:
                    value = int(value)
            except ValueError:
                result.add_error(f"{field_name}必须是有效的数字")
                return result

        if not isinstance(value, (int, float)):
            result.add_error(f"{field_name}必须是数字类型")
            return result

        # 浮点数检查
        if isinstance(value, float) and not self.allow_float:
            result.add_error(f"{field_name}必须是整数")

        # 负数检查
        if value < 0 and not self.allow_negative:
            result.add_error(f"{field_name}不能为负数")

        # 范围检查
        if self.min_value is not None and value < self.min_value:
            result.add_error(f"{field_name}不能小于{self.min_value}")

        if self.max_value is not None and value > self.max_value:
            result.add_error(f"{field_name}不能大于{self.max_value}")

        result.value = value
        return result


class InputValidator:
    """统一输入验证器"""

    def __init__(self) -> None:
        self.validators: dict[str, Validator] = {}

    def register_validator(self, name: str, validator: Validator) -> None:
        """注册验证器"""
        self.validators[name] = validator
        logger.info(f"已注册验证器: {name}")

    def validate(self, value: Any, validator_name: str, field_name: str = "field") -> ValidationResult:
        """使用指定验证器验证输入"""
        if validator_name not in self.validators:
            raise ValueError(f"验证器不存在: {validator_name}")

        validator = self.validators[validator_name]
        return validator.validate(value, field_name)

    def validate_batch(
        self, data: dict[str, Any], rules: dict[str, str]
    ) -> dict[str, ValidationResult]:
        """
        批量验证

        Args:
            data: 待验证的数据字典 {field_name: value}
            rules: 验证规则字典 {field_name: validator_name}

        Returns:
            验证结果字典 {field_name: ValidationResult}
        """
        results = {}

        for field_name, validator_name in rules.items():
            if field_name not in data:
                results[field_name] = ValidationResult(
                    is_valid=False,
                    field_name=field_name,
                    value=None,
                    errors=["字段不存在"]
                )
                continue

            value = data[field_name]
            results[field_name] = self.validate(value, validator_name, field_name)

        return results

    def is_valid(self, results: dict[str, ValidationResult]) -> bool:
        """检查所有验证结果是否都通过"""
        return all(result.is_valid for result in results.values())


# 预定义的验证器实例
string_validator = StringValidator()
path_validator = PathValidator()
image_validator = ImageValidator()
number_validator = NumberValidator()

strict_string_validator = StringValidator(
    min_length=1,
    max_length=1000,
    forbidden_chars=['<', '>', '\'', '"', '\\'],
    sanitize_html=True,
)

# 全局验证器实例
_global_validator: InputValidator | None = None


def get_global_validator() -> InputValidator:
    """获取全局验证器实例"""
    global _global_validator
    if _global_validator is None:
        _global_validator = InputValidator()
        # 注册默认验证器
        _global_validator.register_validator("string", string_validator)
        _global_validator.register_validator("strict_string", strict_string_validator)
        _global_validator.register_validator("path", path_validator)
        _global_validator.register_validator("image", image_validator)
        _global_validator.register_validator("number", number_validator)
        logger.info("全局输入验证器已初始化")
    return _global_validator


# 导出
__all__ = [
    "ValidationError",
    "ValidationResult",
    "ValidationSeverity",
    "Validator",
    "StringValidator",
    "PathValidator",
    "ImageValidator",
    "NumberValidator",
    "InputValidator",
    "get_global_validator",
]
