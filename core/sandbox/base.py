from __future__ import annotations
"""
沙盒系统基础架构

定义沙盒的抽象接口和数据模型。
"""

import asyncio
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class SandboxBackend(Enum):
    """沙盒后端类型"""
    LOCAL = "local"          # 本地执行（不隔离，仅用于开发）
    DOCKER = "docker"        # Docker 容器
    KUBERNETES = "kubernetes"  # Kubernetes Pod


class Language(Enum):
    """支持的编程语言"""
    PYTHON = "python"
    JAVASCRIPT = "javascript"
    NODE = "node"
    TYPESCRIPT = "typescript"
    BASH = "bash"
    SHELL = "shell"


@dataclass
class SandboxConfig:
    """沙盒配置

    定义沙盒的资源限制和安全策略。
    """
    # 资源限制
    max_execution_time: int = 600        # 最大执行时间（秒）
    max_memory: str = "512m"             # 最大内存
    max_cpu: float = 1.0                 # 最大 CPU 核心数
    max_disk_size: str = "1g"            # 最大磁盘使用

    # 安全选项
    enable_network: bool = False         # 是否启用网络
    enable_file_write: bool = True       # 是否允许文件写入
    allowed_paths: list[str] = field(default_factory=list)  # 允许访问的路径

    # 隔离选项
    temp_dir: str = "/tmp/athena-sandbox"  # 临时目录
    container_image: Optional[str] = None  # 容器镜像（Docker/K8s）
    working_dir: str = "/workspace"        # 工作目录

    # 路径映射（虚拟路径 → 实际路径）
    path_mappings: dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "max_execution_time": self.max_execution_time,
            "max_memory": self.max_memory,
            "max_cpu": self.max_cpu,
            "max_disk_size": self.max_disk_size,
            "enable_network": self.enable_network,
            "enable_file_write": self.enable_file_write,
            "allowed_paths": self.allowed_paths,
            "temp_dir": self.temp_dir,
            "container_image": self.container_image,
            "working_dir": self.working_dir,
            "path_mappings": self.path_mappings,
        }


@dataclass
class SandboxResult:
    """沙盒执行结果

    包含代码执行的输出、状态和资源使用情况。
    """
    success: bool                          # 是否成功
    output: str                            # 标准输出
    error: str = ""                        # 标准错误
    exit_code: int = 0                     # 退出码
    execution_time: float = 0.0            # 执行时间（秒）

    # 资源使用
    memory_used: Optional[str] = None      # 内存使用
    cpu_time: Optional[float] = None       # CPU 时间

    # 文件系统
    files_created: list[str] = field(default_factory=list)    # 创建的文件
    files_modified: list[str] = field(default_factory=list)   # 修改的文件
    files_deleted: list[str] = field(default_factory=list)   # 删除的文件

    # 额外元数据
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "success": self.success,
            "output": self.output,
            "error": self.error,
            "exit_code": self.exit_code,
            "execution_time": self.execution_time,
            "memory_used": self.memory_used,
            "cpu_time": self.cpu_time,
            "files_created": self.files_created,
            "files_modified": self.files_modified,
            "files_deleted": self.files_deleted,
            "metadata": self.metadata,
        }


class SandboxException(Exception):
    """沙盒异常基类"""

    def __init__(self, message: str, code: str = "SANDBOX_ERROR"):
        self.message = message
        self.code = code
        super().__init__(self.message)


class TimeoutException(SandboxException):
    """执行超时异常"""

    def __init__(self, message: str = "Execution timeout"):
        super().__init__(message, code="TIMEOUT")


class ResourceLimitException(SandboxException):
    """资源限制异常"""

    def __init__(self, message: str = "Resource limit exceeded"):
        super().__init__(message, code="RESOURCE_LIMIT")


class SecurityException(SandboxException):
    """安全异常"""

    def __init__(self, message: str = "Security violation detected"):
        super().__init__(message, code="SECURITY_VIOLATION")


class Sandbox(ABC):
    """沙盒抽象基类

    定义沙盒的标准接口，所有沙盒实现必须继承此类。
    """

    def __init__(self, config: SandboxConfig | None = None):
        self._config = config or SandboxConfig()
        self._is_initialized = False
        self._session_id: Optional[str] = None

    @property
    def config(self) -> SandboxConfig:
        """获取沙盒配置"""
        return self._config

    @property
    def is_initialized(self) -> bool:
        """检查是否已初始化"""
        return self._is_initialized

    @abstractmethod
    async def initialize(self) -> None:
        """初始化沙盒

        创建沙盒环境，准备执行上下文。
        """
        pass

    @abstractmethod
    async def cleanup(self) -> None:
        """清理沙盒

        删除沙盒环境，释放资源。
        """
        pass

    @abstractmethod
    async def execute_command(
        self,
        command: str,
        working_dir: Optional[str] = None,
        timeout: Optional[int] = None
    ) -> SandboxResult:
        """执行命令

        Args:
            command: 要执行的命令
            working_dir: 工作目录（相对于沙盒工作目录）
            timeout: 超时时间（秒），None 表示使用配置默认值

        Returns:
            SandboxResult: 执行结果
        """
        pass

    @abstractmethod
    async def execute_code(
        self,
        code: str,
        language: Language,
        **kwargs
    ) -> SandboxResult:
        """执行代码

        Args:
            code: 要执行的代码
            language: 编程语言
            **kwargs: 额外参数

        Returns:
            SandboxResult: 执行结果
        """
        pass

    @abstractmethod
    async def read_file(self, path: str) -> str:
        """读取文件

        Args:
            path: 文件路径（相对于沙盒工作目录）

        Returns:
            str: 文件内容
        """
        pass

    @abstractmethod
    async def write_file(
        self,
        path: str,
        content: str,
        append: bool = False
    ) -> None:
        """写入文件

        Args:
            path: 文件路径（相对于沙盒工作目录）
            content: 文件内容
            append: 是否追加模式
        """
        pass

    @abstractmethod
    async def list_files(self, path: str = ".") -> list[str]:
        """列出目录中的文件

        Args:
            path: 目录路径（相对于沙盒工作目录）

        Returns:
            List[str]: 文件列表
        """
        pass

    @abstractmethod
    async def file_exists(self, path: str) -> bool:
        """检查文件是否存在

        Args:
            path: 文件路径（相对于沙盒工作目录）

        Returns:
            bool: 文件是否存在
        """
        pass

    @abstractmethod
    async def delete_file(self, path: str) -> bool:
        """删除文件

        Args:
            path: 文件路径（相对于沙盒工作目录）

        Returns:
            bool: 是否成功删除
        """
        pass

    def resolve_path(self, virtual_path: str) -> str:
        """解析虚拟路径为实际路径

        Args:
            virtual_path: 虚拟路径（以 /mnt/ 开头）

        Returns:
            str: 实际文件系统路径
        """
        # 移除前导斜杠并分割
        parts = virtual_path.lstrip("/").split("/")

        # 尝试匹配路径映射
        for virtual_prefix, actual_path in sorted(
            self._config.path_mappings.items(),
            key=lambda x: len(x[0]),
            reverse=True
        ):
            virtual_parts = virtual_prefix.strip("/").split("/")
            if parts[:len(virtual_parts)] == virtual_parts:
                # 匹配成功，构建实际路径
                relative_parts = parts[len(virtual_parts):]
                return str(actual_path) + "/" + "/".join(relative_parts)

        # 没有匹配，返回原始路径
        return virtual_path

    def reverse_resolve_path(self, actual_path: str) -> str:
        """反向解析实际路径为虚拟路径

        Args:
            actual_path: 实际文件系统路径

        Returns:
            str: 虚拟路径
        """
        for virtual_prefix, actual_prefix in self._config.path_mappings.items():
            if str(actual_path).startswith(str(actual_prefix)):
                relative = str(actual_path)[len(str(actual_prefix)):].lstrip("/")
                return f"{virtual_prefix.rstrip('/')}/{relative}"

        # 没有匹配，返回原始路径
        return actual_path

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}("
            f"initialized={self._is_initialized}, "
            f"backend={self.__class__.__name__})"
        )


class SandboxManager:
    """沙盒管理器

    管理沙盒的生命周期和资源。
    """

    def __init__(self):
        self._sandboxes: dict[str, Sandbox] = {}
        self._lock = asyncio.Lock()

    async def create_sandbox(
        self,
        backend: SandboxBackend = SandboxBackend.LOCAL,
        config: SandboxConfig | None = None,
        session_id: Optional[str] = None
    ) -> Sandbox:
        """创建沙盒

        Args:
            backend: 沙盒后端类型
            config: 沙盒配置
            session_id: 会话 ID

        Returns:
            Sandbox: 沙盒实例
        """
        from .docker_sandbox import DockerSandbox
        from .local import LocalSandbox

        async with self._lock:
            # 生成会话 ID
            if session_id is None:
                import uuid
                session_id = str(uuid.uuid4())

            # 根据后端类型创建沙盒
            if backend == SandboxBackend.LOCAL:
                sandbox = LocalSandbox(config)
            elif backend == SandboxBackend.DOCKER:
                sandbox = DockerSandbox(config)
            else:
                raise ValueError(f"Unsupported backend: {backend}")

            # 初始化沙盒
            await sandbox.initialize()
            sandbox._session_id = session_id

            # 存储沙盒
            self._sandboxes[session_id] = sandbox

            return sandbox

    async def get_sandbox(self, session_id: str) -> Sandbox | None:
        """获取沙盒

        Args:
            session_id: 会话 ID

        Returns:
            Optional[Sandbox]: 沙盒实例，不存在返回 None
        """
        return self._sandboxes.get(session_id)

    async def destroy_sandbox(self, session_id: str) -> bool:
        """销毁沙盒

        Args:
            session_id: 会话 ID

        Returns:
            bool: 是否成功销毁
        """
        async with self._lock:
            sandbox = self._sandboxes.pop(session_id, None)
            if sandbox:
                await sandbox.cleanup()
                return True
            return False

    async def destroy_all(self) -> int:
        """销毁所有沙盒

        Returns:
            int: 销毁的沙盒数量
        """
        count = 0
        async with self._lock:
            for _session_id, sandbox in self._sandboxes.items():
                await sandbox.cleanup()
                count += 1
            self._sandboxes.clear()
        return count

    def list_sandboxes(self) -> list[str]:
        """列出所有沙盒会话 ID

        Returns:
            List[str]: 会话 ID 列表
        """
        return list(self._sandboxes.keys())

    def __len__(self) -> int:
        return len(self._sandboxes)
