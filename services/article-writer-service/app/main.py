#!/usr/bin/env python3
"""
Athena文章撰写服务主程序
Article Writer Service Main Entry

统一文章撰写API服务
"""

import asyncio
import sys
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime

# 添加项目路径
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))
sys.path.insert(0, str(current_dir.parent.parent.parent))

from config import settings
from core.writing_engine import ArticleWritingEngine, WritingRequest, write_article
from openclaw import OpenClawHandover, ArticleContent, handover_to_openclaw

# 日志
import logging
logging.basicConfig(
    level=settings.LOG_LEVEL,
    format=settings.LOG_FORMAT
)
logger = logging.getLogger(__name__)

# 全局变量
writing_engine = None


# API数据模型
class ArticleWriteRequest(BaseModel):
    """文章撰写请求"""
    topic: str
    article_type: str = "ip_education"
    style: str = "shandong_humor"
    platforms: Optional[List[str]] = None
    requirements: Optional[Dict[str, Any]] = None
    word_count: Optional[int] = None
    handover_to_openclaw: bool = False
    generate_images: bool = False


class ArticleWriteResponse(BaseModel):
    """文章撰写响应"""
    success: bool
    article_id: Optional[str] = None
    title: Optional[str] = None
    content: Optional[str] = None
    quality_score: Optional[float] = None
    warnings: Optional[List[str]] = None
    handover_result: Optional[Dict[str, Any]] = None
    message: str = ""


class HandoverRequest(BaseModel):
    """内容交接请求"""
    title: str
    content: str
    platforms: List[str]
    summary: str = ""
    tags: Optional[List[str]] = None
    images: Optional[List[str]] = None


class HandoverResponse(BaseModel):
    """交接响应"""
    success: bool
    article_paths: Dict[str, str] = {}
    message: str = ""
    errors: List[str] = []


# 创建FastAPI应用
app = FastAPI(
    title=settings.SERVICE_NAME,
    description="Athena统一文章撰写服务",
    version=settings.SERVICE_VERSION,
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup():
    """启动时初始化"""
    global writing_engine

    logger.info("🚀 启动Athena文章撰写服务...")
    logger.info(f"📍 端口: {settings.SERVICE_PORT}")

    try:
        writing_engine = ArticleWritingEngine()
        logger.info("✅ 文章撰写引擎初始化完成")
    except Exception as e:
        logger.error(f"❌ 初始化失败: {str(e)}")
        raise


@app.on_event("shutdown")
async def shutdown():
    """关闭时清理"""
    logger.info("🌙 关闭Athena文章撰写服务...")


@app.get("/")
async def root():
    """服务状态"""
    return {
        "service": settings.SERVICE_NAME,
        "version": settings.SERVICE_VERSION,
        "status": "running",
        "features": [
            "统一文章撰写",
            "多种文章类型",
            "多种写作风格",
            "OpenClaw内容交接",
            "写作素材库整合"
        ],
        "openclaw_integration": {
            "enabled": settings.OPENCLAW_HANDOVER_ENABLED,
            "path": str(settings.OPENCLAW_MEDIA_PATH)
        },
        "timestamp": datetime.now().isoformat()
    }


@app.get("/health")
async def health():
    """健康检查"""
    return {
        "status": "healthy",
        "service": settings.SERVICE_NAME,
        "timestamp": datetime.now().isoformat()
    }


@app.post("/api/v1/articles/write", response_model=ArticleWriteResponse)
async def write_article_endpoint(request: ArticleWriteRequest):
    """
    撰写文章API

    Args:
        request: 撰写请求

    Returns:
        撰写结果
    """
    try:
        logger.info(f"📝 收到撰写请求: {request.topic}")

        # 构建撰写请求
        writing_request = WritingRequest(
            topic=request.topic,
            article_type=request.article_type,
            style=request.style,
            platforms=request.platforms or ["微信公众号"],
            requirements=request.requirements or {},
            word_count=request.word_count
        )

        # 执行撰写
        result = await writing_engine.write_article(writing_request)

        if result.success:
            # 如果需要交接
            handover_result = None
            if request.handover_to_openclaw and result.article:
                handover_result = await writing_engine.handover_to_openclaw(
                    result.article,
                    request.platforms or ["微信公众号"]
                )

            return ArticleWriteResponse(
                success=True,
                article_id=result.article.article_id if result.article else None,
                title=result.article.title if result.article else None,
                content=result.markdown_content,
                quality_score=result.article.quality_score if result.article else None,
                warnings=result.warnings,
                handover_result=handover_result,
                message="文章撰写完成"
            )
        else:
            return ArticleWriteResponse(
                success=False,
                message=f"撰写失败: {', '.join(result.errors)}"
            )

    except Exception as e:
        logger.error(f"❌ 撰写异常: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/handover", response_model=HandoverResponse)
async def handover_endpoint(request: HandoverRequest):
    """
    内容交接API

    直接交接已有文章到OpenClaw

    Args:
        request: 交接请求

    Returns:
        交接结果
    """
    try:
        logger.info(f"📤 收到交接请求: {request.title}")

        result = await handover_to_openclaw(
            title=request.title,
            content=request.content,
            platforms=request.platforms,
            summary=request.summary,
            tags=request.tags,
            images=[Path(img) for img in request.images] if request.images else None
        )

        return HandoverResponse(
            success=result.success,
            article_paths={k: str(v) for k, v in result.article_paths.items()},
            message=result.message,
            errors=result.errors
        )

    except Exception as e:
        logger.error(f"❌ 交接异常: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/status")
async def get_status():
    """获取服务状态"""
    handover = OpenClawHandover()
    handover_status = handover.get_handover_status()

    return {
        "service": {
            "name": settings.SERVICE_NAME,
            "version": settings.SERVICE_VERSION,
            "status": "running"
        },
        "openclaw": handover_status,
        "supported_article_types": [
            "ip_education",
            "legal_analysis",
            "industry_insight",
            "patent_guide",
            "casual_blog"
        ],
        "supported_styles": [
            "shandong_humor",
            "professional",
            "cultural",
            "practical"
        ],
        "supported_platforms": [
            "微信公众号",
            "小红书",
            "知乎",
            "今日头条",
            "抖音",
            "快手",
            "微博"
        ]
    }


if __name__ == "__main__":
    import uvicorn

    logger.info("🚀 启动Athena文章撰写服务...")
    logger.info(f"📍 端口: {settings.SERVICE_PORT}")
    logger.info(f"📖 API文档: http://localhost:{settings.SERVICE_PORT}/docs")

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=settings.SERVICE_PORT,
        reload=settings.RELOAD
    )
