#!/usr/bin/env python3
"""
API集成测试
Integration Tests for Browser Automation Service

作者: 小诺·双鱼公主
版本: 1.0.0
"""

import asyncio

import httpx

# 服务基础URL
BASE_URL = "http://localhost:8030"


async def test_health_check():
    """测试健康检查端点"""
    print("\n🧪 测试健康检查...")

    async with httpx.AsyncClient() as client:
        response = await client.get(f"{BASE_URL}/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "active_sessions" in data
        print("✅ 健康检查测试通过")


async def test_navigate():
    """测试导航端点"""
    print("\n🧪 测试导航功能...")

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            f"{BASE_URL}/api/v1/navigate",
            json={"url": "https://www.baidu.com", "wait_until": "load"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "title" in data
        print(f"✅ 导航测试通过 - 标题: {data.get('title')}")


async def test_screenshot():
    """测试截图端点"""
    print("\n🧪 测试截图功能...")

    async with httpx.AsyncClient(timeout=30.0) as client:
        # 先导航到页面
        await client.post(
            f"{BASE_URL}/api/v1/navigate", json={"url": "https://www.baidu.com"}
        )

        # 截图
        response = await client.post(
            f"{BASE_URL}/api/v1/screenshot", json={"full_page": False}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "screenshot" in data
        assert len(data["screenshot"]) > 0
        print(f"✅ 截图测试通过 - 尺寸: {data['width']}x{data['height']}")


async def test_get_content():
    """测试获取内容端点"""
    print("\n🧪 测试获取内容功能...")

    async with httpx.AsyncClient(timeout=30.0) as client:
        # 先导航到页面
        await client.post(
            f"{BASE_URL}/api/v1/navigate", json={"url": "https://www.baidu.com"}
        )

        # 获取内容
        response = await client.get(f"{BASE_URL}/api/v1/content")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "title" in data
        assert "links" in data
        print(f"✅ 获取内容测试通过 - 链接数: {len(data.get('links', []))}")


async def test_evaluate():
    """测试执行JavaScript端点"""
    print("\n🧪 测试执行JavaScript功能...")

    async with httpx.AsyncClient(timeout=30.0) as client:
        # 先导航到页面
        await client.post(
            f"{BASE_URL}/api/v1/navigate", json={"url": "https://www.baidu.com"}
        )

        # 执行JavaScript
        response = await client.post(
            f"{BASE_URL}/api/v1/evaluate", json={"script": "document.title"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "result" in data
        print(f"✅ 执行JavaScript测试通过 - 结果: {data.get('result')}")


async def test_task():
    """测试智能任务端点"""
    print("\n🧪 测试智能任务功能...")

    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(
            f"{BASE_URL}/api/v1/task",
            json={"task": "打开百度首页", "max_steps": 10},
        )
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "steps_taken" in data
        print(f"✅ 智能任务测试通过 - 状态: {data.get('status')}, 步数: {data.get('steps_taken')}")


async def test_status():
    """测试状态端点"""
    print("\n🧪 测试状态功能...")

    async with httpx.AsyncClient() as client:
        response = await client.get(f"{BASE_URL}/api/v1/status")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "active_sessions" in data
        print(f"✅ 状态测试通过 - 活跃会话: {data.get('active_sessions')}")


async def test_config():
    """测试配置端点"""
    print("\n🧪 测试配置功能...")

    async with httpx.AsyncClient() as client:
        response = await client.get(f"{BASE_URL}/api/v1/config")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "config" in data
        print(f"✅ 配置测试通过 - 服务名: {data['config'].get('service_name')}")


async def run_all_tests():
    """运行所有测试"""
    print("=" * 60)
    print("🚀 开始运行API集成测试")
    print("=" * 60)

    tests = [
        ("健康检查", test_health_check),
        ("导航功能", test_navigate),
        ("截图功能", test_screenshot),
        ("获取内容", test_get_content),
        ("执行JavaScript", test_evaluate),
        ("智能任务", test_task),
        ("状态查询", test_status),
        ("配置查询", test_config),
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
