"""
权限模式定义

定义多级权限模式枚举和常量。

作者: Athena平台团队
创建时间: 2026-04-20
"""
from __future__ import annotations

from enum import Enum


class PermissionMode(Enum):
    """权限模式枚举

    定义四种权限模式，控制工具调用的默认行为。
    """

    DEFAULT = "default"  # 默认模式: 未匹配规则时需要用户确认
    AUTO = "auto"  # 自动模式: 未匹配规则时自动拒绝
    BYPASS = "bypass"  # 绕过模式: 允许所有调用
    PLAN = "plan"  # 计划模式: 阻止所有写入操作（v2.0 新增）


# PLAN 模式下被视为"写入"的操作列表
# 这些操作在 PLAN 模式下会被自动拒绝
PLAN_MODE_WRITES: list[str] = [
    # 文件写入操作
    "file:write",
    "file:edit",
    "file:delete",
    "file:move",
    "file:copy",
    # Bash 执行（除非是只读命令）
    "bash:execute",
    "bash:run",
    # 数据库写入操作
    "database:write",
    "database:delete",
    "database:update",
    "database:insert",
    "database:drop",
    # 代理管理
    "agent:delete",
    "agent:stop",
    # 系统操作
    "system:shutdown",
    "system:reboot",
]

# PLAN 模式下被视为"读取"的操作列表
# 这些操作在 PLAN 模式下会被自动允许
PLAN_MODE_READS: list[str] = [
    # 文件读取操作
    "file:read",
    "glob",
    "grep",
    # 网络请求
    "web_search",
    "web_fetch",
    # 任务管理
    "task:get",
    "task:list",
    "task:output",
    # 定时任务
    "cron:list",
    # LSP（代码导航）
    "lsp:*",
]

# 危险命令黑名单
# 这些命令无论权限规则如何配置都会被拒绝
DENIED_COMMANDS: list[str] = [
    # 系统破坏命令
    "rm -rf /",
    "rm -rf /*",
    "rm -rf /.*",
    "mkfs",
    "format",  # Windows 格式化

    # 数据库破坏命令
    "DROP TABLE",
    "DROP DATABASE",
    "DELETE FROM",  # 批量删除
    "TRUNCATE TABLE",

    # 系统控制命令
    "shutdown -h now",
    "shutdown -h +0",
    "shutdown now",
    "poweroff",
    "halt",
    "reboot",
    "init 0",

    # Fork 炸弹
    ":(){ :|:& };:",
    "fork() { fork | fork & }; fork",

    # 其他危险命令
    "dd if=/dev/zero of=/dev/",  # 覆盖设备
    "chmod -R 777 /",  # 修改根目录权限
    "chown -R",  # 批量修改所有者
]

# 只读工具白名单
# 这些工具被认为是安全的，无需权限检查
READ_ONLY_TOOLS: set[str] = {
    "read_file",
    "glob",
    "grep",
    "web_fetch",
    "web_search",
    "task_get",
    "task_list",
    "task_output",
    "cron_list",
}


def is_plan_mode_write(tool_name: str) -> bool:
    """检查工具是否为 PLAN 模式下的写入操作

    Args:
        tool_name: 工具名称

    Returns:
        bool: True 如果是写入操作，False 如果是读取操作
    """
    # 检查是否在写入列表中
    for write_pattern in PLAN_MODE_WRITES:
        # 支持通配符匹配
        if "*" in write_pattern:
            import re

            regex_pattern = re.escape(write_pattern).replace(r"\*", ".*")
            if re.match(f"^{regex_pattern}$", tool_name):
                return True
        elif tool_name == write_pattern:
            return True

    # 检查是否明确在读取列表中
    for read_pattern in PLAN_MODE_READS:
        if "*" in read_pattern:
            import re

            regex_pattern = re.escape(read_pattern).replace(r"\*", ".*")
            if re.match(f"^{regex_pattern}$", tool_name):
                return False
        elif tool_name == read_pattern:
            return False

    # 默认情况：不在明确列表中，保守认为不是写入操作
    # 但需要根据工具名称启发式判断
    write_keywords = ["write", "edit", "delete", "remove", "update", "execute"]
    return any(keyword in tool_name.lower() for keyword in write_keywords)


def is_read_only_tool(tool_name: str) -> bool:
    """检查工具是否为只读工具

    Args:
        tool_name: 工具名称

    Returns:
        bool: True 如果是只读工具，False 如果不是
    """
    return tool_name in READ_ONLY_TOOLS


__all__ = [
    "PermissionMode",
    "PLAN_MODE_WRITES",
    "PLAN_MODE_READS",
    "DENIED_COMMANDS",
    "READ_ONLY_TOOLS",
    "is_plan_mode_write",
    "is_read_only_tool",
]
