#!/usr/bin/env python3
"""
学术搜索工具注册
Academic Search Tool Registration

将学术搜索Handler注册到统一工具注册表

作者: Athena平台团队
版本: v1.0.0
创建: 2026-04-19
"""

import logging
from pathlib import Path

from core.tools.unified_registry import get_unified_registry

logger = logging.getLogger(__name__)


def register_academic_search_tool():
    """
    注册学术搜索工具到统一工具注册表

    此函数在模块导入时自动执行
    """
    try:
        # 获取统一注册表
        registry = get_unified_registry()

        # 检查是否已注册
        if registry.is_registered("academic_search"):
            logger.info("✅ 学术搜索工具已注册，跳过重复注册")
            return True

        # 导入Handler
        from core.tools.handlers.academic_search_handler import academic_search_handler

        # 注册工具
        registry.register(
            tool_id="academic_search",
            tool_function=academic_search_handler,
            metadata={
                "name": "academic_search",
                "category": "academic_search",
                "description": "学术论文和文献搜索（支持Google Scholar和Semantic Scholar）",
                "version": "1.0.0",
                "author": "Athena平台团队",
                "tags": ["academic", "search", "research", "papers", "scholar"],
                "priority": "medium",
                "enabled": True,
                "capabilities": {
                    "supported_sources": ["google_scholar", "semantic_scholar", "both"],
                    "max_results": 100,
                    "requires_api_key": False,  # Semantic Scholar无需密钥
                    "async": True
                },
                "dependencies": {
                    "python": ["aiohttp"],
                    "external": ["Semantic Scholar API", "Google Scholar (optional)"]
                }
            }
        )

        logger.info("✅ 学术搜索工具注册成功")
        return True

    except Exception as e:
        logger.error(f"❌ 学术搜索工具注册失败: {e}")
        return False


# 自动注册
register_academic_search_tool()


__all__ = ["register_academic_search_tool"]
