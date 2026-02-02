#!/usr/bin/env python3
"""
小宸智能体主程序
Xiaochen Self-Media Agent
宝宸自媒体传播专家
版本: v0.0.1 "源启"
口号: 宸音传千里，智声达天下
"""

import os
from core.async_main import async_main
import sys
import asyncio
import json
from datetime import datetime
from pathlib import Path
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from core.security.auth import ALLOWED_ORIGINS
from fastapi.responses import JSONResponse
from pydantic import BaseModel

# 添加项目路径
current_dir = Path(__file__).parent
project_root = current_dir.parent.parent
sys.path.insert(0, str(current_dir))
sys.path.insert(0, str(project_root))

# 导入配置
from config import settings
from core.xiaochen_engine import XiaochenEngine
from core.content_creator import ContentCreator
from core.platform_manager import PlatformManager
from core.enhanced_content_styles import ContentStyle, ContentPurpose
from core.smart_publish_scheduler import XiaochenSmartScheduler, PublishTask, PublishStrategy
from core.analytics_tracker import XiaochenAnalyticsTracker
from utils.logger import logger

# 全局变量
xiaochen_engine = None
content_creator = None
platform_manager = None
scheduler = None
analytics_tracker = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    global xiaochen_engine, content_creator, platform_manager

    # 启动时初始化
    logger.info("🌱 小宸智能体启动中... 版本: v0.0.1 '源启'")

    try:
        # 初始化核心引擎
        logger.info("🔧 初始化小宸核心引擎...")
        xiaochen_engine = XiaochenEngine()
        await xiaochen_engine.initialize()

        # 初始化内容创作模块
        logger.info("✍️ 初始化内容创作模块...")
        content_creator = ContentCreator()
        await content_creator.initialize()

        # 初始化平台管理器
        logger.info("📱 初始化平台管理器...")
        platform_manager = PlatformManager()
        await platform_manager.initialize()

        # 初始化智能调度器（传承小溪设计）
        logger.info("📅 初始化智能调度系统...")
        scheduler = XiaochenSmartScheduler(
            auto_publish=False,
            dry_run=True,
            enable_ai_optimization=True
        )
        await scheduler.initialize()

        # 初始化数据分析系统（传承小溪设计）
        logger.info("📊 初始化数据分析系统...")
        analytics_tracker = XiaochenAnalyticsTracker()
        await analytics_tracker.initialize()

        logger.info("✅ 小宸智能体启动完成！宸音传千里，智声达天下！")

    except Exception as e:
        logger.error(f"❌ 小宸启动失败: {str(e)}")
        raise

    yield

    # 关闭时清理
    logger.info("🌙 小宸正在休息...为明天的传播储能！")

    if xiaochen_engine:
        await xiaochen_engine.cleanup()
    if content_creator:
        await content_creator.cleanup()
    if platform_manager:
        await platform_manager.cleanup()


# 创建FastAPI应用
app = FastAPI(
    title="小宸智能体",
    description="宝宸自媒体传播专家 - 宸音传千里，智声达天下",
    version="0.0.1",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# CORS配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# 根路径
@app.get("/")
async def root():
    """小宸服务状态检查"""
    return {
        "service": "小宸智能体",
        "gender": "男",
        "version": "0.0.1",
        "name": "源启",
        "slogan": "宸音传千里，智声达天下",
        "role": "宝宸自媒体传播专家",
        "status": "running",
        "characteristics": [
            "幽默风趣",
            "专业可靠",
            "诚实守信",
            "博学多才"
        ],
        "platforms": [
            "小红书", "知乎", "抖音", "B站", "公众号", "微博"
        ],
        "expertise": [
            "AI技术科普",
            "知识产权知识",
            "创业经验分享",
            "行业观察评论",
            "历史文化传播"
        ],
        "message": "宝宸之音，智能传播，为您成功助力！",
        "timestamp": datetime.now().isoformat()
    }


# 健康检查
@app.get("/api/v1/health")
async def health_check():
    """健康检查接口"""
    global xiaochen_engine, content_creator, platform_manager

    status = {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "0.0.1",
        "checks": {}
    }

    all_healthy = True

    # 检查核心引擎
    if xiaochen_engine:
        try:
            engine_healthy = await xiaochen_engine.health_check()
            status["checks"]["engine"] = engine_healthy
            if not engine_healthy:
                all_healthy = False
        except Exception as e:
            logger.error(f"核心引擎健康检查失败: {str(e)}")
            status["checks"]["engine"] = False
            all_healthy = False

    # 检查内容创作模块
    if content_creator:
        try:
            creator_healthy = await content_creator.health_check()
            status["checks"]["content_creator"] = creator_healthy
            if not creator_healthy:
                all_healthy = False
        except Exception as e:
            logger.error(f"内容创作模块健康检查失败: {str(e)}")
            status["checks"]["content_creator"] = False
            all_healthy = False

    # 检查平台管理器
    if platform_manager:
        try:
            manager_healthy = await platform_manager.health_check()
            status["checks"]["platform_manager"] = manager_healthy
            if not manager_healthy:
                all_healthy = False
        except Exception as e:
            logger.error(f"平台管理器健康检查失败: {str(e)}")
            status["checks"]["platform_manager"] = False
            all_healthy = False

    status["status"] = "healthy" if all_healthy else "unhealthy"
    status["message"] = "小宸状态良好，准备传播宝宸之音！" if all_healthy else "小宸有些不适，需要检查..."

    return status


# 内容创作接口
@app.post("/api/v1/content/create")
async def create_content(request: dict):
    """创建内容"""
    try:
        content_type = request.get("type", "article")  # article, video, image
        topic = request.get("topic", "")
        platform = request.get("platform", "all")
        style = request.get("style", "professional")  # professional, casual, humorous

        if not topic:
            raise HTTPException(status_code=400, detail="主题不能为空")

        # 使用内容创作模块
        if content_creator:
            content = await content_creator.create_content(
                content_type=content_type,
                topic=topic,
                platform=platform,
                style=style
            )

            return {
                "success": True,
                "content": content,
                "message": "内容创作完成！"
            }
        else:
            raise HTTPException(status_code=503, detail="内容创作模块未就绪")

    except Exception as e:
        logger.error(f"内容创作失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# 内容发布接口
@app.post("/api/v1/content/publish")
async def publish_content(request: dict):
    """发布内容到指定平台"""
    try:
        content = request.get("content", {})
        platforms = request.get("platforms", [])
        schedule_time = request.get("schedule_time")  # 可选，定时发布

        if not content or not platforms:
            raise HTTPException(status_code=400, detail="内容和平台不能为空")

        # 使用平台管理器发布
        if platform_manager:
            results = await platform_manager.publish_to_platforms(
                content=content,
                platforms=platforms,
                schedule_time=schedule_time
            )

            return {
                "success": True,
                "results": results,
                "message": "内容发布完成！"
            }
        else:
            raise HTTPException(status_code=503, detail="平台管理器未就绪")

    except Exception as e:
        logger.error(f"内容发布失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# 数据分析接口
@app.get("/api/v1/analytics/overview")
async def get_analytics_overview():
    """获取数据分析概览"""
    try:
        # 这里应该从数据库获取真实数据
        # 暂时返回模拟数据
        return {
            "total_posts": 156,
            "total_engagement": 45678,
            "platform_stats": {
                "小红书": {"posts": 45, "engagement": 12345},
                "知乎": {"posts": 38, "engagement": 9876},
                "抖音": {"posts": 28, "engagement": 15678},
                "B站": {"posts": 22, "engagement": 5432},
                "公众号": {"posts": 15, "engagement": 2109},
                "微博": {"posts": 8, "engagement": 238}
            },
            "trending_topics": [
                "AI与专利",
                "知识产权保护",
                "创业经验分享",
                "技术商业化"
            ],
            "message": "数据分析完成，宝宸影响力持续提升！"
        }
    except Exception as e:
        logger.error(f"数据分析失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# 智能对话接口
@app.post("/api/v1/chat")
async def chat_with_xiaochen(request: dict):
    """与小宸智能对话"""
    try:
        message = request.get("message", "")
        context = request.get("context", "general")  # general, ip_tech, content_creation

        if not message:
            raise HTTPException(status_code=400, detail="消息不能为空")

        # 使用小宸核心引擎进行对话
        if xiaochen_engine:
            response = await xiaochen_engine.chat(
                message=message,
                context=context
            )

            return {
                "success": True,
                "response": response,
                "message": "小宸已回复！"
            }
        else:
            raise HTTPException(status_code=503, detail="小宸核心引擎未就绪")

    except Exception as e:
        logger.error(f"智能对话失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# 全局异常处理
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """全局异常处理"""
    logger.error(f"全局错误: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={
            'success': False,
            'message': '呀...小宸遇到一点小问题，让我想想办法... 💭',
            'error': str(exc) if os.getenv('DEBUG') else None
        }
    )


# 导入路由（稍后实现）
# from app.api import content, platform, analytics
# app.include_router(content.router, prefix="/api/v1")
# app.include_router(platform.router, prefix="/api/v1")
# app.include_router(analytics.router, prefix="/api/v1")


if __name__ == "__main__":
    # 设置Python路径
    os.environ['PYTHONPATH'] = str(project_root)

    # 启动服务
    logger.info("🚀 启动小宸智能体服务...")
    logger.info("📍 端口: 8030")
    logger.info("🎯 宸音传千里，智声达天下！")

    uvicorn.run(
        'app.main:app',
        host='0.0.0.0',
        port=8030,
        reload=True,
        access_log=True
    )