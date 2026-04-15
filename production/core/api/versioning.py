#!/usr/bin/env python3
"""
Athena平台API版本控制系统
API Versioning System for Athena Platform

创建时间: 2025-12-29
功能: 提供完整的API版本控制、路由、兼容性管理
"""

from __future__ import annotations
import logging
import re
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

from fastapi import APIRouter, FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

# 配置日志
logger = logging.getLogger(__name__)


class APIVersion(str, Enum):
    """API版本枚举"""

    V1 = "v1"
    V2 = "v2"
    LATEST = "latest"


class DeprecationStatus(str, Enum):
    """弃用状态"""

    ACTIVE = "active"  # 活跃版本
    DEPRECATED = "deprecated"  # 已弃用
    SUNSET = "sunset"  # 即将下线
    RETIRED = "retired"  # 已退役


@dataclass
class VersionInfo:
    """版本信息"""

    version: APIVersion
    status: DeprecationStatus
    released_at: datetime
    deprecated_at: datetime | None = None
    sunset_at: datetime | None = None
    retired_at: datetime | None = None
    description: str = ""
    migration_guide: str | None = None
    breaking_changes: list[str] = field(default_factory=list)
    new_features: list[str] = field(default_factory=list)


@dataclass
class APIEndpoint:
    """API端点定义"""

    path: str
    method: str
    version: APIVersion
    handler: Callable
    description: str = ""
    tags: list[str] = field(default_factory=list)
    deprecated: bool = False
    deprecation_message: str | None = None


# API版本注册表
VERSION_REGISTRY: dict[APIVersion, VersionInfo] = {
    APIVersion.V1: VersionInfo(
        version=APIVersion.V1,
        status=DeprecationStatus.ACTIVE,
        released_at=datetime(2024, 1, 1),
        description="初始API版本,包含核心功能",
        migration_guide="/docs/api/v1-to-v2-migration",
    ),
    APIVersion.V2: VersionInfo(
        version=APIVersion.V2,
        status=DeprecationStatus.ACTIVE,
        released_at=datetime(2025, 1, 1),
        description="增强API版本,新增高级功能和性能优化",
        new_features=[
            "统一响应格式",
            "批量操作支持",
            "增强的过滤和排序",
            "更好的错误处理",
            "性能优化",
        ],
        breaking_changes=["响应格式变更", "部分端点重命名"],
    ),
}


class APIVersionMiddleware(BaseHTTPMiddleware):
    """API版本控制中间件"""

    def __init__(
        self,
        app: ASGIApp,
        default_version: APIVersion = APIVersion.V2,
        enable_version_header: bool = True,
        enable_deprecation_warnings: bool = True,
    ):
        """
        初始化版本控制中间件

        Args:
            app: ASGI应用
            default_version: 默认API版本
            enable_version_header: 是否启用版本响应头
            enable_deprecation_warnings: 是否启用弃用警告
        """
        super().__init__(app)
        self.default_version = default_version
        self.enable_version_header = enable_version_header
        self.enable_deprecation_warnings = enable_deprecation_warnings

    async def dispatch(self, request: Request, call_next):
        """处理请求并添加版本相关响应头"""

        # 解析请求的API版本
        requested_version = self._extract_version(request)

        # 验证版本有效性
        version_info = VERSION_REGISTRY.get(requested_version)
        if not version_info:
            # 返回415 Unsupported Media Style
            return JSONResponse(
                status_code=400,
                content={
                    "error": "unsupported_api_version",
                    "message": f"API version '{requested_version}' is not supported",
                    "supported_versions": [v.value for v in VERSION_REGISTRY],
                    "default_version": self.default_version.value,
                },
            )

        # 将版本信息存储在请求状态中
        request.state.api_version = requested_version
        request.state.version_info = version_info

        # 调用下一个中间件/路由
        response = await call_next(request)

        # 添加版本响应头
        if self.enable_version_header:
            response.headers["X-API-Version"] = requested_version.value
            response.headers["X-API-Status"] = version_info.status.value

        # 添加弃用警告头
        if self.enable_deprecation_warnings:
            if version_info.status == DeprecationStatus.DEPRECATED:
                response.headers["X-API-Deprecation"] = "This API version is deprecated"
                if version_info.sunset_at:
                    response.headers["X-API-Sunset-Date"] = version_info.sunset_at.isoformat()
                if version_info.migration_guide:
                    response.headers["X-API-Migration-Guide"] = version_info.migration_guide

        return response

    def _extract_version(self, request: Request) -> APIVersion:
        """
        从请求中提取API版本

        优先级:
        1. 查询参数 ?version=v2
        2. 请求头 X-API-Version
        3. URL路径 /api/v2/...
        4. 默认版本
        """
        # 1. 查询参数
        version = request.query_params.get("version")
        if version:
            try:
                return APIVersion(version.lower())
            except ValueError:
                pass

        # 2. 请求头
        version = request.headers.get("X-API-Version")
        if version:
            try:
                return APIVersion(version.lower())
            except ValueError:
                pass

        # 3. URL路径
        path = request.url.path
        match = re.match(r"/api/(v\d+|latest)/", path)
        if match:
            version_str = match.group(1)
            if version_str == "latest":
                return APIVersion.V2  # LATEST映射到最新版本
            try:
                return APIVersion(version_str)
            except ValueError:
                pass

        # 4. 默认版本
        return self.default_version


class APIVersionRouter:
    """API版本路由管理器"""

    def __init__(self, app: FastAPI):
        """
        初始化路由管理器

        Args:
            app: FastAPI应用实例
        """
        self.app = app
        self.routers: dict[APIVersion, APIRouter] = {}
        self.endpoints: dict[APIVersion, list[APIEndpoint]] = {}

    def create_version_router(
        self,
        version: APIVersion,
        tags: list[str] | None = None,
    ) -> APIRouter:
        """
        创建指定版本的路由器

        Args:
            version: API版本
            tags: 路由标签

        Returns:
            APIRouter实例
        """
        router = APIRouter(
            prefix=f"/api/{version.value}",
            tags=tags or [version.value.upper()],
        )

        self.routers[version] = router
        self.endpoints[version] = []

        # 添加版本信息端点
        self._add_version_info_endpoint(router, version)

        return router

    def register_router(self, router: APIRouter, version: APIVersion) -> Any:
        """
        注册路由器到应用

        Args:
            router: API路由器
            version: API版本
        """
        self.app.include_router(router)
        logger.info(f"Registered {version.value} router")

    def _add_version_info_endpoint(self, router: APIRouter, version: APIVersion) -> Any:
        """添加版本信息端点"""

        @router.get("/version", tags=["versioning"])
        async def get_version_info():
            """获取API版本信息"""
            version_info = VERSION_REGISTRY.get(version)
            if not version_info:
                raise HTTPException(status_code=404, detail="Version not found")

            return {
                "version": version_info.version.value,
                "status": version_info.status.value,
                "released_at": version_info.released_at.isoformat(),
                "deprecated_at": (
                    version_info.deprecated_at.isoformat() if version_info.deprecated_at else None
                ),
                "sunset_at": version_info.sunset_at.isoformat() if version_info.sunset_at else None,
                "retired_at": (
                    version_info.retired_at.isoformat() if version_info.retired_at else None
                ),
                "description": version_info.description,
                "new_features": version_info.new_features,
                "breaking_changes": version_info.breaking_changes,
                "migration_guide": version_info.migration_guide,
            }

        @router.get("/versions", tags=["versioning"])
        async def list_all_versions():
            """列出所有可用的API版本"""
            return {
                "versions": [
                    {
                        "version": info.version.value,
                        "status": info.status.value,
                        "description": info.description,
                        "released_at": info.released_at.isoformat(),
                    }
                    for info in VERSION_REGISTRY.values()
                ],
                "current_version": version.value,
                "recommended_version": APIVersion.V2.value,
            }


def versioned_endpoint(
    version: APIVersion,
    path: str,
    methods: list[str] | None = None,
    description: str = "",
    deprecated: bool = False,
    deprecation_message: str | None = None,
):
    """
    版本化端点装饰器

    Args:
        version: API版本
        path: 端点路径(不含版本前缀)
        methods: 允许的HTTP方法
        description: 端点描述
        deprecated: 是否弃用
        deprecation_message: 弃用消息

    Usage:
        @versioned_endpoint(APIVersion.V2, "/search", methods=["POST"])
        async def search_v2(request: SearchRequest):
            return {"results": [...]}
    """

    def decorator(func: Callable) -> Any:
        # 添加端点元数据
        func._version = version
        func._versioned_path = path
        func._versioned_methods = methods or ["GET"]
        func._versioned_description = description
        func._versioned_deprecated = deprecated
        func._versioned_deprecation_message = deprecation_message

        return func

    return decorator


def deprecated_v1(message: str = "This endpoint is deprecated. Please use v2.") -> Any:
    """
    标记v1端点为弃用

    Args:
        message: 弃用消息
    """

    def decorator(func: Callable) -> Any:
        func._deprecated = True
        func._deprecation_message = message

        # 保留原始函数逻辑,但添加警告
        async def wrapper(*args, **kwargs):
            logger.warning(f"Deprecated v1 endpoint called: {func.__name__}")
            return await func(*args, **kwargs)

        wrapper.__name__ = func.__name__
        wrapper.__doc__ = func.__doc__
        wrapper._deprecated = True
        wrapper._deprecation_message = message

        return wrapper

    return decorator


# 标准响应模型


class APIResponse:
    """标准API响应"""

    @staticmethod
    def success(data: Any, message: str = "Success", meta: dict | None = None) -> dict:
        """
        成功响应

        Args:
            data: 响应数据
            message: 响应消息
            meta: 元数据

        Returns:
            标准响应字典
        """
        response = {
            "success": True,
            "message": message,
            "data": data,
        }

        if meta:
            response["meta"] = meta

        return response

    @staticmethod
    def error(error: str, message: str, code: int | None = None, details: dict | None = None) -> dict:
        """
        错误响应

        Args:
            error: 错误类型
            message: 错误消息
            code: 错误代码
            details: 错误详情

        Returns:
            标准错误响应字典
        """
        response = {
            "success": False,
            "error": error,
            "message": message,
        }

        if code is not None:
            response["code"] = code

        if details:
            response["details"] = details

        return response


# 版本兼容性工具


class VersionCompatibility:
    """版本兼容性检查工具"""

    @staticmethod
    def check_compatibility(
        client_version: str, server_version: APIVersion
    ) -> tuple[bool, str | None]:
        """
        检查客户端版本与服务器版本的兼容性

        Args:
            client_version: 客户端请求的版本
            server_version: 服务器当前版本

        Returns:
            (是否兼容, 错误消息)
        """
        try:
            client_api_version = APIVersion(client_version.lower())
        except ValueError:
            return False, f"Invalid client version: {client_version}"

        # 获取版本信息
        server_info = VERSION_REGISTRY.get(server_version)
        client_info = VERSION_REGISTRY.get(client_api_version)

        if not server_info or not client_info:
            return False, "Version not found in registry"

        # 检查客户端版本是否已退役
        if client_info.status == DeprecationStatus.RETIRED:
            return False, f"Client version {client_version} is retired. Please upgrade."

        # 检查客户端版本是否即将下线
        if client_info.status == DeprecationStatus.SUNSET:
            return (
                True,
                f"Warning: Client version {client_version} will be sunset soon. Please upgrade to {server_version.value}.",
            )

        # 检查客户端版本是否已弃用
        if client_info.status == DeprecationStatus.DEPRECATED:
            return (
                True,
                f"Warning: Client version {client_version} is deprecated. Please upgrade to {server_version.value}.",
            )

        return True, None

    @staticmethod
    def get_recommended_version() -> APIVersion:
        """获取推荐的API版本"""
        return APIVersion.V2

    @staticmethod
    def get_latest_stable_version() -> APIVersion:
        """获取最新的稳定版本"""
        for version, info in VERSION_REGISTRY.items():
            if info.status == DeprecationStatus.ACTIVE:
                return version
        return APIVersion.V2


# 便捷函数


def setup_versioning(
    app: FastAPI,
    default_version: APIVersion = APIVersion.V2,
) -> APIVersionRouter:
    """
    设置API版本控制

    Args:
        app: FastAPI应用
        default_version: 默认API版本

    Returns:
        APIVersionRouter实例
    """
    # 添加版本控制中间件
    app.add_middleware(APIVersionMiddleware, default_version=default_version)

    # 创建路由管理器
    router_manager = APIVersionRouter(app)

    # 添加根路由
    @app.get("/api/versions", tags=["versioning"])
    async def list_api_versions():
        """列出所有可用的API版本"""
        return {
            "versions": [
                {
                    "version": info.version.value,
                    "status": info.status.value,
                    "description": info.description,
                }
                for info in VERSION_REGISTRY.values()
            ],
            "current": default_version.value,
            "recommended": APIVersion.V2.value,
        }

    logger.info(f"API versioning enabled with default version: {default_version.value}")

    return router_manager


# 示例使用

if __name__ == "__main__":
    from fastapi import FastAPI

    # 创建应用
    app = FastAPI(title="Athena Platform API", version="2.0.0")

    # 设置版本控制
    version_router = setup_versioning(app)

    # 创建v1路由器
    v1_router = version_router.create_version_router(APIVersion.V1)

    # 创建v2路由器
    v2_router = version_router.create_version_router(APIVersion.V2)

    # 注册路由器
    version_router.register_router(v1_router, APIVersion.V1)
    version_router.register_router(v2_router, APIVersion.V2)

    # 添加v2端点
    @v2_router.post("/search")
    async def search_v2(query: str):
        """v2搜索接口"""
        return APIResponse.success({"results": []}, "Search completed")

    # 添加v1端点(标记为弃用)
    @v1_router.post("/search")
    @deprecated_v1("Use /api/v2/search instead")
    async def search_v1(query: str):
        """v1搜索接口(已弃用)"""
        return APIResponse.success({"results": []}, "Search completed")

    print("API versioning system initialized")
    print(f"Available versions: {[v.value for v in VERSION_REGISTRY]}")
