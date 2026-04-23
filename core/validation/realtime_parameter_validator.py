#!/usr/bin/env python3
from __future__ import annotations
"""
实时参数验证器
Real-time Parameter Validator

优化参数验证的实时性:
1. 流式参数验证(边输入边验证)
2. 预测性验证(提前检测潜在问题)
3. 增量验证(避免重复验证)
4. 智能缓存(缓存验证结果)
5. 并行验证(多参数并行处理)
6. 实时反馈(即时提供验证建议)

作者: Athena平台团队
创建时间: 2025-12-27
版本: v2.0.0 "实时验证"
"""

import asyncio
import hashlib
import json
import logging
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class ValidationStatus(Enum):
    """验证状态"""

    PENDING = "pending"  # 待验证
    VALIDATING = "validating"  # 验证中
    VALID = "valid"  # 有效
    INVALID = "invalid"  # 无效
    WARNING = "warning"  # 警告
    ERROR = "error"  # 错误


class ValidationPriority(Enum):
    """验证优先级"""

    CRITICAL = "critical"  # 关键(立即验证)
    HIGH = "high"  # 高优先级
    NORMAL = "normal"  # 正常
    LOW = "low"  # 低优先级(可延后)


@dataclass
class ValidationResult:
    """验证结果"""

    status: ValidationStatus
    parameter_name: str
    message: str
    suggestions: list[str] = field(default_factory=list)
    confidence: float = 1.0
    validation_time: float = 0.0
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class ParameterSchema:
    """参数模式定义"""

    name: str
    type: type
    required: bool = True
    min_length: Optional[int] = None
    max_length: Optional[int] = None
    pattern: Optional[str] = None
    enum: list[Any] | None = None
    custom_validator: Callable | None = None
    priority: ValidationPriority = ValidationPriority.NORMAL


@dataclass
class ValidationCache:
    """验证缓存"""

    result: ValidationResult
    timestamp: datetime
    hit_count: int = 0


class RealtimeParameterValidator:
    """
    实时参数验证器

    核心特性:
    1. 流式验证:边输入边验证
    2. 预测性验证:提前检测问题
    3. 增量验证:避免重复验证
    4. 智能缓存:缓存验证结果
    5. 并行处理:多参数并行验证
    6. 实时反馈:即时提供建议
    """

    def __init__(self):
        # 参数模式定义
        self.schemas: dict[str, ParameterSchema] = {}

        # 验证缓存(LRU)
        self.cache: dict[str, ValidationCache] = {}
        self.cache_max_size = 1000
        self.cache_ttl = timedelta(minutes=5)

        # 验证队列
        self.validation_queue: asyncio.Queue = asyncio.Queue()

        # 并行验证器池
        self.max_concurrent_validations = 10

        # 统计信息
        self.stats = {
            "total_validations": 0,
            "cache_hits": 0,
            "cache_misses": 0,
            "parallel_validations": 0,
            "avg_validation_time": 0.0,
        }

        # 实时反馈回调
        self.feedback_callbacks: list[Callable] = []

        logger.info("⚡ 实时参数验证器初始化完成")

    def register_schema(self, schema: ParameterSchema) -> Any:
        """注册参数模式"""
        self.schemas[schema.name] = schema
        logger.debug(f"📋 参数模式已注册: {schema.name}")

    async def validate_streaming(
        self,
        parameters: dict[str, Any],        callback: Callable[[str, ValidationResult, Awaitable[None]]] | None = None,
    ) -> dict[str, ValidationResult]:
        """
        流式验证参数

        Args:
            parameters: 参数字典
            callback: 实时反馈回调

        Returns:
            验证结果字典
        """
        results = {}
        validation_tasks = []

        # 创建验证任务
        for param_name, param_value in parameters.items():
            schema = self.schemas.get(param_name)

            if not schema:
                # 没有模式定义,跳过
                continue

            # 创建验证任务
            task = self._validate_parameter_streaming(param_name, param_value, schema, callback)
            validation_tasks.append(task)

        # 并行执行验证
        if validation_tasks:
            self.stats["parallel_validations"] += len(validation_tasks)
            results_list = await asyncio.gather(*validation_tasks, return_exceptions=True)

            # 整理结果
            for result in results_list:
                if isinstance(result, ValidationResult):
                    results[result.parameter_name] = result

        return results

    async def _validate_parameter_streaming(
        self,
        param_name: str,
        param_value: Any,
        schema: ParameterSchema,
        callback: Callable,
    ) -> ValidationResult:
        """流式验证单个参数"""
        start_time = datetime.now()

        # 检查缓存
        cache_key = self._compute_cache_key(param_name, param_value)
        cached_result = self._get_from_cache(cache_key)

        if cached_result:
            self.stats["cache_hits"] += 1
            logger.debug(f"💾 缓存命中: {param_name}")

            # 触发回调
            if callback:
                await callback(param_name, cached_result.result)

            return cached_result.result

        self.stats["cache_misses"] += 1

        # 执行验证
        result = await self._perform_validation(param_name, param_value, schema)

        # 记录验证时间
        validation_time = (datetime.now() - start_time).total_seconds()
        result.validation_time = validation_time

        # 更新统计
        self.stats["total_validations"] += 1
        self.stats["avg_validation_time"] = (
            self.stats["avg_validation_time"] * (self.stats["total_validations"] - 1)
            + validation_time
        ) / self.stats["total_validations"]

        # 缓存结果
        self._add_to_cache(cache_key, result)

        # 触发回调
        if callback:
            await callback(param_name, result)

        return result

    async def _perform_validation(
        self, param_name: str, param_value: Any, schema: ParameterSchema
    ) -> ValidationResult:
        """执行实际验证"""
        status = ValidationStatus.VALID
        messages = []
        suggestions = []

        # 1. 类型验证
        if not isinstance(param_value, schema.type):
            status = ValidationStatus.INVALID
            messages.append(
                f"类型错误: 期望 {schema.type.__name__}, 实际 {type(param_value).__name__}"
            )
            suggestions.append(f"将参数转换为 {schema.type.__name__} 类型")

        # 2. 必填验证
        if schema.required and param_value is None:
            status = ValidationStatus.ERROR
            messages.append(f"参数 {param_name} 是必填的")
            suggestions.append(f"提供 {param_name} 参数的值")

        # 3. 长度验证
        if isinstance(param_value, (str, list)):
            if schema.min_length and len(param_value) < schema.min_length:
                status = ValidationStatus.INVALID if status == ValidationStatus.VALID else status
                messages.append(f"长度不足: 最小 {schema.min_length}, 实际 {len(param_value)}")
                suggestions.append(f"至少提供 {schema.min_length} 个字符")

            if schema.max_length and len(param_value) > schema.max_length:
                status = ValidationStatus.INVALID if status == ValidationStatus.VALID else status
                messages.append(f"长度超限: 最大 {schema.max_length}, 实际 {len(param_value)}")
                suggestions.append(f"缩减到 {schema.max_length} 个字符以内")

        # 4. 模式验证
        if schema.pattern and isinstance(param_value, str):
            import re

            if not re.match(schema.pattern, param_value):
                status = ValidationStatus.INVALID if status == ValidationStatus.VALID else status
                messages.append(f"格式不匹配: 不符合模式 {schema.pattern}")
                suggestions.append("按照指定格式提供参数")

        # 5. 枚举验证
        if schema.enum and param_value not in schema.enum:
            status = ValidationStatus.INVALID if status == ValidationStatus.VALID else status
            messages.append(f"值不在允许范围内: {schema.enum}")
            suggestions.append(f"从以下值中选择: {', '.join(map(str, schema.enum))}")

        # 6. 自定义验证器
        if schema.custom_validator:
            try:
                custom_result = await schema.custom_validator(param_value)
                if not custom_result.valid:
                    status = (
                        ValidationStatus.INVALID if status == ValidationStatus.VALID else status
                    )
                    messages.append(custom_result.message)
                    if custom_result.suggestions:
                        suggestions.extend(custom_result.suggestions)
            except Exception as e:
                logger.error(f"自定义验证器失败: {e}")
                status = ValidationStatus.ERROR
                messages.append(f"验证器异常: {e!s}")

        # 组合消息
        message = "; ".join(messages) if messages else "验证通过"

        return ValidationResult(
            status=status,
            parameter_name=param_name,
            message=message,
            suggestions=suggestions,
            confidence=1.0 if status == ValidationStatus.VALID else 0.8,
        )

    async def validate_predictive(
        self, partial_parameters: dict[str, Any]
    ) -> dict[str, ValidationResult]:
        """
        预测性验证:基于部分参数预测潜在问题

        Args:
            partial_parameters: 部分参数(可能不完整)

        Returns:
            预测验证结果
        """
        predictions = {}

        # 检查依赖关系
        for param_name, param_value in partial_parameters.items():
            schema = self.schemas.get(param_name)
            if not schema:
                continue

            # 预测缺失的必需参数
            if schema.required and param_value is None:
                predictions[param_name] = ValidationResult(
                    status=ValidationStatus.WARNING,
                    parameter_name=param_name,
                    message=f"预测: {param_name} 将是必填的",
                    suggestions=[f"准备提供 {param_name} 参数"],
                    confidence=0.7,
                )

            # 预测参数格式问题
            if isinstance(param_value, str) and len(param_value) < 3:
                predictions[param_name] = ValidationResult(
                    status=ValidationStatus.WARNING,
                    parameter_name=param_name,
                    message="预测: 参数可能过短",
                    suggestions=["考虑提供更详细的参数值"],
                    confidence=0.6,
                )

        return predictions

    async def validate_incremental(
        self, param_name: str, param_value: Any, previous_result: ValidationResult | None = None
    ) -> ValidationResult:
        """
        增量验证:仅验证变化的部分

        Args:
            param_name: 参数名
            param_value: 参数值
            previous_result: 之前的验证结果

        Returns:
            更新的验证结果
        """
        # 如果没有之前的结果,执行完整验证
        if previous_result is None:
            schema = self.schemas.get(param_name)
            if not schema:
                return ValidationResult(
                    status=ValidationStatus.WARNING,
                    parameter_name=param_name,
                    message=f"未找到参数模式: {param_name}",
                )

            return await self._perform_validation(param_name, param_value, schema)

        # 检查值是否真的变化了
        cache_key = self._compute_cache_key(param_name, param_value)
        if cache_key == self._compute_cache_key(param_name, previous_result):
            # 值未变化,返回之前的结果
            return previous_result

        # 值变化了,重新验证
        schema = self.schemas.get(param_name)
        if schema:
            return await self._perform_validation(param_name, param_value, schema)

        return previous_result

    def _compute_cache_key(self, param_name: str, param_value: Any) -> str:
        """计算缓存键"""
        # 序列化参数值
        try:
            value_str = json.dumps(param_value, sort_keys=True, default=str)
        except Exception:
            value_str = str(param_value)

        # 计算哈希
        key_str = f"{param_name}:{value_str}"
        return hashlib.md5(key_str.encode('utf-8'), usedforsecurity=False).hexdigest()

    def _get_from_cache(self, cache_key: str) -> ValidationCache | None:
        """从缓存获取"""
        if cache_key not in self.cache:
            return None

        cache_entry = self.cache[cache_key]

        # 检查是否过期
        if datetime.now() - cache_entry.timestamp > self.cache_ttl:
            del self.cache[cache_key]
            return None

        cache_entry.hit_count += 1
        return cache_entry

    def _add_to_cache(self, cache_key: str, result: ValidationResult) -> Any:
        """添加到缓存"""
        # LRU淘汰
        if len(self.cache) >= self.cache_max_size:
            # 删除最旧的条目
            oldest_key = min(self.cache.keys(), key=lambda k: self.cache[k].timestamp)
            del self.cache[oldest_key]

        self.cache[cache_key] = ValidationCache(result=result, timestamp=datetime.now())

    async def validate_batch(
        self, parameter_sets: list[dict[str, Any]]
    ) -> list[dict[str, ValidationResult]]:
        """
        批量验证多组参数

        Args:
            parameter_sets: 参数组列表

        Returns:
            验证结果列表
        """
        validation_tasks = [self.validate_streaming(params) for params in parameter_sets]

        results = await asyncio.gather(*validation_tasks)
        return results

    def register_feedback_callback(self, callback: Callable) -> Any:
        """注册实时反馈回调"""
        self.feedback_callbacks.append(callback)

    async def trigger_feedback(self, param_name: str, result: ValidationResult):
        """触发反馈回调"""
        for callback in self.feedback_callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(param_name, result)
                else:
                    callback(param_name, result)
            except Exception as e:
                logger.error(f"反馈回调失败: {e}")

    def get_stats(self) -> dict[str, Any]:
        """获取统计信息"""
        return {
            **self.stats,
            "cache_hit_rate": (
                self.stats["cache_hits"] / (self.stats["cache_hits"] + self.stats["cache_misses"])
                if self.stats["cache_hits"] + self.stats["cache_misses"] > 0
                else 0
            ),
            "cache_size": len(self.cache),
        }

    def clear_cache(self) -> None:
        """清除缓存"""
        self.cache.clear()
        logger.info("🗑️ 验证缓存已清除")


# 导出便捷函数
_validator: RealtimeParameterValidator | None = None


def get_realtime_validator() -> RealtimeParameterValidator:
    """获取实时验证器单例"""
    global _validator
    if _validator is None:
        _validator = RealtimeParameterValidator()
    return _validator
