#!/usr/bin/env python3
from __future__ import annotations
"""
动态资源管理器
Dynamic Resource Manager

智能管理和动态分配系统资源,包括连接池、内存、CPU等
实现资源错误恢复和负载均衡
"""

import asyncio
import logging
import threading
import time
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any

import psutil

logger = logging.getLogger(__name__)


class ResourceType(Enum):
    """资源类型枚举"""

    DATABASE = "database"  # 数据库连接
    CACHE = "cache"  # 缓存连接
    EXTERNAL_API = "external_api"  # 外部API
    MODEL = "model"  # 模型实例
    MEMORY = "memory"  # 内存
    CPU = "cpu"  # CPU
    NETWORK = "network"  # 网络


class ResourceStatus(Enum):
    """资源状态枚举"""

    AVAILABLE = "available"  # 可用
    BUSY = "busy"  # 忙碌
    DEGRADED = "degraded"  # 降级
    UNAVAILABLE = "unavailable"  # 不可用
    RECOVERING = "recovering"  # 恢复中


class RecoveryStrategy(Enum):
    """恢复策略枚举"""

    RETRY = "retry"  # 重试
    FAILOVER = "failover"  # 故障转移
    CIRCUIT_BREAK = "circuit_break"  # 断路
    DEGRADE = "degrade"  # 降级
    RESTART = "restart"  # 重启
    SCALE = "scale"  # 扩容


@dataclass
class ResourceThreshold:
    """资源阈值配置"""

    warning_threshold: float = 0.7  # 警告阈值
    critical_threshold: float = 0.85  # 严重阈值
    recovery_threshold: float = 0.6  # 恢复阈值


@dataclass
class ResourceHealth:
    """资源健康状态"""

    resource_id: str
    resource_type: ResourceType
    status: ResourceStatus
    health_score: float  # 健康分数(0-1)
    current_load: float  # 当前负载(0-1)
    error_rate: float  # 错误率
    last_check_time: datetime
    consecutive_failures: int = 0  # 连续失败次数
    consecutive_successes: int = 0  # 连续成功次数
    avg_response_time: float = 0.0  # 平均响应时间(ms)
    message: str = ""


@dataclass
class ResourceAllocation:
    """资源分配记录"""

    allocation_id: str
    resource_id: str
    requester: str  # 请求者标识
    allocated_at: datetime
    duration: Optional[float] = None  # 持续时间(秒)
    status: str = "active"


@dataclass
class RecoveryAction:
    """恢复动作"""

    action_id: str
    resource_id: str
    strategy: RecoveryStrategy
    triggered_at: datetime
    executed: bool = False
    successful: bool = False
    duration: float = 0.0
    message: str = ""


class DynamicResourceManager:
    """
    动态资源管理器

    核心功能:
    1. 资源健康监控
    2. 动态资源分配
    3. 自动故障恢复
    4. 负载均衡
    """

    def __init__(self, check_interval: float = 5.0):
        """
        初始化资源管理器

        Args:
            check_interval: 健康检查间隔(秒)
        """
        self.name = "动态资源管理器 v1.0"
        self.version = "1.0.0"
        self.check_interval = check_interval

        # 资源注册表
        self.resources: dict[str, Any] = {}

        # 资源健康状态
        self.resource_health: dict[str, ResourceHealth] = {}

        # 资源阈值配置
        self.thresholds: dict[ResourceType, ResourceThreshold] = {
            ResourceType.DATABASE: ResourceThreshold(
                warning_threshold=0.7, critical_threshold=0.85
            ),
            ResourceType.CACHE: ResourceThreshold(warning_threshold=0.8, critical_threshold=0.9),
            ResourceType.EXTERNAL_API: ResourceThreshold(
                warning_threshold=0.6, critical_threshold=0.8
            ),
            ResourceType.MODEL: ResourceThreshold(warning_threshold=0.75, critical_threshold=0.85),
            ResourceType.MEMORY: ResourceThreshold(warning_threshold=0.7, critical_threshold=0.85),
            ResourceType.CPU: ResourceThreshold(warning_threshold=0.75, critical_threshold=0.9),
            ResourceType.NETWORK: ResourceThreshold(warning_threshold=0.7, critical_threshold=0.85),
        }

        # 资源分配记录
        self.allocations: dict[str, ResourceAllocation] = {}

        # 恢复动作历史
        self.recovery_history: list[RecoveryAction] = []

        # 资源回调函数
        self.recovery_callbacks: dict[RecoveryStrategy, Callable] = {
            RecoveryStrategy.RETRY: self._retry_resource,
            RecoveryStrategy.FAILOVER: self._failover_resource,
            RecoveryStrategy.DEGRADE: self._degrade_resource,
            RecoveryStrategy.RESTART: self._restart_resource,
        }

        # 监控线程
        self._monitor_thread: threading.Thread | None = None
        self._monitor_running = False

        # 统计信息
        self.stats = {
            "total_health_checks": 0,
            "total_recoveries": 0,
            "successful_recoveries": 0,
            "failed_recoveries": 0,
            "total_allocations": 0,
            "total_deallocations": 0,
            "recovery_by_strategy": dict.fromkeys(RecoveryStrategy, 0),
        }

    def register_resource(self, resource_id: str, resource_type: ResourceType, resource: Any):
        """
        注册资源

        Args:
            resource_id: 资源ID
            resource_type: 资源类型
            resource: 资源对象
        """
        self.resources[resource_id] = {
            "type": resource_type,
            "resource": resource,
            "registered_at": datetime.now(),
        }

        # 初始化健康状态
        self.resource_health[resource_id] = ResourceHealth(
            resource_id=resource_id,
            resource_type=resource_type,
            status=ResourceStatus.AVAILABLE,
            health_score=1.0,
            current_load=0.0,
            error_rate=0.0,
            last_check_time=datetime.now(),
        )

        logger.info(f"注册资源: {resource_id} ({resource_type.value})")

    def unregister_resource(self, resource_id: str) -> Any:
        """
        注销资源

        Args:
            resource_id: 资源ID
        """
        if resource_id in self.resources:
            self.resources[resource_id]["type"]
            del self.resources[resource_id]
            if resource_id in self.resource_health:
                del self.resource_health[resource_id]
            logger.info(f"注销资源: {resource_id}")

    async def allocate_resource(
        self, resource_type: ResourceType, requester: str, timeout: float = 5.0
    ) -> Optional[str]:
        """
        分配资源

        Args:
            resource_type: 资源类型
            requester: 请求者标识
            timeout: 超时时间

        Returns:
            资源ID或None
        """
        start_time = time.time()

        while time.time() - start_time < timeout:
            # 查找可用资源
            for resource_id, health in self.resource_health.items():
                if (
                    resource_id in self.resources
                    and self.resources[resource_id]["type"] == resource_type
                    and health.status == ResourceStatus.AVAILABLE
                    and health.current_load < self.thresholds[resource_type].warning_threshold
                ):

                    # 分配资源
                    allocation_id = f"alloc_{int(time.time() * 1000)}"
                    self.allocations[allocation_id] = ResourceAllocation(
                        allocation_id=allocation_id,
                        resource_id=resource_id,
                        requester=requester,
                        allocated_at=datetime.now(),
                    )

                    # 更新资源状态
                    health.status = ResourceStatus.BUSY
                    health.current_load = min(1.0, health.current_load + 0.1)

                    self.stats["total_allocations"] += 1
                    logger.info(f"分配资源: {resource_id} -> {requester}")

                    return resource_id

            # 等待后重试
            await asyncio.sleep(0.1)

        logger.warning(f"资源分配超时: {resource_type.value} -> {requester}")
        return None

    async def deallocate_resource(self, allocation_id: str):
        """
        释放资源

        Args:
            allocation_id: 分配ID
        """
        if allocation_id not in self.allocations:
            logger.warning(f"未找到分配记录: {allocation_id}")
            return

        allocation = self.allocations[allocation_id]
        resource_id = allocation.resource_id

        # 计算使用时长
        allocation.duration = (datetime.now() - allocation.allocated_at).total_seconds()
        allocation.status = "released"

        # 更新资源状态
        if resource_id in self.resource_health:
            health = self.resource_health[resource_id]
            health.status = ResourceStatus.AVAILABLE
            health.current_load = max(0.0, health.current_load - 0.1)

        self.stats["total_deallocations"] += 1
        logger.info(f"释放资源: {resource_id} (使用{allocation.duration:.2f}秒)")

    async def check_resource_health(self, resource_id: str) -> ResourceHealth:
        """
        检查资源健康状态

        Args:
            resource_id: 资源ID

        Returns:
            资源健康状态
        """
        if resource_id not in self.resource_health:
            raise ValueError(f"资源不存在: {resource_id}")

        health = self.resource_health[resource_id]
        resource_type = health.resource_type

        try:
            # 根据资源类型执行不同的健康检查
            if resource_type == ResourceType.DATABASE:
                health = await self._check_database_health(resource_id, health)
            elif resource_type == ResourceType.CACHE:
                health = await self._check_cache_health(resource_id, health)
            elif resource_type == ResourceType.EXTERNAL_API:
                health = await self._check_external_api_health(resource_id, health)
            elif resource_type == ResourceType.MODEL:
                health = await self._check_model_health(resource_id, health)
            elif resource_type in [ResourceType.MEMORY, ResourceType.CPU]:
                health = await self._check_system_resource_health(resource_id, health)
            elif resource_type == ResourceType.NETWORK:
                health = await self._check_network_health(resource_id, health)

            health.last_check_time = datetime.now()
            self.stats["total_health_checks"] += 1

        except Exception as e:
            logger.error(f"健康检查失败: {resource_id} - {e}")
            health.consecutive_failures += 1
            health.consecutive_successes = 0
            health.error_rate = min(1.0, health.error_rate + 0.1)

            # 检查是否需要触发恢复
            await self._check_and_trigger_recovery(resource_id, health)

        return health

    async def _check_database_health(
        self, resource_id: str, health: ResourceHealth
    ) -> ResourceHealth:
        """检查数据库健康状态"""
        # 这里应该实际检查数据库连接
        # 模拟实现
        health.health_score = 0.9
        health.current_load = 0.5
        health.avg_response_time = 50.0
        return health

    async def _check_cache_health(self, resource_id: str, health: ResourceHealth) -> ResourceHealth:
        """检查缓存健康状态"""
        # 模拟实现
        health.health_score = 0.95
        health.current_load = 0.4
        health.avg_response_time = 10.0
        return health

    async def _check_external_api_health(
        self, resource_id: str, health: ResourceHealth
    ) -> ResourceHealth:
        """检查外部API健康状态"""
        # 模拟实现
        health.health_score = 0.85
        health.current_load = 0.6
        health.avg_response_time = 200.0
        return health

    async def _check_model_health(self, resource_id: str, health: ResourceHealth) -> ResourceHealth:
        """检查模型健康状态"""
        # 模拟实现
        health.health_score = 0.88
        health.current_load = 0.55
        health.avg_response_time = 150.0
        return health

    async def _check_system_resource_health(
        self, resource_id: str, health: ResourceHealth
    ) -> ResourceHealth:
        """检查系统资源健康状态"""
        try:
            resource_type = health.resource_type

            if resource_type == ResourceType.MEMORY:
                # 检查内存使用率
                memory = psutil.virtual_memory()
                health.current_load = memory.percent / 100.0
                health.health_score = 1.0 - health.current_load

            elif resource_type == ResourceType.CPU:
                # 检查CPU使用率
                cpu_percent = psutil.cpu_percent(interval=1)
                health.current_load = cpu_percent / 100.0
                health.health_score = 1.0 - health.current_load * 0.5

        except Exception as e:
            logger.error(f"系统资源检查失败: {e}")
            health.health_score = 0.5

        return health

    async def _check_network_health(
        self, resource_id: str, health: ResourceHealth
    ) -> ResourceHealth:
        """检查网络健康状态"""
        # 模拟实现
        health.health_score = 0.9
        health.current_load = 0.3
        return health

    async def _check_and_trigger_recovery(self, resource_id: str, health: ResourceHealth):
        """检查并触发恢复动作"""
        threshold = self.thresholds.get(health.resource_type)

        if not threshold:
            return

        # 检查是否需要恢复
        if (
            health.consecutive_failures >= 3
            or health.health_score < (1.0 - threshold.critical_threshold)
            or health.error_rate > 0.5
        ):

            # 确定恢复策略
            strategy = self._determine_recovery_strategy(health)

            # 执行恢复
            await self._execute_recovery(resource_id, strategy)

    def _determine_recovery_strategy(self, health: ResourceHealth) -> RecoveryStrategy:
        """确定恢复策略"""
        if health.consecutive_failures < 3:
            return RecoveryStrategy.RETRY
        elif health.consecutive_failures < 5:
            return RecoveryStrategy.FAILOVER
        else:
            return RecoveryStrategy.RESTART

    async def _execute_recovery(self, resource_id: str, strategy: RecoveryStrategy):
        """执行恢复动作"""
        action_id = f"recovery_{int(time.time() * 1000)}"
        action = RecoveryAction(
            action_id=action_id,
            resource_id=resource_id,
            strategy=strategy,
            triggered_at=datetime.now(),
        )

        try:
            # 更新资源状态
            if resource_id in self.resource_health:
                self.resource_health[resource_id].status = ResourceStatus.RECOVERING

            # 执行恢复回调
            if strategy in self.recovery_callbacks:
                start_time = time.time()
                success = await self.recovery_callbacks[strategy](resource_id)
                action.duration = time.time() - start_time
                action.successful = success
                action.executed = True

            # 更新统计
            self.stats["total_recoveries"] += 1
            self.stats["recovery_by_strategy"][strategy] += 1

            if action.successful:
                self.stats["successful_recoveries"] += 1
                # 重置失败计数
                if resource_id in self.resource_health:
                    health = self.resource_health[resource_id]
                    health.consecutive_failures = 0
                    health.status = ResourceStatus.AVAILABLE
                logger.info(f"恢复成功: {resource_id} - {strategy.value}")
            else:
                self.stats["failed_recoveries"] += 1
                logger.warning(f"恢复失败: {resource_id} - {strategy.value}")

        except Exception as e:
            action.message = str(e)
            logger.error(f"恢复执行异常: {resource_id} - {e}")

        self.recovery_history.append(action)

    async def _retry_resource(self, resource_id: str) -> bool:
        """重试资源"""
        # 模拟重试
        await asyncio.sleep(0.5)
        return True

    async def _failover_resource(self, resource_id: str) -> bool:
        """故障转移"""
        # 模拟故障转移
        await asyncio.sleep(1.0)
        return True

    async def _degrade_resource(self, resource_id: str) -> bool:
        """降级资源"""
        if resource_id in self.resource_health:
            self.resource_health[resource_id].status = ResourceStatus.DEGRADED
        return True

    async def _restart_resource(self, resource_id: str) -> bool:
        """重启资源"""
        # 模拟重启
        await asyncio.sleep(2.0)
        return True

    def start_monitoring(self) -> Any:
        """启动资源监控"""
        if self._monitor_running:
            logger.warning("监控已在运行")
            return

        self._monitor_running = True
        self._monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self._monitor_thread.start()
        logger.info("资源监控已启动")

    def _monitor_loop(self) -> Any:
        """监控循环"""
        while self._monitor_running:
            try:
                # 检查所有资源
                for resource_id in list(self.resource_health.keys()):
                    # 在后台线程中运行异步检查
                    asyncio.run(self.check_resource_health(resource_id))

            except Exception as e:
                logger.error(f"监控循环异常: {e}")

            time.sleep(self.check_interval)

    def stop_monitoring(self) -> Any:
        """停止资源监控"""
        self._monitor_running = False
        if self._monitor_thread:
            self._monitor_thread.join(timeout=5.0)
        logger.info("资源监控已停止")

    def get_resource_health(self, resource_id: str) -> ResourceHealth | None:
        """获取资源健康状态"""
        return self.resource_health.get(resource_id)

    def get_all_health_status(self) -> dict[str, ResourceHealth]:
        """获取所有资源健康状态"""
        return self.resource_health.copy()

    def get_stats(self) -> dict[str, Any]:
        """获取统计信息"""
        stats = self.stats.copy()

        # 计算恢复成功率
        if stats["total_recoveries"] > 0:
            stats["recovery_success_rate"] = (
                stats["successful_recoveries"] / stats["total_recoveries"]
            )
        else:
            stats["recovery_success_rate"] = 0.0

        return stats

    def get_recovery_history(
        self, resource_id: Optional[str] = None, limit: int = 50
    ) -> list[RecoveryAction]:
        """
        获取恢复历史

        Args:
            resource_id: 资源ID(可选)
            limit: 返回数量限制

        Returns:
            恢复动作列表
        """
        history = self.recovery_history

        if resource_id:
            history = [a for a in history if a.resource_id == resource_id]

        return history[-limit:]


# 单例实例
_manager_instance: DynamicResourceManager | None = None


def get_dynamic_resource_manager() -> DynamicResourceManager:
    """获取动态资源管理器单例"""
    global _manager_instance
    if _manager_instance is None:
        _manager_instance = DynamicResourceManager()
        _manager_instance.start_monitoring()
        logger.info("动态资源管理器已初始化")
    return _manager_instance


async def main():
    """测试主函数"""
    manager = get_dynamic_resource_manager()

    # 注册一些测试资源
    manager.register_resource("db_primary", ResourceType.DATABASE, {})
    manager.register_resource("redis_cache", ResourceType.CACHE, {})
    manager.register_resource("memory_resource", ResourceType.MEMORY, {})

    print("=== 动态资源管理测试 ===\n")

    # 检查资源健康
    for resource_id in manager.resources:
        health = await manager.check_resource_health(resource_id)
        print(f"{resource_id}:")
        print(f"  状态: {health.status.value}")
        print(f"  健康分数: {health.health_score:.2f}")
        print(f"  当前负载: {health.current_load:.1%}")

    # 分配资源
    print("\n=== 资源分配测试 ===")
    allocated = await manager.allocate_resource(ResourceType.DATABASE, "test_requester")
    if allocated:
        print(f"成功分配资源: {allocated}")
        await manager.deallocate_resource(f"alloc_{int(time.time() * 1000)}")

    # 显示统计
    stats = manager.get_stats()
    print("\n=== 统计信息 ===")
    print(f"健康检查次数: {stats['total_health_checks']}")
    print(f"恢复次数: {stats['total_recoveries']}")

    # 停止监控
    manager.stop_monitoring()


# 入口点: @async_main装饰器已添加到main函数
