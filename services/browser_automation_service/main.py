#!/usr/bin/env python3
"""
Athena浏览器自动化服务
Browser Automation Service for Athena Platform

提供完整的浏览器自动化API，支持导航、点击、填充、截图等功能

作者: 小诺·双鱼公主
版本: 1.0.0
"""

import signal
import sys
from contextlib import asynccontextmanager

import uvicorn
from api.routes.browser_routes import browser_router
from api.routes.system_routes import system_router
from config.settings import logger, settings
from core.playwright_engine import close_engine
from core.service_registry import (
    ServiceRegistryClient,
    get_heartbeat_manager,
    get_service_registry_client,
)
from core.session_manager import get_session_manager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# 服务启动时间
_start_time = None
_service_registry_client: ServiceRegistryClient | None = None
_heartbeat_manager = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    应用生命周期管理

    管理服务的启动和关闭流程
    """
    global _start_time
    import time

    _start_time = time.time()

    # 启动阶段
    logger.info("=" * 60)
    logger.info("🚀 Athena浏览器自动化服务启动中...")
    logger.info("=" * 60)
    logger.info(f"📋 服务名称: {settings.SERVICE_NAME}")
    logger.info(f"📌 版本: {settings.VERSION}")
    logger.info(f"🌐 监听地址: {settings.HOST}:{settings.PORT}")
    logger.info(f"🧪 浏览器类型: {settings.BROWSER_TYPE}")
    logger.info(f"🎭 无头模式: {settings.BROWSER_HEADLESS}")

    try:
        # 获取会话管理器（初始化）
        session_manager = get_session_manager()

        # 启动会话清理任务
        await session_manager.start_cleanup_task()

        # 🔹 注册服务到统一网关
        if settings.ENVIRONMENT != "test":  # 测试环境不注册
            try:
                global _service_registry_client, _heartbeat_manager

                _service_registry_client = get_service_registry_client()
                await _service_registry_client.register_service()

                # 启动心跳任务
                _heartbeat_manager = get_heartbeat_manager()
                await _heartbeat_manager.start()

            except Exception as e:
                logger.warning(f"⚠️ 服务注册到网关失败，将继续独立运行: {e}")

        logger.info("✅ 服务启动完成!")
        logger.info(f"📖 API文档: http://{settings.HOST}:{settings.PORT}/docs")
        logger.info(f"💊 健康检查: http://{settings.HOST}:{settings.PORT}/health")
        logger.info("=" * 60)

        yield

    except Exception as e:
        logger.error(f"❌ 服务启动失败: {e}")
        raise

    finally:
        # 关闭阶段
        logger.info("=" * 60)
        logger.info("🛑 Athena浏览器自动化服务关闭中...")

        try:
            # 🔹 从网关注册服务
            if _service_registry_client:
                try:
                    await _service_registry_client.deregister_service()
                except Exception as e:
                    logger.warning(f"⚠️ 服务注销失败: {e}")

            # 🔹 停止心跳任务
            if _heartbeat_manager:
                try:
                    await _heartbeat_manager.stop()
                except Exception as e:
                    logger.warning(f"⚠️ 停止心跳任务失败: {e}")

            # 停止会话清理任务
            await session_manager.stop_cleanup_task()

            # 关闭会话管理器
            await session_manager.shutdown()

            # 关闭浏览器引擎
            await close_engine()

            logger.info("✅ 服务已安全关闭")
            logger.info("=" * 60)

        except Exception as e:
            logger.error(f"❌ 关闭服务时出错: {e}")


def create_app() -> FastAPI:
    """
    创建FastAPI应用

    Returns:
        FastAPI: 应用实例
    """
    app = FastAPI(
        title=settings.SERVICE_NAME,
        description="""
        ## Athena浏览器自动化服务

        提供完整的浏览器自动化API，支持：

        - **页面导航**: 导航到指定URL
        - **元素交互**: 点击、填写表单
        - **内容提取**: 获取页面内容
        - **截图**: 全屏或元素截图
        - **JavaScript执行**: 在页面上下文中执行代码
        - **智能任务**: 使用自然语言描述执行复杂任务

        ### 功能特性

        - 基于Playwright的强大浏览器自动化
        - 支持多会话隔离
        - 异步操作，高性能
        - 完善的错误处理和日志
        - RESTful API设计
        """,
        version=settings.VERSION,
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan,
    )

    # 配置CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_origins_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # 注册路由
    app.include_router(system_router)
    app.include_router(browser_router)

    return app


# 创建应用实例
app = create_app()


def handle_signal(signum: int, frame):
    """
    处理系统信号

    Args:
        signum: 信号编号
        frame: 当前帧
    """
    logger.info(f"📶 收到信号: {signum}")
    logger.info("🛑 正在关闭服务...")
    sys.exit(0)


# 注册信号处理器
signal.signal(signal.SIGINT, handle_signal)
signal.signal(signal.SIGTERM, handle_signal)


def main():
    """主函数 - 启动服务"""
    logger.info("🎯 启动Athena浏览器自动化服务...")

    # 配置uvicorn
    uvicorn_config = {
        "host": settings.HOST,
        "port": settings.PORT,
        "log_level": settings.LOG_LEVEL.lower(),
        "access_log": True,
    }

    # 开发模式下使用reload，需要传递字符串形式的app
    if settings.ENVIRONMENT == "development":
        uvicorn.run("main:app", reload=True, **uvicorn_config)
    else:
        uvicorn.run(app, **uvicorn_config)


if __name__ == "__main__":
    main()
