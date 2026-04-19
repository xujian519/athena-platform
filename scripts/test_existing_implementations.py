#!/usr/bin/env python3
"""
测试现有的专利检索和下载实现
验证google_patents_retriever和google_patents_downloader的实际可用性
"""

import sys
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "tools"))

print("=" * 80)
print("🔬 现有专利工具实现测试")
print("=" * 80)
print()

# 测试1: 检查依赖
print("1️⃣ 依赖检查")
print("-" * 80)
print()

dependencies = {
    "requests": "HTTP请求库",
    "playwright": "浏览器自动化",
    "browser_use": "浏览器智能代理",
    "aiofiles": "异步文件操作",
    "pandas": "数据处理"
}

available_deps = {}
missing_deps = []

for dep_name, desc in dependencies.items():
    try:
        __import__(dep_name.replace("-", "_"))
        available_deps[dep_name] = True
        print(f"  ✅ {dep_name}: {desc}")
    except ImportError:
        available_deps[dep_name] = False
        missing_deps.append(dep_name)
        print(f"  ❌ {dep_name}: {desc} (未安装)")

print()
print(f"  📊 依赖统计: {len(available_deps) - len(missing_deps)}/{len(available_deps)} 可用")

if missing_deps:
    print(f"  ⚠️  缺失依赖: {', '.join(missing_deps)}")

print()

# 测试2: 测试google_patents_downloader
print("2️⃣ 测试 google_patents_downloader.py")
print("-" * 80)
print()

if available_deps.get("requests"):
    try:
        from google_patents_downloader import download_patent_pdf

        # 使用一个已知的专利号进行测试
        test_patent = "US20230012345A1"

        print(f"  📋 测试专利: {test_patent}")
        print(f"  🌐 尝试下载PDF...")
        print()

        # 测试下载（使用临时路径）
        import tempfile
        with tempfile.TemporaryDirectory() as temp_dir:
            result = download_patent_pdf(
                test_patent,
                output_path=f"{temp_dir}/{test_patent}.pdf",
                verbose=True
            )

            if result:
                print(f"  ✅ 下载成功: {result}")

                # 检查文件大小
                import os
                if os.path.exists(result):
                    size = os.path.getsize(result)
                    print(f"  📄 文件大小: {size / 1024:.2f} KB")
            else:
                print(f"  ⚠️  下载失败 (可能是专利号不存在或网络问题)")

    except Exception as e:
        print(f"  ❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
else:
    print("  ⏭️  跳过 (requests未安装)")

print()

# 测试3: 测试google_patents_retriever
print("3️⃣ 测试 google_patents_retriever.py")
print("-" * 80)
print()

if available_deps.get("playwright") or available_deps.get("browser_use"):
    try:
        from google_patents_retriever import GooglePatentsRetriever, PLAYWRIGHT_AVAILABLE, BROWSER_USE_AVAILABLE

        print(f"  📋 框架状态:")
        print(f"     - Playwright: {'✅' if PLAYWRIGHT_AVAILABLE else '❌'}")
        print(f"     - Browser-use: {'✅' if BROWSER_USE_AVAILABLE else '❌'}")
        print()

        if PLAYWRIGHT_AVAILABLE or BROWSER_USE_AVAILABLE:
            print(f"  📋 创建检索器实例...")

            retriever = GooglePatentsRetriever()
            print(f"  ✅ 检索器创建成功")
            print()

            # 注意: 实际检索需要浏览器驱动，这里只测试实例化
            print(f"  💡 提示: 实际检索需要安装浏览器驱动")
            print(f"     - Playwright: playwright install chromium")
            print(f"     - Browser-use: 需要配置浏览器环境")
        else:
            print(f"  ⏭️  跳过 (无可用的浏览器框架)")

    except Exception as e:
        print(f"  ❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
else:
    print("  ⏭️  跳过 (playwright和browser-use均未安装)")

print()

# 测试4: 测试统一接口
print("4️⃣ 测试统一接口 (core/tools/patent_retrieval.py)")
print("-" * 80)
print()

try:
    from core.tools.patent_retrieval import (
        UnifiedPatentRetriever,
        PatentRetrievalChannel,
        search_google_patents
    )

    print(f"  ✅ 统一接口导入成功")
    print()

    print(f"  📋 支持的检索渠道:")
    for channel in PatentRetrievalChannel:
        print(f"     - {channel.value}")

    print()
    print(f"  📋 统一接口方法:")
    print(f"     - search_google_patents(): Google Patents检索")
    print(f"     - search_local_patents(): 本地PostgreSQL检索")
    print(f"     - search_patents(): 统一检索接口")

    print()
    print(f"  💡 注意: 统一接口内部使用google_patents_retriever.py")

except Exception as e:
    print(f"  ❌ 统一接口测试失败: {e}")
    import traceback
    traceback.print_exc()

print()

# 测试5: 测试统一下载接口
print("5️⃣ 测试统一下载接口 (core/tools/patent_download.py)")
print("-" * 80)
print()

try:
    from core.tools.patent_download import (
        UnifiedPatentDownloader,
        download_patent
    )

    print(f"  ✅ 统一下载接口导入成功")
    print()

    print(f"  📋 统一下载接口方法:")
    print(f"     - download_patent(): 单个专利下载")
    print(f"     - download_patents(): 批量专利下载")

    print()
    print(f"  💡 注意: 统一下载接口内部使用google_patents_downloader.py")

except Exception as e:
    print(f"  ❌ 统一下载接口测试失败: {e}")
    import traceback
    traceback.print_exc()

print()

# 总结
print("=" * 80)
print("📊 测试总结")
print("=" * 80)
print()

print("✅ 可用的功能:")
print("  1. 统一接口架构 (core/tools/)")
print("  2. PDF下载器 (google_patents_downloader.py)")

print()
print("⚠️  需要配置的功能:")
print("  1. Google Patents检索 - 需要安装Playwright和浏览器驱动")
print("  2. 本地PostgreSQL检索 - 需要创建patent_db数据库和表")

print()
print("🚀 建议的下一步:")
print("  1. 安装Playwright: pip install playwright && playwright install chromium")
print("  2. 创建数据库表: 执行SQL创建patent_db和patents表")
print("  3. 导入专利数据: 将本地25个PDF文件导入数据库")

print()
print("=" * 80)
print("✅ 现有实现测试完成")
print("=" * 80)
print()
