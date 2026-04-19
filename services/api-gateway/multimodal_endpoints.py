#!/usr/bin/env python3
"""
Athena API Gateway - 多模态文件处理端点
Multimodal File Processing Endpoints

为统一网关添加多模态文件处理功能
支持文件上传、解析、提取等操作

Author: Athena Team
Date: 2026-02-24
Version: 1.0.0
"""

import io
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import aiohttp
from fastapi import FastAPI, File, Form, HTTPException, Query, UploadFile
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

# 配置日志
logger = logging.getLogger(__name__)


# ==================== 数据模型 ====================

class FileUploadRequest(BaseModel):
    """文件上传请求"""
    tags: list[str] | None = Field(None, description="文件标签")
    category: str | None = Field(None, description="文件分类")
    auto_process: bool = Field(False, description="是否自动处理文件")


class FileProcessRequest(BaseModel):
    """文件处理请求"""
    file_type: str = Field(..., description="文件类型: pdf, docx, image, etc.")
    operation: str = Field("extract", description="操作类型: extract, parse, analyze")
    options: dict[str, Any] = Field(default_factory=dict, description="处理选项")


class BatchProcessRequest(BaseModel):
    """批量处理请求"""
    file_paths: list[str] = Field(..., description="文件路径列表")
    operation: str = Field("extract", description="操作类型")
    options: dict[str, Any] = Field(default_factory=dict, description="处理选项")


class FileProcessResponse(BaseModel):
    """文件处理响应"""
    success: bool
    file_id: str | None = None
    file_path: str | None = None
    operation: str | None = None
    result: dict[str, Any] | None = None
    error: str | None = None
    timestamp: str


class BatchProcessResponse(BaseModel):
    """批量处理响应"""
    success: bool
    total_files: int
    success_count: int
    failed_count: int
    results: list[dict[str, Any]]
    timestamp: str


# ==================== 适配器客户端 ====================

class MultimodalClient:
    """多模态服务客户端"""

    def __init__(self, base_url: str = "http://localhost:8021"):
        self.base_url = base_url
        self.session = None
        self.logger = logging.getLogger(self.__class__.__name__)

    async def initialize(self):
        """初始化客户端"""
        if self.session is None:
            timeout = aiohttp.ClientTimeout(total=120)  # 2分钟超时
            self.session = aiohttp.ClientSession(timeout=timeout)

    async def cleanup(self):
        """清理客户端"""
        if self.session:
            await self.session.close()
            self.session = None

    async def upload_file(
        self,
        file_content: bytes,
        filename: str,
        mime_type: str,
        tags: list[str] = None,
        category: str = None
    ) -> dict[str, Any]:
        """上传文件"""
        try:
            await self.initialize()

            data = aiohttp.FormData()
            data.add_field('file', file_content, filename=filename, content_type=mime_type)
            if tags:
                data.add_field('tags', ','.join(tags))
            if category:
                data.add_field('category', category)

            url = f"{self.base_url}/api/files/upload"
            async with self.session.post(url, data=data) as response:
                return await response.json()

        except Exception as e:
            self.logger.error(f"Upload error: {e}")
            return {"success": False, "error": str(e)}

    async def get_file_info(self, file_id: str) -> dict[str, Any]:
        """获取文件信息"""
        try:
            await self.initialize()
            url = f"{self.base_url}/api/files/{file_id}"
            async with self.session.get(url) as response:
                return await response.json()
        except Exception as e:
            self.logger.error(f"Get file info error: {e}")
            return {"success": False, "error": str(e)}

    async def list_files(
        self,
        file_type: str = None,
        limit: int = 20,
        offset: int = 0
    ) -> dict[str, Any]:
        """列出文件"""
        try:
            await self.initialize()
            params = {"limit": limit, "offset": offset}
            if file_type:
                params["file_type"] = file_type

            url = f"{self.base_url}/api/files/list"
            async with self.session.get(url, params=params) as response:
                return await response.json()
        except Exception as e:
            self.logger.error(f"List files error: {e}")
            return {"success": False, "error": str(e)}

    async def download_file(self, file_id: str) -> bytes | None:
        """下载文件"""
        try:
            await self.initialize()
            url = f"{self.base_url}/api/files/{file_id}/download"
            async with self.session.get(url) as response:
                if response.status == 200:
                    return await response.read()
        except Exception as e:
            self.logger.error(f"Download error: {e}")
            return None

    async def delete_file(self, file_id: str) -> dict[str, Any]:
        """删除文件"""
        try:
            await self.initialize()
            url = f"{self.base_url}/api/files/{file_id}"
            async with self.session.delete(url) as response:
                return await response.json()
        except Exception as e:
            self.logger.error(f"Delete error: {e}")
            return {"success": False, "error": str(e)}

    async def get_statistics(self) -> dict[str, Any]:
        """获取统计信息"""
        try:
            await self.initialize()
            url = f"{self.base_url}/api/stats"
            async with self.session.get(url) as response:
                return await response.json()
        except Exception as e:
            self.logger.error(f"Get statistics error: {e}")
            return {"success": False, "error": str(e)}


# ==================== 端点路由 ====================

def register_multimodal_endpoints(app: FastAPI, client: MultimodalClient):
    """注册多模态文件处理端点"""

    @app.get("/api/v1/multimodal/health")
    async def multimodal_health_check():
        """多模态服务健康检查"""
        try:
            # 检查多模态服务是否运行
            url = f"{client.base_url}/health"
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=5)) as response:
                    if response.status == 200:
                        health_data = await response.json()
                        return {
                            "status": "healthy",
                            "multimodal_service": health_data,
                            "gateway_timestamp": datetime.now(timezone.utc).isoformat()
                        }
                    else:
                        return {
                            "status": "unhealthy",
                            "error": f"Multimodal service returned {response.status}",
                            "timestamp": datetime.now(timezone.utc).isoformat()
                        }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }

    @app.post("/api/v1/multimodal/upload")
    async def upload_multimodal_file(
        file: UploadFile = File(...),
        tags: str | None = Form(None),
        category: str | None = Form(None),
        auto_process: bool = Form(False)
    ):
        """
        上传多模态文件

        支持的文件类型:
        - 文档: PDF, DOCX, TXT, MD
        - 图片: JPG, PNG, GIF, BMP, WEBP
        - 音频: MP3, WAV, FLAC
        - 视频: MP4, AVI, MKV, MOV
        - 数据: JSON, XML, CSV
        - 代码: PY, JS, HTML, CSS, 等
        """
        try:
            # 读取文件内容
            file_content = await file.read()
            filename = file.filename
            mime_type = file.content_type

            # 解析标签
            tag_list = tags.split(',') if tags else []

            # 上传到多模态服务
            result = await client.upload_file(
                file_content=file_content,
                filename=filename,
                mime_type=mime_type,
                tags=tag_list,
                category=category
            )

            if auto_process and result.get('success'):
                # 自动处理：获取文件信息
                file_info = await client.get_file_info(result['file_id'])
                result['file_info'] = file_info

            return result

        except Exception as e:
            logger.error(f"Multimodal file upload error: {e}")
            raise HTTPException(status_code=500, detail=f"文件上传失败: {str(e)}") from e

    @app.post("/api/v1/multimodal/process")
    async def process_multimodal_file(request: FileProcessRequest):
        """
        处理多模态文件

        根据文件类型执行不同的处理操作:
        - PDF/DOCX: 提取文本内容
        - 图片: OCR文字识别
        - 音频/视频: 转录和元数据提取
        """
        try:
            # 根据文件类型选择处理方法
            processing_funcs = {
                'pdf': client._extract_text_from_pdf,
                'docx': client._extract_text_from_docx,
                'image': client._extract_text_from_image,
            }

            if request.file_type not in processing_funcs:
                raise HTTPException(
                    status_code=400,
                    detail=f"不支持的文件类型: {request.file_type}"
                )

            # 执行处理
            process_func = processing_funcs[request.file_type]
            result = await process_func(request.options.get('file_path'))

            return result

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Multimodal file processing error: {e}")
            raise HTTPException(status_code=500, detail=f"文件处理失败: {str(e)}") from e

    @app.post("/api/v1/multimodal/process-upload")
    async def process_and_upload_file(
        file: UploadFile = File(...),
        operation: str = Form("extract"),
        options: str = Form("{}")
    ):
        """
        上传并处理文件（一步操作）

        先上传文件到多模态服务，然后根据文件类型自动处理
        """
        try:
            # 读取文件
            file_content = await file.read()
            filename = file.filename
            mime_type = file.content_type

            # 解析选项
            try:
                import json
                options = json.loads(options) if options else {}
            except Exception:
                options = {}

            # 确定文件类型
            file_ext = Path(filename).suffix.lower()
            type_map = {
                '.pdf': 'pdf',
                '.docx': 'docx',
                '.doc': 'docx',
                '.jpg': 'image',
                '.jpeg': 'image',
                '.png': 'image',
                '.gif': 'image',
                '.bmp': 'image',
                '.webp': 'image',
            }

            type_map.get(file_ext, 'unknown')

            # 上传文件
            upload_result = await client.upload_file(
                file_content=file_content,
                filename=filename,
                mime_type=mime_type,
                tags=options.get('tags', []),
                category=options.get('category')
            )

            if not upload_result.get('success'):
                return upload_result

            # 如果需要处理，获取文件信息
            if operation != "upload":
                file_info = await client.get_file_info(upload_result['file_id'])
                upload_result['file_info'] = file_info
                upload_result['processed'] = True

            return upload_result

        except Exception as e:
            logger.error(f"Process and upload error: {e}")
            raise HTTPException(status_code=500, detail=f"处理上传失败: {str(e)}") from e

    @app.get("/api/v1/multimodal/files")
    async def list_multimodal_files(
        file_type: str | None = Query(None, description="过滤文件类型"),
        limit: int = Query(20, ge=1, le=100),
        offset: int = Query(0, ge=0)
    ):
        """
        获取多模态文件列表

        可以按文件类型过滤，支持分页
        """
        try:
            result = await client.list_files(
                file_type=file_type,
                limit=limit,
                offset=offset
            )
            return result

        except Exception as e:
            logger.error(f"List multimodal files error: {e}")
            raise HTTPException(status_code=500, detail=f"获取文件列表失败: {str(e)}") from e

    @app.get("/api/v1/multimodal/files/{file_id}")
    async def get_multimodal_file(file_id: str):
        """
        获取多模态文件信息

        包括文件详情和提取的内容
        """
        try:
            result = await client.get_file_info(file_id)
            return result

        except Exception as e:
            logger.error(f"Get multimodal file info error: {e}")
            raise HTTPException(status_code=500, detail=f"获取文件信息失败: {str(e)}") from e

    @app.get("/api/v1/multimodal/files/{file_id}/download")
    async def download_multimodal_file(file_id: str):
        """
        下载多模态文件

        返回原始文件内容
        """
        try:
            content = await client.download_file(file_id)

            if content:
                # 尝试从响应中获取文件名
                file_info = await client.get_file_info(file_id)
                filename = file_info.get('filename', file_id)

                return FileResponse(
                    content=io.BytesIO(content),
                    filename=filename,
                    media_type='application/octet-stream'
                )
            else:
                raise HTTPException(status_code=404, detail="文件不存在")

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Download multimodal file error: {e}")
            raise HTTPException(status_code=500, detail=f"下载文件失败: {str(e)}") from e

    @app.delete("/api/v1/multimodal/files/{file_id}")
    async def delete_multimodal_file(file_id: str):
        """
        删除多模态文件

        同时删除存储的文件和数据库记录
        """
        try:
            result = await client.delete_file(file_id)
            return result

        except Exception as e:
            logger.error(f"Delete multimodal file error: {e}")
            raise HTTPException(status_code=500, detail=f"删除文件失败: {str(e)}") from e

    @app.get("/api/v1/multimodal/stats")
    async def get_multimodal_stats():
        """
        获取多模态文件统计信息

        包括文件数量、大小、类型分布等
        """
        try:
            result = await client.get_statistics()
            return result

        except Exception as e:
            logger.error(f"Get multimodal stats error: {e}")
            raise HTTPException(status_code=500, detail=f"获取统计信息失败: {str(e)}") from e

    @app.post("/api/v1/multimodal/batch")
    async def batch_process_multimodal_files(request: BatchProcessRequest):
        """
        批量处理多模态文件

        支持同时处理多个文件
        """
        try:
            results = []
            success_count = 0
            failed_count = 0

            for file_path in request.file_paths:
                try:
                    # 确定文件类型
                    file_ext = Path(file_path).suffix.lower()
                    type_map = {
                        '.pdf': 'pdf',
                        '.docx': 'docx',
                        '.jpg': 'image',
                        '.jpeg': 'image',
                        '.png': 'image',
                    }

                    file_type = type_map.get(file_ext, 'unknown')

                    # 处理文件
                    process_result = await client._extract_text_from_pdf(file_path)

                    results.append({
                        "file_path": file_path,
                        "file_type": file_type,
                        "operation": request.operation,
                        "result": process_result
                    })

                    if process_result.get('success'):
                        success_count += 1
                    else:
                        failed_count += 1

                except Exception as e:
                    logger.error(f"Batch process error for {file_path}: {e}")
                    results.append({
                        "file_path": file_path,
                        "operation": request.operation,
                        "result": {"success": False, "error": str(e)}
                    })
                    failed_count += 1

            return {
                "success": True,
                "total_files": len(request.file_paths),
                "success_count": success_count,
                "failed_count": failed_count,
                "results": results,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }

        except Exception as e:
            logger.error(f"Batch process error: {e}")
            raise HTTPException(status_code=500, detail=f"批量处理失败: {str(e)}") from e


# ==================== 工具函数 ====================

def setup_multimodal_integration(app: FastAPI, config: dict = None):
    """
    设置多模态集成到网关

    Args:
        app: FastAPI应用实例
        config: 配置字典
    """
    # 默认配置
    if config is None:
        config = {
            "multimodal_service_url": "http://localhost:8021",
            "enabled": True
        }

    if not config.get("enabled", True):
        logger.info("多模态服务集成已禁用")
        return

    # 创建客户端
    client = MultimodalClient(base_url=config["multimodal_service_url"])

    # 注册端点
    register_multimodal_endpoints(app, client)

    # 在应用启动时初始化客户端
    @app.on_event("startup")
    async def initialize_multimodal_client():
        """启动时初始化多模态客户端"""
        await client.initialize()
        logger.info(f"✅ 多模态服务客户端已初始化: {config['multimodal_service_url']}")

    # 在应用关闭时清理客户端
    @app.on_event("shutdown")
    async def cleanup_multimodal_client():
        """关闭时清理多模态客户端"""
        await client.cleanup()
        logger.info("✅ 多模态服务客户端已清理")

    logger.info("✅ 多模态文件处理集成已启用")

    return client


# ==================== 导出函数 ====================

__all__ = [
    "setup_multimodal_integration",
    "MultimodalClient",
    "register_multimodal_endpoints",
    "FileProcessRequest",
    "BatchProcessRequest",
]
