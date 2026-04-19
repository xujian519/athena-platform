#!/usr/bin/env python3
"""
真实工具实现测试

测试所有替换为真实实现的工具

作者: Athena平台团队
创建时间: 2026-01-25
"""

import asyncio
import sys
from pathlib import Path

import pytest

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from core.tools.real_tool_implementations import (
    real_chat_companion_handler,
    real_code_analyzer_handler,
    real_knowledge_graph_handler,
    real_system_monitor_handler,
    real_web_search_handler,
    register_real_tools,
)
from core.tools.tool_call_manager import CallStatus, ToolCallManager


@pytest.mark.integration
class TestRealCodeAnalyzer:
    """测试真实代码分析器"""

    @pytest.mark.asyncio
    async def test_basic_analysis(self):
        """测试基础代码分析"""
        code = """
def hello_world():
    print("Hello, World!")
    return True
"""

        result = await real_code_analyzer_handler(
            params={"code": code, "language": "python"},
            context=None
        )

        assert result["language"] == "python"
        assert "analysis" in result
        assert result["analysis"]["total_lines"] > 0
        assert "quality_score" in result

    @pytest.mark.asyncio
    async def test_complexity_detection(self):
        """测试复杂度检测"""
        # 高复杂度代码
        complex_code = """
def complex_function(x):
    if x > 0:
        if x > 10:
            if x > 20:
                if x > 30:
                    return x
    return 0
"""

        result = await real_code_analyzer_handler(
            params={"code": complex_code, "language": "python"},
            context=None
        )

        assert result["analysis"]["complexity"] > 1
        assert result["analysis"]["complexity_level"] in ["低", "中", "高"]

    @pytest.mark.asyncio
    async def test_issue_detection(self):
        """测试问题检测"""
        # 长行代码
        long_line_code = (
            "def f(): " +
            "x = 1" * 50
        )

        result = await real_code_analyzer_handler(
            params={"code": long_line_code, "language": "python"},
            context=None
        )

        assert "issues" in result
        assert isinstance(result["issues"], list)

    @pytest.mark.asyncio
    async def test_suggestions_generation(self):
        """测试建议生成"""
        good_code = """
def simple_function():
    return 42
"""

        result = await real_code_analyzer_handler(
            params={"code": good_code, "language": "python"},
            context=None
        )

        assert "suggestions" in result
        assert isinstance(result["suggestions"], list)
        assert len(result["suggestions"]) > 0

    @pytest.mark.asyncio
    async def test_missing_code_param(self):
        """测试缺少code参数"""
        with pytest.raises(ValueError, match="缺少必需参数"):
            await real_code_analyzer_handler(
                params={},
                context=None
            )


@pytest.mark.integration
class TestRealSystemMonitor:
    """测试真实系统监控"""

    @pytest.mark.asyncio
    async def test_cpu_monitoring(self):
        """测试CPU监控"""
        result = await real_system_monitor_handler(
            params={"target": "system", "metrics": ["cpu"]},
            context=None
        )

        assert "metrics" in result
        assert "cpu" in result["metrics"]
        assert "usage_percent" in result["metrics"]["cpu"]
        assert 0 <= result["metrics"]["cpu"]["usage_percent"] <= 100

    @pytest.mark.asyncio
    async def test_memory_monitoring(self):
        """测试内存监控"""
        result = await real_system_monitor_handler(
            params={"target": "system", "metrics": ["memory"]},
            context=None
        )

        assert "metrics" in result
        assert "memory" in result["metrics"]
        assert "total_gb" in result["metrics"]["memory"]
        assert "usage_percent" in result["metrics"]["memory"]
        assert result["metrics"]["memory"]["total_gb"] > 0

    @pytest.mark.asyncio
    async def test_disk_monitoring(self):
        """测试磁盘监控"""
        result = await real_system_monitor_handler(
            params={"target": "system", "metrics": ["disk"]},
            context=None
        )

        assert "metrics" in result
        assert "disk" in result["metrics"]
        assert "total_gb" in result["metrics"]["disk"]
        assert result["metrics"]["disk"]["total_gb"] > 0

    @pytest.mark.asyncio
    async def test_all_metrics(self):
        """测试所有指标监控"""
        result = await real_system_monitor_handler(
            params={
                "target": "system",
                "metrics": ["cpu", "memory", "disk", "network"]
            },
            context=None
        )

        assert "metrics" in result
        assert len(result["metrics"]) >= 4
        assert "status" in result
        assert result["status"] in ["healthy", "warning"]


@pytest.mark.integration
class TestRealWebSearch:
    """测试真实网络搜索"""

    @pytest.mark.asyncio
    async def test_basic_search(self):
        """测试基础搜索"""
        result = await real_web_search_handler(
            params={"query": "Python programming", "limit": 5},
            context=None
        )

        assert "query" in result
        assert "total" in result
        assert "results" in result
        assert isinstance(result["results"], list)
        assert len(result["results"]) > 0

    @pytest.mark.asyncio
    async def test_search_result_structure(self):
        """测试搜索结果结构"""
        result = await real_web_search_handler(
            params={"query": "AI technology", "limit": 3},
            context=None
        )

        if len(result["results"]) > 0:
            first_result = result["results"][0]
            assert "title" in first_result
            assert "url" in first_result
            assert "snippet" in first_result

    @pytest.mark.asyncio
    async def test_missing_query_param(self):
        """测试缺少query参数"""
        with pytest.raises(ValueError, match="缺少必需参数"):
            await real_web_search_handler(
                params={},
                context=None
            )

    @pytest.mark.asyncio
    async def test_empty_query(self):
        """测试空查询"""
        with pytest.raises(ValueError, match="缺少必需参数"):
            await real_web_search_handler(
                params={"query": ""},
                context=None
            )


@pytest.mark.integration
class TestRealKnowledgeGraph:
    """测试真实知识图谱"""

    @pytest.mark.asyncio
    async def test_python_entity(self):
        """测试Python实体查询"""
        result = await real_knowledge_graph_handler(
            params={"query": "python", "domain": "programming"},
            context=None
        )

        assert "query" in result
        assert "results" in result
        entities = result["results"]["entities"]
        assert len(entities) > 0
        assert entities[0]["entity"] == "python"
        assert entities[0]["type"] == "programming_language"

    @pytest.mark.asyncio
    async def test_athena_entity(self):
        """测试Athena实体查询"""
        result = await real_knowledge_graph_handler(
            params={"query": "athena", "domain": "platform"},
            context=None
        )

        assert "results" in result
        entities = result["results"]["entities"]
        assert len(entities) > 0
        assert entities[0]["entity"] == "athena"

    @pytest.mark.asyncio
    async def test_related_entities(self):
        """测试关联实体"""
        result = await real_knowledge_graph_handler(
            params={"query": "python", "domain": "programming"},
            context=None
        )

        relations = result["results"]["relations"]
        assert isinstance(relations, list)

    @pytest.mark.asyncio
    async def test_fuzzy_match(self):
        """测试模糊匹配"""
        result = await real_knowledge_graph_handler(
            params={"query": "machine", "domain": "technology"},
            context=None
        )

        entities = result["results"]["entities"]
        assert len(entities) > 0


@pytest.mark.integration
class TestRealChatCompanion:
    """测试真实聊天伴侣"""

    @pytest.mark.asyncio
    async def test_greeting(self):
        """测试问候"""
        result = await real_chat_companion_handler(
            params={"message": "你好"},
            context=None
        )

        assert "response" in result
        assert "intent" in result
        assert result["intent"] == "greeting"
        assert "你好" in result["response"]

    @pytest.mark.asyncio
    async def test_farewell(self):
        """测试告别"""
        result = await real_chat_companion_handler(
            params={"message": "再见"},
            context=None
        )

        assert "response" in result
        assert result["intent"] == "farewell"
        assert "再见" in result["response"]

    @pytest.mark.asyncio
    async def test_help_request(self):
        """测试帮助请求"""
        result = await real_chat_companion_handler(
            params={"message": "帮助"},
            context=None
        )

        assert "response" in result
        assert result["intent"] == "help"
        assert "帮助" in result["response"] or "服务" in result["response"]

    @pytest.mark.asyncio
    async def test_sentiment_detection(self):
        """测试情感检测"""
        # 积极情感
        result_positive = await real_chat_companion_handler(
            params={"message": "我真的很开心"},
            context=None
        )
        assert result_positive["sentiment"] == "positive"

        # 消极情感
        result_negative = await real_chat_companion_handler(
            params={"message": "这让我很难过"},
            context=None
        )
        assert result_negative["sentiment"] == "negative"

    @pytest.mark.asyncio
    async def test_style_variations(self):
        """测试风格变化"""
        # 友好风格
        result_friendly = await real_chat_companion_handler(
            params={"message": "你好", "style": "friendly"},
            context=None
        )

        # 专业风格
        result_professional = await real_chat_companion_handler(
            params={"message": "你好", "style": "professional"},
            context=None
        )

        assert result_friendly["response"] != result_professional["response"]


@pytest.mark.integration
class TestRealToolsIntegration:
    """测试真实工具集成"""

    @pytest.mark.asyncio
    async def test_register_all_real_tools(self):
        """测试注册所有真实工具"""
        manager = ToolCallManager(enable_rate_limit=False)

        # 注册真实工具
        await register_real_tools(manager)

        # 验证工具已注册
        tools = manager.list_tools()
        assert "code_analyzer" in tools
        assert "system_monitor" in tools
        assert "web_search" in tools
        assert "knowledge_graph" in tools
        assert "chat_companion" in tools

        assert len(tools) >= 5

    @pytest.mark.asyncio
    async def test_code_analyzer_through_manager(self):
        """测试通过管理器调用代码分析器"""
        manager = ToolCallManager(enable_rate_limit=False)
        await register_real_tools(manager)

        code = "def test(): return 42"
        result = await manager.call_tool(
            tool_name="code_analyzer",
            parameters={"code": code, "language": "python"}
        )

        assert result.status == CallStatus.SUCCESS
        assert result.result is not None
        assert result.result["language"] == "python"

    @pytest.mark.asyncio
    async def test_system_monitor_through_manager(self):
        """测试通过管理器调用系统监控"""
        manager = ToolCallManager(enable_rate_limit=False)
        await register_real_tools(manager)

        result = await manager.call_tool(
            tool_name="system_monitor",
            parameters={"metrics": ["cpu", "memory"]}
        )

        assert result.status == CallStatus.SUCCESS
        assert result.result is not None
        assert "metrics" in result.result

    @pytest.mark.asyncio
    async def test_web_search_through_manager(self):
        """测试通过管理器调用网络搜索"""
        manager = ToolCallManager(enable_rate_limit=False)
        await register_real_tools(manager)

        result = await manager.call_tool(
            tool_name="web_search",
            parameters={"query": "test search", "limit": 3}
        )

        assert result.status == CallStatus.SUCCESS
        assert result.result is not None
        assert result.result["total"] >= 0

    @pytest.mark.asyncio
    async def test_knowledge_graph_through_manager(self):
        """测试通过管理器调用知识图谱"""
        manager = ToolCallManager(enable_rate_limit=False)
        await register_real_tools(manager)

        result = await manager.call_tool(
            tool_name="knowledge_graph",
            parameters={"query": "python"}
        )

        assert result.status == CallStatus.SUCCESS
        assert result.result is not None
        assert "results" in result.result

    @pytest.mark.asyncio
    async def test_chat_companion_through_manager(self):
        """测试通过管理器调用聊天伴侣"""
        manager = ToolCallManager(enable_rate_limit=False)
        await register_real_tools(manager)

        result = await manager.call_tool(
            tool_name="chat_companion",
            parameters={"message": "你好"}
        )

        assert result.status == CallStatus.SUCCESS
        assert result.result is not None
        assert "response" in result.result

    @pytest.mark.asyncio
    async def test_concurrent_tool_calls(self):
        """测试并发工具调用"""
        manager = ToolCallManager(enable_rate_limit=False)
        await register_real_tools(manager)

        # 并发调用多个工具
        tasks = [
            manager.call_tool("code_analyzer", {"code": "x=1"}),
            manager.call_tool("system_monitor", {"metrics": ["cpu"]}),
            manager.call_tool("knowledge_graph", {"query": "test"}),
            manager.call_tool("chat_companion", {"message": "hi"})
        ]

        results = await asyncio.gather(*tasks)

        # 验证所有调用都成功
        assert all(r.status == CallStatus.SUCCESS for r in results)

    @pytest.mark.asyncio
    async def test_tool_statistics(self):
        """测试工具统计"""
        manager = ToolCallManager(enable_rate_limit=False)
        await register_real_tools(manager)

        # 执行一些调用
        await manager.call_tool("code_analyzer", {"code": "test"})
        await manager.call_tool("system_monitor", {"metrics": ["cpu"]})

        # 获取统计
        stats = manager.get_stats()

        assert stats["total_calls"] >= 2
        assert stats["successful_calls"] >= 2
        assert stats["success_rate"] > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
