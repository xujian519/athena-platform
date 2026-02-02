#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Athena平台 - 多模态文件系统集成
Platform Integration with Multimodal File System
"""

import os
import sys
import json
import asyncio
import logging
from core.logging_config import setup_logging
from datetime import datetime
from pathlib import Path

# 添加路径
sys.path.append(str(Path(__file__).parent.parent.parent / "core"))
sys.path.append(str(Path(__file__).parent.parent / "api"))

# 导入多模态集成服务
try:
    from core.services.multimodal_integration import multimodal_service
    MULTIMODAL_AVAILABLE = True
except ImportError:
    MULTIMODAL_AVAILABLE = False
    logging.warning("多模态文件系统集成服务不可用")

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = setup_logging()

class PlatformMultimodalIntegration:
    """平台多模态文件系统集成类"""

    def __init__(self):
        self.service_available = MULTIMODAL_AVAILABLE
        self.integration_enabled = False

    async def initialize(self):
        """初始化集成"""
        if not self.service_available:
            logger.warning("多模态文件系统服务不可用")
            return False

        try:
            # 检查多模态系统健康状态
            health = await multimodal_service.health_check()
            if health.get("success"):
                self.integration_enabled = True
                logger.info("多模态文件系统集成已启用")
                return True
            else:
                logger.error(f"多模态文件系统健康检查失败: {health.get('error', '未知错误')}")
                return False

        except Exception as e:
            logger.error(f"多模态文件系统集成初始化失败: {e}")
            return False

    async def upload_document(self, file_path: str, doc_type: str = None, metadata: dict = None):
        """
        上传文档到多模态文件系统

        Args:
            file_path: 文件路径
            doc_type: 文档类型 (patent, contract, report等)
            metadata: 元数据

        Returns:
            上传结果
        """
        if not self.integration_enabled:
            return {
                "success": False,
                "error": "多模态文件系统集成未启用",
                "fallback": "建议使用传统文件存储"
            }

        try:
            # 构建描述信息
            description = f"Athena平台文档 - 类型: {doc_type or '通用文档'}"
            if metadata:
                description += f" | 元数据: {json.dumps(metadata, ensure_ascii=False)}"

            # 上传文件
            result = await multimodal_service.upload_file(file_path, description)

            if result.get("success"):
                file_info = result.get("file_info", {})
                # 添加平台特定的元数据
                file_info["platform_metadata"] = {
                    "doc_type": doc_type,
                    "source": "athena_platform",
                    "upload_time": datetime.now().isoformat(),
                    "metadata": metadata or {}
                }

                logger.info(f"文档上传成功: {file_path} -> {file_info['file_id']}")
                return result
            else:
                logger.error(f"文档上传失败: {result.get('error')}")
                return result

        except Exception as e:
            logger.error(f"文档上传异常: {e}")
            return {
                "success": False,
                "error": f"上传异常: {str(e)}"
            }

    async def search_documents(self, file_type: str = None, limit: int = 50):
        """
        搜索文档

        Args:
            file_type: 文件类型过滤
            limit: 返回数量限制

        Returns:
            搜索结果
        """
        if not self.integration_enabled:
            return {
                "success": False,
                "error": "多模态文件系统集成未启用",
                "files": []
            }

        try:
            result = await multimodal_service.list_files(file_type, limit)

            if result.get("success"):
                # 添加平台特定的信息
                files = result.get("files", [])
                for file_info in files:
                    file_info["platform_access"] = {
                        "can_download": True,
                        "can_preview": file_info.get("file_type") in ["document", "image"],
                        "api_endpoint": f"/api/v1/files/{file_info['file_id']}"
                    }

                return result
            else:
                logger.error(f"文档搜索失败: {result.get('error')}")
                return result

        except Exception as e:
            logger.error(f"文档搜索异常: {e}")
            return {
                "success": False,
                "error": f"搜索异常: {str(e)}",
                "files": []
            }

    async def get_document_preview(self, file_id: str):
        """
        获取文档预览信息

        Args:
            file_id: 文件ID

        Returns:
            预览信息
        """
        if not self.integration_enabled:
            return {
                "success": False,
                "error": "多模态文件系统集成未启用"
            }

        try:
            result = await multimodal_service.get_file_info(file_id)

            if result.get("success"):
                file_info = result.get("file_info", {})

                # 添加预览信息
                preview_info = {
                    "file_id": file_id,
                    "filename": file_info.get("filename"),
                    "file_type": file_info.get("file_type"),
                    "size": file_info.get("size"),
                    "upload_time": file_info.get("upload_time"),
                    "preview_available": file_info.get("file_type") in ["document", "image", "text"],
                    "download_url": f"/api/v1/files/{file_id}/download"
                }

                # 如果是小文件，可以提供内容预览
                if file_info.get("size", 0) < 1024 * 1024:  # 小于1MB
                    preview_info["content_preview"] = "内容预览功能需要AI处理集成"

                return {
                    "success": True,
                    "preview_info": preview_info
                }
            else:
                return result

        except Exception as e:
            logger.error(f"获取文档预览异常: {e}")
            return {
                "success": False,
                "error": f"预览异常: {str(e)}"
            }

    async def process_document(self, file_id: str, process_type: str, options: dict = None):
        """
        处理文档（OCR、分析等）

        Args:
            file_id: 文件ID
            process_type: 处理类型 (ocr, analyze, extract_text)
            options: 处理选项

        Returns:
            处理结果
        """
        if not self.integration_enabled:
            return {
                "success": False,
                "error": "多模态文件系统集成未启用",
                "note": "AI处理功能暂未集成"
            }

        # 目前返回处理任务已创建的响应
        # 实际的AI处理将在后续版本中集成
        task_id = f"process_{process_type}_{file_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        return {
            "success": True,
            "message": f"文档处理任务已创建",
            "task_id": task_id,
            "file_id": file_id,
            "process_type": process_type,
            "options": options or {},
            "status": "queued",
            "estimated_time": "30-60秒",
            "note": "AI处理功能正在集成中"
        }

    async def get_system_status(self):
        """获取多模态文件系统状态"""
        if not self.service_available:
            return {
                "service_available": False,
                "error": "多模态文件系统集成服务不可用"
            }

        try:
            health = await multimodal_service.health_check()
            stats = await multimodal_service.get_statistics()

            return {
                "service_available": True,
                "integration_enabled": self.integration_enabled,
                "health": health,
                "statistics": stats,
                "service_info": multimodal_service.get_service_info(),
                "check_time": datetime.now().isoformat()
            }

        except Exception as e:
            return {
                "service_available": True,
                "integration_enabled": False,
                "error": f"状态检查失败: {str(e)}",
                "check_time": datetime.now().isoformat()
            }

# 创建全局实例
platform_multimodal = PlatformMultimodalIntegration()

# 导出主要功能
__all__ = [
    'PlatformMultimodalIntegration',
    'platform_multimodal'
]