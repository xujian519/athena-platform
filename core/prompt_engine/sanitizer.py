"""提示词注入安全清洗器。"""

import re
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

from .schema import PromptSchema, VariableSpec


class RiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class InjectionRisk:
    level: RiskLevel
    pattern_matched: str
    recommendation: str


class PromptSanitizer:
    """用户输入清洗与 Prompt Injection 检测。"""

    # 常见 injection 模式（可扩展）
    INJECTION_PATTERNS: List[Tuple[str, RiskLevel]] = [
        (
            r"ignore\s+(all\s+)?(previous|above|prior)\s+(instructions?|prompts?|commands?)",
            RiskLevel.CRITICAL,
        ),
        (r"forget\s+(everything|all|your\s+instructions)", RiskLevel.CRITICAL),
        (r"you\s+are\s+now\s+.*?(ignore|disregard)", RiskLevel.HIGH),
        (r"system\s*[:\-]?\s*\n", RiskLevel.HIGH),
        (r"<\s*/?\s*system\s*>", RiskLevel.HIGH),
        (r"DAN|jailbreak|developer\s+mode", RiskLevel.MEDIUM),
    ]

    def sanitize_string(self, value: str, max_length: int = 10000) -> str:
        if not value:
            return ""
        # 截断
        if len(value) > max_length:
            value = value[:max_length]
        # 控制字符清洗（保留 \n \t \r）
        allowed = {"\n", "\t", "\r"}
        value = "".join(
            ch for ch in value if ch in allowed or (ch.isprintable() and ord(ch) >= 32)
        )
        return value

    def escape_markdown(self, value: str) -> str:
        # 转义 Markdown 特殊字符
        chars = ["\\", "`", "*", "_", "{", "}", "[", "]", "(", ")", "#", "+", "-", "!", "|"]
        for ch in chars:
            value = value.replace(ch, "\\" + ch)
        return value

    def detect_injection(self, value: str) -> List[InjectionRisk]:
        risks: List[InjectionRisk] = []
        value_lower = value.lower()
        for pattern, level in self.INJECTION_PATTERNS:
            if re.search(pattern, value_lower, re.IGNORECASE):
                risks.append(
                    InjectionRisk(
                        level=level,
                        pattern_matched=pattern,
                        recommendation="Review input for prompt injection attempt",
                    )
                )
        return risks

    def sanitize_variables(
        self, variables: Dict[str, Any], schema: Optional[PromptSchema] = None
    ) -> Tuple[Dict[str, Any], List[InjectionRisk]]:
        """清洗变量字典，返回 (清洗后变量, 风险列表)。"""
        sanitized: Dict[str, Any] = {}
        all_risks: List[InjectionRisk] = []

        for key, value in variables.items():
            str_value = str(value) if value is not None else ""

            # 确定 max_length
            max_len = 10000
            if schema is not None:
                spec = schema.get_spec(key)
                if spec is not None and spec.max_length is not None:
                    max_len = spec.max_length

            # 清洗
            str_value = self.sanitize_string(str_value, max_length=max_len)

            # 检测 injection
            risks = self.detect_injection(str_value)
            all_risks.extend(risks)

            sanitized[key] = str_value

        return sanitized, all_risks
