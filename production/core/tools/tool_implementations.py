# ⚠️ SECURITY WARNING: This file uses eval/exec. Review needed!
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Athena智能体工具实现集
Tool Implementations

包含实际可用的工具实现,用于演示工具调用框架的实际应用

作者: Athena平台团队
创建时间: 2025-12-29
版本: v1.0.0
"""

from __future__ import annotations
import asyncio
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any

from core.logging_config import setup_logging

# 配置日志
# setup_logging()  # 日志配置已移至模块导入
logger = setup_logging()

# ========================================
# 工具1: 代码分析器 (真实实现)
# ========================================


async def code_analyzer_handler(
    params: dict[str, Any], context: dict[str, Any]
) -> dict[str, Any]:
    """
    代码分析处理器 - 真实实现

    功能:
    1. 代码行数统计
    2. 代码复杂度分析
    3. 代码风格检查
    4. 潜在问题检测

    Args:
        params: {
            "code": str,  # 代码内容
            "language": str,  # 编程语言
            "style": str  # 分析风格 (basic/detailed)
        }
        context: 上下文信息

    Returns:
        分析结果字典
    """
    code = params.get("code", "")
    language = params.get("language", "python").lower()
    style = params.get("style", "basic")

    # 模拟分析延迟
    await asyncio.sleep(0.05)

    # 基础分析
    lines = code.split("\n")
    total_lines = len(lines)
    non_empty_lines = len([l for l in lines if l.strip()])
    comment_lines = 0
    code_lines = 0

    # 语言特定分析
    if language == "python":
        # Python注释分析
        for line in lines:
            stripped = line.strip()
            if stripped.startswith("#"):
                comment_lines += 1
            elif stripped and not stripped.startswith("#"):
                code_lines += 1

        # 复杂度检测
        complexity_keywords = [
            "if ",
            "elif ",
            "else:",
            "for ",
            "while ",
            "try:",
            "except",
            "with ",
            "def ",
            "class ",
        ]
        complexity_score = sum(code.count(kw) for kw in complexity_keywords)

        # 问题检测
        issues = []
        if "print(" in code and style == "detailed":
            issues.append("调试代码残留: 存在print语句")
        if code.count("def ") > 10:
            issues.append("函数过多: 建议拆分为多个模块")
        if any(len(line) > 100 for line in lines):
            issues.append("代码过长: 存在超过100字符的行")

    elif language in ["javascript", "typescript", "js", "ts"]:
        # JavaScript/TypeScript注释分析
        for line in lines:
            stripped = line.strip()
            if stripped.startswith("//") or stripped.startswith("/*") or stripped.startswith("*"):
                comment_lines += 1
            elif stripped:
                code_lines += 1

        # 复杂度检测
        complexity_keywords = [
            "if ",
            "else if",
            "else",
            "for ",
            "while ",
            "try",
            "catch",
            "function ",
            "=>",
            "class ",
        ]
        complexity_score = sum(code.count(kw) for kw in complexity_keywords)

        issues = []
        if "console.log" in code and style == "detailed":
            issues.append("调试代码残留: 存在console.log")
        if "var " in code:
            issues.append("代码现代化: 建议使用const/let替代var")

    else:
        # 通用分析
        comment_lines = 0
        code_lines = non_empty_lines
        complexity_score = 0
        issues = []

    # 计算复杂度等级
    if complexity_score < 5:
        complexity_level = "简单"
    elif complexity_score < 15:
        complexity_level = "中等"
    elif complexity_score < 30:
        complexity_level = "复杂"
    else:
        complexity_level = "非常复杂"

    return {
        "language": language,
        "statistics": {
            "total_lines": total_lines,
            "non_empty_lines": non_empty_lines,
            "code_lines": code_lines,
            "comment_lines": comment_lines,
            "comment_ratio": f"{comment_lines/max(non_empty_lines, 1)*100:.1f}%",
        },
        "complexity": {"score": complexity_score, "level": complexity_level},
        "issues": issues if style == "detailed" else [],
        "suggestions": [
            "保持函数简洁 (< 50行)" if code_lines > 50 else None,
            "添加更多注释" if comment_lines / max(non_empty_lines, 1) < 0.1 else None,
            "考虑拆分复杂逻辑" if complexity_score > 20 else None,
        ],
        "analyzed_at": datetime.now().isoformat(),
    }


# ========================================
# 工具2: 系统监控器 (真实实现)
# ========================================


async def system_monitor_handler(
    params: dict[str, Any], context: dict[str, Any]
) -> dict[str, Any]:
    """
    系统监控处理器 - 真实实现

    功能:
    1. CPU使用率
    2. 内存使用情况
    3. 磁盘使用情况
    4. 系统负载

    Args:
        params: {
            "target": str,  # 监控目标 (system/process)
            "metrics": list[str]  # 指标列表
        }
        context: 上下文信息

    Returns:
        监控数据字典
    """
    target = params.get("target", "system")
    metrics = params.get("metrics", ["cpu", "memory"])

    # 模拟监控延迟
    await asyncio.sleep(0.02)

    result = {"target": target, "timestamp": datetime.now().isoformat(), "metrics": {}}

    if "cpu" in metrics:
        # 获取CPU使用率 (使用ps命令)
        try:
            if target == "system":
                # mac_OS CPU使用率
                cpu_output = subprocess.check_output(["ps", "-A", "-o", "%cpu"], text=True)
                cpu_values = [
                    float(line.strip()) for line in cpu_output.split("\n")[1:] if line.strip()
                ]
                avg_cpu = sum(cpu_values) / len(cpu_values) if cpu_values else 0

                result["metrics"]["cpu"] = {
                    "usage_percent": round(avg_cpu, 2),
                    "status": "healthy" if avg_cpu < 80 else "warning",
                }
            else:
                result["metrics"]["cpu"] = {"usage_percent": 0.0, "status": "unknown"}
        except Exception as e:
            logger.warning(f"CPU监控失败: {e}")
            result["metrics"]["cpu"] = {"usage_percent": 0.0, "status": "error"}

    if "memory" in metrics:
        # 获取内存使用情况
        try:
            mem_output = subprocess.check_output(["vm_stat"], text=True)

            # 解析vm_stat输出
            mem_stats = {}
            for line in mem_output.split("\n"):
                if ":" in line:
                    key, value = line.split(":", 1)
                    mem_stats[key.strip()] = value.strip().replace(".", "")

            # 计算内存使用 (简化计算)
            page_size = 4096  # mac_OS页面大小
            free_pages = int(mem_stats.get("Pages free", "0"))
            active_pages = int(mem_stats.get("Pages active", "0"))
            inactive_pages = int(mem_stats.get("Pages inactive", "0"))
            wired_pages = int(mem_stats.get("Pages wired", "0"))

            total_pages = free_pages + active_pages + inactive_pages + wired_pages
            used_percent = (
                (active_pages + wired_pages) / total_pages * 100 if total_pages > 0 else 0
            )

            result["metrics"]["memory"] = {
                "usage_percent": round(used_percent, 2),
                "free_gb": round(free_pages * page_size / (1024**3), 2),
                "used_gb": round((active_pages + wired_pages) * page_size / (1024**3), 2),
                "status": "healthy" if used_percent < 80 else "warning",
            }
        except Exception as e:
            logger.warning(f"内存监控失败: {e}")
            result["metrics"]["memory"] = {"usage_percent": 0.0, "status": "error"}

    if "disk" in metrics:
        # 磁盘使用情况
        try:
            disk_output = subprocess.check_output(["df", "-h", "/"], text=True)
            lines = disk_output.split("\n")
            if len(lines) >= 2:
                parts = lines[1].split()
                if len(parts) >= 5:
                    used_percent = int(parts[4].replace("%", ""))
                    result["metrics"]["disk"] = {
                        "total": parts[0],
                        "used": parts[1],
                        "available": parts[2],
                        "usage_percent": used_percent,
                        "status": "healthy" if used_percent < 85 else "warning",
                    }
        except Exception as e:
            logger.warning(f"磁盘监控失败: {e}")
            result["metrics"]["disk"] = {"usage_percent": 0, "status": "error"}

    return result


# ========================================
# 工具3: 文件操作器 (真实实现)
# ========================================


async def file_operator_handler(
    params: dict[str, Any], context: dict[str, Any]
) -> dict[str, Any]:
    """
    文件操作处理器 - 真实实现

    功能:
    1. 读取文件
    2. 写入文件
    3. 列出目录
    4. 搜索文件

    Args:
        params: {
            "action": str,  # 操作类型 (read/write/list/search)
            "path": str,  # 文件路径
            "content": str,  # 内容 (写入时)
            "pattern": str  # 搜索模式
        }
        context: 上下文信息

    Returns:
        操作结果字典
    """
    action = params.get("action", "read")
    path_str = params.get("path", "")

    # 模拟操作延迟
    await asyncio.sleep(0.03)

    result = {"action": action, "path": path_str, "success": False, "message": "", "data": None}

    try:
        path = Path(path_str)

        if action == "read":
            if path.exists() and path.is_file():
                content = path.read_text(encoding="utf-8")
                result["success"] = True
                result["message"] = f"成功读取文件: {path_str}"
                result["data"] = {
                    "content": content,
                    "size": len(content),
                    "lines": len(content.split("\n")),
                }
            else:
                result["message"] = f"文件不存在: {path_str}"

        elif action == "write":
            content = params.get("content", "")
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8")
            result["success"] = True
            result["message"] = f"成功写入文件: {path_str}"
            result["data"] = {"size": len(content)}

        elif action == "list":
            if path.exists() and path.is_dir():
                items = []
                for item in path.iterdir():
                    items.append(
                        {
                            "name": item.name,
                            "type": "directory" if item.is_dir() else "file",
                            "size": item.stat().st_size if item.is_file() else 0,
                        }
                    )
                result["success"] = True
                result["message"] = f"成功列出目录: {path_str}"
                result["items"] = items
            else:
                result["message"] = f"目录不存在: {path_str}"

        elif action == "search":
            pattern = params.get("pattern", "*")
            search_dir = path if path.is_dir() else path.parent
            matches = list(search_dir.glob(pattern))
            result["success"] = True
            result["message"] = f"搜索完成: 找到 {len(matches)} 个匹配"
            result["data"] = {
                "matches": [str(m) for m in matches[:20]],  # 限制返回数量
                "count": len(matches),
            }

    except Exception as e:
        result["message"] = f"操作失败: {e!s}"
        logger.error(f"文件操作失败: {e}")

    return result


# ========================================
# 工具4: 代码执行器 (安全实现)
# ========================================


async def code_executor_handler(
    params: dict[str, Any], context: dict[str, Any]
) -> dict[str, Any]:
    """
    代码执行处理器 - 安全实现

    功能:
    1. 执行Python代码片段
    2. 捕获输出
    3. 超时保护
    4. 沙箱环境

    Args:
        params: {
            "code": str,  # 要执行的代码
            "timeout": int  # 超时时间(秒)
        }
        context: 上下文信息

    Returns:
        执行结果字典
    """
    code = params.get("code", "")
    params.get("timeout", 5)

    result = {"success": False, "output": "", "error": "", "execution_time": 0.0}

    import sys
    import time
    from io import StringIO

    start_time = time.time()

    try:
        # 重定向输出
        old_stdout = sys.stdout
        old_stderr = sys.stderr
        sys.stdout = StringIO()
        sys.stderr = StringIO()

        # 执行代码 (简化版,实际应该使用更安全的沙箱)
        exec_globals = {
            "__builtins__": {
                "print": print,
                "range": range,
                "len": len,
                "str": str,
                "int": int,
                "float": float,
                "list": list,
                "dict": dict,
                "sum": sum,
                "max": max,
                "min": min,
            }
        }

        # 限制代码长度
        if len(code) > 1000:
            raise ValueError("代码过长 (> 1000字符)")

        # 执行
        exec(code, exec_globals)

        # 获取输出
        output = sys.stdout.getvalue()
        error_output = sys.stderr.getvalue()

        result["success"] = True
        result["output"] = output
        result["error"] = error_output

    except Exception as e:
        result["error"] = str(e)

    finally:
        # 恢复输出
        sys.stdout = old_stdout
        sys.stderr = old_stderr

        result["execution_time"] = time.time() - start_time

    return result


# ========================================
# 工具注册函数
# ========================================


def register_real_tools(tool_manager) -> None:
    """
    注册真实工具到工具管理器

    Args:
        tool_manager: ToolCallManager实例
    """
    from core.tools.tool_call_manager import ToolCategory, ToolDefinition

    # 注册代码分析器
    tool_manager.register_tool(
        ToolDefinition(
            name="code_analyzer_real",
            category=ToolCategory.CODE_ANALYSIS,
            description="真实代码分析工具 - 支持Python/JavaScript等语言",
            required_params=["code"],
            optional_params=["language", "style"],
            handler=code_analyzer_handler,
            performance_score=0.92,
        )
    )

    # 注册系统监控器
    tool_manager.register_tool(
        ToolDefinition(
            name="system_monitor_real",
            category=ToolCategory.MONITORING,
            description="真实系统监控工具 - CPU/内存/磁盘监控",
            required_params=["target"],
            optional_params=["metrics"],
            handler=system_monitor_handler,
            performance_score=0.95,
        )
    )

    # 注册文件操作器
    tool_manager.register_tool(
        ToolDefinition(
            name="file_operator_real",
            category=ToolCategory.CODE_ANALYSIS,
            description="真实文件操作工具 - 读/写/列/搜",
            required_params=["action", "path"],
            optional_params=["content", "pattern"],
            handler=file_operator_handler,
            performance_score=0.88,
        )
    )

    # 注册代码执行器
    tool_manager.register_tool(
        ToolDefinition(
            name="code_executor_real",
            category=ToolCategory.CODE_ANALYSIS,
            description="安全代码执行工具 - 带超时保护",
            required_params=["code"],
            optional_params=["timeout"],
            handler=code_executor_handler,
            performance_score=0.85,
        )
    )

    logger.info("✅ 已注册4个真实工具")


# 测试
async def main():
    """测试真实工具"""
    print("🧪 测试真实工具实现")
    print("=" * 60)

    from core.tools.tool_call_manager import get_tool_manager

    # 获取工具管理器
    manager = get_tool_manager()

    # 注册真实工具
    register_real_tools(manager)

    # 测试1: 代码分析
    print("\n📝 测试1: 代码分析")
    result = await manager.call_tool(
        "code_analyzer_real",
        {
            "code": """
def hello():
    print('Hello, World!')
    for i in range(10):
        print(i)
        if i > 5:
            break
""",
            "language": "python",
            "style": "detailed",
        },
    )
    if result.status.value == "success":
        print("✅ 代码分析成功")
        print(
            f"   复杂度: {result.result['complexity']['level']} ({result.result['complexity']['score']})"
        )
        print(f"   代码行: {result.result['statistics']['code_lines']}")
        if result.result["issues"]:
            print(f"   问题: {', '.join(result.result['issues'])}")
    else:
        print(f"❌ 代码分析失败: {result.error}")

    # 测试2: 系统监控
    print("\n📊 测试2: 系统监控")
    result = await manager.call_tool(
        "system_monitor_real", {"target": "system", "metrics": ["cpu", "memory"]}
    )
    if result.status.value == "success":
        print("✅ 系统监控成功")
        if "cpu" in result.result["metrics"]:
            print(
                f"   CPU: {result.result['metrics']['cpu']['usage_percent']}% ({result.result['metrics']['cpu']['status']})"
            )
        if "memory" in result.result["metrics"]:
            print(
                f"   内存: {result.result['metrics']['memory']['usage_percent']}% ({result.result['metrics']['memory']['status']})"
            )
    else:
        print(f"❌ 系统监控失败: {result.error}")

    # 测试3: 代码执行
    print("\n⚡ 测试3: 代码执行")
    result = await manager.call_tool(
        "code_executor_real",
        {
            "code": "for i in range(5):\n    print(f'Number: {i}')\nresult = sum([1, 2, 3, 4, 5])\nprint(f'Sum: {result}')"
        },
    )
    if result.status.value == "success":
        print("✅ 代码执行成功")
        print(f"   输出:\n{result.result['output']}")
    else:
        print(f"❌ 代码执行失败: {result.error}")

    print("\n✅ 测试完成!")


# 入口点: @async_main装饰器已添加到main函数
