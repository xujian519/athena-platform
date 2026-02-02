#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
小娜专利服务API
Xiaona Patents Service API

小娜的专业专利数据获取和分析服务
提供RESTful API接口供系统调用

作者: 小娜·天秤女神
创建时间: 2025-12-16
版本: v1.0.0
"""

import asyncio
from core.async_main import async_main
import json
import logging
from core.logging_config import setup_logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException, BackgroundTasks, Query, Body
from fastapi.middleware.cors import CORSMiddleware

from core.security.auth import ALLOWED_ORIGINS
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
import uvicorn

# 导入小娜Google专利控制系统
from core.cognition.xiaona_google_patents_controller import (
    XiaonaGooglePatentsController,
    PatentRetrievalRequest,
    PatentRetrievalResult
)

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = setup_logging()

# 创建FastAPI应用
app = FastAPI(
    title="小娜专利服务API",
    description="小娜·天秤女神的专业专利数据获取和分析服务",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 全局变量
xiaona_controller: XiaonaGooglePatentsController | None = None

# Pydantic模型
class PatentRetrievalRequestModel(BaseModel):
    """专利获取请求模型"""
    patent_number: str = Field(..., description="专利号")
    retrieval_type: str = Field("full_text", description="获取类型: full_text, metadata, claims_only, summary")
    priority: str = Field("medium", description="优先级: high, medium, low")
    user_request: str = Field("", description="用户请求描述")
    output_format: List[str] = Field(["json", "structured"], description="输出格式")
    language_preference: str = Field("zh", description="语言偏好")

class BatchRetrievalRequestModel(BaseModel):
    """批量获取请求模型"""
    patents: List[PatentRetrievalRequestModel] = Field(..., description="专利列表")
    batch_name: str = Field("", description="批次名称")

class PatentAnalysisRequestModel(BaseModel):
    """专利分析请求模型"""
    patent_data: Dict[str, Any] = Field(..., description="专利数据")
    analysis_type: str = Field("legal", description="分析类型: legal, technical, commercial")
    focus_areas: List[str] = Field([], description="重点关注领域")

# 启动事件
@app.on_event("startup")
async def startup_event():
    """服务启动时初始化"""
    global xiaona_controller

    logger.info("⚖️ 小娜专利服务启动中...")

    try:
        # 初始化小娜控制器
        xiaona_controller = XiaonaGooglePatentsController()
        await xiaona_controller.initialize()

        logger.info("✅ 小娜专利服务启动成功")
        logger.info("⚖️ 小娜·天秤女神已就绪，提供专业专利服务")

    except Exception as e:
        logger.error(f"❌ 小娜专利服务启动失败: {e}")
        raise

@app.on_event("shutdown")
async def shutdown_event():
    """服务关闭时清理"""
    global xiaona_controller

    if xiaona_controller:
        logger.info("⚖️ 小娜专利服务关闭中...")
        # 清理资源
        xiaona_controller = None
        logger.info("✅ 小娜专利服务已关闭")

# API端点
@app.get("/")
async def root():
    """根路径"""
    return {
        "service": "小娜专利服务API",
        "controller": "小娜·天秤女神",
        "specialization": "专利法律专家",
        "status": "active",
        "version": "1.0.0",
        "endpoints": {
            "single_patent": "/patent/{patent_number}",
            "batch_retrieval": "/patents/batch",
            "patent_analysis": "/patent/analyze",
            "system_status": "/status",
            "health_check": "/health"
        }
    }

@app.get("/health")
async def health_check():
    """健康检查"""
    global xiaona_controller

    if xiaona_controller:
        status = await xiaona_controller.get_system_status()
        return {
            "status": "healthy",
            "controller": "小娜·天秤女神",
            "timestamp": datetime.now().isoformat(),
            "statistics": status.get("statistics", {})
        }
    else:
        raise HTTPException(status_code=503, detail="服务未初始化")

@app.get("/status")
async def get_system_status():
    """获取系统状态"""
    global xiaona_controller

    if not xiaona_controller:
        raise HTTPException(status_code=503, detail="服务未初始化")

    status = await xiaona_controller.get_system_status()
    return JSONResponse(status)

@app.post("/patent/retrieve")
async def retrieve_single_patent(request: PatentRetrievalRequestModel):
    """获取单个专利"""
    global xiaona_controller

    if not xiaona_controller:
        raise HTTPException(status_code=503, detail="服务未初始化")

    try:
        # 转换请求
        retrieval_request = PatentRetrievalRequest(
            patent_number=request.patent_number,
            retrieval_type=request.retrieval_type,
            priority=request.priority,
            user_request=request.user_request,
            output_format=request.output_format,
            language_preference=request.language_preference
        )

        # 执行获取
        result = await xiaona_controller.retrieve_patent(retrieval_request)

        return {
            "success": True,
            "data": result.__dict__,
            "processed_by": "小娜·天秤女神",
            "processing_time": datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"❌ 获取单个专利失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/patent/{patent_number}")
async def get_patent_by_number(
    patent_number: str,
    retrieval_type: str = Query("full_text", description="获取类型"),
    priority: str = Query("medium", description="优先级")
):
    """通过专利号获取专利"""
    global xiaona_controller

    if not xiaona_controller:
        raise HTTPException(status_code=503, detail="服务未初始化")

    try:
        retrieval_request = PatentRetrievalRequest(
            patent_number=patent_number,
            retrieval_type=retrieval_type,
            priority=priority,
            user_request=f"获取专利 {patent_number} 的信息"
        )

        result = await xiaona_controller.retrieve_patent(retrieval_request)

        return {
            "success": result.success,
            "patent_number": patent_number,
            "data": result.__dict__,
            "processed_by": "小娜·天秤女神"
        }

    except Exception as e:
        logger.error(f"❌ 获取专利失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/patents/batch")
async def batch_retrieve_patents(request: BatchRetrievalRequestModel, background_tasks: BackgroundTasks):
    """批量获取专利"""
    global xiaona_controller

    if not xiaona_controller:
        raise HTTPException(status_code=503, detail="服务未初始化")

    try:
        # 转换请求
        retrieval_requests = [
            PatentRetrievalRequest(
                patent_number=patent.patent_number,
                retrieval_type=patent.retrieval_type,
                priority=patent.priority,
                user_request=patent.user_request,
                output_format=patent.output_format,
                language_preference=patent.language_preference
            )
            for patent in request.patents
        ]

        # 执行批量获取
        results = await xiaona_controller.batch_retrieve_patents(retrieval_requests)

        return {
            "success": True,
            "batch_name": request.batch_name or f"batch_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "total_patents": len(request.patents),
            "successful_retrievals": sum(1 for r in results if r.success),
            "failed_retrievals": sum(1 for r in results if not r.success),
            "data": [result.__dict__ for result in results],
            "processed_by": "小娜·天秤女神",
            "processing_time": datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"❌ 批量获取专利失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/patent/analyze")
async def analyze_patent(request: PatentAnalysisRequestModel):
    """分析专利"""
    global xiaona_controller

    if not xiaona_controller:
        raise HTTPException(status_code=503, detail="服务未初始化")

    try:
        # 使用小娜的专业分析能力
        analysis_result = {
            "patent_analysis": "专业分析功能正在开发中",
            "analysis_type": request.analysis_type,
            "focus_areas": request.focus_areas,
            "processed_by": "小娜·天秤女神",
            "analysis_time": datetime.now().isoformat(),
            "status": "in_development"
        }

        return {
            "success": True,
            "data": analysis_result
        }

    except Exception as e:
        logger.error(f"❌ 专利分析失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/statistics")
async def get_patent_statistics():
    """获取专利统计信息"""
    global xiaona_controller

    if not xiaona_controller:
        raise HTTPException(status_code=503, detail="服务未初始化")

    try:
        status = await xiaona_controller.get_system_status()
        statistics = status.get("statistics", {})

        return {
            "statistics": statistics,
            "professional_summary": {
                "total_patents_processed": statistics.get("total_patents_processed", 0),
                "success_rate": (
                    statistics.get("successful_retrievals", 0) /
                    max(1, statistics.get("total_requests", 1)) * 100
                ),
                "legal_analyses_performed": statistics.get("legal_analyses_performed", 0),
                "average_processing_time": statistics.get("average_retrieval_time", 0)
            },
            "controller_info": {
                "name": status.get("controller", "小娜·天秤女神"),
                "specialization": "专利法律专家",
                "professional_level": "expert"
            }
        }

    except Exception as e:
        logger.error(f"❌ 获取统计信息失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# 错误处理
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """HTTP异常处理"""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": True,
            "message": exc.detail,
            "service": "小娜专利服务",
            "timestamp": datetime.now().isoformat()
        }
    )

@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """通用异常处理"""
    logger.error(f"❌ 未处理的异常: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "error": True,
            "message": "服务器内部错误",
            "service": "小娜专利服务",
            "timestamp": datetime.now().isoformat()
        }
    )

# 主函数
def main() -> None:
    """启动服务"""
    logger.info("⚖️ 启动小娜专利服务...")
    logger.info("🌐 服务地址: http://localhost:8006")
    logger.info("📖 API文档: http://localhost:8006/docs")

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8006,
        log_level="info",
        access_log=True
    )

if __name__ == "__main__":
    main()