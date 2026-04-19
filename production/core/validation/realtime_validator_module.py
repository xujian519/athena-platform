#!/usr/bin/env python3
"""
轻量级实时参数验证模块
Lightweight Realtime Parameter Validator Module

从Athena提取的轻量级参数验证能力:
1. 流式参数验证(边输入边验证)
2. 智能缓存(LRU缓存,避免重复验证)
3. 并行验证(多参数并行处理)
4. 实时反馈(即时提供验证建议)
5. 增量验证(仅验证变化部分)

专门为小诺优化,去除Athena强耦合依赖。

作者: Athena平台团队
创建时间: 2025-12-27
版本: v1.0.0 "轻量级集成版"
"""

from __future__ import annotations
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

    VALID = "valid"  # 有效
    INVALID = "invalid"  # 无效
    WARNING = "warning"  # 警告
    ERROR = "error"  # 错误


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

    def is_valid(self) -> bool:
        """是否有效"""
        return self.status == ValidationStatus.VALID

    def has_warnings(self) -> bool:
        """是否有警告"""
        return self.status == ValidationStatus.WARNING

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "status": self.status.value,
            "parameter_name": self.parameter_name,
            "message": self.message,
            "suggestions": self.suggestions,
            "confidence": self.confidence,
            "validation_time": self.validation_time,
            "timestamp": self.timestamp.isoformat(),
        }


@dataclass
class ParameterSchema:
    """参数模式定义"""

    name: str
    type: type
    required: bool = True
    min_length: int | None = None
    max_length: int | None = None
    pattern: str | None = None
    enum: list[str] = None
    custom_validator: Callable | None = None

    # 验证规则描述
    description: str = ""

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "name": self.name,
            "type": self.type.__name__,
            "required": self.required,
            "min_length": self.min_length,
            "max_length": self.max_length,
            "pattern": self.pattern,
            "enum": self.enum,
            "description": self.description,
        }


@dataclass
class ValidationCache:
    """验证缓存"""

    result: ValidationResult
    timestamp: datetime
    hit_count: int = 0


class LightweightRealtimeValidator:
    """
    轻量级实时参数验证模块

    从Athena实时参数验证器提取核心能力,
    专门设计为可被小诺直接导入使用的Python模块。

    核心特性:
    1. 零外部服务依赖
    2. 可选缓存支持
    3. 配置驱动的验证策略
    4. 简化的API接口
    5. 并行验证支持
    """

    def __init__(self, config: dict | None = None):
        """
        初始化轻量级实时验证器

        Args:
            config: 配置字典,包含:
                - enable_cache: 是否启用缓存(默认True)
                - cache_max_size: 缓存最大容量(默认1000)
                - cache_ttl_seconds: 缓存TTL(默认300秒=5分钟)
                - max_concurrent_validations: 最大并发验证数(默认10)
        """
        self.config = config or {}

        # 参数模式定义
        self.schemas: dict[str, ParameterSchema] = {}

        # 配置参数
        self.enable_cache = self.config.get("enable_cache", True)
        self.cache_max_size = self.config.get("cache_max_size", 1000)
        self.cache_ttl_seconds = self.config.get("cache_ttl_seconds", 300)
        self.cache_ttl = timedelta(seconds=self.cache_ttl_seconds)
        self.max_concurrent_validations = self.config.get("max_concurrent_validations", 10)

        # 验证缓存(LRU)
        self.cache: dict[str, ValidationCache] = {}

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

        logger.info("⚡ 轻量级实时参数验证模块初始化完成")
        logger.info(f"   缓存: {'启用' if self.enable_cache else '禁用'}")
        logger.info(f"   缓存容量: {self.cache_max_size}")
        logger.info(f"   缓存TTL: {self.cache_ttl_seconds}秒")

    def register_schema(self, schema: ParameterSchema) -> bool:
        """
        注册参数模式

        Args:
            schema: 参数模式定义

        Returns:
            是否注册成功
        """
        self.schemas[schema.name] = schema
        logger.info(f"📋 参数模式已注册: {schema.name} ({schema.type.__name__})")
        return True

    def register_schemas(self, schemas: list[ParameterSchema]) -> int:
        """
        批量注册参数模式

        Args:
            schemas: 参数模式列表

        Returns:
            成功注册的数量
        """
        count = 0
        for schema in schemas:
            if self.register_schema(schema):
                count += 1
        return count

    async def validate(
        self,
        parameters: dict[str, Any],        callback: Callable[[str, ValidationResult, Awaitable[None]]] | None = None,
    ) -> dict[str, ValidationResult]:
        """
        验证参数(简化版API)

        Args:
            parameters: 参数字典
            callback: 实时反馈回调函数

        Returns:
            验证结果字典
        """
        return await self.validate_streaming(parameters, callback)

    async def validate_streaming(
        self,
        parameters: dict[str, Any],        callback: Callable[[str, ValidationResult, Awaitable[None]]] | None = None,
    ) -> dict[str, ValidationResult]:
        """
        流式验证参数(完整API)

        支持并行验证多个参数,提供实时反馈。

        Args:
            parameters: 参数字典
            callback: 实时反馈回调函数

        Returns:
            验证结果字典
        """
        results = {}
        validation_tasks = []

        # 创建验证任务
        for param_name, param_value in parameters.items():
            schema = self.schemas.get(param_name)

            if not schema:
                # 没有模式定义,跳过或创建警告结果
                logger.debug(f"⚠️ 未找到参数模式: {param_name},跳过验证")
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
                elif isinstance(result, Exception):
                    logger.error(f"验证任务异常: {result}")

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
        if self.enable_cache:
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
        if self.stats["total_validations"] > 1:
            self.stats["avg_validation_time"] = (
                self.stats["avg_validation_time"] * (self.stats["total_validations"] - 1)
                + validation_time
            ) / self.stats["total_validations"]
        else:
            self.stats["avg_validation_time"] = validation_time

        # 缓存结果
        if self.enable_cache:
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

        # 1. 必填验证
        if schema.required and param_value is None:
            status = ValidationStatus.ERROR
            messages.append(f"参数 {param_name} 是必填的")
            suggestions.append(f"提供 {param_name} 参数的值")
            return ValidationResult(
                status=status,
                parameter_name=param_name,
                message="; ".join(messages),
                suggestions=suggestions,
                confidence=1.0,
            )

        # 如果参数为空但非必填,直接通过
        if param_value is None:
            return ValidationResult(
                status=ValidationStatus.VALID,
                parameter_name=param_name,
                message="参数为空但非必填",
                confidence=1.0,
            )

        # 2. 类型验证
        if not isinstance(param_value, schema.type):
            status = ValidationStatus.INVALID
            messages.append(
                f"类型错误: 期望 {schema.type.__name__}, 实际 {type(param_value).__name__}"
            )
            suggestions.append(f"将参数转换为 {schema.type.__name__} 类型")

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

        # 4. 模式验证(正则表达式)
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
                if asyncio.iscoroutinefunction(schema.custom_validator):
                    custom_result = await schema.custom_validator(param_value)
                else:
                    custom_result = schema.custom_validator(param_value)

                # 处理自定义验证器结果
                if isinstance(custom_result, bool):
                    if not custom_result:
                        status = (
                            ValidationStatus.INVALID if status == ValidationStatus.VALID else status
                        )
                        messages.append("自定义验证失败")
                elif hasattr(custom_result, "valid"):
                    if not custom_result.valid:
                        status = (
                            ValidationStatus.INVALID if status == ValidationStatus.VALID else status
                        )
                        messages.append(custom_result.message)
                        if hasattr(custom_result, "suggestions") and custom_result.suggestions:
                            suggestions.extend(custom_result.suggestions)
                elif isinstance(custom_result, str) and custom_result:
                    status = (
                        ValidationStatus.INVALID if status == ValidationStatus.VALID else status
                    )
                    messages.append(custom_result)

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
        cache_key_old = self._compute_cache_key(param_name, previous_result)
        cache_key_new = self._compute_cache_key(param_name, param_value)

        if cache_key_old == cache_key_new:
            # 值未变化,返回之前的结果
            return previous_result

        # 值变化了,重新验证
        schema = self.schemas.get(param_name)
        if schema:
            return await self._perform_validation(param_name, param_value, schema)

        return previous_result

    async def validate_batch(
        self, parameter_sets: list[dict[str, Any]]) -> list[dict[str, ValidationResult]]:
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
        total_requests = self.stats["cache_hits"] + self.stats["cache_misses"]
        cache_hit_rate = self.stats["cache_hits"] / total_requests if total_requests > 0 else 0

        return {
            **self.stats,
            "cache_hit_rate": cache_hit_rate,
            "cache_size": len(self.cache),
            "cache_enabled": self.enable_cache,
        }

    def clear_cache(self) -> None:
        """清除缓存"""
        self.cache.clear()
        logger.info("🗑️ 验证缓存已清除")

    def get_schema(self, param_name: str) -> ParameterSchema | None:
        """获取参数模式"""
        return self.schemas.get(param_name)

    def list_schemas(self) -> list[str]:
        """列出所有已注册的参数模式"""
        return list(self.schemas.keys())


# 便捷函数
_validator_instance: LightweightRealtimeValidator | None = None


def get_realtime_validator(config: dict | None = None) -> LightweightRealtimeValidator:
    """获取实时验证器单例"""
    global _validator_instance
    if _validator_instance is None:
        _validator_instance = LightweightRealtimeValidator(config)
    return _validator_instance


# 使用示例
async def main():
    """演示函数"""
    print("=" * 60)
    print("轻量级实时参数验证模块演示")
    print("=" * 60)

    # 创建验证器
    validator = LightweightRealtimeValidator()

    # 注册参数模式
    validator.register_schema(
        ParameterSchema(
            name="patent_id",
            type=str,
            required=True,
            min_length=5,
            max_length=20,
            pattern=r"^CN\d{7,}$",
            description="专利号,格式为CN+数字",
        )
    )

    validator.register_schema(
        ParameterSchema(
            name="max_results",
            type=int,
            required=False,
            enum=[10, 20, 50, 100],
            description="最大结果数",
        )
    )

    validator.register_schema(
        ParameterSchema(
            name="query",
            type=str,
            required=True,
            min_length=3,
            max_length=200,
            description="搜索关键词",
        )
    )

    # 验证参数
    print("\n📝 测试1: 有效参数")
    params1 = {"patent_id": "CN1234567", "max_results": 10, "query": "人工智能专利"}
    results1 = await validator.validate(params1)

    for param_name, result in results1.items():
        print(f"   {param_name}: {result.status.value} - {result.message}")

    print("\n📝 测试2: 无效参数")
    params2 = {
        "patent_id": "INVALID",  # 格式错误
        "max_results": 15,  # 不在枚举中
        "query": "AI",  # 太短
    }
    results2 = await validator.validate(params2)

    for param_name, result in results2.items():
        print(f"   {param_name}: {result.status.value}")
        print(f"      消息: {result.message}")
        if result.suggestions:
            print(f"      建议: {', '.join(result.suggestions)}")

    # 统计信息
    print("\n📊 统计信息:")
    stats = validator.get_stats()
    print(f"   总验证次数: {stats['total_validations']}")
    print(f"   缓存命中率: {stats['cache_hit_rate']:.1%}")
    print(f"   平均验证时间: {stats['avg_validation_time']*1000:.2f}ms")

    print("\n✅ 演示完成")


# 入口点: @async_main装饰器已添加到main函数
