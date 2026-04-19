"""
Athena Service Discovery - Load Balancing Plugins
服务发现系统负载均衡插件实现

Author: Athena AI Team
Version: 2.0.0
"""

import asyncio
import bisect
import hashlib
import logging
import random
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

from .core_service_registry import HealthStatus, ProtocolType, ServiceInstance

logger = logging.getLogger(__name__)


class LoadBalanceAlgorithm(Enum):
    """负载均衡算法类型"""

    ROUND_ROBIN = "round_robin"
    WEIGHTED_ROUND_ROBIN = "weighted_round_robin"
    LEAST_CONNECTIONS = "least_connections"
    LEAST_RESPONSE_TIME = "least_response_time"
    RESPONSE_TIME_BASED = "response_time_based"
    CONSISTENT_HASH = "consistent_hash"
    RANDOM = "random"
    IP_HASH = "ip_hash"
    FAIR = "fair"


@dataclass
class RequestContext:
    """请求上下文"""

    request_id: str
    service_name: str
    method: str
    path: str
    headers: dict[str, str]
    query_params: dict[str, str]
    timestamp: datetime
    client_ip: str
    user_agent: str
    previous_attempts: list[str] = field(default_factory=list)
    preferred_instance: str | None = None
    stickiness_cookie: str | None = None


@dataclass
class ServiceMetrics:
    """服务指标"""

    service_id: str
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    total_response_time: float = 0.0
    active_connections: int = 0
    last_request_time: datetime | None = None
    avg_response_time: float = 0.0
    error_rate: float = 0.0
    throughput: float = 0.0

    def update_metrics(self, response_time: float, success: bool):
        """更新指标"""
        self.total_requests += 1
        self.total_response_time += response_time
        self.last_request_time = datetime.now()

        if success:
            self.successful_requests += 1
        else:
            self.failed_requests += 1

        # 计算平均值
        self.avg_response_time = self.total_response_time / self.total_requests
        self.error_rate = self.failed_requests / self.total_requests

        # 计算吞吐量（每秒请求数）
        if self.last_request_time:
            time_diff = (datetime.now() - self.last_request_time).total_seconds()
            if time_diff > 0:
                self.throughput = 1.0 / time_diff


class LoadBalancer(ABC):
    """负载均衡器基类"""

    def __init__(self, algorithm: LoadBalanceAlgorithm):
        self.algorithm = algorithm
        self.service_metrics: dict[str, ServiceMetrics] = {}

    @abstractmethod
    async def select_instance(
        self, instances: list[ServiceInstance], context: RequestContext
    ) -> ServiceInstance:
        """选择服务实例"""
        pass

    def get_metrics(self, service_id: str) -> ServiceMetrics | None:
        """获取服务指标"""
        return self.service_metrics.get(service_id)

    def update_metrics(self, service_id: str, response_time: float, success: bool):
        """更新服务指标"""
        if service_id not in self.service_metrics:
            self.service_metrics[service_id] = ServiceMetrics(service_id=service_id)

        self.service_metrics[service_id].update_metrics(response_time, success)


class RoundRobinBalancer(LoadBalancer):
    """轮询负载均衡器"""

    def __init__(self):
        super().__init__(LoadBalanceAlgorithm.ROUND_ROBIN)
        self.current_index = 0

    async def select_instance(
        self, instances: list[ServiceInstance], context: RequestContext
    ) -> ServiceInstance:
        """轮询选择实例"""
        if not instances:
            raise ValueError("No instances available")

        # 过滤健康实例
        healthy_instances = [
            instance
            for instance in instances
            if instance.health_status in [HealthStatus.HEALTHY, HealthStatus.DEGRADED]
        ]

        if not healthy_instances:
            raise ValueError("No healthy instances available")

        # 轮询选择
        selected_instance = healthy_instances[self.current_index % len(healthy_instances)]
        self.current_index += 1

        return selected_instance


class WeightedRoundRobinBalancer(LoadBalancer):
    """加权轮询负载均衡器"""

    def __init__(self):
        super().__init__(LoadBalanceAlgorithm.WEIGHTED_ROUND_ROBIN)
        self.current_weights = {}

    async def select_instance(
        self, instances: list[ServiceInstance], context: RequestContext
    ) -> ServiceInstance:
        """加权轮询选择实例"""
        if not instances:
            raise ValueError("No instances available")

        # 过滤健康实例
        healthy_instances = [
            instance
            for instance in instances
            if instance.health_status in [HealthStatus.HEALTHY, HealthStatus.DEGRADED]
        ]

        if not healthy_instances:
            raise ValueError("No healthy instances available")

        # 计算总权重
        total_weight = sum(instance.weight for instance in healthy_instances)

        # 加权轮询算法
        for instance in healthy_instances:
            service_id = instance.service_id
            if service_id not in self.current_weights:
                self.current_weights[service_id] = 0

            self.current_weights[service_id] += instance.weight

            if self.current_weights[service_id] >= total_weight:
                self.current_weights[service_id] -= total_weight
                return instance

        # 如果没有实例被选中，返回权重最高的实例
        return max(healthy_instances, key=lambda x: x.weight)


class LeastConnectionsBalancer(LoadBalancer):
    """最少连接负载均衡器"""

    def __init__(self):
        super().__init__(LoadBalanceAlgorithm.LEAST_CONNECTIONS)
        self.connection_counts: dict[str, int] = {}

    async def select_instance(
        self, instances: list[ServiceInstance], context: RequestContext
    ) -> ServiceInstance:
        """选择连接数最少的实例"""
        if not instances:
            raise ValueError("No instances available")

        # 过滤健康实例
        healthy_instances = [
            instance
            for instance in instances
            if instance.health_status in [HealthStatus.HEALTHY, HealthStatus.DEGRADED]
        ]

        if not healthy_instances:
            raise ValueError("No healthy instances available")

        # 获取连接数
        connection_counts = {
            instance.service_id: self.connection_counts.get(instance.service_id, 0)
            for instance in healthy_instances
        }

        # 选择连接数最少的实例
        selected_instance = min(
            healthy_instances, key=lambda instance: connection_counts[instance.service_id]
        )

        # 增加连接计数
        self.connection_counts[selected_instance.service_id] += 1

        return selected_instance

    def release_connection(self, service_id: str):
        """释放连接"""
        if service_id in self.connection_counts:
            self.connection_counts[service_id] = max(0, self.connection_counts[service_id] - 1)


class ResponseTimeBasedBalancer(LoadBalancer):
    """基于响应时间的负载均衡器"""

    def __init__(self):
        super().__init__(LoadBalanceAlgorithm.RESPONSE_TIME_BASED)

    async def select_instance(
        self, instances: list[ServiceInstance], context: RequestContext
    ) -> ServiceInstance:
        """基于响应时间选择最优实例"""
        if not instances:
            raise ValueError("No instances available")

        # 过滤健康实例
        healthy_instances = [
            instance
            for instance in instances
            if instance.health_status in [HealthStatus.HEALTHY, HealthStatus.DEGRADED]
        ]

        if not healthy_instances:
            raise ValueError("No healthy instances available")

        # 计算加权响应时间
        weighted_times = {}
        for instance in healthy_instances:
            base_time = self.service_metrics.get(
                instance.service_id, ServiceMetrics(instance.service_id)
            ).avg_response_time

            # 根据健康状态调整权重
            if instance.health_status == HealthStatus.HEALTHY:
                health_factor = 1.0
            elif instance.health_status == HealthStatus.DEGRADED:
                health_factor = 1.5
            else:
                health_factor = 10.0  # 严重惩罚

            # 如果没有历史数据，给一个默认值
            if base_time == 0:
                base_time = 1000  # 默认1秒

            weighted_times[instance.service_id] = base_time * health_factor

        # 选择响应时间最短的实例
        selected_instance = min(
            healthy_instances,
            key=lambda instance: weighted_times.get(instance.service_id, float("inf")),
        )

        return selected_instance


class ConsistentHashBalancer(LoadBalancer):
    """一致性哈希负载均衡器"""

    def __init__(self, virtual_nodes: int = 150):
        super().__init__(LoadBalanceAlgorithm.CONSISTENT_HASH)
        self.virtual_nodes = virtual_nodes
        self.ring = {}
        self.sorted_keys = []
        self._build_ring_lock = asyncio.Lock()

    async def select_instance(
        self, instances: list[ServiceInstance], context: RequestContext
    ) -> ServiceInstance:
        """一致性哈希选择实例"""
        if not instances:
            raise ValueError("No instances available")

        # 过滤健康实例
        healthy_instances = [
            instance
            for instance in instances
            if instance.health_status in [HealthStatus.HEALTHY, HealthStatus.DEGRADED]
        ]

        if not healthy_instances:
            raise ValueError("No healthy instances available")

        # 构建哈希环
        await self._build_hash_ring(healthy_instances)

        # 计算请求的哈希值
        hash_key = self._hash_request(context)

        # 在环上找到下一个节点
        selected_instance = await self._find_next_instance(hash_key)

        return selected_instance

    async def _build_hash_ring(self, instances: list[ServiceInstance]):
        """构建一致性哈希环"""
        async with self._build_ring_lock:
            self.ring.clear()

            for instance in instances:
                for i in range(self.virtual_nodes):
                    virtual_key = f"{instance.service_id}:{i}"
                    hash_value = self._hash(virtual_key)
                    self.ring[hash_value] = instance

            self.sorted_keys = sorted(self.ring.keys())

    async def _find_next_instance(self, hash_key: int) -> ServiceInstance:
        """在环上找到下一个实例"""
        if not self.sorted_keys:
            raise ValueError("No instances available")

        # 二分查找
        idx = bisect.bisect_right(self.sorted_keys, hash_key)
        if idx == len(self.sorted_keys):
            idx = 0

        return self.ring[self.sorted_keys[idx]]

    def _hash_request(self, context: RequestContext) -> int:
        """计算请求哈希值"""
        # 使用请求路径和客户端IP作为哈希输入
        hash_input = f"{context.path}:{context.client_ip}"
        if context.stickiness_cookie:
            hash_input += f":{context.stickiness_cookie}"

        return self._hash(hash_input)

    def _hash(self, key: str) -> int:
        """计算字符串哈希值"""
        return int(hashlib.md5(key.encode()).hexdigest(), 16)


class RandomBalancer(LoadBalancer):
    """随机负载均衡器"""

    def __init__(self):
        super().__init__(LoadBalanceAlgorithm.RANDOM)

    async def select_instance(
        self, instances: list[ServiceInstance], context: RequestContext
    ) -> ServiceInstance:
        """随机选择实例"""
        if not instances:
            raise ValueError("No instances available")

        # 过滤健康实例
        healthy_instances = [
            instance
            for instance in instances
            if instance.health_status in [HealthStatus.HEALTHY, HealthStatus.DEGRADED]
        ]

        if not healthy_instances:
            raise ValueError("No healthy instances available")

        return random.choice(healthy_instances)


class IPHashBalancer(LoadBalancer):
    """IP哈希负载均衡器"""

    def __init__(self):
        super().__init__(LoadBalanceAlgorithm.IP_HASH)

    async def select_instance(
        self, instances: list[ServiceInstance], context: RequestContext
    ) -> ServiceInstance:
        """基于客户端IP哈希选择实例"""
        if not instances:
            raise ValueError("No instances available")

        # 过滤健康实例
        healthy_instances = [
            instance
            for instance in instances
            if instance.health_status in [HealthStatus.HEALTHY, HealthStatus.DEGRADED]
        ]

        if not healthy_instances:
            raise ValueError("No healthy instances available")

        # 计算IP哈希
        hash_value = int(hashlib.md5(context.client_ip.encode()).hexdigest(), 16)
        index = hash_value % len(healthy_instances)

        return healthy_instances[index]


class FairBalancer(LoadBalancer):
    """公平调度负载均衡器"""

    def __init__(self):
        super().__init__(LoadBalanceAlgorithm.FAIR)
        self.request_counts = {}
        self.last_reset_time = time.time()
        self.reset_interval = 300  # 5分钟重置一次

    async def select_instance(
        self, instances: list[ServiceInstance], context: RequestContext
    ) -> ServiceInstance:
        """公平调度选择实例"""
        if not instances:
            raise ValueError("No instances available")

        # 定期重置计数器
        current_time = time.time()
        if current_time - self.last_reset_time > self.reset_interval:
            self.request_counts.clear()
            self.last_reset_time = current_time

        # 过滤健康实例
        healthy_instances = [
            instance
            for instance in instances
            if instance.health_status in [HealthStatus.HEALTHY, HealthStatus.DEGRADED]
        ]

        if not healthy_instances:
            raise ValueError("No healthy instances available")

        # 计算每个实例的请求数
        request_counts = {}
        for instance in healthy_instances:
            service_id = instance.service_id
            request_counts[service_id] = self.request_counts.get(service_id, 0)

        # 选择请求数最少的实例
        selected_instance = min(
            healthy_instances, key=lambda instance: request_counts[instance.service_id]
        )

        # 增加请求计数
        self.request_counts[selected_instance.service_id] += 1

        return selected_instance


class AdaptiveLoadBalancer(LoadBalancer):
    """自适应负载均衡器"""

    def __init__(self):
        super().__init__(LoadBalanceAlgorithm.RESPONSE_TIME_BASED)  # 默认算法
        self.algorithms = {
            LoadBalanceAlgorithm.ROUND_ROBIN: RoundRobinBalancer(),
            LoadBalanceAlgorithm.WEIGHTED_ROUND_ROBIN: WeightedRoundRobinBalancer(),
            LoadBalanceAlgorithm.LEAST_CONNECTIONS: LeastConnectionsBalancer(),
            LoadBalanceAlgorithm.RESPONSE_TIME_BASED: ResponseTimeBasedBalancer(),
            LoadBalanceAlgorithm.CONSISTENT_HASH: ConsistentHashBalancer(),
            LoadBalanceAlgorithm.RANDOM: RandomBalancer(),
            LoadBalanceAlgorithm.IP_HASH: IPHashBalancer(),
            LoadBalanceAlgorithm.FAIR: FairBalancer(),
        }
        self.algorithm_scores = {}
        self.last_evaluation = {}
        self.evaluation_interval = 60  # 1分钟评估一次

    async def select_instance(
        self, instances: list[ServiceInstance], context: RequestContext
    ) -> ServiceInstance:
        """自适应选择负载均衡算法"""
        service_name = context.service_name

        # 检查是否需要重新评估算法
        current_time = time.time()
        if (
            service_name not in self.last_evaluation
            or current_time - self.last_evaluation[service_name] > self.evaluation_interval
        ):
            best_algorithm = await self._select_best_algorithm(service_name, instances)
            self.algorithm = best_algorithm
            self.last_evaluation[service_name] = current_time

            logger.info(
                f"Selected load balance algorithm for {service_name}: {best_algorithm.value}"
            )

        # 使用当前选择的算法
        balancer = self.algorithms[self.algorithm]
        return await balancer.select_instance(instances, context)

    async def _select_best_algorithm(
        self, service_name: str, instances: list[ServiceInstance]
    ) -> LoadBalanceAlgorithm:
        """选择最优负载均衡算法"""
        algorithm_scores = {}

        for algorithm, _balancer in self.algorithms.items():
            score = await self._evaluate_algorithm_performance(algorithm, service_name, instances)
            algorithm_scores[algorithm] = score

        # 选择得分最高的算法
        best_algorithm = max(algorithm_scores.items(), key=lambda x: x[1])[0]
        return best_algorithm

    async def _evaluate_algorithm_performance(
        self, algorithm: LoadBalanceAlgorithm, service_name: str, instances: list[ServiceInstance]
    ) -> float:
        """评估算法性能"""
        # 计算服务的综合指标
        total_response_time = 0
        total_error_rate = 0
        total_throughput = 0
        instance_count = 0

        for instance in instances:
            metrics = self.service_metrics.get(instance.service_id)
            if metrics and metrics.total_requests > 0:
                total_response_time += metrics.avg_response_time
                total_error_rate += metrics.error_rate
                total_throughput += metrics.throughput
                instance_count += 1

        if instance_count == 0:
            return 50.0  # 默认分数

        # 计算平均值
        avg_response_time = total_response_time / instance_count
        avg_error_rate = total_error_rate / instance_count
        avg_throughput = total_throughput / instance_count

        # 归一化评分
        response_time_score = self._normalize_score(avg_response_time, 0, 5000)  # 0-5秒
        error_rate_score = self._normalize_score(avg_error_rate, 0, 1)  # 0-100%
        throughput_score = self._normalize_score(
            avg_throughput, 0, 1000, reverse=True
        )  # 吞吐量越高越好

        # 根据算法类型调整评分权重
        if algorithm in [
            LoadBalanceAlgorithm.RESPONSE_TIME_BASED,
            LoadBalanceAlgorithm.LEAST_RESPONSE_TIME,
        ]:
            weights = (0.6, 0.3, 0.1)  # 响应时间权重更高
        elif algorithm == LoadBalanceAlgorithm.LEAST_CONNECTIONS:
            weights = (0.3, 0.4, 0.3)  # 错误率权重更高
        elif algorithm == LoadBalanceAlgorithm.CONSISTENT_HASH:
            weights = (0.3, 0.3, 0.4)  # 吞吐量权重更高
        else:
            weights = (0.4, 0.3, 0.3)  # 默认权重

        # 计算加权评分
        total_score = (
            response_time_score * weights[0]
            + error_rate_score * weights[1]
            + throughput_score * weights[2]
        )

        return total_score

    def _normalize_score(
        self, value: float, min_val: float, max_val: float, reverse: bool = False
    ) -> float:
        """归一化评分到0-100"""
        if max_val <= min_val:
            return 50.0

        if value <= min_val:
            normalized = 1.0 if not reverse else 0.0
        elif value >= max_val:
            normalized = 0.0 if not reverse else 1.0
        else:
            normalized = 1.0 - (value - min_val) / (max_val - min_val)
            if reverse:
                normalized = 1.0 - normalized

        return normalized * 100.0


class LoadBalancingManager:
    """负载均衡管理器"""

    def __init__(self):
        self.balancers = {}
        self.default_algorithm = LoadBalanceAlgorithm.RESPONSE_TIME_BASED
        self.service_configs = {}

    def register_service_balancer(self, service_name: str, algorithm: LoadBalanceAlgorithm):
        """为服务注册负载均衡器"""
        if algorithm == LoadBalanceAlgorithm.ADAPTIVE:
            balancer = AdaptiveLoadBalancer()
        else:
            balancer_class = self._get_balancer_class(algorithm)
            balancer = balancer_class()

        self.balancers[service_name] = balancer
        self.service_configs[service_name] = algorithm

    def get_service_balancer(self, service_name: str) -> LoadBalancer:
        """获取服务的负载均衡器"""
        if service_name not in self.balancers:
            # 使用默认算法创建
            self.register_service_balancer(service_name, self.default_algorithm)

        return self.balancers[service_name]

    def _get_balancer_class(self, algorithm: LoadBalanceAlgorithm):
        """获取负载均衡器类"""
        balancer_map = {
            LoadBalanceAlgorithm.ROUND_ROBIN: RoundRobinBalancer,
            LoadBalanceAlgorithm.WEIGHTED_ROUND_ROBIN: WeightedRoundRobinBalancer,
            LoadBalanceAlgorithm.LEAST_CONNECTIONS: LeastConnectionsBalancer,
            LoadBalanceAlgorithm.RESPONSE_TIME_BASED: ResponseTimeBasedBalancer,
            LoadBalanceAlgorithm.CONSISTENT_HASH: ConsistentHashBalancer,
            LoadBalanceAlgorithm.RANDOM: RandomBalancer,
            LoadBalanceAlgorithm.IP_HASH: IPHashBalancer,
            LoadBalanceAlgorithm.FAIR: FairBalancer,
        }

        return balancer_map.get(algorithm, RoundRobinBalancer)

    async def select_instance(
        self, service_name: str, instances: list[ServiceInstance], context: RequestContext
    ) -> ServiceInstance:
        """选择服务实例"""
        balancer = self.get_service_balancer(service_name)
        return await balancer.select_instance(instances, context)

    def update_service_metrics(self, service_id: str, response_time: float, success: bool):
        """更新服务指标"""
        for balancer in self.balancers.values():
            balancer.update_metrics(service_id, response_time, success)

    def get_service_metrics(self, service_id: str) -> ServiceMetrics | None:
        """获取服务指标"""
        for balancer in self.balancers.values():
            metrics = balancer.get_metrics(service_id)
            if metrics:
                return metrics
        return None


# 工厂函数
def create_load_balancing_manager() -> LoadBalancingManager:
    """创建负载均衡管理器"""
    return LoadBalancingManager()


def create_balancer(algorithm: LoadBalanceAlgorithm) -> LoadBalancer:
    """创建负载均衡器"""
    manager = create_load_balancing_manager()
    manager.register_service_balancer("default", algorithm)
    return manager.get_service_balancer("default")


# 使用示例
async def main():
    """主函数示例"""
    # 创建负载均衡管理器
    manager = create_load_balancing_manager()

    # 注册不同服务的负载均衡算法
    manager.register_service_balancer("user-service", LoadBalanceAlgorithm.ROUND_ROBIN)
    manager.register_service_balancer("order-service", LoadBalanceAlgorithm.WEIGHTED_ROUND_ROBIN)
    manager.register_service_balancer("api-service", LoadBalanceAlgorithm.ADAPTIVE)

    # 模拟服务实例
    instances = [
        ServiceInstance(
            service_id="user-service-1",
            service_name="user-service",
            version="1.0.0",
            namespace="default",
            host="localhost",
            port=8001,
            protocol=ProtocolType.HTTP,
            weight=100,
            health_status=HealthStatus.HEALTHY,
        ),
        ServiceInstance(
            service_id="user-service-2",
            service_name="user-service",
            version="1.0.0",
            namespace="default",
            host="localhost",
            port=8002,
            protocol=ProtocolType.HTTP,
            weight=200,
            health_status=HealthStatus.HEALTHY,
        ),
    ]

    # 创建请求上下文
    context = RequestContext(
        request_id="req-123",
        service_name="user-service",
        method="GET",
        path="/api/users",
        headers={},
        query_params={},
        timestamp=datetime.now(),
        client_ip="192.168.1.100",
        user_agent="curl/7.68.0",
    )

    # 执行负载均衡
    for i in range(10):
        selected = await manager.select_instance("user-service", instances, context)
        print(f"Request {i + 1}: Selected {selected.service_id}")

        # 模拟请求完成
        response_time = random.uniform(50, 500)
        success = random.random() > 0.1  # 90%成功率

        manager.update_service_metrics(selected.service_id, response_time, success)

    # 查看指标
    metrics = manager.get_service_metrics("user-service-1")
    if metrics:
        print(f"Service 1 metrics: {metrics}")


if __name__ == "__main__":
    asyncio.run(main())
