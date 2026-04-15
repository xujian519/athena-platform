from __future__ import annotations
"""
代码执行器

提供高级接口用于在沙盒中执行代码。
"""

import asyncio
import uuid
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from .base import (
    Language,
    Sandbox,
    SandboxBackend,
    SandboxConfig,
    SandboxManager,
)


@dataclass
class ExecutionRequest:
    """代码执行请求"""
    code: str                              # 要执行的代码
    language: Language                     # 编程语言
    input_data: str | None = None       # 标准输入
    files: dict[str, str] | None = None      # 要创建的文件 {路径: 内容}
    timeout: int | None = None          # 超时时间
    config: SandboxConfig | None = None # 沙盒配置
    backend: SandboxBackend = SandboxBackend.LOCAL  # 沙盒后端
    session_id: str | None = None       # 会话 ID（复用沙盒）

    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "code": self.code,
            "language": self.language.value,
            "input_data": self.input_data,
            "files": self.files,
            "timeout": self.timeout,
            "backend": self.backend.value,
            "session_id": self.session_id,
        }


@dataclass
class ExecutionResponse:
    """代码执行响应"""
    request_id: str                        # 请求 ID
    success: bool                          # 是否成功
    output: str                            # 标准输出
    error: str                             # 标准错误
    execution_time: float                  # 执行时间（秒）
    exit_code: int                         # 退出码
    files: list[str | None] = None      # 输出文件列表
    metadata: dict[str, Any] = None        # 额外元数据

    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "request_id": self.request_id,
            "success": self.success,
            "output": self.output,
            "error": self.error,
            "execution_time": self.execution_time,
            "exit_code": self.exit_code,
            "files": self.files,
            "metadata": self.metadata or {},
        }


class CodeExecutor:
    """代码执行器

    提供高级接口用于安全地执行代码。
    """

    def __init__(self, default_backend: SandboxBackend = SandboxBackend.LOCAL):
        self._default_backend = default_backend
        self._sandbox_manager = SandboxManager()
        self._execution_history: list[dict[str, Any]] = []
        self._max_history = 1000

    async def execute(
        self,
        request: ExecutionRequest
    ) -> ExecutionResponse:
        """执行代码

        Args:
            request: 执行请求

        Returns:
            ExecutionResponse: 执行响应
        """
        request_id = str(uuid.uuid4())
        start_time = datetime.now()

        try:
            # 获取或创建沙盒
            sandbox = await self._get_or_create_sandbox(request)

            # 创建输入文件（如果有）
            if request.files:
                for file_path, content in request.files.items():
                    await sandbox.write_file(file_path, content)

            # 执行代码
            result = await sandbox.execute_code(
                code=request.code,
                language=request.language,
                input=request.input_data
            )

            # 获取输出文件列表
            output_files = None
            if result.success:
                output_files = await sandbox.list_files()

            execution_time = (datetime.now() - start_time).total_seconds()

            # 构建响应
            response = ExecutionResponse(
                request_id=request_id,
                success=result.success,
                output=result.output,
                error=result.error,
                execution_time=execution_time,
                exit_code=result.exit_code,
                files=output_files,
                metadata={
                    "backend": request.backend.value,
                    "language": request.language.value,
                    "timestamp": start_time.isoformat(),
                    "memory_used": result.memory_used,
                    "cpu_time": result.cpu_time,
                }
            )

            # 记录历史
            self._record_execution(request, response)

            return response

        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()

            return ExecutionResponse(
                request_id=request_id,
                success=False,
                output="",
                error=str(e),
                execution_time=execution_time,
                exit_code=-1,
                metadata={"error_type": type(e).__name__}
            )

    async def execute_batch(
        self,
        requests: list[ExecutionRequest]
    ) -> list[ExecutionResponse]:
        """批量执行代码

        Args:
            requests: 执行请求列表

        Returns:
            List[ExecutionResponse]: 执行响应列表
        """
        tasks = [self.execute(request) for request in requests]
        return await asyncio.gather(*tasks)

    async def execute_code(
        self,
        code: str,
        language: str = "python",
        **kwargs
    ) -> ExecutionResponse:
        """快捷执行代码

        Args:
            code: 代码
            language: 编程语言
            **kwargs: 额外参数

        Returns:
            ExecutionResponse: 执行响应
        """
        request = ExecutionRequest(
            code=code,
            language=Language(language),
            **kwargs
        )
        return await self.execute(request)

    async def execute_python(self, code: str, **kwargs) -> ExecutionResponse:
        """执行 Python 代码

        Args:
            code: Python 代码
            **kwargs: 额外参数

        Returns:
            ExecutionResponse: 执行响应
        """
        return await self.execute_code(code, "python", **kwargs)

    async def execute_javascript(self, code: str, **kwargs) -> ExecutionResponse:
        """执行 JavaScript 代码

        Args:
            code: JavaScript 代码
            **kwargs: 额外参数

        Returns:
            ExecutionResponse: 执行响应
        """
        return await self.execute_code(code, "javascript", **kwargs)

    async def execute_shell(self, code: str, **kwargs) -> ExecutionResponse:
        """执行 Shell 代码

        Args:
            code: Shell 代码
            **kwargs: 额外参数

        Returns:
            ExecutionResponse: 执行响应
        """
        return await self.execute_code(code, "bash", **kwargs)

    async def _get_or_create_sandbox(self, request: ExecutionRequest) -> Sandbox:
        """获取或创建沙盒"""
        # 如果指定了会话 ID，尝试复用沙盒
        if request.session_id:
            sandbox = await self._sandbox_manager.get_sandbox(request.session_id)
            if sandbox:
                return sandbox

        # 创建新沙盒
        config = request.config or SandboxConfig()
        backend = request.backend or self._default_backend

        sandbox = await self._sandbox_manager.create_sandbox(
            backend=backend,
            config=config,
            session_id=request.session_id
        )

        return sandbox

    def _record_execution(
        self,
        request: ExecutionRequest,
        response: ExecutionResponse
    ) -> None:
        """记录执行历史"""
        record = {
            "request_id": response.request_id,
            "language": request.language.value,
            "success": response.success,
            "execution_time": response.execution_time,
            "timestamp": response.metadata.get("timestamp"),
        }

        self._execution_history.append(record)

        # 限制历史大小
        if len(self._execution_history) > self._max_history:
            self._execution_history = self._execution_history[-self._max_history:]

    def get_execution_history(
        self,
        limit: int = 100,
        language: str | None = None
    ) -> list[dict[str, Any]]:
        """获取执行历史

        Args:
            limit: 返回记录数量
            language: 筛选特定语言

        Returns:
            list[dict[str, Any]]: 执行历史记录
        """
        history = self._execution_history

        if language:
            history = [h for h in history if h["language"] == language]

        return history[-limit:]

    def get_statistics(self) -> dict[str, Any]:
        """获取执行统计

        Returns:
            dict[str, Any]: 统计信息
        """
        if not self._execution_history:
            return {
                "total_executions": 0,
                "success_rate": 0.0,
                "avg_execution_time": 0.0,
                "by_language": {},
            }

        total = len(self._execution_history)
        successful = sum(1 for h in self._execution_history if h["success"])
        total_time = sum(h["execution_time"] for h in self._execution_history)

        # 按语言统计
        by_language: dict[str, dict[str, Any]] = {}
        for record in self._execution_history:
            lang = record["language"]
            if lang not in by_language:
                by_language[lang] = {"count": 0, "successful": 0, "total_time": 0}
            by_language[lang]["count"] += 1
            if record["success"]:
                by_language[lang]["successful"] += 1
            by_language[lang]["total_time"] += record["execution_time"]

        return {
            "total_executions": total,
            "successful": successful,
            "failed": total - successful,
            "success_rate": successful / total if total > 0 else 0.0,
            "avg_execution_time": total_time / total if total > 0 else 0.0,
            "by_language": by_language,
        }

    async def cleanup_session(self, session_id: str) -> bool:
        """清理会话（销毁沙盒）

        Args:
            session_id: 会话 ID

        Returns:
            bool: 是否成功清理
        """
        return await self._sandbox_manager.destroy_sandbox(session_id)

    async def cleanup_all(self) -> int:
        """清理所有会话

        Returns:
            int: 清理的会话数量
        """
        return await self._sandbox_manager.destroy_all()

    def list_active_sessions(self) -> list[str]:
        """列出活跃会话

        Returns:
            list[str]: 会话 ID 列表
        """
        return self._sandbox_manager.list_sandboxes()


class SafeCodeRunner:
    """安全代码运行器

    提供简化的接口用于安全执行代码。
    """

    def __init__(self, backend: SandboxBackend = SandboxBackend.LOCAL):
        self._executor = CodeExecutor(default_backend=backend)

    async def run(
        self,
        code: str,
        language: str = "python",
        timeout: int = 30,
        input_data: str | None = None,
    ) -> dict[str, Any]:
        """运行代码

        Args:
            code: 代码
            language: 编程语言
            timeout: 超时时间（秒）
            input_data: 标准输入

        Returns:
            dict[str, Any]: 执行结果
        """
        request = ExecutionRequest(
            code=code,
            language=Language(language),
            timeout=timeout,
            input_data=input_data,
            session_id=None,  # 每次使用新沙盒
        )

        response = await self._executor.execute(request)
        return response.to_dict()

    async def run_python(
        self,
        code: str,
        timeout: int = 30,
        **kwargs
    ) -> dict[str, Any]:
        """运行 Python 代码"""
        return await self.run(code, "python", timeout, **kwargs)

    async def run_javascript(
        self,
        code: str,
        timeout: int = 30,
        **kwargs
    ) -> dict[str, Any]:
        """运行 JavaScript 代码"""
        return await self.run(code, "javascript", timeout, **kwargs)

    def get_stats(self) -> dict[str, Any]:
        """获取统计信息"""
        return self._executor.get_statistics()
