#!/usr/bin/env python3
"""
系统管理器 - 服务注册表
System Manager - Service Registry

作者: Athena AI系统
创建时间: 2025-12-11
重构时间: 2026-01-27
版本: 2.0.0
"""

import logging
from threading import Lock
from typing import Any


logger = logging.getLogger(__name__)


class ServiceRegistry:
    """服务注册表

    管理模块提供的服务，支持服务发现和获取。
    """

    def __init__(self):
        """初始化服务注册表"""
        self.services: dict[str, tuple[str, Any]] = {}  # {service_name: (module_id, instance)}
        self.lock = Lock()
        self.logger = logging.getLogger(__name__)

    def register_service(self, module_id: str, service_name: str, instance: Any) -> bool:
        """注册服务

        Args:
            module_id: 模块ID
            service_name: 服务名称
            instance: 服务实例

        Returns:
            是否注册成功
        """
        with self.lock:
            if service_name in self.services:
                self.logger.warning(f"服务已存在: {service_name}")
                return False

            self.services[service_name] = (module_id, instance)
            self.logger.debug(f"服务已注册: {service_name} (模块: {module_id})")
            return True

    def unregister_service(self, service_name: str) -> bool:
        """注销服务

        Args:
            service_name: 服务名称

        Returns:
            是否注销成功
        """
        with self.lock:
            if service_name not in self.services:
                self.logger.warning(f"服务不存在: {service_name}")
                return False

            del self.services[service_name]
            self.logger.debug(f"服务已注销: {service_name}")
            return True

    def get_service(self, service_name: str) -> Any | None:
        """获取服务实例

        Args:
            service_name: 服务名称

        Returns:
            服务实例，不存在则返回None
        """
        with self.lock:
            if service_name not in self.services:
                return None

            _, instance = self.services[service_name]
            return instance

    def get_service_provider(self, service_name: str) -> str | None:
        """获取服务提供者模块ID

        Args:
            service_name: 服务名称

        Returns:
            模块ID，不存在则返回None
        """
        with self.lock:
            if service_name not in self.services:
                return None

            module_id, _ = self.services[service_name]
            return module_id

    def list_services(self) -> dict[str, str]:
        """列出所有服务

        Returns:
            {service_name: module_id} 字典
        """
        with self.lock:
            return {name: module_id for name, (module_id, _) in self.services.items()}

    def list_services_by_module(self, module_id: str) -> list[str]:
        """列出模块提供的所有服务

        Args:
            module_id: 模块ID

        Returns:
            服务名称列表
        """
        with self.lock:
            return [
                name
                for name, (mid, _) in self.services.items()
                if mid == module_id
            ]


__all__ = ["ServiceRegistry"]
