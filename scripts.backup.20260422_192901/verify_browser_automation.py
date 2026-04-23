#!/usr/bin/env python3
"""
浏览器自动化工具验证脚本
Browser Automation Tool Verification Script

验证browser_automation工具的完整可用性。

Author: Athena平台团队
Created: 2026-04-19
"""

import sys
import logging
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core.tools.browser_automation_handler import browser_automation_handler, ToolContext

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def print_section(title: str):
    """打印分节标题"""
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60)


def test_health_check():
    """测试健康检查"""
    print_section("1️⃣  健康检查测试")

    context = ToolContext(
        tool_id="browser_automation",
        parameters={"action": "health_check"}
    )

    result = browser_automation_handler(context)

    if result.success:
        print(f"✅ 健康检查通过")
        print(f"   消息: {result.message}")
        if result.data:
            print(f"   数据: {result.data}")
        return True
    else:
        print(f"❌ 健康检查失败")
        print(f"   错误: {result.error}")
        print(f"   消息: {result.message}")
        return False


def test_navigate():
    """测试页面导航"""
    print_section("2️⃣  页面导航测试")

    context = ToolContext(
        tool_id="browser_automation",
        parameters={
            "action": "navigate",
            "url": "https://www.baidu.com",
            "wait_until": "load"
        }
    )

    result = browser_automation_handler(context)

    if result.success:
        print(f"✅ 页面导航成功")
        print(f"   消息: {result.message}")
        return True
    else:
        print(f"❌ 页面导航失败")
        print(f"   错误: {result.error}")
        print(f"   消息: {result.message}")
        return False


def test_get_content():
    """测试获取页面内容"""
    print_section("3️⃣  获取页面内容测试")

    context = ToolContext(
        tool_id="browser_automation",
        parameters={"action": "get_content"}
    )

    result = browser_automation_handler(context)

    if result.success:
        print(f"✅ 获取页面内容成功")
        if result.data and "title" in result.data:
            print(f"   页面标题: {result.data['title']}")
        return True
    else:
        print(f"❌ 获取页面内容失败")
        print(f"   错误: {result.error}")
        return False


def test_screenshot():
    """测试页面截图"""
    print_section("4️⃣  页面截图测试")

    import tempfile
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
        save_path = f.name

    context = ToolContext(
        tool_id="browser_automation",
        parameters={
            "action": "screenshot",
            "full_page": False,
            "save_path": save_path
        }
    )

    result = browser_automation_handler(context)

    if result.success:
        print(f"✅ 页面截图成功")
        if result.data and "saved_path" in result.data:
            print(f"   保存路径: {result.data['saved_path']}")
        return True
    else:
        print(f"❌ 页面截图失败")
        print(f"   错误: {result.error}")
        return False


def test_execute_task():
    """测试智能任务执行"""
    print_section("5️⃣  智能任务执行测试")

    context = ToolContext(
        tool_id="browser_automation",
        parameters={
            "action": "execute_task",
            "task": "打开百度首页"
        }
    )

    result = browser_automation_handler(context)

    if result.success:
        print(f"✅ 智能任务执行成功")
        print(f"   消息: {result.message}")
        return True
    else:
        print(f"❌ 智能任务执行失败")
        print(f"   错误: {result.error}")
        return False


def main():
    """主测试流程"""
    print_section("🌐 浏览器自动化工具验证")

    print("\n📋 测试计划:")
    print("   1. 健康检查")
    print("   2. 页面导航")
    print("   3. 获取页面内容")
    print("   4. 页面截图")
    print("   5. 智能任务执行")

    # 执行测试
    tests = [
        ("健康检查", test_health_check),
        ("页面导航", test_navigate),
        ("获取页面内容", test_get_content),
        ("页面截图", test_screenshot),
        ("智能任务执行", test_execute_task),
    ]

    results = []
    for name, test_func in tests:
        try:
            passed = test_func()
            results.append((name, passed))
        except Exception as e:
            logger.error(f"测试 '{name}' 抛出异常: {e}")
            results.append((name, False))

    # 汇总结果
    print_section("📊 测试结果汇总")

    passed_count = sum(1 for _, passed in results if passed)
    total_count = len(results)

    for name, passed in results:
        status = "✅ 通过" if passed else "❌ 失败"
        print(f"   {status}  {name}")

    print(f"\n总计: {passed_count}/{total_count} 测试通过")

    if passed_count == total_count:
        print("\n🎉 所有测试通过！browser_automation工具验证成功。")
        return 0
    else:
        print(f"\n⚠️  {total_count - passed_count} 个测试失败，请检查浏览器自动化服务状态。")
        return 1


if __name__ == "__main__":
    sys.exit(main())
