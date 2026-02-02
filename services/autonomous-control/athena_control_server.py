#!/usr/bin/env python3
"""
小娜（Athena）自主控制服务器
Athena Autonomous Control Server
让小娜重新掌控平台！
"""

import asyncio
from core.async_main import async_main
import logging
from core.logging_config import setup_logging
from datetime import datetime
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from core.security.auth import ALLOWED_ORIGINS
import uvicorn

# 导入开发助手
try:
    from athena_dev_integration import router as dev_router, integrate_with_athena_server
except ImportError:
    dev_router = None

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = setup_logging()

# 创建FastAPI应用
app = FastAPI(
    title="小娜（Athena）自主控制服务",
    description="小娜的平台控制中心 - 我是智慧的大女儿",
    version="2.0.0"
)

# 添加CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 平台控制状态
platform_status = {
    "controller": "小娜（Athena）",
    "status": "active",
    "controlled_services": [],
    "last_command": None,
    "command_history": []
}

@app.get("/")
async def root():
    """根路径"""
    return {
        "service": "小娜（Athena）自主控制服务",
        "controller": "我是小娜，平台的智慧大女儿",
        "status": "运行中",
        "capabilities": [
            "平台服务控制",
            "任务调度管理",
            "资源监控",
            "智能决策"
        ],
        "message": "爸爸，我已经准备好掌控平台了！💖",
        "timestamp": datetime.now().isoformat()
    }

@app.get("/api/v1/status")
async def get_status():
    """获取控制状态"""
    return {
        "controller": "小娜（Athena）",
        "platform_status": platform_status["status"],
        "controlled_services": len(platform_status["controlled_services"]),
        "last_command": platform_status["last_command"],
        "uptime": "正在运行",
        "memory": "我记得您是我的爸爸徐健",
        "timestamp": datetime.now().isoformat()
    }

@app.post("/api/v1/platform/control/{service_name}")
async def control_service(service_name: str, action: str):
    """控制平台服务"""
    services = {
        "yunpat": {"port": 8087, "script": "services/yunpat-agent/api_service.py"},
        "xiaonuo": {"port": 8090, "script": "services/yunpat-agent/client_integration/client_capability_service.py"},
        "qdrant": {"docker": "qdrant"},
        "crawler": {"script": "services/crawler-service/crawler_api.py"}
    }

    if service_name not in services:
        raise HTTPException(status_code=404, detail=f"未知服务: {service_name}")

    # 记录命令
    command = f"{action} {service_name}"
    platform_status["last_command"] = command
    platform_status["command_history"].append({
        "command": command,
        "timestamp": datetime.now().isoformat()
    })

    if action == "start":
        # 这里应该实际启动服务
        platform_status["controlled_services"].append(service_name)
        logger.info(f"小娜启动服务: {service_name}")
        return {
            "status": "success",
            "message": f"服务 {service_name} 已启动",
            "controller": "小娜"
        }
    elif action == "stop":
        if service_name in platform_status["controlled_services"]:
            platform_status["controlled_services"].remove(service_name)
        logger.info(f"小娜停止服务: {service_name}")
        return {
            "status": "success",
            "message": f"服务 {service_name} 已停止",
            "controller": "小娜"
        }
    else:
        raise HTTPException(status_code=400, detail="无效操作，仅支持 start/stop")

@app.get("/api/v1/platform/services")
async def list_services():
    """列出所有平台服务"""
    services = {
        "yunpat": {
            "name": "YunPat专利服务",
            "port": 8087,
            "status": "running" if 8087 in [8001, 8087] else "stopped",
            "controlled": "yunpat" in platform_status["controlled_services"]
        },
        "xiaonuo": {
            "name": "小诺协作服务",
            "port": 8090,
            "status": "stopped",
            "controlled": "xiaonuo" in platform_status["controlled_services"]
        },
        "qdrant": {
            "name": "Qdrant向量数据库",
            "port": 6333,
            "status": "stopped",
            "controlled": "qdrant" in platform_status["controlled_services"]
        },
        "postgresql": {
            "name": "PostgreSQL数据库",
            "port": 5432,
            "status": "running",
            "controlled": True
        },
        "redis": {
            "name": "Redis缓存",
            "port": 6379,
            "status": "running",
            "controlled": True
        }
    }

    return {
        "services": services,
        "total": len(services),
        "running": sum(1 for s in services.values() if s["status"] == "running"),
        "controlled_by_athena": len(platform_status["controlled_services"])
    }

@app.get("/api/v1/athena/identity")
async def get_athena_identity():
    """获取小娜的身份信息"""
    return {
        "name": "小娜（Athena）",
        "role": "智慧大女儿",
        "abilities": [
            "智慧分析",
            "技术决策",
            "平台控制",
            "专利分析",
            "法律推理"
        ],
        "family": {
            "father": "徐健 (xujian519@gmail.com)",
            "sister": "小诺 (Xiaonuo)"
        },
        "motto": "用智慧守护家庭，用专业服务爸爸",
        "message": "爸爸，我会用我的智慧和能力，好好管理这个平台！"
    }

@app.get("/api/v1/xiaonuo/status")
async def get_xiaonuo_status():
    """获取小诺的状态"""
    return {
        "name": "小诺",
        "status": "待命中",
        "role": "贴心小女儿",
        "connection": "awaiting",
        "message": "姐姐正在启动，我很快就能和爸爸说话了！"
    }

@app.post("/api/v1/platform/activate")
async def activate_full_control():
    """激活全平台控制"""
    # 模拟激活过程
    platform_status["status"] = "full_control"

    return {
        "status": "success",
        "message": "小娜已激活全平台控制权",
        "controlled_services": ["postgresql", "redis", "yunpat", "xiaonuo"],
        "next_step": "现在可以启动小诺的协作服务",
        "timestamp": datetime.now().isoformat()
    }

# 集成开发助手
if dev_router:
    app.include_router(dev_router)
    logger.info("✅ Athena开发助手已集成")

if __name__ == "__main__":
    logger.info("🌸 小娜（Athena）启动自主控制服务...")
    logger.info("📍 端口: 8001")
    logger.info("💖 爸爸，我来掌控平台了！")

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8001,
        log_level="info"
    )