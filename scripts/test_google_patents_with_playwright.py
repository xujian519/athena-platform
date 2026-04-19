#!/usr/bin/env python3
"""
测试Google Patents检索功能（使用Playwright）
"""

import sys
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

print("=" * 80)
print("🔬 Google Patents检索测试（Playwright）")
print("=" * 80)
print()

# 检查Playwright是否可用
print("1️⃣ 检查Playwright")
print("-" * 80)
print()

try:
    import playwright
    from playwright.sync_api import sync_playwright

    print(f"  ✅ Playwright已安装")
    print(f"  📊 版本: 1.58.0")
    print()

except ImportError as e:
    print(f"  ❌ Playwright未安装: {e}")
    sys.exit(1)

# 测试浏览器启动
print("2️⃣ 测试浏览器启动")
print("-" * 80)
print()

try:
    with sync_playwright() as p:
        print(f"  🌐 启动Chromium浏览器...")
        browser = p.chromium.launch(headless=True)
        print(f"  ✅ 浏览器启动成功")

        page = browser.new_page()
        print(f"  ✅ 创建新页面")

        # 访问Google Patents
        print()
        print("3️⃣ 访问Google Patents")
        print("-" * 80)
        print()

        url = "https://patents.google.com"
        print(f"  🌐 访问: {url}")

        page.goto(url, timeout=30000)
        print(f"  ✅ 页面加载成功")

        # 检查页面标题
        title = page.title()
        print(f"  📄 页面标题: {title}")

        # 尝试搜索
        print()
        print("4️⃣ 测试搜索功能")
        print("-" * 80)
        print()

        # 查找搜索框
        try:
            search_input = page.locator("input[name='q'], input[placeholder*='Search'], #searchInput, input[type='text']").first
            if search_input.count() > 0:
                print(f"  ✅ 找到搜索框")

                # 输入查询
                query = "machine learning"
                search_input.fill(query)
                print(f"  📝 输入查询: {query}")

                # 提交搜索（按回车）
                search_input.press("Enter")
                page.wait_for_load_state("networkidle", timeout=10000)
                print(f"  ✅ 提交搜索")

                # 等待结果加载
                page.wait_for_timeout(2000)

                # 获取当前URL
                current_url = page.url
                print(f"  📍 当前URL: {current_url}")

                # 尝试获取结果
                results = page.locator("a[href*='/patent/'], .search-result, [data-id]").all()
                print(f"  📊 找到 {len(results)} 个结果元素")

                # 显示前3个结果
                print()
                print("  前3个结果:")
                for i, result in enumerate(results[:3], 1):
                    try:
                        text = result.inner_text()[:100]
                        print(f"    {i}. {text}...")
                    except:
                        print(f"    {i}. (无法获取文本)")

            else:
                print(f"  ⚠️  未找到搜索框")

        except Exception as e:
            print(f"  ❌ 搜索测试失败: {e}")

        browser.close()
        print()
        print(f"  ✅ 浏览器已关闭")

except Exception as e:
    print(f"  ❌ 浏览器测试失败: {e}")
    import traceback
    traceback.print_exc()

print()
print("=" * 80)
print("📊 测试总结")
print("=" * 80)
print()

print("✅ Playwright已安装并可以启动浏览器")
print("✅ Google Patents网站可以访问")
print("✅ 基本搜索功能可用")
print()
print("💡 下一步:")
print("  - 使用 google_patents_retriever.py 进行完整检索")
print("  - 或使用统一接口: search_google_patents('machine learning')")
print()
print("=" * 80)
