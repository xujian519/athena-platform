#!/usr/bin/env python3
"""
Athena统一记忆系统 - 生产环境启动脚本
Unified Agent Memory System - Production Service Launcher

为所有智能体提供统一的生产级记忆服务

集成60分钟不使用自动释放功能
"""

from __future__ import annotations
import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

# FastAPI相关
import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

# 导入自动释放功能
try:
    from core.session.auto_release_integration import (
        FastAPIAutoReleaseMixin,
        load_auto_release_config,
    )
    from core.session.service_session_manager import ServiceType
    AUTO_RELEASE_AVAILABLE = True
except ImportError:
    print("⚠️ 自动释放功能模块未找到")
    AUTO_RELEASE_AVAILABLE = False

# 加载环境变量
try:
    from dotenv import load_dotenv
    HAS_DOTENV = True
except ImportError:
    HAS_DOTENV = False
    print("⚠️  python-dotenv未安装，将使用系统环境变量")

# 设置路径
current_dir = Path(__file__).parent
project_root = current_dir.parent.parent
sys.path.insert(0, str(project_root))

# 加载环境变量配置文件
env_file = project_root / "production" / "config" / ".env.memory"
if HAS_DOTENV and env_file.exists():
    load_dotenv(env_file)
    print(f"✅ 已加载环境配置: {env_file}")
else:
    print(f"⚠️  环境配置文件: {env_file}")

# 配置日志
log_dir = project_root / "production" / "logs"
log_dir.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_dir / "unified_memory_service.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


# FastAPI应用
app = FastAPI(
    title="Athena统一记忆系统API",
    description="为所有智能体提供统一的记忆服务",
    version="1.0.0"
)

# CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境应限制具体域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 全局记忆系统实例
memory_system = None

# 自动释放功能实例
auto_release = None


# 请求模型
class MemoryStoreRequest(BaseModel):
    """存储记忆请求"""
    agent_id: str = Field(..., description="智能体ID", example="xiaonuo_pisces")
    content: str = Field(..., description="记忆内容", example="今天学习了Python异步编程")
    memory_type: str = Field(..., description="记忆类型", example="learning")
    importance: float = Field(default=0.5, ge=0.0, le=1.0, description="重要性 (0-1)")
    emotional_weight: float = Field(default=0.0, ge=0.0, le=1.0, description="情感权重 (0-1)")
    family_related: bool = Field(default=False, description="是否与家庭相关")
    work_related: bool = Field(default=True, description="是否与工作相关")
    tags: list[str] = Field(default_factory=list, description="标签列表")
    metadata: dict[str, Any] = Field(default_factory=dict, description="额外元数据")


class MemoryRecallRequest(BaseModel):
    """召回记忆请求"""
    agent_id: str = Field(..., description="智能体ID", example="xiaonuo_pisces")
    query: str = Field(..., description="查询内容", example="我最近学习了什么？")
    limit: int = Field(default=10, ge=1, le=100, description="返回结果数量")
    memory_type: str | None = Field(None, description="记忆类型过滤")


class MemorySearchRequest(BaseModel):
    """搜索记忆请求"""
    query: str = Field(..., description="搜索查询", example="Python编程")
    agent_id: str | None = Field(None, description="智能体ID过滤")
    memory_type: str | None = Field(None, description="记忆类型过滤")
    importance_threshold: float = Field(default=0.0, ge=0.0, le=1.0, description="重要性阈值")
    limit: int = Field(default=20, ge=1, le=100, description="返回结果数量")


# 响应模型
class MemoryResponse(BaseModel):
    """记忆响应"""
    memory_id: str
    agent_id: str
    content: str
    memory_type: str
    importance: float
    created_at: str
    tags: list[str]
    metadata: dict[str, Any]


class MemoryListResponse(BaseModel):
    """记忆列表响应"""
    success: bool
    data: list[MemoryResponse]
    count: int
    timestamp: str


# API端点
@app.get("/", tags=["基础"], summary="服务信息", description="获取服务基本信息和状态")
async def root():
    """
    获取服务基本信息

    返回服务名称、版本和当前运行状态
    """
    return {
        "service": "Athena统一记忆系统",
        "version": "1.0.0",
        "status": "running",
        "timestamp": datetime.now().isoformat(),
        "documentation": "/docs",
        "health_check": "/health"
    }


@app.get("/health", tags=["监控"], summary="健康检查", description="检查服务健康状态和统计信息")
async def health_check():
    """
    健康检查端点

    返回服务状态和基本统计信息：
    - total_agents: 智能体总数
    - total_memories: 记忆总数
    - eternal_memories: 永恒记忆数量
    """
    status = {
        "service": "Athena统一记忆系统",
        "status": "healthy" if memory_system else "initializing",
        "timestamp": datetime.now().isoformat()
    }

    if memory_system:
        try:
            stats = await memory_system.get_system_stats()
            status["statistics"] = {
                "total_agents": stats.get("total_agents", 0),
                "total_memories": stats.get("total_memories", 0),
                "eternal_memories": stats.get("eternal_memories", 0),
                "family_memories": stats.get("total_family_memories", 0)
            }
        except Exception as e:
            status["statistics_error"] = str(e)

    return status


@app.get("/metrics", tags=["监控"], summary="Prometheus指标", description="导出Prometheus格式的监控指标")
async def prometheus_metrics():
    """
    Prometheus监控指标

    导出以下指标：
    - athena_memory_total_agents: 总智能体数量
    - athena_memory_total_memories: 总记忆数量
    - athena_memory_eternal_memories: 永恒记忆数量
    - athena_memory_family_memories: 家庭记忆数量
    """
    if not memory_system:
        return "# Memory system not initialized\n"

    try:
        stats = await memory_system.get_system_stats()
        metrics = [
            "# HELP athena_memory_total_agents Total number of agents",
            "# TYPE athena_memory_total_agents gauge",
            f"athena_memory_total_agents {stats.get('total_agents', 0)}",
            "",
            "# HELP athena_memory_total_memories Total number of memories",
            "# TYPE athena_memory_total_memories gauge",
            f"athena_memory_total_memories {stats.get('total_memories', 0)}",
            "",
            "# HELP athena_memory_eternal_memories Number of eternal memories",
            "# TYPE athena_memory_eternal_memories gauge",
            f"athena_memory_eternal_memories {stats.get('eternal_memories', 0)}",
            "",
            "# HELP athena_memory_family_memories Number of family memories",
            "# TYPE athena_memory_family_memories gauge",
            f"athena_memory_family_memories {stats.get('total_family_memories', 0)}",
        ]
        return "\n".join(metrics)
    except Exception as e:
        return f"# Error generating metrics: {e}\n"


@app.get("/api/v1/stats", tags=["统计"], summary="系统统计", description="获取详细的系统统计信息")
async def get_stats():
    """
    获取系统统计信息

    返回所有智能体的详细统计：
    - total_agents: 智能体总数
    - total_memories: 记忆总数
    - eternal_memories: 永恒记忆数量
    - agents: 各智能体的详细统计
    """
    if not memory_system:
        raise HTTPException(status_code=503, detail="记忆系统未初始化")

    try:
        stats = await memory_system.get_system_stats()
        return {
            "success": True,
            "data": stats,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.post("/api/v1/memory/store", tags=["记忆"], summary="存储记忆", description="为智能体存储新记忆")
async def store_memory(request: MemoryStoreRequest):
    """
    存储新记忆

    为指定智能体存储一条新记忆。

    **示例请求**:
    ```json
    {
        "agent_id": "xiaonuo_pisces",
        "content": "今天学习了Python异步编程",
        "memory_type": "learning",
        "importance": 0.8,
        "tags": ["python", "async"]
    }
    ```

    **返回**: 存储的记忆详情，包括memory_id
    """
    if not memory_system:
        raise HTTPException(status_code=503, detail="记忆系统未初始化")

    try:
        result = await memory_system.store_memory(
            agent_id=request.agent_id,
            content=request.content,
            memory_type=request.memory_type,
            importance=request.importance,
            emotional_weight=request.emotional_weight,
            family_related=request.family_related,
            work_related=request.work_related,
            tags=request.tags,
            metadata=request.metadata
        )

        return {
            "success": True,
            "data": result,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"存储记忆失败: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.post("/api/v1/memory/recall", tags=["记忆"], summary="召回记忆", description="根据查询召回相关记忆")
async def recall_memory(request: MemoryRecallRequest):
    """
    召回记忆

    根据查询内容召回智能体的相关记忆。

    **示例请求**:
    ```json
    {
        "agent_id": "xiaonuo_pisces",
        "query": "我最近学习了什么？",
        "limit": 10
    }
    ```

    **返回**: 相关记忆列表，按相关性排序
    """
    if not memory_system:
        raise HTTPException(status_code=503, detail="记忆系统未初始化")

    try:
        results = await memory_system.recall_memories(
            agent_id=request.agent_id,
            query=request.query,
            limit=request.limit,
            memory_type=request.memory_type
        )

        return {
            "success": True,
            "data": results,
            "count": len(results),
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"召回记忆失败: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.post("/api/v1/memory/search", tags=["记忆"], summary="搜索记忆", description="全局搜索记忆")
async def search_memory(request: MemorySearchRequest):
    """
    搜索记忆

    在所有记忆中搜索，支持多种过滤条件。

    **示例请求**:
    ```json
    {
        "query": "Python编程",
        "importance_threshold": 0.5,
        "limit": 20
    }
    ```

    **返回**: 匹配的记忆列表
    """
    if not memory_system:
        raise HTTPException(status_code=503, detail="记忆系统未初始化")

    try:
        results = await memory_system.search_memories(
            query=request.query,
            agent_id=request.agent_id,
            memory_type=request.memory_type,
            importance_threshold=request.importance_threshold,
            limit=request.limit
        )

        return {
            "success": True,
            "data": results,
            "count": len(results),
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"搜索记忆失败: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e


# 启动事件
@app.on_event("startup")
async def startup_event():
    """启动时初始化记忆系统和自动释放功能"""
    global memory_system, auto_release

    logger.info("🏛️ Athena统一记忆系统启动中...")

    try:
        from core.memory.unified_agent_memory_system import UnifiedAgentMemorySystem

        logger.info("🔄 正在初始化统一记忆系统...")

        # 创建记忆系统实例
        memory_system = UnifiedAgentMemorySystem()

        # 初始化系统
        await memory_system.initialize()

        logger.info("✅ 统一记忆系统初始化成功")

        # 显示系统信息
        try:
            stats = await memory_system.get_system_stats()
            logger.info("=" * 50)
            logger.info("📊 系统状态信息")
            logger.info("=" * 50)
            logger.info("版本: 1.0.0-production")
            logger.info(f"总智能体: {stats.get('total_agents', 0)}")
            logger.info(f"总记忆数: {stats.get('total_memories', 0)}")
            logger.info(f"永恒记忆: {stats.get('eternal_memories', 0)}")
            logger.info(f"家庭记忆: {stats.get('total_family_memories', 0)}")
            logger.info("=" * 50)
        except Exception as e:
            logger.warning(f"⚠️ 无法获取系统信息: {e}")

    except Exception as e:
        logger.error(f"❌ 记忆系统初始化失败: {e}")
        # 不抛出异常，允许API服务继续运行

    # 初始化自动释放功能
    if AUTO_RELEASE_AVAILABLE:
        try:
            from core.session.auto_release_integration import (
                FastAPIAutoReleaseMixin,
                load_auto_release_config,
            )
            from core.session.service_session_manager import ServiceType

            config = load_auto_release_config()
            if config['enabled']:
                auto_release = FastAPIAutoReleaseMixin(
                    service_name="统一记忆系统",
                    service_type=ServiceType.API,
                    auto_stop=True,  # 记忆服务可以自动停止
                    idle_timeout=config['idle_timeout']
                )
                await auto_release.enable_auto_release()

                # 添加活动更新中间件
                auto_release.create_activity_middleware(app)

                logger.info(f"✅ 自动释放功能已启用 (超时: {config['idle_timeout']}秒)")
            else:
                logger.info("ℹ️ 自动释放功能已禁用")
        except Exception as e:
            logger.warning(f"⚠️ 启用自动释放功能失败: {e}")


@app.on_event("shutdown")
async def shutdown_event():
    """关闭时清理资源和自动释放功能"""
    global memory_system, auto_release

    logger.info("🛑 正在关闭统一记忆系统...")

    # 清理自动释放功能
    if auto_release:
        try:
            await auto_release.disable_auto_release()
            logger.info("✅ 自动释放功能已禁用")
        except Exception as e:
            logger.error(f"❌ 禁用自动释放功能失败: {e}")

    if memory_system:
        try:
            await memory_system.close()
            logger.info("✅ 记忆系统已关闭")
        except Exception as e:
            logger.error(f"❌ 关闭记忆系统失败: {e}")

    logger.info("✅ 服务已停止")


def main():
    """主函数"""
    # 服务配置
    host = os.getenv('MEMORY_SERVICE_HOST', '0.0.0.0')
    port = int(os.getenv('MEMORY_SERVICE_PORT', '8900'))

    logger.info("🚀 启动统一记忆系统API服务器...")
    logger.info(f"📡 服务地址: http://{host}:{port}")
    logger.info(f"📖 API文档: http://{host}:{port}/docs")
    logger.info(f"📖 日志文件: {log_dir / 'unified_memory_service.log'}")

    # 启动uvicorn服务器
    uvicorn.run(
        "start_unified_memory_service:app",
        host=host,
        port=port,
        reload=False,
        log_level="info",
        access_log=True
    )


if __name__ == "__main__":
    main()
