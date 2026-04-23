#!/usr/bin/env python3
from __future__ import annotations
"""
服务监控仪表板
Service Monitoring Dashboard

实时监控所有智能体服务的健康状态和性能指标

作者: 小诺·双鱼座 💖
创建: 2025-01-12
版本: v1.0.0
"""

import asyncio
import contextlib
import logging
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Any

from .service_discovery import (
    get_service_discovery,
    get_service_registry,
    initialize_default_services,
)

logger = logging.getLogger(__name__)


class ServiceMetrics:
    """服务指标收集器"""

    def __init__(self):
        """初始化指标收集器"""
        # 指标历史数据 - 存储带时间戳的度量数据
        self.response_times: dict[str, list[dict[str, Any]], defaultdict(list)  # type: ignore[assignment]
        self.request_counts: dict[str, list[dict[str, Any]], defaultdict(list)  # type: ignore[assignment]
        self.error_rates: dict[str, list[dict[str, Any]], defaultdict(list)  # type: ignore[assignment]
        self.health_history: dict[str, list[dict[str, Any]], defaultdict(list)  # type: ignore[assignment]

        # 时间窗口
        self.time_window = timedelta(minutes=10)
        self.max_samples = 100

        logger.info("📊 服务指标收集器已初始化")

    def record_request(
        self,
        agent_id: str,
        response_time: float,
        success: bool,
        timestamp: datetime | None = None,
    ):
        """记录请求指标"""
        if timestamp is None:
            timestamp = datetime.now()

        # 清理过期数据
        self._cleanup_expired_data(agent_id, timestamp)

        # 记录响应时间
        self.response_times[agent_id].append({"value": response_time, "timestamp": timestamp})

        # 记录请求数
        self.request_counts[agent_id].append({"value": 1, "timestamp": timestamp})

        # 记录错误
        self.error_rates[agent_id].append({"value": 0 if success else 1, "timestamp": timestamp})

        # 限制样本数量
        self._limit_samples(agent_id)

    def record_health_check(self, agent_id: str, is_healthy: bool) -> Any:
        """记录健康检查结果"""
        self.health_history[agent_id].append({"value": is_healthy, "timestamp": datetime.now()})

        # 限制样本数量
        if len(self.health_history[agent_id]) > self.max_samples:
            self.health_history[agent_id].pop(0)

    def _cleanup_expired_data(self, agent_id: str, current_time: datetime) -> Any:
        """清理过期数据"""
        cutoff_time = current_time - self.time_window

        # 清理响应时间
        self.response_times[agent_id] = [
            r for r in self.response_times[agent_id] if r["timestamp"] > cutoff_time
        ]

        # 清理请求数
        self.request_counts[agent_id] = [
            r for r in self.request_counts[agent_id] if r["timestamp"] > cutoff_time
        ]

        # 清理错误率
        self.error_rates[agent_id] = [
            r for r in self.error_rates[agent_id] if r["timestamp"] > cutoff_time
        ]

    def _limit_samples(self, agent_id: str) -> Any:
        """限制样本数量"""
        if len(self.response_times[agent_id]) > self.max_samples:
            self.response_times[agent_id].pop(0)

        if len(self.request_counts[agent_id]) > self.max_samples:
            self.request_counts[agent_id].pop(0)

        if len(self.error_rates[agent_id]) > self.max_samples:
            self.error_rates[agent_id].pop(0)

    def get_metrics(self, agent_id: str) -> dict[str, Any]:
        """获取服务指标"""
        # 响应时间统计
        response_times_data = [r["value"] for r in self.response_times[agent_id]]
        avg_response_time = (
            sum(response_times_data) / len(response_times_data) if response_times_data else 0
        )
        max_response_time = max(response_times_data) if response_times_data else 0
        min_response_time = min(response_times_data) if response_times_data else 0

        # 请求统计
        request_count = len(self.request_counts[agent_id])

        # 错误率统计
        error_data = [e["value"] for e in self.error_rates[agent_id]]
        error_rate = sum(error_data) / len(error_data) if error_data else 0

        # 健康状态
        health_data = self.health_history[agent_id]
        if health_data:
            healthy_count = sum(1 for h in health_data if h["value"])
            health_percentage = healthy_count / len(health_data) * 100
        else:
            health_percentage = 100

        return {
            "agent_id": agent_id,
            "avg_response_time": round(avg_response_time, 3),
            "max_response_time": round(max_response_time, 3),
            "min_response_time": round(min_response_time, 3),
            "request_count": request_count,
            "error_rate": round(error_rate, 3),
            "health_percentage": round(health_percentage, 1),
            "timestamp": datetime.now().isoformat(),
        }

    def get_all_metrics(self) -> dict[str, dict[str, Any]]:
        """获取所有服务指标"""
        all_agent_ids = set()
        all_agent_ids.update(self.response_times.keys())
        all_agent_ids.update(self.request_counts.keys())
        all_agent_ids.update(self.error_rates.keys())

        return {agent_id: self.get_metrics(agent_id) for agent_id in all_agent_ids}


class ServiceMonitor:
    """服务监控器"""

    def __init__(self):
        """初始化服务监控器"""
        self.registry = get_service_registry()
        self.metrics = ServiceMetrics()
        self.monitoring_task = None
        self.is_running = False

        logger.info("📡 服务监控器已初始化")

    async def start(self):
        """启动监控"""
        if self.is_running:
            return

        self.is_running = True
        self.monitoring_task = asyncio.create_task(self._monitoring_loop())
        logger.info("🚀 服务监控器已启动")

    async def stop(self):
        """停止监控"""
        self.is_running = False

        if self.monitoring_task:
            self.monitoring_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self.monitoring_task

        logger.info("🛑 服务监控器已停止")

    async def _monitoring_loop(self):
        """监控循环"""
        while self.is_running:
            try:
                await self._collect_metrics()
                await asyncio.sleep(10)  # 每10秒收集一次
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"❌ 监控失败: {e}")
                await asyncio.sleep(5)

    async def _collect_metrics(self):
        """收集指标"""
        import aiohttp

        for agent_id, instances in self.registry.services.items():
            for instance in instances:
                try:
                    # 模拟请求并测量响应时间
                    start_time = datetime.now()
                    health_url = f"{instance.endpoint}/health"

                    async with aiohttp.ClientSession() as session, session.get(
                        health_url, timeout=aiohttp.ClientTimeout(total=5)
                    ) as response:
                        response_time = (datetime.now() - start_time).total_seconds()
                        is_healthy = response.status == 200

                        # 记录指标
                        self.metrics.record_request(agent_id, response_time, is_healthy)
                        self.metrics.record_health_check(agent_id, is_healthy)

                        # 更新实例状态
                        if is_healthy:
                            instance.mark_healthy()
                        else:
                            instance.mark_unhealthy()

                        instance.record_request(is_healthy, response_time)

                except Exception as e:
                    logger.warning(f"⚠️ 监控检查失败: {instance.endpoint} - {e}")
                    self.metrics.record_request(agent_id, 5.0, False)
                    self.metrics.record_health_check(agent_id, False)
                    instance.mark_unhealthy()

    def get_dashboard(self) -> dict[str, Any]:
        """获取监控仪表板数据"""
        return {
            "timestamp": datetime.now().isoformat(),
            "summary": self.registry.get_statistics(),
            "services": self._get_services_status(),
            "metrics": self.metrics.get_all_metrics(),
        }

    def _get_services_status(self) -> dict[str, Any]:
        """获取所有服务状态"""
        services = {}

        for agent_id, instances in self.registry.services.items():
            healthy_instances = [s for s in instances if s.is_healthy]
            unhealthy_instances = [s for s in instances if not s.is_healthy]

            services[agent_id] = {
                "total_instances": len(instances),
                "healthy_instances": len(healthy_instances),
                "unhealthy_instances": len(unhealthy_instances),
                "instances": [s.to_dict() for s in instances],
            }

        return services

    def print_dashboard(self) -> Any:
        """打印监控仪表板"""
        dashboard = self.get_dashboard()

        print("\n" + "=" * 80)
        print("📊 智能体服务监控仪表板")
        print("=" * 80)
        print(f"⏰ 时间: {dashboard['timestamp']}")
        print()

        # 摘要
        summary = dashboard["summary"]
        print("📈 服务摘要:")
        print(f"  • 智能体数量: {summary['total_agents']}")
        print(f"  • 实例总数: {summary['total_instances']}")
        print(f"  • 健康实例: {summary['healthy_instances']} ✅")
        print(f"  • 不健康实例: {summary['unhealthy_instances']} ❌")
        print(f"  • 总请求数: {summary['total_requests']}")
        print(f"  • 成功请求: {summary['successful_requests']}")
        print(f"  • 成功率: {summary['overall_success_rate']:.1%}")
        print()

        # 服务状态
        print("🔍 服务状态:")
        for agent_id, status in dashboard["services"].items():
            health_icon = "✅" if status["unhealthy_instances"] == 0 else "⚠️"
            print(f"  {health_icon} {agent_id}:")
            print(f"      实例: {status['healthy_instances']}/{status['total_instances']} 健康")

            for instance in status["instances"]:
                status_icon = "✅" if instance["is_healthy"] else "❌"
                print(f"      {status_icon} {instance['endpoint']}")
                print(
                    f"         请求数: {instance['total_requests']}, "
                    f"成功率: {instance['success_rate']:.1%}, "
                    f"平均响应: {instance['average_response_time']:.3f}s"
                )
        print()

        # 性能指标
        print("📊 性能指标:")
        for agent_id, metrics in dashboard["metrics"].items():
            print(f"  {agent_id}:")
            print(f"    • 平均响应时间: {metrics['avg_response_time']:.3f}s")
            print(f"    • 最大响应时间: {metrics['max_response_time']:.3f}s")
            print(f"    • 请求数量: {metrics['request_count']}")
            print(f"    • 错误率: {metrics['error_rate']:.1%}")
            print(f"    • 健康度: {metrics['health_percentage']:.1f}%")
        print()

        print("=" * 80)


# ==================== 全局单例 ====================

_service_monitor: ServiceMonitor | None = None


def get_service_monitor() -> ServiceMonitor:
    """获取服务监控器单例"""
    global _service_monitor
    if _service_monitor is None:
        _service_monitor = ServiceMonitor()
    return _service_monitor


async def start_monitoring():
    """启动服务监控"""
    # 初始化默认服务
    initialize_default_services()

    # 启动服务发现
    discovery = get_service_discovery()
    await discovery.start()

    # 启动服务监控
    monitor = get_service_monitor()
    await monitor.start()

    logger.info("✅ 服务监控已启动")


async def stop_monitoring():
    """停止服务监控"""
    discovery = get_service_discovery()
    await discovery.stop()

    monitor = get_service_monitor()
    await monitor.stop()

    logger.info("🛑 服务监控已停止")


if __name__ == "__main__":
    # 测试代码
    async def test():
        """测试服务监控"""
        await start_monitoring()

        print("\n" + "=" * 80)
        print("📡 服务监控测试")
        print("=" * 80)

        # 运行监控一段时间
        print("\n⏳ 监控运行中...")
        for i in range(6):
            await asyncio.sleep(10)

            # 打印仪表板
            print(f"\n--- 监控报告 {i+1}/6 ---")
            monitor = get_service_monitor()
            monitor.print_dashboard()

        # 停止监控
        await stop_monitoring()

        print("\n" + "=" * 80)
        print("✅ 测试完成")
        print("=" * 80)

    asyncio.run(test())
