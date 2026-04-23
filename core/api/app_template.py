#!/usr/bin/env python3
from __future__ import annotations
"""
Athena平台FastAPI应用程序模板
FastAPI Application Template for Athena Platform

标准化的FastAPI应用结构和配置

作者: Athena AI系统
创建时间: 2025-12-18
版本: v1.0.0
"""

import logging
import uuid
from typing import Any

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse

from core.security.auth import ALLOWED_ORIGINS

from .standards import (
    APIError,
    APIVersion,
    APIVersionMiddleware,
    ResponseBuilder,
)

logger = logging.getLogger(__name__)


class AthenaFastAPIApp:
    """Athena FastAPI应用程序类"""

    def __init__(
        self,
        title: str = "Athena Platform API",
        description: str = "Athena智能工作平台API",
        version: str = "1.0.0",
        api_version: APIVersion = APIVersion.V1,
        debug: bool = False,
    ):
        self.title = title
        self.description = description
        self.version = version
        self.api_version = api_version
        self.debug = debug

        # 创建FastAPI应用
        self.app = FastAPI(
            title=title,
            description=description,
            version=version,
            docs_url="/docs" if debug else None,
            redoc_url="/redoc" if debug else None,
            openapi_url="/openapi.json" if debug else None,
        )

        # 配置应用
        self._setup_middleware()
        self._setup_exception_handlers()
        self._setup_routes()

    def _setup_middleware(self) -> Any:
        """设置中间件"""
        # CORS中间件
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=ALLOWED_ORIGINS,  # 生产环境应该设置具体的域名
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

        # 信任主机中间件(生产环境)
        if not self.debug:
            self.app.add_middleware(
                TrustedHostMiddleware, allowed_hosts=["localhost", "127.0.0.1", "*.yourdomain.com"]
            )

        # 请求ID中间件
        @self.app.middleware("http")
        async def add_request_id(request: Request, call_next):
            request_id = str(uuid.uuid4())
            request.state.request_id = request_id

            response = await call_next(request)
            response.headers["X-Request-ID"] = request_id
            return response

        # API版本中间件
        version_middleware = APIVersionMiddleware(self.app)
        self.app.add_middleware(lambda app, middleware: middleware(app), version_middleware)

    def _setup_exception_handlers(self) -> Any:
        """设置异常处理器"""

        @self.app.exception_handler(APIError)
        async def api_error_handler(request: Request, error: APIError):
            """API错误处理"""
            request_id = getattr(request.state, "request_id", None)
            response = ResponseBuilder.error(
                error=error, request_id=request_id, api_version=self.api_version
            )
            return JSONResponse(
                content=response.dict(),
                status_code=self._get_http_status(error.error_code),
                headers={"X-API-Version": self.api_version},
            )

        @self.app.exception_handler(HTTPException)
        async def http_exception_handler(request: Request, error: HTTPException):
            """HTTP异常处理"""
            request_id = getattr(request.state, "request_id", None)
            api_error = APIError(
                error_code="HTTP_ERROR",
                message=error.detail,
                error_details={"status_code": error.status_code},
            )
            response = ResponseBuilder.error(
                error=api_error, request_id=request_id, api_version=self.api_version
            )
            return JSONResponse(
                content=response.dict(),
                status_code=error.status_code,
                headers={"X-API-Version": self.api_version},
            )

        @self.app.exception_handler(Exception)
        async def general_exception_handler(request: Request, error: Exception):
            """通用异常处理"""
            logger.error(f"未处理的异常: {error!s}", exc_info=True)
            request_id = getattr(request.state, "request_id", None)
            response = ResponseBuilder.error(
                error=error,
                request_id=request_id,
                api_version=self.api_version,
                include_stack=self.debug,
            )
            return JSONResponse(
                content=response.dict(),
                status_code=500,
                headers={"X-API-Version": self.api_version},
            )

    def _setup_routes(self) -> Any:
        """设置基础路由"""

        @self.app.get("/", tags=["Root"])
        async def root():
            """根路径"""
            return ResponseBuilder.success(
                data={
                    "title": self.title,
                    "description": self.description,
                    "version": self.version,
                    "api_version": self.api_version,
                    "status": "running",
                },
                message="Athena平台API正在运行",
                api_version=self.api_version,
            )

        @self.app.get("/health", tags=["Health"])
        async def health_check():
            """健康检查"""
            return ResponseBuilder.success(
                data={
                    "status": "healthy",
                    "timestamp": "2025-12-18T23:50:00Z",
                    "uptime": "0h 0m 0s",
                    "version": self.version,
                    "api_version": self.api_version,
                },
                message="服务健康状态正常",
                api_version=self.api_version,
            )

        @self.app.get("/version", tags=["Version"])
        async def get_version_info():
            """获取版本信息"""
            return ResponseBuilder.success(
                data={
                    "app_version": self.version,
                    "api_version": self.api_version,
                    "python_version": "3.14+",
                    "fastapi_version": "0.104+",
                },
                message="版本信息",
                api_version=self.api_version,
            )

    def _get_http_status(self, error_code: str) -> int:
        """获取HTTP状态码"""
        from .standards import HTTP_STATUS_MAPPING, ErrorCode

        return HTTP_STATUS_MAPPING.get(ErrorCode(error_code), 500)

    def include_router(self, router, prefix: str = "", tags: list | None = None) -> None:
        """添加路由器"""
        self.app.include_router(router, prefix=prefix, tags=tags)

    def get_app(self) -> FastAPI:
        """获取FastAPI应用实例"""
        return self.app


# ============================================================================
# 便捷函数
# ============================================================================


def create_athena_app(
    title: str = "Athena Platform API",
    description: str = "Athena智能工作平台API",
    version: str = "1.0.0",
    api_version: APIVersion = APIVersion.V1,
    debug: bool = False,
) -> FastAPI:
    """创建Athena FastAPI应用的便捷函数"""
    app_builder = AthenaFastAPIApp(
        title=title, description=description, version=version, api_version=api_version, debug=debug
    )
    return app_builder.get_app()


def success_response(data: Any = None, message: str = "操作成功") -> Any:
    """创建成功响应的便捷函数"""
    return ResponseBuilder.success(data=data, message=message)


def error_response(error: Exception, message: Optional[str] = None) -> Any:
    """创建错误响应的便捷函数"""
    if isinstance(error, APIError):
        return ResponseBuilder.error(error=error)
    else:
        api_error = APIError(error_code="UNKNOWN_ERROR", message=message or "未知错误")
        return ResponseBuilder.error(error=api_error)


# ============================================================================
# 应用工厂模式
# ============================================================================


class AppFactory:
    """应用程序工厂"""

    @staticmethod
    def create_app(config: dict[str, Any]) -> FastAPI:
        """创建应用实例"""
        return create_athena_app(
            title=config.get("title", "Athena Platform API"),
            description=config.get("description", "Athena智能工作平台API"),
            version=config.get("version", "1.0.0"),
            api_version=APIVersion(config.get("api_version", "v1")),
            debug=config.get("debug", False),
        )

    @staticmethod
    def create_production_app() -> FastAPI:
        """创建生产环境应用"""
        config = {
            "title": "Athena Platform API",
            "description": "Athena智能工作平台生产环境API",
            "version": "1.0.0",
            "api_version": "v1",
            "debug": False,
        }
        return AppFactory.create_app(config)

    @staticmethod
    def create_development_app() -> FastAPI:
        """创建开发环境应用"""
        config = {
            "title": "Athena Platform API (Dev)",
            "description": "Athena智能工作平台开发环境API",
            "version": "1.0.0-dev",
            "api_version": "v1",
            "debug": True,
        }
        return AppFactory.create_app(config)
