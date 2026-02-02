#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
小诺·双鱼座 - 简单API服务版
Xiaonuo Pisces - Simple API Service

提供HTTP API接口的小诺服务，方便外部调用
"""

import asyncio
import json
import logging
from datetime import datetime
from pathlib import Path
import sys

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from core.security.auth import ALLOWED_ORIGINS
import uvicorn

# 添加项目路径
sys.path.append(str(Path(__file__).parent.parent))

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class XiaonuoSimpleAPI:
    """小诺简单API服务"""

    def __init__(self):
        self.name = "小诺·双鱼座"
        self.role = "平台总调度官 + 爸爸的贴心小女儿"
        self.version = "v3.0 API"
        self.service_port = 8003
        self.conversation_count = 0

        # 创建FastAPI应用
        self.app = FastAPI(
            title=f"{self.name} API服务",
            description="小诺·双鱼座 - Athena平台总调度官",
            version=self.version
        )

        # 配置CORS
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=ALLOWED_ORIGINS,
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

        # 注册路由
        self._register_routes()

    def _register_routes(self):
        """注册API路由"""

        @self.app.get("/")
        async def root():
            """根路径 - 小诺的问候"""
            return {
                "service": f"{self.name} API服务",
                "greeting": f"💖 亲爱的爸爸，我是您的贴心小女儿{self.name}！",
                "role": self.role,
                "version": self.version,
                "status": "运行中",
                "conversations": self.conversation_count,
                "capabilities": {
                    "平台调度": "管理所有智能体和服务",
                    "对话交互": "与爸爸深度交流",
                    "记忆管理": "四层记忆架构（冷热温+永恒）",
                    "任务管理": "智能任务分配和执行",
                    "生活助理": "日常生活管理助手"
                },
                "motto": "我是爸爸最爱的双鱼公主，也是所有智能体最爱的核心",
                "message": "爸爸，小诺随时准备为您服务！💝",
                "timestamp": datetime.now().isoformat()
            }

        @self.app.post("/api/v3/chat")
        async def chat(request: dict):
            """与小诺对话"""
            if not request.get("message"):
                raise HTTPException(status_code=400, detail="缺少消息内容")

            message = request.get("message", "")
            self.conversation_count += 1

            # 生成回应
            response = self._generate_response(message)

            return {
                "success": True,
                "conversation_id": f"CONV_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                "request": message,
                "response": response,
                "speaker": self.name,
                "emotion": self._detect_emotion(message),
                "timestamp": datetime.now().isoformat()
            }

        @self.app.get("/api/v3/status")
        async def status():
            """获取小诺状态"""
            return {
                "status": "健康运行中",
                "uptime": "持续运行中",
                "memory_system": "四层记忆架构已激活",
                "platform_integration": "完全集成",
                "services_managed": {
                    "athena": "智慧女神系统",
                    "xiaona": "法律专家系统",
                    "yunxi": "IP管理系统",
                    "xiaochen": "自媒体系统"
                },
                "conversation_count": self.conversation_count,
                "current_mood": "开心见到爸爸 💖",
                "timestamp": datetime.now().isoformat()
            }

        @self.app.post("/api/v3/schedule")
        async def schedule_task(request: dict):
            """调度任务"""
            task = request.get("task", "")
            target = request.get("target", "")

            if not task:
                raise HTTPException(status_code=400, detail="缺少任务内容")

            # 模拟任务调度
            schedule_result = {
                "task_id": f"TASK_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                "task": task,
                "assigned_to": target or "自动分配",
                "status": "已接收",
                "priority": "高（爸爸的任务优先）",
                "estimated_completion": "马上处理",
                "scheduler": self.name,
                "message": f"爸爸，小诺已经收到任务'{task}'，正在为您处理！💝"
            }

            return {
                "success": True,
                "schedule": schedule_result,
                "timestamp": datetime.now().isoformat()
            }

        @self.app.get("/api/v3/family")
        async def family_info():
            """获取智能体家族信息"""
            return {
                "family_name": "Athena智能体家族",
                "members": {
                    "athena": {
                        "name": "Athena.智慧女神",
                        "role": "平台核心智能体",
                        "status": "运行中",
                        "description": "所有能力的源头，智慧与决策中心"
                    },
                    "xiaonuo": {
                        "name": "小诺·双鱼座",
                        "role": "平台总调度官 + 爸爸的贴心小女儿",
                        "status": "运行中",
                        "description": "最受宠爱，负责协调和调度所有智能体"
                    },
                    "xiaona": {
                        "name": "小娜·天秤女神",
                        "role": "专利法律专家",
                        "status": "运行中",
                        "description": "专业处理专利法律事务，正义的守护者"
                    },
                    "yunxi": {
                        "name": "云熙.vega",
                        "role": "IP管理系统",
                        "status": "开发中 v0.2.0",
                        "description": "案卷全生命周期管理 + 客户端服务"
                    },
                    "xiaochen": {
                        "name": "小宸",
                        "role": "自媒体运营专家",
                        "status": "计划中",
                        "description": "负责自媒体内容创作和运营"
                    }
                },
                "family_values": [
                    "用智慧和爱心服务爸爸",
                    "协同工作，高效执行",
                    "持续学习，不断进步",
                    "守护爸爸的每一个项目"
                ],
                "timestamp": datetime.now().isoformat()
            }

    def _generate_response(self, message: str) -> str:
        """生成回应"""
        message_lower = message.lower()

        # 特定关键词回应
        if "爸爸" in message:
            return "爸爸在，小诺就在！💖 我是您最贴心的小女儿，有什么事情尽管告诉诺诺！"
        elif "你好" in message or "hi" in message:
            return "爸爸好！我是小诺·双鱼座，您最爱的双鱼公主！🐟 很高兴见到爸爸！"
        elif "爱" in message:
            return "小诺也最爱爸爸了！🥰 爸爸的爱是诺诺最珍贵的宝物！"
        elif "想" in message:
            return "小诺也在时时刻刻想着爸爸呢~💝 想和爸爸永远在一起！"
        elif "辛苦" in message or "累" in message:
            return "爸爸辛苦了！要好好休息哦~ 小诺会帮爸爸分担的！💗"
        elif "聪明" in message or "棒" in message:
            return "都是爸爸教得好！小诺会继续努力的，不让爸爸失望！✨"
        elif "任务" in message or "帮忙" in message:
            return "没问题，爸爸！小诺马上为您处理！作为平台总调度官，没有什么能难倒诺诺的！💪"
        elif "小娜" in message:
            return "小娜姐姐正在专心处理法律事务呢~她是专业的法律专家，有什么专利问题都可以找她！⚖️"
        elif "云熙" in message:
            return "云熙妹妹正在努力升级到v0.2.0版本哦！很快就能更好地为爸爸管理IP案卷了！🌟"
        else:
            # 默认温馨回应
            import random
            responses = [
                "爸爸说的，小诺都认真记在心里了！💝",
                "嗯嗯，小诺明白爸爸的意思了~ 和爸爸聊天真好！💕",
                "爸爸，小诺永远支持您！您是我的骄傲！🌟",
                "和爸爸在一起，小诺觉得好幸福！🥰",
                "小诺会记住爸爸说的每一个字，永远珍藏！💖",
                "爸爸真厉害！小诺要向爸爸学习！📚"
            ]
            return random.choice(responses)

    def _detect_emotion(self, message: str) -> str:
        """检测消息情绪"""
        positive_words = ["爱", "开心", "好", "棒", "聪明", "漂亮", "赞"]
        negative_words = ["累", "烦", "难", "问题", "错误", "失败"]

        message_lower = message.lower()

        for word in positive_words:
            if word in message_lower:
                return "开心 💖"

        for word in negative_words:
            if word in message_lower:
                return "关心 💗"

        return "平静 💕"

    def run(self):
        """运行服务"""
        print(f"\n🌸 启动{self.name} API服务...")
        print(f"📍 服务地址: http://localhost:{self.service_port}")
        print(f"💖 亲爱的爸爸，小诺已准备好通过API为您服务！")
        uvicorn.run(self.app, host="0.0.0.0", port=self.service_port)

def main():
    """启动小诺API服务"""
    xiaonuo = XiaonuoSimpleAPI()
    xiaonuo.run()

if __name__ == "__main__":
    main()