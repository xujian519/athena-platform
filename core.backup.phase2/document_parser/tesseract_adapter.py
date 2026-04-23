#!/usr/bin/env python3
from __future__ import annotations
"""
Tesseract文档解析适配器
Tesseract Document Parser Adapter

自包含的Tesseract调用，不依赖core.perception模块。
直接通过subprocess调用tesseract二进制文件完成OCR。
作者: Athena平台团队
"""

import asyncio
import logging
import os
import subprocess
import tempfile
import time
from typing import Any

from core.document_parser.base import BaseDocumentParser, ParseRequest, ParseResult, ParserBackend

logger = logging.getLogger(__name__)

# 支持的图片扩展名
_IMAGE_EXTENSIONS = frozenset({".png", ".jpg", ".jpeg", ".tiff", ".bmp", ".gif", ".webp"})

# 语言代码到tesseract -l 参数的映射
_LANG_TO_TESSERACT = {
    "chinese": "chi_sim+eng",
    "english": "eng",
    "mixed": "chi_sim+eng",
    "traditional": "chi_tra+eng",
}


class TesseractAdapter(BaseDocumentParser):
    """
    Tesseract文档解析适配器

    自包含实现，直接调用tesseract二进制文件。
    PDF先通过pdftoppm转图片再OCR处理。
    """

    def __init__(self, dpi: int = 300, language: str = "chinese"):
        super().__init__(ParserBackend.TESSERACT)
        self.dpi = max(72, min(dpi, 600))  # DPI范围限制
        self.default_language = language
        self._tesseract_path: str | None = None
        self._is_available: bool = False

        # 统计信息
        self._total_requests: int = 0
        self._total_failures: int = 0

    async def initialize(self) -> bool:
        """初始化Tesseract适配器，查找并验证tesseract二进制"""
        self._tesseract_path = self._find_tesseract()
        self._is_available = self._check_tesseract_available()
        self._initialized = True
        logger.info("Tesseract适配器初始化: available=%s, path=%s", self._is_available, self._tesseract_path)
        return self._is_available

    async def health_check(self) -> bool:
        """检查Tesseract可用性"""
        self._is_available = self._check_tesseract_available()
        return self._is_available

    async def parse(self, request: ParseRequest) -> ParseResult:
        """解析文档，支持PDF和图片"""
        start_time = time.time()
        self._total_requests += 1

        # 文件校验
        if not os.path.isfile(request.file_path):
            return ParseResult(
                error=f"文件不存在: {request.file_path}",
                backend_used="tesseract",
                processing_time=time.time() - start_time,
            )

        # 未初始化检查
        if not self._initialized:
            return ParseResult(
                error="Tesseract适配器未初始化",
                backend_used="tesseract",
                processing_time=time.time() - start_time,
            )

        # tesseract不可用
        if not self._is_available:
            return ParseResult(
                error="Tesseract二进制不可用，请安装tesseract-ocr",
                backend_used="tesseract",
                processing_time=time.time() - start_time,
            )

        ext = os.path.splitext(request.file_path)[1].lower()

        try:
            if ext == ".pdf":
                result = await self._parse_pdf(request)
            elif ext in _IMAGE_EXTENSIONS:
                result = await self._parse_image(request)
            else:
                return ParseResult(
                    error=f"不支持的文件格式: {ext}",
                    backend_used="tesseract",
                    processing_time=time.time() - start_time,
                )

            result.processing_time = time.time() - start_time
            result.backend_used = "tesseract"
            return result

        except Exception as e:
            self._total_failures += 1
            logger.warning("Tesseract解析失败: %s", e)
            return ParseResult(
                error=str(e),
                backend_used="tesseract",
                processing_time=time.time() - start_time,
            )

    # ------------------------------------------------------------------
    # 核心OCR调用（内联实现，无外部依赖）
    # ------------------------------------------------------------------

    def _run_tesseract(self, input_file: str, lang_code: str) -> str:
        """
        直接调用tesseract二进制，返回识别文本。

        Args:
            input_file: 图片文件路径
            lang_code: tesseract语言代码，如 chi_sim+eng

        Returns:
            OCR识别出的文本

        Raises:
            RuntimeError: tesseract调用失败
            FileNotFoundError: tesseract二进制不存在
        """
        if not self._tesseract_path:
            raise FileNotFoundError("tesseract二进制未找到")

        cmd = [
            self._tesseract_path,
            input_file,
            "stdout",   # 输出到stdout
            "-l", lang_code,
            "--oem", "1",  # LSTM神经网络引擎
            "--psm", "6",  # 假设单列文本块
        ]

        logger.debug("执行tesseract命令: %s", " ".join(cmd))

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=30,
        )

        if result.returncode != 0:
            stderr_msg = result.stderr.strip() if result.stderr else "未知错误"
            raise RuntimeError(f"tesseract调用失败(returncode={result.returncode}): {stderr_msg}")

        return result.stdout.strip()

    async def _parse_image(self, request: ParseRequest) -> ParseResult:
        """直接OCR图片文件"""
        lang_code = self._to_tesseract_lang(request.language)
        loop = asyncio.get_running_loop()

        text = await loop.run_in_executor(
            None,
            self._run_tesseract,
            request.file_path,
            lang_code,
        )

        confidence = self._estimate_confidence(text)

        return ParseResult(
            content=text,
            confidence=confidence,
            backend_used="tesseract",
            page_count=1,
        )

    async def _parse_pdf(self, request: ParseRequest) -> ParseResult:
        """PDF转图片后OCR处理"""
        # 检查pdftoppm可用性
        pdftoppm_path = self._find_pdftoppm()
        if not pdftoppm_path:
            return ParseResult(
                error="pdftoppm不可用，无法将PDF转为图片",
                backend_used="tesseract",
            )

        lang_code = self._to_tesseract_lang(request.language)
        loop = asyncio.get_running_loop()

        with tempfile.TemporaryDirectory(prefix="athena_tesseract_") as tmp_dir:
            # PDF转图片
            image_paths = await self._pdf_to_images(request.file_path, tmp_dir, pdftoppm_path)
            if not image_paths:
                return ParseResult(
                    error="PDF转图片失败",
                    backend_used="tesseract",
                )

            # 逐页OCR
            all_text_parts: list[str] = []
            total_confidence = 0.0

            for img_path in image_paths:
                try:
                    text = await loop.run_in_executor(
                        None,
                        self._run_tesseract,
                        img_path,
                        lang_code,
                    )
                    if text:
                        all_text_parts.append(text)
                    total_confidence += self._estimate_confidence(text)
                except Exception as e:
                    logger.warning("页面OCR失败 %s: %s", img_path, e)
                    all_text_parts.append(f"[OCR失败: {e}]")

            avg_confidence = total_confidence / len(image_paths) if image_paths else 0.0
            full_text = "\n\n".join(all_text_parts)

            return ParseResult(
                content=full_text,
                confidence=avg_confidence,
                backend_used="tesseract",
                page_count=len(image_paths),
            )

    # ------------------------------------------------------------------
    # 工具方法
    # ------------------------------------------------------------------

    async def _pdf_to_images(
        self, pdf_path: str, output_dir: str, pdftoppm_path: str
    ) -> list[str]:
        """使用pdftoppm将PDF转换为图片"""
        loop = asyncio.get_running_loop()

        def _convert():
            output_prefix = os.path.join(output_dir, "page")
            try:
                result = subprocess.run(
                    [pdftoppm_path, "-png", "-r", str(self.dpi), pdf_path, output_prefix],
                    capture_output=True,
                    text=True,
                    timeout=120,
                )
                if result.returncode != 0:
                    logger.warning("pdftoppm失败: %s", result.stderr)
                    return []
            except subprocess.TimeoutExpired:
                logger.warning("pdftoppm超时(120s)")
                return []
            except Exception as e:
                logger.warning("pdftoppm异常: %s", e)
                return []

            # 收集生成的图片
            images = []
            for f in sorted(os.listdir(output_dir)):
                if f.endswith(".png"):
                    images.append(os.path.join(output_dir, f))
            return images

        return await loop.run_in_executor(None, _convert)

    @staticmethod
    def _find_tesseract() -> str | None:
        """查找tesseract可执行文件"""
        try:
            result = subprocess.run(
                ["which", "tesseract"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            if result.returncode == 0:
                return result.stdout.strip()
        except Exception:
            pass

        # 常见安装路径
        for path in [
            "/usr/bin/tesseract",
            "/usr/local/bin/tesseract",
            "/opt/homebrew/bin/tesseract",
        ]:
            if os.path.exists(path):
                return path
        return None

    def _check_tesseract_available(self) -> bool:
        """检查tesseract是否可用"""
        if not self._tesseract_path:
            return False
        try:
            result = subprocess.run(
                [self._tesseract_path, "--version"],
                capture_output=True,
                timeout=5,
            )
            return result.returncode == 0
        except Exception:
            return False

    @staticmethod
    def _find_pdftoppm() -> str | None:
        """查找pdftoppm可执行文件"""
        try:
            result = subprocess.run(["which", "pdftoppm"], capture_output=True, text=True)
            if result.returncode == 0:
                return result.stdout.strip()
        except Exception:
            pass

        for path in ["/usr/bin/pdftoppm", "/usr/local/bin/pdftoppm", "/opt/homebrew/bin/pdftoppm"]:
            if os.path.exists(path):
                return path
        return None

    @staticmethod
    def _to_tesseract_lang(lang: str) -> str:
        """将语言代码映射为tesseract -l 参数值"""
        # 先做一层语义映射（ch/zh/cn -> chinese等）
        semantic = {
            "ch": "chinese",
            "zh": "chinese",
            "cn": "chinese",
            "en": "english",
        }.get((lang or "ch").lower(), lang or "chinese")

        # 再映射为tesseract -l 参数
        return _LANG_TO_TESSERACT.get(semantic, "chi_sim+eng")

    @staticmethod
    def _estimate_confidence(text: str) -> float:
        """基于输出文本质量估算置信度"""
        if not text:
            return 0.0

        score = 0.95

        # 文本过短则降低置信度
        if len(text) < 10:
            score -= 0.1

        # 中文字符比例
        chinese_chars = sum(1 for c in text if "\u4e00" <= c <= "\u9fff")
        if chinese_chars > 0:
            score -= 0.05

        # 英文字符
        has_english = any(c.isalpha() and ord(c) < 128 for c in text)
        if has_english:
            score -= 0.02

        return max(0.0, min(1.0, score))

    def get_stats(self) -> dict[str, Any]:
        """获取统计信息"""
        return {
            "backend": "tesseract",
            "available": self._is_available,
            "initialized": self._initialized,
            "total_requests": self._total_requests,
            "total_failures": self._total_failures,
            "dpi": self.dpi,
            "tesseract_path": self._tesseract_path,
        }

    @property
    def is_available(self) -> bool:
        return self._is_available
