#!/usr/bin/env python3
"""
通信模块监控API端点
Communication Module Monitoring API Endpoints

提供Prometheus指标暴露的HTTP端点

作者: Athena AI系统
创建时间: 2026-01-25
版本: 1.0.0
"""

from __future__ import annotations
import logging

from fastapi import APIRouter, status
from fastapi.responses import PlainTextResponse

from core.communication.monitoring import PROMETHEUS_AVAILABLE, get_metrics

logger = logging.getLogger(__name__)

# 创建路由器
router = APIRouter(prefix="/metrics", tags=["监控"])


@router.get("", response_class=PlainTextResponse)
@router.get("/", response_class=PlainTextResponse)
async def get_metrics():
    """
    获取Prometheus格式的监控指标

    返回Prometheus格式的指标数据,用于Prometheus服务器抓取。

    Returns:
        PlainTextResponse: Prometheus格式的指标数据
    """
    if not PROMETHEUS_AVAILABLE:
        return PlainTextResponse(
            content="# Prometheus监控不可用\n",
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            media_type="text/plain",
        )

    metrics = get_metrics()
    metrics_text = metrics.get_metrics_text()

    return PlainTextResponse(
        content=metrics_text, status_code=status.HTTP_200_OK, media_type=metrics.get_content_type()
    )


@router.get("/health")
async def metrics_health():
    """
    监控服务健康检查

    Returns:
        dict: 健康状态信息
    """
    return {
        "service": "athena-communication-metrics",
        "status": "healthy" if PROMETHEUS_AVAILABLE else "degraded",
        "prometheus_available": PROMETHEUS_AVAILABLE,
    }


@router.get("/info")
async def metrics_info():
    """
    监控服务信息

    Returns:
        dict: 监控服务信息
    """
    metrics = get_metrics()

    return {
        "service": "athena-communication-metrics",
        "version": "1.0.0",
        "enabled": metrics.is_enabled(),
        "metrics": {
            "message_sent_total": "发送消息总数",
            "message_received_total": "接收消息总数",
            "connection_acquired_total": "从连接池获取连接总数",
            "connection_released_total": "释放连接回连接池总数",
            "active_connections": "当前活跃连接数",
            "idle_connections": "当前空闲连接数",
            "message_processing_seconds": "消息处理时间分布",
            "batch_processing_seconds": "批处理时间分布",
            "errors_total": "错误总数",
            "validation_failures_total": "输入验证失败总数",
        },
    }


# 导出路由器
__all__ = ["router"]
