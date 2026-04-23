#!/usr/bin/env python3
"""
验证academic_search_handler并注册到统一工具注册表
"""
import asyncio
import sys

sys.path.insert(0, '/Users/xujian/Athena工作平台')

from core.logging_config import setup_logging

logger = setup_logging()


async def verify_academic_search_handler():
    """验证academic_search_handler"""
    print("=" * 60)
    print("🔍 验证academic_search_handler")
    print("=" * 60)

    # 1. 检查文件存在
    print("\n1. 检查文件...")
    import os
    handler_path = "/Users/xujian/Athena工作平台/core/tools/handlers/academic_search_handler.py"

    if os.path.exists(handler_path):
        print(f"   ✅ 文件存在: {handler_path}")
    else:
        print(f"   ❌ 文件不存在: {handler_path}")
        return False

    # 2. 导入handler
    print("\n2. 导入handler...")
    try:
        from core.tools.handlers.academic_search_handler import academic_search_handler
        print("   ✅ 导入成功")
    except Exception as e:
        print(f"   ❌ 导入失败: {e}")
        return False

    # 3. 检查MCP服务器
    print("\n3. 检查MCP学术搜索服务器...")
    try:
        # 测试MCP学术搜索功能
        result = await mcp_academic_search_search_papers(
            query="machine learning",
            limit=5,
            year="2024"
        )

        if result and len(result) > 0:
            print(f"   ✅ MCP学术搜索可用，找到 {len(result)} 篇论文")
            print(f"   第一篇: {result[0].get('title', 'N/A')}")
        else:
            print("   ⚠️ MCP学术搜索未返回结果")
    except Exception as e:
        print(f"   ⚠️ MCP学术搜索测试失败: {e}")

    # 4. 测试handler功能
    print("\n4. 测试handler功能...")
    try:
        # academic_search_handler使用@tool装饰器，直接传递参数
        result = await academic_search_handler(
            query="patent analysis",
            source="auto",
            limit=5,
            year="2024"
        )

        print(f"   ✅ Handler调用成功")
        print(f"   结果类型: {type(result)}")

        if isinstance(result, dict):
            print(f"   包含键: {list(result.keys())[:5]}...")

            # 检查是否有搜索结果
            if 'papers' in result:
                papers = result.get('papers', [])
                print(f"   找到论文数: {len(papers)}")
                if len(papers) > 0:
                    print(f"   第一篇: {papers[0].get('title', 'N/A')}")

        return True

    except Exception as e:
        print(f"   ❌ Handler调用失败: {e}")
        import traceback
        traceback.print_exc()
        return False


async def register_academic_search():
    """注册academic_search到统一工具注册表"""
    print("\n" + "=" * 60)
    print("📝 注册academic_search到统一工具注册表")
    print("=" * 60)

    from core.tools.unified_registry import get_unified_registry
    from core.tools.base import ToolCategory, ToolPriority

    registry = get_unified_registry()

    # 等待注册表初始化
    if not registry._initialized:
        print("⏳ 初始化统一工具注册表...")
        await registry.initialize(auto_discover=False)

    # 检查是否已注册
    existing = registry.get("academic_search")
    if existing is not None:
        print("   ⚠️ academic_search已注册，跳过")
        return True

    # 注册懒加载工具
    success = registry.register_lazy(
        tool_id="academic_search",
        import_path="core.tools.handlers.academic_search_handler",
        function_name="academic_search_handler",
        metadata={
            "name": "学术搜索",
            "description": "学术搜索和论文检索工具（基于Semantic Scholar API）",
            "category": ToolCategory.ACADEMIC_SEARCH,
            "priority": ToolPriority.HIGH,
            "can_handle": "论文检索、学术搜索、文献调研",
        }
    )

    if success:
        print("   ✅ 注册成功")

        # 验证注册
        tool = registry.get("academic_search")
        if tool is not None:
            print("   ✅ 工具可访问")
            return True
        else:
            print("   ❌ 工具无法访问")
            return False
    else:
        print("   ❌ 注册失败")
        return False


async def main():
    """主函数"""
    try:
        # 1. 验证handler
        verified = await verify_academic_search_handler()

        if not verified:
            print("\n⚠️ Handler验证失败，跳过注册")
            return 1

        # 2. 注册到统一工具注册表
        registered = await register_academic_search()

        if registered:
            print("\n" + "=" * 60)
            print("🎉 academic_search验证和注册完成！")
            print("=" * 60)
            return 0
        else:
            print("\n⚠️ 注册失败")
            return 1

    except Exception as e:
        print(f"\n❌ 过程出错: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
