#!/usr/bin/env python3
"""
健康检查API端点
Health Check API Endpoint

提供HTTP接口访问系统健康状态。

作者: Athena平台团队
创建时间: 2026-02-03
版本: v1.0.0
"""

from datetime import datetime
from typing import Any

from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse

from core.legal_world_model.health_check import (
    ComponentHealth,
    HealthStatus,
    SystemHealthReport,
    check_health,
)

router = APIRouter(prefix="/health", tags=["health"])


@router.get("/", response_model=dict[str, Any])
async def get_health_root():
    """
    获取简化健康状态

    Returns:
        简化的健康状态字典
    """
    try:
        report = await check_health()

        return {
            "status": report.overall_status.value,
            "timestamp": report.timestamp.isoformat(),
            "components": {
                name: comp.status.value
                for name, comp in report.components.items()
            },
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"健康检查失败: {e}")


@router.get("/detailed", response_model=dict[str, Any])
async def get_health_detailed():
    """
    获取详细健康状态

    Returns:
        详细的健康状态字典
    """
    try:
        report = await check_health()
        return report.to_dict()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"健康检查失败: {e}")


@router.get("/components")
async def get_components_health():
    """
    获取各组件健康状态

    Returns:
        各组件的健康状态列表
    """
    try:
        report = await check_health()

        components_list = []
        for name, comp in report.components.items():
            components_list.append({
                "name": name,
                "status": comp.status.value,
                "message": comp.message,
                "response_time_ms": comp.response_time_ms,
                "timestamp": comp.timestamp.isoformat(),
            })

        return {
            "components": components_list,
            "total": len(components_list),
            "healthy": report.healthy_components,
            "degraded": report.degraded_components,
            "unhealthy": report.unhealthy_components,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取组件状态失败: {e}")


@router.get("/ping")
async def ping():
    """
    简单ping端点

    用于负载均衡器健康检查。
    """
    return {
        "status": "ok",
        "timestamp": datetime.now().isoformat(),
    }


@router.post("/test/{component_name}")
async def test_component(component_name: str):
    """
    测试特定组件

    Args:
        component_name: 组件名称 (neo4j, postgres, qdrant, cache)

    Returns:
        测试结果
    """
    allowed_components = ["neo4j", "postgres", "qdrant", "cache"]

    if component_name not in allowed_components:
        raise HTTPException(
            status_code=400,
            detail=f"未知的组件: {component_name}. "
            f"允许的组件: {', '.join(allowed_components)}",
        )

    try:
        report = await check_health()

        if component_name in report.components:
            comp = report.components[component_name]
            return {
                "component": component_name,
                "status": comp.status.value,
                "message": comp.message,
                "response_time_ms": comp.response_time_ms,
                "timestamp": comp.timestamp.isoformat(),
            }
        else:
            raise HTTPException(
                status_code=404,
                detail=f"组件 {component_name} 未在报告中找到"
            )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"测试组件失败: {e}")


# 便捷函数：创建路由
def create_health_router() -> APIRouter:
    """
    创建健康检查路由

    Returns:
        配置好的APIRouter
    """
    return router


__all__ = [
    "router",
    "create_health_router",
    "get_health_root",
    "get_health_detailed",
    "get_components_health",
    "ping",
    "test_component",
]
