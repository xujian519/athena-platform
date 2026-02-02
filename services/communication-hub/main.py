#!/usr/bin/env python3
"""
communication-hub - 服务描述
"""

import os
from core.async_main import async_main
import logging
from core.logging_config import setup_logging
from datetime import datetime
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from core.security.auth import ALLOWED_ORIGINS

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = setup_logging()

# 创建FastAPI应用
app = FastAPI(
    title="communication-hub",
    description="服务描述",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    """根路径"""
    return {
        "service": "communication-hub",
        "status": "running",
        "version": "1.0.0",
        "timestamp": datetime.now().isoformat()
    }

@app.get("/health")
async def health_check():
    """健康检查"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat()
    }

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)
