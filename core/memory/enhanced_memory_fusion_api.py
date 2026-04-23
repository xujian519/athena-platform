#!/usr/bin/env python3
from __future__ import annotations
"""
增强记忆API服务器 - 集成向量-图融合
Enhanced Memory API Server with Vector-Graph Fusion

为现有记忆系统添加向量-图融合能力

作者: 小诺·双鱼公主
创建时间: 2025-12-28
"""


# 导入融合服务
import sys
from contextlib import asynccontextmanager
from pathlib import Path

import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from core.logging_config import setup_logging
from core.security.auth import ALLOWED_ORIGINS

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.fusion import get_fusion_api

# 配置日志
# setup_logging()  # 日志配置已移至模块导入
logger = setup_logging()


# 全局融合API
fusion_api = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    global fusion_api

    # 启动时初始化
    logger.info("🚀 启动增强记忆API服务器...")
    fusion_api = get_fusion_api()
    await fusion_api.initialize()
    logger.info("✅ 融合API已初始化")

    yield

    # 关闭时清理
    logger.info("🔌 关闭融合API...")


# 请求/响应模型
class FusionStoreRequest(BaseModel):
    """融合存储请求"""

    agent_id: str
    content: str
    memory_type: str = "conversation"
    importance: float = Field(default=0.5, ge=0.0, le=1.0)
    tags: list[str] = []
    metadata: dict = {}


class FusionSearchRequest(BaseModel):
    """融合搜索请求"""

    query: str
    agent_id: Optional[str] = None
    memory_type: Optional[str] = None
    limit: int = Field(default=10, ge=1, le=100)
    strategy: str = Field(default="fusion_both")


# FastAPI应用
app = FastAPI(
    title="Athena增强记忆API",
    description="集成向量-图融合的记忆系统API",
    version="2.0.0",
    lifespan=lifespan,
)

# CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# 健康检查
@app.get("/health")
async def health_check():
    """健康检查"""
    health = await fusion_api.health_check()
    return {"status": "ok", "fusion": health}


# 存储记忆
@app.post("/api/v1/memories")
async def store_memory(request: FusionStoreRequest):
    """存储记忆到向量-图融合系统"""
    try:
        pass

        result = await fusion_api.store_memory(request)
        return result
    except Exception:
        logger.error("操作失败: e", exc_info=True)
        raise


# 搜索记忆
@app.post("/api/v1/memories/search")
async def search_memories(request: FusionSearchRequest):
    """搜索记忆"""
    try:
        pass

        results = await fusion_api.search_memories(request)
        return results
    except Exception:
        logger.error("操作失败: e", exc_info=True)
        raise


# 获取单个记忆
@app.get("/api/v1/memories/{memory_id}")
async def get_memory(memory_id: str):
    """获取单个记忆"""
    try:
        if not memory_id:
            raise HTTPException(status_code=404, detail="记忆ID不存在")
        # TODO: 从存储中获取记忆
        raise NotImplementedError("待实现")
    except HTTPException:
        logger.error("操作失败", exc_info=True)
        raise
    except Exception:
        logger.error("操作失败: e", exc_info=True)
        raise


# 获取统计信息
@app.get("/api/v1/memories/stats")
async def get_statistics():
    """获取统计信息"""
    try:
        if fusion_api:
            return await fusion_api.get_statistics()
        return {"total_memories": 0, "status": "uninitialized"}
    except Exception:
        logger.error("操作失败: e", exc_info=True)
        raise


# 批量存储记忆
@app.post("/api/v1/memories/batch")
async def batch_store_memories(requests: list[FusionStoreRequest]):
    """批量存储记忆"""
    try:
        results = []
        for req in requests:
            result = await fusion_api.store_memory(req)
            results.append(result)

        return {"success": True, "total": len(results), "results": results}
    except Exception:
        logger.error("操作失败: e", exc_info=True)
        raise


def main() -> None:
    """主函数"""
    uvicorn.run(app, host="127.0.0.1", port=8100, log_level="info")  # 内网通信


if __name__ == "__main__":
    main()
