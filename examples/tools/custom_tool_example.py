#!/usr/bin/env python3
"""
自定义工具开发示例

演示如何开发、注册和使用自定义工具。

作者: Athena平台团队
创建时间: 2026-04-19
版本: v1.0.0
"""

import asyncio
import time
from typing import Any

from core.tools.base import (
    ToolCapability,
    ToolCategory,
    ToolDefinition,
    ToolPerformance,
    ToolPriority,
    get_global_registry,
)
from core.tools.tool_call_manager import ToolCallManager, get_tool_manager


# ========================================
# 示例1: 简单函数工具
# ========================================

def simple_calculator(parameters: dict[str, Any], context: dict[str, Any] | None = None) -> dict[str, Any]:
    """
    简单计算器工具

    Args:
        parameters: 包含operation和两个操作数
        context: 上下文信息

    Returns:
        计算结果
    """
    operation = parameters.get("operation")
    a = parameters.get("a")
    b = parameters.get("b")

    if operation == "add":
        result = a + b
    elif operation == "subtract":
        result = a - b
    elif operation == "multiply":
        result = a * b
    elif operation == "divide":
        if b == 0:
            return {"error": "除数不能为零"}
        result = a / b
    else:
        return {"error": f"未知操作: {operation}"}

    return {
        "operation": operation,
        "operands": [a, b],
        "result": result,
    }


# ========================================
# 示例2: 异步工具
# ========================================

async def async_data_fetcher(parameters: dict[str, Any], context: dict[str, Any] | None = None) -> dict[str, Any]:
    """
    异步数据获取工具

    Args:
        parameters: 包含url和timeout
        context: 上下文信息

    Returns:
        获取的数据
    """
    url = parameters.get("url", "https://api.example.com/data")
    timeout = parameters.get("timeout", 5.0)

    # 模拟异步操作
    await asyncio.sleep(1.0)

    return {
        "url": url,
        "data": {"message": "模拟数据获取成功"},
        "fetch_time": time.time(),
    }


# ========================================
# 示例3: 带错误处理的工具
# ========================================

async def robust_file_processor(parameters: dict[str, Any], context: dict[str, Any] | None = None) -> dict[str, Any]:
    """
    健壮的文件处理工具（带错误处理）

    Args:
        parameters: 包含file_path和operation
        context: 上下文信息

    Returns:
        处理结果
    """
    file_path = parameters.get("file_path")
    operation = parameters.get("operation")

    try:
        # 参数验证
        if not file_path:
            return {"error": "文件路径不能为空"}

        if not operation:
            return {"error": "操作类型不能为空"}

        # 模拟文件操作
        await asyncio.sleep(0.5)

        if operation == "analyze":
            return {
                "file_path": file_path,
                "analysis": {
                    "size": 1024,
                    "lines": 42,
                    "encoding": "utf-8",
                },
            }
        elif operation == "validate":
            return {
                "file_path": file_path,
                "valid": True,
                "errors": [],
            }
        else:
            return {"error": f"未知操作: {operation}"}

    except Exception as e:
        return {
            "error": f"处理失败: {str(e)}",
            "file_path": file_path,
            "operation": operation,
        }


# ========================================
# 示例4: 带状态的工具
# ========================================

class StatefulCounter:
    """带状态的工具类"""

    def __init__(self):
        self.count = 0

    async def increment(self, parameters: dict[str, Any], context: dict[str, Any] | None = None) -> dict[str, Any]:
        """增加计数"""
        self.count += 1
        return {
            "count": self.count,
            "timestamp": time.time(),
        }

    async def reset(self, parameters: dict[str, Any], context: dict[str, Any] | None = None) -> dict[str, Any]:
        """重置计数"""
        old_count = self.count
        self.count = 0
        return {
            "old_count": old_count,
            "new_count": self.count,
        }


# ========================================
# 工具注册
# ========================================

async def register_custom_tools(manager: ToolCallManager):
    """注册所有自定义工具"""

    # 1. 简单计算器
    calculator_tool = ToolDefinition(
        tool_id="simple_calculator",
        name="简单计算器",
        description="执行基本的数学运算（加、减、乘、除）",
        category=ToolCategory.DATA_PROCESSING,
        priority=ToolPriority.MEDIUM,
        capability=ToolCapability(
            input_types=["number", "operation"],
            output_types=["number"],
            domains=["general"],
            task_types=["calculation"],
        ),
        implementation_type="function",
        implementation_ref="simple_calculator",
        required_params=["operation", "a", "b"],
        optional_params=[],
        handler=simple_calculator,
        timeout=5.0,
        tags={"math", "calculator", "basic"},
    )
    manager.register_tool(calculator_tool)

    # 2. 异步数据获取器
    fetcher_tool = ToolDefinition(
        tool_id="async_data_fetcher",
        name="异步数据获取器",
        description="异步获取远程数据",
        category=ToolCategory.API_INTEGRATION,
        priority=ToolPriority.HIGH,
        capability=ToolCapability(
            input_types=["url", "timeout"],
            output_types=["json"],
            domains=["web", "api"],
            task_types=["data_fetch"],
        ),
        implementation_type="function",
        implementation_ref="async_data_fetcher",
        required_params=["url"],
        optional_params=["timeout"],
        handler=async_data_fetcher,
        timeout=30.0,
        tags={"async", "api", "fetch"},
    )
    manager.register_tool(fetcher_tool)

    # 3. 健壮文件处理器
    processor_tool = ToolDefinition(
        tool_id="robust_file_processor",
        name="文件处理器",
        description="处理文件操作（分析、验证）",
        category=ToolCategory.DATA_PROCESSING,
        priority=ToolPriority.HIGH,
        capability=ToolCapability(
            input_types=["file_path", "operation"],
            output_types=["json"],
            domains=["filesystem"],
            task_types=["file_processing"],
        ),
        implementation_type="function",
        implementation_ref="robust_file_processor",
        required_params=["file_path", "operation"],
        optional_params=[],
        handler=robust_file_processor,
        timeout=10.0,
        max_retries=3,
        tags={"file", "processing", "robust"},
    )
    manager.register_tool(processor_tool)

    # 4. 带状态的计数器
    counter_instance = StatefulCounter()

    counter_tool = ToolDefinition(
        tool_id="stateful_counter",
        name="状态计数器",
        description="带状态的计数工具",
        category=ToolCategory.MONITORING,
        priority=ToolPriority.LOW,
        capability=ToolCapability(
            input_types=["operation"],
            output_types=["number"],
            domains=["state"],
            task_types=["counting"],
        ),
        implementation_type="function",
        implementation_ref="stateful_counter",
        required_params=["operation"],
        optional_params=[],
        handler=counter_instance.increment,  # 绑定实例方法
        timeout=5.0,
        tags={"state", "counter", "demo"},
    )
    manager.register_tool(counter_tool)

    print(f"✅ 已注册 {len(manager.tools)} 个自定义工具")


# ========================================
# 使用示例
# ========================================

async def example_1_simple_tool():
    """示例1: 使用简单工具"""
    print("\n" + "=" * 60)
    print("示例1: 使用简单计算器工具")
    print("=" * 60)

    manager = get_tool_manager()
    await register_custom_tools(manager)

    # 测试计算器
    operations = [
        {"operation": "add", "a": 10, "b": 5},
        {"operation": "subtract", "a": 10, "b": 5},
        {"operation": "multiply", "a": 10, "b": 5},
        {"operation": "divide", "a": 10, "b": 5},
        {"operation": "divide", "a": 10, "b": 0},  # 错误情况
    ]

    for params in operations:
        result = await manager.call_tool("simple_calculator", params)
        print(f"\n操作: {params['operation']}")
        print(f"结果: {result.result}")
        print(f"状态: {result.status.value}")


async def example_2_async_tool():
    """示例2: 使用异步工具"""
    print("\n" + "=" * 60)
    print("示例2: 使用异步数据获取工具")
    print("=" * 60)

    manager = get_tool_manager()

    # 并发调用多个异步工具
    urls = [
        "https://api.example.com/data1",
        "https://api.example.com/data2",
        "https://api.example.com/data3",
    ]

    start_time = time.time()

    tasks = [manager.call_tool("async_data_fetcher", {"url": url}) for url in urls]
    results = await asyncio.gather(*tasks)

    elapsed = time.time() - start_time

    print(f"\n并发获取 {len(urls)} 个URL")
    print(f"总耗时: {elapsed:.2f}秒")
    print(f"平均每个: {elapsed/len(urls):.2f}秒")

    for i, result in enumerate(results):
        print(f"\nURL {i+1}:")
        print(f"  状态: {result.status.value}")
        print(f"  结果: {result.result}")


async def example_3_error_handling():
    """示例3: 错误处理"""
    print("\n" + "=" * 60)
    print("示例3: 错误处理示例")
    print("=" * 60)

    manager = get_tool_manager()

    # 测试各种错误情况
    test_cases = [
        {"file_path": "", "operation": "analyze"},  # 空路径
        {"file_path": "/tmp/test.txt", "operation": ""},  # 空操作
        {"file_path": "/tmp/test.txt", "operation": "analyze"},  # 正常
        {"file_path": "/tmp/test.txt", "operation": "unknown"},  # 未知操作
    ]

    for params in test_cases:
        result = await manager.call_tool("robust_file_processor", params)
        print(f"\n参数: {params}")
        print(f"状态: {result.status.value}")
        if result.result:
            if "error" in result.result:
                print(f"错误: {result.result['error']}")
            else:
                print(f"结果: {result.result}")


async def example_4_performance_monitoring():
    """示例4: 性能监控"""
    print("\n" + "=" * 60)
    print("示例4: 性能监控")
    print("=" * 60)

    manager = get_tool_manager()

    # 多次调用工具
    print("\n执行多次工具调用...")
    for i in range(10):
        await manager.call_tool("simple_calculator", {"operation": "add", "a": i, "b": i * 2})

    # 获取统计信息
    stats = manager.get_stats()

    print("\n工具调用统计:")
    print(f"  总调用数: {stats['total_calls']}")
    print(f"  成功数: {stats['successful_calls']}")
    print(f"  失败数: {stats['failed_calls']}")
    print(f"  成功率: {stats['success_rate']:.2%}")
    print(f"  平均执行时间: {stats['avg_execution_time']:.3f}秒")

    # 获取特定工具的性能
    tool_perf = manager.get_tool_performance("simple_calculator")
    if tool_perf:
        print(f"\nsimple_calculator 性能:")
        print(f"  调用次数: {tool_perf['calls']}")
        print(f"  成功次数: {tool_perf['successes']}")
        print(f"  平均时间: {tool_perf['avg_time']:.3f}秒")


async def example_5_tool_discovery():
    """示例5: 工具发现"""
    print("\n" + "=" * 60)
    print("示例5: 工具发现和查询")
    print("=" * 60)

    manager = get_tool_manager()
    await register_custom_tools(manager)

    # 列出所有工具
    print("\n所有已注册工具:")
    for tool_name in manager.list_tools():
        tool = manager.get_tool(tool_name)
        print(f"  - {tool.name} ({tool.category.value})")
        print(f"    描述: {tool.description}")
        print(f"    优先级: {tool.priority.value}")

    # 按分类查找
    print("\n数据处理类工具:")
    registry = get_global_registry()
    data_tools = registry.find_by_category(ToolCategory.DATA_PROCESSING)
    for tool in data_tools:
        print(f"  - {tool.name}: {tool.description}")

    # 按标签查找
    print("\n带 'demo' 标签的工具:")
    demo_tools = registry.find_by_tag("demo")
    for tool in demo_tools:
        print(f"  - {tool.name}: {tool.description}")


async def main():
    """运行所有示例"""
    print("\n" + "=" * 60)
    print("自定义工具开发示例")
    print("=" * 60)

    await example_1_simple_tool()
    await example_2_async_tool()
    await example_3_error_handling()
    await example_4_performance_monitoring()
    await example_5_tool_discovery()

    print("\n" + "=" * 60)
    print("所有示例运行完成!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
