"""
统一Agent配置管理

整合两套架构的配置项，提供统一的配置接口。
支持字典初始化、配置验证和默认值管理。

Author: Athena Team
Version: 1.0.0
Date: 2026-04-24
"""

from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass
class UnifiedAgentConfig:
    """
    统一Agent配置

    整合两套架构的配置项，提供默认值和验证。
    支持从字典创建，方便配置文件加载。

    Attributes:
        name: Agent名称（唯一标识符）
        role: Agent角色描述
        version: Agent版本号
        # LLM配置
        model: 使用的模型名称
        temperature: 温度参数（0-1）
        max_tokens: 最大生成token数
        # 通信配置
        enable_gateway: 是否启用Gateway通信
        gateway_url: Gateway WebSocket URL
        enable_message_bus: 是否启用传统MessageBus（向后兼容）
        # 记忆系统配置
        enable_memory: 是否启用统一记忆系统
        project_path: 项目路径（用于记忆系统）
        # 工具配置
        enable_tools: 是否启用工具系统
        tool_registry: 工具注册表配置
        # 性能配置
        max_concurrent_requests: 最大并发请求数
        request_timeout: 请求超时时间（秒）
    """
    # 基础配置
    name: str
    role: str
    version: str = "1.0.0"

    # LLM配置
    model: str = "gpt-4"
    temperature: float = 0.7
    max_tokens: int = 2000

    # 通信配置
    enable_gateway: bool = True
    gateway_url: str = "ws://localhost:8005/ws"
    enable_message_bus: bool = True  # 向后兼容

    # 记忆系统配置
    enable_memory: bool = True
    project_path: Optional[str] = None

    # 工具配置
    enable_tools: bool = True
    tool_registry: Optional[str] = None

    # 追踪配置
    enable_tracing: bool = True  # 启用OpenTelemetry分布式追踪

    # 性能配置
    max_concurrent_requests: int = 10
    request_timeout: int = 60

    # 扩展配置（预留）
    extra: Optional[dict[str, Any]] = field(default_factory=dict)

    def validate(self) -> tuple[bool, list[str]]:
        """
        验证配置有效性

        Returns:
            (是否有效, 错误消息列表)
        """
        errors = []

        # 基础配置验证
        if not self.name:
            errors.append("name不能为空")
        if not self.role:
            errors.append("role不能为空")

        # LLM配置验证
        if not 0.0 <= self.temperature <= 1.0:
            errors.append("temperature必须在0-1之间")
        if self.max_tokens <= 0:
            errors.append("max_tokens必须大于0")

        # 性能配置验证
        if self.max_concurrent_requests <= 0:
            errors.append("max_concurrent_requests必须大于0")
        if self.request_timeout <= 0:
            errors.append("request_timeout必须大于0")

        return len(errors) == 0, errors

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "name": self.name,
            "role": self.role,
            "version": self.version,
            "model": self.model,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "enable_gateway": self.enable_gateway,
            "gateway_url": self.gateway_url,
            "enable_message_bus": self.enable_message_bus,
            "enable_memory": self.enable_memory,
            "project_path": self.project_path,
            "enable_tools": self.enable_tools,
            "tool_registry": self.tool_registry,
            "enable_tracing": self.enable_tracing,
            "max_concurrent_requests": self.max_concurrent_requests,
            "request_timeout": self.request_timeout,
            **(self.extra or {})
        }

    @classmethod
    def from_dict(cls, config: dict[str, Any]) -> "UnifiedAgentConfig":
        """
        从字典创建配置

        Args:
            config: 配置字典，支持所有配置项

        Returns:
            UnifiedAgentConfig实例

        Example:
            >>> config = UnifiedAgentConfig.from_dict({
            ...     "name": "xiaona-legal",
            ...     "role": "legal-expert",
            ...     "model": "gpt-4",
            ...     "temperature": 0.8
            ... })
        """
        # 提取扩展配置
        known_fields = {
            "name", "role", "version", "model", "temperature", "max_tokens",
            "enable_gateway", "gateway_url", "enable_message_bus",
            "enable_memory", "project_path", "enable_tools", "tool_registry",
            "enable_tracing", "max_concurrent_requests", "request_timeout"
        }
        extra = {k: v for k, v in config.items() if k not in known_fields}

        return cls(
            name=config.get("name", ""),
            role=config.get("role", ""),
            version=config.get("version", "1.0.0"),
            model=config.get("model", "gpt-4"),
            temperature=config.get("temperature", 0.7),
            max_tokens=config.get("max_tokens", 2000),
            enable_gateway=config.get("enable_gateway", True),
            gateway_url=config.get("gateway_url", "ws://localhost:8005/ws"),
            enable_message_bus=config.get("enable_message_bus", True),
            enable_memory=config.get("enable_memory", True),
            project_path=config.get("project_path"),
            enable_tools=config.get("enable_tools", True),
            tool_registry=config.get("tool_registry"),
            enable_tracing=config.get("enable_tracing", True),
            max_concurrent_requests=config.get("max_concurrent_requests", 10),
            request_timeout=config.get("request_timeout", 60),
            extra=extra if extra else None
        )

    @classmethod
    def create_minimal(cls, name: str, role: str) -> "UnifiedAgentConfig":
        """创建最小配置（使用所有默认值）"""
        return cls(name=name, role=role)

    def with_overrides(self, **kwargs) -> "UnifiedAgentConfig":
        """
        创建配置副本并覆盖指定字段

        Args:
            **kwargs: 要覆盖的字段

        Returns:
            新的配置实例

        Example:
            >>> config = UnifiedAgentConfig.create_minimal("test", "tester")
            >>> new_config = config.with_overrides(model="gpt-3.5-turbo", temperature=0.5)
        """
        data = self.to_dict()
        data.update(kwargs)
        return self.from_dict(data)


# ============ 配置构建器 ============


class UnifiedAgentConfigBuilder:
    """
    配置构建器 - 流式接口创建配置

    Example:
        >>> config = (UnifiedAgentConfigBuilder()
        ...     .name("xiaona-legal")
        ...     .role("legal-expert")
        ...     .model("gpt-4")
        ...     .temperature(0.8)
        ...     .build())
    """

    def __init__(self):
        self._config: dict[str, Any] = {}

    def name(self, name: str) -> "UnifiedAgentConfigBuilder":
        self._config["name"] = name
        return self

    def role(self, role: str) -> "UnifiedAgentConfigBuilder":
        self._config["role"] = role
        return self

    def version(self, version: str) -> "UnifiedAgentConfigBuilder":
        self._config["version"] = version
        return self

    def model(self, model: str) -> "UnifiedAgentConfigBuilder":
        self._config["model"] = model
        return self

    def temperature(self, temperature: float) -> "UnifiedAgentConfigBuilder":
        self._config["temperature"] = temperature
        return self

    def max_tokens(self, max_tokens: int) -> "UnifiedAgentConfigBuilder":
        self._config["max_tokens"] = max_tokens
        return self

    def enable_gateway(self, enable: bool = True) -> "UnifiedAgentConfigBuilder":
        self._config["enable_gateway"] = enable
        return self

    def gateway_url(self, url: str) -> "UnifiedAgentConfigBuilder":
        self._config["gateway_url"] = url
        return self

    def enable_memory(self, enable: bool = True) -> "UnifiedAgentConfigBuilder":
        self._config["enable_memory"] = enable
        return self

    def project_path(self, path: str) -> "UnifiedAgentConfigBuilder":
        self._config["project_path"] = path
        return self

    def enable_tools(self, enable: bool = True) -> "UnifiedAgentConfigBuilder":
        self._config["enable_tools"] = enable
        return self

    def enable_tracing(self, enable: bool = True) -> "UnifiedAgentConfigBuilder":
        self._config["enable_tracing"] = enable
        return self

    def build(self) -> UnifiedAgentConfig:
        """构建配置对象"""
        return UnifiedAgentConfig.from_dict(self._config)


# ============ 预定义配置模板 ============


class ConfigTemplates:
    """预定义配置模板"""

    @staticmethod
    def legal_agent(name: str = "xiaona-legal") -> UnifiedAgentConfig:
        """法律专家Agent配置模板"""
        return UnifiedAgentConfig(
            name=name,
            role="legal-expert",
            model="gpt-4",
            temperature=0.3,  # 法律分析需要低温度
            max_tokens=4000,
            enable_memory=True,
            enable_tools=True
        )

    @staticmethod
    def coordinator_agent(name: str = "xiaonuo-coordinator") -> UnifiedAgentConfig:
        """协调器Agent配置模板"""
        return UnifiedAgentConfig(
            name=name,
            role="coordinator",
            model="gpt-4",
            temperature=0.5,
            max_tokens=2000,
            enable_gateway=True,
            enable_memory=True
        )

    @staticmethod
    def search_agent(name: str = "yunxi-search") -> UnifiedAgentConfig:
        """检索Agent配置模板"""
        return UnifiedAgentConfig(
            name=name,
            role="search-expert",
            model="gpt-3.5-turbo",
            temperature=0.2,
            max_tokens=1000,
            enable_tools=True
        )

    @staticmethod
    def minimal(name: str, role: str) -> UnifiedAgentConfig:
        """最小配置模板"""
        return UnifiedAgentConfig.create_minimal(name, role)


# ============ 导出 ============

__all__ = [
    "UnifiedAgentConfig",
    "UnifiedAgentConfigBuilder",
    "ConfigTemplates",
]
