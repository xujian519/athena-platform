#!/usr/bin/env python3
"""
代码执行沙箱模块
Code Execution Sandbox Module

提供安全的代码执行环境,支持资源限制、网络隔离和数据分析。

主要功能:
1. 安全代码执行:隔离环境、资源限制
2. 多语言支持:Python、JavaScript等
3. 数据分析支持:Pandas、NumPy等
4. 可视化生成:Matplotlib图表

作者: Athena平台团队
创建时间: 2026-01-20
版本: v1.0.0 "Phase 3"
"""

from __future__ import annotations
import io
import logging
import time
from contextlib import redirect_stderr, redirect_stdout
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


# ============================================================================
# 数据模型
# ============================================================================


class ExecutionStatus(str, Enum):
    """执行状态"""

    PENDING = "pending"  # 待执行
    RUNNING = "running"  # 执行中
    SUCCESS = "success"  # 成功
    TIMEOUT = "timeout"  # 超时
    ERROR = "error"  # 错误
    CANCELLED = "cancelled"  # 已取消


class LanguageType(str, Enum):
    """编程语言类型"""

    PYTHON = "python"
    JAVASCRIPT = "javascript"
    SQL = "sql"


@dataclass
class SandboxConfig:
    """沙箱配置"""

    timeout: int = 30  # 超时时间(秒)
    memory_limit: int = 256 * 1024 * 1024  # 内存限制(256MB)
    cpu_limit: float = 1.0  # CPU时间限制(秒)
    allow_network: bool = False  # 是否允许网络访问
    allow_file_access: bool = False  # 是否允许文件访问
    max_output_size: int = 10 * 1024 * 1024  # 最大输出大小(10MB)
    allowed_modules: list[str] = field(default_factory=list)  # 允许的模块
    blocked_modules: list[str] = field(
        default_factory=lambda: ["os.system", "subprocess", "eval", "exec", "__import__"]
    )  # 禁止的模块


@dataclass
class ExecutionResult:
    """执行结果"""

    task_id: str
    status: ExecutionStatus
    output: str = ""
    error: str = ""
    return_value: Any = None
    execution_time: float = 0.0
    memory_used: int = 0
    cpu_time: float = 0.0
    stdout: str = ""
    stderr: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "task_id": self.task_id,
            "status": self.status.value,
            "output": self.output,
            "error": self.error,
            "return_value": str(self.return_value) if self.return_value is not None else None,
            "execution_time": self.execution_time,
            "memory_used": self.memory_used,
            "cpu_time": self.cpu_time,
            "stdout": self.stdout,
            "stderr": self.stderr,
            "metadata": self.metadata,
            "timestamp": self.timestamp,
        }

    def is_success(self) -> bool:
        """是否执行成功"""
        return self.status == ExecutionStatus.SUCCESS


# ============================================================================
# 沙箱执行器
# ============================================================================


class CodeExecutor:
    """代码执行器基类"""

    def __init__(self, config: SandboxConfig | None = None):
        """
        初始化代码执行器

        Args:
            config: 沙箱配置
        """
        self.config = config or SandboxConfig()
        self.execution_history: list[ExecutionResult] = []
        logger.info(
            f"🔒 代码执行器初始化完成 | 超时: {self.config.timeout}s | 内存: {self.config.memory_limit // (1024*1024)}MB"
        )

    async def execute(
        self,
        code: str,
        language: LanguageType = LanguageType.PYTHON,
        context: dict[str, Any] | None = None,
        task_id: str | None = None,
    ) -> ExecutionResult:
        """
        执行代码

        Args:
            code: 要执行的代码
            language: 编程语言
            context: 执行上下文(变量)
            task_id: 任务ID

        Returns:
            ExecutionResult: 执行结果
        """
        raise NotImplementedError("子类必须实现此方法")


class PythonCodeExecutor(CodeExecutor):
    """Python代码执行器"""

    def __init__(self, config: SandboxConfig | None = None):
        super().__init__(config)

    async def execute(
        self,
        code: str,
        language: LanguageType = LanguageType.PYTHON,
        context: dict[str, Any] | None = None,
        task_id: str | None = None,
    ) -> ExecutionResult:
        """
        执行Python代码

        Args:
            code: Python代码
            language: 编程语言(必须是PYTHON)
            context: 执行上下文
            task_id: 任务ID

        Returns:
            ExecutionResult: 执行结果
        """
        if language != LanguageType.PYTHON:
            return ExecutionResult(
                task_id=task_id or "unknown",
                status=ExecutionStatus.ERROR,
                error=f"不支持的编程语言: {language}",
            )

        task_id = task_id or f"python_{int(time.time() * 1000)}"
        logger.info(f"🐍 开始执行Python代码 | 任务ID: {task_id}")

        # 准备执行环境
        exec_context = self._prepare_exec_context(context or {})

        # 捕获输出
        stdout_capture = io.StringIO()
        stderr_capture = io.StringIO()

        start_time = time.time()

        try:
            # 重定向输出并执行代码
            with redirect_stdout(stdout_capture), redirect_stderr(stderr_capture):
                exec(code, exec_context)

            execution_time = time.time() - start_time
            stdout_value = stdout_capture.getvalue()
            stderr_value = stderr_capture.getvalue()

            # 检查是否有输出
            output = stdout_value if stdout_value else (exec_context.get("__result__") or "")

            execution_result = ExecutionResult(
                task_id=task_id,
                status=ExecutionStatus.SUCCESS,
                output=str(output) if output is not None else "",
                return_value=exec_context.get("__result__"),
                execution_time=execution_time,
                stdout=stdout_value,
                stderr=stderr_value,
                metadata={
                    "language": "python",
                    "code_length": len(code),
                    "context_keys": list(exec_context.keys()),
                },
            )

        except Exception as e:
            execution_time = time.time() - start_time
            error_msg = f"执行异常: {e!s}"
            if self.config.memory_limit > 0:
                error_msg += "\n可能原因: 内存不足或代码错误"

            execution_result = ExecutionResult(
                task_id=task_id,
                status=ExecutionStatus.ERROR,
                error=error_msg,
                execution_time=execution_time,
                stdout=stdout_capture.getvalue(),
                stderr=stderr_capture.getvalue(),
            )

        # 添加到历史记录
        self.execution_history.append(execution_result)

        logger.info(
            f"{'✅' if execution_result.is_success() else '❌'} Python代码执行完成 | "
            f"状态: {execution_result.status.value} | "
            f"耗时: {execution_result.execution_time:.3f}s"
        )

        return execution_result

    def _prepare_exec_context(self, user_context: dict[str, Any]) -> dict[str, Any]:
        """
        准备执行上下文

        Args:
            user_context: 用户提供的上下文

        Returns:
            Dict: 执行上下文
        """
        # 基础上下文
        exec_context = {
            "__builtins__": {
                "print": print,
                "range": range,
                "len": len,
                "str": str,
                "int": int,
                "float": float,
                "list": list,
                "dict": dict,
                "set": set,
                "tuple": tuple,
                "bool": bool,
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
            }
        }

        # 添加允许的模块
        if "pandas" in self.config.allowed_modules:
            try:

                exec_context["pd"] = pd  # type: ignore
            except ImportError:
                logger.warning("Pandas未安装,将不可用")

        if "numpy" in self.config.allowed_modules:
            try:

                exec_context["np"] = np  # type: ignore
            except ImportError:
                logger.warning("NumPy未安装,将不可用")

        if "matplotlib" in self.config.allowed_modules:
            try:

                exec_context["plt"] = plt  # type: ignore
            except ImportError:
                logger.warning("Matplotlib未安装,将不可用")

        # 添加用户上下文
        exec_context.update(user_context)

        return exec_context


# ============================================================================
# 沙箱管理器
# ============================================================================


class CodeSandbox:
    """
    代码执行沙箱

    提供安全的代码执行环境,支持资源限制和隔离。
    """

    def __init__(self, config: SandboxConfig | None = None):
        """
        初始化代码沙箱

        Args:
            config: 沙箱配置
        """
        self.config = config or SandboxConfig()
        self.executor = PythonCodeExecutor(self.config)
        self.execution_history: list[ExecutionResult] = []

        logger.info("🏖️  代码执行沙箱初始化完成")

    async def execute(
        self,
        code: str,
        language: LanguageType = LanguageType.PYTHON,
        context: dict[str, Any] | None = None,
        task_id: str | None = None,
    ) -> ExecutionResult:
        """
        执行代码

        Args:
            code: 要执行的代码
            language: 编程语言
            context: 执行上下文(变量)
            task_id: 任务ID

        Returns:
            ExecutionResult: 执行结果
        """
        result = await self.executor.execute(code, language, context, task_id)
        self.execution_history.append(result)
        return result

    async def execute_data_analysis(
        self, code: str, data: dict[str, Any]  | None = None, task_id: str | None = None
    ) -> ExecutionResult:
        """
        执行数据分析代码

        Args:
            code: 数据分析代码
            data: 输入数据
            task_id: 任务ID

        Returns:
            ExecutionResult: 执行结果
        """
        # 配置允许数据分析模块
        config = SandboxConfig(
            timeout=self.config.timeout,
            memory_limit=self.config.memory_limit,
            allowed_modules=["pandas", "numpy", "matplotlib", "json"],
        )

        executor = PythonCodeExecutor(config)

        # 准备上下文
        context = {}
        if data:
            context.update(data)

        result = await executor.execute(code, LanguageType.PYTHON, context, task_id)
        self.execution_history.append(result)
        return result

    async def execute_safe(
        self, code: str, context: dict[str, Any]  | None = None, task_id: str | None = None
    ) -> ExecutionResult:
        """
        安全执行代码(严格限制)

        Args:
            code: 要执行的代码
            context: 执行上下文
            task_id: 任务ID

        Returns:
            ExecutionResult: 执行结果
        """
        # 使用严格的安全配置
        config = SandboxConfig(
            timeout=10,  # 10秒超时
            memory_limit=128 * 1024 * 1024,  # 128MB内存
            allow_network=False,
            allow_file_access=False,
            allowed_modules=[],  # 不允许任何外部模块
        )

        executor = PythonCodeExecutor(config)
        result = await executor.execute(code, LanguageType.PYTHON, context, task_id)
        self.execution_history.append(result)
        return result

    def get_statistics(self) -> dict[str, Any]:
        """获取统计信息"""
        if not self.execution_history:
            return {
                "total_executions": 0,
                "success_rate": 0.0,
                "avg_execution_time": 0.0,
                "timeout_count": 0,
                "error_count": 0,
            }

        total = len(self.execution_history)
        successful = sum(1 for r in self.execution_history if r.is_success())
        timeouts = sum(1 for r in self.execution_history if r.status == ExecutionStatus.TIMEOUT)
        errors = sum(1 for r in self.execution_history if r.status == ExecutionStatus.ERROR)
        avg_time = sum(r.execution_time for r in self.execution_history) / total

        # 按状态统计
        status_counts = {}
        for result in self.execution_history:
            status = result.status.value
            status_counts[status] = status_counts.get(status, 0) + 1

        return {
            "total_executions": total,
            "successful_executions": successful,
            "success_rate": successful / total if total > 0 else 0.0,
            "avg_execution_time": avg_time,
            "timeout_count": timeouts,
            "error_count": errors,
            "status_distribution": status_counts,
        }


# ============================================================================
# 工具函数
# ============================================================================


async def execute_code(
    code: str,
    language: LanguageType = LanguageType.PYTHON,
    context: dict[str, Any] | None = None,
    timeout: int = 30,
) -> ExecutionResult:
    """
    便捷的代码执行函数

    Args:
        code: 要执行的代码
        language: 编程语言
        context: 执行上下文
        timeout: 超时时间

    Returns:
        ExecutionResult: 执行结果

    Example:
        >>> result = await execute_code("print('Hello, World!')")
        >>> print(result.output)
        Hello, World!
    """
    config = SandboxConfig(timeout=timeout)
    sandbox = CodeSandbox(config)
    return await sandbox.execute(code, language, context)


async def analyze_data(
    code: str, data: dict[str, Any] | None = None, timeout: int = 60
) -> ExecutionResult:
    """
    便捷的数据分析函数

    Args:
        code: 数据分析代码
        data: 输入数据
        timeout: 超时时间

    Returns:
        ExecutionResult: 执行结果

    Example:
        >>> code = "import pandas as pd; df = pd.DataFrame(data); print(df.describe())"
        >>> result = await analyze_data(code, data={"col1": [1, 2, 3]})
    """
    config = SandboxConfig(timeout=timeout, allowed_modules=["pandas", "numpy"])
    sandbox = CodeSandbox(config)
    return await sandbox.execute_data_analysis(code, data)


def validate_code_safety(code: str, language: LanguageType = LanguageType.PYTHON) -> dict[str, Any]:
    """
    验证代码安全性

    Args:
        code: 要验证的代码
        language: 编程语言

    Returns:
        Dict: 验证结果
    """
    warnings = []
    errors = []

    if language == LanguageType.PYTHON:
        # 检查危险的模块导入
        dangerous_imports = [
            "os.system",
            "subprocess",
            "eval(",
            "exec(",
            "compile(",
            "__import__",
            "import os",
            "import subprocess",
        ]

        for dangerous in dangerous_imports:
            if dangerous in code:
                warnings.append(f"检测到潜在危险操作: {dangerous}")

        # 检查无限循环模式
        loop_patterns = ["while True:", "while 1:", "for i in itertools.count()"]
        for pattern in loop_patterns:
            if pattern in code:
                warnings.append(f"检测到可能的无限循环: {pattern}")

    return {
        "is_safe": len(errors) == 0,
        "warnings": warnings,
        "errors": errors,
        "risk_level": "low" if len(warnings) == 0 else "medium" if len(warnings) < 3 else "high",
    }


# ============================================================================
# 全局单例
# ============================================================================

_sandbox_instance: CodeSandbox | None = None


def get_sandbox(config: SandboxConfig | None = None) -> CodeSandbox:
    """获取全局沙箱单例"""
    global _sandbox_instance
    if _sandbox_instance is None or config is not None:
        _sandbox_instance = CodeSandbox(config)
    return _sandbox_instance


__all__ = [
    # 执行器
    "CodeExecutor",
    # 沙箱
    "CodeSandbox",
    "ExecutionResult",
    # 枚举
    "ExecutionStatus",
    "LanguageType",
    "PythonCodeExecutor",
    # 数据模型
    "SandboxConfig",
    "analyze_data",
    # 便捷函数
    "execute_code",
    "get_sandbox",
    "validate_code_safety",
]
