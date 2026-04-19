#!/usr/bin/env python3
"""
Athena爬虫服务
Athena Crawler Service
统一的多引擎爬虫服务，支持智能路由和成本控制
"""

import asyncio
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Any

import httpx
import uvicorn

# 导入爬虫核心组件
from config.hybrid_config import HybridCrawlerConfig
from core.hybrid_crawler_manager import HybridCrawlerManager
from fastapi import BackgroundTasks, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, BaseSettings, Field
from storage.data_storage_manager import DataStorageManager
from utils.data_processor import DataProcessor

from core.logging_config import setup_logging
from core.security.auth import ALLOWED_ORIGINS

# 配置日志
# setup_logging()  # 日志配置已移至模块导入
logger = setup_logging()

# 配置管理
class Settings(BaseSettings):
    """服务配置管理"""
    app_name: str = "Athena Crawler Service"
    version: str = "2.0.0"
    debug: bool = False
    port: int = 8001

    # 爬虫配置
    max_concurrent_crawls: int = 5
    default_timeout: int = 30
    enable_cache: bool = True
    cache_ttl: int = 3600  # 1小时

    # 成本控制
    monthly_cost_limit: float = 100.0
    daily_cost_limit: float = 10.0
    enable_cost_monitoring: bool = True

    # 存储配置
    storage_type: str = "file"  # file, redis, postgresql
    storage_path: str = "./data/crawler"

    # 代理配置
    enable_proxy: bool = False
    proxy_list: list[str] = []

    class Config:
        env_file = ".env"

# 全局变量
settings = Settings()
crawler_manager: HybridCrawlerManager | None = None
storage_manager: DataStorageManager | None = None
data_processor: DataProcessor | None = None

# 请求/响应模型
class CrawlRequest(BaseModel):
    """爬取请求模型"""
    url: str = Field(..., description="要爬取的URL")
    engine: str | None = Field(None, description="指定爬虫引擎：auto, internal, crawl4ai, firecrawl")
    options: dict[str, Any] = Field(default_factory=dict, description="爬取选项")
    priority: int = Field(1, description="优先级 1-5")
    callback_url: str | None = Field(None, description="完成后的回调URL")

class BatchCrawlRequest(BaseModel):
    """批量爬取请求"""
    urls: list[str] = Field(..., description="URL列表")
    engine: str | None = Field(None, description="指定爬虫引擎")
    options: dict[str, Any] = Field(default_factory=dict)
    max_concurrent: int = Field(5, description="最大并发数")

class CrawlResponse(BaseModel):
    """爬取响应模型"""
    task_id: str
    url: str
    status: str
    result: dict[str, Any] | None = None
    error: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    timestamp: str

# 应用生命周期管理
@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用启动和关闭时的生命周期管理"""
    global crawler_manager, storage_manager, data_processor

    # 启动时初始化
    logger.info(f"启动 {settings.app_name} v{settings.version}")

    try:
        # 初始化配置
        config = HybridCrawlerConfig()
        logger.info("配置加载完成")

        # 初始化存储管理器
        storage_manager = DataStorageManager(
            storage_type=settings.storage_type,
            base_path=settings.storage_path
        )
        await storage_manager.initialize()
        logger.info(f"存储管理器初始化完成: {settings.storage_type}")

        # 初始化数据处理器
        data_processor = DataProcessor()
        logger.info("数据处理器初始化完成")

        # 初始化爬虫管理器
        crawler_manager = HybridCrawlerManager(
            config=config,
            storage_manager=storage_manager,
            data_processor=data_processor
        )
        await crawler_manager.initialize()
        logger.info("混合爬虫管理器初始化完成")

        # 启动后台任务
        asyncio.create_task(monitor_cost_usage())
        logger.info("成本监控任务已启动")

        logger.info("爬虫服务启动完成")

    except Exception as e:
        logger.error(f"服务初始化失败: {e}")
        raise

    yield

    # 关闭时清理
    logger.info("正在关闭爬虫服务...")
    if crawler_manager:
        await crawler_manager.shutdown()
    if storage_manager:
        await storage_manager.close()
    logger.info("爬虫服务已关闭")

# 创建FastAPI应用
app = FastAPI(
    title=settings.app_name,
    description="Athena平台智能爬虫服务，支持多引擎智能路由和成本控制",
    version=settings.version,
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

# 后台任务：监控成本使用
async def monitor_cost_usage():
    """监控成本使用情况"""
    while True:
        try:
            if crawler_manager and settings.enable_cost_monitoring:
                stats = await crawler_manager.get_cost_stats()

                # 检查日限制
                if stats.get('daily_cost', 0) > settings.daily_cost_limit:
                    logger.warning(f"日成本限制警告: ${stats['daily_cost']:.2f}/${settings.daily_cost_limit}")

                # 检查月限制
                if stats.get('monthly_cost', 0) > settings.monthly_cost_limit:
                    logger.error(f"月成本限制警告: ${stats['monthly_cost']:.2f}/${settings.monthly_cost_limit}")

        except Exception as e:
            logger.error(f"成本监控错误: {e}")

        await asyncio.sleep(300)  # 每5分钟检查一次

# API端点
@app.get("/")
async def root():
    """根路径"""
    return {
        "service": settings.app_name,
        "version": settings.version,
        "status": "running",
        "engines": ["internal", "crawl4ai", "firecrawl"],
        "message": "Athena智能爬虫服务运行正常",
        "timestamp": datetime.now().isoformat()
    }

@app.get("/health")
async def health():
    """健康检查"""
    health_status = {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "components": {}
    }

    try:
        # 检查爬虫管理器
        if crawler_manager:
            manager_status = await crawler_manager.health_check()
            health_status["components"]["crawler_manager"] = manager_status
        else:
            health_status["status"] = "degraded"
            health_status["components"]["crawler_manager"] = {"status": "not_initialized"}

        # 检查存储管理器
        if storage_manager:
            storage_health = await storage_manager.health_check()
            health_status["components"]["storage_manager"] = storage_health
        else:
            health_status["status"] = "degraded"
            health_status["components"]["storage_manager"] = {"status": "not_initialized"}

    except Exception as e:
        logger.error(f"健康检查失败: {e}")
        health_status["status"] = "unhealthy"
        health_status["error"] = str(e)

    return health_status

@app.post("/api/v2/crawl", response_model=CrawlResponse)
async def crawl_url(request: CrawlRequest, background_tasks: BackgroundTasks):
    """智能爬取URL"""
    if not crawler_manager:
        raise HTTPException(status_code=503, detail="爬虫服务未初始化")

    # 验证URL
    if not request.url.startswith(('http://', 'https://')):
        raise HTTPException(status_code=400, detail="无效的URL格式")

    # 创建爬取任务
    task_id = await crawler_manager.create_crawl_task(
        url=request.url,
        engine=request.engine,
        options=request.options,
        priority=request.priority
    )

    # 如果需要回调，添加到后台任务
    if request.callback_url:
        background_tasks.add_task(
            execute_callback,
            task_id,
            request.callback_url
        )

    logger.info(f"创建爬取任务: {task_id} for {request.url}")

    # 执行爬取
    try:
        result = await crawler_manager.execute_crawl(task_id)

        # 保存结果
        if storage_manager:
            await storage_manager.save_crawl_result(task_id, result)

        return CrawlResponse(
            task_id=task_id,
            url=request.url,
            status="completed",
            result=result.get('data'),
            metadata=result.get('metadata', {}),
            timestamp=datetime.now().isoformat()
        )

    except Exception as e:
        logger.error(f"爬取失败 {task_id}: {e}")
        return CrawlResponse(
            task_id=task_id,
            url=request.url,
            status="failed",
            error=str(e),
            timestamp=datetime.now().isoformat()
        )

@app.get("/api/v2/task/{task_id}")
async def get_task_status(task_id: str):
    """获取任务状态"""
    if not crawler_manager:
        raise HTTPException(status_code=503, detail="爬虫服务未初始化")

    try:
        status = await crawler_manager.get_task_status(task_id)
        return status
    except Exception:
        raise HTTPException(status_code=404, detail=f"任务不存在: {task_id}") from None

@app.post("/api/v2/batch/crawl")
async def batch_crawl(request: BatchCrawlRequest):
    """批量爬取"""
    if not crawler_manager:
        raise HTTPException(status_code=503, detail="爬虫服务未初始化")

    if len(request.urls) > 100:
        raise HTTPException(status_code=400, detail="批量任务最多支持100个URL")

    # 创建批量任务
    batch_id = await crawler_manager.create_batch_task(
        urls=request.urls,
        engine=request.engine,
        options=request.options,
        max_concurrent=min(request.max_concurrent, settings.max_concurrent_crawls)
    )

    # 启动批量爬取
    asyncio.create_task(
        crawler_manager.execute_batch_crawl(batch_id)
    )

    logger.info(f"创建批量任务: {batch_id} with {len(request.urls)} URLs")

    return {
        "batch_id": batch_id,
        "total_urls": len(request.urls),
        "status": "processing",
        "timestamp": datetime.now().isoformat()
    }

@app.get("/api/v2/batch/{batch_id}")
async def get_batch_status(batch_id: str):
    """获取批量任务状态"""
    if not crawler_manager:
        raise HTTPException(status_code=503, detail="爬虫服务未初始化")

    try:
        status = await crawler_manager.get_batch_status(batch_id)
        return status
    except Exception:
        raise HTTPException(status_code=404, detail=f"批量任务不存在: {batch_id}") from None

@app.get("/api/v2/stats")
async def get_statistics():
    """获取服务统计信息"""
    if not crawler_manager:
        raise HTTPException(status_code=503, detail="爬虫服务未初始化")

    try:
        # 获取爬虫统计
        crawler_stats = await crawler_manager.get_statistics()

        # 获取存储统计
        storage_stats = {}
        if storage_manager:
            storage_stats = await storage_manager.get_statistics()

        # 获取成本统计
        cost_stats = {}
        if settings.enable_cost_monitoring:
            cost_stats = await crawler_manager.get_cost_stats()

        return {
            "service": {
                "name": settings.app_name,
                "version": settings.version,
                "uptime": "0h 0m 0s"  # TODO: 计算实际运行时间
            },
            "crawler": crawler_stats,
            "storage": storage_stats,
            "cost": cost_stats,
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"获取统计信息失败: {e}")
        raise HTTPException(status_code=500, detail="获取统计信息失败") from e

@app.get("/api/v2/config")
async def get_config():
    """获取当前配置"""
    return {
        "max_concurrent_crawls": settings.max_concurrent_crawls,
        "default_timeout": settings.default_timeout,
        "enable_cache": settings.enable_cache,
        "cache_ttl": settings.cache_ttl,
        "monthly_cost_limit": settings.monthly_cost_limit,
        "daily_cost_limit": settings.daily_cost_limit,
        "storage_type": settings.storage_type,
        "enable_proxy": settings.enable_proxy
    }

@app.post("/api/v2/config")
async def update_config(config: dict[str, Any]):
    """更新配置（仅限运行时配置）"""
    try:
        # 更新允许的配置项
        if "max_concurrent_crawls" in config:
            settings.max_concurrent_crawls = config["max_concurrent_crawls"]

        if "enable_cost_monitoring" in config:
            settings.enable_cost_monitoring = config["enable_cost_monitoring"]

        # 如果爬虫管理器支持，更新其配置
        if crawler_manager and hasattr(crawler_manager, 'update_config'):
            await crawler_manager.update_config(config)

        logger.info("配置更新成功")
        return {"message": "配置更新成功", "updated": list(config.keys())}

    except Exception as e:
        logger.error(f"配置更新失败: {e}")
        raise HTTPException(status_code=400, detail=f"配置更新失败: {str(e)}") from e

# 辅助函数
async def execute_callback(task_id: str, callback_url: str):
    """执行回调通知"""
    try:
        # 获取任务状态
        if crawler_manager:
            status = await crawler_manager.get_task_status(task_id)

            # 发送回调
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    callback_url,
                    json=status,
                    timeout=10.0
                )
                response.raise_for_status()
                logger.info(f"回调发送成功: {callback_url}")

    except Exception as e:
        logger.error(f"回调发送失败 {task_id}: {e}")

if __name__ == "__main__":
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=settings.port,
        reload=settings.debug,
        log_level="info"
    )
