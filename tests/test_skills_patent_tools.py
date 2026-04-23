#!/usr/bin/env python3
"""
测试技能工具：专利检索和下载

验证：
1. 工具是否正确注册到统一注册表
2. 检索智能体是否能调用这些工具
3. 基本功能是否可用

Author: Athena平台团队
Created: 2026-04-23
"""

import asyncio
import sys
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


async def test_tool_registration():
    """测试工具注册"""
    print("\n" + "="*70)
    print("测试1: 工具注册验证")
    print("="*70)

    try:
        from core.tools.unified_registry import get_unified_registry

        registry = get_unified_registry()

        # 检查工具是否注册
        tools_to_check = [
            "skills_patent_search",
            "skills_patent_download",
            "skills_patent_batch_download",
            "skills_patent_info"
        ]

        print("\n检查工具注册状态:")
        all_registered = True
        for tool_id in tools_to_check:
            tool = registry.get(tool_id)
            is_registered = tool is not None
            status = "✅ 已注册" if is_registered else "❌ 未注册"
            print(f"  {tool_id}: {status}")

            if is_registered:
                # 尝试获取元数据
                if hasattr(tool, 'metadata'):
                    print(f"    - 描述: {tool.metadata.get('description', 'N/A')}")
                    print(f"    - 类别: {tool.metadata.get('category', 'N/A')}")
                    print(f"    - 版本: {tool.metadata.get('version', 'N/A')}")
            else:
                all_registered = False

        if all_registered:
            print("\n✅ 所有工具注册成功")
            return True
        else:
            print("\n⚠️  部分工具未注册")
            return False

    except Exception as e:
        print(f"\n❌ 工具注册测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_patent_search():
    """测试专利检索"""
    print("\n" + "="*70)
    print("测试2: 专利检索功能")
    print("="*70)

    try:
        from core.tools.unified_registry import get_unified_registry

        registry = get_unified_registry()
        tool = registry.get("skills_patent_search")

        if not tool:
            print("❌ 专利检索工具未注册")
            return False

        # 测试检索
        print("\n执行检索测试:")
        print("  查询: '骨髓腔输液装置'")

        result = tool.function(
            query="骨髓腔输液装置",
            num_results=5,
            output_dir="/tmp/patent_search_test"
        )

        if result.get("success"):
            print(f"  ✅ 检索成功")
            print(f"  - 检索式: {result.get('query', 'N/A')}")
            print(f"  - 检索链接: {result.get('search_url', 'N/A')[:60]}...")
            print(f"  - 报告路径: {result.get('report_path', 'N/A')}")
            print(f"  - JSON路径: {result.get('json_path', 'N/A')}")
            return True
        else:
            print(f"  ❌ 检索失败: {result.get('error', 'Unknown error')}")
            return False

    except Exception as e:
        print(f"\n❌ 专利检索测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_patent_info():
    """测试专利信息查询"""
    print("\n" + "="*70)
    print("测试3: 专利信息查询")
    print("="*70)

    try:
        from core.tools.unified_registry import get_unified_registry

        registry = get_unified_registry()
        tool = registry.get("skills_patent_info")

        if not tool:
            print("❌ 专利信息查询工具未注册")
            return False

        # 测试信息查询
        print("\n执行信息查询测试:")
        print("  专利号: US11739244B2")

        result = tool.function(
            patent_number="US11739244B2"
        )

        if result.get("success"):
            print(f"  ✅ 查询成功")
            print(f"  - 专利号: {result.get('patent_number', 'N/A')}")
            print(f"  - 标题: {result.get('title', 'N/A')[:60]}...")
            print(f"  - 专利页: {result.get('patent_url', 'N/A')[:60]}...")
            return True
        else:
            print(f"  ❌ 查询失败: {result.get('error', 'Unknown error')}")
            return False

    except Exception as e:
        print(f"\n❌ 专利信息查询测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_retriever_agent():
    """测试检索智能体集成"""
    print("\n" + "="*70)
    print("测试4: 检索智能体集成")
    print("="*70)

    try:
        from core.framework.agents.xiaona.retriever_agent import RetrieverAgent
        from core.framework.agents.xiaona.base_component import AgentExecutionContext

        # 创建检索智能体
        print("\n创建检索智能体...")
        agent = RetrieverAgent()

        print(f"  ✅ 智能体ID: {agent.agent_id}")
        print(f"  ✅ 智能体状态: {agent.status.value}")

        # 检查能力
        capabilities = agent.get_capabilities()
        print(f"\n智能体能力 (共{len(capabilities)}个):")
        for cap in capabilities:
            print(f"  - {cap.name}: {cap.description}")

        # 检查是否包含下载能力
        has_download = any(cap.name == "patent_download" for cap in capabilities)

        if has_download:
            print("\n✅ 检索智能体已集成专利下载能力")
            return True
        else:
            print("\n⚠️  检索智能体未包含专利下载能力")
            return False

    except Exception as e:
        print(f"\n❌ 检索智能体测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """主测试函数"""
    print("\n" + "="*70)
    print("技能工具测试：专利检索和下载")
    print("="*70)

    results = []

    # 测试1: 工具注册
    results.append(await test_tool_registration())

    # 测试2: 专利检索
    results.append(await test_patent_search())

    # 测试3: 专利信息查询
    results.append(await test_patent_info())

    # 测试4: 检索智能体集成
    results.append(await test_retriever_agent())

    # 汇总结果
    print("\n" + "="*70)
    print("测试结果汇总")
    print("="*70)

    test_names = [
        "工具注册验证",
        "专利检索功能",
        "专利信息查询",
        "检索智能体集成"
    ]

    for i, (name, result) in enumerate(zip(test_names, results), 1):
        status = "✅ 通过" if result else "❌ 失败"
        print(f"  测试{i}: {name} - {status}")

    passed = sum(results)
    total = len(results)

    print(f"\n总计: {passed}/{total} 测试通过")

    if passed == total:
        print("\n✅ 所有测试通过！技能工具已成功集成到检索智能体。")
        return 0
    else:
        print(f"\n⚠️  {total - passed} 个测试失败，请检查错误信息。")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
