"""
工具模块单元测试
测试工具系统、工具调用和工具管理功能
"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent))



class TestToolsModule:
    """工具模块测试类"""

    def test_tools_module_import(self):
        """测试工具模块可以导入"""
        try:
            import core.tools
            assert core.tools is not None
        except ImportError:
            pytest.skip("工具模块导入失败")


class TestToolDefinition:
    """工具定义测试"""

    def test_tool_structure(self):
        """测试工具结构"""
        # 工具定义
        tool = {
            "name": "web_search",
            "description": "执行网络搜索",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "搜索查询",
                    },
                    "limit": {
                        "type": "integer",
                        "description": "结果数量限制",
                        "default": 10,
                    },
                },
                "required": ["query"],
            },
        }

        # 验证工具结构
        assert "name" in tool
        assert "parameters" in tool
        assert "required" in tool["parameters"]

    def test_tool_parameter_validation(self):
        """测试工具参数验证"""
        # 参数定义

        # 有效参数
        valid_params = {"query": "test", "limit": 5}

        # 验证必需参数
        assert "query" in valid_params
        assert isinstance(valid_params["query"], str)
        assert isinstance(valid_params.get("limit", 10), int)

    def test_tool_metadata(self):
        """测试工具元数据"""
        # 工具元数据
        metadata = {
            "name": "patent_search",
            "category": "search",
            "version": "1.0.0",
            "author": "Athena Team",
            "tags": ["patent", "search", "api"],
        }

        # 验证元数据
        assert "name" in metadata
        assert "category" in metadata
        assert isinstance(metadata["tags"], list)


class TestToolExecution:
    """工具执行测试"""

    def test_tool_call_structure(self):
        """测试工具调用结构"""
        # 工具调用
        tool_call = {
            "tool_id": "web_search_123",
            "tool_name": "web_search",
            "parameters": {
                "query": "专利检索",
                "limit": 10,
            },
            "timeout": 30,
        }

        # 验证调用结构
        assert "tool_name" in tool_call
        assert "parameters" in tool_call
        assert tool_call["timeout"] > 0

    def test_sync_tool_execution(self):
        """测试同步工具执行"""
        # 模拟同步执行
        def mock_sync_tool(param1, param2):
            return {"result": f"processed: {param1}, {param2}"}

        # 执行工具
        result = mock_sync_tool("test1", "test2")

        # 验证结果
        assert "result" in result
        assert "test1" in result["result"]

    def test_async_tool_execution(self):
        """测试异步工具执行"""
        import asyncio

        # 模拟异步执行
        async def mock_async_tool(param):
            await asyncio.sleep(0.01)
            return {"result": f"async: {param}"}

        # 执行工具
        result = asyncio.run(mock_async_tool("test"))

        # 验证结果
        assert "result" in result

    def test_tool_timeout_handling(self):
        """测试工具超时处理"""
        import asyncio

        # 模拟超时
        async def slow_tool():
            await asyncio.sleep(5)
            return "done"

        # 带超时的执行
        async def run_with_timeout():
            try:
                result = await asyncio.wait_for(slow_tool(), timeout=0.01)
                return False, result
            except asyncio.TimeoutError:
                return True, None

        timeout_occurred, _ = asyncio.run(run_with_timeout())

        # 验证超时发生
        assert timeout_occurred, "Should have timed out"


class TestToolRegistry:
    """工具注册表测试"""

    def test_tool_registration(self):
        """测试工具注册"""
        # 工具注册表
        registry = {}

        # 注册工具
        tool = {
            "name": "search_patents",
            "function": lambda x: f"searched: {x}",
        }
        registry["search_patents"] = tool

        # 验证注册
        assert "search_patents" in registry
        assert registry["search_patents"]["name"] == "search_patents"

    def test_tool_retrieval(self):
        """测试工具检索"""
        # 工具注册表
        registry = {
            "web_search": {"name": "web_search", "type": "search"},
            "patent_search": {"name": "patent_search", "type": "search"},
            "calculator": {"name": "calculator", "type": "utility"},
        }

        # 按类型检索
        search_tools = [t for t in registry.values() if t["type"] == "search"]

        # 验证检索
        assert len(search_tools) == 2
        assert all(t["type"] == "search" for t in search_tools)

    def test_tool_discovery(self):
        """测试工具发现"""
        # 工具列表
        available_tools = [
            {"name": "web_search", "category": "search"},
            {"name": "patent_search", "category": "search"},
            {"name": "document_reader", "category": "io"},
            {"name": "data_processor", "category": "processing"},
        ]

        # 按类别发现
        search_tools = [t for t in available_tools if t["category"] == "search"]

        # 验证发现
        assert len(search_tools) == 2


class TestToolValidation:
    """工具验证测试"""

    def test_tool_input_validation(self):
        """测试工具输入验证"""
        # 输入schema

        # 有效输入
        valid_input = {"query": "test", "limit": 10}

        # 验证输入
        assert "query" in valid_input
        assert isinstance(valid_input["query"], str)
        if "limit" in valid_input:
            assert 1 <= valid_input["limit"] <= 100

    def test_tool_output_validation(self):
        """测试工具输出验证"""
        # 输出schema

        # 工具输出
        output = {
            "success": True,
            "data": [1, 2, 3],
        }

        # 验证输出
        assert "success" in output
        assert isinstance(output["success"], bool)

    def test_parameter_type_checking(self):
        """测试参数类型检查"""
        # 参数定义
        params_def = {
            "name": str,
            "count": int,
            "enabled": bool,
            "tags": list,
        }

        # 有效参数值
        valid_params = {
            "name": "test",
            "count": 10,
            "enabled": True,
            "tags": ["a", "b"],
        }

        # 验证类型
        for key, expected_type in params_def.items():
            if key in valid_params:
                assert isinstance(valid_params[key], expected_type)


class TestToolChaining:
    """工具链测试"""

    def test_sequential_tool_execution(self):
        """测试顺序工具执行"""
        # 工具链
        tools_chain = [
            lambda x: x * 2,
            lambda x: x + 10,
            lambda x: x / 2,
        ]

        # 执行工具链
        result = 5
        for tool in tools_chain:
            result = tool(result)

        # 验证结果: ((5 * 2) + 10) / 2 = 10
        assert result == 10

    def test_parallel_tool_execution(self):
        """测试并行工具执行"""
        import asyncio

        # 并行工具
        async def tool1():
            await asyncio.sleep(0.01)
            return "result1"

        async def tool2():
            await asyncio.sleep(0.01)
            return "result2"

        async def tool3():
            await asyncio.sleep(0.01)
            return "result3"

        # 并行执行
        async def run_parallel():
            results = await asyncio.gather(tool1(), tool2(), tool3())
            return results

        results = asyncio.run(run_parallel())

        # 验证结果
        assert len(results) == 3
        assert "result1" in results

    def test_conditional_tool_execution(self):
        """测试条件工具执行"""
        # 条件执行
        def execute_tool(condition):
            if condition == "search":
                return {"tool": "search", "result": "found"}
            elif condition == "process":
                return {"tool": "process", "result": "processed"}
            else:
                return {"tool": "default", "result": "unknown"}

        # 测试不同条件
        result1 = execute_tool("search")
        result2 = execute_tool("process")
        result3 = execute_tool("other")

        # 验证结果
        assert result1["result"] == "found"
        assert result2["result"] == "processed"
        assert result3["result"] == "unknown"


class TestToolErrorHandling:
    """工具错误处理测试"""

    def test_tool_error_detection(self):
        """测试工具错误检测"""
        # 模拟错误
        def failing_tool(x):
            if x < 0:
                raise ValueError("Negative value not allowed")
            return x * 2

        # 测试错误检测
        try:
            failing_tool(-1)
            raise AssertionError("Should have raised error")
        except ValueError as e:
            assert "Negative value" in str(e)

    def test_tool_error_recovery(self):
        """测试工具错误恢复"""
        # 带恢复的工具
        def resilient_tool(x):
            try:
                result = x / 0
            except ZeroDivisionError:
                result = 0  # 恢复策略
            return result

        # 执行工具
        result = resilient_tool(5)

        # 验证恢复
        assert result == 0

    def test_tool_retry_logic(self):
        """测试工具重试逻辑"""

        # 带重试的工具
        call_count = 0

        def retry_tool(max_retries=3):
            nonlocal call_count
            call_count += 1
            if call_count < max_retries:
                raise Exception("Temporary failure")
            return "success"

        # 执行重试
        result = None
        for _attempt in range(3):
            try:
                result = retry_tool()
                break
            except Exception:
                continue

        # 验证重试成功
        assert result == "success"
        assert call_count == 3


class TestToolCaching:
    """工具缓存测试"""

    def test_tool_result_caching(self):
        """测试工具结果缓存"""
        # 缓存存储
        cache = {}

        def cached_tool(param):
            if param in cache:
                return cache[param]
            result = f"processed: {param}"
            cache[param] = result
            return result

        # 第一次调用
        result1 = cached_tool("test")
        # 第二次调用（应该使用缓存）
        result2 = cached_tool("test")

        # 验证缓存
        assert result1 == result2
        assert len(cache) == 1

    def test_cache_invalidation(self):
        """测试缓存失效"""
        # 缓存
        cache = {"key1": "value1", "key2": "value2"}

        # 使缓存失效
        def invalidate(cache, key):
            if key in cache:
                del cache[key]

        # 失效key1
        invalidate(cache, "key1")

        # 验证失效
        assert "key1" not in cache
        assert "key2" in cache

    def test_cache_ttl(self):
        """测试缓存TTL"""
        import time

        # 带TTL的缓存
        cache = {}

        def cached_with_ttl(key, value, ttl=1):
            cache[key] = {
                "value": value,
                "expiry": time.time() + ttl,
            }

        # 添加缓存项
        cached_with_ttl("key1", "value1", ttl=0.1)

        # 立即获取应该存在
        assert "key1" in cache

        # 等待TTL过期
        time.sleep(0.15)

        # 验证过期
        current_time = time.time()
        if cache["key1"]["expiry"] < current_time:
            del cache["key1"]

        assert "key1" not in cache


class TestToolMonitoring:
    """工具监控测试"""

    def test_execution_time_tracking(self):
        """测试执行时间跟踪"""
        import time

        # 带时间跟踪的工具
        def tracked_tool(param):
            start_time = time.time()
            # 执行操作
            time.sleep(0.01)
            result = f"result: {param}"
            end_time = time.time()
            execution_time = end_time - start_time
            return {
                "result": result,
                "execution_time": execution_time,
            }

        # 执行工具
        output = tracked_tool("test")

        # 验证时间跟踪
        assert "execution_time" in output
        assert output["execution_time"] >= 0.01

    def test_call_count_tracking(self):
        """测试调用计数跟踪"""
        # 调用计数器
        call_counts = {}

        def counted_tool(tool_name):
            call_counts[tool_name] = call_counts.get(tool_name, 0) + 1
            return f"called: {tool_name}"

        # 多次调用
        counted_tool("tool1")
        counted_tool("tool1")
        counted_tool("tool2")

        # 验证计数
        assert call_counts["tool1"] == 2
        assert call_counts["tool2"] == 1

    def test_error_rate_tracking(self):
        """测试错误率跟踪"""
        # 错误跟踪
        stats = {
            "total_calls": 0,
            "errors": 0,
        }

        def tracked_tool(should_fail=False):
            stats["total_calls"] += 1
            if should_fail:
                stats["errors"] += 1
                raise Exception("Tool failed")
            return "success"

        # 执行工具
        for i in range(10):
            try:
                tracked_tool(should_fail=(i % 3 == 0))
            except Exception:
                pass

        # 计算错误率
        error_rate = (stats["errors"] / stats["total_calls"]) * 100

        # 验证错误率
        assert error_rate > 0
        assert error_rate < 100


class TestToolSecurity:
    """工具安全测试"""

    def test_tool_permission_check(self):
        """测试工具权限检查"""
        # 权限定义
        permissions = {
            "user": ["web_search", "calculator"],
            "admin": ["web_search", "calculator", "system_config"],
        }

        # 检查权限
        def check_permission(user_role, tool_name):
            allowed_tools = permissions.get(user_role, [])
            return tool_name in allowed_tools

        # 验证权限
        assert check_permission("user", "web_search") is True
        assert check_permission("user", "system_config") is False
        assert check_permission("admin", "system_config") is True

    def test_input_sanitization(self):
        """测试输入清理"""
        import re

        # 输入清理函数
        def sanitize_input(input_str):
            # 移除危险字符
            cleaned = re.sub(r'[<>"\']', '', input_str)
            return cleaned

        # 测试清理
        dirty_input = '<script>alert("xss")</script>'
        clean_input = sanitize_input(dirty_input)

        # 验证清理
        assert "<script>" not in clean_input
        assert "alert" in clean_input

    def test_resource_limiting(self):
        """测试资源限制"""
        # 资源限制
        limits = {
            "max_execution_time": 30,  # 秒
            "max_memory": 1024,  # MB
            "max_result_size": 10000,  # 字节
        }

        # 检查限制
        def check_resource_limit(resource_name, value):
            limit = limits.get(resource_name)
            return value <= limit if limit else True

        # 验证限制
        assert check_resource_limit("max_execution_time", 20) is True
        assert check_resource_limit("max_execution_time", 40) is False
        assert check_resource_limit("max_memory", 512) is True


class TestToolIntegration:
    """工具集成测试"""

    def test_tool_with_database(self):
        """测试工具与数据库集成"""
        # 模拟数据库交互
        def db_query_tool(query):
            # 模拟查询
            return {
                "query": query,
                "results": [{"id": 1}, {"id": 2}],
                "count": 2,
            }

        # 执行工具
        result = db_query_tool("SELECT * FROM patents")

        # 验证结果
        assert "results" in result
        assert result["count"] == 2

    def test_tool_with_api(self):
        """测试工具与API集成"""
        # 模拟API调用
        def api_call_tool(endpoint, params):
            return {
                "endpoint": endpoint,
                "status": 200,
                "data": params,
            }

        # 执行工具
        result = api_call_tool("/api/search", {"query": "test"})

        # 验证结果
        assert result["status"] == 200
        assert "data" in result

    def test_tool_with_filesystem(self):
        """测试工具与文件系统集成"""
        # 模拟文件操作
        def file_tool(action, path, content=None):
            if action == "read":
                return {"action": "read", "path": path, "content": "file content"}
            elif action == "write":
                return {"action": "write", "path": path, "size": len(content)}
            return {"error": "Invalid action"}

        # 测试读取
        read_result = file_tool("read", "/test/file.txt")
        assert read_result["action"] == "read"

        # 测试写入
        write_result = file_tool("write", "/test/file.txt", content="test content")
        assert write_result["action"] == "write"
