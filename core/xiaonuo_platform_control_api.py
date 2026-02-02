#!/usr/bin/env python3
"""
小诺平台控制API服务
Xiaonuo Platform Control API Service

提供RESTful API接口控制整个平台
"""

import sys
from datetime import datetime
from pathlib import Path


# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))


import uvicorn
from fastapi import BackgroundTasks, FastAPI, HTTPException
from pydantic import BaseModel
from xiaonuo_platform_controller_v2 import EnhancedPlatformController

# 初始化FastAPI应用
app = FastAPI(
    title="小诺平台控制API",
    description="Athena Platform Control API - 小诺的全平台控制能力",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# 初始化平台控制器
controller = None

# ========== 数据模型 ==========

class ServiceControlRequest(BaseModel):
    """服务控制请求"""
    service: str


class ServiceControlResponse(BaseModel):
    """服务控制响应"""
    success: bool
    service: str
    message: str | None = None
    error: str | None = None
    pid: int | None = None


class PlatformSummaryResponse(BaseModel):
    """平台摘要响应"""
    platform: str
    controller: str
    timestamp: str
    features: dict[str, bool]
    summary: dict[str, int]
    by_category: dict[str, dict[str, int]]


# ========== API端点 ==========

@app.get("/")
async def root():
    """根端点"""
    return {
        "service": "小诺平台控制API",
        "controller": "小诺·双鱼公主 v2.0.0",
        "status": "running",
        "timestamp": datetime.now().isoformat(),
        "endpoints": {
            "platform": "/platform",
            "services": "/services",
            "control": "/control/{action}",
            "health": "/health",
            "docs": "/docs"
        }
    }


@app.get("/health")
async def health_check():
    """健康检查端点"""
    return {
        "status": "healthy",
        "controller": "xiaonuo-pisces-princess",
        "nlp_interface": True,
        "platform_control": True,
        "container_management": controller.container_manager.is_available() if controller else False,
        "auto_monitoring": controller.restart_manager.running if controller else False,
        "timestamp": datetime.now().isoformat()
    }


@app.get("/platform", response_model=PlatformSummaryResponse)
async def get_platform_summary():
    """获取平台摘要"""
    if not controller:
        raise HTTPException(status_code=503, detail="控制器未初始化")

    return controller.get_platform_summary()


@app.get("/services")
async def list_services():
    """列出所有服务"""
    if not controller:
        raise HTTPException(status_code=503, detail="控制器未初始化")

    return controller.get_all_status()


@app.get("/services/{service_name}")
async def get_service_status(service_name: str):
    """获取单个服务状态"""
    if not controller:
        raise HTTPException(status_code=503, detail="控制器未初始化")

    return controller.get_service_status(service_name)


@app.post("/control/start")
async def start_service(request: ServiceControlRequest, background_tasks: BackgroundTasks):
    """启动服务"""
    if not controller:
        raise HTTPException(status_code=503, detail="控制器未初始化")

    result = controller.start_service(request.service)
    return result


@app.post("/control/stop")
async def stop_service(request: ServiceControlRequest):
    """停止服务"""
    if not controller:
        raise HTTPException(status_code=503, detail="控制器未初始化")

    result = controller.stop_service(request.service)
    return result


@app.post("/control/restart")
async def restart_service(request: ServiceControlRequest):
    """重启服务"""
    if not controller:
        raise HTTPException(status_code=503, detail="控制器未初始化")

    result = controller.restart_service(request.service)
    return result


@app.post("/control/start-all")
async def start_all_services():
    """启动所有服务"""
    if not controller:
        raise HTTPException(status_code=503, detail="控制器未初始化")

    return controller.start_all()


@app.post("/control/stop-all")
async def stop_all_services():
    """停止所有服务"""
    if not controller:
        raise HTTPException(status_code=503, detail="控制器未初始化")

    return controller.stop_all()


@app.get("/health/services")
async def check_all_services_health():
    """检查所有服务健康状态"""
    if not controller:
        raise HTTPException(status_code=503, detail="控制器未初始化")

    return {
        service: controller.health_checker.check_health(service_info)
        for service, service_info in controller.services.items()
    }


@app.get("/health/services/{service_name}")
async def check_service_health(service_name: str):
    """检查单个服务健康状态"""
    if not controller:
        raise HTTPException(status_code=503, detail="控制器未初始化")

    if service_name not in controller.services:
        raise HTTPException(status_code=404, detail=f"服务不存在: {service_name}")

    return controller.health_checker.check_health(controller.services[service_name])


@app.post("/monitoring/enable")
async def enable_auto_monitoring(interval: int = 30):
    """启用自动监控"""
    if not controller:
        raise HTTPException(status_code=503, detail="控制器未初始化")

    return controller.enable_auto_monitoring(interval)


@app.post("/monitoring/disable")
async def disable_auto_monitoring():
    """禁用自动监控"""
    if not controller:
        raise HTTPException(status_code=503, detail="控制器未初始化")

    return controller.disable_auto_monitoring()


@app.get("/dependencies")
async def get_dependency_graph():
    """获取服务依赖关系图"""
    if not controller:
        raise HTTPException(status_code=503, detail="控制器未初始化")

    return {
        "dependencies": controller.dependency_graph.dependencies,
        "startup_order": controller.dependency_graph.get_startup_order(),
        "reverse_dependencies": controller.dependency_graph.reverse_deps
    }


# ========== 启动和关闭 ==========

def startup():
    """应用启动时初始化"""
    global controller
    controller = EnhancedPlatformController()
    print("✅ 小诺平台控制API已初始化")


def shutdown():
    """应用关闭时清理"""
    global controller
    if controller:
        controller.disable_auto_monitoring()
        print("✅ 小诺平台控制API已关闭")


# 注册生命周期事件
app.add_event_handler("startup", startup)
app.add_event_handler("shutdown", shutdown)


# ========== 主程序 ==========

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="小诺平台控制API服务")
    parser.add_argument("--host", default="0.0.0.0", help="监听地址")
    parser.add_argument("--port", type=int, default=8003, help="监听端口")
    parser.add_argument("--reload", action="store_true", help="自动重载")

    args = parser.parse_args()

    print("=" * 60)
    print("🎀 小诺平台控制API服务")
    print("=" * 60)
    print("启动服务...")
    print(f"地址: http://{args.host}:{args.port}")
    print(f"文档: http://{args.host}:{args.port}/docs")
    print("=" * 60)

    uvicorn.run(
        "xiaonuo_platform_control_api:app",
        host=args.host,
        port=args.port,
        reload=args.reload
    )
