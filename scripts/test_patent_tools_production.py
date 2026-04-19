#!/usr/bin/env python3
"""
专利工具生产环境集成测试
验证专利检索和下载工具在生产环境中的完整功能
"""

import asyncio
import sys
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

print("=" * 80)
print("🔬 专利工具生产环境集成测试")
print("=" * 80)
print()

async def test_tool_registration():
    """测试工具注册"""
    print("1️⃣ 工具注册测试")
    print("-" * 80)
    print()

    try:
        from core.tools.tool_call_manager import get_tool_manager

        # 获取工具调用管理器（会自动触发工具注册）
        manager = get_tool_manager()

        print(f"  ✅ 工具调用管理器初始化成功")
        print()

        # 检查专利工具是否已注册
        tool_ids = manager.list_tools()

        patent_tools = [tid for tid in tool_ids if 'patent' in tid.lower()]

        print(f"  📋 已注册的专利工具: {len(patent_tools)}")
        for tool_id in patent_tools:
            tool = manager.get_tool(tool_id)
            print(f"     - {tool_id}")
            if tool:
                print(f"       名称: {tool.name}")
                print(f"       分类: {tool.category.value}")
                print(f"       状态: {'✅ 启用' if tool.enabled else '❌ 禁用'}")
            print()

        # 检查特定工具
        required_tools = ['patent_search', 'patent_download']
        missing_tools = [t for t in required_tools if t not in patent_tools]

        if missing_tools:
            print(f"  ❌ 缺失工具: {', '.join(missing_tools)}")
            return False
        else:
            print(f"  ✅ 所有必需工具已注册")

        return True

    except Exception as e:
        print(f"  ❌ 工具注册测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

    print()


async def test_patent_search():
    """测试专利检索功能"""
    print("2️⃣ 专利检索功能测试")
    print("-" * 80)
    print()

    try:
        from core.tools.tool_call_manager import get_tool_manager

        manager = get_tool_manager()

        # 测试Google Patents检索
        print(f"  📋 测试查询: machine learning")
        print(f"  🔍 渠道: google_patents")
        print()

        result = await manager.call_tool(
            "patent_search",
            parameters={
                "query": "machine learning",
                "channel": "google_patents",
                "max_results": 3
            }
        )

        if result.status.value == "success":
            print(f"  ✅ 检索成功")
            print(f"  📊 执行时间: {result.execution_time:.2f}秒")

            # 处理结果
            result_data = result.result
            if isinstance(result_data, dict):
                total = result_data.get('total_results', 'N/A')
                print(f"  📊 结果数量: {total}")
                print()

                # 显示前3个结果
                results = result_data.get('results', [])
                for i, item in enumerate(results[:3], 1):
                    print(f"  {i}. {item.get('patent_id', 'N/A')}")
                    print(f"     标题: {item.get('title', 'N/A')[:80]}...")
                    print(f"     来源: {item.get('source', 'N/A')}")
                print()

            return True
        else:
            print(f"  ❌ 检索失败: {result.error or 'Unknown error'}")
            return False

    except Exception as e:
        print(f"  ❌ 专利检索测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

    print()


async def test_patent_download():
    """测试专利下载功能"""
    print("3️⃣ 专利下载功能测试")
    print("-" * 80)
    print()

    try:
        from core.tools.tool_call_manager import get_tool_manager

        manager = get_tool_manager()

        # 测试单个专利下载
        test_patent = "US20230012345A1"
        print(f"  📋 测试专利: {test_patent}")
        print(f"  💾 下载到: /tmp/patents")
        print()

        result = await manager.call_tool(
            "patent_download",
            parameters={
                "patent_numbers": [test_patent],
                "output_dir": "/tmp/patents"
            }
        )

        if result.get("status") == "success":
            print(f"  ✅ 下载成功")

            # 显示下载结果
            results = result.get('result', {}).get('results', [])
            for item in results:
                if item.get('success'):
                    print(f"  📄 文件路径: {item.get('file_path')}")
                    print(f"  📊 文件大小: {item.get('file_size_mb', 0):.2f} MB")
                    print(f"  ⏱️  下载耗时: {item.get('download_time', 0):.2f} 秒")
                else:
                    print(f"  ❌ 下载失败: {item.get('error', 'Unknown error')}")
            print()

            return True
        else:
            print(f"  ❌ 下载失败: {result.get('error', 'Unknown error')}")
            return False

    except Exception as e:
        print(f"  ❌ 专利下载测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

    print()


async def test_dual_channel_search():
    """测试双渠道并发检索"""
    print("4️⃣ 双渠道并发检索测试")
    print("-" * 80)
    print()

    try:
        from core.tools.tool_call_manager import get_tool_manager

        manager = get_tool_manager()

        # 测试双渠道检索
        print(f"  📋 测试查询: AI芯片")
        print(f"  🔍 渠道: both (本地 + Google)")
        print()

        result = await manager.call_tool(
            "patent_search",
            parameters={
                "query": "AI芯片",
                "channel": "both",
                "max_results": 5
            }
        )

        if result.get("status") == "success":
            print(f"  ✅ 双渠道检索成功")

            results = result.get('result', {})

            # 显示各渠道结果数
            if 'local' in results:
                local_count = len(results.get('local', []))
                print(f"  📊 本地结果: {local_count}")

            if 'google' in results:
                google_count = len(results.get('google', []))
                print(f"  📊 Google结果: {google_count}")

            total_results = results.get('total_results', 0)
            print(f"  📊 总结果数: {total_results}")
            print()

            return True
        else:
            print(f"  ❌ 双渠道检索失败: {result.get('error', 'Unknown error')}")
            return False

    except Exception as e:
        print(f"  ❌ 双渠道检索测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

    print()


async def test_batch_download():
    """测试批量下载功能"""
    print("5️⃣ 批量下载功能测试")
    print("-" * 80)
    print()

    try:
        from core.tools.tool_call_manager import get_tool_manager

        manager = get_tool_manager()

        # 测试批量下载
        test_patents = ["US20230012345A1", "US20230012346A1"]
        print(f"  📋 测试专利: {', '.join(test_patents)}")
        print(f"  💾 下载到: /tmp/patents")
        print()

        result = await manager.call_tool(
            "patent_download",
            parameters={
                "patent_numbers": test_patents,
                "output_dir": "/tmp/patents"
            }
        )

        if result.get("status") == "success":
            print(f"  ✅ 批量下载完成")

            results = result.get('result', {}).get('results', [])
            success_count = sum(1 for r in results if r.get('success'))
            total_count = len(results)

            print(f"  📊 成功: {success_count}/{total_count}")

            for item in results:
                patent_id = item.get('patent_number', 'N/A')
                if item.get('success'):
                    print(f"     ✅ {patent_id}: {item.get('file_size_mb', 0):.2f} MB")
                else:
                    print(f"     ❌ {patent_id}: {item.get('error', 'Unknown error')}")

            print()

            return True
        else:
            print(f"  ❌ 批量下载失败: {result.get('error', 'Unknown error')}")
            return False

    except Exception as e:
        print(f"  ❌ 批量下载测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

    print()


async def main():
    """主测试函数"""
    all_passed = True

    # 1. 工具注册测试
    passed = await test_tool_registration()
    all_passed = all_passed and passed

    # 2. 专利检索测试
    passed = await test_patent_search()
    all_passed = all_passed and passed

    # 3. 专利下载测试
    passed = await test_patent_download()
    all_passed = all_passed and passed

    # 4. 双渠道检索测试
    passed = await test_dual_channel_search()
    all_passed = all_passed and passed

    # 5. 批量下载测试
    passed = await test_batch_download()
    all_passed = all_passed and passed

    # 总结
    print("=" * 80)
    print("📊 测试总结")
    print("=" * 80)
    print()

    if all_passed:
        print("✅ 所有测试通过")
        print()
        print("🚀 专利工具已成功集成到生产环境工具库")
        print()
        print("📋 可用功能:")
        print("  1. 专利检索 - patent_search")
        print("  2. 专利下载 - patent_download")
        print("  3. 双渠道检索 - 同时使用本地和Google")
        print("  4. 批量下载 - 一次下载多个专利")
        print()
        print("💡 使用方式:")
        print("  from core.tools import get_tool_manager")
        print("  manager = get_tool_manager()")
        print("  result = await manager.call_tool('patent_search', parameters={...})")
        print()
    else:
        print("❌ 部分测试失败")
        print()
        print("💡 请检查:")
        print("  1. 工具是否正确注册")
        print("  2. Playwright是否已安装")
        print("  3. 数据库表是否已创建")
        print("  4. 网络连接是否正常")
        print()

    print("=" * 80)
    print("✅ 生产环境集成测试完成")
    print("=" * 80)
    print()

    return 0 if all_passed else 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
