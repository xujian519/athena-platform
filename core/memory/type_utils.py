#!/usr/bin/env python3
"""
类型统一工具

解决TaskDomain和StepType的Enum/str混用问题。

Author: Athena平台团队
Created: 2026-01-20
Version: v1.0.0
"""

from enum import Enum
from typing import Any


def normalize_enum_value(value: str | Optional[Enum, enum_class: type | None = None) -> str:
    """
    将Enum或str标准化为字符串值

    Args:
        value: Enum实例、字符串或None
        enum_class: 可选的Enum类，用于验证

    Returns:
        标准化的字符串值

    Examples:
        >>> normalize_enum_value(TaskDomain.PATENT)
        'patent'
        >>> normalize_enum_value('patent')
        'patent'
        >>> normalize_enum_value(None)
        ''
    """
    if value is None:
        return ""

    # 如果是Enum，提取其值
    if isinstance(value, Enum):
        return value.value

    # 如果已经是字符串，直接返回
    if isinstance(value, str):
        return value

    # 其他类型转换为字符串
    return str(value)


def safe_domain_getter(value: Any) -> str:
    """
    安全获取domain值，统一返回字符串

    Args:
        value: TaskDomain Enum或字符串

    Returns:
        标准化的domain字符串
    """
    return normalize_enum_value(value)


def safe_step_type_getter(value: Any) -> str:
    """
    安全获取step_type值，统一返回字符串

    Args:
        value: StepType Enum或字符串

    Returns:
        标准化的step_type字符串
    """
    return normalize_enum_value(value)


def ensure_enum(value: str | Enum, enum_class: type) -> Enum:
    """
    确保值是Enum类型

    Args:
        value: 字符串或Enum
        enum_class: 目标Enum类

    Returns:
        Enum实例

    Raises:
        ValueError: 如果值无法转换为Enum
    """
    if isinstance(value, enum_class):
        return value

    if isinstance(value, str):
        try:
            return enum_class(value)
        except ValueError as e:
            raise ValueError(f"'{value}' is not a valid {enum_class.__name__}") from e

    raise TypeError(f"Expected str or {enum_class.__name__}, got {type(value)}")


__all__ = [
    'ensure_enum',
    'normalize_enum_value',
    'safe_domain_getter',
    'safe_step_type_getter'
]
