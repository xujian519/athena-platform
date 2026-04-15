#!/usr/bin/env python3
"""
参数验证工具
Parameter Validation Utilities

为学习引擎提供统一的参数验证功能

作者: Athena AI Team
版本: 1.0.0
创建: 2026-01-29
"""

from __future__ import annotations
from collections.abc import Callable
from functools import wraps
from typing import Any


class ValidationError(Exception):
    """参数验证错误"""
    pass


def validate_range(
    param_name: str,
    min_value: float | None = None,
    max_value: float | None = None,
    allow_none: bool = False,
):
    """
    验证参数在指定范围内的装饰器

    Args:
        param_name: 参数名称
        min_value: 最小值（包含）
        max_value: 最大值（包含）
        allow_none: 是否允许None值

    Example:
        @validate_range("satisfaction", min_value=0.0, max_value=1.0)
        def set_satisfaction(self, satisfaction: float):
            self.satisfaction = satisfaction
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # 从kwargs中获取参数值
            param_value = kwargs.get(param_name)

            # 检查None
            if param_value is None:
                if not allow_none:
                    raise ValidationError(
                        f"参数 '{param_name}' 不能为None"
                    )
                return func(*args, **kwargs)

            # 检查范围
            if min_value is not None and param_value < min_value:
                raise ValidationError(
                    f"参数 '{param_name}' 必须 >= {min_value}, 实际值: {param_value}"
                )

            if max_value is not None and param_value > max_value:
                raise ValidationError(
                    f"参数 '{param_name}' 必须 <= {max_value}, 实际值: {param_value}"
                )

            return func(*args, **kwargs)
        return wrapper
    return decorator


def validate_type(
    param_name: str,
    expected_type: type | tuple,
    allow_none: bool = False,
):
    """
    验证参数类型的装饰器

    Args:
        param_name: 参数名称
        expected_type: 期望的类型
        allow_none: 是否允许None值
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            param_value = kwargs.get(param_name)

            if param_value is None:
                if not allow_none:
                    raise ValidationError(
                        f"参数 '{param_name}' 不能为None"
                    )
                return func(*args, **kwargs)

            if not isinstance(param_value, expected_type):
                type_name = (
                    expected_type.__name__ if isinstance(expected_type, type)
                    else "或".join(t.__name__ for t in expected_type)
                )
                raise ValidationError(
                    f"参数 '{param_name}' 必须是 {type_name} 类型，"
                    f"实际类型: {type(param_value).__name__}"
                )

            return func(*args, **kwargs)
        return wrapper
    return decorator


def validate_non_empty(param_name: str, allow_none: bool = False):
    """
    验证参数非空的装饰器

    Args:
        param_name: 参数名称
        allow_none: 是否允许None值
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            param_value = kwargs.get(param_name)

            if param_value is None:
                if not allow_none:
                    raise ValidationError(
                        f"参数 '{param_name}' 不能为None"
                    )
                return func(*args, **kwargs)

            # 检查字符串、列表、字典是否为空
            if isinstance(param_value, (str, list, dict)):
                if len(param_value) == 0:
                    raise ValidationError(
                        f"参数 '{param_name}' 不能为空"
                    )

            return func(*args, **kwargs)
        return wrapper
    return decorator


def validate_in_choices(
    param_name: str,
    choices: list[Any],
    allow_none: bool = False,
):
    """
    验证参数在允许的选项中的装饰器

    Args:
        param_name: 参数名称
        choices: 允许的选项列表
        allow_none: 是否允许None值
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            param_value = kwargs.get(param_name)

            if param_value is None:
                if not allow_none:
                    raise ValidationError(
                        f"参数 '{param_name}' 不能为None"
                    )
                return func(*args, **kwargs)

            if param_value not in choices:
                raise ValidationError(
                    f"参数 '{param_name}' 必须是 {choices} 之一，"
                    f"实际值: {param_value}"
                )

            return func(*args, **kwargs)
        return wrapper
    return decorator


# =============================================================================
# 验证工具函数
# =============================================================================

def validate_satisfaction(satisfaction: float | None) -> float:
    """
    验证用户满意度参数

    Args:
        satisfaction: 用户满意度 (0-1)

    Returns:
        验证后的满意度值

    Raises:
        ValidationError: 如果验证失败
    """
    if satisfaction is None:
        return 0.5  # 默认中性值

    if not isinstance(satisfaction, (int, float)):
        raise ValidationError(
            f"satisfaction 必须是数字类型，实际类型: {type(satisfaction).__name__}"
        )

    if not 0.0 <= satisfaction <= 1.0:
        raise ValidationError(
            f"satisfaction 必须在 [0.0, 1.0] 范围内，实际值: {satisfaction}"
        )

    return float(satisfaction)


def validate_confidence(confidence: float) -> float:
    """
    验证置信度参数

    Args:
        confidence: 置信度 (0-1)

    Returns:
        验证后的置信度值

    Raises:
        ValidationError: 如果验证失败
    """
    if not isinstance(confidence, (int, float)):
        raise ValidationError(
            f"confidence 必须是数字类型，实际类型: {type(confidence).__name__}"
        )

    if not 0.0 <= confidence <= 1.0:
        raise ValidationError(
            f"confidence 必须在 [0.0, 1.0] 范围内，实际值: {confidence}"
        )

    return float(confidence)


def validate_options(options: list[Any]) -> list[Any]:
    """
    验证选项列表

    Args:
        options: 选项列表

    Returns:
        验证后的选项列表

    Raises:
        ValidationError: 如果验证失败
    """
    if not isinstance(options, list):
        raise ValidationError(
            f"options 必须是列表类型，实际类型: {type(options).__name__}"
        )

    if len(options) == 0:
        raise ValidationError(
            "options 列表不能为空"
        )

    return options


def validate_context(context: Any) -> dict:
    """
    验证上下文参数

    Args:
        context: 上下文对象

    Returns:
        验证后的上下文字典

    Raises:
        ValidationError: 如果验证失败
    """
    if context is None:
        return {}

    if not isinstance(context, dict):
        raise ValidationError(
            f"context 必须是字典类型，实际类型: {type(context).__name__}"
        )

    return context


# =============================================================================
# 批量验证装饰器
# =============================================================================

def validate_learning_experience(
    satisfaction_required: bool = False,
    confidence_required: bool = True,
):
    """
    学习经验验证装饰器

    Args:
        satisfaction_required: 是否要求满意度参数
        confidence_required: 是否要求置信度参数
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(
            self,
            context: Any,
            action: str,
            result: dict,
            success: bool = True,
            confidence: float = 0.0,
            execution_time_ms: float = 0.0,
            true_action: str | None = None,
            user_satisfaction: float | None = None,
            **kwargs
        ):
            # 验证context
            context = validate_context(context)

            # 验证action
            if not isinstance(action, str):
                raise ValidationError(
                    "action 必须是字符串类型"
                )

            # 验证result
            if not isinstance(result, dict):
                raise ValidationError(
                    "result 必须是字典类型"
                )

            # 验证success
            if not isinstance(success, bool):
                raise ValidationError(
                    "success 必须是布尔类型"
                )

            # 验证confidence
            if confidence_required:
                confidence = validate_confidence(confidence)

            # 验证execution_time_ms
            if not isinstance(execution_time_ms, (int, float)) or execution_time_ms < 0:
                raise ValidationError(
                    f"execution_time_ms 必须是非负数，实际值: {execution_time_ms}"
                )

            # 验证user_satisfaction
            if satisfaction_required and user_satisfaction is not None:
                user_satisfaction = validate_satisfaction(user_satisfaction)

            # 调用原函数
            return func(
                self,
                context=context,
                action=action,
                result=result,
                success=success,
                confidence=confidence,
                execution_time_ms=execution_time_ms,
                true_action=true_action,
                user_satisfaction=user_satisfaction,
                **kwargs
            )
        return wrapper
    return decorator


# =============================================================================
# 测试代码
# =============================================================================
if __name__ == "__main__":
    print("=" * 80)
    print("🧪 测试参数验证工具")
    print("=" * 80)

    # 测试validate_satisfaction
    print("\n✅ 测试validate_satisfaction:")
    try:
        assert validate_satisfaction(0.5) == 0.5
        assert validate_satisfaction(None) == 0.5
        print("   正常值: 通过")

        try:
            validate_satisfaction(1.5)
        except ValidationError as e:
            print(f"   超范围: {e}")
    except Exception as e:
        print(f"   ❌ 意外错误: {e}")

    # 测试validate_confidence
    print("\n✅ 测试validate_confidence:")
    try:
        assert validate_confidence(0.9) == 0.9
        print("   正常值: 通过")

        try:
            validate_confidence(-0.1)
        except ValidationError as e:
            print(f"   负数: {e}")
    except Exception as e:
        print(f"   ❌ 意外错误: {e}")

    # 测试装饰器
    print("\n✅ 测试装饰器:")

    @validate_range("value", min_value=0, max_value=100)
    def test_range(value: int):
        return value

    try:
        assert test_range(value=50) == 50
        print("   范围装饰器: 正常值通过")

        try:
            test_range(value=150)
        except ValidationError as e:
            print(f"   范围装饰器: 超范围 {e}")
    except Exception as e:
        print(f"   ❌ 意外错误: {e}")

    print("\n" + "=" * 80)
    print("✅ 参数验证工具测试完成!")
    print("=" * 80)
