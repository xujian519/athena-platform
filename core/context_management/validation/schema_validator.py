#!/usr/bin/env python3
"""
Schema验证器 - Phase 3.1安全加固

Schema Validator - 使用Pydantic进行Schema验证

核心功能:
- Schema验证（基于Pydantic模型）
- 类型检查（str/int/float/bool/dict/list）
- 长度限制（min_length, max_length）
- 格式验证（正则表达式：email、url、uuid等）
- 必填字段检查

作者: Athena平台团队
创建时间: 2026-04-24
版本: v3.1.0
"""

import logging
import re
import uuid
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Pattern, Set

from pydantic import BaseModel, ValidationError as PydanticValidationError

from .base_validator import BaseContextValidator, ValidationError

logger = logging.getLogger(__name__)


@dataclass
class FieldRule:
    """
    字段验证规则

    Attributes:
        field_name: 字段名
        required: 是否必填
        field_type: 期望的类型
        min_length: 最小长度（用于字符串/列表）
        max_length: 最大长度
        min_value: 最小值（用于数字）
        max_value: 最大值
        pattern: 正则表达式模式
        allowed_values: 允许的值列表
        custom_validator: 自定义验证函数
    """

    field_name: str
    required: bool = False
    field_type: Optional[type] = None
    min_length: Optional[int] = None
    max_length: Optional[int] = None
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    pattern: Optional[Pattern] = None
    allowed_values: Optional[Set[Any]] = None
    custom_validator: Optional[Callable[[Any], bool]] = None


class SchemaValidator(BaseContextValidator):
    """
    Schema验证器

    提供基于规则的Schema验证功能：
    - 字段类型检查
    - 长度限制
    - 值范围检查
    - 格式验证
    - 自定义验证
    """

    # 常用正则表达式模式
    EMAIL_PATTERN = re.compile(
        r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    )
    URL_PATTERN = re.compile(
        r'^(https?:\/\/)?'  # protocol
        r'(([a-zA-Z0-9-]+\.)+[a-zA-Z]{2,}|'  # domain
        r'localhost|'  # localhost
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # IP
        r'(:\d+)?(\/[^\s]*)?$'
    )
    UUID_PATTERN = re.compile(
        r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$',
        re.IGNORECASE
    )
    PHONE_PATTERN = re.compile(
        r'^(\+\d{1,3}[- ]?)?\d{10,15}$'
    )
    IP_ADDRESS_PATTERN = re.compile(
        r'^(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})$'
    )

    def __init__(
        self,
        field_rules: Optional[List[FieldRule]] = None,
        pydantic_model: Optional[type[BaseModel]] = None,
        **kwargs
    ):
        """
        初始化Schema验证器

        Args:
            field_rules: 字段验证规则列表
            pydantic_model: Pydantic模型（可选）
            **kwargs: 其他参数传递给基类
        """
        super().__init__(validator_name="SchemaValidator", **kwargs)

        self._field_rules: Dict[str, FieldRule] = {}
        if field_rules:
            for rule in field_rules:
                self._field_rules[rule.field_name] = rule

        self._pydantic_model = pydantic_model

        logger.info(
            f"✅ Schema验证器: {len(self._field_rules)}条规则, "
            f"Pydantic模型={'是' if pydantic_model else '否'}"
        )

    def add_rule(self, rule: FieldRule) -> None:
        """
        添加字段验证规则

        Args:
            rule: 字段规则
        """
        self._field_rules[rule.field_name] = rule
        logger.debug(f"➕ 添加规则: {rule.field_name}")

    def remove_rule(self, field_name: str) -> None:
        """
        移除字段验证规则

        Args:
            field_name: 字段名
        """
        if field_name in self._field_rules:
            del self._field_rules[field_name]
            logger.debug(f"➖ 移除规则: {field_name}")

    async def _validate_context(self, context) -> None:
        """
        验证上下文数据

        Args:
            context: 待验证的上下文对象
        """
        # 获取上下文数据字典
        data = context.to_dict() if hasattr(context, 'to_dict') else context.__dict__

        # 使用Pydantic模型验证（如果有）
        if self._pydantic_model:
            self._validate_with_pydantic(data)

        # 使用字段规则验证
        for field_name, rule in self._field_rules.items():
            await self._validate_field(data, field_name, rule)

    def _validate_with_pydantic(self, data: Dict[str, Any]) -> None:
        """
        使用Pydantic模型验证数据

        Args:
            data: 待验证的数据
        """
        if not self._pydantic_model:
            return

        try:
            self._pydantic_model(**data)
        except PydanticValidationError as e:
            # 转换Pydantic错误为ValidationError
            for error in e.errors():
                self.add_error(ValidationError(
                    field=".".join(str(loc) for loc in error['loc']),
                    message=error['msg'],
                    code=error['type'],
                    value=error.get('input'),
                ))

    async def _validate_field(
        self, data: Dict[str, Any], field_name: str, rule: FieldRule
    ) -> None:
        """
        验证单个字段

        Args:
            data: 数据字典
            field_name: 字段名
            rule: 验证规则
        """
        value = data.get(field_name)

        # 必填检查
        if rule.required and value is None:
            self.add_error(ValidationError(
                field=field_name,
                message=f"字段 '{field_name}' 是必填的",
                code="REQUIRED_FIELD_MISSING",
                value=value,
            ))
            return

        # 如果值为None且非必填，跳过其他验证
        if value is None:
            return

        # 类型检查
        if rule.field_type and not isinstance(value, rule.field_type):
            self.add_error(ValidationError(
                field=field_name,
                message=f"字段 '{field_name}' 类型错误: 期望 {rule.field_type.__name__}, 实际 {type(value).__name__}",
                code="TYPE_MISMATCH",
                value=value,
            ))
            return

        # 长度检查（字符串和列表）
        if rule.min_length is not None or rule.max_length is not None:
            length = len(value) if hasattr(value, '__len__') else 0

            if rule.min_length is not None and length < rule.min_length:
                self.add_error(ValidationError(
                    field=field_name,
                    message=f"字段 '{field_name}' 长度不足: {length} < {rule.min_length}",
                    code="MIN_LENGTH_VIOLATION",
                    value=value,
                ))

            if rule.max_length is not None and length > rule.max_length:
                self.add_error(ValidationError(
                    field=field_name,
                    message=f"字段 '{field_name}' 长度超限: {length} > {rule.max_length}",
                    code="MAX_LENGTH_VIOLATION",
                    value=value,
                ))

        # 值范围检查（数字）
        if rule.min_value is not None or rule.max_value is not None:
            if isinstance(value, (int, float)):
                if rule.min_value is not None and value < rule.min_value:
                    self.add_error(ValidationError(
                        field=field_name,
                        message=f"字段 '{field_name}' 值过小: {value} < {rule.min_value}",
                        code="MIN_VALUE_VIOLATION",
                        value=value,
                    ))

                if rule.max_value is not None and value > rule.max_value:
                    self.add_error(ValidationError(
                        field=field_name,
                        message=f"字段 '{field_name}' 值过大: {value} > {rule.max_value}",
                        code="MAX_VALUE_VIOLATION",
                        value=value,
                    ))

        # 正则表达式验证
        if rule.pattern and isinstance(value, str):
            if not rule.pattern.match(value):
                self.add_error(ValidationError(
                    field=field_name,
                    message=f"字段 '{field_name}' 格式不匹配",
                    code="PATTERN_MISMATCH",
                    value=value,
                ))

        # 允许值检查
        if rule.allowed_values is not None:
            if value not in rule.allowed_values:
                self.add_error(ValidationError(
                    field=field_name,
                    message=f"字段 '{field_name}' 值不在允许列表中: {value}",
                    code="VALUE_NOT_ALLOWED",
                    value=value,
                ))

        # 自定义验证器
        if rule.custom_validator:
            try:
                if not rule.custom_validator(value):
                    self.add_error(ValidationError(
                        field=field_name,
                        message=f"字段 '{field_name}' 自定义验证失败",
                        code="CUSTOM_VALIDATION_FAILED",
                        value=value,
                    ))
            except Exception as e:
                logger.error(f"❌ 自定义验证器异常: {e}")

    async def _security_check_context(self, context) -> None:
        """
        Schema验证器不执行安全检查（由SecurityChecker负责）

        Args:
            context: 待检查的上下文对象
        """
        pass

    # 类方法：快速创建常用验证规则

    @classmethod
    def email_rule(
        cls, field_name: str, required: bool = False
    ) -> FieldRule:
        """创建邮箱验证规则"""
        return FieldRule(
            field_name=field_name,
            required=required,
            field_type=str,
            pattern=cls.EMAIL_PATTERN,
        )

    @classmethod
    def url_rule(
        cls, field_name: str, required: bool = False
    ) -> FieldRule:
        """创建URL验证规则"""
        return FieldRule(
            field_name=field_name,
            required=required,
            field_type=str,
            pattern=cls.URL_PATTERN,
        )

    @classmethod
    def uuid_rule(
        cls, field_name: str, required: bool = False
    ) -> FieldRule:
        """创建UUID验证规则"""
        return FieldRule(
            field_name=field_name,
            required=required,
            field_type=str,
            pattern=cls.UUID_PATTERN,
        )

    @classmethod
    def string_rule(
        cls,
        field_name: str,
        required: bool = False,
        min_length: Optional[int] = None,
        max_length: Optional[int] = None,
    ) -> FieldRule:
        """创建字符串验证规则"""
        return FieldRule(
            field_name=field_name,
            required=required,
            field_type=str,
            min_length=min_length,
            max_length=max_length,
        )

    @classmethod
    def integer_rule(
        cls,
        field_name: str,
        required: bool = False,
        min_value: Optional[int] = None,
        max_value: Optional[int] = None,
    ) -> FieldRule:
        """创建整数验证规则"""
        return FieldRule(
            field_name=field_name,
            required=required,
            field_type=int,
            min_value=min_value,
            max_value=max_value,
        )

    @classmethod
    def float_rule(
        cls,
        field_name: str,
        required: bool = False,
        min_value: Optional[float] = None,
        max_value: Optional[float] = None,
    ) -> FieldRule:
        """创建浮点数验证规则"""
        return FieldRule(
            field_name=field_name,
            required=required,
            field_type=float,
            min_value=min_value,
            max_value=max_value,
        )

    @classmethod
    def enum_rule(
        cls,
        field_name: str,
        allowed_values: Set[Any],
        required: bool = False,
    ) -> FieldRule:
        """创建枚举验证规则"""
        return FieldRule(
            field_name=field_name,
            required=required,
            allowed_values=allowed_values,
        )


__all__ = [
    "SchemaValidator",
    "FieldRule",
]
