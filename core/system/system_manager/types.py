#!/usr/bin/env python3
"""
系统管理器 - 类型定义
System Manager - Type Definitions

作者: Athena AI系统
创建时间: 2025-12-11
重构时间: 2026-01-27
版本: 2.0.0
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


class ModuleState(Enum):
    """模块状态"""
    LOADED = "loaded"
    INITIALIZING = "initializing"
    READY = "ready"
    STARTING = "starting"
    RUNNING = "running"
    STOPPING = "stopping"
    STOPPED = "stopped"
    UNLOADING = "unloading"
    ERROR = "error"
    DEPRECATED = "deprecated"


class DependencyType(Enum):
    """依赖类型"""
    REQUIRED = "required"
    OPTIONAL = "optional"
    WEAK = "weak"
    CONFLICTS = "conflicts"


class HealthStatus(Enum):
    """健康状态"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


@dataclass
class ModuleMetadata:
    """模块元数据"""
    module_id: str
    name: str
    version: str
    description: str
    file_path: str
    class_name: str = "BaseModule"
    dependencies: dict[str, DependencyType] = field(default_factory=dict)
    provides: list[str] = field(default_factory=list)
    requires: list[str] = field(default_factory=list)
    config_schema: dict[str, Any] = field(default_factory=dict)
    max_retries: int = 3
    auto_restart: bool = True
    health_check_interval: float = 30.0


@dataclass
class ModuleInstance:
    """模块实例"""
    metadata: ModuleMetadata
    module_class: type
    instance: Any
    state: ModuleState
    config: dict[str, Any] = field(default_factory=dict)
    health_status: HealthStatus = HealthStatus.UNKNOWN
    error_count: int = 0
    last_error: str | None = None
    last_health_check: datetime | None = None
    start_time: datetime | None = None
    load_time: datetime | None = None


__all__ = [
    "ModuleState",
    "DependencyType",
    "HealthStatus",
    "ModuleMetadata",
    "ModuleInstance",
]
