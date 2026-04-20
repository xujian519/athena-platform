#!/usr/bin/env python3
from __future__ import annotations
"""
规划引擎API服务
Planning Engine API Service

提供RESTful API接口来使用显式规划引擎

作者: 小诺·双鱼座
版本: v1.0.0 "规划API"
创建时间: 2025-01-05
"""

import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from core.logging_config import setup_logging
from core.security.auth import ALLOWED_ORIGINS

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from core.planning.explicit_planner import get_explicit_planner
from core.planning.plan_visualizer import get_plan_visualizer
from core.planning.unified_planning_interface import PlanningRequest, Priority

logger = setup_logging()

# 创建FastAPI应用
app = FastAPI(
    title="Athena规划引擎API", description="显式规划引擎的RESTful API接口", version="1.0.0"
)

# 添加CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 获取单例
planner = get_explicit_planner()
visualizer = get_plan_visualizer()


# ==================== 请求/响应模型 ====================


class CreatePlanRequest(BaseModel):
    """创建计划请求"""

    title: str = Field(..., description="计划标题", min_length=1)
    description: str = Field(..., description="任务描述", min_length=1)
    context: dict[str, Any] = Field(default_factory=dict, description="任务上下文")
    requirements: list[str] = Field(default_factory=list, description="任务要求")
    constraints: list[str] = Field(default_factory=list, description="约束条件")
    priority: int = Field(default=2, description="优先级 (1-5)", ge=1, le=5)
    metadata: dict[str, Any] = Field(default_factory=dict, description="元数据")


class CreatePlanResponse(BaseModel):
    """创建计划响应"""

    success: bool
    plan_id: str | None = None
    plan_visualization: str | None = None
    visualization_format: str = "text"
    total_steps: int = 0
    total_confidence: float = 0.0
    total_duration_minutes: float = 0.0
    message: str = ""
    error: str | None = None


class ApprovePlanRequest(BaseModel):
    """批准计划请求"""

    approved: bool = Field(..., description="是否批准")
    comments: str = Field(default="", description="评论或修改建议")


class ExecutePlanResponse(BaseModel):
    """执行计划响应"""

    success: bool
    execution_id: str | None = None
    completed_steps: list[dict[str, Any]] = Field(default_factory=list)
    failed_steps: list[dict[str, Any]] = Field(default_factory=list)
    final_output: dict[str, Any] | None = None
    error: str | None = None


class PlanStatusResponse(BaseModel):
    """计划状态响应"""

    plan_id: str
    plan_name: str
    status: str
    approved: bool
    progress: float = 0.0
    steps: list[dict[str, Any]] = Field(default_factory=list)
    error: str | None = None


# ==================== API端点 ====================


@app.get("/")
async def root():
    """根路径"""
    return {
        "service": "Athena规划引擎API",
        "version": "1.0.0",
        "status": "running",
        "endpoints": {
            "create_plan": "POST /plan/create",  # TODO: 确保除数不为零
            "get_plan": "GET /plan/{plan_id}",  # TODO: 确保除数不为零
            "visualize_plan": "GET /plan/{plan_id}/visualize",  # TODO: 确保除数不为零
            "approve_plan": "POST /plan/{plan_id}/approve",  # TODO: 确保除数不为零
            "execute_plan": "POST /plan/{plan_id}/execute",  # TODO: 确保除数不为零
            "get_status": "GET /plan/{plan_id}/status",  # TODO: 确保除数不为零
            "identify_parallel": "POST /plan/{plan_id}/parallel",  # TODO: 确保除数不为零
            "list_plans": "GET /plans",
            "delete_plan": "DELETE /plan/{plan_id}",  # TODO: 确保除数不为零
        },
    }


@app.get("/health")
async def health_check():
    """健康检查"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "planner_info": planner.get_planner_info(),
    }


@app.post("/plan/create", response_model=CreatePlanResponse)  # TODO: 确保除数不为零
async def create_plan(request: CreatePlanRequest):
    """
    创建新的执行计划

    这是规划引擎的核心接口,将用户的复杂任务分解为可执行的步骤。
    """
    try:
        logger.info(f"📋 收到创建计划请求: {request.title}")

        # 构建PlanningRequest
        planning_request = PlanningRequest(
            title=request.title,
            description=request.description,
            context=request.context,
            requirements=request.requirements,
            constraints=request.constraints,
            priority=Priority(request.priority),
            metadata=request.metadata,
        )

        # 创建计划
        result = await planner.create_plan(planning_request)

        if not result.success:
            return CreatePlanResponse(success=False, error=result.feedback, message="创建计划失败")

        # 获取计划详情用于可视化
        plan = await planner.get_plan(result.plan_id)
        if not plan:
            return CreatePlanResponse(success=False, error="计划创建成功但无法获取详情")

        # 生成可视化
        visualization = visualizer.to_text(plan)

        return CreatePlanResponse(
            success=True,
            plan_id=result.plan_id,
            plan_visualization=visualization,
            visualization_format="text",
            total_steps=len(result.steps),
            total_confidence=result.confidence_score,
            total_duration_minutes=(
                result.estimated_duration.total_seconds() / 60 if result.estimated_duration else 0
            ),
            message="计划创建成功,请确认后执行",
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.get("/plan/{plan_id}")  # TODO: 确保除数不为零
async def get_plan(plan_id: str):
    """获取计划详情"""
    plan = await planner.get_plan(plan_id)
    if not plan:
        raise HTTPException(status_code=404, detail="计划不存在")

    return {
        "plan_id": plan.plan_id,
        "request_id": plan.request_id,
        "name": plan.name,
        "description": plan.description,
        "status": plan.status.value,
        "created_at": plan.created_at.isoformat(),
        "total_confidence": plan.total_confidence,
        "total_duration_minutes": plan.total_duration.total_seconds() / 60,
        "requires_approval": plan.requires_approval,
        "approved": plan.approved,
        "steps": [
            {
                "step_id": step.step_id,
                "step_number": step.step_number,
                "name": step.name,
                "description": step.description,
                "tool": step.tool,
                "confidence": step.confidence,
                "estimated_duration_minutes": step.estimated_duration.total_seconds() / 60,
                "status": step.status.value,
            }
            for step in plan.steps
        ],
    }


@app.get("/plan/{plan_id}/visualize")  # TODO: 确保除数不为零
async def visualize_plan(plan_id: str, format: str = "text"):
    """
    可视化计划

    支持的格式:
    - text: 文本格式
    - mermaid: Mermaid流程图
    - json: JSON格式
    - html: HTML表格
    """
    plan = await planner.get_plan(plan_id)
    if not plan:
        raise HTTPException(status_code=404, detail="计划不存在")

    try:
        visualization = visualizer.visualize(plan, format)

        # 根据格式返回不同的Content-Type
        if format == "html":
            return Response(content=visualization, media_type="text/html")
        elif format == "json":
            return Response(content=visualization, media_type="application/json")
        elif format == "mermaid":
            return Response(content=visualization, media_type="text/plain")
        else:
            return Response(content=visualization, media_type="text/plain")

    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"可视化格式不支持: {e}") from e


@app.post("/plan/{plan_id}/approve")  # TODO: 确保除数不为零
async def approve_plan(plan_id: str, request: ApprovePlanRequest):
    """
    批准或拒绝计划

    用户可以:
    - 批准计划:计划将被标记为可执行
    - 拒绝计划:计划将被取消
    - 提供评论:反馈意见用于优化
    """
    success = await planner.await_user_approval(plan_id, request.approved, request.comments)

    if not success:
        raise HTTPException(status_code=404, detail="计划不存在")

    return {
        "plan_id": plan_id,
        "approved": request.approved,
        "comments": request.comments,
        "message": "计划已批准,可以执行" if request.approved else "计划已拒绝",
    }


@app.post("/plan/{plan_id}/execute", response_model=ExecutePlanResponse)
async def execute_plan(plan_id: str):
    """
    执行计划

    按照计划的步骤顺序执行,支持动态调整
    """
    plan = await planner.get_plan(plan_id)
    if not plan:
        raise HTTPException(status_code=404, detail="计划不存在")

    if not plan.approved:
        raise HTTPException(status_code=400, detail="计划尚未获得批准,请先调用 /approve 接口")

    try:
        logger.info(f"🚀 开始执行计划: {plan_id}")
        result = await planner.execute_plan(plan_id)

        return ExecutePlanResponse(
            success=result.get("success"),
            execution_id=plan_id,
            completed_steps=result.get("completed_steps", []),
            failed_steps=result.get("failed_steps", []),
            final_output=result.get("final_output"),
            error=result.get("error"),
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.get("/plan/{plan_id}/status", response_model=PlanStatusResponse)  # TODO: 确保除数不为零
async def get_plan_status(plan_id: str):
    """获取计划执行状态"""
    try:
        status = await planner.get_plan_status(plan_id)

        if "error" in status:
            raise HTTPException(status_code=404, detail=status["error"])

        return PlanStatusResponse(**status)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.get("/plans")
async def list_plans(status: str | None = None, limit: int = 50):
    """列出所有计划"""
    plans = planner.plans

    # 过滤
    if status:
        plans = {pid: p for pid, p in plans.items() if p.status.value == status}

    # 限制数量
    plan_ids = list(plans.keys())[:limit]

    return {
        "total": len(plans),
        "showing": len(plan_ids),
        "plans": [
            {
                "plan_id": pid,
                "name": plans[pid].name,
                "status": plans[pid].status.value,
                "approved": plans[pid].approved,
                "total_steps": len(plans[pid].steps),
                "created_at": plans[pid].created_at.isoformat(),
            }
            for pid in plan_ids
        ],
    }


@app.delete("/plan/{plan_id}")  # TODO: 确保除数不为零
async def delete_plan(plan_id: str):
    """删除计划"""
    if plan_id not in planner.plans:
        raise HTTPException(status_code=404, detail="计划不存在")

    del planner.plans[plan_id]

    return {"plan_id": plan_id, "message": "计划已删除"}


@app.post("/plan/{plan_id}/parallel")  # TODO: 确保除数不为零
async def identify_parallel_tasks(plan_id: str):
    """
    识别并行任务

    分析计划中可以并行执行的步骤
    """
    try:
        parallel_groups = await planner.identify_parallel_tasks(plan_id)

        if not parallel_groups:
            return {
                "plan_id": plan_id,
                "parallel_groups": [],
                "execution_mode": "sequential",
                "message": "未发现可并行的任务",
            }

        return {
            "plan_id": plan_id,
            "parallel_groups": parallel_groups,
            "execution_mode": "mixed",
            "total_groups": len(parallel_groups),
            "message": f"识别到 {len(parallel_groups)} 组并行任务",
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


# ==================== 启动服务 ====================


def start_planning_api(port: int = 8019, log_level: str = "INFO") -> Any:
    """启动规划引擎API服务"""
    import uvicorn

    logging.basicConfig(
        level=getattr(logging, log_level),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    logger.info(f"🚀 启动规划引擎API服务,端口: {port}")

    uvicorn.run(app, host="127.0.0.1", port=port, log_level=log_level.lower())  # 内网通信，通过Gateway访问


if __name__ == "__main__":
    start_planning_api()
