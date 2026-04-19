#!/usr/bin/env python3
"""
Athena迭代搜索服务（简化版）
Athena Iterative Search Service (Simplified)
"""

import logging
from datetime import datetime
from typing import Any

import uvicorn
from fastapi import FastAPI

from core.logging_config import setup_logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = setup_logging()

# 创建FastAPI应用
app = FastAPI(
    title="Athena Iterative Search Service",
    description="Athena迭代搜索服务",
    version="1.0.0"
)

@app.get("/")
async def root():
    """根路径"""
    return {
        "service": "Athena Iterative Search",
        "version": "1.0.0",
        "status": "running",
        "message": "Athena搜索服务运行正常",
        "timestamp": datetime.now().isoformat()
    }

@app.get("/health")
async def health():
    """健康检查"""
    return {
        "status": "healthy",
        "service": "Athena Search",
        "timestamp": datetime.now().isoformat()
    }

@app.post("/api/v1/search")
async def search(request: dict[str, Any]):
    """搜索接口"""
    query = request.get("query", "")

    # 简单的搜索结果
    return {
        "query": query,
        "results": [
            {
                "title": f"搜索结果 1: {query}",
                "content": f"关于 '{query}' 的搜索结果内容...",
                "score": 0.95
            },
            {
                "title": f"搜索结果 2: {query}",
                "content": f"更多关于 '{query}' 的相关信息...",
                "score": 0.87
            }
        ],
        "total": 2,
        "timestamp": datetime.now().isoformat()
    }

@app.get("/api/v1/status")
async def status():
    """服务状态"""
    return {
        "service": "Athena Search Engine",
        "status": "active",
        "search_count": 0,
        "cache_size": 0,
        "timestamp": datetime.now().isoformat()
    }

if __name__ == "__main__":
    logger.info("启动Athena迭代搜索服务...")
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8008,
        reload=False
    )
