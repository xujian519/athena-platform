#!/usr/bin/env python3
from __future__ import annotations
"""
轻量协调器 - 主协调器
Lightweight Coordinator - Main Coordinator

作者: Athena AI系统
创建时间: 2025-12-05
重构时间: 2026-01-27
版本: 2.0.0
"""

import asyncio
import inspect
import logging
from collections.abc import Callable
from datetime import datetime, timedelta
from typing import Any

from core.search.registry.tool_registry import ToolRegistry, get_tool_registry
from core.search.selector.athena_search_selector import (  # type: ignore
    AthenaSearchSelector,
    get_search_selector,
)
from core.search.standards.base_search_tool import BaseSearchTool

from .config_manager import ConfigManager
from .health_monitor import HealthMonitor
from .types import (
    Alert,
    AlertLevel,
    ConfigItem,
    ConfigType,
    HealthStatus,
    MetricPoint,
    MetricType,
)

logger = logging.getLogger(__name__)


class LightweightCoordinator:
    """
    轻量协调器

    设计原则:
    1. 轻量协调 - 不干预工具运行,只做协调和监控
    2. 配置统一 - 管理跨工具配置
    3. 指标聚合 - 收集和分析性能指标
    4. 事件传播 - 工具间事件协调
    """

    def __init__(
        self,
        registry: ToolRegistry | None = None,
        selector: AthenaSearchSelector | None = None,
        config: Optional[dict[str, Any]] = None,
    ):
        """初始化轻量协调器

        Args:
            registry: 工具注册表
            selector: 搜索选择器
            config: 配置字典
        """
        self.registry = registry or get_tool_registry()
        self.selector = selector or get_search_selector()
        self.config = config or {}

        # 初始化子模块
        self.config_manager = ConfigManager()
        self.health_monitor = HealthMonitor(
            self.registry, self._add_metric_callback
        )

        # 指标存储
        self.metrics: list[MetricPoint] = []
        self.alerts: list[Alert] = []

        # 事件处理
        self.event_handlers: dict[str, list[Callable[..., Any]]] = {}

        # 统计信息
        self.stats: dict[str, Any] = {
            "total_configs": 0,
            "total_metrics": 0,
            "total_alerts": 0,
            "start_time": datetime.now(),
        }

        # 监控任务
        self._monitoring_tasks: list[asyncio.Task] = []
        self._is_running = False

        # 初始化默认配置
        self._initialize_default_configs()
        self._initialize_alert_rules()

    async def initialize(self) -> bool:
        """初始化协调器

        Returns:
            是否初始化成功
        """
        try:
            logger.info("🚀 初始化轻量协调器...")

            # 加载配置
            await self._load_configurations()

            # 启动健康监控
            await self._start_health_monitoring()

            # 启动指标清理
            await self._start_metric_cleanup()

            self._is_running = True
            logger.info("✅ 轻量协调器初始化完成")
            return True

        except Exception as e:
            logger.error(f"❌ 轻量协调器初始化失败: {e}")
            return False

    # === 配置管理 ===

    async def set_config(
        self,
        key: str,
        value: Any,
        config_type: ConfigType,
        description: str = "",
        scope: str = "global",
        tool_name: Optional[str] = None,
    ) -> bool:
        """设置配置"""
        return await self.config_manager.set_config(
            key, value, config_type, description, scope, tool_name, self._sync_config_to_tool
        )

    def get_config(self, key: str, scope: str = "global", default: Any = None) -> Any:
        """获取配置"""
        return self.config_manager.get_config(key, scope, default)

    def subscribe_config(
        self, key: str, callback: Callable[..., Any], scope: str = "global"
    ):
        """订阅配置变更"""
        self.config_manager.subscribe_config(key, callback, scope)

    # === 指标收集 ===

    async def add_metric(
        self,
        tool_name: str,
        metric_type: MetricType,
        metric_name: str,
        value: float,
        unit: str = "",
        tags: dict[str, str] | None = None,
        metadata: Optional[dict[str, Any]] = None,
    ):
        """添加指标"""
        metric_point = MetricPoint(
            tool_name=tool_name,
            metric_type=metric_type,
            metric_name=metric_name,
            value=value,
            unit=unit,
            tags=tags or {},
            metadata=metadata or {},
        )

        self.metrics.append(metric_point)

        # 触发告警检查
        await self._check_alert_rules(metric_point)

        # 统计
        self.stats["total_metrics"] = len(self.metrics)

    # === 健康监控 ===

    async def check_tool_health(self, tool_name: str) -> HealthStatus:
        """检查工具健康状态"""
        return await self.health_monitor.check_tool_health(tool_name)

    async def check_all_tools_health(self) -> dict[str, HealthStatus]:
        """检查所有工具健康状态"""
        return await self.health_monitor.check_all_tools_health()

    # === 告警系统 ===

    async def add_alert(
        self,
        level: AlertLevel,
        title: str,
        message: str,
        tool_name: Optional[str] = None,
        metric_point: MetricPoint | None = None,
    ) -> Alert:
        """添加告警"""
        import uuid

        alert = Alert(
            id=str(uuid.uuid4()),
            level=level,
            title=title,
            message=message,
            tool_name=tool_name,
            metric_point=metric_point,
        )

        self.alerts.append(alert)
        await self._handle_alert(alert)

        self.stats["total_alerts"] = len(self.alerts)
        return alert

    # === 事件系统 ===

    def register_event_handler(
        self, event_type: str, handler: Callable[..., Any]
    ) -> None:
        """注册事件处理器"""
        if event_type not in self.event_handlers:
            self.event_handlers[event_type] = []
        self.event_handlers[event_type].append(handler)

    async def emit_event(self, event_type: str, data: dict[str, Any]):
        """触发事件"""
        if event_type in self.event_handlers:
            for handler in self.event_handlers[event_type]:
                try:
                    result = handler(data)
                    if inspect.iscoroutinefunction(handler):
                        await result
                except Exception as e:
                    logger.error(f"❌ 事件处理器错误: {e}")

    # === 内部方法 ===

    def _initialize_default_configs(self):
        """初始化默认配置"""
        default_configs = {
            "health_check_interval": 60,
            "metric_retention_days": 7,
            "alert_cooldown_seconds": 300,
        }
        for key, value in default_configs.items():
            self.config[key] = value

    def _initialize_alert_rules(self):
        """初始化告警规则"""
        self.alert_rules = [
            {
                "name": "high_error_rate",
                "condition": lambda m: m.metric_type == MetricType.ERRORS
                and m.value > 10,
                "level": AlertLevel.WARNING,
                "title": "高错误率告警",
                "message_template": "工具 {tool_name} 错误率过高: {value}",
            },
            {
                "name": "low_health_score",
                "condition": lambda m: m.metric_name == "health_score"
                and m.value < 0.7,
                "level": AlertLevel.WARNING,
                "title": "低健康评分告警",
                "message_template": "工具 {tool_name} 健康评分过低: {value}",
            },
        ]

    async def _load_configurations(self):
        """加载配置"""
        pass

    async def _sync_config_to_tool(self, tool_name: str, config_item: ConfigItem):
        """同步配置到工具"""
        try:
            tool: BaseSearchTool = self.registry.get_tool(tool_name)
            if tool and hasattr(tool, "update_config"):
                await tool.update_config({config_item.key: config_item.value})
        except Exception as e:
            logger.error(f"❌ 同步配置到工具 {tool_name} 失败: {e}")

    async def _add_metric_callback(self, **kwargs):
        """指标添加回调"""
        await self.add_metric(**kwargs)

    async def _start_health_monitoring(self):
        """启动健康监控"""
        if self.config.get("health_check_enabled", True):
            task = asyncio.create_task(self._health_monitoring_loop())
            self._monitoring_tasks.append(task)

    async def _health_monitoring_loop(self):
        """健康监控循环"""
        interval = self.config.get("health_check_interval", 60)
        while self._is_running:
            try:
                await self.check_all_tools_health()
                await asyncio.sleep(interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"❌ 健康监控错误: {e}")
                await asyncio.sleep(interval)

    async def _start_metric_cleanup(self):
        """启动指标清理"""
        task = asyncio.create_task(self._metric_cleanup_loop())
        self._monitoring_tasks.append(task)

    async def _metric_cleanup_loop(self):
        """指标清理循环"""
        retention_days = self.config.get("metric_retention_days", 7)
        while self._is_running:
            try:
                await asyncio.sleep(86400)  # 每天执行一次
                cutoff = datetime.now() - timedelta(days=retention_days)
                self.metrics = [
                    m for m in self.metrics if m.timestamp > cutoff
                ]
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"❌ 指标清理错误: {e}")

    async def _check_alert_rules(self, metric_point: MetricPoint):
        """检查告警规则"""
        for rule in self.alert_rules:
            if rule["condition"](metric_point):
                await self.add_alert(
                    level=rule["level"],
                    title=rule["title"],
                    message=rule["message_template"].format(
                        tool_name=metric_point.tool_name, value=metric_point.value
                    ),
                    tool_name=metric_point.tool_name,
                    metric_point=metric_point,
                )

    async def _handle_alert(self, alert: Alert):
        """处理告警"""
        logger.warning(
            f"🚨 告警: [{alert.level.value}] {alert.title} - {alert.message}"
        )
        await self.emit_event("alert", {"alert": alert})

    # === 统计和报告 ===

    def get_stats(self) -> dict[str, Any]:
        """获取统计信息"""
        stats = self.stats.copy()
        stats["config_manager"] = self.config_manager.get_stats()
        return stats

    def generate_health_report(self) -> dict[str, Any]:
        """生成健康报告"""
        health_status = self.health_monitor.get_all_health_status()
        return {
            "timestamp": datetime.now(),
            "tools": {
                name: {"status": h.status, "score": h.score}
                for name, h in health_status.items()
            },
            "summary": {
                "total": len(health_status),
                "healthy": sum(1 for h in health_status.values() if h.status == "healthy"),
                "warning": sum(1 for h in health_status.values() if h.status == "warning"),
                "error": sum(1 for h in health_status.values() if h.status == "error"),
                "critical": sum(
                    1 for h in health_status.values() if h.status == "critical"
                ),
            },
        }

    # === 清理 ===

    async def shutdown(self):
        """关闭协调器"""
        logger.info("🛑 关闭轻量协调器...")
        self._is_running = False

        # 取消监控任务
        for task in self._monitoring_tasks:
            if not task.done():
                task.cancel()

        # 等待任务完成
        await asyncio.gather(*self._monitoring_tasks, return_exceptions=True)

        await self._save_state()
        logger.info("✅ 轻量协调器已关闭")

    async def _save_state(self):
        """保存状态"""
        pass


__all__ = ["LightweightCoordinator"]
