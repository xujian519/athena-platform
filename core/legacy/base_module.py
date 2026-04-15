#!/usr/bin/env python3
from __future__ import annotations
"""
基础模块接口标准
Base Module Interface Standard

定义所有核心模块的统一接口,实现标准化和一致性

作者: Athena AI系统
创建时间: 2025-12-11
版本: 1.0.0
"""

import asyncio
import logging
import time
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class ModuleStatus(Enum):
    """模块状态枚举"""

    UNINITIALIZED = "uninitialized"
    INITIALIZING = "initializing"
    READY = "ready"
    RUNNING = "running"
    PAUSED = "paused"
    ERROR = "error"
    STOPPING = "stopping"
    STOPPED = "stopped"


class HealthStatus(Enum):
    """健康状态枚举"""

    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


@dataclass
class ModuleMetrics:
    """模块指标"""

    operation_count: int = 0
    success_count: int = 0
    error_count: int = 0
    average_response_time: float = 0.0
    last_operation_time: datetime | None = None
    uptime: float = 0.0
    memory_usage: float = 0.0
    cpu_usage: float = 0.0


@dataclass
class ModuleConfig:
    """模块配置"""

    module_id: str
    module_name: str
    version: str = "1.0.0"
    auto_start: bool = True
    max_retries: int = 3
    retry_delay: float = 1.0
    health_check_interval: float = 30.0
    metrics_enabled: bool = True
    logging_level: str = "INFO"
    custom_config: dict[str, Any] = field(default_factory=dict)


class BaseModule(ABC):
    """
    基础模块类

    所有核心模块的基类,定义统一的接口和标准行为
    """

    def __init__(self, agent_id: str, config: dict | None = None):
        """
        初始化基础模块

        Args:
            agent_id: 智能体ID
            config: 模块配置
        """
        self.agent_id = agent_id
        self.config = config or {}

        # 基本属性
        self.module_id = str(uuid.uuid4())
        self.status = ModuleStatus.UNINITIALIZED
        self.health_status = HealthStatus.UNKNOWN
        self.start_time: datetime | None = None
        self.last_health_check: datetime | None = None

        # 指标统计
        self.metrics = ModuleMetrics()
        self._operation_times: list[float] = []

        # 错误处理
        self.last_error: Exception | None = None
        self.error_history: list[dict[str, Any]] = []

        # 事件处理
        self._event_handlers: dict[str, list[callable]] = {}

        # 日志器
        self.logger = logging.getLogger(f"{self.__class__.__name__}_{self.agent_id}")

        # 初始化配置
        self._module_config = self._parse_config()

    def _parse_config(self) -> ModuleConfig:
        """解析模块配置"""
        return ModuleConfig(
            module_id=self.module_id,
            module_name=self.__class__.__name__,
            version=self.config.get("version", "1.0.0"),
            auto_start=self.config.get("auto_start", True),
            max_retries=self.config.get("max_retries", 3),
            retry_delay=self.config.get("retry_delay", 1.0),
            health_check_interval=self.config.get("health_check_interval", 30.0),
            metrics_enabled=self.config.get("metrics_enabled", True),
            logging_level=self.config.get("logging_level", "INFO"),
            custom_config=self.config.get("custom_config", {}),
        )

    async def initialize(self) -> bool:
        """
        初始化模块

        Returns:
            bool: 初始化是否成功
        """
        try:
            self.status = ModuleStatus.INITIALIZING
            self.logger.info(f"🔧 初始化模块: {self.__class__.__name__}")

            # 设置日志级别
            log_level = getattr(logging, self._module_config.logging_level.upper(), logging.INFO)
            self.logger.set_level(log_level)

            # 执行子类初始化
            init_result = await self._on_initialize()

            if init_result:
                self.status = ModuleStatus.READY
                self.health_status = HealthStatus.HEALTHY
                self.start_time = datetime.now()
                self.logger.info(f"✅ 模块初始化成功: {self.__class__.__name__}")

                # 触发初始化完成事件
                await self._emit_event("initialized", {"module": self.__class__.__name__})

                return True
            else:
                self.status = ModuleStatus.ERROR
                self.logger.error(f"❌ 模块初始化失败: {self.__class__.__name__}")
                return False

        except Exception as e:
            self._handle_error(e, "initialize")
            self.status = ModuleStatus.ERROR
            self.health_status = HealthStatus.UNHEALTHY
            return False

    async def start(self) -> bool:
        """
        启动模块

        Returns:
            bool: 启动是否成功
        """
        try:
            if self.status not in [ModuleStatus.READY, ModuleStatus.STOPPED]:
                if self.status == ModuleStatus.RUNNING:
                    self.logger.warning(f"⚠️ 模块已在运行: {self.__class__.__name__}")
                    return True
                else:
                    self.logger.error(f"❌ 模块状态不允许启动: {self.status}")
                    return False

            self.status = ModuleStatus.RUNNING
            self.logger.info(f"🚀 启动模块: {self.__class__.__name__}")

            # 执行子类启动逻辑
            start_result = await self._on_start()

            if start_result:
                self.logger.info(f"✅ 模块启动成功: {self.__class__.__name__}")
                await self._emit_event("started", {"module": self.__class__.__name__})
                return True
            else:
                self.status = ModuleStatus.ERROR
                self.logger.error(f"❌ 模块启动失败: {self.__class__.__name__}")
                return False

        except Exception as e:
            self._handle_error(e, "start")
            self.status = ModuleStatus.ERROR
            return False

    async def stop(self) -> bool:
        """
        停止模块

        Returns:
            bool: 停止是否成功
        """
        try:
            if self.status != ModuleStatus.RUNNING:
                self.logger.warning(f"⚠️ 模块未在运行: {self.__class__.__name__}")
                return True

            self.status = ModuleStatus.STOPPING
            self.logger.info(f"🛑 停止模块: {self.__class__.__name__}")

            # 执行子类停止逻辑
            stop_result = await self._on_stop()

            if stop_result:
                self.status = ModuleStatus.STOPPED
                self.logger.info(f"✅ 模块停止成功: {self.__class__.__name__}")
                await self._emit_event("stopped", {"module": self.__class__.__name__})
                return True
            else:
                self.status = ModuleStatus.ERROR
                self.logger.error(f"❌ 模块停止失败: {self.__class__.__name__}")
                return False

        except Exception as e:
            self._handle_error(e, "stop")
            self.status = ModuleStatus.ERROR
            return False

    async def shutdown(self) -> bool:
        """
        关闭模块

        Returns:
            bool: 关闭是否成功
        """
        try:
            self.logger.info(f"🔌 关闭模块: {self.__class__.__name__}")

            # 如果正在运行,先停止
            if self.status == ModuleStatus.RUNNING:
                await self.stop()

            # 执行子类关闭逻辑
            shutdown_result = await self._on_shutdown()

            if shutdown_result:
                self.status = ModuleStatus.STOPPED
                self.health_status = HealthStatus.UNKNOWN
                self.logger.info(f"✅ 模块关闭成功: {self.__class__.__name__}")
                await self._emit_event("shutdown", {"module": self.__class__.__name__})
                return True
            else:
                self.logger.error(f"❌ 模块关闭失败: {self.__class__.__name__}")
                return False

        except Exception as e:
            self._handle_error(e, "shutdown")
            return False

    def get_status(self) -> dict[str, Any]:
        """
        获取模块状态

        Returns:
            dict[str, Any]: 状态信息
        """
        uptime = 0.0
        if self.start_time:
            uptime = (datetime.now() - self.start_time).total_seconds()

        return {
            "module_id": self.module_id,
            "module_name": self.__class__.__name__,
            "agent_id": self.agent_id,
            "status": self.status.value,
            "health_status": self.health_status.value,
            "uptime": uptime,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "last_health_check": (
                self.last_health_check.isoformat() if self.last_health_check else None
            ),
            "last_error": str(self.last_error) if self.last_error else None,
            "metrics": {
                "operation_count": self.metrics.operation_count,
                "success_count": self.metrics.success_count,
                "error_count": self.metrics.error_count,
                "success_rate": self.metrics.success_count / max(self.metrics.operation_count, 1),
                "average_response_time": self.metrics.average_response_time,
                "memory_usage": self.metrics.memory_usage,
                "cpu_usage": self.metrics.cpu_usage,
            },
            "config": {
                "version": self._module_config.version,
                "auto_start": self._module_config.auto_start,
                "max_retries": self._module_config.max_retries,
                "health_check_interval": self._module_config.health_check_interval,
            },
        }

    async def health_check(self) -> HealthStatus:
        """
        健康检查

        Returns:
            HealthStatus: 健康状态
        """
        try:
            self.last_health_check = datetime.now()

            # 执行子类健康检查
            health_result = await self._on_health_check()

            # 更新健康状态
            if health_result and self.status == ModuleStatus.RUNNING:
                self.health_status = HealthStatus.HEALTHY
            elif health_result:
                self.health_status = HealthStatus.DEGRADED
            else:
                self.health_status = HealthStatus.UNHEALTHY

            return self.health_status

        except Exception as e:
            self._handle_error(e, "health_check")
            self.health_status = HealthStatus.UNHEALTHY
            return self.health_status

    async def execute_with_metrics(
        self, operation_name: str, operation_func: callable, *args, **kwargs
    ):
        """
        带指标统计的执行操作

        Args:
            operation_name: 操作名称
            operation_func: 操作函数
            *args: 位置参数
            **kwargs: 关键字参数

        Returns:
            操作结果
        """
        start_time = time.time()

        try:
            # 更新操作计数
            self.metrics.operation_count += 1

            # 执行操作
            result = await operation_func(*args, **kwargs)

            # 更新成功计数
            self.metrics.success_count += 1

            # 计算响应时间
            operation_time = time.time() - start_time
            self._update_response_time(operation_time)

            # 记录操作时间
            self._operation_times.append(operation_time)
            if len(self._operation_times) > 1000:  # 限制历史记录数量
                self._operation_times = self._operation_times[-1000:]

            self.metrics.last_operation_time = datetime.now()

            # 触发操作完成事件
            await self._emit_event(
                "operation_completed",
                {"operation": operation_name, "duration": operation_time, "success": True},
            )

            return result

        except Exception as e:
            # 更新错误计数
            self.metrics.error_count += 1
            self._handle_error(e, operation_name)

            # 计算响应时间
            operation_time = time.time() - start_time
            self._update_response_time(operation_time)

            # 触发操作失败事件
            await self._emit_event(
                "operation_failed",
                {"operation": operation_name, "duration": operation_time, "error": str(e)},
            )

            raise

    def _update_response_time(self, operation_time: float) -> Any:
        """更新平均响应时间"""
        if self.metrics.operation_count == 1:
            self.metrics.average_response_time = operation_time
        else:
            # 使用指数移动平均
            alpha = 0.1
            self.metrics.average_response_time = (
                alpha * operation_time + (1 - alpha) * self.metrics.average_response_time
            )

    def _handle_error(self, error: Exception, context: str) -> Any:
        """处理错误"""
        self.last_error = error

        # 记录错误历史
        error_info = {
            "timestamp": datetime.now().isoformat(),
            "context": context,
            "error_type": type(error).__name__,
            "error_message": str(error),
            "module_status": self.status.value,
        }

        self.error_history.append(error_info)

        # 限制错误历史数量
        if len(self.error_history) > 100:
            self.error_history = self.error_history[-100:]

        self.logger.error(f"❌ 模块错误 [{context}]: {error}")

    async def _emit_event(self, event_name: str, event_data: dict[str, Any]):
        """触发事件"""
        if event_name in self._event_handlers:
            for handler in self._event_handlers[event_name]:
                try:
                    await handler(event_data)
                except Exception as e:
                    self.logger.error(f"❌ 事件处理器错误: {e}")

    def add_event_handler(self, event_name: str, handler: callable) -> None:
        """添加事件处理器"""
        if event_name not in self._event_handlers:
            self._event_handlers[event_name] = []
        self._event_handlers[event_name].append(handler)

    def remove_event_handler(self, event_name: str, handler: callable) -> None:
        """移除事件处理器"""
        if event_name in self._event_handlers:
            try:
                self._event_handlers[event_name].remove(handler)
            except ValueError as e:  # 记录异常但不中断流程
                logger.debug(f"[base_module] ValueError: {e}")

    # 抽象方法 - 子类必须实现
    @abstractmethod
    async def _on_initialize(self) -> bool:
        """子类初始化逻辑"""
        pass

    @abstractmethod
    async def _on_start(self) -> bool:
        """子类启动逻辑"""
        pass

    @abstractmethod
    async def _on_stop(self) -> bool:
        """子类停止逻辑"""
        pass

    @abstractmethod
    async def _on_shutdown(self) -> bool:
        """子类关闭逻辑"""
        pass

    @abstractmethod
    async def _on_health_check(self) -> bool:
        """子类健康检查逻辑"""
        pass


# 工具函数
async def initialize_module(module: BaseModule) -> bool:
    """初始化模块的便捷函数"""
    return await module.initialize()


async def start_module(module: BaseModule) -> bool:
    """启动模块的便捷函数"""
    return await module.start()


async def stop_module(module: BaseModule) -> bool:
    """停止模块的便捷函数"""
    return await module.stop()


async def shutdown_module(module: BaseModule) -> bool:
    """关闭模块的便捷函数"""
    return await module.shutdown()


def get_module_info(module: BaseModule) -> dict[str, Any]:
    """获取模块信息的便捷函数"""
    return module.get_status()


# 模块装饰器
def module_retry(max_retries: int = 3, delay: float = 1.0) -> Any:
    """模块操作重试装饰器"""

    def decorator(func) -> None:
        async def wrapper(*args, **kwargs):
            last_exception = None

            for attempt in range(max_retries + 1):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt < max_retries:
                        await asyncio.sleep(delay * (2**attempt))  # 指数退避
                    else:
                        raise last_exception from e

            return None

        return wrapper

    return decorator
