#!/usr/bin/env python3
"""
生产环境集成测试
Production Integration Test for Google Scholar

测试在生产环境中调用Google Scholar功能

作者: 小诺·双鱼公主 (Xiaonuo Pisces Princess)
版本: v1.0.0
创建: 2025-12-31
"""

from __future__ import annotations
import asyncio
import os
import sys
from pathlib import Path

# 设置路径
current_dir = Path(__file__).parent
project_root = current_dir.parent.parent
sys.path.insert(0, str(project_root))


async def test_production_integration():
    """测试生产环境集成"""

    print()
    print("=" * 70)
    print("🧪 Google Scholar 生产环境集成测试")
    print("=" * 70)
    print()

    # 配置API密钥
    api_key = os.getenv('SERPER_API_KEY')

    if not api_key:
        print("❌ 未设置 SERPER_API_KEY 环境变量")
        print("   请设置: export SERPER_API_KEY='your_api_key'")
        print()
        return

    print("📝 配置信息:")
    print(f"   API密钥: {api_key[:10]}...{api_key[-6:]}")
    print(f"   项目根目录: {project_root}")
    print("   Python路径已添加")
    print()

    tests_passed = 0
    tests_failed = 0

    # 测试1: 导入核心模块
    print("📦 测试 1: 导入核心模块")
    print("-" * 70)

    try:
        from core.agents.athena_scholar_tools import (
            scholar_paper_search,
        )
        from core.search.external.serper_api_manager import (
            SerperAPIManager,
            SerperConfig,
            SerperSearchRequest,
            SerperSearchType,
        )
        from core.search.tools.google_scholar_tool import (
            create_scholar_search,
        )

        print("✅ 所有核心模块导入成功")
        tests_passed += 1
    except Exception as e:
        print(f"❌ 模块导入失败: {e}")
        tests_failed += 1
        return

    print()

    # 测试2: Serper API 管理器
    print("🔧 测试 2: Serper API 管理器")
    print("-" * 70)

    try:
        config = SerperConfig(
            api_key=api_key,
            enable_cache=True
        )

        async with SerperAPIManager(config) as manager:
            # 测试搜索
            request = SerperSearchRequest(
                query="deep learning",
                search_type=SerperSearchType.SCHOLAR,
                num_results=3
            )

            result = await manager.search(request)

            if result.success:
                print("✅ API调用成功")
                print(f"   查询: {result.query}")
                print(f"   结果数: {result.total_results}")
                print(f"   耗时: {result.search_time:.2f}秒")
                print(f"   信用点: {result.api_credits_used}")

                if result.results:
                    print("\n   前3个结果:")
                    for i, r in enumerate(result.results[:3], 1):
                        print(f"   [{i}] {r['title'][:50]}...")

                tests_passed += 1
            else:
                print(f"❌ 搜索失败: {result.error_message}")
                tests_failed += 1

    except Exception as e:
        print(f"❌ Serper管理器测试失败: {e}")
        tests_failed += 1
        import traceback
        traceback.print_exc()

    print()

    # 测试3: Scholar 搜索工具
    print("🎓 测试 3: Google Scholar 搜索工具")
    print("-" * 70)

    try:
        tool = await create_scholar_search(api_key)

        from core.search.standards.base_search_tool import SearchQuery

        query = SearchQuery(
            text="neural networks",
            max_results=3
        )

        response = await tool.search(query)

        if response.success:
            print("✅ 工具调用成功")
            print(f"   找到: {response.total_found} 个结果")
            print(f"   耗时: {response.search_time:.2f}秒")

            if response.documents:
                print("\n   前3个文档:")
                for i, doc in enumerate(response.documents[:3], 1):
                    print(f"   [{i}] {doc.title[:50]}...")
                    print(f"       作者: {', '.join(doc.metadata.get('authors', [])[:2])}")

            tests_passed += 1
        else:
            print("❌ 工具调用失败")
            tests_failed += 1

    except Exception as e:
        print(f"❌ Scholar工具测试失败: {e}")
        tests_failed += 1
        import traceback
        traceback.print_exc()

    print()

    # 测试4: 小娜工具集成
    print("💖 测试 4: 小娜学术工具集成")
    print("-" * 70)

    try:
        result = await scholar_paper_search(
            query="quantum computing",
            max_results=3
        )

        if result['success']:
            print("✅ 小娜工具调用成功")
            print(f"   找到论文: {result['total_found']}")
            print(f"   耗时: {result['search_time']:.2f}秒")

            if result['results']:
                print("\n   前3篇论文:")
                for i, paper in enumerate(result['results'][:3], 1):
                    print(f"   [{i}] {paper['title'][:50]}...")
                    print(f"       年份: {paper.get('year', 'N/A')}")

            tests_passed += 1
        else:
            print("❌ 小娜工具调用失败")
            tests_failed += 1

    except Exception as e:
        print(f"❌ 小娜工具测试失败: {e}")
        tests_failed += 1
        import traceback
        traceback.print_exc()

    print()

    # 测试总结
    print("=" * 70)
    print("📊 测试总结")
    print("=" * 70)
    print(f"✅ 通过: {tests_passed}")
    print(f"❌ 失败: {tests_failed}")
    print(f"📈 成功率: {(tests_passed/(tests_passed+tests_failed)*100):.1f}%")
    print()

    if tests_failed == 0:
        print("🎉 所有测试通过！Google Scholar功能可以在生产环境使用！")
        print()
        print("📚 生产环境使用指南:")
        print("   1. 导入模块: from core.agents.athena_scholar_tools import scholar_paper_search")
        print("   2. 调用函数: await scholar_paper_search('your query')")
        print("   3. 查看文档: docs/google_scholar_integration.md")
        print()
        print("🚀 启动服务: python production/scripts/scholar_search_service.py")
    else:
        print("⚠️  部分测试失败，请检查配置和依赖")

    print("=" * 70)
    print()


if __name__ == '__main__':
    try:
        asyncio.run(test_production_integration())
    except KeyboardInterrupt:
        print("\n\n⚠️  测试被中断")
    except Exception as e:
        print(f"\n\n❌ 测试异常: {e}")
        sys.exit(1)
