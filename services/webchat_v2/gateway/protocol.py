#!/usr/bin/env python3
"""
Gateway协议定义
基于Moltbot/Clawdbot的Gateway协议

定义Request/Response/Event消息帧格式

作者: Athena平台团队
创建时间: 2025-01-31
版本: 2.0.0
"""

from datetime import datetime
from typing import Any, Dict, Optional
from enum import Enum
import uuid


class FrameType(str, Enum):
    """消息帧类型"""
    REQUEST = "request"
    RESPONSE = "response"
    EVENT = "event"
    ERROR = "error"


class GatewayProtocol:
    """Gateway协议处理器"""

    @staticmethod
    def create_request(
        method: str,
        params: Dict[str, Any],
        request_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        创建请求帧

        Args:
            method: 方法名称
            params: 方法参数
            request_id: 请求ID（可选，默认自动生成）

        Returns:
            请求帧字典
        """
        return {
            "type": FrameType.REQUEST.value,
            "id": request_id or str(uuid.uuid4()),
            "method": method,
            "params": params,
            "timestamp": datetime.now().isoformat(),
        }

    @staticmethod
    def create_response(
        request_id: str,
        result: Any = None,
        error: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        创建响应帧

        Args:
            request_id: 对应的请求ID
            result: 结果数据
            error: 错误信息（如果有）

        Returns:
            响应帧字典
        """
        frame: Dict[str, Any] = {
            "type": FrameType.RESPONSE.value,
            "id": request_id,
            "timestamp": datetime.now().isoformat(),
        }

        if error:
            frame["error"] = error
        else:
            frame["result"] = result

        return frame

    @staticmethod
    def create_event(
        event_type: str,
        data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        创建事件帧

        Args:
            event_type: 事件类型
            data: 事件数据

        Returns:
            事件帧字典
        """
        return {
            "type": FrameType.EVENT.value,
            "event": event_type,
            "data": data,
            "timestamp": datetime.now().isoformat(),
        }

    @staticmethod
    def validate_frame(frame: Dict[str, Any]) -> bool:
        """
        验证消息帧格式

        Args:
            frame: 待验证的消息帧

        Returns:
            是否有效
        """
        required_fields = ["type", "timestamp"]
        if not all(field in frame for field in required_fields):
            return False

        frame_type = frame.get("type")

        if frame_type == FrameType.REQUEST.value:
            return "method" in frame and "id" in frame
        elif frame_type == FrameType.RESPONSE.value:
            return "id" in frame
        elif frame_type == FrameType.EVENT.value:
            return "event" in frame

        return False

    @staticmethod
    def validate_frame_enhanced(frame: Dict[str, Any]) -> Dict[str, Any]:
        """
        增强的消息帧验证（返回详细错误信息）

        Args:
            frame: 待验证的消息帧

        Returns:
            验证结果字典 {"valid": bool, "error": str|None}
        """
        # 检查基本类型
        if not isinstance(frame, dict):
            return {"valid": False, "error": "消息帧必须是字典类型"}

        # 检查必需字段
        required_fields = ["type", "timestamp"]
        missing_fields = [f for f in required_fields if f not in frame]
        if missing_fields:
            return {"valid": False, "error": f"缺少必需字段: {', '.join(missing_fields)}"}

        # 检查type字段值
        frame_type = frame.get("type")
        valid_types = [ft.value for ft in FrameType]
        if frame_type not in valid_types:
            return {"valid": False, "error": f"无效的type值: {frame_type}"}

        # 检查timestamp格式
        timestamp = frame.get("timestamp")
        if not isinstance(timestamp, str):
            return {"valid": False, "error": "timestamp必须是字符串"}

        # 根据type验证特定字段
        if frame_type == FrameType.REQUEST.value:
            if "method" not in frame:
                return {"valid": False, "error": "请求帧缺少method字段"}
            if "id" not in frame:
                return {"valid": False, "error": "请求帧缺少id字段"}
            # 验证params必须是字典
            params = frame.get("params")
            if params is not None and not isinstance(params, dict):
                return {"valid": False, "error": "params必须是字典类型"}

        elif frame_type == FrameType.RESPONSE.value:
            if "id" not in frame:
                return {"valid": False, "error": "响应帧缺少id字段"}
            # 必须有result或error之一
            if "result" not in frame and "error" not in frame:
                return {"valid": False, "error": "响应帧必须有result或error字段"}

        elif frame_type == FrameType.EVENT.value:
            if "event" not in frame:
                return {"valid": False, "error": "事件帧缺少event字段"}
            # 验证data
            data = frame.get("data")
            if data is not None and not isinstance(data, dict):
                return {"valid": False, "error": "data必须是字典类型"}

        return {"valid": True, "error": None}


# 支持的方法列表
class GatewayMethod:
    """Gateway方法常量"""

    # 聊天方法
    SEND = "send"
    POLL = "poll"
    ABORT = "abort"

    # 平台能力方法
    PLATFORM_MODULES = "platform_modules"
    PLATFORM_INVOKE = "platform_invoke"

    # 会话管理方法
    SESSIONS_LIST = "sessions_list"
    SESSIONS_PATCH = "sessions_patch"
    SESSIONS_RESET = "sessions_reset"
    SESSIONS_COMPACT = "sessions_compact"

    # 配置管理方法
    CONFIG_GET = "config_get"
    CONFIG_SET = "config_set"
    CONFIG_PATCH = "config_patch"


# 支持的事件类型
class GatewayEventType:
    """Gateway事件常量"""

    # 连接事件
    CONNECTED = "connected"
    DISCONNECTED = "disconnected"

    # 聊天事件
    CHAT_MESSAGE = "chat.message"
    CHAT_THINKING = "chat.thinking"
    CHAT_ERROR = "chat.error"

    # 系统事件
    HEARTBEAT = "heartbeat"
    ERROR = "error"
