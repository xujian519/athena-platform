from __future__ import annotations
"""
技能沙盒集成模块

允许技能在安全的沙盒环境中执行代码。
"""


from typing import Any

from core.sandbox import (
    CodeExecutor,
    SafeCodeRunner,
    Sandbox,
    SandboxBackend,
    SandboxConfig,
)


class SandboxSkillMixin:
    """沙盒技能混入类

    为技能添加沙盒执行能力。
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._sandbox: Sandbox | None = None
        self._code_runner: SafeCodeRunner | None = None
        self._sandbox_backend: SandboxBackend = SandboxBackend.LOCAL
        self._session_id: Optional[str] = None

    async def setup_sandbox(
        self,
        backend: SandboxBackend = SandboxBackend.LOCAL,
        config: SandboxConfig | None = None,
        session_id: Optional[str] = None
    ) -> None:
        """初始化沙盒环境

        Args:
            backend: 沙盒后端类型
            config: 沙盒配置
            session_id: 会话 ID（用于复用沙盒）
        """
        self._sandbox_backend = backend
        self._session_id = session_id

        # 创建代码执行器
        self._code_runner = SafeCodeRunner(backend=backend)

        # 如果需要持久化沙盒，创建并初始化
        if session_id:
            from core.sandbox import SandboxManager
            manager = SandboxManager()
            self._sandbox = await manager.create_sandbox(
                backend=backend,
                config=config,
                session_id=session_id
            )

    async def execute_in_sandbox(
        self,
        code: str,
        language: str = "python",
        timeout: int = 30,
        input_data: Optional[str] = None,
        files: Optional[dict[str, str]] = None
    ) -> dict[str, Any]:
        """在沙盒中执行代码

        Args:
            code: 要执行的代码
            language: 编程语言
            timeout: 超时时间（秒）
            input_data: 标准输入
            files: 要创建的文件 {路径: 内容}

        Returns:
            dict[str, Any]: 执行结果
        """
        if self._code_runner is None:
            await self.setup_sandbox()

        return await self._code_runner.run(
            code=code,
            language=language,
            timeout=timeout,
            input_data=input_data
        )

    async def execute_python_in_sandbox(
        self,
        code: str,
        timeout: int = 30,
        **kwargs
    ) -> dict[str, Any]:
        """在沙盒中执行 Python 代码

        Args:
            code: Python 代码
            timeout: 超时时间
            **kwargs: 额外参数

        Returns:
            dict[str, Any]: 执行结果
        """
        return await self.execute_in_sandbox(code, "python", timeout, **kwargs)

    async def execute_javascript_in_sandbox(
        self,
        code: str,
        timeout: int = 30,
        **kwargs
    ) -> dict[str, Any]:
        """在沙盒中执行 JavaScript 代码

        Args:
            code: JavaScript 代码
            timeout: 超时时间
            **kwargs: 额外参数

        Returns:
            dict[str, Any]: 执行结果
        """
        return await self.execute_in_sandbox(code, "javascript", timeout, **kwargs)

    async def cleanup_sandbox(self) -> None:
        """清理沙盒资源"""
        if self._session_id and self._code_runner:
            await self._code_runner._executor.cleanup_session(self._session_id)
        self._sandbox = None


class ScriptExecutionSkill:
    """脚本执行技能

    允许在沙盒中执行用户提供的脚本。
    """

    def __init__(self, backend: SandboxBackend = SandboxBackend.LOCAL):
        self._backend = backend
        self._code_runner = SafeCodeRunner(backend)

    async def execute_script(
        self,
        script: str,
        language: str = "python",
        timeout: int = 60,
        input_data: Optional[str] = None
    ) -> dict[str, Any]:
        """执行脚本

        Args:
            script: 脚本内容
            language: 编程语言
            timeout: 超时时间
            input_data: 标准输入

        Returns:
            dict[str, Any]: 执行结果
        """
        result = await self._code_runner.run(
            code=script,
            language=language,
            timeout=timeout,
            input_data=input_data
        )

        return {
            "success": result["success"],
            "output": result["output"],
            "error": result["error"],
            "execution_time": result["execution_time"],
            "exit_code": result["exit_code"],
        }

    async def execute_script_with_files(
        self,
        script: str,
        files: dict[str, str],
        language: str = "python",
        timeout: int = 60
    ) -> dict[str, Any]:
        """执行脚本（带文件支持）

        Args:
            script: 脚本内容
            files: 文件映射 {路径: 内容}
            language: 编程语言
            timeout: 超时时间

        Returns:
            dict[str, Any]: 执行结果
        """
        from core.sandbox import ExecutionRequest, Language

        request = ExecutionRequest(
            code=script,
            language=Language(language),
            files=files,
            timeout=timeout,
            backend=self._backend,
        )

        executor = CodeExecutor(default_backend=self._backend)
        response = await executor.execute(request)

        return response.to_dict()

    def get_execution_stats(self) -> dict[str, Any]:
        """获取执行统计"""
        return self._code_runner.get_stats()


# 预定义的安全执行函数
async def execute_code_safely(
    code: str,
    language: str = "python",
    timeout: int = 30,
    backend: SandboxBackend = SandboxBackend.LOCAL
) -> dict[str, Any]:
    """安全执行代码（便捷函数）

    Args:
        code: 代码
        language: 编程语言
        timeout: 超时时间
        backend: 沙盒后端

    Returns:
        dict[str, Any]: 执行结果
    """
    runner = SafeCodeRunner(backend=backend)
    return await runner.run(code, language, timeout)


async def execute_python_safely(
    code: str,
    timeout: int = 30,
    backend: SandboxBackend = SandboxBackend.LOCAL
) -> dict[str, Any]:
    """安全执行 Python 代码（便捷函数）"""
    return await execute_code_safely(code, "python", timeout, backend)


async def execute_javascript_safely(
    code: str,
    timeout: int = 30,
    backend: SandboxBackend = SandboxBackend.LOCAL
) -> dict[str, Any]:
    """安全执行 JavaScript 代码（便捷函数）"""
    return await execute_code_safely(code, "javascript", timeout, backend)
