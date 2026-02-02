#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Athena平台 - 多模态文件系统API接口
Platform API Endpoints for Multimodal File System Integration
"""

from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Query, BackgroundTasks
from fastapi.responses import JSONResponse, FileResponse
from typing import List, Optional, Dict, Any
import asyncio
import logging
from datetime import datetime
from pathlib import Path
import tempfile
import shutil

# 导入集成服务
from core.services.multimodal_integration import multimodal_service

# 创建路由器
router = APIRouter(
    prefix="/api/multimodal",
    tags=["多模态文件系统"],
    responses={404: {"description": "Not found"}}
)

logger = logging.getLogger(__name__)

@router.get("/status")
async def get_service_status():
    """获取多模态文件系统服务状态"""
    try:
        # 健康检查
        health = await multimodal_service.health_check()
        service_info = multimodal_service.get_service_info()

        return JSONResponse(content={
            "success": True,
            "service": "multimodal_file_system",
            "status": health.get("status", "unknown"),
            "health": health,
            "service_info": service_info,
            "timestamp": datetime.now().isoformat()
        })

    except Exception as e:
        logger.error(f"获取服务状态失败: {e}")
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": str(e),
                "service": "multimodal_file_system",
                "status": "error"
            }
        )

@router.post("/upload")
async def upload_file_to_multimodal(
    file: UploadFile = File(...),
    description: Optional[str] = Form(None),
    tags: Optional[str] = Form(None),
    background_tasks: BackgroundTasks = BackgroundTasks()
):
    """
    上传文件到多模态文件系统

    Args:
        file: 上传的文件
        description: 文件描述
        tags: 文件标签（逗号分隔）
    """
    try:
        # 创建临时文件
        with tempfile.NamedTemporaryFile(delete=False, suffix=Path(file.filename).suffix) as tmp_file:
            shutil.copyfileobj(file.file, tmp_file)
            tmp_file_path = tmp_file.name

        # 添加描述信息
        full_description = description or ""
        if tags:
            full_description += f" [Tags: {tags}]"

        # 异步上传到多模态系统
        result = await multimodal_service.upload_file(tmp_file_path, full_description)

        # 清理临时文件
        background_tasks.add_task(Path.unlink, Path(tmp_file_path))

        if result.get("success"):
            return JSONResponse(content={
                "success": True,
                "message": "文件上传成功",
                "file_info": result.get("file_info"),
                "upload_time": datetime.now().isoformat()
            })
        else:
            return JSONResponse(
                status_code=400,
                content={
                    "success": False,
                    "error": result.get("error", "上传失败"),
                    "filename": file.filename
                }
            )

    except Exception as e:
        logger.error(f"文件上传异常: {e}")
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": f"上传异常: {str(e)}",
                "filename": file.filename
            }
        )

@router.get("/files")
async def list_multimodal_files(
    file_type: Optional[str] = Query(None, description="文件类型过滤"),
    limit: Optional[int] = Query(100, description="返回数量限制"),
    offset: Optional[int] = Query(0, description="偏移量")
):
    """获取多模态文件系统中的文件列表"""
    try:
        result = await multimodal_service.list_files(file_type, limit)

        if result.get("success"):
            # 添加平台集成的额外信息
            files = result.get("files", [])
            for file_info in files:
                file_info["platform_integration"] = {
                    "api_download_url": f"/api/multimodal/files/{file_info['file_id']}/download",
                    "api_info_url": f"/api/multimodal/files/{file_info['file_id']}",
                    "integrated_at": datetime.now().isoformat()
                }

            return JSONResponse(content={
                "success": True,
                "files": files,
                "total_files": result.get("total_files", 0),
                "filters": {
                    "type": file_type,
                    "limit": limit,
                    "offset": offset
                },
                "timestamp": datetime.now().isoformat()
            })
        else:
            return JSONResponse(
                status_code=400,
                content={
                    "success": False,
                    "error": result.get("error", "获取文件列表失败")
                }
            )

    except Exception as e:
        logger.error(f"获取文件列表异常: {e}")
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": f"获取异常: {str(e)}"
            }
        )

@router.get("/files/{file_id}")
async def get_multimodal_file_info(file_id: str):
    """获取多模态文件信息"""
    try:
        result = await multimodal_service.get_file_info(file_id)

        if result.get("success"):
            file_info = result.get("file_info", {})
            file_info["platform_integration"] = {
                "api_download_url": f"/api/multimodal/files/{file_id}/download",
                "direct_download_url": f"http://localhost:8001/download/{file_id}",
                "integrated_at": datetime.now().isoformat()
            }

            return JSONResponse(content={
                "success": True,
                "file_info": file_info
            })
        else:
            error_msg = result.get("error", "文件不存在")
            if "不存在" in error_msg:
                raise HTTPException(status_code=404, detail=error_msg)
            else:
                return JSONResponse(
                    status_code=400,
                    content={
                        "success": False,
                        "error": error_msg
                    }
                )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取文件信息异常: {e}")
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": f"获取异常: {str(e)}"
            }
        )

@router.get("/files/{file_id}/download")
async def download_multimodal_file(file_id: str, background_tasks: BackgroundTasks):
    """从多模态文件系统下载文件"""
    try:
        # 使用临时目录下载
        with tempfile.TemporaryDirectory() as tmp_dir:
            result = await multimodal_service.download_file(file_id, tmp_dir)

            if result.get("success"):
                file_path = Path(result.get("file_path"))
                if file_path.exists():
                    # 获取原始文件名
                    file_info = result.get("file_info", {})
                    original_filename = file_info.get("filename", f"file_{file_id}")

                    # 返回文件并标记清理
                    background_tasks.add_task(lambda: None)  # 临时文件会自动清理

                    return FileResponse(
                        path=str(file_path),
                        filename=original_filename,
                        media_type='application/octet-stream'
                    )
                else:
                    raise HTTPException(status_code=404, detail="下载的文件不存在")
            else:
                error_msg = result.get("error", "下载失败")
                if "不存在" in error_msg:
                    raise HTTPException(status_code=404, detail=error_msg)
                else:
                    return JSONResponse(
                        status_code=400,
                        content={
                            "success": False,
                            "error": error_msg
                        }
                    )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"下载文件异常: {e}")
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": f"下载异常: {str(e)}"
            }
        )

@router.post("/batch/upload")
async def batch_upload_to_multimodal(
    files: List[UploadFile] = File(...),
    descriptions: Optional[str] = Form(None),
    tags: Optional[str] = Form(None),
    background_tasks: BackgroundTasks = BackgroundTasks()
):
    """
    批量上传文件到多模态文件系统

    Args:
        files: 上传的文件列表
        descriptions: 描述列表（逗号分隔）
        tags: 标签（逗号分隔）
    """
    try:
        # 处理描述列表
        desc_list = []
        if descriptions:
            desc_list = [d.strip() for d in descriptions.split(",")]

        # 为所有文件添加标签
        if tags:
            tag_suffix = f" [Tags: {tags}]"
            for i in range(len(desc_list)):
                desc_list[i] = desc_list[i] + tag_suffix if desc_list[i] else tag_suffix
            # 如果描述数量少于文件数量，剩余文件使用标签
            while len(desc_list) < len(files):
                desc_list.append(tag_suffix if tags else None)

        # 创建临时文件
        tmp_file_paths = []
        for file in files:
            with tempfile.NamedTemporaryFile(delete=False, suffix=Path(file.filename).suffix) as tmp_file:
                shutil.copyfileobj(file.file, tmp_file)
                tmp_file_paths.append(tmp_file.name)

        # 批量上传
        results = await multimodal_service.batch_upload(tmp_file_paths, desc_list)

        # 清理临时文件
        for tmp_path in tmp_file_paths:
            background_tasks.add_task(Path.unlink, Path(tmp_path))

        # 统计结果
        success_count = sum(1 for r in results if r.get("success"))
        failed_count = len(results) - success_count

        return JSONResponse(content={
            "success": True,
            "message": f"批量上传完成",
            "total_files": len(files),
            "success_count": success_count,
            "failed_count": failed_count,
            "results": results,
            "timestamp": datetime.now().isoformat()
        })

    except Exception as e:
        logger.error(f"批量上传异常: {e}")
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": f"批量上传异常: {str(e)}"
            }
        )

@router.get("/statistics")
async def get_multimodal_statistics():
    """获取多模态文件系统统计信息"""
    try:
        result = await multimodal_service.get_statistics()

        if result.get("success"):
            # 添加平台集成统计
            stats = result.get("statistics", {})
            stats["platform_integration"] = {
                "api_endpoint": "/api/multimodal",
                "integration_active": True,
                "last_check": datetime.now().isoformat()
            }

            return JSONResponse(content={
                "success": True,
                "statistics": stats,
                "storage_info": result.get("storage_info", {}),
                "timestamp": datetime.now().isoformat()
            })
        else:
            return JSONResponse(
                status_code=400,
                content={
                    "success": False,
                    "error": result.get("error", "获取统计失败")
                }
            )

    except Exception as e:
        logger.error(f"获取统计信息异常: {e}")
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": f"获取异常: {str(e)}"
            }
        )

@router.post("/process/{file_id}")
async def process_multimodal_file(
    file_id: str,
    process_type: str = Form(..., description="处理类型: ocr, analyze, extract"),
    options: Optional[str] = Form(None, description="处理选项（JSON格式）")
):
    """
    处理多模态文件（预留接口，用于AI处理集成）

    Args:
        file_id: 文件ID
        process_type: 处理类型
        options: 处理选项
    """
    try:
        # 首先检查文件是否存在
        file_result = await multimodal_service.get_file_info(file_id)
        if not file_result.get("success"):
            raise HTTPException(status_code=404, detail="文件不存在")

        file_info = file_result.get("file_info", {})

        # 解析处理选项
        process_options = {}
        if options:
            import json
            try:
                process_options = json.loads(options)
            except json.JSONDecodeError:
                return JSONResponse(
                    status_code=400,
                    content={
                        "success": False,
                        "error": "处理选项格式错误，需要JSON格式"
                    }
                )

        # 这里可以集成AI处理功能
        # 目前返回处理任务已创建的响应
        task_id = f"task_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{file_id[:8]}"

        return JSONResponse(content={
            "success": True,
            "message": f"文件处理任务已创建",
            "task_id": task_id,
            "file_info": {
                "file_id": file_id,
                "filename": file_info.get("filename"),
                "file_type": file_info.get("file_type")
            },
            "process_type": process_type,
            "process_options": process_options,
            "status": "queued",
            "created_at": datetime.now().isoformat(),
            "note": "AI处理功能将在后续版本中集成"
        })

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"文件处理异常: {e}")
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": f"处理异常: {str(e)}"
            }
        )

# 导出路由器
__all__ = ['router']