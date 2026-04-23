#!/usr/bin/env python3

"""
感知模块错误处理器
Perception Module Error Handler

提供统一的错误处理、重试机制和降级策略

作者: Athena AI系统
创建时间: 2025-12-11
版本: 1.0.0
"""

import asyncio
import inspect
import logging
import random
import traceback
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from functools import wraps
from typing import Any, Optional

from . import BaseProcessor, InputType, PerceptionResult

logger = logging.getLogger(__name__)


class ErrorType(Enum):
    """错误类型"""

    NETWORK_ERROR = "network_error"
    MODEL_ERROR = "model_error"
    DATA_ERROR = "data_error"
    TIMEOUT_ERROR = "timeout_error"
    MEMORY_ERROR = "memory_error"
    UNKNOWN_ERROR = "unknown_error"


class ErrorSeverity(Enum):
    """错误严重程度"""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class ErrorInfo:
    """错误信息"""

    error_type: ErrorType
    severity: ErrorSeverity
    message: str
    exception: Exception
    timestamp: datetime = field(default_factory=datetime.now)
    retry_count: int = 0
    context: dict[str, Any] = field(default_factory=dict)


class RetryConfig:
    """重试配置"""

    def __init__(
        self,
        max_retries: int = 3,
        base_delay: float = 1.0,
        max_delay: float = 10.0,
        exponential_base: float = 2.0,
        jitter: bool = True,
    ):
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.exponential_base = exponential_base
        self.jitter = jitter


class FallbackStrategy:
    """降级策略"""

    def __init__(
        self,
        name: str,
        fallback_processor: Optional[str] = None,
        fallback_data: Optional[Any] = None,
        confidence_penalty: float = 0.1,
    ):
        self.name = name
        self.fallback_processor = fallback_processor
        self.fallback_data = fallback_data
        self.confidence_penalty = confidence_penalty


class PerceptionErrorHandler:
    """感知模块错误处理器"""

    def __init__(self, config: Optional[dict[str, Any]] = None):
        self.config = config or {}

        # 错误统计
        self.error_counts: dict[str, int] = {}
        self.error_details: list[ErrorInfo] = []

        # 重试配置
        self.retry_configs = {
            ErrorType.NETWORK_ERROR: RetryConfig(max_retries=5, base_delay=2.0),
            ErrorType.MODEL_ERROR: RetryConfig(max_retries=2, base_delay=1.0),
            ErrorType.TIMEOUT_ERROR: RetryConfig(max_retries=3, base_delay=1.5),
            ErrorType.DATA_ERROR: RetryConfig(max_retries=1, base_delay=0.5),
            ErrorType.MEMORY_ERROR: RetryConfig(max_retries=0, base_delay=0.0),  # 内存错误不重试
            ErrorType.UNKNOWN_ERROR: RetryConfig(max_retries=2, base_delay=1.0),
        }

        # 降级策略
        self.fallback_strategies = {
            "text_processor": [
                FallbackStrategy("simple_keyword", None, None, 0.2),
                FallbackStrategy("basic_processing", None, None, 0.1),
            ],
            "image_processor": [
                FallbackStrategy("resize_image", None, None, 0.3),
                FallbackStrategy("color_analysis", None, None, 0.2),
            ],
            "audio_processor": [
                FallbackStrategy("basic_features", None, None, 0.2),
                FallbackStrategy("silence_detection", None, None, 0.1),
            ],
            "video_processor": [
                FallbackStrategy("frame_extraction", None, None, 0.3),
                FallbackStrategy("duration_analysis", None, None, 0.2),
            ],
            "multimodal_processor": [
                FallbackStrategy("text_only", "text_processor", None, 0.4),
                FallbackStrategy("basic_multimodal", None, None, 0.2),
            ],
        }

        # 错误处理回调
        self.error_callbacks: list[Callable] = []

        logger.info("🛡️ 感知模块错误处理器初始化完成")

    def classify_error(self, exception: Exception) -> ErrorType:
        """分类错误"""
        error_message = str(exception).lower()

        if (
            "connection" in error_message
            or "network" in error_message
            or "timeout" in error_message
        ):
            if "timeout" in error_message:
                return ErrorType.TIMEOUT_ERROR
            return ErrorType.NETWORK_ERROR

        elif "memory" in error_message or "memory" in error_message:
            return ErrorType.MEMORY_ERROR

        elif (
            "model" in error_message or "embedding" in error_message or "tokenizer" in error_message
        ):
            return ErrorType.MODEL_ERROR

        elif "data" in error_message or "format" in error_message or "parse" in error_message:
            return ErrorType.DATA_ERROR

        else:
            return ErrorType.UNKNOWN_ERROR

    def determine_severity(self, error_type: ErrorType, exception: Exception) -> ErrorSeverity:
        """确定错误严重程度"""
        if error_type == ErrorType.MEMORY_ERROR:
            return ErrorSeverity.HIGH

        elif error_type == ErrorType.MODEL_ERROR:
            return ErrorSeverity.MEDIUM

        elif error_type == ErrorType.NETWORK_ERROR:
            return ErrorSeverity.LOW

        elif "critical" in str(exception).lower():
            return ErrorSeverity.CRITICAL

        else:
            return ErrorSeverity.MEDIUM

    def calculate_retry_delay(self, retry_count: int, config: RetryConfig) -> float:
        """计算重试延迟"""
        # 指数退避
        delay = config.base_delay * (config.exponential_base**retry_count)

        # 限制最大延迟
        delay = min(delay, config.max_delay)

        # 添加抖动
        if config.jitter:
            jitter_factor = random.uniform(0.8, 1.2)
            delay *= jitter_factor

        return delay

    async def execute_with_retry(
        self, processor: BaseProcessor, func: Callable, *args, **kwargs
    ) -> PerceptionResult:
        """带重试机制执行函数"""
        error_type = None
        last_exception = None

        for attempt in range(self.retry_configs[ErrorType.UNKNOWN_ERROR].max_retries + 1):
            try:
                # 执行函数
                result = await func(processor, *args, **kwargs)

                # 如果有重试,记录恢复
                if attempt > 0:
                    logger.info(f"处理器 {processor.processor_id} 第 {attempt + 1} 次尝试成功")

                return result

            except Exception as e:
                last_exception = e
                error_type = self.classify_error(e)
                severity = self.determine_severity(error_type, e)

                # 记录错误
                error_info = ErrorInfo(
                    error_type=error_type,
                    severity=severity,
                    message=str(e),
                    exception=e,
                    retry_count=attempt,
                    context={"processor_id": processor.processor_id, "attempt": attempt + 1},
                )

                await self._record_error(error_info)

                # 如果是最后一次尝试,不再重试
                if attempt >= self.retry_configs[error_type].max_retries:
                    break

                # 计算重试延迟
                retry_delay = self.calculate_retry_delay(attempt, self.retry_configs[error_type])

                logger.warning(
                    f"处理器 {processor.processor_id} 第 {attempt + 1} 次尝试失败,{retry_delay:.2f}秒后重试: {e!s}"
                )
                await asyncio.sleep(retry_delay)

        # 所有重试都失败,尝试降级处理
        return await self._fallback_processing(
            processor,
            args[0] if args else None,
            args[1] if len(args) > 1 else "unknown",
            last_exception,
        )

    async def _fallback_processing(
        self, processor: BaseProcessor, data: Any, input_type: str, original_exception: Exception
    ) -> PerceptionResult:
        """降级处理"""
        processor_type = processor.__class__.__name__.lower()

        if processor_type not in self.fallback_strategies:
            # 没有降级策略,创建错误结果
            return self._create_error_result(
                data, input_type, original_exception, processor.processor_id
            )

        # 尝试降级策略
        for strategy in self.fallback_strategies[processor_type]:
            try:
                logger.info(f"尝试降级策略: {strategy.name}")

                if strategy.fallback_data is not None:
                    # 使用预定义的降级数据
                    return self._create_fallback_result(
                        data,
                        input_type,
                        strategy.fallback_data,
                        strategy.confidence_penalty,
                        processor.processor_id,
                    )

                elif strategy.fallback_processor:
                    # 使用备用处理器
                    # 这里应该实例化备用处理器
                    logger.info(f"使用备用处理器: {strategy.fallback_processor}")
                    # 简化实现
                    return self._create_fallback_result(
                        data,
                        input_type,
                        "备用处理器处理",
                        strategy.confidence_penalty,
                        processor.processor_id,
                    )

                else:
                    # 其他降级逻辑
                    continue

            except Exception as fallback_error:
                logger.error(f"降级策略 {strategy.name} 失败: {fallback_error}")
                continue

        # 所有降级策略都失败
        return self._create_error_result(
            data, input_type, original_exception, processor.processor_id
        )

    def _create_error_result(
        self, data: Any, input_type: str, exception: Exception, processor_id: str
    ) -> PerceptionResult:
        """创建错误结果"""
        error_type = self.classify_error(exception)
        severity = self.determine_severity(error_type, exception)

        return PerceptionResult(
            input_type=self._convert_input_type(input_type),
            raw_content=data,
            processed_content=None,
            features={
                "error": True,
                "error_type": error_type.value,
                "error_severity": severity.value,
                "error_message": str(exception),
                "traceback": traceback.format_exc(),
            },
            confidence=0.0,
            metadata={
                "error": True,
                "processor_id": processor_id,
                "error_timestamp": datetime.now().isoformat(),
            },
            timestamp=datetime.now(),
        )

    def _create_fallback_result(
        self,
        data: Any,
        input_type: str,
        fallback_content: Any,
        confidence_penalty: float,
        processor_id: str,
    ) -> PerceptionResult:
        """创建降级结果"""

        return PerceptionResult(
            input_type=self._convert_input_type(input_type),
            raw_content=data,
            processed_content=fallback_content,
            features={
                "fallback": True,
                "fallback_processor": processor_id,
                "confidence_penalty": confidence_penalty,
            },
            confidence=max(0.0, 0.9 - confidence_penalty),
            metadata={
                "fallback": True,
                "processor_id": processor_id,
                "fallback_timestamp": datetime.now().isoformat(),
            },
            timestamp=datetime.now(),
        )

    def _convert_input_type(self, input_type: str) -> InputType:
        """转换输入类型"""
        try:
            return InputType(input_type.lower())
        except ValueError:
            return InputType.UNKNOWN

    async def _record_error(self, error_info: ErrorInfo):
        """记录错误"""
        # 更新错误计数
        error_key = f"{error_info.error_type.value}_{error_info.severity.value}"
        self.error_counts[error_key] = self.error_counts.get(error_key, 0) + 1

        # 添加到错误详情列表
        self.error_details.append(error_info)

        # 保持错误详情列表大小
        if len(self.error_details) > 1000:
            self.error_details = self.error_details[-500:]

        # 触发错误回调
        for callback in self.error_callbacks:
            try:
                if inspect.iscoroutinefunction(callback):
                    await callback(error_info)
                else:
                    callback(error_info)
            except Exception as callback_error:
                logger.error(f"错误回调执行失败: {callback_error}")

    def add_error_callback(self, callback: Callable) -> None:
        """添加错误回调"""
        self.error_callbacks.append(callback)

    def get_error_statistics(self) -> dict[str, Any]:
        """获取错误统计"""
        total_errors = sum(self.error_counts.values())

        return {
            "total_errors": total_errors,
            "error_counts_by_type": self.error_counts,
            "recent_errors": len(
                [e for e in self.error_details if (datetime.now() - e.timestamp).seconds < 3600]
            ),
            "error_rate": total_errors / max(total_errors + 100, 1),  # 假设总请求数
            "last_error_time": (
                self.error_details[-1].timestamp.isoformat() if self.error_details else None
            ),
        }

    def clear_error_history(self) -> None:
        """清除错误历史"""
        self.error_counts.clear()
        self.error_details.clear()
        logger.info("错误历史已清除")


# 全局错误处理器实例
_global_error_handler: Optional[PerceptionErrorHandler] = None


def get_global_error_handler(config: Optional[dict[str, Any]] = None) -> PerceptionErrorHandler:
    """获取全局错误处理器"""
    global _global_error_handler
    if _global_error_handler is None:
        _global_error_handler = PerceptionErrorHandler(config)
    return _global_error_handler


# 错误处理装饰器
def handle_errors(config: Optional[dict[str, Any]] = None) -> Optional[Any]:
    """错误处理装饰器"""

    def decorator(cls) -> Any:
        # 保存原始方法
        if hasattr(cls, "process"):
            original_process = cls.process

            async def new_process(self, data: Any, input_type: str, **kwargs) -> PerceptionResult:
                # 获取全局错误处理器
                error_handler = get_global_error_handler(config)

                # 包装错误处理
                return await error_handler.execute_with_retry(
                    self, original_process, data, input_type, **kwargs
                )

            cls.process = new_process

        return cls

    return decorator


# 重试装饰器
def retry(config: Optional[dict[str, Any]] = None) -> Any:
    """重试装饰器"""

    def decorator(func) -> None:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # 这里应该实现重试逻辑
            return await func(*args, **kwargs)

        return wrapper

    return decorator

