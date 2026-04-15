"""
Athena Service Discovery - Health Check Plugins
服务发现系统健康检查插件实现

Author: Athena AI Team
Version: 2.0.0
"""

import asyncio
import logging
import statistics
import time
from abc import ABC, abstractmethod
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

import aiohttp
import grpc

from .core_service_registry import HealthCheckConfig, HealthStatus, ServiceInstance, ServiceRegistry

logger = logging.getLogger(__name__)


class HealthCheckType(Enum):
    """健康检查类型"""

    HTTP = "http"
    HTTPS = "https"
    TCP = "tcp"
    GRPC = "grpc"
    GRAPHQL = "graphql"
    SCRIPT = "script"


@dataclass
class HealthCheckResult:
    """健康检查结果"""

    status: HealthStatus
    duration: float
    message: str
    timestamp: datetime
    details: dict[str, Any] = field(default_factory=dict)


class HealthChecker(ABC):
    """健康检查器基类"""

    def __init__(self, config: HealthCheckConfig):
        self.config = config

    @abstractmethod
    async def check(self, instance: ServiceInstance) -> HealthCheckResult:
        """执行健康检查"""
        pass


class HTTPHealthChecker(HealthChecker):
    """HTTP健康检查器"""

    async def check(self, instance: ServiceInstance) -> HealthCheckResult:
        """HTTP健康检查"""
        start_time = time.time()

        try:
            # 构建检查URL
            scheme = "https" if instance.protocol.value == "https" else "http"
            url = f"{scheme}://{instance.host}:{instance.port}{self.config.http_path}"

            # 执行HTTP检查
            timeout = aiohttp.ClientTimeout(total=self.config.timeout)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(url, headers=self.config.headers) as response:
                    duration = time.time() - start_time

                    # 检查状态码
                    if response.status in self.config.expected_codes:
                        return HealthCheckResult(
                            status=HealthStatus.HEALTHY,
                            duration=duration,
                            message=f"HTTP check passed with status {response.status}",
                            timestamp=datetime.now(),
                            details={
                                "url": url,
                                "status_code": response.status,
                                "response_headers": dict(response.headers),
                            },
                        )
                    else:
                        return HealthCheckResult(
                            status=HealthStatus.UNHEALTHY,
                            duration=duration,
                            message=f"HTTP check failed: unexpected status {response.status}",
                            timestamp=datetime.now(),
                            details={
                                "url": url,
                                "status_code": response.status,
                                "expected_codes": self.config.expected_codes,
                            },
                        )

        except asyncio.TimeoutError:
            return HealthCheckResult(
                status=HealthStatus.UNHEALTHY,
                duration=time.time() - start_time,
                message="HTTP check timeout",
                timestamp=datetime.now(),
            )
        except Exception as e:
            return HealthCheckResult(
                status=HealthStatus.UNHEALTHY,
                duration=time.time() - start_time,
                message=f"HTTP check error: {str(e)}",
                timestamp=datetime.now(),
            )


class TCPHealthChecker(HealthChecker):
    """TCP健康检查器"""

    async def check(self, instance: ServiceInstance) -> HealthCheckResult:
        """TCP连接检查"""
        start_time = time.time()

        try:
            # 尝试TCP连接
            future = asyncio.open_connection(instance.host, instance.port)
            reader, writer = await asyncio.wait_for(future, timeout=self.config.timeout)

            duration = time.time() - start_time
            writer.close()
            await writer.wait_closed()

            return HealthCheckResult(
                status=HealthStatus.HEALTHY,
                duration=duration,
                message="TCP connection successful",
                timestamp=datetime.now(),
                details={"host": instance.host, "port": instance.port},
            )

        except asyncio.TimeoutError:
            return HealthCheckResult(
                status=HealthStatus.UNHEALTHY,
                duration=time.time() - start_time,
                message="TCP connection timeout",
                timestamp=datetime.now(),
            )
        except Exception as e:
            return HealthCheckResult(
                status=HealthStatus.UNHEALTHY,
                duration=time.time() - start_time,
                message=f"TCP connection error: {str(e)}",
                timestamp=datetime.now(),
            )


class GRPCHealthChecker(HealthChecker):
    """gRPC健康检查器"""

    async def check(self, instance: ServiceInstance) -> HealthCheckResult:
        """gRPC健康检查"""
        start_time = time.time()

        try:
            # 创建gRPC通道
            channel = grpc.insecure_channel(f"{instance.host}:{instance.port}")

            # 使用标准gRPC健康检查服务
            from grpc_health.v1 import health_pb2, health_pb2_grpc

            stub = health_pb2_grpc.HealthStub(channel)
            request = health_pb2.HealthCheckRequest(service="")  # 空字符串检查服务整体状态

            # 执行检查
            response = await asyncio.wait_for(
                asyncio.get_event_loop().run_in_executor(None, stub.Check, request),
                timeout=self.config.timeout,
            )

            duration = time.time() - start_time
            channel.close()

            # 检查响应状态
            if response.status == health_pb2.HealthCheckResponse.SERVING:
                return HealthCheckResult(
                    status=HealthStatus.HEALTHY,
                    duration=duration,
                    message="gRPC service is SERVING",
                    timestamp=datetime.now(),
                    details={
                        "host": instance.host,
                        "port": instance.port,
                        "status": response.status,
                    },
                )
            else:
                return HealthCheckResult(
                    status=HealthStatus.DEGRADED,
                    duration=duration,
                    message=f"gRPC service status: {response.status}",
                    timestamp=datetime.now(),
                    details={
                        "host": instance.host,
                        "port": instance.port,
                        "status": response.status,
                    },
                )

        except asyncio.TimeoutError:
            return HealthCheckResult(
                status=HealthStatus.UNHEALTHY,
                duration=time.time() - start_time,
                message="gRPC health check timeout",
                timestamp=datetime.now(),
            )
        except Exception as e:
            return HealthCheckResult(
                status=HealthStatus.UNHEALTHY,
                duration=time.time() - start_time,
                message=f"gRPC health check error: {str(e)}",
                timestamp=datetime.now(),
            )


class GraphQLHealthChecker(HealthChecker):
    """GraphQL健康检查器"""

    async def check(self, instance: ServiceInstance) -> HealthCheckResult:
        """GraphQL健康检查"""
        start_time = time.time()

        try:
            # 构建GraphQL健康检查查询
            query = """
            query {
                __schema {
                    types {
                        name
                    }
                }
            }
            """

            # 发送GraphQL查询
            scheme = "https" if instance.protocol.value == "https" else "http"
            url = f"{scheme}://{instance.host}:{instance.port}/graphql"

            timeout = aiohttp.ClientTimeout(total=self.config.timeout)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.post(
                    url,
                    json={"query": query},
                    headers=self.config.headers or {"Content-Type": "application/json"},
                ) as response:
                    duration = time.time() - start_time
                    data = await response.json()

                    if response.status == 200 and "errors" not in data:
                        return HealthCheckResult(
                            status=HealthStatus.HEALTHY,
                            duration=duration,
                            message="GraphQL schema query successful",
                            timestamp=datetime.now(),
                            details={
                                "url": url,
                                "status_code": response.status,
                                "schema_types": len(
                                    data.get("data", {}).get("__schema", {}).get("types", [])
                                ),
                            },
                        )
                    else:
                        return HealthCheckResult(
                            status=HealthStatus.UNHEALTHY,
                            duration=duration,
                            message=f"GraphQL query failed: {data.get('errors', 'Unknown error')}",
                            timestamp=datetime.now(),
                            details={
                                "url": url,
                                "status_code": response.status,
                                "errors": data.get("errors"),
                            },
                        )

        except Exception as e:
            return HealthCheckResult(
                status=HealthStatus.UNHEALTHY,
                duration=time.time() - start_time,
                message=f"GraphQL health check error: {str(e)}",
                timestamp=datetime.now(),
            )


class HealthCheckManager:
    """健康检查管理器"""

    def __init__(self, registry: ServiceRegistry):
        self.registry = registry
        self.checkers = {
            HealthCheckType.HTTP: HTTPHealthChecker,
            HealthCheckType.HTTPS: HTTPHealthChecker,
            HealthCheckType.TCP: TCPHealthChecker,
            HealthCheckType.GRPC: GRPCHealthChecker,
            HealthCheckType.GRAPHQL: GraphQLHealthChecker,
        }
        self.health_check_tasks: dict[str, asyncio.Task] = {}
        self.health_history: dict[str, list[HealthCheckResult]] = {}
        self.service_configs: dict[str, HealthCheckConfig] = {}
        self.callbacks: list[Callable] = []
        self.running = False

    async def start(self):
        """启动健康检查管理器"""
        self.running = True
        logger.info("Health check manager started")

    async def stop(self):
        """停止健康检查管理器"""
        self.running = False

        # 取消所有健康检查任务
        for task in self.health_check_tasks.values():
            task.cancel()

        # 等待所有任务完成
        if self.health_check_tasks:
            await asyncio.gather(*self.health_check_tasks.values(), return_exceptions=True)

        self.health_check_tasks.clear()
        logger.info("Health check manager stopped")

    async def start_health_check(self, instance: ServiceInstance, config: HealthCheckConfig):
        """启动对服务实例的健康检查"""
        service_id = instance.service_id

        # 如果已经在检查，先停止
        if service_id in self.health_check_tasks:
            await self.stop_health_check(service_id)

        # 保存配置
        self.service_configs[service_id] = config

        # 启动健康检查任务
        task = asyncio.create_task(self._health_check_loop(instance, config))
        self.health_check_tasks[service_id] = task

        logger.info(f"Started health check for service {service_id}")

    async def stop_health_check(self, service_id: str):
        """停止对服务实例的健康检查"""
        if service_id in self.health_check_tasks:
            task = self.health_check_tasks[service_id]
            task.cancel()

            try:
                await task
            except asyncio.CancelledError:
                pass

            del self.health_check_tasks[service_id]

            # 清理配置和历史
            self.service_configs.pop(service_id, None)
            self.health_history.pop(service_id, None)

            logger.info(f"Stopped health check for service {service_id}")

    async def _health_check_loop(self, instance: ServiceInstance, config: HealthCheckConfig):
        """健康检查循环"""
        service_id = instance.service_id

        while self.running:
            try:
                # 执行健康检查
                result = await self._execute_health_check(instance, config)

                # 更新健康历史
                if service_id not in self.health_history:
                    self.health_history[service_id] = []

                self.health_history[service_id].append(result)

                # 保持最近100次检查记录
                if len(self.health_history[service_id]) > 100:
                    self.health_history[service_id] = self.health_history[service_id][-100:]

                # 更新服务实例健康状态
                old_status = instance.health_status
                new_status = self._determine_health_status(service_id, result, config)

                if old_status != new_status:
                    await self.registry.update_service_instance(
                        service_id, {"health_status": new_status, "last_heartbeat": datetime.now()}
                    )

                    # 触发状态变更回调
                    await self._trigger_status_callbacks(service_id, old_status, new_status)

                # 等待下次检查
                await asyncio.sleep(config.interval)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Health check error for {service_id}: {e}")
                await asyncio.sleep(5)  # 错误后短暂等待

    async def _execute_health_check(
        self, instance: ServiceInstance, config: HealthCheckConfig
    ) -> HealthCheckResult:
        """执行单次健康检查"""
        # 选择合适的检查器
        checker_type = self._get_checker_type(instance)
        checker_class = self.checkers.get(checker_type)

        if not checker_class:
            return HealthCheckResult(
                status=HealthStatus.UNKNOWN,
                duration=0,
                message=f"No health checker available for {checker_type}",
                timestamp=datetime.now(),
            )

        # 执行检查，支持重试
        last_exception = None
        for attempt in range(config.retries + 1):
            try:
                checker = checker_class(config)
                result = await checker.check(instance)

                if attempt > 0:
                    result.message += f" (after {attempt} retries)"

                return result

            except Exception as e:
                last_exception = e
                if attempt < config.retries:
                    await asyncio.sleep(1)  # 重试间隔

        # 所有重试都失败
        return HealthCheckResult(
            status=HealthStatus.UNHEALTHY,
            duration=0,
            message=f"Health check failed after {config.retries + 1} attempts: {str(last_exception)}",
            timestamp=datetime.now(),
        )

    def _get_checker_type(self, instance: ServiceInstance) -> HealthCheckType:
        """根据服务协议确定检查器类型"""
        protocol = instance.protocol.value.upper()

        if protocol in ["HTTP", "HTTPS"]:
            return HealthCheckType.HTTPS if protocol == "HTTPS" else HealthCheckType.HTTP
        elif protocol == "GRPC":
            return HealthCheckType.GRPC
        elif protocol == "GRAPHQL":
            return HealthCheckType.GRAPHQL
        else:
            return HealthCheckType.TCP  # 默认使用TCP检查

    def _determine_health_status(
        self, service_id: str, current_result: HealthCheckResult, config: HealthCheckConfig
    ) -> HealthStatus:
        """确定服务健康状态"""
        history = self.health_history.get(service_id, [])

        if len(history) < config.failure_threshold:
            # 检查次数不足，使用当前结果
            return current_result.status

        # 分析最近的检查结果
        recent_results = history[-config.success_threshold + config.failure_threshold :]

        # 统计健康检查结果
        healthy_count = sum(1 for r in recent_results if r.status == HealthStatus.HEALTHY)
        unhealthy_count = len(recent_results) - healthy_count

        # 根据阈值确定状态
        if unhealthy_count >= config.failure_threshold:
            return HealthStatus.UNHEALTHY
        elif healthy_count >= config.success_threshold:
            return HealthStatus.HEALTHY
        elif current_result.status == HealthStatus.DEGRADED:
            return HealthStatus.DEGRADED
        else:
            return current_result.status

    async def _trigger_status_callbacks(
        self, service_id: str, old_status: HealthStatus, new_status: HealthStatus
    ):
        """触发健康状态变更回调"""
        for callback in self.callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(service_id, old_status, new_status)
                else:
                    callback(service_id, old_status, new_status)
            except Exception as e:
                logger.error(f"Health status callback error: {e}")

    def add_status_callback(self, callback: Callable):
        """添加健康状态变更回调"""
        self.callbacks.append(callback)

    def remove_status_callback(self, callback: Callable):
        """移除健康状态变更回调"""
        if callback in self.callbacks:
            self.callbacks.remove(callback)

    async def get_service_health_summary(
        self, service_name: str, namespace: str = "default"
    ) -> dict[str, Any]:
        """获取服务健康状态摘要"""
        instances = await self.registry.discover_services(service_name, namespace)

        if not instances:
            return {
                "service_name": service_name,
                "namespace": namespace,
                "total_instances": 0,
                "healthy_instances": 0,
                "unhealthy_instances": 0,
                "unknown_instances": 0,
                "degraded_instances": 0,
                "health_percentage": 0,
                "instances": [],
            }

        # 统计各状态实例数
        status_counts = {
            HealthStatus.HEALTHY: 0,
            HealthStatus.UNHEALTHY: 0,
            HealthStatus.UNKNOWN: 0,
            HealthStatus.DEGRADED: 0,
            HealthStatus.MAINTENANCE: 0,
        }

        instance_details = []
        for instance in instances:
            status_counts[instance.health_status] += 1

            # 获取健康检查历史
            history = self.health_history.get(instance.service_id, [])
            recent_checks = history[-10:] if len(history) >= 10 else history

            # 计算平均响应时间
            avg_duration = 0
            if recent_checks:
                durations = [r.duration for r in recent_checks]
                avg_duration = statistics.mean(durations)

            instance_details.append(
                {
                    "service_id": instance.service_id,
                    "host": instance.host,
                    "port": instance.port,
                    "health_status": instance.health_status.value,
                    "last_heartbeat": instance.last_heartbeat.isoformat()
                    if instance.last_heartbeat
                    else None,
                    "avg_response_time": round(avg_duration, 3),
                    "check_count": len(history),
                }
            )

        # 计算健康百分比
        total_instances = len(instances)
        healthy_instances = (
            status_counts[HealthStatus.HEALTHY] + status_counts[HealthStatus.DEGRADED]
        )
        health_percentage = (
            (healthy_instances / total_instances) * 100 if total_instances > 0 else 0
        )

        return {
            "service_name": service_name,
            "namespace": namespace,
            "total_instances": total_instances,
            "healthy_instances": status_counts[HealthStatus.HEALTHY],
            "unhealthy_instances": status_counts[HealthStatus.UNHEALTHY],
            "unknown_instances": status_counts[HealthStatus.UNKNOWN],
            "degraded_instances": status_counts[HealthStatus.DEGRADED],
            "maintenance_instances": status_counts[HealthStatus.MAINTENANCE],
            "health_percentage": round(health_percentage, 2),
            "instances": instance_details,
        }

    async def get_service_health_history(self, service_id: str, limit: int = 50) -> list[dict]:
        """获取服务健康检查历史"""
        history = self.health_history.get(service_id, [])
        recent_history = history[-limit:] if len(history) >= limit else history

        return [
            {
                "timestamp": result.timestamp.isoformat(),
                "status": result.status.value,
                "duration": round(result.duration, 3),
                "message": result.message,
                "details": result.details,
            }
            for result in recent_history
        ]


# 工厂函数
def create_health_check_manager(registry: ServiceRegistry) -> HealthCheckManager:
    """创建健康检查管理器"""
    return HealthCheckManager(registry)


# 使用示例
async def main():
    """主函数示例"""
    import os
    import sys

    # 添加父目录到路径以便导入模块
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

    from .core_service_registry import create_service_discovery

    # 创建服务注册中心
    config = {"storage": {"type": "redis", "redis_url": "redis://localhost:6379"}}

    registry = await create_service_discovery(config)

    # 创建健康检查管理器
    health_manager = create_health_check_manager(registry)
    await health_manager.start()

    # 添加状态变更回调
    async def status_changed(service_id: str, old_status: HealthStatus, new_status: HealthStatus):
        logger.info(
            f"Service {service_id} status changed: {old_status.value} -> {new_status.value}"
        )

    health_manager.add_status_callback(status_changed)

    try:
        # 保持服务运行
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        await health_manager.stop()
        await registry.close()


if __name__ == "__main__":
    asyncio.run(main())
