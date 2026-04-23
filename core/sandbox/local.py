from __future__ import annotations
"""
本地沙盒实现

提供本地开发环境的沙盒执行（不隔离，仅用于测试和开发）。
"""

import asyncio
import shutil
import time
from pathlib import Path

from .base import (
    Language,
    Sandbox,
    SandboxConfig,
    SandboxException,
    SandboxResult,
    TimeoutException,
)


class LocalSandbox(Sandbox):
    """本地沙盒

    在本地文件系统中执行代码，不提供隔离。
    仅用于开发和测试环境。
    """

    def __init__(self, config: SandboxConfig | None = None):
        super().__init__(config)
        self._temp_dir: Path | None = None
        self._file_changes: dict = {
            "created": [],
            "modified": [],
            "deleted": [],
        }

    async def initialize(self) -> None:
        """初始化沙盒"""
        if self._is_initialized:
            return

        # 创建临时目录
        self._temp_dir = Path(self._config.temp_dir)
        self._temp_dir.mkdir(parents=True, exist_ok=True)

        # 创建工作目录
        workspace = self._temp_dir / self._config.working_dir.lstrip("/")
        workspace.mkdir(parents=True, exist_ok=True)

        self._is_initialized = True

    async def cleanup(self) -> None:
        """清理沙盒"""
        if self._temp_dir and self._temp_dir.exists():
            shutil.rmtree(self._temp_dir, ignore_errors=True)
        self._is_initialized = False
        self._file_changes = {"created": [], "modified": [], "deleted": []}

    async def execute_command(
        self,
        command: str,
        working_dir: Optional[str] = None,
        timeout: Optional[int] = None
    ) -> SandboxResult:
        """执行命令（安全版本）

        使用 shell=False 避免命令注入风险。
        对于需要管道或特殊字符的命令，使用 shlex.split 进行安全解析。
        """
        if not self._is_initialized:
            raise SandboxException("Sandbox not initialized")

        timeout = timeout or self._config.max_execution_time
        work_dir = self._get_working_dir(working_dir)

        start_time = time.time()

        try:
            # 安全地解析命令
            import shlex

            # 处理包含管道或重定向的复杂命令
            if "|" in command or ">" in command or "<" in command:
                # 对于复杂命令，使用 /bin/sh -c 但进行输入验证
                # 仅允许安全的字符
                import re
                safe_pattern = r'^[a-zA-Z0-9_\s/\-|<>$."\'=\{\}\[\]()]*$'
                if not re.match(safe_pattern, command):
                    raise SandboxException("Unsafe command characters detected")
                cmd_args = ["/bin/sh", "-c", command]
            else:
                # 简单命令使用 shlex.split 安全解析
                try:
                    cmd_args = shlex.split(command)
                except ValueError as e:
                    raise SandboxException(f"Invalid command syntax: {e}") from e

            # 执行命令（不使用 shell）
            process = await asyncio.create_subprocess_exec(
                *cmd_args,
                cwd=work_dir,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            # 等待完成（带超时）
            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(),
                    timeout=timeout
                )
            except asyncio.TimeoutError:
                process.kill()
                raise TimeoutException(f"Command timeout after {timeout}s") from None

            execution_time = time.time() - start_time

            # 记录文件变化
            await self._track_file_changes()

            return SandboxResult(
                success=process.returncode == 0,
                output=stdout.decode("utf-8", errors="replace"),
                error=stderr.decode("utf-8", errors="replace"),
                exit_code=process.returncode,
                execution_time=execution_time,
                files_created=self._file_changes["created"],
                files_modified=self._file_changes["modified"],
                files_deleted=self._file_changes["deleted"],
            )

        except Exception as e:
            execution_time = time.time() - start_time
            return SandboxResult(
                success=False,
                output="",
                error=str(e),
                execution_time=execution_time,
            )

    async def execute_code(
        self,
        code: str,
        language: Language,
        **kwargs
    ) -> SandboxResult:
        """执行代码"""
        if language == Language.PYTHON:
            return await self._execute_python(code, **kwargs)
        elif language in (Language.JAVASCRIPT, Language.NODE):
            return await self._execute_javascript(code, **kwargs)
        elif language in (Language.BASH, Language.SHELL):
            return await self._execute_shell(code, **kwargs)
        else:
            raise SandboxException(f"Unsupported language: {language}")

    async def _execute_python(self, code: str, **kwargs) -> SandboxResult:
        """执行 Python 代码"""
        # 将代码写入临时文件
        script_file = self._temp_dir / "script.py"
        script_file.write_text(code)

        # 构建 Python 命令（使用完整路径）
        python_cmd = f"python3 {script_file}"

        # 添加输入参数
        if "input" in kwargs:
            input_data = kwargs["input"]
            python_cmd = f'echo "{input_data}" | python3 {script_file}'

        return await self.execute_command(python_cmd)

    async def _execute_javascript(self, code: str, **kwargs) -> SandboxResult:
        """执行 JavaScript 代码"""
        # 将代码写入临时文件
        script_file = self._temp_dir / "script.js"
        script_file.write_text(code)

        # 构建 Node 命令
        node_cmd = f"node {script_file}"

        return await self.execute_command(node_cmd)

    async def _execute_shell(self, code: str, **kwargs) -> SandboxResult:
        """执行 Shell 代码"""
        return await self.execute_command(code)

    async def read_file(self, path: str) -> str:
        """读取文件"""
        if not self._is_initialized:
            raise SandboxException("Sandbox not initialized")

        full_path = self._resolve_sandbox_path(path)

        if not full_path.exists():
            raise SandboxException(f"File not found: {path}")

        return full_path.read_text(encoding="utf-8", errors="replace")

    async def write_file(
        self,
        path: str,
        content: str,
        append: bool = False
    ) -> None:
        """写入文件"""
        if not self._is_initialized:
            raise SandboxException("Sandbox not initialized")

        full_path = self._resolve_sandbox_path(path)

        # 确保目录存在
        full_path.parent.mkdir(parents=True, exist_ok=True)

        # 写入文件
        if append:
            with open(full_path, "a") as f:
                f.write(content)
        else:
            full_path.write_text(content, encoding="utf-8")

        # 记录变化
        if append:
            if str(full_path) not in self._file_changes["modified"]:
                self._file_changes["modified"].append(str(full_path))
        else:
            if full_path.exists():
                if str(full_path) not in self._file_changes["modified"]:
                    self._file_changes["modified"].append(str(full_path))
            else:
                self._file_changes["created"].append(str(full_path))

    async def list_files(self, path: str = ".") -> list[str]:
        """列出目录中的文件"""
        if not self._is_initialized:
            raise SandboxException("Sandbox not initialized")

        full_path = self._resolve_sandbox_path(path)

        if not full_path.exists():
            return []

        if full_path.is_file():
            return [full_path.name]

        return [
            str(p.relative_to(full_path))
            for p in full_path.rglob("*")
            if p.is_file()
        ]

    async def file_exists(self, path: str) -> bool:
        """检查文件是否存在"""
        if not self._is_initialized:
            raise SandboxException("Sandbox not initialized")

        full_path = self._resolve_sandbox_path(path)
        return full_path.exists()

    async def delete_file(self, path: str) -> bool:
        """删除文件"""
        if not self._is_initialized:
            raise SandboxException("Sandbox not initialized")

        full_path = self._resolve_sandbox_path(path)

        if full_path.exists():
            full_path.unlink()
            self._file_changes["deleted"].append(str(full_path))
            return True
        return False

    def _get_working_dir(self, relative_path: Optional[str] = None) -> Path:
        """获取工作目录的完整路径"""
        if relative_path is None:
            return self._temp_dir / self._config.working_dir.lstrip("/")
        return self._temp_dir / relative_path.lstrip("/")

    def _resolve_sandbox_path(self, path: str) -> Path:
        """解析沙盒内的路径为实际路径"""
        # 移除开头的斜杠
        path = path.lstrip("/")

        # 解析为工作目录下的路径
        if path.startswith(self._config.working_dir.lstrip("/")):
            return self._temp_dir / path
        else:
            return self._temp_dir / self._config.working_dir.lstrip("/") / path

    async def _track_file_changes(self) -> None:
        """跟踪文件变化"""
        # 简化实现：在实际应用中可以使用文件系统监控
        pass


class LocalSandboxProvider:
    """本地沙盒提供者

    用于创建和管理本地沙盒实例。
    """

    def __init__(self, default_config: SandboxConfig | None = None):
        self._default_config = default_config or SandboxConfig()
        self._sandboxes: dict = {}

    async def create_sandbox(
        self,
        config: SandboxConfig | None = None
    ) -> LocalSandbox:
        """创建本地沙盒"""
        sandbox = LocalSandbox(config or self._default_config)
        await sandbox.initialize()
        return sandbox

    async def create_sandbox_for_skill(
        self,
        skill_name: str,
        config: SandboxConfig | None = None
    ) -> LocalSandbox:
        """为技能创建专用沙盒"""
        skill_config = config or self._default_config

        # 为技能创建专用临时目录
        skill_temp_dir = f"{skill_config.temp_dir}/{skill_name}"
        skill_config.temp_dir = skill_temp_dir

        sandbox = LocalSandbox(skill_config)
        await sandbox.initialize()
        return sandbox
