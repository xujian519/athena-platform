#!/usr/bin/env python3
"""
学习引擎输入验证器
Learning Engine Input Validator

提供全面的输入验证功能，确保数据安全性和完整性。

作者: Athena平台团队
版本: 1.0.0
创建时间: 2026-01-28
"""

import logging
from dataclasses import dataclass
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class ValidationSeverity(str, Enum):
    """验证严重程度"""

    WARNING = "warning"  # 警告：允许但需要记录
    ERROR = "error"  # 错误：拒绝请求


@dataclass
class ValidationResult:
    """验证结果"""

    is_valid: bool
    errors: list[str]
    warnings: list[str]
    severity: ValidationSeverity

    def add_error(self, message: str) -> None:
        """添加错误"""
        self.errors.append(message)
        self.is_valid = False
        if self.severity != ValidationSeverity.ERROR:
            self.severity = ValidationSeverity.ERROR

    def add_warning(self, message: str) -> None:
        """添加警告"""
        self.warnings.append(message)
        if self.severity != ValidationSeverity.ERROR:
            self.severity = ValidationSeverity.WARNING


class InputValidator:
    """
    输入验证器

    提供全面的输入验证功能。
    """

    # 默认配置
    MAX_DATA_SIZE = 10 * 1024 * 1024  # 10MB
    MAX_STRING_LENGTH = 10000  # 10000字符
    MAX_DICT_DEPTH = 10  # 最大字典嵌套深度
    MAX_LIST_LENGTH = 1000  # 最大列表长度

    def __init__(
        self,
        max_data_size: int = MAX_DATA_SIZE,
        max_string_length: int = MAX_STRING_LENGTH,
        max_dict_depth: int = MAX_DICT_DEPTH,
        max_list_length: int = MAX_LIST_LENGTH,
    ):
        self.max_data_size = max_data_size
        self.max_string_length = max_string_length
        self.max_dict_depth = max_dict_depth
        self.max_list_length = max_list_length

    async def validate_context(self, context: dict[str, Any]) -> ValidationResult:
        """
        验证上下文数据

        Args:
            context: 上下文字典

        Returns:
            验证结果
        """
        result = ValidationResult(is_valid=True, errors=[], warnings=[], severity=ValidationSeverity.WARNING)

        # 检查类型
        if not isinstance(context, dict):
            result.add_error(f"上下文必须是字典类型，实际类型: {type(context).__name__}")
            return result

        # 检查大小
        try:
            data_size = len(str(context))
            if data_size > self.max_data_size:
                result.add_error(
                    f"上下文数据过大: {data_size}字节，最大允许: {self.max_data_size}字节"
                )
        except Exception as e:
            result.add_error(f"无法计算上下文大小: {e}")
            return result

        # 检查嵌套深度
        depth = self._calculate_depth(context)
        if depth > self.max_dict_depth:
            result.add_warning(
                f"上下文嵌套深度过大: {depth}，建议: {self.max_dict_depth}"
            )

        # 检查字符串长度
        self._validate_string_lengths(context, result)

        # 检查列表长度
        self._validate_list_lengths(context, result)

        return result

    async def validate_experience_data(self, data: dict[str, Any]) -> ValidationResult:
        """
        验证经验数据

        Args:
            data: 经验数据字典

        Returns:
            验证结果
        """
        result = ValidationResult(is_valid=True, errors=[], warnings=[], severity=ValidationSeverity.WARNING)

        # 检查类型
        if not isinstance(data, dict):
            result.add_error(f"经验数据必须是字典类型，实际类型: {type(data).__name__}")
            return result

        # 检查必需字段
        required_fields = ["type", "context", "content", "outcome"]
        missing_fields = [f for f in required_fields if f not in data]
        if missing_fields:
            result.add_error(f"缺少必需字段: {missing_fields}")

        # 验证嵌套字段
        if "context" in data:
            context_result = await self.validate_context(data["context"])
            result.errors.extend(context_result.errors)
            result.warnings.extend(context_result.warnings)
            if not context_result.is_valid:
                result.is_valid = False

        # 检查数据大小
        try:
            data_size = len(str(data))
            if data_size > self.max_data_size:
                result.add_error(
                    f"经验数据过大: {data_size}字节，最大允许: {self.max_data_size}字节"
                )
        except Exception as e:
            result.add_warning(f"无法计算经验数据大小: {e}")

        return result

    async def validate_action(self, action: str) -> ValidationResult:
        """
        验证操作字符串

        Args:
            action: 操作字符串

        Returns:
            验证结果
        """
        result = ValidationResult(is_valid=True, errors=[], warnings=[], severity=ValidationSeverity.WARNING)

        # 检查类型
        if not isinstance(action, str):
            result.add_error(f"操作必须是字符串类型，实际类型: {type(action).__name__}")
            return result

        # 检查长度
        if len(action) > self.max_string_length:
            result.add_error(
                f"操作字符串过长: {len(action)}字符，最大允许: {self.max_string_length}字符"
            )

        # 检查是否为空
        if not action.strip():
            result.add_error("操作字符串不能为空")

        # 检查是否包含危险字符
        dangerous_chars = ["\x00", "\r"]
        if any(char in action for char in dangerous_chars):
            result.add_warning("操作字符串包含潜在危险字符")

        return result

    async def validate_result(self, result: Any) -> ValidationResult:
        """
        验证结果数据

        Args:
            result: 结果数据

        Returns:
            验证结果
        """
        validation_result = ValidationResult(is_valid=True, errors=[], warnings=[], severity=ValidationSeverity.WARNING)

        # 检查是否为None
        if result is None:
            validation_result.add_warning("结果为None")
            return validation_result

        # 如果是字典，验证其内容
        if isinstance(result, dict):
            # 检查大小
            try:
                data_size = len(str(result))
                if data_size > self.max_data_size:
                    validation_result.add_error(
                        f"结果数据过大: {data_size}字节，最大允许: {self.max_data_size}字节"
                    )
            except Exception as e:
                validation_result.add_warning(f"无法计算结果大小: {e}")

        return validation_result

    async def validate_reward(self, reward: float) -> ValidationResult:
        """
        验证奖励值

        Args:
            reward: 奖励值

        Returns:
            验证结果
        """
        result = ValidationResult(is_valid=True, errors=[], warnings=[], severity=ValidationSeverity.WARNING)

        # 检查类型
        if not isinstance(reward, (int, float)):
            result.add_error(f"奖励值必须是数值类型，实际类型: {type(reward).__name__}")
            return result

        # 检查范围
        if reward < -100 or reward > 100:
            result.add_warning(f"奖励值异常: {reward}，正常范围: [-100, 100]")

        # 检查是否为NaN或无穷
        if reward != reward:  # NaN检查
            result.add_error("奖励值不能为NaN")
        elif abs(reward) == float("inf"):
            result.add_error("奖励值不能为无穷")

        return result

    async def validate_learning_input(
        self,
        context: dict[str, Any] | None,
        action: str | None,
        result: Any | None,
        reward: float | None = None,
    ) -> ValidationResult:
        """
        综合验证学习输入

        Args:
            context: 上下文
            action: 操作
            result: 结果
            reward: 奖励值

        Returns:
            综合验证结果
        """
        final_result = ValidationResult(is_valid=True, errors=[], warnings=[], severity=ValidationSeverity.WARNING)

        # 验证上下文
        if context is not None:
            context_result = await self.validate_context(context)
            final_result.errors.extend(context_result.errors)
            final_result.warnings.extend(context_result.warnings)
            if not context_result.is_valid:
                final_result.is_valid = False

        # 验证操作
        if action is not None:
            action_result = await self.validate_action(action)
            final_result.errors.extend(action_result.errors)
            final_result.warnings.extend(action_result.warnings)
            if not action_result.is_valid:
                final_result.is_valid = False

        # 验证结果
        if result is not None:
            result_validation = await self.validate_result(result)
            final_result.errors.extend(result_validation.errors)
            final_result.warnings.extend(result_validation.warnings)
            if not result_validation.is_valid:
                final_result.is_valid = False

        # 验证奖励
        if reward is not None:
            reward_result = await self.validate_reward(reward)
            final_result.errors.extend(reward_result.errors)
            final_result.warnings.extend(reward_result.warnings)
            if not reward_result.is_valid:
                final_result.is_valid = False

        return final_result

    def _calculate_depth(self, obj: Any, current_depth: int = 0) -> int:
        """计算嵌套深度"""
        if not isinstance(obj, dict) or not obj:
            return current_depth

        max_depth = current_depth
        for value in obj.values():
            if isinstance(value, dict):
                depth = self._calculate_depth(value, current_depth + 1)
                max_depth = max(max_depth, depth)
            elif isinstance(value, list):
                for item in value:
                    if isinstance(item, dict):
                        depth = self._calculate_depth(item, current_depth + 1)
                        max_depth = max(max_depth, depth)

        return max_depth

    def _validate_string_lengths(self, obj: Any, result: ValidationResult) -> None:
        """验证字符串长度"""
        if isinstance(obj, str):
            if len(obj) > self.max_string_length:
                result.add_warning(
                    f"字符串过长: {len(obj)}字符，最大允许: {self.max_string_length}字符"
                )
        elif isinstance(obj, dict):
            for value in obj.values():
                self._validate_string_lengths(value, result)
        elif isinstance(obj, list):
            for item in obj:
                self._validate_string_lengths(item, result)

    def _validate_list_lengths(self, obj: Any, result: ValidationResult) -> None:
        """验证列表长度"""
        if isinstance(obj, list):
            if len(obj) > self.max_list_length:
                result.add_warning(
                    f"列表过长: {len(obj)}元素，最大允许: {self.max_list_length}元素"
                )
            for item in obj:
                self._validate_list_lengths(item, result)
        elif isinstance(obj, dict):
            for value in obj.values():
                self._validate_list_lengths(value, result)


# 全局验证器实例
_global_validator: InputValidator | None = None


def get_input_validator() -> InputValidator:
    """获取全局输入验证器"""
    global _global_validator
    if _global_validator is None:
        _global_validator = InputValidator()
    return _global_validator


__all__ = [
    "ValidationSeverity",
    "ValidationResult",
    "InputValidator",
    "get_input_validator",
]
