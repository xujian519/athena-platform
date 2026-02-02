#!/usr/bin/env python3
"""
进度跟踪器
统一的进度跟踪和报告功能
"""

import time
import logging
from typing import Optional, Dict, Any
from datetime import datetime, timedelta


class ProgressTracker:
    """进度跟踪器"""

    def __init__(self, total_items: int, name: str = "任务"):
        self.total_items = total_items
        self.current_item = 0
        self.name = name
        self.start_time = time.time()
        self.logger = logging.getLogger(__name__)
        self.last_report_time = self.start_time

    def update(self, increment: int = 1, message: str = None) -> Any:
        """更新进度"""
        self.current_item += increment
        self.current_time = time.time()

        # 每10秒或每10%报告一次
        elapsed = self.current_time - self.last_report_time
        progress_percent = (self.current_item / self.total_items) * 100

        if elapsed > 10 or (progress_percent % 10 < 1):
            self.report_progress(message)

    def report_progress(self, message: str = None) -> Any:
        """报告进度"""
        progress_percent = (self.current_item / self.total_items) * 100
        elapsed = time.time() - self.start_time

        rate = self.current_item / elapsed if elapsed > 0 else 0
        eta = (self.total_items - self.current_item) / rate if rate > 0 else 0

        progress_info = {
            'name': self.name,
            'progress': f"{self.current_item}/{self.total_items}",
            'percent': f"{progress_percent:.1f}%",
            'elapsed': f"{elapsed:.2f}s",
            'rate': f"{rate:.2f}/s",
            'eta': f"{eta:.2f}s"
        }

        if message:
            progress_info['message'] = message

        self.logger.info(f"{self.name}进度: {progress_percent:.1f}% "
                         f"({self.current_item}/{self.total_items}) "
                         f"{rate:.2f}/s ETA:{eta:.2f}s")

        if message:
            self.logger.info(f"  -> {message}")

        self.last_report_time = time.time()

    def complete(self) -> Any:
        """完成任务"""
        elapsed = time.time() - self.start_time
        rate = self.total_items / elapsed if elapsed > 0 else 0

        self.logger.info(f"\n✅ {self.name}完成!")
        self.logger.info(f"   总数: {self.total_items}")
        self.logger.info(f"   耗时: {elapsed:.2f}秒")
        self.logger.info(f"   速度: {rate:.2f}/秒")

    @property
    def progress_percent(self) -> Any:
        """获取进度百分比"""
        return (self.current_item / self.total_items) * 100


class MultiProgressTracker:
    """多任务进度跟踪器"""

    def __init__(self):
        self.tasks = {}
        self.logger = logging.getLogger(__name__)

    def add_task(self, task_name: str, total_items: int) -> None:
        """添加任务"""
        self.tasks[task_name] = ProgressTracker(total_items, task_name)

    def update_task(self, task_name: str, increment: int = 1, message: str = None) -> None:
        """更新任务进度"""
        if task_name in self.tasks:
            self.tasks[task_name].update(increment, message)

    def complete_task(self, task_name: str) -> Any:
        """完成任务"""
        if task_name in self.tasks:
            self.tasks[task_name].complete()

    def report_all(self) -> Any:
        """报告所有任务进度"""
        self.logger.info("=== 任务进度总览 ===")
        for name, tracker in self.tasks.items():
            self.logger.info(f"{name}: {tracker.progress_percent:.1f}%")
        self.logger.info("=" * 40)


# 便捷的进度跟踪装饰器
def track_progress(name: str = None) -> Any:
    """进度跟踪装饰器"""
    def decorator(func) -> None:
        def wrapper(*args, **kwargs) -> Any:
            # 尝试从参数获取总数
            total_items = kwargs.get('total_items')
            if not total_items and args:
                total_items = args[0] if isinstance(args[0], int) else None

            if total_items:
                tracker = ProgressTracker(total_items, name or func.__name__)
                try:
                    result = func(*args, **kwargs)
                    tracker.complete()
                    return result
                except Exception as e:
                    logger = logging.getLogger(__name__)
                    logger.error(f"{name}执行失败: {e}")
                    return None
            else:
                return func(*args, **kwargs)

        return decorator
    return decorator