#!/usr/bin/env python3
"""
上下文验证插件 - Phase 2.3示例插件

Validation Plugin - 验证上下文数据的完整性和有效性

功能:
- 数据完整性检查
- 格式验证
- 安全检查

作者: Athena平台团队
创建时间: 2026-04-24
"""

import logging
import re
from typing import Any, Dict, List, Optional

from ..base_context import BaseContextPlugin, BaseContext

logger = logging.getLogger(__name__)


class ValidationError(Exception):
    """验证错误"""
    pass


class ValidationPlugin(BaseContextPlugin):
    """
    上下文验证插件

    验证上下文数据的完整性和有效性。

    配置参数:
    - required_fields: 必需字段列表
    - max_length: 字段最大长度
    - patterns: 字段格式验证模式
    - check_injection: 是否检查注入攻击
    """

    def __init__(self):
        super().__init__(
            plugin_name="validation",
            plugin_version="1.0.0",
            dependencies=[],
        )
        self._required_fields = []
        self._max_length = 100000
        self._patterns = {}
        self._check_injection = True

    async def initialize(self, config: Dict[str, Any]) -> None:
        """
        初始化验证插件

        Args:
            config: 配置参数
        """
        await super().initialize(config)

        self._required_fields = config.get("required_fields", [])
        self._max_length = config.get("max_length", 100000)
        self._patterns = config.get("patterns", {})
        self._check_injection = config.get("check_injection", True)

        logger.info(
            f"✅ 验证插件初始化: required_fields={len(self._required_fields)}, "
            f"patterns={len(self._patterns)}"
        )

    async def execute(self, context: BaseContext, **_kwargs) -> dict[str, Any]:
        """
        执行验证

        Args:
            context: 上下文对象
            **kwargs: 执行参数

        Returns:
            dict[str, Any]: 验证结果
                - valid: 是否通过验证
                - errors: 错误列表
                - warnings: 警告列表
        """
        errors = []
        warnings = []

        # 1. 检查必需字段
        errors.extend(self._check_required_fields(context))

        # 2. 检查长度限制
        warnings.extend(self._check_length(context))

        # 3. 检查格式
        errors.extend(self._check_patterns(context))

        # 4. 安全检查
        if self._check_injection:
            errors.extend(self._check_injection_attacks(context))

        valid = len(errors) == 0

        logger.debug(
            f"✅ 验证完成: valid={valid}, errors={len(errors)}, warnings={len(warnings)}"
        )

        return {
            "valid": valid,
            "errors": errors,
            "warnings": warnings,
        }

    def _check_required_fields(self, context: BaseContext) -> list[str]:
        """检查必需字段"""
        errors = []

        for field in self._required_fields:
            if not hasattr(context, field) and field not in context.metadata:
                errors.append(f"缺少必需字段: {field}")
            else:
                value = getattr(context, field, None) or context.metadata.get(field)
                if value is None or value == "":
                    errors.append(f"必需字段为空: {field}")

        return errors

    def _check_length(self, context: BaseContext) -> list[str]:
        """检查长度限制"""
        warnings = []

        # 检查上下文ID长度
        if len(context.context_id) > 1000:
            warnings.append(f"context_id过长: {len(context.context_id)}")

        # 检查元数据大小
        metadata_str = str(context.metadata)
        if len(metadata_str) > self._max_length:
            warnings.append(f"元数据过大: {len(metadata_str)}")

        return warnings

    def _check_patterns(self, context: BaseContext) -> list[str]:
        """检查格式"""
        errors = []

        for field, pattern in self._patterns.items():
            value = getattr(context, field, None) or context.metadata.get(field, "")
            value_str = str(value)

            if not re.match(pattern, value_str):
                errors.append(f"字段格式不匹配: {field} (pattern: {pattern})")

        return errors

    def _check_injection_attacks(self, context: BaseContext) -> list[str]:
        """检查注入攻击"""
        errors = []

        # 危险模式列表
        dangerous_patterns = [
            r"<script[^>]*>.*?</script>",  # XSS
            r"javascript:",  # JavaScript URL
            r"on\w+\s*=",  # 事件处理器
            r"\$\{.*?\}",  # 模板注入
            r"DROP\s+TABLE",  # SQL注入
            r"__import__\(",  # Python代码注入
        ]

        # 检查所有字符串值
        context_dict = context.to_dict()
        context_str = str(context_dict)

        for pattern in dangerous_patterns:
            if re.search(pattern, context_str, re.IGNORECASE):
                errors.append(f"检测到潜在注入攻击: {pattern}")
                break

        return errors


__all__ = ["ValidationPlugin", "ValidationError"]
