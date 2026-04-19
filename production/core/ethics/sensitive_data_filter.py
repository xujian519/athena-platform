"""
敏感信息过滤器 - 防止敏感数据泄露到日志
Sensitive Information Filter - Prevent Sensitive Data Leakage in Logs

功能:
1. 过滤敏感字段(密码、token、API密钥等)
2. 过滤用户个人身份信息(PII)
3. 过滤查询参数中的敏感内容
4. 可扩展的敏感模式匹配
"""

from __future__ import annotations
import re
from collections.abc import Sequence
from dataclasses import dataclass
from re import Pattern
from typing import Any


@dataclass
class SensitivePattern:
    """敏感信息模式"""

    name: str
    pattern: Pattern
    description: str
    replacement: str = "***"


class SensitiveDataFilter:
    """敏感数据过滤器

    防止敏感信息泄露到日志中
    """

    # 默认敏感字段名
    DEFAULT_SENSITIVE_FIELDS: set[str] = {
        "password",
        "passwd",
        "pwd",
        "token",
        "access_token",
        "refresh_token",
        "auth_token",
        "api_key",
        "apikey",
        "api-key",
        "secret",
        "secret_key",
        "private_key",
        "credential",
        "credentials",
        "session_id",
        "sessionid",
        "cookie",
        "cookies",
        "ssn",
        "social_security",
        "credit_card",
        "creditcard",
        "cc_number",
        "bank_account",
        "bankaccount",
        "pin",
        "pin_code",
    }

    # 默认敏感模式
    DEFAULT_PATTERNS: list[SensitivePattern] = [
        SensitivePattern(
            name="email",
            pattern=re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"),
            description="电子邮件地址",
        ),
        SensitivePattern(
            name="phone",
            pattern=re.compile(r"\b\d{3}[-.]?\d{3}[-.]?\d{4}\b"),
            description="电话号码",
        ),
        SensitivePattern(
            name="ip_address",
            pattern=re.compile(r"\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b"),
            description="IP地址",
        ),
        SensitivePattern(
            name="credit_card",
            pattern=re.compile(r"\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b"),
            description="信用卡号",
        ),
        SensitivePattern(
            name="ssn", pattern=re.compile(r"\b\d{3}-\d{2}-\d{4}\b"), description="社会安全号码"
        ),
        SensitivePattern(
            name="api_key",
            pattern=re.compile(r"\b[A-Za-z0-9]{32,}\b"),
            description="API密钥(32字符以上)",
        ),
        SensitivePattern(
            name="bearer_token",
            pattern=re.compile(r"Bearer\s+[A-Za-z0-9\-._~+/]+=*", re.IGNORECASE),
            description="Bearer令牌",
        ),
    ]

    def __init__(
        self,
        sensitive_fields: set[str] | None = None,
        custom_patterns: list[dict] | None = None,
        enabled: bool = True,
    ):
        """初始化敏感数据过滤器

        Args:
            sensitive_fields: 敏感字段名集合
            custom_patterns: 自定义敏感模式
            enabled: 是否启用过滤
        """
        self.sensitive_fields = sensitive_fields or self.DEFAULT_SENSITIVE_FIELDS.copy()
        self.patterns: list[SensitivePattern] = self.DEFAULT_PATTERNS.copy()
        if custom_patterns:
            self.patterns.extend(custom_patterns)
        self.enabled = enabled
        self._compile_patterns()

    def _compile_patterns(self) -> Any:
        """预编译正则表达式"""
        for pattern in self.patterns:
            if not isinstance(pattern.pattern, Pattern):
                pattern.pattern = re.compile(pattern.pattern)

    def is_sensitive_field(self, field_name: str) -> bool:
        """检查字段名是否敏感

        Args:
            field_name: 字段名

        Returns:
            bool: 是否敏感
        """
        field_lower = field_name.lower()
        return any(sensitive in field_lower for sensitive in self.sensitive_fields)

    def filter_dict(self, data: dict[str, Any], max_depth: int = 10) -> dict[str, Any]:
        """过滤字典中的敏感数据

        Args:
            data: 输入字典
            max_depth: 最大递归深度

        Returns:
            过滤后的字典
        """
        if not self.enabled or max_depth <= 0:
            return data

        filtered = {}
        for key, value in data.items():
            if self.is_sensitive_field(key):
                filtered[key] = "***FILTERED***"
            elif isinstance(value, dict):
                filtered[key] = self.filter_dict(value, max_depth - 1)
            elif isinstance(value, (list, tuple)):
                filtered[key] = self.filter_sequence(value, max_depth - 1)
            elif isinstance(value, str):
                filtered[key] = self.filter_string(value)
            else:
                filtered[key] = value
        return filtered

    def filter_sequence(self, sequence: Sequence[Any], max_depth: int = 10) -> list[Any]:
        """过滤序列中的敏感数据

        Args:
            sequence: 输入序列
            max_depth: 最大递归深度

        Returns:
            过滤后的列表
        """
        if not self.enabled or max_depth <= 0:
            return list(sequence) if not isinstance(sequence, list) else sequence

        filtered = []
        for item in sequence:
            if isinstance(item, dict):
                filtered.append(self.filter_dict(item, max_depth - 1))
            elif isinstance(item, (list, tuple)):
                filtered.append(self.filter_sequence(item, max_depth - 1))
            elif isinstance(item, str):
                filtered.append(self.filter_string(item))
            else:
                filtered.append(item)
        return filtered

    def filter_string(self, text: str) -> str:
        """过滤字符串中的敏感模式

        Args:
            text: 输入文本

        Returns:
            过滤后的文本
        """
        if not self.enabled:
            return text

        result = text
        for pattern in self.patterns:
            result = pattern.pattern.sub(pattern.replacement, result)
        return result

    def filter_log_message(self, message: str, context: dict[str, Any] | None = None) -> str:
        """过滤日志消息

        Args:
            message: 日志消息
            context: 上下文字典

        Returns:
            过滤后的日志消息
        """
        if not self.enabled:
            return message

        # 过滤消息中的敏感模式
        filtered_message = self.filter_string(message)

        # 如果有上下文,过滤敏感字段
        if context:
            filtered_context = self.filter_dict(context)
            # 添加过滤后的上下文到消息
            context_str = ", ".join(f"{k}={v}" for k, v in filtered_context.items())
            if context_str:
                filtered_message = f"{filtered_message} | {context_str}"

        return filtered_message

    def add_sensitive_field(self, field_name: str) -> None:
        """添加敏感字段

        Args:
            field_name: 字段名
        """
        self.sensitive_fields.add(field_name.lower())

    def add_pattern(self, pattern: SensitivePattern) -> None:
        """添加敏感模式

        Args:
            pattern: 敏感模式
        """
        if not isinstance(pattern.pattern, Pattern):
            pattern.pattern = re.compile(pattern.pattern)
        self.patterns.append(pattern)

    def remove_pattern(self, name: str) -> None:
        """移除敏感模式

        Args:
            name: 模式名称
        """
        self.patterns = [p for p in self.patterns if p.name != name]

    def get_stats(self) -> dict[str, Any]:
        """获取过滤器统计信息

        Returns:
            统计信息字典
        """
        return {
            "enabled": self.enabled,
            "sensitive_fields_count": len(self.sensitive_fields),
            "patterns_count": len(self.patterns),
            "pattern_names": [p.name for p in self.patterns],
        }


# 全局过滤器实例
_global_filter: SensitiveDataFilter | None = None


def get_sensitive_data_filter() -> SensitiveDataFilter:
    """获取全局敏感数据过滤器"""
    global _global_filter
    if _global_filter is None:
        _global_filter = SensitiveDataFilter()
    return _global_filter


def create_sensitive_data_filter(
    sensitive_fields: set[str] | None = None,
    custom_patterns: list[dict] | None = None,
) -> SensitiveDataFilter:
    """创建敏感数据过滤器

    Args:
        sensitive_fields: 敏感字段名集合
        custom_patterns: 自定义敏感模式

    Returns:
        敏感数据过滤器实例
    """
    return SensitiveDataFilter(sensitive_fields=sensitive_fields, custom_patterns=custom_patterns)


# 便捷函数
def filter_sensitive_data(data: Any) -> Any:
    """过滤敏感数据(便捷函数)

    Args:
        data: 输入数据

    Returns:
        过滤后的数据
    """
    filter_obj = get_sensitive_data_filter()
    if isinstance(data, dict):
        return filter_obj.filter_dict(data)
    elif isinstance(data, (list, tuple)):
        return filter_obj.filter_sequence(list(data))
    elif isinstance(data, str):
        return filter_obj.filter_string(data)
    else:
        return data


def filter_log(message: str | None = None, context: dict[str, Any] | None = None) -> str:
    """过滤日志消息(便捷函数)

    Args:
        message: 日志消息
        context: 上下文字典

    Returns:
        过滤后的日志消息
    """
    filter_obj = get_sensitive_data_filter()
    return filter_obj.filter_log_message(message, context)
