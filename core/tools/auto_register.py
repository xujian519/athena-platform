#!/usr/bin/env python3
"""
生产工具自动注册模块

在工具系统初始化时自动注册生产级工具。

Author: Athena平台团队
Created: 2026-04-19
"""

import logging
from typing import TYPE_CHECKING

from .base import ToolCapability, ToolCategory, ToolDefinition, ToolPriority, get_global_registry

if TYPE_CHECKING:
    from .enhanced_document_parser import enhanced_document_parser_handler
    from .real_tool_implementations import real_web_search_handler

logger = logging.getLogger(__name__)


def auto_register_production_tools() -> None:
    """
    自动注册生产级工具到全局工具注册表

    注册的工具包括:
    1. local_web_search - 本地网络搜索
    2. enhanced_document_parser - 增强文档解析器（OCR）
    3. patent_search - 专利检索（PostgreSQL + Google Patents）
    4. patent_download - 专利下载（Google Patents PDF）
    """
    registry = get_global_registry()

    # 检查工具是否已注册（只检查一个代表性的工具）
    if "patent_search" in registry._tools:
        logger.debug("生产工具已注册，跳过自动注册")
        return

    try:
        # 导入工具处理器（延迟导入避免循环依赖）
        from .enhanced_document_parser import enhanced_document_parser_handler
        from .real_tool_implementations import real_web_search_handler

        # ========================================
        # 1. 本地网络搜索工具
        # ========================================
        registry.register(
            ToolDefinition(
                tool_id="local_web_search",
                name="本地网络搜索",
                description="本地网络搜索工具 - 基于SearXNG+Firecrawl，无需外部API，完全本地化运行",
                category=ToolCategory.WEB_SEARCH,
                priority=ToolPriority.HIGH,
                capability=ToolCapability(
                    input_types=["query"],
                    output_types=["search_results"],
                    domains=["all"],
                    task_types=["search", "information_retrieval"],
                    features={
                        "local": True,
                        "privacy_safe": True,
                        "no_api_key": True,
                        "multi_engine": True,
                    }
                ),
                required_params=["query"],
                optional_params=["limit"],
                handler=real_web_search_handler,
                timeout=30.0,
                enabled=True,
            )
        )
        logger.info("✅ 生产工具已自动注册: local_web_search")

    except Exception as e:
        logger.warning(f"⚠️  本地网络搜索工具注册失败: {e}")

    # ========================================
    # 2. 增强文档解析器（OCR）
    # ========================================
    try:
        from .enhanced_document_parser import enhanced_document_parser_handler

        registry.register(
            ToolDefinition(
                tool_id="enhanced_document_parser",
                name="增强文档解析器",
                description="增强文档解析工具 - 支持PDF OCR、图片OCR、表格提取、图片提取，基于minerU引擎",
                category=ToolCategory.DATA_EXTRACTION,
                priority=ToolPriority.HIGH,
                capability=ToolCapability(
                    input_types=["document", "image", "pdf"],
                    output_types=["text", "markdown", "structured_data"],
                    domains=["all"],
                    task_types=["parse", "extract", "ocr"],
                    features={
                        "ocr_enabled": True,
                        "table_extraction": True,
                        "image_extraction": True,
                        "markdown_output": True,
                        "multi_format": True,
                        "confidence_scoring": True,
                    }
                ),
                required_params=["file_path"],
                optional_params=[
                    "use_ocr",
                    "extract_images",
                    "extract_tables",
                    "max_length"
                ],
                handler=enhanced_document_parser_handler,
                timeout=120.0,  # OCR可能需要较长时间
                enabled=True,
            )
        )
        logger.info("✅ 生产工具已自动注册: enhanced_document_parser")

    except Exception as e:
        logger.warning(f"⚠️  增强文档解析器注册失败: {e}")

    # ========================================
    # 3. 专利检索工具
    # ========================================
    try:
        from .patent_retrieval import patent_search_handler

        registry.register(
            ToolDefinition(
                tool_id="patent_search",
                name="专利检索",
                description="统一专利检索工具 - 支持本地PostgreSQL patent_db和Google Patents两个渠道",
                category=ToolCategory.PATENT_SEARCH,
                priority=ToolPriority.HIGH,
                capability=ToolCapability(
                    input_types=["query", "patent_number"],
                    output_types=["patent_data", "search_results"],
                    domains=["patent", "legal", "intellectual_property"],
                    task_types=["search", "retrieval", "analysis"],
                    features={
                        "local_postgres": True,
                        "google_patents": True,
                        "dual_channel": True,
                        "vector_search": True,
                        "fulltext_search": True,
                    }
                ),
                required_params=["query"],
                optional_params=["channel", "max_results"],
                handler=patent_search_handler,
                timeout=60.0,  # 检索可能需要较长时间
                enabled=True,
            )
        )
        logger.info("✅ 生产工具已自动注册: patent_search")

    except Exception as e:
        logger.warning(f"⚠️  专利检索工具注册失败: {e}")

    # ========================================
    # 4. 专利下载工具
    # ========================================
    try:
        from .patent_download import patent_download_handler

        registry.register(
            ToolDefinition(
                tool_id="patent_download",
                name="专利下载",
                description="专利PDF下载工具 - 从Google Patents下载专利原文PDF",
                category=ToolCategory.DATA_EXTRACTION,
                priority=ToolPriority.HIGH,
                capability=ToolCapability(
                    input_types=["patent_numbers"],
                    output_types=["pdf_files", "file_paths"],
                    domains=["patent", "legal", "intellectual_property"],
                    task_types=["download", "extract", "archive"],
                    features={
                        "google_patents": True,
                        "pdf_format": True,
                        "batch_download": True,
                        "metadata_extraction": True,
                    }
                ),
                required_params=["patent_numbers"],
                optional_params=["output_dir"],
                handler=patent_download_handler,
                timeout=300.0,  # 下载可能需要很长时间（多个专利）
                enabled=True,
            )
        )
        logger.info("✅ 生产工具已自动注册: patent_download")

    except Exception as e:
        logger.warning(f"⚠️  专利下载工具注册失败: {e}")


# 模块导入时自动注册
_auto_registered = False


def _ensure_production_tools_registered():
    """确保生产工具已注册（线程安全的单次执行）"""
    global _auto_registered

    if not _auto_registered:
        try:
            auto_register_production_tools()
            _auto_registered = True
        except Exception as e:
            logger.error(f"生产工具自动注册失败: {e}")


# 在模块导入时自动执行注册
_ensure_production_tools_registered()
