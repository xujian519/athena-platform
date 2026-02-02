"""
参数验证和收集模块

提供对话式参数收集功能,解决参数填充有效性问题。

主要组件:
- ParameterValidator: 参数验证器
- ConversationalCollector: 对话式参数收集器
"""

from .parameter_validator import (
    ParameterDefinition,
    ParameterValidator,
    ParamRequirement,
    ValidationResult,
)

__all__ = [
    "CollectionContext",
    "CollectionState",
    "ConversationalCollector",
    "ParamRequirement",
    "ParameterDefinition",
    "ParameterValidator",
    "ValidationResult",
]
