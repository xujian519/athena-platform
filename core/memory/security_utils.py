#!/usr/bin/env python3
from __future__ import annotations
"""
安全工具模块

提供路径验证、输入验证和敏感数据保护功能。

Author: Athena平台团队
Created: 2026-01-20
Version: v1.0.0
"""

import hashlib
import logging
import re
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class SecurityError(Exception):
    """安全异常"""
    pass


class PathValidator:
    """
    路径验证器

    防止路径遍历攻击，确保文件操作在允许的范围内。
    """

    # 危险路径模式
    DANGEROUS_PATTERNS = [
        r'\.\./',      # 父目录遍历
        r'\.\.\*',     # 父目录遍历（带通配符）
        r'~',          # 主目录
        r'\$[A-Za-z_]' # 环境变量
    ]

    def __init__(self, allowed_base_dirs: set[Path]):
        """
        初始化路径验证器

        Args:
            allowed_base_dirs: 允许的基础目录集合
        """
        self.allowed_base_dirs = {
            p.resolve() if isinstance(p, Path) else Path(p).resolve()
            for p in allowed_base_dirs
        }

    def validate_path(self, file_path: Any, must_exist: bool = False) -> Path:
        """
        验证并规范化路径

        Args:
            file_path: 要验证的路径（str或Path）
            must_exist: 路径是否必须存在

        Returns:
            规范化后的Path对象

        Raises:
            SecurityError: 路径不安全或超出允许范围
        """
        # 转换为Path对象
        if not isinstance(file_path, (str, Path)):
            raise SecurityError(f"无效的路径类型: {type(file_path)}")

        path = Path(file_path)

        # 检查危险模式
        path_str = str(path)
        for pattern in self.DANGEROUS_PATTERNS:
            if re.search(pattern, path_str):
                raise SecurityError(
                    f"路径包含危险模式 '{pattern}': {file_path}"
                )

        # 规范化路径（解析..和.）
        try:
            resolved_path = path.resolve()
        except (OSError, RuntimeError) as e:
            raise SecurityError(f"无法解析路径: {e}") from e

        # 检查是否在允许的基础目录内
        is_allowed = False
        for base_dir in self.allowed_base_dirs:
            try:
                # 检查resolved_path是否在base_dir内
                resolved_path.relative_to(base_dir)
                is_allowed = True
                break
            except ValueError:
                # 不在这个base_dir内，继续检查下一个
                continue

        if not is_allowed:
            raise SecurityError(
                f"路径超出允许范围: {resolved_path}\n"
                f"允许的目录: {[str(d) for d in self.allowed_base_dirs]}"
            )

        # 检查路径是否存在（如果要求）
        if must_exist and not resolved_path.exists():
            raise SecurityError(f"路径不存在: {resolved_path}")

        return resolved_path

    def safe_open(
        self,
        file_path: Any,
        mode: str = 'r',
        **kwargs
    ) -> Any:
        """
        安全打开文件

        Args:
            file_path: 文件路径
            mode: 打开模式
            **kwargs: 传递给open()的其他参数

        Returns:
            文件对象

        Raises:
            SecurityError: 路径不安全
        """
        validated_path = self.validate_path(file_path)
        return open(validated_path, mode, **kwargs)


class InputValidator:
    """
    输入验证器

    验证外部输入，防止注入攻击。
    """

    # 最大长度限制
    MAX_STRING_LENGTH = 10_000
    MAX_PATTERN_LENGTH = 100

    # 危险字符模式
    DANGEROUS_CHARS = {
        '\x00': '空字节',
        '\r': '回车符',
        '\n': '换行符',
        '\t': '制表符'
    }

    def __init__(self):
        """初始化输入验证器"""
        self.logger = logger

    def validate_string(
        self,
        value: Any,
        field_name: str = "value",
        max_length: Optional[int] = None,
        allow_empty: bool = False,
        dangerous_chars: bool = False
    ) -> str:
        """
        验证字符串输入

        Args:
            value: 要验证的值
            field_name: 字段名（用于错误消息）
            max_length: 最大长度
            allow_empty: 是否允许空字符串
            dangerous_chars: 是否允许危险字符

        Returns:
            验证后的字符串

        Raises:
            SecurityError: 验证失败
        """
        max_length = max_length or self.MAX_STRING_LENGTH

        # 检查类型
        if not isinstance(value, str):
            raise SecurityError(
                f"{field_name}: 必须是字符串类型, 实际: {type(value)}"
            )

        # 检查长度
        if len(value) > max_length:
            raise SecurityError(
                f"{field_name}: 长度超限 ({len(value)} > {max_length})"
            )

        # 检查空值
        if not allow_empty and not value.strip():
            raise SecurityError(f"{field_name}: 不能为空")

        # 检查危险字符
        if not dangerous_chars:
            for char, name in self.DANGEROUS_CHARS.items():
                if char in value:
                    raise SecurityError(
                        f"{field_name}: 包含危险字符 '{name}' (\\x{ord(char):02x})"
                    )

        return value

    def validate_pattern_id(self, pattern_id: Any) -> str:
        """
        验证pattern_id格式

        Args:
            pattern_id: pattern ID

        Returns:
            验证后的pattern_id

        Raises:
            SecurityError: 格式无效
        """
        pattern_id = self.validate_string(
            pattern_id,
            field_name="pattern_id",
            max_length=self.MAX_PATTERN_LENGTH,
            allow_empty=False
        )

        # pattern_id应该只包含安全字符
        if not re.match(r'^[a-zA-Z0-9_-]+$', pattern_id):
            raise SecurityError(
                f"pattern_id格式无效: {pattern_id}. "
                f"只允许字母、数字、下划线和连字符"
            )

        return pattern_id

    def validate_file_name(self, file_name: Any) -> str:
        """
        验证文件名

        Args:
            file_name: 文件名

        Returns:
            验证后的文件名

        Raises:
            SecurityError: 文件名无效
        """
        file_name = self.validate_string(
            file_name,
            field_name="file_name",
            max_length=255,
            allow_empty=False
        )

        # 检查危险字符
        dangerous_chars = {'/', '\\', ':', '*', '?', '"', '<', '>', '|', '\x00'}
        for char in dangerous_chars:
            if char in file_name:
                raise SecurityError(
                    f"文件名包含非法字符 '{char}': {file_name}"
                )

        # 检查保留名称（Windows）
        reserved_names = {
            'CON', 'PRN', 'AUX', 'NUL',
            'COM1', 'COM2', 'COM3', 'COM4', 'COM5', 'COM6', 'COM7', 'COM8', 'COM9',
            'LPT1', 'LPT2', 'LPT3', 'LPT4', 'LPT5', 'LPT6', 'LPT7', 'LPT8', 'LPT9'
        }
        name_without_ext = file_name.split('.')[0].upper()
        if name_without_ext in reserved_names:
            raise SecurityError(f"文件名是保留名称: {file_name}")

        return file_name


class SensitiveDataFilter(logging.Filter):
    """
    敏感数据过滤器

    防止敏感信息被记录到日志中。
    """

    # 敏感数据模式
    SENSITIVE_PATTERNS = [
        (r'password["\']?\s*[:=]\s*["\']?[^"\'}\s]+', 'password=***'),
        (r'api_key["\']?\s*[:=]\s*["\']?[^"\'}\s]+', 'api_key=***'),
        (r'token["\']?\s*[:=]\s*["\']?[^"\'}\s]+', 'token=***'),
        (r'secret["\']?\s*[:=]\s*["\']?[^"\'}\s]+', 'secret=***'),
        (r'Bearer\s+[A-Za-z0-9\-._~+/]+=*', 'Bearer ***'),
        # Email地址
        (r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', '***@***.***'),
        # IP地址（可选，根据需求）
        (r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b', '***.***.***.***'),
    ]

    def filter(self, record: logging.LogRecord) -> bool:
        """
        过滤日志记录中的敏感数据

        Args:
            record: 日志记录

        Returns:
            True表示记录应该被记录
        """
        if hasattr(record, 'msg') and isinstance(record.msg, str):
            record.msg = self._filter_sensitive(record.msg)

        if hasattr(record, 'args') and record.args:
            new_args = []
            for arg in record.args:
                if isinstance(arg, str):
                    new_args.append(self._filter_sensitive(arg))
                else:
                    new_args.append(arg)
            record.args = tuple(new_args)

        return True

    def _filter_sensitive(self, text: str) -> str:
        """过滤文本中的敏感数据"""
        for pattern, replacement in self.SENSITIVE_PATTERNS:
            text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)
        return text


def hash_sensitive_data(data: str, salt: str = "") -> str:
    """
    对敏感数据进行哈希，用于日志记录

    Args:
        data: 敏感数据
        salt: 盐值

    Returns:
        哈希值（前8位）
    """
    if not data:
        return "***"

    salted = f"{salt}{data}"
    hash_value = hashlib.sha256(salted.encode()).hexdigest()
    return f"<hash:{hash_value[:8]}...>"


__all__ = [
    'InputValidator',
    'PathValidator',
    'SecurityError',
    'SensitiveDataFilter',
    'hash_sensitive_data'
]
