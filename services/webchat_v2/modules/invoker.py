#!/usr/bin/env python3
"""
平台模块调用器
处理模块调用请求，包括权限检查、参数验证等

作者: Athena平台团队
创建时间: 2025-01-31
版本: 2.0.1
"""

import asyncio
import time
from typing import Any, Callable, Dict, Optional

from .registry import (
    ModuleDefinition,
    ModuleStatus,
    InvokeRequest,
    InvokeResult,
    PlatformModuleRegistry,
)


class PlatformModuleInvoker:
    """平台模块调用器（带线程安全保护和超时控制）"""

    # 默认超时时间（秒）
    DEFAULT_TIMEOUT = 30

    def __init__(
        self,
        registry: PlatformModuleRegistry,
        identity_manager,
        default_timeout: int = DEFAULT_TIMEOUT
    ):
        """
        初始化调用器

        Args:
            registry: 模块注册表
            identity_manager: 身份管理器
            default_timeout: 默认超时时间
        """
        self.registry = registry
        self.identity_manager = identity_manager
        self.default_timeout = default_timeout
        self._metrics: Dict[str, Dict] = {}
        self._metrics_lock = asyncio.Lock()  # 线程安全保护

    async def invoke(
        self,
        request: InvokeRequest,
        timeout: Optional[int] = None
    ) -> InvokeResult:
        """
        调用平台模块（带超时控制）

        Args:
            request: 调用请求
            timeout: 超时时间（秒），None使用默认值

        Returns:
            调用结果
        """
        start_time = time.time()
        timeout = timeout or self.default_timeout

        try:
            # 1. 获取模块定义
            module_def = self.registry.get_module(request.module)
            if not module_def:
                return InvokeResult(
                    success=False,
                    error=f"模块不存在: {request.module}",
                    module=request.module,
                    action=request.action,
                )

            # 2. 检查模块是否启用
            if not module_def.enabled:
                return InvokeResult(
                    success=False,
                    error=f"模块已禁用: {request.module}",
                    module=request.module,
                    action=request.action,
                )

            # 3. 检查模块状态
            if module_def.status != ModuleStatus.AVAILABLE:
                return InvokeResult(
                    success=False,
                    error=f"模块不可用: {request.module} (状态: {module_def.status.value})",
                    module=request.module,
                    action=request.action,
                )

            # 4. 检查操作是否支持
            if request.action not in module_def.actions:
                return InvokeResult(
                    success=False,
                    error=f"操作不支持: {request.action} (模块: {request.module})",
                    module=request.module,
                    action=request.action,
                )

            # 5. 权限检查
            if not await self._check_permission(
                request.user_id,
                request.module,
                request.action
            ):
                return InvokeResult(
                    success=False,
                    error="权限不足",
                    module=request.module,
                    action=request.action,
                )

            # 6. 参数验证
            validation_error = self._validate_params(
                module_def,
                request.action,
                request.params
            )
            if validation_error:
                return InvokeResult(
                    success=False,
                    error=f"参数错误: {validation_error}",
                    module=request.module,
                    action=request.action,
                )

            # 7. 获取处理器并执行（带超时控制）
            handler = self.registry.get_handler(request.module, request.action)
            if not handler:
                # 如果没有注册处理器，返回模拟结果
                result_data = await self._mock_handler(
                    request.module,
                    request.action,
                    request.params
                )
            else:
                # 使用asyncio.wait_for添加超时控制
                result_data = await asyncio.wait_for(
                    handler(request.params),
                    timeout=timeout
                )

            # 8. 记录指标
            execution_time = time.time() - start_time
            await self._record_metrics(request.module, request.action, True, execution_time)

            return InvokeResult(
                success=True,
                data=result_data,
                module=request.module,
                action=request.action,
                execution_time=execution_time,
            )

        except asyncio.TimeoutError:
            execution_time = time.time() - start_time
            await self._record_metrics(request.module, request.action, False, execution_time)

            return InvokeResult(
                success=False,
                error=f"调用超时（超过{timeout}秒）",
                module=request.module,
                action=request.action,
                execution_time=execution_time,
            )

        except Exception as e:
            execution_time = time.time() - start_time
            await self._record_metrics(request.module, request.action, False, execution_time)

            return InvokeResult(
                success=False,
                error=str(e),
                module=request.module,
                action=request.action,
                execution_time=execution_time,
            )

    async def _check_permission(
        self,
        user_id: str,
        module: str,
        action: str
    ) -> bool:
        """检查权限"""
        identity = await self.identity_manager.get_identity(user_id)

        # 特权用户拥有所有权限
        if identity.admin_access:
            return True

        # 某些模块需要高级权限
        if module in ['tool.export', 'tool.report'] and not identity.advanced_features:
            return False

        return True

    def _validate_params(
        self,
        module_def: ModuleDefinition,
        action: str,
        params: Dict[str, Any]
    ) -> Optional[str]:
        """验证参数"""
        if action not in module_def.parameters:
            return None  # 没有参数定义，跳过验证

        param_def = module_def.parameters[action]

        # 检查必需参数
        for param_name, spec in param_def.items():
            if spec.get('required', False) and param_name not in params:
                return f"缺少必需参数: {param_name}"

            # 类型检查
            if param_name in params:
                expected_type = spec.get('type')
                if expected_type == 'string' and not isinstance(params[param_name], str):
                    return f"参数类型错误: {param_name} 应为字符串"
                elif expected_type == 'integer' and not isinstance(params[param_name], int):
                    return f"参数类型错误: {param_name} 应为整数"

        return None

    async def _record_metrics(
        self,
        module: str,
        action: str,
        success: bool,
        execution_time: float
    ) -> None:
        """记录指标（线程安全）"""
        key = f"{module}.{action}"

        async with self._metrics_lock:
            if key not in self._metrics:
                self._metrics[key] = {
                    "total_calls": 0,
                    "success_calls": 0,
                    "failure_calls": 0,
                    "total_time": 0.0,
                }

            self._metrics[key]["total_calls"] += 1
            if success:
                self._metrics[key]["success_calls"] += 1
            else:
                self._metrics[key]["failure_calls"] += 1
            self._metrics[key]["total_time"] += execution_time

    async def get_metrics(self, module: Optional[str] = None) -> Dict:
        """
        获取调用指标（线程安全）

        Args:
            module: 模块名称（可选）

        Returns:
            指标字典
        """
        async with self._metrics_lock:
            if module:
                return {
                    k: v.copy() for k, v in self._metrics.items()
                    if k.startswith(f"{module}.")
                }
            return {k: v.copy() for k, v in self._metrics.items()}

    async def _mock_handler(
        self,
        module: str,
        action: str,
        params: Dict[str, Any]
    ) -> Any:
        """
        模拟处理器（用于测试）

        Args:
            module: 模块名称
            action: 操作名称
            params: 参数

        Returns:
            模拟结果
        """
        await asyncio.sleep(0.1)  # 模拟处理延迟
        return {
            "module": module,
            "action": action,
            "params": params,
            "message": f"模拟执行: {module}.{action}",
            "timestamp": time.time(),
        }
