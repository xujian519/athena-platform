#!/usr/bin/env python3
"""
决策API接口 - Decision API
提供REST API接口供外部系统调用决策服务

作者: 小诺·双鱼座
版本: v1.0.0 "决策API"
创建时间: 2025-12-17
"""

from datetime import datetime
from typing import Any

import uvicorn
from fastapi import BackgroundTasks, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

# 导入决策服务
from core.decision.decision_service import DecisionService
from core.security.auth import ALLOWED_ORIGINS

# 创建FastAPI应用
app = FastAPI(
    title="小诺决策API",
    description="人机协作决策服务API",
    version="1.0.0"
)

# 添加CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 初始化决策服务
decision_service = DecisionService()

# 后台任务
background_tasks = BackgroundTasks()

# Pydantic模型
class DecisionOption(BaseModel):
    id: str = Field(..., description="选项ID")
    title: str = Field(..., description="选项标题")
    description: str = Field(..., description="选项描述")
    confidence: float = Field(0.5, ge=0, le=1, description="置信度")
    risk_level: str = Field("medium", description="风险等级：low/medium/high")
    estimated_cost: float | None = Field(None, description="预估成本")
    expected_outcome: str | None = Field(None, description="预期结果")

class DecisionRequest(BaseModel):
    problem: str = Field(..., description="决策问题描述")
    options: list[DecisionOption] = Field(..., description="决策选项列表")
    category: str = Field("general", description="决策类别")
    context: dict[str, Any] | None = Field(None, description="上下文信息")

class QuickDecisionRequest(BaseModel):
    prompt: str = Field(..., description="决策提示词")
    options: list[str] | None = Field(None, description="快速选项列表")

class DecisionResponse(BaseModel):
    success: bool = Field(..., description="决策是否成功")
    chosen_option: str | None = Field(None, description="选择的选项ID")
    confidence: float = Field(..., description="决策置信度")
    human_feedback: str | None = Field(None, description="人类反馈")
    rationale: str | None = Field(None, description="决策理由")
    engine: str = Field(..., description="使用的决策引擎")
    timestamp: str = Field(..., description="决策时间")

class DecisionStats(BaseModel):
    total_decisions: int
    human_involved: int
    auto_decisions: int
    human_involvement_rate: str
    average_confidence: str
    categories: dict[str, int]
    recent_decisions: list[dict[str, str]

# API路由
@app.get("/")
async def root():
    return {
        "service": "小诺决策API",
        "version": "1.0.0",
        "description": "人机协作决策服务",
        "endpoints": {
            "POST /decision": "执行决策",
            "POST /decision/quick": "快速决策",
            "GET /decision/stats": "决策统计",
            "GET /decision/templates": "决策模板"
        }
    }

@app.post("/decision", response_model=DecisionResponse)
async def make_decision(request: DecisionRequest):
    """执行决策"""
    try:
        # 执行决策
        result = await decision_service.make_decision(
            problem=request.problem,
            options=[opt.dict() for opt in request.options],
            category=request.category,
            context=request.context
        )

        return DecisionResponse(
            success=result.get("success", False),
            chosen_option=result.get("chosen_option"),
            confidence=result.get("confidence", 0.0),
            human_feedback=result.get("human_feedback"),
            rationale=result.get("rationale"),
            engine=result.get("engine", "unknown"),
            timestamp=datetime.now().isoformat()
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"决策失败: {str(e)}") from e

@app.post("/decision/quick", response_model=DecisionResponse)
async def quick_decision(request: QuickDecisionRequest):
    """快速决策"""
    try:
        # 快速决策
        if request.options:
            await decision_service.make_decision(
                problem=request.prompt,
                options=[
                    {"title": opt, "description": opt, "confidence": 0.5}
                    for opt in request.options
                ]
            )
        else:
            response_text = await decision_service.quick_decision(request.prompt)

            return DecisionResponse(
                success=True,
                chosen_option="quick_response",
                confidence=0.7,
                human_feedback=None,
                rationale=response_text,
                engine="quick_template",
                timestamp=datetime.now().isoformat()
            )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"快速决策失败: {str(e)}") from e

@app.get("/decision/stats", response_model=DecisionStats)
async def get_decision_stats():
    """获取决策统计"""
    try:
        stats = decision_service.get_decision_stats()
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取统计失败: {str(e)}") from e

@app.get("/decision/templates")
async def list_templates():
    """列出决策模板"""
    try:
        templates = decision_service.list_templates()
        return {"templates": templates}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取模板失败: {str(e)}") from e

# 健康检查
@app.get("/health")
async def health_check():
    """健康检查"""
    return {
        "status": "healthy",
        "service": "decision_api",
        "timestamp": datetime.now().isoformat()
    }

# 批量决策接口
@app.post("/decision/batch")
async def batch_decision(requests: list[DecisionRequest]):
    """批量决策"""
    try:
        results = []

        for request in requests:
            result = await decision_service.make_decision(
                problem=request.problem,
                options=[opt.dict() for opt in request.options],
                category=request.category,
                context=request.context
            )
            results.append({
                "problem": request.problem,
                "result": result
            })

        return {"success": True, "results": results}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"批量决策失败: {str(e)}") from e

# 历史查询
@app.get("/decision/history")
async def get_decision_history(limit: int = 10):
    """获取决策历史"""
    try:
        history = decision_service.decision_history[-limit:]
        return {
            "history": [
                {
                    "id": d.id,
                    "problem": d.problem,
                    "category": d.category,
                    "timestamp": d.timestamp.isoformat(),
                    "human_involved": d.human_involved
                }
                for d in history
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取历史失败: {str(e)}") from e

# 启动服务器
if __name__ == "__main__":
    print("🎯 启动小诺决策API服务...")
    print("📍 http://localhost:8000/docs 查看API文档")
    print("🎯 http://localhost:8000/health 健康检查")

    uvicorn.run(
        "decision_api:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
