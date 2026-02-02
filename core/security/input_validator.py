#!/usr/bin/env python3
"""
输入安全验证器
Input Security Validator

增强的输入安全验证,防止各种安全威胁:
1. XSS攻击
2. SQL注入
3. 模板注入
4. 路径遍历
5. 命令注入
6. Python注入

作者: Athena平台团队
创建时间: 2026-01-16
版本: 1.0.0
"""

import html
import logging
import math
import re
from collections import Counter
from enum import Enum

logger = logging.getLogger(__name__)


class SecurityLevel(Enum):
    """安全级别"""

    LOW = "low"  # 低:基础检查
    MEDIUM = "medium"  # 中:标准检查
    HIGH = "high"  # 高:严格检查
    STRICT = "strict"  # 严格:最大安全


class SecurityThreat(Enum):
    """安全威胁类型"""

    XSS = "XSS攻击"
    SQL_INJECTION = "SQL注入"
    JS_INJECTION = "JavaScript注入"
    TEMPLATE_INJECTION = "模板注入"
    PYTHON_INJECTION = "Python注入"
    PATH_TRAVERSAL = "路径遍历"
    COMMAND_INJECTION = "命令注入"


class InputValidator:
    """
    增强的输入安全验证器

    提供全面的安全检查功能,检测各种常见的安全威胁
    """

    # 安全威胁检测模式
    THREAT_PATTERNS = {
        SecurityThreat.XSS: [
            re.compile(r"<script[^>]*>.*?</script>", re.IGNORECASE | re.DOTALL),
            re.compile(r"javascript:", re.IGNORECASE),
            re.compile(r"on\w+\s*=", re.IGNORECASE),
            re.compile(r"<iframe[^>]*>", re.IGNORECASE),
            re.compile(r"<embed[^>]*>", re.IGNORECASE),
            re.compile(r"<object[^>]*>", re.IGNORECASE),
            re.compile(r"onload\s*=", re.IGNORECASE),
            re.compile(r"onerror\s*=", re.IGNORECASE),
            re.compile(r"<img[^>]*onerror[^>]*>", re.IGNORECASE),
        ],
        SecurityThreat.SQL_INJECTION: [
            re.compile(r"('|\-\-|;|\/\*|\*\/|@@)", re.IGNORECASE),
            re.compile(
                r"\b(union|select|insert|delete|drop|create|alter|exec|execute|executesql)\b",
                re.IGNORECASE,
            ),
            re.compile(r"\b(or|and)\s+\d+\s*=\s*\d+", re.IGNORECASE),
            re.compile(r"\bor\s+1\s*=\s*1", re.IGNORECASE),
            re.compile(r";\s*(drop|delete|insert|update)\b", re.IGNORECASE),
            re.compile(r"\*\s*from\s*\w+", re.IGNORECASE),
        ],
        SecurityThreat.JS_INJECTION: [
            re.compile(r"javascript:", re.IGNORECASE),
            re.compile(r"vbscript:", re.IGNORECASE),
            re.compile(r"onload\s*=", re.IGNORECASE),
            re.compile(r"onerror\s*=", re.IGNORECASE),
            re.compile(r"onclick\s*=", re.IGNORECASE),
        ],
        SecurityThreat.TEMPLATE_INJECTION: [
            re.compile(r"\$\{[^}]*\}"),
            re.compile(r"\{\{[^}]*\}\}"),
            re.compile(r"\{%[^}]*%\}"),
            re.compile(r"\{#.*?#\}"),  # Jinja2注释
        ],
        SecurityThreat.PYTHON_INJECTION: [
            re.compile(r"__\w+__"),  # 魔术方法
            re.compile(r"import\s+\w+"),
            re.compile(r"from\s+\w+\s+import"),
            re.compile(r"eval\s*\("),
            re.compile(r"exec\s*\("),
            re.compile(r"compile\s*\("),
            re.compile(r"__import__\("),
        ],
        SecurityThreat.PATH_TRAVERSAL: [
            re.compile(r"\.\.[\/\\]"),
            re.compile(r"%2e%2e", re.IGNORECASE),  # URL编码的..
            re.compile(r"~\/"),  # Unix home目录
            re.compile(r"%5c", re.IGNORECASE),  # URL编码的\
            re.compile(r"\\x2e\\x2e\\x2e"),  # 十六进制编码的...
        ],
        SecurityThreat.COMMAND_INJECTION: [
            re.compile(r"[;&|`$]"),  # Shell元字符
            re.compile(r"\|.*\|"),  # 管道
            re.compile(r"&&"),  # 命令连接符
            re.compile(r"\`\$\(.*?\)\`"),  # 命令替换
            re.compile(r"\$\(.*?\)"),  # 命令替换
        ],
    }

    def __init__(self, security_level: SecurityLevel = SecurityLevel.HIGH):
        """
        初始化验证器

        Args:
            security_level: 安全级别
        """
        self.security_level = security_level
        logger.info(f"🔒 安全验证器初始化: 级别={security_level.value}")

    def validate(self, input_data: str, context: str = "") -> tuple[bool, list[str]]:
        """
        全面安全验证

        Args:
            input_data: 输入数据
            context: 上下文信息(用于日志)

        Returns:
            (is_valid, threat_list): 是否有效,威胁列表
        """
        if not isinstance(input_data, str):
            return False, ["输入类型错误:必须是字符串"]

        threats = []

        # 根据安全级别选择检测深度
        checks_to_run = self._get_checks_for_level()

        # 执行各类威胁检测(在原始输入上进行,避免清理破坏检测)
        for threat_type in checks_to_run:
            patterns = self.THREAT_PATTERNS.get(threat_type, [])
            for pattern in patterns:
                if pattern.search(input_data):
                    threat_msg = f"{threat_type.value}: 发现匹配 '{pattern.pattern}'"
                    threats.append(threat_msg)
                    logger.warning(f"🚨 安全威胁检测: {threat_msg} in {context}")

        # 深度验证(高安全级别)
        if self.security_level in [SecurityLevel.HIGH, SecurityLevel.STRICT]:
            # 使用清理后的输入进行深度验证
            cleaned_input = self._sanitize_input(input_data)
            threats.extend(self._deep_validation(cleaned_input))

        is_valid = len(threats) == 0

        if not is_valid:
            logger.warning(f"🚨 输入验证失败: {context}")
            for threat in threats:
                logger.warning(f"  - {threat}")

        return is_valid, threats

    def _get_checks_for_level(self) -> list[SecurityThreat]:
        """根据安全级别获取要执行的检查"""
        # 所有级别都检查基础威胁
        base_checks = [
            SecurityThreat.XSS,
            SecurityThreat.SQL_INJECTION,
        ]

        if self.security_level == SecurityLevel.LOW:
            return base_checks

        if self.security_level == SecurityLevel.MEDIUM:
            return [*base_checks, SecurityThreat.JS_INJECTION, SecurityThreat.PATH_TRAVERSAL]

        if self.security_level == SecurityLevel.HIGH:
            return list(SecurityThreat)  # 全部检查

        if self.security_level == SecurityLevel.STRICT:
            return list(SecurityThreat)  # 全部检查(更严格的阈值)

        return base_checks

    def _sanitize_input(self, input_data: str) -> str:
        """基础清理"""
        # HTML转义
        sanitized = html.escape(input_data)

        # 移除控制字符
        sanitized = re.sub(r"[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]", "", sanitized)

        # 移除零宽字符
        sanitized = re.sub(r"[\u200B-\u200F\ufeff]", "", sanitized)

        return sanitized

    def _deep_validation(self, input_data: str) -> list[str]:
        """深度验证"""
        threats = []

        # 检查编码异常
        try:
            input_data.encode("utf-8")
        except UnicodeEncodeError:
            threats.append("编码异常: 包含无效的Unicode字符")

        # 检查长度限制
        if len(input_data) > 100000:
            threats.append(f"长度异常: 输入过长 ({len(input_data)} 字符)")

        # 检查熵值(检测随机字符串攻击)
        if len(input_data) > 100:
            entropy = self._calculate_entropy(input_data)
            if entropy > 7.5:
                threats.append(f"熵值异常: {entropy:.2f} (可能为随机字符串攻击)")

        # 检查字符分布异常
        char_dist = self._check_character_distribution(input_data)
        if char_dist:
            threats.append(char_dist)

        return threats

    def _calculate_entropy(self, data: str) -> float:
        """计算字符串熵值"""
        if not data:
            return 0.0

        counter = Counter(data)
        total = len(data)
        entropy = 0.0

        for count in counter.values():
            probability = count / total
            entropy -= probability * math.log2(probability)

        return entropy

    def _check_character_distribution(self, data: str) -> str | None:
        """检查字符分布是否异常"""
        if len(data) < 50:
            return None

        # 检查是否有大量重复字符
        char_freq = Counter(data)
        max_freq = char_freq.most_common(1)[0][1]
        max_freq_ratio = max_freq / len(data)

        if max_freq_ratio > 0.5:
            return f"字符分布异常: 单字符占比过高 ({max_freq_ratio:.1%})"

        # 检查是否有大量连续相同字符
        max_consecutive = 0
        current_consecutive = 1
        prev_char = None

        for char in data:
            if char == prev_char:
                current_consecutive += 1
            else:
                max_consecutive = max(max_consecutive, current_consecutive)
                current_consecutive = 1
                prev_char = char

        max_consecutive = max(max_consecutive, current_consecutive)

        if max_consecutive > 10:
            return f"字符分布异常: 连续相同字符过多 ({max_consecutive})"

        return None

    def sanitize(self, input_data: str) -> str:
        """
        清理和净化输入

        Args:
            input_data: 原始输入

        Returns:
            str: 清理后的安全输入
        """
        # HTML转义
        sanitized = html.escape(input_data)

        # 移除危险字符
        sanitized = re.sub(r"[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]", "", sanitized)

        # 移除零宽字符
        sanitized = re.sub(r"[\u200B-\u200F\ufeff]", "", sanitized)

        # 标准化Unicode
        import unicodedata

        sanitized = unicodedata.normalize("NFKC", sanitized)

        return sanitized

    def validate_sql_query(self, query: str) -> tuple[bool, list[str]]:
        """
        验证SQL查询的安全性

        Args:
            query: SQL查询语句

        Returns:
            (is_safe, issues): 是否安全,问题列表
        """
        issues = []

        # 检查危险关键字
        dangerous_keywords = [
            "DROP",
            "DELETE",
            "TRUNCATE",
            "ALTER",
            "CREATE",
            "EXEC",
            "EXECUTE",
            "EXECUTESQL",
            "xp_cmdshell",
            "sp_oacreate",
        ]

        query_upper = query.upper()
        for keyword in dangerous_keywords:
            if keyword in query_upper:
                issues.append(f"包含危险关键字: {keyword}")

        # 检查注释注入
        if "--" in query or "/*" in query:
            issues.append("包含SQL注释标记(可能的注释注入)")

        # 检查多个语句
        if ";" in query.strip()[:-1]:  # 允许结尾的分号
            issues.append("包含多个SQL语句(可能的注入)")

        # 检查字符串拼接
        if re.search(r'"\s*\+\s*"', query) or re.search(r"'\s*\+\s*'", query):
            issues.append("使用字符串拼接(应该使用参数化查询)")

        is_safe = len(issues) == 0

        return is_safe, issues

    def check_file_path(self, file_path: str) -> tuple[bool, list[str]]:
        """
        检查文件路径的安全性

        Args:
            file_path: 文件路径

        Returns:
            (is_safe, issues): 是否安全,问题列表
        """
        issues = []

        # 检查路径遍历
        if ".." in file_path:
            issues.append("包含父目录引用(..)")

        # 检查绝对路径
        if file_path.startswith("/") or (len(file_path) > 1 and file_path[1] == ":"):
            issues.append("使用绝对路径(可能不安全)")

        # 检查敏感目录
        sensitive_dirs = ["/etc", "/sys", "/proc", "/root", "~"]
        for sensitive_dir in sensitive_dirs:
            if file_path.startswith(sensitive_dir):
                issues.append(f"尝试访问敏感目录: {sensitive_dir}")

        # 检查URL编码的路径遍历
        if "%2e%2e" in file_path.lower():
            issues.append("包含URL编码的路径遍历")

        is_safe = len(issues) == 0

        return is_safe, issues


# 单例模式
_validator: InputValidator | None = None


def get_input_validator(security_level: SecurityLevel = SecurityLevel.HIGH) -> InputValidator:
    """
    获取输入验证器单例

    Args:
        security_level: 安全级别

    Returns:
        InputValidator: 验证器实例
    """
    global _validator
    if _validator is None or _validator.security_level != security_level:
        _validator = InputValidator(security_level)
    return _validator


def validate_input(
    input_data: str, context: str = "", security_level: SecurityLevel = SecurityLevel.HIGH
) -> tuple[bool, list[str]]:
    """
    便捷函数:验证输入

    Args:
        input_data: 输入数据
        context: 上下文
        security_level: 安全级别

    Returns:
        (is_valid, threats): 是否有效,威胁列表
    """
    validator = get_input_validator(security_level)
    return validator.validate(input_data, context)
