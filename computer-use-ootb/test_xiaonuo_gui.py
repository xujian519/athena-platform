#!/usr/bin/env python3
"""
测试小诺GUI控制器功能
"""

import asyncio
import json
import aiohttp

async def test_xiaonuo_gui():
    """测试小诺GUI控制器的各种功能"""

    base_url = "http://localhost:8000"

    async with aiohttp.ClientSession() as session:

        print("🚀 开始测试小诺GUI控制器...\n")

        # 测试1：健康检查
        print("1. 测试健康检查...")
        async with session.get(f"{base_url}/health") as resp:
            if resp.status == 200:
                data = await resp.json()
                print(f"   ✓ 服务状态: {data['status']}")
            else:
                print(f"   ✗ 健康检查失败: {resp.status}")
                return

        # 测试2：屏幕截图
        print("\n2. 测试屏幕截图...")
        async with session.post(f"{base_url}/screenshot") as resp:
            if resp.status == 200:
                data = await resp.json()
                print(f"   ✓ 截图成功: {data['screenshot_path']}")
            else:
                print(f"   ✗ 截图失败: {resp.status}")

        # 测试3：屏幕分析
        print("\n3. 测试屏幕分析...")
        analyze_request = {
            "question": "请描述当前屏幕上的主要内容"
        }
        async with session.post(
            f"{base_url}/analyze-screen",
            json=analyze_request
        ) as resp:
            if resp.status == 200:
                data = await resp.json()
                print("   ✓ 屏幕分析成功")
                print(f"   分析结果: {data.get('content', '无内容')[:200]}...")
            else:
                print(f"   ✗ 屏幕分析失败: {resp.status}")
                error = await resp.text()
                print(f"   错误信息: {error}")

        # 测试4：命令执行（简单的测试命令）
        print("\n4. 测试命令执行...")
        command_request = {
            "command": "分析当前屏幕，并告诉我如何点击屏幕左上角的图标",
            "enable_confirmation": False,  # 关闭确认以便测试
            "timeout": 30
        }

        print(f"   发送命令: {command_request['command']}")
        async with session.post(
            f"{base_url}/execute-command",
            json=command_request
        ) as resp:
            if resp.status == 200:
                data = await resp.json()
                print("   ✓ 命令执行成功")
                print(f"   执行结果: {data.get('message', '无消息')}")
                if 'glm_analysis' in data:
                    print(f"   GLM分析: {data['glm_analysis'][:300]}...")
            else:
                print(f"   ✗ 命令执行失败: {resp.status}")
                error = await resp.text()
                print(f"   错误信息: {error}")

        print("\n✅ 测试完成！")
        print("\n📋 小诺GUI控制器功能:")
        print("   - 屏幕截图和分析")
        print("   - 基于GLM-4V的视觉理解")
        print("   - 智能GUI操作指导")
        print("   - 交互式操作确认")

        print("\n🌐 API地址:")
        print(f"   - 主服务: {base_url}")
        print(f"   - API文档: {base_url}/docs")

if __name__ == "__main__":
    # 运行测试
    asyncio.run(test_xiaonuo_gui())