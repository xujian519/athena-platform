#!/usr/bin/env python3
"""
技术图纸分析服务
Technical Drawing Analysis Service

提供REST API接口进行技术图纸智能分析
"""

import os

# 添加项目路径
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

import uvicorn
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from core.logging_config import setup_logging
from core.security.auth import ALLOWED_ORIGINS

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from services.ai_models.glm_full_suite.glm_unified_client import ZhipuAIUnifiedClient

from core.perception.technical_drawing_analyzer import AnalysisLevel, TechnicalDrawingAnalyzer

# 配置日志
# setup_logging()  # 日志配置已移至模块导入
logger = setup_logging()

# 创建FastAPI应用
app = FastAPI(
    title="技术图纸智能分析服务",
    description="基于GLM-4V的技术图纸理解API",
    version="1.0.0"
)

# 添加CORS支持
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 全局变量
glm_client: ZhipuAIUnifiedClient | None = None
analyzer: TechnicalDrawingAnalyzer | None = None


@app.on_event("startup")
async def startup_event():
    """启动时初始化"""
    global glm_client, analyzer

    logger.info("🚀 启动技术图纸分析服务...")

    # 初始化GLM客户端
    glm_client = ZhipuAIUnifiedClient()
    await glm_client.__aenter__()

    # 初始化分析器
    analyzer = TechnicalDrawingAnalyzer(
        glm_client=glm_client,
        max_image_size=2048,
        chunk_size=1024,
        enable_chunking=True
    )

    logger.info("✅ 服务启动完成!")


@app.on_event("shutdown")
async def shutdown_event():
    """关闭时清理"""
    global glm_client

    if glm_client:
        await glm_client.__aexit__(None, None, None)

    logger.info("👋 服务已关闭")


# ==================== Pydantic模型 ====================

class AnalysisRequest(BaseModel):
    """分析请求"""
    analysis_level: str = "intermediate"  # basic, intermediate, advanced
    specification_text: str | None = None
    related_claims: list[str] | None = None


class AnalysisResponse(BaseModel):
    """分析响应"""
    success: bool
    drawing_type: str
    title: str
    description: str
    confidence: float
    components: list[dict[str, Any]]
    technical_features: list[str]
    working_principle: str
    related_claims: list[str]
    processing_time: float
    model_used: str
    tokens_used: int
    error: str | None = None


class HealthResponse(BaseModel):
    """健康检查响应"""
    status: str
    service: str
    version: str
    timestamp: str


# ==================== API端点 ====================

@app.get("/", response_model=dict[str, Any])
async def root():
    """根路径"""
    return {
        "service": "技术图纸智能分析服务",
        "version": "1.0.0",
        "status": "running",
        "endpoints": {
            "health": "/health",
            "analyze": "/api/v1/analyze",
            "analyze_upload": "/api/v1/analyze/upload",
            "batch_analyze": "/api/v1/analyze/batch"
        }
    }


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """健康检查"""
    return HealthResponse(
        status="healthy",
        service="technical-drawing-analysis",
        version="1.0.0",
        timestamp=datetime.now().isoformat()
    )


@app.post("/api/v1/analyze", response_model=AnalysisResponse)
async def analyze_drawing(
    file: UploadFile = File(...),
    analysis_level: str = Form("intermediate"),
    specification_text: str | None = Form(None),
    related_claims: str | None = Form(None)
):
    """
    分析技术图纸

    参数:
    - file: 图像文件
    - analysis_level: 分析深度 (basic/intermediate/advanced)
    - specification_text: 说明书文本(可选)
    - related_claims: 相关权利要求,用分号分隔(可选)

    返回: 分析结果
    """
    try:
        # 验证文件类型
        if not file.content_type.startswith('image/'):
            raise HTTPException(status_code=400, detail="只支持图像文件")

        # 读取上传的文件
        contents = await file.read()

        # 保存临时文件
        temp_dir = Path("/tmp/drawing_analysis")
        temp_dir.mkdir(exist_ok=True)

        temp_file = temp_dir / f"{datetime.now().timestamp()}_{file.filename}"
        with open(temp_file, "wb") as f:
            f.write(contents)

        logger.info(f"📊 分析图纸: {file.filename} (级别: {analysis_level})")

        # 解析分析级别
        level_map = {
            "basic": AnalysisLevel.BASIC,
            "intermediate": AnalysisLevel.INTERMEDIATE,
            "advanced": AnalysisLevel.ADVANCED
        }
        level = level_map.get(analysis_level.lower(), AnalysisLevel.INTERMEDIATE)

        # 解析权利要求
        claims_list = None
        if related_claims:
            claims_list = [c.strip() for c in related_claims.split(';') if c.strip()]

        # 执行分析
        result = await analyzer.analyze(
            image_path=str(temp_file),
            analysis_level=level,
            specification_text=specification_text,
            related_claims=claims_list
        )

        # 清理临时文件
        temp_file.unlink()

        # 构建响应
        return AnalysisResponse(
            success=result.error is None,
            drawing_type=result.drawing_type.value,
            title=result.title,
            description=result.description,
            confidence=result.confidence,
            components=result.components,
            technical_features=result.technical_features,
            working_principle=result.working_principle,
            related_claims=result.related_claims,
            processing_time=result.processing_time,
            model_used=result.model_used,
            tokens_used=result.tokens_used,
            error=result.error
        )

    except Exception as e:
        logger.error(f"❌ 分析失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.post("/api/v1/analyze/batch")
async def batch_analyze_drawings(
    files: list[UploadFile] = File(...),
    analysis_level: str = Form("intermediate")
):
    """
    批量分析技术图纸

    参数:
    - files: 多个图像文件
    - analysis_level: 分析深度

    返回: 批量分析结果
    """
    try:
        if len(files) > 10:
            raise HTTPException(status_code=400, detail="最多支持10个文件")

        results = []
        level_map = {
            "basic": AnalysisLevel.BASIC,
            "intermediate": AnalysisLevel.INTERMEDIATE,
            "advanced": AnalysisLevel.ADVANCED
        }
        level = level_map.get(analysis_level.lower(), AnalysisLevel.INTERMEDIATE)

        temp_dir = Path("/tmp/drawing_analysis")
        temp_dir.mkdir(exist_ok=True)

        for file in files:
            try:
                contents = await file.read()
                temp_file = temp_dir / f"{datetime.now().timestamp()}_{file.filename}"

                with open(temp_file, "wb") as f:
                    f.write(contents)

                result = await analyzer.analyze(
                    image_path=str(temp_file),
                    analysis_level=level
                )

                results.append({
                    "filename": file.filename,
                    "success": result.error is None,
                    "drawing_type": result.drawing_type.value,
                    "title": result.title,
                    "description": result.description[:200],
                    "processing_time": result.processing_time,
                    "error": result.error
                })

                temp_file.unlink()

            except Exception as e:
                logger.error(f"处理 {file.filename} 失败: {str(e)}")
                results.append({
                    "filename": file.filename,
                    "success": False,
                    "error": str(e)
                })

        return {
            "total": len(files),
            "successful": sum(1 for r in results if r["success"]),
            "reports/reports/results": results
        }

    except Exception as e:
        logger.error(f"❌ 批量分析失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.get("/api/v1/statistics")
async def get_statistics():
    """获取服务统计信息"""
    stats = analyzer.get_statistics()
    return {
        "service": "technical-drawing-analysis",
        "statistics": stats,
        "timestamp": datetime.now().isoformat()
    }


# ==================== 主函数 ====================

def main() -> None:
    """启动服务"""
    uvicorn.run(
        "drawing_analysis_api:app",
        host="0.0.0.0",
        port=8013,
        reload=True,
        log_level="info"
    )


if __name__ == "__main__":
    main()
