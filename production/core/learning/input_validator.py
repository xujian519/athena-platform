#!/usr/bin/env python3
from __future__ import annotations
"""
学习模块输入验证器
Learning Module Input Validator

提供输入数据的验证功能，"""

from dataclasses import dataclass, field
from typing import Any


@dataclass
class ValidationResult:
    """验证结果"""
    is_valid: bool
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


class InputValidator:
    """输入验证器基类"""

    def validate(self, data: dict[str, Any]) -> ValidationResult:
        """
        验证输入数据

        Args:
            data: 待验证的输入数据
                - query: 查询内容 (必填)
                - content: 待分析内容 (必填)
                - context: 上下文信息 (可选)
                - max_length: 最大长度限制 (可选)
                - min_items: 最小项数限制 (可选)

        Returns:
            ValidationResult: 验证结果对象
        """
        errors: list[str] = []
        warnings: list[str] = []

        # 检查数据类型
        if not isinstance(data, dict):
            return ValidationResult(
                is_valid=False,
                errors=["输入数据必须是字典类型"],
                warnings=[]
            )

        # 检查必填字段
        required_fields = ["query", "content"]
        for field_name in required_fields:
            if field_name not in data:
                errors.append(f"缺少必填字段: {field_name}")

        # 检查可选字段并添加提示
        if "context" in data:
            warnings.append("建议提供context信息以提高分析准确性")

        # 检查字段长度
        if "query" in data:
            query = data["query"]
            if len(query) > 100:
                errors.append("查询内容过长，可能影响性能")

        if "content" in data:
            content = data["content"]
            if len(content) > 10000:
                errors.append("内容长度超过10000个字符")

        # 检查context类型
        if "context" in data and not isinstance(data["context"], dict):
            warnings.append("context字段应该是字典类型")

        # 检查最小项数
        if "min_items" in data:
            min_items = data["min_items"]
            if not isinstance(min_items, int) or min_items < 1:
                errors.append("min_items必须是正整数且必须 >= 1")

        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings
        )


def get_input_validator() -> InputValidator:
    """获取输入验证器实例"""
    return InputValidator()
