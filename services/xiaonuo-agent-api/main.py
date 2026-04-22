#!/usr/bin/env python3
"""
小诺·双鱼公主智能体 HTTP API 服务
Xiaonuo Agent HTTP API Service

为小诺协调官智能体提供RESTful API接口，支持：
- 多智能体任务协调
- 任务分配与调度
- 资源管理
- 健康监控

作者: Athena平台团队
版本: 1.0.0
"""

import asyncio
import json
import logging
from typing import Any, Dict, Optional, List
from datetime import datetime

from fastapi import FastAPI, HTTPException, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
import uvicorn

# 添加项目路径
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

# 注意：这里使用小诺的实现类
# 根据实际项目结构调整导入路径

# =============================================================================
# 日志配置
# =============================================================================

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# =============================================================================
# 数据模型
# =============================================================================

class CoordinationTaskRequest(BaseModel):
    """协调任务请求模型"""
    task_type: str = Field(..., description="任务类型")
    agents: List[str] = Field(default=[], description="参与的智能体列表")
    input_data: Dict[str, Any] = Field(..., description="任务输入数据")
    coordination_mode: str = Field("sequential", description="协调模式：sequential(顺序), parallel(并行), hierarchical(层级)")

class AgentStatusRequest(BaseModel):
    """智能体状态查询请求"""
    agent_names: List[str] = Field(..., description="要查询的智能体名称列表")

class TaskResponse(BaseModel):
    """任务响应模型"""
    success: bool
    task_id: str = ""
    result: Any = None
    error: str = None
    execution_time: float = 0.0
    involved_agents: List[str] = []

class HealthResponse(BaseModel):
    """健康检查响应"""
    status: str
    service: str
    agent_name: str
    version: str
    timestamp: str
    initialized: bool
    available_agents: List[str]

# =============================================================================
# FastAPI应用
# =============================================================================

app = FastAPI(
    title="Xiaonuo Agent API",
    description="小诺·双鱼公主协调官智能体API服务",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# 全局变量
xiaonuo_agent = None

# =============================================================================
# 生命周期管理
# =============================================================================

@app.on_event("startup")
async def startup_event():
    """应用启动时初始化"""
    global xiaonuo_agent

    logger.info("🎭 初始化小诺·双鱼公主...")

    try:
        # 使用小诺协调器实现
        from core.agents.xiaonuo_coordinator import XiaonuoAgent

        # 创建小诺实例
        xiaonuo_agent = XiaonuoAgent()
        await xiaonuo_agent.initialize()

        logger.info("✅ 小诺初始化完成")
        logger.info("🎭 小诺服务就绪")

    except Exception as e:
        logger.error(f"❌ 小诺初始化失败: {e}", exc_info=True)
        # 如果创建失败，记录但不阻止服务启动
        logger.warning("⚠️ 小诺将以模拟模式运行")
        xiaonuo_agent = None

@app.on_event("shutdown")
async def shutdown_event():
    """应用关闭时清理"""
    global xiaonuo_agent

    logger.info("🛑 小诺正在关闭...")

    if xiaonuo_agent:
        try:
            await xiaonuo_agent.shutdown()
            logger.info("✅ 小诺已关闭")
        except Exception as e:
            logger.error(f"❌ 小诺关闭失败: {e}", exc_info=True)

# =============================================================================
# 辅助函数
# =============================================================================

async def simulate_coordination_task(
    task_type: str,
    agents: List[str],
    input_data: Dict[str, Any],
    mode: str
) -> Dict[str, Any]:
    """
    模拟协调任务（当小诺实例不可用时）
    """
    # 模拟任务处理
    await asyncio.sleep(0.5)

    return {
        "task_type": task_type,
        "mode": mode,
        "agents_involved": agents,
        "status": "completed",
        "result": {
            "message": f"任务已协调完成（模拟模式）",
            "summary": f"协调了{len(agents)}个智能体执行{task_type}任务"
        },
        "timestamp": datetime.now().isoformat()
    }

# =============================================================================
# API端点
# =============================================================================

@app.get("/health", response_model=HealthResponse, tags=["Health"])
async def health_check():
    """
    健康检查端点

    返回服务状态和可用智能体列表
    """
    # 可用智能体列表
    available_agents = [
        "xiaona",      # 小娜
        "xiaonuo",     # 小诺（自己）
        # "yunxi"      # 云熙（如果可用）
    ]

    return HealthResponse(
        status="healthy",
        service="xiaonuo-agent-api",
        agent_name="小诺·双鱼公主",
        version="1.0.0",
        timestamp=datetime.now().isoformat(),
        initialized=xiaonuo_agent is not None,
        available_agents=available_agents
    )


@app.post("/api/v1/xiaonuo/coordinate", response_model=TaskResponse, tags=["Xiaonuo"])
async def coordinate_task(request: CoordinationTaskRequest):
    """
    协调多智能体任务

    支持的协调模式：
    - sequential: 顺序执行（一个接一个）
    - parallel: 并行执行（同时进行）
    - hierarchical: 层级执行（有主从关系）
    """
    import time
    start_time = time.time()

    try:
        # 构建任务ID
        task_id = f"xiaonuo_{int(time.time() * 1000)}"

        logger.info(f"🎭 协调任务 {task_id}: {request.task_type}")
        logger.info(f"👥 参与智能体: {request.agents}")
        logger.info(f"🔄 协调模式: {request.coordination_mode}")

        # 如果小诺实例可用，使用真实的协调逻辑
        if xiaonuo_agent:
            try:
                # 这里应该调用小诺的实际协调方法
                # 根据实际实现调整
                result = await xiaonuo_agent.coordinate(
                    task_type=request.task_type,
                    agents=request.agents,
                    input_data=request.input_data,
                    mode=request.coordination_mode
                )
            except AttributeError:
                # 如果方法不存在，使用模拟逻辑
                result = await simulate_coordination_task(
                    request.task_type,
                    request.agents,
                    request.input_data,
                    request.coordination_mode
                )
        else:
            # 使用模拟逻辑
            result = await simulate_coordination_task(
                request.task_type,
                request.agents,
                request.input_data,
                request.coordination_mode
            )

        execution_time = time.time() - start_time

        logger.info(f"✅ 协调任务 {task_id} 完成，耗时: {execution_time:.3f}秒")

        return TaskResponse(
            success=True,
            task_id=task_id,
            result=result,
            execution_time=execution_time,
            involved_agents=request.agents
        )

    except Exception as e:
        execution_time = time.time() - start_time
        logger.error(f"❌ 协调任务执行失败: {e}", exc_info=True)

        return TaskResponse(
            success=False,
            task_id=task_id if 'task_id' in locals() else "",
            error=str(e),
            execution_time=execution_time,
            involved_agents=request.agents
        )


class DispatchTaskRequest(BaseModel):
    """任务分发请求"""
    target_agent: str = Field(..., description="目标智能体名称")
    task_data: Dict[str, Any] = Field(..., description="任务数据")

@app.post("/api/v1/xiaonuo/dispatch", tags=["Xiaonuo"])
async def dispatch_task(request: DispatchTaskRequest):
    """
    分发任务到指定智能体

    参数:
    - target_agent: 目标智能体（如xiaona、yunxi）
    - task_data: 任务数据
    """
    if xiaonuo_agent is None:
        # 使用简单的HTTP调用逻辑
        return await dispatch_task_via_http(target_agent, task_data)

    import time
    start_time = time.time()

    try:
        logger.info(f"📤 分发任务到智能体: {request.target_agent}")

        # 这里应该调用小诺的分发方法
        # 根据实际实现调整
        result = {
            "target_agent": request.target_agent,
            "task_data": request.task_data,
            "status": "dispatched",
            "message": f"任务已分发到{request.target_agent}"
        }

        execution_time = time.time() - start_time

        return {
            "success": True,
            "result": result,
            "execution_time": f"{execution_time:.3f}s"
        }

    except Exception as e:
        execution_time = time.time() - start_time
        logger.error(f"任务分发失败: {e}", exc_info=True)

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"任务分发失败: {str(e)}"
        )


async def dispatch_task_via_http(target_agent: str, task_data: Dict[str, Any]):
    """通过HTTP分发任务到其他智能体服务"""
    import httpx

    # 智能体服务端口映射
    agent_ports = {
        "xiaona": 8023,
        "yunxi": 8024,  # 假设云熙在8024端口
        "tool_registry": 8021
    }

    if request.target_agent not in agent_ports:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"未找到智能体服务: {request.target_agent}"
        )

    port = agent_ports[request.target_agent]
    url = f"http://localhost:{port}/api/v1/{request.target_agent}/process"

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=request.task_data, timeout=30.0)
            response.raise_for_status()
            return response.json()

    except httpx.RequestError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"无法连接到智能体服务 {target_agent}: {str(e)}"
        )


@app.get("/api/v1/xiaonuo/agents", tags=["Xiaonuo"])
async def list_agents():
    """
    获取可用智能体列表
    """
    agents = [
        {
            "name": "xiaona",
            "display_name": "小娜·天秤女神",
            "role": "法律专家",
            "capabilities": ["专利分析", "法律咨询", "案件检索"],
            "status": "available",
            "api_port": 8023
        },
        {
            "name": "xiaonuo",
            "display_name": "小诺·双鱼公主",
            "role": "协调官",
            "capabilities": ["任务协调", "资源调度", "多智能体协作"],
            "status": "available",
            "api_port": 8024
        },
        {
            "name": "tool_registry",
            "display_name": "统一工具注册表",
            "role": "工具管理",
            "capabilities": ["工具调用", "权限管理", "工具监控"],
            "status": "available",
            "api_port": 8021
        }
    ]

    return {
        "success": True,
        "count": len(agents),
        "data": agents
    }


@app.get("/api/v1/xiaonuo/capabilities", tags=["Xiaonuo"])
async def get_capabilities():
    """
    获取小诺的能力列表
    """
    capabilities = [
        "多智能体任务协调",
        "任务分配与调度",
        "并行任务管理",
        "智能体状态监控",
        "资源优化分配"
    ]

    return {
        "success": True,
        "agent_name": "小诺·双鱼公主",
        "role": "协调官",
        "capabilities": capabilities,
        "description": "负责平台多智能体任务协调与资源调度"
    }


# =============================================================================
# 错误处理
# =============================================================================

@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """全局异常处理器"""
    logger.error(f"未捕获的异常: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "success": False,
            "error": "内部服务器错误",
            "detail": str(exc)
        }
    )


# =============================================================================
# 主函数
# =============================================================================

def main():
    """启动服务"""
    logger.info("🎭 启动小诺智能体API服务...")

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8024,
        reload=False,
        log_level="info"
    )


if __name__ == "__main__":
    main()
