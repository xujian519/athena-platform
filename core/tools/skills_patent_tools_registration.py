#!/usr/bin/env python3
"""
技能工具注册：专利检索和下载
Skills Tools Registration: Patent Search and Download

将专利检索和下载技能工具注册到统一工具注册表

Author: Athena平台团队
Version: v1.0.0
Created: 2026-04-23
"""

import logging
from pathlib import Path
from typing import Dict, Any, Optional

from core.tools.unified_registry import get_unified_registry

logger = logging.getLogger(__name__)


def patent_search_handler(
    query: str,
    num_results: int = 20,
    output_dir: Optional[str] = None
) -> Dict[str, Any]:
    """
    专利检索处理器

    Args:
        query: 技术描述或检索式
        num_results: 结果数量（默认20）
        output_dir: 输出目录（可选）

    Returns:
        检索结果字典
    """
    from core.tools.skills_patent_search import get_patent_search_tool

    tool = get_patent_search_tool()

    # 判断是技术描述还是检索式
    if query.startswith("--query") or " AND " in query or " OR " in query:
        # 检索式
        return tool.search_by_query(query, num_results, output_dir)
    else:
        # 技术描述
        return tool.search_by_description(query, num_results, output_dir)


def patent_download_handler(
    patent_number: str,
    output_dir: str = ".",
    open_after_download: bool = False,
    proxy: Optional[str] = None
) -> Dict[str, Any]:
    """
    专利下载处理器

    Args:
        patent_number: 专利号（如：CN123456789A, US11739244B2）
        output_dir: 输出目录
        open_after_download: 下载后自动打开
        proxy: 代理设置

    Returns:
        下载结果字典
    """
    from core.tools.skills_patent_download import get_patent_download_tool

    tool = get_patent_download_tool()
    result = tool.download_single(patent_number, output_dir, open_after_download, proxy)
    return result.to_dict()


def patent_batch_download_handler(
    patent_numbers: list,
    output_dir: str = ".",
    proxy: Optional[str] = None
) -> Dict[str, Any]:
    """
    批量专利下载处理器

    Args:
        patent_numbers: 专利号列表
        output_dir: 输出目录
        proxy: 代理设置

    Returns:
        下载结果字典
    """
    from core.tools.skills_patent_download import get_patent_download_tool

    tool = get_patent_download_tool()
    results = tool.download_batch(patent_numbers, output_dir, proxy)

    return {
        "success": True,
        "total": len(results),
        "successful": sum(1 for r in results if r.success),
        "failed": sum(1 for r in results if not r.success),
        "results": [r.to_dict() for r in results]
    }


def patent_info_handler(
    patent_number: str,
    proxy: Optional[str] = None
) -> Dict[str, Any]:
    """
    专利信息查询处理器

    Args:
        patent_number: 专利号
        proxy: 代理设置

    Returns:
        专利信息字典
    """
    from core.tools.skills_patent_download import get_patent_download_tool

    tool = get_patent_download_tool()
    return tool.get_patent_info(patent_number, proxy)


def register_skills_patent_tools():
    """
    注册专利检索和下载技能工具到统一工具注册表

    此函数在模块导入时自动执行
    """
    try:
        # 获取统一注册表
        registry = get_unified_registry()

        # 注册专利检索工具
        patent_search_tool = registry.get("skills_patent_search")
        if patent_search_tool is None:
            registry.register(
                tool_id="skills_patent_search",
                tool_function=patent_search_handler,
                metadata={
                    "name": "skills_patent_search",
                    "category": "patent",
                    "description": "专利智能检索工具（支持技术描述和检索式）",
                    "version": "1.0.0",
                    "author": "Athena平台团队",
                    "tags": ["patent", "search", "google_patents", "keywords"],
                    "priority": "high",
                    "enabled": True,
                    "capabilities": {
                        "input_types": ["技术描述", "检索式"],
                        "output_types": ["检索报告", "JSON数据"],
                        "max_results": 100,
                        "requires_api_key": False,
                        "async": False
                    },
                    "dependencies": {
                        "python": ["subprocess", "json", "pathlib"],
                        "external": ["Google Patents"],
                        "scripts": [
                            "~/skills/patent-search/scripts/search_patents.py"
                        ]
                    }
                }
            )
            logger.info("✅ 专利检索技能工具注册成功")
        else:
            logger.info("✅ 专利检索技能工具已注册，跳过重复注册")

        # 注册专利下载工具
        patent_download_tool = registry.get("skills_patent_download")
        if patent_download_tool is None:
            registry.register(
                tool_id="skills_patent_download",
                tool_function=patent_download_handler,
                metadata={
                    "name": "skills_patent_download",
                    "category": "patent",
                    "description": "专利PDF下载工具（支持多国专利）",
                    "version": "1.0.0",
                    "author": "Athena平台团队",
                    "tags": ["patent", "download", "pdf", "google_patents"],
                    "priority": "high",
                    "enabled": True,
                    "capabilities": {
                        "supported_formats": ["CN", "US", "EP", "WO", "JP", "KR", "DE", "GB"],
                        "batch_download": True,
                        "requires_api_key": False,
                        "async": False
                    },
                    "dependencies": {
                        "python": ["subprocess", "pathlib"],
                        "external": ["Google Patents"],
                        "scripts": [
                            "~/skills/patent-download/scripts/download_patent.py"
                        ]
                    }
                }
            )
            logger.info("✅ 专利下载技能工具注册成功")
        else:
            logger.info("✅ 专利下载技能工具已注册，跳过重复注册")

        # 注册批量专利下载工具
        batch_download_tool = registry.get("skills_patent_batch_download")
        if batch_download_tool is None:
            registry.register(
                tool_id="skills_patent_batch_download",
                tool_function=patent_batch_download_handler,
                metadata={
                    "name": "skills_patent_batch_download",
                    "category": "patent",
                    "description": "批量专利PDF下载工具",
                    "version": "1.0.0",
                    "author": "Athena平台团队",
                    "tags": ["patent", "download", "batch", "pdf"],
                    "priority": "medium",
                    "enabled": True,
                    "capabilities": {
                        "supported_formats": ["CN", "US", "EP", "WO", "JP", "KR", "DE", "GB"],
                        "batch_download": True,
                        "requires_api_key": False,
                        "async": False
                    }
                }
            )
            logger.info("✅ 批量专利下载技能工具注册成功")

        # 注册专利信息查询工具
        patent_info_tool = registry.get("skills_patent_info")
        if patent_info_tool is None:
            registry.register(
                tool_id="skills_patent_info",
                tool_function=patent_info_handler,
                metadata={
                    "name": "skills_patent_info",
                    "category": "patent",
                    "description": "专利信息查询工具（不下载PDF）",
                    "version": "1.0.0",
                    "author": "Athena平台团队",
                    "tags": ["patent", "info", "metadata"],
                    "priority": "low",
                    "enabled": True,
                    "capabilities": {
                        "supported_formats": ["CN", "US", "EP", "WO", "JP", "KR", "DE", "GB"],
                        "requires_api_key": False,
                        "async": False
                    }
                }
            )
            logger.info("✅ 专利信息查询技能工具注册成功")

        logger.info("✅ 所有专利技能工具注册完成")
        return True

    except Exception as e:
        logger.error(f"❌ 专利技能工具注册失败: {e}")
        return False


# 自动注册
register_skills_patent_tools()


__all__ = [
    "register_skills_patent_tools",
    "patent_search_handler",
    "patent_download_handler",
    "patent_batch_download_handler",
    "patent_info_handler"
]
