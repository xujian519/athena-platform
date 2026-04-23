from __future__ import annotations
"""
性能监控模块
Performance Monitoring Module

提供性能监控装饰器和工具函数
"""

import functools
import logging
import threading
import time
from collections import defaultdict
from collections.abc import Callable
from datetime import datetime
from typing import Any

logger = logging.getLogger(__name__)


# ============================================
# 性能统计存储
# ============================================


class PerformanceStats:
    """性能统计数据"""

    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._stats = defaultdict(
                        lambda: {
                            "count": 0,
                            "total_time": 0.0,
                            "min_time": float("inf"),
                            "max_time": 0.0,
                            "last_time": None,
                            "errors": 0,
                        }
                    )
        return cls._instance

    def record(self, name: str, duration: float, success: bool = True) -> Any:
        """记录性能数据"""
        with self._lock:
            stats = self._stats[name]
            stats["count"] += 1
            stats["total_time"] += duration
            stats["min_time"] = min(stats["min_time"], duration)
            stats["max_time"] = max(stats["max_time"], duration)
            stats["last_time"] = datetime.now()
            if not success:
                stats["errors"] += 1

    def get_stats(self, name: Optional[str] = None) -> dict:
        """获取统计数据"""
        with self._lock:
            if name:
                stats = self._stats.get(name, {})
                if stats and stats["count"] > 0:
                    return {
                        "name": name,
                        "count": stats["count"],
                        "avg_time": stats["total_time"] / stats["count"],
                        "min_time": stats["min_time"],
                        "max_time": stats["max_time"],
                        "total_time": stats["total_time"],
                        "last_time": stats["last_time"],
                        "error_rate": stats["errors"] / stats["count"],
                    }
                return {}
            else:
                return {
                    name: {
                        "count": s["count"],
                        "avg_time": s["total_time"] / s["count"] if s["count"] > 0 else 0,
                        "min_time": s["min_time"] if s["count"] > 0 else 0,
                        "max_time": s["max_time"],
                        "error_rate": s["errors"] / s["count"] if s["count"] > 0 else 0,
                    }
                    for name, s in self._stats.items()
                    if s["count"] > 0
                }

    def reset(self, name: Optional[str] = None) -> Any:
        """重置统计数据"""
        with self._lock:
            if name:
                if name in self._stats:
                    del self._stats[name]
            else:
                self._stats.clear()


# 全局性能统计实例
perf_stats = PerformanceStats()


# ============================================
# 性能监控装饰器
# ============================================


def monitor_performance(
    name: Optional[str] = None, threshold: Optional[float] = None, log_slow_calls: bool = True
):
    """
    性能监控装饰器

    Args:
        name: 监控名称,默认使用函数名
        threshold: 慢调用阈值(秒),超过则记录警告
        log_slow_calls: 是否记录慢调用

    Example:
        @monitor_performance(threshold=1.0)
        async def my_function():
            pass
    """

    def decorator(func: Callable) -> Callable:
        monitor_name = name or f"{func.__module__}.{func.__name__}"

        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            start_time = time.perf_counter()
            success = True

            try:
                result = await func(*args, **kwargs)
                return result
            except Exception:
                success = False
                raise
            finally:
                duration = time.perf_counter() - start_time
                perf_stats.record(monitor_name, duration, success)

                # 记录慢调用
                if log_slow_calls and threshold and duration > threshold:
                    logger.warning(
                        f"⚠️  慢调用检测: {monitor_name} "
                        f"耗时 {duration:.3f}s (阈值: {threshold}s)"
                    )

                # 正常日志
                if success:
                    logger.info(f"✓ {monitor_name} 完成: {duration:.3f}s")
                else:
                    logger.error(f"✗ {monitor_name} 失败: {duration:.3f}s")

        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs) -> Any:
            start_time = time.perf_counter()
            success = True

            try:
                result = func(*args, **kwargs)
                return result
            except Exception:
                success = False
                raise
            finally:
                duration = time.perf_counter() - start_time
                perf_stats.record(monitor_name, duration, success)

                # 记录慢调用
                if log_slow_calls and threshold and duration > threshold:
                    logger.warning(
                        f"⚠️  慢调用检测: {monitor_name} "
                        f"耗时 {duration:.3f}s (阈值: {threshold}s)"
                    )

                # 正常日志
                if success:
                    logger.debug(f"✓ {monitor_name} 完成: {duration:.3f}s")
                else:
                    logger.error(f"✗ {monitor_name} 失败: {duration:.3f}s")

        # 根据函数类型返回对应的wrapper
        if asyncio and asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator


# ============================================
# 上下文管理器
# ============================================


class PerformanceMonitor:
    """性能监控上下文管理器"""

    def __init__(self, name: str, threshold: Optional[float] = None):
        self.name = name
        self.threshold = threshold
        self.start_time = None
        self.duration = None

    def __enter__(self):
        self.start_time = time.perf_counter()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.duration = time.perf_counter() - self.start_time
        success = exc_type is None

        perf_stats.record(self.name, self.duration, success)

        if success:
            logger.info(f"✓ {self.name} 完成: {self.duration:.3f}s")
        else:
            logger.error(f"✗ {self.name} 失败: {self.duration:.3f}s")

        if self.threshold and self.duration > self.threshold:
            logger.warning(
                f"⚠️  慢调用检测: {self.name} "
                f"耗时 {self.duration:.3f}s (阈值: {self.threshold}s)"
            )

        return False  # 不抑制异常


# ============================================
# 性能报告
# ============================================


def generate_performance_report(name: Optional[str] = None) -> dict:
    """生成性能报告"""
    stats = perf_stats.get_stats(name)

    if not stats:
        return {"message": "暂无性能数据"}

    if name:
        return {
            "监控项": name,
            "调用次数": stats["count"],
            "平均耗时": f"{stats['avg_time']:.3f}s",
            "最小耗时": f"{stats['min_time']:.3f}s",
            "最大耗时": f"{stats['max_time']:.3f}s",
            "总耗时": f"{stats['total_time']:.3f}s",
            "错误率": f"{stats['error_rate']*100:.2f}%",
            "最后调用": stats["last_time"].isoformat() if stats["last_time"] else None,
        }
    else:
        return {
            "性能监控报告": {
                k: {
                    "调用次数": v["count"],
                    "平均耗时": f"{v['avg_time']:.3f}s",
                    "错误率": f"{v['error_rate']*100:.2f}%",
                }
                for k, v in stats.items()
            },
            "生成时间": datetime.now().isoformat(),
        }


# ============================================
# 工具函数
# ============================================


def get_slow_queries(threshold: float = 1.0) -> list:
    """获取慢查询列表"""
    stats = perf_stats.get_stats()
    slow_queries = []

    for name, stat in stats.items():
        if stat["avg_time"] > threshold:
            slow_queries.append(
                {"name": name, "avg_time": stat["avg_time"], "count": stat["count"]}
            )

    return sorted(slow_queries, key=lambda x: x["avg_time"], reverse=True)


def reset_stats(name: Optional[str] = None) -> Any:
    """重置统计数据"""
    perf_stats.reset(name)
    logger.info(f"性能统计已重置: {name or '全部'}")


# ============================================
# 导入asyncio(延迟导入以避免依赖问题)
# ============================================
try:
    import asyncio
except ImportError:
    asyncio = None
