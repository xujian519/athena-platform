#!/usr/bin/env python3
"""
基础验证器 - Phase 3.1安全加固

Base Context Validator - 提供IContextValidator接口的基础实现

核心功能:
- 实现IContextValidator接口
- 提供验证错误和安全问题的数据结构
- 支持验证链和组合验证

作者: Athena平台团队
创建时间: 2026-04-24
版本: v3.1.0
"""

import logging
from abc import abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional

from ..interfaces import IContext, IContextValidator

logger = logging.getLogger(__name__)


@dataclass
class ValidationError:
    """
    验证错误

    Attributes:
        field: 字段名
        message: 错误消息
        code: 错误代码
        value: 导致错误的值
    """

    field: str
    message: str
    code: str
    value: Any = None
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "field": self.field,
            "message": self.message,
            "code": self.code,
            "value": str(self.value) if self.value is not None else None,
            "timestamp": self.timestamp,
        }

    def __str__(self) -> str:
        return f"ValidationError({self.field}: {self.message})"


@dataclass
class SecurityIssue:
    """
    安全问题

    Attributes:
        severity: 严重程度 (critical/high/medium/low/info)
        category: 安全类别 (sql_injection/xss/command_injection/path_traversal等)
        description: 问题描述
        evidence: 证据（导致问题的输入）
        location: 位置信息
        recommendation: 修复建议
    """

    severity: str
    category: str
    description: str
    evidence: str
    location: Optional[str] = None
    recommendation: Optional[str] = None
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

    # 严重程度等级
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"

    # 安全类别
    SQL_INJECTION = "sql_injection"
    XSS = "xss"
    COMMAND_INJECTION = "command_injection"
    PATH_TRAVERSAL = "path_traversal"
    LDAP_INJECTION = "ldap_injection"
    NOSQL_INJECTION = "nosql_injection"
    SSRF = "ssrf"
    XXE = "xxe"

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "severity": self.severity,
            "category": self.category,
            "description": self.description,
            "evidence": self.evidence,
            "location": self.location,
            "recommendation": self.recommendation,
            "timestamp": self.timestamp,
        }

    def __str__(self) -> str:
        return f"SecurityIssue[{self.severity}]({self.category}: {self.description})"

    @classmethod
    def get_severity_level(cls, severity: str) -> int:
        """
        获取严重程度等级（数字越大越严重）

        Args:
            severity: 严重程度字符串

        Returns:
            int: 严重程度等级 (0-4)
        """
        levels = {
            cls.INFO: 0,
            cls.LOW: 1,
            cls.MEDIUM: 2,
            cls.HIGH: 3,
            cls.CRITICAL: 4,
        }
        return levels.get(severity.lower(), 0)


class BaseContextValidator(IContextValidator):
    """
    基础上下文验证器

    提供IContextValidator接口的基础实现：
    - 验证错误收集
    - 安全问题收集
    - 验证链支持
    """

    def __init__(
        self,
        validator_name: str,
        strict_mode: bool = False,
        fail_fast: bool = False,
    ):
        """
        初始化基础验证器

        Args:
            validator_name: 验证器名称
            strict_mode: 严格模式（任何警告都视为错误）
            fail_fast: 快速失败（发现第一个问题就停止）
        """
        self._name = validator_name
        self._strict_mode = strict_mode
        self._fail_fast = fail_fast
        self._validation_errors: List[ValidationError] = []
        self._security_issues: List[SecurityIssue] = []

        logger.info(f"✅ 验证器初始化: {validator_name} (strict={strict_mode}, fail_fast={fail_fast})")

    @property
    def validator_name(self) -> str:
        """验证器名称"""
        return self._name

    @property
    def validation_errors(self) -> List[ValidationError]:
        """验证错误列表"""
        return self._validation_errors.copy()

    @property
    def security_issues(self) -> List[SecurityIssue]:
        """安全问题列表"""
        return self._security_issues.copy()

    def clear_errors(self) -> None:
        """清空错误列表"""
        self._validation_errors.clear()
        self._security_issues.clear()

    def add_error(self, error: ValidationError) -> None:
        """
        添加验证错误

        Args:
            error: 验证错误
        """
        self._validation_errors.append(error)
        logger.debug(f"➕ 验证错误: {error}")

    def add_security_issue(self, issue: SecurityIssue) -> None:
        """
        添加安全问题

        Args:
            issue: 安全问题
        """
        self._security_issues.append(issue)
        logger.warning(f"⚠️ 安全问题: {issue}")

    def has_errors(self) -> bool:
        """是否有验证错误"""
        return len(self._validation_errors) > 0

    def has_security_issues(self) -> bool:
        """是否有安全问题"""
        return len(self._security_issues) > 0

    def has_critical_issues(self) -> bool:
        """是否有严重安全问题"""
        return any(
            issue.severity == SecurityIssue.CRITICAL for issue in self._security_issues
        )

    def get_critical_issues(self) -> List[SecurityIssue]:
        """获取严重安全问题"""
        return [
            issue for issue in self._security_issues
            if issue.severity == SecurityIssue.CRITICAL
        ]

    def get_high_severity_issues(self) -> List[SecurityIssue]:
        """获取高危安全问题"""
        return [
            issue for issue in self._security_issues
            if issue.severity in [SecurityIssue.CRITICAL, SecurityIssue.HIGH]
        ]

    async def validate(self, context: IContext) -> bool:
        """
        验证上下文数据

        Args:
            context: 待验证的上下文对象

        Returns:
            bool: 验证通过返回True
        """
        self.clear_errors()

        try:
            # 调用子类实现的验证逻辑
            await self._validate_context(context)

            # 在严格模式下，任何安全问题都是验证失败
            if self._strict_mode and self.has_security_issues():
                return False

            return not self.has_errors()

        except Exception as e:
            logger.error(f"❌ 验证过程中发生异常: {e}")
            self.add_error(ValidationError(
                field="validation",
                message=f"验证过程异常: {str(e)}",
                code="VALIDATION_EXCEPTION",
            ))
            return False

    async def security_check(self, context: IContext) -> List[str]:
        """
        执行安全检查

        Args:
            context: 待检查的上下文对象

        Returns:
            List[str]: 发现的安全问题描述列表
        """
        self.clear_errors()

        try:
            # 调用子类实现的安全检查逻辑
            await self._security_check_context(context)

            # 返回安全问题描述列表
            return [str(issue) for issue in self._security_issues]

        except Exception as e:
            logger.error(f"❌ 安全检查过程中发生异常: {e}")
            return [f"安全检查异常: {str(e)}"]

    @abstractmethod
    async def _validate_context(self, context: IContext) -> None:
        """
        执行具体的验证逻辑（子类实现）

        Args:
            context: 待验证的上下文对象
        """
        pass

    @abstractmethod
    async def _security_check_context(self, context: IContext) -> None:
        """
        执行具体的安全检查逻辑（子类实现）

        Args:
            context: 待检查的上下文对象
        """
        pass

    def get_validation_report(self) -> Dict[str, Any]:
        """
        获取验证报告

        Returns:
            Dict: 验证报告
        """
        critical_count = sum(1 for i in self._security_issues if i.severity == SecurityIssue.CRITICAL)
        high_count = sum(1 for i in self._security_issues if i.severity == SecurityIssue.HIGH)
        medium_count = sum(1 for i in self._security_issues if i.severity == SecurityIssue.MEDIUM)
        low_count = sum(1 for i in self._security_issues if i.severity == SecurityIssue.LOW)

        return {
            "validator": self._name,
            "timestamp": datetime.now().isoformat(),
            "validation_errors": [e.to_dict() for e in self._validation_errors],
            "security_issues": [i.to_dict() for i in self._security_issues],
            "summary": {
                "total_errors": len(self._validation_errors),
                "total_security_issues": len(self._security_issues),
                "critical_issues": critical_count,
                "high_issues": high_count,
                "medium_issues": medium_count,
                "low_issues": low_count,
                "has_errors": self.has_errors(),
                "has_security_issues": self.has_security_issues(),
                "has_critical_issues": self.has_critical_issues(),
            },
        }


__all__ = [
    "BaseContextValidator",
    "ValidationError",
    "SecurityIssue",
]
