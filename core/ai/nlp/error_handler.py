#!/usr/bin/env python3

"""
NLP系统错误处理和重试机制
NLP System Error Handler and Retry Mechanism

提供智能的错误处理、重试机制和优雅降级

作者: 系统管理员
创建时间: 2025-12-20
版本: v1.0.0
"""

import json
import logging
import random
import threading
import time
from enum import Enum
from functools import wraps
from typing import TYPE_CHECKING, Any, Optional

import numpy as np

if TYPE_CHECKING:
    from collections.abc import Callable

# 设置日志
logger = logging.getLogger(__name__)


class ErrorSeverity(Enum):
    """错误严重程度"""

    LOW = "low"  # 轻微错误,可以忽略
    MEDIUM = "medium"  # 中等错误,需要重试
    HIGH = "high"  # 严重错误,需要降级
    CRITICAL = "critical"  # 致命错误,需要停止


class FallbackStrategy(Enum):
    """降级策略"""

    RETRY = "retry"  # 重试
    CACHE_FALLBACK = "cache_fallback"  # 使用缓存结果
    SIMPLIFY_TASK = "simplify_task"  # 简化任务
    USE_SMALLER_MODEL = "use_smaller_model"  # 使用更小的模型
    RETURN_DEFAULT = "return_default"  # 返回默认值
    RAISE_ERROR = "raise_error"  # 抛出错误


class NLError(Exception):
    """NLP系统自定义错误基类"""

    def __init__(
        self,
        message: str,
        severity: ErrorSeverity = ErrorSeverity.MEDIUM,
        error_code: Optional[str] = None,
        context: Optional[dict[str, Any]] = None,
    ):
        super().__init__(message)
        self.message = message
        self.severity = severity
        self.error_code = error_code or "NLP_UNKNOWN"
        self.context = context or {}
        self.timestamp = time.time()


class ModelLoadError(NLError):
    """模型加载错误"""

    def __init__(self, message: str, model_name: Optional[str] = None):
        super().__init__(message, ErrorSeverity.HIGH, "MODEL_LOAD_ERROR")
        self.context["model_name"] = model_name


class InferenceError(NLError):
    """推理错误"""

    def __init__(self, message: str, operation: Optional[str] = None, input_data: Any = None):
        super().__init__(message, ErrorSeverity.MEDIUM, "INFERENCE_ERROR")
        self.context["operation"] = operation
        self.context["input_data_summary"] = str(input_data)[:100] if input_data else None


class ResourceExhaustedError(NLError):
    """资源耗尽错误"""

    def __init__(self, message: str, resource_type: Optional[str] = None):
        super().__init__(message, ErrorSeverity.HIGH, "RESOURCE_EXHAUSTED")
        self.context["resource_type"] = resource_type


class CacheError(NLError):
    """缓存错误"""

    def __init__(self, message: str, cache_key: Optional[str] = None):
        super().__init__(message, ErrorSeverity.LOW, "CACHE_ERROR")
        self.context["cache_key"] = cache_key


class ErrorHandler:
    """错误处理器"""

    def __init__(self):
        self.error_stats = {
            "total_errors": 0,
            "error_types": {},
            "error_severities": {},
            "recent_errors": [],
        }
        self.lock = threading.Lock()

        # 错误处理策略配置
        self.strategies = {
            ModelLoadError: FallbackStrategy.RETRY,
            InferenceError: FallbackStrategy.RETRY,
            ResourceExhaustedError: FallbackStrategy.SIMPLIFY_TASK,
            CacheError: FallbackStrategy.RETURN_DEFAULT,
        }

        # 重试配置
        self.retry_config = {
            "max_attempts": 3,
            "base_delay": 1.0,
            "max_delay": 30.0,
            "exponential_base": 2.0,
            "jitter": True,
        }

    def handle_error(self, error: Exception, context: Optional[dict[str, Any]] = None) -> Any:
        """处理错误"""
        with self.lock:
            self._record_error(error, context)

        logger.error(f"处理错误: {error}")

        # 确定错误类型和策略
        if isinstance(error, NLError):
            strategy = self.strategies.get(type(error), FallbackStrategy.RAISE_ERROR)
        else:
            strategy = FallbackStrategy.RETRY

        # 执行降级策略
        return self._execute_fallback_strategy(strategy, error, context)

    def _record_error(self, error: Exception, context: Optional[dict[str, Any]] = None) -> Any:
        """记录错误统计"""
        self.error_stats["total_errors"] += 1

        error_type = type(error).__name__
        self.error_stats["error_types"][error_type] = (
            self.error_stats["error_types"].get(error_type, 0) + 1
        )

        severity = error.severity.value if isinstance(error, NLError) else "medium"

        self.error_stats["error_severities"][severity] = (
            self.error_stats["error_severities"].get(severity, 0) + 1
        )

        # 记录最近的错误
        error_record = {
            "timestamp": time.time(),
            "type": error_type,
            "message": str(error),
            "context": context,
        }

        self.error_stats["recent_errors"].append(error_record)

        # 保持最近100个错误记录
        if len(self.error_stats["recent_errors"]) > 100:
            self.error_stats["recent_errors"] = self.error_stats["recent_errors"][-100:]

    def _execute_fallback_strategy(
        self, strategy: FallbackStrategy, error: Exception, context: Optional[dict[str, Any]] = None
    ) -> Any:
        """执行降级策略"""
        logger.info(f"执行降级策略: {strategy.value}")

        if strategy == FallbackStrategy.RETRY:
            raise error  # 重试由装饰器处理
        elif strategy == FallbackStrategy.CACHE_FALLBACK:
            logger.info("尝试使用缓存结果")
            return None  # 由调用方处理缓存逻辑
        elif strategy == FallbackStrategy.SIMPLIFY_TASK:
            logger.info("简化任务复杂度")
            return None  # 由调用方处理简化逻辑
        elif strategy == FallbackStrategy.USE_SMALLER_MODEL:
            logger.info("使用更小的模型")
            return None  # 由调用方处理模型切换
        elif strategy == FallbackStrategy.RETURN_DEFAULT:
            logger.info("返回默认值")
            return self._get_default_value(context)
        elif strategy == FallbackStrategy.RAISE_ERROR:
            raise error
        else:
            raise error

    def _get_default_value(self, context: Optional[dict[str, Any]] = None) -> Any:
        """根据上下文返回默认值"""
        if not context:
            return None

        operation = context.get("operation", "")

        if "encode" in operation:

            return np.zeros(768)  # 默认编码向量
        elif "extract_entities" in operation:
            return []  # 默认空实体列表
        elif "similarity" in operation:
            return 0.0  # 默认相似度
        else:
            return None

    def get_error_stats(self) -> dict[str, Any]:
        """获取错误统计"""
        with self.lock:
            return self.error_stats.copy()

    def clear_error_stats(self) -> None:
        """清空错误统计"""
        with self.lock:
            self.error_stats = {
                "total_errors": 0,
                "error_types": {},
                "error_severities": {},
                "recent_errors": [],
            }
            logger.info("错误统计已清空")


# 全局错误处理器实例
global_error_handler = None


def get_error_handler() -> ErrorHandler:
    """获取全局错误处理器实例"""
    global global_error_handler
    if global_error_handler is None:
        global_error_handler = ErrorHandler()
    return global_error_handler


def robust_retry(
    max_attempts: Optional[int] = None,
    base_delay: Optional[float] = None,
    max_delay: Optional[float] = None,
    exceptions: tuple[type[Exception], ...] = (Exception,),
    fallback_strategy: FallbackStrategy = FallbackStrategy.RAISE_ERROR,
):
    """健壮的重试装饰器"""

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            handler = get_error_handler()
            config = handler.retry_config

            # 使用配置的默认值
            attempts = max_attempts or config["max_attempts"]
            delay = base_delay or config["base_delay"]
            max_delay_value = max_delay or config["max_delay"]

            last_error = None

            for attempt in range(attempts):
                try:
                    return func(*args, **kwargs)

                except exceptions as e:
                    last_error = e
                    logger.warning(f"第 {attempt + 1} 次尝试失败: {e}")

                    if attempt == attempts - 1:
                        # 最后一次尝试失败
                        logger.error(f"所有重试均失败: {e}")
                        context = {
                            "function": func.__name__,
                            "attempt": attempt + 1,
                            "args": str(args)[:100],
                            "kwargs": str(kwargs)[:100],
                        }

                        try:
                            return handler.handle_error(e, context)
                        except Exception as fallback_error:
                            logger.error(f"降级策略也失败: {fallback_error}")
                            raise last_error from fallback_error

                    # 计算延迟时间(指数退避 + 抖动)
                    current_delay = min(
                        delay * (config["exponential_base"] ** attempt), max_delay_value
                    )

                    if config["jitter"]:
                        # 添加随机抖动,避免雷群效应
                        jitter = random.uniform(0, current_delay * 0.1)
                        current_delay += jitter

                    logger.info(f"等待 {current_delay:.2f} 秒后重试...")
                    time.sleep(current_delay)

            # 理论上不会到达这里
            assert last_error is not None
            raise last_error

        return wrapper

    return decorator


def with_fallback(
    primary_func: Callable[..., Any],
    fallback_func: Optional[Callable[..., Any]] = None,
    fallback_strategy: FallbackStrategy = FallbackStrategy.RETURN_DEFAULT,
    default_value: Any = None,
):
    """带有降级策略的函数包装器"""

    @wraps(primary_func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        try:
            return primary_func(*args, **kwargs)

        except Exception as e:
            logger.warning(f"主函数失败,尝试降级策略: {e}")
            handler = get_error_handler()

            context = {
                "function": primary_func.__name__,
                "args": str(args)[:100],
                "kwargs": str(kwargs)[:100],
            }

            if fallback_func:
                try:
                    logger.info("使用备用函数")
                    return fallback_func(*args, **kwargs)
                except Exception as fallback_error:
                    logger.error(f"备用函数也失败: {fallback_error}")

            if default_value is not None:
                logger.info("使用默认值")
                return default_value

            # 尝试错误处理器的降级策略
            try:
                return handler.handle_error(e, context)
            except Exception:
                logger.error("所有降级策略都失败")
                raise e from None

    return wrapper


def safe_execute(func: Callable[..., Any], *args: Any, **kwargs: Any) -> tuple[Any, bool]:
    """安全执行函数,返回 (结果, 是否成功)"""
    try:
        result = func(*args, **kwargs)
        return result, True
    except Exception as e:
        logger.error(f"安全执行失败: {e}")
        return None, False


class CircuitBreaker:
    """断路器模式实现"""

    def __init__(self, failure_threshold: int = 5, recovery_timeout: int = 60):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failure_count = 0
        self.last_failure_time = None
        self.state = "CLOSED"  # CLOSED, OPEN, HALF_OPEN
        self.lock = threading.Lock()

    def call(self, func: Callable[..., Any], *args: Any, **kwargs: Any) -> Any:
        """通过断路器调用函数"""
        with self.lock:
            if self.state == "OPEN":
                last_failure = self.last_failure_time
                if last_failure is not None and time.time() - last_failure > self.recovery_timeout:
                    self.state = "HALF_OPEN"
                    logger.info("断路器状态: OPEN -> HALF_OPEN")
                else:
                    raise NLError(
                        "断路器开启,拒绝调用", ErrorSeverity.HIGH, "CIRCUIT_BREAKER_OPEN"
                    )

            try:
                result = func(*args, **kwargs)

                # 成功调用,重置失败计数
                if self.state == "HALF_OPEN":
                    self.state = "CLOSED"
                    logger.info("断路器状态: HALF_OPEN -> CLOSED")

                self.failure_count = 0
                return result

            except Exception as e:
                self.failure_count += 1
                self.last_failure_time = time.time()

                if self.failure_count >= self.failure_threshold:
                    self.state = "OPEN"
                    logger.warning(f"断路器状态: CLOSED -> OPEN (失败次数: {self.failure_count})")

                raise e


# 使用示例装饰器
@robust_retry(max_attempts=3, fallback_strategy=FallbackStrategy.RETURN_DEFAULT)
def robust_inference(text: str) -> Any:
    """健壮的推理函数示例"""
    # 这里放置实际的推理逻辑
    pass


if __name__ == "__main__":
    # 测试错误处理器
    handler = ErrorHandler()

    # 模拟错误
    try:
        raise InferenceError("测试推理错误", "encode_text", "测试文本")
    except Exception as e:
        handler.handle_error(e, {"test": True})

    # 显示错误统计
    stats = handler.get_error_stats()
    print("错误统计:", json.dumps(stats, indent=2, ensure_ascii=False))

