#!/usr/bin/env python3
"""
执行模块 - 配置常量
Execution Module - Configuration Constants

这个模块定义了执行系统中使用的所有配置常量,
避免魔法数字散布在代码中,提高可维护性。

作者: Athena平台团队
版本: v1.0.0
创建时间: 2026-01-24
"""

from dataclasses import dataclass
from typing import Any

# =============================================================================
# 并发控制常量
# =============================================================================


class ConcurrencyLimits:
    """并发限制常量"""

    # 默认并发任务数
    DEFAULT_MAX_CONCURRENT = 10

    # 最大并发任务数
    MAX_CONCURRENT_TASKS = 100

    # 最大并发操作数
    MAX_CONCURRENT_OPERATIONS = 1000

    # 默认工作线程数
    DEFAULT_MAX_WORKERS = 10

    # 最大工作线程数(通常为CPU核心数的2倍)
    MAX_WORKERS_MULTIPLIER = 2


# =============================================================================
# 超时配置常量
# =============================================================================


class TimeoutLimits:
    """超时限制常量"""

    # 默认任务超时时间(秒)
    DEFAULT_TASK_TIMEOUT = 300.0  # 5分钟

    # 最小任务超时时间(秒)
    MIN_TASK_TIMEOUT = 1.0

    # 最大任务超时时间(秒)
    MAX_TASK_TIMEOUT = 3600.0  # 1小时

    # 默认API调用超时(秒)
    DEFAULT_API_TIMEOUT = 30.0

    # 默认HTTP请求超时(秒)
    DEFAULT_HTTP_TIMEOUT = 30.0

    # 死锁检测超时(秒)
    DEADLOCK_TIMEOUT = 30.0

    # 饥饿检测超时(秒)
    STARVATION_TIMEOUT = 60.0


# =============================================================================
# 队列配置常量
# =============================================================================


class QueueLimits:
    """队列限制常量"""

    # 默认任务队列大小
    DEFAULT_QUEUE_SIZE = 10000

    # 最大任务队列大小
    MAX_QUEUE_SIZE = 100000

    # 队列检查间隔(秒)
    QUEUE_CHECK_INTERVAL = 0.1

    # 队列等待超时(秒)
    QUEUE_WAIT_TIMEOUT = 1.0


# =============================================================================
# 重试配置常量
# =============================================================================


class RetryLimits:
    """重试限制常量"""

    # 默认最大重试次数
    DEFAULT_MAX_RETRIES = 3

    # 最大重试次数
    MAX_RETRIES = 10

    # 重试延迟基数(秒)
    RETRY_DELAY_BASE = 1.0


# =============================================================================
# 资源限制常量
# =============================================================================


class ResourceLimits:
    """资源限制常量"""

    # 默认内存限制(MB)
    DEFAULT_MEMORY_LIMIT = 512

    # 默认CPU核心数
    DEFAULT_CPU_CORES = 1.0

    # 默认磁盘IO限制(MB/s)
    DEFAULT_DISK_IO_LIMIT = 10.0

    # 默认网络带宽限制(Mbps)
    DEFAULT_NETWORK_LIMIT = 1.0

    # 默认GPU内存限制(MB)
    DEFAULT_GPU_MEMORY_LIMIT = 0.0


# =============================================================================
# 监控配置常量
# =============================================================================


class MonitoringLimits:
    """监控限制常量"""

    # 监控采样间隔(秒)
    SAMPLING_INTERVAL = 1.0

    # 统计信息更新间隔(秒)
    STATS_UPDATE_INTERVAL = 10.0

    # 健康检查间隔(秒)
    HEALTH_CHECK_INTERVAL = 30.0

    # 死锁检测间隔(秒)
    DEADLOCK_CHECK_INTERVAL = 5.0

    # 队列大小警告阈值
    QUEUE_SIZE_WARNING_THRESHOLD = 5000


# =============================================================================
# 任务优先级常量
# =============================================================================


class PriorityValues:
    """任务优先级值"""

    CRITICAL = 1  # 关键任务
    HIGH = 2  # 高优先级
    NORMAL = 3  # 普通优先级
    LOW = 4  # 低优先级
    BACKGROUND = 5  # 后台任务


# =============================================================================
# 执行模式常量
# =============================================================================


class ExecutionModes:
    """执行模式常量"""

    SEQUENTIAL = "sequential"  # 顺序执行
    PARALLEL = "parallel"  # 并行执行
    CONDITIONAL = "conditional"  # 条件执行


# =============================================================================
# 配置数据类
# =============================================================================


@dataclass
class ExecutionConfig:
    """
    执行引擎配置数据类

    提供默认配置值和可配置的选项。
    """

    # 并发配置
    max_concurrent: int = ConcurrencyLimits.DEFAULT_MAX_CONCURRENT
    max_workers: int = ConcurrencyLimits.DEFAULT_MAX_WORKERS

    # 超时配置
    task_timeout: float = TimeoutLimits.DEFAULT_TASK_TIMEOUT
    api_timeout: float = TimeoutLimits.DEFAULT_API_TIMEOUT

    # 队列配置
    queue_size: int = QueueLimits.DEFAULT_QUEUE_SIZE

    # 重试配置
    max_retries: int = RetryLimits.DEFAULT_MAX_RETRIES

    # 资源配置
    memory_limit: int = ResourceLimits.DEFAULT_MEMORY_LIMIT
    cpu_cores: float = ResourceLimits.DEFAULT_CPU_CORES

    # 监控配置
    enable_monitoring: bool = True
    enable_deadlock_detection: bool = True
    enable_starvation_detection: bool = True

    # 其他配置
    enable_fair_scheduling: bool = True
    save_state_on_shutdown: bool = True

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "max_concurrent": self.max_concurrent,
            "max_workers": self.max_workers,
            "task_timeout": self.task_timeout,
            "api_timeout": self.api_timeout,
            "queue_size": self.queue_size,
            "max_retries": self.max_retries,
            "memory_limit": self.memory_limit,
            "cpu_cores": self.cpu_cores,
            "enable_monitoring": self.enable_monitoring,
            "enable_deadlock_detection": self.enable_deadlock_detection,
            "enable_starvation_detection": self.enable_starvation_detection,
            "enable_fair_scheduling": self.enable_fair_scheduling,
            "save_state_on_shutdown": self.save_state_on_shutdown,
        }

    @classmethod
    def from_dict(cls, config: dict[str, Any]) -> ExecutionConfig:
        """从字典创建配置"""
        return cls(
            max_concurrent=config.get("max_concurrent", ConcurrencyLimits.DEFAULT_MAX_CONCURRENT),
            max_workers=config.get("max_workers", ConcurrencyLimits.DEFAULT_MAX_WORKERS),
            task_timeout=config.get("task_timeout", TimeoutLimits.DEFAULT_TASK_TIMEOUT),
            api_timeout=config.get("api_timeout", TimeoutLimits.DEFAULT_API_TIMEOUT),
            queue_size=config.get("queue_size", QueueLimits.DEFAULT_QUEUE_SIZE),
            max_retries=config.get("max_retries", RetryLimits.DEFAULT_MAX_RETRIES),
            memory_limit=config.get("memory_limit", ResourceLimits.DEFAULT_MEMORY_LIMIT),
            cpu_cores=config.get("cpu_cores", ResourceLimits.DEFAULT_CPU_CORES),
            enable_monitoring=config.get("enable_monitoring", True),
            enable_deadlock_detection=config.get("enable_deadlock_detection", True),
            enable_starvation_detection=config.get("enable_starvation_detection", True),
            enable_fair_scheduling=config.get("enable_fair_scheduling", True),
            save_state_on_shutdown=config.get("save_state_on_shutdown", True),
        )


# =============================================================================
# 默认配置实例
# =============================================================================

# 默认执行配置
DEFAULT_EXECUTION_CONFIG = ExecutionConfig()

# 高性能执行配置
HIGH_PERFORMANCE_CONFIG = ExecutionConfig(
    max_concurrent=50,
    max_workers=20,
    queue_size=50000,
)

# 低资源执行配置
LOW_RESOURCE_CONFIG = ExecutionConfig(
    max_concurrent=5,
    max_workers=2,
    queue_size=1000,
    memory_limit=256,
    cpu_cores=0.5,
)


# =============================================================================
# 导出所有常量和配置
# =============================================================================

__all__ = [
    # 默认配置
    "DEFAULT_EXECUTION_CONFIG",
    "HIGH_PERFORMANCE_CONFIG",
    "LOW_RESOURCE_CONFIG",
    # 并发限制
    "ConcurrencyLimits",
    # 配置类
    "ExecutionConfig",
    # 执行模式
    "ExecutionModes",
    # 监控限制
    "MonitoringLimits",
    # 优先级值
    "PriorityValues",
    # 队列限制
    "QueueLimits",
    # 资源限制
    "ResourceLimits",
    # 重试限制
    "RetryLimits",
    # 超时限制
    "TimeoutLimits",
]
