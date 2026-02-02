
#!/usr/bin/env python3
"""
向量-图融合记忆API服务器(简化版)
Vector-Graph Fusion Memory API Server (Simplified)

直接使用 asyncio 和 aiohttp,避免 Pydantic 兼容性问题

作者: 小诺·双鱼公主
创建时间: 2025-12-28
"""

import asyncio
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

from core.logging_config import setup_logging

# 添加项目路径
PROJECT_ROOT = str(Path(__file__).parent.parent)
sys.path.insert(0, PROJECT_ROOT)

from aiohttp import web

from core.fusion.vector_graph_fusion_service import FusionConfig, VectorGraphFusionService

# 配置日志
# setup_logging()  # 日志配置已移至模块导入
logger = setup_logging()

# 全局服务
fusion_api = None


async def init_app():
    """初始化应用"""
    global fusion_api
    config = FusionConfig()
    fusion_api = VectorGraphFusionService(config)
    await fusion_api.initialize()
    logger.info("✅ 融合API已初始化")


async def health_check(request: web.Request) -> web.Response:
    """健康检查"""
    return web.json_response(
        {
            "status": "ok",
            "timestamp": datetime.now().isoformat(),
            "fusion": {
                "service_initialized": fusion_api is not None and fusion_api.initialized,
                "vector_dimension": fusion_api.config.vector_dimension if fusion_api else None,
            },
        }
    )


async def store_memory(request: web.Request) -> web.Response:
    """存储记忆"""
    try:
        result = await fusion_api.store_memory(
            agent_id=data["agent_id"],
            content=data["content"],
            memory_type=data.get("memory_type", "conversation"),
            importance=data.get("importance", 0.5),
            tags=data.get("tags", []),
            metadata=data.get("metadata", {}),
        )
        return web.json_response(result)
    except Exception:
        logger.error("操作失败: e", exc_info=True)
        raise


async def search_memories(request: web.Request) -> web.Response:
    """搜索记忆"""
    try:
        results = await fusion_api.search_memories(
            query=data["query"],
            agent_id=data.get("agent_id"),
            memory_type=data.get("memory_type"),
            limit=data.get("limit", 10),
            strategy=None,  # 默认策略
        )
        return web.json_response(
            {
                "results": [r.__dict__ for r in results],
                "total_count": len(results),
                "strategy_used": "fusion_both",
                "query_time_ms": 0,
            }
        )
    except Exception:
        logger.error("操作失败: e", exc_info=True)
        raise


async def get_statistics(request: web.Request) -> web.Response:
    """获取统计信息"""
    try:
        return web.json_response(stats)
    except Exception:
        logger.error("操作失败: e", exc_info=True)
        raise


def setup_routes(app: web.Application) -> Any:
    """设置路由"""
    app.router.add_get("/health", health_check)
    app.router.add_post("/api/v1/memories", store_memory)
    app.router.add_post("/api/v1/memories/search", search_memories)
    app.router.add_get("/api/v1/memories/stats", get_statistics)


async def main():
    """主函数"""
    # 初始化
    await init_app()

    # 创建应用
    app = web.Application()
    setup_routes(app)

    # 启动服务器
    logger.info("🚀 启动融合记忆API服务器 (aiohttp)")
    logger.info("📍 http://localhost:8100")

    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "localhost", 8100)
    await site.start()

    logger.info("✅ 服务已启动")

    # 保持运行
    try:
            await asyncio.sleep(3600)
    except asyncio.CancelledError:
        logger.error("操作失败: e", exc_info=True)
        raise
    finally:
        await runner.cleanup()


# 入口点: @async_main装饰器已添加到main函数
