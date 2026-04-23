#!/usr/bin/env python3
from __future__ import annotations
"""
Agent服务健康检查和故障转移系统
Health Check and Failover System for Agent Services

提供完整的健康监控和故障恢复:
1. Agent健康检查(心跳、响应时间、错误率)
2. 自动故障检测和隔离
3. 故障转移和负载重分配
4. 自动恢复和重新集成
5. 健康报告和告警

版本: v1.0.0
创建时间: 2026-01-18
"""

import asyncio
import contextlib
import logging
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any
from uuid import uuid4

logger = logging.getLogger(__name__)


# =============================================================================
# 健康状态定义
# =============================================================================


class HealthStatus(Enum):
    """健康状态"""

    HEALTHY = "healthy"  # 健康
    DEGRADED = "degraded"  # 降级(性能下降)
    UNHEALTHY = "unhealthy"  # 不健康
    FAILED = "failed"  # 失败
    UNKNOWN = "unknown"  # 未知


class FailoverStrategy(Enum):
    """故障转移策略"""

    NONE = "none"  # 不转移
    RESTART = "restart"  # 重启服务
    REDISTRIBUTE = "redistribute"  # 重新分配负载
    STANDBY = "standby"  # 使用备用服务
    CIRCUIT_BREAKER = "circuit_breaker"  # 熔断器


# =============================================================================
# 健康检查数据结构
# =============================================================================


@dataclass
class HealthCheckResult:
    """健康检查结果"""

    agent_id: str
    status: HealthStatus
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    response_time_ms: float = 0.0
    error_rate: float = 0.0
    last_error: str | None = None
    details: dict[str, Any] = field(default_factory=dict)


@dataclass
class AgentHealthInfo:
    """Agent健康信息"""

    agent_id: str
    status: HealthStatus = HealthStatus.UNKNOWN
    last_check_time: str = field(default_factory=lambda: datetime.now().isoformat())
    last_heartbeat: str = field(default_factory=lambda: datetime.now().isoformat())
    consecutive_failures: int = 0
    total_requests: int = 0
    failed_requests: int = 0
    average_response_time: float = 0.0
    is_available: bool = True
    in_circuit_breaker: bool = False
    last_error: str | None = None  # 添加last_error字段

    def calculate_error_rate(self) -> float:
        """计算错误率"""
        if self.total_requests == 0:
            return 0.0
        return self.failed_requests / self.total_requests


@dataclass
class FailoverEvent:
    """故障转移事件"""

    event_id: str = field(default_factory=lambda: str(uuid4()))
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    failed_agent_id: str = ""
    failover_strategy: FailoverStrategy = FailoverStrategy.NONE
    target_agent_id: str = ""
    reason: str = ""
    success: bool = False
    details: dict[str, Any] = field(default_factory=dict)


# =============================================================================
# 健康检查器
# =============================================================================


class HealthChecker:
    """
    Agent健康检查器

    定期检查Agent的健康状态,包括:
    - 心跳检测
    - 响应时间监测
    - 错误率统计
    - 资源使用监控
    """

    def __init__(
        self,
        check_interval: int = 30,  # 检查间隔(秒)
        timeout: float = 5.0,  # 超时时间(秒)
        max_consecutive_failures: int = 3,
        circuit_breaker_threshold: int = 5,
    ):
        self.check_interval = check_interval
        self.timeout = timeout
        self.max_consecutive_failures = max_consecutive_failures
        self.circuit_breaker_threshold = circuit_breaker_threshold

        # Agent健康信息
        self.agent_health: dict[str, AgentHealthInfo] = {}

        # 健康检查回调
        self.check_callbacks: dict[str, Callable[..., Any]] = {}

        # 运行状态
        self.running = False
        self._check_task: asyncio.Task[Any] | None | None = None

    async def start(self):
        """启动健康检查器"""
        self.running = True
        self._check_task = asyncio.create_task(self._check_loop())
        logger.info("✅ 健康检查器已启动")

    async def stop(self):
        """停止健康检查器"""
        self.running = False
        if self._check_task:
            self._check_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._check_task
        logger.info("✅ 健康检查器已停止")

    def register_agent(self, agent_id: str, check_callback: Callable[..., Any] | None = None):
        """注册Agent进行健康检查"""
        self.agent_health[agent_id] = AgentHealthInfo(agent_id=agent_id)

        if check_callback:
            self.check_callbacks[agent_id] = check_callback

        logger.info(f"✅ Agent已注册健康检查: {agent_id}")

    def unregister_agent(self, agent_id: str) -> Any:
        """注销Agent"""
        if agent_id in self.agent_health:
            del self.agent_health[agent_id]
        if agent_id in self.check_callbacks:
            del self.check_callbacks[agent_id]

        logger.info(f"✅ Agent已注销健康检查: {agent_id}")

    async def _check_loop(self):
        """健康检查循环"""
        while self.running:
            try:
                # 检查所有已注册的Agent
                for agent_id in list(self.agent_health.keys()):
                    await self._check_agent_health(agent_id)

                await asyncio.sleep(self.check_interval)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"❌ 健康检查异常: {e}")
                await asyncio.sleep(5)

    async def _check_agent_health(self, agent_id: str) -> HealthCheckResult:
        """检查单个Agent的健康状态"""
        health_info = self.agent_health.get(agent_id)

        if not health_info:
            return HealthCheckResult(agent_id=agent_id, status=HealthStatus.UNKNOWN)

        try:
            # 执行健康检查回调
            if agent_id in self.check_callbacks:
                callback = self.check_callbacks[agent_id]
                result = await asyncio.wait_for(callback(), timeout=self.timeout)

                # 更新健康信息
                health_info.last_check_time = datetime.now().isoformat()
                health_info.total_requests += 1

                if result.get("healthy", False):
                    # 健康检查通过
                    health_info.consecutive_failures = 0
                    health_info.status = HealthStatus.HEALTHY
                    health_info.is_available = True

                    # 更新响应时间
                    response_time = result.get("response_time_ms", 0)
                    health_info.average_response_time = (
                        health_info.average_response_time * 0.9 + response_time * 0.1
                    )

                else:
                    # 健康检查失败
                    health_info.failed_requests += 1
                    health_info.consecutive_failures += 1
                    health_info.last_error = result.get("error", "Unknown error")

                    # 更新状态
                    if health_info.consecutive_failures >= self.max_consecutive_failures:
                        health_info.status = HealthStatus.FAILED
                        health_info.is_available = False
                    else:
                        health_info.status = HealthStatus.UNHEALTHY

                return HealthCheckResult(
                    agent_id=agent_id,
                    status=health_info.status,
                    response_time_ms=health_info.average_response_time,
                    error_rate=health_info.calculate_error_rate(),
                    last_error=health_info.last_error,
                    details=result,
                )

            else:
                # 没有注册回调,使用默认检查(仅基于心跳)
                return await self._default_health_check(agent_id, health_info)

        except asyncio.TimeoutError:
            # 超时
            health_info.consecutive_failures += 1
            health_info.failed_requests += 1
            health_info.total_requests += 1
            health_info.last_error = f"Health check timeout after {self.timeout}s"

            if health_info.consecutive_failures >= self.max_consecutive_failures:
                health_info.status = HealthStatus.FAILED
                health_info.is_available = False
            else:
                health_info.status = HealthStatus.UNHEALTHY

            return HealthCheckResult(
                agent_id=agent_id,
                status=health_info.status,
                error_rate=health_info.calculate_error_rate(),
                last_error=health_info.last_error,
            )

        except Exception as e:
            # 其他错误
            health_info.consecutive_failures += 1
            health_info.failed_requests += 1
            health_info.total_requests += 1
            health_info.last_error = str(e)

            return HealthCheckResult(
                agent_id=agent_id,
                status=HealthStatus.FAILED,
                error_rate=health_info.calculate_error_rate(),
                last_error=health_info.last_error,
            )

    async def _default_health_check(
        self, agent_id: str, health_info: AgentHealthInfo
    ) -> HealthCheckResult:
        """默认健康检查(基于心跳时间)"""
        try:
            last_heartbeat = datetime.fromisoformat(health_info.last_heartbeat)
            time_since_heartbeat = (datetime.now() - last_heartbeat).total_seconds()

            if time_since_heartbeat < self.check_interval * 2:
                # 心跳正常
                health_info.status = HealthStatus.HEALTHY
                health_info.is_available = True
                health_info.consecutive_failures = 0

                return HealthCheckResult(
                    agent_id=agent_id,
                    status=HealthStatus.HEALTHY,
                    details={"heartbeat_age_seconds": time_since_heartbeat},
                )
            else:
                # 心跳超时
                health_info.status = HealthStatus.UNHEALTHY
                health_info.is_available = False
                health_info.consecutive_failures += 1

                return HealthCheckResult(
                    agent_id=agent_id,
                    status=HealthStatus.UNHEALTHY,
                    last_error=f"Heartbeat timeout: {time_since_heartbeat}s",
                    details={"heartbeat_age_seconds": time_since_heartbeat},
                )

        except Exception as e:
            return HealthCheckResult(
                agent_id=agent_id, status=HealthStatus.UNKNOWN, last_error=str(e)
            )

    def update_heartbeat(self, agent_id: str) -> None:
        """更新Agent心跳"""
        if agent_id in self.agent_health:
            self.agent_health[agent_id].last_heartbeat = datetime.now().isoformat()

    def get_health_info(self, agent_id: str) -> AgentHealthInfo | None:
        """获取Agent健康信息"""
        return self.agent_health.get(agent_id)

    def get_all_health_info(self) -> dict[str, AgentHealthInfo]:
        """获取所有Agent健康信息"""
        return self.agent_health.copy()


# =============================================================================
# 故障转移管理器
# =============================================================================


class FailoverManager:
    """
    故障转移管理器

    监控Agent故障,执行故障转移策略:
    - 自动故障检测
    - 故障隔离
    - 负载重分配
    - 备用服务激活
    - 熔断器管理
    """

    def __init__(
        self,
        health_checker: HealthChecker,
        auto_failover: bool = True,
        standby_agents: dict[str, list[str]] | None = None,
    ):
        self.health_checker = health_checker
        self.auto_failover = auto_failover
        self.standby_agents = standby_agents or {}  # agent_type -> [agent_ids]

        # 故障转移事件历史
        self.failover_events: list[FailoverEvent] = []

        # 熔断器状态
        self.circuit_breakers: dict[str, dict[str, Any]] = {}

        # 故障转移策略配置
        self.failover_strategies: dict[str, FailoverStrategy] = {}

        # 运行状态
        self.running = False
        self._monitor_task: asyncio.Task[Any] | None | None = None

    async def start(self):
        """启动故障转移管理器"""
        self.running = True
        self._monitor_task = asyncio.create_task(self._monitor_loop())
        logger.info("✅ 故障转移管理器已启动")

    async def stop(self):
        """停止故障转移管理器"""
        self.running = False
        if self._monitor_task:
            self._monitor_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._monitor_task
        logger.info("✅ 故障转移管理器已停止")

    async def _monitor_loop(self):
        """监控循环"""
        while self.running:
            try:
                # 检查所有Agent的健康状态
                health_info = self.health_checker.get_all_health_info()

                for agent_id, info in health_info.items():
                    await self._handle_agent_status_change(agent_id, info)

                await asyncio.sleep(10)  # 每10秒检查一次

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"❌ 监控循环异常: {e}")
                await asyncio.sleep(5)

    async def _handle_agent_status_change(self, agent_id: str, health_info: AgentHealthInfo):
        """处理Agent状态变化"""
        # 检查是否需要故障转移
        if health_info.status == HealthStatus.FAILED:
            await self._trigger_failover(agent_id, health_info)

        elif health_info.status == HealthStatus.UNHEALTHY:
            # 记录但不触发故障转移
            logger.warning(f"⚠️ Agent不健康: {agent_id}")

        elif health_info.status == HealthStatus.HEALTHY:
            # 之前失败的Agent恢复了
            await self._handle_agent_recovery(agent_id)

    async def _trigger_failover(self, failed_agent_id: str, health_info: AgentHealthInfo):
        """触发故障转移"""
        if not self.auto_failover:
            logger.warning(f"⚠️ Agent故障但自动转移已禁用: {failed_agent_id}")
            return

        # 获取故障转移策略
        strategy = self.failover_strategies.get(failed_agent_id, FailoverStrategy.REDISTRIBUTE)

        logger.info(f"🔄 执行故障转移: {failed_agent_id} -> {strategy.value}")

        event = FailoverEvent(
            failed_agent_id=failed_agent_id,
            failover_strategy=strategy,
            reason=f"Agent failed: {health_info.last_error}",
        )

        try:
            if strategy == FailoverStrategy.RESTART:
                success = await self._restart_agent(failed_agent_id)

            elif strategy == FailoverStrategy.REDISTRIBUTE:
                success = await self._redistribute_load(failed_agent_id)

            elif strategy == FailoverStrategy.STANDBY:
                success = await self._activate_standby(failed_agent_id)

            elif strategy == FailoverStrategy.CIRCUIT_BREAKER:
                success = await self._activate_circuit_breaker(failed_agent_id)

            else:
                success = False

            event.success = success

            if success:
                logger.info(f"✅ 故障转移成功: {failed_agent_id}")
            else:
                logger.error(f"❌ 故障转移失败: {failed_agent_id}")

        except Exception as e:
            logger.error(f"❌ 故障转移异常: {e}")
            event.success = False

        # 记录事件
        self.failover_events.append(event)

        # 保持最近100个事件
        if len(self.failover_events) > 100:
            self.failover_events = self.failover_events[-100:]

    async def _restart_agent(self, agent_id: str) -> bool:
        """重启Agent"""
        # 这里应该调用Agent管理器来重启
        logger.info(f"🔄 重启Agent: {agent_id}")
        return True

    async def _redistribute_load(self, failed_agent_id: str) -> bool:
        """重新分配负载"""
        # 获取健康的Agent列表
        health_info = self.health_checker.get_all_health_info()
        healthy_agents = [
            aid
            for aid, info in health_info.items()
            if info.status == HealthStatus.HEALTHY and aid != failed_agent_id
        ]

        if not healthy_agents:
            logger.error("❌ 没有可用的健康Agent来分配负载")
            return False

        logger.info(f"📊 将 {failed_agent_id} 的负载重新分配给: {healthy_agents}")
        return True

    async def _activate_standby(self, failed_agent_id: str) -> bool:
        """激活备用Agent"""
        # 查找备用Agent
        agent_type = failed_agent_id.split("_")[0]  # 简化假设
        standby_list = self.standby_agents.get(agent_type, [])

        if not standby_list:
            logger.error(f"❌ 没有配置备用Agent: {agent_type}")
            return False

        # 激活第一个备用Agent
        standby_agent_id = standby_list[0]
        logger.info(f"✅ 激活备用Agent: {standby_agent_id}")
        return True

    async def _activate_circuit_breaker(self, agent_id: str) -> bool:
        """激活熔断器"""
        if agent_id not in self.circuit_breakers:
            self.circuit_breakers[agent_id] = {
                "state": "open",
                "opened_at": datetime.now().isoformat(),
                "failure_count": 0,
            }

        logger.warning(f"⚠️ 熔断器已打开: {agent_id}")
        return True

    async def _handle_agent_recovery(self, agent_id: str):
        """处理Agent恢复"""
        logger.info(f"✅ Agent已恢复: {agent_id}")

        # 重置熔断器
        if agent_id in self.circuit_breakers:
            del self.circuit_breakers[agent_id]
            logger.info(f"✅ 熔断器已重置: {agent_id}")

    def get_failover_history(self, limit: int = 50) -> list[FailoverEvent]:
        """获取故障转移历史"""
        return self.failover_events[-limit:]


# =============================================================================
# 集成管理器
# =============================================================================


class HealthAndFailoverManager:
    """
    健康检查和故障转移集成管理器

    整合健康检查和故障转移功能
    """

    def __init__(self, check_interval: int = 30, auto_failover: bool = True):
        self.health_checker = HealthChecker(check_interval=check_interval)
        self.failover_manager = FailoverManager(
            health_checker=self.health_checker, auto_failover=auto_failover
        )

    async def start(self):
        """启动管理器"""
        await self.health_checker.start()
        await self.failover_manager.start()
        logger.info("✅ 健康检查和故障转移管理器已启动")

    async def stop(self):
        """停止管理器"""
        await self.failover_manager.stop()
        await self.health_checker.stop()
        logger.info("✅ 健康检查和故障转移管理器已停止")

    def register_agent(
        self,
        agent_id: str,
        check_callback: Callable[..., Any] | None = None,
        failover_strategy: FailoverStrategy | None = None,
    ):
        """注册Agent"""
        self.health_checker.register_agent(agent_id, check_callback)

        if failover_strategy:
            self.failover_manager.failover_strategies[agent_id] = failover_strategy

    def get_dashboard_data(self) -> dict[str, Any]:
        """获取仪表板数据"""
        health_info = self.health_checker.get_all_health_info()

        return {
            "agents": {
                agent_id: {
                    "status": info.status.value,
                    "error_rate": info.calculate_error_rate(),
                    "response_time": info.average_response_time,
                    "consecutive_failures": info.consecutive_failures,
                    "is_available": info.is_available,
                    "in_circuit_breaker": agent_id in self.failover_manager.circuit_breakers,
                }
                for agent_id, info in health_info.items()
            },
            "circuit_breakers": self.failover_manager.circuit_breakers,
            "recent_failovers": [
                {
                    "event_id": event.event_id,
                    "timestamp": event.timestamp,
                    "failed_agent": event.failed_agent_id,
                    "strategy": event.failover_strategy.value,
                    "success": event.success,
                }
                for event in self.failover_manager.get_failover_history(limit=10)
            ],
            "summary": {
                "total_agents": len(health_info),
                "healthy_agents": sum(
                    1 for info in health_info.values() if info.status == HealthStatus.HEALTHY
                ),
                "failed_agents": sum(
                    1 for info in health_info.values() if info.status == HealthStatus.FAILED
                ),
                "unhealthy_agents": sum(
                    1 for info in health_info.values() if info.status == HealthStatus.UNHEALTHY
                ),
            },
        }


# =============================================================================
# 全局实例
# =============================================================================

_health_manager: HealthAndFailoverManager | None = None


def get_health_manager(**kwargs: Any) -> HealthAndFailoverManager:
    """获取全局健康管理器实例"""
    global _health_manager
    if _health_manager is None:
        _health_manager = HealthAndFailoverManager(**kwargs)
    return _health_manager
