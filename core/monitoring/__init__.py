#!/usr/bin/env python3
"""
监控模块
Monitoring Module
"""

import logging
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


class MonitoringEngine:
    """监控引擎 - 集成性能监控能力"""

    def __init__(self, agent_id: str, config: dict | None = None):
        self.agent_id = agent_id
        self.config = config or {}
        self.initialized = False
        self.performance_monitor = None
        self.enable_performance_monitoring = self.config.get("enable_performance_monitoring", True)

    async def initialize(self):
        """初始化监控系统"""
        logger.info(f"📊 启动监控引擎: {self.agent_id}")

        try:
            # 初始化性能监控系统
            if self.enable_performance_monitoring:
                from .performance_monitor import get_performance_monitor_instance

                self.performance_monitor = await get_performance_monitor_instance(
                    self.agent_id, self.config.get("performance_monitoring", {})
                )
                logger.info(f"✅ 性能监控系统集成完成: {self.agent_id}")
            else:
                logger.info(f"📝 性能监控功能已禁用: {self.agent_id}")

        except Exception as e:
            logger.warning(f"⚠️ 性能监控系统初始化失败,使用基础监控功能: {e}")
            self.performance_monitor = None

        self.initialized = True

    async def get_monitoring_status(self) -> dict[str, Any]:
        """获取监控状态"""
        if not self.initialized:
            raise RuntimeError("监控系统未初始化")

        if self.performance_monitor:
            performance_summary = await self.performance_monitor.get_performance_summary()
        else:
            performance_summary = {"status": "disabled", "message": "性能监控未启用"}

        return {
            "agent_id": self.agent_id,
            "monitoring_enabled": self.enable_performance_monitoring,
            "performance_monitoring": performance_summary,
            "config": self.config,
            "timestamp": "2025-12-04T12:48:35.000000",
        }

    async def get_performance_metrics(self) -> dict[str, Any]:
        """获取性能指标"""
        if not self.initialized:
            raise RuntimeError("监控系统未初始化")

        if self.performance_monitor:
            return await self.performance_monitor.get_detailed_metrics()
        else:
            return {"error": "性能监控未启用", "agent_id": self.agent_id}

    def record_metric(self, metric_type: str, name: str, value: float, **kwargs) -> Any:
        """记录性能指标"""
        if not self.performance_monitor:
            return False

        try:
            if metric_type == "counter":
                self.performance_monitor.metrics_collector.increment_counter(
                    name, value, kwargs.get("tags")
                )
            elif metric_type == "gauge":
                self.performance_monitor.metrics_collector.set_gauge(
                    name, value, kwargs.get("tags")
                )
            elif metric_type == "timer":
                self.performance_monitor.metrics_collector.record_timer(
                    name, value, kwargs.get("tags")
                )
            elif metric_type == "histogram":
                self.performance_monitor.metrics_collector.record_histogram(
                    name, value, kwargs.get("tags")
                )
            else:
                logger.warning(f"未知的指标类型: {metric_type}")
                return False

            return True

        except Exception as e:
            logger.error(f"记录性能指标失败: {e}")
            return False

    async def add_alert_rule(self, metric_name: str, condition: str, threshold: float, **kwargs):
        """添加告警规则"""
        if not self.performance_monitor:
            return False

        try:
            self.performance_monitor.register_custom_alert(
                metric_name=metric_name, condition=condition, threshold=threshold, **kwargs
            )
            return True

        except Exception as e:
            logger.error(f"添加告警规则失败: {e}")
            return False

    def register_callback(self, event_type: str, callback) -> None:
        """注册回调函数"""
        if not hasattr(self, "_callbacks"):
            self._callbacks = {}
        if event_type not in self._callbacks:
            self._callbacks[event_type] = []
        self._callbacks[event_type].append(callback)

    async def shutdown(self):
        logger.info(f"🔄 关闭监控引擎: {self.agent_id}")

        if self.performance_monitor:
            await self.performance_monitor.shutdown()

        self.initialized = False

    @classmethod
    async def initialize_global(cls):
        if not hasattr(cls, "global_instance"):
            cls.global_instance = cls("global", {})
            await cls.global_instance.initialize()
        return cls.global_instance

    @classmethod
    async def shutdown_global(cls):
        if hasattr(cls, "global_instance") and cls.global_instance:
            await cls.global_instance.shutdown()
            del cls.global_instance


__all__ = ["MonitoringEngine"]
