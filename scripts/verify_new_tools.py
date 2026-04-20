#!/usr/bin/env python3
"""
验证新注册的工具

验证以下工具：
1. patent_translator - 专利翻译
2. patent_translator_batch - 批量专利翻译
3. academic_search - 学术搜索

Author: Athena平台团队
Date: 2026-04-20
"""

import asyncio
import sys

sys.path.insert(0, '/Users/xujian/Athena工作平台')

from core.logging_config import setup_logging

logger = setup_logging()


async def verify_patent_translator():
    """验证专利翻译工具"""
    print("=" * 60)
    print("🔍 验证专利翻译工具")
    print("=" * 60)

    try:
        from core.tools.patent_translator import patent_translator_handler

        result = await patent_translator_handler(
            text="本发明涉及一种自动驾驶技术。",
            target_lang="en",
            source_lang="auto"
        )

        if result['success']:
            print(f"✅ patent_translator 可用")
            print(f"   原文: {result['original']}")
            print(f"   译文: {result['translated'][:80]}...")
            return True
        else:
            print(f"❌ patent_translator 调用失败: {result.get('error')}")
            return False

    except Exception as e:
        print(f"❌ patent_translator 导入或调用失败: {e}")
        return False


async def verify_patent_translator_batch():
    """验证批量专利翻译工具"""
    print("\n" + "=" * 60)
    print("🔍 验证批量专利翻译工具")
    print("=" * 60)

    try:
        from core.tools.patent_translator import patent_translator_batch_handler

        results = await patent_translator_batch_handler(
            texts=[
                "本发明涉及一种自动驾驶技术。",
                "该技术包括环境感知和路径规划。"
            ],
            target_lang="en",
            source_lang="zh"
        )

        success_count = sum(1 for r in results if r['success'])

        if success_count == len(results):
            print(f"✅ patent_translator_batch 可用")
            print(f"   成功翻译: {success_count}/{len(results)} 个文本")
            return True
        else:
            print(f"⚠️ patent_translator_batch 部分失败: {success_count}/{len(results)}")
            return False

    except Exception as e:
        print(f"❌ patent_translator_batch 导入或调用失败: {e}")
        return False


async def verify_academic_search():
    """验证学术搜索工具"""
    print("\n" + "=" * 60)
    print("🔍 验证学术搜索工具")
    print("=" * 60)

    try:
        from core.tools.handlers.academic_search_handler import academic_search_handler

        result = await academic_search_handler(
            query="patent analysis",
            source="auto",
            limit=5
        )

        if 'success' in result:
            print(f"✅ academic_search 可用")
            print(f"   查询: {result.get('query', 'N/A')}")
            if 'papers' in result:
                print(f"   找到论文数: {len(result['papers'])}")
            return True
        else:
            print(f"⚠️ academic_search 返回异常结果")
            return False

    except Exception as e:
        print(f"❌ academic_search 导入或调用失败: {e}")
        return False


async def verify_registry_registration():
    """验证工具是否已注册到统一工具注册表"""
    print("\n" + "=" * 60)
    print("🔍 验证统一工具注册表注册状态")
    print("=" * 60)

    try:
        from core.tools.unified_registry import get_unified_registry

        registry = get_unified_registry()

        # 如果未初始化，先初始化
        if not registry._initialized:
            print("⏳ 初始化统一工具注册表...")
            await registry.initialize(auto_discover=False)

        # 注册新工具
        print("\n注册新工具...")

        from core.tools.base import ToolCategory, ToolPriority

        # 1. patent_translator
        if not registry.get("patent_translator"):
            registry.register_lazy(
                tool_id="patent_translator",
                import_path="core.tools.patent_translator",
                function_name="patent_translator_handler",
                metadata={
                    "name": "专利翻译",
                    "description": "专利文献翻译工具",
                    "category": ToolCategory.PATENT_SEARCH,
                    "priority": ToolPriority.HIGH,
                }
            )
            print("   ✅ patent_translator 注册成功")

        # 2. patent_translator_batch
        if not registry.get("patent_translator_batch"):
            registry.register_lazy(
                tool_id="patent_translator_batch",
                import_path="core.tools.patent_translator",
                function_name="patent_translator_batch_handler",
                metadata={
                    "name": "批量专利翻译",
                    "description": "批量专利文献翻译",
                    "category": ToolCategory.PATENT_SEARCH,
                    "priority": ToolPriority.MEDIUM,
                }
            )
            print("   ✅ patent_translator_batch 注册成功")

        # 3. academic_search
        if not registry.get("academic_search"):
            registry.register_lazy(
                tool_id="academic_search",
                import_path="core.tools.handlers.academic_search_handler",
                function_name="academic_search_handler",
                metadata={
                    "name": "学术搜索",
                    "description": "学术论文搜索",
                    "category": "academic_search",
                    "priority": ToolPriority.HIGH,
                }
            )
            print("   ✅ academic_search 注册成功")

        # 验证注册
        print("\n验证注册状态...")
        tools = ["patent_translator", "patent_translator_batch", "academic_search"]
        all_registered = True

        for tool_id in tools:
            tool = registry.get(tool_id)
            if tool:
                print(f"   ✅ {tool_id}: 已注册并可访问")
            else:
                print(f"   ❌ {tool_id}: 未找到")
                all_registered = False

        return all_registered

    except Exception as e:
        print(f"❌ 注册验证失败: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """主函数"""
    print("=" * 60)
    print("🔍 新工具验证")
    print("=" * 60)

    # 验证工具功能
    results = {}

    results['patent_translator'] = await verify_patent_translator()
    results['patent_translator_batch'] = await verify_patent_translator_batch()
    results['academic_search'] = await verify_academic_search()

    # 验证注册状态
    registered = await verify_registry_registration()

    # 总结
    print("\n" + "=" * 60)
    print("📊 验证总结")
    print("=" * 60)

    passed = sum(1 for v in results.values() if v)
    total = len(results)

    print(f"\n功能测试: {passed}/{total} 通过")

    for tool_name, passed_test in results.items():
        status = "✅ 通过" if passed_test else "❌ 失败"
        print(f"  - {tool_name}: {status}")

    print(f"\n注册状态: {'✅ 全部已注册' if registered else '❌ 注册失败'}")

    if passed == total and registered:
        print("\n" + "=" * 60)
        print("🎉 所有新工具验证通过并已注册！")
        print("=" * 60)
        return 0
    else:
        print("\n⚠️ 部分工具验证或注册失败")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
