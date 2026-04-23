from __future__ import annotations
"""
Docker 沙盒实现

提供基于 Docker 容器的隔离执行环境。
"""

import asyncio
import time
from pathlib import Path

from .base import (
    Language,
    Sandbox,
    SandboxConfig,
    SandboxException,
    SandboxResult,
)


class DockerSandbox(Sandbox):
    """Docker 沙盒

    使用 Docker 容器提供完全隔离的执行环境。
    """

    def __init__(self, config: SandboxConfig | None = None):
        super().__init__(config)
        self._container_id: Optional[str] = None
        self._container_name: Optional[str] = None

    async def initialize(self) -> None:
        """初始化沙盒（创建容器）"""
        if self._is_initialized:
            return

        # 检查 Docker 是否可用
        if not await self._check_docker():
            raise SandboxException("Docker is not available")

        # 生成容器名称
        import uuid
        self._container_name = f"athena-sandbox-{uuid.uuid4().hex[:8]}"

        # 创建容器
        self._container_id = await self._create_container()
        self._is_initialized = True

    async def cleanup(self) -> None:
        """清理沙盒（删除容器）"""
        if self._container_id:
            try:
                await self._docker_command(["rm", "-f", self._container_id])
            except Exception:
                pass
            self._container_id = None
        self._is_initialized = False

    async def execute_command(
        self,
        command: str,
        working_dir: Optional[str] = None,
        timeout: Optional[int] = None
    ) -> SandboxResult:
        """在容器中执行命令"""
        if not self._is_initialized:
            raise SandboxException("Sandbox not initialized")

        timeout = timeout or self._config.max_execution_time
        work_dir = working_dir or self._config.working_dir

        start_time = time.time()

        try:
            # 构建 Docker exec 命令
            docker_cmd = [
                "exec",
                self._container_id,
                "sh", "-c",
                f"cd {work_dir} && {command}"
            ]

            # 执行命令
            result = await asyncio.wait_for(
                self._docker_command(docker_cmd, capture_output=True),
                timeout=timeout
            )

            execution_time = time.time() - start_time

            return SandboxResult(
                success=result["exit_code"] == 0,
                output=result["stdout"],
                error=result["stderr"],
                exit_code=result["exit_code"],
                execution_time=execution_time,
            )

        except asyncio.TimeoutError:
            # 超时，尝试终止命令
            await self._terminate_running_command()
            execution_time = time.time() - start_time
            return SandboxResult(
                success=False,
                output="",
                error=f"Command timeout after {timeout}s",
                execution_time=execution_time,
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
        # 将代码写入容器
        await self.write_file("script.py", code)

        # 构建执行命令
        command = "python3 script.py"

        # 添加输入
        if "input" in kwargs:
            command = f'echo "{kwargs["input"]}" | python3 script.py'

        return await self.execute_command(command)

    async def _execute_javascript(self, code: str, **kwargs) -> SandboxResult:
        """执行 JavaScript 代码"""
        # 将代码写入容器
        await self.write_file("script.js", code)

        # 构建执行命令
        command = "node script.js"

        return await self.execute_command(command)

    async def _execute_shell(self, code: str, **kwargs) -> SandboxResult:
        """执行 Shell 代码"""
        return await self.execute_command(code)

    async def read_file(self, path: str) -> str:
        """读取容器中的文件"""
        if not self._is_initialized:
            raise SandboxException("Sandbox not initialized")

        # 使用 docker cp 复制文件到临时位置
        import tempfile

        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp_path = tmp.name

        try:
            # 复制文件
            await self._docker_command([
                "cp",
                f"{self._container_id}:{self._config.working_dir}/{path.lstrip('/')}",
                tmp_path
            ])

            # 读取内容
            content = Path(tmp_path).read_text(encoding="utf-8", errors="replace")
            return content

        finally:
            # 删除临时文件
            Path(tmp_path).unlink(missing_ok=True)

    async def write_file(
        self,
        path: str,
        content: str,
        append: bool = False
    ) -> None:
        """写入文件到容器"""
        if not self._is_initialized:
            raise SandboxException("Sandbox not initialized")

        import tempfile

        # 创建临时文件
        with tempfile.NamedTemporaryFile(mode="w", delete=False, encoding="utf-8") as tmp:
            tmp.write(content)
            tmp_path = tmp.name

        try:
            # 复制文件到容器
            container_path = f"{self._config.working_dir}/{path.lstrip('/')}"
            await self._docker_command([
                "cp",
                tmp_path,
                f"{self._container_id}:{container_path}"
            ])
        finally:
            # 删除临时文件
            Path(tmp_path).unlink(missing_ok=True)

    async def list_files(self, path: str = ".") -> list[str]:
        """列出容器中的文件"""
        if not self._is_initialized:
            raise SandboxException("Sandbox not initialized")

        target_path = f"{self._config.working_dir}/{path.lstrip('/')}"

        result = await self.execute_command(f"find {target_path} -type f")

        if result.success:
            files = []
            for line in result.output.strip().split("\n"):
                if line:
                    # 返回相对于工作目录的路径
                    rel_path = line.replace(target_path, "").lstrip("/")
                    files.append(rel_path)
            return files
        return []

    async def file_exists(self, path: str) -> bool:
        """检查文件是否存在"""
        if not self._is_initialized:
            raise SandboxException("Sandbox not initialized")

        target_path = f"{self._config.working_dir}/{path.lstrip('/')}"

        result = await self.execute_command(f"test -f {target_path} && echo 'exists'")

        return result.success and "exists" in result.output

    async def delete_file(self, path: str) -> bool:
        """删除容器中的文件"""
        if not self._is_initialized:
            raise SandboxException("Sandbox not initialized")

        target_path = f"{self._config.working_dir}/{path.lstrip('/')}"

        result = await self.execute_command(f"rm -f {target_path}")
        return result.success

    async def _check_docker(self) -> bool:
        """检查 Docker 是否可用"""
        try:
            result = await self._docker_command(["--version"])
            return result["exit_code"] == 0
        except Exception:
            return False

    async def _create_container(self) -> str:
        """创建 Docker 容器"""
        # 构建创建命令
        create_cmd = [
            "create",
            "--name", self._container_name,
            "--memory", self._config.max_memory,
            "--cpus", str(self._config.max_cpu),
        ]

        # 禁用网络（如果配置要求）
        if not self._config.enable_network:
            create_cmd.extend(["--network", "none"])

        # 添加卷映射
        for virtual_path, actual_path in self._config.path_mappings.items():
            create_cmd.extend(["-v", f"{actual_path}:{virtual_path}"])

        # 选择镜像
        image = self._config.container_image or "python:3.11-slim"
        create_cmd.append(image)

        # 保持容器运行
        create_cmd.extend(["sh", "-c", "tail -f /dev/null"])

        # 创建容器
        result = await self._docker_command(create_cmd)

        if result["exit_code"] != 0:
            raise SandboxException(f"Failed to create container: {result['stderr']}")

        # 启动容器
        start_result = await self._docker_command(["start", self._container_name])

        if start_result["exit_code"] != 0:
            raise SandboxException(f"Failed to start container: {start_result['stderr']}")

        # 等待容器启动
        await asyncio.sleep(1)

        return self._container_name

    async def _docker_command(
        self,
        args: list[str],
        capture_output: bool = False
    ) -> dict:
        """执行 Docker 命令"""
        cmd = ["docker"] + args

        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE if capture_output else None,
            stderr=asyncio.subprocess.PIPE if capture_output else None,
        )

        if capture_output:
            stdout, stderr = await process.communicate()
            return {
                "exit_code": process.returncode,
                "stdout": stdout.decode("utf-8", errors="replace"),
                "stderr": stderr.decode("utf-8", errors="replace"),
            }
        else:
            await process.wait()
            return {"exit_code": process.returncode}

    async def _terminate_running_command(self) -> None:
        """终止容器中正在运行的命令"""
        try:
            # 在容器中执行 kill 命令
            await self._docker_command([
                "exec",
                self._container_id,
                "sh", "-c",
                "pkill -9 -f python || pkill -9 -f node || true"
            ])
        except Exception:
            pass
