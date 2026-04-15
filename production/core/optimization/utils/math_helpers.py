#!/usr/bin/env python3
"""
数学工具函数 - 安全的数学运算
Math Helpers - Safe Mathematical Operations

作者: 小诺·双鱼公主
版本: v1.0.0
"""

from __future__ import annotations
import numbers
from typing import TypeVar

# 支持的数值类型
T = TypeVar("T", int, float)


def safe_divide(a: T, b: T, default: T | None = None) -> T | float:
    """
    安全的除法运算,避免除零错误

    Args:
        a: 被除数
        b: 除数
        default: 除数为零时的默认值(如果为None则返回0)

    Returns:
        除法结果或默认值

    Examples:
        >>> safe_divide(10, 2)
        5.0
        >>> safe_divide(10, 0)
        0
        >>> safe_divide(10, 0, default=-1)
        -1
    """
    if not isinstance(a, numbers.Number) or not isinstance(b, numbers.Number):
        raise TypeError(f"参数必须是数值类型: a={type(a)}, b={type(b)}")

    # 检查除数是否为零或接近零
    if b == 0 or (isinstance(b, float) and abs(b) < 1e-10):
        return default if default is not None else 0

    return a / b


def safe_mean(values: list[float]) -> float:
    """
    计算平均值,处理空列表

    Args:
        values: 数值列表

    Returns:
        平均值,空列表返回0

    Examples:
        >>> safe_mean([1, 2, 3, 4, 5])
        3.0
        >>> safe_mean([])
        0
    """
    if not values:
        return 0.0
    return sum(values) / len(values)


def safe_std(values: list[float]) -> float:
    """
    计算标准差,处理空列表或单元素列表

    Args:
        values: 数值列表

    Returns:
        标准差,空列表或单元素返回0

    Examples:
        >>> import math
        >>> abs(safe_std([1, 2, 3, 4, 5]) - 1.414) < 0.01
        True
        >>> safe_std([])
        0
    """
    if len(values) < 2:
        return 0.0
    mean = safe_mean(values)
    variance = sum((x - mean) ** 2 for x in values) / len(values)
    return variance**0.5


def normalize_weights(weights: dict) -> dict:
    """
    归一化权重字典

    Args:
        weights: 权重字典 {key: weight}

    Returns:
        归一化后的权重字典,总和为1

    Examples:
        >>> normalize_weights({'a': 1, 'b': 2, 'c': 3})
        {'a': 0.166..., 'b': 0.333..., 'c': 0.5}
        >>> normalize_weights({})
        {}
    """
    if not weights:
        return {}

    total = sum(weights.values())
    if total == 0:
        # 如果总和为0,平均分配
        equal_weight = 1.0 / len(weights)
        return dict.fromkeys(weights, equal_weight)

    return {k: v / total for k, v in weights.items()}


def weighted_average(values: list[float], weights: list[float]) -> float:
    """
    计算加权平均

    Args:
        values: 数值列表
        weights: 权重列表

    Returns:
        加权平均值

    Examples:
        >>> weighted_average([1, 2, 3], [0.5, 0.3, 0.2])
        1.7
        >>> weighted_average([], [])
        0
    """
    if not values or not weights or len(values) != len(weights):
        return 0.0

    total_weight = sum(weights)
    if total_weight == 0:
        return safe_mean(values)

    weighted_sum = sum(v * w for v, w in zip(values, weights, strict=False))
    return weighted_sum / total_weight


def clamp(value: T, min_val: T, max_val: T) -> T:
    """
    将值限制在指定范围内

    Args:
        value: 输入值
        min_val: 最小值
        max_val: 最大值

    Returns:
        限制后的值

    Examples:
        >>> clamp(5, 0, 10)
        5
        >>> clamp(-5, 0, 10)
        0
        >>> clamp(15, 0, 10)
        10
    """
    return max(min_val, min(value, max_val))


def lerp(a: float, b: float, t: float) -> float:
    """
    线性插值

    Args:
        a: 起始值
        b: 结束值
        t: 插值参数 [0, 1]

    Returns:
        插值结果

    Examples:
        >>> lerp(0, 10, 0.5)
        5.0
        >>> lerp(0, 10, 0.0)
        0.0
        >>> lerp(0, 10, 1.0)
        10.0
    """
    return a + (b - a) * t


def smooth_step(t: float) -> float:
    """
    平滑阶跃函数(S形曲线)

    Args:
        t: 输入值,通常在[0, 1]范围内

    Returns:
        平滑后的值

    Examples:
        >>> smooth_step(0.0)
        0.0
        >>> smooth_step(0.5)
        0.5
        >>> smooth_step(1.0)
        1.0
    """
    t = clamp(t, 0.0, 1.0)
    return t * t * (3 - 2 * t)
