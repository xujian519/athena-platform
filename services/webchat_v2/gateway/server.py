#!/usr/bin/env python3
"""
WebChat Gateway服务器
处理WebSocket连接和消息

作者: Athena平台团队
创建时间: 2025-01-31
版本: 2.0.2
"""

import asyncio
import json
from datetime import datetime, timezone
from typing import Optional

from fastapi import WebSocket, WebSocketDisconnect

from ..gateway import (
    GatewayProtocol,
    GatewaySession,
    GatewaySessionManager,
    GatewayMethod,
    GatewayEventType,
    FrameType,
)
from ..identity import XiaonuoIdentityManager
from ..modules import PlatformModuleRegistry, PlatformModuleInvoker, XiaonuoIntentRouter
from ..logging_config import LoggingMixin, format_request_info


class GatewayMethodHandler(LoggingMixin):
    """Gateway方法处理器（带日志）"""

    def __init__(
        self,
        session_manager: GatewaySessionManager,
        identity_manager: XiaonuoIdentityManager,
        intent_router: XiaonuoIntentRouter,
        platform_invoker: PlatformModuleInvoker,
    ):
        self.session_manager = session_manager
        self.identity_manager = identity_manager
        self.intent_router = intent_router
        self.platform_invoker = platform_invoker

    async def handle_request(
        self,
        session: GatewaySession,
        request: dict
    ) -> dict:
        """处理请求（带异常处理和日志）"""
        method = request.get("method")
        request_id = request.get("id", "")
        params = request.get("params", {})

        # 记录请求
        self.log_debug(
            "处理请求",
            method=method,
            request_id=request_id,
            user_id=session.user_id[:8] + "...",
        )

        try:
            # 路由到具体处理器
            if method == GatewayMethod.SEND:
                return await self._handle_send(session, params)
            elif method == GatewayMethod.PLATFORM_MODULES:
                return await self._handle_platform_modules(session, params)
            elif method == GatewayMethod.PLATFORM_INVOKE:
                return await self._handle_platform_invoke(session, params)
            elif method == GatewayMethod.SESSIONS_LIST:
                return await self._handle_sessions_list(session, params)
            elif method == GatewayMethod.SESSIONS_PATCH:
                return await self._handle_sessions_patch(session, params)
            elif method == GatewayMethod.CONFIG_GET:
                return await self._handle_config_get(session, params)
            elif method == GatewayMethod.CONFIG_SET:
                return await self._handle_config_set(session, params)
            else:
                self.log_warning("未知方法", method=method, request_id=request_id)
                return {"error": f"未知方法: {method}"}

        except Exception as e:
            # 记录异常
            self.log_exception(
                e,
                context=format_request_info(
                    method=method,
                    request_id=request_id,
                    user_id=session.user_id,
                )
            )
            return {"error": str(e)}

    async def _handle_send(self, session: GatewaySession, params: dict) -> dict:
        """处理send方法"""
        message = params.get("message")
        if not message:
            self.log_warning("send方法缺少message参数", user_id=session.user_id[:8] + "...")
            return {"error": "缺少message参数"}

        self.log_info("处理聊天消息", user_id=session.user_id[:8] + "...", message_len=len(message))

        try:
            # 使用意图路由器处理消息
            response, data = await self.intent_router.route_and_execute(
                user_message=message,
                user_id=session.user_id,
                session_id=session.session_id
            )

            # 发送响应事件
            event = GatewayProtocol.create_event(GatewayEventType.CHAT_MESSAGE, {
                "role": "assistant",
                "content": response,
                "data": data,
            })
            await session.send_json(event)

            self.log_debug("聊天消息处理完成", user_id=session.user_id[:8] + "...")
            return {"success": True}

        except Exception as e:
            self.log_exception(e, context={"user_id": session.user_id[:8] + "...", "action": "send"})
            raise

    async def _handle_platform_modules(self, session: GatewaySession, params: dict) -> dict:
        """处理platform_modules方法"""
        modules = self.platform_invoker.registry.list_modules()
        self.log_debug("列出可用模块", count=len(modules))

        return {
            "modules": [
                {
                    "name": m.name,
                    "display_name": m.display_name,
                    "description": m.description,
                    "category": m.category,
                    "actions": m.actions,
                }
                for m in modules
            ]
        }

    async def _handle_platform_invoke(self, session: GatewaySession, params: dict) -> dict:
        """处理platform_invoke方法"""
        from ..modules import InvokeRequest
        from ..logging_config import InvokeTimeoutError

        module = params.get("module")
        action = params.get("action")

        self.log_info(
            "调用平台模块",
            module=module,
            action=action,
            user_id=session.user_id[:8] + "...",
        )

        request = InvokeRequest(
            session_id=session.session_id,
            module=module,
            action=action,
            params=params.get("params", {}),
            user_id=session.user_id,
        )

        try:
            result = await self.platform_invoker.invoke(request)

            if result.success:
                self.log_debug(
                    "模块调用成功",
                    module=module,
                    action=action,
                    time=f"{result.execution_time:.3f}s",
                )
            else:
                self.log_error(
                    "模块调用失败",
                    module=module,
                    action=action,
                    error=result.error,
                )

            return {
                "success": result.success,
                "data": result.data,
                "error": result.error,
                "execution_time": result.execution_time,
            }

        except InvokeTimeoutError as e:
            self.log_exception(e, context={"module": module, "action": action})
            raise

    async def _handle_sessions_list(self, session: GatewaySession, params: dict) -> dict:
        """处理sessions_list方法"""
        user_sessions = await self.session_manager.get_user_sessions(session.user_id)
        self.log_debug("列出用户会话", count=len(user_sessions), user_id=session.user_id[:8] + "...")

        return {
            "sessions": [
                {
                    "session_id": s.session_id,
                    "connected": s.connected,
                }
                for s in user_sessions
            ]
        }

    async def _handle_sessions_patch(self, session: GatewaySession, params: dict) -> dict:
        """处理sessions_patch方法"""
        updates = params.get("updates", {})

        self.log_debug("更新会话配置", updates=updates, session_id=session.session_id[:8] + "...")

        if "thinking" in updates:
            session.thinking_enabled = updates["thinking"]
        if "verbose" in updates:
            session.verbose_enabled = updates["verbose"]
        if "model" in updates:
            session.model = updates["model"]

        return {"success": True}

    async def _handle_config_get(self, session: GatewaySession, params: dict) -> dict:
        """处理config_get方法"""
        key = params.get("key")

        config = {
            "thinking": session.thinking_enabled,
            "verbose": session.verbose_enabled,
            "model": session.model,
        }

        if key:
            return {"value": config.get(key)}
        return config

    async def _handle_config_set(self, session: GatewaySession, params: dict) -> dict:
        """处理config_set方法"""
        key = params.get("key")
        value = params.get("value")

        self.log_debug("设置配置", key=key, value=value, session_id=session.session_id[:8] + "...")

        if key == "thinking":
            session.thinking_enabled = value
        elif key == "verbose":
            session.verbose_enabled = value
        elif key == "model":
            session.model = value

        return {"success": True}


class WebChatGatewayServer(LoggingMixin):
    """WebChat Gateway服务器（带日志和改进的异常处理）"""

    # 消息大小限制（默认1MB）
    MAX_MESSAGE_SIZE = 1024 * 1024

    def __init__(
        self,
        identity_manager: XiaonuoIdentityManager,
        intent_router: XiaonuoIntentRouter,
        platform_invoker: PlatformModuleInvoker,
        heartbeat_interval: int = 30,
        max_message_size: int = MAX_MESSAGE_SIZE,
    ):
        self.session_manager = GatewaySessionManager()
        self.method_handler = GatewayMethodHandler(
            session_manager=self.session_manager,
            identity_manager=identity_manager,
            intent_router=intent_router,
            platform_invoker=platform_invoker,
        )
        self.heartbeat_interval = heartbeat_interval
        self.max_message_size = max_message_size
        self._heartbeat_tasks: dict[str, asyncio.Task] = {}

        self.log_info("Gateway服务器初始化完成",
                     heartbeat_interval=heartbeat_interval,
                     max_message_size=max_message_size)

    async def connect(
        self,
        websocket: WebSocket,
        user_id: str,
        session_id: Optional[str] = None,
        token: Optional[str] = None,
    ):
        """
        处理WebSocket连接（带认证、日志和异常处理）

        Args:
            websocket: WebSocket连接
            user_id: 用户ID
            session_id: 会话ID
            token: JWT认证token
        """
        # 验证JWT token（如果提供）
        if token:
            from ..auth import get_jwt_handler
            from ..logging_config import AuthenticationError

            jwt_handler = get_jwt_handler()
            try:
                payload = jwt_handler.verify_token(token)
                if not payload:
                    raise AuthenticationError("Token无效或已过期")
                if payload.user_id != user_id:
                    raise AuthenticationError(f"Token用户ID不匹配 (token:{payload.user_id} != request:{user_id})")

                self.log_debug("JWT认证成功", user_id=user_id[:8] + "...")

            except AuthenticationError as e:
                await websocket.close(code=1008, reason=str(e))
                self.log_warning("JWT认证失败", user_id=user_id[:8] + "...", error=str(e))
                return
            except Exception as e:
                await websocket.close(code=1008, reason="认证过程出错")
                self.log_error("JWT认证异常", user_id=user_id[:8] + "...", error=str(e))
                return

        await websocket.accept()

        # 创建会话
        session = await self.session_manager.create_session(
            websocket=websocket,
            user_id=user_id,
            session_id=session_id
        )

        self.log_info(
            "WebSocket连接建立",
            user_id=user_id[:8] + "...",
            session_id=session.session_id[:8] + "...",
            auth_enabled="是" if token else "否",
        )

        # 发送连接确认事件
        await session.send_json(GatewayProtocol.create_event(
            GatewayEventType.CONNECTED,
            {
                "session_id": session.session_id,
                "user_id": user_id,
            }
        ))

        # 启动心跳并跟踪任务
        heartbeat_task = asyncio.create_task(self._heartbeat_loop(session))
        self._heartbeat_tasks[session.session_id] = heartbeat_task

        # 消息处理循环
        try:
            while session.connected:
                try:
                    # 接收消息（带大小限制）
                    data = await websocket.receive_text()

                    # 验证消息大小
                    message_size = len(data.encode('utf-8'))
                    if message_size > self.max_message_size:
                        self.log_warning(
                            "消息过大，拒绝处理",
                            size=message_size,
                            max_size=self.max_message_size,
                            session_id=session.session_id[:8] + "...",
                        )
                        await session.send_json(GatewayProtocol.create_response(
                            request_id="",
                            error=f"消息过大（最大{self.max_message_size}字节）"
                        ))
                        continue

                    # 解析JSON
                    try:
                        frame = json.loads(data)
                    except json.JSONDecodeError as e:
                        self.log_warning("JSON解析失败", error=str(e), session_id=session.session_id[:8] + "...")
                        await session.send_json(GatewayProtocol.create_response(
                            request_id="",
                            error="JSON解析错误"
                        ))
                        continue

                    # 验证消息帧（增强版）
                    validation_result = GatewayProtocol.validate_frame_enhanced(frame)
                    if not validation_result["valid"]:
                        self.log_warning(
                            "消息帧验证失败",
                            error=validation_result["error"],
                            session_id=session.session_id[:8] + "...",
                        )
                        await session.send_json(GatewayProtocol.create_response(
                            request_id=frame.get("id", ""),
                            error=validation_result["error"]
                        ))
                        continue

                    # 处理请求
                    if frame["type"] == FrameType.REQUEST.value:
                        response = await self.method_handler.handle_request(session, frame)

                        # 构建响应帧：直接使用handler返回的结果
                        response_frame = GatewayProtocol.create_response(
                            request_id=frame.get("id", ""),
                            result=response,
                            error=response.get("error") if "error" in response else None
                        )
                        await session.send_json(response_frame)

                except RuntimeError as e:
                    # WebSocket已关闭
                    if "websocket is closed" in str(e).lower():
                        break
                    raise

        except WebSocketDisconnect as e:
            self.log_info(
                "WebSocket断开连接",
                code=e.code,
                reason=e.reason or "正常关闭",
                user_id=user_id[:8] + "...",
                session_id=session.session_id[:8] + "...",
            )
            await self._cleanup_session(session.session_id)

        except Exception as e:
            self.log_exception(
                e,
                context={
                    "user_id": user_id[:8] + "...",
                    "session_id": session.session_id[:8] + "...",
                    "event": "message_loop",
                }
            )
            try:
                await session.send_json(GatewayProtocol.create_event(
                    GatewayEventType.ERROR,
                    {"message": "服务器内部错误"}
                ))
            except:
                pass
            await self._cleanup_session(session.session_id)

    async def _cleanup_session(self, session_id: str):
        """
        清理会话资源（修复资源泄漏）

        Args:
            session_id: 会话ID
        """
        # 取消心跳任务
        if session_id in self._heartbeat_tasks:
            task = self._heartbeat_tasks[session_id]
            if not task.done():
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass
            del self._heartbeat_tasks[session_id]

        # 关闭会话
        await self.session_manager.close_session(session_id)

        self.log_debug("会话资源已清理", session_id=session_id[:8] + "...")

    async def _heartbeat_loop(self, session: GatewaySession):
        """心跳循环"""
        try:
            while session.connected:
                await session.send_json(GatewayProtocol.create_event(
                    GatewayEventType.HEARTBEAT,
                    {"timestamp": datetime.now(timezone.utc).isoformat()}
                ))
                await asyncio.sleep(self.heartbeat_interval)
        except asyncio.CancelledError:
            # 任务被取消，正常退出
            self.log_debug("心跳任务已取消", session_id=session.session_id[:8] + "...")
            raise
        except Exception as e:
            # 连接断开或发送失败
            self.log_debug("心跳循环退出", session_id=session.session_id[:8] + "...", error=str(e))

    def get_active_count(self) -> int:
        """获取活跃会话数"""
        return self.session_manager.get_active_count_sync()
