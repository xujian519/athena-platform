"""提示词模板变量 Schema 定义。"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, List, Optional


class VariableType(str, Enum):
    STRING = "string"
    INT = "int"
    FLOAT = "float"
    BOOL = "bool"
    LIST = "list"
    DICT = "dict"


@dataclass
class VariableSpec:
    """单个变量的规范定义。"""

    name: str
    type: VariableType = VariableType.STRING
    required: bool = True
    source: str = ""  # user_input | document | extracted | system
    default: Any = None
    description: str = ""
    max_length: Optional[int] = None
    pattern: Optional[str] = None  # 正则校验（可选）
    enum: Optional[List[str]] = None  # 枚举值（可选）


@dataclass
class PromptSchema:
    """提示词模板的完整 Schema。

    Attributes:
        rule_id: 提示词唯一标识（与 inventory ID 对应）
        template_version: 模板版本号（语义化版本，如 "1.0.0"）
        variables: 变量规范列表
    """

    rule_id: str
    template_version: str
    variables: List[VariableSpec] = field(default_factory=list)

    @property
    def version(self) -> str:
        """语义化版本号，与 template_version 保持一致。"""
        return self.template_version

    def get_required_vars(self) -> List[str]:
        return [v.name for v in self.variables if v.required]

    def get_optional_vars(self) -> List[str]:
        return [v.name for v in self.variables if not v.required]

    def get_spec(self, name: str) -> Optional[VariableSpec]:
        for v in self.variables:
            if v.name == name:
                return v
        return None

    def is_compatible_with(self, target_version: str) -> bool:
        """检查当前版本是否与目标版本向后兼容。

        向后兼容原则（语义化版本）：
        - 主版本号（MAJOR）必须相同
        - 当前次版本号（MINOR） >= 目标次版本号
        - 修订号（PATCH）不参与兼容性判断
        """
        try:
            c_major, c_minor, _ = map(int, self.template_version.split("."))
            t_major, t_minor, _ = map(int, target_version.split("."))
        except ValueError:
            return self.template_version == target_version
        if c_major != t_major:
            return False
        if c_minor < t_minor:
            return False
        return True

    def upgrade_variables(self, variables: dict) -> dict:
        """根据 Schema 定义升级/规范化变量字典。

        - 填充默认值（对可选变量）
        - 保留已传入的值
        """
        upgraded = dict(variables)
        for spec in self.variables:
            if spec.name not in upgraded and spec.default is not None:
                upgraded[spec.name] = spec.default
        return upgraded
