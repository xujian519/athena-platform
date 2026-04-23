#!/usr/bin/env python3
"""
统一工具注册表 HTTP API 服务
Unified Tool Registry HTTP API Service

提供工具注册表的RESTful API接口，支持：
- 工具列表查询
- 工具详情获取
- 工具执行
- 权限检查
- 健康监控

作者: Athena平台团队
版本: 1.0.0
"""

import asyncio
import logging

# 添加项目路径
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

import uvicorn
from fastapi import FastAPI, HTTPException, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

sys.path.insert(0, str(Path(__file__).parent.parent))

from core.tools.permissions import PermissionMode, ToolPermissionContext
from core.tools.unified_registry import ToolHealthStatus, get_unified_registry

# =============================================================================
# 日志配置
# =============================================================================

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# =============================================================================
# 数据模型
# =============================================================================

class ToolInfo(BaseModel):
    """工具信息模型"""
    id: str
    name: str
    category: str = ""
    description: str = ""
    enabled: bool = True
    healthy: bool = True
    metadata: dict[str, Any] = Field(default_factory=dict)

class ToolExecuteRequest(BaseModel):
    """工具执行请求"""
    tool_name: str = Field(..., description="工具名称")
    parameters: dict[str, Any] = Field(default_factory=dict, description="工具参数")
    user_context: dict[str, Any] = Field(default_factory=dict, description="用户上下文（用于权限检查）")

class ToolExecuteResponse(BaseModel):
    """工具执行响应"""
    success: bool
    tool_name: str
    result: Any = None
    error: str = None
    execution_time: float = 0.0

class HealthResponse(BaseModel):
    """健康检查响应"""
    status: str
    service: str
    version: str
    timestamp: str
    total_tools: int
    enabled_tools: int
    healthy_tools: int

# =============================================================================
# FastAPI应用
# =============================================================================

app = FastAPI(
    title="Athena Unified Tool Registry API",
    description="统一工具注册表HTTP API服务",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# 全局变量
tool_registry = None
permission_context = None

# =============================================================================
# 生命周期管理
# =============================================================================

@app.on_event("startup")
async def startup_event():
    """应用启动时初始化"""
    global tool_registry, permission_context

    logger.info("🔧 初始化工具注册表...")

    try:
        # 获取工具注册表
        tool_registry = get_unified_registry()

        # 初始化注册表（如果需要）
        if not tool_registry._initialized:
            await tool_registry.initialize()

        # 获取工具统计信息
        stats = tool_registry.get_statistics()
        logger.info(f"✅ 工具注册表加载成功，共 {stats.get('total_tools', 0)} 个工具")

        # 初始化权限上下文（默认AUTO模式）
        permission_context = ToolPermissionContext(mode=PermissionMode.AUTO)
        logger.info("✅ 权限上下文初始化完成")

        # 执行健康检查
        health_report = tool_registry.get_health_report()
        healthy_count = sum(1 for r in health_report.values() if r.get('status') == 'healthy')

        logger.info(f"📊 工具健康状态: {healthy_count}/{len(health_report)} 健康")

    except Exception as e:
        logger.error(f"❌ 启动失败: {e}", exc_info=True)
        raise

@app.on_event("shutdown")
async def shutdown_event():
    """应用关闭时清理"""
    logger.info("🛑 工具注册表API服务正在关闭...")

# =============================================================================
# API端点
# =============================================================================

@app.get("/health", response_model=HealthResponse, tags=["Health"])
async def health_check():
    """
    健康检查端点

    返回服务状态和工具统计信息
    """
    if tool_registry is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="服务未就绪"
        )

    # 获取统计信息
    stats = tool_registry.get_statistics()
    health_report = tool_registry.get_health_report()

    return HealthResponse(
        status="healthy",
        service="tool-registry-api",
        version="1.0.0",
        timestamp=datetime.now().isoformat(),
        total_tools=stats.get('total_tools', 0),
        enabled_tools=stats.get('enabled_tools', 0),
        healthy_tools=sum(1 for r in health_report.values() if r['healthy'])
    )


@app.get("/api/v1/tools", tags=["Tools"])
async def list_tools(
    category: str = None,
    enabled_only: bool = False
):
    """
    获取工具列表

    参数:
    - category: 按分类过滤
    - enabled_only: 只返回已启用的工具
    """
    if tool_registry is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="服务未就绪"
        )

    try:
        # 获取所有工具（通过base_registry）
        from core.tools.base import get_global_registry
        base_registry = get_global_registry()
        all_tools = list(base_registry._tools.values())

        # 过滤
        if category:
            def category_match(t):
                cat_str = str(t.category)
                if hasattr(t.category, 'value') and t.category.value == category:
                    return True
                return cat_str == category
            all_tools = [t for t in all_tools if category_match(t)]

        if enabled_only:
            all_tools = [t for t in all_tools if t.enabled]

        # 转换为响应模型
        tools_info = []
        for tool in all_tools:
            # 检查健康状态
            health_status = tool_registry.get_health_status(tool.tool_id)
            is_healthy = health_status == ToolHealthStatus.HEALTHY

            # 使用config而不是metadata
            metadata = tool.config if hasattr(tool, 'config') else {}

            tools_info.append(ToolInfo(
                id=tool.tool_id,
                name=tool.name,
                category=tool.category.value if hasattr(tool.category, 'value') else str(tool.category),
                description=tool.description,
                enabled=tool.enabled,
                healthy=is_healthy,
                metadata=metadata
            ))

        return {
            "success": True,
            "count": len(tools_info),
            "data": tools_info
        }

    except Exception as e:
        logger.error(f"获取工具列表失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取工具列表失败: {str(e)}"
        )


@app.get("/api/v1/tools/stats", tags=["Tools"])
async def get_statistics():
    """
    获取工具注册表统计信息

    注意：此路由必须在 /api/v1/tools/{tool_name} 之前定义
    """
    if tool_registry is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="服务未就绪"
        )

    try:
        stats = tool_registry.get_statistics()
        health_report = tool_registry.get_health_report()

        return {
            "success": True,
            "data": {
                **stats,
                "health_report": health_report
            }
        }

    except Exception as e:
        logger.error(f"获取统计信息失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取统计信息失败: {str(e)}"
        )


@app.get("/api/v1/tools/{tool_name}", tags=["Tools"])
async def get_tool(tool_name: str):
    """
    获取单个工具的详细信息

    注意：此路由必须在具体路径（如stats）之后定义
    """
    if tool_registry is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="服务未就绪"
        )

    try:
        tool = tool_registry.get(tool_name)

        if tool is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"工具 '{tool_name}' 不存在"
            )

        # 检查健康状态
        health_status = tool_registry.get_health_status(tool.tool_id)
        is_healthy = health_status == ToolHealthStatus.HEALTHY

        # 使用config而不是metadata
        metadata = tool.config if hasattr(tool, 'config') else {}

        return {
            "success": True,
            "data": {
                "id": tool.tool_id,
                "name": tool.name,
                "category": tool.category.value if hasattr(tool.category, 'value') else str(tool.category),
                "description": tool.description,
                "enabled": tool.enabled,
                "healthy": is_healthy,
                "metadata": metadata
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取工具详情失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取工具详情失败: {str(e)}"
        )


@app.post("/api/v1/tools/execute", response_model=ToolExecuteResponse, tags=["Tools"])
async def execute_tool(request: ToolExecuteRequest):
    """
    执行工具

    参数:
    - tool_name: 工具名称
    - parameters: 工具参数
    - user_context: 用户上下文（用于权限检查）
    """
    if tool_registry is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="服务未就绪"
        )

    import time
    start_time = time.time()

    try:
        # 1. 获取工具
        tool = tool_registry.get(request.tool_name)

        if tool is None:
            return ToolExecuteResponse(
                success=False,
                tool_name=request.tool_name,
                error=f"工具 '{request.tool_name}' 不存在",
                execution_time=time.time() - start_time
            )

        if not tool.enabled:
            return ToolExecuteResponse(
                success=False,
                tool_name=request.tool_name,
                error=f"工具 '{request.tool_name}' 未启用",
                execution_time=time.time() - start_time
            )

        # 2. 权限检查
        if permission_context:
            decision = permission_context.check_permission(
                action=f"{tool.category}:{request.tool_name}",
                parameters=request.parameters
            )

            if not decision.allowed:
                logger.warning(f"权限拒绝: {decision.reason}")
                return ToolExecuteResponse(
                    success=False,
                    tool_name=request.tool_name,
                    error=f"权限拒绝: {decision.reason}",
                    execution_time=time.time() - start_time
                )

        # 3. 执行工具
        logger.info(f"执行工具: {request.tool_name} 参数: {request.parameters}")

        # 检查工具是否是异步的
        if asyncio.iscoroutinefunction(tool.function):
            result = await tool.function(**request.parameters)
        else:
            result = tool.function(**request.parameters)

        execution_time = time.time() - start_time

        logger.info(f"工具执行成功: {request.tool_name} 耗时: {execution_time:.3f}秒")

        return ToolExecuteResponse(
            success=True,
            tool_name=request.tool_name,
            result=result,
            execution_time=execution_time
        )

    except Exception as e:
        execution_time = time.time() - start_time
        logger.error(f"工具执行失败: {e}", exc_info=True)

        return ToolExecuteResponse(
            success=False,
            tool_name=request.tool_name,
            error=str(e),
            execution_time=execution_time
        )


@app.get("/api/v1/tools/categories", tags=["Tools"])
async def list_categories():
    """
    获取工具分类列表
    """
    if tool_registry is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="服务未就绪"
        )

    try:
        all_tools = tool_registry.list_tools()
        categories = {tool.category for tool in all_tools}

        return {
            "success": True,
            "count": len(categories),
            "data": sorted(categories)
        }

    except Exception as e:
        logger.error(f"获取分类列表失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取分类列表失败: {str(e)}"
        )


@app.delete("/api/v1/stats", tags=["Monitoring"], include_in_schema=False)
async def get_statistics_deprecated():
    """废弃的统计端点，重定向到新端点"""
    raise HTTPException(
        status_code=status.HTTP_301_MOVED_PERMANENTLY,
        detail="请使用 /api/v1/tools/stats",
        headers={"Location": "/api/v1/tools/stats"}
    )


# =============================================================================
# 错误处理
# =============================================================================

@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """全局异常处理器"""
    logger.error(f"未捕获的异常: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "success": False,
            "error": "内部服务器错误",
            "detail": str(exc)
        }
    )


# =============================================================================
# 主函数
# =============================================================================

def main():
    """启动服务"""
    logger.info("🚀 启动工具注册表API服务...")

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8021,
        reload=False,
        log_level="info"
    )


if __name__ == "__main__":
    main()
