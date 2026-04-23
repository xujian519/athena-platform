#!/usr/bin/env python3
"""
验证所有24个Claude Code基础工具注册状态

Author: Athena平台团队
Created: 2026-04-20
Version: v1.0.0
"""

import asyncio
import sys

sys.path.insert(0, "/Users/xujian/Athena工作平台")

from core.tools.base import ToolCategory, ToolDefinition, ToolPriority
from core.tools.unified_registry import get_unified_registry


async def register_tools_quiet():
    """静默注册所有工具"""
    from core.tools.p0_basic_tools import bash_handler, read_handler, write_handler
    from core.tools.p1_search_edit_tools import (
        edit_handler,
        glob_handler,
        grep_handler,
        web_fetch_handler,
        web_search_handler,
    )
    from core.tools.p2_agent_task_tools import (
        agent_handler,
        task_create_handler,
        task_get_handler,
        task_list_handler,
        task_stop_handler,
        task_update_handler,
    )
    from core.tools.p3_mcp_workflow_tools import (
        enter_plan_mode_handler,
        enter_worktree_handler,
        exit_plan_mode_handler,
        exit_worktree_handler,
        list_mcp_resources_handler,
        mcp_tool_handler,
        notebook_edit_handler,
        read_mcp_resource_handler,
        send_message_handler,
        tool_search_handler,
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


async def verify_all_tools():
    """验证所有24个基础工具"""
    print("=" * 80)
    print("🔍 验证所有24个Claude Code基础工具注册状态")
    print("=" * 80)
    print()

    # 首先注册所有工具
    print("正在注册所有工具...")
    await register_tools_quiet()
    print()

    registry = get_unified_registry()
    await registry.initialize()

    # 所有24个工具
    all_tools = [
        ("P0基础工具", [
            ("bash", "Bash命令执行", "执行Shell命令，支持cd、ls、pwd、git、make等系统命令"),
            ("read", "文件读取", "读取文件内容，支持大文件分页读取、多种编码格式"),
            ("write", "文件写入", "写入文件内容，支持创建、覆盖、追加模式"),
        ]),
        ("P1搜索编辑工具", [
            ("glob", "文件名模式搜索", "使用通配符模式搜索文件名（*.py, **/*.md等）"),
            ("grep", "内容搜索", "在文件内容中搜索正则表达式匹配"),
            ("edit", "文本替换", "精确替换文件中的文本（支持多行替换）"),
            ("web_search", "网络搜索", "在互联网上搜索信息"),
            ("web_fetch", "网页抓取", "抓取网页内容并转换为Markdown"),
        ]),
        ("P2 Agent协作工具", [
            ("agent", "启动子Agent", "启动专门的子Agent处理任务"),
            ("task_create", "创建后台任务", "创建后台异步任务"),
            ("task_list", "列出所有任务", "列出所有后台任务"),
            ("task_get", "获取任务详情", "获取指定任务的详细信息"),
            ("task_update", "更新任务状态", "更新任务的状态和结果"),
            ("task_stop", "停止任务", "停止正在运行的任务"),
        ]),
        ("P3 MCP工作流工具", [
            ("mcp_tool", "调用MCP服务", "调用MCP服务执行操作"),
            ("list_mcp_resources", "列出MCP资源", "列出MCP服务的可用资源"),
            ("read_mcp_resource", "读取MCP资源", "读取MCP资源内容"),
            ("enter_plan_mode", "进入规划模式", "进入规划模式"),
            ("exit_plan_mode", "退出规划模式", "退出规划模式"),
            ("enter_worktree", "创建并进入git worktree", "创建并进入git worktree"),
            ("exit_worktree", "退出并删除git worktree", "退出并删除git worktree"),
            ("tool_search", "搜索工具", "搜索工具注册表"),
            ("notebook_edit", "编辑Jupyter笔记本", "编辑Jupyter笔记本"),
            ("send_message", "Agent间消息传递", "Agent间消息传递"),
        ])
    ]

    total_registered = 0
    total_tools = 0

    for category, tools in all_tools:
        print(f"📍 {category}")
        print("-" * 80)

        for tool_id, tool_name, tool_desc in tools:
            total_tools += 1
            tool = registry.get(tool_id)
            if tool:
                total_registered += 1
                status = "✅"
                info = "已注册"
            else:
                status = "❌"
                info = "未注册"

            print(f"{status} {tool_id:20} - {tool_name:25} - {info}")
            if tool:
                print(f"   描述: {tool_desc}")
        print()

    print("=" * 80)
    print(f"注册率: {total_registered}/{total_tools} = {total_registered/total_tools*100:.1f}%")
    print("=" * 80)
    print()

    if total_registered == total_tools:
        print("🎉 所有工具已成功注册！Athena平台现已具备完整的Claude Code基础工具能力！")
        print()
        print("📚 工具能力:")
        print("   ✅ P0基础工具 (3个) - Agent工作的基础")
        print("   ✅ P1搜索编辑工具 (5个) - 增强Agent能力")
        print("   ✅ P2 Agent协作工具 (6个) - 多Agent协作")
        print("   ✅ P3 MCP工作流工具 (10个) - 扩展能力")
        print()
    else:
        print(f"⚠️  还有 {total_tools-total_registered} 个工具未成功注册。")
        print()

    return total_registered == total_tools


if __name__ == "__main__":
    success = asyncio.run(verify_all_tools())
    sys.exit(0 if success else 1)
