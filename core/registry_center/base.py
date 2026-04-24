"""
基础接口层 - 定义注册表核心抽象

提供所有注册表必须实现的基础接口，确保一致性。
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Optional
from uuid import uuid4


class RegistryEventType(Enum):
    """注册表事件类型"""

    ENTITY_REGISTERED = "entity_registered"
    ENTITY_UNREGISTERED = "entity_unregistered"
    ENTITY_UPDATED = "entity_updated"
    HEALTH_CHECK_FAILED = "health_check_failed"
    REGISTRY_CLEARED = "registry_cleared"


@dataclass
class RegistryEvent:
    """注册表事件"""

    event_id: str = field(default_factory=lambda: str(uuid4()))
    event_type: RegistryEventType = RegistryEventType.ENTITY_REGISTERED
    entity_id: str = ""
    entity_type: str = ""
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    data: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "event_id": self.event_id,
            "event_type": self.event_type.value,
            "entity_id": self.entity_id,
            "entity_type": self.entity_type,
            "timestamp": self.timestamp,
            "data": self.data,
        }


# 事件监听器类型
EventListener = Callable[[RegistryEvent], None]


class BaseRegistry(ABC):
    """
    注册表基础接口

    所有注册表必须实现此接口，确保API一致性。
    """

    @abstractmethod
    def register(self, entity_id: str, entity: Any) -> bool:
        """
        注册实体

        Args:
            entity_id: 实体唯一标识
            entity: 实体对象

        Returns:
            bool: 注册是否成功
        """
        pass

    @abstractmethod
    def unregister(self, entity_id: str) -> bool:
        """
        注销实体

        Args:
            entity_id: 实体唯一标识

        Returns:
            bool: 注销是否成功
        """
        pass

    @abstractmethod
    def get(self, entity_id: str) -> Optional[Any]:
        """
        获取实体

        Args:
            entity_id: 实体唯一标识

        Returns:
            实体对象，不存在返回None
        """
        pass

    @abstractmethod
    def exists(self, entity_id: str) -> bool:
        """
        检查实体是否存在

        Args:
            entity_id: 实体唯一标识

        Returns:
            bool: 是否存在
        """
        pass

    @abstractmethod
    def list_all(self) -> list[Any]:
        """
        列出所有实体

        Returns:
            实体列表
        """
        pass

    @abstractmethod
    def count(self) -> int:
        """
        获取实体数量

        Returns:
            实体数量
        """
        pass

    @abstractmethod
    def clear(self) -> None:
        """清空注册表"""
        pass

    # 可选接口 - 子类可以覆盖

    def update(self, entity_id: str, entity: Any) -> bool:
        """
        更新实体

        Args:
            entity_id: 实体唯一标识
            entity: 新的实体对象

        Returns:
            bool: 更新是否成功
        """
        if not self.exists(entity_id):
            return False
        # 默认实现：先注销再注册
        self.unregister(entity_id)
        return self.register(entity_id, entity)

    def add_event_listener(self, event_type: RegistryEventType, listener: EventListener) -> None:
        """
        添加事件监听器

        Args:
            event_type: 事件类型
            listener: 监听器函数
        """
        # 默认实现：什么都不做（子类可以覆盖）
        # 参数名以下划线开头表示 intentionally unused
        _ = event_type, listener
        pass

    def remove_event_listener(self, event_type: RegistryEventType, listener: EventListener) -> None:
        """
        移除事件监听器

        Args:
            event_type: 事件类型
            listener: 监听器函数
        """
        # 默认实现：什么都不做（子类可以覆盖）
        # 参数名以下划线开头表示 intentionally unused
        _ = event_type, listener
        pass

    def get_statistics(self) -> dict[str, Any]:
        """
        获取统计信息

        Returns:
            统计信息字典
        """
        return {
            "total_entities": self.count(),
            "registry_type": self.__class__.__name__,
        }

    def health_check(self) -> dict[str, Any]:
        """
        健康检查

        Returns:
            健康状态字典
        """
        return {
            "healthy": True,
            "message": "Registry is healthy",
        }
