#!/usr/bin/env python3
"""
多模态文件处理服务适配器
Multimodal File Processing Service Adapter

将多模态文件处理系统集成到Athena统一网关
支持文件上传、解析、提取等多种文件处理功能

Author: Athena Team
Date: 2026-02-24
Version: 1.0.0
"""

import asyncio
import json
import logging

# 导入适配器基类
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

import aiohttp

sys.path.insert(0, str(Path(__file__).parent))
from patent_search_adapter import AdapterConfig, BaseAdapter

# 配置日志
logger = logging.getLogger(__name__)


@dataclass
class FileProcessResult:
    """文件处理结果"""
    file_id: str
    filename: str
    file_type: str
    file_size: int
    processed: bool
    extracted_text: str | None = None
    metadata: dict[str, Any] = None
    error: str | None = None


class MultimodalAdapter(BaseAdapter):
    """多模态文件处理服务适配器"""

    def __init__(self, config: AdapterConfig):
        super().__init__(config)
        self.service_name = "multimodal-fileservice"
        self.api_prefix = "/api/files"

    async def upload_file(
        self,
        file_content: bytes,
        filename: str,
        mime_type: str,
        tags: list[str] | None = None,
        category: str | None = None
    ) -> dict[str, Any]:
        """
        上传文件到多模态处理服务

        Args:
            file_content: 文件二进制内容
            filename: 文件名
            mime_type: MIME类型
            tags: 标签列表
            category: 分类

        Returns:
            上传结果
        """
        try:
            await self.initialize()

            # 准备表单数据
            data = aiohttp.FormData()
            data.add_field('file', file_content, filename=filename, content_type=mime_type)

            if tags:
                data.add_field('tags', ','.join(tags))
            if category:
                data.add_field('category', category)

            # 上传文件
            url = f"{self.config.service_url}{self.api_prefix}/upload"
            self.logger.info(f"Uploading file: {filename} ({len(file_content)} bytes)")

            async with self.session.post(url, data=data) as response:
                response_data = await response.json()

                if response.status == 200 and response_data.get('success'):
                    file_id = response_data.get('file_id')
                    self.logger.info(f"File uploaded successfully: {file_id}")

                    return {
                        "success": True,
                        "file_id": file_id,
                        "filename": response_data.get('filename'),
                        "file_type": response_data.get('file_type'),
                        "file_size": response_data.get('file_size'),
                        "message": response_data.get('message'),
                        "timestamp": datetime.now().isoformat(),
                    }
                else:
                    return await self._handle_error(
                        Exception(f"Upload failed: {response.status} - {response_data}")
                    )

        except Exception as error:
            self.logger.error(f"File upload error: {error}")
            return await self._handle_error(error)

    async def process_file(
        self,
        file_path: str,
        processing_type: str = "extract"
    ) -> dict[str, Any]:
        """
        处理文件（提取内容/解析格式）

        Args:
            file_path: 文件路径
            processing_type: 处理类型 (extract/parse/analyze)

        Returns:
            处理结果
        """
        try:
            await self.initialize()

            # 读取文件
            with open(file_path, 'rb') as f:
                file_content = f.read()
            filename = Path(file_path).name

            # 首先上传文件
            upload_result = await self.upload_file(
                file_content=file_content,
                filename=filename,
                mime_type=self._get_mime_type(file_path)
            )

            if not upload_result.get('success'):
                return upload_result

            file_id = upload_result['file_id']

            # 获取文件信息（包含提取的内容）
            file_info = await self.get_file_info(file_id)

            return {
                "success": True,
                "file_id": file_id,
                "processing_type": processing_type,
                "file_info": file_info,
                "timestamp": datetime.now().isoformat(),
            }

        except Exception as error:
            self.logger.error(f"File processing error: {error}")
            return await self._handle_error(error)

    async def get_file_info(self, file_id: str) -> dict[str, Any]:
        """
        获取文件信息

        Args:
            file_id: 文件ID

        Returns:
            文件信息
        """
        try:
            await self.initialize()

            url = f"{self.config.service_url}{self.api_prefix}/{file_id}"
            self.logger.info(f"Getting file info: {file_id}")

            async with self.session.get(url) as response:
                response_data = await response.json()

                if response.status == 200:
                    return response_data
                else:
                    return await self._handle_error(
                        Exception(f"Get file info failed: {response.status}")
                    )

        except Exception as error:
            self.logger.error(f"Get file info error: {error}")
            return await self._handle_error(error)

    async def list_files(
        self,
        file_type: str | None = None,
        limit: int = 20,
        offset: int = 0
    ) -> dict[str, Any]:
        """
        列出文件

        Args:
            file_type: 文件类型过滤
            limit: 返回数量限制
            offset: 偏移量

        Returns:
            文件列表
        """
        try:
            await self.initialize()

            params = {}
            if file_type:
                params['file_type'] = file_type
            params['limit'] = limit
            params['offset'] = offset

            url = f"{self.config.service_url}{self.api_prefix}/list"

            async with self.session.get(url, params=params) as response:
                response_data = await response.json()

                if response.status == 200:
                    return response_data
                else:
                    return await self._handle_error(
                        Exception(f"List files failed: {response.status}")
                    )

        except Exception as error:
            self.logger.error(f"List files error: {error}")
            return await self._handle_error(error)

    async def download_file(self, file_id: str, save_path: str | None = None) -> dict[str, Any]:
        """
        下载文件

        Args:
            file_id: 文件ID
            save_path: 保存路径（可选）

        Returns:
            下载结果
        """
        try:
            await self.initialize()

            url = f"{self.config.service_url}{self.api_prefix}/{file_id}/download"

            async with self.session.get(url) as response:
                if response.status == 200:
                    content = await response.read()

                    if save_path:
                        # 保存到文件
                        Path(save_path).parent.mkdir(parents=True, exist_ok=True)
                        with open(save_path, 'wb') as f:
                            f.write(content)

                        self.logger.info(f"File downloaded to: {save_path}")
                        return {
                            "success": True,
                            "file_id": file_id,
                            "save_path": save_path,
                            "size": len(content)
                        }
                    else:
                        # 返回二进制内容
                        return {
                            "success": True,
                            "file_id": file_id,
                            "content": content,
                            "size": len(content)
                        }
                else:
                    return await self._handle_error(
                        Exception(f"Download failed: {response.status}")
                    )

        except Exception as error:
            self.logger.error(f"Download error: {error}")
            return await self._handle_error(error)

    async def delete_file(self, file_id: str) -> dict[str, Any]:
        """
        删除文件

        Args:
            file_id: 文件ID

        Returns:
            删除结果
        """
        try:
            await self.initialize()

            url = f"{self.config.service_url}{self.api_prefix}/{file_id}"

            async with self.session.delete(url) as response:
                response_data = await response.json()

                if response.status == 200:
                    self.logger.info(f"File deleted: {file_id}")
                    return response_data
                else:
                    return await self._handle_error(
                        Exception(f"Delete failed: {response.status}")
                    )

        except Exception as error:
            self.logger.error(f"Delete error: {error}")
            return await self._handle_error(error)

    async def get_statistics(self) -> dict[str, Any]:
        """
        获取统计信息

        Returns:
            统计信息
        """
        try:
            await self.initialize()

            url = f"{self.config.service_url}/api/stats"

            async with self.session.get(url) as response:
                response_data = await response.json()

                if response.status == 200:
                    return response_data
                else:
                    return await self._handle_error(
                        Exception(f"Get statistics failed: {response.status}")
                    )

        except Exception as error:
            self.logger.error(f"Get statistics error: {error}")
            return await self._handle_error(error)

    async def extract_text_from_pdf(self, file_path: str) -> dict[str, Any]:
        """
        从PDF文件提取文本

        Args:
            file_path: PDF文件路径

        Returns:
            提取结果
        """
        try:
            await self.initialize()

            # 读取PDF文件
            with open(file_path, 'rb') as f:
                file_content = f.read()
            filename = Path(file_path).name

            # 上传文件
            upload_result = await self.upload_file(
                file_content=file_content,
                filename=filename,
                mime_type="application/pdf",
                tags=["pdf", "text-extraction"],
                category="document"
            )

            if not upload_result.get('success'):
                return upload_result

            # 获取文件信息（包含提取的文本）
            file_info = await self.get_file_info(upload_result['file_id'])

            return {
                "success": True,
                "file_id": upload_result['file_id'],
                "text_content": file_info.get('extracted_text', ''),
                "metadata": file_info.get('metadata', {}),
                "timestamp": datetime.now().isoformat(),
            }

        except Exception as error:
            self.logger.error(f"PDF text extraction error: {error}")
            return await self._handle_error(error)

    async def extract_text_from_docx(self, file_path: str) -> dict[str, Any]:
        """
        从DOCX文件提取文本

        Args:
            file_path: DOCX文件路径

        Returns:
            提取结果
        """
        try:
            await self.initialize()

            with open(file_path, 'rb') as f:
                file_content = f.read()
            filename = Path(file_path).name

            upload_result = await self.upload_file(
                file_content=file_content,
                filename=filename,
                mime_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                tags=["docx", "text-extraction"],
                category="document"
            )

            if not upload_result.get('success'):
                return upload_result

            file_info = await self.get_file_info(upload_result['file_id'])

            return {
                "success": True,
                "file_id": upload_result['file_id'],
                "text_content": file_info.get('extracted_text', ''),
                "metadata": file_info.get('metadata', {}),
                "timestamp": datetime.now().isoformat(),
            }

        except Exception as error:
            self.logger.error(f"DOCX text extraction error: {error}")
            return await self._handle_error(error)

    async def extract_text_from_image(
        self,
        file_path: str,
        use_ocr: bool = True
    ) -> dict[str, Any]:
        """
        从图片提取文本（OCR）

        Args:
            file_path: 图片文件路径
            use_ocr: 是否使用OCR

        Returns:
            提取结果
        """
        try:
            await self.initialize()

            with open(file_path, 'rb') as f:
                file_content = f.read()
            filename = Path(file_path).name

            mime_type = "image/png"
            if filename.endswith('.jpg') or filename.endswith('.jpeg'):
                mime_type = "image/jpeg"
            elif filename.endswith('.gif'):
                mime_type = "image/gif"
            elif filename.endswith('.bmp'):
                mime_type = "image/bmp"
            elif filename.endswith('.webp'):
                mime_type = "image/webp"

            upload_result = await self.upload_file(
                file_content=file_content,
                filename=filename,
                mime_type=mime_type,
                tags=["image", "ocr", "text-extraction"] if use_ocr else ["image"],
                category="image"
            )

            if not upload_result.get('success'):
                return upload_result

            file_info = await self.get_file_info(upload_result['file_id'])

            # 图片OCR处理可能需要更长时间
            # 这里返回基本信息，实际OCR处理是异步的
            return {
                "success": True,
                "file_id": upload_result['file_id'],
                "ocr_enabled": use_ocr,
                "text_content": file_info.get('extracted_text', ''),
                "metadata": file_info.get('metadata', {}),
                "timestamp": datetime.now().isoformat(),
            }

        except Exception as error:
            self.logger.error(f"Image OCR error: {error}")
            return await self._handle_error(error)

    def _get_mime_type(self, file_path: str) -> str:
        """根据文件扩展名获取MIME类型"""
        ext = Path(file_path).suffix.lower()
        mime_map = {
            '.pdf': 'application/pdf',
            '.doc': 'application/msword',
            '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            '.txt': 'text/plain',
            '.md': 'text/markdown',
            '.json': 'application/json',
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.png': 'image/png',
            '.gif': 'image/gif',
            '.bmp': 'image/bmp',
            '.webp': 'image/webp',
            '.tiff': 'image/tiff',
            '.svg': 'image/svg+xml',
            '.mp3': 'audio/mpeg',
            '.wav': 'audio/wav',
            '.mp4': 'video/mp4',
            '.zip': 'application/zip',
            '.csv': 'text/csv',
            '.xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        }
        return mime_map.get(ext, 'application/octet-stream')

    async def batch_process_files(
        self,
        file_paths: list[str],
        processing_type: str = "extract"
    ) -> dict[str, Any]:
        """
        批量处理文件

        Args:
            file_paths: 文件路径列表
            processing_type: 处理类型

        Returns:
            批量处理结果
        """
        results = []
        success_count = 0
        failed_count = 0

        for file_path in file_paths:
            try:
                result = await self.process_file(file_path, processing_type)
                results.append({
                    "file_path": file_path,
                    "result": result
                })
                if result.get('success'):
                    success_count += 1
                else:
                    failed_count += 1
            except Exception as error:
                self.logger.error(f"Batch process error for {file_path}: {error}")
                results.append({
                    "file_path": file_path,
                    "result": {"success": False, "error": str(error)}
                })
                failed_count += 1

        return {
            "success": True,
            "total_files": len(file_paths),
            "success_count": success_count,
            "failed_count": failed_count,
            "results": results,
            "timestamp": datetime.now().isoformat(),
        }


# 注册适配器到工厂
from patent_search_adapter import AdapterFactory

AdapterFactory.register("multimodal-fileservice", MultimodalAdapter)


# 使用示例
async def main():
    """测试多模态适配器"""
    config = AdapterConfig(
        service_url="http://localhost:8021",
        health_threshold=5000,
        timeout=60000,  # 60秒 - 文件处理可能需要更长时间
        retry_attempts=3,
        debug_mode=True
    )

    adapter = MultimodalAdapter(config)
    await adapter.initialize()

    try:
        # 健康检查
        health = await adapter.health_check()
        print(f"Health status: {health}")

        # 获取统计信息
        stats = await adapter.get_statistics()
        print(f"Statistics: {json.dumps(stats, indent=2, ensure_ascii=False)}")

        # 上传文件测试
        test_content = b"Test document content\nThis is a test."
        upload_result = await adapter.upload_file(
            file_content=test_content,
            filename="test.txt",
            mime_type="text/plain",
            tags=["test"],
            category="test"
        )
        print(f"Upload result: {json.dumps(upload_result, indent=2, ensure_ascii=False)}")

        # 获取文件列表
        files = await adapter.list_files(limit=5)
        print(f"Files: {json.dumps(files, indent=2, ensure_ascii=False)}")

    finally:
        await adapter.cleanup()


if __name__ == "__main__":
    asyncio.run(main())
