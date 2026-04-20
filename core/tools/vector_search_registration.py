#!/usr/bin/env python3
"""
vector_search工具自动注册模块

在平台启动时自动注册vector_search工具到统一工具注册表。
"""

import logging

logger = logging.getLogger(__name__)


def register_vector_search_tool() -> bool:
    """
    注册vector_search工具到统一工具注册表

    Returns:
        bool: 注册是否成功
    """
    try:
        from core.tools.unified_registry import get_unified_registry

        registry = get_unified_registry()

        # 工具配置
        tool_id = "vector_search"
        import_path = "core.tools.vector_search_handler"
        function_name = "vector_search_handler"

        metadata = {
            "name": "vector_search",
            "description": "向量语义搜索（基于BGE-M3模型，1024维）",
            "category": "vector_search",
            "tags": ["search", "vector", "semantic", "bge-m3", "1024dim"],
            "version": "1.0.0",
            "author": "Athena Team",
        }

        # 检查是否已注册
        if tool_id in registry._lazy_tools:
            logger.debug(f"🔄 工具 '{tool_id}' 已注册，跳过")
            return True

        # 注册为懒加载工具
        success = registry.register_lazy(
            tool_id=tool_id,
            import_path=import_path,
            function_name=function_name,
            metadata=metadata,
        )

        if success:
            logger.info(f"✅ vector_search工具已自动注册到统一工具注册表")
            return True
        else:
            logger.warning(f"⚠️ vector_search工具注册失败")
            return False

    except Exception as e:
        logger.error(f"❌ vector_search工具自动注册失败: {e}")
        return False


# 自动注册（当模块被导入时）
if __name__ != "__main__":
    register_vector_search_tool()
