#!/usr/bin/env python3
"""
输入验证工具函数
Input Validation Helpers

作者: 小诺·双鱼公主
版本: v1.0.0
"""

import re
from typing import Any, Dict, List, Optional, TypeVar

T = TypeVar("T")


def validate_string(
    value: Any,
    param_name: str = "value",
    min_length: int = 0,
    max_length: int = 10000,
    allow_empty: bool = False,
    pattern: str | None = None,
) -> str:
    """
    验证字符串参数

    Args:
        value: 输入值
        param_name: 参数名称
        min_length: 最小长度
        max_length: 最大长度
        allow_empty: 是否允许空字符串
        pattern: 正则表达式模式

    Returns:
        验证后的字符串

    Raises:
        ValueError: 验证失败
        TypeError: 类型错误

    Examples:
        >>> validate_string("hello", "text", min_length=1)
        'hello'
        >>> validate_string("", "text", allow_empty=False)
        ValueError: text不能为空
    """
    if not isinstance(value, str):
        raise TypeError(f"{param_name}必须是字符串类型")

    if not value and not allow_empty:
        raise ValueError(f"{param_name}不能为空")

    if len(value) < min_length:
        raise ValueError(f"{param_name}长度不能小于{min_length}")

    if len(value) > max_length:
        raise ValueError(f"{param_name}长度不能大于{max_length}")

    if pattern and not re.match(pattern, value):
        raise ValueError(f"{param_name}格式不正确")

    return value


def validate_number(
    value: Any,
    param_name: str = "value",
    min_value: float | None = None,
    max_value: float | None = None,
    allow_zero: bool = True,
) -> float:
    """
    验证数值参数

    Args:
        value: 输入值
        param_name: 参数名称
        min_value: 最小值
        max_value: 最大值
        allow_zero: 是否允许零

    Returns:
        验证后的数值

    Raises:
        ValueError: 验证失败
        TypeError: 类型错误

    Examples:
        >>> validate_number(5, "age", min_value=0, max_value=120)
        5.0
        >>> validate_number(0, "rate", allow_zero=False)
        ValueError: rate不能为零
    """
    if not isinstance(value, (int, float)):
        raise TypeError(f"{param_name}必须是数值类型")

    num_value = float(value)

    if not allow_zero and num_value == 0:
        raise ValueError(f"{param_name}不能为零")

    if min_value is not None and num_value < min_value:
        raise ValueError(f"{param_name}不能小于{min_value}")

    if max_value is not None and num_value > max_value:
        raise ValueError(f"{param_name}不能大于{max_value}")

    return num_value


def validate_dict(
    value: Any,
    param_name: str = "value",
    required_keys: list[str] | None = None,
    allow_empty: bool = True,
) -> dict[str, Any]:
    """
    验证字典参数

    Args:
        value: 输入值
        param_name: 参数名称
        required_keys: 必需的键列表
        allow_empty: 是否允许空字典

    Returns:
        验证后的字典

    Raises:
        ValueError: 验证失败
        TypeError: 类型错误

    Examples:
        >>> validate_dict({"a": 1}, "data")
        {'a': 1}
        >>> validate_dict({}, "data", allow_empty=False)
        ValueError: data不能为空字典
    """
    if not isinstance(value, dict):
        raise TypeError(f"{param_name}必须是字典类型")

    if not value and not allow_empty:
        raise ValueError(f"{param_name}不能为空字典")

    if required_keys:
        missing_keys = set(required_keys) - set(value.keys())
        if missing_keys:
            raise ValueError(f"{param_name}缺少必需的键: {missing_keys}")

    return value


def validate_list(
    value: Any,
    param_name: str = "value",
    min_length: int = 0,
    max_length: int | None = None,
    allow_empty: bool = True,
    item_type: type | None = None,
) -> list[Any]:
    """
    验证列表参数

    Args:
        value: 输入值
        param_name: 参数名称
        min_length: 最小长度
        max_length: 最大长度
        allow_empty: 是否允许空列表
        item_type: 列表项类型

    Returns:
        验证后的列表

    Raises:
        ValueError: 验证失败
        TypeError: 类型错误

    Examples:
        >>> validate_list([1, 2, 3], "items", min_length=1)
        [1, 2, 3]
        >>> validate_list([], "items", allow_empty=False)
        ValueError: items不能为空列表
    """
    if not isinstance(value, list):
        raise TypeError(f"{param_name}必须是列表类型")

    if not value and not allow_empty:
        raise ValueError(f"{param_name}不能为空列表")

    if len(value) < min_length:
        raise ValueError(f"{param_name}长度不能小于{min_length}")

    if max_length is not None and len(value) > max_length:
        raise ValueError(f"{param_name}长度不能大于{max_length}")

    if item_type:
        for i, item in enumerate(value):
            if not isinstance(item, item_type):
                raise TypeError(f"{param_name}[{i}]必须是{item_type.__name__}类型")

    return value


def validate_positive_number(value: Any, param_name: str = "value") -> float:
    """
    验证正数

    Args:
        value: 输入值
        param_name: 参数名称

    Returns:
        验证后的数值

    Raises:
        ValueError: 验证失败
        TypeError: 类型错误
    """
    return validate_number(value, param_name, min_value=0.0, allow_zero=False)


def validate_probability(value: Any, param_name: str = "probability") -> float:
    """
    验证概率值 (0-1)

    Args:
        value: 输入值
        param_name: 参数名称

    Returns:
        验证后的概率值

    Raises:
        ValueError: 验证失败
        TypeError: 类型错误
    """
    return validate_number(value, param_name, min_value=0.0, max_value=1.0)


def validate_percentage(value: Any, param_name: str = "percentage") -> float:
    """
    验证百分比 (0-100)

    Args:
        value: 输入值
        param_name: 参数名称

    Returns:
        验证后的百分比

    Raises:
        ValueError: 验证失败
        TypeError: 类型错误
    """
    return validate_number(value, param_name, min_value=0.0, max_value=100.0)


def validate_file_path(value: Any, param_name: str = "file_path", must_exist: bool = False) -> str:
    """
    验证文件路径

    Args:
        value: 输入值
        param_name: 参数名称
        must_exist: 文件是否必须存在

    Returns:
        验证后的文件路径

    Raises:
        ValueError: 验证失败
        TypeError: 类型错误
    """
    from pathlib import Path

    if not isinstance(value, (str, Path)):
        raise TypeError(f"{param_name}必须是字符串或Path类型")

    path = Path(value)

    if must_exist and not path.exists():
        raise ValueError(f"{param_name}指向的文件不存在: {value}")

    return str(path)
