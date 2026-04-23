"""
监控模块

> 版本: v1.0
> 更新: 2026-04-21

统一的日志和监控系统
"""

from .logger import (
    UnifiedLogger,
    get_logger,
    bind_context,
    setup_logging,
)

from .metrics import (
    # 系统指标
    cpu_usage,
    memory_usage,
    disk_usage,
    # 应用指标
    http_requests_total,
    http_request_duration,
    http_requests_in_flight,
    http_requests_failed_total,
    # Agent指标
    agent_executions_total,
    agent_execution_duration,
    agent_active_count,
    # 业务指标
    patent_analysis_total,
    llm_tokens_used_total,
    llm_request_duration,
    # 辅助函数
    record_http_request,
    record_agent_execution,
    record_patent_analysis,
    record_llm_request,
    get_metrics_text,
)

__all__ = [
    # 日志
    "UnifiedLogger",
    "get_logger",
    "bind_context",
    "setup_logging",
    # 指标
    "cpu_usage",
    "memory_usage",
    "disk_usage",
    "http_requests_total",
    "http_request_duration",
    "http_requests_in_flight",
    "http_requests_failed_total",
    "agent_executions_total",
    "agent_execution_duration",
    "agent_active_count",
    "patent_analysis_total",
    "llm_tokens_used_total",
    "llm_request_duration",
    # 辅助函数
    "record_http_request",
    "record_agent_execution",
    "record_patent_analysis",
    "record_llm_request",
    "get_metrics_text",
]
