#!/usr/bin/env python3
"""
性能指标收集插件 - Phase 2.3示例插件

Metrics Plugin - 收集和上报上下文操作的性能指标

功能:
- 执行时间统计
- Token使用统计
- 操作成功率统计
- 性能瓶颈分析

作者: Athena平台团队
创建时间: 2026-04-24
"""

import logging
import time
from collections import defaultdict
from typing import Any, Dict, List, Optional

from ..base_context import BaseContextPlugin, BaseContext

logger = logging.getLogger(__name__)


class MetricsPlugin(BaseContextPlugin):
    """
    性能指标收集插件

    收集和统计上下文操作的性能指标。

    配置参数:
    - enabled_metrics: 启用的指标类型列表
    - sample_rate: 采样率（0.0-1.0，默认1.0）
    - export_interval: 导出间隔（秒）
    """

    def __init__(self):
        super().__init__(
            plugin_name="metrics",
            plugin_version="1.0.0",
            dependencies=[],
        )
        self._enabled_metrics = ["execution_time", "token_count", "success_rate"]
        self._sample_rate = 1.0
        self._export_interval = 60

        # 指标存储
        self._execution_times = defaultdict(list)
        self._token_counts = defaultdict(list)
        self._operation_counts = defaultdict(lambda: {"success": 0, "failure": 0})
        self._start_times = {}

    async def initialize(self, config: Dict[str, Any]) -> None:
        """
        初始化指标插件

        Args:
            config: 配置参数
        """
        await super().initialize(config)

        self._enabled_metrics = config.get("enabled_metrics", self._enabled_metrics)
        self._sample_rate = config.get("sample_rate", 1.0)
        self._export_interval = config.get("export_interval", 60)

        logger.info(
            f"✅ 指标插件初始化: metrics={self._enabled_metrics}, "
            f"sample_rate={self._sample_rate}"
        )

    async def execute(self, _context: BaseContext, **kwargs) -> dict[str, Any]:
        """
        收集指标

        Args:
            _context: 上下文对象（未使用）
            **kwargs: 执行参数
                - operation: 操作名称
                - start_time: 开始时间（可选）
                - token_count: Token数量（可选）
                - success: 是否成功（默认True）

        Returns:
            dict[str, Any]: 指标结果
        """
        operation = kwargs.get("operation", "unknown")
        start_time = kwargs.get("start_time")
        token_count = kwargs.get("token_count")
        success = kwargs.get("success", True)

        results = {}

        # 采样检查
        import random

        if random.random() > self._sample_rate:
            return {"sampled": False}

        # 1. 执行时间统计
        if "execution_time" in self._enabled_metrics and start_time is not None:
            exec_time = time.time() - start_time
            self._execution_times[operation].append(exec_time)
            results["execution_time"] = exec_time

        # 2. Token统计
        if "token_count" in self._enabled_metrics and token_count is not None:
            self._token_counts[operation].append(token_count)
            results["token_count"] = token_count

        # 3. 成功率统计
        if "success_rate" in self._enabled_metrics:
            if success:
                self._operation_counts[operation]["success"] += 1
            else:
                self._operation_counts[operation]["failure"] += 1
            results["success"] = success

        logger.debug(f"📊 指标收集: {operation}, results={list(results.keys())}")

        return {
            "sampled": True,
            "metrics": results,
        }

    async def start_timing(self, operation: str) -> str:
        """
        开始计时

        Args:
            operation: 操作名称

        Returns:
            str: 计时ID
        """
        timing_id = f"{operation}_{time.time()}"
        self._start_times[timing_id] = time.time()
        return timing_id

    async def end_timing(self, timing_id: str) -> float:
        """
        结束计时

        Args:
            timing_id: 计时ID

        Returns:
            float: 执行时间（秒）
        """
        start_time = self._start_times.pop(timing_id, None)
        if start_time is None:
            return 0.0
        return time.time() - start_time

    def get_statistics(self) -> dict[str, Any]:
        """
        获取统计摘要

        Returns:
            dict[str, Any]: 统计摘要
        """
        stats = {
            "execution_time": {},
            "token_count": {},
            "success_rate": {},
        }

        # 执行时间统计
        for operation, times in self._execution_times.items():
            if times:
                stats["execution_time"][operation] = {
                    "count": len(times),
                    "avg": sum(times) / len(times),
                    "min": min(times),
                    "max": max(times),
                }

        # Token统计
        for operation, counts in self._token_counts.items():
            if counts:
                stats["token_count"][operation] = {
                    "count": len(counts),
                    "total": sum(counts),
                    "avg": sum(counts) / len(counts),
                }

        # 成功率统计
        for operation, counts in self._operation_counts.items():
            total = counts["success"] + counts["failure"]
            if total > 0:
                stats["success_rate"][operation] = {
                    "success": counts["success"],
                    "failure": counts["failure"],
                    "rate": counts["success"] / total,
                }

        return stats

    def reset_statistics(self) -> None:
        """重置所有统计"""
        self._execution_times.clear()
        self._token_counts.clear()
        self._operation_counts.clear()
        logger.info("📊 统计已重置")

    def export_metrics(self) -> dict[str, Any]:
        """
        导出指标数据

        Returns:
            dict[str, Any]: 指标数据
        """
        return self.get_statistics()


__all__ = ["MetricsPlugin"]
