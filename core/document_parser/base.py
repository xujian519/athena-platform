#!/usr/bin/env python3
from __future__ import annotations
"""
文档解析抽象基类与数据模型
Document Parser Abstract Base Class and Data Models

作者: Athena平台团队
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class ParserBackend(str, Enum):
    """文档解析后端类型"""
    MINERU = "mineru"
    TESSERACT = "tesseract"


@dataclass
class ParseRequest:
    """统一的文档解析请求"""

    file_path: str  # 文件路径
    language: str = "ch"  # 语言代码
    extract_tables: bool = True  # 是否提取表格
    extract_formulas: bool = False  # 是否提取公式
    return_markdown: bool = True  # 是否返回Markdown
    timeout: float = 300.0  # 超时秒数


@dataclass
class ParseResult:
    """统一的文档解析结果"""

    content: str = ""  # 纯文本内容
    markdown_content: str = ""  # Markdown格式内容
    tables: list[dict[str, Any]] = field(default_factory=list)  # 表格数据
    confidence: float = 0.0  # 置信度
    backend_used: str = ""  # 实际使用的后端
    processing_time: float = 0.0  # 处理耗时(秒)
    page_count: int = 0  # 页数
    from_cache: bool = False  # 是否来自缓存
    error: str = ""  # 错误信息


class BaseDocumentParser(ABC):
    """文档解析适配器基类"""

    def __init__(self, backend: ParserBackend):
        self.backend = backend
        self._initialized = False

    @abstractmethod
    async def initialize(self) -> bool:
        """初始化解析器，返回是否成功"""

    @abstractmethod
    async def parse(self, request: ParseRequest) -> ParseResult:
        """解析文档"""

    @abstractmethod
    async def health_check(self) -> bool:
        """健康检查"""

    @abstractmethod
    def get_stats(self) -> dict[str, Any]:
        """获取统计信息"""

    def is_initialized(self) -> bool:
        return self._initialized
