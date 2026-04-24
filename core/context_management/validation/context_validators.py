#!/usr/bin/env python3
"""
上下文验证器 - Phase 3.1安全加固

Context Validators - 针对不同上下文类型的专用验证器

核心组件:
- ContextValidator: 通用上下文验证器
- TaskContextValidator: 任务上下文验证器
- SessionContextValidator: 会话上下文验证器

作者: Athena平台团队
创建时间: 2026-04-24
版本: v3.1.0
"""

import logging
from typing import Any, Dict, List, Optional

from ..interfaces import IContext
from .base_validator import BaseContextValidator, SecurityIssue, ValidationError
from .schema_validator import SchemaValidator
from .security_checker import SecurityChecker

logger = logging.getLogger(__name__)


class ContextValidator(BaseContextValidator):
    """
    通用上下文验证器

    结合Schema验证和安全检查的复合验证器。
    适用于所有实现了IContext接口的上下文对象。

    使用示例:
        validator = ContextValidator(strict_mode=True)
        is_valid = await validator.validate(context)
        issues = await validator.security_check(context)
    """

    def __init__(
        self,
        strict_mode: bool = False,
        fail_fast: bool = False,
        enable_security_check: bool = True,
    ):
        """
        初始化通用上下文验证器

        Args:
            strict_mode: 严格模式（任何警告都视为错误）
            fail_fast: 快速失败（发现第一个问题就停止）
            enable_security_check: 是否启用安全检查
        """
        super().__init__(
            validator_name="ContextValidator",
            strict_mode=strict_mode,
            fail_fast=fail_fast,
        )

        self._enable_security_check = enable_security_check

        # 创建子验证器
        self._schema_validator = SchemaValidator(
            strict_mode=strict_mode,
            fail_fast=fail_fast,
        )
        self._security_checker = SecurityChecker(
            strict_mode=strict_mode,
            fail_fast=fail_fast,
        ) if enable_security_check else None

        logger.info(
            f"✅ 通用上下文验证器初始化: "
            f"strict={strict_mode}, fail_fast={fail_fast}, "
            f"security={enable_security_check}"
        )

    async def _validate_context(self, context: IContext) -> None:
        """
        验证上下文数据

        Args:
            context: 待验证的上下文对象
        """
        # 基本字段验证
        self._validate_basic_fields(context)

        # 委托给Schema验证器
        await self._schema_validator.validate(context)

        # 合并验证错误
        for error in self._schema_validator.validation_errors:
            self.add_error(error)

    def _validate_basic_fields(self, context: IContext) -> None:
        """
        验证基本字段

        Args:
            context: 上下文对象
        """
        # 检查context_id
        if not hasattr(context, 'context_id') or not context.context_id:
            self.add_error(ValidationError(
                field="context_id",
                message="context_id是必填字段",
                code="REQUIRED_FIELD_MISSING",
            ))

        # 检查context_type
        if not hasattr(context, 'context_type') or not context.context_type:
            self.add_error(ValidationError(
                field="context_type",
                message="context_type是必填字段",
                code="REQUIRED_FIELD_MISSING",
            ))

        # 检查时间戳
        if hasattr(context, 'created_at') and context.created_at is None:
            self.add_error(ValidationError(
                field="created_at",
                message="created_at不能为空",
                code="INVALID_TIMESTAMP",
            ))

    async def _security_check_context(self, context: IContext) -> None:
        """
        执行安全检查

        Args:
            context: 待检查的上下文对象
        """
        if self._security_checker:
            await self._security_checker.security_check(context)

            # 合并安全问题
            for issue in self._security_checker.security_issues:
                self.add_security_issue(issue)


class TaskContextValidator(ContextValidator):
    """
    任务上下文验证器

    专门用于验证任务上下文的验证器，提供任务特定的验证规则。

    验证内容:
    - task_id: 必填，格式验证
    - task_description: 必填，长度限制
    - status: 枚举值检查
    - steps: 列表验证
    - global_variables: 字典验证
    """

    # 允许的任务状态
    ALLOWED_STATUSES = {
        "active", "suspended", "completed", "failed", "cancelled"
    }

    def __init__(
        self,
        strict_mode: bool = False,
        fail_fast: bool = False,
        max_description_length: int = 5000,
        max_steps: int = 1000,
    ):
        """
        初始化任务上下文验证器

        Args:
            strict_mode: 严格模式
            fail_fast: 快速失败
            max_description_length: 最大描述长度
            max_steps: 最大步骤数
        """
        super().__init__(
            strict_mode=strict_mode,
            fail_fast=fail_fast,
            enable_security_check=True,
        )

        self._name = "TaskContextValidator"
        self._max_description_length = max_description_length
        self._max_steps = max_steps

        # 添加任务特定的Schema规则
        from .schema_validator import FieldRule, SchemaValidator

        task_id_rule = SchemaValidator.string_rule(
            "task_id",
            required=True,
            min_length=1,
            max_length=100,
        )
        self._schema_validator.add_rule(task_id_rule)

        logger.info(
            f"✅ 任务上下文验证器初始化: "
            f"max_desc={max_description_length}, max_steps={max_steps}"
        )

    async def _validate_context(self, context: IContext) -> None:
        """
        验证任务上下文

        Args:
            context: 待验证的上下文对象
        """
        # 先执行基本验证
        await super()._validate_context(context)

        data = context.to_dict() if hasattr(context, 'to_dict') else context.__dict__

        # 验证任务状态
        if "status" in data:
            status = data["status"]
            if isinstance(status, str):
                if status not in self.ALLOWED_STATUSES:
                    self.add_error(self.ValidationError(
                        field="status",
                        message=f"无效的任务状态: {status}",
                        code="INVALID_STATUS",
                        value=status,
                    ))

        # 验证描述长度
        if "task_description" in data:
            description = data["task_description"]
            if isinstance(description, str):
                if len(description) > self._max_description_length:
                    self.add_error(self.ValidationError(
                        field="task_description",
                        message=f"任务描述过长: {len(description)} > {self._max_description_length}",
                        code="MAX_LENGTH_VIOLATION",
                        value=description[:100] + "...",
                    ))

        # 验证步骤数
        if "steps" in data:
            steps = data["steps"]
            if isinstance(steps, list):
                if len(steps) > self._max_steps:
                    self.add_error(self.ValidationError(
                        field="steps",
                        message=f"步骤数过多: {len(steps)} > {self._max_steps}",
                        code="MAX_STEPS_VIOLATION",
                        value=len(steps),
                    ))


class SessionContextValidator(ContextValidator):
    """
    会话上下文验证器

    专门用于验证会话上下文的验证器，提供会话特定的验证规则。

    验证内容:
    - session_id: 必填，UUID格式验证
    - user_id: 必填
    - agent_id: 可选
    - messages: 列表验证，最大消息数
    - metadata: 字典验证，禁止敏感字段
    """

    # 禁止的元数据字段（可能包含敏感信息）
    FORBIDDEN_METADATA_KEYS = {
        "password", "token", "secret", "api_key", "credential",
        "private_key", "auth", "cookie", "session_token",
    }

    def __init__(
        self,
        strict_mode: bool = False,
        fail_fast: bool = False,
        max_messages: int = 10000,
        max_message_length: int = 50000,
    ):
        """
        初始化会话上下文验证器

        Args:
            strict_mode: 严格模式
            fail_fast: 快速失败
            max_messages: 最大消息数
            max_message_length: 单条消息最大长度
        """
        super().__init__(
            strict_mode=strict_mode,
            fail_fast=fail_fast,
            enable_security_check=True,
        )

        self._name = "SessionContextValidator"
        self._max_messages = max_messages
        self._max_message_length = max_message_length

        # 添加会话特定的Schema规则
        from .schema_validator import FieldRule, SchemaValidator

        session_id_rule = SchemaValidator.uuid_rule(
            "session_id",
            required=True,
        )
        self._schema_validator.add_rule(session_id_rule)

        logger.info(
            f"✅ 会话上下文验证器初始化: "
            f"max_messages={max_messages}, max_msg_len={max_message_length}"
        )

    async def _validate_context(self, context: IContext) -> None:
        """
        验证会话上下文

        Args:
            context: 待验证的上下文对象
        """
        # 先执行基本验证
        await super()._validate_context(context)

        data = context.to_dict() if hasattr(context, 'to_dict') else context.__dict__

        # 验证messages字段
        if "messages" in data:
            messages = data["messages"]
            if isinstance(messages, list):
                if len(messages) > self._max_messages:
                    self.add_error(self.ValidationError(
                        field="messages",
                        message=f"消息数过多: {len(messages)} > {self._max_messages}",
                        code="MAX_MESSAGES_VIOLATION",
                        value=len(messages),
                    ))

                # 验证每条消息
                for i, msg in enumerate(messages):
                    if isinstance(msg, dict):
                        content = msg.get("content", "")
                        if isinstance(content, str) and len(content) > self._max_message_length:
                            self.add_error(self.ValidationError(
                                field=f"messages[{i}].content",
                                message=f"消息过长: {len(content)} > {self._max_message_length}",
                                code="MAX_MESSAGE_LENGTH_VIOLATION",
                                value=len(content),
                            ))

        # 验证metadata中的敏感字段
        if "metadata" in data:
            metadata = data["metadata"]
            if isinstance(metadata, dict):
                for key in metadata.keys():
                    if key.lower() in self.FORBIDDEN_METADATA_KEYS:
                        self.add_security_issue(SecurityIssue(
                            severity=SecurityIssue.MEDIUM,
                            category="sensitive_data",
                            description=f"元数据中包含敏感字段: {key}",
                            evidence=key,
                            location=f"metadata.{key}",
                            recommendation="移除敏感字段或使用加密存储",
                        ))


__all__ = [
    "ContextValidator",
    "TaskContextValidator",
    "SessionContextValidator",
]
