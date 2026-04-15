#!/usr/bin/env python3
from __future__ import annotations
"""
记忆系统API服务器
Memory System API Server
"""

import argparse
import json
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Any

import uvicorn
from fastapi import BackgroundTasks, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# 导入记忆系统
from unified_agent_memory_system import AgentType, MemoryType, UnifiedAgentMemorySystem

from core.security.auth import ALLOWED_ORIGINS

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# FastAPI应用
app = FastAPI(
    title="Athena记忆系统API",
    description="统一记忆系统的RESTful API接口",
    version="1.0.0"
)

# CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 全局记忆系统实例
memory_system: UnifiedAgentMemorySystem | None = None

# 通过agent_id获取agent_type的辅助函数
def get_agent_type_by_id(agent_id: str) -> str | None:
    """通过agent_id获取对应的agent_type"""
    # 从智能体注册表中查找
    from unified_agent_memory_system import AGENT_REGISTRY
    for agent_type, identity in AGENT_REGISTRY.items():
        if identity.agent_id == agent_id:
            return agent_type.value
    return None

# 请求模型
class MemoryStoreRequest(BaseModel):
    agent_id: str
    content: str
    memory_type: str
    importance: float = 0.5
    emotional_weight: float = 0.0
    family_related: bool = False
    work_related: bool = True
    tags: list[str] = []
    metadata: dict[str, Any] = {}

class MemoryRecallRequest(BaseModel):
    agent_id: str
    query: str
    limit: int = 10
    memory_type: str | None = None

class MemorySearchRequest(BaseModel):
    query: str
    agent_id: str | None = None
    memory_type: str | None = None
    importance_threshold: float = 0.0
    limit: int = 20

# 启动事件
@app.on_event("startup")
async def startup_event():
    """启动时初始化记忆系统"""
    global memory_system

    # 加载配置
    config_path = os.environ.get('MEMORY_SYSTEM_CONFIG',
                                '/Users/xujian/Athena工作平台/config/memory_system_config.json')

    if Path(config_path).exists():
        with open(config_path, encoding='utf-8') as f:
            json.load(f)
        logger.info(f"加载配置文件: {config_path}")
    else:
        logger.warning("配置文件不存在，使用默认配置")

    # 初始化记忆系统
    memory_system = UnifiedAgentMemorySystem()
    await memory_system.initialize()

    logger.info("记忆系统API服务已启动")

# 健康检查
@app.get("/api/health")
async def health_check():
    """健康检查"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "service": "memory_system",
        "version": "1.0.0"
    }

# 存储记忆
@app.post("/api/memory/store")
async def store_memory(request: MemoryStoreRequest):
    """存储记忆"""
    try:
        # 获取agent_type
        agent_type_str = get_agent_type_by_id(request.agent_id)
        if not agent_type_str:
            raise HTTPException(status_code=400, detail=f"未知的智能体ID: {request.agent_id}")

        agent_type = AgentType(agent_type_str)

        success = await memory_system.store_memory(
            agent_id=request.agent_id,
            agent_type=agent_type,
            content=request.content,
            memory_type=MemoryType(request.memory_type),
            importance=request.importance,
            emotional_weight=request.emotional_weight,
            family_related=request.family_related,
            work_related=request.work_related,
            tags=request.tags,
            metadata=request.metadata
        )

        if success:
            return {"status": "success", "message": "记忆存储成功"}
        else:
            raise HTTPException(status_code=500, detail="记忆存储失败")

    except Exception as e:
        logger.error(f"存储记忆错误: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e

# 检索记忆
@app.post("/api/memory/recall")
async def recall_memory(request: MemoryRecallRequest):
    """检索记忆"""
    try:
        memories = await memory_system.recall_memory(
            agent_id=request.agent_id,
            query=request.query,
            limit=request.limit,
            memory_type=MemoryType(request.memory_type) if request.memory_type else None
        )

        return {
            "status": "success",
            "count": len(memories),
            "memories": [
                {
                    "id": m.get("id"),
                    "content": m.get("content"),
                    "memory_type": m.get("memory_type"),
                    "importance": m.get("importance"),
                    "created_at": m.get("created_at"),
                    "tier": m.get("tier")
                }
                for m in memories
            ]
        }

    except Exception as e:
        logger.error(f"检索记忆错误: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e

# 搜索记忆
@app.post("/api/memory/search")
async def search_memory(request: MemorySearchRequest):
    """搜索记忆"""
    try:
        results = await memory_system.search_memories(
            query=request.query,
            agent_id=request.agent_id,
            memory_type=MemoryType(request.memory_type) if request.memory_type else None,
            importance_threshold=request.importance_threshold,
            limit=request.limit
        )

        return {
            "status": "success",
            "query": request.query,
            "count": len(results),
            "results": results
        }

    except Exception as e:
        logger.error(f"搜索记忆错误: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e

# 获取智能体记忆统计
@app.get("/api/memory/stats/{agent_id}")
async def get_memory_stats(agent_id: str):
    """获取智能体记忆统计"""
    try:
        stats = await memory_system.get_agent_stats(agent_id)
        return {
            "status": "success",
            "agent_id": agent_id,
            "stats": stats
        }

    except Exception as e:
        logger.error(f"获取统计错误: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e

# 跨智能体共享记忆
@app.post("/api/memory/share")
async def share_memory(memory_id: str, target_agents: list[str]):
    """共享记忆给其他智能体"""
    try:
        success = await memory_system.share_memory(memory_id, target_agents)

        if success:
            return {"status": "success", "message": f"记忆已共享给 {len(target_agents)} 个智能体"}
        else:
            raise HTTPException(status_code=500, detail="记忆共享失败")

    except Exception as e:
        logger.error(f"共享记忆错误: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e

# 清理旧记忆
@app.post("/api/memory/cleanup")
async def cleanup_memories(background_tasks: BackgroundTasks):
    """清理旧记忆（后台任务）"""
    background_tasks.add_task(memory_system.cleanup_old_memories)
    return {"status": "accepted", "message": "记忆清理任务已启动"}

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="记忆系统API服务器")
    parser.add_argument("--port", type=int, default=8003, help="服务端口")
    parser.add_argument("--host", type=str, default="0.0.0.0", help="服务主机")

    args = parser.parse_args()

    uvicorn.run(
        "memory_api_server:app",
        host=args.host,
        port=args.port,
        reload=True,
        log_level="info"
    )
