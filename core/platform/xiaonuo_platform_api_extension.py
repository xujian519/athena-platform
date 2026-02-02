#!/usr/bin/env python3
"""
小诺平台控制API扩展
Xiaonuo Platform Control API Extension

为统一网关添加平台控制API端点

作者: 小诺·双鱼公主
版本: v1.0.0
创建: 2025-12-30
"""

# 导入平台控制器
import sys
from pathlib import Path

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

# 确保可以导入platform模块
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from core.platform.xiaonuo_platform_controller_v3 import (
    OrchestrationRequest,
    ServiceAction,
    ServiceControlRequest,
    ServiceControlResponse,
    get_platform_controller,
)

# 创建路由器
router = APIRouter(
    prefix="/platform",
    tags=["platform-control"],
    responses={404: {"description": "Not found"}},
)


# ==================== API端点 ====================


@router.get("/dashboard")
async def get_platform_dashboard():
    """
    获取平台监控仪表板

    返回整个平台的状态概览、服务健康状况、告警和建议。
    """
    controller = get_platform_controller()
    return await controller.get_platform_dashboard()


@router.get("/services")
async def get_all_services():
    """
    获取所有服务状态

    返回平台中所有服务的详细状态信息。
    """
    controller = get_platform_controller()
    return await controller.get_all_services_status()


@router.get("/services/{service_name}")
async def get_service_status(service_name: str):
    """
    获取指定服务状态

    - **service_name**: 服务名称(如 xiaona, yunxi, xiaochen)
    """
    controller = get_platform_controller()
    status = await controller.get_service_status(service_name)

    if "error" in status:
        raise HTTPException(status_code=404, detail=status["error"])

    return status


@router.post("/services/control")
async def control_service(request: ServiceControlRequest):
    """
    控制服务(启动/停止/重启)

    - **service**: 服务名称(如 xiaona, yunxi, xiaochen)
    - **action**: 操作类型(start/stop/restart)
    - **force**: 强制执行(默认false)

    注意:不能停止小诺自己的服务(xiaonuo)
    """
    controller = get_platform_controller()

    if request.action == ServiceAction.START:
        result = await controller.start_service(request.service)
    elif request.action == ServiceAction.STOP:
        result = await controller.stop_service(request.service)
    elif request.action == ServiceAction.RESTART:
        result = await controller.restart_service(request.service)
    else:
        raise HTTPException(status_code=400, detail=f"不支持的操作: {request.action}")

    return result


@router.post("/services/{service_name}/start")
async def start_service(service_name: str):
    """启动指定服务"""
    controller = get_platform_controller()
    return await controller.start_service(service_name)


@router.post("/services/{service_name}/stop")
async def stop_service(service_name: str):
    """停止指定服务"""
    controller = get_platform_controller()
    return await controller.stop_service(service_name)


@router.post("/services/{service_name}/restart")
async def restart_service(service_name: str):
    """重启指定服务"""
    controller = get_platform_controller()
    return await controller.restart_service(service_name)


class AgentCommunicateRequest(BaseModel):
    """智能体通信请求"""

    agent_name: str = Field(..., description="智能体名称")
    message: str = Field(..., description="发送的消息")
    context: dict | None = None


@router.post("/agents/communicate")
async def communicate_with_agent(request: AgentCommunicateRequest):
    """
    与指定智能体通信

    - **agent_name**: 智能体名称(xiaona, yunxi, xiaochen)
    - **message**: 要发送的消息
    - **context**: 可选的上下文信息

    将消息转发给指定的智能体并返回响应。
    """
    controller = get_platform_controller()
    return await controller.communicate_with_agent(
        request.agent_name, request.message, request.context
    )


@router.post("/agents/orchestrate")
async def orchestrate_agents(request: OrchestrationRequest):
    """
    编排多个智能体执行任务

    - **task**: 要执行的任务描述
    - **agents**: 参与的智能体列表
    - **parallel**: 是否并行执行(默认串行)
    - **timeout**: 超时时间(秒,默认300)

    支持串行或并行地让多个智能体协同工作。
    """
    controller = get_platform_controller()
    return await controller.orchestrate_agents(
        request.task, request.agents, request.parallel, request.timeout
    )


@router.get("/agents")
async def list_agents():
    """获取所有可用的智能体列表"""
    controller = get_platform_controller()

    agents = []
    for name, info in controller.services.items():
        if info["type"].value == "agent":
            status = await controller.get_service_status(name)
            agents.append(
                {
                    "name": name,
                    "full_name": info["name"],
                    "port": info["port"],
                    "description": info["description"],
                    "status": status["status"],
                    "healthy": status["healthy"],
                }
            )

    return {"total": len(agents), "agents": agents}


@router.get("/health")
async def platform_health_check():
    """平台控制器健康检查"""
    controller = get_platform_controller()
    all_status = await controller.get_all_services_status()

    return {
        "controller": controller.name,
        "version": controller.version,
        "status": "healthy",
        "services": all_status["summary"],
        "timestamp": all_status["controller"]["timestamp"],
    }


# ==================== 导出函数 ====================


def setup_platform_control_api(app) -> None:
    """
    将平台控制API添加到FastAPI应用

    使用方法:
    ```python
    setup_platform_control_api(app)
    ```
    """
    app.include_router(router)
    return app
