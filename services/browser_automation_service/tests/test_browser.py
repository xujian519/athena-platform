#!/usr/bin/env python3
"""
浏览器操作测试
Browser Operation Tests for Browser Automation Service

作者: 小诺·双鱼公主
版本: 1.0.0
"""

import asyncio

from config.browser_config import get_browser_config
from core.browser_manager import get_browser_manager
from core.playwright_engine import get_engine
from core.session_manager import get_session_manager
from core.task_executor import TaskExecutor


async def test_engine_initialization():
    """测试Playwright引擎初始化"""
    print("\n🧪 测试Playwright引擎初始化...")

    engine = await get_engine()
    assert engine is not None
    assert engine.is_initialized is True
    print(f"✅ 引擎初始化成功 - 浏览器类型: {engine.config.browser_type}")


async def test_browser_manager():
    """测试浏览器管理器"""
    print("\n🧪 测试浏览器管理器...")

    manager = await get_browser_manager()

    # 测试导航
    result = await manager.navigate("https://www.baidu.com")
    assert result["success"] is True
    assert "title" in result
    print(f"✅ 导航成功 - 标题: {result['title']}")

    # 测试截图
    result = await manager.screenshot(full_page=False)
    assert result["success"] is True
    assert "screenshot" in result
    print(f"✅ 截图成功 - 尺寸: {result['width']}x{result['height']}")

    # 测试获取内容
    result = await manager.get_content()
    assert result["success"] is True
    assert "title" in result
    print(f"✅ 获取内容成功 - 链接数: {len(result.get('links', []))}")


async def test_session_manager():
    """测试会话管理器"""
    print("\n🧪 测试会话管理器...")

    session_manager = get_session_manager()

    # 创建会话
    engine = await get_engine()
    context = await engine.create_context("test_context")
    page = await engine.get_page("test_context")

    session = await session_manager.create_session(
        page, context, "test_context", {"test": "data"}
    )

    assert session is not None
    assert session.session_id is not None
    print(f"✅ 创建会话成功 - ID: {session.session_id}")

    # 获取会话
    retrieved = await session_manager.get_session(session.session_id)
    assert retrieved is not None
    assert retrieved.session_id == session.session_id
    print("✅ 获取会话成功")

    # 列出会话
    sessions = await session_manager.list_sessions()
    assert len(sessions) > 0
    print(f"✅ 列出会话成功 - 数量: {len(sessions)}")

    # 删除会话
    deleted = await session_manager.delete_session(session.session_id)
    assert deleted is True
    print("✅ 删除会话成功")


async def test_task_executor():
    """测试任务执行器"""
    print("\n🧪 测试任务执行器...")

    manager = await get_browser_manager()
    executor = TaskExecutor(browser_manager=manager)

    # 测试简单任务
    result = await executor.execute("打开百度首页")
    assert result["success"] is True
    assert result["status"] == "completed"
    print(f"✅ 任务执行成功 - 步数: {result['steps_taken']}")

    # 测试带URL的任务
    result = await executor.execute("访问页面", url="https://www.baidu.com")
    assert result["success"] is True
    print("✅ 带URL任务执行成功")


async def test_browser_config():
    """测试浏览器配置"""
    print("\n🧪 测试浏览器配置...")

    config = get_browser_config("chromium")
    assert config.browser_type == "chromium"
    assert config.headless is True
    print("✅ Chromium配置加载成功")

    launch_options = config.get_launch_options()
    assert "headless" in launch_options
    assert "args" in launch_options
    print("✅ 启动选项生成成功")


async def run_all_tests():
    """运行所有测试"""
    print("=" * 60)
    print("🚀 开始运行浏览器操作测试")
    print("=" * 60)

    tests = [
        ("引擎初始化", test_engine_initialization),
        ("浏览器管理器", test_browser_manager),
        ("会话管理器", test_session_manager),
        ("任务执行器", test_task_executor),
        ("浏览器配置", test_browser_config),
    ]

    passed = 0
    failed = 0

    for name, test_func in tests:
        try:
            await test_func()
            passed += 1
        except AssertionError as e:
            print(f"❌ {name}测试失败: {e}")
            failed += 1
        except Exception as e:
            print(f"❌ {name}测试出错: {e}")
            failed += 1

    print("\n" + "=" * 60)
    print(f"📊 测试结果: {passed} 通过, {failed} 失败")
    print("=" * 60)

    return failed == 0


if __name__ == "__main__":
    success = asyncio.run(run_all_tests())
    exit(0 if success else 1)
