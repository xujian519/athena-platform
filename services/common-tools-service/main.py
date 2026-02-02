#!/usr/bin/env python3
"""
通用工具服务
Common Tools Service
提供系统通用工具的统一API接口
"""

import logging
from core.async_main import async_main
from core.logging_config import setup_logging
import os
import sys
from datetime import datetime
from typing import Dict, Any, Optional, List
from pathlib import Path

# 添加当前目录到Python路径
sys.path.append(str(Path(__file__).parent))

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware

from core.security.auth import ALLOWED_ORIGINS
from pydantic import BaseModel, Field, BaseSettings

# 导入工具模块
from browser_automation_tool import BrowserAutomationTool
from crawler_tool import CrawlerTool
from langextract_tool import LangExtractTool
from langextract_glm_tool import LangExtractGLMTool

# 配置日志
# setup_logging()  # 日志配置已移至模块导入
logger = setup_logging()

class Settings(BaseSettings):
    """配置管理"""
    app_name: str = "Common Tools Service"
    version: str = "1.0.0"
    debug: bool = False
    port: int = 8007

    # 工具配置
    browser_headless: bool = True
    browser_timeout: int = 30
    crawler_timeout: int = 60
    enable_async: bool = True

    class Config:
        env_file = ".env"

settings = Settings()

# 创建FastAPI应用
app = FastAPI(
    title=settings.app_name,
    description="Athena平台通用工具服务",
    version=settings.version,
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 请求/响应模型
class BrowserActionRequest(BaseModel):
    """浏览器操作请求"""
    action: str = Field(..., description="操作类型")
    url: Optional[str] = Field(None, description="目标URL")
    selector: Optional[str] = Field(None, description="CSS选择器")
    text: Optional[str] = Field(None, description="输入文本")
    options: Dict[str, Any] = Field(default_factory=dict, description="额外选项")

class CrawlerRequest(BaseModel):
    """爬虫请求"""
    url: str = Field(..., description="目标URL")
    options: Dict[str, Any] = Field(default_factory=dict, description="爬取选项")

class TextExtractRequest(BaseModel):
    """文本提取请求"""
    text: str = Field(..., description="待处理文本")
    extract_type: str = Field("keywords", description="提取类型")
    options: Dict[str, Any] = Field(default_factory=dict)

# 工具实例管理
class ToolManager:
    """工具管理器"""

    def __init__(self):
        self.browser_tool = None
        self.crawler_tool = None
        self.langextract_tool = None
        self.langextract_glm_tool = None

    async def initialize(self):
        """初始化所有工具"""
        try:
            self.browser_tool = BrowserAutomationTool()
            self.crawler_tool = CrawlerTool()
            self.langextract_tool = LangExtractTool()
            self.langextract_glm_tool = LangExtractGLMTool()
            logger.info("所有工具初始化完成")
        except Exception as e:
            logger.error(f"工具初始化失败: {e}")
            raise

    async def cleanup(self):
        """清理资源"""
        if self.browser_tool:
            try:
                await self.browser_tool.close()
            except Exception as e:
            logger.error(f"Error: {e}", exc_info=True)
        logger.info("工具资源清理完成")

tool_manager = ToolManager()

# 启动和关闭事件
@app.on_event("startup")
async def startup_event():
    """启动时初始化"""
    logger.info(f"启动 {settings.app_name} v{settings.version}")
    await tool_manager.initialize()

@app.on_event("shutdown")
async def shutdown_event():
    """关闭时清理"""
    logger.info("正在关闭服务...")
    await tool_manager.cleanup()

# API端点
@app.get("/")
async def root():
    """根路径"""
    return {
        "service": settings.app_name,
        "version": settings.version,
        "status": "running",
        "tools": {
            "browser_automation": True,
            "crawler": True,
            "langextract": True,
            "langextract_glm": True
        },
        "message": "通用工具服务运行正常",
        "timestamp": datetime.now().isoformat()
    }

@app.get("/health")
async def health():
    """健康检查"""
    tools_status = {
        "browser_automation": tool_manager.browser_tool is not None,
        "crawler": tool_manager.crawler_tool is not None,
        "langextract": tool_manager.langextract_tool is not None,
        "langextract_glm": tool_manager.langextract_glm_tool is not None
    }

    all_healthy = all(tools_status.values())

    return {
        "status": "healthy" if all_healthy else "degraded",
        "tools": tools_status,
        "timestamp": datetime.now().isoformat()
    }

# 浏览器自动化接口
@app.post("/api/v1/browser/execute")
async def execute_browser_action(request: BrowserActionRequest):
    """执行浏览器操作"""
    if not tool_manager.browser_tool:
        raise HTTPException(status_code=503, detail="浏览器工具未初始化")

    try:
        result = await tool_manager.browser_tool.execute_action(
            action=request.action,
            url=request.url,
            selector=request.selector,
            text=request.text,
            options=request.options
        )
        return {
            "success": True,
            "result": result,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"浏览器操作失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/browser/screenshot")
async def take_screenshot(url: str, selector: str | None = None):
    """截图"""
    if not tool_manager.browser_tool:
        raise HTTPException(status_code=503, detail="浏览器工具未初始化")

    try:
        result = await tool_manager.browser_tool.take_screenshot(
            url=url,
            selector=selector
        )
        return {
            "success": True,
            "screenshot": result,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"截图失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# 爬虫接口
@app.post("/api/v1/crawler/crawl")
async def crawl_url(request: CrawlerRequest):
    """爬取网页"""
    if not tool_manager.crawler_tool:
        raise HTTPException(status_code=503, detail="爬虫工具未初始化")

    try:
        result = await tool_manager.crawler_tool.crawl(
            url=request.url,
            options=request.options
        )
        return {
            "success": True,
            "data": result,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"爬取失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/crawler/batch")
async def batch_crawl(urls: List[str], options: Dict[str, Any] = None):
    """批量爬取"""
    if not tool_manager.crawler_tool:
        raise HTTPException(status_code=503, detail="爬虫工具未初始化")

    options = options or {}
    results = []

    for url in urls:
        try:
            result = await tool_manager.crawler_tool.crawl(url=url, options=options)
            results.append({
                "url": url,
                "success": True,
                "data": result
            })
        except Exception as e:
            logger.error(f"批量爬取失败 {url}: {e}")
            results.append({
                "url": url,
                "success": False,
                "error": str(e)
            })

    return {
        "success": True,
        "results": results,
        "total": len(urls),
        "successful": sum(1 for r in results if r["success"]),
        "timestamp": datetime.now().isoformat()
    }

# 文本提取接口
@app.post("/api/v1/text/extract")
async def extract_text_features(request: TextExtractRequest):
    """提取文本特征"""
    if not tool_manager.langextract_tool:
        raise HTTPException(status_code=503, detail="文本提取工具未初始化")

    try:
        result = await tool_manager.langextract_tool.extract(
            text=request.text,
            extract_type=request.extract_type,
            options=request.options
        )
        return {
            "success": True,
            "features": result,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"文本提取失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/text/extract-glm")
async def extract_with_glm(request: TextExtractRequest):
    """使用GLM模型提取文本特征"""
    if not tool_manager.langextract_glm_tool:
        raise HTTPException(status_code=503, detail="GLM文本提取工具未初始化")

    try:
        result = await tool_manager.langextract_glm_tool.extract(
            text=request.text,
            extract_type=request.extract_type,
            options=request.options
        )
        return {
            "success": True,
            "features": result,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"GLM文本提取失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# 工具状态接口
@app.get("/api/v1/tools/status")
async def get_tools_status():
    """获取所有工具状态"""
    return {
        "browser_automation": {
            "initialized": tool_manager.browser_tool is not None,
            "active": tool_manager.browser_tool.is_active() if tool_manager.browser_tool else False
        },
        "crawler": {
            "initialized": tool_manager.crawler_tool is not None,
            "active": True  # 爬虫工具总是活跃的
        },
        "langextract": {
            "initialized": tool_manager.langextract_tool is not None,
            "active": True
        },
        "langextract_glm": {
            "initialized": tool_manager.langextract_glm_tool is not None,
            "active": True
        }
    }

# 统计接口
@app.get("/api/v1/stats")
async def get_statistics():
    """获取服务统计信息"""
    return {
        "service": {
            "name": settings.app_name,
            "version": settings.version,
            "uptime": "0h 0m 0s"  # TODO: 计算实际运行时间
        },
        "tools": {
            "total": 4,
            "active": sum([
                tool_manager.browser_tool is not None,
                tool_manager.crawler_tool is not None,
                tool_manager.langextract_tool is not None,
                tool_manager.langextract_glm_tool is not None
            ])
        },
        "performance": {
            "requests_total": 0,  # TODO: 添加请求计数
            "requests_success": 0,
            "requests_failed": 0,
            "avg_response_time": 0
        }
    }

if __name__ == "__main__":
    import uvicorn
    logger.info(f"启动 {settings.app_name} v{settings.version}")
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=settings.port,
        reload=settings.debug
    )