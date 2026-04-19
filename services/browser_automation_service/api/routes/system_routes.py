#!/usr/bin/env python3
"""
系统路由
System Routes for Browser Automation Service

提供健康检查、状态查询、配置获取等系统端点

作者: 小诺·双鱼公主
版本: 1.0.0
"""

import time
from datetime import datetime
from typing import Any

from config.settings import logger, settings
from fastapi import APIRouter

from api.models.responses import (
    ConfigResponse,
    HealthResponse,
    StatusResponse,
)

system_router = APIRouter(tags=["系统"])

# 服务启动时间
_start_time = time.time()


@system_router.get(
    "/health",
    response_model=HealthResponse,
    summary="健康检查",
    description="检查服务是否正常运行",
)
async def health_check() -> HealthResponse:
    """
    健康检查端点

    Returns:
        HealthResponse: 服务健康状态
    """
    try:
        # 获取活跃会话数
        from core.session_manager import get_session_manager

        session_manager = get_session_manager()
        active_sessions = session_manager.active_count

        return HealthResponse(
            status="healthy",
            service=settings.SERVICE_NAME,
            version=settings.VERSION,
            timestamp=datetime.now(),
            uptime_seconds=time.time() - _start_time,
            active_sessions=active_sessions,
        )

    except Exception as e:
        logger.error(f"❌ 健康检查失败: {e}")
        return HealthResponse(
            status="unhealthy",
            service=settings.SERVICE_NAME,
            version=settings.VERSION,
            timestamp=datetime.now(),
        )


@system_router.get(
    "/api/v1/status",
    response_model=StatusResponse,
    summary="获取状态",
    description="获取服务当前状态信息",
)
async def get_status() -> StatusResponse:
    """
    获取服务状态

    Returns:
        StatusResponse: 服务状态
    """
    try:
        from core.browser_manager import get_browser_manager

        manager = await get_browser_manager()
        status_dict = await manager.get_status()

        # 字段映射：total_sessions -> total_sessions_created
        return StatusResponse(
            success=status_dict.get("success", True),
            active_sessions=status_dict.get("active_sessions", 0),
            total_sessions_created=status_dict.get("total_sessions", 0),
            sessions=status_dict.get("sessions", []),
        )

    except Exception as e:
        logger.error(f"❌ 获取状态失败: {e}")
        return StatusResponse(
            success=False,
            active_sessions=0,
            total_sessions=0,
            sessions=[],
        )


@system_router.get(
    "/api/v1/config",
    response_model=ConfigResponse,
    summary="获取配置",
    description="获取服务当前配置信息",
)
async def get_config() -> ConfigResponse:
    """
    获取服务配置

    Returns:
        ConfigResponse: 配置信息
    """
    try:
        # 返回非敏感配置信息
        config_dict = {
            "service_name": settings.SERVICE_NAME,
            "version": settings.VERSION,
            "browser_type": settings.BROWSER_TYPE,
            "browser_headless": settings.BROWSER_HEADLESS,
            "max_concurrent_sessions": settings.MAX_CONCURRENT_SESSIONS,
            "session_timeout": settings.SESSION_TIMEOUT,
            "max_concurrent_tasks": settings.MAX_CONCURRENT_TASKS,
            "task_timeout": settings.TASK_TIMEOUT,
            "enable_screenshots": settings.ENABLE_SCREENSHOTS,
            "enable_video_recording": settings.ENABLE_VIDEO_RECORDING,
            "enable_websocket": settings.ENABLE_WEBSOCKET,
            "enable_metrics": settings.ENABLE_METRICS,
            "log_level": settings.LOG_LEVEL,
        }

        return ConfigResponse(success=True, config=config_dict)

    except Exception as e:
        logger.error(f"❌ 获取配置失败: {e}")
        return ConfigResponse(success=False, config={"error": str(e)})


@system_router.get(
    "/",
    summary="根路径",
    description="服务基本信息",
)
async def root() -> dict[str, Any]:
    """
    根路径端点

    Returns:
        dict: 服务基本信息
    """
    return {
        "service": settings.SERVICE_NAME,
        "version": settings.VERSION,
        "status": "running",
        "description": "Athena浏览器自动化服务 - Browser Automation Service",
        "author": "小诺·双鱼公主",
        "endpoints": {
            "health": "/health",
            "docs": "/docs",
            "api_v1_navigate": "/api/v1/navigate",
            "api_v1_click": "/api/v1/click",
            "api_v1_fill": "/api/v1/fill",
            "api_v1_screenshot": "/api/v1/screenshot",
            "api_v1_content": "/api/v1/content",
            "api_v1_evaluate": "/api/v1/evaluate",
            "api_v1_task": "/api/v1/task",
            "api_v1_status": "/api/v1/status",
            "api_v1_config": "/api/v1/config",
        },
        "timestamp": datetime.now().isoformat(),
    }


# 导出
__all__ = ["system_router"]
