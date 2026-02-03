#!/usr/bin/env python3
"""
学习与适应模块 API 接口
Learning & Adaptation Module API

提供RESTful API接口用于访问学习与适应模块功能:
1. 学习引擎接口
2. 元学习接口
3. 在线学习接口
4. 强化学习接口
5. 监控和统计接口

作者: Athena平台团队
版本: 1.0.0
创建时间: 2026-01-24
"""

import logging
from datetime import datetime
from enum import Enum
from typing import Any, Optional

from fastapi import APIRouter, BackgroundTasks, Depends, FastAPI, HTTPException, Query
from fastapi import status as http_status  # 重命名避免冲突
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

# 导入学习模块组件
from .learning_engine import LearningEngine
from .production_rl_integration import ProductionRLSystem, get_production_rl_system
from .rl_monitoring import RLMonitoringService, get_monitoring_service

logger = logging.getLogger(__name__)

# ==================== API Router ====================

router = APIRouter(
    prefix="/api/v1/learning",
    tags=["learning"],
    responses={404: {"description": "Not found"}, 500: {"description": "Internal server error"}},
)

# ==================== FastAPI App ====================
# 创建FastAPI应用实例(用于直接运行)

app = FastAPI(
    title="Learning & Adaptation Module API",
    description="学习与适应模块RESTful API接口",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# 包含路由
app.include_router(router)


# 根路径
@app.get("/")
async def app_root():
    """API根路径"""
    return {
        "message": "Learning & Adaptation Module API",
        "version": "1.0.0",
        "status": "running",
        "endpoints": {
            "health": "/api/v1/learning/health",
            "learn": "/api/v1/learning/learn",
            "statistics": "/api/v1/learning/statistics",
            "rl": "/api/v1/learning/rl",
            "monitoring": "/api/v1/learning/monitoring",
        },
    }


# ==================== Pydantic Models ====================


class LearningTaskType(str, Enum):
    """学习任务类型"""

    SUPERVISED = "supervised"
    UNSUPERVISED = "unsupervised"
    REINFORCEMENT = "reinforcement"
    META_LEARNING = "meta_learning"
    TRANSFER = "transfer"


class LearningRequest(BaseModel):
    """学习请求模型"""

    task_type: LearningTaskType = Field(..., description="学习任务类型")
    context: dict[str, Any] = Field(default_factory=dict, description="学习上下文")
    data: list[dict[str, Any]] = Field(default_factory=list, description="训练数据")
    config: Optional[dict[str, Any]] = Field(None, description="学习配置")
    metadata: Optional[dict[str, Any]] = Field(None, description="元数据")


class LearningResponse(BaseModel):
    """学习响应模型"""

    task_id: str = Field(..., description="任务ID")
    status: str = Field(..., description="状态")
    message: str = Field(..., description="消息")
    result: Optional[dict[str, Any]] = Field(None, description="学习结果")
    timestamp: datetime = Field(default_factory=datetime.now, description="时间戳")


class LearningStatistics(BaseModel):
    """学习统计模型"""

    total_tasks: int = Field(..., description="总任务数")
    successful_tasks: int = Field(..., description="成功任务数")
    failed_tasks: int = Field(..., description="失败任务数")
    success_rate: float = Field(..., description="成功率")
    average_learning_time: float = Field(..., description="平均学习时间(秒)")
    last_learning_time: Optional[datetime] = Field(None, description="最后学习时间")


class RLInteractionRequest(BaseModel):
    """强化学习交互请求"""

    user_input: str = Field(..., description="用户输入")
    agent_response: str = Field(..., description="智能体响应")
    capability_used: str = Field(..., description="使用的能力")
    context: Optional[dict[str, Any]] = Field(None, description="上下文")
    explicit_feedback: Optional[float] = Field(None, ge=0.0, le=1.0, description="显式反馈(0-1)")
    response_time: float = Field(default=0.0, ge=0.0, description="响应时间(秒)")
    error_occurred: bool = Field(default=False, description="是否发生错误")
    user_corrected: bool = Field(default=False, description="用户是否纠正")


class MonitoringMetrics(BaseModel):
    """监控指标模型"""

    timestamp: datetime = Field(..., description="时间戳")
    total_interactions: int = Field(..., description="总交互数")
    recent_rewards: dict[str, float] = Field(..., description="最近奖励统计")
    quality_metrics: dict[str, float] = Field(..., description="质量指标")
    rl_agent: dict[str, Any] = Field(..., description="RL智能体状态")
    alerts: list[dict[str, Any]] = Field(default_factory=list, description="告警列表")


# ==================== Dependencies ====================


def get_learning_system() -> LearningEngine:
    """获取学习引擎实例"""
    return LearningEngine(agent_id="api_service")


def get_rl_system() -> ProductionRLSystem:
    """获取强化学习系统实例"""
    return get_production_rl_system()


def get_monitoring() -> RLMonitoringService:
    """获取监控服务实例"""
    return get_monitoring_service()


# ==================== API Endpoints ====================


@router.get("/", summary="学习模块根路径")
async def root():
    """学习模块API根路径"""
    return {
        "module": "Learning & Adaptation Module",
        "version": "1.0.0",
        "status": "operational",
        "endpoints": {
            "learning": "/learn",
            "statistics": "/statistics",
            "rl": "/rl",
            "monitoring": "/monitoring",
        },
    }


@router.get("/health", summary="健康检查")
async def health_check():
    """健康检查端点"""
    return {"status": "healthy", "timestamp": datetime.now().isoformat(), "module": "learning"}


@router.post("/learn", response_model=LearningResponse, summary="执行学习任务")
async def execute_learning(
    request: LearningRequest,
    background_tasks: BackgroundTasks,
    learning_system: LearningEngine = Depends(get_learning_system),
):
    """
    执行学习任务

    - **task_type**: 学习任务类型(监督/无监督/强化/元学习/迁移)
    - **context**: 学习上下文信息
    - **data**: 训练数据
    - **config**: 可选的学习配置参数
    - **metadata**: 可选的元数据
    """
    try:
        task_id = f"task_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"

        # 验证输入
        if not request.data and request.task_type != LearningTaskType.REINFORCEMENT:
            raise HTTPException(
                status_code=http_status.HTTP_400_BAD_REQUEST,
                detail=f"任务类型 {request.task_type} 需要提供训练数据",
            )

        # 异步执行学习任务
        result = await learning_system.learn(
            data={"context": request.context, "config": request.config or {}, "data": request.data}
        )  # type: ignore

        return LearningResponse(
            task_id=task_id, status="completed", message="学习任务执行成功", result=result
        )

    except Exception as e:
        logger.error(f"学习任务执行失败: {e}")
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"学习任务执行失败: {e!s}",
        )


@router.get("/statistics", response_model=LearningStatistics, summary="获取学习统计")
async def get_statistics(learning_system: LearningEngine = Depends(get_learning_system)):
    """
    获取学习统计信息

    返回学习引擎的统计指标,包括任务数、成功率等
    """
    try:
        # 这里应该从实际的学习引擎获取统计信息
        # 示例实现
        return LearningStatistics(
            total_tasks=100,
            successful_tasks=95,
            failed_tasks=5,
            success_rate=0.95,
            average_learning_time=2.5,
            last_learning_time=datetime.now(),
        )
    except Exception as e:
        logger.error(f"获取统计信息失败: {e}")
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取统计信息失败: {e!s}",
        )


# ==================== 强化学习端点 ====================


@router.post("/rl/interaction", summary="记录RL交互")
async def record_rl_interaction(
    request: RLInteractionRequest, rl_system: ProductionRLSystem = Depends(get_rl_system)
):
    """
    记录一次用户交互并更新强化学习模型

    - **user_input**: 用户输入文本
    - **agent_response**: 智能体响应
    - **capability_used**: 使用的能力名称
    - **context**: 可选的上下文信息
    - **explicit_feedback**: 可选的显式反馈(0-1)
    - **response_time**: 响应时间(秒)
    - **error_occurred**: 是否发生错误
    - **user_corrected**: 用户是否纠正了响应
    """
    try:
        result = await rl_system.record_interaction(
            user_input=request.user_input,
            agent_response=request.agent_response,
            capability_used=request.capability_used,
            context=request.context,
            explicit_feedback=request.explicit_feedback,
            response_time=request.response_time,
            error_occurred=request.error_occurred,
            user_corrected=request.user_corrected,
        )

        return {
            "status": "success",
            "interaction_id": result.get("interaction_id"),
            "reward": result.get("reward"),
            "message": "交互记录成功",
        }

    except Exception as e:
        logger.error(f"记录RL交互失败: {e}")
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"记录交互失败: {e!s}"
        )


@router.get("/rl/summary", summary="获取RL学习摘要")
async def get_rl_summary(rl_system: ProductionRLSystem = Depends(get_rl_system)):
    """
    获取强化学习系统的学习摘要

    包括交互统计、奖励趋势、能力使用分布等
    """
    try:
        summary = rl_system.get_learning_summary()
        return {"status": "success", "data": summary}
    except Exception as e:
        logger.error(f"获取RL摘要失败: {e}")
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"获取摘要失败: {e!s}"
        )


# ==================== 监控端点 ====================


@router.get("/monitoring/metrics", response_model=MonitoringMetrics, summary="获取监控指标")
async def get_monitoring_metrics(monitoring: RLMonitoringService = Depends(get_monitoring)):
    """
    获取实时监控指标

    包括交互统计、奖励分布、质量指标、RL智能体状态等
    """
    try:
        status = await monitoring.get_current_status()
        return MonitoringMetrics(**status["metrics"])
    except Exception as e:
        logger.error(f"获取监控指标失败: {e}")
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取监控指标失败: {e!s}",
        )


@router.get("/monitoring/report", summary="获取监控报告")
async def get_monitoring_report(monitoring: RLMonitoringService = Depends(get_monitoring)):
    """
    获取监控报告

    返回格式化的监控报告文本
    """
    try:
        from .rl_monitoring import RLEvaluationReport

        report_generator = RLEvaluationReport(monitoring.rl_system)
        report = await report_generator.generate_daily_report()
        return {"status": "success", "report": report, "timestamp": datetime.now().isoformat()}
    except Exception as e:
        logger.error(f"获取监控报告失败: {e}")
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"获取报告失败: {e!s}"
        )


@router.post("/monitoring/start", summary="启动监控服务")
async def start_monitoring(
    interval_seconds: int = Query(3600, ge=60, description="监控间隔(秒)"),
    monitoring: RLMonitoringService = Depends(get_monitoring),
):
    """
    启动监控服务

    - **interval_seconds**: 监控间隔,默认3600秒(1小时)
    """
    try:
        if monitoring._is_running:
            return {"status": "already_running", "message": "监控服务已在运行"}

        await monitoring.start_monitoring(interval_seconds)
        return {"status": "success", "message": f"监控服务已启动,间隔: {interval_seconds}秒"}
    except Exception as e:
        logger.error(f"启动监控失败: {e}")
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"启动监控失败: {e!s}"
        )


@router.post("/monitoring/stop", summary="停止监控服务")
async def stop_monitoring(monitoring: RLMonitoringService = Depends(get_monitoring)):
    """停止监控服务"""
    try:
        if not monitoring._is_running:
            return {"status": "not_running", "message": "监控服务未运行"}

        await monitoring.stop_monitoring()
        return {"status": "success", "message": "监控服务已停止"}
    except Exception as e:
        logger.error(f"停止监控失败: {e}")
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"停止监控失败: {e!s}"
        )


# ==================== 错误处理 ====================
# 注意: 异常处理器需要在FastAPI应用级别添加,而不是路由级别
# 以下函数可以添加到主应用中使用


async def http_exception_handler(request, exc):
    """HTTP异常处理器"""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "message": exc.detail,
                "status_code": exc.status_code,
                "timestamp": datetime.now().isoformat(),
            }
        },
    )


async def general_exception_handler(request, exc):
    """通用异常处理器"""
    logger.error(f"未处理的异常: {exc}", exc_info=True)
    return JSONResponse(
        status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": {
                "message": "内部服务器错误",
                "detail": str(exc),
                "status_code": 500,
                "timestamp": datetime.now().isoformat(),
            }
        },
    )


# ==================== 导出 ====================


class LearningAPI:
    """学习API接口类 - 提供编程式访问"""

    def __init__(self):
        self.app = app
        self.router = router

    def get_app(self) -> FastAPI:
        """获取FastAPI应用实例"""
        return self.app

    def get_router(self) -> APIRouter:
        """获取API路由器"""
        return self.router


# 全局 API 实例
_learning_api_instance: LearningAPI | None = None


def get_learning_api() -> LearningAPI:
    """获取学习API单例"""
    global _learning_api_instance
    if _learning_api_instance is None:
        _learning_api_instance = LearningAPI()
    return _learning_api_instance


__all__ = ["app", "LearningAPI", "get_learning_api", "router"]
