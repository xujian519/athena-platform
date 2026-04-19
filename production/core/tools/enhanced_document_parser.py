#!/usr/bin/env python3
"""
Athena增强文档解析器 - 集成minerU OCR

支持多种文档格式，包括OCR图像识别功能

作者: Athena平台团队
创建时间: 2026-04-19
版本: v2.0.0 - OCR增强版
"""

import asyncio
import base64
import logging
import mimetypes
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

import aiohttp
from aiohttp import ClientTimeout

from core.logging_config import setup_logging

logger = setup_logging()


# ========================================
# OCR配置
# ========================================

MINERU_API_URL = os.getenv("MINERU_API_URL", "http://localhost:7860")
MINERU_TIMEOUT = int(os.getenv("MINERU_TIMEOUT", "120"))  # OCR可能需要较长时间


# ========================================
# 增强文档解析器
# ========================================

class EnhancedDocumentParser:
    """增强文档解析器 - 支持OCR"""

    def __init__(self, mineru_url: str = MINERU_API_URL):
        """
        初始化解析器

        Args:
            mineru_url: minerU服务URL
        """
        self.mineru_url = mineru_url.rstrip("/")
        self.session: Optional[aiohttp.ClientSession] = None

    async def _get_session(self) -> aiohttp.ClientSession:
        """获取或创建HTTP会话"""
        if self.session is None or self.session.closed:
            timeout = ClientTimeout(total=MINERU_TIMEOUT)
            headers = {
                "User-Agent": "Athena-Document-Parser/2.0"
            }
            self.session = aiohttp.ClientSession(timeout=timeout, headers=headers)
        return self.session

    def _encode_image_to_base64(self, image_path: Path) -> str:
        """
        将图片编码为base64

        Args:
            image_path: 图片路径

        Returns:
            base64编码的字符串
        """
        with open(image_path, "rb") as f:
            return base64.b64encode(f.read()).decode('utf-8')

    async def check_mineru_health(self) -> bool:
        """
        检查minerU服务健康状态

        Returns:
            服务是否可用
        """
        try:
            session = await self._get_session()
            async with session.get(f"{self.mineru_url}/health", timeout=5) as response:
                return response.status == 200
        except Exception as e:
            logger.warning(f"minerU服务不可用: {e}")
            return False

    async def parse_with_mineru_ocr(
        self,
        file_path: str,
        extract_images: bool = True,
        extract_tables: bool = True
    ) -> dict[str, Any]:
        """
        使用minerU OCR解析文档

        Args:
            file_path: 文件路径
            extract_images: 是否提取图片
            extract_tables: 是否提取表格

        Returns:
            解析结果
        """
        path = Path(file_path)

        if not path.exists():
            return {
                "success": False,
                "error": f"文件不存在: {file_path}"
            }

        # 检查文件大小（minerU限制）
        file_size_mb = path.stat().st_size / (1024 * 1024)
        if file_size_mb > 50:  # 50MB限制
            return {
                "success": False,
                "error": f"文件过大 ({file_size_mb:.1f}MB)，minerU限制50MB"
            }

        try:
            session = await self._get_session()

            # 准备请求数据
            # 对于PDF，直接发送文件路径（如果minerU在本地）
            # 对于图片，发送base64编码
            is_image = path.suffix.lower() in ['.png', '.jpg', '.jpeg', '.bmp', '.tiff', '.gif']

            if is_image:
                # 图片文件：转换为base64
                image_base64 = self._encode_image_to_base64(path)
                payload = {
                    "file": f"data:image/{path.suffix[1:]};base64,{image_base64}",
                    "extract_images": extract_images,
                    "extract_tables": extract_tables,
                }
            else:
                # PDF等文档：发送文件路径（本地文件）
                payload = {
                    "file": str(path),
                    "extract_images": extract_images,
                    "extract_tables": extract_tables,
                }

            logger.info(f"📄 调用minerU OCR: {path.name} ({file_size_mb:.1f}MB)")

            # 调用minerU API
            async with session.post(
                f"{self.mineru_url}/api/v1/general",
                json=payload
            ) as response:
                if response.status == 200:
                    data = await response.json()

                    # 解析minerU返回的结果
                    return {
                        "success": True,
                        "method": "mineru_ocr",
                        "content": data.get("content", ""),
                        "markdown": data.get("markdown", ""),
                        "images": data.get("images", []),
                        "tables": data.get("tables", []),
                        "pages": data.get("pages", 0),
                        "metadata": {
                            "engine": "minerU",
                            "file_size_mb": file_size_mb,
                            "processing_time": data.get("processing_time", 0),
                            "ocr_confidence": data.get("confidence", 0),
                        }
                    }
                else:
                    error_text = await response.text()
                    logger.error(f"minerU API错误 {response.status}: {error_text}")
                    return {
                        "success": False,
                        "error": f"minerU API返回错误: {response.status}",
                        "details": error_text[:200]
                    }

        except asyncio.TimeoutError:
            return {
                "success": False,
                "error": f"OCR处理超时（>{MINERU_TIMEOUT}秒），文件可能过大"
            }
        except Exception as e:
            logger.error(f"minerU OCR失败: {e}")
            return {
                "success": False,
                "error": f"OCR处理失败: {str(e)}"
            }

    async def parse_text_file(self, file_path: str, max_length: int = 10000) -> dict[str, Any]:
        """
        解析纯文本文件

        Args:
            file_path: 文件路径
            max_length: 最大内容长度

        Returns:
            解析结果
        """
        path = Path(file_path)

        try:
            content = path.read_text(encoding="utf-8", errors="ignore")

            return {
                "success": True,
                "method": "text_parser",
                "content": content[:max_length] if len(content) > max_length else content,
                "content_truncated": len(content) > max_length,
                "metadata": {
                    "type": "text",
                    "encoding": "utf-8",
                    "line_count": len(content.split("\n")),
                    "char_count": len(content),
                    "word_count": len(content.split()),
                }
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"文本文件解析失败: {str(e)}"
            }

    async def parse(
        self,
        file_path: str,
        use_ocr: bool = True,
        extract_images: bool = True,
        extract_tables: bool = True,
        max_length: int = 50000
    ) -> dict[str, Any]:
        """
        智能解析文档（自动选择最佳方法）

        Args:
            file_path: 文件路径
            use_ocr: 是否使用OCR
            extract_images: 是否提取图片
            extract_tables: 是否提取表格
            max_length: 最大内容长度

        Returns:
            解析结果
        """
        path = Path(file_path)

        if not path.exists():
            return {
                "success": False,
                "error": f"文件不存在: {file_path}"
            }

        # 获取文件信息
        file_stat = path.stat()
        file_info = {
            "name": path.name,
            "size": file_stat.st_size,
            "size_mb": round(file_stat.st_size / (1024 * 1024), 2),
            "extension": path.suffix,
            "modified": datetime.fromtimestamp(file_stat.st_mtime).isoformat(),
        }

        # 识别MIME类型
        mime_type, _ = mimetypes.guess_type(file_path)
        file_info["mime_type"] = mime_type

        logger.info(f"📄 解析文档: {path.name} ({file_info['extension']})")

        # 根据文件类型选择解析方法
        extension = path.suffix.lower()

        # 文本文件 - 直接读取
        if extension in ['.txt', '.md', '.py', '.js', '.json', '.yaml', '.yml', '.xml', '.html', '.css', '.sh', '.csv']:
            result = await self.parse_text_file(file_path, max_length)

        # PDF或图片文件 - 使用OCR
        elif extension in ['.pdf', '.png', '.jpg', '.jpeg', '.bmp', '.tiff', '.gif']:
            if use_ocr:
                # 检查minerU是否可用
                mineru_available = await self.check_mineru_health()

                if mineru_available:
                    result = await self.parse_with_mineru_ocr(
                        file_path,
                        extract_images,
                        extract_tables
                    )
                else:
                    result = {
                        "success": False,
                        "error": "minerU服务不可用，无法进行OCR解析。请启动minerU服务。"
                    }
            else:
                result = {
                    "success": False,
                    "error": f"{extension}格式需要OCR支持，请设置use_ocr=True"
                }

        # Word文档
        elif extension in ['.docx', '.doc']:
            result = {
                "success": False,
                "error": "Word文档暂不支持（可通过minerU转换后处理）"
            }

        else:
            result = {
                "success": False,
                "error": f"暂不支持 {extension} 格式"
            }

        # 添加文件信息到结果
        if isinstance(result, dict):
            result["file_info"] = file_info

        return result

    async def close(self):
        """关闭会话"""
        if self.session and not self.session.closed:
            await self.session.close()


# ========================================
# 全局实例
# ========================================

_parser_instance: Optional[EnhancedDocumentParser] = None


async def get_document_parser() -> EnhancedDocumentParser:
    """获取文档解析器实例（单例）"""
    global _parser_instance
    if _parser_instance is None:
        _parser_instance = EnhancedDocumentParser()
    return _parser_instance


# ========================================
# 工具处理器
# ========================================

async def enhanced_document_parser_handler(
    params: dict[str, Any],
    context: dict[str, Any]
) -> dict[str, Any]:
    """
    增强文档解析处理器 - 支持OCR

    功能:
    1. 文本文件解析
    2. PDF OCR识别（通过minerU）
    3. 图片OCR识别（通过minerU）
    4. 表格提取
    5. 图片提取

    Args:
        params: {
            "file_path": str,           # 文件路径
            "use_ocr": bool,             # 是否使用OCR (默认True)
            "extract_images": bool,     # 是否提取图片 (默认True)
            "extract_tables": bool,     # 是否提取表格 (默认True)
            "max_length": int           # 最大内容长度 (默认50000)
        }
        context: 上下文信息

    Returns:
        解析结果
    """
    file_path = params.get("file_path", "")
    use_ocr = params.get("use_ocr", True)
    extract_images = params.get("extract_images", True)
    extract_tables = params.get("extract_tables", True)
    max_length = params.get("max_length", 50000)

    if not file_path:
        return {
            "success": False,
            "error": "缺少必需参数: file_path"
        }

    logger.info(f"📄 增强文档解析: {file_path}")

    try:
        parser = await get_document_parser()

        result = await parser.parse(
            file_path=file_path,
            use_ocr=use_ocr,
            extract_images=extract_images,
            extract_tables=extract_tables,
            max_length=max_length
        )

        if result.get("success"):
            logger.info(f"✅ 文档解析成功: {result.get('method', 'unknown')}")
        else:
            logger.warning(f"⚠️ 文档解析失败: {result.get('error', 'unknown')}")

        return result

    except Exception as e:
        logger.error(f"❌ 文档解析异常: {e}")
        return {
            "success": False,
            "error": f"文档解析异常: {str(e)}"
        }


# ========================================
# 便捷函数
# ========================================

async def parse_document(file_path: str, **kwargs) -> dict[str, Any]:
    """
    便捷函数：解析文档

    Args:
        file_path: 文件路径
        **kwargs: 其他参数

    Returns:
        解析结果
    """
    parser = await get_document_parser()
    return await parser.parse(file_path, **kwargs)


async def parse_pdf_with_ocr(file_path: str) -> dict[str, Any]:
    """
    便捷函数：解析PDF（使用OCR）

    Args:
        file_path: PDF文件路径

    Returns:
        解析结果
    """
    parser = await get_document_parser()
    return await parser.parse(
        file_path,
        use_ocr=True,
        extract_images=True,
        extract_tables=True
    )


async def parse_image_with_ocr(file_path: str) -> dict[str, Any]:
    """
    便捷函数：解析图片（使用OCR）

    Args:
        file_path: 图片文件路径

    Returns:
        解析结果
    """
    parser = await get_document_parser()
    return await parser.parse(
        file_path,
        use_ocr=True,
        extract_images=False,
        extract_tables=False
    )


__all__ = [
    "EnhancedDocumentParser",
    "enhanced_document_parser_handler",
    "get_document_parser",
    "parse_document",
    "parse_pdf_with_ocr",
    "parse_image_with_ocr",
]
