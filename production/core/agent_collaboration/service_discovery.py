#!/usr/bin/env python3
"""
服务发现与负载均衡模块
Service Discovery and Load Balancing Module

提供智能服务发现、健康检查和负载均衡功能

作者: 小诺·双鱼座 💖
创建: 2025-01-12
版本: v1.0.0
"""

from __future__ import annotations
import asyncio
import contextlib
import logging
import random
from datetime import datetime
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class LoadBalancingStrategy(Enum):
    """负载均衡策略"""

    ROUND_ROBIN = "round_robin"  # 轮询
    RANDOM = "random"  # 随机
    LEAST_CONNECTIONS = "least_connections"  # 最少连接
    WEIGHTED = "weighted"  # 权重
    HEALTH_FIRST = "health_first"  # 健康优先


class ServiceInstance:
    """服务实例"""

    def __init__(
        self,
        instance_id: str,
        agent_id: str,
        host: str,
        port: int,
        weight: int = 1,
        metadata: dict[str, Any] | None = None,
    ):
        self.instance_id = instance_id
        self.agent_id = agent_id
        self.host = host
        self.port = port
        self.weight = weight
        self.metadata = metadata or {}

        # 健康状态
        self.is_healthy = True
        self.last_health_check: datetime | None = None
        self.consecutive_failures = 0
        self.max_consecutive_failures = 3

        # 连接统计
        self.active_connections = 0
        self.total_requests = 0
        self.successful_requests = 0
        self.failed_requests = 0
        self.average_response_time = 0.0

    @property
    def endpoint(self) -> str:
        """获取服务端点"""
        return f"http://{self.host}:{self.port}"

    def mark_healthy(self) -> None:
        """标记为健康"""
        self.is_healthy = True
        self.consecutive_failures = 0
        self.last_health_check = datetime.now()

    def mark_unhealthy(self) -> None:
        """标记为不健康"""
        self.consecutive_failures += 1
        if self.consecutive_failures >= self.max_consecutive_failures:
            self.is_healthy = False
        self.last_health_check = datetime.now()

    def record_request(self, success: bool, response_time: float) -> None:
        """记录请求"""
        self.total_requests += 1
        if success:
            self.successful_requests += 1
        else:
            self.failed_requests += 1

        # 更新平均响应时间(指数移动平均)
        alpha = 0.3
        self.average_response_time = (
            alpha * response_time + (1 - alpha) * self.average_response_time
        )

    def increment_connections(self) -> None:
        """增加连接数"""
        self.active_connections += 1

    def decrement_connections(self) -> None:
        """减少连接数"""
        self.active_connections = max(0, self.active_connections - 1)

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "instance_id": self.instance_id,
            "agent_id": self.agent_id,
            "endpoint": self.endpoint,
            "is_healthy": self.is_healthy,
            "weight": self.weight,
            "active_connections": self.active_connections,
            "total_requests": self.total_requests,
            "success_rate": (
                self.successful_requests / self.total_requests if self.total_requests > 0 else 0
            ),
            "average_response_time": self.average_response_time,
            "last_health_check": (
                self.last_health_check.isoformat() if self.last_health_check else None
            ),
        }


class ServiceRegistry:
    """服务注册中心"""

    def __init__(self):
        """初始化服务注册中心"""
        # agent_id -> list[ServiceInstance]
        self.services: dict[str, list[ServiceInstance]] = {}

        # 负载均衡状态
        self.round_robin_index: dict[str, int] = {}

        logger.info("📋 服务注册中心已初始化")

    def register(self, instance: ServiceInstance) -> None:
        """注册服务实例"""
        agent_id = instance.agent_id

        if agent_id not in self.services:
            self.services[agent_id] = []
            self.round_robin_index[agent_id] = 0

        # 检查是否已存在
        existing = next(
            (s for s in self.services[agent_id] if s.instance_id == instance.instance_id), None
        )

        if existing:
            # 更新现有实例
            existing.host = instance.host
            existing.port = instance.port
            existing.weight = instance.weight
            existing.metadata = instance.metadata
            logger.info(f"🔄 更新服务实例: {instance.instance_id}")
        else:
            # 添加新实例
            self.services[agent_id].append(instance)
            logger.info(f"✅ 注册服务实例: {instance.instance_id} -> {instance.endpoint}")

    def deregister(self, instance_id: str) -> None:
        """注销服务实例"""
        for _agent_id, instances in self.services.items():
            for i, instance in enumerate(instances):
                if instance.instance_id == instance_id:
                    instances.pop(i)
                    logger.info(f"❌ 注销服务实例: {instance_id}")
                    return

    def get_instances(self, agent_id: str, healthy_only: bool = True) -> list[ServiceInstance]:
        """获取服务实例列表"""
        instances = self.services.get(agent_id, [])

        if healthy_only:
            instances = [s for s in instances if s.is_healthy]

        return instances

    def get_instance(
        self, agent_id: str, strategy: LoadBalancingStrategy = LoadBalancingStrategy.HEALTH_FIRST
    ) -> ServiceInstance | None:
        """根据负载均衡策略获取实例"""
        instances = self.get_instances(agent_id, healthy_only=True)

        if not instances:
            return None

        if strategy == LoadBalancingStrategy.ROUND_ROBIN:
            return self._round_robin_select(agent_id, instances)
        elif strategy == LoadBalancingStrategy.RANDOM:
            return random.choice(instances)
        elif strategy == LoadBalancingStrategy.LEAST_CONNECTIONS:
            return min(instances, key=lambda s: s.active_connections)
        elif strategy == LoadBalancingStrategy.WEIGHTED:
            return self._weighted_select(instances)
        else:  # HEALTH_FIRST
            # 优先选择最健康的实例(最高成功率 + 最低响应时间)
            return max(
                instances,
                key=lambda s: (
                    s.successful_requests / s.total_requests if s.total_requests > 0 else 1.0,
                    -s.average_response_time,
                ),
            )

    def _round_robin_select(
        self, agent_id: str, instances: list[ServiceInstance]
    ) -> ServiceInstance:
        """轮询选择"""
        index = self.round_robin_index.get(agent_id, 0) % len(instances)
        self.round_robin_index[agent_id] = (index + 1) % len(instances)
        return instances[index]

    def _weighted_select(self, instances: list[ServiceInstance]) -> ServiceInstance:
        """加权随机选择"""
        total_weight = sum(s.weight for s in instances)
        if total_weight == 0:
            return random.choice(instances)

        rand = random.uniform(0, total_weight)
        current = 0

        for instance in instances:
            current += instance.weight
            if rand <= current:
                return instance

        return instances[-1]

    def get_all_services(self) -> dict[str, list[dict[str, Any]]]:
        """获取所有服务"""
        return {
            agent_id: [s.to_dict() for s in instances]
            for agent_id, instances in self.services.items()
        }

    def get_statistics(self) -> dict[str, Any]:
        """获取统计信息"""
        total_instances = sum(len(instances) for instances in self.services.values())
        healthy_instances = sum(
            sum(1 for s in instances if s.is_healthy) for instances in self.services.values()
        )

        total_requests = sum(
            sum(s.total_requests for s in instances) for instances in self.services.values()
        )

        total_successful = sum(
            sum(s.successful_requests for s in instances) for instances in self.services.values()
        )

        return {
            "total_agents": len(self.services),
            "total_instances": total_instances,
            "healthy_instances": healthy_instances,
            "unhealthy_instances": total_instances - healthy_instances,
            "total_requests": total_requests,
            "successful_requests": total_successful,
            "overall_success_rate": (
                total_successful / total_requests if total_requests > 0 else 0
            ),
        }


class ServiceDiscovery:
    """服务发现"""

    def __init__(self, registry: ServiceRegistry):
        """初始化服务发现"""
        self.registry = registry
        self.health_check_interval = 30  # 秒
        self.health_check_task: asyncio.Task[Any] | None | None = None
        self.is_running = False

        logger.info("🔍 服务发现已初始化")

    async def start(self):
        """启动服务发现"""
        if self.is_running:
            return

        self.is_running = True
        self.health_check_task = asyncio.create_task(self._health_check_loop())
        logger.info("🚀 服务发现已启动")

    async def stop(self):
        """停止服务发现"""
        self.is_running = False

        if self.health_check_task:
            self.health_check_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self.health_check_task

        logger.info("🛑 服务发现已停止")

    async def _health_check_loop(self):
        """健康检查循环"""
        while self.is_running:
            try:
                await self._perform_health_checks()
                await asyncio.sleep(self.health_check_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"❌ 健康检查失败: {e}")
                await asyncio.sleep(5)

    async def _perform_health_checks(self):
        """执行健康检查"""
        import aiohttp

        for _agent_id, instances in self.registry.services.items():
            for instance in instances:
                try:
                    # 执行健康检查
                    health_url = f"{instance.endpoint}/health"

                    async with aiohttp.ClientSession() as session, session.get(
                        health_url, timeout=aiohttp.ClientTimeout(total=5)
                    ) as response:
                        if response.status == 200:
                            instance.mark_healthy()
                        else:
                            instance.mark_unhealthy()

                except Exception as e:
                    logger.warning(f"⚠️ 健康检查失败: {instance.endpoint} - {e}")
                    instance.mark_unhealthy()

    def discover_service(self, agent_id: str) -> ServiceInstance | None:
        """发现服务(返回最佳实例)"""
        return self.registry.get_instance(agent_id, LoadBalancingStrategy.HEALTH_FIRST)

    def get_service_status(self, agent_id: str) -> dict[str, Any]:
        """获取服务状态"""
        instances = self.registry.get_instances(agent_id, healthy_only=False)

        return {
            "agent_id": agent_id,
            "total_instances": len(instances),
            "healthy_instances": sum(1 for s in instances if s.is_healthy),
            "unhealthy_instances": sum(1 for s in instances if not s.is_healthy),
            "instances": [s.to_dict() for s in instances],
        }


# ==================== 全局单例 ====================

_service_registry: ServiceRegistry | None = None
_service_discovery: ServiceDiscovery | None = None


def get_service_registry() -> ServiceRegistry:
    """获取服务注册中心单例"""
    global _service_registry
    if _service_registry is None:
        _service_registry = ServiceRegistry()
    return _service_registry


def get_service_discovery() -> ServiceDiscovery:
    """获取服务发现单例"""
    global _service_discovery
    if _service_discovery is None:
        _service_discovery = ServiceDiscovery(get_service_registry())
    return _service_discovery


# ==================== 初始化默认服务 ====================


def initialize_default_services() -> None:
    """初始化默认服务"""
    registry = get_service_registry()

    # 小娜服务
    registry.register(
        ServiceInstance(
            instance_id="xiaona-8001",
            agent_id="xiaona",
            host="localhost",
            port=8001,
            weight=1,
            metadata={"version": "v2.0.0-standalone", "role": "专利法律专家"},
        )
    )

    # 小宸服务
    registry.register(
        ServiceInstance(
            instance_id="xiaochen-8006",
            agent_id="xiaochen",
            host="localhost",
            port=8006,
            weight=1,
            metadata={"version": "v2.0.0-standalone", "role": "自媒体运营专家"},
        )
    )


    logger.info("✅ 默认服务已注册到服务发现中心")


if __name__ == "__main__":
    # 测试代码
    async def test():
        """测试服务发现和负载均衡"""
        # 初始化
        initialize_default_services()

        registry = get_service_registry()
        discovery = get_service_discovery()

        # 启动健康检查
        await discovery.start()

        print("\n" + "=" * 70)
        print("🔍 服务发现和负载均衡测试")
        print("=" * 70)

        # 显示所有服务
        print("\n📊 已注册服务:")
        all_services = registry.get_all_services()
        for agent_id, instances in all_services.items():
            print(f"\n  {agent_id}:")
            for instance in instances:
                status = "✅ 健康" if instance["is_healthy"] else "❌ 不健康"
                print(f"    - {instance['endpoint']} ({status})")

        # 显示统计信息
        print("\n📈 统计信息:")
        stats = registry.get_statistics()
        for key, value in stats.items():
            print(f"  {key}: {value}")

        # 测试服务发现
        print("\n🔍 服务发现测试:")
        for agent_id in ["xiaona", "xiaochen", "yunxi"]:
            instance = discovery.discover_service(agent_id)
            if instance:
                print(f"  {agent_id}: {instance.endpoint} (权重: {instance.weight})")
            else:
                print(f"  {agent_id}: 未发现可用实例")

        # 等待一段时间
        print("\n⏳ 健康检查运行中...")
        await asyncio.sleep(35)

        # 停止服务发现
        await discovery.stop()

        print("\n" + "=" * 70)
        print("✅ 测试完成")
        print("=" * 70)

    asyncio.run(test())
