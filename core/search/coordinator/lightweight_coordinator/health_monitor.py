#!/usr/bin/env python3
from __future__ import annotations
"""
轻量协调器 - 健康监控模块
Lightweight Coordinator - Health Monitor

作者: Athena AI系统
创建时间: 2025-12-05
重构时间: 2026-01-27
版本: 2.0.0
"""

import asyncio
import logging
from typing import Any

from core.search.registry.tool_registry import ToolRegistry
from core.search.standards.base_search_tool import BaseSearchTool

from .types import HealthStatus, MetricType

logger = logging.getLogger(__name__)


class HealthMonitor:
    """健康监控器"""

    def __init__(
        self, registry: ToolRegistry, metric_callback: callable | None = None
    ):
        """初始化健康监控器

        Args:
            registry: 工具注册表
            metric_callback: 指标回调函数
        """
        self.registry = registry
        self.metric_callback = metric_callback
        self.health_status: dict[str, HealthStatus] = {}

    async def check_tool_health(self, tool_name: str) -> HealthStatus:
        """检查工具健康状态

        Args:
            tool_name: 工具名称

        Returns:
            健康状态
        """
        try:
            tool: BaseSearchTool = self.registry.get_tool(tool_name)
            if not tool:
                return HealthStatus(tool_name=tool_name, status="not_found", score=0.0)

            # 执行健康检查
            health_info = await tool.health_check()

            # 计算健康评分
            score = self._calculate_health_score(tool_name, health_info)

            # 确定状态
            if score >= 0.9:
                status = "healthy"
            elif score >= 0.7:
                status = "warning"
            elif score >= 0.5:
                status = "error"
            else:
                status = "critical"

            health_status = HealthStatus(
                tool_name=tool_name, status=status, score=score, details=health_info
            )

            self.health_status[tool_name] = health_status

            # 添加指标
            if self.metric_callback:
                await self.metric_callback(
                    tool_name=tool_name,
                    metric_type=MetricType.AVAILABILITY,
                    metric_name="health_score",
                    value=score,
                    tags={"status": status},
                )

            return health_status

        except Exception as e:
            logger.error(f"❌ 检查工具 {tool_name} 健康状态失败: {e}")
            error_status = HealthStatus(
                tool_name=tool_name,
                status="error",
                score=0.0,
                details={"error": str(e)},
            )
            self.health_status[tool_name] = error_status
            return error_status

    async def check_all_tools_health(self) -> dict[str, HealthStatus]:
        """检查所有工具健康状态

        Returns:
            所有工具的健康状态字典
        """
        health_results = {}
        tool_names = self.registry.list_tools()

        tasks = [self.check_tool_health(tool_name) for tool_name in tool_names]
        health_statuses = await asyncio.gather(*tasks, return_exceptions=True)

        for tool_name, status in zip(tool_names, health_statuses, strict=False):
            if isinstance(status, Exception):
                logger.error(f"❌ 工具 {tool_name} 健康检查异常: {status}")
                health_results[tool_name] = HealthStatus(
                    tool_name=tool_name,
                    status="error",
                    score=0.0,
                    details={"error": str(status)},
                )
            else:
                health_results[tool_name] = status

        return health_results

    def _calculate_health_score(
        self, tool_name: str, health_info: dict[str, Any]
    ) -> float:
        """计算健康评分

        Args:
            tool_name: 工具名称
            health_info: 健康信息

        Returns:
            健康评分 (0.0-1.0)
        """
        score = 1.0

        # 检查基本状态
        if health_info.get("status") != "ok":
            score -= 0.3

        # 检查错误率
        error_rate = health_info.get("error_rate", 0.0)
        score -= error_rate * 0.5

        # 检查响应时间
        response_time = health_info.get("response_time_ms", 0)
        if response_time > 5000:  # 超过5秒
            score -= 0.2
        elif response_time > 2000:  # 超过2秒
            score -= 0.1

        # 检查最近失败
        recent_failures = health_info.get("recent_failures", 0)
        score -= min(recent_failures * 0.1, 0.3)

        return max(score, 0.0)

    def get_health_status(self, tool_name: str) -> HealthStatus | None:
        """获取工具健康状态

        Args:
            tool_name: 工具名称

        Returns:
            健康状态,如果不存在返回None
        """
        return self.health_status.get(tool_name)

    def get_all_health_status(self) -> dict[str, HealthStatus]:
        """获取所有工具健康状态

        Returns:
            所有工具的健康状态字典
        """
        return self.health_status.copy()


__all__ = ["HealthMonitor"]
