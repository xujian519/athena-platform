#!/usr/bin/env python3
"""
工具调用管理器单元测试

测试工具调用、超时、重试、速率限制等功能。
"""
import sys
import time
from pathlib import Path
from unittest.mock import patch

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

import pytest

from core.tools.tool_call_manager import (
    CallStatus,
    ToolCallManager,
    ToolCallRequest,
    ToolCallResult,
)


class TestToolCallRequest:
    """测试工具调用请求"""

    def test_creation(self):
        """测试创建请求"""
        request = ToolCallRequest(
            request_id="test-123",
            tool_name="test_tool",
            parameters={"query": "test"},
            priority=2,
            timeout=30.0,
        )

        assert request.request_id == "test-123"
        assert request.tool_name == "test_tool"
        assert request.parameters == {"query": "test"}
        assert request.priority == 2
        assert request.timeout == 30.0
        assert request.context is None

    def test_creation_with_context(self):
        """测试创建带上下文的请求"""
        context = {"session_id": "session-1", "user_id": "user-1"}

        request = ToolCallRequest(
            request_id="test-123",
            tool_name="test_tool",
            parameters={},
            context=context,
        )

        assert request.context == context


class TestToolCallResult:
    """测试工具调用结果"""

    def test_creation_success(self):
        """测试创建成功结果"""
        result = ToolCallResult(
            request_id="test-123",
            tool_name="test_tool",
            status=CallStatus.SUCCESS,
            result={"data": "success"},
            execution_time=1.5,
        )

        assert result.request_id == "test-123"
        assert result.tool_name == "test_tool"
        assert result.status == CallStatus.SUCCESS
        assert result.result == {"data": "success"}
        assert result.error is None
        assert result.execution_time == 1.5

    def test_creation_failure(self):
        """测试创建失败结果"""
        result = ToolCallResult(
            request_id="test-123",
            tool_name="test_tool",
            status=CallStatus.FAILED,
            error="执行失败",
            execution_time=0.5,
        )

        assert result.status == CallStatus.FAILED
        assert result.error == "执行失败"
        assert result.result is None

    def test_creation_timeout(self):
        """测试创建超时结果"""
        result = ToolCallResult(
            request_id="test-123",
            tool_name="test_tool",
            status=CallStatus.TIMEOUT,
            error="执行超时",
            execution_time=30.0,
        )

        assert result.status == CallStatus.TIMEOUT
        assert result.error == "执行超时"


class TestToolCallManager:
    """测试工具调用管理器"""

    def test_initialization(self):
        """测试初始化"""
        manager = ToolCallManager()

        assert manager.tools is not None
        assert len(manager.call_history) == 0
        assert manager.log_dir.exists()

    def test_initialization_with_rate_limit(self):
        """测试初始化(启用速率限制)"""
        manager = ToolCallManager(
            enable_rate_limit=True,
            max_calls_per_minute=60,
        )

        assert manager.enable_rate_limit is True
        assert manager.rate_limiter is not None

    def test_register_tool(self):
        """测试注册工具"""
        from core.tools.base import ToolDefinition, ToolPriority

        manager = ToolCallManager()

        tool = ToolDefinition(
            name="test_tool",
            display_name="测试工具",
            description="测试工具描述",
            category="test",
            priority=ToolPriority.MEDIUM,
            parameters=[],
        )

        manager.register_tool(tool)

        assert "test_tool" in manager.tools
        assert manager.tools["test_tool"].name == "test_tool"

    def test_execute_tool_success(self):
        """测试成功执行工具"""
        from core.tools.base import ToolDefinition, ToolPriority

        manager = ToolCallManager()

        # 创建模拟工具
        tool = ToolDefinition(
            name="test_tool",
            display_name="测试工具",
            description="测试工具",
            category="test",
            priority=ToolPriority.MEDIUM,
            parameters=[],
        )

        manager.register_tool(tool)

        # 模拟执行函数
        def mock_execute(params):
            return {"result": "success"}

        # 使用mock替代实际执行
        with patch.object(manager, "_execute_tool_impl", return_value={"result": "success"}):
            request = ToolCallRequest(
                request_id="test-123",
                tool_name="test_tool",
                parameters={},
            )

            result = manager.execute_tool(request)

            assert result.status == CallStatus.SUCCESS
            assert result.result == {"result": "success"}
            assert result.request_id == "test-123"

    def test_execute_tool_timeout(self):
        """测试工具执行超时"""
        from core.tools.base import ToolDefinition, ToolPriority

        manager = ToolCallManager()

        tool = ToolDefinition(
            name="slow_tool",
            display_name="慢速工具",
            description="执行时间长的工具",
            category="test",
            priority=ToolPriority.MEDIUM,
            parameters=[],
        )

        manager.register_tool(tool)

        # 模拟超时执行
        def slow_execute(params):
            time.sleep(5)  # 超过timeout
            return {"result": "done"}

        request = ToolCallRequest(
            request_id="test-456",
            tool_name="slow_tool",
            parameters={},
            timeout=1.0,  # 1秒超时
        )

        with patch.object(manager, "_execute_tool_impl", side_effect=slow_execute):
            result = manager.execute_tool(request)

            # 应该超时
            assert result.status in [CallStatus.TIMEOUT, CallStatus.FAILED]

    def test_execute_tool_not_found(self):
        """测试执行不存在的工具"""
        manager = ToolCallManager()

        request = ToolCallRequest(
            request_id="test-789",
            tool_name="non_existent_tool",
            parameters={},
        )

        result = manager.execute_tool(request)

        assert result.status == CallStatus.FAILED
        assert "未找到" in result.error or "not found" in result.error.lower()

    def test_rate_limiting(self):
        """测试速率限制"""
        from core.tools.base import ToolDefinition, ToolPriority

        manager = ToolCallManager(
            enable_rate_limit=True,
            max_calls_per_minute=2,  # 每分钟最多2次
        )

        tool = ToolDefinition(
            name="test_tool",
            display_name="测试工具",
            description="测试",
            category="test",
            priority=ToolPriority.MEDIUM,
            parameters=[],
        )

        manager.register_tool(tool)

        # 第一次调用(应该成功)
        request1 = ToolCallRequest(
            request_id="test-1",
            tool_name="test_tool",
            parameters={},
        )

        with patch.object(manager, "_execute_tool_impl", return_value={"result": "ok"}):
            result1 = manager.execute_tool(request1)
            assert result1.status == CallStatus.SUCCESS

            # 第二次调用(应该成功)
            request2 = ToolCallRequest(
                request_id="test-2",
                tool_name="test_tool",
                parameters={},
            )

            result2 = manager.execute_tool(request2)
            assert result2.status == CallStatus.SUCCESS

            # 第三次调用(应该被限流)
            request3 = ToolCallRequest(
                request_id="test-3",
                tool_name="test_tool",
                parameters={},
            )

            result3 = manager.execute_tool(request3)
            # 速率限制应该阻止调用
            assert result3.status == CallStatus.FAILED or "rate limit" in str(result3.error).lower() or "速率" in str(result3.error)

    def test_call_history(self):
        """测试调用历史记录"""
        from core.tools.base import ToolDefinition, ToolPriority

        manager = ToolCallManager(max_history=10)

        tool = ToolDefinition(
            name="test_tool",
            display_name="测试工具",
            description="测试",
            category="test",
            priority=ToolPriority.MEDIUM,
            parameters=[],
        )

        manager.register_tool(tool)

        # 执行多次调用
        for i in range(5):
            request = ToolCallRequest(
                request_id=f"test-{i}",
                tool_name="test_tool",
                parameters={"index": i},
            )

            with patch.object(manager, "_execute_tool_impl", return_value={"result": i}):
                manager.execute_tool(request)

        # 检查历史记录
        assert len(manager.call_history) == 5

        # 获取历史记录
        history = manager.get_call_history(limit=3)
        assert len(history) == 3

    def test_get_statistics(self):
        """测试获取统计信息"""
        from core.tools.base import ToolDefinition, ToolPriority

        manager = ToolCallManager()

        tool = ToolDefinition(
            name="test_tool",
            display_name="测试工具",
            description="测试",
            category="test",
            priority=ToolPriority.MEDIUM,
            parameters=[],
        )

        manager.register_tool(tool)

        # 执行一些调用
        for i in range(3):
            request = ToolCallRequest(
                request_id=f"test-{i}",
                tool_name="test_tool",
                parameters={},
            )

            with patch.object(manager, "_execute_tool_impl", return_value={"result": "ok"}):
                manager.execute_tool(request)

        # 获取统计信息
        stats = manager.get_statistics()

        assert "total_calls" in stats
        assert stats["total_calls"] == 3
        assert "success_count" in stats
        assert "failure_count" in stats

    def test_cleanup_old_history(self):
        """测试清理旧历史记录"""
        from core.tools.base import ToolDefinition, ToolPriority

        manager = ToolCallManager(max_history=5)

        tool = ToolDefinition(
            name="test_tool",
            display_name="测试工具",
            description="测试",
            category="test",
            priority=ToolPriority.MEDIUM,
            parameters=[],
        )

        manager.register_tool(tool)

        # 执行超过max_history的调用
        for i in range(10):
            request = ToolCallRequest(
                request_id=f"test-{i}",
                tool_name="test_tool",
                parameters={},
            )

            with patch.object(manager, "_execute_tool_impl", return_value={"result": i}):
                manager.execute_tool(request)

        # 由于deque的maxlen设置,历史记录应该被自动限制
        assert len(manager.call_history) <= 5


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
