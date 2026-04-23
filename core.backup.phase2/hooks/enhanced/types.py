#!/usr/bin/env python3
"""
Hook系统增强 - 数据类型定义

定义增强Hook系统的核心数据结构。

Author: Athena平台团队
创建时间: 2026-04-20
版本: 2.0.0
"""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


class HookState(Enum):
    """Hook生命周期状态"""

    REGISTERED = "registered"  # 已注册
    ACTIVATING = "activating"  # 激活中
    ACTIVE = "active"  # 活跃
    DEACTIVATING = "deactivating"  # 停用中
    INACTIVE = "inactive"  # 未激活
    UNREGISTERING = "unregistering"  # 卸载中
    UNREGISTERED = "unregistered"  # 已卸载
    ERROR = "error"  # 错误状态


class HookStatus(Enum):
    """Hook执行状态"""

    PENDING = "pending"  # 等待执行
    RUNNING = "running"  # 执行中
    COMPLETED = "completed"  # 已完成
    FAILED = "failed"  # 失败
    SKIPPED = "skipped"  # 已跳过
    STOPPED = "stopped"  # 被中断


@dataclass
class HookResult:
    """Hook执行结果"""

    success: bool  # 是否成功
    data: Any = None  # 返回数据
    error: str | None = None  # 错误信息
    execution_time: float = 0.0  # 执行时间（秒）
    stopped: bool = False  # 是否中断链
    modified_context: bool = False  # 是否修改了上下文
    status: HookStatus = HookStatus.COMPLETED  # 执行状态

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "success": self.success,
            "data": self.data,
            "error": self.error,
            "execution_time": self.execution_time,
            "stopped": self.stopped,
            "modified_context": self.modified_context,
            "status": self.status.value,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "HookResult":
        """从字典创建"""
        return cls(
            success=data.get("success", True),
            data=data.get("data"),
            error=data.get("error"),
            execution_time=data.get("execution_time", 0.0),
            stopped=data.get("stopped", False),
            modified_context=data.get("modified_context", False),
            status=HookStatus(data.get("status", "completed")),
        )


@dataclass
class HookMetrics:
    """Hook性能指标"""

    hook_id: str  # Hook ID
    call_count: int = 0  # 调用次数
    total_time: float = 0.0  # 总耗时（秒）
    avg_time: float = 0.0  # 平均耗时（秒）
    min_time: float = float("inf")  # 最小耗时（秒）
    max_time: float = 0.0  # 最大耗时（秒）
    error_count: int = 0  # 错误次数
    last_execution: float | None = None  # 最后执行时间戳
    success_rate: float = 1.0  # 成功率

    def update(self, execution_time: float, success: bool) -> None:
        """更新指标

        Args:
            execution_time: 执行时间（秒）
            success: 是否成功
        """
        self.call_count += 1
        self.total_time += execution_time
        self.avg_time = self.total_time / self.call_count
        self.min_time = min(self.min_time, execution_time)
        self.max_time = max(self.max_time, execution_time)

        if not success:
            self.error_count += 1

        # 计算成功率
        self.success_rate = (self.call_count - self.error_count) / self.call_count if self.call_count > 0 else 1.0

        self.last_execution = time.time()

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "hook_id": self.hook_id,
            "call_count": self.call_count,
            "total_time": self.total_time,
            "avg_time": self.avg_time,
            "min_time": self.min_time if self.min_time != float("inf") else 0.0,
            "max_time": self.max_time,
            "error_count": self.error_count,
            "last_execution": self.last_execution,
            "success_rate": self.success_rate,
        }


@dataclass
class PerformanceReport:
    """性能报告"""

    total_hooks: int  # Hook总数
    total_calls: int  # 总调用次数
    total_time: float  # 总耗时（秒）
    avg_time_per_call: float  # 平均每次调用耗时（秒）
    slowest_hook: tuple[str, float] | None  # 最慢的Hook (hook_id, time)
    fastest_hook: tuple[str, float] | None  # 最快的Hook (hook_id, time)
    error_rate: float  # 错误率
    throughput: float = 0.0  # 吞吐量（calls/s）

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "total_hooks": self.total_hooks,
            "total_calls": self.total_calls,
            "total_time": self.total_time,
            "avg_time_per_call": self.avg_time_per_call,
            "slowest_hook": self.slowest_hook,
            "fastest_hook": self.fastest_hook,
            "error_rate": self.error_rate,
            "throughput": self.throughput,
        }


@dataclass
class TraceEntry:
    """执行追踪条目"""

    hook_id: str  # Hook ID
    hook_type: str  # Hook类型
    timestamp: datetime  # 时间戳
    execution_time: float  # 执行时间（秒）
    success: bool  # 是否成功
    context_data: dict[str, Any] = field(default_factory=dict)  # 上下文数据快照
    error: str | None = None  # 错误信息

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "hook_id": self.hook_id,
            "hook_type": self.hook_type,
            "timestamp": self.timestamp.isoformat(),
            "execution_time": self.execution_time,
            "success": self.success,
            "context_data": self.context_data,
            "error": self.error,
        }


@dataclass
class BenchmarkResult:
    """基准测试结果"""

    hook_id: str  # Hook ID
    iterations: int  # 迭代次数
    total_time: float  # 总耗时（秒）
    avg_time: float  # 平均耗时（秒）
    min_time: float  # 最小耗时（秒）
    max_time: float  # 最大耗时（秒）
    p50_time: float  # P50耗时（秒）
    p95_time: float  # P95耗时（秒）
    p99_time: float  # P99耗时（秒）
    throughput: float  # 吞吐量（ops/s）

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "hook_id": self.hook_id,
            "iterations": self.iterations,
            "total_time": self.total_time,
            "avg_time": self.avg_time,
            "min_time": self.min_time,
            "max_time": self.max_time,
            "p50_time": self.p50_time,
            "p95_time": self.p95_time,
            "p99_time": self.p99_time,
            "throughput": self.throughput,
        }


@dataclass
class HookDependency:
    """Hook依赖关系"""

    hook_id: str  # Hook ID
    depends_on: list[str]  # 依赖的Hook ID列表
    required: bool = True  # 是否必须满足

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "hook_id": self.hook_id,
            "depends_on": self.depends_on,
            "required": self.required,
        }


__all__ = [
    "HookState",
    "HookStatus",
    "HookResult",
    "HookMetrics",
    "PerformanceReport",
    "TraceEntry",
    "BenchmarkResult",
    "HookDependency",
]
