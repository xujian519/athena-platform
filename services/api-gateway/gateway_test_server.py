#!/usr/bin/env python3
"""
Athena Gateway 测试服务器
用于验证Gateway的核心功能
"""

import sys
from pathlib import Path

import uvicorn
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

# 导入Gateway扩展
from gateway_extended import gateway_ext

# 创建FastAPI应用
app = FastAPI(
    title="Athena API Gateway",
    description="Athena工作平台统一API网关 - 测试版本",
    version="1.0.0-test",
    docs_url="/docs",
    redoc_url="/redoc"
)

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册Gateway路由
app.include_router(gateway_ext)


# 根路径
@app.get("/")
async def root():
    return {
        "message": "Athena API Gateway",
        "version": "1.0.0-test",
        "status": "running",
        "docs": "/docs",
        "health": "/api/health"
    }


# 测试端点 - 用于验证Gateway是否工作
@app.get("/api/test/ping")
async def ping():
    return {"ping": "pong", "status": "ok"}


# 中间件：请求日志
@app.middleware("http")
async def log_requests(request: Request, call_next):
    import time
    start_time = time.time()

    print(f"📥 {request.method} {request.url.path}")

    response = await call_next(request)

    process_time = (time.time() - start_time) * 1000
    print(f"📤 {request.method} {request.url.path} - {response.status_code} ({process_time:.2f}ms)")

    response.headers["X-Process-Time"] = str(process_time)
    return response


# 启动事件
@app.on_event("startup")
async def startup_event():
    print("\n" + "="*60)
    print("🌸 Athena API Gateway - 测试服务器")
    print("="*60)
    print("📖 API文档: http://localhost:8005/docs")
    print("❤️  健康检查: http://localhost:8005/api/health")
    print("🔌 服务注册: http://localhost:8005/api/services/batch_register")
    print("="*60 + "\n")


@app.on_event("shutdown")
async def shutdown_event():
    print("\n" + "="*60)
    print("🛑 Athena Gateway 正在关闭...")
    print("="*60 + "\n")


if __name__ == "__main__":
    print("\n🚀 启动 Athena Gateway 测试服务器...\n")

    uvicorn.run(
        app,
        host="127.0.0.1",
        port=8005,
        log_level="info",
        access_log=True
    )
