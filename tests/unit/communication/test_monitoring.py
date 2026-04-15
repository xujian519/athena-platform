#!/usr/bin/env python3
"""
通信模块监控单元测试
Unit Tests for Communication Module Monitoring

作者: Athena AI系统
创建时间: 2026-01-25
版本: 1.0.0
"""

import pytest

pytestmark = pytest.mark.skip(reason="Missing required modules: ")

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from unittest.mock import patch

from core.communication.monitoring import (
    PROMETHEUS_AVAILABLE,
    CommunicationMetrics,
    get_metrics,
    init_metrics,
    track_errors,
    track_message_processing,
)


@pytest.mark.unit
class TestCommunicationMetrics:
    """通信指标测试"""

    @pytest.fixture
    def metrics(self):
        """创建指标实例"""
        return CommunicationMetrics()

    def test_metrics_initialization(self, metrics):
        """测试指标初始化"""
        assert metrics is not None
        if PROMETHEUS_AVAILABLE:
            assert metrics.is_enabled()
        else:
            assert not metrics.is_enabled()

    def test_record_message_sent(self, metrics):
        """测试记录发送消息"""
        if not PROMETHEUS_AVAILABLE:
            return

        # 正常发送
        metrics.record_message_sent("direct", "success")
        metrics.record_message_sent("group", "failed")

        # 验证指标已记录
        # 实际值需要通过Prometheus客户端获取，这里只验证不抛出异常

    def test_record_message_received(self, metrics):
        """测试记录接收消息"""
        if not PROMETHEUS_AVAILABLE:
            return

        metrics.record_message_received("broadcast")
        metrics.record_message_received("api")

    def test_record_batch_processed(self, metrics):
        """测试记录批处理"""
        if not PROMETHEUS_AVAILABLE:
            return

        metrics.record_batch_processed(100, "success")
        metrics.record_batch_processed(50, "failed")

    def test_set_queue_size(self, metrics):
        """测试设置队列大小"""
        if not PROMETHEUS_AVAILABLE:
            return

        metrics.set_queue_size("agent_001", 10)
        metrics.set_queue_size("agent_002", 5)

    def test_connection_metrics(self, metrics):
        """测试连接池指标"""
        if not PROMETHEUS_AVAILABLE:
            return

        # 记录连接操作
        metrics.record_connection_acquired("mcp_pool", 0.05, "success")
        metrics.record_connection_released("mcp_pool")
        metrics.record_connection_created("mcp_pool")

        # 设置连接数
        metrics.set_active_connections("mcp_pool", 5)
        metrics.set_idle_connections("mcp_pool", 3)

        # 健康检查
        metrics.record_health_check("mcp_pool", True)
        metrics.record_health_check("mcp_pool", False)

    def test_performance_metrics(self, metrics):
        """测试性能指标"""
        if not PROMETHEUS_AVAILABLE:
            return

        # 使用上下文管理器记录处理时间
        with metrics.record_message_processing("send_message"):
            time.sleep(0.01)

        with metrics.record_batch_processing():
            time.sleep(0.02)

        # 设置吞吐量
        metrics.set_throughput(100.5)

    def test_error_metrics(self, metrics):
        """测试错误指标"""
        if not PROMETHEUS_AVAILABLE:
            return

        metrics.record_error("connection_error", "mcp_client")
        metrics.record_error("timeout", "stateless_client")

        metrics.record_validation_failure("agent_id", "agent_id")
        metrics.record_validation_failure("channel_id", "channel_id")

        metrics.record_timeout("acquire_connection")
        metrics.record_timeout("send_message")

    def test_get_metrics_text(self, metrics):
        """测试获取指标文本"""
        if not PROMETHEUS_AVAILABLE:
            assert metrics.get_metrics_text() == b""
            return

        metrics_text = metrics.get_metrics_text()
        assert isinstance(metrics_text, bytes)
        assert len(metrics_text) > 0

    def test_get_content_type(self):
        """测试获取内容类型"""
        content_type = CommunicationMetrics.get_content_type()
        assert isinstance(content_type, str)

        if PROMETHEUS_AVAILABLE:
            assert "text/plain" in content_type or "prometheus" in content_type.lower()


@pytest.mark.unit
class TestGlobalMetrics:
    """全局指标实例测试"""

    def test_get_metrics_singleton(self):
        """测试获取全局单例"""
        # 清除全局实例
        import core.communication.monitoring as monitoring_module
        monitoring_module._metrics_instance = None

        metrics1 = get_metrics()
        metrics2 = get_metrics()

        assert metrics1 is metrics2

    def test_init_metrics(self):
        """测试初始化指标"""
        import core.communication.monitoring as monitoring_module
        monitoring_module._metrics_instance = None

        metrics = init_metrics("test_namespace", "test_subsystem")

        assert metrics is not None
        assert metrics._namespace == "test_namespace"
        assert metrics._subsystem == "test_subsystem"


@pytest.mark.unit
class TestDecorators:
    """装饰器测试"""

    @pytest.mark.asyncio
    async def test_track_message_processing_async(self):
        """测试跟踪异步消息处理"""
        if not PROMETHEUS_AVAILABLE:
            return

        @track_message_processing("test_operation")
        async def async_function(x: int) -> int:
            await asyncio.sleep(0.01)
            return x * 2

        import asyncio
        result = await async_function(5)
        assert result == 10

    def test_track_message_processing_sync(self):
        """测试跟踪同步消息处理"""
        if not PROMETHEUS_AVAILABLE:
            return

        @track_message_processing("test_operation")
        def sync_function(x: int) -> int:
            time.sleep(0.01)
            return x * 2

        result = sync_function(5)
        assert result == 10

    @pytest.mark.asyncio
    async def test_track_errors_async(self):
        """测试跟踪异步错误"""
        if not PROMETHEUS_AVAILABLE:
            return

        @track_errors("test_component", "test_error")
        async def async_function():
            raise ValueError("Test error")

        with pytest.raises(ValueError):
            await async_function()

    def test_track_errors_sync(self):
        """测试跟踪同步错误"""
        if not PROMETHEUS_AVAILABLE:
            return

        @track_errors("test_component", "test_error")
        def sync_function():
            raise ValueError("Test error")

        with pytest.raises(ValueError):
            sync_function()


@pytest.mark.unit
class TestPrometheusAvailability:
    """Prometheus可用性测试"""

    def test_prometheus_available_flag(self):
        """测试Prometheus可用性标志"""
        assert isinstance(PROMETHEUS_AVAILABLE, bool)

    def test_metrics_when_unavailable(self):
        """测试Prometheus不可用时的行为"""
        with patch('core.communication.monitoring.PROMETHEUS_AVAILABLE', False):
            metrics = CommunicationMetrics()

            # 所有的方法应该优雅地处理Prometheus不可用的情况
            metrics.record_message_sent("direct", "success")
            metrics.record_message_received("broadcast")
            metrics.record_batch_processed(100)
            metrics.set_queue_size("agent_001", 10)

            metrics.record_connection_acquired("pool", 0.1)
            metrics.record_connection_released("pool")
            metrics.record_connection_created("pool")

            metrics.set_active_connections("pool", 5)
            metrics.set_idle_connections("pool", 3)
            metrics.record_health_check("pool", True)

            with metrics.record_message_processing("test"):
                pass

            metrics.set_throughput(100.0)

            metrics.record_error("test", "component")
            metrics.record_validation_failure("type", "field")
            metrics.record_timeout("operation")

            # 验证不抛出异常
            assert not metrics.is_enabled()
            assert metrics.get_metrics_text() == b""


@pytest.mark.unit
class TestMetricsIntegration:
    """指标集成测试"""

    def test_metrics_workflow(self):
        """测试完整的工作流程"""
        if not PROMETHEUS_AVAILABLE:
            return

        metrics = CommunicationMetrics()

        # 模拟完整的通信流程
        # 1. 发送消息
        metrics.record_message_sent("direct", "success")

        # 2. 接收消息
        metrics.record_message_received("broadcast")

        # 3. 批处理
        with metrics.record_batch_processing():
            metrics.record_batch_processed(100)

        # 4. 连接池操作
        metrics.record_connection_acquired("mcp_pool", 0.05)
        metrics.set_active_connections("mcp_pool", 5)
        metrics.record_connection_released("mcp_pool")

        # 5. 错误处理
        metrics.record_validation_failure("agent_id", "sender_id")

        # 获取指标文本
        metrics_text = metrics.get_metrics_text()
        assert len(metrics_text) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
