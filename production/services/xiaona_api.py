#!/usr/bin/env python3
"""
小娜FastAPI服务
提供REST API接口
"""

from __future__ import annotations
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

import logging
from typing import Any

import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from core.security.auth import ALLOWED_ORIGINS

# 导入代理
try:
    from xiaona_agent_v2 import QueryRequest, QueryResponse, XiaonaAgentV2
except ImportError:
    # 如果在同一目录
    import sys
    sys.path.insert(0, '.')
    from xiaona_agent_v2 import QueryRequest, XiaonaAgentV2

# 初始化
app = FastAPI(
    title="小娜 API",
    description="专利法律AI助手 - v2.1 Production",
    version="2.1.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 全局代理
agent: XiaonaAgentV2 | None = None

# 日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class QueryInput(BaseModel):
    """查询输入"""
    message: str
    scenario: str = "general"
    use_rag: bool = True


@app.on_event("startup")
async def startup_event():
    """启动事件"""
    global agent
    logger.info("初始化小娜代理...")
    agent = XiaonaAgentV2()
    logger.info("小娜代理初始化完成")


@app.get("/")
async def root():
    """根路径"""
    return {
        "service": "小娜 API",
        "version": "2.1.0",
        "status": "running",
        "docs": "/docs"
    }


@app.get("/health")
async def health():
    """健康检查"""
    if agent:
        return agent.get_status()
    return {"status": "initializing"}


@app.post("/query")
async def query(input: QueryInput) -> dict[str, Any]:
    """查询接口"""
    if not agent:
        raise HTTPException(status_code=503, detail="代理未初始化")

    request = QueryRequest(
        message=input.message,
        scenario=input.scenario,
        use_rag=input.use_rag
    )

    response = agent.query(request)

    return {
        "response": response.response,
        "scenario": response.scenario,
        "need_human_input": response.need_human_input,
        "tokens": {
            "prompt": response.prompt_tokens,
            "completion": response.completion_tokens,
            "total": response.total_tokens
        },
        "provider": response.provider,
        "latency_ms": response.latency_ms,
        "rag_used": response.rag_used
    }


@app.post("/switch_scenario/{scenario}")
async def switch_scenario(scenario: str):
    """切换场景"""
    if not agent:
        raise HTTPException(status_code=503, detail="代理未初始化")

    if scenario not in ["general", "patent_writing", "office_action"]:
        raise HTTPException(status_code=400, detail="无效的场景")

    message = agent.switch_scenario(scenario)
    return {"message": message, "scenario": scenario}


@app.post("/reset")
async def reset():
    """重置对话"""
    if not agent:
        raise HTTPException(status_code=503, detail="代理未初始化")

    message = agent.reset_conversation()
    return {"message": message}


if __name__ == "__main__":
    uvicorn.run(
        "xiaona_api:app",
        host="0.0.0.0",
        port=8001,  # 修改为8001端口以匹配服务管理器配置
        reload=True,
        log_level="info"
    )
