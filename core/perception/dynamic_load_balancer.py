#!/usr/bin/env python3
from __future__ import annotations
"""
动态负载均衡器
Dynamic Load Balancer

智能地将请求分配到不同的处理器,优化整体系统性能。

功能特性:
1. 多种负载均衡算法
2. 健康检查
3. 动态权重调整
4. 请求追踪
5. 性能监控

负载均衡算法:
- 轮询 (Round Robin)
- 加权轮询 (Weighted Round Robin)
- 最少连接 (Least Connections)
- 最短响应时间 (Least Response Time)
- 一致性哈希 (Consistent Hashing)
- 自适应 (Adaptive)

作者: Athena AI系统
创建时间: 2026-01-25
版本: 1.0.0
"""

import asyncio
import contextlib
import hashlib
import inspect
import logging
import time
from abc import ABC, abstractmethod
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class LoadBalancingStrategy(Enum):
    """负载均衡策略"""

    ROUND_ROBIN = "round_robin"  # 轮询
    WEIGHTED_ROUND_ROBIN = "weighted_round_robin"  # 加权轮询
    LEAST_CONNECTIONS = "least_connections"  # 最少连接
    LEAST_RESPONSE_TIME = "least_response_time"  # 最短响应时间
    CONSISTENT_HASH = "consistent_hash"  # 一致性哈希
    ADAPTIVE = "adaptive"  # 自适应


class HealthStatus(Enum):
    """健康状态"""

    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    DISABLED = "disabled"


@dataclass
class ProcessorNode:
    """处理器节点"""

    id: str
    processor: Any  # 处理器实例
    weight: int = 1  # 权重
    active_connections: int = 0  # 活跃连接数
    total_requests: int = 0  # 总请求数
    successful_requests: int = 0  # 成功请求数
    failed_requests: int = 0  # 失败请求数
    avg_response_time: float = 0.0  # 平均响应时间(秒)
    last_health_check: datetime | None = None
    health_status: HealthStatus = HealthStatus.HEALTHY
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def success_rate(self) -> float:
        """成功率"""
        if self.total_requests == 0:
            return 1.0
        return self.successful_requests / self.total_requests

    @property
    def failure_rate(self) -> float:
        """失败率"""
        return 1.0 - self.success_rate

    @property
    def load_score(self) -> float:
        """负载评分(越低越好)"""
        # 结合连接数和响应时间
        connection_score = self.active_connections / max(1, self.weight)
        time_score = self.avg_response_time
        return connection_score * 0.5 + time_score * 0.5


@dataclass
class RoutingResult:
    """路由结果"""

    success: bool
    node_id: Optional[str] = None
    result: Any = None
    error: Exception | None = None
    routing_time: float = 0.0
    processing_time: float = 0.0
    total_time: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class LoadBalancerMetrics:
    """负载均衡器指标"""

    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    total_routing_time: float = 0.0
    total_processing_time: float = 0.0
    avg_response_time: float = 0.0

    # 节点分布
    node_request_counts: dict[str, int] = field(default_factory=dict)

    # 策略切换历史
    strategy_changes: int = 0
    last_strategy_change: datetime | None = None

    @property
    def overall_success_rate(self) -> float:
        """整体成功率"""
        if self.total_requests == 0:
            return 1.0
        return self.successful_requests / self.total_requests

    @property
    def distribution_balance(self) -> float:
        """分布均衡度(0-1,1表示完全均衡)"""
        if not self.node_request_counts:
            return 1.0

        counts = list(self.node_request_counts.values())
        if sum(counts) == 0:
            return 1.0

        max_count = max(counts)
        avg_count = sum(counts) / len(counts)

        if max_count == 0:
            return 1.0

        # 计算变异系数的倒数
        variance = sum((c - avg_count) ** 2 for c in counts) / len(counts)
        std_dev = variance**0.5
        if std_dev == 0:
            return 1.0

        cv = std_dev / avg_count
        return max(0.0, 1.0 - cv)


class LoadBalancingAlgorithm(ABC):
    """负载均衡算法抽象基类"""

    @abstractmethod
    async def select_node(self, nodes: list[ProcessorNode]) -> ProcessorNode | None:
        """选择节点

        Args:
            nodes: 可用节点列表

        Returns:
            选中的节点,如果没有可用节点返回None
        """
        pass


class RoundRobinAlgorithm(LoadBalancingAlgorithm):
    """轮询算法"""

    def __init__(self):
        self._current_index = 0

    async def select_node(self, nodes: list[ProcessorNode]) -> ProcessorNode | None:
        """按顺序选择下一个节点"""
        if not nodes:
            return None

        # 过滤健康节点
        healthy_nodes = [
            n for n in nodes if n.health_status in (HealthStatus.HEALTHY, HealthStatus.DEGRADED)
        ]

        if not healthy_nodes:
            return None

        node = healthy_nodes[self._current_index % len(healthy_nodes)]
        self._current_index += 1
        return node


class WeightedRoundRobinAlgorithm(LoadBalancingAlgorithm):
    """加权轮询算法"""

    def __init__(self):
        self._current_weight = 0
        self._gcd = 1

    async def select_node(self, nodes: list[ProcessorNode]) -> ProcessorNode | None:
        """按权重选择节点"""
        if not nodes:
            return None

        healthy_nodes = [
            n for n in nodes if n.health_status in (HealthStatus.HEALTHY, HealthStatus.DEGRADED)
        ]

        if not healthy_nodes:
            return None

        # 计算最大权重
        max_weight = max(n.weight for n in healthy_nodes)

        while True:
            self._current_weight += 1
            if self._current_weight > max_weight:
                self._current_weight = 1

            for node in healthy_nodes:
                if node.weight >= self._current_weight:
                    return node


class LeastConnectionsAlgorithm(LoadBalancingAlgorithm):
    """最少连接算法"""

    async def select_node(self, nodes: list[ProcessorNode]) -> ProcessorNode | None:
        """选择活跃连接最少的节点"""
        if not nodes:
            return None

        healthy_nodes = [
            n for n in nodes if n.health_status in (HealthStatus.HEALTHY, HealthStatus.DEGRADED)
        ]

        if not healthy_nodes:
            return None

        # 选择活跃连接最少的节点
        return min(healthy_nodes, key=lambda n: n.active_connections)


class LeastResponseTimeAlgorithm(LoadBalancingAlgorithm):
    """最短响应时间算法"""

    async def select_node(self, nodes: list[ProcessorNode]) -> ProcessorNode | None:
        """选择平均响应时间最短的节点"""
        if not nodes:
            return None

        healthy_nodes = [
            n for n in nodes if n.health_status in (HealthStatus.HEALTHY, HealthStatus.DEGRADED)
        ]

        if not healthy_nodes:
            return None

        # 选择响应时间最短的节点
        return min(healthy_nodes, key=lambda n: n.avg_response_time)


class ConsistentHashAlgorithm(LoadBalancingAlgorithm):
    """一致性哈希算法"""

    def __init__(self, replicas: int = 150):
        """初始化一致性哈希

        Args:
            replicas: 虚拟节点数量
        """
        self.replicas = replicas
        self._ring: dict[int, ProcessorNode] = {}
        self._sorted_keys: list[int] = []

    def _build_ring(self, nodes: list[ProcessorNode]) -> None:
        """构建哈希环"""
        self._ring.clear()
        self._sorted_keys.clear()

        for node in nodes:
            for i in range(self.replicas):
                key = self._hash_key(f"{node.id}:{i}")
                self._ring[key] = node
                self._sorted_keys.append(key)

        self._sorted_keys.sort()

    def _hash_key(self, key: str) -> int:
        """计算哈希值"""
        # Python 3.14兼容性：不使用usedforsecurity参数
        hash_obj = hashlib.md5(key.encode('utf-8'))
        return int(hash_obj.hexdigest(), 16)

    async def select_node(
        self,
        nodes: list[ProcessorNode],
        request_key: Optional[str] = None,
    ) -> ProcessorNode | None:
        """根据请求键选择节点"""
        if not nodes:
            return None

        healthy_nodes = [
            n for n in nodes if n.health_status in (HealthStatus.HEALTHY, HealthStatus.DEGRADED)
        ]

        if not healthy_nodes:
            return None

        # 重建哈希环
        self._build_ring(healthy_nodes)

        # 如果没有提供请求键,使用随机键
        if request_key is None:
            request_key = str(time.time())

        hash_value = self._hash_key(request_key)

        # 查找节点
        for key in self._sorted_keys:
            if hash_value <= key:
                return self._ring[key]

        # 环绕到第一个节点
        return self._ring[self._sorted_keys[0]]


class AdaptiveAlgorithm(LoadBalancingAlgorithm):
    """自适应算法 - 动态选择最优策略"""

    def __init__(self):
        self._algorithms = {
            "least_connections": LeastConnectionsAlgorithm(),
            "least_response_time": LeastResponseTimeAlgorithm(),
        }
        self._current_algorithm = "least_connections"
        self._last_evaluation = datetime.now()

    async def select_node(self, nodes: list[ProcessorNode]) -> ProcessorNode | None:
        """根据当前状态动态选择算法"""
        if not nodes:
            return None

        # 每10秒评估一次当前算法
        if (datetime.now() - self._last_evaluation).total_seconds() > 10:
            self._evaluate_and_switch(nodes)

        algorithm = self._algorithms[self._current_algorithm]
        return await algorithm.select_node(nodes)

    def _evaluate_and_switch(self, nodes: list[ProcessorNode]) -> None:
        """评估并切换算法"""
        if not nodes:
            return

        # 根据节点状态选择算法
        avg_connections = sum(n.active_connections for n in nodes) / len(nodes)
        avg_response_time = sum(n.avg_response_time for n in nodes) / len(nodes)

        # 连接数差异大时使用最少连接
        connection_variance = sum(
            (n.active_connections - avg_connections) ** 2 for n in nodes
        ) / len(nodes)

        response_variance = sum(
            (n.avg_response_time - avg_response_time) ** 2 for n in nodes
        ) / len(nodes)

        if connection_variance > response_variance:
            self._current_algorithm = "least_connections"
        else:
            self._current_algorithm = "least_response_time"

        self._last_evaluation = datetime.now()


class DynamicLoadBalancer:
    """动态负载均衡器

    智能地将请求分配到不同的处理器。

    使用示例:
        >>> balancer = DynamicLoadBalancer(
        >>>     strategy=LoadBalancingStrategy.ADAPTIVE
        >>> )
        >>> await balancer.initialize()
        >>>
        >>> # 添加处理器节点
        >>> balancer.add_node("processor1", processor1, weight=2)
        >>> balancer.add_node("processor2", processor2, weight=1)
        >>>
        >>> # 路由请求
        >>> result = await balancer.route_request(
        >>>     lambda p: p.process(data)
        >>> )
    """

    def __init__(
        self,
        strategy: LoadBalancingStrategy = LoadBalancingStrategy.ADAPTIVE,
        health_check_interval: float = 30.0,  # 健康检查间隔(秒)
        enable_health_check: bool = True,
    ):
        """初始化负载均衡器

        Args:
            strategy: 负载均衡策略
            health_check_interval: 健康检查间隔
            enable_health_check: 是否启用健康检查
        """
        self.strategy = strategy
        self.health_check_interval = health_check_interval
        self.enable_health_check = enable_health_check

        # 节点
        self._nodes: dict[str, ProcessorNode] = {}

        # 算法
        self._algorithm = self._create_algorithm(strategy)

        # 指标
        self._metrics = LoadBalancerMetrics()

        # 锁
        self._lock = asyncio.Lock()

        # 后台任务
        self._health_check_task: asyncio.Task | None = None
        self._running = False

        # 请求键生成器
        self._request_counter = 0

        logger.info(
            f"⚖️ 初始化动态负载均衡器 " f"(策略={strategy.value}, 健康检查={enable_health_check})"
        )

    def _create_algorithm(self, strategy: LoadBalancingStrategy) -> LoadBalancingAlgorithm:
        """创建算法实例"""
        if strategy == LoadBalancingStrategy.ROUND_ROBIN:
            return RoundRobinAlgorithm()
        elif strategy == LoadBalancingStrategy.WEIGHTED_ROUND_ROBIN:
            return WeightedRoundRobinAlgorithm()
        elif strategy == LoadBalancingStrategy.LEAST_CONNECTIONS:
            return LeastConnectionsAlgorithm()
        elif strategy == LoadBalancingStrategy.LEAST_RESPONSE_TIME:
            return LeastResponseTimeAlgorithm()
        elif strategy == LoadBalancingStrategy.CONSISTENT_HASH:
            return ConsistentHashAlgorithm()
        else:  # ADAPTIVE
            return AdaptiveAlgorithm()

    async def initialize(self) -> None:
        """初始化负载均衡器"""
        if self._running:
            return

        self._running = True

        # 启动健康检查
        if self.enable_health_check:
            self._health_check_task = asyncio.create_task(self._health_check_loop())

        logger.info("✅ 动态负载均衡器启动完成")

    async def shutdown(self) -> None:
        """关闭负载均衡器"""
        logger.info("🛑 关闭动态负载均衡器...")

        self._running = False

        if self._health_check_task:
            self._health_check_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._health_check_task

        logger.info("✅ 动态负载均衡器已关闭")

    def add_node(
        self,
        node_id: str,
        processor: Any,
        weight: int = 1,
        metadata: Optional[dict[str, Any]] = None,
    ) -> None:
        """添加处理器节点

        Args:
            node_id: 节点ID
            processor: 处理器实例
            weight: 权重
            metadata: 元数据
        """
        node = ProcessorNode(
            id=node_id,
            processor=processor,
            weight=weight,
            metadata=metadata or {},
        )
        self._nodes[node_id] = node
        self._metrics.node_request_counts[node_id] = 0

        logger.info(f"📦 添加节点: {node_id} (权重={weight})")

    def remove_node(self, node_id: str) -> None:
        """移除处理器节点"""
        if node_id in self._nodes:
            del self._nodes[node_id]
            logger.info(f"🗑️ 移除节点: {node_id}")

    def update_node_weight(self, node_id: str, weight: int) -> None:
        """更新节点权重"""
        if node_id in self._nodes:
            self._nodes[node_id].weight = weight
            logger.info(f"⚖️ 更新权重: {node_id} -> {weight}")

    async def route_request(
        self,
        handler: Callable[[Any], Any],
        request_key: Optional[str] = None,
        **kwargs: Any,
    ) -> RoutingResult:
        """路由请求

        Args:
            handler: 处理函数(接收处理器节点作为参数)
            request_key: 请求键(用于一致性哈希)
            **kwargs: 额外参数

        Returns:
            路由结果
        """
        start_time = time.time()
        self._metrics.total_requests += 1

        try:
            # 选择节点
            select_start = time.time()

            nodes = list(self._nodes.values())
            if self.strategy == LoadBalancingStrategy.CONSISTENT_HASH:
                node = await self._algorithm.select_node(nodes, request_key)
            else:
                node = await self._algorithm.select_node(nodes)

            select_time = time.time() - select_start

            if node is None:
                raise RuntimeError("没有可用的处理器节点")

            # 更新节点状态
            node.active_connections += 1
            node.total_requests += 1

            # 更新指标
            if node.id not in self._metrics.node_request_counts:
                self._metrics.node_request_counts[node.id] = 0
            self._metrics.node_request_counts[node.id] += 1

            # 处理请求
            process_start = time.time()

            if inspect.iscoroutinefunction(handler):
                result = await handler(node.processor, **kwargs)
            else:
                result = handler(node.processor, **kwargs)

            process_time = time.time() - process_start
            total_time = time.time() - start_time

            # 更新节点状态
            node.active_connections -= 1
            node.successful_requests += 1

            # 更新平均响应时间(指数移动平均)
            alpha = 0.2
            node.avg_response_time = alpha * process_time + (1 - alpha) * node.avg_response_time

            # 更新指标
            self._metrics.successful_requests += 1
            self._metrics.total_routing_time += select_time
            self._metrics.total_processing_time += process_time

            logger.debug(
                f"✅ 请求路由成功: {node.id} "
                f"(路由={select_time:.3f}s, 处理={process_time:.3f}s)"
            )

            return RoutingResult(
                success=True,
                node_id=node.id,
                result=result,
                routing_time=select_time,
                processing_time=process_time,
                total_time=total_time,
            )

        except Exception as e:
            total_time = time.time() - start_time

            # 更新失败指标
            if node:
                node.active_connections -= 1
                node.failed_requests += 1

            self._metrics.failed_requests += 1

            logger.error(f"❌ 请求路由失败: {e}")

            return RoutingResult(
                success=False,
                node_id=node.id if node else None,
                error=e,
                total_time=total_time,
            )

    async def _health_check_loop(self) -> None:
        """健康检查循环"""
        while self._running:
            try:
                await asyncio.sleep(self.health_check_interval)
                await self._perform_health_checks()

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"❌ 健康检查异常: {e}")

    async def _perform_health_checks(self) -> None:
        """执行健康检查"""
        for node in self._nodes.values():
            try:
                # 检查处理器是否有health_check方法
                if hasattr(node.processor, "health_check"):
                    is_healthy = node.processor.health_check()

                    if is_healthy:
                        if node.health_status != HealthStatus.HEALTHY:
                            logger.info(f"💚 节点恢复健康: {node.id}")
                            node.health_status = HealthStatus.HEALTHY
                    else:
                        if node.health_status == HealthStatus.HEALTHY:
                            logger.warning(f"💛 节点状态降级: {node.id}")
                            node.health_status = HealthStatus.DEGRADED

                # 检查失败率
                if node.failure_rate > 0.5 and node.total_requests > 10:
                    logger.warning(f"❌ 节点失败率过高: {node.id} ({node.failure_rate:.1%})")
                    node.health_status = HealthStatus.UNHEALTHY

                node.last_health_check = datetime.now()

            except Exception as e:
                logger.error(f"❌ 健康检查失败 {node.id}: {e}")
                node.health_status = HealthStatus.UNHEALTHY

    def get_metrics(self) -> LoadBalancerMetrics:
        """获取指标"""
        # 计算平均响应时间
        if self._metrics.total_requests > 0:
            self._metrics.avg_response_time = (
                self._metrics.total_processing_time / self._metrics.total_requests
            )

        return self._metrics

    def get_node_status(self) -> dict[str, dict[str, Any]]:
        """获取节点状态"""
        return {
            node_id: {
                "weight": node.weight,
                "active_connections": node.active_connections,
                "total_requests": node.total_requests,
                "success_rate": node.success_rate,
                "avg_response_time": node.avg_response_time,
                "health_status": node.health_status.value,
                "load_score": node.load_score,
            }
            for node_id, node in self._nodes.items()
        }

    def change_strategy(self, new_strategy: LoadBalancingStrategy) -> None:
        """更改负载均衡策略

        Args:
            new_strategy: 新策略
        """
        if new_strategy != self.strategy:
            old_strategy = self.strategy
            self.strategy = new_strategy
            self._algorithm = self._create_algorithm(new_strategy)

            self._metrics.strategy_changes += 1
            self._metrics.last_strategy_change = datetime.now()

            logger.info(f"🔄 策略切换: {old_strategy.value} -> {new_strategy.value}")


# 便捷函数
def create_load_balancer(
    strategy: LoadBalancingStrategy = LoadBalancingStrategy.ADAPTIVE,
    health_check_interval: float = 30.0,
) -> DynamicLoadBalancer:
    """创建负载均衡器"""
    return DynamicLoadBalancer(
        strategy=strategy,
        health_check_interval=health_check_interval,
    )


__all__ = [
    "DynamicLoadBalancer",
    "HealthStatus",
    "LoadBalancerMetrics",
    "LoadBalancingStrategy",
    "ProcessorNode",
    "RoutingResult",
    "create_load_balancer",
]
