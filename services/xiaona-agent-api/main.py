#!/usr/bin/env python3
"""
小娜·天秤女神智能体 HTTP API 服务
Xiaona Agent HTTP API Service

为小娜法律专家智能体提供RESTful API接口，支持：
- 专利分析任务处理
- 法律咨询
- 案件检索
- 健康监控

作者: Athena平台团队
版本: 1.0.0
"""

import asyncio
import json
import logging
from typing import Any, Dict, Optional
from datetime import datetime

from fastapi import FastAPI, HTTPException, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
import uvicorn

# 添加项目路径
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.agents.xiaona_professional import XiaonaProfessionalAgent

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

class TaskRequest(BaseModel):
    """任务请求模型"""
    task_type: str = Field(..., description="任务类型：patent_analysis, legal_consult, case_search等")
    input_data: Dict[str, Any] = Field(..., description="任务输入数据")
    options: Dict[str, Any] = Field(default_factory=dict, description="可选参数")

class TaskResponse(BaseModel):
    """任务响应模型"""
    success: bool
    task_id: str = ""
    result: Any = None
    error: str = None
    execution_time: float = 0.0

class HealthResponse(BaseModel):
    """健康检查响应"""
    status: str
    service: str
    agent_name: str
    version: str
    timestamp: str
    initialized: bool
    capabilities: list

# =============================================================================
# FastAPI应用
# =============================================================================

app = FastAPI(
    title="Xiaona Agent API",
    description="小娜·天秤女神法律专家智能体API服务",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# 全局变量
xiaona_agent: Optional[XiaonaProfessionalAgent] = None

# =============================================================================
# 生命周期管理
# =============================================================================

@app.on_event("startup")
async def startup_event():
    """应用启动时初始化"""
    global xiaona_agent

    logger.info("🌟 初始化小娜·天秤女神...")

    try:
        # 创建小娜实例
        xiaona_agent = XiaonaProfessionalAgent()
        await xiaona_agent.initialize()

        logger.info("✅ 小娜初始化完成")
        logger.info("📱 小娜服务就绪")

    except Exception as e:
        logger.error(f"❌ 小娜初始化失败: {e}", exc_info=True)
        raise

@app.on_event("shutdown")
async def shutdown_event():
    """应用关闭时清理"""
    global xiaona_agent

    logger.info("🛑 小娜正在关闭...")

    if xiaona_agent:
        try:
            await xiaona_agent.shutdown()
            logger.info("✅ 小娜已关闭")
        except Exception as e:
            logger.error(f"❌ 小娜关闭失败: {e}", exc_info=True)

# =============================================================================
# API端点
# =============================================================================

@app.get("/health", response_model=HealthResponse, tags=["Health"])
async def health_check():
    """
    健康检查端点

    返回服务状态和智能体能力列表
    """
    if xiaona_agent is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="服务未就绪"
        )

    # 获取智能体能力
    capabilities = []
    if hasattr(xiaona_agent, 'capabilities'):
        capabilities = xiaona_agent.capabilities

    return HealthResponse(
        status="healthy",
        service="xiaona-agent-api",
        agent_name="小娜·天秤女神",
        version="1.0.0",
        timestamp=datetime.now().isoformat(),
        initialized=True,
        capabilities=capabilities
    )


@app.post("/api/v1/xiaona/process", response_model=TaskResponse, tags=["Xiaona"])
async def process_task(request: TaskRequest):
    """
    处理小娜任务

    支持的任务类型：
    - patent_analysis: 专利分析
    - legal_consult: 法律咨询
    - case_search: 案件检索
    - document_review: 文档审查
    """
    if xiaona_agent is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="服务未就绪"
        )

    import time
    start_time = time.time()

    try:
        # 构建任务ID
        task_id = f"xiaona_{int(time.time() * 1000)}"

        logger.info(f"📝 处理任务 {task_id}: {request.task_type}")
        logger.debug(f"输入数据: {request.input_data}")

        # 根据任务类型调用不同的处理方法
        if request.task_type == "patent_analysis":
            # 专利分析任务
            patent_id = request.input_data.get("patent_id")
            if not patent_id:
                raise ValueError("专利分析任务需要提供patent_id参数")

            # 调用小娜的分析方法
            result = await xiaona_agent.analyze_patent(patent_id)

        elif request.task_type == "legal_consult":
            # 法律咨询任务
            question = request.input_data.get("question")
            if not question:
                raise ValueError("法律咨询任务需要提供question参数")

            result = await xiaona_agent.legal_consult(question)

        elif request.task_type == "case_search":
            # 案件检索任务
            keywords = request.input_data.get("keywords")
            if not keywords:
                raise ValueError("案件检索任务需要提供keywords参数")

            result = await xiaona_agent.search_cases(keywords)

        elif request.task_type == "general":
            # 通用任务处理
            input_text = request.input_data.get("input", "")
            result_json = await xiaona_agent.process(input_text)

            # 尝试解析JSON结果
            try:
                result = json.loads(result_json)
            except:
                result = {"output": result_json}

        else:
            # 默认使用process方法
            input_text = request.input_data.get("input", str(request.input_data))
            result_json = await xiaona_agent.process(input_text)

            try:
                result = json.loads(result_json)
            except:
                result = {"output": result_json}

        execution_time = time.time() - start_time

        logger.info(f"✅ 任务 {task_id} 完成，耗时: {execution_time:.3f}秒")

        return TaskResponse(
            success=True,
            task_id=task_id,
            result=result,
            execution_time=execution_time
        )

    except Exception as e:
        execution_time = time.time() - start_time
        logger.error(f"❌ 任务执行失败: {e}", exc_info=True)

        return TaskResponse(
            success=False,
            task_id=task_id if 'task_id' in locals() else "",
            error=str(e),
            execution_time=execution_time
        )


class PatentAnalysisRequest(BaseModel):
    """专利分析请求"""
    patent_id: str = Field(..., description="专利号，如CN123456789A")
    analysis_type: str = Field("creativity", description="分析类型：creativity(创造性), infringement(侵权), validity(有效性)")

@app.post("/api/v1/xiaona/analyze-patent", tags=["Xiaona"])
async def analyze_patent(request: PatentAnalysisRequest):
    """
    专利分析专用接口

    参数:
    - patent_id: 专利号
    - analysis_type: 分析类型
    """
    if xiaona_agent is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="服务未就绪"
        )

    import time
    start_time = time.time()

    try:
        logger.info(f"🔍 分析专利: {request.patent_id}, 类型: {request.analysis_type}")

        # 调用分析方法
        result = await xiaona_agent.analyze_patent(request.patent_id, request.analysis_type)

        execution_time = time.time() - start_time

        return {
            "success": True,
            "patent_id": request.patent_id,
            "analysis_type": request.analysis_type,
            "result": result,
            "execution_time": f"{execution_time:.3f}s"
        }

    except Exception as e:
        execution_time = time.time() - start_time
        logger.error(f"专利分析失败: {e}", exc_info=True)

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"专利分析失败: {str(e)}"
        )


@app.get("/api/v1/xiaona/capabilities", tags=["Xiaona"])
async def get_capabilities():
    """
    获取小娜的能力列表
    """
    if xiaona_agent is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="服务未就绪"
        )

    try:
        capabilities = []

        if hasattr(xiaona_agent, 'capabilities'):
            capabilities = xiaona_agent.capabilities

        return {
            "success": True,
            "agent_name": "小娜·天秤女神",
            "capabilities": capabilities,
            "description": "法律专家智能体，擅长专利分析、法律咨询、案件检索"
        }

    except Exception as e:
        logger.error(f"获取能力列表失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取能力列表失败: {str(e)}"
        )


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
    logger.info("🌟 启动小娜智能体API服务...")

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8023,
        reload=False,
        log_level="info"
    )


if __name__ == "__main__":
    main()
