#!/usr/bin/env python3
"""
OA答复系统重试机制
Office Action Response System Retry Mechanism

使用tenacity库实现智能重试策略

功能:
1. 指数退避重试
2. 条件重试 (根据异常类型)
3. 最大重试次数限制
4. 重试统计和监控
5. 自定义重试策略

作者: 小诺·双鱼公主
创建时间: 2026-01-26
版本: v1.0.0
"""

from __future__ import annotations
import logging
from collections.abc import Callable
from functools import wraps
from typing import Any, TypeVar

from tenacity import (
    Retrying,
    before_sleep_log,
    retry_if_exception_message,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
    wait_random_exponential,
)

from core.logging_config import setup_logging
from core.utils.error_handling import (
    KnowledgeGraphError,
    PatternExtractionError,
    WorkflowRecordError,
)

logger = setup_logging()

T = TypeVar("T")


# ===== 自定义重试装饰器 =====

def retry_on_transient_error(
    max_attempts: int = 3,
    wait_min: float = 1.0,
    wait_max: float = 10.0,
    exponential_base: int = 2,
):
    """
    重试瞬态错误 (如网络超时、临时服务不可用)

    Args:
        max_attempts: 最大尝试次数
        wait_min: 最小等待时间 (秒)
        wait_max: 最大等待时间 (秒)
        exponential_base: 指数退避基数

    Returns:
        装饰器函数

    适用场景:
        - 数据库连接超时
        - API调用临时失败
        - 网络抖动
    """

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            retrier = Retrying(
                stop=stop_after_attempt(max_attempts),
                wait=wait_random_exponential(
                    multiplier=1,
                    min=wait_min,
                    max=wait_max,
                    exp_base=exponential_base,
                ),
                before_sleep=before_sleep_log(logger, logging.WARNING),
                reraise=True,
            )

            return retrier(func, *args, **kwargs)

        return wrapper

    return decorator


def retry_on_workflow_error(
    max_attempts: int = 3,
    wait_min: float = 2.0,
    wait_max: float = 30.0,
):
    """
    重试工作流记录错误

    Args:
        max_attempts: 最大尝试次数
        wait_min: 最小等待时间 (秒)
        wait_max: 最大等待时间 (秒)

    Returns:
        装饰器函数

    适用场景:
        - 文件IO临时失败
        - 存储空间临时不足
        - 权限问题
    """

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            retrier = Retrying(
                stop=stop_after_attempt(max_attempts),
                wait=wait_exponential(
                    multiplier=1,
                    min=wait_min,
                    max=wait_max,
                ),
                retry=retry_if_exception_type(WorkflowRecordError),
                before_sleep=before_sleep_log(logger, logging.WARNING),
                reraise=True,
            )

            return retrier(func, *args, **kwargs)

        return wrapper

    return decorator


def retry_on_pattern_error(
    max_attempts: int = 2,
    wait_min: float = 1.0,
    wait_max: float = 5.0,
):
    """
    重试模式提取错误

    Args:
        max_attempts: 最大尝试次数
        wait_min: 最小等待时间 (秒)
        wait_max: 最大等待时间 (秒)

    Returns:
        装饰器函数

    适用场景:
        - 向量搜索临时失败
        - 知识图谱连接问题
        - 序列化错误
    """

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        async def async_wrapper(*args: Any, **kwargs: Any) -> T:
            retrier = Retrying(
                stop=stop_after_attempt(max_attempts),
                wait=wait_exponential(
                    multiplier=1,
                    min=wait_min,
                    max=wait_max,
                ),
                retry=retry_if_exception_type(PatternExtractionError),
                before_sleep=before_sleep_log(logger, logging.WARNING),
                reraise=True,
            )

            async def _retry():
                return await retrier(func, *args, **kwargs)

            return await _retry()

        return async_wrapper

    return decorator


def retry_on_knowledge_graph_error(
    max_attempts: int = 3,
    wait_min: float = 1.0,
    wait_max: float = 10.0,
):
    """
    重试知识图谱错误

    Args:
        max_attempts: 最大尝试次数
        wait_min: 最小等待时间 (秒)
        wait_max: 最大等待时间 (秒)

    Returns:
        装饰器函数

    适用场景:
        - 图数据库连接问题
        - 查询超时
        - 临时性约束违反
    """

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        async def async_wrapper(*args: Any, **kwargs: Any) -> T:
            retrier = Retrying(
                stop=stop_after_attempt(max_attempts),
                wait=wait_random_exponential(
                    multiplier=1,
                    min=wait_min,
                    max=wait_max,
                ),
                retry=retry_if_exception_type(KnowledgeGraphError),
                before_sleep=before_sleep_log(logger, logging.WARNING),
                reraise=True,
            )

            async def _retry():
                return await retrier(func, *args, **kwargs)

            return await _retry()

        return async_wrapper

    return decorator


# ===== 高级重试策略 =====

class RetryableOperation:
    """可重试操作的基类"""

    def __init__(
        self,
        operation_name: str,
        max_attempts: int = 3,
        timeout: float = 30.0,
    ):
        """初始化操作"""
        self.operation_name = operation_name
        self.max_attempts = max_attempts
        self.timeout = timeout
        self.attempt_count = 0

    async def execute(self) -> Any:
        """
        执行操作 (需要子类实现)

        Returns:
            操作结果
        """
        raise NotImplementedError

    async def run_with_retry(self) -> Any:
        """
        带重试地运行操作

        Returns:
            操作结果
        """
        retrier = Retrying(
            stop=stop_after_attempt(self.max_attempts),
            wait=wait_exponential(multiplier=1, min=1.0, max=10.0),
            before_sleep=self._before_sleep,
            reraise=True,
        )

        return await retrier(self._attempt)

    async def _attempt(self) -> Any:
        """单次尝试"""
        self.attempt_count += 1
        logger.info(f"尝试 {self.operation_name} (第{self.attempt_count}次)")

        try:
            result = await asyncio.wait_for(
                self.execute(),
                timeout=self.timeout,
            )
            logger.info(f"✅ {self.operation_name} 成功 (第{self.attempt_count}次尝试)")
            return result
        except Exception as e:
            logger.warning(f"❌ {self.operation_name} 失败 (第{self.attempt_count}次尝试): {e}")
            raise

    def _before_sleep(self, retry_state):
        """重试前的回调"""
        logger.warning(
            f"⏳ {self.operation_name} 将在 {retry_state.next_action.sleep}s 后重试"
            f" (尝试 {retry_state.attempt_number}/{self.max_attempts})"
        )


# ===== 条件重试 =====

def retry_if_specific_message(message: str | list[str]):
    """
    根据错误消息决定是否重试

    Args:
        message: 要匹配的错误消息

    Returns:
        重试条件函数
    """
    if isinstance(message, str):
        messages = [message]
    else:
        messages = message

    def should_retry(exception: Exception) -> bool:
        """检查是否应该重试"""
        error_msg = str(exception).lower()
        return any(msg.lower() in error_msg for msg in messages)

    return should_retry


def retry_on_network_error(max_attempts: int = 3):
    """
    重试网络相关错误

    Args:
        max_attempts: 最大尝试次数

    Returns:
        装饰器函数

    适用场景:
        - ConnectionError
        - TimeoutError
        - HTTP 5xx错误
    """
    network_keywords = [
        "connection",
        "timeout",
        "network",
        "5xx",
        "502",
        "503",
        "504",
    ]

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            retrier = Retrying(
                stop=stop_after_attempt(max_attempts),
                wait=wait_exponential(multiplier=1, min=1.0, max=10.0),
                retry=retry_if_exception_message(retry_if_specific_message(network_keywords)),
                before_sleep=before_sleep_log(logger, logging.WARNING),
                reraise=True,
            )

            return retrier(func, *args, **kwargs)

        return wrapper

    return decorator


# ===== 使用示例 =====

"""
# 示例1: 重试瞬态错误
@retry_on_transient_error(max_attempts=3)
def save_trajectory_to_file(trajectory):
    # 保存轨迹到文件
    pass

# 示例2: 重试工作流错误
@retry_on_workflow_error(max_attempts=2)
def record_workflow_step(step_data):
    # 记录工作流步骤
    pass

# 示例3: 异步重试模式错误
@retry_on_pattern_error(max_attempts=2)
async def extract_pattern(trajectory):
    # 提取模式
    pass

# 示例4: 重试网络错误
@retry_on_network_error(max_attempts=3)
def call_external_api(url, data):
    # 调用外部API
    pass

# 示例5: 使用可重试操作基类
class SavePatternOperation(RetryableOperation):
    def __init__(self, pattern):
        super().__init__(
            operation_name="保存模式",
            max_attempts=3,
        )
        self.pattern = pattern

    async def execute(self):
        # 实际的保存逻辑
        await save_pattern_to_db(self.pattern)
        return self.pattern.pattern_id

# 使用
operation = SavePatternOperation(pattern)
result = await operation.run_with_retry()
"""

import asyncio

# ===== 统计和监控 =====

class RetryStatistics:
    """重试统计"""

    def __init__(self):
        """初始化统计"""
        self.total_attempts = 0
        self.total_retries = 0
        self.total_failures = 0
        self.operation_stats: dict[str, dict[str, Any]] = {}

    def record_attempt(self, operation_name: str, success: bool, retry_count: int):
        """记录尝试"""
        self.total_attempts += 1
        self.total_retries += retry_count

        if not success:
            self.total_failures += 1

        if operation_name not in self.operation_stats:
            self.operation_stats[operation_name] = {
                "attempts": 0,
                "retries": 0,
                "failures": 0,
            }

        self.operation_stats[operation_name]["attempts"] += 1
        self.operation_stats[operation_name]["retries"] += retry_count
        if not success:
            self.operation_stats[operation_name]["failures"] += 1

    def get_summary(self) -> dict[str, Any]:
        """获取统计摘要"""
        success_rate = (
            (self.total_attempts - self.total_failures) / self.total_attempts
            if self.total_attempts > 0
            else 0.0
        )

        return {
            "total_attempts": self.total_attempts,
            "total_retries": self.total_retries,
            "total_failures": self.total_failures,
            "success_rate": success_rate,
            "avg_retries_per_attempt": (
                self.total_retries / self.total_attempts
                if self.total_attempts > 0
                else 0.0
            ),
            "operation_stats": self.operation_stats,
        }


# ===== 全局统计实例 =====

_global_retry_stats = RetryStatistics()


def get_retry_statistics() -> RetryStatistics:
    """获取全局重试统计"""
    return _global_retry_stats


if __name__ == "__main__":
    # 示例：测试重试机制
    print("重试机制模块已加载")
    print("可用的装饰器:")
    print("  - @retry_on_transient_error")
    print("  - @retry_on_workflow_error")
    print("  - @retry_on_pattern_error")
    print("  - @retry_on_knowledge_graph_error")
    print("  - @retry_on_network_error")
