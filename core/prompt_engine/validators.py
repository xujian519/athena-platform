"""提示词变量校验器。"""

import re
from dataclasses import dataclass, field
from typing import Any

from .schema import PromptSchema, VariableSpec, VariableType


@dataclass
class ValidationResult:
    valid: bool
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


class VariableValidator:
    """基于 PromptSchema 的变量校验器。"""

    def validate(self, schema: PromptSchema, variables: dict) -> ValidationResult:
        errors: list[str] = []
        warnings: list[str] = []

        for spec in schema.variables:
            value = variables.get(spec.name)

            # required 检查
            if spec.required and (value is None or value == ""):
                errors.append(f"Missing required variable: {spec.name}")
                continue

            if value is None:
                continue

            # 类型检查
            type_ok, type_msg = self._check_type(value, spec.type)
            if not type_ok:
                errors.append(f"Variable {spec.name}: {type_msg}")

            # max_length 检查
            if spec.max_length is not None and len(str(value)) > spec.max_length:
                errors.append(
                    f"Variable {spec.name} exceeds max_length {spec.max_length}"
                )

            # 正则检查
            if spec.pattern is not None:
                if not re.match(spec.pattern, str(value)):
                    errors.append(
                        f"Variable {spec.name} does not match pattern {spec.pattern}"
                    )

            # 枚举检查
            if spec.enum is not None:
                if str(value) not in spec.enum:
                    errors.append(
                        f"Variable {spec.name} must be one of {spec.enum}"
                    )

        # 检查是否有未声明的变量（warning 不阻断）
        declared = {v.name for v in schema.variables}
        for key in variables:
            if key not in declared and not key.startswith("__"):
                warnings.append(f"Undeclared variable: {key}")

        return ValidationResult(valid=len(errors) == 0, errors=errors, warnings=warnings)

    def _check_type(self, value: Any, expected: VariableType) -> tuple[bool, str]:
        if expected == VariableType.STRING:
            return True, ""  # 任何值都可转为字符串
        if expected == VariableType.INT:
            if isinstance(value, int) and not isinstance(value, bool):
                return True, ""
            try:
                int(value)
                return True, ""
            except (ValueError, TypeError):
                return False, f"expected int, got {type(value).__name__}"
        if expected == VariableType.FLOAT:
            if isinstance(value, (int, float)) and not isinstance(value, bool):
                return True, ""
            try:
                float(value)
                return True, ""
            except (ValueError, TypeError):
                return False, f"expected float, got {type(value).__name__}"
        if expected == VariableType.BOOL:
            if isinstance(value, bool):
                return True, ""
            if isinstance(value, str) and value.lower() in ("true", "false", "1", "0"):
                return True, ""
            return False, f"expected bool, got {type(value).__name__}"
        if expected == VariableType.LIST:
            if isinstance(value, list):
                return True, ""
            return False, f"expected list, got {type(value).__name__}"
        if expected == VariableType.DICT:
            if isinstance(value, dict):
                return True, ""
            return False, f"expected dict, got {type(value).__name__}"
        return True, ""
