#!/usr/bin/env python3
"""
统一参数验证框架
Unified Parameter Validation Framework

为所有智能体提供统一的参数验证能力:
1. 参数完整性检查
2. 参数类型验证
3. 参数值范围验证
4. 参数依赖关系验证
5. 参数自动纠错
6. 验证规则引擎

作者: Athena平台团队
创建时间: 2025-12-26
版本: v1.0.0 "统一验证"
"""

import logging
import re
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple, Union

logger = logging.getLogger(__name__)


class ValidationSeverity(Enum):
    """验证严重程度"""

    INFO = "info"  # 信息
    WARNING = "warning"  # 警告
    ERROR = "error"  # 错误
    CRITICAL = "critical"  # 严重


class ParameterType(Enum):
    """参数类型"""

    STRING = "string"
    INTEGER = "integer"
    FLOAT = "float"
    BOOLEAN = "boolean"
    LIST = "list"
    DICT = "dict"
    DATE = "date"
    DATETIME = "datetime"
    EMAIL = "email"
    URL = "url"
    PHONE = "phone"
    FILE_PATH = "file_path"
    JSON = "json"


@dataclass
class ValidationRule:
    """验证规则"""

    name: str
    type_check: ParameterType | None = None
    required: bool = False
    default: Any = None
    min_value: int | float | None = None
    max_value: int | float | None = None
    min_length: int | None = None
    max_length: int | None = None
    pattern: str | None = None
    allowed_values: list["key"] = None
    custom_validator: Callable[[Any, tuple[bool, str]]] | None = None
    depends_on: list["key"] = None


@dataclass
class ValidationResult:
    """验证结果"""

    is_valid: bool
    parameter_name: str
    parameter_value: Any
    severity: ValidationSeverity
    message: str
    suggestions: list[str] = field(default_factory=list)
    corrected_value: Any = None
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class ParameterSchema:
    """参数模式"""

    parameter_name: str
    rules: list[ValidationRule]
    description: str = ""


class UnifiedParameterValidator:
    """
    统一参数验证器

    核心功能:
    1. 多类型参数验证
    2. 复杂规则支持
    3. 依赖关系检查
    4. 自动纠错
    5. 详细错误提示
    """

    def __init__(self):
        # 参数模式库
        self.schemas: dict[str, ParameterSchema] = {}

        # 工具参数规范
        self.tool_parameters: dict[str, dict[str, ParameterSchema]] = {}

        # 验证统计
        self.metrics = {
            "total_validations": 0,
            "valid_count": 0,
            "invalid_count": 0,
            "corrected_count": 0,
        }

        logger.info("✅ 统一参数验证框架初始化完成")

    def register_parameter_schema(
        self,
        schema_id: str,
        parameter_name: str,
        rules: list[ValidationRule],
        description: str = "",
    ):
        """注册参数模式"""
        schema = ParameterSchema(
            parameter_name=parameter_name, rules=rules, description=description
        )

        if schema_id not in self.schemas:
            self.schemas[schema_id] = {}

        self.schemas[schema_id][parameter_name] = schema

        logger.debug(f"📝 参数模式已注册: {schema_id}.{parameter_name}")

    def register_tool_parameters(self, tool_id: str, parameters: dict[str, ParameterSchema]):
        """注册工具参数规范"""
        self.tool_parameters[tool_id] = parameters
        logger.info(f"🔧 工具参数已注册: {tool_id} ({len(parameters)} 个参数)")

    async def validate_parameter(
        self,
        parameter_name: str,
        parameter_value: Any,
        rules: list[ValidationRule],
        context: dict[str, Any] | None = None,
    ) -> ValidationResult:
        """
        验证单个参数

        Args:
            parameter_name: 参数名
            parameter_value: 参数值
            rules: 验证规则列表
            context: 上下文(用于依赖检查)

        Returns:
            ValidationResult: 验证结果
        """
        context = context or {}
        results = []
        corrected_value = parameter_value
        severity = ValidationSeverity.INFO

        for rule in rules:
            # 1. 必填检查
            if rule.required and parameter_value is None:
                if rule.default is not None:
                    corrected_value = rule.default
                    results.append((ValidationSeverity.WARNING, f"使用默认值: {rule.default}"))
                    self.metrics["corrected_count"] += 1
                else:
                    results.append((ValidationSeverity.ERROR, "参数为必填项"))
                    severity = max(severity, ValidationSeverity.ERROR, key=lambda x: x.value)
                    continue

            # 如果参数值为None且非必填,跳过其他检查
            if parameter_value is None:
                continue

            # 2. 类型检查
            if rule.type_check:
                type_result = await self._validate_type(parameter_value, rule.type_check)
                if not type_result[0]:
                    results.append((ValidationSeverity.ERROR, type_result[1]))
                    severity = max(severity, ValidationSeverity.ERROR, key=lambda x: x.value)
                    continue

            # 3. 范围检查
            if rule.min_value is not None or rule.max_value is not None:
                range_result = await self._validate_range(
                    parameter_value, rule.min_value, rule.max_value
                )
                if not range_result[0]:
                    results.append((ValidationSeverity.WARNING, range_result[1]))
                    severity = max(severity, ValidationSeverity.WARNING, key=lambda x: x.value)

            # 4. 长度检查
            if rule.min_length is not None or rule.max_length is not None:
                length_result = await self._validate_length(
                    parameter_value, rule.min_length, rule.max_length
                )
                if not length_result[0]:
                    results.append((ValidationSeverity.WARNING, length_result[1]))
                    severity = max(severity, ValidationSeverity.WARNING, key=lambda x: x.value)

            # 5. 模式检查
            if rule.pattern:
                pattern_result = await self._validate_pattern(parameter_value, rule.pattern)
                if not pattern_result[0]:
                    results.append((ValidationSeverity.ERROR, pattern_result[1]))
                    severity = max(severity, ValidationSeverity.ERROR, key=lambda x: x.value)

            # 6. 允许值检查
            if rule.allowed_values:
                allowed_result = await self._validate_allowed_values(
                    parameter_value, rule.allowed_values
                )
                if not allowed_result[0]:
                    results.append((ValidationSeverity.ERROR, f"允许的值: {rule.allowed_values}"))
                    severity = max(severity, ValidationSeverity.ERROR, key=lambda x: x.value)

            # 7. 自定义验证器
            if rule.custom_validator:
                custom_result = rule.custom_validator(parameter_value)
                if not custom_result[0]:
                    results.append((ValidationSeverity.ERROR, custom_result[1]))
                    severity = max(severity, ValidationSeverity.ERROR, key=lambda x: x.value)

            # 8. 依赖检查
            if rule.depends_on:
                dep_result = await self._validate_dependencies(
                    parameter_name, rule.depends_on, context
                )
                if not dep_result[0]:
                    results.append((ValidationSeverity.WARNING, dep_result[1]))
                    severity = max(severity, ValidationSeverity.WARNING, key=lambda x: x.value)

        # 更新统计
        self.metrics["total_validations"] += 1
        if severity in [ValidationSeverity.ERROR, ValidationSeverity.CRITICAL]:
            self.metrics["invalid_count"] += 1
        else:
            self.metrics["valid_count"] += 1

        # 生成验证结果
        is_valid = severity not in [ValidationSeverity.ERROR, ValidationSeverity.CRITICAL]
        message = "; ".join(r[1] for r in results) if results else "验证通过"

        return ValidationResult(
            is_valid=is_valid,
            parameter_name=parameter_name,
            parameter_value=parameter_value,
            severity=severity,
            message=message,
            corrected_value=corrected_value if corrected_value != parameter_value else None,
        )

    async def validate_parameters(
        self, tool_id: str, parameters: dict[str, Any]
    ) -> tuple[bool, list[ValidationResult]]:
        """
        验证工具的所有参数

        Args:
            tool_id: 工具ID
            parameters: 参数字典

        Returns:
            tuple[是否全部通过, 验证结果列表]
        """
        tool_schema = self.tool_parameters.get(tool_id)

        if not tool_schema:
            logger.warning(f"⚠️ 工具参数规范不存在: {tool_id}")
            return True, []  # 没有规范时跳过验证

        results = []
        all_valid = True

        # 检查必填参数
        for param_name, param_schema in tool_schema.items():
            param_value = parameters.get(param_name)

            result = await self.validate_parameter(
                param_name, param_value, param_schema.rules, context=parameters
            )

            results.append(result)

            if not result.is_valid:
                all_valid = False

        # 检查未知参数
        for param_name in parameters:
            if param_name not in tool_schema:
                results.append(
                    ValidationResult(
                        is_valid=True,
                        parameter_name=param_name,
                        parameter_value=parameters[param_name],
                        severity=ValidationSeverity.INFO,
                        message="未知参数,可能已忽略",
                    )
                )

        return all_valid, results

    async def pre_execution_check(
        self, tool_id: str, parameters: dict[str, Any]
    ) -> tuple[bool, str | None, dict[str, Any]:
        """
        执行前完整性检查

        Returns:
            tuple[是否可以执行, 错误信息, 纠正后的参数]
        """
        # 1. 参数验证
        all_valid, results = await self.validate_parameters(tool_id, parameters)

        if not all_valid:
            errors = [r.message for r in results if not r.is_valid]
            return False, "; ".join(errors), parameters

        # 2. 应用纠正值
        corrected_params = parameters.copy()
        for result in results:
            if result.corrected_value is not None:
                corrected_params[result.parameter_name] = result.corrected_value

        # 3. 检查工具可用性(简化实现)
        # 实际应该检查工具服务状态
        tool_available = True

        if not tool_available:
            return False, f"工具 {tool_id} 当前不可用", parameters

        return True, None, corrected_params

    async def _validate_type(
        self, value: Any, expected_type: ParameterType
    ) -> tuple[bool, str | None]:
        """验证参数类型"""
        if expected_type == ParameterType.STRING:
            if not isinstance(value, str):
                try:
                    str(value)
                    return True, None
                except Exception as e:
                    logger.debug(f"空except块已触发: {e}")
                    return False, f"期望字符串类型,实际: {type(value).__name__}"
            return True, None

        elif expected_type == ParameterType.INTEGER:
            if isinstance(value, int):
                return True, None
            if isinstance(value, float) and value.is_integer():
                return True, None
            return False, f"期望整数类型,实际: {type(value).__name__}"

        elif expected_type == ParameterType.FLOAT:
            if isinstance(value, (int, float)):
                return True, None
            return False, f"期望浮点数类型,实际: {type(value).__name__}"

        elif expected_type == ParameterType.BOOLEAN:
            if isinstance(value, bool):
                return True, None
            return False, f"期望布尔类型,实际: {type(value).__name__}"

        elif expected_type == ParameterType.LIST:
            if isinstance(value, list):
                return True, None
            return False, f"期望列表类型,实际: {type(value).__name__}"

        elif expected_type == ParameterType.DICT:
            if isinstance(value, dict):
                return True, None
            return False, f"期望字典类型,实际: {type(value).__name__}"

        elif expected_type == ParameterType.EMAIL:
            pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
            if re.match(pattern, str(value)):
                return True, None
            return False, "邮箱格式不正确"

        elif expected_type == ParameterType.URL:
            pattern = r"^https?://[^\s/$.?#].[^\s]*$"
            if re.match(pattern, str(value)):
                return True, None
            return False, "URL格式不正确"

        elif expected_type == ParameterType.PHONE:
            pattern = r"^1[3-9]\d{9}$"
            if re.match(pattern, str(value)):
                return True, None
            return False, "手机号格式不正确"

        return False, f"未实现的类型检查: {expected_type}"

    async def _validate_range(
        self,
        value: Any,
        min_value: int | Optional[float],
        max_value: int | Optional[float],
    ) -> tuple[bool, str | None]:
        """验证数值范围"""
        try:
            num_value = float(value)
        except (ValueError, TypeError):
            return False, "无法转换为数值"

        if min_value is not None and num_value < min_value:
            return False, f"值 {num_value} 小于最小值 {min_value}"

        if max_value is not None and num_value > max_value:
            return False, f"值 {num_value} 大于最大值 {max_value}"

        return True, None

    async def _validate_length(
        self, value: Any, min_length: int, max_length: int,
    ) -> tuple[bool, str | None]:
        """验证长度"""
        try:
            length = len(value)
        except TypeError:
            return False, "无法计算长度"

        if min_length is not None and length < min_length:
            return False, f"长度 {length} 小于最小长度 {min_length}"

        if max_length is not None and length > max_length:
            return False, f"长度 {length} 大于最大长度 {max_length}"

        return True, None

    async def _validate_pattern(self, value: Any, pattern: str) -> tuple[bool, str | None]:
        """验证正则模式"""
        if not isinstance(value, str):
            return False, "模式验证需要字符串类型"

        if re.match(pattern, value):
            return True, None

        return False, f"不匹配模式: {pattern}"

    async def _validate_allowed_values(
        self, value: Any, allowed_values: list[Any]
    ) -> tuple[bool, str | None]:
        """验证允许值"""
        if value in allowed_values:
            return True, None

        return False, f"值 {value} 不在允许列表中"

    async def _validate_dependencies(
        self, param_name: str, depends_on: list[str], context: dict[str, Any]
    ) -> tuple[bool, str | None]:
        """验证依赖关系"""
        for dep_param in depends_on:
            if dep_param not in context or context[dep_param] is None:
                return False, f"缺少依赖参数: {dep_param}"

        return True, None

    async def get_validator_metrics(self) -> dict[str, Any]:
        """获取验证器统计指标"""
        total = self.metrics["total_validations"]

        return {
            "total_validations": total,
            "valid_count": self.metrics["valid_count"],
            "invalid_count": self.metrics["invalid_count"],
            "corrected_count": self.metrics["corrected_count"],
            "valid_rate": self.metrics["valid_count"] / max(total, 1),
            "invalid_rate": self.metrics["invalid_count"] / max(total, 1),
            "correction_rate": self.metrics["corrected_count"] / max(total, 1),
        }


# 导出便捷函数
_validator: UnifiedParameterValidator | None = None


def get_parameter_validator() -> UnifiedParameterValidator:
    """获取参数验证器单例"""
    global _validator
    if _validator is None:
        _validator = UnifiedParameterValidator()
        _initialize_common_schemas(_validator)
    return _validator


def _initialize_common_schemas(validator: UnifiedParameterValidator) -> Any:
    """初始化通用参数模式"""

    # 文本参数
    validator.register_parameter_schema(
        "common",
        "text",
        rules=[
            ValidationRule(
                name="text_type", type_check=ParameterType.STRING, min_length=1, max_length=10000
            )
        ],
        description="通用文本参数",
    )

    # 整数参数
    validator.register_parameter_schema(
        "common",
        "integer",
        rules=[ValidationRule(name="integer_type", type_check=ParameterType.INTEGER)],
        description="通用整数参数",
    )

    # 布尔参数
    validator.register_parameter_schema(
        "common",
        "boolean",
        rules=[
            ValidationRule(name="boolean_type", type_check=ParameterType.BOOLEAN, default=False)
        ],
        description="通用布尔参数",
    )

    # 邮箱参数
    validator.register_parameter_schema(
        "common",
        "email",
        rules=[ValidationRule(name="email_type", type_check=ParameterType.EMAIL)],
        description="通用邮箱参数",
    )

    # URL参数
    validator.register_parameter_schema(
        "common",
        "url",
        rules=[ValidationRule(name="url_type", type_check=ParameterType.URL)],
        description="通用URL参数",
    )
