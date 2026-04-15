#!/usr/bin/env python3
"""
多模态文件系统真实客户端

连接到现有的多模态文件系统服务
"""

from __future__ import annotations
import asyncio
import logging
from pathlib import Path
from typing import Any

import aiofiles
import aiohttp

from .multimodal_integration import (
    DocumentParseResult,
    MediaContent,
    MediaType,
    MockMultimodalProcessor,
    MultimodalProcessor,
    MultimodalUnderstanding,
    OCRResult,
)

logger = logging.getLogger(__name__)


class RealMultimodalProcessor(MultimodalProcessor):
    """
    真实多模态处理器

    连接到本地的多模态文件系统服务API
    默认地址: http://localhost:8200 (多模态服务端口)
    """

    def __init__(
        self,
        base_url: str = "http://localhost:8200",
        timeout: float = 60.0,
        retry_attempts: int = 3,
    ):
        """
        初始化真实多模态处理器

        Args:
            base_url: 多模态服务的基础URL
            timeout: 请求超时时间(秒)
            retry_attempts: 失败重试次数
        """
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.retry_attempts = retry_attempts
        self._session: aiohttp.ClientSession | None = None

    async def _get_session(self) -> aiohttp.ClientSession:
        """获取或创建aiohttp会话"""
        if self._session is None or self._session.closed:
            timeout = aiohttp.ClientTimeout(total=self.timeout)
            self._session = aiohttp.ClientSession(timeout=timeout)
        return self._session

    async def close(self):
        """关闭客户端连接"""
        if self._session and not self._session.closed:
            await self._session.close()

    async def _request(self, method: str, endpoint: str, **kwargs: Any) -> dict[str, Any]:
        """
        发送HTTP请求到多模态服务

        Args:
            method: HTTP方法
            endpoint: API端点
            **kwargs: 额外参数

        Returns:
            响应数据字典
        """
        session = await self._get_session()
        url = f"{self.base_url}{endpoint}"

        for attempt in range(self.retry_attempts):
            try:
                async with session.request(method, url, **kwargs) as response:
                    response.raise_for_status()
                    return await response.json()

            except aiohttp.ClientError as e:
                logger.warning(f"请求失败 (尝试 {attempt + 1}/{self.retry_attempts}): {e}")
                if attempt == self.retry_attempts - 1:
                    raise
                await asyncio.sleep(1 * (attempt + 1))

        return {}

    async def process_image(self, image_data: str | bytes, ocr: bool = True) -> OCRResult:
        """
        处理图片 - OCR识别

        Args:
            image_data: 图片路径或二进制数据
            ocr: 是否进行OCR识别

        Returns:
            OCR识别结果
        """
        try:
            # 准备图片数据
            if isinstance(image_data, str):
                # 文件路径
                file_path = Path(image_data)
                if not file_path.exists():
                    raise FileNotFoundError(f"图片文件不存在: {image_data}")

                async with aiofiles.open(file_path, "rb") as f:
                    image_bytes = await f.read()

                file_name = file_path.name
            else:
                # 二进制数据
                image_bytes = image_data
                file_name = "image.png"

            # 上传文件进行处理
            data = aiohttp.FormData()
            data.add_field("file", image_bytes, filename=file_name, content_type="image/png")
            data.add_field("ocr", "true" if ocr else "false")

            result = await self._request("POST", "/api/v1/process/image", data=data)

            # 转换响应为OCRResult
            return OCRResult(
                success=result.get("success", True),
                text=result.get("text", ""),
                confidence=result.get("confidence", 0.0),
                regions=result.get("regions", []),
                language=result.get("language", "unknown"),
                processing_time=result.get("processing_time", 0.0),
            )

        except Exception as e:
            logger.error(f"处理图片失败: {e}")
            return OCRResult(success=False, text="", confidence=0.0, error=str(e))

    async def parse_document(self, file_path: str) -> DocumentParseResult:
        """
        解析文档

        Args:
            file_path: 文档文件路径

        Returns:
            文档解析结果
        """
        try:
            file_path_obj = Path(file_path)
            if not file_path_obj.exists():
                raise FileNotFoundError(f"文档文件不存在: {file_path}")

            # 读取文件内容
            async with aiofiles.open(file_path_obj, "rb") as f:
                file_bytes = await f.read()

            # 上传文件进行解析
            data = aiohttp.FormData()
            data.add_field(
                "file",
                file_bytes,
                filename=file_path_obj.name,
                content_type="application/octet-stream",
            )

            result = await self._request("POST", "/api/v1/process/document", data=data)

            # 转换响应为DocumentParseResult
            return DocumentParseResult(
                success=result.get("success", True),
                content=result.get("content", ""),
                metadata=result.get("metadata", {}),
                page_count=result.get("page_count", 0),
                sections=result.get("sections", []),
                tables=result.get("tables", []),
                images=result.get("images", []),
                processing_time=result.get("processing_time", 0.0),
            )

        except Exception as e:
            logger.error(f"解析文档失败: {e}")
            return DocumentParseResult(success=False, content="", error=str(e))

    async def understand_multimodal(self, inputs: list[MediaContent]) -> MultimodalUnderstanding:
        """
        多模态融合理解

        Args:
            inputs: 媒体内容列表

        Returns:
            多模态理解结果
        """
        try:
            # 准备多模态输入
            payload = {"contents": [], "text_input": ""}

            for item in inputs:
                if item.media_type == MediaType.TEXT:
                    payload["text_input"] += item.content + "\n"
                elif item.media_type in [MediaType.IMAGE, MediaType.DOCUMENT]:
                    # 对于文件类型,需要先上传
                    if isinstance(item.content, str) and Path(item.content).exists():
                        # 上传文件并获取URL
                        async with aiofiles.open(item.content, "rb") as f:
                            file_bytes = await f.read()

                        data = aiohttp.FormData()
                        data.add_field("file", file_bytes, filename=Path(item.content).name)

                        upload_result = await self._request(
                            "POST", "/api/v1/files/upload", data=data
                        )

                        payload["contents"].append(
                            {
                                "type": item.media_type.value,
                                "url": upload_result.get("url", ""),
                                "metadata": item.metadata,
                            }
                        )
                    else:
                        payload["contents"].append(
                            {
                                "type": item.media_type.value,
                                "content": str(item.content),
                                "metadata": item.metadata,
                            }
                        )

            # 发送理解请求
            result = await self._request("POST", "/api/v1/understand/multimodal", json=payload)

            # 转换响应为MultimodalUnderstanding
            return MultimodalUnderstanding(
                success=result.get("success", True),
                primary_content=result.get("primary_content", ""),
                summary=result.get("summary", ""),
                insights=result.get("insights", []),
                entities=result.get("entities", []),
                relationships=result.get("relationships", []),
                confidence=result.get("confidence", 0.0),
                processing_time=result.get("processing_time", 0.0),
            )

        except Exception as e:
            logger.error(f"多模态理解失败: {e}")
            return MultimodalUnderstanding(success=False, primary_content="", error=str(e))

    async def batch_process(
        self, file_paths: list[str], concurrency: int = 5
    ) -> list[OCRResult | DocumentParseResult]:
        """
        批量处理文件

        Args:
            file_paths: 文件路径列表
            concurrency: 并发数

        Returns:
            处理结果列表
        """
        semaphore = asyncio.Semaphore(concurrency)

        async def process_one(file_path: str):
            async with semaphore:
                file_path_obj = Path(file_path)
                suffix = file_path_obj.suffix.lower()

                if suffix in [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp"]:
                    return await self.process_image(file_path, ocr=True)
                else:
                    return await self.parse_document(file_path)

        tasks = [process_one(fp) for fp in file_paths]
        return await asyncio.gather(*tasks)

    async def health_check(self) -> bool:
        """
        健康检查

        Returns:
            服务是否可用
        """
        try:
            data = await self._request("GET", "/health")
            return data.get("status") == "healthy"
        except Exception as e:
            logger.debug(f"空except块已触发: {e}")
            return False


# 工厂函数
def create_multimodal_processor(processor_type: str = "real", **kwargs: Any) -> MultimodalProcessor:
    """
    创建多模态处理器

    Args:
        processor_type: 处理器类型 ("real" 或 "mock")
        **kwargs: 处理器配置参数

    Returns:
        多模态处理器实例
    """
    if processor_type == "real":
        return RealMultimodalProcessor(**kwargs)
    else:
        return MockMultimodalProcessor(**kwargs)


# 导出
__all__ = [
    "RealMultimodalProcessor",
    "create_multimodal_processor",
]
