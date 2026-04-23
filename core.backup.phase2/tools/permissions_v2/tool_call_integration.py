"""
工具调用权限检查集成

将新的权限系统集成到工具调用管理器中。

作者: Athena平台团队
创建时间: 2026-04-20
"""
from __future__ import annotations

import logging
from typing import Any

from core.tools.tool_call_manager import ToolCallManager, ToolCallRequest, ToolCallResult, CallStatus
from core.tools.permissions_v2.manager import get_global_permission_manager
from core.tools.permissions_v2.modes import PermissionMode

logger = logging.getLogger(__name__)


class PermissionCheckedToolCallManager(ToolCallManager):
    """带权限检查的工具调用管理器

    在原有 ToolCallManager 基础上增加权限检查功能。

    权限检查位置：
    - 在速率限制检查之后
    - 在工具存在性检查之后
    - 在 Pre-tool-use Hooks 之前

    这样确保：
    1. 速率限制仍然有效
    2. 工具存在性仍然检查
    3. 权限检查在 Hooks 之前执行
    4. 如果权限被拒绝，可以提前返回
    """

    def __init__(self, *args, **kwargs):
        """初始化带权限检查的工具调用管理器"""
        super().__init__(*args, **kwargs)

        # 初始化全局权限管理器
        self.permission_manager = get_global_permission_manager()

        # 配置权限模式（从环境变量或配置文件）
        import os

        permission_mode = os.getenv("ATHENA_PERMISSION_MODE", "default")
        config_path = os.getenv("ATHENA_PERMISSION_CONFIG", "config/permissions.yaml")

        try:
            self.permission_manager.initialize(
                mode=PermissionMode(permission_mode),
                config_path=config_path,
            )
            logger.info(f"✅ 权限系统已初始化 (模式: {permission_mode})")
        except Exception as e:
            logger.warning(f"⚠️ 权限系统初始化失败，使用默认配置: {e}")
            self.permission_manager.initialize()

    async def call_tool(
        self,
        tool_name: str,
        parameters: dict[str, Any],
        context: dict[str, Any] | None = None,
        priority: int = 2,
        timeout: float | None = None,
    ) -> ToolCallResult:
        """调用工具（带权限检查）

        Args:
            tool_name: 工具名称
            parameters: 工具参数
            context: 调用上下文
            priority: 优先级 (1=high, 2=medium, 3=low)
            timeout: 超时时间（秒）

        Returns:
            ToolCallResult: 调用结果
        """
        # 生成请求ID
        import uuid

        request_id = str(uuid.uuid4())
        request = ToolCallRequest(
            request_id=request_id,
            tool_name=tool_name,
            parameters=parameters,
            context=context,
            priority=priority,
        )

        # 🚦 速率限制检查
        if self.enable_rate_limit and self.rate_limiter:
            allowed = await self.rate_limiter.acquire(timeout=0)
            if not allowed:
                logger.warning(f"🚫 速率限制:工具调用被拒绝 {tool_name}")
                result = ToolCallResult(
                    request_id=request_id,
                    tool_name=tool_name,
                    status=CallStatus.FAILED,
                    error="速率限制:调用过于频繁,请稍后重试",
                    execution_time=0.0,
                )
                self.stats["rate_limited_calls"] += 1
                self._record_result(result)
                return result

        # 🔒 权限检查（新增）
        allowed, reason = self.permission_manager.check_permission(tool_name, parameters)
        if not allowed:
            logger.warning(f"🚫 权限拒绝: {tool_name} - {reason}")

            # 获取当前权限模式
            current_mode = self.permission_manager.get_mode()

            result = ToolCallResult(
                request_id=request_id,
                tool_name=tool_name,
                status=CallStatus.FAILED,
                error=f"权限拒绝: {reason}",
                execution_time=0.0,
                metadata={
                    "permission_denied": True,
                    "permission_reason": reason,
                    "permission_mode": current_mode.value,
                },
            )
            self.stats["permission_denied_calls"] = self.stats.get("permission_denied_calls", 0) + 1
            self._record_result(result)
            return result

        # 检查工具是否存在
        tool = self.get_tool(tool_name)
        if not tool:
            result = ToolCallResult(
                request_id=request_id,
                tool_name=tool_name,
                status=CallStatus.FAILED,
                error=f"工具不存在: {tool_name}",
            )
            self._record_result(result)
            return result

        # 验证必需参数
        missing_params = [p for p in tool.required_params if p not in parameters]
        if missing_params:
            result = ToolCallResult(
                request_id=request_id,
                tool_name=tool_name,
                status=CallStatus.FAILED,
                error=f"缺少必需参数: {missing_params}",
            )
            self._record_result(result)
            return result

        # 设置超时
        effective_timeout = timeout or tool.timeout

        # 🎣 执行Pre-tool-use Hooks
        if self.enable_hooks and self.hook_registry:
            from core.tools.hooks import HookContext, HookEvent

            hook_context = HookContext(
                tool_name=tool_name,
                parameters=parameters,
                context=context,
                request_id=request_id,
            )

            try:
                hook_result = await self.hook_registry.execute_hooks(
                    HookEvent.PRE_TOOL_USE, hook_context
                )

                # Hook阻止调用
                if not hook_result.should_proceed:
                    logger.warning(
                        f"🚫 工具调用被Hook阻止: {tool_name} - {hook_result.error_message}"
                    )
                    result = ToolCallResult(
                        request_id=request_id,
                        tool_name=tool_name,
                        status=CallStatus.FAILED,
                        error=hook_result.error_message or "Hook阻止调用",
                        execution_time=0.0,
                        metadata=hook_result.metadata,
                    )
                    self.stats["hook_blocked_calls"] += 1
                    self._record_result(result)
                    return result

                # 应用修改后的参数
                if hook_result.modified_parameters:
                    parameters = hook_result.modified_parameters
                    logger.info(f"🔧 Hook修改参数: {tool_name}")

            except Exception as e:
                logger.error(f"❌ Pre-tool-use Hook执行失败: {e}")
                # Hook错误不应阻止主流程

        # 执行调用（调用父类方法）
        return await super().call_tool(tool_name, parameters, context, priority, timeout)

    def set_permission_mode(self, mode: PermissionMode) -> None:
        """设置权限模式

        Args:
            mode: 新的权限模式
        """
        self.permission_manager.set_mode(mode)
        logger.info(f"🔄 权限模式已切换: {mode.value}")

    def get_permission_mode(self) -> PermissionMode:
        """获取当前权限模式

        Returns:
            PermissionMode: 当前权限模式
        """
        return self.permission_manager.get_mode()


# ========================================
# 工厂函数
# ========================================


def create_tool_manager_with_permissions(*args, **kwargs) -> PermissionCheckedToolCallManager:
    """创建带权限检查的工具调用管理器

    Args:
        *args: 位置参数
        **kwargs: 关键字参数

    Returns:
        PermissionCheckedToolCallManager: 工具调用管理器实例
    """
    return PermissionCheckedToolCallManager(*args, **kwargs)


__all__ = [
    "PermissionCheckedToolCallManager",
    "create_tool_manager_with_permissions",
]
