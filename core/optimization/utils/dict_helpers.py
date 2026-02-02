#!/usr/bin/env python3
"""
字典工具函数 - 安全的字典访问和操作
Dict Helpers - Safe Dictionary Access and Operations

作者: 小诺·双鱼公主
版本: v1.0.0
"""

from collections.abc import Callable
from typing import Dict, List, Optional, TypeVar, Union

K = TypeVar("K")
V = TypeVar("V", bound=int | float | str)


def safe_get_nested(
    data: dict[K, dict[K, V], outer_key: K, inner_key: K, default: V] | None = None
) -> V | None:
    """
    安全访问嵌套字典

    Args:
        data: 嵌套字典
        outer_key: 外层键
        inner_key: 内层键
        default: 默认值

    Returns:
        字典值或默认值

    Examples:
        >>> data = {'a': {'b': 1}}
        >>> safe_get_nested(data, 'a', 'b')
        1
        >>> safe_get_nested(data, 'x', 'y', 0)
        0
    """
    if not data:
        return default

    inner_dict = data.get(outer_key)
    if not inner_dict:
        return default

    return inner_dict.get(inner_key, default)


def safe_set_nested(data: dict[K, dict[K, V]], outer_key: K, inner_key: K, value: V) -> None:
    """
    安全设置嵌套字典值

    Args:
        data: 嵌套字典
        outer_key: 外层键
        inner_key: 内层键
        value: 要设置的值

    Examples:
        >>> data = {}
        >>> safe_set_nested(data, 'a', 'b', 1)
        >>> data
        {'a': {'b': 1}}
    """
    if outer_key not in data:
        data[outer_key] = {}
    data[outer_key][inner_key] = value


def safe_max_from_dict(
    data: dict[K, int | float], default: int | float | None = None
) -> int | Optional[float]:
    """
    安全获取字典中的最大值

    Args:
        data: 数值字典
        default: 空字典时的默认值

    Returns:
        最大值或默认值

    Examples:
        >>> safe_max_from_dict({'a': 1, 'b': 2})
        2
        >>> safe_max_from_dict({})
    """
    if not data:
        return default
    return max(data.values())


def safe_get_or_default(
    data: dict[K, V, key: K, default: V, factory: Callable[[], V]] | None = None
) -> V:
    """
    获取字典值或创建默认值

    Args:
        data: 字典
        key: 键
        default: 默认值
        factory: 值工厂函数(可选)

    Returns:
        字典值或默认/工厂创建的值

    Examples:
        >>> data = {}
        >>> safe_get_or_default(data, 'a', 0)
        0
        >>> safe_get_or_default(data, 'a', 0, lambda: defaultdict(int))
        defaultdict(<class 'int'>, {})
    """
    if key in data:
        return data[key]

    if factory is not None:
        data[key] = factory()
        return data[key]

    return default


def ensure_nested_dict(data: dict[K, dict[K, V]], outer_key: K) -> dict[K, V]:
    """
    确保嵌套字典的外层键存在

    Args:
        data: 嵌套字典
        outer_key: 外层键

    Returns:
        内层字典

    Examples:
        >>> data = {}
        >>> inner = ensure_nested_dict(data, 'a')
        >>> inner['x'] = 1
        >>> data
        {'a': {'x': 1}}
    """
    if outer_key not in data:
        data[outer_key] = {}
    return data[outer_key]


def safe_increment(data: dict[K, float], key: K, delta: float = 1.0) -> float:
    """
    安全增加字典中的数值

    Args:
        data: 字典
        key: 键
        delta: 增量

    Returns:
        增加后的值

    Examples:
        >>> data = {'a': 1.0}
        >>> safe_increment(data, 'a', 2.0)
        3.0
        >>> safe_increment(data, 'b', 1.0)
        1.0
    """
    if key not in data:
        data[key] = 0.0
    data[key] += delta
    return data[key]


def merge_dicts(base: dict[K, V], update: dict[K, V]) -> dict[K, V]:
    """
    合并字典,返回新字典

    Args:
        base: 基础字典
        update: 更新字典

    Returns:
        合并后的新字典

    Examples:
        >>> merge_dicts({'a': 1}, {'b': 2})
        {'a': 1, 'b': 2}
        >>> merge_dicts({'a': 1}, {'a': 2})
        {'a': 2}
    """
    result = base.copy()
    result.update(update)
    return result


def filter_dict_by_keys(data: dict[K, V], keys: list[K]) -> dict[K, V]:
    """
    按键列表过滤字典

    Args:
        data: 字典
        keys: 要保留的键列表

    Returns:
        过滤后的字典

    Examples:
        >>> filter_dict_by_keys({'a': 1, 'b': 2, 'c': 3}, ['a', 'c'])
        {'a': 1, 'c': 3}
    """
    return {k: v for k, v in data.items() if k in keys}


def normalize_dict_values(data: dict[K, float]) -> dict[K, float]:
    """
    归一化字典值(使总和为1)

    Args:
        data: 数值字典

    Returns:
        归一化后的字典

    Examples:
        >>> normalize_dict_values({'a': 1, 'b': 2, 'c': 3})
        {'a': 0.166..., 'b': 0.333..., 'c': 0.5}
    """
    total = sum(data.values())
    if total == 0:
        # 平均分配
        equal = 1.0 / len(data) if data else 0
        return dict.fromkeys(data, equal)
    return {k: v / total for k, v in data.items()}
