#!/usr/bin/env python3
"""
注册cache_management工具到统一工具注册表
"""

import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def main():
    """主函数"""

    print("=" * 80)
    print("注册cache_management工具到统一工具注册表")
    print("=" * 80)
    print()

    # 导入统一工具注册表
    from core.tools.unified_registry import get_unified_registry

    registry = get_unified_registry()

    # 工具配置
    tool_id = "cache_management"
    import_path = "core.tools.cache_management_handler"
    function_name = "cache_management_handler"

    metadata = {
        "name": "cache_management",
        "description": "统一缓存管理系统 - 提供Redis缓存读写、批量操作、统计和清理功能",
        "category": "cache_management",
        "tags": ["cache", "redis", "performance", "storage", "management"],
        "version": "1.0.0",
        "author": "Athena Team",
    }

    # 检查工具是否已注册
    if tool_id in registry._lazy_tools:
        print(f"⚠️ 工具 '{tool_id}' 已存在，将先删除旧版本")

    # 注册为懒加载工具
    success = registry.register_lazy(
        tool_id=tool_id,
        import_path=import_path,
        function_name=function_name,
        metadata=metadata,
    )

    if success:
        print(f"✅ 工具 '{tool_id}' 已成功注册到统一工具注册表")
        print()
        print("工具信息:")
        print(f"  工具ID: {tool_id}")
        print(f"  导入路径: {import_path}")
        print(f"  函数名: {function_name}")
        print(f"  名称: {metadata['name']}")
        print(f"  描述: {metadata['description']}")
        print(f"  分类: {metadata['category']}")
        print(f"  标签: {', '.join(metadata['tags'])}")
        print()
    else:
        print(f"❌ 工具 '{tool_id}' 注册失败")
        return False

    # 验证注册
    print("验证注册...")
    tool = registry.get(tool_id)

    if tool:
        print(f"✅ 工具验证成功，可以正常调用")
        print()

        # 测试工具调用
        print("测试工具调用...")
        import asyncio

        async def test_tool():
            result = await tool(
                action="stats"
            )
            return result

        try:
            result = asyncio.run(test_tool())

            if result.get("success"):
                print(f"✅ 工具调用测试成功")
                print(f"   操作: {result['action']}")
                stats = result.get('stats', {})
                print(f"   缓存统计:")
                print(f"     命中率: {stats.get('hit_rate', 0)}%")
                print(f"     总键数: {stats.get('total_keys', 0)}")
                print(f"     内存使用: {stats.get('memory_usage', 'unknown')}")
                print()
                return True
            else:
                print(f"⚠️ 工具调用返回错误: {result.get('error')}")
                print()
                return False

        except Exception as e:
            print(f"❌ 工具调用测试失败: {e}")
            print()
            return False
    else:
        print(f"❌ 工具验证失败，无法获取工具")
        print()
        return False


if __name__ == "__main__":
    try:
        success = main()

        print("=" * 80)
        if success:
            print("✅ cache_management工具注册完成并验证通过")
        else:
            print("❌ cache_management工具注册或验证失败")
        print("=" * 80)

        exit(0 if success else 1)

    except Exception as e:
        print(f"❌ 注册过程出错: {e}")
        import traceback

        traceback.print_exc()
        exit(1)
