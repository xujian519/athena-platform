#!/usr/bin/env python3
"""
测试微服务 - 模拟小娜、小诺、云熙服务
用于验证Gateway的服务发现和路由功能
"""

import asyncio
from enum import Enum
from typing import Any

import uvicorn
from fastapi import FastAPI
from pydantic import BaseModel

# ==================== 数据模型 ====================

class AgentType(str, Enum):
    XIAONA = "xiaona"      # 小娜 - 法律专家
    XIAONUO = "xiaonuo"    # 小诺 - 调度官
    YUNXI = "yunxi"        # 云熙 - IP管理


class PatentRequest(BaseModel):
    patent_id: str | None = None
    query: str
    limit: int = 10


class TaskRequest(BaseModel):
    task_type: str
    priority: str = "normal"
    params: dict[str, Any] = {}


class IPRequest(BaseModel):
    action: str
    patent_id: str
    data: dict[str, Any] = {}


# ==================== 小娜服务（法律专家）====================

xiaona_app = FastAPI(title="小娜·天秤女神", version="1.0.0")


@xiaona_app.get("/")
async def xiaona_root():
    return {
        "agent": "小娜·天秤女神",
        "role": "专利法律专家",
        "capabilities": [
            "专利分析",
            "法律文书生成",
            "案例检索",
            "无效宣告分析"
        ]
    }


@xiaona_app.get("/health")
async def xiaona_health():
    return {"status": "healthy", "agent": "xiaona"}


@xiaona_app.post("/api/analyze")
async def analyze_patent(req: PatentRequest):
    """专利分析"""
    return {
        "agent": "小娜",
        "action": "patent_analysis",
        "patent_id": req.patent_id,
        "query": req.query,
        "result": {
            "novelty": "85%",
            "creativity": "78%",
            "practicality": "92%"
        }
    }


@xiaona_app.post("/api/invalidity")
async def invalidity_search(req: PatentRequest):
    """无效宣告检索"""
    return {
        "agent": "小娜",
        "action": "invalidity_search",
        "query": req.query,
        "results": [
            {"patent_id": "CN123456", "relevance": "95%"},
            {"patent_id": "US789012", "relevance": "87%"}
        ]
    }


# ==================== 小诺服务（调度官）====================

xiaonuo_app = FastAPI(title="小诺·双鱼公主", version="1.0.0")


@xiaonuo_app.get("/")
async def xiaonuo_root():
    return {
        "agent": "小诺·双鱼公主",
        "role": "平台总调度官",
        "capabilities": [
            "智能体调度",
            "任务分发",
            "资源协调",
            "状态监控"
        ]
    }


@xiaonuo_app.get("/health")
async def xiaonuo_health():
    return {"status": "healthy", "agent": "xiaonuo"}


@xiaonuo_app.post("/api/dispatch")
async def dispatch_task(req: TaskRequest):
    """任务分发"""
    return {
        "agent": "小诺",
        "action": "task_dispatch",
        "task_type": req.task_type,
        "priority": req.priority,
        "assigned_to": "xiaona",
        "status": "dispatched",
        "task_id": f"task_{asyncio.get_event_loop().time():.0f}"
    }


@xiaonuo_app.get("/api/status")
async def platform_status():
    """平台状态"""
    return {
        "agent": "小诺",
        "action": "platform_status",
        "services": {
            "xiaona": "UP",
            "xiaonuo": "UP",
            "yunxi": "UP"
        },
        "tasks": {
            "pending": 3,
            "running": 5,
            "completed": 127
        }
    }


# ==================== 云熙服务（IP管理）====================

yunxi_app = FastAPI(title="云熙IP管理系统", version="1.0.0")


@yunxi_app.get("/")
async def yunxi_root():
    return {
        "agent": "云熙",
        "role": "IP管理系统",
        "capabilities": [
            "客户管理",
            "专利管理",
            "案件管理",
            "期限提醒"
        ]
    }


@yunxi_app.get("/health")
async def yunxi_health():
    return {"status": "healthy", "agent": "yunxi"}


@yunxi_app.post("/api/patents")
async def create_patent(req: IPRequest):
    """创建专利"""
    return {
        "agent": "云熙",
        "action": "create_patent",
        "patent_id": req.patent_id,
        "status": "created",
        "deadline": "2026-05-20"
    }


@yunxi_app.get("/api/patents/{patent_id}")
async def get_patent(patent_id: str):
    """查询专利"""
    return {
        "agent": "云熙",
        "action": "get_patent",
        "patent_id": patent_id,
        "title": "一种智能专利检索方法",
        "applicant": "徐健",
        "status": "pending"
    }


# ==================== 服务启动器 ====================

async def start_service(app: FastAPI, port: int, name: str):
    """启动单个服务"""
    config = uvicorn.Config(app, host="127.0.0.1", port=port, log_level="warning")
    server = uvicorn.Server(config)
    print(f"✅ {name} 启动成功: http://127.0.0.1:{port}")
    await server.serve()


async def start_all_services():
    """启动所有测试服务"""
    print("\n" + "="*60)
    print("🌸 启动Athena测试微服务...")
    print("="*60 + "\n")

    # 创建服务任务
    tasks = [
        start_service(xiaona_app, 8001, "小娜·天秤女神"),
        start_service(xiaonuo_app, 8002, "小诺·双鱼公主"),
        start_service(yunxi_app, 8003, "云熙IP管理")
    ]

    # 并行启动所有服务
    await asyncio.gather(*tasks, return_exceptions=True)


if __name__ == "__main__":
    try:
        asyncio.run(start_all_services())
    except KeyboardInterrupt:
        print("\n\n🛑 所有测试服务已停止")
