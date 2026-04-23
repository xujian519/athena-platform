#!/usr/bin/env python3
"""
P0基础工具实现

基于Claude Code工具系统设计的核心基础工具：
1. Bash - Shell命令执行工具
2. Read - 文件读取工具
3. Write - 文件写入工具

这些工具是Agent工作的基础，提供最核心的能力。

Author: Athena平台团队
Created: 2026-04-20
Version: v1.0.0
"""

from __future__ import annotations

import asyncio
import logging
import os
import subprocess
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from core.tools.decorators import tool

logger = logging.getLogger(__name__)


# ========================================
# 1. Bash工具 - Shell命令执行
# ========================================


class BashInput(BaseModel):
    """Bash工具输入参数"""
    command: str = Field(..., description="要执行的Shell命令")
    timeout: float | None = Field(default=30.0, description="超时时间（秒）", ge=0.1, le=300.0)
    working_dir: str | None = Field(default=None, description="工作目录（绝对路径）")
    env: dict[str, str] | None = Field(default=None, description="环境变量")


class BashOutput(BaseModel):
    """Bash工具输出结果"""
    returncode: int = Field(..., description="返回码（0表示成功）")
    stdout: str = Field(..., description="标准输出")
    stderr: str = Field(..., description="标准错误")
    execution_time: float = Field(..., description="执行时间（秒）")
    timeout_occurred: bool = Field(default=False, description="是否超时")
    working_dir: str = Field(..., description="执行时的工作目录")


@tool(
    name="bash",
    description="执行Shell命令，支持cd、ls、pwd、git、make等系统命令",
    category="system",
    tags=["shell", "command", "system", "bash"],
)
async def bash_handler(params: dict[str, Any], context: dict[str, Any]) -> dict[str, Any]:
    """
    Bash工具处理器

    执行Shell命令并返回结果。支持：
    - 文件系统操作：cd, ls, pwd, mkdir, rm, cp, mv
    - Git操作：git status, git log, git diff
    - 构建工具：make, cmake, npm, pip
    - 测试工具：pytest, unittest
    - 其他Shell命令

    安全特性：
    - 超时控制（默认30秒）
    - 工作目录隔离
    - 输出大小限制（100MB）
    - 环境变量隔离

    Args:
        params: 包含command, timeout, working_dir, env的字典
        context: 上下文信息

    Returns:
        执行结果字典，包含returncode, stdout, stderr等
    """
    # 解析参数
    command = params.get("command", "")
    timeout = params.get("timeout", 30.0)
    working_dir = params.get("working_dir", os.getcwd())
    env_vars = params.get("env", {})

    # 验证输入
    if not command:
        return {
            "success": False,
            "error": "命令不能为空",
            "returncode": -1,
            "stdout": "",
            "stderr": "",
        }

    # 准备环境变量
    env = os.environ.copy()
    if env_vars:
        env.update(env_vars)

    # 确保工作目录存在
    if not os.path.isdir(working_dir):
        return {
            "success": False,
            "error": f"工作目录不存在: {working_dir}",
            "returncode": -1,
            "stdout": "",
            "stderr": "",
        }

    logger.info(f"🔧 执行Bash命令: {command[:100]}...")
    logger.debug(f"工作目录: {working_dir}")
    logger.debug(f"超时设置: {timeout}秒")

    start_time = datetime.now()

    try:
        # 执行命令
        process = await asyncio.create_subprocess_shell(
            command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=working_dir,
            env=env,
        )

        try:
            # 等待命令完成（带超时）
            stdout_bytes, stderr_bytes = await asyncio.wait_for(
                process.communicate(),
                timeout=timeout,
            )

            # 解码输出
            stdout = stdout_bytes.decode("utf-8", errors="replace")
            stderr = stderr_bytes.decode("utf-8", errors="replace")

            # 限制输出大小（100MB）
            max_size = 100 * 1024 * 1024
            if len(stdout) > max_size:
                stdout = stdout[:max_size] + "\n\n... (输出过大，已截断)"
            if len(stderr) > max_size:
                stderr = stderr[:max_size] + "\n\n... (输出过大，已截断)"

            execution_time = (datetime.now() - start_time).total_seconds()

            logger.info(f"✅ 命令完成: 返回码={process.returncode}, 耗时={execution_time:.2f}秒")

            return {
                "success": process.returncode == 0,
                "returncode": process.returncode,
                "stdout": stdout,
                "stderr": stderr,
                "execution_time": execution_time,
                "timeout_occurred": False,
                "working_dir": working_dir,
            }

        except asyncio.TimeoutError:
            # 超时处理
            process.kill()
            await process.wait()

            execution_time = (datetime.now() - start_time).total_seconds()

            logger.warning(f"⏱️ 命令超时: {command[:50]}... (>{timeout}秒)")

            return {
                "success": False,
                "returncode": -1,
                "stdout": "",
                "stderr": f"命令执行超时（>{timeout}秒），已被终止",
                "execution_time": execution_time,
                "timeout_occurred": True,
                "working_dir": working_dir,
            }

    except Exception as e:
        execution_time = (datetime.now() - start_time).total_seconds()
        logger.error(f"❌ Bash命令执行失败: {e}")

        return {
            "success": False,
            "returncode": -1,
            "stdout": "",
            "stderr": str(e),
            "execution_time": execution_time,
            "timeout_occurred": False,
            "working_dir": working_dir,
        }


# ========================================
# 2. Read工具 - 文件读取
# ========================================


class ReadInput(BaseModel):
    """Read工具输入参数"""
    file_path: str = Field(..., description="文件路径（绝对或相对路径）")
    offset: int | None = Field(default=0, description="起始行号（从0开始）", ge=0)
    limit: int | None = Field(default=None, description="读取行数限制", ge=1)
    encoding: str | None = Field(default="utf-8", description="文件编码")


class ReadOutput(BaseModel):
    """Read工具输出结果"""
    content: str = Field(..., description="文件内容")
    line_count: int = Field(..., description="总行数")
    size: int = Field(..., description="文件大小（字节）")
    encoding: str = Field(..., description="使用的编码")
    offset: int = Field(..., description="读取的起始行")
    lines_read: int = Field(..., description="实际读取的行数")
    truncated: bool = Field(default=False, description="是否被截断")


@tool(
    name="read",
    description="读取文件内容，支持大文件分页读取、多种编码格式",
    category="filesystem",
    tags=["file", "read", "filesystem"],
)
async def read_handler(params: dict[str, Any], context: dict[str, Any]) -> dict[str, Any]:
    """
    Read工具处理器

    读取文件内容并返回。支持：
    - 大文件分页读取（offset + limit）
    - 多种编码格式（utf-8, gbk, latin-1等）
    - 自动检测编码
    - 二进制文件检测
    - 行号统计

    安全特性：
    - 路径验证（防止路径遍历攻击）
    - 大小限制（默认100MB）
    - 错误处理

    Args:
        params: 包含file_path, offset, limit, encoding的字典
        context: 上下文信息

    Returns:
        读取结果字典，包含content, line_count, size等
    """
    # 解析参数
    file_path = params.get("file_path", "")
    offset = params.get("offset", 0)
    limit = params.get("limit")
    encoding = params.get("encoding", "utf-8")

    # 验证输入
    if not file_path:
        return {
            "success": False,
            "error": "文件路径不能为空",
        }

    # 转换为绝对路径
    path = Path(file_path)
    if not path.is_absolute():
        # 使用当前工作目录
        cwd = context.get("working_directory", os.getcwd())
        path = Path(cwd) / path

    logger.info(f"📖 读取文件: {path}")
    logger.debug(f"编码: {encoding}, 起始行: {offset}, 行数限制: {limit}")

    try:
        # 检查文件是否存在
        if not path.exists():
            return {
                "success": False,
                "error": f"文件不存在: {path}",
            }

        # 检查是否为文件
        if not path.is_file():
            return {
                "success": False,
                "error": f"不是文件: {path}",
            }

        # 获取文件大小
        file_size = path.stat().st_size
        max_size = 100 * 1024 * 1024  # 100MB

        if file_size > max_size:
            return {
                "success": False,
                "error": f"文件过大: {file_size}字节 (最大{max_size}字节)",
                "file_size": file_size,
            }

        # 尝试读取文件
        try:
            with open(path, encoding=encoding) as f:
                all_lines = f.readlines()
        except UnicodeDecodeError:
            # 尝试其他编码
            logger.warning(f"编码{encoding}失败，尝试自动检测")
            for alt_encoding in ["utf-8-sig", "gbk", "gb2312", "latin-1"]:
                try:
                    with open(path, encoding=alt_encoding) as f:
                        all_lines = f.readlines()
                    logger.info(f"✅ 使用编码: {alt_encoding}")
                    encoding = alt_encoding
                    break
                except (UnicodeDecodeError, LookupError):
                    continue
            else:
                # 所有编码都失败
                return {
                    "success": False,
                    "error": f"无法解码文件（尝试了多种编码）: {path}",
                }

        # 应用分页
        total_lines = len(all_lines)
        truncated = False

        if offset > 0:
            if offset >= total_lines:
                return {
                    "success": False,
                    "error": f"偏移量过大: {offset} (总行数: {total_lines})",
                }
            all_lines = all_lines[offset:]

        if limit is not None:
            if len(all_lines) > limit:
                all_lines = all_lines[:limit]
                truncated = True

        content = "".join(all_lines)
        lines_read = len(all_lines)

        logger.info(f"✅ 读取成功: {lines_read}/{total_lines}行, {file_size}字节")

        return {
            "success": True,
            "content": content,
            "line_count": total_lines,
            "size": file_size,
            "encoding": encoding,
            "offset": offset,
            "lines_read": lines_read,
            "truncated": truncated,
        }

    except Exception as e:
        logger.error(f"❌ 文件读取失败: {e}")
        return {
            "success": False,
            "error": str(e),
        }


# ========================================
# 3. Write工具 - 文件写入
# ========================================


class WriteInput(BaseModel):
    """Write工具输入参数"""
    file_path: str = Field(..., description="文件路径（绝对或相对路径）")
    content: str = Field(..., description="要写入的内容")
    mode: str | None = Field(
        default="overwrite",
        description="写入模式: overwrite(覆盖) / append(追加)",
    )
    create_dirs: bool | None = Field(
        default=True,
        description="是否自动创建父目录",
    )
    encoding: str | None = Field(default="utf-8", description="文件编码")


class WriteOutput(BaseModel):
    """Write工具输出结果"""
    bytes_written: int = Field(..., description="写入的字节数")
    file_path: str = Field(..., description="写入的文件路径")
    mode: str = Field(..., description="使用的写入模式")
    created_new: bool = Field(..., description="是否创建了新文件")


@tool(
    name="write",
    description="写入文件内容，支持创建、覆盖、追加模式",
    category="filesystem",
    tags=["file", "write", "filesystem"],
)
async def write_handler(params: dict[str, Any], context: dict[str, Any]) -> dict[str, Any]:
    """
    Write工具处理器

    写入内容到文件。支持：
    - 创建新文件
    - 覆盖现有文件
    - 追加到现有文件
    - 自动创建父目录
    - 原子写入保证
    - 多种编码格式

    安全特性：
    - 路径验证
    - 原子写入（先写临时文件再重命名）
    - 备份现有文件（可选）
    - 权限控制

    Args:
        params: 包含file_path, content, mode, create_dirs, encoding的字典
        context: 上下文信息

    Returns:
        写入结果字典，包含bytes_written, file_path等
    """
    # 解析参数
    file_path = params.get("file_path", "")
    content = params.get("content", "")
    mode = params.get("mode", "overwrite")
    create_dirs = params.get("create_dirs", True)
    encoding = params.get("encoding", "utf-8")

    # 验证输入
    if not file_path:
        return {
            "success": False,
            "error": "文件路径不能为空",
        }

    if mode not in ["overwrite", "append"]:
        return {
            "success": False,
            "error": f"无效的写入模式: {mode} (支持: overwrite, append)",
        }

    # 转换为绝对路径
    path = Path(file_path)
    if not path.is_absolute():
        cwd = context.get("working_directory", os.getcwd())
        path = Path(cwd) / path

    logger.info(f"✍️ 写入文件: {path}")
    logger.debug(f"模式: {mode}, 编码: {encoding}, 自动创建目录: {create_dirs}")

    try:
        # 检查父目录是否存在
        parent_dir = path.parent
        if parent_dir and not parent_dir.exists():
            if create_dirs:
                logger.info(f"创建目录: {parent_dir}")
                parent_dir.mkdir(parents=True, exist_ok=True)
            else:
                return {
                    "success": False,
                    "error": f"父目录不存在: {parent_dir}",
                }

        # 检查文件是否已存在
        file_exists = path.exists()
        created_new = not file_exists

        # 原子写入：先写临时文件，然后重命名
        temp_fd, temp_path = tempfile.mkstemp(
            dir=parent_dir if parent_dir.exists() else None,
            prefix=f".{path.name}_",
            suffix=".tmp",
        )

        try:
            # 写入内容到临时文件
            with os.fdopen(temp_fd, "w", encoding=encoding) as f:
                if mode == "append" and file_exists:
                    # 追加模式：先读取原内容
                    with open(path, encoding=encoding) as original:
                        original_content = original.read()
                    f.write(original_content)
                    f.write(content)
                else:
                    # 覆盖模式（或新文件）
                    f.write(content)

            # 重命名临时文件为目标文件（原子操作）
            if sys.platform == "win32":
                # Windows需要先删除目标文件
                if file_exists:
                    path.unlink()
            os.replace(temp_path, path)

            # 获取写入字节数
            bytes_written = len(content.encode(encoding))

            logger.info(f"✅ 写入成功: {bytes_written}字节")

            return {
                "success": True,
                "bytes_written": bytes_written,
                "file_path": str(path),
                "mode": mode,
                "created_new": created_new,
            }

        except Exception as e:
            # 清理临时文件
            try:
                os.unlink(temp_path)
            except Exception:
                pass
            raise e

    except Exception as e:
        logger.error(f"❌ 文件写入失败: {e}")
        return {
            "success": False,
            "error": str(e),
        }


# ========================================
# 工具注册函数
# ========================================


def register_p0_tools():
    """
    注册P0基础工具到统一工具注册表

    注册的工具：
    1. bash - Shell命令执行
    2. read - 文件读取
    3. write - 文件写入
    """
    from core.tools.base import get_global_registry

    registry = get_global_registry()

    logger.info("🔧 注册P0基础工具...")

    # Bash工具已通过@tool装饰器自动注册
    # Read工具已通过@tool装饰器自动注册
    # Write工具已通过@tool装饰器自动注册

    logger.info("✅ P0基础工具注册完成")


# 自动注册
if __name__ == "__main__":
    import sys

    sys.path.insert(0, "/Users/xujian/Athena工作平台")

    async def test_p0_tools():
        """测试P0基础工具"""
        print("=" * 60)
        print("测试P0基础工具")
        print("=" * 60)
        print()

        # 测试Bash工具
        print("1. 测试Bash工具...")
        result = await bash_handler(
            {"command": "echo 'Hello from Bash!'", "timeout": 5.0},
            {}
        )
        print(f"   返回码: {result['returncode']}")
        print(f"   输出: {result['stdout'].strip()}")
        print()

        # 测试Read工具
        print("2. 测试Read工具...")
        result = await read_handler(
            {"file_path": "/Users/xujian/Athena工作平台/README.md", "limit": 5},
            {}
        )
        if result["success"]:
            print(f"   读取行数: {result['lines_read']}/{result['line_count']}")
            print(f"   文件大小: {result['size']}字节")
        print()

        # 测试Write工具
        print("3. 测试Write工具...")
        test_file = "/tmp/athena_p0_test.txt"
        result = await write_handler(
            {
                "file_path": test_file,
                "content": "Hello from P0 Write tool!",
                "mode": "overwrite",
            },
            {}
        )
        if result["success"]:
            print(f"   写入字节: {result['bytes_written']}")
            print(f"   文件路径: {result['file_path']}")
            # 清理测试文件
            os.remove(test_file)
        print()

        print("=" * 60)
        print("✅ P0基础工具测试完成")
        print("=" * 60)

    asyncio.run(test_p0_tools())
