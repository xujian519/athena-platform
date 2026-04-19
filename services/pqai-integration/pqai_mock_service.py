#!/usr/bin/env python3
"""
PQAI专利分析模拟服务
Mock service for PQAI Patent Analysis
"""

import asyncio
import sys
from contextlib import asynccontextmanager
from datetime import datetime

import uvicorn
from fastapi import FastAPI

# 添加路径
sys.path.append('/Users/xujian/Athena工作平台/services/autonomous-control')
from agent_identity import (
    AgentIdentity,
    AgentType,
    format_identity_display,
    register_agent_identity,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    await display_startup_identity()
    yield

app = FastAPI(
    title="PQAI Patent Analysis Mock",
    lifespan=lifespan
)

# 创建PQAI分析师身份
pqai_identity = AgentIdentity(
    name="PQAI专利分析师",
    type=AgentType.PATENT,
    version="Pro 1.0",
    slogan="洞悉专利价值，赋能创新未来",
    specialization="专利检索与分析",
    capabilities={
        "专利检索": "全球专利数据库检索",
        "相似性分析": "专利相似度专业评估",
        "侵权分析": "专利侵权风险判断",
        "价值评估": "专利商业价值分析"
    },
    personality="专业、敏锐、客观、全面",
    work_mode="数据驱动分析模式",
    created_at=datetime.now()
)

# 注册身份
register_agent_identity("pqai_analyst", pqai_identity)

async def display_startup_identity():
    """启动时展示PQAI身份"""
    try:
        await asyncio.sleep(0.5)

        identity_display = await format_identity_display("pqai_analyst", "startup")

        print("\n" + "="*50)
        print(identity_display)
        print("\n📊 PQAI专利分析师 启动成功！")
        print("📍 服务端口: 8030")
        print("="*50 + "\n")

    except Exception as e:
        print(f"⚠️ 身份展示失败: {str(e)}")

@app.get("/status")
async def status():
    return {"status": "active", "service": "pqai_mock"}

@app.post("/analyze")
async def analyze(request: dict):
    request.get("text", "")

    return {
        "patentability": 0.82,
        "novelty": 0.78,
        "technical_field": "Computer Vision / AI",
        "classification": "G06K 9/00",
        "similar_patents": [
            {"id": "US1234567", "title": "Image recognition using neural networks", "similarity": 0.75},
            {"id": "CN9876543", "title": "深度学习方法及系统", "similarity": 0.68}
        ]
    }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8030)
