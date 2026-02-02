#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
混合多模态API网关 - 集成版本
Hybrid Multimodal API Gateway - Integrated Version

集成Athena统一存储架构，提供智能路由的多模态文件处理服务
Integrated with Athena unified storage architecture for intelligent multimodal processing
"""

import sys
from core.async_main import async_main
import os
from pathlib import Path
from datetime import datetime
import asyncio
import json
import uuid
from typing import Dict, List, Any, Optional

# 添加项目路径
sys.path.append(str(Path(__file__).parent.parent.parent))

from fastapi import FastAPI, File, UploadFile, HTTPException, Form, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware

from core.security.auth import ALLOWED_ORIGINS
from pydantic import BaseModel
import uvicorn
import aiofiles

# 导入存储管理器
from storage_manager import (
    MultimodalStorageManager,
    ProcessingStatus,
    ProcessingMethod,
    FileType
)

# 导入智能路由器
from intelligent_router import (
    get_intelligent_router,
    process_file_intelligently,
    ProcessingRequest,
    ProcessingPriority,
    DataSensitivity
)

# 创建FastAPI应用
app = FastAPI(
    title="Athena智能多模态API网关 - 集成版",
    description="集成统一存储架构的智能多模态处理平台",
    version="2.0.0"
)

# CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 全局存储管理器
storage_manager = None

async def get_storage_manager():
    """获取存储管理器实例"""
    global storage_manager
    if storage_manager is None:
        storage_manager = MultimodalStorageManager()
    return storage_manager

# 响应模型
class HybridProcessingResponse(BaseModel):
    success: bool
    request_id: str
    file_id: int | None = None
    method_used: str
    processing_time: float
    cost: float
    quality_score: float
    result: Optional[Dict[str, Any]] = None
    error: str | None = None

class BatchProcessingResponse(BaseModel):
    success: bool
    batch_id: str
    total_files: int
    processed_files: int
    failed_files: int
    total_cost: float
    total_time: float
    results: List[Dict[str, Any]]

class FileInfo(BaseModel):
    id: int
    original_filename: str
    file_type: str
    file_size: int
    mime_type: Optional[str]
    processing_status: str
    processing_method: Optional[str]
    created_at: Optional[str]
    processed_at: Optional[str]

# 后台处理任务
async def process_file_background(
    file_id: int,
    file_path: str,
    priority: ProcessingPriority,
    sensitivity: DataSensitivity,
    high_quality: bool,
    request_id: str
):
    """后台处理文件"""
    storage = await get_storage_manager()
    router = get_intelligent_router()

    try:
        # 更新状态为处理中
        await storage.update_processing_status(
            file_id=file_id,
            status=ProcessingStatus.PROCESSING
        )

        # 创建处理请求
        processing_request = ProcessingRequest(
            file_path=file_path,
            priority=priority,
            sensitivity=sensitivity,
            high_quality=high_quality,
            batch_size=1
        )

        # 智能选择处理方法
        method = router.choose_optimal_method(processing_request)

        # 执行处理
        start_time = datetime.now()
        result = await process_file_intelligently(
            file_path=file_path,
            priority=priority.value,
            sensitivity=sensitivity.value,
            high_quality=high_quality,
            force_method=method.value
        )
        processing_time = (datetime.now() - start_time).total_seconds()

        if result['success']:
            # 处理成功
            await storage.update_processing_status(
                file_id=file_id,
                status=ProcessingStatus.COMPLETED,
                method=ProcessingMethod(method.value.upper()),
                result=result
            )

            # 如果有向量数据，存储到向量数据库
            if 'vector' in result:
                await storage.store_file_vector(
                    file_id=file_id,
                    vector=result['vector'],
                    vector_metadata={
                        'processing_method': method.value,
                        'quality_score': result.get('quality_score', 0.0),
                        'request_id': request_id
                    }
                )

            print(f"✅ 文件处理完成: ID={file_id}, 方法={method.value}, 耗时={processing_time:.2f}s")
        else:
            # 处理失败
            await storage.update_processing_status(
                file_id=file_id,
                status=ProcessingStatus.FAILED,
                error_message=result.get('error', '未知错误')
            )
            print(f"❌ 文件处理失败: ID={file_id}, 错误={result.get('error')}")

    except Exception as e:
        # 异常处理
        await storage.update_processing_status(
            file_id=file_id,
            status=ProcessingStatus.FAILED,
            error_message=str(e)
        )
        print(f"❌ 文件处理异常: ID={file_id}, 异常={str(e)}")

# API端点
@app.get("/")
async def root():
    """根端点"""
    return {
        "message": "Athena智能多模态API网关 - 集成版",
        "version": "2.0.0",
        "features": [
            "智能路由（MCP vs 本地）",
            "统一存储架构",
            "向量搜索支持",
            "批量处理",
            "实时统计"
        ]
    }

@app.get("/api/health")
async def health_check():
    """健康检查"""
    try:
        storage = await get_storage_manager()
        stats = await storage.get_statistics()

        return {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "storage": {
                "total_files": stats.get('total_files', 0),
                "processing_success_rate": stats.get('processing_success_rate', 0.0)
            },
            "services": {
                "database": "connected" if storage._db_engine else "disconnected",
                "qdrant": "connected" if storage._qdrant_client else "disconnected"
            }
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

@app.post("/api/process", response_model=HybridProcessingResponse)
async def process_file_hybrid(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    priority: str = Form("normal"),
    sensitivity: str = Form("public"),
    high_quality: bool = Form(False)
):
    """智能处理单文件"""
    start_time = datetime.now()
    request_id = str(uuid.uuid4())

    try:
        # 参数验证
        if priority not in ["low", "normal", "high", "urgent"]:
            priority = "normal"

        if sensitivity not in ["public", "internal", "confidential", "secret"]:
            sensitivity = "public"

        # 转换为枚举类型
        priority_enum = ProcessingPriority(priority.upper())
        sensitivity_enum = DataSensitivity(sensitivity.upper())

        # 创建临时文件
        temp_dir = Path("/tmp/athena_multimodal")
        temp_dir.mkdir(parents=True, exist_ok=True)

        temp_file_path = temp_dir / f"{request_id}_{file.filename}"

        # 保存上传的文件
        async with aiofiles.open(temp_file_path, 'wb') as f:
            content = await file.read()
            await f.write(content)

        # 获取存储管理器
        storage = await get_storage_manager()

        # 存储文件到统一存储
        file_id = await storage.store_file(
            source_path=str(temp_file_path),
            original_filename=file.filename,
            mime_type=file.content_type
        )

        if not file_id:
            raise HTTPException(status_code=500, detail="文件存储失败")

        # 获取文件路径用于处理
        file_info = await storage.get_file_info(file_id)
        if not file_info:
            raise HTTPException(status_code=500, detail="获取文件信息失败")

        file_path = file_info['storage_path']

        # 启动后台处理任务
        background_tasks.add_task(
            process_file_background,
            file_id=file_id,
            file_path=file_path,
            priority=priority_enum,
            sensitivity=sensitivity_enum,
            high_quality=high_quality,
            request_id=request_id
        )

        # 获取智能路由器进行预估
        router = get_intelligent_router()
        processing_request = ProcessingRequest(
            file_path=file_path,
            priority=priority_enum,
            sensitivity=sensitivity_enum,
            high_quality=high_quality,
            batch_size=1
        )

        # 预测处理方法
        predicted_method = router.choose_optimal_method(processing_request)

        # 预估成本和时间
        estimated_cost = router.calculate_cost(processing_request, predicted_method)
        estimated_time = router.estimate_processing_time(processing_request, predicted_method)

        processing_time = (datetime.now() - start_time).total_seconds()

        return HybridProcessingResponse(
            success=True,
            request_id=request_id,
            file_id=file_id,
            method_used=predicted_method.value,
            processing_time=processing_time,
            cost=estimated_cost,
            quality_score=router.predict_quality_score(processing_request, predicted_method),
            result={
                "message": "文件已接收，正在后台处理",
                "estimated_processing_time": estimated_time,
                "file_info": {
                    "filename": file.filename,
                    "size": len(content),
                    "type": file.content_type
                }
            }
        )

    except Exception as e:
        processing_time = (datetime.now() - start_time).total_seconds()
        return HybridProcessingResponse(
            success=False,
            request_id=request_id,
            method_used="unknown",
            processing_time=processing_time,
            cost=0.0,
            quality_score=0.0,
            error=str(e)
        )

@app.post("/api/batch-process", response_model=BatchProcessingResponse)
async def process_batch_files(
    background_tasks: BackgroundTasks,
    files: List[UploadFile] = File(...),
    priority: str = Form("normal"),
    sensitivity: str = Form("public"),
    max_concurrent: int = Form(3)
):
    """批量处理文件"""
    start_time = datetime.now()
    batch_id = str(uuid.uuid4())

    try:
        # 参数验证
        if priority not in ["low", "normal", "high", "urgent"]:
            priority = "normal"

        if sensitivity not in ["public", "internal", "confidential", "secret"]:
            sensitivity = "public"

        if max_concurrent < 1 or max_concurrent > 10:
            max_concurrent = 3

        # 转换为枚举类型
        priority_enum = ProcessingPriority(priority.upper())
        sensitivity_enum = DataSensitivity(sensitivity.upper())

        storage = await get_storage_manager()
        results = []

        # 处理每个文件
        for i, file in enumerate(files):
            file_start_time = datetime.now()
            file_request_id = f"{batch_id}_{i}"

            try:
                # 创建临时文件
                temp_dir = Path("/tmp/athena_multimodal")
                temp_dir.mkdir(parents=True, exist_ok=True)

                temp_file_path = temp_dir / f"{file_request_id}_{file.filename}"

                # 保存上传的文件
                async with aiofiles.open(temp_file_path, 'wb') as f:
                    content = await file.read()
                    await f.write(content)

                # 存储文件到统一存储
                file_id = await storage.store_file(
                    source_path=str(temp_file_path),
                    original_filename=file.filename,
                    mime_type=file.content_type
                )

                if file_id:
                    # 获取文件信息
                    file_info = await storage.get_file_info(file_id)
                    file_path = file_info['storage_path']

                    # 启动后台处理（如果有并发槽位）
                    if i < max_concurrent:
                        background_tasks.add_task(
                            process_file_background,
                            file_id=file_id,
                            file_path=file_path,
                            priority=priority_enum,
                            sensitivity=sensitivity_enum,
                            high_quality=True,  # 批量处理默认高质量
                            request_id=file_request_id
                        )

                    file_processing_time = (datetime.now() - file_start_time).total_seconds()

                    results.append({
                        "success": True,
                        "file_id": file_id,
                        "filename": file.filename,
                        "size": len(content),
                        "processing_time": file_processing_time,
                        "status": "queued" if i >= max_concurrent else "processing"
                    })
                else:
                    results.append({
                        "success": False,
                        "filename": file.filename,
                        "error": "文件存储失败"
                    })

            except Exception as e:
                results.append({
                    "success": False,
                    "filename": file.filename,
                    "error": str(e)
                })

        # 统计结果
        processed_files = len([r for r in results if r.get("success")])
        failed_files = len(results) - processed_files
        total_time = (datetime.now() - start_time).total_seconds()

        # 预估总成本
        router = get_intelligent_router()
        estimated_cost = processed_files * 0.01  # 简化成本计算

        return BatchProcessingResponse(
            success=True,
            batch_id=batch_id,
            total_files=len(files),
            processed_files=processed_files,
            failed_files=failed_files,
            total_cost=estimated_cost,
            total_time=total_time,
            results=results
        )

    except Exception as e:
        total_time = (datetime.now() - start_time).total_seconds()
        return BatchProcessingResponse(
            success=False,
            batch_id=batch_id,
            total_files=len(files),
            processed_files=0,
            failed_files=len(files),
            total_cost=0.0,
            total_time=total_time,
            results=[{"error": str(e)}]
        )

@app.get("/api/file/{file_id}")
async def get_file_info(file_id: int):
    """获取文件信息"""
    try:
        storage = await get_storage_manager()
        file_info = await storage.get_file_info(file_id)

        if not file_info:
            raise HTTPException(status_code=404, detail="文件不存在")

        return file_info

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/search/vector")
async def search_by_vector(
    query: str,
    limit: int = 10,
    file_type: str | None = None
):
    """通过文本查询搜索相似文件（语义搜索）"""
    try:
        # 这里应该将查询文本转换为向量
        # 为了简化，我们使用随机向量作为示例
        import random
        query_vector = [random.random() for _ in range(768)]

        # 转换文件类型
        file_type_enum = None
        if file_type:
            try:
                file_type_enum = FileType(file_type.lower())
            except ValueError:
                logger.error(f"Error: {e}", exc_info=True)

        storage = await get_storage_manager()
        results = await storage.search_by_vector(
            query_vector=query_vector,
            limit=limit,
            file_type=file_type_enum
        )

        return {
            "success": True,
            "query": query,
            "results": results,
            "total": len(results)
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "results": []
        }

@app.get("/api/statistics")
async def get_statistics():
    """获取处理统计信息"""
    try:
        storage = await get_storage_manager()
        stats = await storage.get_statistics()

        return {
            "success": True,
            "timestamp": datetime.now().isoformat(),
            "statistics": stats
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

@app.get("/api/files")
async def list_files(
    status: str | None = None,
    file_type: str | None = None,
    limit: int = 50,
    offset: int = 0
):
    """列出文件"""
    try:
        storage = await get_storage_manager()
        # 这里需要实现分页查询逻辑
        # 由于我们使用的是简单的存储管理器，这里返回空列表
        # 在实际项目中，应该从数据库查询

        return {
            "success": True,
            "files": [],
            "total": 0,
            "limit": limit,
            "offset": offset,
            "filters": {
                "status": status,
                "file_type": file_type
            }
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "files": []
        }

@app.delete("/api/file/{file_id}")
async def delete_file(file_id: int):
    """删除文件"""
    try:
        storage = await get_storage_manager()
        file_info = await storage.get_file_info(file_id)

        if not file_info:
            raise HTTPException(status_code=404, detail="文件不存在")

        # 删除物理文件
        if os.path.exists(file_info['storage_path']):
            os.remove(file_info['storage_path'])

        # 删除元数据文件
        meta_path = file_info['storage_path'] + '.meta.json'
        if os.path.exists(meta_path):
            os.remove(meta_path)

        # 更新状态为已归档（而不是真正删除）
        await storage.update_processing_status(
            file_id=file_id,
            status=ProcessingStatus.ARCHIVED
        )

        return {
            "success": True,
            "message": f"文件 {file_id} 已删除"
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/cleanup")
async def cleanup_old_files(days: int = 30):
    """清理旧文件"""
    try:
        storage = await get_storage_manager()
        cleaned_count = await storage.cleanup_old_files(days=days)

        return {
            "success": True,
            "cleaned_files": cleaned_count,
            "message": f"已清理 {cleaned_count} 个超过 {days} 天的旧文件"
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "cleaned_files": 0
        }

# 启动事件
@app.on_event("startup")
async def startup_event():
    """应用启动事件"""
    print("🚀 启动Athena智能多模态API网关 - 集成版")
    print("=" * 50)

    # 初始化存储管理器
    storage = await get_storage_manager()

    # 获取初始统计
    stats = await storage.get_statistics()
    print(f"📊 存储统计: {stats.get('total_files', 0)} 个文件")
    print(f"✅ 数据库: {'已连接' if storage._db_engine else '未连接'}")
    print(f"🔗 向量存储: {'已连接' if storage._qdrant_client else '未连接'}")
    print("=" * 50)

if __name__ == "__main__":
    uvicorn.run(
        "hybrid_api_gateway_integrated:app",
        host="0.0.0.0",
        port=8090,
        reload=True,
        log_level="info"
    )