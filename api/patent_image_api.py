#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
专利图像分析API服务
Patent Image Analysis API Service

本地开发环境启动脚本
"""

import asyncio
import logging
import os
import tempfile
import traceback
from contextlib import asynccontextmanager
from datetime import datetime
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from PIL import Image
import uvicorn

# 添加项目路径
import sys
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from production.core.perception.processors.patent_image_analyzer import (
    PatentImageAnalyzer,
    ImageAnalysisResult,
    ImageType
)

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 全局分析器实例
analyzer: Optional[PatentImageAnalyzer] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    global analyzer

    # 启动时加载模型
    logger.info("正在启动专利图像分析服务...")
    logger.info("正在加载模型...")

    try:
        analyzer = PatentImageAnalyzer(device="cpu")
        analyzer.load_models()
        logger.info("✓ 模型加载完成")
    except Exception as e:
        logger.error(f"✗ 模型加载失败: {e}")
        logger.error(traceback.format_exc())
        # 即使模型加载失败，也继续启动服务（部分功能可用）

    yield

    # 关闭时清理资源
    logger.info("正在关闭服务...")


# 创建FastAPI应用
app = FastAPI(
    title="专利图像分析API",
    description="多模态专利附图智能分析服务",
    version="1.0.0",
    lifespan=lifespan
)

# 添加CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health_check():
    """健康检查端点"""
    status = {
        "service": "patent_image_analysis",
        "status": "healthy" if analyzer else "degraded",
        "timestamp": datetime.now().isoformat(),
        "models": {}
    }

    if analyzer:
        if analyzer.clip_model is not None:
            status["models"]["clip"] = "loaded"
        if analyzer.blip_model is not None:
            status["models"]["blip"] = "loaded"

    return JSONResponse(content=status)


@app.get("/")
async def root():
    """根路径"""
    return {
        "service": "专利图像分析API",
        "version": "1.0.0",
        "endpoints": {
            "health": "/health",
            "analyze": "/api/v1/patent/image/analyze",
            "docs": "/docs"
        },
        "documentation": "请访问 /docs 查看API文档"
    }


@app.post("/api/v1/patent/image/analyze")
async def analyze_patent_image(
    file: UploadFile = File(..., description="专利附图文件"),
    reference_text: str = Form("", description="参考文本（可选）")
):
    """
    分析专利附图

    Args:
        file: 图像文件（支持PNG、JPG、JPEG等格式）
        reference_text: 参考文本，用于图文一致性检查

    Returns:
        分析结果，包含：
        - image_id: 图像唯一标识
        - image_type: 图像类型（流程图、结构图等）
        - caption: 自动生成的图像描述
        - ocr_text: 提取的文字内容
        - consistency_score: 图文一致性分数
        - processing_time: 处理时间（秒）
    """
    if not analyzer:
        raise HTTPException(
            status_code=503,
            detail="服务未完全初始化，模型正在加载中"
        )

    # 验证文件
    if not file.content_type.startswith("image/"):
        raise HTTPException(
            status_code=400,
            detail=f"不支持的文件类型: {file.content_type}，请上传图像文件"
        )

    # 保存临时文件
    temp_file = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp:
            content = await file.read()
            tmp.write(content)
            tmp.flush()
            temp_file = tmp.name

        # 执行分析
        logger.info(f"正在分析图像: {file.filename}")
        result = await analyzer.analyze(temp_file, reference_text)

        # 转换为字典响应
        response_data = {
            "status": "completed",
            "result": result.to_dict(),
            "message": "分析完成"
        }

        logger.info(f"分析完成: {result.image_type}, 耗时: {result.processing_time:.2f}秒")
        return JSONResponse(content=response_data)

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"分析失败: {e}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"分析失败: {str(e)}")

    finally:
        # 清理临时文件
        if temp_file and os.path.exists(temp_file):
            try:
                os.unlink(temp_file)
            except:
                pass


@app.get("/api/v1/patent/search")
async def search_patents(
    query: str = "",
    top_k: int = 10
):
    """
    专利检索端点（预留接口）

    Args:
        query: 检索关键词
        top_k: 返回结果数量

    Returns:
        检索结果列表
    """
    # TODO: 实现多模态检索功能
    return {
        "status": "implemented",
        "message": "多模态检索功能开发中",
        "query": query,
        "top_k": top_k,
        "results": []
    }


if __name__ == "__main__":
    # 启动服务
    port = int(os.getenv("PORT", 8888))
    host = os.getenv("HOST", "0.0.0.0")

    logger.info(f"启动专利图像分析服务...")
    logger.info(f"服务地址: http://{host}:{port}")
    logger.info(f"API文档: http://{host}:{port}/docs")

    uvicorn.run(
        "api.patent_image_api:app",
        host=host,
        port=port,
        reload=True,  # 开发模式，支持热重载
        log_level="info"
    )
