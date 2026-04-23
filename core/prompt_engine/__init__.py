"""
Prompt Engineering 核心模块

提供：
- PromptRenderer: Jinja2 模板渲染
- VariableValidator: 变量校验
- PromptSanitizer: 注入清洗
- PromptSchema / VariableSpec: 模板协议定义
"""

from .renderer import PromptRenderer
from .sanitizer import InjectionRisk, PromptSanitizer, RiskLevel
from .schema import PromptSchema, VariableSpec, VariableType
from .validators import ValidationResult, VariableValidator

__all__ = [
    "InjectionRisk",
    "PromptRenderer",
    "PromptSanitizer",
    "PromptSchema",
    "RiskLevel",
    "ValidationResult",
    "VariableSpec",
    "VariableType",
    "VariableValidator",
]
