#!/usr/bin/env python3
"""
通信模块 - 统一导出接口
Communication Module - Unified Export Interface

提供完整的通信功能，包括:
- 基础消息通信
- WebSocket 实时双向通信
- 消息持久化
- 增强监控
- 学习对话管理

作者: Athena AI系统
版本: v2.0.0
更新时间: 2026-01-30
"""

import logging

logger = logging.getLogger(__name__)

# =============================================================================
# === 基础通信引擎 ===
# =============================================================================

class CommunicationEngine:
    """基础通信引擎"""

    def __init__(self, agent_id: str, config: dict | None = None):
        self.agent_id = agent_id
        self.config = config or {}
        self.initialized = False

    async def initialize(self):
        logger.info(f"💬 启动通信引擎: {self.agent_id}")
        self.initialized = True

    async def send_message(self, message, channel="default"):
        return {"status": "sent", "message": message}

    def register_callback(self, event_type: str, callback) -> None:
        """注册回调函数"""
        if not hasattr(self, "_callbacks"):
            self._callbacks = {}
        if event_type not in self._callbacks:
            self._callbacks[event_type] = []
        self._callbacks[event_type].append(callback)

    async def shutdown(self):
        logger.info(f"🔄 关闭通信引擎: {self.agent_id}")
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


# =============================================================================
# === 增强通信模块 ===
# =============================================================================

# 导入增强通信模块
try:
    from .enhanced_communication_module import (
        ChannelResult,
        EnhancedCommunicationConfig,
        EnhancedCommunicationModule,
        MessageResult,
    )

    ENHANCED_COMMUNICATION_AVAILABLE = True
except ImportError as e:
    logger.warning(f"增强通信模块导入失败: {e}")
    ENHANCED_COMMUNICATION_AVAILABLE = False
    EnhancedCommunicationModule = None
    EnhancedCommunicationConfig = None
    MessageResult = None
    ChannelResult = None


# =============================================================================
# === WebSocket 通信 ===
# =============================================================================

try:
    from .websocket.websocket_server import (
        WebSocketServer,
        get_websocket_server,
        start_websocket_server,
    )
    from .websocket.connection_manager import (
        ConnectionManager,
        get_connection_manager,
    )
    from .websocket.message_protocol import (
        MessageProtocol,
        WebSocketMessage,
        MessageType,
    )

    WEBSOCKET_AVAILABLE = True
except ImportError as e:
    logger.warning(f"WebSocket模块导入失败: {e}")
    WEBSOCKET_AVAILABLE = False
    WebSocketServer = None
    ConnectionManager = None
    MessageProtocol = None
    WebSocketMessage = None
    MessageType = None


# =============================================================================
# === 持久化引擎 ===
# =============================================================================

try:
    from .persistent_engine import (
        PersistentCommunicationEngine,
        get_persistent_engine,
    )

    PERSISTENT_ENGINE_AVAILABLE = True
except ImportError as e:
    logger.warning(f"持久化引擎导入失败: {e}")
    PERSISTENT_ENGINE_AVAILABLE = False
    PersistentCommunicationEngine = None


# =============================================================================
# === 持久化后端 ===
# =============================================================================

try:
    from .persistence.base_persistence import (
        BasePersistenceBackend,
        PersistenceConfig,
    )
    from .persistence.file_persistence import FilePersistenceBackend
    from .persistence.redis_persistence import RedisPersistenceBackend
    from .persistence.persistence_manager import (
        PersistenceManager,
        get_persistence_manager,
    )
    from .persistence.queue_recovery import (
        QueueRecoveryManager,
        get_recovery_manager,
    )

    PERSISTENCE_AVAILABLE = True
except ImportError as e:
    logger.warning(f"持久化后端导入失败: {e}")
    PERSISTENCE_AVAILABLE = False
    BasePersistenceBackend = None
    PersistenceConfig = None
    FilePersistenceBackend = None
    RedisPersistenceBackend = None
    PersistenceManager = None
    QueueRecoveryManager = None


# =============================================================================
# === 学习对话管理器 ===
# =============================================================================

try:
    from .learning_dialog_manager import (
        DialogContext,
        DialogManager,
        DialogTurn,
        LearningDialogManager,
        get_dialog_manager,
    )

    DIALOG_MANAGER_AVAILABLE = True
except ImportError as e:
    logger.warning(f"学习对话管理器导入失败: {e}")
    DIALOG_MANAGER_AVAILABLE = False
    DialogContext = None
    DialogManager = None
    DialogTurn = None
    LearningDialogManager = None


# =============================================================================
# === 增强监控 ===
# =============================================================================

try:
    from .enhanced_monitoring import (
        CommunicationMetrics,
        CommunicationMonitor,
        MetricsCollector,
        get_monitor,
    )

    MONITORING_AVAILABLE = True
except ImportError as e:
    logger.warning(f"增强监控模块导入失败: {e}")
    MONITORING_AVAILABLE = False
    CommunicationMetrics = None
    CommunicationMonitor = None
    MetricsCollector = None


# =============================================================================
# === 通信引擎 (完整版) ===
# =============================================================================

try:
    from .communication_engine import (
        Channel,
        ChannelType,
        CommunicationEngine as FullCommunicationEngine,
        Message,
        MessageStatus,
        MessageType as EngineMessageType,
        ProtocolType,
    )

    FULL_ENGINE_AVAILABLE = True
except ImportError as e:
    logger.warning(f"完整通信引擎导入失败: {e}")
    FULL_ENGINE_AVAILABLE = False
    FullCommunicationEngine = None
    Channel = None
    ChannelType = None
    Message = None
    MessageStatus = None
    EngineMessageType = None
    ProtocolType = None


# =============================================================================
# === 轻量级通信引擎 ===
# =============================================================================

try:
    from .lightweight_communication_engine import (
        LightweightCommunicationEngine,
        get_lightweight_engine,
    )

    LIGHTWEIGHT_ENGINE_AVAILABLE = True
except ImportError as e:
    logger.warning(f"轻量级通信引擎导入失败: {e}")
    LIGHTWEIGHT_ENGINE_AVAILABLE = False
    LightweightCommunicationEngine = None


# =============================================================================
# === 优化通信模块 ===
# =============================================================================

try:
    from .optimized_communication_module import (
        OptimizedCommunicationModule,
        get_optimized_module,
    )

    OPTIMIZED_MODULE_AVAILABLE = True
except ImportError as e:
    logger.warning(f"优化通信模块导入失败: {e}")
    OPTIMIZED_MODULE_AVAILABLE = False
    OptimizedCommunicationModule = None


# =============================================================================
# === 其他组件 ===
# =============================================================================

try:
    from .task_manager import TaskManager
    from .message_handler import MessageHandler
    from .rate_limit import RateLimiter
    from .tracking import MessageTracker
    from .metrics import MetricsAPI
    from .validation import validate_message, validate_channel
except ImportError as e:
    logger.warning(f"其他组件导入失败: {e}")
    TaskManager = None
    MessageHandler = None
    RateLimiter = None
    MessageTracker = None
    MetricsAPI = None
    validate_message = None
    validate_channel = None


# =============================================================================
# === 统一导出列表 ===
# =============================================================================

__all__ = [
    # === 基础通信引擎 ===
    "CommunicationEngine",
    # === 增强通信模块 ===
    "EnhancedCommunicationModule",
    "EnhancedCommunicationConfig",
    "MessageResult",
    "ChannelResult",
    # === WebSocket 通信 ===
    "WebSocketServer",
    "ConnectionManager",
    "MessageProtocol",
    "WebSocketMessage",
    "MessageType",
    # === 持久化引擎 ===
    "PersistentCommunicationEngine",
    # === 持久化后端 ===
    "BasePersistenceBackend",
    "PersistenceConfig",
    "FilePersistenceBackend",
    "RedisPersistenceBackend",
    "PersistenceManager",
    "QueueRecoveryManager",
    # === 学习对话管理器 ===
    "LearningDialogManager",
    "DialogManager",
    "DialogContext",
    "DialogTurn",
    # === 增强监控 ===
    "CommunicationMonitor",
    "CommunicationMetrics",
    "MetricsCollector",
    # === 完整通信引擎 ===
    "FullCommunicationEngine",
    "Channel",
    "ChannelType",
    "Message",
    "MessageStatus",
    "ProtocolType",
    # === 轻量级通信引擎 ===
    "LightweightCommunicationEngine",
    # === 优化通信模块 ===
    "OptimizedCommunicationModule",
    # === 其他组件 ===
    "TaskManager",
    "MessageHandler",
    "RateLimiter",
    "MessageTracker",
    "MetricsAPI",
    # === 便捷函数 ===
    "get_websocket_server",
    "get_connection_manager",
    "get_persistent_engine",
    "get_persistence_manager",
    "get_recovery_manager",
    "get_dialog_manager",
    "get_monitor",
    "get_lightweight_engine",
    "get_optimized_module",
    "validate_message",
    "validate_channel",
]


# =============================================================================
# === 模块可用性检查 ===
# =============================================================================

def get_module_capabilities() -> dict:
    """获取通信模块可用能力"""
    return {
        "enhanced_communication": ENHANCED_COMMUNICATION_AVAILABLE,
        "websocket": WEBSOCKET_AVAILABLE,
        "persistent_engine": PERSISTENT_ENGINE_AVAILABLE,
        "persistence": PERSISTENCE_AVAILABLE,
        "dialog_manager": DIALOG_MANAGER_AVAILABLE,
        "monitoring": MONITORING_AVAILABLE,
        "full_engine": FULL_ENGINE_AVAILABLE,
        "lightweight_engine": LIGHTWEIGHT_ENGINE_AVAILABLE,
        "optimized_module": OPTIMIZED_MODULE_AVAILABLE,
    }


def get_available_features() -> list:
    """获取可用功能列表"""
    capabilities = get_module_capabilities()
    return [name for name, available in capabilities.items() if available]
