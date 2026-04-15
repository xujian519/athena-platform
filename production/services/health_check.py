#!/usr/bin/env python3
"""
小诺健康检查服务
Xiaonuo Health Check Service

提供生产级健康检查端点，支持：
- 基础健康检查
- 详细健康检查
- 就绪检查
- 存活检查

作者: Athena团队
创建时间: 2026-02-09
版本: v1.0.0
"""

from __future__ import annotations
import os
import time
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from fastapi import Depends, FastAPI, Header, HTTPException, status
from pydantic import BaseModel

# 导入日志配置
from production.logging.xiaonuo_logging import get_health_logger

# =============================================================================
# 认证配置
# =============================================================================

# API密钥配置（从环境变量读取）
HEALTH_CHECK_API_KEY = os.getenv("HEALTH_CHECK_API_KEY", "")


async def verify_api_key(x_api_key: str | None = Header(None, alias="X-API-Key")) -> bool:
    """
    验证API密钥

    参数:
        x_api_key: API密钥

    返回:
        bool: 认证是否成功

    异常:
        HTTPException: 403 - 当API密钥无效时
    """
    # 如果配置了API密钥，则必须验证
    if HEALTH_CHECK_API_KEY:
        if x_api_key != HEALTH_CHECK_API_KEY:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Invalid or missing API Key"
            )
    # 如果未配置API密钥，则允许访问（开发环境）
    return True


# =============================================================================
# 应用生命周期管理
# =============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    应用生命周期管理

    处理应用启动和关闭事件，替代已弃用的@app.on_event

    参数:
        app: FastAPI应用实例

    返回:
        AsyncGenerator: 异步生成器
    """
    logger = get_health_logger()

    # 启动时执行
    logger.info("🏥 小诺健康检查服务已启动")
    logger.info(f"   启动时间: {datetime.now().isoformat()}")

    yield

    # 关闭时执行
    logger.info("🏥 小诺健康检查服务正在关闭")


# 创建FastAPI应用
app = FastAPI(
    title="小诺健康检查服务",
    description="Xiaonuo Pisces Health Check Service",
    version="1.0.0",
    docs_url="/health/docs",
    redoc_url="/health/redoc",
    lifespan=lifespan
)


# =============================================================================
# 数据模型
# =============================================================================

@dataclass
class HealthStatus:
    """健康状态"""

    healthy: bool
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    version: str = "1.0.0"
    uptime: float = 0.0

    # 组件状态
    components: dict[str, bool] = field(default_factory=dict)

    # 性能指标
    metrics: dict[str, Any] = field(default_factory=dict)

    # 错误信息
    errors: list[str] = field(default_factory=list)


class HealthResponse(BaseModel):
    """健康检查响应"""

    status: str  # healthy, degraded, unhealthy
    timestamp: str
    version: str
    uptime: float
    components: dict[str, dict[str, Any]]
    metrics: dict[str, Any]


class ReadinessResponse(BaseModel):
    """就绪检查响应"""

    ready: bool
    timestamp: str
    checks: dict[str, bool]


class LivenessResponse(BaseModel):
    """存活检查响应"""

    alive: bool
    timestamp: str
    uptime: float


# =============================================================================
# 全局状态
# =============================================================================

# 服务启动时间
START_TIME = time.time()

# 组件状态
COMPONENT_STATUS = {
    "memory": True,
    "collaboration": True,
    "api": True,
    "websocket": True,
    "scheduling": True,
}


# =============================================================================
# 辅助函数
# =============================================================================

def get_uptime() -> float:
    """获取运行时间"""
    return time.time() - START_TIME


async def check_component(component_name: str) -> tuple[bool, str | None]:
    """检查单个组件状态"""
    try:
        # 这里添加实际的组件检查逻辑
        if component_name == "memory":
            # 检查记忆系统
            return True, None

        elif component_name == "collaboration":
            # 检查协作系统
            return True, None

        elif component_name == "api":
            # 检查API服务
            return True, None

        elif component_name == "websocket":
            # 检查WebSocket服务
            return True, None

        elif component_name == "scheduling":
            # 检查任务调度
            return True, None

        else:
            return False, f"未知组件: {component_name}"

    except Exception as e:
        return False, str(e)


async def collect_metrics() -> dict[str, Any]:
    """收集性能指标"""
    return {
        "uptime": get_uptime(),
        "memory_usage": 0,  # 实际实现需要获取真实内存使用
        "cpu_usage": 0.0,   # 实际实现需要获取真实CPU使用
        "active_connections": 0,
        "requests_processed": 0,
        "tasks_completed": 0,
        "tasks_failed": 0,
    }


# =============================================================================
# API端点
# =============================================================================

@app.get("/health", response_model=HealthResponse, tags=["Health"], dependencies=[Depends(verify_api_key)])
async def health_check(detailed: bool = False):
    """
    健康检查端点

    参数:
        detailed: 是否返回详细信息

    返回:
        HealthResponse: 健康状态响应
    """
    try:
        # 检查所有组件
        components = {}
        all_healthy = True
        errors = []

        for component_name in COMPONENT_STATUS.keys():
            is_healthy, error = await check_component(component_name)
            components[component_name] = {
                "healthy": is_healthy,
                "error": error,
            }

            if not is_healthy:
                all_healthy = False
                if error:
                    errors.append(f"{component_name}: {error}")

        # 收集性能指标
        metrics = await collect_metrics() if detailed else {}

        # 确定整体状态
        if all_healthy:
            status_str = "healthy"
        elif len(errors) < len(COMPONENT_STATUS):
            status_str = "degraded"
        else:
            status_str = "unhealthy"

        return HealthResponse(
            status=status_str,
            timestamp=datetime.now().isoformat(),
            version="1.0.0",
            uptime=get_uptime(),
            components=components,
            metrics=metrics,
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"健康检查失败: {str(e)}"
        ) from e


@app.get("/health/ready", response_model=ReadinessResponse, tags=["Health"])
async def readiness_check():
    """
    就绪检查端点

    检查服务是否准备好接收请求
    """
    checks = {}

    # 检查关键组件
    for component_name in ["memory", "api", "scheduling"]:
        is_healthy, _ = await check_component(component_name)
        checks[component_name] = is_healthy

    # 所有关键组件都健康才算就绪
    ready = all(checks.values())

    return ReadinessResponse(
        ready=ready,
        timestamp=datetime.now().isoformat(),
        checks=checks,
    )


@app.get("/health/live", response_model=LivenessResponse, tags=["Health"])
async def liveness_check():
    """
    存活检查端点

    检查服务是否仍在运行（用于Kubernetes liveness probe）
    """
    return LivenessResponse(
        alive=True,
        timestamp=datetime.now().isoformat(),
        uptime=get_uptime(),
    )


@app.get("/health/detailed", response_model=HealthResponse, tags=["Health"])
async def detailed_health_check():
    """
    详细健康检查端点

    返回完整的健康状态和性能指标
    """
    return await health_check(detailed=True)


# =============================================================================
# 主函数
# =============================================================================

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        app,
        host="127.0.0.1",
        port=8099,
        log_level="info",
        access_log=True,
    )
