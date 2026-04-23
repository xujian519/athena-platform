#!/usr/bin/env python3

"""
小诺容错机制和降级策略
Xiaonuo Fault Tolerance and Degradation Strategies

提供系统级别的容错处理和智能降级策略

功能:
1. 异常检测和处理
2. 自动重试机制
3. 智能降级策略
4. 熔断器模式
5. 故障恢复机制

作者: 小诺AI团队
日期: 2025-12-18
"""

import os
import random
import sys
import threading
import time
import traceback
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import TYPE_CHECKING, Any, TypeVar, Optional

from core.logging_config import setup_logging

if TYPE_CHECKING:
    from collections.abc import Callable

# 添加模块路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 配置日志
# setup_logging()  # 日志配置已移至模块导入
logger = setup_logging()

T = TypeVar("T")


class ErrorType(Enum):
    """错误类型"""

    NETWORK_ERROR = "network_error"  # 网络错误
    TIMEOUT_ERROR = "timeout_error"  # 超时错误
    DECODE_ERROR = "decode_error"  # 解码错误
    VALIDATION_ERROR = "validation_error"  # 验证错误
    PROCESSING_ERROR = "processing_error"  # 处理错误
    MEMORY_ERROR = "memory_error"  # 内存错误
    RATE_LIMIT_ERROR = "rate_limit_error"  # 限流错误
    AUTHENTICATION_ERROR = "auth_error"  # 认证错误
    UNKNOWN_ERROR = "unknown_error"  # 未知错误


class CircuitState(Enum):
    """熔断器状态"""

    CLOSED = "closed"  # 关闭状态(正常工作)
    OPEN = "open"  # 开启状态(熔断)
    HALF_OPEN = "half_open"  # 半开状态(试探性恢复)


class DegradationLevel(Enum):
    """降级级别"""

    NONE = "none"  # 无降级
    LIGHT = "light"  # 轻度降级
    MEDIUM = "medium"  # 中度降级
    HEAVY = "heavy"  # 重度降级
    CRITICAL = "critical"  # 临界降级


@dataclass
class ErrorContext:
    """错误上下文"""

    error_type: ErrorType
    error_message: str
    timestamp: datetime
    retry_count: int = 0
    context_data: dict[str, Any] = field(default_factory=dict)
    stack_trace: Optional[str] = None


@dataclass
class RetryConfig:
    """重试配置"""

    max_attempts: int = 3
    base_delay: float = 1.0
    max_delay: float = 60.0
    exponential_base: float = 2.0
    jitter: bool = True
    retry_on: list[ErrorType] = field(
        default_factory=lambda: [
            ErrorType.NETWORK_ERROR,
            ErrorType.TIMEOUT_ERROR,
            ErrorType.RATE_LIMIT_ERROR,
        ]
    )


@dataclass
class CircuitBreakerConfig:
    """熔断器配置"""

    failure_threshold: int = 5  # 失败阈值
    recovery_timeout: float = 60.0  # 恢复超时
    expected_exception: type = Exception
    success_threshold: int = 3  # 成功阈值(半开状态)


class CircuitBreaker:
    """熔断器实现"""

    def __init__(self, config: CircuitBreakerConfig):
        self.config = config
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time: Optional[datetime] = None
        self.lock = threading.Lock()

    def __call__(self, func: Callable[..., T]) -> Callable[..., T]:
        """装饰器实现"""

        def wrapper(*args: Any, **kwargs: Any) -> T:
            if not self.allow_request():
                raise Exception("Circuit breaker is OPEN")

            try:
                result = func(*args, **kwargs)
                self.on_success()
                return result
            except Exception:
                self.on_failure()
                raise

        return wrapper

    def allow_request(self) -> bool:
        """是否允许请求"""
        with self.lock:
            if self.state == CircuitState.CLOSED:
                return True
            elif self.state == CircuitState.OPEN:
                return self._should_attempt_reset()
            else:  # HALF_OPEN
                return True

    def on_success(self) -> Any:
        """成功时调用"""
        with self.lock:
            if self.state == CircuitState.HALF_OPEN:
                self.success_count += 1
                if self.success_count >= self.config.success_threshold:
                    self.state = CircuitState.CLOSED
                    self.failure_count = 0
                    self.success_count = 0
                    logger.info("🔄 Circuit breaker transitioned to CLOSED")
            elif self.state == CircuitState.CLOSED:
                self.failure_count = max(0, self.failure_count - 1)

    def on_failure(self) -> Any:
        """失败时调用"""
        with self.lock:
            self.failure_count += 1
            self.last_failure_time = datetime.now()

            if (
                self.state == CircuitState.CLOSED
                and self.failure_count >= self.config.failure_threshold
            ):
                self.state = CircuitState.OPEN
                logger.warning("⚠️ Circuit breaker transitioned to OPEN")
            elif self.state == CircuitState.HALF_OPEN:
                self.state = CircuitState.OPEN
                logger.warning("⚠️ Circuit breaker transitioned back to OPEN")

    def _should_attempt_reset(self) -> bool:
        """是否应该尝试重置"""
        if self.last_failure_time is None:
            return True

        elapsed = (datetime.now() - self.last_failure_time).total_seconds()
        return elapsed >= self.config.recovery_timeout

    def get_state(self) -> dict[str, Any]:
        """获取熔断器状态"""
        with self.lock:
            return {
                "state": self.state.value,
                "failure_count": self.failure_count,
                "success_count": self.success_count,
                "last_failure_time": (
                    self.last_failure_time.isoformat() if self.last_failure_time else None
                ),
                "config": {
                    "failure_threshold": self.config.failure_threshold,
                    "recovery_timeout": self.config.recovery_timeout,
                    "success_threshold": self.config.success_threshold,
                },
            }


class FaultToleranceManager:
    """容错管理器"""

    def __init__(self):
        """初始化容错管理器"""
        # 错误统计
        self.error_stats: defaultdict[str | ErrorType, list[Any] = defaultdict(list)
        self.error_counts: defaultdict[str | ErrorType, int] = defaultdict(int)
        self.error_lock = threading.Lock()

        # 熔断器注册表
        self.circuit_breakers: dict[str, CircuitBreaker] = {}

        # 降级策略注册表
        self.degradation_strategies: dict[ErrorType, list[Callable[..., Any]] = {}

        # 重试配置
        self.retry_configs: dict[str, RetryConfig] = {}

        # 健康检查
        self.health_checks: dict[str, Callable[..., Any]] = {}

        # 恢复机制
        self.recovery_handlers: dict[ErrorType, list[Callable[..., Any]] = {}

        logger.info("🚀 容错管理器初始化完成")

    def register_circuit_breaker(self, name: str, config: CircuitBreakerConfig) -> CircuitBreaker:
        """注册熔断器"""
        breaker = CircuitBreaker(config)
        self.circuit_breakers[name] = breaker
        logger.info(f"📋 注册熔断器: {name}")
        return breaker

    def register_degradation_strategy(
        self, error_type: ErrorType, strategy: Callable[..., Any]
    ) -> Any:
        """注册降级策略"""
        if error_type not in self.degradation_strategies:
            self.degradation_strategies[error_type]] = []
        self.degradation_strategies[error_type].append(strategy)
        logger.info(f"📋 注册降级策略: {error_type.value}")

    def register_retry_config(self, name: str, config: RetryConfig) -> Any:
        """注册重试配置"""
        self.retry_configs[name] = config
        logger.info(f"📋 注册重试配置: {name}")

    def register_health_check(self, name: str, check_func: Callable[..., Any]) -> Any:
        """注册健康检查"""
        self.health_checks[name] = check_func
        logger.info(f"📋 注册健康检查: {name}")

    def register_recovery_handler(self, error_type: ErrorType, handler: Callable[..., Any]) -> Any:
        """注册恢复处理器"""
        if error_type not in self.recovery_handlers:
            self.recovery_handlers[error_type]] = []
        self.recovery_handlers[error_type].append(handler)
        logger.info(f"📋 注册恢复处理器: {error_type.value}")

    def handle_error(self, error: Exception, context: Optional[dict[str, Any]] = None) -> ErrorContext:
        """处理错误"""
        error_type = self._classify_error(error)
        error_message = str(error)
        stack_trace = traceback.format_exc()

        error_context = ErrorContext(
            error_type=error_type,
            error_message=error_message,
            timestamp=datetime.now(),
            context_data=context or {},
            stack_trace=stack_trace,
        )

        # 记录错误
        self._record_error(error_context)

        # 触发恢复机制
        self._trigger_recovery(error_context)

        return error_context

    def execute_with_fallback(
        self,
        primary_func: Callable[[], T],
        fallback_func: Callable[[], T],
        error_context: Optional[dict[str, Any]] = None,
    ) -> T:
        """执行带降级的函数"""
        try:
            return primary_func()
        except Exception as e:
            error_ctx = self.handle_error(e, error_context)
            logger.warning(f"⚠️ 主要函数失败,尝试降级: {error_ctx.error_type.value}")

            # 尝试降级策略
            if error_context is not None:
                fallback_result = self._try_degradation_strategies(
                    error_ctx.error_type, error_context
                )
                if fallback_result is not None:
                    return fallback_result

            # 执行降级函数
            return fallback_func()

    def execute_with_retry(
        self, func: Callable[..., T], config_name: Optional[str] = None, *args: Any, **kwargs: Any
    ) -> T:
        """执行带重试的函数"""
        config = self.retry_configs.get(config_name or "default", RetryConfig())
        last_exception = None

        for attempt in range(config.max_attempts):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                last_exception = e
                error_type = self._classify_error(e)

                # 检查是否应该重试
                if error_type not in config.retry_on:
                    break

                if attempt < config.max_attempts - 1:
                    # 计算延迟
                    delay = self._calculate_retry_delay(attempt, config)
                    logger.warning(
                        f"⚠️ 尝试 {attempt + 1}/{config.max_attempts} 失败,{delay:.1f}s后重试: {e}"
                    )
                    time.sleep(delay)

        # 所有重试都失败了
        if last_exception is not None:
            final_error = last_exception
            self.handle_error(final_error)
            raise final_error
        else:
            raise RuntimeError("All retry attempts failed but no exception was recorded")

    def _classify_error(self, error: Exception) -> ErrorType:
        """分类错误类型"""
        error_message = str(error).lower()
        error_type_name = type(error).__name__.lower()

        if "timeout" in error_message or "timeout" in error_type_name:
            return ErrorType.TIMEOUT_ERROR
        elif "connection" in error_message or "network" in error_message:
            return ErrorType.NETWORK_ERROR
        elif "decode" in error_message or "encoding" in error_message:
            return ErrorType.DECODE_ERROR
        elif "validation" in error_message or "invalid" in error_message:
            return ErrorType.VALIDATION_ERROR
        elif (
            "modules/modules/memory/modules/memory/modules/memory/memory" in error_message
            or "out of memory" in error_message
        ):
            return ErrorType.MEMORY_ERROR
        elif "rate limit" in error_message or "too many requests" in error_message:
            return ErrorType.RATE_LIMIT_ERROR
        elif "authentication" in error_message or "unauthorized" in error_message:
            return ErrorType.AUTHENTICATION_ERROR
        elif "processing" in error_message:
            return ErrorType.PROCESSING_ERROR
        else:
            return ErrorType.UNKNOWN_ERROR

    def _record_error(self, error_context: ErrorContext) -> Any:
        """记录错误"""
        with self.error_lock:
            self.error_stats[error_context.error_type].append(error_context)
            self.error_counts[error_context.error_type] += 1

            # 保持最近1000个错误记录
            if len(self.error_stats[error_context.error_type]) > 1000:
                self.error_stats[error_context.error_type] = self.error_stats[
                    error_context.error_type
                ][-1000:]

    def _trigger_recovery(self, error_context: ErrorContext) -> Any:
        """触发恢复机制"""
        if error_context.error_type in self.recovery_handlers:
            for handler in self.recovery_handlers[error_context.error_type]:
                try:
                    handler(error_context)
                except Exception as e:
                    logger.error(f"❌ 恢复处理器失败: {e}")

    def _try_degradation_strategies(
        self, error_type: ErrorType, context: dict[str, Any]]
    ) -> Optional[Any]:
        """尝试降级策略"""
        if error_type not in self.degradation_strategies:
            return None

        for strategy in self.degradation_strategies[error_type]:
            try:
                result = strategy(context)
                if result is not None:
                    logger.info(f"✅ 降级策略成功: {error_type.value}")
                    return result
            except Exception as e:
                logger.warning(f"⚠️ 降级策略失败: {e}")

        return None

    def _calculate_retry_delay(self, attempt: int, config: RetryConfig) -> float:
        """计算重试延迟"""
        delay = config.base_delay * (config.exponential_base**attempt)
        delay = min(delay, config.max_delay)

        if config.jitter:
            # 添加抖动
            jitter = delay * 0.1 * random.random()
            delay += jitter

        return delay

    def get_current_degradation_level(self) -> DegradationLevel:
        """获取当前降级级别"""
        sum(self.error_counts.values())
        recent_errors = self._count_recent_errors(minutes=5)

        if recent_errors == 0:
            return DegradationLevel.NONE
        elif recent_errors < 5:
            return DegradationLevel.LIGHT
        elif recent_errors < 20:
            return DegradationLevel.MEDIUM
        elif recent_errors < 50:
            return DegradationLevel.HEAVY
        else:
            return DegradationLevel.CRITICAL

    def _count_recent_errors(self, minutes: int = 5) -> int:
        """计算最近几分钟的错误数"""
        cutoff_time = datetime.now() - timedelta(minutes=minutes)
        count = 0

        with self.error_lock:
            for errors in self.error_stats.values():
                count += sum(1 for error in errors if error.timestamp >= cutoff_time)

        return count

    def get_system_health(self) -> dict[str, Any]:
        """获取系统健康状态"""
        # 执行健康检查
        health_results = {}
        for name, check_func in self.health_checks.items():
            try:
                health_results[name] = check_func()
            except Exception as e:
                health_results[name]] = {"status": "unhealthy", "error": str(e)}

        # 获取熔断器状态
        circuit_breaker_states = {
            name: breaker.get_state() for name, breaker in self.circuit_breakers.items()
        }

        # 计算降级级别
        degradation_level = self.get_current_degradation_level()

        # 错误统计
        recent_errors = self._count_recent_errors(minutes=10)
        total_errors = sum(self.error_counts.values())

        return {
            "degradation_level": degradation_level.value,
            "recent_errors_10min": recent_errors,
            "total_errors": total_errors,
            "error_counts": {
                str(k.value) if isinstance(k, ErrorType) else str(k): v
                for k, v in self.error_counts.items()
            },
            "health_checks": health_results,
            "circuit_breakers": circuit_breaker_states,
            "timestamp": datetime.now().isoformat(),
        }

    def get_error_analysis(self) -> dict[str, Any]:
        """获取错误分析"""
        analysis: dict[str, Any] = {"error_trends": {}, "error_patterns": {}, "recommendations": []}

        with self.error_lock:
            # 分析错误趋势
            for error_type, errors in self.error_stats.items():
                if errors:
                    # 按小时分组
                    hourly_counts = defaultdict(int)
                    for error in errors:
                        hour = error.timestamp.strftime("%Y-%m-%d %H:00")
                        hourly_counts[hour] += 1

                    error_key = (
                        str(error_type.value)
                        if isinstance(error_type, ErrorType)
                        else str(error_type)
                    )
                    trends_dict = analysis.get("error_trends")
                    if isinstance(trends_dict, dict):
                        trends_dict[error_key] = dict(hourly_counts)

            # 分析错误模式
            for error_type, errors in self.error_stats.items():
                if errors:
                    # 最常见的错误消息
                    message_counts = defaultdict(int)
                    for error in errors:
                        message_counts[error.error_message] += 1

                    # Convert to Counter to use most_common
                    from collections import Counter

                    error_key = (
                        str(error_type.value)
                        if isinstance(error_type, ErrorType)
                        else str(error_type)
                    )
                    patterns_dict = analysis.get("error_patterns")
                    if isinstance(patterns_dict, dict):
                        patterns_dict[error_key] = dict(Counter(message_counts).most_common(5))

        # 生成建议
        analysis["recommendations"] = self._generate_recommendations()

        return analysis

    def _generate_recommendations(self) -> list[str]:
        """生成优化建议"""
        recommendations = []

        # 基于错误频率的建议
        total_errors = sum(self.error_counts.values())
        if total_errors > 100:
            recommendations.append("系统错误率较高,建议检查基础设施和代码质量")

        # 基于错误类型的建议
        for error_type, count in self.error_counts.items():
            if error_type == ErrorType.TIMEOUT_ERROR and count > 10:
                recommendations.append("超时错误较多,建议优化网络配置和增加超时时间")
            elif error_type == ErrorType.MEMORY_ERROR and count > 5:
                recommendations.append("内存错误较多,建议优化内存使用和增加内存容量")
            elif error_type == ErrorType.RATE_LIMIT_ERROR and count > 10:
                recommendations.append("限流错误较多,建议实现请求限流和缓存机制")

        return recommendations


# 预定义的降级策略
class FallbackStrategies:
    """预定义的降级策略"""

    @staticmethod
    def empty_response(context: dict[str, Any]) -> dict[str, Any]:
        """空响应降级"""
        return {"status": "degraded", "message": "服务暂时不可用,请稍后重试", "data": None}

    @staticmethod
    def cached_response(context: dict[str, Any]) -> dict[str, Any]:
        """缓存响应降级"""
        # 这里应该从缓存获取响应
        # 简化实现
        return {"status": "cached", "message": "返回缓存数据", "data": None}

    @staticmethod
    def simplified_response(context: dict[str, Any]) -> dict[str, Any]:
        """简化响应降级"""
        return {"status": "simplified", "message": "返回简化结果", "data": {}}

    @staticmethod
    def default_nlp_response(context: dict[str, Any]) -> dict[str, Any]:
        """默认NLP响应降级"""
        return {
            "intent": "query",
            "confidence": 0.5,
            "selected_tools": ["web_search"],
            "parameters": {},
            "warnings": ["服务降级,返回默认结果"],
        }


# 使用示例和装饰器
def with_fallback(
    fallback_func: Callable[..., Any] = None, error_context: Optional[dict[str, Any]] = None
) -> Any:
    """带降级的装饰器"""

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            ft_manager = FaultToleranceManager()
            return ft_manager.execute_with_fallback(
                lambda: func(*args, **kwargs),
                fallback_func or FallbackStrategies.empty_response,  # type: ignore[arg-type]
                error_context,
            )

        return wrapper

    if fallback_func is None:
        # 被用作无参数装饰器
        def real_decorator(func: Callable[..., Any]) -> Callable[..., Any]:
            return decorator(func)

        return real_decorator
    else:
        return decorator(fallback_func)


def with_retry(config_name: str = "default") -> Any:
    """带重试的装饰器"""

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            ft_manager = FaultToleranceManager()
            return ft_manager.execute_with_retry(func, config_name, *args, **kwargs)

        return wrapper

    return decorator


def with_circuit_breaker(breaker_name: str) -> Any:
    """带熔断器的装饰器"""

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        ft_manager = FaultToleranceManager()
        if breaker_name in ft_manager.circuit_breakers:
            return ft_manager.circuit_breakers[breaker_name](func)
        else:
            logger.warning(f"⚠️ 熔断器 {breaker_name} 未找到,直接执行函数")
            return func

    return decorator


# 使用示例
if __name__ == "__main__":
    print("🧪 测试容错机制和降级策略...")

    # 创建容错管理器
    ft_manager = FaultToleranceManager()

    # 注册熔断器
    ft_manager.register_circuit_breaker(
        "test_api", CircuitBreakerConfig(failure_threshold=3, recovery_timeout=10.0)
    )

    # 注册重试配置
    ft_manager.register_retry_config(
        "network_retry", RetryConfig(max_attempts=5, base_delay=0.5, exponential_base=1.5)
    )

    # 注册降级策略
    ft_manager.register_degradation_strategy(
        ErrorType.NETWORK_ERROR, FallbackStrategies.cached_response
    )

    # 注册健康检查
    def check_database() -> dict[str, Any]:
        # 模拟健康检查
        return {"status": "healthy", "response_time": 50}

    ft_manager.register_health_check("infrastructure/infrastructure/database", check_database)

    # 测试函数
    @with_retry("network_retry")
    def unreliable_network_call() -> Any:
        import random

        if random.random() < 0.7:  # 70%失败率
            raise Exception("Network timeout")
        return "Success"

    @with_fallback(FallbackStrategies.default_nlp_response)
    def nlp_processing(text: str) -> Any:
        import random

        if random.random() < 0.3:  # 30%失败率
            raise Exception("Processing failed")
        return {"intent": "search", "confidence": 0.9, "selected_tools": ["web_search"]}

    print("\n🔄 测试重试机制...")
    try:
        result = unreliable_network_call()
        print(f"   结果: {result}")
    except Exception as e:
        print(f"   最终失败: {e}")

    print("\n🔄 测试降级机制...")
    result = nlp_processing("测试文本")
    print(f"   降级结果: {result}")

    print("\n📊 系统健康状态:")
    health = ft_manager.get_system_health()
    print(f"   降级级别: {health['degradation_level']}")
    print(f"   最近错误数: {health['recent_errors_10min']}")
    print(f"   健康检查: {health['health_checks']}")

    print("\n✅ 容错机制和降级策略测试完成!")

