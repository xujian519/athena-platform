#!/usr/bin/env python3
"""
安全模块
Security Module
"""

from __future__ import annotations
import logging
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


class SecurityEngine:
    """安全引擎 - 集成认证和访问控制能力"""

    def __init__(self, agent_id: str, config: dict | None = None):
        self.agent_id = agent_id
        self.config = config or {}
        self.initialized = False
        self.auth_manager = None
        self.access_controller = None
        self.enable_auth = self.config.get("enable_auth", True)
        self.enable_access_control = self.config.get("enable_access_control", True)

    async def initialize(self):
        """初始化安全引擎"""
        logger.info(f"🔐 启动安全引擎: {self.agent_id}")

        try:
            # 初始化认证管理器
            if self.enable_auth:
                from .auth_manager import get_auth_manager_instance

                self.auth_manager = await get_auth_manager_instance(self.config.get("auth", {}))
                logger.info(f"✅ 认证管理器集成完成: {self.agent_id}")
            else:
                logger.info(f"📝 认证功能已禁用: {self.agent_id}")

            # 初始化访问控制
            if self.enable_access_control and self.auth_manager:
                from .access_control import AccessController

                self.access_controller = AccessController(
                    self.auth_manager, self.config.get("access_control", {})
                )
                await self.access_controller.initialize()
                logger.info(f"✅ 访问控制系统集成完成: {self.agent_id}")
            else:
                logger.info(f"📝 访问控制功能已禁用: {self.agent_id}")

        except Exception as e:
            logger.warning(f"⚠️ 安全系统初始化失败,使用基础安全功能: {e}")
            self.auth_manager = None
            self.access_controller = None

        self.initialized = True

    async def authenticate(
        self, username: str, password: str, **kwargs
    ) -> dict[str, Any] | None:
        """用户认证"""
        if not self.auth_manager:
            return {"error": "认证功能未启用"}

        try:
            result = await self.auth_manager.authenticate_user(username, password, **kwargs)
            if result:
                user, session = result
                return {
                    "success": True,
                    "user_id": user.user_id,
                    "username": user.username,
                    "role": user.role.value,
                    "session_id": session.session_id,
                    "expires_at": session.expires_at.isoformat() if session.expires_at else None,
                }
            else:
                return {"success": False, "error": "认证失败"}
        except Exception as e:
            logger.error(f"认证错误: {e}")
            return {"success": False, "error": str(e)}

    async def verify_access(self, user_id: str, resource: str, action: str, **kwargs) -> bool:
        """验证访问权限"""
        if not self.access_controller:
            return True  # 如果没有访问控制,默认允许

        try:
            from .access_control import Action, Resource

            resource_enum = (
                Resource(resource) if resource in [r.value for r in Resource] else Resource.API
            )
            action_enum = Action(action) if action in [a.value for a in Action] else Action.READ

            result = await self.access_controller.check_access(
                user_id=user_id, resource=resource_enum, action=action_enum, **kwargs
            )
            return result.decision.value == "allow"
        except Exception as e:
            logger.error(f"访问验证错误: {e}")
            return False

    async def create_token(
        self, user_id: str, scopes: list[str] | None = None, **kwargs
    ) -> str | None:
        """创建访问令牌"""
        if not self.auth_manager:
            return None

        try:
            token = await self.auth_manager.create_access_token(user_id, scopes, **kwargs)
            return token.token if token else None
        except Exception as e:
            logger.error(f"令牌创建错误: {e}")
            return None

    async def validate_token(self, token: str, **kwargs) -> dict[str, Any] | None:
        """验证访问令牌"""
        if not self.auth_manager:
            return None

        try:
            result = await self.auth_manager.login_with_token(token, **kwargs)
            if result:
                user, session = result
                return {
                    "success": True,
                    "user_id": user.user_id,
                    "username": user.username,
                    "role": user.role.value,
                    "session_id": session.session_id,
                }
            else:
                return {"success": False, "error": "令牌无效"}
        except Exception as e:
            logger.error(f"令牌验证错误: {e}")
            return {"success": False, "error": str(e)}

    async def logout(self, session_id: str) -> bool:
        """用户登出"""
        if not self.auth_manager:
            return True

        try:
            return await self.auth_manager.logout_user(session_id)
        except Exception as e:
            logger.error(f"登出错误: {e}")
            return False

    async def register_user(
        self, username: str, email: str, password: str, role: str = "user", **kwargs
    ) -> dict[str, Any] | None:
        """注册用户"""
        if not self.auth_manager:
            return {"error": "用户注册功能未启用"}

        try:
            from .auth_manager import UserRole

            role_enum = UserRole(role) if role in [r.value for r in UserRole] else UserRole.USER

            user = await self.auth_manager.register_user(username, email, password, role_enum)
            if user:
                return {
                    "success": True,
                    "user_id": user.user_id,
                    "username": user.username,
                    "role": user.role.value,
                }
            else:
                return {"success": False, "error": "用户注册失败"}
        except Exception as e:
            logger.error(f"用户注册错误: {e}")
            return {"success": False, "error": str(e)}

    async def get_user_info(self, user_id: str) -> dict[str, Any] | None:
        """获取用户信息"""
        if not self.auth_manager:
            return None

        try:
            return await self.auth_manager.get_user_info(user_id)
        except Exception as e:
            logger.error(f"获取用户信息错误: {e}")
            return None

    async def change_password(self, user_id: str, old_password: str, new_password: str) -> bool:
        """修改密码"""
        if not self.auth_manager:
            return False

        try:
            return await self.auth_manager.change_password(user_id, old_password, new_password)
        except Exception as e:
            logger.error(f"密码修改错误: {e}")
            return False

    async def get_security_stats(self) -> dict[str, Any]:
        """获取安全统计信息"""
        stats = {
            "agent_id": self.agent_id,
            "auth_enabled": self.enable_auth,
            "access_control_enabled": self.enable_access_control,
            "timestamp": "2025-12-04T12:52:43.000000",
        }

        if self.auth_manager:
            try:
                auth_stats = await self.auth_manager.get_auth_stats()
                stats["authentication"] = auth_stats
            except Exception as e:
                logger.error(f"获取认证统计错误: {e}")

        if self.access_controller:
            try:
                access_stats = await self.access_controller.get_access_stats()
                stats["access_control"] = access_stats
            except Exception as e:
                logger.error(f"获取访问控制统计错误: {e}")

        return stats

    async def add_access_policy(
        self, resource: str, action: str, effect: str, **kwargs
    ) -> str | None:
        """添加访问策略"""
        if not self.access_controller:
            return None

        try:
            from .access_control import AccessDecision, Action, Resource

            resource_enum = (
                Resource(resource) if resource in [r.value for r in Resource] else Resource.API
            )
            action_enum = Action(action) if action in [a.value for a in Action] else Action.READ
            effect_enum = (
                AccessDecision(effect)
                if effect in [e.value for e in AccessDecision]
                else AccessDecision.DENY
            )

            policy_id = await self.access_controller.add_policy(
                resource=resource_enum, action=action_enum, effect=effect_enum, **kwargs
            )
            return policy_id
        except Exception as e:
            logger.error(f"添加访问策略错误: {e}")
            return None

    def register_callback(self, event_type: str, callback) -> None:
        """注册回调函数"""
        if not hasattr(self, "_callbacks"):
            self._callbacks = {}
        if event_type not in self._callbacks:
            self._callbacks[event_type] = []
        self._callbacks[event_type].append(callback)

    async def shutdown(self):
        logger.info(f"🔄 关闭安全引擎: {self.agent_id}")

        if self.access_controller:
            await self.access_controller.shutdown()

        if self.auth_manager:
            from .auth_manager import shutdown_auth_manager

            await shutdown_auth_manager()

        self.initialized = False

    @classmethod
    async def initialize_global(cls):
        if not hasattr(cls, "global_instance"):
            cls.global_instance = cls("global", {})
            await cls.global_instance.initialize()
        return cls.global_instance

    @classmethod
    async def shutdown_global(cls):
        if hasattr(cls, "global_instance") and cls.global_instance:
            await cls.global_instance.shutdown()
            del cls.global_instance


__all__ = ["SecurityEngine"]
