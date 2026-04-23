#!/usr/bin/env python3
"""
验证并注册专利翻译工具到统一工具注册表

功能：
1. 验证patent_translator_handler功能
2. 测试多语言翻译（中英日韩）
3. 验证专利术语保护
4. 注册到统一工具注册表

Author: Athena平台团队
Date: 2026-04-20
"""

import asyncio
import sys
from typing import Dict, Any

sys.path.insert(0, '/Users/xujian/Athena工作平台')

from core.logging_config import setup_logging

logger = setup_logging()


async def test_basic_translation():
    """测试基本翻译功能"""
    print("=" * 60)
    print("🔍 测试1: 基本翻译功能")
    print("=" * 60)

    try:
        from core.tools.patent_translator import patent_translator_handler

        # 测试中文→英文
        test_cases = [
            {
                "name": "中文→英文",
                "text": "本发明涉及一种自动驾驶技术，属于智能交通领域。",
                "target_lang": "en",
                "expected_keywords": ["invention", "autonomous driving", "intelligent transportation"]
            },
            {
                "name": "英文→中文",
                "text": "The present invention relates to an autonomous driving technology.",
                "target_lang": "zh",
                "expected_keywords": ["本发明", "自动驾驶", "技术"]
            }
        ]

        print("\n测试用例:")
        all_passed = True

        for i, case in enumerate(test_cases, 1):
            print(f"\n{i}. {case['name']}")
            print(f"   原文: {case['text'][:50]}...")

            result = await patent_translator_handler(
                text=case['text'],
                target_lang=case['target_lang'],
                source_lang="auto",
                preserve_terms=True
            )

            if result['success']:
                print(f"   ✅ 翻译成功")
                print(f"   译文: {result['translated'][:80]}...")
                print(f"   源语言: {result['source_lang']} → 目标语言: {result['target_lang']}")

                # 检查关键词
                found_keywords = [
                    kw for kw in case['expected_keywords']
                    if kw.lower() in result['translated'].lower()
                ]
                if found_keywords:
                    print(f"   ✅ 关键词匹配: {', '.join(found_keywords)}")
                else:
                    print(f"   ⚠️ 关键词未完全匹配")
            else:
                print(f"   ❌ 翻译失败: {result.get('error', 'Unknown error')}")
                all_passed = False

        return all_passed

    except Exception as e:
        logger.error(f"基本翻译测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_patent_terms_preservation():
    """测试专利术语保护"""
    print("\n" + "=" * 60)
    print("🔍 测试2: 专利术语保护")
    print("=" * 60)

    try:
        from core.tools.patent_translator import patent_translator_handler

        test_cases = [
            {
                "name": "中文权利要求术语",
                "text": "本发明包括以下权利要求：1. 一种自动驾驶方法...",
                "target_lang": "en",
                "preserve_terms": True,
                "expected_terms": ["claims"]
            },
            {
                "name": "英文专利术语",
                "text": "The invention includes the following claims and detailed description.",
                "target_lang": "zh",
                "preserve_terms": True,
                "expected_terms": ["权利要求", "说明书"]
            }
        ]

        print("\n测试用例:")
        all_passed = True

        for i, case in enumerate(test_cases, 1):
            print(f"\n{i}. {case['name']}")
            print(f"   原文: {case['text']}")

            result = await patent_translator_handler(
                text=case['text'],
                target_lang=case['target_lang'],
                source_lang="auto",
                preserve_terms=case['preserve_terms']
            )

            if result['success']:
                print(f"   译文: {result['translated']}")

                # 检查术语保留
                found_terms = [
                    term for term in case['expected_terms']
                    if term in result['translated']
                ]

                if found_terms:
                    print(f"   ✅ 术语保留成功: {', '.join(found_terms)}")
                else:
                    print(f"   ⚠️ 术语未完全保留")
            else:
                print(f"   ❌ 翻译失败: {result.get('error', 'Unknown error')}")
                all_passed = False

        return all_passed

    except Exception as e:
        logger.error(f"术语保护测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_batch_translation():
    """测试批量翻译"""
    print("\n" + "=" * 60)
    print("🔍 测试3: 批量翻译")
    print("=" * 60)

    try:
        from core.tools.patent_translator import patent_translator_batch_handler

        texts = [
            "本发明涉及一种自动驾驶技术。",
            "该技术包括环境感知、路径规划和运动控制。",
            "权利要求1所述的方法，其特征在于..."
        ]

        print(f"\n待翻译文本数: {len(texts)}")
        for i, text in enumerate(texts, 1):
            print(f"{i}. {text}")

        results = await patent_translator_batch_handler(
            texts=texts,
            target_lang="en",
            source_lang="auto",
            preserve_terms=True
        )

        print(f"\n翻译结果:")
        success_count = sum(1 for r in results if r['success'])

        for i, result in enumerate(results, 1):
            if result['success']:
                print(f"{i}. ✅ {result['translated'][:60]}...")
            else:
                print(f"{i}. ❌ {result.get('error', 'Unknown error')}")

        print(f"\n成功率: {success_count}/{len(texts)}")

        return success_count == len(texts)

    except Exception as e:
        logger.error(f"批量翻译测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_language_support():
    """测试多语言支持"""
    print("\n" + "=" * 60)
    print("🔍 测试4: 多语言支持")
    print("=" * 60)

    try:
        from core.tools.patent_translator import patent_translator_handler

        test_cases = [
            {
                "name": "日语测试",
                "text": "本発明は自動運転技術に関する。",
                "target_lang": "zh"
            },
            {
                "name": "韩语测试",
                "text": "본 발명은 자율 주행 기술에 관한 것이다.",
                "target_lang": "en"
            }
        ]

        print("\n测试用例:")
        all_passed = True

        for i, case in enumerate(test_cases, 1):
            print(f"\n{i}. {case['name']}")
            print(f"   原文: {case['text']}")

            result = await patent_translator_handler(
                text=case['text'],
                target_lang=case['target_lang'],
                source_lang="auto",
                preserve_terms=True
            )

            if result['success']:
                print(f"   ✅ 翻译成功")
                print(f"   译文: {result['translated'][:80]}...")
                print(f"   检测到的源语言: {result['source_lang']}")
            else:
                print(f"   ⚠️ 翻译失败: {result.get('error', 'Unknown error')}")
                all_passed = False

        return all_passed

    except Exception as e:
        logger.error(f"多语言测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


async def register_to_unified_registry():
    """注册到统一工具注册表"""
    print("\n" + "=" * 60)
    print("📝 注册到统一工具注册表")
    print("=" * 60)

    try:
        from core.tools.unified_registry import get_unified_registry
        from core.tools.base import ToolCategory, ToolPriority

        registry = get_unified_registry()

        # 等待注册表初始化
        if not registry._initialized:
            print("⏳ 初始化统一工具注册表...")
            await registry.initialize(auto_discover=False)

        # 注册patent_translator
        print("\n1. 注册 patent_translator...")

        existing = registry.get("patent_translator")
        if existing is not None:
            print("   ⚠️ patent_translator已注册，跳过")
        else:
            success = registry.register_lazy(
                tool_id="patent_translator",
                import_path="core.tools.patent_translator",
                function_name="patent_translator_handler",
                metadata={
                    "name": "专利翻译",
                    "description": "专利文献翻译工具，支持中英日韩多语言互译",
                    "category": ToolCategory.PATENT_SEARCH,
                    "priority": ToolPriority.HIGH,
                    "can_handle": "专利翻译、文献翻译、多语言专利"
                }
            )

            if success:
                print("   ✅ 注册成功")
            else:
                print("   ❌ 注册失败")
                return False

        # 注册patent_translator_batch
        print("\n2. 注册 patent_translator_batch...")

        existing = registry.get("patent_translator_batch")
        if existing is not None:
            print("   ⚠️ patent_translator_batch已注册，跳过")
        else:
            success = registry.register_lazy(
                tool_id="patent_translator_batch",
                import_path="core.tools.patent_translator",
                function_name="patent_translator_batch_handler",
                metadata={
                    "name": "批量专利翻译",
                    "description": "批量专利文献翻译，支持大规模文本翻译",
                    "category": ToolCategory.PATENT_SEARCH,
                    "priority": ToolPriority.MEDIUM,
                    "can_handle": "批量翻译、大规模翻译"
                }
            )

            if success:
                print("   ✅ 注册成功")
            else:
                print("   ❌ 注册失败")
                return False

        # 验证注册
        print("\n3. 验证注册...")

        tool1 = registry.get("patent_translator")
        tool2 = registry.get("patent_translator_batch")

        if tool1 is not None and tool2 is not None:
            print("   ✅ 两个工具都已成功注册并可访问")
            return True
        else:
            print(f"   ❌ 工具访问失败 (patent_translator: {tool1 is not None}, patent_translator_batch: {tool2 is not None})")
            return False

    except Exception as e:
        logger.error(f"注册失败: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """主函数"""
    print("=" * 60)
    print("🔍 专利翻译工具验证和注册")
    print("=" * 60)

    # 运行测试
    test_results = {}

    test_results['basic_translation'] = await test_basic_translation()
    test_results['terms_preservation'] = await test_patent_terms_preservation()
    test_results['batch_translation'] = await test_batch_translation()
    test_results['language_support'] = await test_language_support()

    # 注册到统一工具注册表
    registered = await register_to_unified_registry()

    # 总结
    print("\n" + "=" * 60)
    print("📊 测试总结")
    print("=" * 60)

    passed_tests = sum(1 for v in test_results.values() if v)
    total_tests = len(test_results)

    print(f"\n测试通过: {passed_tests}/{total_tests}")

    for test_name, passed in test_results.items():
        status = "✅ 通过" if passed else "❌ 失败"
        print(f"  - {test_name}: {status}")

    print(f"\n注册状态: {'✅ 成功' if registered else '❌ 失败'}")

    if passed_tests == total_tests and registered:
        print("\n" + "=" * 60)
        print("🎉 专利翻译工具验证和注册完成！")
        print("=" * 60)
        return 0
    else:
        print("\n⚠️ 部分测试或注册失败")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
