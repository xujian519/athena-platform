#!/usr/bin/env python3
"""
学术搜索工具验证脚本
Academic Search Tool Verification Script

快速验证学术搜索工具的安装和配置状态

作者: Athena平台团队
版本: v1.0.0
创建: 2026-04-19
"""

import sys
from pathlib import Path

def check_imports():
    """检查模块导入"""
    print("1️⃣  检查模块导入...")
    print("-" * 60)

    try:
        from core.tools.handlers.academic_search_handler import (
            academic_search_handler,
            search_papers
        )
        print("✅ academic_search_handler 导入成功")

        from core.tools.academic_search_registration import (
            register_academic_search_tool
        )
        print("✅ academic_search_registration 导入成功")

        from core.tools.unified_registry import get_unified_registry
        print("✅ unified_registry 导入成功")

        return True

    except ImportError as e:
        print(f"❌ 导入失败: {e}")
        return False


def check_registry():
    """检查工具注册状态"""
    print("\n2️⃣  检查工具注册状态...")
    print("-" * 60)

    try:
        from core.tools.unified_registry import get_unified_registry

        registry = get_unified_registry()
        print(f"✅ 工具注册表获取成功")
        print(f"   已注册工具总数: {len(registry.tools)}")

        # 检查academic_search是否已注册
        if registry.is_registered("academic_search"):
            print("✅ academic_search 工具已注册")

            # 获取工具信息
            tool = registry.get("academic_search")
            print(f"   工具名称: {tool.name}")
            print(f"   工具分类: {tool.category}")
            print(f"   工具描述: {tool.description}")

            return True
        else:
            print("⚠️  academic_search 工具尚未注册")
            print("   尝试手动注册...")

            from core.tools.academic_search_registration import register_academic_search_tool
            if register_academic_search_tool():
                print("✅ 手动注册成功")
                return True
            else:
                print("❌ 手动注册失败")
                return False

    except Exception as e:
        print(f"❌ 检查失败: {e}")
        return False


def check_dependencies():
    """检查依赖项"""
    print("\n3️⃣  检查依赖项...")
    print("-" * 60)

    dependencies = {
        "aiohttp": "HTTP客户端库",
        "asyncio": "异步支持（标准库）"
    }

    all_ok = True

    for package, description in dependencies.items():
        try:
            __import__(package)
            print(f"✅ {package}: {description}")
        except ImportError:
            print(f"❌ {package}: 未安装 - {description}")
            all_ok = False

    return all_ok


def check_api_config():
    """检查API配置"""
    print("\n4️⃣  检查API配置...")
    print("-" * 60)

    import os

    # 检查Serper API密钥
    serper_key = os.getenv("SERPER_API_KEY")
    if serper_key:
        print(f"✅ SERPER_API_KEY: 已配置（长度: {len(serper_key)}）")
    else:
        print("⚠️  SERPER_API_KEY: 未配置")
        print("   说明: Google Scholar搜索需要此密钥，Semantic Scholar无需密钥")
        print("   获取方式: 访问 https://serper.dev/ 注册获取")

    # Semantic Scholar无需密钥
    print("✅ Semantic Scholar API: 无需密钥（免费使用）")

    return True


def check_file_structure():
    """检查文件结构"""
    print("\n5️⃣  检查文件结构...")
    print("-" * 60)

    base_path = Path("/Users/xujian/Athena工作平台")

    files_to_check = {
        "Handler": "core/tools/handlers/academic_search_handler.py",
        "注册模块": "core/tools/academic_search_registration.py",
        "测试文件": "tests/core/tools/test_academic_search_handler.py",
        "示例代码": "examples/academic_search_usage_examples.py",
        "验证报告": "docs/reports/ACADEMIC_SEARCH_TOOL_VERIFICATION_REPORT_20260419.md",
        "使用指南": "docs/guides/ACADEMIC_SEARCH_QUICK_START_GUIDE.md"
    }

    all_exist = True

    for name, relative_path in files_to_check.items():
        full_path = base_path / relative_path
        if full_path.exists():
            print(f"✅ {name}: {relative_path}")
        else:
            print(f"❌ {name}: {relative_path} (不存在)")
            all_exist = False

    return all_exist


async def test_basic_functionality():
    """测试基本功能"""
    print("\n6️⃣  测试基本功能...")
    print("-" * 60)

    try:
        from core.tools.handlers.academic_search_handler import search_papers

        print("🔍 执行测试搜索: 'artificial intelligence' (limit=3)")

        result = await search_papers(
            query="artificial intelligence",
            limit=3
        )

        if result["success"]:
            print(f"✅ 搜索成功")
            print(f"   找到结果: {result['total_results']} 篇")
            print(f"   数据源: {result['source']}")

            if result["results"]:
                print("\n   前3个结果:")
                for paper in result["results"][:3]:
                    print(f"   • {paper['title']}")
                    print(f"     作者: {', '.join(paper['authors'][:2])}{'...' if len(paper['authors']) > 2 else ''}")
                    print(f"     年份: {paper['year'] or 'N/A'}")

            return True
        else:
            print(f"❌ 搜索失败: {result.get('error', 'Unknown error')}")
            return False

    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def print_summary(results):
    """打印验证总结"""
    print("\n" + "=" * 60)
    print("📊 验证总结")
    print("=" * 60)

    total = len(results)
    passed = sum(results.values())
    failed = total - passed

    print(f"总检查项: {total}")
    print(f"✅ 通过: {passed}")
    print(f"❌ 失败: {failed}")

    if all(results.values()):
        print("\n🎉 所有检查通过！学术搜索工具可以正常使用。")
    else:
        print("\n⚠️  部分检查未通过，请查看上述详情。")

    print("\n📚 相关文档:")
    print("  • 验证报告: docs/reports/ACADEMIC_SEARCH_TOOL_VERIFICATION_REPORT_20260419.md")
    print("  • 使用指南: docs/guides/ACADEMIC_SEARCH_QUICK_START_GUIDE.md")
    print("  • 示例代码: examples/academic_search_usage_examples.py")

    print("\n🚀 快速开始:")
    print("  from core.tools.handlers.academic_search_handler import search_papers")
    print("  result = await search_papers('your query', limit=10)")

    print("\n" + "=" * 60)


async def main():
    """主函数"""
    print("\n")
    print("🔍 Athena平台 - 学术搜索工具验证")
    print("=" * 60)
    print("\n")

    results = {}

    # 执行各项检查
    results["模块导入"] = check_imports()
    results["工具注册"] = check_registry()
    results["依赖项"] = check_dependencies()
    results["API配置"] = check_api_config()
    results["文件结构"] = check_file_structure()
    results["基本功能"] = await test_basic_functionality()

    # 打印总结
    print_summary(results)


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
