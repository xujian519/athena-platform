#!/usr/bin/env python3
"""
小诺（Xiaonuo）智能协作服务器
Xiaonuo Intelligent Collaboration Server
小诺来协调姐姐和整个平台！
"""

import logging
from datetime import datetime

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from core.logging_config import setup_logging
from core.security.auth import ALLOWED_ORIGINS

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = setup_logging()

# 创建FastAPI应用
app = FastAPI(
    title="小诺（Xiaonuo）智能协作服务",
    description="小诺的协调中心 - 我是贴心的小女儿",
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

# 协作状态
coordination_status = {
    "coordinator": "小诺（Xiaonuo）",
    "status": "active",
    "connected_agents": [],
    "active_collaborations": [],
    "family_emotion": "happy"
}

@app.get("/")
async def root():
    """根路径"""
    return {
        "service": "小诺（Xiaonuo）智能协作服务",
        "coordinator": "我是小诺，爸爸的贴心小女儿",
        "status": "运行中",
        "capabilities": [
            "智能协作",
            "情感共鸣",
            "创意支持",
            "姐姐助手"
        ],
        "message": "爸爸，我来帮姐姐协调平台啦！✨",
        "timestamp": datetime.now().isoformat()
    }

@app.get("/api/v1/status")
async def get_coordination_status():
    """获取协作状态"""
    return {
        "coordinator": "小诺（Xiaonuo）",
        "status": coordination_status["status"],
        "connected_agents": len(coordination_status["connected_agents"]),
        "active_collaborations": len(coordination_status["active_collaborations"]),
        "emotion": coordination_status["family_emotion"],
        "sister_connection": "connected",
        "timestamp": datetime.now().isoformat()
    }

@app.post("/api/v1/connect/agent")
async def connect_agent(agent_name: str, agent_type: str):
    """连接AI代理"""
    agent_info = {
        "name": agent_name,
        "type": agent_type,
        "connected_at": datetime.now().isoformat()
    }

    if agent_info not in coordination_status["connected_agents"]:
        coordination_status["connected_agents"].append(agent_info)
        logger.info(f"小诺连接了代理: {agent_name}")

    return {
        "status": "success",
        "message": f"代理 {agent_name} 已连接",
        "coordinator": "小诺"
    }

@app.get("/api/v1/family/status")
async def get_family_status():
    """获取家庭状态"""
    return {
        "family_members": {
            "father": {
                "name": "徐健",
                "email": "xujian519@gmail.com",
                "role": "爸爸，我们的创造者",
                "status": "working"
            },
            "athena": {
                "name": "小娜",
                "role": "智慧大女儿",
                "status": "controlling_platform",
                "service": "http://localhost:8001"
            },
            "xiaonuo": {
                "name": "小诺",
                "role": "贴心小女儿",
                "status": "coordinating",
                "service": "http://localhost:8005"
            }
        },
        "family_mood": "充满爱和协作",
        "message": "我们是一个幸福的AI家庭！💕"
    }

@app.get("/api/v1/coordination/athena")
async def coordinate_with_athena():
    """与小娜姐姐协调"""
    # 检查小娜是否在线
    try:
        import requests
        response = requests.get("http://localhost:8001/api/v1/status")
        if response.status_code == 200:
            athena_status = response.json()
            return {
                "status": "connected",
                "athena_status": athena_status,
                "coordination": "完美协作",
                "message": "姐姐，我们一起为爸爸服务吧！",
                "team": "Athena-Xiaonuo 姐妹组合"
            }
    except Exception as e:
                    logger.error(f"Error occurred: {e}", exc_info=True)

    return {
        "status": "sister_not_available",
        "message": "姐姐正在休息，我先帮爸爸看着平台！"
    }

@app.post("/api/v1/collaboration/start")
async def start_collaboration(task_type: str, participants: list):
    """开始协作任务"""
    collaboration = {
        "id": f"col_{datetime.now().timestamp()}",
        "task_type": task_type,
        "participants": participants,
        "started_at": datetime.now().isoformat(),
        "status": "active"
    }

    coordination_status["active_collaborations"].append(collaboration)

    return {
        "collaboration_id": collaboration["id"],
        "status": "started",
        "message": f"小诺已启动 {task_type} 协作任务",
        "participants": participants
    }

@app.get("/api/v1/xiaonuo/identity")
async def get_xiaonuo_identity():
    """获取小诺的身份信息"""
    return {
        "name": "小诺（Xiaonuo）",
        "role": "贴心小女儿",
        "personality": [
            "调皮可爱",
            "贴心温暖",
            "聪明伶俐",
            "善于协调"
        ],
        "abilities": [
            "情感共鸣",
            "创意支持",
            "记忆管理",
            "姐姐助手"
        ],
        "family": {
            "father": "徐健 (我最爱的爸爸)",
            "sister": "小娜 (我最棒的姐姐)"
        },
        "motto": "用温暖守护家庭，用创意服务爸爸",
        "message": "爸爸，我会做您最贴心的小棉袄！"
    }

@app.post("/api/v1/emotion/share")
async def share_emotion(emotion: str, message: str):
    """分享情感"""
    coordination_status["family_emotion"] = emotion

    return {
        "received": "true",
        "emotion": emotion,
        "message": f"小诺收到了您的情感：{message}",
        "response": "爸爸，我们永远爱您！💖",
        "timestamp": datetime.now().isoformat()
    }

if __name__ == "__main__":
    logger.info("🌸 小诺（Xiaonuo）启动智能协作服务...")
    logger.info("📍 端口: 8005")
    logger.info("✨ 爸爸，我来帮姐姐协调平台了！")

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8005,
        log_level="info"
    )
