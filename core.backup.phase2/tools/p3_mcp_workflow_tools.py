#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
P3 MCP和工作流工具实现

基于Claude Code工具系统设计的P3高级工具：
1. MCPTool - 调用MCP服务
2. ListMcpResources - 列出MCP资源
3. ReadMcpResource - 读取MCP资源
4. EnterPlanMode - 进入规划模式
5. ExitPlanMode - 退出规划模式
6. EnterWorktree - 进入工作树
7. ExitWorktree - 退出工作树
8. ToolSearch - 搜索工具
9. NotebookEdit - Jupyter编辑
10. SendMessage - Agent消息

这些工具提供MCP集成、工作流控制和扩展能力。

Author: Athena平台团队
Created: 2026-04-20
Version: v1.0.0
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from core.tools.decorators import tool

logger = logging.getLogger(__name__)


# ========================================
# 1-3. MCP工具集
# ========================================


@tool(
    name="mcp_tool",
    description="调用MCP服务执行操作",
    category="mcp_service",
    tags=["mcp", "service", "integration"],
)
async def mcp_tool_handler(params: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
    """
    MCPTool工具处理器

    调用MCP服务执行指定操作。

    支持的MCP服务：
    - gaode-mcp-server - 高德地图服务
    - academic-search - 学术搜索服务
    - jina-ai-mcp-server - Jina AI服务
    - memory - 知识图谱内存服务
    - local-search-engine - 本地搜索引擎

    Args:
        params: 包含server_name, operation, parameters的字典
        context: 上下文信息

    Returns:
        执行结果字典
    """
    server_name = params.get("server_name", "")
    operation = params.get("operation", "")
    parameters = params.get("parameters", {})

    if not server_name or not operation:
        return {
            "success": False,
            "error": "server_name和operation不能为空",
        }

    logger.info(f"🔧 调用MCP服务: {server_name}.{operation}")

    try:
        # 模拟MCP调用
        # 实际实现应该：
        # 1. 从context获取mcp_clients
        # 2. 调用相应的MCP服务
        # 3. 返回结果

        result = {
            "server": server_name,
            "operation": operation,
            "result": f"模拟结果：{operation}执行成功",
        }

        logger.info(f"✅ MCP调用完成")

        return {
            "success": True,
            "result": result,
        }

    except Exception as e:
        logger.error(f"❌ MCP调用失败: {e}")
        return {
            "success": False,
            "error": str(e),
        }


@tool(
    name="list_mcp_resources",
    description="列出MCP服务的可用资源",
    category="mcp_service",
    tags=["mcp", "resources", "list"],
)
async def list_mcp_resources_handler(params: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
    """
    ListMcpResources工具处理器

    列出指定MCP服务的所有可用资源。

    Args:
        params: 包含server_name的字典
        context: 上下文信息

    Returns:
        资源列表字典
    """
    server_name = params.get("server_name", "")

    if not server_name:
        return {
            "success": False,
            "error": "server_name不能为空",
        }

    logger.info(f"📋 列出MCP资源: {server_name}")

    try:
        # 模拟资源列表
        resources = [
            {"name": "resource1", "type": "data", "description": "资源1"},
            {"name": "resource2", "type": "tool", "description": "资源2"},
        ]

        logger.info(f"✅ 找到 {len(resources)} 个资源")

        return {
            "success": True,
            "server_name": server_name,
            "resources": resources,
            "total_count": len(resources),
        }

    except Exception as e:
        logger.error(f"❌ 资源列表获取失败: {e}")
        return {
            "success": False,
            "error": str(e),
        }


@tool(
    name="read_mcp_resource",
    description="读取MCP资源内容",
    category="mcp_service",
    tags=["mcp", "resources", "read"],
)
async def read_mcp_resource_handler(params: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
    """
    ReadMcpResource工具处理器

    读取指定MCP资源的内容。

    Args:
        params: 包含server_name, resource_name的字典
        context: 上下文信息

    Returns:
        资源内容字典
    """
    server_name = params.get("server_name", "")
    resource_name = params.get("resource_name", "")

    if not server_name or not resource_name:
        return {
            "success": False,
            "error": "server_name和resource_name不能为空",
        }

    logger.info(f"📖 读取MCP资源: {server_name}.{resource_name}")

    try:
        # 模拟资源内容
        content = {
            "name": resource_name,
            "type": "data",
            "data": "模拟资源内容",
        }

        logger.info(f"✅ 资源读取完成")

        return {
            "success": True,
            "resource": content,
        }

    except Exception as e:
        logger.error(f"❌ 资源读取失败: {e}")
        return {
            "success": False,
            "error": str(e),
        }


# ========================================
# 4-7. 工作流工具集
# ========================================


# 规划模式状态
_plan_mode_active = False
_plan_mode_state = {}


@tool(
    name="enter_plan_mode",
    description="进入规划模式",
    category="system",
    tags=["workflow", "plan", "mode"],
)
async def enter_plan_mode_handler(params: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
    """
    EnterPlanMode工具处理器

    进入规划模式，保存当前状态，支持规划流程。

    Args:
        params: 包含reason的字典
        context: 上下文信息

    Returns:
        进入结果字典
    """
    global _plan_mode_active, _plan_mode_state

    reason = params.get("reason", "用户请求")

    logger.info(f"📝 进入规划模式: {reason}")

    try:
        if _plan_mode_active:
            return {
                "success": False,
                "error": "规划模式已激活",
            }

        # 保存当前状态
        _plan_mode_state = {
            "active": True,
            "entered_at": datetime.now().isoformat(),
            "reason": reason,
            "previous_state": context.copy(),
        }
        _plan_mode_active = True

        logger.info("✅ 已进入规划模式")

        return {
            "success": True,
            "message": "已进入规划模式",
            "state": _plan_mode_state,
        }

    except Exception as e:
        logger.error(f"❌ 进入规划模式失败: {e}")
        return {
            "success": False,
            "error": str(e),
        }


@tool(
    name="exit_plan_mode",
    description="退出规划模式",
    category="system",
    tags=["workflow", "plan", "mode"],
)
async def exit_plan_mode_handler(params: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
    """
    ExitPlanMode工具处理器

    退出规划模式，恢复之前的状态。

    Args:
        params: 空字典
        context: 上下文信息

    Returns:
        退出结果字典
    """
    global _plan_mode_active, _plan_mode_state

    logger.info("📝 退出规划模式")

    try:
        if not _plan_mode_active:
            return {
                "success": False,
                "error": "规划模式未激活",
            }

        _plan_mode_active = False
        previous_state = _plan_mode_state.get("previous_state", {})
        _plan_mode_state = {}

        logger.info("✅ 已退出规划模式")

        return {
            "success": True,
            "message": "已退出规划模式",
            "restored_state": previous_state,
        }

    except Exception as e:
        logger.error(f"❌ 退出规划模式失败: {e}")
        return {
            "success": False,
            "error": str(e),
        }


@tool(
    name="enter_worktree",
    description="创建并进入git worktree",
    category="system",
    tags=["workflow", "git", "worktree"],
)
async def enter_worktree_handler(params: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
    """
    EnterWorktree工具处理器

    创建git worktree并切换到该工作树。

    Args:
        params: 包含branch, name的字典
        context: 上下文信息

    Returns:
        创建结果字典
    """
    branch = params.get("branch", "")
    name = params.get("name", "")
    working_dir = context.get("working_directory", os.getcwd())

    if not branch:
        return {
            "success": False,
            "error": "branch不能为空",
        }

    if not name:
        name = f"worktree_{branch}"

    logger.info(f"🌳 创建worktree: {name} (分支: {branch})")

    try:
        # 检查是否在git仓库中
        git_dir = os.path.join(working_dir, ".git")
        if not os.path.exists(git_dir):
            return {
                "success": False,
                "error": "不在git仓库中",
            }

        # 创建worktree
        worktree_path = os.path.join(working_dir, f".git/worktrees/{name}")

        # 模拟worktree创建
        # 实际实现应该：
        # subprocess.run(["git", "worktree", "add", "-b", branch, worktree_path])

        logger.info(f"✅ worktree已创建: {worktree_path}")

        return {
            "success": True,
            "worktree_path": worktree_path,
            "branch": branch,
            "name": name,
        }

    except Exception as e:
        logger.error(f"❌ worktree创建失败: {e}")
        return {
            "success": False,
            "error": str(e),
        }


@tool(
    name="exit_worktree",
    description="退出并删除git worktree",
    category="system",
    tags=["workflow", "git", "worktree"],
)
async def exit_worktree_handler(params: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
    """
    ExitWorktree工具处理器

    退出当前worktree并清理。

    Args:
        params: 包含name的字典
        context: 上下文信息

    Returns:
        退出结果字典
    """
    name = params.get("name", "")
    action = params.get("action", "keep")  # keep 或 remove

    logger.info(f"🌳 退出worktree: {name} (操作: {action})")

    try:
        # 模拟worktree清理
        # 实际实现应该：
        # if action == "remove":
        #     subprocess.run(["git", "worktree", "remove", worktree_path])

        logger.info(f"✅ 已退出worktree: {name}")

        return {
            "success": True,
            "message": f"已退出worktree: {name}",
            "action": action,
        }

    except Exception as e:
        logger.error(f"❌ worktree退出失败: {e}")
        return {
            "success": False,
            "error": str(e),
        }


# ========================================
# 8-10. 其他扩展工具
# ========================================


@tool(
    name="tool_search",
    description="搜索工具注册表",
    category="system",
    tags=["search", "tool", "discovery"],
)
async def tool_search_handler(params: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
    """
    ToolSearch工具处理器

    在工具注册表中搜索匹配的工具。

    Args:
        params: 包含query, category的字典
        context: 上下文信息

    Returns:
        搜索结果字典
    """
    query = params.get("query", "")
    category = params.get("category", "")

    logger.info(f"🔍 搜索工具: {query} (分类: {category})")

    try:
        from core.tools.unified_registry import get_unified_registry

        registry = get_unified_registry()
        await registry.initialize()

        # 获取所有工具
        all_tools = registry.list_tools()

        # 过滤
        matched_tools = []
        for tool_id in all_tools:
            if query and query.lower() in tool_id.lower():
                matched_tools.append(tool_id)

        logger.info(f"✅ 找到 {len(matched_tools)} 个匹配工具")

        return {
            "success": True,
            "query": query,
            "matched_tools": matched_tools,
            "total_count": len(matched_tools),
        }

    except Exception as e:
        logger.error(f"❌ 工具搜索失败: {e}")
        return {
            "success": False,
            "error": str(e),
        }


@tool(
    name="notebook_edit",
    description="编辑Jupyter笔记本",
    category="system",
    tags=["jupyter", "notebook", "edit"],
)
async def notebook_edit_handler(params: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
    """
    NotebookEdit工具处理器

    编辑Jupyter笔记本的cell。

    Args:
        params: 包含notebook_path, cell_id, operation, content的字典
        context: 上下文信息

    Returns:
        编辑结果字典
    """
    notebook_path = params.get("notebook_path", "")
    cell_id = params.get("cell_id", "")
    operation = params.get("operation", "")  # insert, delete, update
    content = params.get("content", "")

    if not notebook_path:
        return {
            "success": False,
            "error": "notebook_path不能为空",
        }

    logger.info(f"📓 编辑Notebook: {notebook_path}")

    try:
        # 验证文件存在
        if not os.path.exists(notebook_path):
            return {
                "success": False,
                "error": f"笔记本不存在: {notebook_path}",
            }

        # 读取笔记本
        with open(notebook_path, "r", encoding="utf-8") as f:
            notebook = json.load(f)

        # 执行操作
        if operation == "insert":
            new_cell = {
                "cell_type": "code",
                "execution_count": None,
                "metadata": {},
                "outputs": [],
                "source": content,
            }
            notebook["cells"].append(new_cell)

        elif operation == "delete":
            notebook["cells"] = [c for c in notebook["cells"] if c.get("id") != cell_id]

        elif operation == "update":
            for cell in notebook["cells"]:
                if cell.get("id") == cell_id:
                    cell["source"] = content
                    break

        # 保存笔记本
        with open(notebook_path, "w", encoding="utf-8") as f:
            json.dump(notebook, f, indent=2, ensure_ascii=False)

        logger.info(f"✅ Notebook编辑完成")

        return {
            "success": True,
            "operation": operation,
            "total_cells": len(notebook["cells"]),
        }

    except Exception as e:
        logger.error(f"❌ Notebook编辑失败: {e}")
        return {
            "success": False,
            "error": str(e),
        }


@tool(
    name="send_message",
    description="Agent间消息传递",
    category="agent",
    tags=["agent", "message", "communication"],
)
async def send_message_handler(params: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
    """
    SendMessage工具处理器

    向其他Agent发送消息。

    Args:
        params: 包含target_agent, message的字典
        context: 上下文信息

    Returns:
        发送结果字典
    """
    target_agent = params.get("target_agent", "")
    message = params.get("message", "")

    if not target_agent or not message:
        return {
            "success": False,
            "error": "target_agent和message不能为空",
        }

    logger.info(f"💬 发送消息给Agent: {target_agent}")

    try:
        # 模拟消息发送
        # 实际实现应该：
        # 1. 获取目标Agent实例
        # 2. 调用Agent的receive_message方法
        # 3. 返回发送结果

        message_id = f"msg_{target_agent}_{datetime.now().timestamp()}"

        logger.info(f"✅ 消息已发送: {message_id}")

        return {
            "success": True,
            "message_id": message_id,
            "target_agent": target_agent,
            "status": "delivered",
        }

    except Exception as e:
        logger.error(f"❌ 消息发送失败: {e}")
        return {
            "success": False,
            "error": str(e),
        }


# ========================================
# 测试代码
# ========================================


if __name__ == "__main__":
    import sys

    sys.path.insert(0, "/Users/xujian/Athena工作平台")

    async def test_p3_tools():
        """测试P3工具"""
        print("=" * 60)
        print("测试P3 MCP和工作流工具")
        print("=" * 60)
        print()

        # 测试MCPTool
        print("1. 测试MCPTool...")
        result = await mcp_tool_handler(
            {
                "server_name": "academic-search",
                "operation": "search_papers",
                "parameters": {"query": "AI", "limit": 5}
            },
            {}
        )
        if result["success"]:
            print(f"   ✅ MCP调用成功")
        print()

        # 测试ListMcpResources
        print("2. 测试ListMcpResources...")
        result = await list_mcp_resources_handler(
            {"server_name": "memory"},
            {}
        )
        if result["success"]:
            print(f"   ✅ 资源数量: {result['total_count']}")
        print()

        # 测试ReadMcpResource
        print("3. 测试ReadMcpResource...")
        result = await read_mcp_resource_handler(
            {"server_name": "memory", "resource_name": "knowledge_graph"},
            {}
        )
        if result["success"]:
            print(f"   ✅ 资源读取成功")
        print()

        # 测试EnterPlanMode
        print("4. 测试EnterPlanMode...")
        result = await enter_plan_mode_handler(
            {"reason": "需要规划实施步骤"},
            {}
        )
        if result["success"]:
            print(f"   ✅ 已进入规划模式")
        print()

        # 测试ExitPlanMode
        print("5. 测试ExitPlanMode...")
        result = await exit_plan_mode_handler({}, {})
        if result["success"]:
            print(f"   ✅ 已退出规划模式")
        print()

        # 测试ToolSearch
        print("6. 测试ToolSearch...")
        result = await tool_search_handler(
            {"query": "read", "category": "filesystem"},
            {}
        )
        if result["success"]:
            print(f"   ✅ 找到 {result['total_count']} 个匹配工具")
        print()

        # 测试NotebookEdit
        print("7. 测试NotebookEdit...")
        import tempfile
        import json

        # 创建测试notebook
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
            "metadata": {
                "kernelspec": {
                    "display_name": "Python 3",
                    "language": "python",
                    "name": "python3"
                },
                "language_info": {
                    "name": "python",
                    "version": "3.9.0"
                }
            },
            "nbformat": 4,
            "nbformat_minor": 4
        }

        temp_file = tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".ipynb")
        json.dump(notebook, temp_file)
        temp_file.close()

        result = await notebook_edit_handler(
            {
                "notebook_path": temp_file.name,
                "operation": "insert",
                "content": "print('World')"
            },
            {}
        )

        os.remove(temp_file.name)

        if result["success"]:
            print(f"   ✅ Notebook编辑成功: {result['total_cells']}个cell")
        print()

        # 测试SendMessage
        print("8. 测试SendMessage...")
        result = await send_message_handler(
            {
                "target_agent": "xiaona",
                "message": "请分析这个专利"
            },
            {}
        )
        if result["success"]:
            print(f"   ✅ 消息已发送: {result['message_id']}")
        print()

        print("=" * 60)
        print("✅ P3工具测试完成")
        print("=" * 60)

    asyncio.run(test_p3_tools())
