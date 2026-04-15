#!/usr/bin/env python3
"""
日志脱敏器
Log Sanitizer

版本: 1.0.0
功能:
- 自动识别和脱敏敏感信息
- 支持多种敏感信息类型
- 可配置脱敏规则
- 保留数据格式用于调试
"""

from __future__ import annotations
import json
import logging
import re
from dataclasses import dataclass
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class SanitizationRule:
    """脱敏规则"""

    name: str
    pattern: str
    replacement: str = "[REDACTED]"
    flags: int = re.IGNORECASE
    enabled: bool = True

    def compile(self) -> re.Pattern:
        """编译正则表达式"""
        return re.compile(self.pattern, flags=self.flags)


class LogSanitizer:
    """
    日志脱敏器

    自动识别和脱敏敏感信息,保护用户隐私
    """

    # 默认脱敏规则
    DEFAULT_RULES = [
        # 邮箱地址
        SanitizationRule(
            name="email",
            pattern=r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",
            replacement="[EMAIL_REDACTED]",
        ),
        # 手机号(中国)
        SanitizationRule(name="phone", pattern=r"\b1[3-9]\d{9}\b", replacement="[PHONE_REDACTED]"),
        # 身份证号
        SanitizationRule(
            name="id_card", pattern=r"\b\d{17}[\dXx]\b", replacement="[ID_CARD_REDACTED]"
        ),
        # 银行卡号
        SanitizationRule(
            name="bank_card", pattern=r"\b\d{16,19}\b", replacement="[BANK_CARD_REDACTED]"
        ),
        # 密码字段
        SanitizationRule(
            name="password",
            pattern=r'(password|passwd|pwd)["\']?\s*[:=]\s*["\']?[^"\'\s]+',
            replacement=r"\1: [PASSWORD_REDACTED]",
        ),
        # API密钥
        SanitizationRule(
            name="api_key",
            pattern=r'(api_key|apikey|access_token|secret)["\']?\s*[:=]\s*["\']?[^"\'\s]+',
            replacement=r"\1: [API_KEY_REDACTED]",
        ),
        # JWT Token
        SanitizationRule(
            name="jwt_token",
            pattern=r"eyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+",
            replacement="[JWT_TOKEN_REDACTED]",
        ),
        # Bearer Token
        SanitizationRule(
            name="bearer_token",
            pattern=r"Bearer\s+[A-Za-z0-9\-._~+/]+=*",
            replacement="Bearer [TOKEN_REDACTED]",
        ),
        # IP地址(可选,根据需求)
        SanitizationRule(
            name="ip_address",
            pattern=r"\b(?:\d{1,3}\.){3}\d{1,3}\b",
            replacement="[IP_REDACTED]",
            enabled=False,  # 默认关闭,可根据需要启用
        ),
        # 信用卡号(Luhn算法格式)
        SanitizationRule(
            name="credit_card",
            pattern=r"\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b",
            replacement="[CREDIT_CARD_REDACTED]",
        ),
        # SSN(美国社会安全号)
        SanitizationRule(
            name="ssn", pattern=r"\b\d{3}-\d{2}-\d{4}\b", replacement="[SSN_REDACTED]"
        ),
    ]

    def __init__(self, custom_rules: list[SanitizationRule] | None = None):
        """
        初始化脱敏器

        Args:
            custom_rules: 自定义脱敏规则
        """
        self.rules = self.DEFAULT_RULES.copy()
        if custom_rules:
            self.rules.extend(custom_rules)

        # 编译所有启用的规则
        self.compiled_rules = [rule.compile() for rule in self.rules if rule.enabled]

        logger.info(f"✅ 日志脱敏器初始化完成,规则数: {len(self.compiled_rules)}")

    def sanitize(self, message: str) -> str:
        """
        脱敏日志消息

        Args:
            message: 原始日志消息

        Returns:
            脱敏后的消息
        """
        if not message:
            return message

        sanitized = message
        for rule in self.compiled_rules:
            sanitized = rule.pattern.sub(rule.replacement, sanitized)

        return sanitized

    def sanitize_dict(self, data: dict[str, Any]) -> dict[str, Any]:
        """
        脱敏字典数据

        Args:
            data: 原始字典

        Returns:
            脱敏后的字典
        """
        if not data:
            return data

        sanitized = {}
        for key, value in data.items():
            # 检查键名是否包含敏感字段
            if self._is_sensitive_key(key):
                sanitized[key] = "[REDACTED]"
            elif isinstance(value, str):
                sanitized[key] = self.sanitize(value)
            elif isinstance(value, dict):
                sanitized[key] = self.sanitize_dict(value)
            elif isinstance(value, list):
                sanitized[key] = self.sanitize_list(value)
            else:
                sanitized[key] = value

        return sanitized

    def sanitize_list(self, data: list[Any]) -> list[Any]:
        """
        脱敏列表数据

        Args:
            data: 原始列表

        Returns:
            脱敏后的列表
        """
        if not data:
            return data

        sanitized = []
        for item in data:
            if isinstance(item, str):
                sanitized.append(self.sanitize(item))
            elif isinstance(item, dict):
                sanitized.append(self.sanitize_dict(item))
            elif isinstance(item, list):
                sanitized.append(self.sanitize_list(item))
            else:
                sanitized.append(item)

        return sanitized

    def _is_sensitive_key(self, key: str) -> bool:
        """
        检查键名是否为敏感字段

        Args:
            key: 键名

        Returns:
            是否为敏感字段
        """
        sensitive_keywords = [
            "password",
            "passwd",
            "pwd",
            "token",
            "secret",
            "key",
            "api_key",
            "apikey",
            "access_key",
            "private_key",
            "auth",
            "credit_card",
            "ssn",
            "id_card",
        ]

        key_lower = key.lower()
        return any(keyword in key_lower for keyword in sensitive_keywords)

    def sanitize_json(self, json_str: str) -> str:
        """
        脱敏JSON字符串

        Args:
            json_str: JSON字符串

        Returns:
            脱敏后的JSON字符串
        """
        try:
            data = json.loads(json_str)
            sanitized = self.sanitize_dict(data)
            return json.dumps(sanitized, ensure_ascii=False)
        except (json.JSONDecodeError, TypeError):
            # 如果解析失败,直接进行文本脱敏
            return self.sanitize(json_str)

    def add_rule(self, rule: SanitizationRule):
        """
        添加自定义规则

        Args:
            rule: 脱敏规则
        """
        self.rules.append(rule)
        if rule.enabled:
            self.compiled_rules.append(rule.compile())
            logger.info(f"✅ 已添加脱敏规则: {rule.name}")

    def remove_rule(self, name: str) -> bool:
        """
        移除脱敏规则

        Args:
            name: 规则名称

        Returns:
            是否成功移除
        """
        for i, rule in enumerate(self.rules):
            if rule.name == name:
                self.rules.pop(i)
                # 重新编译
                self.compiled_rules = [r.compile() for r in self.rules if r.enabled]
                logger.info(f"❌ 已移除脱敏规则: {name}")
                return True
        return False

    def get_stats(self, text: str) -> dict[str, int]:
        """
        统计脱敏情况

        Args:
            text: 原始文本

        Returns:
            各类敏感信息的数量
        """
        stats = {}
        for rule in self.rules:
            if rule.enabled:
                matches = rule.pattern.findall(text)
                if matches:
                    stats[rule.name] = len(matches)

        return stats


class SanitizingFormatter(logging.Formatter):
    """
    脱敏日志格式化器

    自动脱敏日志中的敏感信息
    """

    def __init__(
        self,
        sanitizer: LogSanitizer | None = None,
        fmt: str | None = None,
        datefmt: str | None = None,
    ):
        """
        初始化格式化器

        Args:
            sanitizer: 脱敏器(None使用默认)
            fmt: 日志格式
            datefmt: 日期格式
        """
        super().__init__(fmt=fmt, datefmt=datefmt)
        self.sanitizer = sanitizer or LogSanitizer()

    def format(self, record: logging.LogRecord) -> str:
        """
        格式化日志记录(脱敏)

        Args:
            record: 日志记录

        Returns:
            格式化并脱敏后的日志
        """
        # 先调用父类格式化
        formatted = super().format(record)

        # 脱敏
        sanitized = self.sanitizer.sanitize(formatted)

        return sanitized


# 全局单例
_global_sanitizer: LogSanitizer | None = None


def get_log_sanitizer() -> LogSanitizer:
    """
    获取全局日志脱敏器

    Returns:
        LogSanitizer实例
    """
    global _global_sanitizer

    if _global_sanitizer is None:
        _global_sanitizer = LogSanitizer()

    return _global_sanitizer


def sanitize_log(message: str) -> str:
    """
    便捷函数:脱敏日志消息

    Args:
        message: 原始消息

    Returns:
        脱敏后的消息
    """
    return get_log_sanitizer().sanitize(message)


def sanitize_log_dict(data: dict[str, Any]) -> dict[str, Any]:
    """
    便捷函数:脱敏字典数据

    Args:
        data: 原始字典

    Returns:
        脱敏后的字典
    """
    return get_log_sanitizer().sanitize_dict(data)


# 自定义脱敏规则示例
CUSTOM_RULES = [
    # 自定义规则可以在这里添加
    # SanitizationRule(
    #     name="custom_field",
    #     pattern=r'custom_pattern',
    #     replacement="[CUSTOM_REDACTED]"
    # ),
]
