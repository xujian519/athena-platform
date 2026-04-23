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
    """提示词模板的完整 Schema。"""

    rule_id: str
    template_version: str
    variables: List[VariableSpec] = field(default_factory=list)

    def get_required_vars(self) -> List[str]:
        return [v.name for v in self.variables if v.required]

    def get_optional_vars(self) -> List[str]:
        return [v.name for v in self.variables if not v.required]

    def get_spec(self, name: str) -> Optional[VariableSpec]:
        for v in self.variables:
            if v.name == name:
                return v
        return None
