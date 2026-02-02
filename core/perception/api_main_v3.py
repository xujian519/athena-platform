#!/usr/bin/env python3
"""
Athena 感知模块 - 生产级API服务 v3.0
集成Redis缓存、异步任务队列、批处理优化
最后更新: 2026-01-26
"""

from fastapi import FastAPI, HTTPException, Depends, Header, BackgroundTasks
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
import uvicorn
import asyncio
import logging
from datetime import datetime
import os
import sys
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# 导入处理器
from core.perception.processors.tesseract_ocr import TesseractOCRProcessor
from core.perception.processors.opencv_image_processor import OpenCVImageProcessor

# 导入缓存和任务队列
from core.perception.cache.redis_cache import RedisCacheManager
from core.perception.queue.async_task_queue import AsyncTaskQueue, TaskPriority

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ========================================
# 数据模型
# ========================================

class HealthResponse(BaseModel):
    """健康检查响应"""
    status: str
    version: str
    timestamp: str
    uptime: float
    ocr_available: bool
    image_processor_available: bool
    cache_available: bool
    task_queue_running: bool

class OCRRequest(BaseModel):
    """OCR请求"""
    image_path: str = Field(..., description="图像文件路径")
    language: str = Field(default="chinese", description="语言: chinese, english, mixed")
    preprocess: bool = Field(default=True, description="是否预处理图像")
    enhance_contrast: bool = Field(default=False, description="是否增强对比度")
    use_cache: bool = Field(default=True, description="是否使用缓存")
    priority: str = Field(default="normal", description="任务优先级: low, normal, high, urgent")

class OCRResponse(BaseModel):
    """OCR响应"""
    success: bool
    task_id: str | None = None
    agent_id: str
    status: str
    text: str | None = None
    confidence: float | None = None
    processing_time: float | None = None
    word_count: int | None = None
    char_count: int | None = None
    cached: bool = False
    error: str | None = None

class ImageProcessRequest(BaseModel):
    """图像处理请求"""
    image_path: str = Field(..., description="图像文件路径")
    operation: str = Field(..., description="操作类型")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="操作参数")
    use_cache: bool = Field(default=True, description="是否使用缓存")
    priority: str = Field(default="normal", description="任务优先级")

class ImageProcessResponse(BaseModel):
    """图像处理响应"""
    success: bool
    task_id: str | None = None
    agent_id: str
    operation: str
    result: Optional[Dict[str, Any]] | None = None
    processing_time: float | None = None
    cached: bool = False
    error: str | None = None

class BatchProcessRequest(BaseModel):
    """批量处理请求"""
    image_paths: List[str] = Field(..., description="图像文件路径列表")
    operation: str = Field(..., description="操作类型")
    parameters: Dict[str, Any] = Field(default_factory=dict)
    use_cache: bool = Field(default=True)
    concurrent: int = Field(default=5, description="并发数")

# ========================================
# 全局实例
# ========================================

# 处理器
ocr_processor = TesseractOCRProcessor()
image_processor = OpenCVImageProcessor()

# 缓存管理器
cache_manager = RedisCacheManager(
    redis_url=os.getenv("REDIS_URL", "redis://localhost:6379/1"),
    default_ttl=3600
)

# 任务队列
task_queue = AsyncTaskQueue(
    max_concurrent_tasks=10,
    max_queue_size=1000
)

# ========================================
# FastAPI应用
# ========================================

app = FastAPI(
    title="Athena Perception Module",
    description="企业级多模态感知处理服务 v3.0 - 集成缓存和任务队列",
    version="3.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# 记录启动时间
import time
app.state.start_time = time.time()

# ========================================
# 启动和关闭事件
# ========================================

@app.on_event("startup")
async def startup_event():
    """应用启动时执行"""
    logger.info("="*60)
    logger.info("Athena 感知模块 v3.0 启动中...")
    logger.info("="*60)

    # 连接Redis
    await cache_manager.connect()

    # 启动任务队列
    await task_queue.start(num_workers=5)

    # 检查OCR处理器
    if ocr_processor.is_available():
        logger.info(f"✓ Tesseract OCR可用: {ocr_processor.get_version()}")
    else:
        logger.warning("⚠ Tesseract OCR不可用")

    # 检查图像处理器
    if image_processor.is_available():
        logger.info(f"✓ OpenCV可用: {image_processor.get_version()}")
    else:
        logger.warning("⚠ OpenCV不可用")

    # 检查缓存
    if cache_manager.is_available():
        logger.info("✓ Redis缓存已连接")
    else:
        logger.warning("⚠ Redis缓存不可用")

    # 检查任务队列
    if task_queue._running:
        logger.info("✓ 任务队列已启动")
    else:
        logger.warning("⚠ 任务队列未启动")

    logger.info("✓ 感知模块服务启动完成")
    logger.info(f"✓ API地址: http://localhost:8070")
    logger.info(f"✓ API文档: http://localhost:8070/docs")

@app.on_event("shutdown")
async def shutdown_event():
    """应用关闭时执行"""
    logger.info("感知模块服务关闭中...")

    # 停止任务队列
    await task_queue.stop()

    # 断开Redis连接
    await cache_manager.disconnect()

# ========================================
# 依赖项
# ========================================

async def get_agent_id(x_agent_id: str = Header(..., description="智能体ID")) -> str:
    """从请求头获取智能体ID"""
    valid_agents = ["athena", "xiaonuo", "xiaona"]

    if x_agent_id not in valid_agents:
        logger.warning(f"未知的智能体ID: {x_agent_id}")

    return x_agent_id

def parse_priority(priority_str: str) -> TaskPriority:
    """解析优先级字符串"""
    priority_map = {
        "low": TaskPriority.LOW,
        "normal": TaskPriority.NORMAL,
        "high": TaskPriority.HIGH,
        "urgent": TaskPriority.URGENT
    }
    return priority_map.get(priority_str.lower(), TaskPriority.NORMAL)

# ========================================
# API端点
# ========================================

@app.get("/", tags=["根路径"])
async def root():
    """根路径"""
    cache_avail = cache_manager.is_available()

    return {
        "service": "Athena Perception Module",
        "version": "3.0.0",
        "status": "running",
        "timestamp": datetime.now().isoformat(),
        "features": {
            "ocr": {
                "available": ocr_processor.is_available(),
                "engine": "Tesseract" if ocr_processor.is_available() else "None"
            },
            "image_processor": {
                "available": image_processor.is_available(),
                "operations": image_processor.get_supported_operations() if image_processor.is_available() else []
            },
            "cache": {
                "available": cache_avail,
                "type": "Redis" if cache_avail else "None"
            },
            "task_queue": {
                "running": task_queue._running,
                "stats": task_queue.get_stats()
            }
        },
        "endpoints": {
            "health": "/health",
            "docs": "/docs",
            "metrics": "/metrics",
            "cache_stats": "/cache/stats",
            "queue_stats": "/queue/stats",
            "api": {
                "ocr": "/api/v3/perception/ocr",
                "image": "/api/v3/perception/image",
                "batch": "/api/v3/perception/batch"
            }
        }
    }

@app.get("/health", response_model=HealthResponse, tags=["健康检查"])
async def health_check():
    """健康检查端点"""
    import time
    uptime = time.time() - app.state.start_time

    return HealthResponse(
        status="healthy",
        version="3.0.0",
        timestamp=datetime.now().isoformat(),
        uptime=uptime,
        ocr_available=ocr_processor.is_available(),
        image_processor_available=image_processor.is_available(),
        cache_available=cache_manager.is_available(),
        task_queue_running=task_queue._running
    )

@app.get("/cache/stats", tags=["缓存管理"])
async def get_cache_stats():
    """获取缓存统计信息"""
    if cache_manager.is_available():
        health = await cache_manager.health_check()
        health["stats"] = cache_manager.get_stats()
        return health
    else:
        return {"status": "unavailable", "error": "Redis不可用"}

@app.get("/queue/stats", tags=["任务队列"])
async def get_queue_stats():
    """获取任务队列统计信息"""
    return task_queue.get_stats()

@app.post("/cache/clear", tags=["缓存管理"])
async def clear_cache():
    """清空所有缓存"""
    success = await cache_manager.clear_all()
    if success:
        return {"message": "缓存已清空"}
    else:
        raise HTTPException(status_code=500, detail="清空缓存失败")

# ========================================
# v3 API端点（集成缓存和任务队列）
# ========================================

@app.post("/api/v3/perception/ocr", response_model=OCRResponse, tags=["感知处理-v3"])
async def process_ocr_v3(
    request: OCRRequest,
    agent_id: str = Depends(get_agent_id)
):
    """
    OCR文字识别（v3.0 - 集成缓存和任务队列）

    新增功能：
    - Redis结果缓存
    - 异步任务队列
    - 任务优先级
    - 自动重试
    """
    import uuid
    task_id = str(uuid.uuid4())

    logger.info(f"[{agent_id}] 收到OCR请求: {request.image_path}")

    try:
        # 1. 检查缓存
        cached_result = None
        if request.use_cache and cache_manager.is_available():
            cached_result = await cache_manager.get_ocr_result(
                request.image_path,
                request.language,
                request.preprocess
            )

            if cached_result:
                logger.info(f"[{agent_id}] OCR缓存命中: {request.image_path}")
                return OCRResponse(
                    success=True,
                    task_id=task_id,
                    agent_id=agent_id,
                    status="completed",
                    text=cached_result.get("text"),
                    confidence=cached_result.get("confidence"),
                    processing_time=0.001,  # 缓存返回，几乎无耗时
                    word_count=cached_result.get("word_count"),
                    char_count=cached_result.get("char_count"),
                    cached=True
                )

        # 2. 创建异步任务
        async def ocr_task():
            # 使用真实OCR处理器
            result = await ocr_processor.process_ocr(
                image_path=request.image_path,
                language=request.language,
                preprocess=request.preprocess,
                enhance_contrast=request.enhance_contrast
            )

            # 保存到缓存
            if request.use_cache and cache_manager.is_available():
                await cache_manager.set_ocr_result(
                    request.image_path,
                    request.language,
                    request.preprocess,
                    result
                )

            return result

        # 3. 提交到任务队列
        priority = parse_priority(request.priority)
        queue_task_id = await task_queue.submit(ocr_task, priority=priority)

        # 4. 等待任务完成
        result = await task_queue.get_task_result(queue_task_id, timeout=60)

        logger.info(f"[{agent_id}] OCR处理成功: {result['word_count']}个词")

        return OCRResponse(
            success=True,
            task_id=task_id,
            agent_id=agent_id,
            status="completed",
            text=result["text"],
            confidence=result["confidence"],
            processing_time=result["processing_time"],
            word_count=result["word_count"],
            char_count=result["char_count"],
            cached=False
        )

    except asyncio.TimeoutError:
        logger.error(f"[{agent_id}] OCR处理超时")
        return OCRResponse(
            success=False,
            agent_id=agent_id,
            status="timeout",
            error="处理超时"
        )
    except Exception as e:
        logger.error(f"[{agent_id}] OCR处理失败: {e}")
        return OCRResponse(
            success=False,
            agent_id=agent_id,
            status="failed",
            error=str(e)
        )

@app.post("/api/v3/perception/image", response_model=ImageProcessResponse, tags=["感知处理-v3"])
async def process_image_v3(
    request: ImageProcessRequest,
    agent_id: str = Depends(get_agent_id)
):
    """
    图像处理（v3.0 - 集成缓存和任务队列）

    新增功能：
    - Redis特征缓存
    - 异步任务队列
    - 任务优先级
    """
    import uuid
    task_id = str(uuid.uuid4())

    logger.info(f"[{agent_id}] 收到图像处理请求: {request.operation}")

    try:
        # 1. 检查缓存
        cached_result = None
        if request.use_cache and cache_manager.is_available():
            cached_result = await cache_manager.get_image_features(
                request.image_path,
                request.operation,
                request.parameters
            )

            if cached_result:
                logger.info(f"[{agent_id}] 图像特征缓存命中")
                return ImageProcessResponse(
                    success=True,
                    task_id=task_id,
                    agent_id=agent_id,
                    operation=request.operation,
                    result=cached_result,
                    processing_time=0.001,
                    cached=True
                )

        # 2. 创建异步任务
        async def image_task():
            result = await image_processor.process_image(
                image_path=request.image_path,
                operation=request.operation,
                parameters=request.parameters
            )

            # 保存到缓存
            if request.use_cache and cache_manager.is_available():
                await cache_manager.set_image_features(
                    request.image_path,
                    request.operation,
                    result["result"],
                    request.parameters
                )

            return result

        # 3. 提交到任务队列
        priority = parse_priority(request.priority)
        queue_task_id = await task_queue.submit(image_task, priority=priority)

        # 4. 等待任务完成
        result = await task_queue.get_task_result(queue_task_id, timeout=60)

        logger.info(f"[{agent_id}] 图像处理成功")

        return ImageProcessResponse(
            success=True,
            task_id=task_id,
            agent_id=agent_id,
            operation=request.operation,
            result=result["result"],
            processing_time=result["processing_time"],
            cached=False
        )

    except Exception as e:
        logger.error(f"[{agent_id}] 图像处理失败: {e}")
        return ImageProcessResponse(
            success=False,
            agent_id=agent_id,
            operation=request.operation,
            error=str(e)
        )

@app.post("/api/v3/perception/batch", tags=["感知处理-v3"])
async def batch_process_v3(
    request: BatchProcessRequest,
    agent_id: str = Depends(get_agent_id)
):
    """
    批量处理（v3.0 - 并发优化）

    新增功能：
    - 并发控制
    - 进度跟踪
    - 批量缓存查询
    """
    import uuid
    batch_id = str(uuid.uuid4())

    logger.info(f"[{agent_id}] 批量处理请求: {len(request.image_paths)}个文件")

    try:
        # 1. 批量查询缓存
        cached_results = {}
        remaining_paths = []

        if request.use_cache and cache_manager.is_available():
            for path in request.image_paths:
                if request.operation == "ocr":
                    cached = await cache_manager.get_ocr_result(
                        path,
                        request.parameters.get("language", "chinese"),
                        request.parameters.get("preprocess", True)
                    )
                else:
                    cached = await cache_manager.get_image_features(
                        path,
                        request.operation,
                        request.parameters
                    )

                if cached:
                    cached_results[path] = cached
                else:
                    remaining_paths.append(path)

            logger.info(f"[{agent_id}] 缓存命中: {len(cached_results)}/{len(request.image_paths)}")

        if not remaining_paths:
            # 全部缓存命中
            return {
                "batch_id": batch_id,
                "agent_id": agent_id,
                "operation": request.operation,
                "total": len(request.image_paths),
                "success": len(cached_results),
                "failed": 0,
                "cached": len(cached_results),
                "results": cached_results
            }

        # 2. 创建批量任务
        async def process_batch():
            results = {}

            # 限制并发数
            semaphore = asyncio.Semaphore(request.concurrent)

            async def process_single(path):
                async with semaphore:
                    if request.operation == "ocr":
                        result = await ocr_processor.process_ocr(
                            path,
                            **request.parameters
                        )
                    else:
                        result = await image_processor.process_image(
                            path,
                            request.operation,
                            request.parameters
                        )
                    return path, result

            # 并发处理
            tasks = [process_single(path) for path in remaining_paths]
            completed = await asyncio.gather(*tasks, return_exceptions=True)

            for item in completed:
                if isinstance(item, Exception):
                    continue
                path, result = item
                results[path] = result

            return results

        # 3. 提交批量任务
        queue_task_id = await task_queue.submit(process_batch, priority=TaskPriority.NORMAL)

        # 4. 等待完成
        new_results = await task_queue.get_task_result(queue_task_id, timeout=300)

        # 5. 合并缓存和新结果
        all_results = {**cached_results, **new_results}

        # 统计结果
        success_count = sum(1 for r in all_results.values() if isinstance(r, dict) and r.get("success", True))
        fail_count = len(all_results) - success_count

        return {
            "batch_id": batch_id,
            "agent_id": agent_id,
            "operation": request.operation,
            "total": len(request.image_paths),
            "success": success_count,
            "failed": fail_count,
            "cached": len(cached_results),
            "results": all_results
        }

    except Exception as e:
        logger.error(f"[{agent_id}] 批量处理失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ========================================
# 主函数
# ========================================

if __name__ == "__main__":
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8070,
        log_level="info",
        access_log=True,
        workers=1
    )
