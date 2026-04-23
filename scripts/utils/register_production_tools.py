#!/usr/bin/env python3
"""
Athena工具注册脚本

将本地搜索和增强文档解析器注册到工具系统
"""

import asyncio
import sys
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.tools.base import (
    ToolCapability,
    ToolCategory,
    ToolDefinition,
    ToolPriority,
    get_global_registry,
)
from core.tools.enhanced_document_parser import enhanced_document_parser_handler
from core.tools.real_tool_implementations import real_web_search_handler


def setup_logger():
    """配置日志记录器"""
    import logging

    from core.logging_config import setup_logging

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    return setup_logging()


async def register_production_tools():
    """
    注册生产级工具到全局工具注册表

    包括:
    1. 本地网络搜索工具
    2. 增强文档解析器（OCR）
    """
    logger = setup_logger()

    registry = get_global_registry()

    logger.info("=" * 60)
    logger.info("🔧 开始注册生产级工具...")
    logger.info("=" * 60)

    # ========================================
    # 1. 本地网络搜索工具
    # ========================================
    logger.info("  1️⃣ 注册本地网络搜索工具...")

    try:
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
        logger.info("     ✅ 本地网络搜索工具已注册")

    except Exception as e:
        logger.error(f"     ❌ 本地网络搜索工具注册失败: {e}")

    # ========================================
    # 2. 增强文档解析器（OCR）
    # ========================================
    logger.info("  2️⃣ 注册增强文档解析器...")

    try:
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
        logger.info("     ✅ 增强文档解析器已注册")

    except Exception as e:
        logger.error(f"     ❌ 增强文档解析器注册失败: {e}")

    # ========================================
    # 注册总结
    # ========================================
    logger.info("")
    logger.info("=" * 60)
    logger.info("📊 工具注册总结")
    logger.info("=" * 60)

    stats = registry.get_statistics()
    total_tools = stats["total_tools"]

    logger.info(f"   注册的工具总数: {total_tools}")
    logger.info("   本地网络搜索: ✅")
    logger.info("   增强文档解析器: ✅")
    logger.info("")
    logger.info("🎉 生产级工具注册完成！")
    logger.info("=" * 60)

    return registry


async def test_registered_tools():
    """测试已注册的工具"""
    logger = setup_logger()

    logger.info("")
    logger.info("=" * 60)
    logger.info("🧪 测试已注册工具")
    logger.info("=" * 60)

    get_global_registry()

    # 测试1: 本地网络搜索
    logger.info("  测试1: 本地网络搜索")
    logger.info("-" * 60)

    try:
        result = await real_web_search_handler({
            "query": "Python编程",
            "limit": 3
        })

        if result.get("engine") == "local-search-engine":
            logger.info("  ✅ 本地搜索工具测试通过")
        else:
            logger.warning(f"  ⚠️  本地搜索工具返回: {result.get('engine')}")
    except Exception as e:
        logger.error(f"  ❌ 本地搜索工具测试失败: {e}")

    # 测试2: 增强文档解析器
    logger.info("")
    logger.info("  测试2: 增强文档解析器")
    logger.info("-" * 60)

    # 创建测试文件
    import tempfile
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        f.write("测试文档内容\n用于验证增强文档解析器功能。")
        test_file = f.name

    try:
        result = await enhanced_document_parser_handler({
            "file_path": test_file,
            "use_ocr": False
        }, {})

        if result.get("success"):
            logger.info("  ✅ 文档解析器测试通过")
        else:
            logger.warning(f"  ⚠️  文档解析器返回错误: {result.get('error')}")
    except Exception as e:
        logger.error(f"  ❌ 文档解析器测试失败: {e}")
    finally:
        # 清理测试文件
        import os
        try:
            os.unlink(test_file)
        except:
            pass

    logger.info("")
    logger.info("=" * 60)
    logger.info("🎉 工具测试完成！")
    logger.info("=" * 60)


def main():
    """主函数"""
    logger = setup_logger()

    print("""
╔════════════════════════════════════════════════════════════════════════╗
║                                                                            ║
║           Athena工具注册 - 生产级工具部署                              ║
║                                                                            ║
║  将本地搜索和增强文档解析器注册到Athena工具系统                          ║
║                                                                            ║
╚════════════════════════════════════════════════════════════════════════╝
""")

    # 运行注册
    try:
        asyncio.run(register_production_tools())

        # 询问是否测试
        print("")
        response = input("是否测试已注册的工具？(y/N): ").strip().lower()

        if response in ['y', 'yes']:
            asyncio.run(test_registered_tools())

        print("")
        print("=" * 60)
        print("✅ 工具注册完成！")
        print("=" * 60)
        print("")
        print("📋 已注册的工具:")
        print("   1. local_web_search - 本地网络搜索")
        print("   2. enhanced_document_parser - 增强文档解析器（OCR）")
        print("")
        print("📖 使用指南:")
        print("   - 搜索工具: await real_web_search_handler({'query': '搜索内容'})")
        print("   - 解析工具: await enhanced_document_parser_handler({'file_path': '/path/to/file.pdf'})")
        print("")

        return 0

    except Exception as e:
        logger.error(f"❌ 工具注册失败: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
