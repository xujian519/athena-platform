#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""测试工具注册"""

import sys
import asyncio

sys.path.insert(0, "/Users/xujian/Athena工作平台")

from core.tools.unified_registry import get_unified_registry
from core.tools.base import ToolDefinition, ToolCategory, ToolPriority


async def test_bash_handler(params, context):
    """测试Bash处理器"""
    return {"test": "success"}


async def test_registration():
    """测试注册"""
    registry = get_unified_registry()

    print("注册前:")
    print(f"  bash工具存在: {registry.get('bash') is not None}")
    print()

    # 注册工具
    print("注册bash工具...")
    registry.register(
        ToolDefinition(
            tool_id="bash",
            name="Bash测试",
            description="测试",
            category=ToolCategory.SYSTEM,
            priority=ToolPriority.HIGH,
            required_params=[],
            optional_params=[],
            handler=test_bash_handler,
            timeout=30.0,
        )
    )
    print("  已注册")
    print()

    # 检查是否注册成功
    print("注册后:")
    bash_tool = registry.get("bash")
    print(f"  bash工具存在: {bash_tool is not None}")
    if bash_tool:
        if hasattr(bash_tool, 'handler'):
            print(f"  有handler属性: True")
        elif callable(bash_tool):
            print(f"  可调用: True")
        else:
            print(f"  类型: {type(bash_tool)}")
    print()


if __name__ == "__main__":
    asyncio.run(test_registration())
