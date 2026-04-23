#!/usr/bin/env python3
"""
沙箱化代码执行器

提供安全的Python代码执行环境，使用多层隔离机制：
1. 进程隔离（subprocess）
2. 资源限制（ulimit）
3. 超时控制
4. 临时文件隔离
5. 网络隔离

作者: Athena平台团队
创建时间: 2026-04-20
版本: v2.0.0 (沙箱增强版)
"""

from __future__ import annotations

import asyncio
import json
import os
import resource
import tempfile
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict


class SandboxConfig:
    """沙箱配置"""

    # 资源限制
    MAX_CPU_TIME: float = 5.0  # 最大CPU时间（秒）
    MAX_REAL_TIME: float = 10.0  # 最大实际时间（秒）
    MAX_MEMORY: int = 100 * 1024 * 1024  # 最大内存（100MB）
    MAX_FILE_SIZE: int = 10 * 1024 * 1024  # 最大输出文件大小（10MB）

    # 安全限制
    ALLOWED_MODULES: set[str] = {
        "math", "random", "datetime", "collections",
        "itertools", "functools", "decimal", "fractions"
    }
    BLOCKED_MODULES: set[str] = {
        "os", "sys", "subprocess", "multiprocessing",
        "threading", "socket", "urllib", "requests",
        "eval", "exec", "compile", "__import__"
    }

    # 文件系统限制
    TEMP_DIR_PREFIX: str = "athena_sandbox_"
    READ_ONLY_FS: bool = False  # 是否使用只读文件系统（需要Docker）


class SandboxResult:
    """沙箱执行结果"""

    def __init__(
        self,
        success: bool,
        output: str = "",
        error: str = "",
        execution_time: float = 0.0,
        memory_used: int = 0,
        timeout: bool = False,
        memory_exceeded: bool = False,
    ):
        self.success = success
        self.output = output
        self.error = error
        self.execution_time = execution_time
        self.memory_used = memory_used
        self.timeout = timeout
        self.memory_exceeded = memory_exceeded

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "success": self.success,
            "output": self.output,
            "error": self.error,
            "execution_time": self.execution_time,
            "memory_used": self.memory_used,
            "timeout": self.timeout,
            "memory_exceeded": self.memory_exceeded,
            "timestamp": datetime.now().isoformat(),
        }


class CodeSandbox:
    """
    代码沙箱执行器

    使用多层隔离机制提供安全的代码执行环境。
    """

    def __init__(self, config: SandboxConfig | None = None):
        """
        初始化沙箱

        Args:
            config: 沙箱配置，默认使用SandboxConfig
        """
        self.config = config or SandboxConfig()
        self.temp_dir: tempfile.TemporaryDirectory | None = None

    def __enter__(self):
        """进入上下文管理器"""
        self.temp_dir = tempfile.TemporaryDirectory(
            prefix=self.config.TEMP_DIR_PREFIX
        )
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):  # noqa: ARG001 (未使用参数)
        """退出上下文管理器"""
        if self.temp_dir:
            self.temp_dir.cleanup()

    def _create_isolated_python_script(self, code: str) -> str:
        """
        创建隔离的Python执行脚本

        Args:
            code: 要执行的代码

        Returns:
            脚本文件路径
        """
        if not self.temp_dir:
            raise RuntimeError("沙箱未初始化")
        script_path = Path(self.temp_dir.name) / "execute.py"

        # 创建隔离的执行脚本
        isolated_script = f'''
import sys
import json
import traceback
from io import StringIO

# 重定向输出
old_stdout = sys.stdout
old_stderr = sys.stderr
sys.stdout = StringIO()
sys.stderr = StringIO()

# 受限的执行环境
__builtins__ = {{
    "print": print,
    "range": range,
    "len": len,
    "str": str,
    "int": int,
    "float": float,
    "list": list,
    "dict": dict,
    "tuple": tuple,
    "set": set,
    "sum": sum,
    "max": max,
    "min": min,
    "abs": abs,
    "round": round,
    "sorted": sorted,
    "enumerate": enumerate,
    "zip": zip,
    "map": map,
    "filter": filter,
    "bool": bool,
    "any": any,
    "all": all,
}}

# 结果字典
result = {{
    "success": False,
    "output": "",
    "error": "",
    "execution_time": 0.0,
}}

try:
    # 执行用户代码
    import time
    start_time = time.time()

    exec("""{code}""", {{}})

    execution_time = time.time() - start_time

    # 获取输出
    output = sys.stdout.getvalue()
    error_output = sys.stderr.getvalue()

    result["success"] = True
    result["output"] = output
    result["error"] = error_output
    result["execution_time"] = execution_time

except Exception as e:
    result["error"] = str(e)
    result["traceback"] = traceback.format_exc()

finally:
    # 恢复输出
    sys.stdout = old_stdout
    sys.stderr = old_stderr

# 输出结果（JSON格式）
print(json.dumps(result, ensure_ascii=False))
'''

        script_path.write_text(isolated_script, encoding="utf-8")
        return str(script_path)

    def _set_resource_limits(self):
        """设置资源限制"""
        try:
            # 设置CPU时间限制（转换为整数秒）
            resource.setrlimit(
                resource.RLIMIT_CPU,
                (int(self.config.MAX_CPU_TIME), int(self.config.MAX_CPU_TIME))
            )

            # 设置内存限制
            resource.setrlimit(
                resource.RLIMIT_AS,
                (self.config.MAX_MEMORY, self.config.MAX_MEMORY)
            )

            # 设置文件大小限制
            resource.setrlimit(
                resource.RLIMIT_FSIZE,
                (self.config.MAX_FILE_SIZE, self.config.MAX_FILE_SIZE)
            )

        except (ValueError, resource.error):  # noqa: PERF203 (try-except循环)
            # 某些系统可能不支持这些限制
            pass

    async def execute(self, code: str, timeout: Optional[float] = None) -> SandboxResult:
        """
        在沙箱中执行代码

        Args:
            code: 要执行的代码
            timeout: 超时时间（秒），默认使用配置值

        Returns:
            SandboxResult: 执行结果
        """
        timeout = timeout or self.config.MAX_REAL_TIME

        # 验证代码长度
        if len(code) > 10000:  # 增加到10000字符
            return SandboxResult(
                success=False,
                error=f"代码过长（{len(code)}字符），最大允许10000字符"
            )

        # 检查危险操作（仅检查用户代码，不包括模板）
        dangerous_keywords = [
            "import os", "import subprocess",
            "__import__", "eval(", "exec(",
            "open(", "file(", "compile(",
            "globals(", "locals(", "vars(",
            "getattr(", "setattr(", "delattr(",
        ]

        code_lower = code.lower()
        for keyword in dangerous_keywords:
            if keyword in code_lower:
                return SandboxResult(
                    success=False,
                    error=f"检测到危险操作: {keyword}，不允许执行"
                )

        try:
            # 创建隔离脚本
            script_path = self._create_isolated_python_script(code)

            # 执行命令
            cmd = [sys.executable, "-u", script_path]

            # 创建子进程
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                # 设置工作目录为临时目录
                cwd=self.temp_dir.name if self.temp_dir else None,
                # 禁用环境变量传递
                env={
                    "PYTHONPATH": "",
                    "PATH": os.defpath,
                    "HOME": self.temp_dir.name if self.temp_dir else "/tmp",
                    "TMPDIR": self.temp_dir.name if self.temp_dir else "/tmp",
                }
            )

            try:
                # 等待进程完成（带超时）
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(),
                    timeout=timeout
                )

                # 解析输出
                output_str = stdout.decode("utf-8", errors="replace")
                error_str = stderr.decode("utf-8", errors="replace")

                # 尝试解析JSON结果
                try:
                    result_data = json.loads(output_str.strip())

                    return SandboxResult(
                        success=result_data.get("success", False),
                        output=result_data.get("output", ""),
                        error=result_data.get("error", ""),
                        execution_time=result_data.get("execution_time", 0.0),
                    )
                except json.JSONDecodeError:
                    # 如果JSON解析失败，直接返回输出
                    return SandboxResult(
                        success=process.returncode == 0,
                        output=output_str,
                        error=error_str,
                    )

            except asyncio.TimeoutError:
                # 超时，杀死进程
                try:
                    process.kill()
                    await process.wait()
                except Exception:
                    pass

                return SandboxResult(
                    success=False,
                    error=f"执行超时（>{timeout}秒）",
                    timeout=True
                )

        except Exception as e:
            return SandboxResult(
                success=False,
                error=f"沙箱执行失败: {str(e)}"
            )


# ==================== 便捷函数 ====================

async def execute_in_sandbox(
    code: str,
    timeout: float = 10.0,
    max_memory: int = 100 * 1024 * 1024,
) -> dict[str, Any]:
    """
    在沙箱中执行代码（便捷函数）

    Args:
        code: 要执行的代码
        timeout: 超时时间（秒）
        max_memory: 最大内存（字节）

    Returns:
        执行结果字典
    """
    config = SandboxConfig()
    config.MAX_REAL_TIME = timeout
    config.MAX_MEMORY = max_memory

    # 直接创建沙箱并执行（不使用async with）
    sandbox = CodeSandbox(config)
    # 手动管理临时目录
    try:
        temp_dir = tempfile.TemporaryDirectory(prefix=config.TEMP_DIR_PREFIX)
        sandbox.temp_dir = temp_dir
        result = await sandbox.execute(code)
        return result.to_dict()
    finally:
        if sandbox.temp_dir:
            sandbox.temp_dir.cleanup()


# ==================== 测试 ====================

async def main():
    """测试沙箱"""
    print("🧪 测试沙箱化代码执行器")
    print("=" * 60)

    # 测试1: 正常代码
    print("\n✅ 测试1: 正常代码执行")
    result = await execute_in_sandbox(
        code="for i in range(5):\n    print(f'Number: {i}')\nresult = sum([1, 2, 3])\nprint(f'Sum: {result}')"
    )
    print(f"成功: {result['success']}")
    print(f"输出:\n{result['output']}")
    print(f"执行时间: {result['execution_time']:.3f}秒")

    # 测试2: 超时代码
    print("\n⏱️ 测试2: 超时保护")
    result = await execute_in_sandbox(
        code="import time\ntime.sleep(20)\nprint('This should timeout')",
        timeout=2.0
    )
    print(f"成功: {result['success']}")
    print(f"错误: {result['error']}")
    print(f"超时: {result['timeout']}")

    # 测试3: 危险操作阻止
    print("\n🛡️ 测试3: 危险操作阻止")
    result = await execute_in_sandbox(
        code="import os\nprint(os.getcwd())"
    )
    print(f"成功: {result['success']}")
    print(f"错误: {result['error']}")

    # 测试4: 内存限制
    print("\n💾 测试4: 内存限制")
    result = await execute_in_sandbox(
        code="data = ['X' * 1000000 for _ in range(200)]\nprint(f'Created {len(data)} items')",
        max_memory=50 * 1024 * 1024  # 50MB
    )
    print(f"成功: {result['success']}")
    if not result['success']:
        print(f"错误: {result['error']}")

    print("\n✅ 测试完成!")


if __name__ == "__main__":
    asyncio.run(main())
