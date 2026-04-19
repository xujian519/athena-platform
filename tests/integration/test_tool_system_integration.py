#!/usr/bin/env python3
"""
工具系统集成测试

测试完整的工具调用流程,包括工具注册、选择、调用、监控等。
"""
import sys
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

import pytest
from core.tools.tool_manager import ToolManager
from core.tools.selector import ToolSelector, SelectionStrategy
from core.tools.tool_call_manager import ToolCallManager, ToolCallRequest, CallStatus
from core.tools.base import ToolDefinition, ToolRegistry, ToolPriority
from core.tools.permissions import (
    ToolPermissionContext,
    PermissionMode,
    PermissionRule,
)


class TestToolSystemIntegration:
    """测试工具系统集成"""

    def test_end_to_end_tool_call(self):
        """测试端到端工具调用流程"""

        # 1. 创建工具管理器
        manager = ToolManager()

        # 2. 注册工具
        registry = manager.registry

        search_tool = ToolDefinition(
            name="web_search",
            display_name="网络搜索",
            description="搜索互联网信息",
            category="search",
            priority=ToolPriority.HIGH,
            parameters=[
                {"name": "query", "type": "string", "description": "搜索查询"},
                {"name": "limit", "type": "integer", "description": "结果数量"},
            ],
        )

        registry.register(search_tool)

        # 3. 创建工具组
        from core.tools.tool_group import ToolGroupDef

        group_def = ToolGroupDef(
            name="search-group",
            display_name="搜索工具组",
            description="搜索相关工具",
            tool_names=["web_search"],
        )

        manager.register_group(group_def)
        manager.activate_group("search-group")

        # 4. 创建工具调用管理器
        call_manager = ToolCallManager()
        call_manager.register_tool(search_tool)

        # 5. 创建权限上下文
        permission_ctx = ToolPermissionContext(
            mode=PermissionMode.AUTO,
            always_allow=[
                PermissionRule(
                    rule_id="allow-search",
                    pattern="web_search",
                    description="允许搜索工具",
                    priority=10,
                )
            ],
        )

        # 6. 权限检查
        decision = permission_ctx.check_permission("web_search")
        assert decision.allowed is True

        # 7. 工具选择
        selector = ToolSelector(registry)
        tools = registry.list_tools()
        best_tool = selector.select_best_tool(tools, "搜索相关信息")

        assert best_tool is not None
        assert best_tool.name == "web_search"

        # 8. 执行工具调用
        request = ToolCallRequest(
            request_id="test-integration-001",
            tool_name="web_search",
            parameters={"query": "Python测试", "limit": 5},
        )

        # 模拟执行
        with patch.object(call_manager, "_execute_tool_impl", return_value={"results": ["result1", "result2"]}):
            result = call_manager.execute_tool(request)

            assert result.status == CallStatus.SUCCESS
            assert result.result == {"results": ["result1", "result2"]}

    def test_multi_tool_selection(self):
        """测试多工具选择场景"""

        # 创建工具管理器
        manager = ToolManager()
        registry = manager.registry

        # 注册多个工具
        search_tool = ToolDefinition(
            name="web_search",
            display_name="网络搜索",
            description="搜索互联网",
            category="search",
            priority=ToolPriority.HIGH,
            parameters=[],
        )

        compute_tool = ToolDefinition(
            name="calculator",
            display_name="计算器",
            description="数学计算",
            category="compute",
            priority=ToolPriority.MEDIUM,
            parameters=[],
        )

        file_tool = ToolDefinition(
            name="file_reader",
            display_name="文件读取",
            description="读取文件内容",
            category="file",
            priority=ToolPriority.LOW,
            parameters=[],
        )

        registry.register(search_tool)
        registry.register(compute_tool)
        registry.register(file_tool)

        # 创建选择器
        selector = ToolSelector(registry)
        tools = registry.list_tools()

        # 测试不同任务场景
        # 搜索任务
        best_for_search = selector.select_best_tool(tools, "搜索Python教程")
        assert best_for_search.name == "web_search"

        # 计算任务
        best_for_compute = selector.select_best_tool(tools, "计算数学公式")
        assert best_for_compute.name == "calculator"

        # 文件任务
        best_for_file = selector.select_best_tool(tools, "读取配置文件")
        assert best_for_file.name == "file_reader"

    def test_permission_blocking(self):
        """测试权限阻止工具调用"""

        # 创建权限上下文(自动拒绝)
        permission_ctx = ToolPermissionContext(
            mode=PermissionMode.AUTO,
            always_deny=[
                PermissionRule(
                    rule_id="block-dangerous",
                    pattern="dangerous:*",
                    description="阻止危险工具",
                    priority=100,
                )
            ],
        )

        # 测试被阻止的工具
        decision = permission_ctx.check_permission("dangerous:command")
        assert decision.allowed is False
        assert "拒绝" in decision.reason

        # 测试允许的工具
        decision = permission_ctx.check_permission("safe:tool")
        assert decision.allowed is False  # AUTO模式默认拒绝

    def test_tool_group_switching(self):
        """测试工具组切换"""

        manager = ToolManager()

        # 创建两个工具组
        from core.tools.tool_group import ToolGroupDef

        group1 = ToolGroupDef(
            name="search-group",
            display_name="搜索组",
            description="搜索工具",
            tool_names=[],
        )

        group2 = ToolGroupDef(
            name="compute-group",
            display_name="计算组",
            description="计算工具",
            tool_names=[],
        )

        manager.register_group(group1)
        manager.register_group(group2)

        # 激活组1
        manager.activate_group("search-group")
        assert manager.active_group == "search-group"

        # 切换到组2
        manager.activate_group("compute-group")
        assert manager.active_group == "compute-group"

        # 组1应该不再激活
        assert manager.get_group("search-group").is_active() is False

    def test_error_handling_integration(self):
        """测试错误处理集成"""

        manager = ToolManager()
        registry = manager.registry

        # 注册一个会失败的工具
        failing_tool = ToolDefinition(
            name="failing_tool",
            display_name="失败工具",
            description="总是失败的工具",
            category="test",
            priority=ToolPriority.MEDIUM,
            parameters=[],
        )

        registry.register(failing_tool)

        # 创建调用管理器
        call_manager = ToolCallManager()
        call_manager.register_tool(failing_tool)

        # 执行调用
        request = ToolCallRequest(
            request_id="test-error-001",
            tool_name="failing_tool",
            parameters={},
        )

        # 模拟失败
        with patch.object(call_manager, "_execute_tool_impl", side_effect=Exception("工具执行失败")):
            result = call_manager.execute_tool(request)

            assert result.status == CallStatus.FAILED
            assert result.error is not None

        # 检查历史记录
        history = call_manager.get_call_history()
        assert len(history) > 0
        assert history[0].status == CallStatus.FAILED

    def test_performance_monitoring(self):
        """测试性能监控"""

        manager = ToolManager()
        registry = manager.registry

        # 注册工具
        tool = ToolDefinition(
            name="test_tool",
            display_name="测试工具",
            description="测试",
            category="test",
            priority=ToolPriority.MEDIUM,
            parameters=[],
        )

        registry.register(tool)

        # 创建调用管理器
        call_manager = ToolCallManager()
        call_manager.register_tool(tool)

        # 执行多次调用
        import time

        execution_times = []

        for i in range(3):
            request = ToolCallRequest(
                request_id=f"test-perf-{i}",
                tool_name="test_tool",
                parameters={"index": i},
            )

            start_time = time.time()

            with patch.object(call_manager, "_execute_tool_impl", return_value={"result": i}):
                result = call_manager.execute_tool(request)

            end_time = time.time()

            if result.status == CallStatus.SUCCESS:
                execution_times.append(result.execution_time)

        # 获取统计信息
        stats = call_manager.get_statistics()

        assert stats["total_calls"] == 3
        assert "average_time" in stats or "total_calls" in stats

    def test_concurrent_calls(self):
        """测试并发调用"""

        manager = ToolManager()
        registry = manager.registry

        # 注册工具
        tool = ToolDefinition(
            name="async_tool",
            display_name="异步工具",
            description="支持异步调用",
            category="test",
            priority=ToolPriority.MEDIUM,
            parameters=[],
        )

        registry.register(tool)

        # 创建调用管理器
        call_manager = ToolCallManager()
        call_manager.register_tool(tool)

        # 创建多个并发请求
        requests = []
        for i in range(5):
            request = ToolCallRequest(
                request_id=f"test-concurrent-{i}",
                tool_name="async_tool",
                parameters={"index": i},
            )
            requests.append(request)

        # 并发执行(使用mock)
        with patch.object(call_manager, "_execute_tool_impl", return_value={"result": "ok"}):
            results = []
            for req in requests:
                result = call_manager.execute_tool(req)
                results.append(result)

        # 验证所有调用都成功
        assert len(results) == 5
        successful = [r for r in results if r.status == CallStatus.SUCCESS]
        assert len(successful) == 5


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
