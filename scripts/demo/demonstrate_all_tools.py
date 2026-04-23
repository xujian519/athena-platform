#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Athena平台基础工具综合演示

展示24个Claude Code基础工具的完整能力。

Author: Athena平台团队
Created: 2026-04-20
Version: v1.0.0
"""

import sys
import asyncio
import os
import tempfile

sys.path.insert(0, "/Users/xujian/Athena工作平台")

from core.tools.unified_registry import get_unified_registry
from core.tools.base import ToolDefinition, ToolCategory, ToolPriority


async def register_tools_quiet():
    """静默注册所有工具"""
    from core.tools.p0_basic_tools import bash_handler, read_handler, write_handler
    from core.tools.p1_search_edit_tools import (
        glob_handler,
        grep_handler,
        edit_handler,
        web_search_handler,
        web_fetch_handler,
    )
    from core.tools.p2_agent_task_tools import (
        agent_handler,
        task_create_handler,
        task_list_handler,
        task_get_handler,
        task_update_handler,
        task_stop_handler,
    )
    from core.tools.p3_mcp_workflow_tools import (
        mcp_tool_handler,
        list_mcp_resources_handler,
        read_mcp_resource_handler,
        enter_plan_mode_handler,
        exit_plan_mode_handler,
        enter_worktree_handler,
        exit_worktree_handler,
        tool_search_handler,
        notebook_edit_handler,
        send_message_handler,
    )

    registry = get_unified_registry()

    # P0工具
    tools = [
        ("bash", "Bash命令执行", ToolCategory.SYSTEM, ToolPriority.HIGH, ["command"], ["timeout", "working_dir", "env"], bash_handler, 300.0),
        ("read", "文件读取", ToolCategory.FILESYSTEM, ToolPriority.HIGH, ["file_path"], ["offset", "limit", "encoding"], read_handler, 30.0),
        ("write", "文件写入", ToolCategory.FILESYSTEM, ToolPriority.HIGH, ["file_path", "content"], ["mode", "create_dirs", "encoding"], write_handler, 30.0),
        # P1工具
        ("glob", "文件名模式搜索", ToolCategory.FILESYSTEM, ToolPriority.MEDIUM, ["pattern"], ["path", "limit"], glob_handler, 30.0),
        ("grep", "内容搜索", ToolCategory.FILESYSTEM, ToolPriority.MEDIUM, ["pattern"], ["path", "limit", "context"], grep_handler, 30.0),
        ("edit", "文本替换", ToolCategory.FILESYSTEM, ToolPriority.MEDIUM, ["file_path", "old_text", "new_text"], ["backup"], edit_handler, 30.0),
        ("web_search", "网络搜索", ToolCategory.WEB_SEARCH, ToolPriority.MEDIUM, ["query"], ["limit"], web_search_handler, 30.0),
        ("web_fetch", "网页抓取", ToolCategory.WEB_SEARCH, ToolPriority.MEDIUM, ["url"], ["timeout"], web_fetch_handler, 30.0),
        # P2工具
        ("agent", "启动子Agent", ToolCategory.SYSTEM, ToolPriority.HIGH, ["agent_type", "task"], ["context"], agent_handler, 300.0),
        ("task_create", "创建后台任务", ToolCategory.SYSTEM, ToolPriority.MEDIUM, ["name", "description", "command"], ["working_dir", "auto_start"], task_create_handler, 10.0),
        ("task_list", "列出所有任务", ToolCategory.SYSTEM, ToolPriority.LOW, [], [], task_list_handler, 10.0),
        ("task_get", "获取任务详情", ToolCategory.SYSTEM, ToolPriority.LOW, ["task_id"], [], task_get_handler, 10.0),
        ("task_update", "更新任务状态", ToolCategory.SYSTEM, ToolPriority.MEDIUM, ["task_id", "status"], ["result"], task_update_handler, 10.0),
        ("task_stop", "停止任务", ToolCategory.SYSTEM, ToolPriority.MEDIUM, ["task_id"], [], task_stop_handler, 10.0),
        # P3工具
        ("mcp_tool", "调用MCP服务", ToolCategory.MCP_SERVICE, ToolPriority.MEDIUM, ["server_name", "operation"], ["parameters"], mcp_tool_handler, 60.0),
        ("list_mcp_resources", "列出MCP资源", ToolCategory.MCP_SERVICE, ToolPriority.LOW, ["server_name"], [], list_mcp_resources_handler, 30.0),
        ("read_mcp_resource", "读取MCP资源", ToolCategory.MCP_SERVICE, ToolPriority.LOW, ["server_name", "resource_name"], [], read_mcp_resource_handler, 30.0),
        ("enter_plan_mode", "进入规划模式", ToolCategory.SYSTEM, ToolPriority.LOW, [], ["reason"], enter_plan_mode_handler, 10.0),
        ("exit_plan_mode", "退出规划模式", ToolCategory.SYSTEM, ToolPriority.LOW, [], [], exit_plan_mode_handler, 10.0),
        ("enter_worktree", "创建并进入git worktree", ToolCategory.SYSTEM, ToolPriority.LOW, ["branch"], ["name"], enter_worktree_handler, 30.0),
        ("exit_worktree", "退出并删除git worktree", ToolCategory.SYSTEM, ToolPriority.LOW, ["name"], ["action"], exit_worktree_handler, 30.0),
        ("tool_search", "搜索工具", ToolCategory.SYSTEM, ToolPriority.LOW, [], ["query", "category"], tool_search_handler, 10.0),
        ("notebook_edit", "编辑Jupyter笔记本", ToolCategory.FILESYSTEM, ToolPriority.LOW, ["notebook_path", "operation"], ["cell_id", "content"], notebook_edit_handler, 30.0),
        ("send_message", "Agent间消息传递", ToolCategory.SYSTEM, ToolPriority.MEDIUM, ["target_agent", "message"], [], send_message_handler, 10.0),
    ]

    for tool_data in tools:
        tool_id, name, category, priority, required, optional, handler, timeout = tool_data
        try:
            registry.register(
                ToolDefinition(
                    tool_id=tool_id,
                    name=name,
                    description=name,
                    category=category,
                    priority=priority,
                    required_params=required,
                    optional_params=optional,
                    handler=handler,
                    timeout=timeout,
                )
            )
        except:
            pass  # 工具可能已经注册


async def demonstrate_all_tools():
    """演示所有24个基础工具"""
    print("=" * 80)
    print("🚀 Athena平台基础工具综合演示")
    print("展示24个Claude Code基础工具的完整能力")
    print("=" * 80)
    print()

    # 静默注册所有工具
    await register_tools_quiet()

    registry = get_unified_registry()
    await registry.initialize()

    # ========================================
    # 第一组: P0基础工具 (3个)
    # ========================================
    print("📍 第一组: P0基础工具 - Agent工作的基础")
    print("-" * 80)
    print()

    # 1. Bash工具
    print("1️⃣ Bash工具 - Shell命令执行")
    bash_tool = registry.get("bash")
    if bash_tool and bash_tool.handler:
        result = await bash_tool.handler(
            {"command": "echo 'Hello from Bash!' && date", "timeout": 5.0},
            {}
        )
        print(f"   命令: echo 'Hello from Bash!' && date")
        print(f"   返回码: {result['returncode']}")
        print(f"   输出: {result['stdout'].strip()}")
    print()

    # 2. Read工具
    print("2️⃣ Read工具 - 文件读取")
    read_tool = registry.get("read")
    if read_tool and read_tool.handler:
        result = await read_tool.handler(
            {"file_path": "/Users/xujian/Athena工作平台/README.md", "limit": 5},
            {}
        )
        print(f"   文件: README.md")
        print(f"   总行数: {result['line_count']}")
        print(f"   读取: {result['lines_read']}行")
        print(f"   内容预览: {result['content'][:80]}...")
    print()

    # 3. Write工具
    print("3️⃣ Write工具 - 文件写入")
    write_tool = registry.get("write")
    if write_tool and write_tool.handler:
        temp_file = tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".txt")
        result = await write_tool.handler(
            {
                "file_path": temp_file.name,
                "content": "Hello from Write tool!\n这是测试内容。",
                "mode": "overwrite"
            },
            {}
        )
        print(f"   文件: {temp_file.name}")
        print(f"   写入字节: {result['bytes_written']}")
        print(f"   创建新文件: {result['created_new']}")
        os.remove(temp_file.name)
    print()

    # ========================================
    # 第二组: P1搜索编辑工具 (5个)
    # ========================================
    print("📍 第二组: P1搜索和编辑工具 - 增强Agent能力")
    print("-" * 80)
    print()

    # 4. Glob工具
    print("4️⃣ Glob工具 - 文件名模式搜索")
    glob = registry.get("glob")
    if glob:
        result = await glob.function(
            {"pattern": "*.md", "path": "/Users/xujian/Athena工作平台/docs/reports", "limit": 5},
            {}
        )
        print(f"   模式: *.md")
        print(f"   路径: docs/reports")
        print(f"   找到: {result['total_count']}个匹配文件")
        for match in result['matches'][:3]:
            print(f"      - {os.path.basename(match)}")
    print()

    # 5. Grep工具
    print("5️⃣ Grep工具 - 内容搜索")
    grep = registry.get("grep")
    if grep:
        result = await grep.function(
            {"pattern": "^# ", "path": "/Users/xujian/Athena工作平台/README.md", "limit": 3},
            {}
        )
        print(f"   模式: ^#  (搜索标题)")
        print(f"   文件: README.md")
        print(f"   找到: {result['total_count']}个匹配")
        if result['matches']:
            match = result['matches'][0]
            print(f"   示例: {os.path.basename(match['file_path'])}:{match['line_number']}")
    print()

    # 6. Edit工具
    print("6️⃣ Edit工具 - 文本替换")
    edit = registry.get("edit")
    if edit:
        temp_file = tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".txt")
        temp_file.write("Hello World\n")
        temp_file.close()

        result = await edit.function(
            {
                "file_path": temp_file.name,
                "old_text": "World",
                "new_text": "Athena"
            },
            {}
        )
        print(f"   文件: {temp_file.name}")
        print(f"   替换: World → Athena")
        print(f"   替换数: {result['replacements']}")
        print(f"   备份: {result.get('backup_path', '无')}")

        # 验证
        with open(temp_file.name, "r") as f:
            content = f.read()
        print(f"   验证: {content.strip()}")
        os.remove(temp_file.name)
        if result.get("backup_path") and os.path.exists(result["backup_path"]):
            os.remove(result["backup_path"])
    print()

    # 7. WebSearch工具
    print("7️⃣ WebSearch工具 - 网络搜索")
    web_search = registry.get("web_search")
    if web_search:
        result = await web_search.function(
            {"query": "Python asyncio", "limit": 3},
            {}
        )
        print(f"   查询: Python asyncio")
        print(f"   找到: {len(result['results'])}个结果")
        if result['results']:
            print(f"   示例: {result['results'][0]['title']}")
    print()

    # 8. WebFetch工具
    print("8️⃣ WebFetch工具 - 网页抓取")
    web_fetch = registry.get("web_fetch")
    if web_fetch:
        result = await web_fetch.function(
            {"url": "https://example.com"},
            {}
        )
        print(f"   URL: https://example.com")
        print(f"   状态: {'成功' if result['success'] else '失败'}")
        print(f"   内容长度: {len(result.get('content', ''))}字符")
    print()

    # ========================================
    # 第三组: P2 Agent协作工具 (6个)
    # ========================================
    print("📍 第三组: P2 Agent协作工具 - 多Agent协作")
    print("-" * 80)
    print()

    # 9. Agent工具
    print("9️⃣ Agent工具 - 启动子Agent")
    agent = registry.get("agent")
    if agent:
        result = await agent.function(
            {
                "agent_type": "xiaona",
                "task": "简要分析专利CN123456789A的创造性"
            },
            {}
        )
        print(f"   Agent类型: xiaona (法律专家)")
        print(f"   任务: 分析专利创造性")
        print(f"   Agent ID: {result['agent_id']}")
    print()

    # 10. TaskCreate工具
    print("🔟 TaskCreate工具 - 创建后台任务")
    task_create = registry.get("task_create")
    if task_create:
        result = await task_create.function(
            {
                "name": "示例后台任务",
                "description": "这是一个示例任务",
                "command": "echo 'Task running' && sleep 1",
                "auto_start": False
            },
            {}
        )
        print(f"   任务名称: 示例后台任务")
        print(f"   任务ID: {result['task_id']}")
        print(f"   状态: {result['status']}")
        task_id = result['task_id']
    print()

    # 11. TaskList工具
    print("1️⃣1️⃣ TaskList工具 - 列出所有任务")
    task_list = registry.get("task_list")
    if task_list:
        result = await task_list.function({}, {})
        print(f"   任务总数: {result['total_count']}")
        if result['tasks']:
            print(f"   最新任务: {result['tasks'][0]['name']}")
    print()

    # 12. TaskGet工具
    print("1️⃣2️⃣ TaskGet工具 - 获取任务详情")
    task_get = registry.get("task_get")
    if task_get:
        result = await task_get.function({"task_id": task_id}, {})
        if result['success']:
            print(f"   任务ID: {result['task']['task_id']}")
            print(f"   任务名称: {result['task']['name']}")
            print(f"   任务状态: {result['task']['status']}")
    print()

    # 13. TaskUpdate工具
    print("1️⃣3️⃣ TaskUpdate工具 - 更新任务状态")
    task_update = registry.get("task_update")
    if task_update:
        result = await task_update.function(
            {
                "task_id": task_id,
                "status": "completed",
                "result": "任务完成"
            },
            {}
        )
        print(f"   任务ID: {result['task_id']}")
        print(f"   状态更新: {result['old_status']} → {result['new_status']}")
    print()

    # 14. TaskStop工具 (跳过，因为任务已完成)
    print("1️⃣4️⃣ TaskStop工具 - 停止任务")
    print("   (跳过 - 任务已完成，无需停止)")
    print()

    # ========================================
    # 第四组: P3 MCP工作流工具 (10个)
    # ========================================
    print("📍 第四组: P3 MCP和工作流工具 - 扩展能力")
    print("-" * 80)
    print()

    # 15. MCPTool工具
    print("1️⃣5️⃣ MCPTool工具 - 调用MCP服务")
    mcp_tool = registry.get("mcp_tool")
    if mcp_tool:
        result = await mcp_tool.function(
            {
                "server_name": "academic-search",
                "operation": "search_papers",
                "parameters": {"query": "AI", "limit": 3}
            },
            {}
        )
        print(f"   服务: academic-search")
        print(f"   操作: search_papers")
        print(f"   状态: {'成功' if result['success'] else '失败'}")
    print()

    # 16. ListMcpResources工具
    print("1️⃣6️⃣ ListMcpResources工具 - 列出MCP资源")
    list_mcp = registry.get("list_mcp_resources")
    if list_mcp:
        result = await list_mcp.function(
            {"server_name": "memory"},
            {}
        )
        print(f"   服务: memory")
        print(f"   资源数量: {result['total_count']}")
    print()

    # 17. ReadMcpResource工具
    print("1️⃣7️⃣ ReadMcpResource工具 - 读取MCP资源")
    read_mcp = registry.get("read_mcp_resource")
    if read_mcp:
        result = await read_mcp.function(
            {"server_name": "memory", "resource_name": "knowledge_graph"},
            {}
        )
        print(f"   服务: memory")
        print(f"   资源: knowledge_graph")
        print(f"   状态: {'成功' if result['success'] else '失败'}")
    print()

    # 18-21. 工作流工具 (Enter/Exit PlanMode, Enter/Exit Worktree)
    print("1️⃣8️⃣-2️⃣1️⃣ 工作流工具组 - PlanMode和Worktree")
    print("   EnterPlanMode / ExitPlanMode - 规划模式控制")
    print("   EnterWorktree / ExitWorktree - Git工作树管理")
    print("   (这些工具主要在复杂工作流中使用)")
    print()

    # 22. ToolSearch工具
    print("2️⃣2️⃣ ToolSearch工具 - 搜索工具")
    tool_search = registry.get("tool_search")
    if tool_search:
        result = await tool_search.function(
            {"query": "file", "category": "filesystem"},
            {}
        )
        print(f"   搜索查询: file (分类: filesystem)")
        print(f"   匹配工具数: {result['total_count']}")
        for tool in result['matched_tools'][:3]:
            print(f"      - {tool}")
    print()

    # 23. NotebookEdit工具
    print("2️⃣3️⃣ NotebookEdit工具 - Jupyter编辑")
    notebook_edit = registry.get("notebook_edit")
    if notebook_edit:
        import json
        notebook = {
            "cells": [
                {
                    "cell_type": "code",
                    "execution_count": 1,
                    "metadata": {},
                    "outputs": [],
                    "source": "print('Hello')",
                }
            ],
            "metadata": {"language_info": {"name": "python", "version": "3.9"}},
            "nbformat": 4,
            "nbformat_minor": 4
        }

        temp_file = tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".ipynb")
        json.dump(notebook, temp_file)
        temp_file.close()

        result = await notebook_edit.function(
            {
                "notebook_path": temp_file.name,
                "operation": "insert",
                "content": "print('Athena')"
            },
            {}
        )
        print(f"   Notebook: {os.path.basename(temp_file.name)}")
        print(f"   操作: insert")
        print(f"   总cell数: {result['total_cells']}")

        os.remove(temp_file.name)
    print()

    # 24. SendMessage工具
    print("2️⃣4️⃣ SendMessage工具 - Agent消息传递")
    send_message = registry.get("send_message")
    if send_message:
        result = await send_message.function(
            {
                "target_agent": "xiaona",
                "message": "请分析这个专利"
            },
            {}
        )
        print(f"   目标Agent: xiaona")
        print(f"   消息: 请分析这个专利")
        print(f"   消息ID: {result['message_id']}")
        print(f"   状态: {result['status']}")
    print()

    # ========================================
    # 总结
    # ========================================
    print("=" * 80)
    print("✅ 所有24个基础工具演示完成")
    print("=" * 80)
    print()

    print("📊 工具统计:")
    print("-" * 80)

    all_tools = [
        ("P0基础工具", ["bash", "read", "write"]),
        ("P1搜索编辑工具", ["glob", "grep", "edit", "web_search", "web_fetch"]),
        ("P2 Agent协作工具", ["agent", "task_create", "task_list", "task_get", "task_update", "task_stop"]),
        ("P3 MCP工作流工具", ["mcp_tool", "list_mcp_resources", "read_mcp_resource",
                             "enter_plan_mode", "exit_plan_mode", "enter_worktree", "exit_worktree",
                             "tool_search", "notebook_edit", "send_message"])
    ]

    total = 0
    for category, tools in all_tools:
        registered = sum(1 for t in tools if registry.get(t))
        print(f"{category}:")
        print(f"   已注册: {registered}/{len(tools)}")
        total += registered

    print()
    print(f"总计: {total}/24 = {total/24*100:.1f}%")
    print()

    print("🎉 Athena平台现已具备完整的Claude Code基础工具能力！")
    print()

    print("📚 更多信息:")
    print("   - 完整报告: docs/reports/FINAL_ACHIEVEMENT_REPORT_20260420.md")
    print("   - 工具文档: docs/api/UNIFIED_TOOL_REGISTRY_API.md")
    print()


if __name__ == "__main__":
    asyncio.run(demonstrate_all_tools())
