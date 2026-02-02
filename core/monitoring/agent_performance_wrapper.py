#!/usr/bin/env python3
"""
智能体性能监控包装器
Agent Performance Monitoring Wrapper

为小诺、小娜等智能体服务提供统一的性能监控功能
"""

import asyncio
import contextlib
import logging
import time
from collections.abc import Callable
from datetime import datetime
from functools import wraps
from typing import Any, Dict, Optional


# 导入性能监控器
try:
    from core.monitoring.bge_m3_performance_monitor import BGE_M3_PerformanceMonitor

    MONITOR_AVAILABLE = True
except ImportError:
    MONITOR_AVAILABLE = False
    logging.warning("BGE-M3性能监控器不可用,将使用简化监控")

logger = logging.getLogger(__name__)


class AgentPerformanceMonitor:
    """智能体性能监控器

    为小诺、小娜等智能体提供统一的性能监控接口
    """

    def __init__(
        self,
        agent_name: str,
        enable_bge_monitoring: bool = True,
        alert_thresholds: dict[str, float] | None = None,
        monitoring_interval: int = 60,
    ):
        """初始化监控器

        Args:
            agent_name: 智能体名称(xiaonuo/xiaona/yunxi等)
            enable_bge_monitoring: 是否启用BGE-M3模型监控
            alert_thresholds: 告警阈值
            monitoring_interval: 监控间隔(秒)
        """
        self.agent_name = agent_name
        self.enable_bge_monitoring = enable_bge_monitoring and MONITOR_AVAILABLE
        self.monitoring_interval = monitoring_interval

        # BGE-M3性能监控器
        self.bge_monitor: BGE_M3_PerformanceMonitor | None = None
        if self.enable_bge_monitoring:
            try:
                self.bge_monitor = BGE_M3_PerformanceMonitor(
                    alert_thresholds=alert_thresholds,
                    monitoring_interval=monitoring_interval,
                )
                logger.info(f"✅ {agent_name} BGE-M3性能监控已启用")
            except Exception as e:
                logger.warning(f"⚠️  BGE-M3监控初始化失败: {e}")

        # 基础监控统计
        self.basic_stats = {
            "start_time": datetime.now(),
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "total_processing_time": 0.0,
            "last_request_time": None,
            "peak_memory_usage": 0.0,
        }

        # 监控状态
        self.is_monitoring = False
        self.monitoring_task: asyncio.Task | None = None

    async def start_monitoring(self):
        """启动监控"""
        if self.is_monitoring:
            logger.warning(f"⚠️  {self.agent_name} 监控已在运行")
            return

        self.is_monitoring = True
        self.basic_stats["start_time"] = datetime.now()

        # 启动BGE-M3监控
        if self.bge_monitor:
            try:
                self.bge_monitor.start_monitoring()
                logger.info(f"📊 {self.agent_name} BGE-M3监控已启动")
            except Exception as e:
                logger.error(f"❌ 启动BGE-M3监控失败: {e}")

        # 启动定期监控任务
        self.monitoring_task = asyncio.create_task(self._monitoring_loop())

        logger.info(f"🚀 {self.agent_name} 性能监控已启动")

    async def stop_monitoring(self):
        """停止监控"""
        if not self.is_monitoring:
            return

        self.is_monitoring = False

        # 停止BGE-M3监控
        if self.bge_monitor:
            try:
                self.bge_monitor.stop_monitoring()
                logger.info(f"📊 {self.agent_name} BGE-M3监控已停止")
            except Exception as e:
                logger.error(f"❌ 停止BGE-M3监控失败: {e}")

        # 取消监控任务
        if self.monitoring_task:
            self.monitoring_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self.monitoring_task

        logger.info(f"🛑 {self.agent_name} 性能监控已停止")

    async def _monitoring_loop(self):
        """监控循环"""
        while self.is_monitoring:
            try:
                # 检查告警条件
                await self._check_alerts()

                # 等待下一次检查
                await asyncio.sleep(self.monitoring_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"❌ 监控循环错误: {e}")
                await asyncio.sleep(5)

    async def _check_alerts(self):
        """检查告警条件"""
        try:
            # 获取资源使用情况
            import psutil

            memory_percent = psutil.virtual_memory().percent
            cpu_percent = psutil.cpu_percent(interval=1)

            # 更新峰值内存使用
            if memory_percent > self.basic_stats["peak_memory_usage"]:
                self.basic_stats["peak_memory_usage"] = memory_percent

            # 检查告警阈值
            if self.bge_monitor:
                thresholds = self.bge_monitor.alert_thresholds

                # 内存使用告警
                if memory_percent > thresholds.get("memory_percent", 90):
                    logger.warning(f"⚠️  [{self.agent_name}] 内存使用过高: {memory_percent:.1f}%")

                # CPU使用告警
                if cpu_percent > thresholds.get("cpu_percent", 95):
                    logger.warning(f"⚠️  [{self.agent_name}] CPU使用过高: {cpu_percent:.1f}%")

                # 检查BGE-M3性能告警
                stats = self.bge_monitor.get_stats()
                if stats.total_operations > 0:
                    error_rate = stats.failed_operations / stats.total_operations
                    if error_rate > thresholds.get("error_rate", 0.05):
                        logger.warning(
                            f"⚠️  [{self.agent_name}] 错误率过高: " f"{error_rate*100:.1f}%"
                        )

                    if stats.avg_duration > thresholds.get("avg_duration", 5.0):
                        logger.warning(
                            f"⚠️  [{self.agent_name}] 平均处理时间过长: "
                            f"{stats.avg_duration:.2f}秒"
                        )

        except Exception as e:
            logger.error(f"❌ 检查告警失败: {e}")

    def record_request(
        self,
        success: bool = True,
        processing_time: float = 0.0,
        operation: str = "request",
    ):
        """记录请求

        Args:
            success: 是否成功
            processing_time: 处理时间(秒)
            operation: 操作类型
        """
        self.basic_stats["total_requests"] += 1
        self.basic_stats["last_request_time"] = datetime.now()

        if success:
            self.basic_stats["successful_requests"] += 1
        else:
            self.basic_stats["failed_requests"] += 1

        self.basic_stats["total_processing_time"] += processing_time

    def record_bge_operation(
        self,
        operation: str,
        duration: float,
        batch_size: int = 1,
        text_length: int = 0,
        token_count: int = 0,
        success: bool = True,
        error_message: str = "",
    ):
        """记录BGE-M3操作

        Args:
            operation: 操作类型(encode/encode_batch等)
            duration: 耗时(秒)
            batch_size: 批次大小
            text_length: 文本长度
            token_count: token数量
            success: 是否成功
            error_message: 错误信息
        """
        if self.bge_monitor:
            # 使用record_operation方法,它接受关键字参数
            self.bge_monitor.record_operation(
                operation=operation,
                duration=duration,
                batch_size=batch_size,
                text_length=text_length,
                token_count=token_count,
                success=success,
                error_message=error_message,
            )

    def get_performance_report(self) -> dict[str, Any]:
        """获取性能报告

        Returns:
            性能报告字典
        """
        report = {
            "agent_name": self.agent_name,
            "timestamp": datetime.now().isoformat(),
            "monitoring_enabled": self.is_monitoring,
            "bge_monitoring_enabled": self.enable_bge_monitoring,
        }

        # 基础统计
        uptime = datetime.now() - self.basic_stats["start_time"]
        total_requests = self.basic_stats["total_requests"]

        report["basic_stats"] = {
            "uptime_seconds": uptime.total_seconds(),
            "uptime_formatted": str(uptime).split(".")[0],  # 去掉微秒
            "total_requests": total_requests,
            "successful_requests": self.basic_stats["successful_requests"],
            "failed_requests": self.basic_stats["failed_requests"],
            "success_rate": (
                self.basic_stats["successful_requests"] / total_requests
                if total_requests > 0
                else 1.0
            ),
            "avg_processing_time": (
                self.basic_stats["total_processing_time"] / total_requests
                if total_requests > 0
                else 0.0
            ),
            "peak_memory_usage": self.basic_stats["peak_memory_usage"],
        }

        # BGE-M3统计
        if self.bge_monitor:
            try:
                bge_stats = self.bge_monitor.get_stats()
                report["bge_stats"] = {
                    "total_operations": bge_stats.total_operations,
                    "successful_operations": bge_stats.successful_operations,
                    "failed_operations": bge_stats.failed_operations,
                    "avg_duration": bge_stats.avg_duration,
                    "p95_duration": bge_stats.p95_duration,
                    "p99_duration": bge_stats.p99_duration,
                    "throughput_per_second": bge_stats.throughput_per_second,
                }
            except Exception as e:
                logger.error(f"❌ 获取BGE-M3统计失败: {e}")
                report["bge_stats"] = {"error": str(e)}

        # 资源使用
        try:
            import psutil

            report["resource_usage"] = {
                "cpu_percent": psutil.cpu_percent(interval=0.1),
                "memory_mb": psutil.virtual_memory().used / (1024 * 1024),
                "memory_percent": psutil.virtual_memory().percent,
            }
        except Exception as e:
            logger.error(f"❌ 获取资源使用失败: {e}")
            report["resource_usage"] = {"error": str(e)}

        return report

    def print_performance_report(self) -> Any:
        """打印性能报告"""
        report = self.get_performance_report()

        logger.info("\n" + "=" * 70)
        logger.info(f"📊 {report['agent_name']} 性能报告")
        logger.info("=" * 70)
        logger.info(f"⏰ 运行时间: {report['basic_stats']['uptime_formatted']}")
        logger.info(f"📈 总请求数: {report['basic_stats']['total_requests']}")
        logger.info(f"✅ 成功请求: {report['basic_stats']['successful_requests']}")
        logger.info(f"❌ 失败请求: {report['basic_stats']['failed_requests']}")
        logger.info(f"📊 成功率: {report['basic_stats']['success_rate']*100:.1f}%")
        logger.info(f"⏱️  平均处理时间: {report['basic_stats']['avg_processing_time']:.3f}秒")
        logger.info(f"💾 峰值内存: {report['basic_stats']['peak_memory_usage']:.1f}%")

        if "bge_stats" in report and "error" not in report["bge_stats"]:
            bge = report["bge_stats"]
            logger.info("\n🤖 BGE-M3统计:")
            logger.info(f"  总操作数: {bge['total_operations']}")
            logger.info(f"  平均耗时: {bge['avg_duration']:.3f}秒")
            logger.info(f"  P95耗时: {bge['p95_duration']:.3f}秒")
            logger.info(f"  吞吐量: {bge['throughput_per_second']:.2f} ops/秒")

        if "resource_usage" in report and "error" not in report["resource_usage"]:
            res = report["resource_usage"]
            logger.info("\n💻 当前资源:")
            logger.info(f"  CPU: {res['cpu_percent']:.1f}%")
            logger.info(f"  内存: {res['memory_mb']:.0f}MB ({res['memory_percent']:.1f}%)")

        logger.info("=" * 70 + "\n")


def monitor_performance(operation: str = "request") -> Any:
    """性能监控装饰器

    Args:
        operation: 操作类型名称

    Usage:
        @monitor_performance("encode")
        async def encode_text(text: str):
            ...
    """

    def decorator(func: Callable) -> Any:
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            # 尝试从kwargs中获取monitor实例
            monitor = kwargs.pop("monitor", None)

            start_time = time.time()
            success = True
            error_message = ""

            try:
                result = await func(*args, **kwargs)
                return result
            except Exception as e:
                success = False
                error_message = str(e)
                raise
            finally:
                duration = time.time() - start_time

                # 记录到监控器
                if monitor and isinstance(monitor, AgentPerformanceMonitor):
                    monitor.record_request(
                        success=success,
                        processing_time=duration,
                        operation=operation,
                    )

                    # 如果是BGE-M3相关操作,记录详细信息
                    if operation in ["encode", "encode_batch", "embed"]:
                        monitor.record_bge_operation(
                            operation=operation,
                            duration=duration,
                            success=success,
                            error_message=error_message,
                        )

        @wraps(func)
        def sync_wrapper(*args, **kwargs) -> Any:
            monitor = kwargs.pop("monitor", None)

            start_time = time.time()
            success = True
            error_message = ""

            try:
                result = func(*args, **kwargs)
                return result
            except Exception as e:
                success = False
                error_message = str(e)
                raise
            finally:
                duration = time.time() - start_time

                if monitor and isinstance(monitor, AgentPerformanceMonitor):
                    monitor.record_request(
                        success=success,
                        processing_time=duration,
                        operation=operation,
                    )

                    if operation in ["encode", "encode_batch", "embed"]:
                        monitor.record_bge_operation(
                            operation=operation,
                            duration=duration,
                            success=success,
                            error_message=error_message,
                        )

        # 根据函数类型返回相应的包装器
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator


def create_monitor_for_agent(
    agent_name: str, enable_bge_monitoring: bool = True, **kwargs
) -> AgentPerformanceMonitor:
    """为智能体创建监控器的便捷函数

    Args:
        agent_name: 智能体名称
        enable_bge_monitoring: 是否启用BGE-M3监控
        **kwargs: 其他参数

    Returns:
        AgentPerformanceMonitor实例
    """
    return AgentPerformanceMonitor(
        agent_name=agent_name, enable_bge_monitoring=enable_bge_monitoring, **kwargs
    )


# 预配置的监控器
def create_xiaonuo_monitor() -> AgentPerformanceMonitor:
    """创建小诺监控器"""
    return create_monitor_for_agent(
        agent_name="xiaonuo",
        enable_bge_monitoring=True,
        alert_thresholds={
            "avg_duration": 3.0,  # 小诺响应较快,3秒告警
            "error_rate": 0.03,  # 3%错误率告警
            "memory_percent": 85,  # 85%内存告警
            "cpu_percent": 90,  # 90% CPU告警
        },
    )


def create_xiaona_monitor() -> AgentPerformanceMonitor:
    """创建小娜监控器"""
    return create_monitor_for_agent(
        agent_name="xiaona",
        enable_bge_monitoring=True,
        alert_thresholds={
            "avg_duration": 10.0,  # 小娜涉及深度推理,10秒告警
            "error_rate": 0.05,  # 5%错误率告警
            "memory_percent": 90,  # 90%内存告警
            "cpu_percent": 95,  # 95% CPU告警
        },
    )


if __name__ == "__main__":
    # 测试监控器
    import asyncio

    async def test():
        # 创建小诺监控器
        monitor = create_xiaonuo_monitor()
        await monitor.start_monitoring()

        # 模拟一些操作
        for i in range(10):
            monitor.record_request(
                success=i % 10 != 0,  # 10%失败率
                processing_time=0.5 + i * 0.1,
                operation="test_request",
            )

            monitor.record_bge_operation(
                operation="encode",
                duration=0.3 + i * 0.05,
                batch_size=1,
                text_length=100,
                token_count=150,
                success=True,
            )

            await asyncio.sleep(0.1)

        # 打印报告
        monitor.print_performance_report()

        # 停止监控
        await monitor.stop_monitoring()

    asyncio.run(test())
