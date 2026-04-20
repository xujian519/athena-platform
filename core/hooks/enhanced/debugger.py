#!/usr/bin/env python3
"""
Hook调试器

提供Hook的调试和追踪功能。

Author: Athena平台团队
创建时间: 2026-04-20
版本: 2.0.0
"""
from __future__ import annotations

import asyncio
import logging
from collections import defaultdict
from datetime import datetime
from typing import Any

from ..base import HookContext
from .types import TraceEntry

logger = logging.getLogger(__name__)


class HookDebugger:
    """Hook调试器

    提供断点、追踪和可视化等调试功能。
    """

    def __init__(self):
        """初始化调试器"""
        self._breakpoints: set[str] = set()
        self._trace_log: list[TraceEntry] = []
        self._enabled = False
        self._call_counts: dict[str, int] = defaultdict(int)
        self._lock = asyncio.Lock()

        logger.info("🐛 HookDebugger初始化完成")

    def enable_debugging(self) -> None:
        """启用调试模式"""
        self._enabled = True
        logger.info("✅ 调试模式已启用")

    def disable_debugging(self) -> None:
        """禁用调试模式"""
        self._enabled = False
        logger.info("⚪ 调试模式已禁用")

    def is_enabled(self) -> bool:
        """检查调试模式是否启用

        Returns:
            bool: 是否启用
        """
        return self._enabled

    def set_breakpoint(self, hook_id: str) -> None:
        """设置断点

        Args:
            hook_id: Hook ID
        """
        self._breakpoints.add(hook_id)
        logger.info(f"🔴 断点已设置: {hook_id}")

    def remove_breakpoint(self, hook_id: str) -> None:
        """移除断点

        Args:
            hook_id: Hook ID
        """
        self._breakpoints.discard(hook_id)
        logger.info(f"⚪ 断点已移除: {hook_id}")

    def has_breakpoint(self, hook_id: str) -> bool:
        """检查是否有断点

        Args:
            hook_id: Hook ID

        Returns:
            bool: 是否有断点
        """
        return hook_id in self._breakpoints

    def clear_breakpoints(self) -> None:
        """清空所有断点"""
        self._breakpoints.clear()
        logger.info("🗑️ 所有断点已清空")

    async def trace_execution(
        self,
        hook_id: str,
        hook_type: str,
        context: HookContext,
        execution_time: float,
        success: bool,
        error: str | None = None,
    ) -> None:
        """追踪Hook执行

        Args:
            hook_id: Hook ID
            hook_type: Hook类型
            context: Hook上下文
            execution_time: 执行时间
            success: 是否成功
            error: 错误信息
        """
        if not self._enabled:
            return

        async with self._lock:
            self._call_counts[hook_id] += 1

            # 创建追踪条目
            entry = TraceEntry(
                hook_id=hook_id,
                hook_type=hook_type,
                timestamp=datetime.now(),
                execution_time=execution_time,
                success=success,
                context_data=self._capture_context(context),
                error=error,
            )

            self._trace_log.append(entry)

            # 检查断点
            if hook_id in self._breakpoints:
                logger.warning(f"🛑 断点触发: {hook_id}")
                # 这里可以添加断点处理逻辑

    def _capture_context(self, context: HookContext) -> dict[str, Any]:
        """捕获上下文数据快照

        Args:
            context: Hook上下文

        Returns:
            dict: 上下文数据快照
        """
        # 只捕获非敏感数据
        snapshot = {
            "hook_type": context.hook_type.value,
            "data_keys": list(context.data.keys()),
        }

        # 限制数据大小
        for key, value in context.data.items():
            if isinstance(value, (str, int, float, bool, type(None))):
                snapshot[key] = value
            else:
                snapshot[key] = f"<{type(value).__name__}>"

        return snapshot

    async def get_trace_log(self, limit: int | None = None) -> list[TraceEntry]:
        """获取执行追踪日志

        Args:
            limit: 返回条数限制

        Returns:
            list[TraceEntry]: 追踪日志
        """
        async with self._lock:
            if limit:
                return self._trace_log[-limit:]
            return self._trace_log.copy()

    async def get_call_counts(self) -> dict[str, int]:
        """获取Hook调用次数

        Returns:
            dict[str, int]: Hook ID到调用次数的映射
        """
        async with self._lock:
            return self._call_counts.copy()

    async def clear_trace_log(self) -> None:
        """清空追踪日志"""
        async with self._lock:
            self._trace_log.clear()
            self._call_counts.clear()
            logger.info("🗑️ 追踪日志已清空")

    def visualize_execution(self) -> str:
        """可视化执行流程（生成Mermaid图表）

        Returns:
            str: Mermaid图表代码
        """
        if not self._trace_log:
            return "graph TD\n    NoData[无执行数据]"

        lines = ["graph TD"]
        node_map = {}
        node_id = 0

        for entry in self._trace_log:
            # 创建节点
            node_name = f"Hook{node_id}"
            label = f"{entry.hook_id}\\n({entry.execution_time*1000:.2f}ms)"
            if not entry.success:
                label += f"\\n❌ {entry.error or 'Failed'}"

            lines.append(f"    {node_name}[\"{label}\"]")
            node_map[entry.hook_id] = node_name
            node_id += 1

            # 创建连接
            if node_id > 1:
                prev_node = f"Hook{node_id - 2}"
                lines.append(f"    {prev_node} --> {node_name}")

        # 添加统计
        lines.append("\n    %% 统计信息")
        lines.append(f"    TotalCalls[总调用: {len(self._trace_log)}次]")

        return "\n".join(lines)

    def get_statistics(self) -> dict[str, Any]:
        """获取调试统计信息

        Returns:
            dict: 统计信息
        """
        total_calls = len(self._trace_log)
        successful_calls = sum(1 for e in self._trace_log if e.success)
        failed_calls = total_calls - successful_calls

        total_time = sum(e.execution_time for e in self._trace_log)
        avg_time = total_time / total_calls if total_calls > 0 else 0.0

        hook_stats = defaultdict(lambda: {"calls": 0, "errors": 0, "total_time": 0.0})
        for entry in self._trace_log:
            stats = hook_stats[entry.hook_id]
            stats["calls"] += 1
            if not entry.success:
                stats["errors"] += 1
            stats["total_time"] += entry.execution_time

        return {
            "total_calls": total_calls,
            "successful_calls": successful_calls,
            "failed_calls": failed_calls,
            "success_rate": successful_calls / total_calls if total_calls > 0 else 0.0,
            "total_time": total_time,
            "avg_time": avg_time,
            "hook_stats": dict(hook_stats),
            "breakpoints": list(self._breakpoints),
            "enabled": self._enabled,
        }


__all__ = [
    "HookDebugger",
]
