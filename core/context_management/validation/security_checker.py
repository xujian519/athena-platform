#!/usr/bin/env python3
"""
安全检查器 - Phase 3.1安全加固

Security Checker - 检测各种恶意输入和注入攻击

核心功能:
- SQL注入检测
- XSS攻击检测
- 命令注入检测
- 路径遍历检测
- LDAP注入检测
- NoSQL注入检测
- 输入清理和转义

安全目标:
- 检测100%的常见SQL注入模式
- 检测100%的常见XSS攻击向量
- 检测95%以上的命令注入模式
- 检测100%的路径遍历攻击

作者: Athena平台团队
创建时间: 2026-04-24
版本: v3.1.0
"""

import html
import logging
import re
import string
from typing import Any, Dict, List, Optional, Set, Tuple

from .base_validator import BaseContextValidator, SecurityIssue

logger = logging.getLogger(__name__)


class SecurityChecker(BaseContextValidator):
    """
    安全检查器

    检测各种恶意输入和注入攻击：
    - SQL注入（基于模式匹配）
    - XSS攻击（基于危险标签和属性）
    - 命令注入（基于Shell元字符）
    - 路径遍历（基于路径模式）
    - LDAP注入（基于LDAP特殊字符）
    - NoSQL注入（基于NoSQL操作符）
    """

    # SQL注入关键字和模式
    SQL_KEYWORDS: Set[str] = {
        "SELECT", "INSERT", "UPDATE", "DELETE", "DROP", "UNION",
        "EXEC", "EXECUTE", "CREATE", "ALTER", "TRUNCATE", "GRANT",
        "REVOKE", "DECLARE", "SCRIPT", "JAVASCRIPT", "VBSCRIPT",
    }

    SQL_COMMENT_PATTERNS: Set[str] = {"--", "#", "/*", "*/", ";"}

    SQL_INJECTION_PATTERNS = [
        # 经典SQL注入（修复以匹配带引号的值）
        r"'.*\sOR\s+.*=.*",  # ' OR '1'='1' 模式
        r"'.*\sAND\s+.*=.*",  # ' AND '1'='1' 模式
        r"'\s*(OR|AND)\s+\w+\s*=\s*\w+",  # ' OR 1=1 模式
        r"'\s*(OR|AND)\s+\w+\s*!=\s*\w+",  # ' OR 1!=2
        r"'\s*(OR|AND)\s+\w+\s*<>\s*\w+",  # ' OR 1<>2
        r"'\s*(OR|AND)\s+\w+\s*<\s*\w+",  # ' OR 1<2
        r"'\s*(OR|AND)\s+\w+\s*>\s*\w+",  # ' OR 1>2
        # 时间盲注
        r"WAITFOR\s+DELAY",
        r"SLEEP\s*\(",
        r"BENCHMARK\s*\(",
        # 堆叠查询
        r";\s*DROP",
        r";\s*DELETE",
        r";\s*INSERT",
        r";\s*UPDATE",
        # Union攻击
        r"UNION\s+ALL\s+SELECT",
        r"UNION\s+SELECT",
        # Hex编码
        r"0x[0-9a-fA-F]+",
    ]

    # XSS危险标签和属性
    XSS_DANGEROUS_TAGS: Set[str] = {
        "script", "iframe", "object", "embed", "form",
        "input", "button", "link", "meta", "style",
    }

    XSS_DANGEROUS_EVENTS: Set[str] = {
        "onerror", "onload", "onclick", "onmouseover", "onmouseout",
        "onfocus", "onblur", "onkeydown", "onkeypress", "onkeyup",
        "onsubmit", "onreset", "onchange", "onselect",
    }

    XSS_PATTERNS = [
        r"<\s*script[^>]*>.*?<\s*/\s*script\s*>",
        r"javascript:",
        r"vbscript:",
        r"data:text/html",
        r"on\w+\s*=",
        r"<\s*iframe",
        r"<\s*object",
        r"<\s*embed",
        r"fromCharCode",
        r"&#x",
        r"&#\d+",
    ]

    # 命令注入元字符
    COMMAND_META_CHARS: Set[str] = {
        ";", "|", "&", "$", "`", "\n",
        "(", ")", "{", "}", "[", "]", ">", "<",
    }

    COMMAND_INJECTION_PATTERNS = [
        r";\s*\w+\s+",  # ; command
        r"\|\s*\w+\s+",  # | command
        r"&&\s*\w+\s+",  # && command
        r"\|\|\s*\w+\s+",  # || command
        r"`[^`]*`",  # `command`
        r"\$\([^)]*\)",  # $(command)
        r"\{[^}]*\}",  # {command}
    ]

    # 路径遍历模式
    PATH_TRAVERSAL_PATTERNS = [
        r"\.\./",
        r"\.\.\\",
        r"\.\.%5c",
        r"\.\.%2f",
        r"\.\.%252f",
        r"%2e%2e",
        r"%252e%252e",
        r"~.*?/",
    ]

    # LDAP注入特殊字符
    LDAP_SPECIAL_CHARS: Set[str] = {
        "*", "(", ")", "\\", "NUL", "="
    }

    LDAP_INJECTION_PATTERNS = [
        r"\*\)\([^)]*",
        r"\([a-zA-Z]*\*",
        r"\([a-zA-Z]*=[^)]*\)\([a-zA-Z]*",
        r"!\([^)]*\)",
        r"\|\([^)]*\)",
    ]

    # NoSQL注入操作符
    NOSQL_OPERATORS: Set[str] = {
        "$where", "$ne", "$gt", "$lt", "$gte", "$lte",
        "$in", "$nin", "$regex", "$exists", "$or",
        "$and", "$not", "$nor", "$elemMatch",
    }

    NOSQL_INJECTION_PATTERNS = [
        r"\$where\s*:",
        r"\$ne\s*:",
        r"\$regex\s*:",
        r"function\s*\(",
        r"return\s+this\.",
    ]

    def __init__(
        self,
        enable_sql_check: bool = True,
        enable_xss_check: bool = True,
        enable_command_check: bool = True,
        enable_path_check: bool = True,
        enable_ldap_check: bool = True,
        enable_nosql_check: bool = True,
        **kwargs
    ):
        """
        初始化安全检查器

        Args:
            enable_sql_check: 启用SQL注入检测
            enable_xss_check: 启用XSS检测
            enable_command_check: 启用命令注入检测
            enable_path_check: 启用路径遍历检测
            enable_ldap_check: 启用LDAP注入检测
            enable_nosql_check: 启用NoSQL注入检测
            **kwargs: 其他参数传递给基类
        """
        super().__init__(validator_name="SecurityChecker", **kwargs)

        self._enable_sql_check = enable_sql_check
        self._enable_xss_check = enable_xss_check
        self._enable_command_check = enable_command_check
        self._enable_path_check = enable_path_check
        self._enable_ldap_check = enable_ldap_check
        self._enable_nosql_check = enable_nosql_check

        # 编译所有正则表达式
        self._sql_patterns = [re.compile(p, re.IGNORECASE) for p in self.SQL_INJECTION_PATTERNS]
        self._xss_patterns = [re.compile(p, re.IGNORECASE | re.DOTALL) for p in self.XSS_PATTERNS]
        self._command_patterns = [re.compile(p, re.IGNORECASE) for p in self.COMMAND_INJECTION_PATTERNS]
        self._path_patterns = [re.compile(p, re.IGNORECASE) for p in self.PATH_TRAVERSAL_PATTERNS]
        self._ldap_patterns = [re.compile(p, re.IGNORECASE) for p in self.LDAP_INJECTION_PATTERNS]
        self._nosql_patterns = [re.compile(p, re.IGNORECASE) for p in self.NOSQL_INJECTION_PATTERNS]

        logger.info(
            f"✅ 安全检查器初始化: "
            f"SQL={enable_sql_check}, XSS={enable_xss_check}, "
            f"CMD={enable_command_check}, PATH={enable_path_check}, "
            f"LDAP={enable_ldap_check}, NoSQL={enable_nosql_check}"
        )

    async def _validate_context(self, context) -> None:
        """
        安全检查器不执行数据验证（由SchemaValidator负责）

        Args:
            context: 待验证的上下文对象
        """
        pass

    async def _security_check_context(self, context) -> None:
        """
        执行安全检查

        Args:
            context: 待检查的上下文对象
        """
        # 获取上下文数据字典
        data = context.to_dict() if hasattr(context, 'to_dict') else context.__dict__

        # 递归检查所有字符串值
        await self._check_data(data, path="root")

    async def _check_data(self, data: Any, path: str) -> None:
        """
        递归检查数据

        Args:
            data: 待检查的数据
            path: 数据路径
        """
        if isinstance(data, str):
            await self._check_string(data, path)
        elif isinstance(data, dict):
            for key, value in data.items():
                new_path = f"{path}.{key}"
                await self._check_data(value, new_path)
        elif isinstance(data, (list, tuple)):
            for i, item in enumerate(data):
                new_path = f"{path}[{i}]"
                await self._check_data(item, new_path)

    async def _check_string(self, value: str, path: str) -> None:
        """
        检查字符串值

        Args:
            value: 字符串值
            path: 数据路径
        """
        # SQL注入检测
        if self._enable_sql_check:
            await self._check_sql_injection(value, path)

        # XSS检测
        if self._enable_xss_check:
            await self._check_xss(value, path)

        # 命令注入检测
        if self._enable_command_check:
            await self._check_command_injection(value, path)

        # 路径遍历检测
        if self._enable_path_check:
            await self._check_path_traversal(value, path)

        # LDAP注入检测
        if self._enable_ldap_check:
            await self._check_ldap_injection(value, path)

        # NoSQL注入检测
        if self._enable_nosql_check:
            await self._check_nosql_injection(value, path)

    async def _check_sql_injection(self, value: str, path: str) -> None:
        """
        检测SQL注入

        Args:
            value: 字符串值
            path: 数据路径
        """
        # 首先检查SQL注入模式（这些更精确）
        for pattern in self._sql_patterns:
            if pattern.search(value):
                self.add_security_issue(SecurityIssue(
                    severity=SecurityIssue.CRITICAL,
                    category=SecurityIssue.SQL_INJECTION,
                    description=f"检测到SQL注入模式",
                    evidence=value,
                    location=path,
                    recommendation="使用参数化查询或ORM",
                ))
                if self._fail_fast:
                    return

        upper_value = value.upper()

        # 检查SQL关键字
        for keyword in self.SQL_KEYWORDS:
            if keyword in upper_value:
                # 确保是完整的单词（而不是部分匹配）
                pattern = r'\b' + keyword + r'\b'
                if re.search(pattern, upper_value):
                    self.add_security_issue(SecurityIssue(
                        severity=SecurityIssue.HIGH,
                        category=SecurityIssue.SQL_INJECTION,
                        description=f"检测到SQL关键字: {keyword}",
                        evidence=value,
                        location=path,
                        recommendation="移除SQL关键字或使用参数化查询",
                    ))
                    if self._fail_fast:
                        return

        # 检查SQL注释
        for comment in self.SQL_COMMENT_PATTERNS:
            if comment in value:
                self.add_security_issue(SecurityIssue(
                    severity=SecurityIssue.HIGH,
                    category=SecurityIssue.SQL_INJECTION,
                    description=f"检测到SQL注释: {comment}",
                    evidence=value,
                    location=path,
                    recommendation="移除SQL注释字符",
                ))
                if self._fail_fast:
                    return

    async def _check_xss(self, value: str, path: str) -> None:
        """
        检测XSS攻击

        Args:
            value: 字符串值
            path: 数据路径
        """
        lower_value = value.lower()

        # 检查危险标签
        for tag in self.XSS_DANGEROUS_TAGS:
            if f"<{tag}" in lower_value or f"</{tag}" in lower_value:
                self.add_security_issue(SecurityIssue(
                    severity=SecurityIssue.HIGH,
                    category=SecurityIssue.XSS,
                    description=f"检测到危险HTML标签: {tag}",
                    evidence=value,
                    location=path,
                    recommendation="使用HTML实体编码或白名单过滤",
                ))
                if self._fail_fast:
                    return

        # 检查危险事件
        for event in self.XSS_DANGEROUS_EVENTS:
            if event in lower_value:
                self.add_security_issue(SecurityIssue(
                    severity=SecurityIssue.MEDIUM,
                    category=SecurityIssue.XSS,
                    description=f"检测到危险事件处理器: {event}",
                    evidence=value,
                    location=path,
                    recommendation="移除事件处理器或使用CSP",
                ))
                if self._fail_fast:
                    return

        # 检查XSS模式
        for pattern in self._xss_patterns:
            if pattern.search(value):
                self.add_security_issue(SecurityIssue(
                    severity=SecurityIssue.HIGH,
                    category=SecurityIssue.XSS,
                    description=f"检测到XSS攻击模式",
                    evidence=value,
                    location=path,
                    recommendation="使用HTML实体编码",
                ))
                if self._fail_fast:
                    return

    async def _check_command_injection(self, value: str, path: str) -> None:
        """
        检测命令注入

        Args:
            value: 字符串值
            path: 数据路径
        """
        # 检查Shell元字符
        for char in self.COMMAND_META_CHARS:
            if char in value:
                # 检查是否在命令上下文中
                if char in [";", "|", "&", "`", "$", ">", "<", "\n", "\r"]:
                    self.add_security_issue(SecurityIssue(
                        severity=SecurityIssue.HIGH,
                        category=SecurityIssue.COMMAND_INJECTION,
                        description=f"检测到Shell元字符: {repr(char)}",
                        evidence=value,
                        location=path,
                        recommendation="避免直接执行Shell命令，使用subprocess列表参数",
                    ))
                    if self._fail_fast:
                        return

        # 检查命令注入模式
        for pattern in self._command_patterns:
            if pattern.search(value):
                self.add_security_issue(SecurityIssue(
                    severity=SecurityIssue.CRITICAL,
                    category=SecurityIssue.COMMAND_INJECTION,
                    description=f"检测到命令注入模式",
                    evidence=value,
                    location=path,
                    recommendation="使用白名单验证，避免Shell解释",
                ))
                if self._fail_fast:
                    return

    async def _check_path_traversal(self, value: str, path: str) -> None:
        """
        检测路径遍历攻击

        Args:
            value: 字符串值
            path: 数据路径
        """
        # 检查路径遍历模式
        for pattern in self._path_patterns:
            if pattern.search(value):
                self.add_security_issue(SecurityIssue(
                    severity=SecurityIssue.CRITICAL,
                    category=SecurityIssue.PATH_TRAVERSAL,
                    description=f"检测到路径遍历攻击",
                    evidence=value,
                    location=path,
                    recommendation="使用白名单验证路径，避免直接拼接",
                ))
                if self._fail_fast:
                    return

        # 检查绝对路径（可能泄露系统信息）
        windows_drives = ("C:", "D:", "E:", "F:", "G:")
        if value.startswith(("/", "\\")) or value.startswith(windows_drives):
            self.add_security_issue(SecurityIssue(
                severity=SecurityIssue.MEDIUM,
                category=SecurityIssue.PATH_TRAVERSAL,
                description=f"检测到绝对路径",
                evidence=value,
                location=path,
                recommendation="使用相对路径或路径白名单",
            ))

    async def _check_ldap_injection(self, value: str, path: str) -> None:
        """
        检测LDAP注入

        Args:
            value: 字符串值
            path: 数据路径
        """
        # 检查LDAP特殊字符
        for char in self.LDAP_SPECIAL_CHARS:
            if char in value:
                # 检查是否在注入上下文中
                if char == "*" and ("*" in value and "(" in value):
                    self.add_security_issue(SecurityIssue(
                        severity=SecurityIssue.MEDIUM,
                        category=SecurityIssue.LDAP_INJECTION,
                        description=f"检测到LDAP特殊字符: {repr(char)}",
                        evidence=value,
                        location=path,
                        recommendation="使用LDAP转义或白名单验证",
                    ))
                    if self._fail_fast:
                        return

        # 检查LDAP注入模式
        for pattern in self._ldap_patterns:
            if pattern.search(value):
                self.add_security_issue(SecurityIssue(
                    severity=SecurityIssue.HIGH,
                    category=SecurityIssue.LDAP_INJECTION,
                    description=f"检测到LDAP注入模式",
                    evidence=value,
                    location=path,
                    recommendation="使用LDAP过滤器转义",
                ))
                if self._fail_fast:
                    return

    async def _check_nosql_injection(self, value: str, path: str) -> None:
        """
        检测NoSQL注入

        Args:
            value: 字符串值
            path: 数据路径
        """
        # 检查NoSQL操作符
        for operator in self.NOSQL_OPERATORS:
            if operator in value:
                self.add_security_issue(SecurityIssue(
                    severity=SecurityIssue.HIGH,
                    category=SecurityIssue.NOSQL_INJECTION,
                    description=f"检测到NoSQL操作符: {operator}",
                    evidence=value,
                    location=path,
                    recommendation="避免直接使用用户输入构建查询",
                ))
                if self._fail_fast:
                    return

        # 检查NoSQL注入模式
        for pattern in self._nosql_patterns:
            if pattern.search(value):
                self.add_security_issue(SecurityIssue(
                    severity=SecurityIssue.CRITICAL,
                    category=SecurityIssue.NOSQL_INJECTION,
                    description=f"检测到NoSQL注入模式",
                    evidence=value,
                    location=path,
                    recommendation="使用类型安全的查询构建器",
                ))
                if self._fail_fast:
                    return

    # 工具方法

    @staticmethod
    def sanitize_html(value: str) -> str:
        """
        清理HTML，转义危险字符

        Args:
            value: 输入字符串

        Returns:
            str: 清理后的字符串
        """
        return html.escape(value, quote=True)

    @staticmethod
    def sanitize_filename(value: str) -> str:
        """
        清理文件名，移除危险字符

        Args:
            value: 输入字符串

        Returns:
            str: 清理后的文件名
        """
        # 移除路径遍历字符
        value = value.replace("..", "")
        value = value.replace("/", "")
        value = value.replace("\\", "")

        # 移除特殊字符
        allowed_chars = string.ascii_letters + string.digits + "._-"
        return "".join(c for c in value if c in allowed_chars)

    @staticmethod
    def sanitize_path(value: str, allowed_dirs: Optional[Set[str]] = None) -> str:
        """
        清理路径，防止路径遍历

        Args:
            value: 输入路径
            allowed_dirs: 允许的目录列表

        Returns:
            str: 清理后的路径
        """
        # 移除路径遍历模式
        value = value.replace("..", "")
        value = value.replace("\\", "/")

        # 标准化路径
        parts = value.split("/")
        parts = [p for p in parts if p]

        # 如果有白名单，检查路径是否在允许的目录下
        if allowed_dirs and parts:
            if parts[0] not in allowed_dirs:
                parts = []

        return "/".join(parts)


__all__ = [
    "SecurityChecker",
]
