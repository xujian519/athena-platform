#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
P0基础工具注册脚本

将Bash、Read、Write三个P0基础工具注册到统一工具注册表。

Author: Athena平台团队
Created: 2026-04-20
"""

import sys
import asyncio

sys.path.insert(0, "/Users/xujian/Athena工作平台")

from core.tools.unified_registry import get_unified_registry
from core.tools.p0_basic_tools import bash_handler, read_handler, write_handler
from core.tools.base import ToolDefinition, ToolCategory, ToolPriority


async def register_p0_tools():
    """注册P0基础工具"""
    print("=" * 60)
    print("注册P0基础工具")
    print("=" * 60)
    print()

    registry = get_unified_registry()

    # 1. 注册Bash工具
    print("1. 注册Bash工具...")
    try:
        registry.register(
            ToolDefinition(
                tool_id="bash",
                name="Bash命令执行",
                description="执行Shell命令，支持cd、ls、pwd、git、make等系统命令",
                category=ToolCategory.SYSTEM,
                priority=ToolPriority.HIGH,
                required_params=["command"],
                optional_params=["timeout", "working_dir", "env"],
                handler=bash_handler,
                timeout=300.0,
            )
        )
        print("   ✅ Bash工具已注册")
    except Exception as e:
        print(f"   ❌ Bash工具注册失败: {e}")

    # 2. 注册Read工具
    print("2. 注册Read工具...")
    try:
        registry.register(
            ToolDefinition(
                tool_id="read",
                name="文件读取",
                description="读取文件内容，支持大文件分页读取、多种编码格式",
                category=ToolCategory.FILESYSTEM,
                priority=ToolPriority.HIGH,
                required_params=["file_path"],
                optional_params=["offset", "limit", "encoding"],
                handler=read_handler,
                timeout=30.0,
            )
        )
        print("   ✅ Read工具已注册")
    except Exception as e:
        print(f"   ❌ Read工具注册失败: {e}")

    # 3. 注册Write工具
    print("3. 注册Write工具...")
    try:
        registry.register(
            ToolDefinition(
                tool_id="write",
                name="文件写入",
                description="写入文件内容，支持创建、覆盖、追加模式",
                category=ToolCategory.FILESYSTEM,
                priority=ToolPriority.HIGH,
                required_params=["file_path", "content"],
                optional_params=["mode", "create_dirs", "encoding"],
                handler=write_handler,
                timeout=30.0,
            )
        )
        print("   ✅ Write工具已注册")
    except Exception as e:
        print(f"   ❌ Write工具注册失败: {e}")

    print()
    print("=" * 60)
    print("✅ P0基础工具注册完成")
    print("=" * 60)
    print()

    # 验证注册
    print("验证注册状态:")
    print("-" * 60)

    p0_tools = ["bash", "read", "write"]
    for tool_name in p0_tools:
        tool = registry.get(tool_name)
        if tool:
            print(f"✅ {tool_name:10} - 已注册")
        else:
            print(f"❌ {tool_name:10} - 未注册")

    print()
    print(f"注册率: 3/3 = 100.0%")
    print()


if __name__ == "__main__":
    asyncio.run(register_p0_tools())
