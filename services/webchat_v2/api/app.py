#!/usr/bin/env python3
"""
FastAPI应用入口
WebChat V2 Gateway服务

作者: Athena平台团队
创建时间: 2025-01-31
版本: 2.0.2
"""

from contextlib import asynccontextmanager
from fastapi import APIRouter, FastAPI, WebSocket, Query
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional

from ..identity import XiaonuoIdentityManager
from ..modules import PlatformModuleRegistry, PlatformModuleInvoker, XiaonuoIntentRouter
from ..gateway.server import WebChatGatewayServer
from ..config.settings import settings
from ..logging_config import setup_logging, get_logger


# 初始化日志（使用配置文件中的日志轮转设置）
setup_logging(
    log_level=settings.log_level,
    log_file=settings.log_file,
    max_bytes=settings.log_max_bytes,
    backup_count=settings.log_backup_count,
)
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时执行
    logger.info("=" * 60)
    logger.info("WebChat V2 Gateway 服务启动")
    logger.info("=" * 60)
    logger.info(f"版本: 2.0.2")
    logger.info(f"WebSocket端点: ws://localhost:{settings.port}/gateway/ws")
    logger.info(f"健康检查: http://localhost:{settings.port}/gateway/health")
    logger.info(f"模块列表: http://localhost:{settings.port}/gateway/modules")
    logger.info(f"配置:")
    logger.info(f"  - 心跳间隔: {settings.heartbeat_interval}秒")
    logger.info(f"  - 消息大小限制: {settings.max_message_size}字节")
    logger.info(f"  - 模块调用超时: {settings.module_invoke_timeout}秒")
    logger.info(f"  - 身份持久化: {settings.identity_persistence_path}")
    logger.info("=" * 60)

    yield

    # 关闭时执行
    logger.info("WebChat V2 Gateway 服务关闭")


# 创建全局实例（应用配置）
identity_manager = XiaonuoIdentityManager(
    persistence_path=settings.identity_persistence_path
)
module_registry = PlatformModuleRegistry()
module_invoker = PlatformModuleInvoker(
    module_registry,
    identity_manager,
    default_timeout=settings.module_invoke_timeout
)
intent_router = XiaonuoIntentRouter(module_invoker)
gateway_server = WebChatGatewayServer(
    identity_manager=identity_manager,
    intent_router=intent_router,
    platform_invoker=module_invoker,
    heartbeat_interval=settings.heartbeat_interval,
    max_message_size=settings.max_message_size,
)


# 创建FastAPI应用
app = FastAPI(
    title="WebChat V2 Gateway",
    description="基于Gateway架构的WebChat服务",
    version="2.0.2",
    lifespan=lifespan,
)

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# 创建路由
gateway_router = APIRouter(prefix="/gateway", tags=["Gateway"])


@gateway_router.websocket("/ws")
async def gateway_websocket(
    websocket: WebSocket,
    user_id: str = Query(...),
    session_id: Optional[str] = Query(None),
    token: Optional[str] = Query(None),
):
    """
    Gateway WebSocket端点（支持JWT认证）

    Args:
        websocket: WebSocket连接
        user_id: 用户ID（必需）
        session_id: 会话ID（可选）
        token: JWT认证token（可选，用于生产环境）
    """
    await gateway_server.connect(
        websocket=websocket,
        user_id=user_id,
        session_id=session_id,
        token=token,
    )


@gateway_router.get("/health")
async def health_check():
    """健康检查"""
    return {
        "status": "healthy",
        "service": "WebChat V2 Gateway",
        "version": "2.0.2",
        "active_sessions": gateway_server.get_active_count(),
    }


@gateway_router.get("/modules")
async def list_modules():
    """列出可用模块"""
    modules = module_registry.list_modules()

    return {
        "modules": [
            {
                "name": m.name,
                "display_name": m.display_name,
                "description": m.description,
                "category": m.category,
                "actions": m.actions,
            }
            for m in modules
        ],
        "categories": module_registry.get_categories(),
    }


# 注册路由
app.include_router(gateway_router)


# 根路径
@app.get("/")
async def root():
    """根路径"""
    return {
        "service": "WebChat V2 Gateway",
        "version": "2.0.2",
        "status": "running",
        "endpoints": {
            "websocket": "/gateway/ws",
            "health": "/gateway/health",
            "modules": "/gateway/modules",
        },
        "features": {
            "authentication": "JWT support (ready)",
            "thread_safety": "asyncio.Lock protection",
            "resource_management": "heartbeat task tracking",
            "input_validation": "enhanced frame validation",
            "data_persistence": "JSON file storage",
            "logging": "structured logging with exception tracking",
        },
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_level="info",
    )
