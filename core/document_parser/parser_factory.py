#!/usr/bin/env python3
from __future__ import annotations
"""
文档解析工厂
Document Parser Factory

三级降级策略: MinerU → PyMuPDF/pdfplumber → Tesseract
作者: Athena平台团队
"""

import asyncio
import logging
import os
import threading
import time
from typing import Any

from core.document_parser.base import BaseDocumentParser, ParseRequest, ParseResult, ParserBackend
from core.document_parser.mineru_adapter import MinerUAdapter
from core.document_parser.tesseract_adapter import TesseractAdapter

logger = logging.getLogger(__name__)

# 文本层提取的最低有效字符数阈值
_TEXT_LAYER_MIN_CHARS = 100

# 单例锁
_instance_lock = threading.Lock()


class DocumentParserFactory:
    """
    文档解析工厂 - 管理解析器实例和降级策略

    降级链:
    1. MinerU (优先): 高质量PDF/图片OCR和结构化解析
    2. PyMuPDF/pdfplumber (文本层提取): 有文本层的PDF直接提取
    3. Tesseract (兜底): 本地OCR引擎

    MinerU 失败后自动重新探测恢复。
    """

    _instance: DocumentParserFactory | None = None

    def __init__(self, config: dict[str, Any] | None = None):
        self._config = config or {}
        self._parsers: dict[ParserBackend, BaseDocumentParser] = {}
        self._initialized = False

        # 降级配置
        self._fallback_enabled = self._config.get("auto_fallback_enabled", True)

        # 状态追踪
        self._mineru_last_failure: float = 0.0
        self._mineru_recovery_interval: float = 60.0  # 失败后60秒重试MinerU

    @classmethod
    def get_instance(cls, config: dict[str, Any] | None = None) -> DocumentParserFactory:
        """获取单例实例（线程安全）"""
        if cls._instance is None:
            with _instance_lock:
                if cls._instance is None:
                    cls._instance = cls(config)
        elif config is not None:
            logger.warning("DocumentParserFactory单例已存在，忽略新config参数")
        return cls._instance

    @classmethod
    def reset_instance(cls):
        """重置单例（测试用）"""
        with _instance_lock:
            cls._instance = None

    async def initialize(self) -> bool:
        """初始化所有解析器"""
        if self._initialized:
            return True

        results: dict[str, bool] = {}

        # 初始化MinerU适配器
        try:
            mineru_config = self._config.get("mineru", {})
            mineru = MinerUAdapter(
                base_url=mineru_config.get("base_url", "http://127.0.0.1:7860"),
                parse_backend=mineru_config.get("backend", "pipeline"),
                parse_method=mineru_config.get("parse_method", "auto"),
                request_timeout=mineru_config.get("request_timeout", 300),
            )
            await mineru.initialize()
            self._parsers[ParserBackend.MINERU] = mineru
            results["mineru"] = mineru.is_available
        except Exception as e:
            logger.warning("MinerU初始化失败: %s", e)
            results["mineru"] = False

        # 初始化Tesseract适配器
        try:
            tesseract_config = self._config.get("tesseract", {})
            tesseract = TesseractAdapter(
                dpi=tesseract_config.get("dpi", 300),
                language=tesseract_config.get("language", "chinese"),
            )
            await tesseract.initialize()
            self._parsers[ParserBackend.TESSERACT] = tesseract
            results["tesseract"] = tesseract.is_available
        except Exception as e:
            logger.warning("Tesseract初始化失败: %s", e)
            results["tesseract"] = False

        self._initialized = True
        logger.info("文档解析工厂初始化完成: %s", results)
        return any(results.values())

    async def parse(self, request: ParseRequest) -> ParseResult:
        """
        解析文档，自动选择最优解析器

        降级策略:
        1. 有文本层的PDF → 尝试PyMuPDF直接提取
        2. MinerU可用 → 使用MinerU解析
        3. 以上失败 → 降级到Tesseract
        """
        start_time = time.time()

        if not self._initialized:
            await self.initialize()

        # Step 1: 尝试文本层直接提取（仅PDF）
        ext = os.path.splitext(request.file_path)[1].lower()
        if ext == ".pdf":
            text_result = await self._try_extract_text_layer(request)
            if text_result and len(text_result.strip()) > _TEXT_LAYER_MIN_CHARS:
                return ParseResult(
                    content=text_result.strip(),
                    backend_used="pymupdf",
                    confidence=0.99,
                    processing_time=time.time() - start_time,
                )

        # Step 2: 尝试MinerU
        mineru = self._parsers.get(ParserBackend.MINERU)
        if mineru and mineru.is_available:
            # 检查是否在恢复冷却期
            if time.time() - self._mineru_last_failure > self._mineru_recovery_interval:
                try:
                    result = await mineru.parse(request)
                    if not result.error:
                        result.processing_time = time.time() - start_time
                        return result
                    logger.info("MinerU解析失败，降级: %s", result.error)
                    self._mineru_last_failure = time.time()
                except Exception as e:
                    logger.warning("MinerU异常，降级: %s", e)
                    self._mineru_last_failure = time.time()

        # Step 3: 降级到Tesseract
        if self._fallback_enabled:
            tesseract = self._parsers.get(ParserBackend.TESSERACT)
            if tesseract and tesseract.is_available:
                logger.info("降级到Tesseract解析")
                result = await tesseract.parse(request)
                result.processing_time = time.time() - start_time
                return result

        # 所有解析器都不可用
        return ParseResult(
            error="所有文档解析器均不可用",
            backend_used="none",
            processing_time=time.time() - start_time,
        )

    async def _try_extract_text_layer(self, request: ParseRequest) -> str | None:
        """尝试用PyMuPDF直接提取PDF文本层（异步非阻塞）"""
        try:
            import fitz  # PyMuPDF
        except ImportError:
            return None

        def _extract() -> str | None:
            try:
                with fitz.open(request.file_path) as doc:
                    text_parts = []
                    for page in doc:
                        text = page.get_text("text")
                        if text.strip():
                            text_parts.append(text)
                    return "\n\n".join(text_parts) if text_parts else None
            except Exception as e:
                logger.debug("PyMuPDF文本提取失败: %s", e)
                return None

        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, _extract)

    def get_parser(self, backend: ParserBackend) -> BaseDocumentParser | None:
        """获取指定后端的解析器"""
        return self._parsers.get(backend)

    async def health_check_all(self) -> dict[str, bool]:
        """检查所有解析器健康状态"""
        results: dict[str, bool] = {}
        for backend, parser in self._parsers.items():
            try:
                results[backend.value] = await parser.health_check()
            except Exception:
                results[backend.value] = False
        return results

    def get_stats(self) -> dict[str, Any]:
        """获取所有解析器统计信息"""
        stats: dict[str, Any] = {"initialized": self._initialized, "parsers": {}}
        for backend, parser in self._parsers.items():
            stats["parsers"][backend.value] = parser.get_stats()
        return stats

    def is_initialized(self) -> bool:
        """是否已初始化"""
        return self._initialized


def get_parser_factory() -> DocumentParserFactory:
    """获取文档解析工厂实例（便捷函数）"""
    return DocumentParserFactory.get_instance()


def run_async_safe(coro: Any, timeout: float = 300.0) -> Any:
    """
    安全地从同步代码调用async函数

    处理以下场景：
    1. 没有运行中的事件循环 → asyncio.run()
    2. 已有运行中的事件循环（FastAPI/Jupyter）→ 在新线程中执行
    """
    import concurrent.futures

    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None

    if loop and loop.is_running():
        # 已有运行中的事件循环（如FastAPI、Jupyter），在新线程中执行
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
            future = pool.submit(asyncio.run, coro)
            return future.result(timeout=timeout)
    else:
        # 没有运行中的循环，安全使用asyncio.run()
        return asyncio.run(coro)
