"""
统一LLM层 - 安全工具
敏感信息脱敏和安全检查工具

作者: Claude Code
日期: 2026-01-23
"""

import logging
import re
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


def mask_api_key(api_key: str, visible_chars: int = 8) -> str:
    """
    脱敏API密钥

    Args:
        api_key: 原始API密钥
        visible_chars: 保留可见的首尾字符数

    Returns:
        str: 脱敏后的API密钥

    Examples:
        >>> mask_api_key("sk-1234567890abcdef")
        'sk-1234****bcdef'
    """
    if not api_key:
        return "***"

    if len(api_key) <= visible_chars * 2:
        return "***"  # 太短,全部隐藏

    # 保留首尾几个字符,中间用星号代替
    visible_start = api_key[:visible_chars]
    visible_end = api_key[-visible_chars:]
    masked_length = len(api_key) - visible_chars * 2

    return f"{visible_start}{'*' * masked_length}{visible_end}"


def mask_sensitive_data(data: str | None = None, patterns: Optional[dict[str | None = None, str | None = None) -> str:
    """
    脱敏敏感数据

    Args:
        data: 原始数据
        patterns: 敏感模式字典 {pattern: replacement}

    Returns:
        str: 脱敏后的数据

    Examples:
        >>> mask_sensitive_data("API key: sk-1234567890")
        'API key: sk-****7890'
    """
    if not data:
        return data

    # 默认敏感模式
    default_patterns: dict[str, str] = {
        # API密钥模式 (sk-xxx, api-key-xxx)
        r"\bsk-[a-zA-Z0-9]{20,}\b": "sk-***",
        r'\bapi[_-]?key["\']?\s*[:=]\s*["\']?[a-zA-Z0-9]{20,}["\']?': "api_key=***",
        r"\bBearer\s+[a-zA-Z0-9]{20,}\b": "Bearer ***",
        # 密码模式
        r'\bpassword["\']?\s*[:=]\s*["\']?[^"\'\s]+["\']?': "password=***",
        # Token模式
        r'\btoken["\']?\s*[:=]\s*["\']?[a-zA-Z0-9]{20,}["\']?': "token=***",
    }

    patterns_to_use = {**default_patterns, **(patterns or {})}

    masked_data = data
    for pattern, replacement in patterns_to_use.items():
        masked_data = re.sub(pattern, replacement, masked_data, flags=re.IGNORECASE)

    return masked_data


def safe_log_request(
    message: str, request_data: dict[str, Any, exclude_fields: list | None = None
) -> str:
    """
    安全地记录请求数据(脱敏敏感信息)

    Args:
        message: 日志消息
        request_data: 请求数据
        exclude_fields: 需要排除的字段列表

    Returns:
        str: 脱敏后的日志内容
    """
    # 默认排除的敏感字段
    default_exclude_fields = {
        "api_key",
        "apikey",
        "api-key",
        "password",
        "token",
        "secret",
        "authorization",
        "bearer",
        "credentials",
    }

    exclude_fields_set = set(exclude_fields or []) | default_exclude_fields

    # 复制数据以避免修改原始数据
    safe_data = {}
    for key, value in request_data.items():
        if key.lower() in exclude_fields_set:
            # 对敏感字段进行脱敏
            if isinstance(value, str) and len(value) > 8:
                safe_data[key] = mask_api_key(value)
            else:
                safe_data[key] = "***"
        else:
            safe_data[key] = value

    # 格式化日志消息
    log_parts = [message]
    for key, value in safe_data.items():
        log_parts.append(f"{key}={value}")

    return " ".join(log_parts)


def validate_api_key(api_key: str) -> bool:
    """
    验证API密钥格式

    Args:
        api_key: API密钥

    Returns:
        bool: 是否有效

    Examples:
        >>> validate_api_key("sk-1234567890abcdef")
        True
        >>> validate_api_key("")
        False
    """
    if not api_key:
        return False

    # 检查最小长度
    if len(api_key) < 10:
        return False

    # 检查常见API密钥模式
    patterns = [
        r"^sk-[a-zA-Z0-9]{20,}$",  # OpenAI/DeepSeek格式
        r"^[0-9a-f]{32,}$",  # 32位hex格式
        r"^[0-9a-f]{40,}$",  # 40位hex格式
        r"^[a-zA-Z0-9_-]{20,}$",  # 通用格式
    ]

    return any(re.match(pattern, api_key) for pattern in patterns)


def sanitize_log_message(message: str) -> str:
    """
    清理日志消息中的敏感信息

    Args:
        message: 原始日志消息

    Returns:
        str: 清理后的日志消息
    """
    return mask_sensitive_data(message)


class SensitiveDataFilter(logging.Filter):
    """
    日志过滤器 - 自动脱敏敏感信息
    """

    def filter(self, record):
        """
        过滤日志记录

        Args:
            record: 日志记录

        Returns:
            logging.LogRecord: 过滤后的日志记录
        """
        if record.msg:
            record.msg = sanitize_log_message(str(record.msg))
        if record.args:
            record.args = tuple(
                sanitize_log_message(str(arg)) if isinstance(arg, str) else arg
                for arg in record.args
            )
        return record


# 添加敏感数据过滤器到根日志记录器
def setup_sensitive_data_filter():
    """设置敏感数据过滤器到根日志记录器"""
    filter = SensitiveDataFilter()
    logging.getLogger().addFilter(filter)
    logger.info("✅ 敏感数据过滤器已安装到根日志记录器")
