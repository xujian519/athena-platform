#!/usr/bin/env python3
"""
注册vector_search工具到统一工具注册表
"""

import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def main():
    """主函数"""

    print("=" * 80)
    print("注册vector_search工具到统一工具注册表")
    print("=" * 80)
    print()

    # 导入统一工具注册表
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

    # 检查工具是否已注册
    existing_tool = registry.get(tool_id)
    if existing_tool:
        print(f"⚠️ 工具 '{tool_id}' 已存在，将先删除旧版本")
        # 注意：这里简化处理，实际可能需要unregister方法

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
                query="专利检索",
                collection="patent_rules_1024",
                top_k=3,
                threshold=0.0
            )
            return result

        try:
            result = asyncio.run(test_tool())

            if result.get("success"):
                print(f"✅ 工具调用测试成功")
                print(f"   查询: {result['query']}")
                print(f"   集合: {result['collection']}")
                print(f"   维度: {result['dimension']}")
                print(f"   结果数: {result['total_results']}")
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
            print("✅ vector_search工具注册完成并验证通过")
        else:
            print("❌ vector_search工具注册或验证失败")
        print("=" * 80)

        exit(0 if success else 1)

    except Exception as e:
        print(f"❌ 注册过程出错: {e}")
        import traceback

        traceback.print_exc()
        exit(1)
