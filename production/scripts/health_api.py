#!/usr/bin/env python3
"""
健康检查API服务器
Health Check API Server

提供HTTP接口用于监控和健康检查

作者: Athena AI系统
创建时间: 2026-01-27
版本: v1.0.0
"""

from __future__ import annotations
from datetime import datetime
from pathlib import Path

import psutil
import uvicorn
from fastapi import FastAPI
from fastapi.responses import JSONResponse, PlainTextResponse

# 添加项目路径
project_root = Path(__file__).parent.parent.parent
import sys

sys.path.insert(0, str(project_root))

from core.execution.execution_engine.engine import ExecutionEngine

# 创建FastAPI应用
app = FastAPI(
    title="Athena平台健康检查API",
    description="提供生产环境监控和健康检查接口",
    version="1.0.0"
)


@app.get("/")
async def root():
    """根路径"""
    return {
        "service": "Athena平台健康检查API",
        "version": "1.0.0",
        "status": "running",
        "timestamp": datetime.now().isoformat()
    }


@app.get("/health")
async def health_check():
    """基础健康检查"""
    return JSONResponse({
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "services": {
            "api": "running"
        }
    })


@app.get("/health/detailed")
async def detailed_health_check():
    """详细健康检查"""
    health_data = {
        "timestamp": datetime.now().isoformat(),
        "system": {},
        "services": {}
    }

    # 系统指标
    process = psutil.Process()
    health_data["system"] = {
        "cpu_percent": process.cpu_percent(interval=0.1),
        "memory_mb": process.memory_info().rss / 1024 / 1024,
        "memory_percent": process.memory_percent(),
        "num_threads": process.num_threads()
    }

    # 服务状态
    pid_file = Path("production/pids/execution_engine.pid")
    if pid_file.exists():
        pid = int(pid_file.read_text().strip())
        if psutil.pid_exists(pid):
            health_data["services"]["execution_engine"] = {
                "status": "running",
                "pid": pid
            }
        else:
            health_data["services"]["execution_engine"] = {
                "status": "stopped",
                "pid": pid
            }
    else:
        health_data["services"]["execution_engine"] = {
            "status": "not_initialized"
        }

    return JSONResponse(health_data)


@app.get("/health/execution-engine")
async def execution_engine_health():
    """执行引擎健康检查"""
    try:
        engine = ExecutionEngine(agent_id="health_check")
        await engine.initialize()
        health = await engine.health_check()
        await engine.shutdown()

        return JSONResponse({
            "status": health.value,
            "timestamp": datetime.now().isoformat(),
            "details": health.details if hasattr(health, 'details') else {}
        })
    except Exception as e:
        return JSONResponse({
            "status": "error",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }, status=503)


@app.get("/metrics")
async def metrics():
    """Prometheus格式的指标"""
    metrics = []

    # 系统指标
    process = psutil.Process()
    cpu = process.cpu_percent(interval=0.1)
    memory = process.memory_info().rss / 1024 / 1024

    metrics.append("# HELP system_cpu_percent CPU使用率")
    metrics.append("# TYPE system_cpu_percent gauge")
    metrics.append(f"system_cpu_percent {cpu}")

    metrics.append("# HELP system_memory_mb 内存使用(MB)")
    metrics.append("# TYPE system_memory_mb gauge")
    metrics.append(f"system_memory_mb {memory}")

    return PlainTextResponse(
        content="\n".join(metrics)
    )


def main():
    """启动API服务器"""
    print("=" * 60)
    print("Athena平台健康检查API")
    print("=" * 60)
    print("启动HTTP服务器...")
    print("端点:")
    print("  - GET /                 : 基本信息")
    print("  - GET /health          : 基础健康检查")
    print("  - GET /health/detailed  : 详细健康检查")
    print("  - GET /health/execution-engine : 执行引擎健康")
    print("  - GET /metrics         : Prometheus指标")
    print("")
    print("服务地址: http://localhost:8081")
    print("=" * 60)

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8081,
        log_level="info"
    )


if __name__ == "__main__":
    main()
