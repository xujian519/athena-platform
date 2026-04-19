from __future__ import annotations
"""
Athena 沙盒系统

提供安全的代码执行环境，支持容器隔离和资源限制。

参考：DeerFlow 沙盒系统设计
"""

from .base import (
    Language,
    ResourceLimitException,
    Sandbox,
    SandboxBackend,
    SandboxConfig,
    SandboxException,
    SandboxManager,
    SandboxResult,
    SecurityException,
    TimeoutException,
)
from .docker_sandbox import DockerSandbox
from .executor import (
    CodeExecutor,
    ExecutionRequest,
    ExecutionResponse,
    SafeCodeRunner,
)
from .local import LocalSandbox, LocalSandboxProvider

__all__ = [
    # 基础组件
    "Sandbox",
    "SandboxConfig",
    "SandboxResult",
    "SandboxException",
    "SandboxManager",
    "SandboxBackend",
    "Language",
    "TimeoutException",
    "ResourceLimitException",
    "SecurityException",

    # 沙盒实现
    "LocalSandbox",
    "LocalSandboxProvider",
    "DockerSandbox",

    # 代码执行
    "CodeExecutor",
    "ExecutionRequest",
    "ExecutionResponse",
    "SafeCodeRunner",
]

# 默认沙盒配置
DEFAULT_SANDBOX_CONFIG = SandboxConfig(
    max_execution_time=600,  # 10分钟
    max_memory="512m",       # 512MB
    max_cpu=1.0,            # 1个CPU核心
    enable_network=False,    # 禁用网络
    enable_file_write=True,  # 允许写入
    temp_dir="/tmp/athena-sandbox",
)
