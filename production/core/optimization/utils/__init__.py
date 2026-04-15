#!/usr/bin/env python3
"""
优化工具模块
Optimization Utils Module

提供通用的工具函数和辅助类
"""

from __future__ import annotations
from .dict_helpers import (
    ensure_nested_dict,
    filter_dict_by_keys,
    merge_dicts,
    normalize_dict_values,
    safe_get_nested,
    safe_get_or_default,
    safe_increment,
    safe_max_from_dict,
    safe_set_nested,
)
from .math_helpers import (
    clamp,
    lerp,
    normalize_weights,
    safe_divide,
    safe_mean,
    safe_std,
    smooth_step,
    weighted_average,
)
from .validation_helpers import (
    validate_dict,
    validate_file_path,
    validate_list,
    validate_number,
    validate_percentage,
    validate_positive_number,
    validate_probability,
    validate_string,
)

__all__ = [
    "clamp",
    "ensure_nested_dict",
    "filter_dict_by_keys",
    "lerp",
    "merge_dicts",
    "normalize_dict_values",
    "normalize_weights",
    "safe_divide",
    "safe_get_nested",
    "safe_get_or_default",
    "safe_increment",
    "safe_max_from_dict",
    "safe_mean",
    "safe_set_nested",
    "safe_std",
    "smooth_step",
    "validate_dict",
    "validate_file_path",
    "validate_list",
    "validate_number",
    "validate_percentage",
    "validate_positive_number",
    "validate_probability",
    "validate_string",
    "weighted_average",
]
