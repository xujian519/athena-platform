#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
注册所有24个Claude Code基础工具

将所有P0、P1、P2、P3工具注册到统一工具注册表。

Author: Athena平台团队
Created: 2026-04-20
Version: v1.0.0
"""

import sys
import asyncio

sys.path.insert(0, "/Users/xujian/Athena工作平台")

from core.tools.unified_registry import get_unified_registry
from core.tools.base import ToolDefinition, ToolCategory, ToolPriority

# 导入所有工具处理器
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


async def register_all_tools():
    """注册所有24个基础工具"""
    print("=" * 80)
    print("注册所有24个Claude Code基础工具")
    print("=" * 80)
    print()

    registry = get_unified_registry()
    await registry.initialize()

    # ========================================
    # P0基础工具 (3个)
    # ========================================
    print("📍 P0基础工具 - Agent工作的基础")
    print("-" * 80)

    # 1. Bash工具
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

    # 2. Read工具
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

    # 3. Write工具
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

    # ========================================
    # P1搜索编辑工具 (5个)
    # ========================================
    print("📍 P1搜索和编辑工具 - 增强Agent能力")
    print("-" * 80)

    # 4. Glob工具
    print("4. 注册Glob工具...")
    try:
        registry.register(
            ToolDefinition(
                tool_id="glob",
                name="文件名模式搜索",
                description="使用通配符模式搜索文件名（*.py, **/*.md等）",
                category=ToolCategory.FILESYSTEM,
                priority=ToolPriority.MEDIUM,
                required_params=["pattern"],
                optional_params=["path", "limit"],
                handler=glob_handler,
                timeout=30.0,
            )
        )
        print("   ✅ Glob工具已注册")
    except Exception as e:
        print(f"   ❌ Glob工具注册失败: {e}")

    # 5. Grep工具
    print("5. 注册Grep工具...")
    try:
        registry.register(
            ToolDefinition(
                tool_id="grep",
                name="内容搜索",
                description="在文件内容中搜索正则表达式匹配",
                category=ToolCategory.FILESYSTEM,
                priority=ToolPriority.MEDIUM,
                required_params=["pattern"],
                optional_params=["path", "limit", "context"],
                handler=grep_handler,
                timeout=30.0,
            )
        )
        print("   ✅ Grep工具已注册")
    except Exception as e:
        print(f"   ❌ Grep工具注册失败: {e}")

    # 6. Edit工具
    print("6. 注册Edit工具...")
    try:
        registry.register(
            ToolDefinition(
                tool_id="edit",
                name="文本替换",
                description="精确替换文件中的文本（支持多行替换）",
                category=ToolCategory.FILESYSTEM,
                priority=ToolPriority.MEDIUM,
                required_params=["file_path", "old_text", "new_text"],
                optional_params=["backup"],
                handler=edit_handler,
                timeout=30.0,
            )
        )
        print("   ✅ Edit工具已注册")
    except Exception as e:
        print(f"   ❌ Edit工具注册失败: {e}")

    # 7. WebSearch工具
    print("7. 注册WebSearch工具...")
    try:
        registry.register(
            ToolDefinition(
                tool_id="web_search",
                name="网络搜索",
                description="在互联网上搜索信息",
                category=ToolCategory.WEB_SEARCH,
                priority=ToolPriority.MEDIUM,
                required_params=["query"],
                optional_params=["limit"],
                handler=web_search_handler,
                timeout=30.0,
            )
        )
        print("   ✅ WebSearch工具已注册")
    except Exception as e:
        print(f"   ❌ WebSearch工具注册失败: {e}")

    # 8. WebFetch工具
    print("8. 注册WebFetch工具...")
    try:
        registry.register(
            ToolDefinition(
                tool_id="web_fetch",
                name="网页抓取",
                description="抓取网页内容并转换为Markdown",
                category=ToolCategory.WEB_SEARCH,
                priority=ToolPriority.MEDIUM,
                required_params=["url"],
                optional_params=["timeout"],
                handler=web_fetch_handler,
                timeout=30.0,
            )
        )
        print("   ✅ WebFetch工具已注册")
    except Exception as e:
        print(f"   ❌ WebFetch工具注册失败: {e}")

    print()

    # ========================================
    # P2 Agent协作工具 (6个)
    # ========================================
    print("📍 P2 Agent协作工具 - 多Agent协作")
    print("-" * 80)

    # 9. Agent工具
    print("9. 注册Agent工具...")
    try:
        registry.register(
            ToolDefinition(
                tool_id="agent",
                name="启动子Agent",
                description="启动专门的子Agent处理任务",
                category=ToolCategory.SYSTEM,
                priority=ToolPriority.HIGH,
                required_params=["agent_type", "task"],
                optional_params=["context"],
                handler=agent_handler,
                timeout=300.0,
            )
        )
        print("   ✅ Agent工具已注册")
    except Exception as e:
        print(f"   ❌ Agent工具注册失败: {e}")

    # 10. TaskCreate工具
    print("10. 注册TaskCreate工具...")
    try:
        registry.register(
            ToolDefinition(
                tool_id="task_create",
                name="创建后台任务",
                description="创建后台异步任务",
                category=ToolCategory.SYSTEM,
                priority=ToolPriority.MEDIUM,
                required_params=["name", "description", "command"],
                optional_params=["working_dir", "auto_start"],
                handler=task_create_handler,
                timeout=10.0,
            )
        )
        print("   ✅ TaskCreate工具已注册")
    except Exception as e:
        print(f"   ❌ TaskCreate工具注册失败: {e}")

    # 11. TaskList工具
    print("11. 注册TaskList工具...")
    try:
        registry.register(
            ToolDefinition(
                tool_id="task_list",
                name="列出所有任务",
                description="列出所有后台任务",
                category=ToolCategory.SYSTEM,
                priority=ToolPriority.LOW,
                required_params=[],
                optional_params=[],
                handler=task_list_handler,
                timeout=10.0,
            )
        )
        print("   ✅ TaskList工具已注册")
    except Exception as e:
        print(f"   ❌ TaskList工具注册失败: {e}")

    # 12. TaskGet工具
    print("12. 注册TaskGet工具...")
    try:
        registry.register(
            ToolDefinition(
                tool_id="task_get",
                name="获取任务详情",
                description="获取指定任务的详细信息",
                category=ToolCategory.SYSTEM,
                priority=ToolPriority.LOW,
                required_params=["task_id"],
                optional_params=[],
                handler=task_get_handler,
                timeout=10.0,
            )
        )
        print("   ✅ TaskGet工具已注册")
    except Exception as e:
        print(f"   ❌ TaskGet工具注册失败: {e}")

    # 13. TaskUpdate工具
    print("13. 注册TaskUpdate工具...")
    try:
        registry.register(
            ToolDefinition(
                tool_id="task_update",
                name="更新任务状态",
                description="更新任务的状态和结果",
                category=ToolCategory.SYSTEM,
                priority=ToolPriority.MEDIUM,
                required_params=["task_id", "status"],
                optional_params=["result"],
                handler=task_update_handler,
                timeout=10.0,
            )
        )
        print("   ✅ TaskUpdate工具已注册")
    except Exception as e:
        print(f"   ❌ TaskUpdate工具注册失败: {e}")

    # 14. TaskStop工具
    print("14. 注册TaskStop工具...")
    try:
        registry.register(
            ToolDefinition(
                tool_id="task_stop",
                name="停止任务",
                description="停止正在运行的任务",
                category=ToolCategory.SYSTEM,
                priority=ToolPriority.MEDIUM,
                required_params=["task_id"],
                optional_params=[],
                handler=task_stop_handler,
                timeout=10.0,
            )
        )
        print("   ✅ TaskStop工具已注册")
    except Exception as e:
        print(f"   ❌ TaskStop工具注册失败: {e}")

    print()

    # ========================================
    # P3 MCP工作流工具 (10个)
    # ========================================
    print("📍 P3 MCP和工作流工具 - 扩展能力")
    print("-" * 80)

    # 15. MCPTool工具
    print("15. 注册MCPTool工具...")
    try:
        registry.register(
            ToolDefinition(
                tool_id="mcp_tool",
                name="调用MCP服务",
                description="调用MCP服务执行操作",
                category=ToolCategory.MCP_SERVICE,
                priority=ToolPriority.MEDIUM,
                required_params=["server_name", "operation"],
                optional_params=["parameters"],
                handler=mcp_tool_handler,
                timeout=60.0,
            )
        )
        print("   ✅ MCPTool工具已注册")
    except Exception as e:
        print(f"   ❌ MCPTool工具注册失败: {e}")

    # 16. ListMcpResources工具
    print("16. 注册ListMcpResources工具...")
    try:
        registry.register(
            ToolDefinition(
                tool_id="list_mcp_resources",
                name="列出MCP资源",
                description="列出MCP服务的可用资源",
                category=ToolCategory.MCP_SERVICE,
                priority=ToolPriority.LOW,
                required_params=["server_name"],
                optional_params=[],
                handler=list_mcp_resources_handler,
                timeout=30.0,
            )
        )
        print("   ✅ ListMcpResources工具已注册")
    except Exception as e:
        print(f"   ❌ ListMcpResources工具注册失败: {e}")

    # 17. ReadMcpResource工具
    print("17. 注册ReadMcpResource工具...")
    try:
        registry.register(
            ToolDefinition(
                tool_id="read_mcp_resource",
                name="读取MCP资源",
                description="读取MCP资源内容",
                category=ToolCategory.MCP_SERVICE,
                priority=ToolPriority.LOW,
                required_params=["server_name", "resource_name"],
                optional_params=[],
                handler=read_mcp_resource_handler,
                timeout=30.0,
            )
        )
        print("   ✅ ReadMcpResource工具已注册")
    except Exception as e:
        print(f"   ❌ ReadMcpResource工具注册失败: {e}")

    # 18. EnterPlanMode工具
    print("18. 注册EnterPlanMode工具...")
    try:
        registry.register(
            ToolDefinition(
                tool_id="enter_plan_mode",
                name="进入规划模式",
                description="进入规划模式",
                category=ToolCategory.SYSTEM,
                priority=ToolPriority.LOW,
                required_params=[],
                optional_params=["reason"],
                handler=enter_plan_mode_handler,
                timeout=10.0,
            )
        )
        print("   ✅ EnterPlanMode工具已注册")
    except Exception as e:
        print(f"   ❌ EnterPlanMode工具注册失败: {e}")

    # 19. ExitPlanMode工具
    print("19. 注册ExitPlanMode工具...")
    try:
        registry.register(
            ToolDefinition(
                tool_id="exit_plan_mode",
                name="退出规划模式",
                description="退出规划模式",
                category=ToolCategory.SYSTEM,
                priority=ToolPriority.LOW,
                required_params=[],
                optional_params=[],
                handler=exit_plan_mode_handler,
                timeout=10.0,
            )
        )
        print("   ✅ ExitPlanMode工具已注册")
    except Exception as e:
        print(f"   ❌ ExitPlanMode工具注册失败: {e}")

    # 20. EnterWorktree工具
    print("20. 注册EnterWorktree工具...")
    try:
        registry.register(
            ToolDefinition(
                tool_id="enter_worktree",
                name="创建并进入git worktree",
                description="创建并进入git worktree",
                category=ToolCategory.SYSTEM,
                priority=ToolPriority.LOW,
                required_params=["branch"],
                optional_params=["name"],
                handler=enter_worktree_handler,
                timeout=30.0,
            )
        )
        print("   ✅ EnterWorktree工具已注册")
    except Exception as e:
        print(f"   ❌ EnterWorktree工具注册失败: {e}")

    # 21. ExitWorktree工具
    print("21. 注册ExitWorktree工具...")
    try:
        registry.register(
            ToolDefinition(
                tool_id="exit_worktree",
                name="退出并删除git worktree",
                description="退出并删除git worktree",
                category=ToolCategory.SYSTEM,
                priority=ToolPriority.LOW,
                required_params=["name"],
                optional_params=["action"],
                handler=exit_worktree_handler,
                timeout=30.0,
            )
        )
        print("   ✅ ExitWorktree工具已注册")
    except Exception as e:
        print(f"   ❌ ExitWorktree工具注册失败: {e}")

    # 22. ToolSearch工具
    print("22. 注册ToolSearch工具...")
    try:
        registry.register(
            ToolDefinition(
                tool_id="tool_search",
                name="搜索工具",
                description="搜索工具注册表",
                category=ToolCategory.SYSTEM,
                priority=ToolPriority.LOW,
                required_params=[],
                optional_params=["query", "category"],
                handler=tool_search_handler,
                timeout=10.0,
            )
        )
        print("   ✅ ToolSearch工具已注册")
    except Exception as e:
        print(f"   ❌ ToolSearch工具注册失败: {e}")

    # 23. NotebookEdit工具
    print("23. 注册NotebookEdit工具...")
    try:
        registry.register(
            ToolDefinition(
                tool_id="notebook_edit",
                name="编辑Jupyter笔记本",
                description="编辑Jupyter笔记本",
                category=ToolCategory.FILESYSTEM,
                priority=ToolPriority.LOW,
                required_params=["notebook_path", "operation"],
                optional_params=["cell_id", "content"],
                handler=notebook_edit_handler,
                timeout=30.0,
            )
        )
        print("   ✅ NotebookEdit工具已注册")
    except Exception as e:
        print(f"   ❌ NotebookEdit工具注册失败: {e}")

    # 24. SendMessage工具
    print("24. 注册SendMessage工具...")
    try:
        registry.register(
            ToolDefinition(
                tool_id="send_message",
                name="Agent间消息传递",
                description="Agent间消息传递",
                category=ToolCategory.SYSTEM,
                priority=ToolPriority.MEDIUM,
                required_params=["target_agent", "message"],
                optional_params=[],
                handler=send_message_handler,
                timeout=10.0,
            )
        )
        print("   ✅ SendMessage工具已注册")
    except Exception as e:
        print(f"   ❌ SendMessage工具注册失败: {e}")

    print()
    print("=" * 80)
    print("✅ 所有24个基础工具注册完成")
    print("=" * 80)
    print()

    # 验证注册
    print("验证注册状态:")
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
        for tool_name in tools:
            tool = registry.get(tool_name)
            if tool:
                print(f"      ✅ {tool_name}")
            else:
                print(f"      ❌ {tool_name}")
        total += registered
        print()

    print(f"总计: {total}/24 = {total/24*100:.1f}%")
    print()

    if total == 24:
        print("🎉 所有工具已成功注册！Athena平台现已具备完整的Claude Code基础工具能力！")
    else:
        print(f"⚠️  还有 {24-total} 个工具未成功注册，请检查错误信息。")
    print()


if __name__ == "__main__":
    asyncio.run(register_all_tools())
