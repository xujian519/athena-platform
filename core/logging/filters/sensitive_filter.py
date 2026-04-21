"""
敏感信息过滤器
Sensitive Data Filter

自动过滤或脱敏日志中的敏感信息
"""
import logging
import re
from typing import List, Dict, Pattern, Any, Optional


class SensitiveDataFilter(logging.Filter):
    """敏感信息过滤器

    自动识别并脱敏日志中的敏感信息

    支持的敏感信息类型:
    - 手机号: 138****1234
    - 身份证: 110101****1234
    - 邮箱: u****@example.com
    - 银行卡: 6222****1234
    - 密码: [REDACTED]
    - Token: [REDACTED]
    - API Key: [REDACTED]
    - 自定义模式
    """

    # 默认敏感信息正则模式
    DEFAULT_PATTERNS = {
        "phone": r'1[3-9]\d{9}',  # 手机号
        "id_card": r'[1-9]\d{5}(18|19|20)\d{2}(0[1-9]|1[0-2])(0[1-9]|[12]\d|3[01])\d{3}[\dXx]',  # 身份证
        "email": r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}',  # 邮箱
        "bank_card": r'\d{16,19}',  # 银行卡号
    }

    # 默认敏感字段名
    DEFAULT_SENSITIVE_FIELDS = [
        "password", "passwd", "pwd",
        "token", "access_token", "refresh_token",
        "api_key", "apikey", "api-key",
        "secret", "private_key", "private-key",
        "authorization", "auth"
    ]

    def __init__(
        self,
        patterns: Optional[Dict[str, str]] = None,
        sensitive_fields: Optional[List[str]] = None,
        mask_char: str = "*",
        mask_ratio: float = 0.5
    ):
        """初始化敏感信息过滤器

        Args:
            patterns: 自定义正则模式字典 {name: pattern}
            sensitive_fields: 敏感字段名列表
            mask_char: 脱敏字符
            mask_ratio: 脱敏比例（0-1，0.5表示脱敏50%）
        """
        super().__init__()

        self.mask_char = mask_char
        self.mask_ratio = mask_ratio

        # 合并默认和自定义模式
        self.patterns = {**self.DEFAULT_PATTERNS}
        if patterns:
            self.patterns.update(patterns)

        # 编译正则表达式
        self.compiled_patterns: Dict[str, Pattern] = {
            name: re.compile(pattern)
            for name, pattern in self.patterns.items()
        }

        # 合并默认和自定义敏感字段
        self.sensitive_fields = set(self.DEFAULT_SENSITIVE_FIELDS)
        if sensitive_fields:
            self.sensitive_fields.update(sensitive_fields)

    def filter(self, record: logging.LogRecord) -> bool:
        """过滤日志记录

        脱敏日志消息中的敏感信息

        Args:
            record: 日志记录

        Returns:
            始终返回True（允许记录通过）
        """
        # 脱敏消息
        if hasattr(record, "msg"):
            record.msg = self._sanitize(str(record.msg))

        # 脱敏格式化后的消息
        if record.getMessage():
            record.message = self._sanitize(record.getMessage())

        # 脱敏参数中的敏感字段
        if hasattr(record, "args") and record.args:
            record.args = self._sanitize_args(record.args)

        return True

    def _sanitize(self, text: str) -> str:
        """脱敏文本中的敏感信息

        Args:
            text: 原始文本

        Returns:
            脱敏后的文本
        """
        sanitized = text

        # 应用所有正则模式
        for pattern_name, pattern in self.compiled_patterns.items():
            matches = pattern.finditer(sanitized)

            for match in matches:
                original = match.group()
                masked = self._mask_value(original, pattern_name)
                sanitized = sanitized.replace(original, masked, 1)

        return sanitized

    def _mask_value(self, value: str, pattern_name: str) -> str:
        """脱敏单个值

        Args:
            value: 原始值
            pattern_name: 模式名称

        Returns:
            脱敏后的值
        """
        length = len(value)
        if length <= 4:
            # 短值完全脱敏
            return self.mask_char * length

        # 计算脱敏数量
        mask_count = int(length * self.mask_ratio)

        # 特殊处理：保留部分信息
        if pattern_name == "phone":
            # 手机号：保留前3位和后4位
            return f"{value[:3]}{self.mask_char * 4}{value[-4:]}"
        elif pattern_name == "id_card":
            # 身份证：保留前6位和后4位
            return f"{value[:6]}{self.mask_char * 8}{value[-4:]}"
        elif pattern_name == "email":
            # 邮箱：保留第一个字符和域名
            at_index = value.find("@")
            if at_index > 1:
                return f"{value[0]}{self.mask_char * (at_index - 1)}{value[at_index:]}"
            return value
        elif pattern_name == "bank_card":
            # 银行卡：保留前4位和后4位
            return f"{value[:4]}{self.mask_char * (length - 8)}{value[-4:]}"
        else:
            # 通用：保留前后部分
            keep = length - mask_count
            return f"{value[:keep//2]}{self.mask_char * mask_count}{value[-(keep-keep//2):]}"

    def _sanitize_args(self, args: tuple) -> tuple:
        """脱敏参数中的敏感字段

        Args:
            args: 原始参数元组

        Returns:
            脱敏后的参数元组
        """
        sanitized = []

        for arg in args:
            if isinstance(arg, dict):
                # 字典：脱敏敏感字段
                sanitized.append(self._sanitize_dict(arg))
            else:
                sanitized.append(arg)

        return tuple(sanitized)

    def _sanitize_dict(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """脱敏字典中的敏感字段

        Args:
            data: 原始字典

        Returns:
            脱敏后的字典
        """
        sanitized = {}

        for key, value in data.items():
            # 检查是否是敏感字段
            if key.lower() in self.sensitive_fields:
                # 完全脱敏
                sanitized[key] = "[REDACTED]"
            elif isinstance(value, str):
                # 字符串值：应用内容脱敏
                sanitized[key] = self._sanitize(value)
            elif isinstance(value, dict):
                # 嵌套字典：递归脱敏
                sanitized[key] = self._sanitize_dict(value)
            else:
                sanitized[key] = value

        return sanitized

    def add_pattern(self, name: str, pattern: str) -> None:
        """添加自定义敏感信息模式

        Args:
            name: 模式名称
            pattern: 正则表达式
        """
        self.patterns[name] = pattern
        self.compiled_patterns[name] = re.compile(pattern)

    def add_sensitive_field(self, field_name: str) -> None:
        """添加敏感字段名

        Args:
            field_name: 字段名
        """
        self.sensitive_fields.add(field_name.lower())
