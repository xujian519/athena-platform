"""
健康检查器
Health Checker for Service Registry
"""
import asyncio
import logging
import httpx
from typing import Optional, Dict, Any
from datetime import datetime
from socket import socket, AF_INET, SOCK_STREAM

from core.service_registry.models import (
    ServiceInstance,
    ServiceStatus,
    HealthCheckConfig
)
from core.service_registry.storage import ServiceRegistryStorage


logger = logging.getLogger(__name__)


class HealthCheckResult:
    """健康检查结果"""

    def __init__(
        self,
        healthy: bool,
        message: str = "",
        response_time_ms: float = 0
    ):
        self.healthy = healthy
        self.message = message
        self.response_time_ms = response_time_ms


class HealthChecker:
    """健康检查器"""

    def __init__(
        self,
        storage: Optional[ServiceRegistryStorage] = None,
        config: Optional[HealthCheckConfig] = None
    ):
        """初始化健康检查器

        Args:
            storage: 存储实例
            config: 健康检查配置
        """
        self.storage = storage or ServiceRegistryStorage()
        self.config = config or HealthCheckConfig()
        self.unhealthy_counts: Dict[str, int] = {}  # 不健康计数
        self.healthy_counts: Dict[str, int] = {}     # 健康计数

    def _get_instance_key(self, service_name: str, instance_id: str) -> str:
        """获取实例键"""
        return f"{service_name}:{instance_id}"

    async def check_http(
        self,
        instance: ServiceInstance,
        config: HealthCheckConfig
    ) -> HealthCheckResult:
        """HTTP健康检查

        Args:
            instance: 服务实例
            config: 健康检查配置

        Returns:
            检查结果
        """
        start_time = datetime.now()

        try:
            url = f"http://{instance.address}{config.http_path}"

            async with httpx.AsyncClient(timeout=config.check_timeout) as client:
                response = await client.request(
                    method=config.http_method,
                    url=url
                )

                response_time = (datetime.now() - start_time).total_seconds() * 1000

                if response.status_code == config.http_expected_status:
                    return HealthCheckResult(
                        healthy=True,
                        message=f"HTTP {response.status_code}",
                        response_time_ms=response_time
                    )
                else:
                    return HealthCheckResult(
                        healthy=False,
                        message=f"HTTP {response.status_code} (expected {config.http_expected_status})",
                        response_time_ms=response_time
                    )

        except httpx.TimeoutException:
            return HealthCheckResult(
                healthy=False,
                message="HTTP check timeout",
                response_time_ms=(datetime.now() - start_time).total_seconds() * 1000
            )
        except Exception as e:
            return HealthCheckResult(
                healthy=False,
                message=f"HTTP check failed: {str(e)}",
                response_time_ms=(datetime.now() - start_time).total_seconds() * 1000
            )

    async def check_tcp(
        self,
        instance: ServiceInstance,
        config: HealthCheckConfig
    ) -> HealthCheckResult:
        """TCP健康检查

        Args:
            instance: 服务实例
            config: 健康检查配置

        Returns:
            检查结果
        """
        start_time = datetime.now()

        try:
            port = config.tcp_port or instance.port

            sock = socket(AF_INET)
            sock.settimeout(config.check_timeout)
            result = sock.connect_ex((instance.host, port))
            sock.close()

            response_time = (datetime.now() - start_time).total_seconds() * 1000

            if result == 0:
                return HealthCheckResult(
                    healthy=True,
                    message=f"TCP connection successful",
                    response_time_ms=response_time
                )
            else:
                return HealthCheckResult(
                    healthy=False,
                    message=f"TCP connection failed (error code: {result})",
                    response_time_ms=response_time
                )

        except Exception as e:
            return HealthCheckResult(
                healthy=False,
                message=f"TCP check failed: {str(e)}",
                response_time_ms=(datetime.now() - start_time).total_seconds() * 1000
            )

    async def check_heartbeat(
        self,
        instance: ServiceInstance,
        config: HealthCheckConfig
    ) -> HealthCheckResult:
        """心跳健康检查

        Args:
            instance: 服务实例
            config: 健康检查配置

        Returns:
            检查结果
        """
        # 心跳检查只检查最后心跳时间
        if instance.is_expired(config.heartbeat_timeout):
            return HealthCheckResult(
                healthy=False,
                message=f"Heartbeat expired (last: {instance.last_heartbeat.isoformat()})",
                response_time_ms=0
            )
        else:
            return HealthCheckResult(
                healthy=True,
                message=f"Heartbeat OK (last: {instance.last_heartbeat.isoformat()})",
                response_time_ms=0
            )

    async def check_instance(
        self,
        instance: ServiceInstance,
        config: Optional[HealthCheckConfig] = None
    ) -> HealthCheckResult:
        """检查单个实例

        Args:
            instance: 服务实例
            config: 健康检查配置

        Returns:
            检查结果
        """
        config = config or self.config
        instance_key = self._get_instance_key(instance.service_name, instance.instance_id)

        try:
            # 根据检查类型执行检查
            if config.check_type == "http":
                result = await self.check_http(instance, config)
            elif config.check_type == "tcp":
                result = await self.check_tcp(instance, config)
            elif config.check_type == "heartbeat":
                result = await self.check_heartbeat(instance, config)
            else:
                return HealthCheckResult(
                    healthy=False,
                    message=f"Unknown check type: {config.check_type}",
                    response_time_ms=0
                )

            # 更新计数
            if result.healthy:
                self.unhealthy_counts[instance_key] = 0
                self.healthy_counts[instance_key] = self.healthy_counts.get(instance_key, 0) + 1
            else:
                self.healthy_counts[instance_key] = 0
                self.unhealthy_counts[instance_key] = self.unhealthy_counts.get(instance_key, 0) + 1

            # 更新实例状态
            await self._update_instance_status(instance, result, config)

            return result

        except Exception as e:
            logger.error(f"❌ 检查实例失败 {instance_key}: {e}")
            return HealthCheckResult(
                healthy=False,
                message=f"Check error: {str(e)}",
                response_time_ms=0
            )

    async def _update_instance_status(
        self,
        instance: ServiceInstance,
        result: HealthCheckResult,
        config: HealthCheckConfig
    ):
        """更新实例状态

        Args:
            instance: 服务实例
            result: 检查结果
            config: 健康检查配置
        """
        instance_key = self._get_instance_key(instance.service_name, instance.instance_id)
        old_status = instance.status
        new_status = old_status

        # 判断是否应该标记为不健康
        if not result.healthy:
            if self.unhealthy_counts[instance_key] >= config.unhealthy_threshold:
                new_status = ServiceStatus.UNHEALTHY

        # 判断是否应该恢复为健康
        elif result.healthy:
            if self.healthy_counts[instance_key] >= config.healthy_threshold:
                new_status = ServiceStatus.HEALTHY

        # 状态变化时更新存储
        if new_status != old_status:
            instance.status = new_status
            await self.storage.update_instance(instance)
            logger.info(
                f"🔄 状态变化: {instance.service_name}/{instance.instance_id} "
                f"{old_status.value} -> {new_status.value}"
            )

    async def check_all_instances(
        self,
        service_name: Optional[str] = None
    ) -> Dict[str, HealthCheckResult]:
        """检查所有实例

        Args:
            service_name: 服务名称（可选，不指定则检查所有服务）

        Returns:
            实例键 -> 检查结果
        """
        results = {}

        try:
            # 获取服务列表
            if service_name:
                services = [service_name]
            else:
                services = await self.storage.get_all_services()

            # 检查每个服务的每个实例
            for svc_name in services:
                instances = await self.storage.get_all_instances(svc_name)

                for instance in instances:
                    instance_key = self._get_instance_key(instance.service_name, instance.instance_id)
                    result = await self.check_instance(instance)
                    results[instance_key] = result

                    logger.debug(
                        f"检查结果: {instance_key} - "
                        f"{'✅' if result.healthy else '❌'} "
                        f"{result.message} ({result.response_time_ms:.2f}ms)"
                    )

            return results

        except Exception as e:
            logger.error(f"❌ 检查所有实例失败: {e}")
            return results

    async def start_background_check(self, interval_seconds: Optional[int] = None):
        """启动后台健康检查

        Args:
            interval_seconds: 检查间隔（秒），默认使用配置的间隔
        """
        interval = interval_seconds or self.config.check_interval

        logger.info(f"🔄 启动后台健康检查（间隔: {interval}秒）")

        while True:
            try:
                results = await self.check_all_instances()

                # 统计
                total = len(results)
                healthy = sum(1 for r in results.values() if r.healthy)
                unhealthy = total - healthy

                logger.info(
                    f"📊 健康检查完成: {total}个实例, "
                    f"✅{healthy}个健康, ❌{unhealthy}个不健康"
                )

            except Exception as e:
                logger.error(f"❌ 后台健康检查出错: {e}")

            # 等待下一次检查
            await asyncio.sleep(interval)


# 便捷函数
_checker_instance: Optional[HealthChecker] = None


def get_health_checker() -> HealthChecker:
    """获取健康检查器实例（单例模式）"""
    global _checker_instance
    if _checker_instance is None:
        _checker_instance = HealthChecker()
    return _checker_instance
