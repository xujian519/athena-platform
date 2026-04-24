"""
统一实现层 - 提供线程安全的统一注册中心实现

核心特性：
- 线程安全（RLock）
- 健康检查（heartbeat机制）
- 性能监控（metrics收集）
- 事件通知（pub/sub模式）
- 单例模式
"""

import logging
import threading
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional

from core.registry_center.base import (
    BaseRegistry,
    EventListener,
    RegistryEvent,
    RegistryEventType,
)

logger = logging.getLogger(__name__)


@dataclass
class RegistryMetrics:
    """注册表性能指标"""

    register_count: int = 0
    unregister_count: int = 0
    query_count: int = 0
    error_count: int = 0
    last_activity: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "register_count": self.register_count,
            "unregister_count": self.unregister_count,
            "query_count": self.query_count,
            "error_count": self.error_count,
            "last_activity": self.last_activity,
        }


@dataclass
class HealthCheckConfig:
    """健康检查配置"""

    heartbeat_interval: int = 30  # 心跳间隔（秒）
    heartbeat_timeout: int = 90  # 心跳超时（秒）
    enable_auto_check: bool = True  # 是否启用自动检查


class UnifiedRegistryCenter(BaseRegistry):
    """
    统一注册中心

    单例模式，线程安全，提供完整的注册表功能。

    特性：
    1. 线程安全：使用RLock保护所有操作
    2. 事件通知：支持注册/注销/更新事件
    3. 性能监控：自动收集操作指标
    4. 健康检查：支持心跳检测
    5. 统计信息：提供详细的统计数据
    """

    _instance: Optional["UnifiedRegistryCenter"] = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    # 在__new__中设置初始化标志，确保__init__只执行一次
                    cls._instance._initialized = False  # type: ignore[attr-defined]
        return cls._instance

    def __init__(self):
        # 使用getattr安全访问_initialized属性，避免类型检查器警告
        if getattr(self, "_initialized", False):
            return

        # 核心存储
        self._entities: dict[str, Any] = {}
        self._entity_types: dict[str, str] = {}  # entity_id -> type
        self._type_index: dict[str, list[str]] = defaultdict(list)  # type -> entity_ids
        self._heartbeats: dict[str, str] = {}  # entity_id -> timestamp

        # 并发控制
        self._lock = threading.RLock()

        # 事件系统
        self._event_listeners: dict[RegistryEventType, list[EventListener]] = defaultdict(list)

        # 性能监控
        self._metrics = RegistryMetrics()

        # 健康检查配置
        self._health_config = HealthCheckConfig()

        # 初始化完成
        self._initialized = True
        logger.info("✅ 统一注册中心初始化完成")

    @classmethod
    def get_instance(cls) -> "UnifiedRegistryCenter":
        """获取单例实例"""
        return cls()

    # ==================== 核心CRUD操作 ====================

    def register(self, entity_id: str, entity: Any, entity_type: str = "default") -> bool:
        """
        注册实体

        Args:
            entity_id: 实体唯一标识
            entity: 实体对象
            entity_type: 实体类型（用于分类索引）

        Returns:
            bool: 注册是否成功
        """
        try:
            with self._lock:
                # 检查是否已存在
                if entity_id in self._entities:
                    logger.warning(f"⚠️ 实体 {entity_id} 已存在，将更新")
                    self.unregister(entity_id)

                # 注册实体
                self._entities[entity_id] = entity
                self._entity_types[entity_id] = entity_type
                self._type_index[entity_type].append(entity_id)
                self._heartbeats[entity_id] = datetime.now().isoformat()

                # 更新指标
                self._metrics.register_count += 1
                self._metrics.last_activity = datetime.now().isoformat()

                # 发布事件
                self._emit_event(
                    RegistryEvent(
                        event_type=RegistryEventType.ENTITY_REGISTERED,
                        entity_id=entity_id,
                        entity_type=entity_type,
                        data={"entity_type": entity_type},
                    )
                )

                logger.info(f"✅ 注册实体: {entity_id} (类型: {entity_type})")
                return True

        except Exception as e:
            logger.error(f"❌ 注册实体失败 {entity_id}: {e}")
            self._metrics.error_count += 1
            return False

    def unregister(self, entity_id: str) -> bool:
        """
        注销实体

        Args:
            entity_id: 实体唯一标识

        Returns:
            bool: 注销是否成功
        """
        try:
            with self._lock:
                if entity_id not in self._entities:
                    logger.warning(f"⚠️ 实体 {entity_id} 不存在")
                    return False

                entity_type = self._entity_types[entity_id]

                # 从索引中移除
                self._type_index[entity_type].remove(entity_id)
                if not self._type_index[entity_type]:
                    del self._type_index[entity_type]

                # 删除实体
                del self._entities[entity_id]
                del self._entity_types[entity_id]
                del self._heartbeats[entity_id]

                # 更新指标
                self._metrics.unregister_count += 1
                self._metrics.last_activity = datetime.now().isoformat()

                # 发布事件
                self._emit_event(
                    RegistryEvent(
                        event_type=RegistryEventType.ENTITY_UNREGISTERED,
                        entity_id=entity_id,
                        entity_type=entity_type,
                    )
                )

                logger.info(f"✅ 注销实体: {entity_id}")
                return True

        except Exception as e:
            logger.error(f"❌ 注销实体失败 {entity_id}: {e}")
            self._metrics.error_count += 1
            return False

    def get(self, entity_id: str) -> Optional[Any]:
        """
        获取实体

        Args:
            entity_id: 实体唯一标识

        Returns:
            实体对象，不存在返回None
        """
        with self._lock:
            self._metrics.query_count += 1
            return self._entities.get(entity_id)

    def exists(self, entity_id: str) -> bool:
        """
        检查实体是否存在

        Args:
            entity_id: 实体唯一标识

        Returns:
            bool: 是否存在
        """
        with self._lock:
            return entity_id in self._entities

    def list_all(self) -> list[Any]:
        """
        列出所有实体

        Returns:
            实体列表
        """
        with self._lock:
            return list(self._entities.values())

    def list_by_type(self, entity_type: str) -> list[Any]:
        """
        按类型列出实体

        Args:
            entity_type: 实体类型

        Returns:
            实体列表
        """
        with self._lock:
            entity_ids = self._type_index.get(entity_type, [])
            return [self._entities[eid] for eid in entity_ids if eid in self._entities]

    def count(self) -> int:
        """
        获取实体数量

        Returns:
            实体数量
        """
        with self._lock:
            return len(self._entities)

    def count_by_type(self, entity_type: str) -> int:
        """
        按类型获取实体数量

        Args:
            entity_type: 实体类型

        Returns:
            实体数量
        """
        with self._lock:
            return len(self._type_index.get(entity_type, []))

    def clear(self) -> None:
        """清空注册表"""
        with self._lock:
            self._entities.clear()
            self._entity_types.clear()
            self._type_index.clear()
            self._heartbeats.clear()

            # 发布事件
            self._emit_event(RegistryEvent(event_type=RegistryEventType.REGISTRY_CLEARED))

            logger.info("✅ 清空注册表")

    # ==================== 事件系统 ====================

    def add_event_listener(self, event_type: RegistryEventType, listener: EventListener) -> None:
        """
        添加事件监听器

        Args:
            event_type: 事件类型
            listener: 监听器函数
        """
        with self._lock:
            if listener not in self._event_listeners[event_type]:
                self._event_listeners[event_type].append(listener)
                logger.info(f"✅ 添加事件监听器: {event_type.value}")

    def remove_event_listener(self, event_type: RegistryEventType, listener: EventListener) -> None:
        """
        移除事件监听器

        Args:
            event_type: 事件类型
            listener: 监听器函数
        """
        with self._lock:
            if listener in self._event_listeners[event_type]:
                self._event_listeners[event_type].remove(listener)
                logger.info(f"✅ 移除事件监听器: {event_type.value}")

    def _emit_event(self, event: RegistryEvent) -> None:
        """
        发布事件

        Args:
            event: 事件对象
        """
        listeners = self._event_listeners.get(event.event_type, [])
        for listener in listeners:
            try:
                listener(event)
            except Exception as e:
                logger.error(f"❌ 事件监听器执行失败: {e}")

    # ==================== 健康检查 ====================

    def update_heartbeat(self, entity_id: str) -> None:
        """
        更新实体心跳

        Args:
            entity_id: 实体唯一标识
        """
        with self._lock:
            if entity_id in self._entities:
                self._heartbeats[entity_id] = datetime.now().isoformat()

    def check_health(self) -> dict[str, Any]:
        """
        检查所有实体健康状态

        Returns:
            健康状态字典
        """
        with self._lock:
            current_time = datetime.now()
            unhealthy_entities = []

            for entity_id, heartbeat_str in self._heartbeats.items():
                try:
                    heartbeat = datetime.fromisoformat(heartbeat_str)
                    time_diff = (current_time - heartbeat).total_seconds()

                    if time_diff > self._health_config.heartbeat_timeout:
                        unhealthy_entities.append(
                            {"entity_id": entity_id, "last_heartbeat": heartbeat_str, "timeout_seconds": time_diff}
                        )

                except Exception as e:
                    logger.error(f"❌ 检查实体 {entity_id} 健康状态失败: {e}")

            return {
                "healthy": len(unhealthy_entities) == 0,
                "total_entities": len(self._entities),
                "unhealthy_count": len(unhealthy_entities),
                "unhealthy_entities": unhealthy_entities,
            }

    # ==================== 统计信息 ====================

    def get_statistics(self) -> dict[str, Any]:
        """
        获取统计信息

        Returns:
            统计信息字典
        """
        with self._lock:
            type_counts = {etype: len(ids) for etype, ids in self._type_index.items()}

            return {
                "total_entities": len(self._entities),
                "entity_types": len(self._type_index),
                "type_distribution": type_counts,
                "metrics": self._metrics.to_dict(),
                "health_config": {
                    "heartbeat_interval": self._health_config.heartbeat_interval,
                    "heartbeat_timeout": self._health_config.heartbeat_timeout,
                    "auto_check_enabled": self._health_config.enable_auto_check,
                },
            }

    def get_metrics(self) -> RegistryMetrics:
        """
        获取性能指标

        Returns:
            性能指标对象
        """
        with self._lock:
            return self._metrics

    def health_check(self) -> dict[str, Any]:
        """
        注册中心自身健康检查

        Returns:
            健康状态字典
        """
        health_status = self.check_health()
        return {
            "healthy": health_status["healthy"],
            "message": f"Registry has {len(self._entities)} entities",
            "entity_health": health_status,
        }
