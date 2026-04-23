from __future__ import annotations
"""
结构化日志模块
Structured Logging Module
"""

from .structured_decision_logger import (
    DecisionLogEntry,
    LogLevel as DecisionLogLevel,
    StructuredDecisionLogger,
    get_decision_logger,
    log_decision_process,
)

from .unified_logger import (
    UnifiedLogger,
    LogLevel,
    get_logger,
    ContextFilter,
    JSONFormatter,
    TextFormatter,
)

from .handlers import (
    AsyncLogHandler,
    RotatingFileHandler,
    RemoteHandler,
)

from .filters import (
    SensitiveDataFilter,
)

from .config import (
    LoggingConfigLoader,
)

__all__ = [
    # 原有导出（结构化决策日志）
    "DecisionLogEntry",
    "StructuredDecisionLogger",
    "get_decision_logger",
    "log_decision_process",
    "DecisionLogLevel",  # 重命名以避免冲突

    # 新增导出（统一日志系统）
    "UnifiedLogger",
    "LogLevel",
    "get_logger",
    "ContextFilter",
    "JSONFormatter",
    "TextFormatter",

    # 新增导出（高级处理器）
    "AsyncLogHandler",
    "RotatingFileHandler",
    "RemoteHandler",

    # 新增导出（过滤器）
    "SensitiveDataFilter",

    # 新增导出（配置系统）
    "LoggingConfigLoader",
]
