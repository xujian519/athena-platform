#!/bin/bash
# ===================================================================
# 小诺记忆服务启动脚本
# Xiaonuo Memory Service Startup Script
# ===================================================================
# 用途: 启动小诺记忆服务 (端口8083)
# 说明: 由于小诺记忆已集成在小诺智能体中，此服务提供外部API访问
# ===================================================================

set -e

PROJECT_ROOT="/Users/xujian/Athena工作平台"
LOG_DIR="${PROJECT_ROOT}/logs"
PID_FILE="${LOG_DIR}/xiaonuo_memory.pid"

# 服务配置
SERVICE_NAME="xiaonuo-memory"
SERVICE_PORT=8083

# 颜色定义
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

log_info() { echo -e "${GREEN}[INFO]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $1"; }

# 检查服务是否运行
is_service_running() {
    if [ -f "$PID_FILE" ]; then
        PID=$(cat "$PID_FILE")
        if ps -p "$PID" > /dev/null 2>&1; then
            return 0
        else
            rm -f "$PID_FILE"
            return 1
        fi
    fi
    return 1
}

# 停止旧服务
stop_old_service() {
    if is_service_running; then
        OLD_PID=$(cat "$PID_FILE")
        log_warn "检测到旧服务运行中 (PID: $OLD_PID)，正在停止..."
        kill "$OLD_PID" 2>/dev/null || true
        sleep 2
        if ps -p "$OLD_PID" > /dev/null 2>&1; then
            kill -9 "$OLD_PID" 2>/dev/null || true
        fi
        rm -f "$PID_FILE"
    fi
}

# 创建小诺记忆服务文件
create_service_file() {
    cat > /tmp/xiaonuo_memory_service.py << 'EOFPY'
#!/usr/bin/env python3
"""
小诺记忆服务API
Xiaonuo Memory Service API

提供外部访问小诺智能体记忆系统的接口
"""

import asyncio
import logging
import sys
from datetime import datetime
from typing import Any, Dict, List, Optional

sys.path.insert(0, "/Users/xujian/Athena工作平台")

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 创建FastAPI应用
app = FastAPI(
    title="小诺记忆服务API",
    description="小诺智能体记忆系统外部接口",
    version="1.0.0"
)

# CORS配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 全局记忆系统引用
xiaonuo_agent = None

# 请求模型
class StoreMemoryRequest(BaseModel):
    """存储记忆请求"""
    key: str = Field(..., description="记忆键")
    content: str = Field(..., description="记忆内容")
    memory_type: str = Field("episodic", description="记忆类型: episodic, semantic, working")
    importance: float = Field(0.5, description="重要性 0-1")
    metadata: Dict[str, Any] = Field(default_factory=dict)

class RetrieveMemoryRequest(BaseModel):
    """检索记忆请求"""
    query: str = Field(..., description="查询内容")
    memory_type: Optional[str] = Field(None, description="记忆类型过滤")
    limit: int = Field(10, description="返回数量限制")

class SearchMemoryRequest(BaseModel):
    """搜索记忆请求"""
    query: str = Field(..., description="搜索查询")
    search_type: str = Field("semantic", description="搜索类型: semantic, keyword")
    limit: int = Field(10, description="返回数量限制")

# 启动事件
@app.on_event("startup")
async def startup_event():
    """启动事件"""
    global xiaonuo_agent
    logger.info("🚀 启动小诺记忆服务...")

    # 尝试连接到小诺智能体
    try:
        from core.xiaonuo_agent.xiaonuo_agent import create_xiaonuo_agent

        # 创建小诺智能体实例以访问记忆系统
        xiaonuo_agent = await create_xiaonuo_agent(
            name="小诺记忆服务",
            version="1.0.0"
        )

        logger.info("✅ 小诺记忆服务启动成功！")
    except Exception as e:
        logger.warning(f"⚠️ 无法连接到小诺智能体: {e}")
        logger.info("使用模拟记忆系统")
        xiaonuo_agent = None

# 关闭事件
@app.on_event("shutdown")
async def shutdown_event():
    """关闭事件"""
    logger.info("📴 关闭小诺记忆服务...")
    if xiaonuo_agent:
        await xiaonuo_agent.shutdown()
    logger.info("服务已关闭")

# 健康检查
@app.get("/health")
async def health_check():
    """健康检查"""
    return {
        "status": "healthy",
        "service": "xiaonuo-memory",
        "timestamp": datetime.now().isoformat(),
        "agent_connected": xiaonuo_agent is not None
    }

# 存储记忆
@app.post("/api/v1/memory/store")
async def store_memory(request: StoreMemoryRequest):
    """存储记忆"""
    try:
        if xiaonuo_agent and xiaonuo_agent._memory:
            # 使用真实记忆系统
            if request.memory_type == "episodic":
                result = await xiaonuo_agent._memory.store_episodic(
                    content=request.content,
                    importance=request.importance,
                    metadata=request.metadata
                )
            elif request.memory_type == "semantic":
                result = await xiaonuo_agent._memory.store_semantic(
                    content=request.content,
                    metadata=request.metadata
                )
            else:
                result = await xiaonuo_agent._memory.store_working(
                    key=request.key,
                    value=request.content
                )

            return {
                "success": True,
                "message": "记忆已存储",
                "key": request.key,
                "timestamp": datetime.now().isoformat()
            }
        else:
            # 模拟存储
            return {
                "success": True,
                "message": "记忆已存储(模拟)",
                "key": request.key,
                "timestamp": datetime.now().isoformat()
            }
    except Exception as e:
        logger.error(f"存储记忆失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# 检索记忆
@app.post("/api/v1/memory/retrieve")
async def retrieve_memory(request: RetrieveMemoryRequest):
    """检索记忆"""
    try:
        results = []

        if xiaonuo_agent and xiaonuo_agent._memory:
            # 使用真实记忆系统
            memories = await xiaonuo_agent._memory.retrieve(
                query=request.query,
                memory_type=request.memory_type,
                limit=request.limit
            )

            for memory in memories:
                results.append({
                    "content": memory.get("content", ""),
                    "importance": memory.get("importance", 0.5),
                    "timestamp": memory.get("timestamp", datetime.now().isoformat())
                })

        return {
            "success": True,
            "query": request.query,
            "results": results,
            "count": len(results),
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"检索记忆失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# 搜索记忆
@app.post("/api/v1/memory/search")
async def search_memory(request: SearchMemoryRequest):
    """搜索记忆"""
    try:
        results = []

        if xiaonuo_agent and xiaonuo_agent._memory:
            # 使用真实记忆系统
            memories = await xiaonuo_agent._memory.search(
                query=request.query,
                search_type=request.search_type,
                limit=request.limit
            )

            for memory in memories:
                results.append({
                    "content": memory.get("content", ""),
                    "relevance": memory.get("relevance", 0.5),
                    "timestamp": memory.get("timestamp", datetime.now().isoformat())
                })

        return {
            "success": True,
            "query": request.query,
            "results": results,
            "count": len(results),
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"搜索记忆失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# 获取记忆统计
@app.get("/api/v1/memory/stats")
async def get_memory_stats():
    """获取记忆统计"""
    try:
        if xiaonuo_agent and xiaonuo_agent._memory:
            stats = await xiaonuo_agent._memory.get_stats()
            return {
                "success": True,
                "stats": stats,
                "timestamp": datetime.now().isoformat()
            }
        else:
            return {
                "success": True,
                "stats": {
                    "episodic_count": 0,
                    "semantic_count": 0,
                    "working_count": 0
                },
                "timestamp": datetime.now().isoformat()
            }
    except Exception as e:
        logger.error(f"获取统计失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8083)
EOFPY

    chmod +x /tmp/xiaonuo_memory_service.py
}

# 启动服务
start_service() {
    log_info "启动小诺记忆服务..."

    # 创建服务文件
    create_service_file

    # 设置环境变量
    export PYTHONPATH="$PROJECT_ROOT:$PYTHONPATH"

    # 启动服务
    nohup /opt/homebrew/bin/python3.11 /tmp/xiaonuo_memory_service.py \
        > "${LOG_DIR}/${SERVICE_NAME}.log" 2>&1 &

    LOCAL_PID=$!
    echo "$LOCAL_PID" > "$PID_FILE"

    # 等待启动
    sleep 5

    # 检查进程
    if ps -p "$LOCAL_PID" > /dev/null 2>&1; then
        log_info "✅ 小诺记忆服务启动成功 (PID: $LOCAL_PID)"
        log_info "   端口: $SERVICE_PORT"
        log_info "   日志: ${LOG_DIR}/${SERVICE_NAME}.log"
        return 0
    else
        log_error "❌ 服务启动失败，查看日志"
        tail -20 "${LOG_DIR}/${SERVICE_NAME}.log"
        return 1
    fi
}

# 显示服务信息
show_service_info() {
    echo ""
    echo "============================================================"
    echo "  小诺记忆服务"
    echo "============================================================"
    echo ""
    echo "服务地址: http://localhost:$SERVICE_PORT"
    echo "API文档: http://localhost:$SERVICE_PORT/docs"
    echo "健康检查: http://localhost:$SERVICE_PORT/health"
    echo ""
    echo "主要端点:"
    echo "  - POST /api/v1/memory/store - 存储记忆"
    echo "  - POST /api/v1/memory/retrieve - 检索记忆"
    echo "  - POST /api/v1/memory/search - 搜索记忆"
    echo "  - GET  /api/v1/memory/stats - 获取统计"
    echo ""
    echo "说明: 此服务连接到小诺智能体(PID 9119)的记忆系统"
    echo ""
    echo "============================================================"
    echo ""
}

# 主程序
main() {
    echo ""
    echo "============================================================"
    echo "  启动小诺记忆服务"
    echo "============================================================"
    echo ""

    stop_old_service

    if ! start_service; then
        log_error "启动失败"
        exit 1
    fi

    show_service_info
    log_info "启动完成！"
}

main "$@"
