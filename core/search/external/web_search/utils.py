#!/usr/bin/env python3
"""
联网搜索引擎 - 便捷工具
Web Search Engines - Utility Functions

提供便捷函数和全局实例

作者: 小娜 & 小诺
创建时间: 2025-12-04
重构时间: 2026-01-26
版本: 2.1.0
"""

from typing import Any

from core.logging_config import setup_logging
from core.search.external.web_search.manager import UnifiedWebSearchManager
from core.search.external.web_search.types import SearchEngineType, SearchResponse

logger = setup_logging()


async def quick_search(
    query: str, engine: str = "tavily", **kwargs: Any
) -> SearchResponse:
    """快速搜索 - 便捷函数"""
    manager = UnifiedWebSearchManager()

    try:
        engine_type = SearchEngineType(engine)
        return await manager.search(query, [engine_type])
    except ValueError:
        # 如果引擎类型无效,使用默认搜索引擎
        return await manager.search(query)


# 全局实例
_web_search_manager: UnifiedWebSearchManager | None = None


def get_web_search_manager() -> UnifiedWebSearchManager:
    """获取全局搜索管理器实例"""
    global _web_search_manager
    if _web_search_manager is None:
        _web_search_manager = UnifiedWebSearchManager()
    return _web_search_manager


async def test_web_search():
    """测试联网搜索功能"""
    logger.info("🔍 测试联网搜索功能...")

    manager = get_web_search_manager()

    try:
        # 测试Tavily搜索
        logger.info("\n1️⃣ 测试Tavily搜索...")
        tavily_result = await manager.search(
            "artificial intelligence patents",
            engines=[SearchEngineType.TAVILY],
            max_results=5,
        )

        if tavily_result.success:
            logger.info(f"✅ Tavily搜索成功")
            logger.info(f"   查询: {tavily_result.query}")
            logger.info(f"   结果数量: {tavily_result.total_results}")
            logger.info(f"   搜索时间: {tavily_result.search_time:.2f}秒")
            logger.info(f"   API密钥: {tavily_result.api_key_used}")

            # 显示前3个结果
            for i, result in enumerate(tavily_result.results[:3]):
                logger.info(f"   {i+1}. {result.title}")
                logger.info(f"      URL: {result.url}")
                logger.info(f"      摘要: {result.snippet[:100]}...")
        else:
            logger.info(f"❌ Tavily搜索失败: {tavily_result.error_message}")
    except Exception as e:
        logger.error(f"❌ 测试搜索异常: {e}")
