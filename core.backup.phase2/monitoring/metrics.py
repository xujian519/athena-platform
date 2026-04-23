"""
Prometheus监控指标

> 版本: v1.0
> 更新: 2026-04-21
> 说明: 统一的监控指标定义和收集
"""

from prometheus_client import (
    Counter,
    Histogram,
    Gauge,
    CollectorRegistry,
    generate_latest,
)
from typing import Dict, Any


# ==================== 系统指标 ====================

cpu_usage = Gauge(
    'cpu_usage_percent',
    'CPU使用率（%）'
)

memory_usage = Gauge(
    'memory_usage_bytes',
    '内存使用量（字节）'
)

disk_usage = Gauge(
    'disk_usage_percent',
    '磁盘使用率（%）'
)


# ==================== 应用指标 ====================

http_requests_total = Counter(
    'http_requests_total',
    'HTTP请求总数',
    ['method', 'endpoint', 'status']
)

http_request_duration = Histogram(
    'http_request_duration_seconds',
    'HTTP请求耗时（秒）',
    ['method', 'endpoint']
)

http_requests_in_flight = Gauge(
    'http_requests_in_flight',
    '处理中的HTTP请求数'
)

http_requests_failed_total = Counter(
    'http_requests_failed_total',
    '失败的HTTP请求数',
    ['method', 'endpoint', 'error_type']
)


# ==================== Agent指标 ====================

agent_executions_total = Counter(
    'agent_executions_total',
    'Agent执行总数',
    ['agent_name', 'status']
)

agent_execution_duration = Histogram(
    'agent_execution_duration_seconds',
    'Agent执行耗时（秒）',
    ['agent_name']
)

agent_active_count = Gauge(
    'agent_active_count',
    '活跃Agent数量'
)


# ==================== 业务指标 ====================

patent_analysis_total = Counter(
    'patent_analysis_total',
    '专利分析总数',
    ['analysis_type', 'status']
)

llm_tokens_used_total = Counter(
    'llm_tokens_used_total',
    'LLM Token使用总量',
    ['model', 'operation']
)

llm_request_duration = Histogram(
    'llm_request_duration_seconds',
    'LLM请求耗时（秒）',
    ['model', 'operation']
)


# ==================== 辅助函数 ====================

def record_http_request(
    method: str,
    endpoint: str,
    status_code: int,
    duration: float
) -> None:
    """
    记录HTTP请求指标
    
    参数:
        method: HTTP方法
        endpoint: 端点路径
        status_code: HTTP状态码
        duration: 请求耗时（秒）
    """
    http_requests_total.labels(
        method=method,
        endpoint=endpoint,
        status=status_code
    ).inc()
    
    http_request_duration.labels(
        method=method,
        endpoint=endpoint
    ).observe(duration)
    
    if status_code >= 400:
        http_requests_failed_total.labels(
            method=method,
            endpoint=endpoint,
            error_type="http_error"
        ).inc()


def record_agent_execution(
    agent_name: str,
    status: str,
    duration: float
) -> None:
    """
    记录Agent执行指标
    
    参数:
        agent_name: Agent名称
        status: 执行状态（success/failed）
        duration: 执行耗时（秒）
    """
    agent_executions_total.labels(
        agent_name=agent_name,
        status=status
    ).inc()
    
    agent_execution_duration.labels(
        agent_name=agent_name
    ).observe(duration)


def record_patent_analysis(
    analysis_type: str,
    status: str
) -> None:
    """
    记录专利分析指标
    
    参数:
        analysis_type: 分析类型
        status: 分析状态
    """
    patent_analysis_total.labels(
        analysis_type=analysis_type,
        status=status
    ).inc()


def record_llm_request(
    model: str,
    operation: str,
    duration: float,
    tokens_used: int = 0
) -> None:
    """
    记录LLM请求指标
    
    参数:
        model: 模型名称
        operation: 操作类型
        duration: 请求耗时（秒）
        tokens_used: Token使用量
    """
    llm_request_duration.labels(
        model=model,
        operation=operation
    ).observe(duration)
    
    if tokens_used > 0:
        llm_tokens_used_total.labels(
            model=model,
            operation=operation
        ).inc(tokens_used)


def get_metrics_text() -> bytes:
    """
    获取Prometheus指标文本
    
    返回:
        Prometheus格式的指标文本
    """
    return generate_latest()


__all__ = [
    # 系统指标
    "cpu_usage",
    "memory_usage",
    "disk_usage",
    # 应用指标
    "http_requests_total",
    "http_request_duration",
    "http_requests_in_flight",
    "http_requests_failed_total",
    # Agent指标
    "agent_executions_total",
    "agent_execution_duration",
    "agent_active_count",
    # 业务指标
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
