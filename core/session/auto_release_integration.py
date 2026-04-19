#!/usr/bin/env python3
from __future__ import annotations
"""
服务自动释放集成工具
Service Auto-Release Integration Utilities

为现有服务提供便捷的自动释放功能集成

作者: Athena平台团队
版本: 1.0.0
创建时间: 2026-02-09
"""

import logging
import os

from core.session.service_session_manager import (
    ServiceSession,
    ServiceType,
    auto_register_current_process,
    get_service_session_manager,
)

logger = logging.getLogger(__name__)


class ServiceAutoReleaseMixin:
    """
    服务自动释放混入类

    为现有服务提供自动释放功能的便捷集成方式。
    """

    def __init__(
        self,
        service_name: str,
        service_type: ServiceType,
        auto_stop: bool = True,
        idle_timeout: int | None = None
    ):
        """
        初始化自动释放功能

        Args:
            service_name: 服务名称
            service_type: 服务类型
            auto_stop: 是否自动停止
            idle_timeout: 自定义空闲超时时间（秒）
        """
        self.service_name = service_name
        self.service_type = service_type
        self.auto_stop = auto_stop
        self.idle_timeout = idle_timeout

        # 会话对象
        self._session: ServiceSession | None = None
        self._manager = None
        self._auto_release_enabled = False

    async def enable_auto_release(self) -> ServiceSession:
        """
        启用自动释放功能

        Returns:
            注册的会话对象
        """
        try:
            # 注册当前服务
            self._session = await auto_register_current_process(
                service_type=self.service_type,
                service_name=self.service_name,
                auto_stop=self.auto_stop,
                custom_timeout=self.idle_timeout
            )

            # 获取管理器
            self._manager = get_service_session_manager()
            self._auto_release_enabled = True

            logger.info(
                f"✅ 自动释放功能已启用: {self.service_name} "
                f"(自动停止: {self.auto_stop})"
            )

            return self._session

        except Exception as e:
            logger.error(f"❌ 启用自动释放功能失败: {e}")
            self._auto_release_enabled = False
            raise

    async def update_activity(self) -> bool:
        """
        更新服务活动时间

        Returns:
            是否更新成功
        """
        if not self._auto_release_enabled or not self._session:
            return False

        try:
            success = self._manager.update_activity(self._session.process_id)
            if success:
                logger.debug(f"🔄 活动时间已更新: {self.service_name}")
            return success
        except Exception as e:
            logger.error(f"❌ 更新活动时间失败: {e}")
            return False

    def get_session_info(self) -> ServiceSession | None:
        """
        获取会话信息

        Returns:
            会话对象，如果未启用则返回None
        """
        return self._session

    def is_auto_release_enabled(self) -> bool:
        """
        检查自动释放是否启用

        Returns:
            是否启用
        """
        return self._auto_release_enabled

    async def disable_auto_release(self):
        """禁用自动释放功能"""
        if self._manager:
            try:
                await self._manager.stop_monitoring()
                logger.info(f"🛑 自动释放功能已禁用: {self.service_name}")
            except Exception as e:
                logger.error(f"❌ 禁用自动释放功能失败: {e}")

        self._auto_release_enabled = False


class FastAPIAutoReleaseMixin:
    """
    FastAPI服务自动释放混入类

    为FastAPI服务提供自动释放功能，包括中间件自动更新活动时间。
    """

    def __init__(
        self,
        service_name: str,
        service_type: ServiceType,
        auto_stop: bool = True,
        idle_timeout: int | None = None
    ):
        """
        初始化FastAPI自动释放功能

        Args:
            service_name: 服务名称
            service_type: 服务类型
            auto_stop: 是否自动停止
            idle_timeout: 自定义空闲超时时间（秒）
        """
        self.service_name = service_name
        self.service_type = service_type
        self.auto_stop = auto_stop
        self.idle_timeout = idle_timeout

        # 会话对象
        self._session: ServiceSession | None = None
        self._manager = None
        self._auto_release_enabled = False

    async def enable_auto_release(self) -> ServiceSession:
        """
        启用自动释放功能

        Returns:
            注册的会话对象
        """
        try:
            # 注册当前服务
            self._session = await auto_register_current_process(
                service_type=self.service_type,
                service_name=self.service_name,
                auto_stop=self.auto_stop,
                custom_timeout=self.idle_timeout
            )

            # 获取管理器
            self._manager = get_service_session_manager()
            self._auto_release_enabled = True

            logger.info(
                f"✅ 自动释放功能已启用: {self.service_name} "
                f"(自动停止: {self.auto_stop})"
            )

            return self._session

        except Exception as e:
            logger.error(f"❌ 启用自动释放功能失败: {e}")
            self._auto_release_enabled = False
            raise

    async def update_activity(self) -> bool:
        """
        更新服务活动时间

        Returns:
            是否更新成功
        """
        if not self._auto_release_enabled or not self._session:
            return False

        try:
            success = self._manager.update_activity(self._session.process_id)
            return success
        except Exception as e:
            logger.error(f"❌ 更新活动时间失败: {e}")
            return False

    def create_activity_middleware(self, app):
        """
        创建活动更新中间件

        Args:
            app: FastAPI应用实例

        Returns:
            中间件函数
        """
        from fastapi import Request

        @app.middleware("http")
        async def activity_update_middleware(request: Request, call_next):
            """中间件：每个请求都更新活动时间"""
            # 更新活动时间
            await self.update_activity()

            # 继续处理请求
            response = await call_next(request)
            return response

        logger.info(f"✅ 活动更新中间件已添加: {self.service_name}")
        return activity_update_middleware

    def get_session_info(self) -> ServiceSession | None:
        """
        获取会话信息

        Returns:
            会话对象，如果未启用则返回None
        """
        return self._session

    def is_auto_release_enabled(self) -> bool:
        """
        检查自动释放是否启用

        Returns:
            是否启用
        """
        return self._auto_release_enabled

    async def disable_auto_release(self):
        """禁用自动释放功能"""
        if self._manager:
            try:
                await self._manager.stop_monitoring()
                logger.info(f"🛑 自动释放功能已禁用: {self.service_name}")
            except Exception as e:
                logger.error(f"❌ 禁用自动释放功能失败: {e}")

        self._auto_release_enabled = False


# =============================================================================
# === 配置工具 ===
# =============================================================================

def load_auto_release_config() -> dict:
    """
    从环境变量加载自动释放配置

    环境变量：
    - ATHENA_AUTO_RELEASE_ENABLED: 是否启用自动释放（默认: true）
    - ATHENA_IDLE_TIMEOUT: 空闲超时时间（秒，默认: 3600）
    - ATHENA_CLEANUP_INTERVAL: 清理检查间隔（秒，默认: 300）

    Returns:
        配置字典
    """
    return {
        'enabled': os.getenv('ATHENA_AUTO_RELEASE_ENABLED', 'true').lower() == 'true',
        'idle_timeout': int(os.getenv('ATHENA_IDLE_TIMEOUT', '3600')),
        'cleanup_interval': int(os.getenv('ATHENA_CLEANUP_INTERVAL', '300')),
    }


def get_service_auto_stop_config(service_name: str) -> bool:
    """
    获取服务的自动停止配置

    核心服务（Gateway、小诺）默认不自动停止

    Args:
        service_name: 服务名称

    Returns:
        是否自动停止
    """
    # 核心服务不自动停止
    core_services = ['gateway', 'xiaonuo', '小诺']
    return not any(core in service_name.lower() for core in core_services)


# =============================================================================
# === 装饰器 ===
# =============================================================================

def with_auto_release(
    service_name: str,
    service_type: ServiceType,
    auto_stop: bool | None = None,
    idle_timeout: int | None = None
):
    """
    自动释放装饰器

    为服务函数自动添加会话管理和活动更新功能

    Args:
        service_name: 服务名称
        service_type: 服务类型
        auto_stop: 是否自动停止（None表示自动判断）
        idle_timeout: 自定义空闲超时时间

    Returns:
        装饰器函数
    """
    def decorator(func):
        async def wrapper(*args, **kwargs):
            # 注册会话
            session = await auto_register_current_process(
                service_type=service_type,
                service_name=service_name,
                auto_stop=auto_stop if auto_stop is not None else get_service_auto_stop_config(service_name),
                custom_timeout=idle_timeout
            )

            manager = get_service_session_manager()

            try:
                # 执行原函数
                result = await func(*args, **kwargs)

                # 更新活动时间
                manager.update_activity(session.process_id)

                return result

            except Exception as e:
                logger.error(f"服务执行错误: {e}")
                raise

        return wrapper
    return decorator


__all__ = [
    "ServiceAutoReleaseMixin",
    "FastAPIAutoReleaseMixin",
    "load_auto_release_config",
    "get_service_auto_stop_config",
    "with_auto_release",
]
