#!/usr/bin/env python3
"""工具库并发测试"""

import pytest

pytestmark = pytest.mark.skip(reason="Missing required modules: ")

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from concurrent.futures import ThreadPoolExecutor, as_completed

from core.tools import (
    ToolCapability,
    ToolCategory,
    ToolDefinition,
    ToolPriority,
    ToolRegistry,
    ToolSelector,
)


class TestToolRegistryConcurrency:
    """工具注册中心并发测试"""

    def test_concurrent_register(self):
        """测试并发注册"""
        registry = ToolRegistry()

        def register_tool(tool_id):
            tool = ToolDefinition(
                tool_id=f"tool_{tool_id}",
                name=f"工具{tool_id}",
                description="并发测试工具",
                category=ToolCategory.PATENT_SEARCH,
                priority=ToolPriority.MEDIUM,
                capability=ToolCapability(
                    input_types=["text"],
                    output_types=["json"],
                    domains=["test"],
                    task_types=["test"],
                ),
            )
            return registry.register(tool)

        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(register_tool, i) for i in range(50)]
            [f.result() for f in as_completed(futures)]

        stats = registry.get_statistics()
        assert stats["total_tools"] == 50

    def test_concurrent_query(self):
        """测试并发查询"""
        registry = ToolRegistry()

        # 先注册100个工具
        for i in range(100):
            tool = ToolDefinition(
                tool_id=f"tool_{i}",
                name=f"工具{i}",
                description="测试工具",
                category=ToolCategory.PATENT_SEARCH,
                priority=ToolPriority.MEDIUM,
                capability=ToolCapability(
                    input_types=["text"],
                    output_types=["json"],
                    domains=["test"],
                    task_types=["test"],
                ),
            )
            registry.register(tool)

        def query_tools():
            results = registry.search_tools(
                category=ToolCategory.PATENT_SEARCH,
                domain="test",
            )
            return len(results)

        with ThreadPoolExecutor(max_workers=20) as executor:
            futures = [executor.submit(query_tools) for _ in range(100)]
            results = [f.result() for f in as_completed(futures)]

        assert all(r > 0 for r in results)


class TestToolSelectorConcurrency:
    """工具选择器并发测试"""

    def test_concurrent_selection(self):
        """测试并发选择"""
        registry = ToolRegistry()

        for i in range(50):
            tool = ToolDefinition(
                tool_id=f"search_tool_{i}",
                name=f"搜索工具{i}",
                description="搜索工具",
                category=ToolCategory.PATENT_SEARCH,
                priority=ToolPriority.HIGH if i < 10 else ToolPriority.MEDIUM,
                capability=ToolCapability(
                    input_types=["text"],
                    output_types=["json"],
                    domains=["patent"],
                    task_types=["search"],
                ),
            )
            registry.register(tool)

        selector = ToolSelector(registry)

        async def select_tool():
            return await selector.select_tool(
                task_type="search",
                domain="patent",
            )

        async def run_concurrent():
            tasks = [select_tool() for _ in range(50)]
            results = await asyncio.gather(*tasks)
            return results

        results = asyncio.run(run_concurrent())
        assert all(r is not None for r in results)
