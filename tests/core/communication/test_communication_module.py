#!/usr/bin/env python3
"""
通信模块测试用例
Communication Module Tests

测试通信模块的核心功能，包括:
- 基础通信引擎
- WebSocket服务器
- 持久化引擎
- 学习对话管理器
- 增强监控

作者: Athena AI系统
版本: v1.0.0
创建时间: 2026-01-30
"""

import sys
from pathlib import Path
from unittest.mock import MagicMock

import pytest

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))


# =============================================================================
# === 基础通信引擎测试 ===
# =============================================================================

class TestCommunicationEngine:
    """基础通信引擎测试"""

    @pytest.fixture
    def engine(self):
        from core.communication import CommunicationEngine
        return CommunicationEngine(agent_id="test_agent", config={"test": True})

    def test_initialization(self, engine):
        """测试引擎初始化"""
        assert engine.agent_id == "test_agent"
        assert engine.config == {"test": True}
        assert engine.initialized is False

    @pytest.mark.asyncio
    async def test_initialize(self, engine):
        """测试引擎启动"""
        await engine.initialize()
        assert engine.initialized is True

    @pytest.mark.asyncio
    async def test_send_message(self, engine):
        """测试发送消息"""
        await engine.initialize()
        result = await engine.send_message("test message", channel="test")
        assert result["status"] == "sent"
        assert result["message"] == "test message"

    def test_register_callback(self, engine):
        """测试注册回调函数"""
        callback = MagicMock()
        engine.register_callback("test_event", callback)
        assert "test_event" in engine._callbacks
        assert callback in engine._callbacks["test_event"]

    @pytest.mark.asyncio
    async def test_shutdown(self, engine):
        """测试引擎关闭"""
        await engine.initialize()
        await engine.shutdown()
        assert engine.initialized is False

    @pytest.mark.asyncio
    async def test_global_instance(self):
        """测试全局实例"""
        from core.communication import CommunicationEngine
        instance1 = await CommunicationEngine.initialize_global()
        instance2 = await CommunicationEngine.initialize_global()
        assert instance1 is instance2
        await CommunicationEngine.shutdown_global()


# =============================================================================
# === 增强通信模块测试 ===
# =============================================================================

class TestEnhancedCommunicationModule:
    """增强通信模块测试"""

    @pytest.fixture
    def module(self):
        try:
            from core.communication import EnhancedCommunicationModule
            return EnhancedCommunicationModule
        except ImportError:
            pytest.skip("EnhancedCommunicationModule not available")

    @pytest.mark.asyncio
    async def test_module_initialization(self, module):
        """测试模块初始化"""
        instance = module(agent_id="test_agent")
        await instance.initialize()
        assert instance.initialized is True
        await instance.shutdown()


# =============================================================================
# === WebSocket 通信测试 ===
# =============================================================================

class TestWebSocketCommunication:
    """WebSocket 通信测试"""

    @pytest.fixture
    def websocket_available(self):
        try:
            from core.communication import WebSocketServer
            return True
        except ImportError:
            return False

    def test_websocket_import(self, websocket_available):
        """测试WebSocket导入"""
        if not websocket_available:
            pytest.skip("WebSocket not available")
        from core.communication import ConnectionManager, WebSocketServer
        assert WebSocketServer is not None
        assert ConnectionManager is not None

    @pytest.mark.asyncio
    async def test_connection_manager(self, websocket_available):
        """测试连接管理器"""
        if not websocket_available:
            pytest.skip("WebSocket not available")
        from core.communication import get_connection_manager
        manager = get_connection_manager()
        assert manager is not None


# =============================================================================
# === 持久化引擎测试 ===
# =============================================================================

class TestPersistentEngine:
    """持久化引擎测试"""

    @pytest.fixture
    def persistent_engine_available(self):
        try:
            from core.communication import PersistentCommunicationEngine
            return True
        except ImportError:
            return False

    def test_persistent_engine_import(self, persistent_engine_available):
        """测试持久化引擎导入"""
        if not persistent_engine_available:
            pytest.skip("PersistentCommunicationEngine not available")
        from core.communication import (
            FilePersistenceBackend,
            PersistentCommunicationEngine,
            RedisPersistenceBackend,
        )
        assert PersistentCommunicationEngine is not None
        assert FilePersistenceBackend is not None
        assert RedisPersistenceBackend is not None

    @pytest.mark.asyncio
    async def test_file_persistence(self, persistent_engine_available):
        """测试文件持久化"""
        if not persistent_engine_available:
            pytest.skip("PersistentCommunicationEngine not available")
        from core.communication import (
            FilePersistenceBackend,
            PersistenceConfig,
        )
        config = PersistenceConfig(
            storage_path="/tmp/test_communication",
            max_file_size=1024 * 1024,
        )
        backend = FilePersistenceBackend(config)
        await backend.initialize()
        # 测试保存和加载
        await backend.save("test_key", {"test": "data"})
        data = await backend.load("test_key")
        assert data == {"test": "data"}
        await backend.shutdown()


# =============================================================================
# === 学习对话管理器测试 ===
# =============================================================================

class TestLearningDialogManager:
    """学习对话管理器测试"""

    @pytest.fixture
    def dialog_manager_available(self):
        try:
            from core.communication import LearningDialogManager
            return True
        except ImportError:
            return False

    def test_dialog_manager_import(self, dialog_manager_available):
        """测试对话管理器导入"""
        if not dialog_manager_available:
            pytest.skip("LearningDialogManager not available")
        from core.communication import (
            DialogContext,
            DialogTurn,
            LearningDialogManager,
        )
        assert LearningDialogManager is not None
        assert DialogContext is not None
        assert DialogTurn is not None

    @pytest.mark.asyncio
    async def test_dialog_manager(self, dialog_manager_available):
        """测试对话管理器"""
        if not dialog_manager_available:
            pytest.skip("LearningDialogManager not available")
        from core.communication import get_dialog_manager
        manager = get_dialog_manager()
        assert manager is not None


# =============================================================================
# === 增强监控测试 ===
# =============================================================================

class TestEnhancedMonitoring:
    """增强监控测试"""

    @pytest.fixture
    def monitoring_available(self):
        try:
            from core.communication import CommunicationMonitor
            return True
        except ImportError:
            return False

    def test_monitoring_import(self, monitoring_available):
        """测试监控模块导入"""
        if not monitoring_available:
            pytest.skip("CommunicationMonitor not available")
        from core.communication import (
            CommunicationMetrics,
            CommunicationMonitor,
            MetricsCollector,
        )
        assert CommunicationMonitor is not None
        assert CommunicationMetrics is not None
        assert MetricsCollector is not None


# =============================================================================
# === 模块可用性测试 ===
# =============================================================================

class TestModuleCapabilities:
    """模块可用性测试"""

    def test_get_module_capabilities(self):
        """测试获取模块能力"""
        from core.communication import get_module_capabilities
        capabilities = get_module_capabilities()
        assert isinstance(capabilities, dict)
        assert "enhanced_communication" in capabilities
        assert "websocket" in capabilities
        assert "persistent_engine" in capabilities
        assert "dialog_manager" in capabilities
        assert "monitoring" in capabilities

    def test_get_available_features(self):
        """测试获取可用功能"""
        from core.communication import get_available_features
        features = get_available_features()
        assert isinstance(features, list)


# =============================================================================
# === 集成测试 ===
# =============================================================================

class TestCommunicationIntegration:
    """通信模块集成测试"""

    @pytest.mark.asyncio
    async def test_communication_flow(self):
        """测试完整通信流程"""
        from core.communication import CommunicationEngine
        engine = CommunicationEngine(agent_id="integration_test")

        # 初始化
        await engine.initialize()
        assert engine.initialized is True

        # 发送消息
        result = await engine.send_message(
            message="integration_test_message",
            channel="integration"
        )
        assert result["status"] == "sent"

        # 注册并触发回调
        callback_triggered = {"triggered": False}

        async def test_callback(data):
            callback_triggered["triggered"] = True

        engine.register_callback("message_sent", test_callback)

        # 关闭
        await engine.shutdown()
        assert engine.initialized is False


# =============================================================================
# === 性能测试 ===
# =============================================================================

class TestCommunicationPerformance:
    """通信模块性能测试"""

    @pytest.mark.asyncio
    @pytest.mark.benchmark(group="communication")
    async def test_send_message_performance(self, benchmark):
        """测试发送消息性能"""
        from core.communication import CommunicationEngine
        engine = CommunicationEngine(agent_id="perf_test")
        await engine.initialize()

        async def send_messages():
            for i in range(100):
                await engine.send_message(f"message_{i}", channel="perf")

        await benchmark(send_messages)
        await engine.shutdown()


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
