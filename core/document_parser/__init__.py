#!/usr/bin/env python3
"""
文档解析模块
Document Parser Module

提供统一的文档解析接口，支持多后端降级策略。

使用示例:
    from core.document_parser import get_parser_factory, ParseRequest

    factory = get_parser_factory()
    await factory.initialize()
    result = await factory.parse(ParseRequest(file_path="test.pdf"))
"""

from core.document_parser.base import BaseDocumentParser, ParseRequest, ParseResult, ParserBackend
from core.document_parser.mineru_adapter import MinerUAdapter
from core.document_parser.parser_factory import DocumentParserFactory, get_parser_factory, run_async_safe
from core.document_parser.tesseract_adapter import TesseractAdapter

__all__ = [
    "BaseDocumentParser",
    "ParseRequest",
    "ParseResult",
    "ParserBackend",
    "MinerUAdapter",
    "TesseractAdapter",
    "DocumentParserFactory",
    "get_parser_factory",
    "run_async_safe",
]
