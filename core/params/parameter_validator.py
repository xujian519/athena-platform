"""
参数验证器

验证用户输入参数的完整性、类型和条件。
"""

import re
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional, Type


class ParamRequirement(Enum):
    """参数需求级别"""

    REQUIRED = "required"  # 必需参数
    OPTIONAL = "optional"  # 可选参数
    CONDITIONAL = "conditional"  # 条件参数


@dataclass
class ParameterDefinition:
    """参数定义"""

    name: str  # 参数名称
    requirement: ParamRequirement  # 需求级别
    param_type: type  # 参数类型
    description: str  # 参数描述
    default_value: Any = None  # 默认值
    validation_pattern: str | None = None  # 验证正则表达式
    validation_options: list[Any] | None = None  # 枚举选项
    depends_on: str | None = None  # 依赖的其他参数


@dataclass
class ValidationResult:
    """验证结果"""

    valid: bool  # 是否有效
    missing_params: list[str]  # 缺失的必需参数
    invalid_params: list[str]  # 无效的参数
    suggestions: dict[str, str]  # 参数建议
    confidence: float = 0.0  # 参数完整性评分 (0-1)


class ParameterValidator:
    """
    参数验证器

    根据意图类型验证参数的完整性、类型和条件。
    """

    # 各意图的参数定义
    INTENT_PARAMETERS = {
        # 小娜 - 专利相关
        "patent_analysis": [
            ParameterDefinition(
                "patent_number",
                ParamRequirement.REQUIRED,
                str,
                "专利申请号或公开号(例如: CN202310123456)",
                validation_pattern=r"^(CN)?\d{9,13}$",
            ),
            ParameterDefinition(
                "analysis_depth",
                ParamRequirement.OPTIONAL,
                str,
                "分析深度:basic(基础) 或 detailed(详细)",
                default_value="basic",
                validation_options=["basic", "detailed"],
            ),
        ],
        "patent_drafting": [
            ParameterDefinition("invention_title", ParamRequirement.REQUIRED, str, "发明名称"),
            ParameterDefinition("technical_field", ParamRequirement.REQUIRED, str, "技术领域"),
            ParameterDefinition("background_art", ParamRequirement.OPTIONAL, str, "背景技术"),
            ParameterDefinition("invention_content", ParamRequirement.OPTIONAL, str, "发明内容"),
            ParameterDefinition("brief_description", ParamRequirement.OPTIONAL, str, "附图说明"),
            ParameterDefinition(
                "detailed_description", ParamRequirement.OPTIONAL, str, "具体实施方式"
            ),
        ],
        "oa_response": [
            ParameterDefinition("oa_number", ParamRequirement.REQUIRED, str, "审查意见通知书编号"),
            ParameterDefinition(
                "rejection_reasons", ParamRequirement.REQUIRED, str, "驳回理由/审查意见"
            ),
            ParameterDefinition(
                "patent_number",
                ParamRequirement.REQUIRED,
                str,
                "专利申请号",
                validation_pattern=r"^(CN)?\d{9,13}$",
            ),
        ],
        "patent_search": [
            ParameterDefinition("keywords", ParamRequirement.REQUIRED, str, "检索关键词"),
            ParameterDefinition(
                "search_field", ParamRequirement.OPTIONAL, str, "检索领域", default_value="all"
            ),
            ParameterDefinition(
                "time_range", ParamRequirement.OPTIONAL, str, "时间范围", default_value="recent"
            ),
        ],
        # 小娜 - 法律相关
        "legal_consultation": [
            ParameterDefinition("question", ParamRequirement.REQUIRED, str, "法律问题描述"),
            ParameterDefinition(
                "legal_area",
                ParamRequirement.OPTIONAL,
                str,
                "法律领域(如:专利法、商标法、著作权法等)",
            ),
        ],
        "infringement_analysis": [
            ParameterDefinition("target_product", ParamRequirement.REQUIRED, str, "目标产品/技术"),
            ParameterDefinition(
                "patent_number",
                ParamRequirement.REQUIRED,
                str,
                "对比的专利号",
                validation_pattern=r"^(CN)?\d{9,13}$",
            ),
        ],
        # 通用
        "daily_chat": [
            # 日常对话不需要特定参数
        ],
        "coding_assistant": [
            ParameterDefinition("task", ParamRequirement.REQUIRED, str, "编程任务描述"),
            ParameterDefinition(
                "language", ParamRequirement.OPTIONAL, str, "编程语言", default_value="python"
            ),
            ParameterDefinition("code_context", ParamRequirement.OPTIONAL, str, "代码上下文"),
        ],
        "data_analyst": [
            ParameterDefinition("task", ParamRequirement.REQUIRED, str, "分析任务描述"),
            ParameterDefinition("data_source", ParamRequirement.OPTIONAL, str, "数据来源"),
        ],
    }

    def __init__(self):
        """初始化参数验证器"""
        self.intent_params = self.INTENT_PARAMETERS

    def validate(self, intent: str, params: dict[str, Any]) -> ValidationResult:
        """
        验证参数完整性

        Args:
            intent: 意图类型
            params: 用户提供的参数

        Returns:
            ValidationResult: 验证结果
        """
        param_defs = self.intent_params.get(intent, [])

        missing_params = []
        invalid_params = []
        suggestions = {}

        # 检查必需参数
        for param_def in param_defs:
            if param_def.requirement == ParamRequirement.REQUIRED:
                if param_def.name not in params or not params[param_def.name]:
                    missing_params.append(param_def.name)
                    suggestions[param_def.name] = (
                        f"请提供{param_def.description}。" f"示例:{param_def.name}='...'"
                    )

            # 检查参数类型和格式
            if param_def.name in params:
                value = params[param_def.name]

                # 类型检查
                if not isinstance(value, param_def.param_type):
                    try:
                        # 尝试类型转换
                        params[param_def.name] = param_def.param_type(value)
                    except (ValueError, TypeError):
                        invalid_params.append(param_def.name)
                        suggestions[param_def.name] = (
                            f"{param_def.name}应该是{param_def.param_type.__name__}类型"
                        )
                        continue

                # 格式验证(正则表达式)
                if param_def.validation_pattern:
                    if not re.match(param_def.validation_pattern, str(value)):
                        invalid_params.append(param_def.name)
                        suggestions[param_def.name] = (
                            f"{param_def.name}格式不正确。{param_def.description}"
                        )

                # 枚举选项验证
                if param_def.validation_options:
                    if value not in param_def.validation_options:
                        invalid_params.append(param_def.name)
                        suggestions[param_def.name] = (
                            f"{param_def.name}必须是以下之一: {', '.join(param_def.validation_options)}"
                        )

        # 计算完整性评分
        total_required = sum(1 for p in param_defs if p.requirement == ParamRequirement.REQUIRED)
        provided_required = total_required - len(missing_params)

        confidence = provided_required / total_required if total_required > 0 else 1.0

        return ValidationResult(
            valid=len(missing_params) == 0 and len(invalid_params) == 0,
            missing_params=missing_params,
            invalid_params=invalid_params,
            suggestions=suggestions,
            confidence=confidence,
        )

    def get_required_params(self, intent: str) -> list[ParameterDefinition]:
        """获取指定意图的必需参数列表"""
        param_defs = self.intent_params.get(intent, [])
        return [p for p in param_defs if p.requirement == ParamRequirement.REQUIRED]

    def get_param_description(self, intent: str, param_name: str) -> str | None:
        """获取参数的描述信息"""
        param_defs = self.intent_params.get(intent, [])
        for p in param_defs:
            if p.name == param_name:
                return p.description
        return None

    def suggest_next_question(self, intent: str, current_params: dict[str, Any]) -> str | None:
        """
        建议下一个收集参数的问题

        Args:
            intent: 意图类型
            current_params: 当前已收集的参数

        Returns:
            建议的问题文本,如果所有必需参数都已收集则返回None
        """
        param_defs = self.intent_params.get(intent, [])

        for param_def in param_defs:
            if param_def.requirement == ParamRequirement.REQUIRED:
                if param_def.name not in current_params:
                    return f"请提供{param_def.description}。"

        return None
